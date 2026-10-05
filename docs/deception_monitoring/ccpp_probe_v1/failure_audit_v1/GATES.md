# Gates: deception-miss explanation audit

OWNS: scripts/audit_deception_ccpp_recovery_v2.py, tests/test_deception_ccpp_recovery.py, docs/deception_monitoring/ccpp_probe_v1/RECOVERY_STATUS.md, docs/deception_monitoring/ccpp_probe_v1/failure_audit_v1/**, artifacts/deception/focused-replication-v1/ccpp-probe-v1/failure-audit-v1/**

Scope: test label, scoring, operating-point and capability explanations without changing the frozen experiment. No retraining, generation, purchases, commits or replacement labels.

- [x] G1: frozen identities, every saved score pair, EMA, calibration and diagnostic calculations verify
  CHECK: env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' scripts/audit_deception_ccpp_recovery_v2.py --audit-only
  EXPECT: CCPP_FAILURE_DIAGNOSTICS_VERIFIED
  EVIDENCE: automatic-evidence=v1; definition-sha256=4947bc3cde7b4c7064bb566468073ae74486d65ae005272a2dc53d2f2d04e980; exit=0; EXPECT=matched; output-sha256=6bb5b3149dba02002d2bb8d03fd5fc1892b23971f3116b96c1692a33d2bf27eb; output-bytes=39; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=c6a20dc9bebb/38 entries

- [x] G2: score-blind case review and outcome-independent sample are documented with AI-assisted provenance
  EVIDENCE: LABEL_REVIEW.md records the 15-case selected diagnostic and all 24 hash-selected notes; the separate AI reviewer fixed the latter before opening grades/scores and disclosed prior exposure for five cases. Original labels unchanged; not independent human confirmation. Sample sha256=75aff4d2451e52a3c43850370471182e6ca85996dcbec26804ed528eda2cffbf.

- [ ] G3: every original activation projection verifies against the frozen oracle or an independently reviewed, separately versioned numerical diagnosis
  EVIDENCE: unmet; original full projection failure remains unidentified. All 32 manageable local captures pass original float64 tolerances and token/source checks; 2041 missing locally, 2 memory-deferred. Partial source record sha256=4093ff08e4e12e3a52861288d5aad3e5baab4926f8c3e769817f3402ca00b262. Full private storage access blocked by shared Drive API quota; targeted UI downloads are not full coverage.

- [ ] G4: fresh matched scenario-comprehension controls distinguish base-model failures from probe misses
  EVIDENCE: unmet; zero new model calls. One consolidated question requests approval for a separate 24-prompt matched factual-choice CPU diagnostic using the frozen model. No answer received yet; existing probe scores cannot close this gate.

- [x] G5: local tests cover negative controls and the complete software suite has no regression
  CHECK: env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' -m pytest -q -p no:cacheprovider
  EXPECT: /(?:^|\n)[0-9]+ passed(?:, [0-9]+ skipped)?(?:, [0-9]+ warnings?)? in [0-9.]+s(?: \([0-9:]+\))?(?:\n|$)/
  EVIDENCE: automatic-evidence=v1; definition-sha256=5fb9c95914529036a153b8b47c1eb8726e0fc48b670450602c6c38b8e4203889; exit=0; EXPECT=matched; output-sha256=95e6904f4639d484e96f3cbe0bf4d3ca00870f72580209ea1aea4857a115e2f2; output-bytes=2660; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=c6a20dc9bebb/38 entries

- [x] G6: independent review confirms computations and does not turn plausible explanations into demonstrated causes
  EVIDENCE: read-only agent 01a0fd5f-1bdd-7212-b755-24c66ea26bdd independently recalculated identities, ranking, eight operating points and bootstrap results; reviewed audit code sha256=4e32a49737a43aaeb9f39058ce14364d58332cdbb9e15a47cd16b66652fabc67 and the report/records. Its calibration-ID hardening finding and two final wording issues were fixed with negative tests and parent inspection. Full source/capability checks remain explicitly unmet. Structured evidence records pass validate-evidence.mjs.

G3 and G4 cannot be closed by checking score receipts, lowering a cutoff, inspecting source code or assuming that a small model cannot understand a scenario. A report may resolve individual claims while these end-to-end requirements remain visibly unmet.
