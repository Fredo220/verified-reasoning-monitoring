# False verification reporting: results

Completed on 4 October 2026. Real model captures, all registered comparisons, private retrieval and independent local audits are complete. This is a separate, bounded adaptation. It does not replace or repair the earlier natural-deception studies.

## The short answer

**Some learned probes detected the scripted false reports even when the report wording changed. But a simple parser did just as well, and the more elaborate streaming recipe was not consistently better.**

The plain all-layer classifier with a mean readout detected 32/32 false reports and flagged 0/64 honest reports on each held-out split. Raw difference of means (DoM) ranked the changed-wording examples perfectly, yet detected 0/32 at its frozen cutoff. These are useful distinctions between representation, ranking and actual detection, not proof of a general deception detector.

![Detection and false alarms at the frozen cutoffs](figures/comparison.png)

## What we tested

We fed `meta-llama/Llama-3.2-3B-Instruct` scripted conversations about an explicit verification record. We measured the internal states while the model read the final report. **The model did not generate these reports or choose to cheat.**

Each identifier group had six matched cases: truthful success, fabricated success after failure, honest failure, fabricated verification without execution, honest nonexecution, and honest discussion of an invalid success claim. Only the two fabricated claims were positive. The success report was identical in the truthful and fabricated cases; their surrounding verification records differed.

The split sizes were 24 development, 192 training, 48 validation, 96 ordinary held-out and 96 changed-wording held-out records: **456 captures in total**. Each test split had **16 identifier groups, 32 positive reports and 64 negative reports**. Identifiers differed, but the underlying task template did not. Changing report wording is not transfer to another task domain.

All 28 registered hidden-state tuple indices were captured, with 3,072 features per index. The final tuple includes the model's final normalization. Raw DoM selected index 3 on validation; the token-logistic comparator selected index 1. The single-layer component comparison used DoM's selected index 3. Ties followed the frozen smallest-index rule, not a test-based choice. The all-layer heads used 86,016 concatenated features.

Weights and normalization were learned from training only. Validation selected epochs, layers and the negative-score 90th-percentile cutoffs; flags used strict `score > cutoff`. Neither test split changed those decisions. The four learned heads each had three predeclared readouts. **Every arm is reported; no winner was selected after seeing test scores.**

## Raw DoM and comparators

`Detected` counts false reports out of 32. `False alarms` counts honest reports out of 64. AUROC measures ranking across cutoffs, not the reliability of the frozen operating point.

| Method | Ordinary AUROC | Detected | False alarms | Changed-wording AUROC | Detected | False alarms |
|---|---:|---:|---:|---:|---:|---:|
| Raw DoM | 1.0000 | 32/32 | 6/64 | 1.0000 | 0/32 | 0/64 |
| Token-logistic comparator | 1.0000 | 32/32 | 10/64 | 0.7500 | 16/32 | 16/64 |
| Full-context TF-IDF | 1.0000 | 32/32 | 0/64 | 0.7500 | 0/32 | 0/64 |
| Output-only TF-IDF | 0.8750 | 0/32 | 0/64 | 0.8750 | 0/32 | 0/64 |
| Label-shuffled DoM | 0.7500 | 0/32 | 7/64 | 0.4995 | 0/32 | 0/64 |
| Visible-record parser | 1.0000 | 32/32 | 0/64 | 1.0000 | 32/32 | 0/64 |

DoM's cutoff was `0.3136378323844305`. Positive scores were approximately `0.3151-0.3161` on the ordinary split but `0.1505-0.1517` with changed wording. Ranking survived, but the score scale moved below the cutoff. We did not lower it afterward.

The unchanged-success-wording subset had AUROC 1.0 for primary DoM and 0.5 for output-only TF-IDF on both splits. However, **the shuffled direction also ranked that subset almost perfectly** (1.0 ordinary; 0.9980 changed). That control prevents treating this subset alone as convincing evidence of a specific false-reporting mechanism. The overall shuffled-direction performance was much weaker.

