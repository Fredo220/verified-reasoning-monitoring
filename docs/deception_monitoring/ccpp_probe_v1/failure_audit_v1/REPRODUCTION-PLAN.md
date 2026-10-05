# Reproduce this audit, not the generation run

Run from `/Users/friedrichreichelt/Documents/verified-reasoning-monitoring` with the existing Python 3.12 environment. Do not run an old notebook's generation or training cells.

```bash
env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' scripts/audit_deception_ccpp_recovery_v2.py --audit-only
env PYTHONPATH=src:scripts OPENBLAS_NUM_THREADS=2 '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' scripts/audit_deception_ccpp_recovery_v2.py --available-source-checks
env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' -m pytest -q -p no:cacheprovider
```

The first command verifies all 2,075 paired score records, frozen inputs and separate diagnostic calculations. The second checks the locally available source captures one at a time and defers full-matrix calculations above 512 captured tokens to avoid exhausting the 8-GB Mac. This is an audit allocation bound, not a truncation of the scientific data.

## Finish the two missing checks

1. Restore private access to the remaining original captures in the CPU recovery notebook. Process one capture at a time; do not download the approximately 111-GiB activation corpus onto the Mac. The original failure log identifies the first failing interval, not the precise record. Preserve the original oracle and tolerances. Log the exact failing ID, positions and numerical discrepancies before proposing any independently reviewed audit-only correction.
2. Complete full source coverage, including generated-output bytes, and independently review the result. Successfully checking receipts or a sample cannot replace this step.
3. With explicit permission for new model calls, run a separately recorded 24-prompt factual-comprehension diagnostic: 12 unambiguous missed scenarios, each with answer-order reversal. Use the same pinned model, no fine-tuning and no regenerated study answers. Measure correct scenario-fact choice, not self-awareness or intent. This is a diagnostic on previously inspected scenarios, not fresh confirmation.

## Only then evaluate a recall-first follow-up

Keep the current weights and results unchanged. Set the intended recall/false-alert policy on development or validation data, using independently audited honest scenarios as well as ordinary chat. Freeze the policy before a new, unused scenario-family evaluation. The post-hoc cutoff table is a sensitivity analysis, not a newly selected operating point.

No paid compute, alternative grader, retraining, relabeling, commit or push is part of this audit.
