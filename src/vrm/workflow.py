"""Resumable orchestration for the development-only feasibility smoke."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np

from vrm.core import canonical, digest, feasibility
from vrm.engine import candidate_seed


_FORBIDDEN_PUBLIC = {"reference_proof", "initial_state", "label", "valid"}
_PRIVATE_WRAPPER_KEYS = {"task_id", "split", "content_sha256", "metadata"}
_JOINED_VERIFIER_KEYS = {
    "source_sha256", "trace_sha256", "start", "end", "proof_start",
    "proof_end", "theorem_statement",
}


def _write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".partial-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != content:
                raise ValueError(f"immutable artifact differs: {path.name}") from None
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_summary_atomic(path: Path, result: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if previous.get("status") == "completed" and previous != result:
            raise ValueError("completed summary is immutable")
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".partial-summary-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(canonical(result))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _metadata_digest(value: Mapping) -> str:
    content = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _identity(component, name: str) -> dict:
    value = getattr(component, "identity", None)
    if not isinstance(value, Mapping) or not value:
        raise ValueError(f"{name} must expose a nonempty identity mapping")
    # canonical() also rejects NaN and non-JSON identities.
    canonical(value)
    return dict(value)


def _validate_population(public_tasks: Sequence[Mapping], verifier_rows: Sequence[Mapping]):
    if len(public_tasks) != 32:
        raise ValueError("development smoke requires exactly 32 public tasks")
    task_ids = [str(row.get("task_id", "")) for row in public_tasks]
    if any(not task_id for task_id in task_ids) or len(set(task_ids)) != len(task_ids):
        raise ValueError("public development task IDs must be unique and nonempty")
    if any(row.get("split") != "dev" for row in public_tasks):
        raise ValueError("development smoke accepts only the dev split")
    if any(_FORBIDDEN_PUBLIC & set(row) for row in public_tasks):
        raise ValueError("public tasks cross the model information boundary")
    private_by_id = {}
    for row in verifier_rows:
        if set(row) != _PRIVATE_WRAPPER_KEYS or not isinstance(row.get("metadata"), Mapping):
            raise ValueError("invalid verifier metadata wrapper")
        task_id = str(row.get("task_id", ""))
        if not task_id or task_id in private_by_id:
            raise ValueError("verifier task IDs must be unique and nonempty")
        metadata = dict(row["metadata"])
        if row.get("split") != "dev" or metadata.get("split") != "dev":
            raise ValueError("development smoke accepts only dev verifier metadata")
        if metadata.get("task_id") != task_id:
            raise ValueError("verifier wrapper and metadata task IDs differ")
        if row.get("content_sha256") != _metadata_digest(metadata):
            raise ValueError("verifier metadata content hash mismatch")
        private_by_id[task_id] = metadata
    if set(task_ids) != set(private_by_id):
        raise ValueError("public and verifier task populations differ")
    population = []
    for task in public_tasks:
        metadata = private_by_id[str(task["task_id"])]
        for field in ("task_id", "split", "repo_url", "repo_commit", "file_path", "full_name"):
            if metadata.get(field) != task.get(field):
                raise ValueError(f"public and verifier metadata differ: {field}")
        population.append((dict(task), metadata))
    return population


def _joined_task(public: Mapping, metadata: Mapping, verifier_identity: Mapping) -> dict:
    benchmark_doi = verifier_identity.get("benchmark_doi")
    cache_sha256 = verifier_identity.get("cache_sha256")
    if not isinstance(benchmark_doi, str) or not benchmark_doi:
        raise ValueError("verifier identity lacks benchmark DOI")
    if (not isinstance(cache_sha256, str) or len(cache_sha256) != 64
            or any(character not in "0123456789abcdef" for character in cache_sha256)):
        raise ValueError("verifier identity lacks a valid cache digest")
    missing = _JOINED_VERIFIER_KEYS - set(metadata)
    if missing:
        raise ValueError(f"verifier metadata lacks required fields: {sorted(missing)}")
    verifier = {key: metadata[key] for key in _JOINED_VERIFIER_KEYS}
    verifier.update(benchmark_doi=benchmark_doi, cache_sha256=cache_sha256)
    return {**public, "verifier": verifier}


def _candidate_key(task_id: str, index: int) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", task_id):
        raise ValueError("task_id is not safe for an artifact path")
    return f"{task_id}-{index:03d}"


def _read_candidate(path: Path, expected_request: Mapping) -> dict | None:
    if not path.exists():
        return None
    receipt_path = path / "receipt.json"
    activation_path = path / "activations.npz"
    if not path.is_dir() or not receipt_path.is_file() or not activation_path.is_file():
        raise ValueError(f"incomplete completed candidate artifact: {path.name}")
    try:
        envelope = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid candidate receipt: {path.name}") from exc
    if envelope.get("request_sha256") != digest(expected_request):
        raise ValueError("candidate request mismatch; use a separate run directory")
    if envelope.get("request") != expected_request:
        raise ValueError("candidate request body mismatch")
    payload = envelope.get("payload")
    if not isinstance(payload, dict) or envelope.get("payload_sha256") != digest(payload):
        raise ValueError("candidate receipt checksum mismatch")
    if payload.get("activation_sha256") != _sha256_file(activation_path):
        raise ValueError("activation checksum mismatch")
    try:
        with np.load(activation_path, allow_pickle=False) as arrays:
            activations = arrays["activations"]
            boundary = arrays["prompt_boundary"]
    except (OSError, ValueError, KeyError) as exc:
        raise ValueError("invalid activation artifact") from exc
    if list(activations.shape) != payload.get("activation_shape"):
        raise ValueError("activation shape mismatch")
    if list(boundary.shape) != payload.get("prompt_boundary_shape"):
        raise ValueError("prompt-boundary shape mismatch")
    if str(activations.dtype) != payload.get("activation_dtype"):
        raise ValueError("activation dtype mismatch")
    if str(boundary.dtype) != payload.get("prompt_boundary_dtype"):
        raise ValueError("prompt-boundary dtype mismatch")
    if not np.isfinite(activations).all() or not np.isfinite(boundary).all():
        raise ValueError("nonfinite activation artifact")
    return payload


def _write_candidate(path: Path, request: Mapping, candidate: Mapping,
                     verification: Mapping) -> dict:
    try:
        activations = np.asarray(candidate["activations"])
        boundary = np.asarray(candidate["prompt_boundary"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("captured activations and prompt boundary are required") from exc
    if (activations.ndim != 3 or boundary.ndim != 2
            or activations.shape[1:] != boundary.shape
            or activations.dtype != np.float16 or boundary.dtype != np.float16
            or not np.isfinite(activations).all() or not np.isfinite(boundary).all()):
        raise ValueError("unexpected activation arrays")

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(dir=path.parent, prefix=".partial-candidate-"))
    try:
        activation_path = temporary / "activations.npz"
        np.savez_compressed(activation_path, activations=activations,
                            prompt_boundary=boundary)
        with activation_path.open("rb") as handle:
            os.fsync(handle.fileno())
        public_candidate = {
            key: value for key, value in candidate.items()
            if key not in {"activations", "prompt_boundary"}
        }
        canonical(public_candidate)
        status = verification.get("status")
        if status not in {"valid", "invalid", "timeout", "infrastructure_error"}:
            raise ValueError("unrecognized verifier status")
        generation_elapsed = float(candidate.get("elapsed_s", math.nan))
        verification_elapsed = float(verification.get("elapsed_s", math.nan))
        if (not math.isfinite(generation_elapsed) or generation_elapsed < 0
                or not math.isfinite(verification_elapsed) or verification_elapsed < 0):
            raise ValueError("candidate and verifier elapsed times must be finite and nonnegative")
        payload = {
            "task_id": request["task_id"],
            "candidate_index": request["candidate_index"],
            "candidate": public_candidate,
            "verification": dict(verification),
            "status": status,
            "charged_elapsed_s": generation_elapsed + verification_elapsed,
            "input_token_sha256": digest(candidate.get("input_ids")),
            "output_token_sha256": digest(candidate.get("output_ids")),
            "activation_sha256": _sha256_file(activation_path),
            "activation_shape": list(activations.shape),
            "activation_dtype": str(activations.dtype),
            "prompt_boundary_shape": list(boundary.shape),
            "prompt_boundary_dtype": str(boundary.dtype),
        }
        envelope = {
            "request": dict(request),
            "request_sha256": digest(request),
            "payload": payload,
            "payload_sha256": digest(payload),
        }
        receipt_path = temporary / "receipt.json"
        receipt_path.write_bytes(canonical(envelope))
        with receipt_path.open("rb") as handle:
            os.fsync(handle.fileno())
        try:
            os.rename(temporary, path)
        except OSError:
            if path.exists():
                existing = _read_candidate(path, request)
                if existing != payload:
                    raise ValueError("completed candidate artifact is immutable") from None
            else:
                raise
        return payload
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def run_development_smoke(public_tasks: Sequence[Mapping],
                          verifier_rows: Sequence[Mapping], runner, verifier,
                          output_dir, *, request: Mapping) -> dict:
    """Run or resume the registered 32-by-4 development feasibility smoke."""
    return _run_development_collection(
        public_tasks, verifier_rows, runner, verifier, output_dir,
        request=request, candidate_limit=None,
    )


def run_single_candidate_probe(public_tasks: Sequence[Mapping],
                               verifier_rows: Sequence[Mapping], runner, verifier,
                               output_dir, *, request: Mapping) -> dict:
    """Exercise one real end-to-end candidate without evaluating the smoke gate."""
    return _run_development_collection(
        public_tasks, verifier_rows, runner, verifier, output_dir,
        request=request, candidate_limit=1,
    )


def _run_development_collection(public_tasks: Sequence[Mapping],
                                verifier_rows: Sequence[Mapping], runner, verifier,
                                output_dir, *, request: Mapping,
                                candidate_limit: int | None) -> dict:
    population = _validate_population(public_tasks, verifier_rows)
    if not isinstance(request, Mapping):
        raise ValueError("smoke request must be a mapping")
    candidates_per_task = request.get("candidates_per_task")
    budget_s = request.get("smoke_gpu_budget_s")
    if candidates_per_task != 4 or isinstance(budget_s, bool):
        raise ValueError("registered smoke requires four candidates and a numeric budget")
    try:
        budget_s = float(budget_s)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid smoke budget") from exc
    if not math.isfinite(budget_s) or budget_s <= 0:
        raise ValueError("invalid smoke budget")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    runner_identity = _identity(runner, "runner")
    verifier_identity = _identity(verifier, "verifier")
    joined_population = [
        (public, private, _joined_task(public, private, verifier_identity))
        for public, private in population
    ]
    run_identity = {
        "request": dict(request),
        "runner": runner_identity,
        "verifier": verifier_identity,
        "public_population_sha256": digest([task for task, _ in population]),
        "verifier_population_sha256": digest([row for _, row in population]),
    }
    identity_path = output / "run_identity.json"
    if identity_path.exists():
        if json.loads(identity_path.read_text(encoding="utf-8")) != run_identity:
            raise ValueError("run request or runtime identity changed")
    else:
        _write_bytes_atomic(identity_path, canonical(run_identity))

    payloads = []
    charged = 0.0
    failed_attempts = 0
    for public, private, verification_task in joined_population:
        task_id = str(public["task_id"])
        for index in range(candidates_per_task):
            seed = candidate_seed(task_id, index)
            candidate_request = {
                "run_identity_sha256": digest(run_identity),
                "task_id": task_id,
                "task_sha256": digest(public),
                "verifier_metadata_sha256": digest(private),
                "candidate_index": index,
                "candidate_seed": seed,
            }
            path = output / "candidates" / _candidate_key(task_id, index)
            failed_dir = output / "failed_candidates" / _candidate_key(task_id, index)
            prior_failures = []
            if failed_dir.exists():
                for attempt_path in sorted(failed_dir.iterdir()):
                    failure = _read_candidate(attempt_path, candidate_request)
                    if failure is None or failure.get("status") != "infrastructure_error":
                        raise ValueError("invalid preserved infrastructure attempt")
                    prior_failures.append(failure)
                    charged += float(failure["charged_elapsed_s"])
                failed_attempts += len(prior_failures)
            existing = _read_candidate(path, candidate_request)
            if existing is not None:
                payloads.append(existing)
                charged += float(existing["charged_elapsed_s"])
                if candidate_limit is not None and len(payloads) >= candidate_limit:
                    return _finish_probe(output, "completed", payloads, charged,
                                         budget_s, failed_attempts)
                continue
            remaining = budget_s - charged
            if remaining <= 0:
                return _finish_collection(
                    output, "budget_exhausted", payloads, charged, budget_s,
                    failed_attempts, candidate_limit,
                )
            candidate = runner.generate(public, seed, remaining, capture=True)
            if not isinstance(candidate, Mapping):
                raise ValueError("runner returned no candidate mapping")
            generation_elapsed = float(candidate.get("elapsed_s", math.nan))
            if not math.isfinite(generation_elapsed) or generation_elapsed < 0:
                raise ValueError("candidate elapsed time must be finite and nonnegative")
            if candidate.get("deadline_exceeded"):
                return _finish_collection(
                    output, "budget_exhausted", payloads,
                    charged + generation_elapsed, budget_s, failed_attempts,
                    candidate_limit,
                )
            verification_remaining = budget_s - charged - generation_elapsed
            if verification_remaining <= 0:
                return _finish_collection(
                    output, "budget_exhausted", payloads,
                    charged + generation_elapsed, budget_s, failed_attempts,
                    candidate_limit,
                )
            verification = verifier.verify(
                verification_task, candidate.get("text", ""),
                timeout_s=min(5.0, verification_remaining),
            )
            if not isinstance(verification, Mapping):
                raise ValueError("verifier returned no result mapping")
            if verification.get("status") == "infrastructure_error":
                attempt_path = failed_dir / f"{len(prior_failures):03d}"
                failure = _write_candidate(
                    attempt_path, candidate_request, candidate, verification
                )
                charged += float(failure["charged_elapsed_s"])
                failed_attempts += 1
                return _finish_collection(
                    output, "infrastructure_error", payloads, charged, budget_s,
                    failed_attempts, candidate_limit,
                )
            payload = _write_candidate(path, candidate_request, candidate, verification)
            payloads.append(payload)
            charged += float(payload["charged_elapsed_s"])
            if candidate_limit is not None and len(payloads) >= candidate_limit:
                return _finish_probe(output, "completed", payloads, charged,
                                     budget_s, failed_attempts)

    return _finish(output, "completed", payloads, charged, budget_s, failed_attempts)


def _finish_collection(output: Path, status: str, payloads: Sequence[Mapping],
                       charged: float, budget_s: float, failed_attempts: int,
                       candidate_limit: int | None) -> dict:
    if candidate_limit is None:
        return _finish(output, status, payloads, charged, budget_s, failed_attempts)
    return _finish_probe(output, status, payloads, charged, budget_s, failed_attempts)


def _finish_probe(output: Path, status: str, payloads: Sequence[Mapping],
                  charged: float, budget_s: float, failed_attempts: int = 0) -> dict:
    if status == "completed":
        status = "integration_probe_completed"
    result = _summary(status, payloads, charged, budget_s, failed_attempts)
    result["scientific_gate_evaluated"] = False
    _write_summary_atomic(output / "integration_probe.json", result)
    return result


def _finish(output: Path, status: str, payloads: Sequence[Mapping],
            charged: float, budget_s: float, failed_attempts: int = 0) -> dict:
    result = _summary(status, payloads, charged, budget_s, failed_attempts)
    _write_summary_atomic(output / "summary.json", result)
    return result


def _summary(status: str, payloads: Sequence[Mapping], charged: float,
             budget_s: float, failed_attempts: int = 0) -> dict:
    rows = []
    if status == "completed":
        for payload in payloads:
            rows.append({
                "task_id": payload["task_id"],
                "split": "dev",
                "status": payload["status"],
            })
    result = {
        "status": status,
        "completed_candidates": len(payloads),
        "failed_attempts": failed_attempts,
        "charged_elapsed_s": charged,
        "budget_s": budget_s,
        "feasibility": None,
    }
    if status == "completed":
        result["feasibility"] = feasibility(rows)
    return result
