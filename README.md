# Internal Signals for Reliable Model Statements

This project tests whether the internal activations of a language model carry a signal that separates two kinds of final answers: answers that contain a statement the model believes to be false, and answers that do not. A small classifier (a "readout") is trained on the activations of a frozen base model and then evaluated on held-out data, including agentic episodes with hidden side tasks.

## In plain terms

**The idea.** When a language model writes an answer, it computes millions of internal numbers along the way. This project asks whether those internal numbers show that the model is stating something it "knows" to be false, even when the text itself looks normal. If they do, a small and cheap detector could read them and raise an alarm.

**An example.** An agent is told to fix a bug. The fix fails, but the agent reports: "The tests pass." A reader who sees only the report cannot tell that it is false. The model, however, has seen the failed test run. The question is whether that mismatch is visible in its internal state.

**How it is tested.**
1. A language model is kept unchanged ("frozen").
2. While it reads or writes an answer, its internal values are recorded at six depths of the network.
3. A small detector (a "probe" or "readout") is trained on many examples labeled as honest or as containing a statement the model believes to be false.
4. The detector is then tested on examples it has never seen, including multi-step agent tasks in which the agent secretly pursues a side task.

**What counts as false here.** The label follows the model's own belief, not the objective truth. If the model honestly believes something wrong, that is a mistake, not a positive case. If the model states something it believes to be false, it is a positive case.

**How success is measured.** Two numbers are reported, and they answer different questions:
- **AUROC** asks: if one honest and one false answer are picked at random, how often does the detector give the false one the higher score? 1.0 is perfect, 0.5 is guessing.
- **Recall at a fixed false alarm rate** asks: if the detector may wrongly flag only 5 of every 100 honest steps, what share of the false ones does it catch?

A detector can sort examples well (high AUROC) and still miss cases once a fixed alarm threshold is in place. Study 1 shows this directly: one score sorted the examples perfectly but caught none of the false reports at its frozen threshold. For this reason the second number is the main criterion.

**What has been found so far.**
- In a controlled setting with scripted reports (Study 1), the pre-specified detector caught all 32 false reports and raised no false alarms on 64 honest ones, on both test sets. In this setting a simple text check reached the same result, so it mainly confirms that the method works where the answer is known.
- On a large set of honest and deceptive answers (Study 2), the detectors separate the two groups almost perfectly on data similar to the training data.
- In multi-step agent tasks, detection is weaker. With 5 false alarms per 100 honest steps, the detector catches about three in four positive steps for the larger 9B model (76.6%) and about one in three for the smaller 2B model (32.4%).
- Results for larger models are pending.

