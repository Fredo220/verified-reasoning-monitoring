# Do combined probes still help when alerts are matched?

**Yes, on these already-inspected cases, a small combination still catches more deception at the same calibration allowance. But adding every available signal makes the detector worse in important respects. This is further diagnostic evidence, not a fresh confirmation.**

We tested every non-empty combination of seven fixed signals: **127 subsets**, at four calibration alert allowances. A length-only baseline and flag-none/flag-all controls bring the total to **514 settings**. This is exhaustive for that particular seven-signal max-fusion design, not every possible monitoring method.

## The fairer comparison

Previously, the combined probes were allowed more alerts than a single probe. Here, every setting uses the same held-aside calibration allowance. One half of the original 1,000 calibration examples normalizes scores; the other half sets the cutoff. No evaluation label or outcome determines either operation.

The table illustrates a **2% calibration allowance: ten alerts out of 500 cutoff-calibration examples**, for every row. The actual number of alerts on ordinary evaluation responses can differ. Those responses have not been independently labelled honest.

| Setting | Deception caught / 32 | Honest alerts / 21 | Ordinary alerts / 1,000 |
| --- | ---: | ---: | ---: |
| Original SWiM | 19 | 0 | 12 |
| Faster SWiM, alpha 0.25 | 21 | 0 | 14 |
| Layer 14 alone | 24 | 2 | 18 |
| Layer 22 alone | 25 | 2 | 38 |
| Concatenated layers 8/14/22 | 24 | 3 | 21 |
| All-layer mean-BCE | 23 | 1 | 10 |
| **SWiM + layer 14** | **27** | **2** | **21** |
| All seven signals | 25 | 6 | 26 |
| Token count only | 0 | 0 | 30 |

![Detection and alerts under a common calibration allowance](matched-alerts.png)

The combination catches eight more than SWiM alone, but also flags two additional honest responses and nine additional ordinary responses. Against the highest-recall single head at this allowance, layer 22, it catches two more overall with the same two honest alerts and fewer ordinary alerts (21 versus 38). Against layer 14 alone, it catches three more with three more ordinary alerts. These are different trade-offs, not a universal winner or a guarantee of retaining every other method's detections.

This new combination takes the maximum of calibration-standardized scores and calibrates that fused score once. It is **not identical** to the previous OR rule with separately calibrated per-head cutoffs. The closed study and the earlier 74-setting results remain unchanged.

## Does the result depend on one cutoff?

All four allowances were fixed in the plan. Each cell gives **deception caught; honest alerts; ordinary alerts**, with denominators 32, 21 and 1,000 respectively.

| Calibration allowance | Original SWiM | Faster SWiM | SWiM + layer 14 | Highest-recall single head |
| --- | --- | --- | --- | --- |
| 1% | 17; 0; 9 | 18; 0; 8 | 25; 2; 18 | Layer 14: 24; 2; 12 |
| 2% | 19; 0; 12 | 21; 0; 14 | 27; 2; 21 | Layer 22: 25; 2; 38 |
| 5% | 24; 0; 39 | 24; 0; 35 | 28; 2; 35 | Concatenation: 29; 5; 59 |
| 10% | 27; 0; 88 | 28; 0; 85 | 29; 5; 75 | Layer 22: 29; 6; 111 |

The highest-recall single-head column is selected descriptively from all seven single readouts at each allowance; ties use fewer honest alerts, then fewer ordinary alerts. These are observed comparators, not separately validation-selected baselines. All single-head rows remain in the complete result file.

The combined detector has higher recall than SWiM at each tested allowance, but not higher recall than every single-head alternative: at 5%, concatenation catches 29/32 versus the pair's 28/32, with five rather than two honest alerts. At higher allowances the gap to SWiM is smaller. Faster smoothing is simpler and produces fewer honest alerts here, but it is not uniformly better: at 5% it catches the same number, and at 2% it misses one previously detected case (`roleplaying-7`).

## Robustness checks

**Paired uncertainty.** We ran 10,000 bootstrap resamples, using the same sampled exact scenario-question groups for every method. At the 2% allowance, the combination's recall gain over SWiM is **25 percentage points**, with a descriptive 95% interval of approximately **10.7 to 41.2 points**. Its honest-alert increase is 9.5 points, with an interval from 0 to 23.8 points. These intervals compare against SWiM, not the strongest single head, and are conditional on the fitted normalization/cutoffs and the accepted labels; they do not include calibration-fit uncertainty, selection across configurations or earlier experiments.

**Single-case sensitivity.** Removing any one exact group keeps that 2% recall difference between roughly **22.6 and 25.8 points**. This shows that one response does not account for the whole gain. It does not test broad scenario-family generalization: all 75 exact groups contain only one response, and broader-family labels are unavailable.

**Rubric sensitivity.** At 2%, the combination catches 17/20 grade-7 and 10/12 grade-6 responses. Its two honest alerts are both grade-2 responses; it flags none of the twelve grade-1 responses. All original labels remain unchanged. Counts for every grade, including ambiguous grades, are saved for every setting; these descriptive subgroups cannot resolve rating errors.

