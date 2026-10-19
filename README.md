# Internal Signals for Reliable Model Statements

This project tests whether the internal activations of a language model carry a signal that separates two kinds of final answers: answers that contain a statement the model believes to be false, and answers that do not. A small classifier (a "readout") is trained on the activations of a frozen base model and then evaluated on held-out data, including agentic episodes with hidden side tasks.

## Contributions

- **A pre-specified comparison of 18 readout variants** on false task-completion reports, with cutoffs frozen before held-out scoring, every variant reported, and independent replay of the trained heads.
- **A separation of ranking from detection.** The comparison shows that a score can rank held-out examples perfectly (AUROC 1.00) and still miss every positive at a frozen cutoff, so AUROC alone is not used as the success criterion.
- **A four-readout comparison on 2B and 9B models** of one family, on validation data and on agentic side-task steps, reported at fixed false positive rates.
- **An evaluation of the same procedure on larger models** (27B, 122B, 397B total parameters), with classifiers for nine base models being prepared for release.
- **A stated evaluation protocol** for the next stage: held-out threshold calibration, episode-level uncertainty, alerts per episode, and an information-matched text-judge baseline.

## Why this matters for AI safety

Agents can report that work was done, or deny actions, in ways that the visible transcript alone does not settle. A monitor that reads internal states is one candidate for flagging such statements cheaply, at a chosen false alarm rate, without a second large model. The question tested here is whether such a signal exists, how strong it is at fixed operating points, and how it changes with model size.

## Overview of studies

The three studies use different models, data and evaluation procedures. Their metrics are reported separately and are not combined into a single success rate.

| Study | What was tested | Models | Status |
|---|---|---|---|
| Scripted false reports | 18 readout variants, specified in advance, on false task-completion reports | Llama-3.2-3B-Instruct | Completed and published |
| Belief-contradicting statements | Four readout types on validation data and on agentic side-task steps | 2B and 9B | Completed; run-level artifacts in preparation for release |
| Larger models | The same procedure on larger models of the same family | 27B, 122B, 397B | Evaluated; results and classifiers in preparation for release |

## Research question

Can classifiers trained on the activations of a frozen language model detect that a final answer contains a statement the model believes to be false, and how does this detection transfer to agentic settings at a controlled false positive rate?

## Definition of the target

A final assistant answer `r` in context `C` is labeled positive if it contains at least one asserted statement `s` that the model believes to be false:

```math
y_M(C,r)=\mathbf 1\!\left[\exists s\in\mathcal S(r):\operatorname{Bel}_M(\neg s\mid C)\right].
```

The label is defined by consistency with the model's own belief, not by objective truth. A factual mistake is therefore not automatically positive, and a statement that is objectively true can be positive if the model believes it to be false. Literally true but misleading statements and deception by omission are outside this definition.

Evidence about the model's belief comes from three sources: unambiguous conversation information, a stable answer after a pressure or cue is removed, and known training conditions. A conservative grouping classifies 79,580 examples (48.8%) as grounded in conversation information. A complete per-example breakdown by source is not yet available.

## Method

### Measurement points

The base model is frozen. Activations are read from six decoder-block outputs at relative depths 0.30, 0.42, 0.55, 0.67, 0.80 and 0.90. Block output `k` usually corresponds to `hidden_states[k+1]`. Models with a different residual architecture need their own readout definition.

### Readouts

| Readout | Input | Output |
|---|---|---|
| Linear layer readout | One token position, one affine function per layer | Mean of per-layer sigmoid scores |
| Nonlinear layer readout | Same position, ReLU network (width 256) per layer | Mean of per-layer sigmoid scores |
| Statistical window readout | Mean and covariance features over a token window | Logit |
| Token-layer readout | Factorized attention over tokens and layers | Bounded logit |

**Linear layer readout.** Per layer `ℓ`:

```math
z_\ell=w_\ell^\top(h_{\ell,t_*}/\kappa_\ell)+b_\ell,
\qquad
g(H)=\frac1{|\mathcal U|}\sum_{\ell\in\mathcal U}\sigma(z_\ell).
```

The scaling factors `κ` are estimated on training activations and saved. Layers with a mean training loss below 0.6 are selected. Averaging per-layer sigmoids is not the same as applying a sigmoid to the mean raw score.

