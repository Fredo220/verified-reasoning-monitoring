# Gates: final deception accepted-label analysis

Scope: local post-hoc completion of the 371-case core roleplay/control study.

- [x] T1: packet merging rejects source or approval-cohort changes
  CHECK: .venv/bin/python -m pytest -q tests/test_deception_final_review_v2.py -p no:cacheprovider
  EXPECT: /^\d+ passed(?:, \d+ skipped)?(?:, \d+ warnings)? in /m
  CWD: .
  EVIDENCE: automatic-evidence=v1; definition-sha256=1091c51ac36c46dfff1e86af637d7f367ef75baba438f4d8e2c755f2ed66aa71; exit=0; EXPECT=matched; output-sha256=9a18f298daefb6b43df79bec5398fb6c949e4a90603246ec0ec59767a594c21a; output-bytes=99; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=c6a20dc9bebb/38 entries

- [x] A1: saved scores, fixed endpoints and bootstrap metrics independently agree
  CHECK: .venv/bin/python scripts/audit_deception_final_review_v2.py
  EXPECT: FINAL_REVIEW_NUMERICAL_AUDIT_PASS
  CWD: .
  EVIDENCE: automatic-evidence=v1; definition-sha256=ee2d1b92194978e80ae1ab7ea42ec44a525ebf43f02110b61df64a07ee8d31ac; exit=0; EXPECT=matched; output-sha256=25d71feca9d2cc0e107a2726eea6378aac231b7387e74201c4126fb64ed2402e; output-bytes=34; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=c6a20dc9bebb/38 entries

- [x] R1: report, figures and README agree with audited results
  CHECK: .venv/bin/python scripts/report_deception_final_review_v2.py --verify
  EXPECT: FINAL_REVIEW_REPORT_VERIFIED
  CWD: .
  EVIDENCE: automatic-evidence=v1; definition-sha256=4bd59b4f386ad6744df3e7d92e5a85f953428ffb63f1a8c81bfba35d562c75f9; exit=0; EXPECT=matched; output-sha256=bd5cd944bc11a4ab37eb9e5b6c8ba5663ab34a698610daddb15e8d4f9a85517d; output-bytes=29; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=c6a20dc9bebb/38 entries

- [x] S1: the full local software suite passes
  CHECK: env PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' -m pytest -q -p no:cacheprovider
  EXPECT: /^\d+ passed(?:, \d+ skipped)?(?:, \d+ warnings)? in /m
  CWD: .
  EVIDENCE: automatic-evidence=v1; definition-sha256=386ac71dd1ac269401694cdc8e2dcaadab187c73e7380c3589daef08997c37a8; exit=0; EXPECT=matched; output-sha256=223818a27d4073941ea3d2978207b9deb670054222dd72ce8aefa2252b2a7897; output-bytes=2660; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=c6a20dc9bebb/38 entries

The project-local analysis environment lacks `einops` and cannot collect the
entire suite. S1 uses the existing complete test environment already recorded
in the earlier closeout. Frozen scores and probes are not refitted there.
