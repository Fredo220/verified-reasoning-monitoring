"""Public-only development packets and immutable generation returns.

This file transport is for offline development, not prospective H3 timing.
Hashes detect drift/corruption; they do not authenticate an untrusted producer.
"""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np

from vrm.core import canonical, digest
from vrm.engine import candidate_seed
from vrm.workflow import _candidate_key, _sha256_file, _validate_population, _write_bytes_atomic


_TASK_FIELDS = {"task_id", "group_id", "split", "repo_url", "repo_commit", "file_path", "full_name", "prompt"}
_CANDIDATE_FIELDS = {
    "text", "input_ids", "output_ids", "prompt_sha256", "sum_logp", "mean_logp", "token_logps",
    "generation_s", "extraction_s", "elapsed_s", "deadline_exceeded", "seed", "answer_start", "answer_end",
}
_RUNTIME_FIELDS = {"python", "platform", "packages", "cuda", "gpu", "model_id", "model_revision",
                   "tokenizer_revision", "dtype", "device", "chat_template_sha256", "n_layers"}
_PINS = ("model_id", "model_revision", "tokenizer_revision", "dtype")


def development_request(public_tasks, verifier_rows, config):
    population = _validate_population(public_tasks, verifier_rows)
    tasks = [public for public, _ in population]
    if any(set(task) != _TASK_FIELDS for task in tasks):
        raise ValueError("public task fields differ from the model-visible schema")
    return {"schema": "vrm-dev-generation-v1", "prospective_h3": False,
            "config_sha256": config["config_sha256"], "tasks": tasks,
            "model": {key: config[key] for key in _PINS},
            "max_input_tokens": config["max_input_tokens"],
            "max_new_tokens": config["max_new_tokens"], "candidates_per_task": 4}


