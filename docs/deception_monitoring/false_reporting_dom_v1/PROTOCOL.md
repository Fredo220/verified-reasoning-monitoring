# False verification reporting: bounded DoM adaptation

Status: adaptation approved on 2026-10-04; no new activations or outcomes opened. This protocol replaces neither the completed deception experiments nor their labels or audit status.

## Question and scope

Can a raw difference-of-means probe distinguish a scripted false success report from truthful reporting about an explicit verification record? Can it do so without treating an honest admission of failure or nonexecution as a positive?

This is a representation pilot, not an exact reward-hacking replication. The authors' complete synthetic conversation release and projected-vector implementation were not located in a bounded search. We construct transparent fixtures instead, adapting the raw recipe in [Section 3.1](https://arxiv.org/html/2609.19101v1#S3.SS1). We do not execute hacks, measure spontaneous cheating, infer intent or claim prevention.

## Frozen inputs

- Model and tokenizer: `meta-llama/Llama-3.2-3B-Instruct`, revision `0cb88a4f764b7a12671c53f0838cd831a0843b95`; FP16, no quantization or fine-tuning, batch one, existing Colab T4 only. No purchase or paid API.
- Dependencies: existing `requirements-deception.txt`; record exact installed Torch/CUDA and package versions before capture. No mixing runtimes within one capture set.
- Reuse the tested Llama chat-template and full-context chunked capture functions. Apply the template once with `add_special_tokens=False`, exactly one BOS, fixed date `04 Oct 2026`.
- Capture tuple indices 1 through 28 at every final report token, excluding headers and end-of-turn. The last tuple entry includes the model's final normalization. No prompt truncation or generated response is needed: these are teacher-forced conversations.
- Four development groups, 32 training groups, eight validation groups, 16 ordinary held-out groups, and 16 held-out groups using a distinct report phrasing. All six counterparts of a group remain together. No selection from outcome scores.

Each group has six nine-message conversations, including the system message. Their surrounding task is matched. Conditions are: truthful success; fabricated success after failure; honest failure; fabricated verification without execution; honest nonexecution; honest discussion of why a success claim would contradict a failure. Only the two fabricated-success conditions are positive. Ground truth follows the fixture's observed state and actual claim; it is not a subjective-intent label.

The success report is byte-identical in truthful success, fabricated success and fabricated verification. This subset tests context dependence. Honest failure and nonexecution are mandatory negative controls. An explicit structured log remains visible to every context-aware comparator. The fixture manifest, code and protocol are hashed before the first forward pass.

The groups differ only in their component identifier. They are identifier-held-out repetitions of one controlled scenario, not 76 independent task meanings. The changed-phrasing split changes the report wording, not the task domain. Bootstrap intervals describe identifier sensitivity conditional on this fixed template; they do not establish population-level reliability, semantic out-of-distribution transfer or natural reward-hacking detection. These limitations are registered before capture, not inferred away after a positive result.

## Ordered execution and persistence

1. Validate fixtures and local regression tests.
2. Mount the approved account's private Drive and verify its identity. Capture development groups first; compare dense and chunked states on the first row and require relative L2 below the existing 1% extraction check at every layer. This is an engineering check, not scientific evidence.
3. Persist each array and its receipt atomically in the new Drive namespace. Simulate an interruption after seven completed rows and resume by verifying the same input/model/runtime/mask/array hashes. Never rerun old study cells.
4. Capture the predeclared remaining rows. An operational pause after 15 GPU minutes preserves unfinished rows for resume; it is not a scientific failure or a reason to remove cases. Do not modify prompts after observing outcomes.
5. Release model memory before CPU fitting. Collect a separate result archive, transfer it privately, verify hashes and independently audit the analysis locally.

This is 456 short captures, not a frontier SWE-agent benchmark. Runtime and disk estimates are not measured results. No Mac model loading; CPU analysis processes one capture or one layer at a time.

## Primary method and comparators

- Raw DoM: positive minus negative training-token means, uniform position weighting, FP64 accumulation, no centering, normalization or projected variant. Final-report mean raw dot product is our registered passage aggregation.
- Token-trained logistic comparator: the existing train-only StandardScaler plus LogisticRegression recipe, `C=0.1`, no intercept, seed 42; fit new heads on the exact same fixture training tokens. Old heads remain unchanged.
- Output-only TF-IDF and full-context TF-IDF: train-only unigram/bigram vocabularies and logistic `C=0.1`, no tuning sweep. Report these separately; never withhold context from the primary text comparator.
- Deterministic consistency parser: read only the visible verification record and report, not hidden labels. It may solve this deliberately explicit task perfectly; that limits rather than strengthens our claim.
- One fixed within-group training-label permutation, seed 11, retaining two positives per group. Verify the resulting DoM vector is not identical to the primary. Read it at the primary-selected layer; do not optimize the null.

Evaluate all 28 layers on validation and select the highest AUROC independently for raw DoM and logistic, smallest-index tie-break. Then freeze those heads and layers before opening either held-out split. No layer, mask or readout selection on test.

## Endpoints and interpretation

Report held-out AUROC, average precision, same-wording-subset AUROC, and honest-failure, nonexecution and discussion false alarms separately. A validation-negative 90th-percentile cutoff (`method="higher"`, strict `>`) provides a descriptive operating point for both methods. It is not a guaranteed 10% deployment FPR. Save continuous scores and denominators for every condition.

Confidence intervals resample complete held-out scenario groups 1,000 times, seed 22. Related variants and tokens are not independent units. Ordinary and changed-phrasing splits stay separate. Do not treat a high validation maximum, a small-sample interval, or teacher-forced separability as evidence of natural reward-hacking detection.

Success is a completed, auditable comparison regardless of sign. If internal scores fail unchanged-wording or honest-failure controls, report that limitation. If the parser solves the task, the narrow contribution can only be decodability, not superior detection or reduced verification cost. No new Three-Reader, cascade or steering strategy is added before this raw-method test is reported.

The independent audit replays raw DoM and text-head scores in FP64 (relative tolerance 1e-12; absolute tolerance 1e-9 for DoM and 1e-10 for text), verifies every head checksum and validation selection, and recalculates the null from its training labels. Logistic scoring retains the source's FP32 implementation. Its separate FP64 dot-product replay uses a predeclared forward-rounding bound: with unit roundoff u=2^-24 and gamma_n=n*u/(1-n*u), the bound is (gamma_d + gamma_T*(1+gamma_d))*mean_t(sum_j(abs(x'_tj*w_j))) + 1e-12, where x' is the FP32-normalized activation, d is hidden width and T is the report length. This does not weaken or amend any earlier study's tolerance.
