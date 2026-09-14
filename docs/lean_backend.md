# Trusted Lean verifier backend

**Status:** the hardened local Linux/arm64 Docker runtime passed preflight and
all seven registered real acceptance cases on 2026-09-14. No Gemma candidate or
H1-H3 outcome had been opened at that point.

This document describes the verifier used by the approved study. It records the
implemented trust boundary and the evidence required before any real Gemma
candidate can count as `valid`. It is not a security certification.

## Purpose

The model produces one complete, unfenced Lean proof beginning with `by`. The
host process does not execute that proof directly and a LeanDojo
`ProofFinished` observation cannot grant validity. A candidate is `valid` only
when pinned Comparator accepts the reconstructed challenge/solution pair and
the worker returns the exact provenance receipt expected by the host.

## Frozen identity

| Component | Frozen value |
| --- | --- |
| Benchmark | LeanDojo Benchmark 4 v3, DOI `10.5281/zenodo.18815372` |
| Mathlib | `https://github.com/leanprover-community/mathlib4` at `1bc7728a050fc18ca2683f614c531cd7050ff063` |
| LeanDojo | version `4.20.0`, commit `3bbc4c02fb8a058b282c8d3982a02d6563f3b08a` |
| Lean | `v4.29.0-rc1` |
| Comparator | `ae061f79cdf7af458a26348177cfbd62da0123f6` |
| Comparator compatibility patch | `02382151f52b32c7d66bb355974bc218cd73644f1557be11853b78499a8bee03` |
| Landrun | `811cfff51ceaf3d9843708aa6d22e9b84ccac8b4` |
| lean4export | `048394e1afeeb52b0fa27bcf3f1ade2ff0f0ab6d` |
| Lean4Checker | `b7398199245524275543dec6113229c9bb4902e5` |
| Permitted axioms | `propext`, `Quot.sound`, `Classical.choice` |
| Accepted container image ID | `sha256:0c1ed089532fdb118749ec6033e634282344766c923c57738f82ee07b62ce21c` |
| Accepted container platform | `linux/arm64` |
| Hardened seccomp profile | `85ea2ee4cfc4f957232ea300ee87890d4a56f44aeeb4a4ecd177e3eb778c5c1e` |

`configs/study.json` is the machine-readable scientific authority. The approved
runtime amendment and Docker addendum govern only the fields they explicitly
supersede. `src/vrm/lean.py` and this document must agree with those records.
The old notebook's native transport is not an accepted execution path.

The exact LeanDojo pretraced-cache object was unavailable from its documented
official location. Before any model outcome was opened, the approved
[runtime provenance amendment](runtime_provenance_amendment_2026-09-13.md)
replaced only that unavailable runtime path with the same canonical Mathlib
checkout and Mathlib's official Azure build cache. It also corrected the Lean
and Comparator pins to the versions required by that checkout. Tasks, prompts,
splits, private verifier data, hypotheses, endpoints, and gates did not change.

The observed Colab kernel could not enforce Landlock. Before any model outcome
was opened, the [Docker runtime addendum](docker_verifier_runtime_addendum_2026-09-14.md)
therefore accepted a hardened local Linux/arm64 verifier. It preserves the same
proof semantics and component revisions while binding the container, seccomp
profile and required one-line Landrun compatibility patch.

## Information boundary

The generator receives only the public task fields and prompt defined in
`docs/data_contract.md`. Reference proofs, theorem source spans, source and
trace digests, and all verification outcomes remain in the private verifier
artifact.

Immediately before verification, the workflow joins public and private rows by
task identity and revalidates:

- benchmark, repository, commit, task, split, file, and theorem identity;
- canonical private-record and population hashes;
- source, trace, and full-cache hashes;
- exact theorem declaration and proof boundaries.

The candidate replaces only the recorded proof span. The theorem statement and
surrounding source remain pinned. The reference proof is used only after a
candidate rejection to check that the frozen source and verifier still accept
the original theorem; it is never a model or monitor input.

## Comparator decision

Each verification creates an isolated Lean project with:

- a `Challenge` module containing the target theorem with `sorry` in the proof
  position;
- a `Solution` module containing the same theorem and the candidate proof;
- the exact target theorem name;
- only the three registered permitted axioms;
- NanoDA disabled.

