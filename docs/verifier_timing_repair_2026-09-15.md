# Verifier timing repair, September 15

**Status: time-accounting defects repaired; study execution remains paused.**
No Gemma candidates, activations, smoke outcomes or protected results were
generated. No study budget, corpus, model or scientific threshold was changed.
This is an infrastructure report, not a test of H1-H3.

## What was wrong

The five-second argument previously limited the Comparator subprocess rather
than the complete check. The host transport additionally allowed 600 seconds,
and a rejected candidate could trigger a separate 180-second reference audit.
The scheduler checked the total task deadline but did not independently reject
a successful verdict that exceeded its individual five-second allowance.
Thus a five-second request was not a five-second end-to-end contract. Treating
this only as slow hardware would have missed a real implementation defect.

## What changed

- Verification now uses one absolute host deadline, without worker grace.
- Preparation, the candidate check and any reference diagnostic share time.
- Native verification receives the host deadline; Docker work is stopped by
  the host transport deadline. Required process/container cleanup still occurs.
- A late valid or invalid verdict becomes an unresolved timeout, not a scientific
  validity label. A reference-audit timeout does not establish invalidity.
- The scheduler independently checks both per-check and per-task budgets and
  records `within_verification_budget` and `verification_budget_s`.
- Seven new regression cases cover the demonstrated faults and shared deadline.

The changes do not bypass Comparator, kernel replay, statement/axiom checks,
source provenance, Landrun, seccomp, non-root operation or read-only mounts.
Preflight must be completed outside timed execution. Automatic preflight is a
convenience for untimed use, not permission to hide setup inside H3.

## Measurements

All controls use the already known development theorem `Nat.abundant_twelve`,
the pinned image/cache and `by decide` (or the known invalid `by contradiction`).
Long diagnostic limits here are not adopted study budgets.

| Control | Measured wall time | Result |
|---|---:|---|
| Original code, phase instrumentation, 1 CPU, 180s diagnostic limit | 163.171s | Valid |
| Repaired code, no instrumentation, 1 CPU, 180s diagnostic limit | 53.796s | Valid |
| Repaired code, no instrumentation, 2 CPUs, 180s diagnostic limit | 35.539s | Valid |
| Repaired code, 1 CPU, actual 5s allowance | 6.415s including termination/cleanup | Timeout |
| Repaired code, known invalid, 1 CPU, shared 180s diagnostic limit | 86.079s | Invalid |

The old 40.53-second control remains in the September 14 evidence. Do not
replace it with today's result or describe either number as a universal Lean
latency. The instrumented run is not a fair speed comparison with the later
warm, uninstrumented runs. CPU counts were tested sequentially only once, so
the 2-CPU observation does not establish a stable causal speedup or a percentile.
The production CPU limit remains unchanged at one CPU.

In the phase profile, Python setup before Comparator took about 3.53 seconds;
audit-project construction itself took 0.022 seconds. Comparator took 155.77
seconds. Sampled child processes and build logs locate the large costs in Lake
initialization, two module builds and two exports, followed by kernel checking.
This argues against spending time on a new Python daemon to chase an order-of-
magnitude speedup. Removing the actual proof checks would change the guarantee.

## Verification and reproducibility

Pinned Python 3.12 suite: **198 passed, 7 skipped**. The skipped tests are the
opt-in real security suite, not silently counted as new passing runtime tests.
Known-valid, known-invalid and timeout controls were run separately above.
The other unchanged security controls retain their September 14 acceptance;
that historical acceptance is not evidence of five-second feasibility.

Raw profile, timing controls and the diagnostic scripts are retained under
`protocol/evidence/verifier-timing-2026-09-15/`. Each timing record identifies
the worker source hash and runtime. The profile used the pre-repair worker;
the uninstrumented controls used the repaired worker. Scripts refer to the
documented local cache/fixture paths and require the pinned Python environment
and accepted local Docker image. They are infrastructure tools, not study CLI
commands. Never use their reference proofs as model-generated observations.

## Budget recommendation, not an approved amendment

Do not retain five seconds as though it were demonstrated feasible, and do not
just substitute 40 seconds: today's valid control exceeded that on one CPU,
and the rejected candidate needed 86 seconds including its reference audit.

The next decision must cover the complete schedule. Before choosing final
numbers, use a small fixed representative set of known development fixtures
on the intended runtime, without looking at model outcomes. Then combine those
measurements with generation/transfer measurements from a separately authorized
development integration step. Check whether pair generation plus verification
fits a meaningful task budget and whether the complete smoke/study fits its
resource caps. Do not infer those costs from the one theorem measured here.

A larger per-check limit and corresponding task budget can be scientifically
legitimate through a dated pre-outcome amendment, applied equally to every
method. No exact new limit is approved or implemented by this report. The
one-hour smoke interpretation and twelve GPU-hour allocation cap must also be
checked; a local CPU verifier does not make GPU idle time free.

If no affordable meaningful schedule fits, report that resource limitation,
not a negative H1-H3 result. Preserve the corpus and working infrastructure.
There is no reason to restart them.

For the repair-only handoff, use [the proposed goal](verifier_repair_goal.md).
