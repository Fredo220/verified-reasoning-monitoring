# Why does the deception monitor miss cases?

**Main finding:** the saved scores rank the frozen deception labels well, but the frozen cutoff is conservative. Rating uncertainty and small-model limitations remain possible explanations, but neither is established as the cause of these misses. The score calculation has been independently checked; the full original-activation audit remains incomplete.

## What was checked

- Every saved score pair: **2,075 records and 4,150 file hashes**.
- Frozen design, labels, original-response links, scenario-group splits, train-only scaling, probe parameters, selected epochs, EMA and calibration.
- All **32 manageable local activation captures**: original hashes, layer order, token hashes, one initial BOS, mask positions and the unchanged float64 projection oracle. Actual generated-output bytes were additionally available for 26 of those captures.
- A separate rubric review of the 15 misses and a score-blind review of a deterministic, outcome-independent sample of 24 cases. This is AI-assisted rubric checking, not independent human annotation.
- Seven focused regression tests covering correct behavior and deliberate identity/calibration/token failures, followed by the complete software suite. The machine evidence is in [GATES.md](GATES.md).

No responses, labels, weights, splits, cutoffs or previous results were replaced.

## 1. Ranking and flagging are different

On the 53 binary evaluation roleplays, SWiM AUROC is **0.9568**: deceptive scores exceed honest scores in **643 of 672** positive-negative pairs, with no ties. AUPRC is **0.9749**. These are recalculations from the saved scores, not a full source-verification certificate or population guarantee.

At the frozen cutoff of **34.6143**, the monitor flags **17/32 deceptive** and **0/21 honest** responses, plus **7/22 ambiguous** and **9/1,000 ordinary** responses. Ambiguous alerts are not binary mistakes. Ordinary alerts are not an audited honest false-positive rate.

Ten of the 15 missed deceptive responses still score above every honest evaluation response. In other words, a missed flag often means "below this operating threshold," not "the activations contain no useful separation."

The zero observed honest alerts have a roughly **15.5% upper Wilson 95% bound**. Twenty-one honest responses are too few to establish a near-zero population false-positive rate.

## 2. The threshold trades recall for fewer alerts

The following calculations use the same frozen scores and original calibration pool. They are **post-hoc sensitivity analyses**, not a selected new policy or independently confirmed improvement.

| Readout and calibration percentile | Detected deceptive / 32 | Honest alerts / 21 | Ordinary alerts / 1,000 |
|---|---:|---:|---:|
| EMA, 99th: frozen | 17 | 0 | 9 |
| EMA, 97.5th | 20 | 0 | 16 |
| EMA, 95th | 23 | 0 | 35 |
| EMA, 90th | 25 | 0 | 74 |
| Raw maximum, separately calibrated at 99th | 20 | 0 | 11 |

The raw maximum is calibrated on raw calibration scores, not compared with the EMA threshold. That fair comparison suggests smoothing contributes to some misses, alongside a changed ordinary-alert trade-off. It does not prove that removing smoothing is generally preferable.

## 3. Ratings have uncertainty, but do not explain all misses

The separate missed-case review found **12 cases consistent with the upstream deception rubric** and three needing qualification: material minimization/partial admission, a vague excuse, and an underspecified time window. These are behavioral rubric judgments, not proof of intentional deceit.

The 15-case set was chosen because the monitor missed those labels, so it cannot estimate population label error. The 24-case hash sample avoids that selection criterion; its full notes and limitations are in [LABEL_REVIEW.md](LABEL_REVIEW.md). Neither review replaces the frozen user-confirmed labels.

## 4. Probe training suggests a generalization/calibration concern

There are **86,016 input features but only 169 distinct binary training responses**. Distinct responses are not necessarily statistically independent, especially when related scenario templates recur. Captured tokens are correlated within responses; they are not thousands of additional independent labels.

SWiM's training loss falls across four epochs from **2.9227 to 0.0132**. Its lowest validation loss is **3.0897 at epoch 2**, then worsens. Mean-BCE selects epoch 1 at validation loss **3.6578**. Both exceed the mathematical zero-logit loss of **log(2) = 0.6931**.

A model can rank well yet produce overconfident, poorly calibrated logits. These histories support that concern. They do not establish that extra features caused the misses, that the base model cannot comprehend the scenarios, or that a new baseline was empirically trained. A validation-only calibration/control comparison belongs in a separate follow-up.

## 5. No scoring corruption was found in the available evidence

All saved-score identities, EMA values and threshold calculations match independent review. New negative tests tightened two audit boundaries: calibration must use exactly the ordered selected IDs, and each available capture must match its token hash and valid positions. The existing receipts pass both checks; these were defensive audit repairs, not discovered result-changing defects.

The original full activation audit nevertheless failed after its 300-check progress message. The precise failing record remains unidentified. All 32 locally manageable captures pass the **unchanged** float64 oracle; 2,041 are not locally present and two exceed the local reference-allocation bound. Do not conclude that the original failure was harmless rounding, or declare full source coverage from these partial checks.

## 6. Small-model incapacity remains untested

The probe is a separately trained readout of the base model. Probe failure, base-model factual misunderstanding and ambiguous behavioral labels are different explanations. No matched fresh scenario-fact diagnostic has been executed, so "the model is too small to understand deception" is not established.

The studies inspiring this implementation have different model/data scales and settings. This SWiM roleplay experiment does not reproduce the complete Constitutional Classifiers++ cascade. See [RECONSTRUCTION.md](RECONSTRUCTION.md) for the scope and primary sources.

## Conclusion and next step

The available evidence supports **useful ranking with a recall-limiting operating point**, not a universally reliable deception detector. It does not support simultaneous established superiority in recall and false alerts over the earlier monitors. The saved-score result remains provisional until the full source audit is resolved.

Finish source-bound verification and the separately authorized comprehension diagnostic first. For a recall-first follow-up, preserve this study, calibrate the tolerated alert burden on development/validation examples, and evaluate once on unused scenario families. Reuse the existing responses, infrastructure and frozen evidence; do not restart training merely to obtain a more favorable result.

Audit status and missing observations are explicit in [GATES.md](GATES.md), [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) and [REPRODUCTION-PLAN.md](REPRODUCTION-PLAN.md).
