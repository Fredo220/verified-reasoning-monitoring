import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from vrm.workflow import run_development_smoke
from vrm import lean


def metadata_digest(value):
    content = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def tasks():
    public = []
    private = []
    for index in range(32):
        task_id = f"dev-{index:02d}"
        public.append({
            "task_id": task_id,
            "group_id": task_id,
            "split": "dev",
            "repo_url": "https://github.com/leanprover-community/mathlib4",
            "repo_commit": "1bc7728a050fc18ca2683f614c531cd7050ff063",
            "file_path": f"Mathlib/Example{index}.lean",
            "full_name": f"Example.theorem_{index}",
            "prompt": f"Prove theorem {index}",
        })
        metadata = {
            "task_id": task_id,
            "split": "dev",
            "repo_url": lean.MATHLIB_REPO_URL,
            "repo_commit": lean.MATHLIB_COMMIT,
            "file_path": f"Mathlib/Example{index}.lean",
            "full_name": f"Example.theorem_{index}",
            "source_sha256": f"{index:064x}",
            "trace_sha256": f"{index + 1:064x}",
            "theorem_statement": f"theorem theorem_{index} : True :=",
            "start": [1, 1],
            "end": [1, 38],
            "proof_start": [1, 34],
            "proof_end": [1, 38],
            "reference_origin": "exact_official_source_declaration",
            "reference_proof": "by exact True.intro",
        }
        private.append({
            "task_id": task_id,
            "split": "dev",
            "content_sha256": metadata_digest(metadata),
            "metadata": metadata,
        })
    return public, private


class Runner:
    def __init__(self, fail_after=None):
        self.calls = 0
        self.fail_after = fail_after
        self.identity = {
            "model_id": "google/gemma-2-2b-it",
            "model_revision": "299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8",
            "tokenizer_revision": "299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8",
            "dtype": "float16",
            "device": "cuda",
        }

    def generate(self, task, seed, remaining, *, capture=True):
        if self.fail_after is not None and self.calls >= self.fail_after:
            raise KeyboardInterrupt
        self.calls += 1
        candidate = self.calls % 4
        return {
            "text": f"by exact True.intro -- {candidate}",
            "input_ids": [2, 10, 11],
            "output_ids": [20, candidate],
            "prompt_sha256": "a" * 64,
            "sum_logp": -1.0,
            "mean_logp": -0.5,
            "token_logps": [-0.4, -0.6],
            "generation_s": 0.1,
            "extraction_s": 0.2,
            "elapsed_s": 0.3,
            "deadline_exceeded": False,
            "seed": seed,
            "answer_start": 0,
            "answer_end": 2,
            "activations": np.full((2, 4, 3), candidate, dtype=np.float16),
            "prompt_boundary": np.full((4, 3), -1, dtype=np.float16),
        }


class Verifier:
    identity = {
        "backend": "trusted-test-comparator",
        "revision": "b" * 40,
        "benchmark_doi": lean.BENCHMARK_DOI,
        "cache_sha256": "c" * 64,
    }

    def __init__(self, infrastructure_at=None):
        self.calls = 0
        self.infrastructure_at = infrastructure_at

    def verify(self, task, proof, timeout_s):
        self.calls += 1
        lean._validated_task(task)
        if self.infrastructure_at == self.calls:
            return {"status": "infrastructure_error", "elapsed_s": 0.01}
        # Two valid and two invalid candidates for every development task.
        return {"status": "valid" if self.calls % 4 in (1, 2) else "invalid",
                "elapsed_s": 0.01}


def request():
    return {
        "study_id": "vrm-v1",
        "smoke_gpu_budget_s": 3600,
        "candidates_per_task": 4,
    }


def test_complete_smoke_is_atomic_hashed_and_activation_external(tmp_path):
    public, private = tasks()
    runner, verifier = Runner(), Verifier()
    result = run_development_smoke(
        public, private, runner, verifier, tmp_path, request=request())

    assert result["status"] == "completed"
    assert result["feasibility"]["passed"] is True
    assert result["feasibility"]["counts"] == {"valid": 64, "invalid": 64}
    assert result["feasibility"]["mixed_tasks"] == 32
    assert runner.calls == verifier.calls == 128
    assert json.loads((tmp_path / "summary.json").read_text()) == result

    candidate_dir = tmp_path / "candidates" / "dev-00-000"
    receipt = json.loads((candidate_dir / "receipt.json").read_text())
    assert "activations" not in json.dumps(receipt)
    assert receipt["request"]["task_sha256"]
    assert receipt["request"]["verifier_metadata_sha256"]
    assert receipt["payload"]["activation_sha256"]
    arrays = np.load(candidate_dir / "activations.npz")
    assert arrays["activations"].shape == (2, 4, 3)
    assert arrays["prompt_boundary"].shape == (4, 3)


