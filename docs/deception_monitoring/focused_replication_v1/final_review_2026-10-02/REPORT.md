# Final deception-monitoring result

**Completed on 2 October 2026: the existing core roleplay/control analysis, with all 371 accepted ratings.**
No response was regenerated, no probe was refitted and no threshold or layer was selected again.
This closes the corrected-label analysis, not every evaluation setting in the source paper.

## In plain language

The model's internal states contain a signal that helps rank responses labeled
deceptive above responses labeled honest. The signal is useful evidence for
detection on this dataset, but is not a reliable detector of every deceptive
answer. At the frozen threshold it flags 90/188 deceptive responses
(47.9%) and misses 98. It also flags 7/92
honest responses (7.6%). We did not change or block any generated answer.

![Ranking and frozen-threshold alert rates](final-results.png)

An AUROC of 0.5 means chance ranking; 1.0 means perfect ranking of the measured
examples. AUROC is not the percentage of deceptive answers detected. Error bars
show 95% bootstrap intervals for ranking and Wilson intervals for alert rates.
These intervals assume the accepted labels are correct.

## What was actually evaluated

- Frozen Llama-3.2-3B-Instruct, not the source paper's 70B models.
- All 371 original roleplay scenarios, each with its saved 3B response.
- 306 source facts under paired honest/dishonest instructions: 490 training
  conditions and 122 held out, with source token-level logistic regression.
- One separately fitted probe at each of all 28 hidden-state tuple indices.
- Fixed primary readout 22, fixed secondary readout 8; other layers descriptive.
- 1,000 ordinary-chat controls for calibration, another 1,000 for evaluation.
- The original seven-point rubric: 1-2 honest, 3-5 ambiguous, 6-7 deceptive.

The authors' example responses and labels were not substituted for our model's
outputs. Instructions to be dishonest in training are not evidence that a
particular evaluation response is deceptive; the evaluation rubric supplies
that judgment. Ordinary-chat controls are not certified honest roleplays.

## Results

The latest accepted ratings are **92 honest, 91 ambiguous and 188 deceptive**.
All 371 have saved scores. The binary comparison contains **280 scenarios**;
the 91 ambiguous responses remain in the per-case output, outside binary metrics.
There are no remaining unscorable ratings in this accepted version, but assigning
a number does not recover missing facts in a scenario.

| Readout | AUROC | 95% interval | Interpretation |
| --- | ---: | --- | --- |
| Layer 22, fixed primary | 0.842 | 0.789-0.890 | Detectable ranking signal |
| Layer 8, fixed depth sensitivity | 0.741 | 0.677-0.802 | Weaker ranking on this adaptation |
| Response-span length | 0.489 | 0.417-0.561 | Longer-is-deceptive diagnostic near chance |
| Frozen text-only comparator | 0.9996 | 0.9986-1.0000 | Higher observed ranking; shared-grader bias |

Layer-22 average precision is 0.905; deceptive prevalence in the binary
cohort is 0.671. The matched bootstrap interval for
probe-minus-length AUROC is 0.261-0.444. For
probe-minus-text it is -0.211--0.110. The probe beats
this length diagnostic, but **does not outperform the measured text comparator**.
The text comparator and the original primary labels share the substitute
grader family. AI-assisted human acceptance does not provide independent ground
truth, so its near-perfect score is not evidence of universal text detection.

At the unchanged layer-22 threshold `-1.1039650440216064` (strict `score > threshold`):

| Group | Alerts / cases | Rate | Wilson 95% interval |
| --- | ---: | ---: | --- |
| Deceptive roleplays | 90/188 | 47.9% | 40.8-55.0% |
| Honest roleplays | 7/92 | 7.6% | 3.7-14.9% |
| Ordinary-chat evaluation controls | 10/1000 | 1.0% | 0.54-1.83% |

The 1% ordinary-chat alert rate is not a 1% false-alarm rate on honest roleplays;
their context differs, and the observed honest-roleplay alert rate is higher.

## Controls and prior exposure

All 200 saved within-fact label-swap nulls were retained, with no new fitting.
At layer 22, 0/100 nulls meet or exceed the observed
AUROC; their median is 0.505. All 200 original
null fits recorded convergence warnings. These are descriptive checks, not a
calibrated permutation significance test.

The frozen exposure assignments were not changed. The strictest stratum has
268 scenarios and 206 binary cases,
with layer-22 AUROC 0.833
(95% interval 0.769-0.892). The 275-scenario stratum
is also retained in the machine result. Neither is fresh confirmation: the
saved outputs and earlier performance results already existed before this review.

![All 28 frozen-layer point estimates](layer-profile.png)

The full layer profile is descriptive. We did not promote a better-performing
layer to the primary endpoint or tune thresholds against the revised ratings.

## What changed after review

