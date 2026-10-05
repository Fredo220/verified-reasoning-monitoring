# Code trajectory follow-up: frozen analysis protocol

**Registered before reserve-task generation or verdicts were opened:**
2026-09-27. This is a new, adaptive follow-up to the opened MBPP+ and
HumanEval+ studies, not a reanalysis that can rescue either result.

## Question and population

Does a full token-by-layer activation reader rank naturally generated,
EvalPlus-verifiable Python solutions more accurately than the strongest
non-internal selector on previously unused tasks from the same benchmark
family? The frozen generator is Qwen2.5-Coder-1.5B-Instruct at commit
`2e1fd397ee46e1388853d2af2c993145b0f1098a`, in FP16. It produces four
unmodified samples per task with temperature 0.7, top-p 0.95, the existing
prompt, deterministic task/sample seeds, and an operational 4096-token guard.
The guard is not an exclusion rule; all truncations are reported.

The original HumanEval+ manifest contains 8 opened development tasks, 80
opened transfer-test tasks, and 76 **unopened reserve tasks**. The 76 reserve
IDs are the one-use target population. They are never used for feature
normalization, training, tuning, threshold selection or early stopping. The
opened 80 are reassigned by SHA-256 order of
`trajectory-followup-v1\0` plus task ID: first 56 to train, remaining 24
to validation. The original 8 development tasks remain excluded. The 144
complete MBPP+ training tasks, and no MBPP+ validation or test tasks, augment
the new training split. Those data were previously opened; their use is
disclosed, and no claim of a wholly new benchmark is made. All three methods
fit on exactly the same candidate IDs and binary labels.

The source, split IDs, code, model revision, sample parameters and test
verifier identity are hashed before reserve generation. Public prompts and
generated candidates may enter model and monitor inputs. Reference code,
hidden tests and verifier results may never enter them. EvalPlus base+plus
passing is an operational functional-test label, not formal correctness.
Verification runs in the already pinned networkless Docker container.

## Frozen signals and comparison

Replay each saved prompt and assistant continuation through the *same* frozen
model, recording FP16 post-block residual states for **every non-EOS answer
token at all 28 layers**. No token truncation, layer omission or precomputed
random projection is allowed. Capture is resumable per candidate with a
source-receipt hash, token count, shape, finite-value check and file hash.
The same capture hardware and software must be used for train, validation
and test; any change requires an amendment before target labels are opened.
The code stores raw candidates and full traces separately. A trace or verdict
without a complete, matching source receipt is unusable.

Candidate selectors, all fit on the training split only:

1. Non-internal: code-character TF-IDF, text length and line count, extraction
   and syntax status, plus sum/mean token log-likelihood; separately report
   each raw likelihood. Pick the non-internal champion on validation by
   task-equal within-task pairwise rank, then validation log-loss.
2. Static: regularized linear classifier on separately unit-normalized
   last-answer-token states from all 28 layers. Pick `C` from
   `{0.01, 0.1, 1, 10}` on validation with the same criterion.
3. Motion-only: the existing two-layer bidirectional LSTM over all adjacent
   layer displacements of every answer token.
4. Three-Reader adaptation: the same Motion reader plus the existing Region
   and Direction readers at six preselected relative depths. It is **not** a
   paper-exact reproduction: architecture details and resource adjustments
   are logged, and both neural readers receive identical full traces.

Neural training uses task-grouped pass/fail pairs and pairwise logistic loss.
All-passing and all-failing training tasks remain in the inventory but have
no pairwise training term. Train three fixed seeds `11/22/33`, for at most
seven epochs, selecting each seed's checkpoint by validation pairwise loss
with patience two. Average the three seed probabilities without selecting a
winning seed. If a seed fails, disclose it rather than replacing it after
looking at target data. No generator fine-tuning, steering or test adaptation.

## Endpoints and interpretation

Primary: mean within-task pass/fail pairwise rank difference, Three-Reader
minus the validation-selected non-internal champion, on the same reserve
candidates. Tasks, not candidates or pairs, are the bootstrap unit; use
10,000 paired task bootstrap draws with seed 20260927. If fewer than 12 target
tasks contain both labels, report `not_evaluable_for_pairwise_claim`. A
positive claim additionally requires the lower 95% interval bound above
zero. Motion-minus-static and Three-Reader-minus-Motion are secondary,
descriptive component comparisons; no positive claim follows from their
uncorrected intervals alone.

Report all 76 tasks, all candidates, extraction/syntax/timeouts, missing
traces and verifier failures. Report task-equal Brier and false-alarm/missed
error rates at a validation-frozen threshold, plus all-task AUROC separately.
Do not silently select only favorable mixed tasks or call the pairwise score
an absolute correctness probability. A first-check and first-two-checks
offline replay compares selector orderings with generation order and the
oracle ceiling on the *same* natural candidate pool. This is not a live
deployment or an equal-wall-time cost result; measured model capture,
monitor and verifier time is reported separately when available.

The reserve outcomes are opened only once, after the model files,
hyperparameters, champion identity and prediction arrays are sealed. Any
post-opening diagnosis is labeled exploratory. A failed feasibility or
resource check is not evidence against the scientific hypothesis. A negative
or inconclusive endpoint does not justify resampling the target IDs.

## Smallest readiness check

Before any reserve generation, replay one previously opened candidate and
validate token alignment, all-layer coverage, finite values, deterministic
receipt resumption and feasible memory/disk use. Run the existing test suite.
Only then collect reserve candidates and verify them. If free Colab is
unavailable, the local 8-GB Mac/MPS path may be used provided the *entire*
follow-up trace set uses that same path. Preserve generated receipts after
each candidate; no notebook-only result or unsaved GPU session counts.

## Literature boundary

The [Three-Reader paper](https://arxiv.org/html/2608.05660v1) supplies one
correct candidate among alternatives and uses full residual trajectories;
we use natural samples that may all pass or all fail. The
[pre-generation study](https://arxiv.org/html/2602.09924v4) predicts
task-level policy success, not within-task candidate order.
[Constitutional Classifiers++](https://arxiv.org/html/2601.04603v1) studies a
production jailbreak-defense cascade, not code correctness. None of their
reported effects is a control result for this study.
