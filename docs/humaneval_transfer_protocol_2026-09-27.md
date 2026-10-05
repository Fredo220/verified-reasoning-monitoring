# HumanEval+ transfer check for multi-signal monitoring

Registered 2026-09-27 before any HumanEval+ model candidate or verifier verdict
was generated. This is a **new** follow-up. The original MBPP+ result remains
unchanged. The MBPP+ validation set was already opened while developing this
follow-up, so the present test is needed for any independent transfer claim.

## Frozen source and task allocation

- Source: official EvalPlus HumanEval+ `v0.1.10` JSONL gzip, downloaded from
  the `humanevalplus_release` GitHub release. Compressed SHA-256:
  `272720b90ac375502c8ed23cd791c2a93dfb22a911641a494da74a426c09f101`.
  It contains 164 unique `HumanEval/*` tasks. EvalPlus implementation is
  pinned to tag `v0.3.1` at commit
  `e5d0ed0bab96280b60b637ec7f15b5e4841b0cb2`.
- Sort task IDs by SHA-256 of `vrm-humaneval-transfer-v1\0{task_id}`. First
  eight are open development; next 80 are a one-use test; remaining 76 are
  reserve and will not be evaluated in this study. No filtering by outcome.
- The public model handoff contains only `task_id` and the source `prompt`
  (function signature and docstring). `canonical_solution`, `test`,
  `base_input`, `plus_input`, `contract` and `entry_point` stay verifier-side.
  Hash the public prompts and source separately.

## Frozen generator and verification

- Generator: `Qwen/Qwen2.5-Coder-1.5B-Instruct` commit
  `2e1fd397ee46e1388853d2af2c993145b0f1098a`, tokenizer at the same
  commit, FP16, batch one, Mac MPS. No model fine-tuning.
- Keep the completed-code prompt prefix and deterministic outer-fence-only
  extraction from the MBPP+ study. Four independent natural samples per task,
  temperature 0.7, top-p 0.95, the existing task/sample seed function. EOS is
  the normal stopping condition; 4096 tokens is a logged technical context
  guard, not an exclusion. Store raw outputs and activation receipts atomically.
- Only the pinned EvalPlus base **and** plus functional tests can label a
  candidate. Run generated code solely in the existing restricted, networkless
  Docker verifier image with a HumanEval-specific worker. A task with an
  infrastructure failure is excluded from binary metrics and remains in the
  inventory; syntax and extraction failures remain failures. A test pass is
  functional-test passage, not proof of semantic correctness.
- Before opening development labels, the HumanEval worker SHA-256 is frozen as
  `d9a00d47c867ede53dc2d25d846a253c68cc9fb0fb7aee7c50b9c79e5cb63e9e`,
  the Docker image ID as
  `sha256:0ae4285e1b317d7cb066d7b297129b3ca28e53e624135b33516cb3fb8b406b42`,
  and seccomp SHA-256 as
  `85ea2ee4cfc4f957232ea300ee87890d4a56f44aeeb4a4ecd177e3eb778c5c1e`.

## Feasibility and endpoints

1. On eight open development tasks, generate and verify all 32 candidates.
   Require at least two tasks with zero passes and two with at least one pass,
   no unexplained verifier failures, and successful resume/hash readback.
   Otherwise report feasibility and stop before the one-use test. Do not
   change task IDs or thresholds in response to those eight outcomes.
2. Fit the pre-generation ridge on the existing MBPP+ training tasks, with
   layer and regularization selected only by five-fold training-task CV.
   The already observed choice (layer index 20, alpha 0.01) is frozen for the
   transfer evaluation. Compare it with a prompt-text/length ridge whose
   training-CV alpha is 10.0. All features are computed before code
   generation. Primary metric: paired per-task absolute-error difference for
   the four-sample pass fraction, with 10,000 task bootstrap replicates.
   Support requires the 95% interval's upper bound below zero.
3. Secondary: apply the fixed MBPP+ candidate-level static and strong
   non-internal text/likelihood monitors to the same scorable test candidates.
   Compare their individual probabilities and a fixed equal-weight blend,
   with and without the pre-generation task prior. Report task-equal Brier,
   task-equal cross-task AUROC and within-mixed-task ranking separately. A
   constant task prior cannot improve within-task ranking by addition.
   No threshold or weight is selected on HumanEval+ test outcomes.
4. False alarms, misses, pass prevalence, mixed-task count, verifier costs,
   and incomplete/model-truncated outputs remain visible. No generalization
   beyond these two public code benchmarks is claimed. Public benchmark
   pretraining contamination remains possible.

The published Three-Reader needs full token-by-layer trajectories and a
different training recipe. Its use is **not** established by this transfer
test. A later, separately registered component experiment may compare Motion,
Region and Direction after full trajectories are collected. The transfer
result cannot be rescued by that later analysis.

## Execution freeze before test verdicts

The development gate was completed on 2026-09-27: 32/32 candidates classified,
16 passes, 12 functional failures, four extraction failures and no verifier
infrastructure failures. Six tasks had at least one pass and two had none, so
the registered feasibility gate passed. Its immutable gate artifact has
`record_sha256=1f4259fde0a87509551039d0a3bd3c0dc6feefe22f3b9245efdf99de7fd0dc44`.
These are **development** observations, not transfer evidence.

Before opening any of the 80 test-task verdicts, the implementation was fixed
at these SHA-256 values:

- `src/vrm/code_transfer.py`: `681fd0fdcc372118faaad3c6acf4dc97d0b874b39bcfb830500e383143eefcdd`
- `src/vrm/code_transfer_verify.py`: `d7c711742eede4a1d14a67c34670b644494b4b832858c4c32690da162b407a1b`
- `src/vrm/code_transfer_analysis.py`: `a578bd9b99ba27b4f619cb8487f3429e8b034e97f527bdf4d13a8df5713b7490`

Generation and atomic receipt storage of the one-use test set may already be
in progress. That does not reveal functional labels. Do not alter the frozen
analysis after test verdicts become visible. If an implementation defect is
found, report it and separate any repair analysis from the frozen primary
result.

Sources: [pre-generation probes](https://arxiv.org/html/2602.09924v4),
[Three-Reader](https://arxiv.org/html/2608.05660v1),
[Constitutional Classifiers++](https://arxiv.org/html/2601.04603v1),
[EvalPlus](https://github.com/evalplus/evalplus/tree/v0.3.1).
