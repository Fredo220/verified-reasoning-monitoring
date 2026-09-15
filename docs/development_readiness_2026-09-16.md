# Development readiness: timing, authentication, and handoff

Continuation: the owner has since approved the one-candidate budget below and
branch-only publication. See the [execution instructions](colab_generation_handoff.md)
and [approved record](../protocol/development_probe_budget_2026-09-16.json).
The new integration command passes the 246-test local suite (7 real cases
skipped). Live execution is tracked in `GATES.md`. The remainder preserves the
initial readiness snapshot, including its then-pending approvals.

Updated September 16, 2026 (Europe/Berlin). This is a repair report, not a
study result. The corpus, model, yield gate, and H1-H3 endpoints are unchanged.
No natural model candidate was generated during this work. No commit or push
was made.

## What is verified

| Work item | Verified evidence | Remaining work |
| --- | --- | --- |
| Measure local verification | Three fixed development reference proofs accepted; an invalid control rejected, after a shared-file access repair | These few timings do not establish study-wide feasibility |
| Choose a realistic budget | Measured proposal below; original five/30-second limits preserved | Owner approval and a narrowly scoped development amendment |
| Repair login and prepare data transfer | Authentication tests, live local HF check, public-only request export and immutable return-store tests pass | Live Colab Secret check and actual Colab-to-local generation/verification integration |
| Run one candidate, then the smoke | Not run | Approved budgets, reviewed execution commit, runtime, and working transfer/accounting |

The local suite reports **237 passed, 7 skipped**. The seven skipped cases
require the explicit real Linux acceptance environment. They passed in the
earlier acceptance run; that history is not a fresh run of those tests today.
The four real fixture checks below were executed separately. Authentication
failure tests use controlled HTTP/Secret stand-ins, not deliberately revoked
real credentials. No real Gemma forward pass has been performed.

## Real timing measurements

Before observing results, the script selected the first three development
task IDs in ascending order, then added one nonexistent-identifier control to
the first task. It used the pinned Docker verifier, one worker CPU, and a
180-second **diagnostic** ceiling. No GPU was allocated. This diagnostic
ceiling is not an amendment to the study's five-second verifier limit.

| Fixture | Initial run | After file-access repair |
| --- | --- | --- |
| `complEDS₂_three`, reference | Infrastructure error, 81.19 s | Valid, 52.06 s |
| Same task, invalid identifier | Infrastructure error, 31.43 s | Invalid, 64.84 s |
| `PLift.up_inj`, reference | Valid, 25.58 s | Valid, 25.65 s |
| `Relation.le_onFun_map`, reference | Valid, 30.17 s | Valid, 25.27 s |

The first failure was not a proof failure: Docker could not read the mounted
`Mathlib/Data/Set/Subsingleton.olean.server` file and returned `Bad file
descriptor`. Replacing that file with a byte-identical copy restored reads.
The backup remains local. The file SHA-256 remained
`8765b19b68cfbb349a41505623346a26a6c177d3a2ed713673f7d36de5a0d8b7`;
the full cache hash before and after remained
`14f2b096ac58afa54b625ac64c281bdfc112f9f327b3c196df46bfccf5473fd1`.
This isolates an observed host/container file-access problem, not a proven
root cause inside OrbStack. No cache contents, runtime pins, security controls,
or tasks were changed. Both runs are preserved, including failures.

Raw receipts and selection/source hashes:
[evidence manifest](../protocol/evidence/verifier-readiness-2026-09-16/manifest.json),
[measurement script](../protocol/evidence/verifier-readiness-2026-09-16/measure.py).
The manifest checksums the original files. The recorded Git HEAD alone does
not identify the uncommitted repairs; the receipts also record the measured
verifier source and script hashes.

These are single observations on three tasks, not a latency percentile or
power estimate. They show that the present trusted verifier does not fit five
seconds on this laptop. `timeout` must remain distinct from `invalid`.

### Budget proposal awaiting approval

For **one development integration candidate only**, propose up to 120 seconds
for verification and 180 seconds of active end-to-end work after loading.
Count generation, extraction, transfers, verification and cleanup; separately
report any manual waiting. GPU allocation, including loading and idle time,
must remain below the existing one-hour smoke allocation and count toward the
total study allocation. Stop and report if the candidate cannot fit.