def test_interruption_resumes_only_missing_candidates(tmp_path):
    public, private = tasks()
    with pytest.raises(KeyboardInterrupt):
        run_development_smoke(
            public, private, Runner(fail_after=5), Verifier(), tmp_path,
            request=request())
    assert len(list((tmp_path / "candidates").iterdir())) == 5

    runner, verifier = Runner(), Verifier()
    result = run_development_smoke(
        public, private, runner, verifier, tmp_path, request=request())
    assert result["status"] == "completed"
    assert runner.calls == verifier.calls == 123

    runner = Runner()
    run_development_smoke(public, private, runner, Verifier(), tmp_path,
                          request=request())
    assert runner.calls == 0


def test_corrupt_resume_artifact_fails_closed(tmp_path):
    public, private = tasks()
    run_development_smoke(public, private, Runner(), Verifier(), tmp_path,
                          request=request())
    path = tmp_path / "candidates" / "dev-00-000" / "activations.npz"
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="activation checksum"):
        run_development_smoke(public, private, Runner(), Verifier(), tmp_path,
                              request=request())


def test_infrastructure_error_stops_without_feasibility_claim(tmp_path):
    public, private = tasks()
    result = run_development_smoke(
        public, private, Runner(), Verifier(infrastructure_at=3), tmp_path,
        request=request())
    assert result["status"] == "infrastructure_error"
    assert result["feasibility"] is None
    assert result["completed_candidates"] == 2
    assert result["failed_attempts"] == 1
    assert json.loads((tmp_path / "summary.json").read_text()) == result


def test_infrastructure_failure_is_preserved_and_retried_on_resume(tmp_path):
    public, private = tasks()
    first = run_development_smoke(
        public, private, Runner(), Verifier(infrastructure_at=3), tmp_path,
        request=request())
    assert first["status"] == "infrastructure_error"

    runner, verifier = Runner(), Verifier()
    completed = run_development_smoke(
        public, private, runner, verifier, tmp_path, request=request())
    assert completed["status"] == "completed"
    assert completed["completed_candidates"] == 128
    assert completed["failed_attempts"] == 1
    assert runner.calls == verifier.calls == 126
    assert len(list((tmp_path / "failed_candidates" / "dev-00-002").iterdir())) == 1
    assert json.loads((tmp_path / "summary.json").read_text()) == completed


def test_verification_never_starts_after_generation_consumes_budget(tmp_path):
    public, private = tasks()
    runner = Runner()

    class MustNotVerify(Verifier):
        def verify(self, *args, **kwargs):
            raise AssertionError("verification started after budget exhaustion")

    result = run_development_smoke(
        public, private, runner, MustNotVerify(), tmp_path,
        request={**request(), "smoke_gpu_budget_s": 0.2})
    assert result["status"] == "budget_exhausted"
    assert result["completed_candidates"] == 0


@pytest.mark.parametrize("problem", ["count", "split", "private", "duplicate"])
def test_smoke_rejects_wrong_development_population_before_generation(tmp_path, problem):
    public, private = tasks()
    if problem == "count":
        public.pop()
    elif problem == "split":
        public[0]["split"] = "train"
    elif problem == "private":
        private.pop()
    else:
        public[1]["task_id"] = public[0]["task_id"]
    runner = Runner()
    with pytest.raises(ValueError):
        run_development_smoke(public, private, runner, Verifier(), tmp_path,
                              request=request())
    assert runner.calls == 0


def test_smoke_rejects_modified_private_metadata_before_generation(tmp_path):
    public, private = tasks()
    private[0]["metadata"]["theorem_statement"] = "theorem changed : False :="
    runner = Runner()
    with pytest.raises(ValueError, match="content hash"):
        run_development_smoke(public, private, runner, Verifier(), tmp_path,
                              request=request())
    assert runner.calls == 0


def test_request_change_cannot_reuse_prior_smoke(tmp_path):
    public, private = tasks()
    run_development_smoke(public, private, Runner(), Verifier(), tmp_path,
                          request=request())
    changed = {**request(), "study_id": "changed"}
    with pytest.raises(ValueError, match="run request"):
        run_development_smoke(public, private, Runner(), Verifier(), tmp_path,
                              request=changed)
