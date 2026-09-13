"""Deterministic, fail-closed preparation of the frozen LeanDojo study splits."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import gc
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from typing import Any


UPSTREAM = {
    "benchmark": "LeanDojo Benchmark 4 v3",
    "doi": "10.5281/zenodo.18815372",
    "archive_checksum": "md5:b58af89599d5bbc792abc3744e5d37d9",
    "repo_url": "https://github.com/leanprover-community/mathlib4",
    "repo_commit": "1bc7728a050fc18ca2683f614c531cd7050ff063",
    "leandojo_version": "4.20.0",
    "lean_version": "v4.29.0-rc1",
}

FULL_SIZES = {"dev": 32, "train": 384, "val": 64, "id_test": 80, "ood_test": 40}
REDUCED_SIZES = {"dev": 32, "train": 192, "val": 32, "id_test": 40, "ood_test": 20}

_SPLIT_ORDER = ("dev", "train", "val", "id_test", "ood_test")
_TRAIN_SPLITS = _SPLIT_ORDER[:-1]
_HEX_64 = re.compile(r"[0-9a-f]{64}\Z")
_LEAN_PATH = re.compile(r"[A-Za-z0-9_./-]+\.lean\Z")
_TRUSTED_REFERENCE_ORIGINS = {"TracedTheorem.get_tactic_proof"}


class PreparationError(ValueError):
    """The requested dataset cannot be prepared without violating the protocol."""


def _canonical_payload_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _canonical_bytes(value: Any) -> bytes:
    return _canonical_payload_bytes(value) + b"\n"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _normalise_prompt(value: str) -> str:
    return " ".join(value.split())


def _normalise_newlines(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _require_nonempty_string(row: Mapping[str, Any], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _validate_sizes(sizes: Mapping[str, int]) -> dict[str, int]:
    if not isinstance(sizes, Mapping):
        raise ValueError("sizes must be a mapping")
    unknown = set(sizes) - set(_SPLIT_ORDER)
    if unknown:
        raise ValueError(f"unknown split names: {sorted(unknown)}")
    clean: dict[str, int] = {}
    for split in _SPLIT_ORDER:
        if split not in sizes:
            continue
        count = sizes[split]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"size for {split} must be a non-negative integer")
        clean[split] = count
    return clean


def _validated_assignment_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for source in rows:
        if not isinstance(source, Mapping):
            raise ValueError("each row must be a mapping")
        row = dict(source)
        task_id = _require_nonempty_string(row, "task_id")
        _require_nonempty_string(row, "group_id")
        prompt = _require_nonempty_string(row, "prompt")
        if row.get("upstream_split") not in {"train", "test"}:
            raise ValueError("upstream_split must be train or test")
        if task_id in seen_ids:
            raise ValueError(f"duplicate task_id: {task_id}")
        if not _normalise_prompt(prompt):
            raise ValueError("prompt must contain non-whitespace text")
        seen_ids.add(task_id)
        copied.append(row)
    return copied


def _grouped_representatives(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[tuple[dict[str, Any], str]]]:
    copied = _validated_assignment_rows(rows)
    parent = list(range(len(copied)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    by_group: dict[str, int] = {}
    by_prompt: dict[str, int] = {}
    for index, row in enumerate(copied):
        group_id = row["group_id"]
        prompt_key = _normalise_prompt(row["prompt"])
        if group_id in by_group:
            union(index, by_group[group_id])
        else:
            by_group[group_id] = index
        if prompt_key in by_prompt:
            union(index, by_prompt[prompt_key])
        else:
            by_prompt[prompt_key] = index

    components: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(copied):
        components[find(index)].append(row)

    candidates: dict[str, list[tuple[str, dict[str, Any]]]] = {
        "train": [],
        "test": [],
    }
    excluded: list[tuple[dict[str, Any], str]] = []
    for members in components.values():
        origins = {member["upstream_split"] for member in members}
        if len(origins) != 1:
            excluded.extend((member, "cross_origin_variant") for member in members)
            continue
        signature = json.dumps(
            sorted(
                (
                    member["task_id"],
                    member["group_id"],
                    _normalise_prompt(member["prompt"]),
                )
                for member in members
            ),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        component_hash = _sha256_text("vrm-split-v1\0" + signature)
        representative = min(
            members,
            key=lambda member: (
                _sha256_text(component_hash + "\0" + member["task_id"]),
                member["task_id"],
            ),
        )
        excluded.extend(
            (member, "duplicate_variant")
            for member in members
            if member is not representative
        )
        candidates[next(iter(origins))].append((component_hash, representative))

    ordered = {
        origin: [
            row
            for _, row in sorted(values, key=lambda item: (item[0], item[1]["task_id"]))
        ]
        for origin, values in candidates.items()
    }
    return ordered, excluded


def assign_splits(
    rows: Sequence[Mapping[str, Any]], sizes: Mapping[str, int]
) -> dict[str, list[dict[str, Any]]]:
    """Assign one deterministic representative per transitive variant group."""

    clean_sizes = _validate_sizes(sizes)
    candidates, _ = _grouped_representatives(rows)
    requested_train = sum(clean_sizes.get(split, 0) for split in _TRAIN_SPLITS)
    requested_test = clean_sizes.get("ood_test", 0)
    if len(candidates["train"]) < requested_train:
        raise PreparationError(
            "insufficient independent train groups: "
            f"need {requested_train}, have {len(candidates['train'])}"
        )
    if len(candidates["test"]) < requested_test:
        raise PreparationError(
            "insufficient independent test groups: "
            f"need {requested_test}, have {len(candidates['test'])}"
        )

    result = {split: [] for split in _SPLIT_ORDER if split in clean_sizes}
    offset = 0
    for split in _TRAIN_SPLITS:
        count = clean_sizes.get(split, 0)
        if split in result:
            result[split] = [
                dict(row, split=split)
                for row in candidates["train"][offset : offset + count]
            ]
        offset += count
    if "ood_test" in result:
        result["ood_test"] = [
            dict(row, split="ood_test")
            for row in candidates["test"][:requested_test]
        ]
    return result


def _validated_file_path(value: Any) -> PurePosixPath:
    if not isinstance(value, str) or not _LEAN_PATH.fullmatch(value) or "\\" in value:
        raise PreparationError("file_path is not a canonical Mathlib Lean path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or path.parts[0] != "Mathlib":
        raise PreparationError("file_path is outside the pinned Mathlib source tree")
    if str(path) != value or any(part in {"", ".", ".."} for part in path.parts):
        raise PreparationError("file_path contains path traversal")
    return path


def official_source_url(row: Mapping[str, Any]) -> str:
    """Return a raw URL only for a source in the exact pinned Mathlib repository."""

    if row.get("url") != UPSTREAM["repo_url"]:
        raise PreparationError("repository URL does not match the canonical official URL")
    if row.get("commit") != UPSTREAM["repo_commit"]:
        raise PreparationError("repository commit does not match the official pin")
    path = _validated_file_path(row.get("file_path"))
    return (
        "https://raw.githubusercontent.com/leanprover-community/mathlib4/"
        f"{UPSTREAM['repo_commit']}/{path}"
    )


def _position(value: Any, field: str) -> tuple[int, int]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 2
        or any(
            isinstance(part, bool) or not isinstance(part, int) or part < 1
            for part in value
        )
    ):
        raise PreparationError(f"invalid {field} position")
    return value[0], value[1]


def _position_offset(text: str, value: Any, field: str) -> int:
    line_number, column = _position(value, field)
    lines = text.splitlines(keepends=True)
    if line_number > len(lines):
        raise PreparationError(f"{field} position is outside source")
    line = lines[line_number - 1]
    content_length = len(line.rstrip("\r\n"))
    if column > content_length + 1:
        raise PreparationError(f"{field} position is outside source")
    return sum(len(part) for part in lines[: line_number - 1]) + column - 1


def _slice_source(text: str, start: Any, end: Any, label: str) -> str:
    start_offset = _position_offset(text, start, f"{label}_start")
    end_offset = _position_offset(text, end, f"{label}_end")
    if end_offset <= start_offset:
        raise PreparationError(f"invalid {label} position order")
    return text[start_offset:end_offset]


def _normalised_with_offsets(value: str) -> tuple[str, list[int]]:
    characters: list[str] = []
    offsets = [0]
    index = 0
    while index < len(value):
        if value.startswith("\r\n", index):
            characters.append("\n")
            index += 2
        else:
            character = value[index]
            characters.append("\n" if character == "\r" else character)
            index += 1
        offsets.append(index)
    return "".join(characters), offsets


def _offset_position(text: str, offset: int) -> list[int]:
    line = text.count("\n", 0, offset) + 1
    previous_newline = text.rfind("\n", 0, offset)
    column = offset - previous_newline
    return [line, column]


def _extract_proof(
    source: str, start: Any, end: Any, theorem_statement: str
) -> tuple[str, list[int], list[int]]:
    declaration_start = _position_offset(source, start, "declaration_start")
    declaration_end = _position_offset(source, end, "declaration_end")
    if declaration_end <= declaration_start:
        raise PreparationError("invalid declaration position order")
    declaration = source[declaration_start:declaration_end]
    normalised, offsets = _normalised_with_offsets(declaration)
    statement = _normalise_newlines(theorem_statement)
    if not normalised.startswith(statement):
        raise PreparationError("theorem_statement_source_mismatch")
    raw_statement_end = offsets[len(statement)]
    remainder = declaration[raw_statement_end:]
    proof_leading = len(remainder) - len(remainder.lstrip())
    proof_start_offset = declaration_start + raw_statement_end + proof_leading
    proof = source[proof_start_offset:declaration_end]
    if not re.match(r"by(?:\s|$)", proof):
        raise PreparationError("complete_by_proof")
    return proof, _offset_position(source, proof_start_offset), list(_position(end, "end"))


def _read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreparationError(f"cannot read valid JSON from {path.name}: {exc}") from exc


def _read_jsonl(path: Path) -> list[Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            lines = list(handle)
    except (OSError, UnicodeError) as exc:
        raise PreparationError(f"cannot read {path.name}: {exc}") from exc
    rows = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise PreparationError(
                f"invalid JSON in {path.name} line {line_number}: {exc}"
            ) from exc
    return rows


def _jsonl_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return b"".join(_canonical_bytes(row) for row in rows)


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and bool(_HEX_64.fullmatch(value))


def _md5_file(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise PreparationError(f"cannot read archive_path: {exc}") from exc
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise PreparationError(f"cannot read prepared artifact: {exc}") from exc
    return digest.hexdigest()


def validate_prepared_artifacts(
    prepared_dir: str | os.PathLike[str], amendment: Mapping[str, Any]
) -> dict[str, Any]:
    """Verify the preserved corpus against its approved hash-bound correction."""
    root = Path(prepared_dir)
    if amendment.get("status") != "approved_pre_outcome":
        raise PreparationError("runtime provenance amendment is not approved")
    expected = amendment.get("prepared_artifacts")
    evidence = amendment.get("evidence")
    if not isinstance(expected, Mapping) or not isinstance(evidence, Mapping):
        raise PreparationError("runtime provenance amendment lacks artifact hashes")

    manifest_path = root / "manifest.json"
    expected_manifest = evidence.get("prepared_manifest_sha256")
    if not _is_hash(expected_manifest) or _sha256_file(manifest_path) != expected_manifest:
        raise PreparationError("prepared manifest digest mismatch")
    manifest = _read_json(manifest_path)
    if not isinstance(manifest, Mapping) or manifest.get("status") != "ready":
        raise PreparationError("prepared manifest is not ready")
    declared = manifest.get("artifacts")
    if not isinstance(declared, Mapping) or set(declared) != set(expected):
        raise PreparationError("prepared artifact inventory mismatch")

    for name, expected_digest in expected.items():
        if not isinstance(name, str) or PurePosixPath(name).name != name:
            raise PreparationError("prepared artifact name is invalid")
        if not _is_hash(expected_digest):
            raise PreparationError("prepared artifact digest is invalid")
        artifact_path = root / name
        declared_item = declared.get(name)
        if not isinstance(declared_item, Mapping):
            raise PreparationError("prepared artifact manifest entry is invalid")
        if declared_item.get("sha256") != expected_digest:
            raise PreparationError("prepared artifact declaration mismatch")
        try:
            size = artifact_path.stat().st_size
        except OSError as exc:
            raise PreparationError(f"prepared artifact is missing: {name}") from exc
        if declared_item.get("bytes") != size:
            raise PreparationError("prepared artifact size mismatch")
        if _sha256_file(artifact_path) != expected_digest:
            raise PreparationError("prepared artifact digest mismatch")
    return dict(manifest)


def _fixture_provenance(
    metadata: Mapping[str, Any],
) -> tuple[dict[str, str] | None, list[str]]:
    declared = metadata.get("trusted_fixture_provenance")
    if declared is None:
        return None, []
    if not isinstance(declared, Mapping):
        return None, ["trusted_fixture_provenance must be an object"]
    if declared.get("archive_checksum") != UPSTREAM["archive_checksum"]:
        return None, ["trusted fixture archive checksum does not match the official pin"]
    source_files = declared.get("source_files")
    if not isinstance(source_files, Mapping):
        return None, ["trusted fixture provenance is missing source_files"]
    hashes: dict[str, str] = {}
    for path, value in source_files.items():
        if not isinstance(path, str) or not _is_hash(value):
            return None, ["trusted fixture provenance contains an invalid source hash"]
        hashes[path] = value
    return hashes, []


def _verify_archive(
    metadata: Mapping[str, Any], archive_path: str | os.PathLike[str] | None
) -> tuple[str | None, dict[str, str] | None, list[str]]:
    fixture_hashes, blockers = _fixture_provenance(metadata)
    if blockers:
        return None, None, blockers
    if archive_path is None:
        if fixture_hashes is not None:
            return "trusted_fixture", fixture_hashes, []
        return None, None, [
            "archive_path is required to verify the official Benchmark 4 v3 archive"
        ]
    archive = Path(archive_path)
    if not archive.is_file():
        return None, None, ["archive_path is not a readable file"]
    try:
        actual = _md5_file(archive)
    except PreparationError as exc:
        return None, None, [str(exc)]
    expected = UPSTREAM["archive_checksum"].split(":", 1)[1]
    if actual != expected:
        return None, None, [f"archive md5 mismatch: expected {expected}, got {actual}"]
    return "verified_md5", fixture_hashes, []


def _canonical_git_origin(value: str) -> str | None:
    trimmed = value.strip().removesuffix(".git").rstrip("/")
    if trimmed == UPSTREAM["repo_url"]:
        return UPSTREAM["repo_url"]
    if trimmed == "git@github.com:leanprover-community/mathlib4":
        return UPSTREAM["repo_url"]
    return None


def _git_output(source_root: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(source_root), *arguments],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PreparationError(f"source checkout git command failed: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "unknown git error"
        raise PreparationError(f"source checkout git command failed: {detail}")
    return completed.stdout.strip()


def _verify_source_checkout(
    source_root: str | os.PathLike[str] | None,
    fixture_hashes: Mapping[str, str] | None,
) -> tuple[Path | None, str | None, list[str]]:
    if source_root is None:
        return None, None, ["source_root is required for exact source checkout provenance"]
    root = Path(source_root).resolve()
    if not root.is_dir():
        return None, None, ["source_root is not a directory"]
    if fixture_hashes is not None:
        return root, "trusted_fixture", []
    try:
        top = Path(_git_output(root, "rev-parse", "--show-toplevel")).resolve()
        if top != root:
            raise PreparationError("source_root must be the Git checkout root")
        if _git_output(root, "rev-parse", "HEAD") != UPSTREAM["repo_commit"]:
            raise PreparationError("source checkout HEAD does not match the pinned mathlib commit")
        origin = _git_output(root, "config", "--get", "remote.origin.url")
        if _canonical_git_origin(origin) != UPSTREAM["repo_url"]:
            raise PreparationError("source checkout origin is not canonical mathlib4")
        tracked_status = _git_output(
            root, "status", "--porcelain", "--untracked-files=no"
        )
        if tracked_status:
            raise PreparationError("source checkout has tracked modifications")
    except PreparationError as exc:
        return None, None, [str(exc)]
    return root, "verified_clean_git", []


def _is_official_cache_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    path = PurePosixPath(value)
    expected_parent = f"leanprover-community-mathlib4-{UPSTREAM['repo_commit']}"
    return (
        path.is_absolute()
        and len(path.parts) >= 3
        and path.parts[-2:] == (expected_parent, "mathlib4_d")
        and "lean_dojo" in path.parts
    )


def _benchmark_url_is_acceptable(value: Any) -> bool:
    return value in {
        UPSTREAM["repo_url"],
        UPSTREAM["repo_url"] + ".git",
    } or _is_official_cache_url(value)


def _validate_metadata(metadata: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    from_repo = metadata.get("from_repo")
    if not isinstance(from_repo, Mapping):
        return ["metadata.json is missing from_repo provenance"]
    if not _benchmark_url_is_acceptable(from_repo.get("url")):
        blockers.append("metadata.json from_repo.url is not the official v3 cache or repository")
    if from_repo.get("commit") != UPSTREAM["repo_commit"]:
        blockers.append("metadata.json from_repo.commit does not match the pinned mathlib commit")
    if metadata.get("leandojo_version") != UPSTREAM["leandojo_version"]:
        blockers.append("metadata.json leandojo_version does not match the official pin")
    return blockers


def _valid_budget_decision(path: Path) -> tuple[bool, str | None, str | None]:
    if not path.is_file():
        return False, "reduced plan requires budget_decision.json", None
    try:
        decision = _read_json(path)
    except PreparationError as exc:
        return False, str(exc), None
    if not isinstance(decision, Mapping) or decision.get("made_before_test") is not True:
        return False, "budget_decision.json must record made_before_test=true", None
    values: dict[str, float] = {}
    for field in ("full_estimated_seconds", "reduced_estimated_seconds", "budget_seconds"):
        value = decision.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
        ):
            return False, f"budget_decision.json has invalid {field}", None
        values[field] = float(value)
    if not (
        values["reduced_estimated_seconds"]
        <= values["budget_seconds"]
        < values["full_estimated_seconds"]
    ):
        return False, "budget_decision.json does not justify the reduced plan", None
    if not _is_hash(decision.get("pretest_measurement_sha256")):
        return False, "budget_decision.json has invalid pretest_measurement_sha256", None
    return True, None, _sha256_bytes(_canonical_payload_bytes(decision))


def _render_prompt(tokenizer: Any, initial_state: str) -> tuple[str, int]:
    content = (
        "Prove this Lean 4 theorem. Return only a complete proof beginning with `by`.\n\n"
        + initial_state
    )
    apply_template = getattr(tokenizer, "apply_chat_template", None)
    if callable(apply_template) and getattr(tokenizer, "chat_template", None):
        encoded = apply_template(
            [{"role": "user", "content": content}],
            tokenize=True,
            add_generation_prompt=True,
        )
        token_ids = encoded.get("input_ids") if isinstance(encoded, Mapping) else encoded
        if not isinstance(token_ids, list) or not token_ids:
            raise PreparationError("tokenizer produced empty or invalid chat token IDs")
    else:
        try:
            token_ids = tokenizer.encode(content, add_special_tokens=False)
        except Exception as exc:
            raise PreparationError(f"tokenizer failed on prompt: {exc}") from exc
    return content, len(token_ids)


def _reference_tokens(tokenizer: Any, proof: str) -> int:
    try:
        return len(tokenizer.encode(proof, add_special_tokens=False))
    except Exception as exc:
        raise PreparationError(f"tokenizer failed on reference proof: {exc}") from exc


def _contains_self_reference(initial_state: str, full_name: str) -> bool:
    leaf = full_name.rsplit(".", 1)[-1]
    for name in {full_name, leaf}:
        pattern = rf"(?<![A-Za-z0-9_']){re.escape(name)}(?![A-Za-z0-9_'])"
        if re.search(pattern, initial_state):
            return True
    return False


def _identity(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("url"),
        row.get("commit"),
        row.get("file_path"),
        row.get("full_name"),
        tuple(row.get("start", ()))
        if isinstance(row.get("start"), (list, tuple))
        else row.get("start"),
        tuple(row.get("end", ()))
        if isinstance(row.get("end"), (list, tuple))
        else row.get("end"),
    )


def _task_id(row: Mapping[str, Any]) -> str:
    payload = {
        "repo_url": UPSTREAM["repo_url"],
        "repo_commit": UPSTREAM["repo_commit"],
        "file_path": row.get("file_path"),
        "full_name": row.get("full_name"),
        "start": row.get("start"),
        "end": row.get("end"),
    }
    return _sha256_bytes(_canonical_payload_bytes(payload))


def _audit_row(
    task_id: str,
    group_id: str,
    origin: str,
    trace_sha256: str,
    reasons: Sequence[str],
    *,
    tactic_count: int | None = None,
    prompt: str | None = None,
    prompt_tokens: int | None = None,
    proof: str | None = None,
    reference_tokens: int | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "eligible": not reasons,
        "group_id": group_id,
        "reasons": sorted(set(reasons)),
        "task_id": task_id,
        "trace_sha256": trace_sha256,
        "upstream_split": origin,
    }
    if tactic_count is not None:
        row["recorded_tactics"] = tactic_count
    if prompt is not None:
        row["prompt_sha256"] = _sha256_text(prompt)
    if prompt_tokens is not None:
        row["prompt_tokens"] = prompt_tokens
    if proof is not None:
        row["reference_sha256"] = _sha256_text(proof)
    if reference_tokens is not None:
        row["reference_tokens"] = reference_tokens
    return row


def _manifest_base(tokenizer: Any, sizes: Mapping[str, int], reduced: bool) -> dict[str, Any]:
    tokenizer_name = getattr(tokenizer, "name_or_path", tokenizer.__class__.__name__)
    return {
        "schema_version": 2,
        "status": "blocked",
        "upstream": dict(UPSTREAM),
        "source_policy": {
            "development": "novel_premises/train.json",
            "ood_test": "novel_premises/test.json",
            "upstream_val_used": False,
        },
        "data_loading": {
            "strategy": "sequential_split_arrays",
            "maximum_expanded_splits": 1,
        },
        "plan": "reduced" if reduced else "full",
        "requested_counts": dict(sizes),
        "tokenizer": {"name_or_path": str(tokenizer_name)},
        "limits": {"recorded_tactics": 6, "reference_tokens": 64, "prompt_tokens": 512},
        "provenance": {},
        "counts": {},
        "rejections": {},
        "blockers": [],
        "artifacts": {},
    }


def _atomic_write_directory(output_dir: Path, files: Mapping[str, bytes]) -> None:
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.tmp-", dir=output_dir.parent)
    )
    try:
        for name in sorted(files):
            (temporary / name).write_bytes(files[name])
        if output_dir.exists():
            raise FileExistsError(f"output directory already exists: {output_dir}")
        os.rename(temporary, output_dir)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def _finish_blocked(
    output_dir: Path,
    manifest: dict[str, Any],
    blockers: Sequence[str],
    rejections: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    manifest["blockers"] = sorted(set(blockers))
    manifest["rejections"] = dict(sorted((rejections or {}).items()))
    _atomic_write_directory(output_dir, {"manifest.json": _canonical_bytes(manifest)})
    return manifest


def _load_enrichment(
    path: Path,
) -> tuple[dict[tuple[Any, ...], Mapping[str, Any]], list[str]]:
    if not path.is_file():
        return {}, []
    try:
        rows = _read_jsonl(path)
    except PreparationError as exc:
        return {}, [str(exc)]
    result: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            return {}, ["traced_metadata.jsonl rows must be objects"]
        identity = _identity(row)
        if identity in result:
            return {}, ["ambiguous duplicate identities in traced_metadata.jsonl"]
        result[identity] = row
    return result, []


def _compact_split(
    rows: Any,
    origin: str,
    enrichment: Mapping[tuple[Any, ...], Mapping[str, Any]],
    audits: list[dict[str, Any]],
    rejections: Counter[str],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    if not isinstance(rows, list):
        return [], {}, [f"novel_premises/{origin}.json must contain a JSON array"]
    stubs: list[dict[str, Any]] = []
    details: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    for ordinal, row in enumerate(rows):
        if not isinstance(row, Mapping):
            trace_hash = _sha256_bytes(_canonical_payload_bytes(row))
            rejections["malformed_row"] += 1
            audits.append(
                _audit_row(
                    trace_hash, trace_hash, origin, trace_hash, ["malformed_row"]
                )
            )
            continue
        trace_hash = _sha256_bytes(_canonical_payload_bytes(row))
        task_id = _task_id(row)
        reasons: list[str] = []
        try:
            full_name = _require_nonempty_string(row, "full_name")
        except ValueError:
            full_name = ""
            reasons.append("full_name")
        if (
            row.get("commit") != UPSTREAM["repo_commit"]
            or not _benchmark_url_is_acceptable(row.get("url"))
        ):
            reasons.append("row_provenance")
        file_path = row.get("file_path")
        if isinstance(file_path, str) and file_path.startswith(".lake/packages/"):
            reasons.append("unsupported_dependency_path")
        else:
            try:
                _validated_file_path(file_path)
            except PreparationError:
                reasons.append("unsupported_source_path")
        try:
            _position(row.get("start"), "start")
            _position(row.get("end"), "end")
        except PreparationError:
            reasons.append("source_position")
        statement = row.get("theorem_statement")
        if not isinstance(statement, str) or not statement.strip():
            reasons.append("theorem_statement")
        tactics = row.get("traced_tactics")
        tactic_count = len(tactics) if isinstance(tactics, list) else None
        if tactic_count is None:
            reasons.append("traced_tactics")
            tactics = []
        elif tactic_count > 6:
            reasons.append("recorded_tactics")
        if not tactics or not isinstance(tactics[0], Mapping):
            reasons.append("missing_initial_state")
            initial_state = ""
        else:
            initial_state = tactics[0].get("state_before")
            if not isinstance(initial_state, str) or not initial_state.strip():
                reasons.append("missing_initial_state")
                initial_state = ""
        if full_name and initial_state and _contains_self_reference(initial_state, full_name):
            reasons.append("self_reference")

        extra = enrichment.get(_identity(row))
        if extra is not None:
            extra_state = extra.get("initial_state")
            if (
                isinstance(extra_state, str)
                and full_name
                and _contains_self_reference(extra_state, full_name)
            ):
                blockers.append(
                    f"{origin}[{ordinal}]: self_reference in enriched initial_state"
                )
            if extra.get("initial_state_origin") not in {
                None,
                "pretraced_proof_root",
            }:
                blockers.append(f"{origin}[{ordinal}]: invalid initial_state_origin")
            if extra_state is not None and extra_state != initial_state:
                blockers.append(f"{origin}[{ordinal}]: enriched initial_state mismatch")

        group_value = extra.get("group_id") if extra is not None else row.get("group_id")
        if group_value is not None and (
            not isinstance(group_value, str) or not group_value
        ):
            reasons.append("group_id")
            group_value = None
        group_id = group_value or _sha256_text(
            "vrm-group-v1\0" + _normalise_prompt(initial_state or task_id)
        )
        if reasons:
            for reason in set(reasons):
                rejections[reason] += 1
            audits.append(
                _audit_row(
                    task_id,
                    group_id,
                    origin,
                    trace_hash,
                    reasons,
                    tactic_count=tactic_count,
                )
            )
            continue
        stubs.append(
            {
                "task_id": task_id,
                "group_id": group_id,
                "upstream_split": origin,
                "prompt": initial_state,
            }
        )
        details[task_id] = {
            "end": row["end"],
            "enrichment": extra,
            "file_path": file_path,
            "full_name": full_name,
            "initial_state": initial_state,
            "start": row["start"],
            "theorem_statement": statement,
            "trace_sha256": trace_hash,
            "tactic_count": tactic_count,
        }
    return stubs, details, blockers


def _read_source(
    source_root: Path,
    file_path: str,
    fixture_hashes: Mapping[str, str] | None,
    cache: dict[str, tuple[str, str]],
) -> tuple[str | None, str | None, str | None]:
    if file_path in cache:
        text, digest = cache[file_path]
        return text, digest, None
    source_path = source_root.joinpath(*PurePosixPath(file_path).parts)
    try:
        resolved = source_path.resolve()
        resolved.relative_to(source_root)
    except (OSError, ValueError):
        return None, None, "source_path_escape"
    if not resolved.is_file():
        return None, None, "source_unavailable"
    try:
        text = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None, None, "source_unavailable"
    digest = _sha256_text(text)
    if fixture_hashes is not None:
        expected = fixture_hashes.get(file_path)
        if expected is None:
            return None, None, "fixture source hash missing"
        if digest != expected:
            return None, None, "fixture source_sha256 mismatch"
    cache[file_path] = (text, digest)
    return text, digest, None


def _evaluate_candidate(
    candidate: Mapping[str, Any],
    detail: Mapping[str, Any],
    tokenizer: Any,
    source_root: Path,
    fixture_hashes: Mapping[str, str] | None,
    source_cache: dict[str, tuple[str, str]],
) -> tuple[dict[str, Any] | None, dict[str, Any], list[str]]:
    reasons: list[str] = []
    blockers: list[str] = []
    enrichment = detail.get("enrichment")
    text, source_hash, source_error = _read_source(
        source_root, detail["file_path"], fixture_hashes, source_cache
    )
    proof: str | None = None
    proof_start: list[int] | None = None
    proof_end: list[int] | None = None
    if text is None:
        exported = (
            enrichment.get("reference_proof")
            if isinstance(enrichment, Mapping)
            else None
        )
        trusted_export = (
            isinstance(enrichment, Mapping)
            and enrichment.get("reference_origin") in _TRUSTED_REFERENCE_ORIGINS
            and isinstance(exported, str)
            and bool(re.match(r"by(?:\s|$)", exported))
        )
        if fixture_hashes is not None and trusted_export:
            proof = exported
            proof_start = enrichment.get("proof_start")
            proof_end = enrichment.get("proof_end")
            source_hash = fixture_hashes.get(detail["file_path"])
        else:
            reasons.append(source_error or "source_unavailable")
    else:
        if isinstance(enrichment, Mapping):
            declared_hash = enrichment.get("source_sha256")
            if declared_hash is not None and declared_hash != source_hash:
                blockers.append("source_sha256 mismatch in traced_metadata enrichment")
        try:
            proof, proof_start, proof_end = _extract_proof(
                text,
                detail["start"],
                detail["end"],
                detail["theorem_statement"],
            )
        except PreparationError as exc:
            reasons.append(str(exc))

        if proof is not None and isinstance(enrichment, Mapping):
            enriched_start = enrichment.get("proof_start")
            enriched_end = enrichment.get("proof_end")
            if enriched_start is not None and enriched_end is not None:
                if enriched_start != proof_start:
                    blockers.append("proof_start does not match derived proof position")
                if enriched_end != proof_end:
                    blockers.append("proof_end does not match declaration end")
                try:
                    enriched_proof = _slice_source(
                        text, enriched_start, enriched_end, "proof"
                    )
                except PreparationError as exc:
                    blockers.append(str(exc))
                else:
                    if enriched_proof != proof:
                        blockers.append(
                            "proof_start source span does not match derived proof"
                        )
            exported = enrichment.get("reference_proof")
            if exported is not None:
                if (
                    enrichment.get("reference_origin")
                    not in _TRUSTED_REFERENCE_ORIGINS
                    or not isinstance(exported, str)
                    or not re.match(r"by(?:\s|$)", exported)
                ):
                    blockers.append("untrusted or invalid exported reference proof")
                elif exported != proof:
                    blockers.append("source and exported reference proof mismatch")

    rendered_prompt: str | None = None
    prompt_tokens: int | None = None
    reference_token_count: int | None = None
    if proof is not None:
        try:
            reference_token_count = _reference_tokens(tokenizer, proof)
            rendered_prompt, prompt_tokens = _render_prompt(
                tokenizer, detail["initial_state"]
            )
        except PreparationError as exc:
            blockers.append(str(exc))
        else:
            if reference_token_count > 64:
                reasons.append("reference_tokens")
            if prompt_tokens > 512:
                reasons.append("prompt_tokens")
    audit = _audit_row(
        candidate["task_id"],
        candidate["group_id"],
        candidate["upstream_split"],
        detail["trace_sha256"],
        reasons,
        tactic_count=detail["tactic_count"],
        prompt=rendered_prompt,
        prompt_tokens=prompt_tokens,
        proof=proof,
        reference_tokens=reference_token_count,
    )
    if reasons or blockers or proof is None or rendered_prompt is None:
        return None, audit, blockers
    verifier = {
        "end": detail["end"],
        "file_path": detail["file_path"],
        "full_name": detail["full_name"],
        "proof_end": proof_end,
        "proof_start": proof_start,
        "reference_origin": "exact_official_source_declaration",
        "reference_proof": proof,
        "repo_commit": UPSTREAM["repo_commit"],
        "repo_url": UPSTREAM["repo_url"],
        "source_sha256": source_hash,
        "start": detail["start"],
        "theorem_statement": detail["theorem_statement"],
        "trace_sha256": detail["trace_sha256"],
    }
    selected = dict(candidate, prompt=rendered_prompt, verifier=verifier)
    return selected, audit, []


def prepare(
    benchmark_root: str | os.PathLike[str],
    tokenizer: Any,
    output_dir: str | os.PathLike[str],
    source_root: str | os.PathLike[str] | None = None,
    reduced: bool = False,
    archive_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Prepare deterministic public splits and private verifier metadata."""

    root = Path(benchmark_root)
    destination = Path(output_dir)
    if destination.exists():
        raise FileExistsError(f"output directory already exists: {destination}")
    sizes = dict(REDUCED_SIZES if reduced else FULL_SIZES)
    manifest = _manifest_base(tokenizer, sizes, reduced)
    rejections: Counter[str] = Counter()
    blockers: list[str] = []
    budget_hash: str | None = None

    required = {
        "novel_premises/train.json": root / "novel_premises" / "train.json",
        "novel_premises/test.json": root / "novel_premises" / "test.json",
        "metadata.json": root / "metadata.json",
    }
    blockers.extend(
        f"missing required input: {relative}"
        for relative, path in required.items()
        if not path.is_file()
    )
    if blockers:
        return _finish_blocked(destination, manifest, blockers)
    try:
        metadata = _read_json(required["metadata.json"])
    except PreparationError as exc:
        return _finish_blocked(destination, manifest, [str(exc)])
    if not isinstance(metadata, Mapping):
        return _finish_blocked(
            destination, manifest, ["metadata.json must contain an object"]
        )

    archive_mode, fixture_hashes, archive_blockers = _verify_archive(
        metadata, archive_path
    )
    blockers.extend(archive_blockers)
    if blockers:
        return _finish_blocked(destination, manifest, blockers)
    effective_source_root = source_root if source_root is not None else root / "sources"
    verified_source_root, source_mode, source_blockers = _verify_source_checkout(
        effective_source_root, fixture_hashes
    )
    blockers.extend(source_blockers)
    blockers.extend(_validate_metadata(metadata))
    if blockers or verified_source_root is None:
        return _finish_blocked(destination, manifest, blockers)
    manifest["provenance"] = {
        "archive_verification": archive_mode,
        "source_checkout": source_mode,
    }

    if reduced:
        valid_budget, budget_blocker, budget_hash = _valid_budget_decision(
            root / "budget_decision.json"
        )
        if not valid_budget and budget_blocker:
            return _finish_blocked(destination, manifest, [budget_blocker])

    enrichment, enrichment_blockers = _load_enrichment(
        root / "traced_metadata.jsonl"
    )
    if enrichment_blockers:
        return _finish_blocked(destination, manifest, enrichment_blockers)

    stubs: list[dict[str, Any]] = []
    details: dict[str, dict[str, Any]] = {}
    audits: list[dict[str, Any]] = []
    for origin, path in (
        ("train", required["novel_premises/train.json"]),
        ("test", required["novel_premises/test.json"]),
    ):
        try:
            expanded_rows = _read_json(path)
        except PreparationError as exc:
            return _finish_blocked(destination, manifest, [str(exc)], rejections)
        split_stubs, split_details, split_blockers = _compact_split(
            expanded_rows, origin, enrichment, audits, rejections
        )
        stubs.extend(split_stubs)
        details.update(split_details)
        del expanded_rows
        gc.collect()
        if split_blockers:
            return _finish_blocked(
                destination, manifest, split_blockers, rejections
            )

    try:
        candidates, grouped_out = _grouped_representatives(stubs)
    except ValueError as exc:
        return _finish_blocked(destination, manifest, [str(exc)], rejections)
    for row, reason in grouped_out:
        rejections[reason] += 1
        detail = details[row["task_id"]]
        audits.append(
            _audit_row(
                row["task_id"],
                row["group_id"],
                row["upstream_split"],
                detail["trace_sha256"],
                [reason],
                tactic_count=detail["tactic_count"],
            )
        )

    needed = {
        "train": sum(sizes[split] for split in _TRAIN_SPLITS),
        "test": sizes["ood_test"],
    }
    eligible: dict[str, list[dict[str, Any]]] = {"train": [], "test": []}
    source_cache: dict[str, tuple[str, str]] = {}
    systemic_source_blockers: list[str] = []
    for origin in ("train", "test"):
        for candidate in candidates[origin]:
            if len(eligible[origin]) >= needed[origin]:
                break
            selected, audit, candidate_blockers = _evaluate_candidate(
                candidate,
                details[candidate["task_id"]],
                tokenizer,
                verified_source_root,
                fixture_hashes,
                source_cache,
            )
            audits.append(audit)
            systemic_source_blockers.extend(candidate_blockers)
            for reason in audit["reasons"]:
                rejections[reason] += 1
            if selected is not None:
                eligible[origin].append(selected)
    if systemic_source_blockers:
        return _finish_blocked(
            destination, manifest, systemic_source_blockers, rejections
        )
    for origin in ("train", "test"):
        if len(eligible[origin]) < needed[origin]:
            blockers.append(
                f"insufficient eligible independent {origin} groups: "
                f"need {needed[origin]}, have {len(eligible[origin])}"
            )
    if blockers:
        return _finish_blocked(destination, manifest, blockers, rejections)

    assigned: dict[str, list[dict[str, Any]]] = {}
    offset = 0
    for split in _TRAIN_SPLITS:
        count = sizes[split]
        assigned[split] = eligible["train"][offset : offset + count]
        offset += count
    assigned["ood_test"] = eligible["test"][: sizes["ood_test"]]

    public_files: dict[str, bytes] = {}
    verifier_rows: list[dict[str, Any]] = []
    for split in _SPLIT_ORDER:
        public_rows = []
        for row in assigned[split]:
            verifier = dict(row["verifier"], split=split, task_id=row["task_id"])
            public_rows.append(
                {
                    "file_path": verifier["file_path"],
                    "full_name": verifier["full_name"],
                    "group_id": row["group_id"],
                    "prompt": row["prompt"],
                    "repo_commit": UPSTREAM["repo_commit"],
                    "repo_url": UPSTREAM["repo_url"],
                    "split": split,
                    "task_id": row["task_id"],
                }
            )
            verifier_rows.append(
                {
                    "content_sha256": _sha256_bytes(
                        _canonical_payload_bytes(verifier)
                    ),
                    "metadata": verifier,
                    "split": split,
                    "task_id": row["task_id"],
                }
            )
        public_files[f"{split}.jsonl"] = _jsonl_bytes(public_rows)

    audits.sort(
        key=lambda row: (row["task_id"], row["upstream_split"], row["reasons"])
    )
    verifier_rows.sort(key=lambda row: (row["split"], row["task_id"]))
    files = {
        **public_files,
        "eligibility_audit.jsonl": _jsonl_bytes(audits),
        "verifier_metadata.jsonl": _jsonl_bytes(verifier_rows),
    }
    manifest["status"] = "ready"
    manifest["counts"] = {split: len(assigned[split]) for split in _SPLIT_ORDER}
    manifest["rejections"] = dict(sorted(rejections.items()))
    manifest["source_files_hashed"] = len(source_cache)
    if budget_hash is not None:
        manifest["budget_decision_sha256"] = budget_hash
    manifest["artifacts"] = {
        name: {"sha256": _sha256_bytes(content), "bytes": len(content)}
        for name, content in sorted(files.items())
    }
    files["manifest.json"] = _canonical_bytes(manifest)
    _atomic_write_directory(destination, files)
    return manifest
