# Code-monitoring analysis freeze (2026-09-27)

This record was written while the protected training candidates were still
being generated. No protected train, validation or test verifier labels had
been opened. The open development results and the separate population freeze
are reported in `docs/code_monitoring_population_freeze_2026-09-27.md`.

## Frozen analysis

- Primary population: all activation-scorable natural candidates from the
  frozen train, validation and test task splits. Report unscorable candidates
  and all-candidate verifier outcomes separately; do not silently exclude
  their failures from the study inventory.
- Primary model: all-layer, final-code-token L2-normalized static activation
  probe. Fit on train only; select `C` from `{0.01, 0.1, 1, 10}` by task-equal
  validation pairwise ranking, with validation log loss as tie-breaker.
- Non-internal comparator: sum and mean token log-probability and a
  character-TF-IDF + length/syntax/log-probability logistic model. The learned
  baseline and probe both weight training tasks equally. Select the strongest
  non-internal method by validation task-equal ranking.
- Controls: prompt-final activation probe, within-task train-label shuffle,
  and the non-final generated-token probe on candidates with a distinct
  earlier code position. The H2 gate in `docs/code_monitoring_protocol.md`
  remains unchanged. The shuffled model may select its `C` on validation;
  this is conservative for the primary model when comparing their rankings.
- Secondary direction: within-mixed-task pass-minus-fail direction on train
  only, task-equal average, with an independent within-task shuffled null.
  Too few mixed training tasks or identical directions are `not_evaluable`.
  It cannot change the primary result.
- Freeze the chosen models, baseline, validation threshold and H2 gate in a
  checksum-bound local selection artifact before exporting or labeling test.
  The protected test evaluation is one task-clustered comparison, 10,000
  bootstrap draws with seed `20260926`, and at least 12 mixed test tasks.
  Report all-task AUROC/AUPRC and false alarms/missed errors descriptively.

## Software and evidence identity

The full local suite passed with `475 passed, 7 skipped` before this record.
The test-skipped cases are not empirical proof of the Colab run. The frozen
population manifest is
`39f94d582471af971f80781b251dfd8418dba1d58f14e1066a24710fc6cfb7b1`.
An integration-only fit on two disjoint halves of the **open development**
tasks completed on the local Mac in about four seconds using the actual
28-layer receipts. Its selected settings and scores are not scientific
outcomes and do not enter protected validation selection.

| File | SHA-256 |
| --- | --- |
| `src/vrm/code_analysis.py` | `93a3a9a5e749cd7cb5524e2bf0572a25139e9e0726e08357293696206b84398c` |
| `src/vrm/code_baselines.py` | `c41a4986c7000d8cec27f5966bcdb13a250d5a7007b7cdb5a09eba422abbd1a4` |
| `src/vrm/code_probe.py` | `67d37e74f1a18cdfe97048a719bd4bfad30cc4131cc37cd752958470e20d0f3e` |
| `src/vrm/code_selection.py` | `9f47b3b4a440dd792df06f212ef30b8ae1828b20f22ceaa2e87d53095a47aac0` |
| `src/vrm/code_study.py` | `7a8eac39f68459452fbc7e5d2fa510c156ad17a1af764e283963e2e81238f94a` |
| `src/vrm/code_study_cli.py` | `db9fcd179d5be6aa1414fe4ce9cf5785550ed062b13511185f4ef12b816ab3c6` |
| `src/vrm/code_verify_batch.py` | `0f7d5bbf1d589f608740128177ef33e93df44ba448e7a10eeb917b0b15548905` |
| `configs/code_monitoring.json` | `cf0fc1bbc959460d7685a79f4cc5945c4fb746007b72c777fcca9dc0a0aa1335` |

The uploaded public-only train/validation handoff ZIP has SHA-256
`e32bfcc3e2e77150f203e1e85b496f59ee1229ecb8304a0c1a3d6755466c7a69`.
Its manifest contains both protected split memberships, but the archive
contains only train and validation prompts, not test prompts, solutions,
hidden tests or verifier code. The private verifier remains local.

Any post-freeze analysis-code correction must be dated, justified, tested and
reported before the protected test is opened. It must not be selected for a
better observed test outcome. Free Colab interruptions and missing downloads
are operational states, not hypothesis failures.
