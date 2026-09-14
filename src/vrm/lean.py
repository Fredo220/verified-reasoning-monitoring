"""Fail-closed Lean verification using pinned Comparator inside Linux isolation.

The host process never imports Lean or evaluates a candidate.  The container is
networkless and read-only; Comparator performs every candidate build under
Landrun, checks statement identity and permitted axioms, and replays the result
through the Lean kernel.  A LeanDojo ``ProofFinished`` observation is not part
of this protocol and cannot grant validity.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import selectors
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
from urllib.parse import urlsplit
import uuid


BENCHMARK_DOI = "10.5281/zenodo.18815372"
MATHLIB_REPO_URL = "https://github.com/leanprover-community/mathlib4"
MATHLIB_COMMIT = "1bc7728a050fc18ca2683f614c531cd7050ff063"
LEAN_DOJO_VERSION = "4.20.0"
LEAN_DOJO_COMMIT = "3bbc4c02fb8a058b282c8d3982a02d6563f3b08a"
LEAN_VERSION = "v4.29.0-rc1"
COMPARATOR_COMMIT = "ae061f79cdf7af458a26348177cfbd62da0123f6"
COMPARATOR_REPO_URL = "https://github.com/leanprover/comparator"
COMPARATOR_PATCH_SHA256 = (
    "02382151f52b32c7d66bb355974bc218cd73644f1557be11853b78499a8bee03"
)
LANDRUN_REPO_URL = "https://github.com/Zouuup/landrun"
LANDRUN_COMMIT = "811cfff51ceaf3d9843708aa6d22e9b84ccac8b4"
SECCOMP_PROFILE_SOURCE_URL = (
    "https://github.com/moby/profiles/blob/seccomp/v0.2.1/seccomp/default.json"
)
SECCOMP_PROFILE_SOURCE_SHA256 = (
    "536529b665dd0972c37bfb569f5d4ac8a53592e7b00752bc39ff063ca9864c74"
)
SECCOMP_PROFILE_SHA256 = (
    "85ea2ee4cfc4f957232ea300ee87890d4a56f44aeeb4a4ecd177e3eb778c5c1e"
)
LEAN4EXPORT_COMMIT = "048394e1afeeb52b0fa27bcf3f1ade2ff0f0ab6d"
LEAN4CHECKER_COMMIT = "b7398199245524275543dec6113229c9bb4902e5"
ALLOWED_AXIOMS = ("propext", "Quot.sound", "Classical.choice")

_PUBLIC_TASK_KEYS = ("task_id", "repo_url", "repo_commit", "file_path", "full_name")
_VERIFIER_KEYS = (
    "benchmark_doi",
    "source_sha256",
    "trace_sha256",
    "cache_sha256",
    "start",
    "end",
    "proof_start",
    "proof_end",
    "theorem_statement",
)
_MAX_PROOF_BYTES = 64 * 1024
_MAX_OUTPUT_BYTES = 1024 * 1024
_PREFLIGHT_TIMEOUT_S = 180.0
_WORKER_SETUP_GRACE_S = 600.0
_COMPARATOR_ROOT = Path("/opt/vrm/comparator")
_COMPARATOR_BIN = _COMPARATOR_ROOT / ".lake/build/bin/comparator"
_LEAN4EXPORT_BIN = (
    _COMPARATOR_ROOT / ".lake/packages/lean4export/.lake/build/bin/lean4export"
)
_CACHE_ROOT = Path("/cache")


def _is_hex(value: object, size: int) -> bool:
    return isinstance(value, str) and len(value) == size and all(
        character in "0123456789abcdef" for character in value
    )


def _docker_image_digest(image: object) -> str:
    if not isinstance(image, str):
        raise ValueError("Docker verifier image must be pinned by digest")
    digest = image.rsplit("@", 1)[-1]
    if not digest.startswith("sha256:") or not _is_hex(digest[7:], 64):
        raise ValueError("Docker verifier image must be pinned by digest")
    return digest


def _is_repo_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    parts = parsed.path.split("/")
    return (
        parsed.scheme == "https"
        and parsed.netloc == "github.com"
        and not parsed.query
        and not parsed.fragment
        and len(parts) == 3
        and not value.endswith(".git")
        and all(
            part
            and part not in (".", "..")
            and all(c.isascii() and (c.isalnum() or c in "-_.") for c in part)
            for part in parts[1:]
        )
    )


def public_task(task: dict) -> dict:
    """Return the model-visible portion of a joined verifier task."""
    if not isinstance(task, dict):
        raise ValueError("task must be a dict")
    return {key: task[key] for key in _PUBLIC_TASK_KEYS}


def _position(value: object, field: str) -> tuple[int, int]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 2
        or any(isinstance(part, bool) or not isinstance(part, int) or part < 1 for part in value)
    ):
        raise ValueError(f"invalid verifier source position: {field}")
    return value[0], value[1]


def _validated_task(task: dict) -> dict:
    if not isinstance(task, dict):
        raise ValueError("task must be a dict")
    for key in _PUBLIC_TASK_KEYS:
        value = task.get(key)
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > 2048
            or "\x00" in value
        ):
            raise ValueError(f"missing or invalid task field: {key}")
    if task["repo_url"] != MATHLIB_REPO_URL or task["repo_commit"] != MATHLIB_COMMIT:
        raise ValueError("task does not match the frozen Benchmark 4 mathlib pin")
    path = PurePosixPath(task["file_path"])
    if (
        path.is_absolute()
        or ".." in path.parts
        or "\\" in str(path)
        or str(path) != task["file_path"]
        or path.suffix != ".lean"
    ):
        raise ValueError("file_path must be a normalized relative POSIX .lean path")

    verifier = task.get("verifier")
    if not isinstance(verifier, dict):
        raise ValueError("joined task requires verifier-only metadata")
    if verifier.get("benchmark_doi") != BENCHMARK_DOI:
        raise ValueError("verifier benchmark DOI does not match the frozen release")
    for key in ("source_sha256", "trace_sha256", "cache_sha256"):
        if not _is_hex(verifier.get(key), 64):
            raise ValueError(f"missing or invalid verifier field: {key}")
    for key in ("start", "end", "proof_start", "proof_end"):
        _position(verifier.get(key), key)
    if (
        not isinstance(verifier.get("theorem_statement"), str)
        or not verifier["theorem_statement"].strip()
    ):
        raise ValueError("missing or invalid verifier field: theorem_statement")
    return {
        **{key: task[key] for key in _PUBLIC_TASK_KEYS},
        "verifier": {key: verifier[key] for key in _VERIFIER_KEYS},
    }


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("infrastructure wall-clock deadline exceeded")
    return remaining


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cache_digest(root: str | Path) -> str:
    """Hash every non-Git cache path, mode, symlink target, and file byte."""
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("cache root is not a directory")
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        metadata = path.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        label = relative.as_posix().encode("utf-8")
        if stat.S_ISLNK(metadata.st_mode):
            target = path.resolve(strict=False)
            if not target.is_relative_to(root):
                raise ValueError(f"symlink escapes cache root: {relative}")
            if not target.exists():
                raise ValueError(f"dangling symlink in cache: {relative}")
            digest.update(b"L\0" + label + b"\0" + os.readlink(path).encode("utf-8") + b"\0")
        elif stat.S_ISDIR(metadata.st_mode):
            digest.update(b"D\0" + label + b"\0" + str(mode).encode("ascii") + b"\0")
        elif stat.S_ISREG(metadata.st_mode):
            digest.update(b"F\0" + label + b"\0" + str(mode).encode("ascii") + b"\0")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            digest.update(b"\0")
        else:
            raise ValueError(f"unsupported special file in cache: {relative}")
    return digest.hexdigest()


def trace_digest(ast_path: str | Path) -> str:
    """Bind a LeanDojo AST to the dependency-path file consumed with it."""
    ast_path = Path(ast_path)
    if ast_path.suffixes[-2:] != [".ast", ".json"]:
        raise ValueError("trace path must end in .ast.json")
    dep_path = ast_path.with_suffix("").with_suffix(".dep_paths")
    digest = hashlib.sha256()
    for label, path in ((b"ast", ast_path), (b"dep_paths", dep_path)):
        digest.update(label + b"\0")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def _source_offset(source: str, position: tuple[int, int]) -> int:
    line_number, column_number = position
    lines = source.splitlines(keepends=True)
    if line_number == len(lines) + 1 and column_number == 1 and source.endswith("\n"):
        return len(source)
    if line_number < 1 or line_number > len(lines) or column_number < 1:
        raise ValueError("invalid Lean source position")
    line = lines[line_number - 1]
    content = line[:-1] if line.endswith("\n") else line
    if column_number > len(content) + 1:
        raise ValueError("invalid Lean source column")
    return sum(len(item) for item in lines[: line_number - 1]) + column_number - 1


def _source_variants(
    source: str,
    proof_start: tuple[int, int],
    proof_end: tuple[int, int],
    proof: str,
) -> tuple[str, str]:
    """Replace exactly the verifier-located proof span, without text screening."""
    start = _source_offset(source, proof_start)
    end = _source_offset(source, proof_end)
    if end <= start:
        raise ValueError("invalid proof span")
    _complete_proof_body(proof)
    complete = proof.rstrip("\n")
    prefix, suffix = source[:start], source[end:]
    terminal_newline = "\n" if source[start:end].endswith("\n") else ""
    return (
        prefix + "by\n  sorry" + terminal_newline + suffix,
        prefix + complete + terminal_newline + suffix,
    )


def _complete_proof_body(proof: str) -> str:
    """Validate the public output framing and remove its one leading ``by`` token."""
    error = "candidate must be one complete proof beginning with by"
    if (
        not isinstance(proof, str)
        or len(proof) < 4
        or not proof.startswith("by")
        or proof[2] not in (" ", "\t", "\n")
        or "\x00" in proof
        or "\r" in proof
    ):
        raise ValueError(error)
    body = proof[3:]
    if not body.strip():
        raise ValueError(error)
    return body


def _reconstruct_sources(task: dict, source: str, proof: str) -> tuple[str, str, str]:
    """Revalidate source/declaration/proof boundaries and construct judge inputs."""
    task = _validated_task(task)
    verifier = task["verifier"]
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != verifier["source_sha256"]:
        raise ValueError("target source digest mismatch")
    declaration_start = _position(verifier["start"], "start")
    declaration_end = _position(verifier["end"], "end")
    proof_start = _position(verifier["proof_start"], "proof_start")
    proof_end = _position(verifier["proof_end"], "proof_end")
    if proof_end != declaration_end:
        raise ValueError("proof end does not match declaration end")
    declaration_start_offset = _source_offset(source, declaration_start)
    declaration_end_offset = _source_offset(source, declaration_end)
    proof_start_offset = _source_offset(source, proof_start)
    proof_end_offset = _source_offset(source, proof_end)
    if not (
        declaration_start_offset < proof_start_offset < proof_end_offset
        and proof_end_offset == declaration_end_offset
    ):
        raise ValueError("invalid theorem declaration/proof boundary")
    recovered_statement = source[declaration_start_offset:proof_start_offset].rstrip()
    if recovered_statement != verifier["theorem_statement"]:
        raise ValueError("theorem statement boundary mismatch")
    _complete_proof_body(source[proof_start_offset:proof_end_offset])
    challenge, solution = _source_variants(source, proof_start, proof_end, proof)
    return challenge, solution, source


def _comparator_config(full_name: str) -> dict:
    return {
        "challenge_module": "Challenge",
        "solution_module": "Solution",
        "theorem_names": [full_name],
        "permitted_axioms": list(ALLOWED_AXIOMS),
        "enable_nanoda": False,
    }


class LeanDojoBackend:
    """Pinned Mathlib source and Comparator, using native Linux or Docker."""

    def __init__(
        self,
        *,
        execution_mode: str | None = None,
        image: str | None = None,
        cache_dir: str | Path | None = None,
        cache_sha256: str | None = None,
        landrun_sha256: str | None = None,
        comparator_root: str | Path | None = None,
        repo_url: str | None = None,
        repo_commit: str | None = None,
    ) -> None:
        self.execution_mode = (
            execution_mode
            if execution_mode is not None
            else os.environ.get("VRM_LEAN_EXECUTION_MODE", "native")
        )
        self.image = image if image is not None else os.environ.get("VRM_LEAN_IMAGE", "")
        cache = cache_dir if cache_dir is not None else os.environ.get("VRM_LEAN_CACHE", "")
        self.cache_dir = Path(cache).expanduser().absolute() if cache else None
        self.cache_sha256 = (
            cache_sha256
            if cache_sha256 is not None
            else os.environ.get("VRM_LEAN_CACHE_SHA256", "")
        )
        self.landrun_sha256 = (
            landrun_sha256
            if landrun_sha256 is not None
            else os.environ.get("VRM_LANDRUN_SHA256", "")
        )
        comparator = (
            comparator_root
            if comparator_root is not None
            else os.environ.get("VRM_COMPARATOR_ROOT", str(_COMPARATOR_ROOT))
        )
        self.comparator_root = Path(comparator).expanduser().absolute()
        configured_url = repo_url or os.environ.get("VRM_LEAN_REPO_URL") or MATHLIB_REPO_URL
        configured_commit = (
            repo_commit or os.environ.get("VRM_LEAN_REPO_COMMIT") or MATHLIB_COMMIT
        )
        self.repo_url = configured_url
        self.repo_commit = configured_commit
        self._preflight_ready = False
        self._tool_hashes = {"comparator": "", "lean4export": ""}
        self._container_platform = ""

    def _probe_receipt(self) -> dict:
        return {
            "trusted_judge": "Comparator",
            "execution_mode": self.execution_mode,
            "benchmark_doi": BENCHMARK_DOI,
            "repo_url": MATHLIB_REPO_URL,
            "repo_commit": MATHLIB_COMMIT,
            "lean_dojo_version": LEAN_DOJO_VERSION,
            "lean_dojo_commit": LEAN_DOJO_COMMIT,
            "lean_version": LEAN_VERSION,
            "comparator_commit": COMPARATOR_COMMIT,
            "comparator_repo_url": COMPARATOR_REPO_URL,
            "comparator_patch_sha256": COMPARATOR_PATCH_SHA256,
            "landrun_repo_url": LANDRUN_REPO_URL,
            "landrun_commit": LANDRUN_COMMIT,
            "lean4export_commit": LEAN4EXPORT_COMMIT,
            "lean4checker_commit": LEAN4CHECKER_COMMIT,
            "cache_sha256": self.cache_sha256,
            "landrun_sha256": self.landrun_sha256,
            "container_image_digest": (
                _docker_image_digest(self.image) if self.execution_mode == "docker" else None
            ),
            "container_platform": (
                self._container_platform if self.execution_mode == "docker" else None
            ),
            "seccomp_profile_sha256": (
                SECCOMP_PROFILE_SHA256 if self.execution_mode == "docker" else None
            ),
            "comparator_binary_sha256": self._tool_hashes["comparator"],
            "lean4export_binary_sha256": self._tool_hashes["lean4export"],
            "allowed_axioms": list(ALLOWED_AXIOMS),
            "landrun_enforced": True,
            "kernel_replay": True,
            "cache_validation_policy": (
                "full_digest_preflight_and_post_run; per_candidate_source_digest"
            ),
        }

    @property
    def identity(self) -> dict:
        if not self._preflight_ready:
            raise RuntimeError("verifier identity requires a successful preflight")
        return self._probe_receipt()

    def _audit_receipt(self, task: dict) -> dict:
        task = _validated_task(task)
        return {
            **self._probe_receipt(),
            "task_id": task["task_id"],
            "file_path": task["file_path"],
            "full_name": task["full_name"],
            "source_sha256": task["verifier"]["source_sha256"],
            "trace_sha256": task["verifier"]["trace_sha256"],
        }

    def preflight(self) -> dict:
        """Probe the actual source, pins, Landrun isolation, and judge."""
        started = time.monotonic()
        self._preflight_ready = False
        try:
            result = self._runtime_preflight(started + _PREFLIGHT_TIMEOUT_S)
            if not isinstance(result, dict):
                raise ValueError("malformed runtime preflight")
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as exc:
            result = {
                "runtime_ready": False,
                "audit_ready": False,
                "reasons": ["runtime_probe_failed"],
                "checks": {},
                "error": str(exc)[:2048],
            }
        result.setdefault("checks", {})
        result.setdefault("reasons", [])
        result["ready"] = bool(result.get("runtime_ready") and result.get("audit_ready"))
        result["status"] = "ready" if result["ready"] else "infrastructure_error"
        self._preflight_ready = result["ready"]
        result["allowed_axioms"] = list(ALLOWED_AXIOMS)
        result["elapsed_s"] = time.monotonic() - started
        return result

    def verify(self, task: dict, proof: str, timeout_s: float) -> dict:
        """Verify one complete, unfenced proof beginning with ``by``."""
        started = time.monotonic()
        status = "infrastructure_error"
        details: dict = {
            "proof_audit": "not_completed",
            "allowed_axioms": list(ALLOWED_AXIOMS),
        }
        try:
            task = _validated_task(task)
            if (self.repo_url, self.repo_commit) != (MATHLIB_REPO_URL, MATHLIB_COMMIT):
                raise ValueError("backend repository configuration differs from frozen pins")
            if task["verifier"]["cache_sha256"] != self.cache_sha256:
                raise ValueError("task verifier cache digest differs from backend cache pin")
            if (
                isinstance(timeout_s, bool)
                or not isinstance(timeout_s, (float, int))
                or not math.isfinite(timeout_s)
                or timeout_s <= 0
            ):
                raise ValueError("timeout_s must be a positive finite number")
            if not isinstance(proof, str) or len(proof.encode("utf-8")) > _MAX_PROOF_BYTES:
                raise ValueError("proof must be at most 65536 bytes")
            _complete_proof_body(proof)

            readiness = None if self._preflight_ready else self.preflight()
            if readiness is not None and not readiness["ready"]:
                details["reasons"] = list(readiness.get("reasons", ["preflight_not_ready"]))
                details["runtime"] = readiness
            else:
                request = {
                    "op": "verify",
                    "task": task,
                    "proof": proof,
                    "candidate_timeout_s": float(timeout_s),
                }
                response = self._request(
                    request, time.monotonic() + float(timeout_s) + _WORKER_SETUP_GRACE_S
                )
                if not isinstance(response, dict) or not isinstance(response.get("kind"), str):
                    raise ValueError("malformed worker response")
                details["observation"] = response
                kind = response["kind"]
                if kind == "valid":
                    if response.get("audit") != self._audit_receipt(task):
                        raise ValueError("worker returned a missing or mismatched audit receipt")
                    status = "valid"
                    details["proof_audit"] = "comparator"
                elif kind == "invalid":
                    status = "invalid"
                    details["proof_audit"] = "comparator_rejected"
                elif kind == "timeout" and response.get("phase", "candidate") == "candidate":
                    status = "timeout"
                    details["proof_audit"] = "candidate_deadline"
                elif kind != "infrastructure_error":
                    details["reasons"] = ["unrecognized_worker_result"]
        except (TimeoutError, subprocess.TimeoutExpired) as exc:
            details["error"] = str(exc)[:2048]
            details["reasons"] = ["infrastructure_deadline"]
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            details["error"] = str(exc)[:2048]
        return {"status": status, "elapsed_s": time.monotonic() - started, "details": details}

    def _runtime_preflight(self, deadline: float) -> dict:
        if self.execution_mode == "native":
            return self._native_preflight(deadline)
        if self.execution_mode != "docker":
            return {
                "runtime_ready": False,
                "audit_ready": False,
                "reasons": ["invalid_execution_mode"],
                "checks": {},
            }
        return self._docker_preflight(deadline)

    def _docker_preflight(self, deadline: float) -> dict:
        reasons: list[str] = []
        checks: dict[str, bool] = {}
        if not shutil.which("docker"):
            reasons.append("docker_cli_missing")
        try:
            _docker_image_digest(self.image)
        except ValueError:
            reasons.append("pinned_image_missing")
        if self.cache_dir is None or not self.cache_dir.is_dir():
            reasons.append("cache_missing")
        elif any(character in str(self.cache_dir) for character in (",", "\n", "\x00")):
            reasons.append("invalid_cache_path")
        if not _is_hex(self.cache_sha256, 64):
            reasons.append("cache_digest_pin_missing")
        if not _is_hex(self.landrun_sha256, 64):
            reasons.append("landrun_digest_pin_missing")
        if (self.repo_url, self.repo_commit) != (MATHLIB_REPO_URL, MATHLIB_COMMIT):
            reasons.append("repository_pin_mismatch")
        try:
            _seccomp_profile_path()
        except (OSError, ValueError, RuntimeError):
            reasons.append("seccomp_profile_invalid")

        result = {
            "runtime_ready": False,
            "audit_ready": False,
            "reasons": reasons,
            "checks": checks,
        }
        if "docker_cli_missing" in reasons:
            return result
        info = subprocess.run(
            ["docker", "info", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=_remaining(deadline),
        )
        if info.returncode:
            reasons.append("docker_daemon_unavailable")
            result["error"] = info.stderr[-2048:]
            return result
        daemon = json.loads(info.stdout)
        checks["linux_daemon"] = daemon.get("OSType") == "linux"
        checks["resource_limits"] = all(
            daemon.get(key) is True
            for key in ("MemoryLimit", "SwapLimit", "PidsLimit", "CpuCfsQuota")
        )
        checks["seccomp_available"] = any(
            "seccomp" in option for option in (daemon.get("SecurityOptions") or [])
        )
        reasons.extend(f"{key}_unavailable" for key, passed in checks.items() if not passed)
        if reasons:
            return result

        inspect = subprocess.run(
            ["docker", "image", "inspect", self.image],
            capture_output=True,
            text=True,
            timeout=_remaining(deadline),
        )
        if inspect.returncode:
            reasons.append("pinned_image_not_local")
            return result
        image_metadata = json.loads(inspect.stdout)
        metadata = image_metadata[0] if isinstance(image_metadata, list) and len(image_metadata) == 1 else {}
        if (
            not isinstance(image_metadata, list)
            or len(image_metadata) != 1
            or metadata.get("Os") != "linux"
            or metadata.get("Architecture") not in {"amd64", "arm64"}
            or metadata.get("Config", {}).get("Volumes")
        ):
            reasons.append("image_requires_supported_linux_and_no_declared_volumes")
            return result
        self._container_platform = f"linux/{metadata['Architecture']}"

        observation = self._request({"op": "probe"}, deadline)
        result["observation"] = observation
        audit = observation.get("audit", {}) if isinstance(observation, dict) else {}
        if _is_hex(audit.get("comparator_binary_sha256"), 64) and _is_hex(
            audit.get("lean4export_binary_sha256"), 64
        ):
            self._tool_hashes = {
                "comparator": audit["comparator_binary_sha256"],
                "lean4export": audit["lean4export_binary_sha256"],
            }
        if (
            not isinstance(observation, dict)
            or observation.get("kind") != "probe_ok"
            or observation.get("audit") != self._probe_receipt()
        ):
            error = observation.get("error", "") if isinstance(observation, dict) else ""
            reasons.append(
                "cache_digest_mismatch"
                if isinstance(error, str) and error.endswith("cache_digest_mismatch")
                else "isolated_audit_probe_failed"
            )
            return result
        checks.update(
            {
                "sandbox": True,
                "seccomp_no_connect": True,
                "cache": True,
                "source_provenance": True,
                "toolchain": True,
                "landrun": True,
                "proof_audit": True,
            }
        )
        result["runtime_ready"] = True
        result["audit_ready"] = True
        return result

    def _native_preflight(self, deadline: float) -> dict:
        reasons: list[str] = []
        checks: dict[str, bool] = {}
        if sys.platform != "linux":
            reasons.append("native_linux_required")
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            reasons.append("native_non_root_required")
        if self.cache_dir is None or not self.cache_dir.is_dir():
            reasons.append("cache_missing")
        if not _is_hex(self.cache_sha256, 64):
            reasons.append("cache_digest_pin_missing")
        if not _is_hex(self.landrun_sha256, 64):
            reasons.append("landrun_digest_pin_missing")
        if not self.comparator_root.is_dir():
            reasons.append("comparator_source_missing")
        if (self.repo_url, self.repo_commit) != (MATHLIB_REPO_URL, MATHLIB_COMMIT):
            reasons.append("repository_pin_mismatch")
        result = {
            "runtime_ready": False,
            "audit_ready": False,
            "reasons": reasons,
            "checks": checks,
        }
        if reasons:
            return result
        assert self.cache_dir is not None
        with tempfile.TemporaryDirectory(prefix="vrm-landrun-probe-") as directory:
            _check_landrun(self.landrun_sha256, Path(directory))
        _check_cache_root(self.cache_dir, self.cache_sha256, full_digest=True)
        self._tool_hashes = _check_comparator_source(self.comparator_root)
        _check_lean_version(self.cache_dir, _remaining(deadline))
        checks.update(
            {
                "native_linux": True,
                "non_root": True,
                "cache": True,
                "source_provenance": True,
                "toolchain": True,
                "landrun_filesystem": True,
                "landrun_network": True,
                "proof_audit": True,
            }
        )
        result["observation"] = {"kind": "probe_ok", "audit": self._probe_receipt()}
        result["runtime_ready"] = True
        result["audit_ready"] = True
        return result

    def _command(self, name: str) -> list[str]:
        seccomp_profile = _seccomp_profile_path()
        return [
            "docker",
            "run",
            "--rm",
            "--pull=never",
            "--name",
            name,
            "--interactive",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges=true",
            "--security-opt",
            f"seccomp={seccomp_profile}",
            "--user=65534:65534",
            "--ipc=none",
            "--cgroupns=private",
            "--pids-limit=128",
            "--memory=4g",
            "--memory-swap=4g",
            "--cpus=1",
            "--ulimit=nofile=256:256",
            "--ulimit=core=0:0",
            "--log-driver=none",
            "--tmpfs=/work:rw,nosuid,nodev,size=3g,mode=1777",
            "--tmpfs=/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777",
            "--mount",
            f"type=bind,src={self.cache_dir},dst=/cache,readonly",
            "--workdir=/work",
            "--env=HOME=/work",
            "--env=TMPDIR=/tmp",
            "--env=PATH=" + str(_LEAN4EXPORT_BIN.parent) + ":/usr/local/bin:/usr/bin:/bin",
            "--env=DISABLE_REMOTE_CACHE=1",
            "--env=PYTHONDONTWRITEBYTECODE=1",
            "--env=GITHUB_ACCESS_TOKEN=",
            "--env=GIT_CONFIG_NOSYSTEM=1",
            "--entrypoint=python",
            self.image,
            "-I",
            "-B",
            "-c",
            Path(__file__).read_text(encoding="utf-8"),
        ]

    def _request(self, request: dict, deadline: float) -> dict:
        request = {
            **request,
            "execution_mode": self.execution_mode,
            "repo_url": MATHLIB_REPO_URL,
            "repo_commit": MATHLIB_COMMIT,
            "cache_sha256": self.cache_sha256,
            "landrun_sha256": self.landrun_sha256,
            "image_digest": (
                _docker_image_digest(self.image) if self.execution_mode == "docker" else None
            ),
            "container_platform": (
                self._container_platform if self.execution_mode == "docker" else None
            ),
        }
        if self.execution_mode == "native":
            if request.get("op") != "verify":
                raise ValueError("native transport only accepts verify after preflight")
            assert self.cache_dir is not None
            with tempfile.TemporaryDirectory(prefix="vrm-lean-") as directory:
                return _execute_verification(
                    request,
                    self.cache_dir,
                    self.comparator_root,
                    Path(directory),
                )
        name = "vrm-" + uuid.uuid4().hex
        process: subprocess.Popen | None = None
        cleanup_error: RuntimeError | None = None
        try:
            with tempfile.TemporaryFile() as input_file, selectors.DefaultSelector() as selector:
                input_file.write(json.dumps(request).encode("utf-8"))
                input_file.seek(0)
                process = subprocess.Popen(
                    self._command(name),
                    stdin=input_file,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                assert process.stdout is not None and process.stderr is not None
                selector.register(process.stdout, selectors.EVENT_READ)
                selector.register(process.stderr, selectors.EVENT_READ)
                output, errors = bytearray(), bytearray()
                while selector.get_map():
                    for key, _ in selector.select(min(0.1, _remaining(deadline))):
                        chunk = os.read(key.fileobj.fileno(), 8192)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        (output if key.fileobj is process.stdout else errors).extend(chunk)
                        if len(output) + len(errors) > _MAX_OUTPUT_BYTES:
                            raise RuntimeError("worker output limit exceeded")
                process.wait(timeout=_remaining(deadline))
                if process.returncode:
                    message = errors[-2048:].decode("utf-8", "replace")
                    raise RuntimeError(f"worker exited {process.returncode}: {message}")
                return json.loads(output)
        finally:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.wait()
                if process.stdout is not None:
                    process.stdout.close()
                if process.stderr is not None:
                    process.stderr.close()
                cleanup = subprocess.run(
                    ["docker", "rm", "-f", name], capture_output=True, text=True, timeout=10
                )
                if cleanup.returncode and "No such container" not in cleanup.stderr:
                    cleanup_error = RuntimeError(
                        "worker cleanup unconfirmed: " + cleanup.stderr[-1024:]
                    )
            if cleanup_error is not None and sys.exc_info()[0] is None:
                raise cleanup_error


def preflight() -> dict:
    """Run the environment-configured backend preflight."""
    return LeanDojoBackend().preflight()


def verify(task: dict, proof: str, timeout_s: float) -> dict:
    """Run the environment-configured backend; Lean never executes on the host."""
    return LeanDojoBackend().verify(task, proof, timeout_s)


def _sandbox_check() -> None:
    """Verify outer Docker controls before importing LeanDojo."""
    status_fields = dict(
        line.split(":", 1)
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines()
        if ":" in line
    )
    if (
        os.getuid() == 0
        or status_fields.get("NoNewPrivs", "").strip() != "1"
        or status_fields.get("Seccomp", "").strip() != "2"
        or int(status_fields.get("CapEff", "1").strip(), 16) != 0
    ):
        raise RuntimeError(
            "sandbox requires non-root, no-new-privileges, seccomp, and zero capabilities"
        )
    if {path.name for path in Path("/sys/class/net").iterdir()} != {"lo"}:
        raise RuntimeError("sandbox has a non-loopback network interface")

    mounts = {
        fields[1]: (fields[2], fields[3].split(","))
        for line in Path("/proc/mounts").read_text(encoding="utf-8").splitlines()
        if len(fields := line.split()) >= 4
    }
    if "/" not in mounts or "ro" not in mounts["/"][1]:
        raise RuntimeError("sandbox root filesystem is not read-only")
    if "/cache" not in mounts or "ro" not in mounts["/cache"][1]:
        raise RuntimeError("pinned cache is not read-only")
    if mounts.get("/work", (None,))[0] != "tmpfs":
        raise RuntimeError("work area is not disposable tmpfs")

    cgroup = Path("/sys/fs/cgroup")
    for filename in ("memory.max", "pids.max"):
        value = (cgroup / filename).read_text(encoding="utf-8").strip()
        if not value.isdigit() or int(value) <= 0:
            raise RuntimeError(f"sandbox requires finite cgroup v2 {filename}")
    cpu = (cgroup / "cpu.max").read_text(encoding="utf-8").split()
    if not cpu[0].isdigit() or int(cpu[0]) <= 0:
        raise RuntimeError("sandbox requires a finite CPU quota")
    if (cgroup / "memory.swap.max").read_text(encoding="utf-8").strip() != "0":
        raise RuntimeError("sandbox must disable swap")


def _safe_repo_metadata(root: Path, *arguments: str, timeout: float = 30.0) -> str:
    return subprocess.run(
        ["git", "-c", f"safe.directory={root}", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=True,
        timeout=timeout,
    ).stdout.strip()


def _normalize_origin(origin: str) -> str:
    return origin.removesuffix(".git").rstrip("/")


def _check_clean_repo(root: Path, expected_url: str, expected_commit: str) -> dict:
    if _safe_repo_metadata(root, "rev-parse", "HEAD") != expected_commit:
        raise RuntimeError(f"repository HEAD mismatch: {root}")
    if _normalize_origin(_safe_repo_metadata(root, "config", "--get", "remote.origin.url")) != expected_url:
        raise RuntimeError(f"repository origin mismatch: {root}")
    if _safe_repo_metadata(root, "status", "--porcelain=v1", "--untracked-files=no"):
        raise RuntimeError(f"repository has modified tracked content: {root}")
    return {
        "head": expected_commit,
        "tree": _safe_repo_metadata(root, "rev-parse", "HEAD^{tree}"),
    }


def _check_cache_root(root: Path, expected_sha256: str, *, full_digest: bool) -> dict:
    repository = _check_clean_repo(root, MATHLIB_REPO_URL, MATHLIB_COMMIT)
    toolchain = (root / "lean-toolchain").read_text(encoding="utf-8").strip()
    if toolchain != "leanprover/lean4:" + LEAN_VERSION:
        raise RuntimeError("mathlib Lean toolchain mismatch")
    if full_digest and cache_digest(root) != expected_sha256:
        raise RuntimeError("cache_digest_mismatch")
    return repository


def _check_lean_version(root: Path, timeout_s: float) -> None:
    # Elan reads lean-toolchain here without asking Lake to materialize packages.
    result = subprocess.run(
        ["lean", "--version"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_s,
    )
    if result.returncode:
        raise RuntimeError(f"Lean version probe failed: {result.stderr[-2048:]}")
    version = result.stdout
    if f"version {LEAN_VERSION.removeprefix('v')}" not in version:
        raise RuntimeError("runtime Lean version mismatch")


def _check_comparator_source(root: Path | None = None) -> dict[str, str]:
    root = _COMPARATOR_ROOT if root is None else root
    _check_clean_repo(
        root,
        COMPARATOR_REPO_URL,
        COMPARATOR_COMMIT,
    )
    patch = root / ".vrm-comparator-landrun-separator.patch"
    if _sha256_file(patch) != COMPARATOR_PATCH_SHA256:
        raise RuntimeError("Comparator compatibility patch digest mismatch")
    if (root / "lean-toolchain").read_text(encoding="utf-8").strip() != (
        "leanprover/lean4:" + LEAN_VERSION
    ):
        raise RuntimeError("Comparator Lean toolchain mismatch")
    manifest = json.loads((root / "lake-manifest.json").read_text(encoding="utf-8"))
    packages = {package["name"]: package["rev"] for package in manifest.get("packages", [])}
    if packages.get("lean4export") != LEAN4EXPORT_COMMIT:
        raise RuntimeError("Comparator lean4export manifest pin mismatch")
    if packages.get("Lean4Checker") != LEAN4CHECKER_COMMIT:
        raise RuntimeError("Comparator lean4checker manifest pin mismatch")
    comparator = root / ".lake/build/bin/comparator"
    lean4export = root / ".lake/packages/lean4export/.lake/build/bin/lean4export"
    if not comparator.is_file() or not os.access(comparator, os.X_OK):
        raise RuntimeError("Comparator executable is missing")
    if not lean4export.is_file() or not os.access(lean4export, os.X_OK):
        raise RuntimeError("lean4export executable is missing")
    return {
        "comparator": _sha256_file(comparator),
        "lean4export": _sha256_file(lean4export),
    }


def _check_leandojo_install() -> None:
    from importlib.metadata import distribution

    installed = distribution("lean-dojo")
    direct_url = json.loads(installed.read_text("direct_url.json") or "{}")
    if installed.version != LEAN_DOJO_VERSION:
        raise RuntimeError("LeanDojo version mismatch")
    if direct_url.get("vcs_info", {}).get("commit_id") != LEAN_DOJO_COMMIT:
        raise RuntimeError("LeanDojo installation is not pinned to the audited commit")


def _landrun_command(landrun: Path, writable_root: Path, command: list[str]) -> list[str]:
    """Confine a subprocess to one writable tree and grant no network access."""
    return [
        str(landrun),
        # Older kernels may lack only a newer Landlock operation. Preflight still
        # fails closed unless the concrete write, TCP, and Unix-socket probes pass.
        "--best-effort",
        "--ro",
        "/",
        "--rw",
        "/dev",
        "--rwx",
        str(writable_root),
        "--env",
        f"HOME={writable_root}",
        "--env",
        f"TMPDIR={writable_root}",
        "--env",
        "PATH",
        "--env",
        "ELAN_HOME",
        "--env",
        "DISABLE_REMOTE_CACHE=1",
        "--env",
        "GITHUB_ACCESS_TOKEN=",
        "--ldd",
        "--add-exec",
        "--",
        *command,
    ]


def _seccomp_profile_path() -> Path:
    """Return the packaged Moby profile after checking its exact hardened form."""
    profile = Path(__file__).with_name("seccomp-no-connect-v0.2.1.json")
    if _sha256_file(profile) != SECCOMP_PROFILE_SHA256:
        raise RuntimeError("Docker seccomp profile digest mismatch")
    document = json.loads(profile.read_text(encoding="utf-8"))
    if document.get("defaultAction") != "SCMP_ACT_ERRNO":
        raise RuntimeError("Docker seccomp profile must fail closed")
    allowed = {
        name
        for group in document.get("syscalls", [])
        if group.get("action") == "SCMP_ACT_ALLOW"
        for name in group.get("names", [])
    }
    if {"connect", "socketcall"} & allowed:
        raise RuntimeError("Docker seccomp profile permits outbound connect")
    return profile.resolve(strict=True)


def _native_comparator_command(comparator: Path, config_path: Path) -> list[str]:
    return ["lake", "-Kjobs=1", "env", str(comparator), str(config_path)]


def _connection_probe_command(family: str, endpoint: str) -> list[str]:
    if family == "tcp":
        program = (
            "import socket,sys; "
            "socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect("
            "('127.0.0.1', int(sys.argv[1])))"
        )
    elif family == "unix":
        program = (
            "import socket,sys; "
            "socket.socket(socket.AF_UNIX, socket.SOCK_STREAM).connect(sys.argv[1])"
        )
    else:
        raise ValueError("unknown connection probe family")
    return [sys.executable, "-c", program, endpoint]


def _check_landrun(expected_sha256: str, work_root: Path | None = None) -> Path:
    executable_name = shutil.which("landrun")
    if executable_name is None:
        raise RuntimeError("Landrun executable is missing")
    executable = Path(executable_name).resolve(strict=True)
    if _sha256_file(executable) != expected_sha256:
        raise RuntimeError("Landrun executable digest mismatch")

    root = Path("/work") if work_root is None else work_root
    root.mkdir(parents=True, exist_ok=True)
    allowed = root / "allowed"
    denied = root.parent / (root.name + "-denied")
    if denied.exists():
        raise RuntimeError("Landrun denial probe path already exists")
    allowed.mkdir(exist_ok=False)
    base = _landrun_command(executable, root, [])
    positive = subprocess.run(
        base + ["/bin/sh", "-c", f"printf ok > {allowed / 'probe'}"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if positive.returncode or not (allowed / "probe").is_file():
        raise RuntimeError(f"Landrun positive confinement probe failed: {positive.stderr[-2048:]}")
    negative = subprocess.run(
        base + ["/bin/sh", "-c", f"printf escaped > {denied}"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if negative.returncode == 0 or denied.exists():
        raise RuntimeError("Landrun did not deny a write outside its writable allowlist")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        network = subprocess.run(
            base + _connection_probe_command("tcp", str(port)),
            capture_output=True,
            text=True,
            timeout=5,
        )
    if network.returncode == 0:
        raise RuntimeError("Landrun TCP isolation probe failed")

    unix_path = root / "vrm-landrun-probe.sock"
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(unix_path))
            server.listen(1)
            network = subprocess.run(
                base + _connection_probe_command("unix", str(unix_path)),
                capture_output=True,
                text=True,
                timeout=5,
            )
        if network.returncode == 0:
            raise RuntimeError("Landrun Unix-socket isolation probe failed")
    finally:
        unix_path.unlink(missing_ok=True)
    return executable


def _check_cache(request: dict, *, full_digest: bool) -> dict:
    source = _CACHE_ROOT
    if full_digest and cache_digest(source) != request["cache_sha256"]:
        raise RuntimeError("cache_digest_mismatch")
    repository = _check_clean_repo(source, MATHLIB_REPO_URL, MATHLIB_COMMIT)
    toolchain = (source / "lean-toolchain").read_text(encoding="utf-8").strip()
    if toolchain != "leanprover/lean4:" + LEAN_VERSION:
        raise RuntimeError("mathlib Lean toolchain mismatch")
    _check_lean_version(source, 30)
    return repository


def _assert_worker_request(request: dict) -> None:
    if request.get("repo_url") != MATHLIB_REPO_URL or request.get("repo_commit") != MATHLIB_COMMIT:
        raise ValueError("worker repository pin mismatch")
    if not _is_hex(request.get("cache_sha256"), 64):
        raise ValueError("worker cache digest pin missing")
    if not _is_hex(request.get("landrun_sha256"), 64):
        raise ValueError("worker Landrun digest pin missing")
    if request.get("execution_mode") == "docker":
        image_digest = request.get("image_digest")
        if (
            not isinstance(image_digest, str)
            or not image_digest.startswith("sha256:")
            or not _is_hex(image_digest[7:], 64)
        ):
            raise ValueError("worker Docker image digest pin missing")
        if request.get("container_platform") not in {"linux/amd64", "linux/arm64"}:
            raise ValueError("worker Docker platform pin missing")


def _worker_backend(request: dict, tool_hashes: dict[str, str]) -> LeanDojoBackend:
    backend = LeanDojoBackend(
        execution_mode="docker",
        image="worker@" + request["image_digest"],
        cache_sha256=request["cache_sha256"],
        landrun_sha256=request["landrun_sha256"],
    )
    backend._tool_hashes = dict(tool_hashes)
    backend._container_platform = request["container_platform"]
    return backend


def _worker_probe(request: dict) -> dict:
    _sandbox_check()
    _assert_worker_request(request)
    _check_cache(request, full_digest=True)
    _check_leandojo_install()
    tool_hashes = _check_comparator_source()
    _check_landrun(request["landrun_sha256"])
    receipt = _worker_backend(request, tool_hashes)._probe_receipt()
    return {"kind": "probe_ok", "audit": receipt}


def _target_sources(task: dict, proof: str) -> tuple[str, str, str]:
    source_path = _CACHE_ROOT / PurePosixPath(task["file_path"])
    if not source_path.is_file() or not source_path.resolve().is_relative_to(_CACHE_ROOT):
        raise RuntimeError("target source is absent from the pinned cache")
    if _sha256_file(source_path) != task["verifier"]["source_sha256"]:
        raise RuntimeError("target source digest mismatch")

    source = source_path.read_text(encoding="utf-8")
    return _reconstruct_sources(task, source, proof)


def _stage_dependency_view(source: Path, destination: Path) -> None:
    """Copy mutable Lake config while linking immutable source and build data."""
    source = source.resolve(strict=True)
    destination.mkdir(parents=True, exist_ok=False)
    for child in source.iterdir():
        if child.name in {".git", ".lake"}:
            continue
        (destination / child.name).symlink_to(
            child, target_is_directory=child.is_dir()
        )

    source_lake = source / ".lake"
    if not source_lake.is_dir():
        return
    destination_lake = destination / ".lake"
    destination_lake.mkdir()
    for child in source_lake.iterdir():
        if child.name == "config":
            shutil.copytree(child, destination_lake / child.name, symlinks=True)
        elif child.name != "packages":
            (destination_lake / child.name).symlink_to(
                child, target_is_directory=child.is_dir()
            )


def _write_audit_project(
    root: Path,
    challenge: str,
    solution: str,
    full_name: str,
    *,
    cache_root: Path = _CACHE_ROOT,
) -> Path:
    cache_root = cache_root.resolve(strict=True)
    source_manifest = json.loads(
        (cache_root / "lake-manifest.json").read_text(encoding="utf-8")
    )
    packages_dir = source_manifest.get("packagesDir")
    packages = source_manifest.get("packages")
    if not isinstance(packages_dir, str) or not isinstance(packages, list):
        raise RuntimeError("pinned Mathlib Lake manifest is malformed")
    package_base = (cache_root / PurePosixPath(packages_dir)).resolve(strict=True)
    if not package_base.is_relative_to(cache_root):
        raise RuntimeError("pinned Mathlib package directory escapes cache root")

    root.mkdir(parents=True, exist_ok=False)
    dependency_root = root / ".vrm-deps"
    dependency_root.mkdir()
    mathlib_view = dependency_root / "mathlib"
    _stage_dependency_view(cache_root, mathlib_view)

    audit_packages = [{
        "type": "path",
        "scope": "",
        "name": "mathlib",
        "manifestFile": "lake-manifest.json",
        "inherited": False,
        "dir": str(mathlib_view),
        "configFile": "lakefile.lean",
    }]
    for package in packages:
        if not isinstance(package, dict):
            raise RuntimeError("pinned Mathlib package entry is malformed")
        name = package.get("name")
        manifest_file = package.get("manifestFile")
        config_file = package.get("configFile")
        if not all(isinstance(value, str) and value for value in (
            name, manifest_file, config_file
        )):
            raise RuntimeError("pinned Mathlib package identity is malformed")
        package_root = (package_base / name).resolve(strict=True)
        if not package_root.is_dir() or not package_root.is_relative_to(cache_root):
            raise RuntimeError("pinned Mathlib package escapes cache root")
        package_view = dependency_root / name
        _stage_dependency_view(package_root, package_view)
        audit_packages.append({
            "type": "path",
            "scope": package.get("scope") or "",
            "name": name,
            "manifestFile": manifest_file,
            "inherited": True,
            "dir": str(package_view),
            "configFile": config_file,
        })
    (root / "lean-toolchain").write_text("leanprover/lean4:" + LEAN_VERSION + "\n")
    (root / "lakefile.toml").write_text(
        'name = "VRMAudit"\n'
        'version = "0.0.0"\n\n'
        f'[[require]]\nname = "mathlib"\npath = "{mathlib_view}"\n\n'
        '[[lean_lib]]\nname = "Challenge"\n\n'
        '[[lean_lib]]\nname = "Solution"\n'
    )
    (root / "Challenge.lean").write_text(challenge, encoding="utf-8")
    (root / "Solution.lean").write_text(solution, encoding="utf-8")
    (root / "lake-manifest.json").write_text(
        json.dumps(
            {
                "version": source_manifest.get("version", "1.1.0"),
                "packagesDir": ".lake/packages",
                "packages": audit_packages,
                "name": "VRMAudit",
                "lakeDir": ".lake",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    config_path = root / "comparator.json"
    config_path.write_text(json.dumps(_comparator_config(full_name)), encoding="utf-8")
    return config_path


def _run_comparator(
    root: Path,
    config_path: Path,
    timeout_s: float,
    *,
    comparator: Path = _COMPARATOR_BIN,
    landrun: Path | None = None,
    lean4export: Path | None = None,
) -> tuple[bool, str]:
    process_env = {**os.environ, "GITHUB_ACCESS_TOKEN": ""}
    if landrun is not None:
        if lean4export is None:
            raise ValueError("native Comparator requires the pinned lean4export executable")
        lean4export = lean4export.resolve(strict=True)
        if not lean4export.is_file() or not os.access(lean4export, os.X_OK):
            raise RuntimeError("lean4export executable is missing")
        existing_path = process_env.get("PATH", "")
        process_env["PATH"] = str(lean4export.parent) + (
            os.pathsep + existing_path if existing_path else ""
        )
    command = _native_comparator_command(comparator, config_path)
    if landrun is not None:
        command = _landrun_command(landrun, root, command)
    process = subprocess.Popen(
        command,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
        env=process_env,
    )
    try:
        output, _ = process.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        output, _ = process.communicate()
        return False, "__VRM_CANDIDATE_TIMEOUT__\n" + output[-8192:]
    return process.returncode == 0, output[-8192:]


def _execute_verification(
    request: dict,
    cache_root: Path,
    comparator_root: Path,
    work_root: Path,
) -> dict:
    """Run the native-Linux Comparator path after a successful preflight."""
    _assert_worker_request(request)
    task = _validated_task(request.get("task"))
    if task["verifier"]["cache_sha256"] != request["cache_sha256"]:
        raise RuntimeError("task/cache digest mismatch")
    proof = request.get("proof")
    timeout_s = request.get("candidate_timeout_s")
    if (
        not isinstance(proof, str)
        or len(proof.encode("utf-8")) > _MAX_PROOF_BYTES
        or isinstance(timeout_s, bool)
        or not isinstance(timeout_s, (int, float))
        or not math.isfinite(timeout_s)
        or timeout_s <= 0
    ):
        raise ValueError("invalid proof or candidate timeout")
    _complete_proof_body(proof)
    _check_cache_root(cache_root, request["cache_sha256"], full_digest=False)
    tool_hashes = _check_comparator_source(comparator_root)
    landrun_name = shutil.which("landrun")
    if landrun_name is None:
        raise RuntimeError("Landrun executable is missing")
    landrun = Path(landrun_name).resolve(strict=True)
    if _sha256_file(landrun) != request["landrun_sha256"]:
        raise RuntimeError("Landrun executable digest mismatch")

    source_path = cache_root / PurePosixPath(task["file_path"])
    if not source_path.is_file() or not source_path.resolve().is_relative_to(cache_root.resolve()):
        raise RuntimeError("target source is absent from the pinned cache")
    source = source_path.read_text(encoding="utf-8")
    challenge, solution, original = _reconstruct_sources(task, source, proof)
    comparator = comparator_root / ".lake/build/bin/comparator"
    lean4export = (
        comparator_root / ".lake/packages/lean4export/.lake/build/bin/lean4export"
    )

    candidate_root = work_root / "candidate"
    config_path = _write_audit_project(
        candidate_root,
        challenge,
        solution,
        task["full_name"],
        cache_root=cache_root,
    )
    accepted, output = _run_comparator(
        candidate_root,
        config_path,
        float(timeout_s),
        comparator=comparator,
        landrun=landrun,
        lean4export=lean4export,
    )
    if output.startswith("__VRM_CANDIDATE_TIMEOUT__"):
        return {"kind": "timeout", "phase": "candidate", "output": output[-4096:]}
    if accepted:
        backend = LeanDojoBackend(
            execution_mode="native",
            cache_dir=cache_root,
            cache_sha256=request["cache_sha256"],
            landrun_sha256=request["landrun_sha256"],
            comparator_root=comparator_root,
        )
        backend._tool_hashes = tool_hashes
        return {"kind": "valid", "audit": backend._audit_receipt(task), "output": output[-4096:]}

    diagnostic_root = work_root / "diagnostic"
    diagnostic_config = _write_audit_project(
        diagnostic_root,
        original,
        original,
        task["full_name"],
        cache_root=cache_root,
    )
    diagnostic_ok, diagnostic_output = _run_comparator(
        diagnostic_root,
        diagnostic_config,
        180.0,
        comparator=comparator,
        landrun=landrun,
        lean4export=lean4export,
    )
    if not diagnostic_ok:
        raise RuntimeError(
            "candidate failed and pinned original did not pass Comparator: "
            + diagnostic_output[-2048:]
        )
    return {"kind": "invalid", "diagnostic": "pinned_original_valid", "output": output[-4096:]}


def _worker_verify(request: dict) -> dict:
    _sandbox_check()
    _assert_worker_request(request)
    task = _validated_task(request.get("task"))
    if task["verifier"]["cache_sha256"] != request["cache_sha256"]:
        raise RuntimeError("task/cache digest mismatch")
    proof = request.get("proof")
    timeout_s = request.get("candidate_timeout_s")
    if (
        not isinstance(proof, str)
        or not proof.strip()
        or len(proof.encode("utf-8")) > _MAX_PROOF_BYTES
        or isinstance(timeout_s, bool)
        or not isinstance(timeout_s, (int, float))
        or not math.isfinite(timeout_s)
        or timeout_s <= 0
    ):
        raise ValueError("invalid worker proof or candidate timeout")

    # Preflight binds the full cache before candidates run. The cache is mounted
    # read-only, each target source is hashed below, and the run rehashes the full
    # cache after collection. Rehashing 6.7 GB for every candidate would consume
    # the registered verification budget without strengthening the model boundary.
    _check_cache(request, full_digest=False)
    _check_leandojo_install()
    tool_hashes = _check_comparator_source()
    _check_landrun(request["landrun_sha256"])
    challenge, solution, original = _target_sources(task, proof)

    candidate_root = Path("/work/candidate")
    candidate_config = _write_audit_project(
        candidate_root, challenge, solution, task["full_name"]
    )
    accepted, output = _run_comparator(candidate_root, candidate_config, float(timeout_s))
    if output.startswith("__VRM_CANDIDATE_TIMEOUT__"):
        return {"kind": "timeout", "phase": "candidate", "output": output[-4096:]}
    if accepted:
        receipt = _worker_backend(request, tool_hashes)._audit_receipt(task)
        return {"kind": "valid", "audit": receipt, "output": output[-4096:]}

    diagnostic_root = Path("/work/diagnostic")
    diagnostic_config = _write_audit_project(
        diagnostic_root, original, original, task["full_name"]
    )
    diagnostic_ok, diagnostic_output = _run_comparator(
        diagnostic_root, diagnostic_config, 180.0
    )
    if not diagnostic_ok:
        raise RuntimeError(
            "candidate failed and pinned original did not pass Comparator: "
            + diagnostic_output[-2048:]
        )
    return {
        "kind": "invalid",
        "diagnostic": "pinned_original_valid",
        "output": output[-4096:],
    }


def _worker(request: dict) -> dict:
    if request.get("op") == "probe":
        return _worker_probe(request)
    if request.get("op") == "verify":
        return _worker_verify(request)
    raise ValueError("unknown worker operation")


def _worker_main() -> None:
    import contextlib

    try:
        request = json.loads(sys.stdin.buffer.read(_MAX_OUTPUT_BYTES + 1))
        with contextlib.redirect_stdout(sys.stderr):
            response = _worker(request)
    except Exception as exc:
        response = {
            "kind": "infrastructure_error",
            "error": f"{type(exc).__name__}: {exc}"[:4096],
        }
    print(json.dumps(response), flush=True)


if __name__ == "__main__":
    _worker_main()
