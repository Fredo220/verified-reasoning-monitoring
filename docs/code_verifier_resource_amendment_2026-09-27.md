# Verifier resource amendment (2026-09-27)

This amendment was written after 122 protected training verdicts had been
stored, before validation labels or test candidates were opened. It does not
change the frozen population, generation, model, metrics or selection rule.

The pinned EvalPlus verifier could not produce ground truth for `Mbpp/255` in
the isolated container. Its plus tests include a combinations-with-repetition
case with 1,663,740 output tuples of length 77. The original 256-MB `/work`
tmpfs produced `ENOSPC` during ground-truth serialization. A diagnostic retry
with a 1-GB tmpfs and the same 2-GB container memory cap exited 137. These
are verifier resource failures, not evidence that a model solution is wrong.
The larger tmpfs is retained because it may let less extreme tasks finish; the
CPU, memory, network, read-only filesystem, seccomp and worker restrictions
remain unchanged. The verifier image, source, worker and seccomp hashes are
unchanged. Completed verdicts are never rewritten.

Before validation or test evaluation, the following uniform rule is fixed:

1. An isolated container exit 137, `ENOSPC`, or outer wall timeout is recorded
   as `infra_error` with a bounded resource reason. All other unexpected
   container failures still stop the run. `infra_error` is never a fail label.
2. Every registered candidate retains a checksum-bound receipt and verdict.
   Candidates from a task with at least one `infra_error` are excluded **as
   one whole task** from train, validation and test ranking/calibration, even
   if other candidates from that task received labels. The task and all its
   statuses remain in the inventory and attrition report.
3. Do not replace those tasks or generate extra samples. The existing minimum
   of 12 mixed test tasks still applies after exclusions. Report the number
   of excluded tasks per split and bound conclusions to the verifiable subset.

The rule is an operational missing-data policy, not a way to improve a score.
Because resource-heavy tasks may be systematically harder, the resulting
subset is not claimed representative of all MBPP+ tasks. A large attrition
rate can make the scientific comparison inconclusive even if the code runs.

## Empty plus-test normalization correction

Later in the same verifier pass, all three train shards stopped at
`Mbpp/793`. The sandboxed raw EvalPlus result for one candidate was
`base=fail` with three test details and `plus=pass` with zero details. The
pinned source has exactly zero plus inputs for that task. The original
normalizer incorrectly required a nonempty detail list even when no tests
existed. Validation verification had completed by the time this case was
diagnosed; its aggregate status counts were viewed, but no validation model
selection or test generation had occurred.

The correction accepts an empty `pass` detail list only after matching it to
a zero input count in the pinned, checksum-checked source. An empty list for a
nonempty test set remains an infrastructure failure. The same code applies to
all splits; source, tests, sandbox worker, image and frozen endpoints remain
unchanged. A sandbox replay of the affected candidate established the raw
status/lengths, and the correction was test-first (`25 passed` in the focused
suite). The complete suite subsequently passed (`480 passed, 7 skipped`).
Unsharded coverage checks returned `580/580` train and `260/260` validation
with zero missing verdicts before selection.

Final code identity at the train/validation selection boundary:

| File | SHA-256 |
| --- | --- |
| `src/vrm/code_cli.py` | `400503edba47603687d6e87b590e562e6c55e794253e04f8a841395173b03794` |
| `src/vrm/code_verify.py` | `964e5830a9fb371d45b0c0064ca3274aacd0dae3409e2777ef0965c28c1f6721` |
| `src/vrm/code_verify_batch.py` | `a5e6c5e7555ef24c7d58843b733942c688ec63663e349fc990c859831fa709f7` |
| `src/vrm/code_verdicts.py` | `65d9f2f65dbdc97a1f1e0a48423ec6e5d32d8d6dbd13950176ab433884999491` |
| `src/vrm/code_study.py` | `d80db201a2676204e2fe30ee554139793c578d7e203735f3998053c801b752d0` |
| `src/vrm/code_selection.py` | `97d1f0d1ce07362ea32a0912812acde86f576022acbd0eff9cc0d2751938e3ad` |
| `src/vrm/code_study_cli.py` | `db9fcd179d5be6aa1414fe4ce9cf5785550ed062b13511185f4ef12b816ab3c6` |
| `configs/code_monitoring.json` | `cf0fc1bbc959460d7685a79f4cc5945c4fb746007b72c777fcca9dc0a0aa1335` |
