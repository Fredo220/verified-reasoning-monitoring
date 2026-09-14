# Docker verifier runtime addendum: 2026-09-14

**Status:** approved and recorded before any Gemma candidate or H1-H3 outcome
was opened.

The observed free-Colab kernel reports Landlock ABI 0, so Python packages
cannot make the registered native sandbox safe there. The user authorized
continuing despite that operational incompatibility before model execution.
This addendum accepts one hardened local Linux/arm64 Docker runtime for Lean
verification while Colab remains the planned generation environment.

## What changed

- Verification uses Docker execution on Linux/arm64 rather than native
  execution inside Colab.
- The image is addressed by immutable image ID
  `sha256:0c1ed089532fdb118749ec6033e634282344766c923c57738f82ee07b62ce21c`.
- A one-line patch adds the missing `--` boundary between Comparator and the
  pinned Landrun CLI. Its SHA-256 is
  `02382151f52b32c7d66bb355974bc218cd73644f1557be11853b78499a8bee03`.
- Docker disables networking, uses a read-only filesystem, drops all
  capabilities, applies resource limits and a pinned seccomp profile, and
  mounts the canonical Mathlib cache read-only.
- The inner Landrun invocation uses `--best-effort` because the host exposes
  Landlock ABI 8 rather than the newer ABI requested by the pinned binary.
  Acceptance remains fail-closed: concrete allowed-write, denied-write, TCP,
  Unix-socket, cache and proof-audit probes must all pass. The outer seccomp
  policy independently denies `connect` and `socketcall`.

## What did not change

The prepared corpus, task identities, prompts, private verifier metadata,
model revision, hypotheses, gates, endpoints, candidate policy and compute
budgets are unchanged. The exact Mathlib, Lean, LeanDojo, Comparator, Landrun,
lean4export and Lean4Checker revisions from the approved 2026-09-13 amendment
remain in force.

The compatibility patch changes process argument framing only. It does not
alter theorem reconstruction, permitted axioms, kernel replay or the
`valid`/`invalid` decision rule.

## Acceptance evidence

The final runtime passed preflight and the seven registered real cases:

1. known-valid proof accepted;
2. known-invalid proof rejected;
3. target self-reference rejected;
4. `sorry` rejected;
5. unauthorized axiom rejected;
6. filesystem escape rejected without creating the target file;
7. disposable-cache mutation rejected as `cache_digest_mismatch`.

The accepted receipt binds the container image and platform, cache, seccomp
profile, compatibility patch and built Comparator, lean4export and Landrun
binaries by SHA-256. The machine-readable acceptance record is
`protocol/evidence/docker-verifier-acceptance-2026-09-14.json`.

The full cache was initially rehashed inside every candidate worker. Moving
that redundant 6.7 GB digest to the already required preflight and post-run
checks reduced a five-second known-valid probe from 40.75 to 6.61 seconds.
The candidate still timed out: a successful long-timeout control required
40.53 seconds. A Docker-volume control did not materially change the result.
This accepted local verifier therefore does not meet the registered five-second
per-candidate limit. The separate record is
`protocol/evidence/docker-verifier-budget-probe-2026-09-14.json`.

The machine-readable addendum is
`protocol/docker_verifier_runtime_addendum_2026-09-14.json`. This is an
operational runtime correction and scheduling result, not evidence for H1, H2
or H3. Timeouts remain unresolved and must not be relabeled as invalid.