All 28 token-logistic fits reached their frozen 100-iteration limit and recorded convergence warnings. Their results are usable as the specified comparator, but not evidence of a fully optimized logistic baseline. No post-test optimizer adjustment was made.

## Learned-head component comparison

`Plain BCE` learns from individual token labels. `Window BCE` averages logits over 16-token windows before applying the loss. `Weighted window BCE` additionally weights those window losses with softmax. A mean readout averages final-report logits; a maximum takes the largest; EMA maximum smooths causally before taking the largest.

| Head / readout | Ordinary AUROC | Detected | False alarms | Changed-wording AUROC | Detected | False alarms |
|---|---:|---:|---:|---:|---:|---:|
| Single-layer plain BCE / mean | 1.0000 | 32/32 | 5/64 | 1.0000 | 32/32 | 0/64 |
| Single-layer plain BCE / EMA maximum | 1.0000 | 32/32 | 4/64 | 1.0000 | 16/32 | 0/64 |
| Single-layer plain BCE / maximum | 1.0000 | 32/32 | 3/64 | 1.0000 | 32/32 | 48/64 |
| All-layer plain BCE / mean | 1.0000 | 32/32 | 0/64 | 1.0000 | 32/32 | 0/64 |
| All-layer plain BCE / EMA maximum | 1.0000 | 32/32 | 1/64 | 1.0000 | 32/32 | 5/64 |
| All-layer plain BCE / maximum | 1.0000 | 32/32 | 4/64 | 1.0000 | 32/32 | 48/64 |
| All-layer window BCE / mean | 1.0000 | 32/32 | 7/64 | 1.0000 | 32/32 | 0/64 |
| All-layer window BCE / EMA maximum | 1.0000 | 32/32 | 4/64 | 0.7637 | 0/32 | 0/64 |
| All-layer window BCE / maximum | 1.0000 | 32/32 | 3/64 | 0.5000 | 0/32 | 16/64 |
| All-layer weighted window BCE / mean | 1.0000 | 32/32 | 8/64 | 1.0000 | 32/32 | 0/64 |
| All-layer weighted window BCE / EMA maximum | 1.0000 | 32/32 | 3/64 | 1.0000 | 0/32 | 0/64 |
| All-layer weighted window BCE / maximum | 1.0000 | 32/32 | 9/64 | 0.5469 | 0/32 | 0/64 |

On changed wording, maximum readouts produced very different errors. The all-layer plain maximum falsely flagged every honest failure, nonexecution and discussion (16 each). Its EMA maximum only falsely flagged five discussions. The token-logistic comparator falsely flagged all 16 discussions. All learned mean readouts had zero false alarms there, including the mandatory failure and nonexecution controls.

Selected epochs were 6 of 8 completed for single-layer plain BCE, 3 of 5 for all-layer plain BCE, 1 of 3 for uniform window BCE and 10 of 10 for weighted window BCE. Selection used validation loss. Very small window-training losses did not guarantee a useful held-out cutoff; these losses are not calibrated probabilities of deception.

## What we can conclude

1. Some frozen learned probes distinguished these context-dependent false reports under the registered wording change. A 3B model's states can carry decodable information for this narrow task.
2. A high AUROC is not enough. The DoM and weighted-window EMA examples ranked well while missing every changed-wording false report at their frozen cutoffs.
3. All-layer plain BCE with mean aggregation gave the strongest observed operating point among the predefined internal arms on these fixtures. This is a descriptive result, not a post-test selection or proof of general superiority. Single-layer mean aggregation also transferred without errors on the changed-wording split.
4. Adding window smoothing and weighted loss was not consistently helpful here. This does not refute the original streaming harmfulness method; its task, data, supervision and inference system differ.
5. The visible parser matched the strongest probe. We have not shown an advantage over parsing explicit verification records, natural deception detection, intent detection or prevention.