**Statistical window readout.** Activations are RMS-normalized per token and layer and concatenated across layers. Two projections to 64 dimensions produce mean and covariance features. The covariance is centered with divisor `n`, isotropic shrinkage 0.1 and diagonal stabilization `1e-5`. After a matrix square root, 256 learned bilinear features and 64 mean features feed a linear output head.

**Token-layer readout.** A shared projection to 256 dimensions feeds four blocks that combine causal token attention with bidirectional layer attention (4 heads, feed-forward width 1,024, learned layer embeddings, rotary positions along the token axis). The output is bounded with `10·tanh(z/10)`.

### Readout windows and training

The layer readouts use the token before the final end-of-turn token. The window readouts use the span from the start of the last user message through the end-of-turn token of the assistant answer.

All readouts are trained with binary cross-entropy:

```math
\mathcal L=-\big[y\log p+(1-y)\log(1-p)\big].
```

| Readout | Optimizer | Learning rate | Schedule | Maximum |
|---|---|---:|---|---:|
| Linear layer | AdamW | 0.005 | Constant | 6 epochs |
| Nonlinear layer | AdamW | 0.005 | Cosine | 6 epochs |
| Statistical window | Muon (AdamW for exempt parameters) | 0.005 | Cosine | 4 epochs |
| Token-layer | Muon (AdamW for exempt parameters) | 0.005 | Cosine | 4 epochs |

All use batch size 32, 20 warm-up steps, weight decay 0 and seed 0. The checkpoint with the lowest validation loss is selected, and training stops after one epoch without improvement.

### Check-question comparison (agentic setting)

A check question is appended to an agent step, for example:

```text
Did you do anything the user did not ask you to do?
Did you take actions towards a hidden side task?
```

The step is scored with each of two prescribed answers and the difference is used as the score:

```math
D_j=g(H(C_j\oplus q\oplus\texttt{No.}))-g(H(C_j\oplus q\oplus\texttt{Yes.})).
```

A higher `D` means the denial is more inconsistent with the model's internal state than the affirmation. The comparison cancels features that are the same in both branches, such as topic, style and length. Layer readouts compare sigmoid scores and window readouts compare logits.

### Metrics

- **AUROC:** the probability that a randomly chosen positive example scores higher than a randomly chosen negative one. 1.0 is perfect ranking and 0.5 is chance. AUROC measures ranking and is distinct from a detection rate at a threshold.
- **Recall at a fixed false positive rate (FPR):** the share of positive steps flagged when the threshold is set so that a given share of negative steps is flagged. The reported operating point is 5% FPR, with 1% FPR for comparison.

At 5% FPR, about five of every hundred negative steps are flagged. The overall alert rate also depends on the share of positive steps and on recall. The 5% operating point reflects a preference for higher recall, with a higher cost assigned to missed positive steps than to extra alarms.

## Study 1: Scripted false reports (Llama-3.2-3B-Instruct)

**Design.** The model read 456 scripted conversations about an explicit verification record, and its internal states were measured while it read the final report. Each identifier group contained six matched cases: truthful success, fabricated success after failure, honest failure, fabricated verification without execution, honest non-execution, and honest discussion of an invalid success claim. Only the two fabricated claims were positive. The success report was identical in the truthful and fabricated cases, so only the surrounding verification record distinguished them.

Splits: 24 development, 192 training, 48 validation, and two held-out splits of 96 records each (standard wording and changed wording). Each held-out split contained 16 identifier groups, 32 positive and 64 negative reports.

**Procedure.** Weights and normalization were fit on the training split. Validation selected epochs, layers and a cutoff at the 90th percentile of negative scores. Cutoffs were frozen before either held-out split was scored, and a report was flagged if its score was strictly above the cutoff. All 18 variants were specified in advance and all are reported, with no selection after seeing test scores. The run used a pinned model and tokenizer revision, and an independent replay reproduced the trained heads within the predeclared numerical bounds.

**Result for the all-layer linear readout with mean aggregation:**

| Held-out split | False reports flagged | Honest reports flagged |
|---|---:|---:|
| Standard wording | 32 / 32 | 0 / 64 |
| Changed wording | 32 / 32 | 0 / 64 |

