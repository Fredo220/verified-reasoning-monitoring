# Gates: recall-first saved-score experiment

OWNS: scripts/analyze_deception_recall_readouts_v1.py, tests/test_deception_recall_readouts.py, docs/deception_monitoring/recall_readouts_v1/**, artifacts/deception/focused-replication-v1/ccpp-probe-v1/recall-readouts-v1/**

No fitting, generation, label replacement, upload or changes to previous results. Original source-audit incompleteness remains visible.

- [x] G1: all 74 fixed-grid configurations reproduce from frozen inputs, including trivial controls and complete metrics
  CHECK: env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' scripts/analyze_deception_recall_readouts_v1.py --audit-only
  EXPECT: DECEPTION_RECALL_READOUTS_VERIFIED 74
  EVIDENCE: automatic-evidence=v1; definition-sha256=198770146b6c26f3503e70509b55ab075bb07d82989b311472afa412fe738f6a; exit=0; EXPECT=matched; output-sha256=1a1ef11a4378aab502f4cd62ac2e78db4b5cad685244d70212b5cdc0ffe26b76; output-bytes=38; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=c6a20dc9bebb/38 entries

- [x] G2: negative controls and the full local software suite pass
  CHECK: env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' -m pytest -q -p no:cacheprovider
  EXPECT: /(?:^|\n)[0-9]+ passed(?:, [0-9]+ skipped)?(?:, [0-9]+ warnings?)? in [0-9.]+s(?: \([0-9:]+\))?(?:\n|$)/
  EVIDENCE: automatic-evidence=v1; definition-sha256=5fb9c95914529036a153b8b47c1eb8726e0fc48b670450602c6c38b8e4203889; exit=0; EXPECT=matched; output-sha256=78b7c50ac8b15ecf785ff414883a007ee410f0c7d30652cf9729248e8c89373c; output-bytes=2740; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=c6a20dc9bebb/38 entries

- [x] G3: independent review verifies counts, calibration, preserved originals and qualified interpretation
  EVIDENCE: separate AI reviewer 01a0fd5f-1bdd-7212-b755-24c66ea26bdd independently recalculated all 74 configurations and reported no material defects; reviewed result sha256=3177ff050afc1ed0681a5948cc8371242c226215f10d7f7cf12aa386da909a0e, code sha256=5c932b93e4e47d69afa3e130416206fd6b2c1752db4154821e51eabfbffa633b, PLAN sha256=71018c8349b4e2035eed17b1061b6a2f0acd5205fdc6ad5f22134ac6e1f375ec. Preserved FP32/FP64 conventions, gap resets, old cutoffs and original files; OR calibration counts reported, not assumed. This is numerical/code review, not independent human annotation. Full source-projection verification remains incomplete.

- [x] G4: a human-readable report gives additional detections and additional alerts, with all results saved and no confirmatory claim
  EVIDENCE: REPORT.md sha256=20858d1ac5ef4c11f4c3a21e09ca7a7e7ce8ecf556793387e51d61f60b1cd827 explains recovered and lost detections, honest/ambiguous/ordinary/calibration alerts, existing comparators, label provenance, 74-setting post-hoc selection risk and the unresolved original source audit; links the complete immutable results and does not select a deployment rule or claim new confirmation. Counts checked against results.json; git diff --check passed.
