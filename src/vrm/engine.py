"""Prospective wall-clock experiment. Replay must not be labeled prospective."""

import math
import time

from vrm.core import digest


def candidate_seed(task_id, index):
    return int(digest(["candidate-v1", task_id, index])[:8], 16)


def run_task(task, mode, generate, verify, score, *, budget_s=30.,
             max_candidates=8, clock=time.monotonic):
    if mode not in ("direct", "ranked") or budget_s <= 0:
        raise ValueError("invalid mode or budget")
    start = clock()
    deadline = start + budget_s
    receipts, candidates = [], []
    solved = False
    infrastructure_error = False
    while len(candidates) < max_candidates and clock() < deadline:
        group = []
        for _ in range(1 if mode == "direct" else 2):
            if len(candidates) >= max_candidates or clock() >= deadline:
                break
            index = len(candidates)
            seed = candidate_seed(task["task_id"], index)
            before = clock()
            candidate = generate(task, seed, deadline - before)
            elapsed = clock() - before
            candidate = {**candidate, "candidate_index": index, "seed": seed}
            candidates.append(candidate)
            receipts.append(dict(event="generation", candidate_index=index,
                                 elapsed_s=elapsed, within_budget=clock() <= deadline))
            if clock() >= deadline:
                break
            before = clock()
            value = float(score(candidate)) if mode == "ranked" else 0.
            if not math.isfinite(value):
                raise ValueError("monitor returned nonfinite score")
            receipts.append(dict(event="scoring", candidate_index=index,
                                 elapsed_s=clock()-before, within_budget=clock() <= deadline))
            group.append((value, index, candidate))
        for _, index, candidate in sorted(group, key=lambda x: (-x[0], x[1])):
            remaining = deadline - clock()
            if remaining <= 0:
                break
            before = clock()
            result = verify(task, candidate["text"], timeout_s=min(5., remaining))
            if result["status"] not in ("valid", "invalid", "timeout", "infrastructure_error"):
                raise ValueError("unrecognized verifier result")
            within = clock() <= deadline
            receipts.append(dict(event="verification", candidate_index=index,
                                 result=result, elapsed_s=clock()-before, within_budget=within))
            if result["status"] == "infrastructure_error":
                infrastructure_error = True
                break
            if result["status"] == "valid" and within:
                solved = True
                break
        if solved or infrastructure_error:
            break
    # Activation arrays are persisted by the caller, not duplicated into JSON.
    public_candidates = [{k: v for k, v in c.items() if k != "activations"}
                         for c in candidates]
    return dict(task_id=task["task_id"], mode=mode, budget_s=budget_s,
                elapsed_s=clock()-start, solved=solved, evaluable=not infrastructure_error,
                status="infrastructure_error" if infrastructure_error else "completed",
                candidates=public_candidates, receipts=receipts, prospective=True)