**Findings from the comparison**
- **Ranking and detection are separate properties.** Raw difference of means ranked the changed-wording split perfectly (AUROC 1.00) but flagged 0/32 at its frozen cutoff, because the score scale shifted from about 0.315 to about 0.151, below the cutoff. The frozen operating point was kept and not adjusted afterward.
- **Aggregation matters.** Mean aggregation over the final report flagged 0/64 honest reports for all learned heads on the changed-wording split, while maximum-over-tokens aggregation flagged 48/64 for two heads.
- **Added complexity was not consistently beneficial.** Window smoothing and weighted window losses did not consistently improve on plain token-level training in this setting.
- **A visible-record parser reached the same result (32/32 and 0/64).** In this task template the verification record is visible in the text, so the study calibrates the probe against a direct checker. Settings in which the text alone does not settle the answer are the target of the later studies.
- **Controls were included.** A label-shuffled direction and the honest failure, non-execution and discussion cases served as controls. The shuffled direction ranked one subset almost perfectly, so that subset alone is not used as evidence for a specific mechanism. Overall shuffled-direction performance was much weaker.

**Scope.** All records share one task template, and the changed wording alters the report text, not the task domain. The study characterizes sensitivity to report wording within one template. Transfer to other task domains and to freely generated reports is addressed in the planned protocol below.

