# Kimina development pilot: execution checkpoint

> Preservation update, 2026-09-16: the three historical ZIPs described below
> are no longer present in the reset Colab runtime, locally, or in the searched
> Drive account. The download instructions below are historical, not an
> actionable recovery step. Notebook outputs and the separately preserved
> source/Lean diagnostic evidence remain; the complete historical activations
> have not been recovered. Newly sampled data must not be presented as their
> reconstruction. See [the corrected restart](restart_checkpoint.md).

Date: 2026-09-16. This is a two-task instrument/integration pilot, not a
hypothesis test. H1-H3, monitor training and protected evaluation have not run.
The four originals and one eligible format repair are complete. Both finished
proof bodies were also checked in a separate real Lean diagnostic. Full local
artifact handoff and end-to-end pipeline reconciliation are still pending.

## What actually ran

- Both fixed reference proofs and the six existing proof/security controls
  passed the real isolated local verifier acceptance sequence. The cache
  remained unchanged; total case verification time was 354.18 seconds.
- Pinned `AI-MO/Kimina-Prover-RL-1.7B`, revision
  `1dfd2228afcc35b16eb008a81dfc2b2707750f78`, ran in FP16 on a free T4.
- The two fixed development tasks each received two original sampled answers.
  No answers were regenerated. All 28 post-block layers and all actual prompt
  and response tokens were captured, without the withdrawn 128-token cap.
- The real-checkpoint numerical comparison passed its predeclared tolerances.
  It compared 192 token positions across all layers and 32 saved output-token
  log probabilities. Maximum layer relative L2 error: 0.001651; minimum
  cosine: 0.9999986; maximum log-probability absolute error: 0.01949. Absolute
  activation error reached 16.0, so the relative tolerance should not be
  misread as absolute equality. This short check is not a longest-trace
  equivalence proof or a monitor-quality result.

## Original outputs

The table reports the existing parser's decisions, not Lean validity.

| Task | Attempt | Input tokens | Output tokens | Stop | Parser finding |
| --- | ---: | ---: | ---: | --- | --- |
| `complEDS2_three` (Unicode name retained in artifacts) | 0 | 187 | 8096 | Length guard | Unfinished reasoning block |
| Same task | 1 | 187 | 8096 | Length guard | Unfinished reasoning block |
| `PLift.up_inj` | 0 | 138 | 8096 | Length guard | Unfinished reasoning block |
| Same task | 1 | 138 | 3748 | EOS | No permitted complete final proof |
| `PLift.up_inj`, single repair of attempt 1 | 1 | 515 | 4784 | EOS | Same extra import wrapper |

The three unfinished answers are unresolved, not wrong-proof labels. The EOS
format failure received the approved single repair. Its raw answer and
fixed category feedback, but no reference proof or compiler logs, were given
to the model. The repair finished, but again included an extra `import Mathlib`
before the repeated declaration. Under the existing extraction policy it is
also format-rejected. The original remains unchanged. Repairs remain in the same task
family and are not independent observations.

`prepare_format_repair.py` is a narrow handoff adapter: it validates existing
source identities, receipt hashes and all activation checksums, and accepts
only parser-decidable outcomes. If any proof needs Lean, it refuses to classify
it. Regression tests compare its repair request byte-for-byte with the existing
local verifier. Its remotely produced request must still be reconciled with
the real local handoff; it does not replace trusted verification.

## Separate proof-body diagnostic

To distinguish a wrapper problem from an incorrect proof, a separate diagnostic
removed only the exact leading `import Mathlib` wrapper in both completed
outputs. The existing extractor then removed the exactly matching theorem
declaration. Neither proof body was corrected. This post-run diagnostic does
not change the original parser outcomes or count as another model repair.

The two bodies were transferred through visible notebook output, checked
against the SHA256 values printed in Colab, and submitted to the existing
isolated Lean/Comparator verifier for the original `PLift.up_inj` task:

| Body | Trusted verifier result | Verification seconds |
| --- | --- | ---: |
| Original EOS answer | Invalid; compilation failed | 31.79 |
| Single model repair | Invalid; compilation failed | 19.45 |

Both produced a syntax error and unsolved goals. Their combined verification
time was 51.24 seconds, and the postflight cache digest was unchanged. The
reference for this exact task had already passed. Removing the extra import
therefore did not make either saved answer valid. This does not determine
whether Kimina can solve the task with better public context, and does not
establish a model-level failure rate from two tasks.

Local evidence is preserved in the ignored
`artifacts/kimina-development-20260916/` directory: reference acceptance,
`vrm-kimina-body-diagnostic-results/`, the diagnostic capsule and its script.
The diagnostic summary payload SHA256 is
`7a1cb49e684fae96fa3a1db20d304a24239d4f3111142156b500c14aa1efab9f`.
This narrow transfer is not certification of the full activation archives.