Comparator and its lean4export/Lean4Checker dependencies are pinned and their
built executables are hashed. For the native path, the directory containing the
same hashed `lean4export` executable is prepended to `PATH` before Landrun starts
Comparator; an unbound exporter path fails closed. A successful candidate is
accepted only with an exact audit receipt binding the task, source, trace,
cache, tools, runtime, and axiom policy. A missing, malformed, or mismatched
receipt becomes `infrastructure_error`, never `valid`.

## Linux isolation

The verifier runs as a non-root user in a Linux container. Preflight must
confirm all of the following before any candidate can be trusted:

1. Linux and non-root execution.
2. A clean pinned Mathlib checkout populated from the official Mathlib Azure
   build cache, with the expected full digest and Lean toolchain.
3. A clean pinned Comparator checkout, dependency revisions, and executable
   hashes.
4. The expected Landrun binary digest.
5. The combined Docker/Landrun boundary can write inside the temporary audit
   tree but cannot write outside it.
6. The combined boundary blocks both TCP and Unix-socket connections.
7. The runtime Lean version matches the frozen toolchain.

The trusted host stages each audit project from verified inputs. Comparator,
Lake, and Lean then run under Landrun with `/` read-only and only the temporary
audit tree writable/executable. The sandbox receives only the required runtime
environment and an empty `GITHUB_ACCESS_TOKEN`. The generated proof is
constrained by operating-system isolation and Comparator/kernel checks rather
than by fragile text filtering.

Each audit project receives a pre-resolved, offline Lake manifest. Immutable
source files and build outputs are linked from the clean cache; only Lake's
small per-project configuration metadata is copied into the writable audit
tree. Candidate and diagnostic checks use separate trees. This prevents an
audit from mutating the canonical cache while avoiding any network resolution
during verification.

Docker adds a read-only filesystem, disabled networking, dropped capabilities,
resource limits, a non-root user, a read-only cache mount and a pinned Moby
seccomp profile with `connect` and `socketcall` removed from the allowlist.
Landrun provides the inner filesystem boundary. Because the available kernel
exposes Landlock ABI 8, the inner process uses `--best-effort`; the runtime is
accepted only when concrete write and network denial probes pass. Colab's
unsupported native path remains rejected rather than silently weakened.

## Status policy

The backend reports four distinct states:

- `valid`: Comparator accepted and the exact audit receipt matched.
- `invalid`: Comparator rejected the candidate and accepted the pinned original
  proof in the diagnostic check.
- `timeout`: only the candidate Comparator process exceeded its candidate
  deadline.
- `infrastructure_error`: preflight, provenance, isolation, worker transport,
  source reconstruction, or diagnostic validation failed.

Infrastructure deadlines and setup failures are never converted to candidate
timeouts or negative labels. The final H1/H2 missingness policy is frozen only
after the development smoke, as required by the research plan.

## Real acceptance evidence

Local mocked and unit tests are insufficient. In one freshly provisioned Linux
runtime, set `VRM_RUN_REAL_LEAN_TESTS=1` and provide the audited
`VRM_LEAN_REAL_CASES` fixture. The seven opt-in tests must establish:

1. a known-valid proof is `valid`;
2. a known-invalid proof is `invalid`;
3. target self-reference is rejected;
4. `sorry` is rejected;
5. an unauthorized axiom is rejected;
6. a sandbox-escape attempt is rejected;
7. mutation of a disposable Mathlib cache copy makes preflight fail with
   `cache_digest_mismatch`.

The final Docker run saved structured outcomes, component versions and hashes,
runtime identity and elapsed times. All seven cases passed. The sanitized,
machine-readable record is
`protocol/evidence/docker-verifier-acceptance-2026-09-14.json`. A later runtime
must reproduce acceptance under its own immutable identity; this result does
not make arbitrary Docker or native environments trusted.

## Operational entry points

The accepted local verifier calls:

```text
vrm preflight --execution-mode docker \
  --cache-dir <verified-mathlib-cache> \
  --cache-sha256 <registered-cache-sha256> \
  --landrun-sha256 <registered-landrun-sha256>
```

`VRM_LEAN_IMAGE` must be the immutable accepted image ID or a newly built image
that passes the full acceptance suite. Only a `ready` result permits later
verification. Gemma generation can still run on Colab, but Colab's observed
kernel must not be presented as the trusted verifier. Any split execution must
preserve immutable request identities and include transfer and verification
costs in the later equal-budget utility study. Temporary runtime unavailability
is an operational blocker, not evidence for or against scientific feasibility.
