# Compact audit bundle

This folder is a public-size export of the completed adaptive HumanEval+
trajectory follow-up. Its `predictions.json` was sealed before any reserve
verdict was opened. `verdicts.jsonl` preserves the 304 original verifier
records in prediction order. `result.json` is the immutable machine report.

The local full receipts, checkpoint weights and activation arrays are not
included here. Recalculating score-based metrics from this bundle is possible;
replaying the model or proving capture fidelity requires those larger local
artifacts. See the [result report](../../../docs/trajectory_followup_result_2026-09-27.md)
for methods, limitations and interpretation.

Run `python protocol/evidence/trajectory-followup-v1/export.py` from the
repository root to rebuild and check the bundle from the local
`data/code_monitoring/trajectory-followup-v1/` directory. The export refuses
to overwrite a different existing file.