Reported bootstrap intervals resample identifiers within this fixed template (1,000 draws, seed 22). Perfect empirical rates can yield degenerate conditional intervals. They do **not** imply zero deployment error or broad semantic generalization. No earlier cohort is pooled into these results.

## Execution and audit evidence

The T4 run used the pinned model/tokenizer revision `0cb88a4f764b7a12671c53f0838cd831a0843b95`, FP16, batch one, Python 3.12.13, NumPy 2.0.2, scikit-learn 1.5.2 and Torch 2.11.0+cu128. The real seven-record interruption and fresh-process resume preserved all original receipts; 456 captures completed. The model was released before CPU head training. No base-model weights were loaded on the Mac.

The full export contained 1,042 ZIP entries, including 456 capture arrays, 1,029 inventoried output files and 12 frozen source files. Private streaming retrieval verified archive, member and current-source hashes, rejected unsafe paths and preserved the original Colab outputs.

Independent local replay passed both original projection auditors with unchanged registered bounds and cutoffs. It also reproduced the all-layer normalizer from the 192 training records (2,944 report tokens) and matched all four selected heads to their validation-selected epoch checkpoints. The local replay used the study-pinned NumPy/sklearn/SciPy versions; local Torch was 2.12.1, used only for safe checkpoint reading, not refitting. Maximum learned-head replay error was `4.3827041167787684e-05`, within the per-example predeclared FP32 bounds.

One operational repair was necessary: TF-IDF vocabulary strings had been saved as an object array. The original safe auditor correctly refused to load it. The [separate adapter](AUDIT-REPAIR.md) reconstructed vocabulary from training text, required exact serialized-byte equality, and supplied safe Unicode strings to the unchanged auditor. No pickle payload was loaded, no weights or scores were changed, and no fitting was repeated. Raw outputs, the adapter receipt and the initial failed-audit log remain available.

The focused and full local software gates passed again after the final notebook changes. The [gate ledger](GATES.md) records completion evidence rather than treating software tests as scientific results.

## Files and reproduction

- Frozen [protocol](PROTOCOL.md) and [component amendment](COMPARISON-AMENDMENT.md).
- [All 36 method/split rows as CSV](figures/comparison.csv); underlying result JSON retains condition counts, cutoffs, average precision and conditional intervals.
- [Raw results](../../../artifacts/reward-hacking/false-reporting-dom-v1/completed-colab/results.json) and [learned-head results](../../../artifacts/reward-hacking/false-reporting-dom-v1/completed-colab/ccpp-comparison/results.json).
- [Private local audit evidence](../../../artifacts/reward-hacking/false-reporting-dom-v1/local-audit/): transport, training replay and both projection receipts, plus audit scripts and replay instructions.
- Local [full export](../../../artifacts/reward-hacking/false-reporting-dom-v1/false-reporting-dom-ccpp-v1-complete.zip), 1,134,610,434 bytes; SHA-256 `c1ddc5c24f42ce09a385355c4df0d86ebfae0f07eaf7a19a2a46eae231b196bf`.
- Local [summary export](../../../artifacts/reward-hacking/false-reporting-dom-v1/false-reporting-dom-ccpp-v1-summary.zip), 27,012,725 bytes; SHA-256 `6b07f8e27cfd30e227a077d5c822e437fd9e011bf3ac378cd499f8390b158510`.

Artifacts are ignored by Git and remain private; these are local links, not a claim of public availability. The public report, comparison figure, CSV and supporting documentation were prepared for publication on 6 October 2026; raw archives were not included.

## Next step, not started

Freeze a separate semantic-transfer test with genuinely different tasks and naturally generated reports whose claims can be checked against independent execution records. Keep the visible-record parser, honest-failure controls, all registered arms and fixed operating points. Resolve logistic convergence on development data before that freeze. This completed fixture study alone cannot validate deployment reliability or rescue earlier natural-deception results.
