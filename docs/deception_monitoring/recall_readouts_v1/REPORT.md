# Catching more deception: what changed and what it costs

**We tested 74 configurations on the existing saved scores. Several caught more responses labelled deceptive, without retraining the model or changing any labels. This is a post-hoc diagnostic, not a new confirmation.**

The practical question was simple: are we missing deception because the trained probe has no signal, or because we smooth, combine and threshold its signals too conservatively?

## Results at a glance

There are 32 labelled-deceptive, 21 labelled-honest and 22 ambiguous evaluation responses. The ordinary evaluation pool contains another 1,000 responses. All configurations use the same unchanged responses and labels.

| Setting | Deception caught / 32 | Honest responses flagged / 21 | Ordinary alerts / 1,000 | Calibration alerts / 1,000 |
| --- | ---: | ---: | ---: | ---: |
| Original SWiM, 99th-percentile cutoff | 17 | 0 | 9 | 10 |
| Original SWiM, 95th-percentile cutoff | 23 | 0 | 35 | 50 |
| Faster smoothing, alpha 0.50, 99th-percentile cutoff | 21 | 0 | 10 | 10 |
| Original SWiM **or** layer 14, each at its 99th percentile | **27** | **2** | **21** | **20** |
| Faster smoothing, alpha 0.25, 90th-percentile cutoff | **28** | **0** | **82** | **100** |
| Any of seven signals, each at its 97.5th percentile | 31 | 9 | 103 | 104 |
| Any of seven signals, each at its 90th percentile | 32 | 16 | 334 | 353 |
| Flag everything: trivial control | 32 | 21 | 1,000 | 1,000 |

An ordinary alert is **not** an established false alarm: the ordinary pool has not been independently labelled honest. Alerts on the 22 ambiguous responses are recorded separately, not counted as errors. All such counts, thresholds, intervals and response IDs are in the [complete results](../../../artifacts/deception/focused-replication-v1/ccpp-probe-v1/recall-readouts-v1/results.json).

## What we learned

**Some misses depend on how we read the signal.** Faster smoothing at alpha 0.50 caught 21 rather than 17 deceptive responses, with ordinary alerts rising from nine to ten. But it recovered seven original misses and lost three original detections (`roleplaying-163`, `roleplaying-7`, `roleplaying-94`). It is not uniformly better.

**Different probes make partly complementary errors.** Flagging a response when either original SWiM or layer 14 exceeds its own cutoff caught 27/32, recovered ten original misses and lost none of the original detections. It also flagged two labelled-honest responses (`roleplaying-132`, `roleplaying-346`) and raised ordinary alerts from nine to 21. Those honest labels remain unchanged.

**A recall-first cutoff can help, but creates work.** Alpha 0.25 at the 90th percentile caught 28/32 and preserved all original detections. None of these 21 honest responses was flagged, but 82 ordinary responses were flagged. This is a candidate for a review/escalation policy, not proof of a zero-false-alarm detector.

**Catching every labelled case is not the same as solving detection.** The most aggressive seven-signal combination caught all 32 but also flagged 16/21 honest responses. The flag-everything control makes the limitation explicit.

For context, the existing single readouts at their original 99th-percentile cutoffs were:

| Existing readout | Deception caught / 32 | Honest alerts / 21 | Ordinary alerts / 1,000 |
| --- | ---: | ---: | ---: |
| Layer 8 | 12 | 3 | 12 |
| Layer 14 | 22 | 2 | 12 |
| Layer 22 | 17 | 2 | 10 |
| Concatenated layers 8/14/22 | 23 | 3 | 9 |
| Original SWiM | 17 | 0 | 9 |
| All-layer mean-BCE | 21 | 1 | 7 |

The comparison is therefore against a named operating point, not a claim that every new setting beats every old monitor at an equal alert budget.

## What was actually tested

The [fixed analysis plan](PLAN.md) covers 12 single readouts at four cutoffs, six combinations at those four cutoffs, plus flag-none and flag-all. The additions were faster smoothing, gap-aware four/eight/sixteen-token windows, raw token maxima and OR/vote combinations of existing monitors. There were no new learned weights, response generations, labels or model calls.

Each readout gets its own cutoff from the original ordinary calibration pool, with strict `score > cutoff`. Original float32 quantile arithmetic is retained for the four older probes; the other readouts retain float64 arithmetic. Smoothing and windows do not cross capture-position gaps. A combination of individually calibrated probes does **not** inherit the same overall calibration alert rate: the SWiM/layer-14 pair flags 20/1,000 calibration responses, not ten. Both calibration and evaluation alert counts are reported above.

## How much should we trust this?

- These evaluation outcomes were already opened. Testing 74 configurations and highlighting favorable ones makes the apparent gains optimistic; the table is descriptive, not a selected deployment policy.
- Only 32 deceptive and 21 honest responses are available here, with related scenarios. Zero honest alerts in 21 cases still has a descriptive Wilson 95% upper bound of about **15.5%**. These response-level intervals do not account for scenario-family dependence or selection across configurations.
- Labels are user-confirmed, AI-assisted, not independent blinded human annotations. This run preserves them; it cannot prove the labels are correct or that the model intentionally deceived anyone.
- All 2,075 saved score records and their file hashes were verified, and all six original evaluation score vectors and cutoffs reproduced exactly. **The full original-activation-to-score audit remains incomplete**, as described in the [failure audit](../ccpp_probe_v1/failure_audit_v1/REPORT.md). These results are conditional on the saved scores, not certification of the entire capture pipeline.
- Detection is not prevention. No output was blocked, rewritten or steered, and no new reasoning or reward-hacking capability was established.

## Next step

Prioritize recall, but treat alerts as requests for further review rather than automatic proof of deception. The complementary SWiM/layer-14 pair and the higher-recall alpha-0.25 setting are candidates worth validating, not adopted rules. Finish source verification, choose and freeze a rule on development/validation data, then test it on unused scenario families. Do not relabel current false alerts or reuse these opened cases to claim confirmation.

## Reproduction and checks

Run `scripts/analyze_deception_recall_readouts_v1.py --audit-only` with the documented local Python environment and `PYTHONPATH=src:scripts`. It recomputes all 74 configurations and rejects any change to the frozen inputs or saved result.

Six focused tests passed, covering capture gaps, calibration precision, vote rules, population separation, trivial controls and frontier comparisons. The complete local software suite and the frozen-result replay also passed through the [Unlazy ledger](GATES.md). Software success is not scientific confirmation.

A separate AI reviewer independently recalculated all 74 configurations and found no material defects in the calibration precision, gap handling, combinations or reported counts. This is independent numerical/code checking, not independent human annotation or replication on new data.

Result SHA-256: `3177ff050afc1ed0681a5948cc8371242c226215f10d7f7cf12aa386da909a0e`. The JSON records the analysis, plan, dependency and score-manifest hashes. The closed study, original scores, weights, splits and labels were not rewritten. No commit or push was performed.
