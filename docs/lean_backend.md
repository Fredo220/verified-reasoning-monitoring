# Trusted Lean verifier backend

**Status:** implemented and unit-tested locally; real Linux acceptance remains
unverified.

This document describes the verifier used by the approved study. It records the
implemented trust boundary and the evidence still required before any real
Gemma candidate can count as `valid`. It is not a security certification and it
does not claim that the seven opt-in Linux tests have passed.

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
| Lean | `v4.29.0-rc2` |
| Comparator | `3090445149fbaba51d8177df4eb2121573788341` |
| Landrun | `811cfff51ceaf3d9843708aa6d22e9b84ccac8b4` |
| lean4export | `048394e1afeeb52b0fa27bcf3f1ade2ff0f0ab6d` |
| Lean4Checker | `b7398199245524275543dec6113229c9bb4902e5` |
| Permitted axioms | `propext`, `Quot.sound`, `Classical.choice` |

`configs/study.json` is the machine-readable authority. `src/vrm/lean.py`, the
notebook, and this document must agree with it.

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
built executables are hashed. A successful candidate is accepted only with an
exact audit receipt binding the task, source, trace, cache, tools, runtime, and
axiom policy. A missing, malformed, or mismatched receipt becomes
`infrastructure_error`, never `valid`.

## Native Linux isolation

The Colab path uses native Linux under a dedicated non-root user. Preflight must
confirm all of the following before model loading:

1. Linux and non-root execution.
2. A clean pinned Mathlib cache with the expected full digest and Lean
   toolchain.
3. A clean pinned Comparator checkout, dependency revisions, and executable
   hashes.
4. The expected Landrun binary digest.
5. Landrun can write inside the temporary audit tree but cannot write outside
   it.
6. Landrun blocks both TCP and Unix-socket connections.
7. The runtime Lean version matches the frozen toolchain.

Candidate project setup runs under Landrun with `/` read-only and only the
temporary audit tree writable/executable. The environment clears
`GITHUB_ACCESS_TOKEN`. The generated proof is constrained by operating-system
isolation and Comparator/kernel checks rather than by fragile text filtering.

The code also contains a Docker transport with a read-only filesystem,
network disabled, dropped capabilities, resource limits, a non-root user, and a
read-only cache mount. The approved free-Colab path tests the native transport;
support for Docker is not evidence that the native path works.

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

## Required real acceptance evidence

Local mocked and unit tests are insufficient. In one freshly provisioned Linux
runtime, set `VRM_RUN_REAL_LEAN_TESTS=1` and provide the audited
`VRM_LEAN_REAL_CASES` fixture. The seven opt-in tests must establish:

1. a known-valid proof is `valid`;
2. a known-invalid proof is `invalid`;
3. target self-reference is rejected;
4. `sorry` is rejected;
5. an unauthorized axiom is rejected;
6. a sandbox-escape attempt is rejected;
7. mutation of a disposable cache copy makes preflight fail with
   `cache_digest_mismatch`.

The run must save structured outcomes, component versions and hashes, runtime
identity, and elapsed times. Until all seven tests pass, the verifier is
operationally unverified and the 32-by-4 Gemma smoke must not start.

## Operational entry points

The notebook provisions dependencies and then calls:

```text
vrm preflight --execution-mode native ...
```

Only a `ready` result permits later verification. The package-backed smoke uses
the same configured backend; notebook cells do not implement an alternative
judge. Temporary Colab unavailability is an operational blocker, not evidence
for or against scientific feasibility.