class DevelopmentHandoff:
    def __init__(self, root, request, *, expected_sha256):
        if digest(request) != expected_sha256:
            raise ValueError("handoff request hash mismatch")
        if request.get("schema") != "vrm-dev-generation-v1" or request.get("prospective_h3") is not False:
            raise ValueError("only the offline development handoff is supported")
        tasks = request.get("tasks", [])
        if (len(tasks) != 32 or any(set(task) != _TASK_FIELDS or task["split"] != "dev" for task in tasks)
                or len({task["task_id"] for task in tasks}) != 32
                or request.get("candidates_per_task") != 4):
            raise ValueError("handoff must preserve the complete development population")
        self.root = Path(root)
        self.request = request
        self.request_sha256 = expected_sha256
        self.tasks = {task["task_id"]: task for task in tasks}
        for task_id in self.tasks:
            _candidate_key(task_id, 0)

    def _path(self, task_id, index):
        if task_id not in self.tasks or type(index) is not int or not 0 <= index < 4:
            raise ValueError("candidate index or task outside registered development population")
        return self.root / _candidate_key(task_id, index)

    def _validate(self, task_id, index, candidate, runtime):
        self._path(task_id, index)
        if set(candidate) != _CANDIDATE_FIELDS | {"activations", "prompt_boundary"}:
            raise ValueError("candidate contains missing or unregistered fields")
        if not set(runtime) <= _RUNTIME_FIELDS or any(runtime.get(key) != self.request["model"][key] for key in _PINS):
            raise ValueError("runtime identity does not match the pinned model")
        if runtime.get("device") != "cuda":
            raise ValueError("registered generation requires CUDA")
        if candidate["seed"] != candidate_seed(task_id, index):
            raise ValueError("candidate seed mismatch")
        if candidate["prompt_sha256"] != hashlib.sha256(self.tasks[task_id]["prompt"].encode()).hexdigest():
            raise ValueError("candidate prompt hash mismatch")
        for key, limit in (("input_ids", self.request["max_input_tokens"]),
                           ("output_ids", self.request["max_new_tokens"])):
            ids = candidate[key]
            if not isinstance(ids, list) or not 0 < len(ids) <= limit or any(type(i) is not int or i < 0 for i in ids):
                raise ValueError("invalid token IDs or token count")
        n_tokens = len(candidate["output_ids"])
        if (candidate["answer_start"] != 0 or candidate["answer_end"] != n_tokens
                or len(candidate["token_logps"]) != n_tokens):
            raise ValueError("candidate token alignment mismatch")
        if any(not isinstance(p, (int, float)) or not math.isfinite(p) or p > 1e-6 for p in candidate["token_logps"]):
            raise ValueError("invalid token log probabilities")
        total = sum(candidate["token_logps"])
        if not math.isclose(candidate["sum_logp"], total, abs_tol=1e-6) or not math.isclose(candidate["mean_logp"], total / n_tokens, abs_tol=1e-6):
            raise ValueError("token likelihood summaries disagree")
        for name in ("generation_s", "extraction_s", "elapsed_s"):
            value = candidate[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("invalid generation duration")
        if candidate["elapsed_s"] + 1e-6 < candidate["generation_s"] + candidate["extraction_s"]:
            raise ValueError("generation duration omits extraction cost")
        if candidate["deadline_exceeded"] is not False:
            raise ValueError("incomplete or over-budget generation cannot be returned as complete")
        if not isinstance(candidate["text"], str):
            raise ValueError("candidate text must be a string")
        acts, boundary = np.asarray(candidate["activations"]), np.asarray(candidate["prompt_boundary"])
        if (acts.ndim != 3 or acts.shape[0] != n_tokens or boundary.ndim != 2
                or acts.shape[1:] != boundary.shape or min(boundary.shape) <= 0
                or acts.dtype != np.float16 or boundary.dtype != np.float16
                or not np.isfinite(acts).all() or not np.isfinite(boundary).all()):
            raise ValueError("activation dtype, alignment, or values invalid")
        if "n_layers" in runtime and acts.shape[1] != runtime["n_layers"]:
            raise ValueError("activation layer count differs from runtime")
        public_candidate = {key: candidate[key] for key in _CANDIDATE_FIELDS}
        canonical(public_candidate)
        canonical(runtime)
        return public_candidate

    def write(self, task_id, index, candidate, runtime):
        public = self._validate(task_id, index, candidate, runtime)
        self.root.mkdir(parents=True, exist_ok=True)
        identity = {"request_sha256": self.request_sha256, "runtime": runtime}
        identity_path = self.root / "identity.json"
        if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
            raise ValueError("handoff runtime or request changed")
        _write_bytes_atomic(identity_path, canonical(identity))
        path = self._path(task_id, index)
        if path.exists():
            existing = self.read(task_id, index)
            same = all(existing[k] == public[k] for k in _CANDIDATE_FIELDS)
            same &= all(np.array_equal(existing[k], candidate[k]) for k in ("activations", "prompt_boundary"))
            if not same:
                raise ValueError("completed generation is immutable")
            return
        temporary = Path(tempfile.mkdtemp(dir=self.root, prefix=".partial-"))
        try:
            buffer = io.BytesIO()
            np.savez_compressed(buffer, activations=candidate["activations"], prompt_boundary=candidate["prompt_boundary"])
            _write_bytes_atomic(temporary / "activations.npz", buffer.getvalue())
            payload = {"task_id": task_id, "candidate_index": index, "candidate": public,
                       "runtime": runtime, "activation_sha256": _sha256_file(temporary / "activations.npz")}
            envelope = {"request_sha256": self.request_sha256, "payload": payload, "payload_sha256": digest(payload)}
            _write_bytes_atomic(temporary / "receipt.json", canonical(envelope))
            os.rename(temporary, path)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)

    def read(self, task_id, index):
        path = self._path(task_id, index)
        if not path.exists():
            return None
        if path.is_symlink() or not all((path / name).is_file() and not (path / name).is_symlink()
                                        for name in ("receipt.json", "activations.npz")):
            raise ValueError("incomplete or linked generation artifact")
        envelope = json.loads((path / "receipt.json").read_text())
        payload = envelope["payload"]
        if envelope.get("request_sha256") != self.request_sha256 or envelope.get("payload_sha256") != digest(payload):
            raise ValueError("generation receipt checksum or request mismatch")
        if payload.get("task_id") != task_id or payload.get("candidate_index") != index:
            raise ValueError("generation receipt task/index mismatch")
        identity = json.loads((self.root / "identity.json").read_text())
        if identity != {"request_sha256": self.request_sha256, "runtime": payload["runtime"]}:
            raise ValueError("handoff runtime identity mismatch")
        if _sha256_file(path / "activations.npz") != payload.get("activation_sha256"):
            raise ValueError("activation checksum mismatch")
        with np.load(path / "activations.npz", allow_pickle=False) as arrays:
            candidate = {**payload["candidate"], "activations": arrays["activations"], "prompt_boundary": arrays["prompt_boundary"]}
        self._validate(task_id, index, candidate, payload["runtime"])
        return candidate

    def manifest(self):
        expected = {_candidate_key(t, i) for t in self.tasks for i in range(4)}
        if self.root.exists():
            extras = {p.name for p in self.root.iterdir() if not p.name.startswith(".partial-") and p.name != "identity.json"} - expected
            if extras:
                raise ValueError("unregistered or duplicate generation artifacts")
        count = sum(self.read(t, i) is not None for t in self.tasks for i in range(4))
        return {"request_sha256": self.request_sha256, "completed_candidates": count,
                "expected_candidates": 128, "complete": count == 128,
                "prospective_h3": False, "verification_performed": False,
                "transfer_and_gpu_allocation_accounting": "required_separately"}
