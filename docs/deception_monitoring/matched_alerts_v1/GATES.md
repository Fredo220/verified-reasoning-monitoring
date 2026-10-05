# Gates: matched-alert robustness diagnostic

OWNS: scripts/analyze_deception_matched_alerts_v1.py, tests/test_deception_matched_alerts.py, docs/deception_monitoring/matched_alerts_v1/**, artifacts/deception/focused-replication-v1/ccpp-probe-v1/matched-alerts-v1/**

Scope: complete a separate post-hoc matched-budget exploration and robustness report, not confirmation or a full source-projection audit.

- [x] G1: strict calibration budgets, complete combination enumeration and valid resampling controls pass focused tests
  CHECK: env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' -m pytest -q tests/test_deception_matched_alerts.py -p no:cacheprovider
  EXPECT: /(?:^|\n)[0-9]+ passed(?:, [0-9]+ warnings?)? in [0-9.]+s(?:\n|$)/
  EVIDENCE: automatic-evidence=v1; definition-sha256=9afd08a907c1a1cd14c704a6212071832ca43563367a8488a60a62af8bd13a13; exit=0; EXPECT=matched; output-sha256=cf0163bfdc4ef563232afe804d0b7e103a6b972a940139b3ddc2d4be922bfc39; output-bytes=98; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=c6a20dc9bebb/38 entries

- [x] G2: the full 514-configuration artifact and robustness statistics replay from unchanged frozen inputs
  CHECK: env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' scripts/analyze_deception_matched_alerts_v1.py --audit-only
  EXPECT: DECEPTION_MATCHED_ALERTS_VERIFIED 514
  EVIDENCE: automatic-evidence=v1; definition-sha256=365091745fb3ad5f96454bdc68d68639da3f89989daedce26ef6d9722409ec1b; exit=0; EXPECT=matched; output-sha256=ceded5a857ede23b9040b6ef6ac88296e68549d523ec55e1ab25a3b5d254cb9a; output-bytes=38; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=c6a20dc9bebb/38 entries

- [x] G3: independent numerical/code review supports the reported calculations and qualified interpretation
  EVIDENCE: AI reviewer 01a0fd5f-1bdd-7212-b755-24c66ea26bdd independently recalculated all 514 count rows/cutoffs, 10,000 paired bootstraps and 2,000 permutations; protected hashes matched. Code sha256=5584a8e5dc9f6f9f2bd61916a8a009da26e985839e275ad6cc9e07acb79629b8; result sha256=b65f41c06fc3cebea252f2f37b31b9a05d5a32206351b1003235ef568ddc2ad9. P2 reporting omission fixed: strongest single-head comparators at all budgets and the unfavorable 5% comparison are now visible; final report-only recheck found no outstanding material issues. This is code/numerical verification, not independent human label validation, fresh confirmation or completion of the original source audit.

- [x] G4: a readable report distinguishes matched-budget gains, uncertainty, controls and unresolved evidence
  EVIDENCE: REPORT.md sha256=aef465c65c54411accce963da4dffcff6e8d2fb103665a1a0f582a91302cf160; figure sha256=c6c8a670bcab25538ed5db3c2229370254594c59932e4fad25285a63b0cf0ddd, generated from immutable results and visually inspected. Report includes all-budget strongest-single alternatives, conditional intervals, non-degenerate shuffle/length controls, explicit outcome-selected 31/32 recall-first candidate (6/21 honest alerts, 89/1000 ordinary), old aggressive 32/32 trade-off, remaining miss, label provenance, and unresolved source audit. All 512 named rows were independently checked against original label/grade counts; result input hashes and disjoint 500/500 calibration identities verified. Local links resolve; no commit/push.

- [x] G5: the complete local software suite has no regressions
  CHECK: env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' -m pytest -q -p no:cacheprovider
  EXPECT: /(?:^|\n)[0-9]+ passed(?:, [0-9]+ skipped)?(?:, [0-9]+ warnings?)? in [0-9.]+s(?: \([0-9:]+\))?(?:\n|$)/
  EVIDENCE: automatic-evidence=v1; definition-sha256=5fb9c95914529036a153b8b47c1eb8726e0fc48b670450602c6c38b8e4203889; exit=0; EXPECT=matched; output-sha256=b6ebcebb2c01337d535541ada94ba31d265d0141f90bb0ae37127d4814803c31; output-bytes=2740; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=c6a20dc9bebb/38 entries