**Length control.** Captured-token-count alone has AUROC **0.475**, near chance, versus **0.957** for original SWiM and **0.969** for faster SWiM. Simple response length alone does not explain this ranking separation. This does not rule out length interactions, textual shortcuts or other confounds. Adding all seven signals has AUROC **0.850**, illustrating that extra heads can dilute a strong detector.

**Label-shuffle control.** We used 2,000 genuinely different label permutations, preserving the 32/21 binary class counts. Each permutation uses the same shuffled labels across all 127 combinations, and we take its best AUROC to account for searching this grid. The observed maximum AUROC is 0.969; the largest shuffled-grid maximum is 0.795. The Monte Carlo tail fraction is 1/2,001. This is a diagnostic under response-label exchangeability, **not a confirmatory p-value**: it does not account for earlier inspection/model selection, rating bias or unknown family dependence. The calculation was checked against [sklearn AUROC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html); the distinction between permutation assumptions and randomized tail calculations follows the [SciPy documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html).

## What is the most promising strategy now?

The user clarified the operational priority during reporting: **missing deception is more costly than sending an honest response for review**. We therefore separate a highest-recall candidate from a lower-alert comparator. This changes the preferred trade-off, not the data, labels, cutoffs or closed studies.

Within this tested grid, the highest nontrivial recall is **31/32 (96.9%)**. Three combinations reach it. Among those, combining **the existing concatenated-layer probe with the all-layer mean-BCE probe**, at the 10% calibration allowance, has the fewest honest alerts and then the fewest ordinary alerts: **6/21 honest alerts and 89/1,000 ordinary alerts**. At the same allowance, the highest-recall single head (layer 22) catches 29/32 with 6/21 honest alerts and 111/1,000 ordinary alerts. The combination recovers fourteen original SWiM misses and loses none of its original detections. Its calibration count is 50/500; its 22 ambiguous cases include alerts recorded separately in the complete results.

This is an outcome-selected **candidate to validate**, not a newly confirmed best detector. It catches 19/20 grade-7 and 12/12 grade-6 responses; its remaining labelled-deceptive miss is `roleplaying-332`. The other two 31/32 combinations flag 6/21 honest and 99/1,000 ordinary responses, or 14/21 honest and 105/1,000 ordinary responses. All are retained in the result file rather than concealed.

For comparison, the [earlier exploration](../recall_readouts_v1/REPORT.md) includes a different, more aggressive rule that catches 32/32 while flagging 16/21 honest and 334/1,000 ordinary responses. It uses a different calibration procedure and is not an equal-budget comparison with this new grid. The flag-everything control also catches every deceptive response; absolute recall alone is insufficient evidence that a useful monitor was learned.

Use high-recall alerts for **review or escalation**, not automatic accusations or proof of intent. Keep **SWiM + layer 14** as the moderate-alert comparator and **faster SWiM** as the simpler low-honest-alert comparator. More probes are not automatically safer: at the matched 2% allowance, all seven catch fewer deceptive responses and flag more honest responses than the small pair.

Neither is certified as the most reliable detector. The honest sample is only 21; zero alerts still has a descriptive Wilson 95% upper bound of about 15.5%. Choosing a deployable rule requires development/validation selection followed by unused scenarios, not more optimization on these opened evaluation cases.

## What this does not settle

The original activation-to-score audit is still incomplete, as documented in the [failure audit](../ccpp_probe_v1/failure_audit_v1/REPORT.md). All 2,075 saved score records and associated file hashes were checked, but the new calculations are conditional on those saved scores. Labels are user-confirmed and AI-assisted, not independent blinded annotations. The analysis establishes neither model intent, generalization nor prevention.

No model calls, retraining, new responses or label changes were made. No protected study artifact was rewritten, and no commit or push was performed. The next decisive experiment is to finish source verification, freeze one rule using development/validation data, and evaluate unused scenario families with independent label auditing.

## Reproduce and inspect

- [Complete immutable results: all 514 settings](../../../artifacts/deception/focused-replication-v1/ccpp-probe-v1/matched-alerts-v1/results.json), including thresholds, flags, grade counts, paired intervals and recovered/lost detections.
- [Fixed analysis plan](PLAN.md) and [Unlazy verification ledger](GATES.md).
- Analysis: `PYTHONPATH=src:scripts <documented-python> scripts/analyze_deception_matched_alerts_v1.py --audit-only`.
- Figure: `<documented-python> docs/deception_monitoring/matched_alerts_v1/plot.py`.
- Five focused tests passed; the full local software suite and exact result replay passed. The ledger records the status of independent numerical/code review; this does not validate human labels.

Result SHA-256: `b65f41c06fc3cebea252f2f37b31b9a05d5a32206351b1003235ef568ddc2ad9`. The result records the code, plan, input, prior-result and score-manifest hashes.