## Public-context concern

The historical public request contains `full_name` and `file_path`, but its
`make_request` did not include them in the model message. For this task, the pinned source
is inside `namespace PLift`, while the message supplies the unqualified
`up_inj` declaration and local goal. Missing namespace/definition context is
a plausible instrument problem; its causal contribution has not been tested.
The other task also depends on domain-specific definitions not shown in the
message. This deserves a bounded public-context audit before expansion, not
a new corpus or leaked reference proof. No prompt or model condition has been
changed for those saved outputs. The authorized, separate corrected profile
now adds reviewed public context and audited wrapper extraction in local code.
It has not run on the real model. See the post-pilot section of
[the amendment](amendment.md); real context acceptance remains pending.

## Measured resources and the next decision

Original pipeline time: **1545.77 seconds (25.76 minutes)**, including the first
model load. The wrapper measured 25:53.32 total subprocess wall time. Generation,
capture and compressed storage per candidate averaged 355.28 seconds; model
load contributed approximately 124.66 seconds. Maximum process RSS was
5,079,308 KiB (4.84 GiB). The numerical audit added 32.31 wall seconds.
Readonly handoff inspections and file transfer are additional overhead, not
free operations or candidate improvements.

The single repair added 266.93 pipeline seconds, including its model load,
bringing the original-plus-repair total to **1812.70 seconds (30.21 minutes)**.
Its wrapper measured 4:30.76; maximum process RSS was 5,036,892 KiB. The repair
activation shard is **564,610,013 bytes**, and its ZIP is **564,934,667 bytes**.
The 32.31-second numerical audit and read-only inspection/transfer overhead
are additional. These pipeline durations are not the total time the allocated
Colab runtime remained connected, including idle time.

The four activation shards total **3,056,140,303 bytes**. The original export
ZIP is **3,057,838,001 bytes**. A simple extrapolation to 128 comparable
originals gives roughly **12.63 pipeline hours and 97.8 GB**, before repairs,
extra model loads, monitor training, verification or transfer. This is a rough
projection from only two tasks, not a representative throughput estimate or a
scientific stop. It nevertheless cannot justify blindly launching the full
32-by-4 expansion within the existing resource ceiling.

Before expansion, settle a costed scope decision using these measurements.
Do not silently shorten retained sequences, label unfinished outputs false,
restore obsolete five/30-second cutoffs, replace tasks after their outcomes,
or claim that a small collection pilot establishes H1-H3. Full-capture reader
training remains unmeasured; the published-code comparison is in
[the adaptation audit](../three_reader_implementation.md).

## Artifact handoff and provenance

- Notebook: <https://colab.research.google.com/drive/1MEUCP3OYtGEaJ75mcdFCXGblLE-Zhf6V>.
- Source ZIP SHA256: `d7e9731f6c3388c7781dafd9f1cdf3de83643398b2876036ac50980e432c14f9`.
- Original request SHA256: `4a446ba3c827b5161a2c0cecbb2155c2255824f263c964dc8f65c15a4a50e55e`.
- Original Colab directory: `/content/kimina-results-4a446ba3c827b516`.
- Format-repair request SHA256: `18265508382923257822bad7b2b598e6899241d21b638c7ae9dd14f9237d0576`.
- Repair output directory: `/content/kimina-results-1826550838292325`.
- Numerical audit script SHA256: `b38ff372a6ab207708f556a8e7852336abab7a5e23ef5c58646cd0c138d8804e`.
- Local reference acceptance: `/private/tmp/vrm-kimina-reference-acceptance-20260916-fixed/summary.json`.
- Supplemental metadata ZIP: `/content/kimina-handoff-receipts.zip`, 486,371 bytes;
  SHA256 `7932a0e9131619a6ed3a84b284c9d752d2a8501b8c3884ed6ae97c962775696a`.

Download these three files from the notebook's Files panel using a regular
browser and provide their local paths. Do not rerun model-generation cells:

1. `kimina-results-4a446ba3c827b516.zip` (originals).
2. `kimina-results-1826550838292325.zip` (single repair).
3. `kimina-handoff-receipts.zip` (supplemental audits and metadata).

The original archive was assembled before the numerical and handoff audits;
those JSON receipts must be returned separately as well. A browser displayed
transfer progress but produced no locally discoverable download. A second
small-file control also failed. Preserve the Colab runtime and use a regular
browser download. This is an operational blocker, not a failed mathematical
hypothesis. No remote archive has yet passed local validation.

On receipt, use `vrm.kimina verify` from the preserved original source ZIP
with its original configuration (not the edited package's source identity), verify
all hashes, reconcile the repair request, run the same trusted verifier on the
repair, and check the postflight cache digest. Do not make H1-H3 claims from
this checkpoint. No commits, pushes, paid compute or private verifier uploads
were made for this continuation.
