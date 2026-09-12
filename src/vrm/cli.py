"""Small command-line entry point for the registered study workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from vrm.config import load_study_config
from vrm.data import prepare
from vrm.lean import LeanDojoBackend
from vrm.runtime import HFRunner
from vrm.workflow import run_development_smoke


def _read_jsonl(path: Path) -> list[dict]:
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path} must contain JSON objects")
    return rows


def _backend(args) -> LeanDojoBackend:
    return LeanDojoBackend(
        execution_mode=args.execution_mode,
        cache_dir=args.cache_dir,
        cache_sha256=args.cache_sha256,
        landrun_sha256=args.landrun_sha256,
        comparator_root=args.comparator_root,
    )


def _add_verifier_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--execution-mode", choices=("native", "docker"), default="native")
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--cache-sha256", required=True)
    parser.add_argument("--landrun-sha256", required=True)
    parser.add_argument("--comparator-root")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vrm")
    commands = parser.add_subparsers(dest="command", required=True)

    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--config", default="configs/study.json")
    prepare_parser.add_argument("--benchmark-root", required=True)
    prepare_parser.add_argument("--source-root", required=True)
    prepare_parser.add_argument("--archive", required=True)
    prepare_parser.add_argument("--output", required=True)
    prepare_parser.add_argument("--reduced", action="store_true")
    prepare_parser.add_argument("--local-files-only", action="store_true")

    preflight_parser = commands.add_parser("preflight")
    _add_verifier_arguments(preflight_parser)

    smoke_parser = commands.add_parser("smoke")
    smoke_parser.add_argument("--config", default="configs/study.json")
    smoke_parser.add_argument("--prepared-dir", required=True)
    smoke_parser.add_argument("--output", required=True)
    smoke_parser.add_argument("--local-files-only", action="store_true")
    _add_verifier_arguments(smoke_parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "prepare":
        from transformers import AutoTokenizer

        config = load_study_config(args.config)
        tokenizer = AutoTokenizer.from_pretrained(
            config["model_id"], revision=config["tokenizer_revision"],
            local_files_only=args.local_files_only, trust_remote_code=False,
        )
        result = prepare(
            args.benchmark_root, tokenizer, args.output,
            source_root=args.source_root, reduced=args.reduced,
            archive_path=args.archive,
        )
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("status") == "ready" else 2

    backend = _backend(args)
    readiness = backend.preflight()
    if args.command == "preflight" or not readiness.get("ready"):
        print(json.dumps(readiness, sort_keys=True))
        return 0 if readiness.get("ready") else 2

    config = load_study_config(args.config)
    prepared = Path(args.prepared_dir)
    public = _read_jsonl(prepared / "dev.jsonl")
    private = [
        row for row in _read_jsonl(prepared / "verifier_metadata.jsonl")
        if row.get("split") == "dev"
    ]
    runner = HFRunner(config, local_files_only=args.local_files_only)
    result = run_development_smoke(
        public, private, runner, backend, args.output,
        request={
            "study_id": config["study_id"],
            "config_sha256": config["config_sha256"],
            "smoke_gpu_budget_s": config["smoke_gpu_budget_s"],
            "candidates_per_task": 4,
        },
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