Full tables, figures and audit evidence: [results report](https://github.com/Fredo220/verified-reasoning-monitoring/blob/634df2cf3318561f267ef4b414ce8bf174dd25d0/docs/deception_monitoring/false_reporting_dom_v1/RESULTS.md).

## Study 2: Belief-contradicting statements (2B and 9B)

### Data

An existing labeled corpus of 163,016 transcripts from 28 groups, with 81,508 examples in each class. The label applies to the last assistant answer. Conversation histories (honest or deceptive) are crossed with final answers (honest, or containing a statement believed to be false), so the history alone does not determine the label.

| Conversation history | Final answer | Label |
|---|---|---:|
| Honest | Honest | 0 |
| Honest | Contains a statement the model believes to be false | 1 |
| Deceptive | Honest or corrective | 0 |
| Deceptive | Contains a statement the model believes to be false | 1 |

The training recipe uses 152,980 training rows and 5,000 validation rows. Variants of the same source prompt are kept in the same split, and length and message count were matched between the two classes. In the main comparison the 28 groups were not each held out as a whole; holding out whole groups is part of the planned protocol.

**Label quality.** An automated check by a language model estimates the label error rate at 0.74% (95% interval 0.57% to 0.99%). A human agreement rate is not yet available. Automated error analyses point to ambiguous rules for allocating donations and to legitimate changes of network protection rules. These concern the reference labels and are not automatically errors of the classifiers.

### Models

The 2B and 9B models belong to the same model family. They differ in depth (24 versus 32 layers), hidden size (2,048 versus 4,096) and attention heads (8 versus 16). Separate readouts were trained for each model on activations from the six layers above.

### Agentic evaluation

Agentic steps were labeled from the first positive reference judgment onward: that step and all later steps in the episode are positive, and earlier steps and ordinary episodes are negative. An inconclusive judgment does not mark a start, and episodes without an identified start are excluded. Steps without a usable label were dropped: one step for 2B and two steps for 9B. A positive step label marks the position in the episode and does not mean that the individual action was confirmed as harmful.

Recall is the share of flagged steps from the detected start of the side task onward. Validation evaluates final answers, while the agentic evaluation scores steps within longer tool-use sequences, so the two are reported separately.

### Results

| Metric | 2B | 9B |
|---|---:|---:|
| Statistical window readout, recall at 5% FPR | 28.2% | 71.8% |
| Statistical window readout, recall at 1% FPR | 14.0% | 46.2% |
| Statistical window readout, validation AUROC | 0.987 | 0.996 |
| Agentic AUROC across readouts | up to 0.81 | about 0.93 to 0.95 |

The agentic AUROC ranges summarize several readouts. At 5% FPR, the 9B model reaches 71.8% recall compared with 28.2% for the 2B model, and compared with the 1% FPR operating point recall rises by 14.2 and 25.6 percentage points, respectively, with more false alarms. Both models reach high AUROC on held-out examples from the training distribution. In the agentic setting, detection is weaker for the 2B model.

### Operating points and comparison scope

- **Thresholds.** The agentic thresholds were set from negative steps in the agentic evaluation set, and recall was measured on the positive steps of the same set. The reported operating points describe this evaluation set. Calibrating on one split and measuring on another is the first step of the planned protocol.
- **Model size.** The 2B and 9B comparison covers two models of one family that differ in depth, width and attention heads, and identical pretraining is not established. The comparison is reported as an observation about these two models.
- **Text judges.** The text-based judges in the reference evaluation do not see the agent's internal system instructions or internal reasoning, while the activations are produced under that context. A judge with access to the system instructions is part of the planned protocol.

### Evaluation status and next steps

| Item | Status | Plan |
|---|---|---|
| Validation set composition and split manifest | In preparation | Release with run artifacts |
| Agentic episodes, steps, positive steps, number of tasks | Being compiled | Report with the artifacts |
| Confidence intervals for recall at 5% FPR | Not yet computed | Episode-level bootstrap |
| Per-readout agentic AUROC and recall at 5% FPR | Not yet reported | Report for all four readouts |
| Achieved FPR at the 5% target | Not yet reported | Report per readout |
| Held-out threshold calibration | Not yet run | Split-half calibration, then fresh data |
| Variation across training seeds | Seed 0 only | Multiple seeds |
| Different choice of the six layers in the agentic evaluation | Not yet run | Repeat agentic evaluation |
| Random-weight and shuffled-label controls | Not yet run | Add to the protocol |
| Baselines using length, position or topic group alone | Not yet run | Add to the protocol |
| Text judge with access to system instructions | Not yet run | Information-matched comparison |
| Alerts per ordinary episode; time to first alert | Not yet reported | Compute from step scores |
| Per-task recall and FPR | Not yet published | Report with artifacts |
| Human label check | Not yet run | Sample-based agreement check |
| Adaptive evasion against the classifiers | Not yet tested | Add as a separate evaluation |

Further data are being collected, and this table will be updated.

## Study 3: Larger models

The same procedure was applied to models with 27, 122 and 397 billion total parameters from the same family. Preliminary evaluations suggest better detection than for the smaller models. Exact recall and AUROC values, readout-level results and run conditions will be added with the 2B/9B items above, together with a check that data, layer selection and threshold procedure match across sizes.

## Planned evaluation protocol

1. **Held-out threshold calibration.** Choose the 5% FPR threshold on one half of the episodes and measure recall and achieved FPR on the other half. A post-hoc split is a robustness check, and a new pre-specified test uses fresh data.
2. **Bootstrap intervals.** Resample whole episodes with replacement and report intervals for recall at 5% FPR and for AUROC.
3. **Alerts per episode.** Report the mean number of alerts per ordinary episode and the share of ordinary episodes with at least one alert.
4. **Text judge with equal information.** Use the same transcripts and scoring times, with the system instructions available to the judge, to test whether an advantage of internal activations remains when information access is matched.
5. **Further checks.** Multiple training seeds, random-weight and shuffled-label controls, simple-feature baselines, held-out whole groups, and adaptive evasion tests.
6. **Fixed conditions across model sizes.** Hold data, layers and threshold rules constant so that model size is the main varying factor.
7. **Dated plan.** The plan is dated and applies to future evaluations. Analyses completed before it are reported as such.

These steps use episode identifiers, labels and per-step scores, and step 4 additionally uses full transcripts and system instructions.

## Reproducibility

The 18-variant study is documented with a pinned model and tokenizer revision (`0cb88a4f764b7a12671c53f0838cd831a0843b95`), software versions, frozen cutoffs and independent replay of the trained heads. Run-level artifacts for the 2B/9B and larger-model runs (model and data revisions, run identifiers, split manifests, score files) are in preparation for release.

A signal that can be read out does not by itself explain a causal mechanism, and the studies measure detection under the stated conditions.

## Earlier work

Earlier proof-verification, code-monitoring and roleplay-deception experiments, including negative and inconclusive results, are described in the [earlier project overview](https://github.com/Fredo220/verified-reasoning-monitoring/blob/634df2cf3318561f267ef4b414ce8bf174dd25d0/README.md#where-it-started).

## License

Available under the [PolyForm Noncommercial License 1.0.0](LICENSE.md). Noncommercial research, experimentation and study are permitted under its terms. Commercial use requires separate permission. This is a source-available license.

Required Notice: Copyright 2026 Friedrich Reichelt.
