# Gates: verifier readiness and Colab authentication

OWNS: GATES.md, src/vrm/**, tests/**, notebooks/verified_reasoning_monitoring.ipynb, docs/**, protocol/development_probe_budget_2026-09-16.json, protocol/evidence/verifier-readiness-2026-09-16/**

Scope: Complete the four readiness steps without replacing the corpus, silently changing budgets, or claiming simulated authentication or smoke results as live verification. Colab/Hugging Face login. On September 16 the user approved the proposed one-candidate development budget and explicitly approved commit/push to the existing branch, not a merge to main.

- [x] G1: Known development fixtures have real bounded verification receipts and an evidence-based resource proposal.
  EVIDENCE: protocol/evidence/verifier-readiness-2026-09-16/manifest.json binds both runs and unchanged cache/source hashes; after-mount-repair has three valid references (25.27-52.06s) and an invalid control (64.84s). Proposal and sampling limits in docs/development_readiness_2026-09-16.md. No model run or scientific endpoint.

- [x] G2: Authentication rejects missing, expired/revoked, and unauthorized tokens without leaking credentials and permits a corrected credential on retry.
  CHECK: /private/tmp/vrm-clean-venv-20260913/bin/python -m pytest -q -p no:cacheprovider tests/test_auth.py
  EXPECT: /^[0-9]+ passed in [0-9.]+s$/m
  EVIDENCE: automatic-evidence=v1; definition-sha256=63edacace269af9ada394812c757c5c8a59a02b7b76d2076a6fdafd1aca43584; exit=0; EXPECT=matched; output-sha256=e628bf6067083df1c5d41bbc7a8a8c9014bc9d547f1353039f98964a67d7d700; output-bytes=99; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=8b0ac785dcdc/31 entries

- [x] G3: The user approves concrete measured budget values before configuration or model execution changes.
  EVIDENCE: User request "dann lass die restlichen 3 punkte auch machen" accepts the immediately preceding 120s-verifier/180s-active one-candidate proposal; scope clarified before execution. Frozen study and full-smoke budgets unchanged. See protocol/development_probe_budget_2026-09-16.json.

- [x] G4: A hash-bound development handoff rejects stale, altered, duplicate, and mismatched records; costs and offline-only status are explicit.
  CHECK: /private/tmp/vrm-clean-venv-20260913/bin/python -m pytest -q -p no:cacheprovider tests/test_handoff.py
  EXPECT: /^[0-9]+ passed in [0-9.]+s$/m
  EVIDENCE: automatic-evidence=v1; definition-sha256=774c96613802bd94b24b6bb90fdceabce354493be9c6f09a7d5e7fc55d157d70; exit=0; EXPECT=matched; output-sha256=d6b4a6fd351bfc7e47c022c2e93d2d04445fcab4d7b5b0649fd04527ffd3a3e7; output-bytes=99; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=8b0ac785dcdc/31 entries

- [ ] G5: A live Colab session and the pinned Gemma access check succeed without exposing a credential.
  EVIDENCE: pending

- [ ] G6: After budget approval, one natural candidate and then the real 32-by-4 development smoke are verified against the unchanged yield gate.
  EVIDENCE: pending

- [x] G7: The complete local test suite passes for the final implementation, with skips distinguished from executed integration checks.
  CHECK: /private/tmp/vrm-clean-venv-20260913/bin/python -m pytest -q -p no:cacheprovider
  EXPECT: /^[0-9]+ passed(?:, [0-9]+ skipped)? in [0-9.]+s$/m
  EVIDENCE: automatic-evidence=v1; definition-sha256=ae2c3839b6e1e92a90a629bd1bf4124ed993acd13b590668a3a72679fe511a5c; exit=0; EXPECT=matched; output-sha256=b8e7c52f8afcf24c9b69b13021efe8bb26ffaef07ae5ea828e1361019f025e8d; output-bytes=351; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=8b0ac785dcdc/31 entries

G1 is reviewed against raw timing receipts, source/runtime hashes and the budget proposal. It is not proof of complete-study feasibility. G3 and G5 require external human/session evidence. G6 requires real model and verifier evidence, not unit-test stand-ins. Runnable gates remain unmet until inspected command approval and checker execution. Do not install hooks.
