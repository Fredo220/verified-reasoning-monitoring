# Held-out result: completed-code monitoring (2026-09-27)

## Question and answer

Can a small probe of a frozen code model's activations rank a passing Python
solution above a failing one for the **same unseen task**? Yes, under the
registered H1 criterion. Did it outperform the best validation-selected
non-internal baseline? No. The result supports limited within-task
decodability, not a practical advantage for internal monitoring.

This study is separate from the Gemma/Lean and Kimina development tracks. It
tests selection among completed candidates, not online error detection,
improved generation, causal steering, or general reasoning quality. The
[design](code_monitoring_protocol.md),
[population freeze](code_monitoring_population_freeze_2026-09-27.md),
[analysis freeze](code_monitoring_analysis_freeze_2026-09-27.md),
[verifier resource amendment](code_verifier_resource_amendment_2026-09-27.md),
and [validation selection](code_monitoring_validation_selection_2026-09-27.md)
preceded the test evaluation. Operational verifier corrections and their
timing are recorded in those amendments.

## Execution and coverage

The frozen generator was `Qwen/Qwen2.5-Coder-1.5B-Instruct` at commit
`2e1fd397ee46e1388853d2af2c993145b0f1098a`, FP16 on a free Colab T4.
Four natural candidates were sampled for each of 122 task-grouped MBPP+
test problems. The 488 candidate receipts were mirrored individually to
private Drive storage. A second Colab pass checked each mirror byte-for-byte,
archived all 488 receipts, and read back the archive hash. The local copy has
the same SHA-256:

`00f5671b121e1d6a907f3dbc87cbd43ccb0904cd2239a7fe16d286e7b0746665`

The local, pinned, isolated EvalPlus verifier produced 488/488 matching
verdicts; an unsharded replay reported zero missing. Results below refer to
functional test passage, **not** formal correctness. The exact source and
population identities remain in `configs/code_monitoring.json`; the test
manifest is `39f94d582471af971f80781b251dfd8418dba1d58f14e1066a24710fc6cfb7b1`.

| Test inventory | Count |
| --- | ---: |
| Tasks / candidates | 122 / 488 |
| Pass / functional-test fail | 230 / 213 |
| Extraction fail / syntax fail | 44 / 1 |
| Resource or infrastructure failures | 0 |
| Activation-scorable candidates | 444 |
| Tasks with at least one passing candidate | 74 |
| Mixed pass/fail tasks, all candidates | 36 |
| Mixed pass/fail tasks, activation-scorable | 26 |
| Scorable pass/fail pairs on mixed tasks | 78 |

All 44 unscorable candidates were extraction failures. They remain in the
all-candidate inventory and are not treated as missing verification. The
registered primary endpoint uses the 26 mixed tasks, with tasks rather than
candidates or pairs as the independent units. Mixed tasks were 36/122 (29.5%)
in the all-candidate inventory and 26/122 (21.3%) after activation-scorability
filtering. The all-candidate pass prevalence was 230/488 (47.1%); among
scorable candidates it was 230/444 (51.8%).

## Frozen test comparison

The primary probe uses the last actual code-content token at all 28
post-block layers. Its L2 regularization (`C=10.0`) and the non-internal
champion were selected on validation before any test verdict was opened.
The champion combines code-text TF-IDF, length/syntax features and token
likelihood. All ranking methods below use the same 444 activation-scorable
candidates. A value of 0.5 is chance within a mixed task.

| Task-equal within-task pass/fail ranking | Test score |
| --- | ---: |
| Static activation probe, primary | 0.679 |
| Text/length/syntax/likelihood baseline, selected on validation | 0.737 |
| Mean token log-likelihood | 0.712 |
| Sum token log-likelihood | 0.699 |
| Prompt-final activation control | 0.452 |
| Train-only pass-minus-fail contrast direction, secondary | 0.455 |
| Within-task shuffled-label contrast direction, secondary null | 0.478 |

