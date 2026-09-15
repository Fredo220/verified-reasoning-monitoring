"""Bounded CPU-only development fixtures; never model candidates or test data."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from vrm import lean
from vrm.config import load_protocol_amendment, load_study_config
from vrm.core import canonical, digest
from vrm.data import validate_prepared_artifacts
from vrm.workflow import _joined_task, _validate_population, _write_bytes_atomic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise ValueError("Use a fresh output directory; measurements are immutable")
    config = load_study_config("configs/study.json")
    prepared = Path(args.prepared)
    amendment = load_protocol_amendment(config["protocol_amendment"], "configs/study.json")
    manifest = validate_prepared_artifacts(prepared, amendment)
    public = [json.loads(x) for x in (prepared / "dev.jsonl").read_text().splitlines()]
    private = [json.loads(x) for x in (prepared / "verifier_metadata.jsonl").read_text().splitlines()
               if json.loads(x)["split"] == "dev"]
    population = sorted(_validate_population(public, private), key=lambda pair: pair[0]["task_id"])
    # Selection is fixed before any measured outcome: first three dev task hashes.
    selected = population[:3]
    backend = lean.LeanDojoBackend(
        execution_mode="docker",
        image="sha256:0c1ed089532fdb118749ec6033e634282344766c923c57738f82ee07b62ce21c",
        cache_dir="/private/tmp/vrm-mathlib4-official",
        cache_sha256="14f2b096ac58afa54b625ac64c281bdfc112f9f327b3c196df46bfccf5473fd1",
        landrun_sha256="177fa7db952b2542135c373474c7c5263f8a0607e68fe22fa5fbcc4fae5a320b",
    )
    identity = {
        "purpose": "verifier-only readiness; not a scientific outcome or smoke",
        "selection": "first three dev task_ids in ascending order; no outcome selection",
        "timeout_s": 180, "worker_cpus": 1, "gpu_allocated_s": 0,
        "study_budgets_changed": False, "repeats_per_fixture": 1,
        "source_sha256": hashlib.sha256(Path(lean.__file__).read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "cache_sha256": backend.cache_sha256, "prepared_manifest_sha256": digest(manifest),
        "tasks": [p["task_id"] for p, _ in selected],
        "docker": subprocess.check_output(["docker", "info", "--format",
                    "{{.OSType}} {{.Architecture}} {{.NCPU}} {{.MemTotal}}"], text=True).strip(),
    }
    _write_bytes_atomic(output / "selection.json", canonical(identity))
    readiness = backend.preflight()
    _write_bytes_atomic(output / "preflight.json", canonical(readiness))
    if not readiness.get("ready"):
        print("READINESS_BLOCKED", flush=True)
        return 2
    runs = []
    for i, (public, private) in enumerate(selected):
        task = _joined_task(public, private, backend.identity)
        cases = [("reference", private["reference_proof"])]
        if i == 0:
            cases.append(("invalid_identifier", "by\n  exact vrm_nonexistent_readiness_control"))
        for label, proof in cases:
            result = backend.verify(task, proof, 180)
            receipt = {"task_id": public["task_id"], "full_name": public["full_name"],
                       "case": label, "proof_sha256": hashlib.sha256(proof.encode()).hexdigest(),
                       "selection_sha256": digest(identity), "result": result}
            _write_bytes_atomic(output / f"{i}-{label}.json", canonical(receipt))
            runs.append(receipt)
            print(json.dumps({"case": label, "task": public["full_name"],
                              "status": result["status"], "seconds": result["elapsed_s"]}), flush=True)
    post_hash = lean.cache_digest(backend.cache_dir)
    summary = {"runs": runs, "cache_unchanged": post_hash == backend.cache_sha256,
               "post_cache_sha256": post_hash, "scientific_gate_evaluated": False,
               "selection_sha256": digest(identity)}
    _write_bytes_atomic(output / "summary.json", canonical(summary))
    assert summary["cache_unchanged"]
    print("READINESS_MEASUREMENTS_RECORDED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
