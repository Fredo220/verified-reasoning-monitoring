# Gates: deception-monitor publication audit

OWNS: docs/deception_monitoring/publication_audit_v1/**, scripts/audit_deception_publication_v1.py, scripts/audit_deception_sources_resumable_v1.py, scripts/package_deception_publication_v1.py, scripts/reproduce_deception_release_v1.py, tests/test_deception_publication.py, README.md, artifacts/deception/focused-replication-v1/ccpp-probe-v1/publication-audit-v1/**

Scope: investigate the frozen source-projection failure; verify the layer-8/layer-22 comparison; prepare an accurately qualified, reproducible public release without changing protected results. New experiments, if needed, remain separate diagnostics. No response regeneration or automatic publication.

- [ ] G1: every original activation-to-score projection is verified with the unchanged source identities and tolerance
  EVIDENCE: pending; complete source verification is required to call the original pipeline fully audited. A disclosed missing source is not a successful full audit.

- [ ] G2: layer-8 plus layer-22 fusion counts and the distinction from a newly trained concatenation probe verify against the frozen inputs
  CHECK: env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' scripts/audit_deception_publication_v1.py --audit-only
  EXPECT: DECEPTION_PUBLICATION_AUDIT_VERIFIED
  EVIDENCE: pending

- [x] G3: the public summary distinguishes the closed studies, post-hoc selection, annotation provenance, ordinary alerts and incomplete source verification
  EVIDENCE: README, REPORT.md and RELEASE_README.md checked against the fixed matched-result hash b65f41c06fc3cebea252f2f37b31b9a05d5a32206351b1003235ef568ddc2ad9; fusion versus trained concatenation and conditional score replay are explicitly separated.

- [x] G4: the bounded release package contains reproducible score-level results, provenance, source attribution and redistribution decisions without credentials or private raw captures
  EVIDENCE: release-v2 has exactly eight allowlisted members, no symlinks or extra members; input/result hashes retained; scanner found no configured credential patterns or local paths. ZIP SHA256 2a02e66786526755805ff7c64ede8499553e95305ea1e8c9cd03ddeb24fc1f06. Existing project license and both method sources are included; upstream raw redistribution permission remains unresolved, so raw source material is excluded. This is not a scan of the whole repository/history.

- [ ] G7: the isolated release reproduces all 514 detection settings, rejects changed members and requires neither GPU nor private study files
  CHECK: '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' artifacts/deception/focused-replication-v1/ccpp-probe-v1/publication-audit-v1/release-v2/reproduce.py
  EXPECT: DECEPTION_RELEASE_REPRODUCED 514
  EVIDENCE: pending

- [ ] G5: focused negative controls and the complete existing software suite pass without modifying protected scientific inputs
  CHECK: env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' -m pytest -q -p no:cacheprovider
  EXPECT: /(?:^|\n)[0-9]+ passed(?:, [0-9]+ skipped)?(?:, [0-9]+ warnings?)? in [0-9.]+s(?: \([0-9:]+\))?(?:\n|$)/
  EVIDENCE: pending

- [x] G6: the report states exactly which further experiment is needed for generalization and does not describe an unrun diagnostic as evidence
  EVIDENCE: REPORT.md section 4 requires unused scenario families, a frozen rule and independent score-blind labels; comprehension diagnostics and two-layer concatenation are not described as completed experiments.
