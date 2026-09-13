import json
import hashlib
from pathlib import Path

import pytest

from vrm.config import load_study_config
from vrm.core import digest


def test_frozen_study_config_has_complete_machine_readable_identity():
    config = load_study_config("configs/study.json")
    assert config["model_id"] == "google/gemma-2-2b-it"
    assert config["model_revision"] == config["tokenizer_revision"]
    assert config["benchmark"]["archive_md5"] == "b58af89599d5bbc792abc3744e5d37d9"
    assert config["benchmark"]["mathlib_commit"] == "1bc7728a050fc18ca2683f614c531cd7050ff063"
    assert config["verifier"]["lean_version"] == "v4.29.0-rc1"
    assert config["verifier"]["comparator_repo"] == "https://github.com/leanprover/comparator"
    assert config["verifier"]["comparator_commit"] == "ae061f79cdf7af458a26348177cfbd62da0123f6"
    assert config["verifier"]["landrun_repo"] == "https://github.com/Zouuup/landrun"
    assert config["verifier"]["landrun_commit"] == "811cfff51ceaf3d9843708aa6d22e9b84ccac8b4"
    assert config["verifier"]["allowed_axioms"] == [
        "propext", "Quot.sound", "Classical.choice"]
    assert config["data"]["full_sizes"] == {
        "dev": 32, "train": 384, "val": 64, "id_test": 80, "ood_test": 40}
    assert config["monitor"]["seeds"] == [11, 22, 33]
    amendment = config["protocol_amendment"]
    assert amendment["id"] == "vrm-v1-runtime-provenance-2026-09-13"
    record = Path(amendment["record"])
    assert hashlib.sha256(record.read_bytes()).hexdigest() == amendment["record_sha256"]
    document = json.loads(record.read_text(encoding="utf-8"))
    assert document["status"] == "approved_pre_outcome"
    assert document["approval"]["statement"] == "Amendment genehmigt."
    blocker = Path(document["evidence"]["blocker_artifact"])
    assert hashlib.sha256(blocker.read_bytes()).hexdigest() == (
        document["evidence"]["blocker_artifact_sha256"]
    )
    assert document["evidence"]["prepared_manifest_sha256"] == (
        "9114e446a0050eded479289522211c8141a513b65990a3c5dfe6d59031d7482c"
    )
    assert config["config_sha256"] == digest({
        key: value for key, value in config.items() if key != "config_sha256"})


@pytest.mark.parametrize("mutation", [
    lambda c: c.pop("benchmark"),
    lambda c: c["benchmark"].__setitem__("archive_md5", "not-a-hash"),
    lambda c: c.__setitem__("model_revision", "main"),
    lambda c: c["verifier"].__setitem__("allowed_axioms", ["sorryAx"]),
    lambda c: c["data"]["full_sizes"].__setitem__("dev", 31),
    lambda c: c["monitor"].__setitem__("seeds", [11]),
    lambda c: c["protocol_amendment"].__setitem__("record_sha256", "0" * 64),
])
def test_invalid_or_incomplete_config_fails_closed(tmp_path, mutation):
    config = json.loads(open("configs/study.json", encoding="utf-8").read())
    mutation(config)
    path = tmp_path / "study.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError):
        load_study_config(path)


def test_nonfinite_or_unknown_config_values_are_rejected(tmp_path):
    config = json.loads(open("configs/study.json", encoding="utf-8").read())
    config["task_budget_s"] = float("nan")
    path = tmp_path / "study.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError):
        load_study_config(path)