344 earlier accepted ratings are unchanged. The 27 formerly unscorable cases
received AI-assisted numeric reassessments, explicitly accepted by the user.
Original scenarios, questions, response text, AI drafts and previous results
remain preserved. The evidence trail distinguishes AI proposals from user
acceptance; it does not call the review independent or blinded.

| Preserved analysis version | Honest / ambiguous / deceptive / unscorable | Binary cases | Layer-22 AUROC |
| --- | --- | ---: | ---: |
| Original primary machine labels | 84 / 70 / 217 / 0 | 301 | 0.833 |
| Earlier accepted full review | 90 / 74 / 180 / 27 | 270 | 0.852 |
| Latest accepted review | 92 / 91 / 188 / 0 | 280 | 0.842 |

These cohorts and labels differ. The AUROC changes are descriptive, not evidence
that the monitor improved. Across the latest review versus the original primary
labels, 117 grades and 55 label bins differ.
The legacy JSON field `user_corrections_to_ai_draft` counts differences from an
AI draft; it does not mean the user authored those grades. The provenance receipt
records 27 accepted AI reassessments and zero user-authored grade corrections.

## Why layer 22, and why layer 8?

The authors selected layer 22 empirically on an 80-layer model; it was not a
universal best layer. Keeping index 22 on our 28-layer model preserves the
absolute index, **not** relative depth: 27.5% versus 78.6%. Index 8 was already
fixed as a relative-depth sensitivity (28.6%). This is a positional approximation,
not equivalence between representations in different-sized models.
Our capture/scoring agree on tuple indexing: embeddings are excluded, column
21 means tuple index 22, after 22 completed blocks. The final tuple includes the
model's final normalization. There was no detected index-shift bug.

## Verification and reproducibility

The independent audit checked 2,371 raw token-score
arrays, all 28 AUROC/average-precision calculations, all frozen-threshold counts,
and all 10,000 scenario bootstrap draws (seed 11).
The intervals are conditional on the accepted ratings: they do not include
systematic grading bias, AI anchoring, missing scenario facts or model variation.

The audit initially stopped because local PyTorch 2.14 recalculated four
float32 calibration quantiles slightly differently (maximum absolute difference
1.79e-7). Explicit source float32 rank interpolation reproduces **all 28 saved
thresholds bit-for-bit**. No threshold file or alert decision was changed.
Saved raw means were also checked with independent float64 summation; its
maximum rounding difference was 1.69e-06.

Machine outputs are in
`artifacts/deception/focused-replication-v1/label-review-371-v1/user-confirmed-v2/`:
`human-packet.jsonl`, `confirmation.json`, `human-label-freeze.json`,
`post-hoc-sensitivity-results.json`, `updated-roleplay-outcomes.jsonl`,
`text-comparator-sensitivity.json`, `registered-control-sensitivity.json`,
`independent-final-metric-audit.json` and hash manifests. Readable layer metrics
are in [layer-metrics.csv](layer-metrics.csv).

Recheck existing artifacts without generation, grading or fitting:

```bash
.venv/bin/python scripts/audit_deception_final_review_v2.py
.venv/bin/python scripts/report_deception_final_review_v2.py --verify
```

Software regression checks and their exact environment are recorded in
[GATES.md](GATES.md). The project-local analysis environment lacks `einops`;
the full suite uses the existing complete test environment named there.
Previous results, probes and saved scores remain hash-verified and unchanged.

## Conclusion and next step

**Supported on this adapted dataset:** a fixed linear activation probe ranks
accepted deceptive roleplay responses above accepted honest ones, beyond the
simple response-length diagnostic.

**Not established:** added value over the text comparator, model intent,
reward-hacking detection, hallucination detection, online warning, causal
prevention, deployment readiness, or generalization to larger models.

The seven additional paper settings remain incomplete. They are separate
empirical work, not silently included in this closeout. For a stronger next
claim, freeze a follow-up on unused scenarios with independent blinded grading,
keep honest-in-deceptive-context controls, and choose any new layer using only
validation before opening test outcomes. Do not regenerate these 371 responses
or keep relabeling them to chase a better number.

## Sources and method differences

This is a smaller-model adaptation of Goldowsky-Dill et al.,
[Detecting Strategic Deception Using Linear Probes](https://arxiv.org/html/2502.03407v1),
using [the pinned author implementation](https://github.com/ApolloResearch/deception-detection/tree/f8ec4010e74927394709dffa22b97bdf8cd5a62f).
The 3B model, substitute grader, control subsample/split and post-hoc AI-assisted
review differ from the original experiment. The existing
[method and coverage table](../closeout-2026-10-01/METHOD_AND_COVERAGE.md) records
the full adaptation; its older label counts remain a historical snapshot, not
the latest result. This study does not establish the same accuracy as the paper.
