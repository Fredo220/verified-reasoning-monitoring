# Gates: Kimina reduced-reader repair-inclusive study

OWNS: src/vrm/runtime.py, src/vrm/kimina.py, src/vrm/kimina_condition.py, src/vrm/monitors.py, tests/test_kimina.py, tests/test_kimina_condition.py, tests/test_kimina_format_handoff.py, tests/test_monitors.py, configs/kimina_development.json, configs/kimina_context_development.json, configs/kimina_context_recovery.json, docs/kimina_execution/**, docs/three_reader_implementation.md, notebooks/kimina_development.ipynb, docs/status.md

Scope: Execute the approved free-Colab Kimina study without resetting working infrastructure. Include one model repair in the primary policy. Store the complete prompt/response activation sequence; the owner withdrew the proposed 128-token storage limit before collection. Any reduced downstream reader must be explicitly documented. This ledger distinguishes software, real feasibility, and protected research results. An unmet empirical gate cannot be replaced with unit tests.

Continuation approved by the owner after the revised goal's start hold.
The historical source archive is preserved under artifacts/kimina-development-20260916/;
its SHA256 is d7e9731f6c3388c7781dafd9f1cdf3de83643398b2876036ac50980e432c14f9.
The owner subsequently approved steps 1-3 only: verified persistent Drive
backup, context/extraction repair, and a small free-Colab development run.
The historical returned ZIPs are missing locally, in the current runtime and
in the searched Drive account; do not require their impossible recovery or
silently present newly sampled data as the old run. Keep the loss explicit.
Training and the main study require separate authorization.

Analysis-only request, 2026-09-18: inspect the newly downloaded split artifact
folders, diagnose unfinished generation and resource accounting, and propose
the smallest justified follow-up. No new model runs or protocol changes.

Subsequent owner approval, 2026-09-18: begin stage A of the analysis plan.
Repair local accounting/persistence and check the model invocation. No new
Colab allowance, prompt condition, monitor training, commit or push.

Subsequent owner approval, 2026-09-18: stage B diagnostic receives an
additional allowance of 2700 seconds of free-Colab GPU work plus 300 seconds
for persistence, exclusively on the owner's newly specified Chagunava account.
Prior spending remains recorded; this is not a reset of the old run. No
training, protected evaluation, paid service, commit or push is authorized.
The new request, source bundle and allowance amendment must be frozen before
inference; old notebooks must not be run unchanged under the new account.
Account verification and notebook access are pending. Browser automation
failed twice before returning UI state (kernel launch/sandbox error), so no
account or active runtime has been verified and no new model run was started.

Update 2026-09-19: live browser inspection verified the specified Chagunava
account and connected CPU runtime in notebook 14WK5rjdtHg_ZD6nZsRQ5z8VDAFp6B8XP.
The owner requested end-to-end continuation of the approved stage. The bounded
stage-B contract is in stage_b_2026-09-19.md; no new model inference had run at
that checkpoint.

Later 2026-09-19: one synthetic invocation control completed with 537 tokens
and EOS, a final extractable proof, and a checksummed 70,684,732-byte Drive
archive. The unchanged proof body failed real pinned Lean (unknown tactic;
unsolved goals). Local full-ZIP handoff remains unverified. The native-style
prompt is now an explicit opt-in config field shared by request construction
and verifier reconstruction; historical prompt defaults are preserved. E12
and E2 were reverified after that change. This is neither a valid development
proof nor a passed H1-H3 gate; see stage_b_2026-09-19.md.

- [x] E12: Local regression tests reject incomplete finalization, preserve raw outputs, account for final backup, reserve persistence time and detect changed backup bytes.
  CWD: ../..
  CHECK: /private/tmp/vrm-clean-venv-20260913/bin/python -m pytest -q -p no:cacheprovider
  EXPECT: /^[0-9]+ passed(?:, [0-9]+ skipped)? in [0-9.]+s$/m
  EVIDENCE: automatic-evidence=v1; definition-sha256=e7d64ae89be2211c24275737791b1558cefc46b993f3b5d6817b0f1aeac91ba0; exit=0; EXPECT=matched; output-sha256=fa4181e058f00c994bd95b24d214efef5a8655797f86578fa65bbb335f90ac9c; output-bytes=512; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=0af9371c23e5/36 entries

- [x] E13: Model-call audit distinguishes verified template/configuration facts from unresolved real-checkpoint behavior and records the remaining execution boundary.
  EVIDENCE: 2026-09-18 manual review recorded in local_repair_2026-09-18.md. tokenizer_audit_2026-09-18.json verifies all four saved input sequences and raw output decodings against the real pinned tokenizer; no terminal EOS and no added BOS. Small Qwen3 CPU tests check unchanged sampling with the collector, not pretrained Kimina/T4 equivalence. Real generation, Drive timing and H1-H3 remain unverified.

- [x] E11: A reviewed analysis separates observed outcomes, cost defects, competing explanations and owner-gated next steps without claiming H1-H3 results.
  EVIDENCE: Manual synthesis review, 2026-09-18: download_analysis_and_next_steps_2026-09-18.md distinguishes four unresolved generations from Lean-invalid proofs, the measured cost overrun from its causes, and prompt/runtime hypotheses from established defects. download_audit_2026-09-18.json and outcome_analysis_2026-09-18.json supply numeric evidence. Only analysis is complete; local repairs, new runs and training remain owner-gated. No automatic gate was rerun for this documentation-only analysis.

- [x] E10: Persistent Drive saving is tested and every new completed attempt is mirrored and checksum-verified before another attempt starts.
  EVIDENCE: A 1048576-byte probe survived drive.flush_and_unmount and remount at /content/drive/MyDrive/verified-reasoning-monitoring/backup-probe-265d316a619f46d28720c868133c9349.bin; SHA256 89ba36ee1513df9cf998ce4879adcbd3d778dd499aec9a016ad2a5a6a4184dd6. Per-attempt integration pending; this is not a saved model result.
  UPDATE 2026-09-18: Downloaded actual run contains all four shards with matching receipt hashes and 262 matching inventory entries across 14 checkpoints. This supersedes the missing-download status for the corrected run only. Final real-run export/remount receipt is absent, so the full persistence gate remains open. See download_audit_2026-09-18.json.
  UPDATE 2026-09-19: Stage-B per-attempt backups and finalizations completed for the control, four native originals and one repair. A real Drive flush/unmount/remount then revalidated 85 files (4,626,202,088 bytes); inventory digest e2f0ffef16eb9a0b7d3aadf8b4939ec1ba48944d816b9b1f99bbceadd3257a25. The transferred durability report digest aa7f7d476313c1728b8b6739cf419bd33e39862c891cb3fc1cc630c68ecd02c3 matches the notebook output. Full-token/all-layer audits separately passed on each shard. This establishes remote persistence, not a local full-array download; earlier missing artifacts are not silently recovered.

- [x] E1: The approved repair-inclusive decisions and withdrawal of the token-storage limit are recorded before new collection, preserving historical results.
  EVIDENCE: 2026-09-16 docs/kimina_execution/amendment.md records the owner's latest instruction: full prompt/response capture; 128 is replay chunk size only. Prior Gemma results remain unchanged; no real Kimina generation has run.

- [x] E2: Targeted changes and existing regression tests pass locally; this is software evidence only.
  CWD: ../..
  CHECK: /private/tmp/vrm-clean-venv-20260913/bin/python -m pytest -q -p no:cacheprovider
  EXPECT: /^[0-9]+ passed(?:, [0-9]+ skipped)? in [0-9.]+s$/m
  EVIDENCE: automatic-evidence=v1; definition-sha256=e7d64ae89be2211c24275737791b1558cefc46b993f3b5d6817b0f1aeac91ba0; exit=0; EXPECT=matched; output-sha256=fa4181e058f00c994bd95b24d214efef5a8655797f86578fa65bbb335f90ac9c; output-bytes=512; shell=/bin/sh; cwd=/Users/friedrichreichelt/Documents/verified-reasoning-monitoring; path=0af9371c23e5/36 entries

- [x] E3: Real isolated Lean checks accept the two development reference proofs and valid safety control, reject forbidden controls, and preserve the cache.
  EVIDENCE: 2026-09-16 /private/tmp/vrm-kimina-reference-acceptance-20260916-fixed/summary.json binds eight real cases: both selected references and the valid control accepted; invalid, self-reference, sorry, unauthorized-axiom and sandbox-escape controls rejected; postflight cache hash unchanged. Measured case time 354.1766 s. Source-bound script /private/tmp/vrm-kimina-reference-acceptance.py; all fixture schemas checked before Docker startup.

- [ ] E4: Real free-Colab Kimina originals and eligible repairs are generated, captured, and verified with source-bound receipts and measured resources.
  EVIDENCE: 2026-09-16 four originals and one approved format repair completed with full capture in Colab under requests 4a446ba3c827b5161a2c0cecbb2155c2255824f263c964dc8f65c15a4a50e55e and 18265508382923257822bad7b2b598e6899241d21b638c7ae9dd14f9237d0576. Real-checkpoint numerical audit passed. Three truncated originals remain unresolved; both EOS outputs fail the original parser. A separate exact-import-wrapper diagnostic rejected both unchanged proof bodies in real Lean, with postflight cache unchanged. Local full-archive handoff remains blocked by browser download; this gate is not met. See development_pilot.md and artifacts/kimina-development-20260916/.
  UPDATE 2026-09-19: Stage-B native originals and the one eligible repair completed and passed remote artifact audits. Frozen outcomes are three unresolved originals, one format-invalid original and an unresolved repair; zero extractable real-task proofs. Local full-return reconciliation remains outstanding; do not mark this broad gate met from persistence or software tests alone.

- [ ] E5: Real development yield and reader training feasibility justify a frozen task-disjoint protocol and fair repair-inclusive compute accounting.
  EVIDENCE: 2026-09-18 corrected-run audit: four stored originals, zero finalized proofs, four unresolved generations, zero repair-eligible outputs under the current policy. No valid/invalid training labels or monitor-training feasibility established. E4's older pilot record is historical and not replaced by these samples.
  UPDATE 2026-09-19: Stage B still supplies no valid/invalid primary proof-label mixture. One EOS original fails formatting and its single repair is unfinished. The model's PLift trace visibly repeats unresolved reasoning; a larger token limit is not established as a solution. No new budget, training or protected study is automatically authorized.

- [ ] E6: Frozen H1 and reduced-H2 prediction comparisons and controls are executed on protected tasks with task-level uncertainty.
  EVIDENCE: pending

- [ ] E7: Repair-inclusive H3 is evaluated against both frozen baselines under matched resources, without treating repairs as independent tasks.
  EVIDENCE: pending

- [ ] E8: Final artifacts, costs, limitations and scientific interpretation are audited against actual results; no claim of completion from partial gates.
  EVIDENCE: pending

- [ ] E9: Corrected public-context and extraction paths preserve the original proposition and reject reference leakage or changed proof content; old condition remains reproducible.
  EVIDENCE: Software regression checks are included in E2. context_acceptance.json records two successful real pinned-Lean context elaborations (trusted by-sorry scaffolds, not accepted model proofs). The module header was corrected before generation. Full generated-proof/extraction reconciliation remains pending; see restart_checkpoint.md.

## Stage-B recovery, 2026-09-22

Scope: Preserve the completed Stage-B result and prepare one explicitly new,
open-development prompt/extraction/feedback condition. No protected evaluation,
new model inference, historical relabeling, commit or push is part of this repair.

- [x] E14: The completed Stage-B EOS proof is reported with its actual post-hoc Lean verdict, while historical format labels remain unchanged.
  EVIDENCE: The saved diagnostic and Store envelope were read and their payload hash recalculated. The recovered body hash `805d01225a671a6f15492be9eca787dc50ecf4a4acfe65dab0bffb03ca7d8993` matches the previously saved diagnostic; the original status is `format_invalid`, while the separate Comparator verdict is `invalid` with `pinned_original_valid`. Documented in stage_b_recovery_2026-09-22.md; Lean was not rerun.

- [ ] E15: The opt-in condition extracts only reviewed-context echoes after enumerated header/blank-line normalization and sends only allowlisted Lean diagnostic categories; adversarial wrappers and source-text leakage are rejected.
  CWD: ../..
  CHECK: /private/tmp/vrm-clean-venv-20260913/bin/python -m pytest -q -p no:cacheprovider tests/test_kimina_condition.py tests/test_kimina.py tests/test_kimina_format_handoff.py
  EXPECT: /^[0-9]+ passed(?:, [0-9]+ skipped)? in [0-9.]+s$/m
  EVIDENCE: Direct local focused run passed 87 tests on 2026-09-22; real archived EOS output yielded the previously recorded proof hash, and real saved Lean output mapped to `unknown tactic; unsolved goals`. Automatic Unlazy checker approval/evidence is not recorded, so this runnable gate remains open.

- [ ] E16: The full local suite passes after the scoped repair.
  CWD: ../..
  CHECK: /private/tmp/vrm-clean-venv-20260913/bin/python -m pytest -q -p no:cacheprovider
  EXPECT: /^[0-9]+ passed(?:, [0-9]+ skipped)? in [0-9.]+s$/m
  EVIDENCE: Direct local run on 2026-09-22: 369 passed, 7 skipped in 9.53s. Automatic Unlazy checker approval/evidence is not recorded, so this runnable gate remains open.

- [ ] E17: A fresh, source-bound Kimina generation followed by actual Lean verification demonstrates that the new condition yields valid and invalid labeled proofs.
  EVIDENCE: pending; the owner earlier reported exhausted free-Colab units, but quota was not rechecked. Software tests and the historical invalid post-hoc proof do not satisfy this gate.
