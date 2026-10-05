# Gates: false-reporting DoM adaptation

OWNS: src/vrm/false_reporting_dom.py, tests/test_false_reporting_dom.py, tests/test_false_reporting_ccpp.py, tests/test_false_reporting_notebook.py, scripts/run_false_reporting_dom_v1.py, scripts/run_false_reporting_ccpp_v1.py, notebooks/false_reporting_dom_ccpp_v1.ipynb, docs/deception_monitoring/false_reporting_dom_v1/**, artifacts/reward-hacking/false-reporting-dom-v1/**

- [x] G1: User approved a separate bounded adaptation, not an exact reproduction.
  EVIDENCE: 2026-10-04 answer "Approve the bounded adaptation"; unchanged old studies, new protocol and namespace.
- [x] G2: Fixture matching, labels, grouped splits and leakage boundaries pass local regression tests.
  CHECK: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' -m pytest -q tests/test_false_reporting_dom.py tests/test_false_reporting_ccpp.py tests/test_false_reporting_notebook.py -p no:cacheprovider
  EXPECT: /[0-9]+ passed/
  CWD: /Users/friedrichreichelt/Documents/verified-reasoning-monitoring
  EVIDENCE: automatic-evidence=v1; definition-sha256=e18ccca752356d9d03f4a1b5d0746ef1a6e6913a15d95d5baf3812f4ba10ca8a; exit=0; EXPECT=matched; output-sha256=1b86c4d54adb0b340bef9b22d2d85eb40e191b43374b0f682f9cf9ac30a37c6b; output-bytes=99; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=5037a01e3551/38 entries
- [x] G3: Inputs and code are frozen before the first real capture.
  EVIDENCE: 2026-10-04 prepared 456 rows; canonical design SHA256 4910c8be4bf7b15728b4e99e5ba3acc6f65233934e6aaf7b230111834d9ed02e; private kit SHA256 373474f0112b31f55659f70d194abe9c147bc6bea322964820750a92b6ac1b5b, 47,318 bytes. Independent P1/P2 follow-up found no remaining blocker; focused tests 33 passed. No captures opened.
- [x] G4: Real pinned-model capture, alignment check and interruption/resume complete on Colab with private durable storage.
  EVIDENCE: 2026-10-04 authorized frederic.reichelt account; T4 / 2026.07; seven-record interruption completed in 120.493 s, fresh-process resume captured all 456 records in 196.681 s. Colab returned FALSE_REPORTING_REAL_CAPTURE_VERIFIED and then FALSE_REPORTING_RESULT_AUDIT_VERIFIED, including dense/chunked alignment and original-seven-receipt checks. Private Drive namespace false-reporting-dom-v1-443e29d2e62a. Old notebook unchanged. Independent retrieval is tracked separately in G6.
- [x] G5: Train-only fitting and validation-only selection precede both held-out evaluations.
  EVIDENCE: 2026-10-04 all raw comparators and four CC++ heads completed, with all twelve predeclared readouts. Raw index 3 and logistic index 1 selected from 28-layer validation profiles; single-layer CC++ used frozen index 3. Independent local training replay matched the 192-row/2944-token normalizer and validation-selected epoch weights exactly (epochs 6, 3, 1, 10). Both original auditors replayed frozen validation cutoffs and held-out projections without refitting or tolerance changes. Receipts: artifacts/reward-hacking/false-reporting-dom-v1/local-audit/training.json, raw-projection.json and ccpp-projection.json.
- [x] G6: Retrieved arrays, receipts and metrics pass an independent local audit, with denominators and controls reported.
  EVIDENCE: 2026-10-04 read-only private streaming retrieved full ZIP SHA256 c1ddc5c24f42ce09a385355c4df0d86ebfae0f07eaf7a19a2a46eae231b196bf and summary ZIP SHA256 6b07f8e27cfd30e227a077d5c822e437fd9e011bf3ac378cd499f8390b158510. All 1042 members, 456 arrays, 1029 inventoried output files and 12 frozen source files verified; original Colab outputs preserved. Local raw and twelve-arm CC++ audits passed; maximum learned-head replay error 4.3827041167787684e-05 remained within predeclared bounds. RESULTS.md, figure, 36-row CSV and local-audit/index.json report both 96-record splits (32 positive, 64 negative, 16 identifier groups), all controls, logistic convergence warnings, null-subset limitation and parser equivalence. Temporary local credential removed; no commit or push.
- [x] G7: The full local software suite passes without regression.
  CHECK: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:scripts '/Users/friedrichreichelt/Documents/Machanistic Interpretability/.venv/bin/python' -m pytest -q -p no:cacheprovider
  EXPECT: /[0-9]+ passed/
  CWD: /Users/friedrichreichelt/Documents/verified-reasoning-monitoring
  EVIDENCE: automatic-evidence=v1; definition-sha256=b11c2e04cfb80f70884de3211acece17684730e8f31af3de904d2f4029ed0b1e; exit=0; EXPECT=matched; output-sha256=89359e62b691158210edfd4e849e303c08b090c83f47402a4672c367c75b1228; output-bytes=2740; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=5037a01e3551/38 entries

Ruling: these are inert scripted transcripts; no model-generated shell command, live tampering, subjective-intent label or change to old results is authorized by this adaptation.
