"""CPU contract tests using synthetic activations, not empirical model evidence."""

import copy
import importlib
import json

import numpy as np
import pytest
import torch


@pytest.fixture(scope="module")
def monitors():
    return importlib.import_module("vrm.monitors")


@pytest.fixture(autouse=True)
def cpu_threads():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def records(prefix, count=6):
    rng = np.random.default_rng(42)
    return [
        dict(
            text=("valid proof" if i % 2 else "invalid attempt") + f" {prefix}",
            sum_logp=-float(i + 2),
            mean_logp=-float(i + 2) / 3,
            activations=rng.normal(size=(2 + i % 3, 8, 4)).astype(np.float32),
            label=i % 2,
            task_id=f"{prefix}-{i // 2}",
            split="train" if prefix == "train" else "val",
        )
        for i in range(count)
    ]


def test_motion_order_has_no_cross_token_difference(monitors):
    x = torch.tensor([[[0.0], [1.0], [3.0]], [[10.0], [14.0], [19.0]]])
    torch.testing.assert_close(
        monitors.motion_sequence(x), torch.tensor([[1.0], [2.0], [4.0], [5.0]])
    )


def test_static_features_normalize_each_final_layer(monitors):
    record = dict(activations=np.array([[[99, 99], [88, 88]], [[3, 4], [0, 0]]]))
    np.testing.assert_allclose(monitors.static_features(record), [0.6, 0.8, 0, 0])


def test_relative_sites_have_explicit_post_block_indices(monitors):
    assert monitors.relative_layer_sites(26) == (6, 9, 12, 15, 19, 22)
    assert monitors.relative_layer_sites(32) == (7, 11, 15, 19, 23, 27)
    with pytest.raises(ValueError, match="six|6"):
        monitors.relative_layer_sites(3)


def test_motion_is_batch_padding_and_order_invariant(monitors):
    torch.manual_seed(11)
    reader = monitors.MotionReader(4).eval()
    short, long = torch.randn(1, 8, 4), torch.randn(9, 8, 4)
    assert reader.lstm.num_layers == 2
    assert reader.lstm.hidden_size == 128
    assert reader.lstm.bidirectional
    alone = reader([short])[0]
    torch.testing.assert_close(reader([long, short])[1], alone, atol=1e-6, rtol=1e-5)
    torch.testing.assert_close(reader([short, long])[0], alone, atol=1e-6, rtol=1e-5)
    assert alone.shape == (256,)


def test_location_streams_ignore_magnitude_prompt_and_earlier_answer(monitors):
    torch.manual_seed(11)
    model = monitors.ThreeReader(8, 4).train()
    x = torch.randn(70, 8, 4)
    model([x], [(2, 70)])  # Training-only codebook initialization.
    model.eval()
    changed = x.clone()
    changed[:6] = 10000
    scaled = x * torch.linspace(1, 10, 8)[None, :, None]
    for reader in (model.direction, model.region):
        first = reader([x], [(2, 70)])
        altered = reader([changed], [(2, 70)])
        rescaled = reader([scaled], [(2, 70)])
        if isinstance(first, tuple):
            first, altered, rescaled = first[0], altered[0], rescaled[0]
        torch.testing.assert_close(first, altered)
        torch.testing.assert_close(first, rescaled, atol=1e-6, rtol=1e-5)


def test_vq_is_hard_has_commitment_gradient_and_frozen_eval(monitors):
    torch.manual_seed(11)
    vq = monitors.EMACodebook(2, size=4, decay=0.5, dead_steps=2)
    assert not list(vq.parameters())
    with pytest.raises(RuntimeError, match="initializ"):
        vq.eval()(torch.zeros(1, 2))
    vq.train()
    vq(torch.tensor([[0.0, 0.0], [2.0, 2.0], [4.0, 4.0], [6.0, 6.0]]))
    vq.eval()
    before = copy.deepcopy(vq.state_dict())
    z = torch.tensor([[0.1, 0.2]], requires_grad=True)
    quantized, commitment = vq(z)
    assert torch.any(torch.all(quantized.detach() == vq.embedding, dim=1))
    assert commitment.item() > 0
    (quantized.sum() + commitment).backward()
    assert torch.isfinite(z.grad).all() and z.grad.abs().sum() > 0
    for key, value in before.items():
        torch.testing.assert_close(vq.state_dict()[key], value)


def test_vq_reseeds_unused_entries_from_training_only(monitors):
    vq = monitors.EMACodebook(2, size=4, decay=0.5, dead_steps=1).train()
    vq(torch.zeros(4, 2))
    vq(torch.full((1, 2), 9.0))
    assert torch.any(torch.all(vq.embedding == 9.0, dim=1))
    before = copy.deepcopy(vq.state_dict())
    vq.eval()(torch.full((1, 2), 999.0))
    for key, value in before.items():
        torch.testing.assert_close(vq.state_dict()[key], value)


def test_full_model_batch_invariance_and_state_roundtrip(monitors):
    torch.manual_seed(22)
    model = monitors.ThreeReader(8, 4)
    xs = [torch.randn(n, 8, 4) for n in (2, 7)]
    model(xs)
    model.eval()
    before = copy.deepcopy(model.state_dict())
    joint, _ = model(xs)
    for i, x in enumerate(xs):
        torch.testing.assert_close(model([x])[0][0], joint[i], atol=1e-6, rtol=1e-5)
    other = monitors.ThreeReader(8, 4).eval()
    other.load_state_dict(before)
    torch.testing.assert_close(other(xs)[0], joint)
    for key, value in before.items():
        torch.testing.assert_close(model.state_dict()[key], value)


