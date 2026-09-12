import json
from pathlib import Path

import pytest

from vrm.core import Store, digest, feasibility, paired_effect, select_champions
from vrm.engine import run_task


def test_store_bound_to_request_and_detects_corruption(tmp_path):
    store = Store(tmp_path)
    request = {"model": "fixed", "task_id": "a"}
    store.write("run", request, {"answer": "x"})
    assert store.read("run", request) == {"answer": "x"}
    with pytest.raises(ValueError, match="request"):
        store.read("run", {"model": "changed"})
    path = tmp_path / "run.json"
    data = json.loads(path.read_text())
    data["payload"]["answer"] = "changed"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="checksum"):
        store.read("run", request)


def test_store_cannot_overwrite_completed_run(tmp_path):
    store = Store(tmp_path)
    store.write("run", {}, {"answer": 1})
    with pytest.raises(ValueError, match="immutable"):
        store.write("run", {}, {"answer": 2})
    with pytest.raises(ValueError):
        store.write("../escape", {}, {})


def test_feasibility_requires_real_complete_development_population():
    rows = [dict(task_id=str(i), split="dev", status="valid" if j % 2 else "invalid")
            for i in range(32) for j in range(4)]
    assert feasibility(rows)["passed"]
    assert not feasibility(rows[:-1])["passed"]
    rows[0]["split"] = "test_id"
    with pytest.raises(ValueError, match="development"):
        feasibility(rows)


def test_paired_effect_uses_tasks_and_rejects_missing_pairs():
    result = paired_effect({"a": True, "b": False}, {"a": False, "b": False}, draws=100)
    assert result["difference"] == 0.5
    assert result["n_tasks"] == 2
    with pytest.raises(ValueError, match="same tasks"):
        paired_effect({"a": True}, {"b": True})


def test_selection_is_validation_only_and_deterministic():
    scores = [dict(name="static", internal=True, loss=.5, split="validation"),
              dict(name="text", internal=False, loss=.6, split="validation")]
    assert select_champions(scores) == {"internal": "static", "external": "text"}
    scores[0]["split"] = "test_id"
    with pytest.raises(ValueError, match="validation"):
        select_champions(scores)


class Clock:
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t


def components(clock, generation=2., verification=1., scoring=0.):
    seeds = []
    def generate(task, seed, remaining):
        seeds.append(seed)
        clock.t += generation
        return {"text": "proof", "index": len(seeds) - 1}
    def verify(task, text, timeout_s):
        clock.t += verification
        return {"status": "valid", "elapsed_s": verification}
    def score(candidate):
        clock.t += scoring
        return float(candidate["index"])
    return generate, verify, score, seeds


def test_generation_scoring_verification_all_charge_budget():
    clock = Clock()
    gen, verify, score, _ = components(clock, scoring=2.)
    result = run_task({"task_id": "a"}, "ranked", gen, verify, score, budget_s=7, clock=clock)
    assert not result["solved"]
    assert result["elapsed_s"] >= 7
    assert result["mode"] == "ranked"


def test_late_verification_never_counts_as_success():
    clock = Clock()
    gen, verify, score, _ = components(clock, generation=2, verification=5)
    result = run_task({"task_id": "a"}, "direct", gen, verify, score, budget_s=3, clock=clock)
    assert not result["solved"]
    assert result["receipts"][-1]["within_budget"] is False


def test_ranked_checks_best_first_and_uses_same_candidate_seeds():
    clock = Clock()
    gen, verify, score, seeds = components(clock)
    result = run_task({"task_id": "a"}, "ranked", gen, verify, score, clock=clock)
    assert result["solved"]
    assert result["receipts"][-1]["candidate_index"] == 1
    clock2 = Clock()
    gen2, ver2, sc2, seeds2 = components(clock2)
    run_task({"task_id": "a"}, "direct", gen2, ver2, sc2, clock=clock2)
    assert seeds[0] == seeds2[0]


def test_infrastructure_failure_not_scientific_failure():
    clock = Clock()
    gen, _, score, _ = components(clock)
    result = run_task({"task_id": "a"}, "direct", gen,
                      lambda *a, **kw: {"status": "infrastructure_error"}, score, clock=clock)
    assert result["status"] == "infrastructure_error"
    assert not result["evaluable"]


def test_digest_has_no_nan_or_order_dependency():
    assert digest({"x": 1, "y": 2}) == digest({"y": 2, "x": 1})
    with pytest.raises(ValueError): digest({"x": float("nan")})