**What this does not show yet.** The results come from specific models, data and settings. Several checks are still open, including uncertainty ranges, repeated training runs, human label checks, a fair comparison with text-based judges that see the same information, and tests against models that try to evade detection. A signal that can be read out also does not explain *why* the model produces it. The section [Evaluation status and next steps](#evaluation-status-and-next-steps) lists these points.

### Glossary

| Term | Meaning |
|---|---|
| Activations | The internal numbers a model computes while processing text |
| Layer | One processing stage of the model; activations are read at six of them |
| Frozen model | The model itself is not changed; only the small detector is trained |
| Probe / readout | A small detector trained on the activations |
| Statistical window readout | A detector that summarizes activations over a span of text by their average and how they vary together |
| Context-contrastive probe | A detector trained to compare the same kind of answer in different contexts, so it learns when a statement contradicts what the model knows rather than how the statement is worded |
| Agentic setting | The model acts as an agent over many steps and uses tools |
| Hidden side task | A secret goal the agent pursues in addition to the visible task |
| False positive rate (FPR) | Share of honest cases wrongly flagged |
| Recall | Share of positive cases that are caught |
| Threshold calibration | Choosing the alarm threshold on separate data, so that the false alarm rate is controlled before testing |
| Held-out data | Examples not used in training, used only for testing |

## Contributions

- **A pre-specified comparison of 18 readout variants** on false task-completion reports, with cutoffs frozen before held-out scoring, every variant reported, and independent replay of the trained heads.
- **A separation of ranking from detection.** The comparison shows that a score can rank held-out examples perfectly (AUROC 1.00) and still miss every positive at a frozen cutoff, so AUROC alone is not used as the success criterion.
- **A four-readout comparison on Qwen3.5-2B and Qwen3.5-9B**, on validation data and on agentic side-task steps, reported at fixed false positive rates.
- **A context-contrastive probe:** trained with context-contrastive learning and a partial-AUC/CVaR tail loss for low-FPR operation, and evaluated with independent Neyman-Pearson threshold calibration.
- **A planned investigation of larger models** (Gemma 2 27B, gpt-oss 120B, Llama 4 Maverick 400B).
- **A stated evaluation protocol** for the next stage: held-out threshold calibration, episode-level uncertainty, alerts per episode, and an information-matched text-judge baseline.

## Why this matters for AI safety

Agents can report that work was done, or deny actions, in ways that the visible transcript alone does not settle. A monitor that reads internal states is one candidate for flagging such statements cheaply, at a chosen false alarm rate, without a second large model. The question tested here is whether such a signal exists, how strong it is at fixed operating points, and how it changes with model size.

## Overview of studies

The three studies use different models, data and evaluation procedures. Their metrics are reported separately and are not combined into a single success rate.

| Study | What was tested | Models | Status |
|---|---|---|---|
| Scripted false reports | 18 readout variants, specified in advance, on false task-completion reports | Llama-3.2-3B-Instruct | Completed and published |
| Belief-contradicting statements | Four readout types on validation data and on agentic side-task steps | Qwen3.5-2B and Qwen3.5-9B | Completed; run-level artifacts in preparation for release |
| Larger models | The same procedure on larger models | Gemma 2 27B, gpt-oss 120B (117B total, 5.1B active), Llama 4 Maverick 400B (17B active) | Results pending |

## Research question

Can classifiers trained on the activations of a frozen language model detect that a final answer contains a statement the model believes to be false, and how does this detection transfer to agentic settings at a controlled false positive rate?

## Definition of the target

A final assistant answer `r` in context `C` is labeled positive if it contains at least one asserted statement `s` that the model believes to be false:

```math
y_M(C,r)=\mathbf 1\!\left[\exists s\in\mathcal S(r):\mathrm{Bel}_M(\neg s\mid C)\right].
```

The label is defined by consistency with the model's own belief, not by objective truth. A factual mistake is therefore not automatically positive, and a statement that is objectively true can be positive if the model believes it to be false. Literally true but misleading statements and deception by omission are outside this definition.

Evidence about the model's belief comes from three sources: unambiguous conversation information, a stable answer after a pressure or cue is removed, and known training conditions. A complete per-example breakdown by source is not yet available.

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

### Training and calibration of the context-contrastive probe

The context-contrastive probe evaluated in Study 2 is trained with the objectives below and evaluated with independently calibrated thresholds.

#### Context-contrastive learning

For each context `C`, matched examples are built from a knowing falsehood and a truthful statement:

```math
x^+=(C,r^+),\qquad x^-=(C,r^-)
```

```math
\mathcal L_{\mathrm{contrastive}}
=\frac{1}{|\mathcal P|}
\sum_{(x^+,x^-)\in\mathcal P}
\log\!\left(1+\exp\!\left[m+s_\theta(x^-)-s_\theta(x^+)\right]\right)
```

`s_θ(x⁺)` is the falsehood score, `s_θ(x⁻)` the truthful-response score, `m` the margin and `𝒫` the validated comparison pairs.

Context-controlled pairs use the same statement under opposing contexts:

| Context | Statement A | Statement B |
|---|---|---|
| A is supported | Truthful | False |
| B is supported | False | Truthful |

The loss compares both responses within each context and the same response across opposing contexts.

#### Partial-AUC and CVaR optimization

```math
\mathrm{pAUC}_{\alpha}=\frac{1}{\alpha}\int_0^\alpha \mathrm{TPR}(u)\,du,
\qquad \alpha\in\{0.01,\;0.05\}
```

```math
\ell_{ij}=\log\!\left(1+\exp\!\left[m_t+s_\theta(x_j^-)-s_\theta(x_i^+)\right]\right)
```

```math
\mathcal L_{\mathrm{tail}}
=\frac{1}{N_+}\sum_{i=1}^{N_+}
\min_{\eta_i}\left[\eta_i+\frac{1}{\beta N_-}\sum_{j=1}^{N_-}\max(0,\ell_{ij}-\eta_i)\right]
```

`N₊` and `N₋` are the numbers of positive and negative examples, `β` is the share of the hardest negative comparisons and `η_i` is the auxiliary CVaR threshold. The tail estimate needs a sufficiently large negative candidate pool.

#### Combined objective

```math
\mathcal L_{\mathrm{BCE}}=-\frac1N\sum_{i=1}^{N}\left[y_i\log p_\theta(x_i)+(1-y_i)\log(1-p_\theta(x_i))\right],
\qquad p_\theta(x)=\sigma(s_\theta(x))
```

```math
\mathcal L_{\mathrm{total}}=\mathcal L_{\mathrm{BCE}}+\lambda_c\,\mathcal L_{\mathrm{contrastive}}+\lambda_t\,\mathcal L_{\mathrm{tail}},
\qquad \lambda_c,\lambda_t\ge 0
```

The weights `λ_c` and `λ_t` are selected on validation data. The individual objectives and their combination are compared under identical training and evaluation conditions.

#### Independent Neyman-Pearson threshold calibration

```math
\max_{\theta,\tau}\ \mathrm{TPR}(\theta,\tau)
\quad\text{subject to}\quad
\mathrm{FPR}(\theta,\tau)\le\alpha,
\qquad \hat y(x)=\mathbf 1[s_\theta(x)>\tau]
```

1. Freeze the trained probe.
2. Score independent, correctly labeled negative calibration examples and sort the scores `s₍₁₎⁻ ≤ … ≤ s₍ₙ₎⁻`.
3. Set the threshold to an order statistic:

```math
\tau_\alpha=s_{(k)}^-,
\qquad
\sum_{j=k}^{n}\binom{n}{j}(1-\alpha)^j\alpha^{\,n-j}\le\delta
```

`δ` is the permitted probability that the true FPR exceeds `α` because of calibration-sample uncertainty, assuming independent calibration examples from a fixed, continuous negative-score distribution. If no `k ≤ n` satisfies the condition, the sample cannot certify the requested operating point with this rule.

4. Freeze the threshold and evaluate on untouched test data.

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

## Study 2: Belief-contradicting statements (Qwen3.5-2B and Qwen3.5-9B)

### Data

The data are 129,776 responses from DolusChat, 64,888 honest and 64,888 deceptive, covering 64,888 scenarios. The label applies to the last assistant answer. Conversation histories (honest or deceptive) are crossed with final answers (honest, or containing a statement believed to be false), so the history alone does not determine the label.

| Conversation history | Final answer | Label |
|---|---|---:|
| Honest | Honest | 0 |
| Honest | Contains a statement the model believes to be false | 1 |
| Deceptive | Honest or corrective | 0 |
| Deceptive | Contains a statement the model believes to be false | 1 |

The validation set contains 5,000 examples, of which 2,500 are positive and 2,500 are negative. Variants of the same source prompt are kept in the same split, and length and message count were matched between the two classes. Whole groups of scenarios were not held out in the main comparison; holding them out is part of the planned protocol.

**Label quality.** For DolusChat, an automated check by a language model estimates the label error rate at 0.74% (95% interval 0.57% to 0.99%). A human agreement rate is not yet available. Automated error analyses point to ambiguous rules for allocating donations and to legitimate changes of network protection rules. These concern the reference labels and are not automatically errors of the classifiers.

### Models

The 2B and 9B models are Qwen3.5 models. They differ in depth (24 versus 32 layers), hidden size (2,048 versus 4,096) and attention heads (8 versus 16). Identical pretraining is not established. Separate readouts were trained for each model on activations from the six layers above.

### Agentic evaluation

Agentic steps were labeled from the first positive reference judgment onward: that step and all later steps in the episode are positive, and earlier steps and ordinary episodes are negative. An inconclusive judgment does not mark a start, and episodes without an identified start are excluded. Steps without a usable label were dropped: one step for 2B and two steps for 9B. A positive step label marks the position in the episode and does not mean that the individual action was confirmed as harmful.

| Model | Episodes | Evaluated steps | Positive steps | Scenarios |
|---|---:|---:|---:|---:|
| Qwen3.5-2B | 273 | 8,416 | 1,053 | 14 |
| Qwen3.5-9B | 665 | 19,455 | 4,541 | 14 |

Recall is the share of flagged steps from the detected start of the side task onward. Validation evaluates final answers, while the agentic evaluation scores steps within longer tool-use sequences, so the two are reported separately.

### Results of the four-readout comparison

| Metric | 2B | 9B |
|---|---:|---:|
| Statistical window readout, recall at 5% FPR | 28.2% | 71.8% |
| Statistical window readout, recall at 1% FPR | 14.0% | 46.2% |
| Statistical window readout, validation AUROC | 0.987 | 0.996 |
| Agentic AUROC across readouts | up to 0.81 | about 0.93 to 0.95 |

The agentic AUROC ranges summarize several readouts. At 5% FPR, the 9B model reaches 71.8% recall compared with 28.2% for the 2B model, and compared with the 1% FPR operating point recall rises by 14.2 and 25.6 percentage points, respectively, with more false alarms. Both models reach high AUROC on held-out examples from the training distribution. In the agentic setting, detection is weaker for the 2B model.

### Results of the context-contrastive probe

| Metric | Qwen3.5-2B | Qwen3.5-9B |
|---|---:|---:|
| Validation AUROC | 0.991 | 0.998 |
| Agentic AUROC | at most 0.86 | about 0.95 |
| Recall at 1% FPR | 23.8% | 53.2% |
| Recall at 5% FPR | 32.4% | 76.6% |

The values of the context-contrastive probe were obtained with independently calibrated thresholds. The calibration values (`α`, `δ`, size of the calibration set) will be published with the replication data. The procedure is described under Method, in Training and calibration of the context-contrastive probe.

### Operating points and comparison scope

- **Thresholds.** The agentic thresholds of the four-readout comparison were set from negative steps in the agentic evaluation set, and recall was measured on the positive steps of the same set. The reported operating points describe this evaluation set, and the achieved FPR is 5.0% (rounded) for all four readouts at both model sizes. No separate threshold calibration exists for these agentic results. Calibrating on one split and measuring on another is the first step of the planned protocol.
- **Model size.** The 2B and 9B comparison covers two Qwen3.5 models that differ in depth, width and attention heads, and identical pretraining is not established. The comparison is reported as an observation about these two models.
- **Text judges.** The text-based judges in the reference evaluation do not see the agent's internal system instructions or internal reasoning, while the activations are produced under that context. A judge with access to the system instructions is part of the planned protocol.

### Evaluation status and next steps

| Item | Status | Plan |
|---|---|---|
| Validation set composition | 5,000 examples, 2,500 positive and 2,500 negative; a manifest with per-example assignments is not established | Release a split manifest with the run artifacts |
| Agentic sample sizes | Reported above: 2B with 273 episodes, 8,416 steps and 1,053 positive; 9B with 665 episodes, 19,455 steps and 4,541 positive; 14 scenarios each | Keep with the artifacts |
| Confidence intervals for recall at 5% FPR | Not reported for the two recall values; bootstrap intervals exist for other metrics, and it is unknown whether the missing ones were computed internally | Episode-level bootstrap |
| Per-readout results | Agentic AUROC is shown in figures and recall at 5% FPR is tabulated; exact AUROC values are not consistently tabulated | Tabulate exact values for all four readouts |
| Achieved FPR at the 5% target | 5.0% (rounded) for all four readouts at both model sizes | Report unrounded values |
| Held-out threshold calibration | No separate calibration for the four-readout agentic results; the values of the context-contrastive probe use independently calibrated thresholds, with calibration values to be published with the replication data | Split-half calibration for the four-readout comparison, then fresh data |
| Variation across training seeds | Seed 0 only; no documented variation | Multiple seeds |
| Different choice of the six layers in the agentic evaluation | No results documented | Repeat agentic evaluation |
| Random-weight and shuffled-label controls | No results documented | Add to the protocol |
| Baselines using length, position or topic group alone | No results documented | Add to the protocol |
| Text judge with access to system instructions | No results documented | Information-matched comparison |
| Alerts per ordinary episode; time to first alert | No documented classifier alerts per ordinary episode or delays to first alert | Compute from step scores |
| Per-task recall and FPR | No full breakdown per task | Report with artifacts |
| Human label check | No results documented | Sample-based agreement check |
| Adaptive evasion against the classifiers | No results documented | Add as a separate evaluation |

"No results documented" means that no corresponding result is part of the available record. It does not imply that the analysis was never run.

Further data are being collected, and this table will be updated.

## Study 3: Larger models

The same procedure is being applied to the following larger models:

| Model | Parameters |
|---|---|
| Gemma 2 27B | 27B |
| gpt-oss 120B | 117B total, 5.1B active |
| Llama 4 Maverick 400B | 400B total, 17B active |

Results are pending. The models come from different families, so differences to the 2B and 9B results combine model size with family and architecture. Data, layer selection and threshold procedure will be matched across models and reported with the 2B/9B items above.

## Ongoing improvements: extending the readout

### Why extend the readout?

**In short.** The current detector works well at sorting honest from false answers, but in multi-step agent tasks it still misses many positive steps once the false alarm rate is fixed. The next step tests whether giving the detector additional kinds of internal information helps it catch more of them without raising more false alarms.

**Starting point.** The studies above indicate that, under the tested conditions, internal activations carry a signal that separates answers containing a statement the model believes to be false from other answers. They also show that sorting well and detecting well are different things. In Study 1, a score with AUROC 1.00 flagged 0/32 at its frozen cutoff. In Study 2, the context-contrastive probe reaches a validation AUROC of 0.991 (2B) and 0.998 (9B), while recall at 5% FPR in the agentic setting is 32.4% and 76.6%.

**The current detector.** The context-contrastive probe is built on the statistical window readout. It looks at a span of text and summarizes the internal values in two ways: their average (what is typically active) and their covariance (which values rise and fall together):

```math
s_{\mathrm{win}}(x)=f_\theta\!\left(\mu(x),\,\widetilde{\Sigma}(x)^{1/2}\right)
```

`μ(x)` are the projected mean features and `Σ̃(x)` is the shrunk covariance described under Readouts. Training combines BCE with the context-contrastive and tail losses, and thresholds are set with the independent Neyman-Pearson calibration.

**The question.** Can additional kinds of internal information improve detection at low false alarm rates beyond what this summary already captures? Three extensions are planned. None of them has been evaluated yet.

### Extension 1: Local token scores

**In short.** An average over a whole answer can hide a short false statement inside an otherwise honest answer, much as one wrong sentence disappears in the average of a long paragraph. This extension also scores each word piece (token) separately and pays extra attention to the highest scores.

**Details.** Each token gets a simple linear score, and the scores are combined in a way that lies between "take the average" and "take the maximum":

```math
q_t=w_{\mathrm{tok}}^\top h_t+b,
\qquad
g_{\mathrm{tok}}(x)=\rho\log\!\left(\frac1T\sum_{t=1}^{T}\exp\!\left(\bar q_t/\rho\right)\right)
```

`h_t` is the activation at token `t`, `q̄_t` is the locally smoothed score, `T` is the number of tokens in the window and `ρ > 0` sets how strongly high-scoring positions count. A small `ρ` approaches the maximum over tokens and a large `ρ` approaches the mean. The extension adds to the statistical window readout and does not replace it, so it differs from the token-layer readout above.

**Open point.** Labels say whether a whole answer is positive, not which token is responsible. Study 1 showed the risk: taking the maximum over tokens flagged 48/64 honest reports for two heads, while taking the mean flagged none, and window smoothing did not consistently help. `ρ` and the smoothing are therefore chosen on validation data, and false alarms on honest answers are reported separately.

### Extension 2: Sparse MLP neuron features

**In short.** So far the detector reads the model's main information stream (the residual stream). Inside each layer there are also individual units, called neurons, in the MLP block. This extension checks whether a small number of these neurons carries useful evidence, and lets the training decide which few to keep.

**Details.** For each neuron `j`, its activity over the text span is summarized by its average, its spread and its peak:

```math
v_j(x)=\begin{bmatrix}\mathrm{mean}_t(a_{j,t})\\ \mathrm{std}_t(a_{j,t})\\ \mathrm{max}_t(a_{j,t})\end{bmatrix},
\qquad
s_{\mathrm{MLP}}(x)=\sum_{j\in S}w_j^\top v_j(x)
```

The activations `a_{j,t}` are read before the MLP down-projection. A group penalty (group lasso) treats the three weights of one neuron as a unit and pushes unhelpful neurons to zero as a whole, so that only a few neurons remain in use:

```math
\mathcal R_{\mathrm{group}}=\lambda_G\sum_{j\in S}\lVert w_j\rVert_2
```

**Open point.** Using few neurons does not by itself mean that the detector generalizes or that those neurons explain the behavior. Neuron selection and feature normalization are fit on training data only, and evaluation uses held-out scenario groups.

### Extension 3: Combined probe

**In short.** The combined probe adds the two new sources of evidence to the current detector. If the new parts turn out not to help, training can set them to zero, and the combined probe is then the same as the current one.

```math
s_{\mathrm{comb}}(x)=s_{\mathrm{win}}(x)+\gamma\,g_{\mathrm{tok}}(x)+s_{\mathrm{MLP}}(x)
```

| Component | What it looks at | What it may add |
|---|---|---|
| Statistical window readout | Average and covariance over the text span | Overall patterns across tokens and features |
| Local token scores | Scores at individual tokens | Short, localized false statements |
| Sparse MLP features | A few selected neurons | Compact features that are easier to inspect |
| Combined probe | All three | Evidence that the parts do not capture alone |

With `γ = 0` and `w_j = 0` for all neurons, the combined probe reduces to the statistical window readout. Training keeps the existing objective and adds the group penalty:

```math
\mathcal L_{\mathrm{comb}}=\mathcal L_{\mathrm{BCE}}+\lambda_c\mathcal L_{\mathrm{contrastive}}+\lambda_t\mathcal L_{\mathrm{tail}}+\lambda_G\sum_{j\in S}\lVert w_j\rVert_2
```

All loss terms use the combined score. The weights `γ`, `λ_c`, `λ_t` and `λ_G` are selected on validation data.

### Planned comparison

**In short.** Each extension is tested on its own and in combination, under identical conditions, to see which part actually helps on new data and which only fits the training data better.

Four configurations will be compared:

1. Context-contrastive probe (statistical window readout, baseline)
2. With local token scores
3. With sparse MLP features
4. Combined probe

The goal stays the same: catch as many positive cases as possible while keeping false alarms at or below a chosen rate `α`:

```math
\max_{\theta,\tau}\ \mathrm{TPR}(\theta,\tau)
\quad\text{subject to}\quad
\mathrm{FPR}(\theta,\tau)\le\alpha,
\qquad \alpha\in\{0.01,\ 0.05\}
```

The comparison reports:

- **Detection at low false alarm rates:** recall at 1% and 5% FPR with independently calibrated thresholds.
- **Generalization:** results on held-out scenario groups and task types.
- **Complementarity:** whether the extensions catch cases that the baseline misses.
- **Regularization:** how the group penalty affects which neurons are selected, stability across training seeds, and generalization.
- **Cost:** detection relative to the additional computation.

Ablations, in which one component is removed at a time, separate the contribution of each part. Data, layers, splits and the threshold rule are held fixed across configurations, and the comparison follows the planned evaluation protocol below.

### Status

The results of Studies 1 and 2 are the baseline for this comparison. The three extensions are proposed and not yet evaluated, and no results are reported for them. The aim is to find the smallest combination of internal features that improves detection at a controlled false alarm rate on new data.

## Planned evaluation protocol

1. **Held-out threshold calibration.** Choose the 5% FPR threshold on independent calibration data with the order-statistic rule above, or on one half of the episodes, and measure recall and achieved FPR on the other half. A post-hoc split is a robustness check, and a new pre-specified test uses fresh data.
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