@pytest.mark.parametrize(
    "problem", ["overlap", "test", "missing_split", "shape", "nan", "label", "span"]
)
def test_fit_rejects_invalid_data_before_creating_output(monitors, tmp_path, problem):
    train, val = records("train"), records("val", 2)
    if problem == "overlap":
        val[0]["task_id"] = train[0]["task_id"]
    elif problem == "test":
        val[0]["split"] = "test"
    elif problem == "missing_split":
        val[0].pop("split")
    elif problem == "shape":
        val[0]["activations"] = np.ones((2, 7, 4))
    elif problem == "nan":
        train[0]["activations"][0, 0, 0] = np.nan
    elif problem == "label":
        train[0]["label"] = 2
    else:
        train[0]["answer_start"] = 999
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError):
        monitors.fit_monitors(train, val, out, neural=False)
    assert not out.exists()


def test_baseline_fits_only_training_transforms_and_roundtrips(monitors, tmp_path):
    train, val = records("train"), records("unseenvocabulary", 2)
    train_copy = copy.deepcopy(train)
    names = monitors.fit_monitors(train, val, tmp_path, neural=False)
    assert set(names) == {"static_all_layers", "text", "likelihood", "sum_logp", "mean_logp"}
    for name in names:
        loaded = monitors.load_monitor(tmp_path / name)
        record = {k: v for k, v in val[0].items() if k not in ("label", "task_id")}
        score = loaded.score(record)
        assert isinstance(score, float) and np.isfinite(score)
        if name in ("sum_logp", "mean_logp"):
            assert score == val[0][name]
            assert loaded.metadata["score_kind"] == "raw_log_probability"
        else:
            assert 0 <= score <= 1
            assert loaded.metadata["selected_C"] in (0.01, 0.1, 1.0, 10.0)
        assert loaded.predict([record])[0] == pytest.approx(score)
        assert json.loads((tmp_path / name / "metadata.json").read_text())["name"] == name
    text_model = monitors.load_monitor(tmp_path / "text")
    assert "unseenvocabulary" not in text_model.features.vectorizer.vocabulary_
    np.testing.assert_allclose(
        text_model.features.scaler.mean_,
        np.mean([[len(r["text"]), len(r["text"].split()), r["sum_logp"], r["mean_logp"]]
                 for r in train], axis=0),
    )
    static = monitors.load_monitor(tmp_path / "static_all_layers")
    assert static.estimator.coef_.shape == (1, 32)
    for old, new in zip(train_copy, train):
        np.testing.assert_array_equal(old["activations"], new["activations"])
    with pytest.raises(FileExistsError):
        monitors.fit_monitors(train, val, tmp_path, neural=False)


def test_text_all_empty_training_vocabulary_is_supported(monitors, tmp_path):
    train, val = records("train"), records("val", 2)
    for r in train + val:
        r["text"] = ""
    monitors.fit_monitors(train, val, tmp_path, neural=False)
    assert np.isfinite(monitors.load_monitor(tmp_path / "text").score(val[0]))


def test_neural_training_persists_every_seed_and_restores_best(monitors, tmp_path):
    train, val = records("train", 4), records("val", 2)
    config = monitors.TrainingConfig(max_epochs=2, batch_size=2, accumulation_steps=1)
    names = monitors.fit_neural_monitors(train, val, tmp_path, config=config)
    assert set(names) == {f"{kind}_seed{seed}" for kind in ("motion", "three_reader")
                          for seed in (11, 22, 33)}
    for name in names:
        monitor = monitors.load_monitor(tmp_path / name)
        before = copy.deepcopy(monitor.model.state_dict())
        scores = monitor.predict(val)
        assert scores.shape == (2,)
        assert np.isfinite(scores).all() and np.all((scores >= 0) & (scores <= 1))
        history = monitor.metadata["history"]
        losses = [entry["val_logloss"] for entry in history]
        assert monitor.metadata["best_epoch"] == 1 + int(np.argmin(losses))
        from sklearn.metrics import log_loss

        assert log_loss([0, 1], scores, labels=[0, 1]) == pytest.approx(min(losses), abs=1e-6)
        for key, value in before.items():
            torch.testing.assert_close(monitor.model.state_dict()[key], value)
        assert monitor.score(val[0]) == pytest.approx(scores[0], abs=1e-6)
        assert monitor.metadata["answer_span_fallback_count"] == {"train": 4, "val": 2}


def test_early_stop_and_repeat_training_are_deterministic(monitors, tmp_path):
    train, val = records("train", 4), records("val", 2)
    config = monitors.TrainingConfig(max_epochs=10, min_delta=100, batch_size=2)
    names = monitors.fit_neural_monitors(train, val, tmp_path / "a", config=config,
                                         seeds=(11,), kinds=("three_reader",))
    monitors.fit_neural_monitors(train, val, tmp_path / "b", config=config,
                                seeds=(11,), kinds=("three_reader",))
    a = monitors.load_monitor(tmp_path / "a" / names[0])
    b = monitors.load_monitor(tmp_path / "b" / names[0])
    assert len(a.metadata["history"]) == 3
    assert a.metadata["best_epoch"] == 1
    np.testing.assert_array_equal(a.predict(val), b.predict(val))


def test_fit_default_includes_baselines_and_neural(monitors, tmp_path):
    names = monitors.fit_monitors(
        records("train", 4), records("val", 2), tmp_path,
        config=monitors.TrainingConfig(max_epochs=1, batch_size=2),
    )
    assert len(names) == 11


@pytest.mark.parametrize("kwargs", [{"max_epochs": 11}, {"patience": 0}, {"batch_size": 0}])
def test_training_config_enforces_bounded_training(monitors, kwargs):
    with pytest.raises(ValueError):
        monitors.TrainingConfig(**kwargs)
