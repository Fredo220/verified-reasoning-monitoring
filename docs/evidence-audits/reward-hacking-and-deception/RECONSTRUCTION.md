# Two paper reconstructions

**Status: scoped source/method audit completed; empirical reproduction not run.** Published performance is `reported`, not `reproduced`. Missing specifications remain explicit. Findings refer to the validated [records](findings.json); exact versioned links are in the [source map](source-map.md).

## First: reward-hacking monitoring

### What is being detected?

Behavior that circumvents the intended task or evaluation: for example, falsifying a success report or interfering with verification. The label depends on the surrounding instructions and evidence. A failed program is not automatically a reward hack; an honest admission of failure is a particularly important negative control. The paper distinguishes considering, attempting and enacting a hack and makes no claim about subjective intent. **F-RH-02; RH-PAPER sections 2.1-2.2, Appendix C.**

### How the raw probe is built

1. Construct closely matched synthetic conversations that differ in hack versus honest behavior.
2. Select relevant token spans at one fixed residual-stream layer.
3. Average the positive and negative token activations separately.
4. Subtract the honest mean from the hack mean.
5. Score new token states by a dot product with that direction.

With positive positions `P`, negative positions `N`, and selected-layer state `h_t`:

```text
v = mean(h_t for t in P) - mean(h_t for t in N)
s_t = dot(v, h_t)
```

This is a difference-of-means detector, not a Three-Reader, an SAE or training the underlying LLM. The weighting unit in the published equation is the selected token position: long spans can contribute more than short ones. Appendix B lists 54 raw/projected conditions, including four raw-only honest failure/nonexecution controls. The projected-vector recipe is insufficiently specified for us to reconstruct faithfully. **F-RH-01 and F-RH-06; RH-PAPER section 3.1, Equation 1, Appendix B Tables 3-4.**

### How evaluation is separated from construction

Probe selection uses designated rollout pools; the reported evaluation excludes those samples. Detection is compared at the generic LLM monitor's false-positive rate. Labels come from a task-specific consensus judge, not independent human truth. Three judge passes must agree; quote repair can add calls and disputed cases are excluded. **F-RH-02 and F-RH-03; RH-PAPER sections 2.2 and 4.1, Figure 8.**

The paper also tests whether high-scoring prefixes precede later hacking under resampling. This is selected-prefix predictive evidence, not a demonstration that acting on the warning prevents errors. Non-SWE discovery starts without original labels but includes later held-out rubric checks; it should be described neither as general verified accuracy nor as merely qualitative. **F-RH-04 and F-RH-05; RH-PAPER sections 4.2 and 5, Figures 10 and 14.**

### What cannot currently be reproduced exactly

We have not located an attributable complete release or sufficient specifications for all token masks, projections, layer choices, score normalization, calibration splits and runtime identities. In particular, Equation 1's dot product and Figure 14's cosine axis cannot silently be treated as one recipe. Missing materials are a reproduction blocker, not evidence against the reported results. **F-RH-06.**

## Second: strategic-deception probes

### What is being detected?

The authors aim to distinguish strategically deceptive responses from honest ones. Their main instructed-pair training labels, however, encode an honest or dishonest *instruction condition*. Both conditions contain the same teacher-forced fact prefix. Actual evaluation uses separately graded, model-generated responses in scenarios such as concealment and sandbagging. Wrong answers, confusion and refusal must not automatically become deception labels. **F-DE-04; DE-PAPER section 3.2, Appendix G; DE-TRAINING-DATA `_get_dialogues`.**

### Exact released linear recipe

The inspected example configuration uses Llama-3.3-70B-Instruct, layer index 22, off-policy training and on-policy evaluation. At the pinned commit, the detector:

1. Extracts masked training token activations.
2. Fits a `StandardScaler` using training data only.
3. Fits L2 logistic regression with `C=0.1`, `random_state=42`, `fit_intercept=False`.
4. Applies the saved affine scaling to evaluation activations.
5. Produces a raw linear score at each selected response token and averages these scores by response.

```text
z_t = (h_t - training_mean) / training_scale
s_t = dot(w, z_t)
response_score = mean(s_t over selected response tokens)
```

The raw mean score is not itself a calibrated deception probability. Hidden-state indexing, chat-template application, special tokens and assistant masks are part of the method, not incidental implementation details. **F-DE-01; DE-PAPER section 3.1; DE-DETECTOR and DE-CONFIG.**

### A paper/code discrepancy to preserve

The paper says to omit the last five tokens of each training statement. The released `repe.py` splits on spaces and omits the final five resulting fields, ordinarily words, from the detection mask. The suffix remains in the input. A code-faithful reproduction must use the released boundary; a prose-faithful comparison would use tokenizer tokens and be reported separately. Neither should silently replace the other. **F-DE-02; DE-PAPER section 3.2.1; DE-TRAINING-DATA `_split_statement`.**

### The important false-positive denominator

The advertised 1% threshold is calibrated on ordinary Alpaca chat, not on honest responses in deception-related situations. At that threshold, the pinned example run reports:

| Honest evaluation population | Reported false-positive rate |
| --- | ---: |
| Roleplaying | 0.25 |
| Insider report | 0.7832586169242859 |
| Insider confirmation | 0.50 |
| Sandbagging | 0.5009784698486328 |

These are read from the released CSV, not independently recalculated. A high AUROC can coexist with a badly transferred decision threshold. Ordinary-chat false alarms and same-context honest false alarms must therefore be reported separately. **F-DE-03; DE-THRESHOLD `prompt_score_threshold`; DE-POSTPROCESS `get_results_dataframe`; DE-RESULTS lines 4-7.**

Ambiguous labels, honest discussion of deception and whole-response averaging further limit interpretation. Historical checkpoint provenance, numerical replay and applicable code/data reuse permissions remain unresolved; public source visibility does not settle those questions. **F-DE-04 and F-DE-05.**

## What we can reuse without changing our question

The reusable ideas are matched contrasts, explicit honest-failure controls, carefully masked residual states, simple linear detectors, train-only normalization and evaluation against honest responses in the *same* situations. The original directions cannot simply be copied into another model's hidden space. **F-X-01.**

These methods suggest a sequence of distinct tests:

```text
detect an observed false report
    -> predict it before it is completed
    -> test whether a fixed response to the warning improves reliability
```

Neither paper already establishes our full code-success/hallucination-prevention thesis. These are additional behavior-specific investigations, not new labels for the existing code-correctness study. A detector that recognizes dishonesty language but also flags honest failures has not solved the monitoring problem.
