# Code-candidate monitoring study: staged preregistration

**Registered design:** 2026-09-26. **Status:** design registered; dataset manifest,
execution environment and population size are not yet frozen. No code-study
candidate outcomes have been collected. This is a separate study from the Lean
proof experiment. Its data and hypotheses cannot revise that experiment.

**Pre-data clarification, 2026-09-26:** The first draft specified a fixed
English code request but not its literal text. The exact prompt below and the
single-final-line-break fence rule were fixed during local tests, before any
real code-study candidates or verdicts were collected. They are not
post-outcome changes.

**Pre-outcome amendment, 2026-09-26:** A secondary task-balanced contrast
direction is registered before any real code-study candidate or verdict has
been collected. It cannot replace or rescue the primary static-probe endpoint.
For each training task containing at least one confirmed pass and one confirmed
fail, compute the difference between the mean pass and fail vectors. Vectors
are the same separately unit-normalized, all-post-block-layer final-code-token
features used by the static probe. Average task differences with equal task
weight, then unit-normalize the resulting direction. The candidate score is
its dot product with that fixed train-only direction. No validation or test
label enters fitting. Require at least 12 mixed training tasks and a nonzero
finite direction; otherwise report `not_evaluable`. There is no layer search
or fitted score threshold for this secondary ranking. Refit this direction
after a within-task training-label shuffle as a null, and fail closed if the
null direction equals the original. Report train-split direction stability
only as a diagnostic. Evaluate on the same held-out mixed tasks and with the
same task-clustered intervals as the primary probe, without altering H1/H1+
or the H2 opening gate. Contrastive abliteration work motivates the method,
but this study does not modify weights or infer a universal correctness axis.

**Source/runtime record, 2026-09-27, before candidate generation:** Official
MBPP+ `v0.2.0` release bytes have SHA-256
`af43697e8791c4c149bdfd6b489d8b5412507551ac20e28a439f650b8225db63`;
decompressed content has SHA-256
`b54e762755248ca411b523c917fa9f93c07b5ff2966bf60b3917b853926a3dad`.
The 32-task public development manifest has SHA-256
`1a31453cb71346e0f030c91a083d4e386b9e25f9898e5a37ccdc79386b3b6f65`.
The local verifier worker mounted into the isolated container has SHA-256
`5b48f70163af3fd8e6564975525b8b9068b5caec4a7373588411dfdeb515a1ca`;
the verifier refuses changed worker bytes before Docker execution.
The free T4 runtime loaded the pinned Qwen commit in FP16 under Python
`3.13.15`, Torch `2.11.0+cu128`, Transformers `5.16.1`, Accelerate `1.14.0`,
NumPy `2.1.3`, and scikit-learn `1.6.1`. It reported 28 blocks, hidden size
1536, chat-template SHA-256
`cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`,
and 3.087 GB peak allocated VRAM for loading. No candidate was sampled by
that check. A public-prompt-only similarity scan found a near-duplicate
(`Mbpp/104` and `Mbpp/569`) and several variants; those pairs must be grouped
or excluded from cross-split comparison before the population freeze. The
existing development prompts remain open, and their partner tasks cannot
become protected test units. This scan used no model outcomes or hidden tests.

**Pre-outcome prompt-variant register, 2026-09-27:** A TF-IDF word 1-3 gram
screen followed by reading only public prompts flagged `Mbpp/104`/`Mbpp/569`
(same task), `Mbpp/267`/`Mbpp/287` (odd/even squares), `Mbpp/736`/`Mbpp/786`
(left/right insertion), and `Mbpp/435`/`Mbpp/479` (first/last digit).
The lower-similarity analog pairs `Mbpp/395`/`Mbpp/602` (first
non-repeated/repeated character), `Mbpp/455`/`Mbpp/762` (31/30-day months),
and `Mbpp/145`/`Mbpp/763` (maximum/minimum difference) were also flagged.
`Mbpp/602`, `Mbpp/455`, and `Mbpp/145` are in the open development split;
their partners must be excluded from protected splits. The other pairs must
stay together or be excluded when the population is frozen. This is a
conservative leakage control, not a claim that the paired tasks are identical.
The local protected-population builder now preserves the hashed development
manifest and excludes its three registered partner tasks. Under this pair
register, the remaining source has at most 339 assignable groups. Therefore
the tentative `200/50/96` train/validation/test group allocation (346 groups)
is infeasible. This was established from public prompts and IDs only, before
any model candidate or verifier outcome. A reduced allocation must be selected
once from open development feasibility evidence; `200/50/89` is only a
capacity check, not the chosen study size. Further variant exclusions may
lower the capacity.

