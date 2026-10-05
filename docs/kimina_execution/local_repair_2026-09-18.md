# Local repair and inference-contract audit

Stage A of [the recovery plan](download_analysis_and_next_steps_2026-09-18.md).
Scope: local implementation and checks only. No pretrained model inference,
new Colab run, changed prompt condition, training, commit or push.

## Completed changes

- Generation now uses one monotonic session deadline that charges checkpoint
  and Python overhead, not only the runner's narrower timing fields.
- A 180-second persistence reserve is held inside the existing allowance.
  This is an engineering margin informed by the observed replay/storage/backup
  costs, not a proven worst-case bound or an added allowance. It must be checked
  on real Colab before scaling. If saving unexpectedly overruns, raw evidence
  is retained and the overrun is reported; no next sample is admitted.
- Load duration is sampled once rather than twice at different boundaries.
- Large unchanged NPZ files are hash-verified once per process between full
  checks. A cache hit requires identical source and destination metadata.
  Fresh processes, changed files and finalization perform full SHA-256 checks.
  This is a single-writer optimization, not protection against an adversary
  able to forge filesystem metadata. No global/persistent trust cache is used.
- The final full backup happens before the terminal cost snapshot. A new
  immutable `finalization.json` binds `summary.json` and includes summary
  publication/backup time. Generation return values, verification and the
  format-repair handoff consume this final cost record consistently.
- Publication of the terminal cost receipt itself and external export/idle time
  remain explicitly excluded. The result says `within_recorded_scope`, not
  complete end-to-end cost compliance. An outer Colab/export receipt is still
  needed to account for those final operations in a real run.
- Stored-attempt counts, EOS/length/timeout counts, extractable proof counts and
  verification status are separate. A timeout is visible even if every requested
  attempt was saved. Extractability is never reported as Lean validity.
- A completed resume verifies immutable artifacts and does not load the model.
  A missing final cost receipt or interrupted session requires explicit cost
  review rather than silently discarding elapsed time or resampling.

Old source archives, downloaded results, sampling settings, model pins, token
limits, full-token/all-layer activation capture and verifier safety are unchanged.
The changed source identity deliberately prevents attaching new execution to
old receipts as though it were the same software condition. Historical receipts
remain readable using their archived code; they are not rewritten or invalidated.

## Verification

The first regression run reproduced seven newly tested defects:
`7 failed, 343 passed, 7 skipped`. The final direct local run passed:
**352 passed, 7 skipped in 19.93 seconds**. Unlazy reruns are recorded separately
in [GATES.md](GATES.md), E12 and E2. Skipped integration tests are not claimed
as passed. The pinned top-level packages were restored in a Python 3.12 virtual
environment; [environment and file hashes](local_repair_environment_2026-09-18.json)
record the exact repaired files and installed top-level versions.

Tests cover backup corruption, final backup accounting, reserve exhaustion,
unexpected storage overrun, interruption, immutable resume, unresolved output
status and identical repair-request cost propagation. A small randomly
initialized Qwen3 architecture also produces identical sampled token sequences
with and without the probability collector; teacher-forced log probabilities
agree. This is a local CPU software test, not pretrained Kimina/T4 equivalence.

## Real tokenizer audit

Using the public tokenizer files at Kimina revision
`1dfd2228afcc35b16eb008a81dfc2b2707750f78`, all four downloaded prompts reproduce
the saved input token IDs exactly. Rendering then tokenizing with no additional
special tokens gives the same IDs. Decoding saved output IDs reproduces the
stored raw text exactly. None of the four ends in a configured EOS token.

The tokenizer has no BOS token. Its EOS is 151645 and padding is 151643; the
generation configuration permits both as stopping IDs. The existing generation
implementation already uses those pinned stopping IDs and the expected sampling
settings. There is no evidence of the former Gemma-style double-BOS problem in
this run, and no tokenizer fix was justified.

Evidence: [tokenizer audit](tokenizer_audit_2026-09-18.json) and
[audit script](audit_downloaded_tokenizer.py). The script requires the pinned
tokenizer files under `/private/tmp/kimina-tokenizer-audit/` and the original
download folders. It does not download weights or run inference.

## Remaining decision

We have repaired demonstrated local workflow defects, not the model's tendency
to loop on these prompts. Real-checkpoint generation/instrumentation equivalence,
prompt suitability, task suitability and new Drive timing remain unresolved.
The four old attempts still provide no valid/invalid proof labels and no H1-H3
result. Do not change that conclusion because software tests pass.

Next: obtain a separate free-Colab allowance, freeze one small diagnostic
request, and run the staged sanity/context test from the recovery plan. Record
the new allowance explicitly alongside prior spending; do not reset history.
A change to prompt conditions or cumulative budget validation needs its own
documented amendment. Do not launch training or the protected study yet.
