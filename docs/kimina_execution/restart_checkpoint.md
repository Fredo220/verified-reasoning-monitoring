# Corrected development restart

2026-09-16. Approved scope: persistent backup, public-context/extraction
correction, and the small development run only. No training, main study,
commit, or push is authorized by this continuation.

## Evidence before generation

- The real local regression suite passed the approved Unlazy check; its
  output fingerprint is recorded under E2 in GATES.md.
- Both corrected public contexts elaborate with the pinned Lean compiler.
  The trusted fixtures use `by sorry` to test context/name resolution only,
  not proof validity. See context_acceptance.json. An initial context omitted
  the required `module` header; that was repaired before generation. A prior
  `lake env` check tried to write a readonly configuration lock; the accepted
  check used the pinned Lean executable and explicit existing library paths.
- A 1 MiB Drive probe survived flush, unmount and remount. The actual backup
  helper then passed the same procedure with two synthetic fixture files:
  probe.json SHA256 9faa7268ff278529a4017632fa0f742fe70a94a2ffd703e7a9bee533fa0e3636;
  probe.npz SHA256 7f9200c399dec415eef5a05dc5436f9290eb920974f1ccc6948b9e9cab4c86cf.
  The .npz fixture contains random bytes, not measured activations.

## Frozen inputs and storage

- Public source ZIP: cbd0a9edffb765c853b3318d4a8d69683bba0b8785c5ffca91c4443159734d27.
- Public request: c07b94efeef8b868592c99ebd71f4c27a8d0d75b312ba7f3c12df8b3f505f56e.
- Two existing open-development tasks, two original candidates each.
- Known prior measured cost carried forward: 1845.0046825 seconds. Historical
  idle time and unmeasured transfer overhead are not implied to be included.
- Drive directory: MyDrive/verified-reasoning-monitoring/kimina-context-c07b94efeef8b868.
- Before moving to the next attempt, raw outputs and completed JSON/NPZ
  artifacts are copied and checksum-verified. Different existing files cause
  a stop, not an overwrite. Final export/remount time is recorded separately.

## Current status

Update, 2026-09-18: both downloaded folders contain one complete set of four
attempt receipts and their activation shards. File hashes, backup inventories
and array headers were audited. All four outputs are unfinished reasoning:
three length stops and one operational timeout, with no final proof to verify.
Stored-attempt completion is not scientific completion. Final export/remount
evidence and independent numerical array revalidation are not established by
this download audit. See [analysis and next steps](download_analysis_and_next_steps_2026-09-18.md).
Neither this restart nor context elaboration supplies evidence for H1-H3.
The old lost archives are not recoverable by repeating their random samples.

Local stage A completed on 2026-09-18: see
[repair and tokenizer audit](local_repair_2026-09-18.md).
No replacement samples have been generated. The next Colab diagnostic requires
a separately approved allowance and a frozen request for the updated code.
