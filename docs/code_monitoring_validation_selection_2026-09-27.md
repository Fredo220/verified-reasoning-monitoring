# Frozen code-monitoring validation selection (2026-09-27)

This record was written after all 580 train and 260 validation candidate
receipts had matching local verifier verdicts, and before test candidates or
test labels were opened. The selection is immutable at
`data/code_monitoring/selection-v1/` (local, not part of the public handoff).
Its `selection.json` SHA-256 is
`9478f53710fe5fca9d4bc8535ce8070da0a647e2c5099e5d466bcb7b04ce1f77`;
the fitted `model.joblib` SHA-256 is
`73c50faee0a523ef712d20769d07c56cef8bc64fd2975e7aa257f21fd53385f4`.
The internal selection-record digest is
`a1c5a3cb74a5364ee421d2df70ac8ebd1567810e31d1f87074694615186ef801`.

| Validation measure | Frozen result |
| --- | ---: |
| Mixed tasks | 15 |
| Activation-scorable candidates | 230/260 |
| Static probe task-equal pairwise ranking | 0.7444 |
| Strongest non-internal baseline | text, 0.7278 |
| Prompt-final activation control | 0.4500 |
| Within-task shuffled-label control | 0.7722 |
| Earlier-token control | 0.6611 on its eligible tasks |
| Selected L2 `C` | 10.0 |
| Frozen pass threshold | 0.55 |

The registered H2 gate is `closed_control_margin`: the shuffled-label probe
outscored the primary probe on validation. Motion-only and Three-Reader are
therefore not run. The static probe's small validation edge over the text
baseline is not a held-out result and does not establish H1 or H1+.

Train verdict inventory: 304 pass, 203 test fail, 64 extraction fail, 5
timeout, 1 syntax fail, and 3 resource-related `infra_error` (all on
`Mbpp/255`). Validation: 128 pass, 99 test fail, 30 extraction fail, 3
timeout, and no resource-related `infra_error`. Per the pretest resource
amendment, the entire affected train task was excluded from fitting but
retained in the inventory. No train or validation candidate was regenerated.

The public-only test handoff contains 122 prompts and no reference code,
tests or labels. Its `test.jsonl` SHA-256 is
`ea24ba62c2c7392bffdc5c5fc6d065f4b3f5c9c130886eb19bfa6a69b49efa64`.
The frozen population manifest remains
`39f94d582471af971f80781b251dfd8418dba1d58f14e1066a24710fc6cfb7b1`.
No test result informed any selection or amendment above.
