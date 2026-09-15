import hashlib
import json

import numpy as np
import pytest

from vrm import handoff
from vrm.config import load_study_config
from vrm.core import digest
from vrm.engine import candidate_seed
from test_workflow import tasks, Runner


CONFIG = load_study_config("configs/study.json")


def request():
    public, private = tasks()
    return handoff.development_request(public, private, CONFIG)


def candidate(req, index=0):
    task = req["tasks"][0]
    result = Runner().generate(task, candidate_seed(task["task_id"], index), 60)
    result["prompt_sha256"] = hashlib.sha256(task["prompt"].encode()).hexdigest()
    return result


def test_request_exports_only_public_development_data():
    req = request()
    assert len(req["tasks"]) == 32 and req["prospective_h3"] is False
    assert "reference_proof" not in json.dumps(req)
    public, private = tasks()
    public[0]["reference_proof"] = "secret"
    with pytest.raises(ValueError):
        handoff.development_request(public, private, CONFIG)


def test_duplicate_or_nondev_population_rejected():
    public, private = tasks()
    public[0] = public[1]
    with pytest.raises(ValueError):
        handoff.development_request(public, private, CONFIG)
    public, private = tasks()
    public[0]["split"] = "id_test"
    with pytest.raises(ValueError):
        handoff.development_request(public, private, CONFIG)


def test_roundtrip_is_idempotent_and_records_no_verdict(tmp_path):
    req = request()
    store = handoff.DevelopmentHandoff(tmp_path, req, expected_sha256=digest(req))
    c = candidate(req)
    task_id = req["tasks"][0]["task_id"]
    identity = Runner().identity
    store.write(task_id, 0, c, identity)
    store.write(task_id, 0, c, identity)
    result = store.read(task_id, 0)
    assert np.array_equal(c["activations"], result["activations"])
    assert result["text"] == c["text"]
    assert "verification" not in result and "status" not in result
    assert not store.manifest()["prospective_h3"]
    assert store.manifest()["completed_candidates"] == 1


def test_wrong_request_and_changed_prompt_rejected(tmp_path):
    req = request()
    wrong = json.loads(json.dumps(req))
    wrong["tasks"][0]["prompt"] += " changed"
    with pytest.raises(ValueError, match="hash"):
        handoff.DevelopmentHandoff(tmp_path, wrong, expected_sha256=digest(req))
    store = handoff.DevelopmentHandoff(tmp_path, req, expected_sha256=digest(req))
    c = candidate(req)
    c["prompt_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="prompt"):
        store.write(req["tasks"][0]["task_id"], 0, c, Runner().identity)


@pytest.mark.parametrize("change", ["seed", "revision", "index", "extra", "alignment", "nonfinite", "duration"])
def test_invalid_generation_rejected(tmp_path, change):
    req = request()
    store = handoff.DevelopmentHandoff(tmp_path, req, expected_sha256=digest(req))
    c = candidate(req)
    identity = Runner().identity
    index = 0
    if change == "seed": c["seed"] += 1
    if change == "revision": identity["model_revision"] = "f" * 40
    if change == "index": index = 4
    if change == "extra": c["HF_TOKEN"] = "never-export"
    if change == "alignment": c["output_ids"].append(3)
    if change == "nonfinite": c["activations"][0, 0, 0] = np.nan
    if change == "duration": c["elapsed_s"] = -1
    with pytest.raises(ValueError):
        store.write(req["tasks"][0]["task_id"], index, c, identity)
    assert not list(tmp_path.glob("*/receipt.json"))


def test_tampered_arrays_and_incomplete_record_rejected(tmp_path):
    req = request()
    store = handoff.DevelopmentHandoff(tmp_path, req, expected_sha256=digest(req))
    task_id = req["tasks"][0]["task_id"]
    store.write(task_id, 0, candidate(req), Runner().identity)
    path = next(tmp_path.glob("*/activations.npz"))
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        store.read(task_id, 0)
    path.unlink()
    with pytest.raises(ValueError, match="incomplete"):
        store.read(task_id, 0)


def test_previous_session_or_model_identity_cannot_mix_in_one_return(tmp_path):
    req = request()
    store = handoff.DevelopmentHandoff(tmp_path, req, expected_sha256=digest(req))
    task_id = req["tasks"][0]["task_id"]
    store.write(task_id, 0, candidate(req), Runner().identity)
    identity = {**Runner().identity, "gpu": "different-runtime"}
    with pytest.raises(ValueError, match="runtime"):
        store.write(task_id, 1, candidate(req, 1), identity)


def test_completed_record_cannot_be_overwritten(tmp_path):
    req = request()
    store = handoff.DevelopmentHandoff(tmp_path, req, expected_sha256=digest(req))
    task_id = req["tasks"][0]["task_id"]
    c = candidate(req)
    store.write(task_id, 0, c, Runner().identity)
    c["text"] += " changed"
    with pytest.raises(ValueError, match="immutable"):
        store.write(task_id, 0, c, Runner().identity)


def test_copied_record_under_unregistered_name_is_rejected(tmp_path):
    req = request()
    store = handoff.DevelopmentHandoff(tmp_path, req, expected_sha256=digest(req))
    (tmp_path / "duplicate-record").mkdir()
    with pytest.raises(ValueError, match="duplicate"):
        store.manifest()


def test_likelihood_summary_cannot_disagree_with_tokens(tmp_path):
    req = request()
    store = handoff.DevelopmentHandoff(tmp_path, req, expected_sha256=digest(req))
    c = candidate(req)
    c["sum_logp"] += 1
    with pytest.raises(ValueError, match="likelihood"):
        store.write(req["tasks"][0]["task_id"], 0, c, Runner().identity)


def test_handoff_cli_exports_and_inspects_without_model_or_verifier(tmp_path, monkeypatch, capsys):
    from vrm import cli
    public, private = tasks()
    (tmp_path / "dev.jsonl").write_text("\n".join(json.dumps(t) for t in public))
    rows = private + [{"split": "id_test", "reference_proof": "not for export"}]
    (tmp_path / "verifier_metadata.jsonl").write_text("\n".join(json.dumps(t) for t in rows))
    checked = []
    monkeypatch.setattr(cli, "validate_prepared_artifacts", lambda *a: checked.append(a))
    def forbidden(*args, **kwargs):
        pytest.fail("handoff export initialized model or verifier")
    monkeypatch.setattr(cli, "HFRunner", forbidden)
    monkeypatch.setattr(cli, "LeanDojoBackend", forbidden)
    destination = tmp_path / "request.json"
    assert cli.main(["prepare-handoff", "--prepared-dir", str(tmp_path), "--output", str(destination)]) == 0
    receipt = json.loads(capsys.readouterr().out)
    req = json.loads(destination.read_text())
    assert checked and req == request() and receipt["request_sha256"] == digest(req)
    assert cli.main(["inspect-handoff", "--request", str(destination),
                     "--request-sha256", receipt["request_sha256"],
                     "--returns", str(tmp_path / "returns")]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["completed_candidates"] == 0 and result["complete"] is False