## Question and estimand

Can activations from a frozen code model rank *completed* Python solutions that
pass independent functional tests above solutions that fail, for the same task?
The primary estimand is the mean, across held-out tasks with both outcomes, of
the fraction of pass/fail candidate pairs correctly ranked. Ties count 0.5.
This is selection among completed candidates, not online failure detection,
better code generation, formal correctness, or a causal mechanism.

- **H1:** A regularized activation probe ranks within-task pass/fail pairs
  above chance on unseen tasks.
- **H1+:** Its task-equal pairwise rank exceeds the best validation-selected
  non-internal baseline (token log-probability, code text/length/syntax).
- **H2, gated:** Motion-only or a reduced Three-Reader adaptation adds
  information beyond the static probe on the same held-out tasks. H2 is not
  needed to complete H1 and must not rescue a failed H1.

The unit for uncertainty is the task, not the candidate or token. Report the
number of mixed tasks, their share of all tasks, the number of pairs, and
all-task discrimination separately. A pooled AUROC cannot establish H1.

## Prior work and scope

[Interpreting Code Correctness in Language Models through Activation Steering](https://github.com/MechCode1/Correct_Codegen)
already uses Qwen2.5-Coder-1.5B-Instruct, MBPP+, multiple generations and
activation probes. This study is not the first code-correctness probe. Its
specific test is a task-held-out, task-equal within-task contrast with
non-internal, prompt-only, label-shuffle and token-position controls. The
[pre-generation probe study](https://arxiv.org/abs/2602.09924) addresses
task-level success prediction before a candidate exists; prompt-only scores
are constant within a task and cannot rank its candidates. The
[Three-Reader paper](https://arxiv.org/abs/2608.05660) motivates a gated
component comparison, not a claim that its results transfer to Python code.
Because MBPP+ is public, task-held-out means unseen by the *monitor training*
only. It does not establish that the generator never saw these tasks during
pretraining. Even a positive result is a benchmark-specific robustness check,
not a novel discovery of code-correctness activations.

## Sources and freezing sequence

Provisional generator: `Qwen/Qwen2.5-Coder-1.5B-Instruct`, model and tokenizer
commit `2e1fd397ee46e1388853d2af2c993145b0f1098a`, FP16, batch one,
frozen weights. Provisional benchmark: EvalPlus MBPP+ `v0.2.0`, 378 tasks,
EvalPlus tag `v0.3.1` at `e5d0ed0bab96280b60b637ec7f15b5e4841b0cb2`.
These are source identities, **not** claims that this combination runs on
free Colab. The raw dataset SHA-256, exact 378 IDs, test-image digest, Python
and library versions, prompt hash, and split manifest must be recorded before
any generation. Never load canonical solutions, tests or verifier output into
the generator or monitor.

Two freezes are permitted and recorded in an append-only amendment log:

1. **Design freeze (this document):** question, controls, primary metric,
   leakage boundary and decision logic below. No model outcomes inspected.
2. **Population freeze:** after one open development smoke, choose one study
   size and operational generation guard using only development yields and
   measured resources. Hash the ID manifest and runtime. Protected validation
   and test generation must not start before this freeze. No later tuning of
   task IDs, labels, exclusions or sample size based on test results.

Tentative task allocation is dev 32, train 200, validation 50, test 96 from
the 378 MBPP+ tasks, assigned by deterministic SHA-256 order of task IDs.
Near-duplicate or semantically equivalent prompts are grouped before
allocation, with exclusions logged. If independent groups are insufficient,
the count is reduced once after the open smoke, before population freeze.
The development tasks never enter training, validation or test. A secondary
task source, if attempted, must be separately frozen before its outcomes are
read and cannot rescue the primary result.

## Candidate and label contract

Use one immutable user prompt for every task. Its exact text is the following
prefix followed immediately by the unmodified public MBPP+ `prompt` field:

```text
Write a complete Python module that solves the task below. Define the requested function(s). Return only Python code, without Markdown fences or explanation.

```

No reference solution, test, or verifier field enters this request. Record
separate SHA-256 hashes for the source prompt and rendered model request.
Apply the chat template once. Four independent natural samples per task, temperature 0.7,
top-p 0.95, deterministic per-task/per-sample seeds. Do not require a correct
sample. Generation stops at EOS; an operational token/time guard and every
truncation are logged. A guard is not an exclusion rule and may be adjusted
once on development only. No manual repair of protected outputs.

Store raw output, generated token IDs/log-probabilities, an exact deterministic
code extraction, extraction status and hashes separately. Extraction removes
at most one complete outer Python/py Markdown fence, allowing one final line
break after the closing fence; otherwise it accepts
only a complete plain Python module. It never adds imports, fixes syntax,
changes names or edits code. Ambiguous/multiple fences remain an extraction
failure. A syntax failure is distinct from a test failure.

Run candidates only with separately authorized, reviewed process isolation,
network denial, filesystem limits and resource limits. Never run generated
code inside the notebook kernel or a normal local Python process. A passing
label requires all pinned base and plus tests to pass. Record `pass`,
`test_fail`, `syntax_fail`, `extraction_fail`, `timeout`, and `infra_error`
separately. `infra_error` is missing label, never failure. Timeouts count as
failures only if the verifier's fixed resource policy establishes a candidate
timeout, not when the Colab session disappears. Publish both all-candidate
and code-extractable subsets; do not silently remove invalid outputs.

The [pinned EvalPlus `evaluate` CLI](https://github.com/evalplus/evalplus/blob/v0.3.1/evalplus/evaluate.py)
requires samples for every benchmark task, so it cannot directly evaluate the
open 32-task subset. Its per-problem `check_correctness` API is the planned
integration point, but [that path](https://github.com/evalplus/evalplus/blob/v0.3.1/evalplus/eval/__init__.py)
executes candidate Python through `unsafe_execute`. It may run only inside an
independently checked outer container. The API and proposed image are not yet
an authorized or verified sandbox. Keep this operational gate distinct from
candidate failures.
The pinned [`get_groundtruth` path](https://github.com/evalplus/evalplus/blob/v0.3.1/evalplus/evaluate.py)
executes reference solutions and uses a pickle cache. Prepare expected outputs
inside the same isolated environment with a fresh, pinned cache; do not run
that setup in the notebook kernel or trust an existing cache from another run.
The verifier must load MBPP+ through the pinned
[`get_mbpp_plus`](https://github.com/evalplus/evalplus/blob/v0.3.1/evalplus/data/mbpp.py)
path, which deserializes special test inputs. Raw JSONL test-input fields are
not equivalent verifier inputs. The public handoff may accept either EvalPlus's
uncompressed JSONL cache or its `.jsonl.gz` release download; the first SHA-256
identifies the bytes actually supplied and the second identifies the uncompressed
JSONL content so the verifier can compare both forms.

## Feature boundary and controls

Capture all post-block layers at the last token containing actual extracted
code (not EOS, trailing whitespace, or a closing Markdown fence) and a fixed
earlier generated-token control, using the same prompt and raw candidate
tokens. If a token crosses the code/fence boundary or alignment is ambiguous,
mark that candidate unscorable rather than substituting the raw final token.
Retain its raw output and independent verdict in all-candidate counts; report
unscorable counts by split and verdict. Compare activation and non-internal
rankers on exactly the same scored candidates, and report all-candidate
verifier success separately. Record token-to-text alignment and replay equality
checks. No test
result, reference solution, future candidate, verifier metadata, or candidate
label enters the feature store. The primary static representation is the
concatenation of separately L2-normalized final-token states from all layers.
Fit an L2 logistic probe on training tasks only; choose `C` from
`{0.01, 0.1, 1, 10}` by validation task-equal ranking, with validation
log-loss as tie-breaker. Standardization, calibration and any dimensional
reduction are fitted on training only. Model and tokenizer remain frozen.

Controls use the same task/candidate split: sum and mean raw token
log-probability; code length, syntax, and TF-IDF; and a prompt-final-state
probe for task difficulty. The prompt-only control should be tied within a
task. Train a candidate-label-shuffle null *within each task* and a fixed
non-final generated-token activation probe. Verify that the shuffled direction
is not identical to the primary direction. Compare scores on the same
eligible candidates and report cases whose code was not extractable.

## Open smoke and decision gates

On the 32 open development tasks, collect four samples each. Measure pass,
confirmed fail and mixed-task yield; syntax/extraction/truncation frequencies;
token alignment; GPU time, peak VRAM, storage; verifier isolation; checkpoint
durability and resume. The next step is selected exactly once from this
evidence. If the dataset, model, safe verifier or complete receipt chain is
unavailable, report an operational blocker, not a negative hypothesis result.
If candidate yield is too low for a meaningful mixed-task comparison, report
a development feasibility stop; do not invent positives or repeatedly rebuild
the task population. The population-freeze amendment states the chosen count,
resource guard, mixed-task adequacy criterion and its development rationale.

After fitting the static model, H2 opens only if validation has at least 12
mixed tasks, the activation probe's task-equal pairwise score exceeds 0.60,
and it exceeds both the within-task label-shuffle and non-final-token controls
by at least 0.05 on their common scored tasks. The non-final-token comparison
requires at least 12 mixed tasks with a distinct earlier content-token state;
otherwise H2 remains closed as `control_not_evaluable`.
Otherwise H2 is not run. If opened, compare Motion-only and the full
Motion/Region/Direction implementation on validation and then once on test;
if resource-limited, name it a *reduced adaptation*, not a reproduction.
Record its exact retained token positions and layers before training.

## Protected evaluation and interpretation

Freeze all model choices and thresholds on validation. Open test outcomes
once. For each task with both confirmed pass and fail, compute pairwise
ranking; average tasks equally. Use 10,000 task-cluster bootstrap replicates
with fixed seed 20260926 for 95% percentile intervals on each score and the
paired difference to the strongest validation-selected non-internal control.
For the static probe's pass probability, choose a threshold from
`{0.05, 0.10, ..., 0.95}` using only mixed validation tasks. Minimize the
average of task-equal false-alarm rate (passing candidate flagged as failing)
and task-equal missed-error rate (failing candidate accepted as passing); break
ties by proximity to `0.50`, then by the smaller threshold. Freeze it before
test. Report those two rates, task-equal Brier score and ten-bin equal-width
ECE on the unchanged test scores. These descriptive diagnostics do not alter
the ranking endpoint. Also report all-task AUROC/AUPRC and class prevalence. Exact numbers
of mixed tasks and their pair counts are mandatory. If test has fewer than
12 mixed tasks, the primary test is inconclusive for lack of precision even
if its point estimate is high.

H1 support requires the lower 95% interval for within-task ranking above
0.5. H1+ additionally requires the lower interval of the paired difference
against the selected non-internal baseline above zero. Otherwise report
negative or inconclusive according to effect and precision, not `proved
wrong`. Test-suite passage is not formal correctness; these results cannot
establish universal reasoning, machine intuition, causal intervention,
jailbreak defense or alignment. Publish failed runs and resource costs.
