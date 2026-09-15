# Goal: repair readiness, do not start the study

Work in `/Users/friedrichreichelt/Documents/verified-reasoning-monitoring`.

This is a bounded engineering and protocol-readiness goal, not authorization
to execute the research. Preserve the existing implementation, corpus, splits,
runtime amendments and completed repairs. Do not start Gemma generation,
activation collection, the 32-by-4 smoke, monitor fitting, validation selection
or protected evaluation. Do not commit or push without explicit authorization.

## Research objective to preserve

Determine whether internal activation monitors select completed Lean proof
candidates that yield more externally verified correct task solutions under
the same measured end-to-end time budget than token-likelihood ranking,
text-based ranking and direct checking.

Preserve H1 (prediction), H2 (added value of full Three-Reader) and H3
(practical equal-budget utility). Decodability alone does not establish H3.
Do not add steering, adaptive generation, circuit tracing, SAEs, model training
or online-detection claims to the current study.

## Read the current evidence first

Check Git identity and outstanding changes. Read `docs/status.md`,
`docs/verifier_timing_repair_2026-09-15.md`, `docs/research_plan.md`,
`configs/study.json`, and approved runtime amendments. Use the latest verified
receipts; do not recreate an older checkout or repeat already completed work.
The September 15 repair fixes time accounting. It does not demonstrate that
a complete secure verification fits five seconds.

## Four bounded steps

1. **Measure, do not guess.** Reuse the September 15 phase profile and timing
   controls when code and runtime are unchanged. If a specific uncertainty
   remains, use only known development fixtures with valid provenance, never
   natural model candidates or protected tasks in this repair phase. Record
   cold/preloaded state, CPU limit, memory, worker source hash, image/tool/cache
   identity, startup, checking, diagnostic and cleanup costs. Instrumented
   timings are diagnostic, not production benchmarks. Do not estimate a p95
   from one proof or claim a causal speedup from one sequential CPU comparison.
2. **Make the smallest demonstrated repair.** Write a failing regression test
   first. Maintain one absolute verification deadline, including transport,
   candidate preparation and any required reference diagnostic. Do not restore
   the former 600-second worker grace or a separate 180-second diagnostic budget.
   Verify the scheduler independently rejects a late per-check success even
   when task time remains. Preserve isolation, source checks, statement/axiom
   validation and kernel replay. Do not remove safety checks to meet the cap.
   Avoid a new daemon, verifier rewrite, corpus rebuild or image rebuild unless
   a measured bottleneck makes that specific change necessary.
3. **Check the whole budget, not just one number.** Five seconds per check and
   30 seconds per task remain the current approved values, not immutable laws.
   If they are impractical, prepare a dated pre-outcome amendment proposal,
   not a silent configuration change. Cover the per-check limit, per-task
   limit, smoke accounting, total GPU allocation, CPU time, transfer costs and
   the full/reduced-study projection together. State which generation costs
   are not yet measured because this phase prohibits model execution. Do not
   infer complete-study feasibility from verifier-only timings. A later,
   separately authorized development measurement may be necessary before final
   numbers can be frozen. No broad budget sweep or tuning on hypothesis results.
4. **Verify, document, then stop for a decision.** Run affected tests, then the
   full pinned Python 3.12 suite once for the final code state. Run bounded real
   known-valid, known-invalid and timeout controls. Reuse unchanged security
   evidence; rerun affected isolation/provenance tests if their implementation
   changes. Preserve raw receipts, scripts and hashes. Update status with
   completed repairs, measured limitations and the exact remaining decision.

## Non-negotiable accounting and evidence rules

- Preflight and model/runtime loading belong before timed evaluation and are
  reported separately. A timed controller must use a successfully preflighted
  backend; do not hide lazy setup inside a check.
- Abort proof work at the verification deadline. Cleanup is mandatory and may
  take additional wall time; record and charge it. Never call the entire return
  latency exactly five seconds when cleanup makes it longer. Unconfirmed
  cleanup is an infrastructure failure, not successful verification.
- Keep `valid`, `invalid`, `timeout` and `infrastructure_error` distinct.
  Reference-diagnostic timeout cannot establish that a candidate is invalid.
  A late verdict is not a within-budget success. No failed/missing row disappears.
- Known reference proofs used as infrastructure fixtures stay verifier-private.
  They are not generated candidates and never count toward the smoke yield.
- No weakening the >=20 valid, >=20 invalid and >=8 mixed-task smoke gate.
  No protected outputs, labels, rankings or effects may be inspected here.
- Preserve single chat-template/BOS application, public/private metadata
  separation, hashes, atomic persistence and exact resume identities.
- Preserve actual equal end-to-end charging for all methods. Include generation,
  required activations, scoring, transfers, checking and cleanup. Do not charge
  non-internal baselines for activations they do not need.
- A manual Colab download followed by local verification is not a prospective
  30-second system. Document a feasible execution placement and transfer policy
  before claiming H3 readiness; do not reopen the rejected native Colab Landlock
  path or claim offline replay as a measured prospective result.
- Preserve the approved free-compute limits. GPU allocation includes idle time
  while a GPU remains attached; CPU-only time is separately reported. Do not
  silently reinterpret the one-hour smoke budget to make an overrun disappear.
- A budget amendment is legitimate before outcomes, but needs explicit approval
  and consistent protocol/configuration/call-site/test changes before use.
  Retain old evidence; do not overwrite it as though the old plan passed.

## Execution discipline

Use the existing pinned Python environment and existing tools. Apply the
Karpathy guidelines: state assumptions, test failures, make scoped repairs,
verify results. Prefer one implementer. Use GPT-5.6 Sol for routine work only
when tool-visible delegation is available; reserve the higher-capability audit
for the combined budget/provenance review. Record actual model use, not an
imagined delegation. Ask only for a concrete missing decision or authorization.

## Completion of this repair goal

Deliver the reviewed code changes, test results, real timing receipts, an
evidence-based budget recommendation (or explicit remaining measurement gap),
and a short readiness report with `ready`, `pending_budget_approval`, or a
specific operational blocker. Completion of this repair report does not mean
the scientific study is complete or cleared to run.

Stop here. Request explicit approval for any proposed budget/runtime amendment
and for the next execution phase. A later study-execution goal must incorporate
the approved amendment and existing H1-H3 analysis/selection rules. Never resume
an old end-to-end goal automatically past this repair-only boundary.