Across 10,000 task-cluster bootstrap samples (registered seed `20260926`),
the primary score was **0.679, 95% CI [0.526, 0.821]**. Its paired difference
from the selected text baseline was **-0.058, 95% CI [-0.256, 0.154]**.
Consequently, the frozen evaluator returned
`H1_supported_H1_plus_not_supported`: the H1 interval is above 0.5, but the
probe did **not** show added value over the non-internal comparator. The wide
paired interval also prevents a claim that text is generally superior.

Descriptive AUROC was 0.781 and AUPRC 0.778 across the 444 scorable
candidates from all tasks; neither replaces the within-task endpoint. At
the validation-frozen pass threshold of 0.55, the
task-equal false-alarm rate was 0.255, the missed-error rate 0.366, Brier
score 0.201, and ten-bin ECE 0.100. These error rates are too high to treat
the probe as a reliable decision rule.

## Controls and interpretation

H2 was **not run**. On validation the within-task shuffled-label probe ranked
0.772, above the primary probe's 0.744, so the preregistered
`closed_control_margin` gate failed. Motion-only and Three-Reader cannot be
introduced after seeing the test result to rescue it. The train-only
contrast direction's held-out score of 0.455 also gives no support for a
simple universal pass-minus-fail direction. The main evaluator omitted the
already registered secondary shuffle comparison. It was calculated once
after the primary test result was sealed, using the unchanged fitted primary
and null directions and the same 26 test tasks: 38 mixed training tasks
contributed to the directions; the secondary score's 95% task-bootstrap CI
was [0.301, 0.615], and its paired difference from the shuffled null was
-0.022, 95% CI [-0.272, 0.228]. No parameter or sample was reselected.

The prompt-final control is not a perfectly tied 0.5 control in the stored
FP16 receipts: 25 of 366 within-task comparisons of its arrays were not
bit-identical, with a maximum absolute entry difference of 0.125. Its 0.452
rank must not be interpreted as evidence of an inverse prompt-difficulty
signal. This post-test numerical audit does not change any model or endpoint.

The decisive negative finding is comparative: for these completed MBPP+
candidates, the internal probe did not beat inexpensive code-text features.
The above-chance H1 result is narrow. Only 26 test tasks contribute to that
contrast, the 95% interval is wide, the validation shuffled-label control
was stronger than the primary probe, and public benchmark pretraining
contamination cannot be ruled out. Functional tests can miss incorrect code.
There is no evidence here for a causal mechanism, a safer model, or a cheaper
route to correct outputs.

## Evidence and reproducibility

The frozen selection record SHA-256 is
`9478f53710fe5fca9d4bc8535ce8070da0a647e2c5099e5d466bcb7b04ce1f77`;
the fitted model SHA-256 is
`73c50faee0a523ef712d20769d07c56cef8bc64fd2975e7aa257f21fd53385f4`.
The local test result is
`data/code_monitoring/test-evaluation-v1/heldout-test-result.json`, SHA-256
`90da8960e0fd8e75943d75b9329c620836412d8f759d310851b66ec949f0cea9`.
Its request binds the selection digest
`a1c5a3cb74a5364ee421d2df70ac8ebd1567810e31d1f87074694615186ef801`
to test evidence digest
`eec853d35e794c7714e0330f0ae60a2c20f080300824a1e50355c8e74c8153a1`.

Generation took 1,065.9 s of summed candidate time plus 44.3 s for
activation replay/capture; Colab reported 19.4 minutes for the resumed full
test cell, including its checks. The local suite passed after execution:
`480 passed, 7 skipped`. The full receipts, verifier verdicts and fitted
model currently remain in ignored local/private storage, not in the public
repository. This report and hashes permit an integrity audit, but independent
reproduction requires an explicit artifact release and its own resource and
security review.

The next scientific decision is whether to investigate why the text baseline
and the validation label-shuffle control were so strong. That would be a new
study, not a reinterpretation or retuning of this held-out test.
