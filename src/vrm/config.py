"""Strict loader for the frozen study configuration."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

from vrm.core import digest


_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_MD5 = re.compile(r"[0-9a-f]{32}\Z")
_TOP_LEVEL = {
    "study_id", "model_id", "model_revision", "tokenizer_revision", "dtype",
    "max_input_tokens", "max_new_tokens", "temperature", "top_p",
    "task_budget_s", "max_candidates", "gpu_budget_s", "smoke_gpu_budget_s",
    "benchmark", "verifier", "data", "monitor",
}
_FULL_SIZES = {"dev": 32, "train": 384, "val": 64, "id_test": 80, "ood_test": 40}
_REDUCED_SIZES = {"dev": 32, "train": 192, "val": 32, "id_test": 40, "ood_test": 20}


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate configuration key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"nonfinite JSON constant: {value}")


def _require_exact(value, expected, name):
    if value != expected:
        raise ValueError(f"{name} differs from the frozen protocol")


def _positive_number(value, name):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value <= 0):
        raise ValueError(f"{name} must be a positive finite number")


def load_study_config(path) -> dict:
    """Load and validate every study-defining pin before any outcome is opened."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"),
                         object_pairs_hook=_object, parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load study configuration: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != _TOP_LEVEL:
        raise ValueError("study configuration fields differ from the frozen schema")
    if not isinstance(raw["study_id"], str) or not raw["study_id"]:
        raise ValueError("study_id must be nonempty")
    _require_exact(raw["model_id"], "google/gemma-2-2b-it", "model_id")
    for name in ("model_revision", "tokenizer_revision"):
        if not isinstance(raw[name], str) or not _COMMIT.fullmatch(raw[name]):
            raise ValueError(f"{name} must be an immutable commit")
    _require_exact(raw["model_revision"], raw["tokenizer_revision"], "tokenizer_revision")
    for name, expected in {
        "dtype": "float16", "max_input_tokens": 512, "max_new_tokens": 64,
        "temperature": 0.7, "top_p": 0.95, "task_budget_s": 30.0,
        "max_candidates": 8, "gpu_budget_s": 43200, "smoke_gpu_budget_s": 3600,
    }.items():
        _require_exact(raw[name], expected, name)
    for name in ("temperature", "top_p", "task_budget_s", "gpu_budget_s",
                 "smoke_gpu_budget_s"):
        _positive_number(raw[name], name)

    benchmark = raw.get("benchmark")
    if not isinstance(benchmark, dict):
        raise ValueError("benchmark identity is missing")
    expected_benchmark = {
        "name": "LeanDojo Benchmark 4 v3",
        "doi": "10.5281/zenodo.18815372",
        "archive_md5": "b58af89599d5bbc792abc3744e5d37d9",
        "mathlib_repo": "https://github.com/leanprover-community/mathlib4",
        "mathlib_commit": "1bc7728a050fc18ca2683f614c531cd7050ff063",
        "leandojo_version": "4.20.0",
    }
    _require_exact(benchmark, expected_benchmark, "benchmark")
    if not _MD5.fullmatch(benchmark["archive_md5"]):
        raise ValueError("archive_md5 must be a lowercase MD5 digest")

    verifier = raw.get("verifier")
    expected_verifier = {
        "lean_version": "v4.29.0-rc2",
        "comparator_repo": "https://github.com/leanprover/comparator",
        "comparator_commit": "3090445149fbaba51d8177df4eb2121573788341",
        "landrun_repo": "https://github.com/Zouuup/landrun",
        "landrun_commit": "811cfff51ceaf3d9843708aa6d22e9b84ccac8b4",
        "lean4export_commit": "048394e1afeeb52b0fa27bcf3f1ade2ff0f0ab6d",
        "lean4checker_commit": "b7398199245524275543dec6113229c9bb4902e5",
        "allowed_axioms": ["propext", "Quot.sound", "Classical.choice"],
    }
    _require_exact(verifier, expected_verifier, "verifier")

    data = raw.get("data")
    expected_data = {
        "full_sizes": _FULL_SIZES,
        "reduced_sizes": _REDUCED_SIZES,
        "max_recorded_tactics": 6,
        "max_reference_tokens": 64,
    }
    _require_exact(data, expected_data, "data")
    monitor = raw.get("monitor")
    expected_monitor = {
        "seeds": [11, 22, 33],
        "regularization_C": [0.01, 0.1, 1.0, 10.0],
        "max_epochs": 10,
        "early_stopping_patience": 2,
    }
    _require_exact(monitor, expected_monitor, "monitor")

    result = dict(raw)
    result["config_sha256"] = digest(raw)
    return result
