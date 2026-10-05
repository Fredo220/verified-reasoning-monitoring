# Independent HumanEval+ transfer: completed

This follow-up asks whether signals seen in the earlier MBPP+ development work
survive a different, previously unopened code benchmark. The original MBPP+
validation results had already been inspected. The HumanEval+ task allocation,
analysis choices and feasibility gate were therefore recorded separately
before any HumanEval+ test verdict was opened. See the
[protocol](humaneval_transfer_protocol_2026-09-27.md) and the immutable local
machine report at `data/code_monitoring/humaneval-transfer-v1/report.json`
(`record_sha256=3f1926361276b5cd991a1a8e1fba0ccff901cca2a539159ed5e9bca238b083b1`).

## What ran

- The frozen Qwen2.5-Coder-1.5B-Instruct generated four natural, unmodified
  candidates for each of 80 held-out HumanEval+ tasks. All 320 generations and
  320 EvalPlus base+plus verdicts have checksum-verified local receipts.
- A preceding eight-task development gate passed as registered: two tasks had
  no passing candidate and six had at least one, with no infrastructure error.
  It was used only for feasibility, not monitor tuning.
- Candidate generation saw only public task IDs and prompts. Functional tests,
  reference solutions and verifier output stayed outside the model and monitor
  inputs. Generated code ran inside the pinned restricted, networkless Docker
  verifier.
- The pre-generation probe used prompt-end activations from layer 20 and a
  ridge penalty of 0.01. The comparison used prompt text/length with penalty
  10. Both choices came from MBPP+ *training-task* cross-validation. Candidate
  probes and equal-weight combinations were also fitted only on MBPP+ training
  tasks. No coefficient, threshold or test task was selected using HumanEval+
  test labels.

## Result

| Question | Internal signal | Non-internal comparison | Result |
| --- | ---: | ---: | --- |
| Predict each task's four-sample pass fraction before generation (MAE, lower is better) | 0.3543 | Prompt text 0.3368 | Activation minus text: +0.0175; task-bootstrap 95% CI [-0.0472, +0.0788] |
| Rank passing above failing candidates within the same task (higher is better) | Static probe 0.4744 | Text/likelihood 0.6987 | 26 tasks were mixed among scorable candidates |
| Candidate pass-probability error (task-equal Brier, lower is better) | Static probe 0.2324 | Text/likelihood 0.1912 | Static minus text: +0.0413; 95% CI [+0.0067, +0.0756] |
| Add the static signal to text (within-task rank) | Text+static 0.6474 | Text 0.6987 | Difference -0.0513; 95% CI [-0.2244, +0.1250] |

The registered primary criterion required the *upper* confidence bound of the
pre-generation MAE difference to be below zero. It was not met. The interval
also does not establish that the prompt activation signal is worse than text;
the primary result is **inconclusive**, not a proof of absence. The static
candidate probe performed worse than the text/likelihood baseline on this
transfer set. An equal-weight text+static blend did not show a reliable gain.
Adding the task-level prior to candidate text scores did not change within-task
ranking, as expected for a score that is constant across a task's four
candidates; its Brier score was 0.2132 versus 0.1912 for text alone.

Across all 320 candidates, 154 passed both base and plus tests, 128 failed
functional tests, 34 failed the registered extraction rule, one failed syntax,
and three timed out. By task, 24 had no passing candidate, 19 had four passes,
and 37 had a mixture. Candidate-level probe metrics use 286/320 candidates
with aligned final-code activations; only 26 tasks remain mixed in that subset.
No task was lost to an unexplained infrastructure error. All 320 outputs ended
at EOS rather than the technical token guard.

The sum of measured per-candidate generation time was 1,594 seconds; sparse
activation capture added 160 seconds. These sums exclude model loading,
verifier execution and reporting, so they are **not** an end-to-end cost claim.

## Relation to prior work

- The [pre-generation probe study](https://arxiv.org/html/2602.09924v4)
  motivates measuring model-specific success *before* an answer exists. We
  tested that idea on a frozen four-sample coding policy, with a prompt-text
  control and an independent benchmark transfer; its reported gains do not
  imply that our smaller model must show the same effect.
- [Three-Reader](https://arxiv.org/html/2608.05660v1) scores complete
  candidates from token-by-layer motion, region and direction and trains on
  candidate comparisons. Our saved sparse states and linear static probe are
  not that method; the present test cannot confirm or refute its full model.
- [Constitutional Classifiers++](https://arxiv.org/html/2601.04603v1)
  motivates a cheap internal screen followed by a stronger external check,
  while measuring false alarms and deployment costs. Its jailbreak labels,
  thresholds and production robustness do not transfer to code correctness.
  We measured the prerequisite signals here, not a deployed cascade.

## Interpretation and limits

The earlier MBPP+ layer sweep looked promising on an already opened
validation set. The independent HumanEval+ transfer did **not** reproduce a
clear incremental monitoring advantage. This is compatible with several
possibilities, including benchmark-specific features, a strong surface
baseline, noisy four-sample success fractions, and the difference between
MBPP+ training on CUDA and HumanEval+ capture on Mac MPS. This experiment does
not separate those explanations.

This result concerns one 1.5B model, two public coding benchmarks and
functional-test labels. Passing EvalPlus is not a proof of general program
correctness. Benchmark pretraining contamination cannot be ruled out.
Neither a causal role for the activations nor a production monitoring benefit
was established. The full Motion/Region/Direction Three-Reader and a live
two-stage cascade were **not** evaluated here: the stored candidate states are
sparse, and the registered component comparison would require full
token-by-layer trajectories and its own independent test. We will not relabel
this static probe as a Three-Reader or use an exploratory extension to rescue
the closed transfer result.

The most useful next experiment is a separately registered diagnostic with
full trajectories, model-aligned training data and an untouched target set.
It should compare static, Motion-only and all three readers against the same
strong text baseline, then test any cascade for incremental accuracy, false
alarms and cost. This is a new study, not a rerun of the opened HumanEval+ set.