This is a bounded engineering proposal, not a claim that all tasks fit these
limits. It does not authorize the full 32-by-4 smoke or change H1-H3 budgets.
Before either larger run, measure generation and transport, freeze the
applicable resource amendment, and evaluate affordability. Manual/offline
handoff cannot demonstrate prospective H3 utility under matched wall time.

## Authentication and expired sessions

There are three separate states: Google sign-in, a connected Colab runtime,
and a valid HF credential with access to the pinned Gemma files. One does not
prove the others.

- Each Secret read clears the kernel's old `HF_TOKEN` first. Missing permission,
  an unavailable session, or an empty Secret cannot fall back to that token.
- `auth-check` checks identity without the SDK's identity cache and checks the
  pinned config, weight index and tokenizer metadata. It loads no model.
- Rejected credentials, model permission failures and service/network errors
  receive distinct, credential-free messages. A network error is not labeled
  an expired token. Retry reads the current Secret again.
- Online `HFRunner` repeats this check before tokenizer or model loading and
  passes the selected credential explicitly. Offline loading sends no token.
- No credential, account profile, or raw provider error is written to evidence.

The [local live access receipt](../protocol/evidence/verifier-readiness-2026-09-16/local-hf-access.json)
confirms access to those three pinned files from this Mac. It does not prove
Colab Secret access, full weight downloading, or inference. The browser was
signed in, but its T4 runtime was disconnected when inspected. No runtime was
attached to obtain this local receipt.

After publishing an approved execution commit, set the notebook's exact code
pin to that commit. **Its current old pin does not contain these repairs.**
The notebook deliberately stops rather than silently fetching a mutable
branch. In Colab, enable Secret access, reconnect, and rerun setup/authentication.
Do not print the token or paste it into chat. Do not Run All: the old native
Landlock verifier path remains unsupported on the observed Colab kernel.

## Development handoff: tested foundation, not a completed transport

The new `prepare-handoff` command validates the existing prepared corpus and
exports only the 32 public development tasks. Private verifier metadata and
reference proofs are not exported. The actual local export succeeded:

```text
Request: /private/tmp/vrm-dev-public-request-20260916.json
SHA-256: ca9a20453798dee9bff58482214f0f95046cf0149503aa3832e886aad5e81c12
Generated candidates: 0
```

The `DevelopmentHandoff` return store checks request, prompt, model, seed,
token/activation alignment, likelihood summaries and duration consistency.
It writes each complete candidate atomically and refuses conflicting
overwrites, mixed runtime identities and altered arrays. It never adds a
Lean label to model inputs. Checksums establish consistency, not authenticity
of an untrusted producer.

```sh
python -m vrm.cli prepare-handoff \
  --prepared-dir /path/to/approved-prepared-corpus \
  --output /path/to/public-request.json

python -m vrm.cli inspect-handoff \
  --request /path/to/public-request.json \
  --request-sha256 THE_HASH_PRINTED_ABOVE \
  --returns /path/to/returned-candidates
```

The export and inspection CLI were exercised on the unchanged real corpus;
return-store tests use synthetic candidates. Generation dispatch, actual file
transfer, local-verifier consumption and measured transport/GPU accounting
still need end-to-end integration. Neither an empty return manifest nor unit
tests count as a successful smoke. The existing smoke path still enforces the
original limits; do not rerun it expecting the proposed limits to apply.

## Next actions, in order

1. Obtain a decision on the one-candidate budget proposal. Approval of local
   pytest commands is not approval of a model run or a budget amendment.
2. Finish the smallest split-execution connection using this public request
   and return store. Add interrupted-transfer/resume and cost-accounting tests.
3. Obtain publication approval, publish the reviewed code, pin it in the
   notebook, and check Colab/HF access there without the rejected verifier path.
4. Execute only the approved integration candidate. Inspect its genuine model,
   activation, transfer, runtime and Lean receipts before proposing a full
   development smoke. Keep all failures; do not regenerate the corpus.

The runnable gates in [GATES.md](../GATES.md) are recorded by the Unlazy checker.
Budget approval, live Colab readiness and natural-candidate evidence remain
unmet. H1, H2 and H3 have not been evaluated.
