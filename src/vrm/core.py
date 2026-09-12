"""Small provenance and analysis helpers; no historical-study dependencies."""

import hashlib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, key):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
            raise ValueError("artifact key must be a simple identifier")
        return self.root / f"{key}.json"

    def read(self, key, request):
        path = self.path(key)
        if not path.exists():
            return None
        envelope = json.loads(path.read_text())
        if envelope["request_sha256"] != digest(request):
            raise ValueError("artifact request mismatch; use a separate run directory")
        if envelope["payload_sha256"] != digest(envelope["payload"]):
            raise ValueError("artifact checksum mismatch")
        return envelope["payload"]

    def write(self, key, request, payload):
        path = self.path(key)
        existing = self.read(key, request)
        if existing is not None:
            if existing != payload:
                raise ValueError("completed artifacts are immutable")
            return path
        envelope = dict(request=request, request_sha256=digest(request),
                        payload=payload, payload_sha256=digest(payload))
        fd, name = tempfile.mkstemp(dir=self.root, prefix=".partial-")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(canonical(envelope))
                handle.flush()
                os.fsync(handle.fileno())
            # Atomic no-clobber publication. A concurrent writer cannot overwrite.
            try:
                os.link(name, path)
            except FileExistsError:
                if self.read(key, request) != payload:
                    raise ValueError("completed artifacts are immutable") from None
        finally:
            os.unlink(name)
        return path


def feasibility(rows):
    if any(row["split"] != "dev" for row in rows):
        raise ValueError("feasibility may use development data only")
    groups = defaultdict(list)
    for row in rows:
        groups[row["task_id"]].append(row["status"])
    counts = Counter(row["status"] for row in rows)
    mixed = sum("valid" in s and "invalid" in s for s in groups.values())
    complete = len(groups) == 32 and all(len(s) == 4 for s in groups.values())
    passed = (complete and counts["valid"] >= 20 and counts["invalid"] >= 20
              and mixed >= 8 and not counts["infrastructure_error"])
    return dict(passed=bool(passed), complete=complete, counts=dict(counts),
                mixed_tasks=mixed, n_tasks=len(groups), empirical=bool(rows))


def paired_effect(treatment, baseline, draws=10_000, seed=11):
    if not treatment or treatment.keys() != baseline.keys():
        raise ValueError("paired comparison requires the same tasks, nonempty")
    if any(type(x) is not bool for x in [*treatment.values(), *baseline.values()]):
        raise ValueError("outcomes must be explicit boolean verification successes")
    ids = sorted(treatment)
    differences = np.array([int(treatment[k]) - int(baseline[k]) for k in ids])
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(differences, len(ids), replace=True).mean()
                      for _ in range(draws)])
    return dict(n_tasks=len(ids), difference=float(differences.mean()),
                ci95=[float(x) for x in np.quantile(means, [.025, .975])],
                draws=draws, seed=seed)


def select_champions(scores):
    if not scores or any(s["split"] != "validation" for s in scores):
        raise ValueError("selection is validation-only")
    if any(not np.isfinite(s["loss"]) for s in scores):
        raise ValueError("nonfinite selection metric")
    result = {}
    for key, internal in (("internal", True), ("external", False)):
        candidates = [s for s in scores if s["internal"] == internal]
        if not candidates:
            raise ValueError(f"missing {key} candidates")
        result[key] = min(candidates, key=lambda x: (x["loss"], x["name"]))["name"]
    return result
