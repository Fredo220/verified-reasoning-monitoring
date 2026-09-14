# Execution status

**Updated:** 2026-09-14

The study has not evaluated H1, H2, or H3. The trusted-verifier implementation
gate is complete. The next empirical gate is one natural Gemma candidate,
followed by the registered 32-task by four-candidate development smoke.

## Accepted local implementation

- The public prompt remains raw user content and Gemma's chat template is
  applied exactly once at runtime. The real pinned tokenizer check produces one
  initial BOS token.
- Public task data is separated from reference proofs and verifier-only source
  metadata. Joined records and their hashes are revalidated before verification.
- Candidate activations, prompt boundaries, costs, verification results, and
  immutable request identities are stored atomically and can be resumed.
- The approved prepared-corpus archive has been restored and revalidated without
  regeneration: 32 development, 384 training, 64 validation, 80 ID-test, and 40
  novel-premises tasks. Its SHA-256 is
  `e4d94441f782f79c0cbf7305fba974d9d8b1768e84e1bbff940dec6a4c81c684`; the
  contained frozen manifest matches the amendment-bound hash
  `9114e446a0050eded479289522211c8141a513b65990a3c5dfe6d59031d7482c`.
- The smoke CLI, baseline monitor APIs, Motion-only reader, Three-Reader-shaped
  monitor, budget helpers, and paired-statistics primitives exist.
- The package-backed Colab notebook requires an exact project commit and reads
  `HF_TOKEN` only from Colab Secrets. Its existing native-verifier cells now
  fail safely on the observed Colab kernel and must not be retried. Generation
  and local verification still need a hash-bound split-execution handoff before
  the one-candidate integration probe can run.
- The verifier contract and its exact runtime, provenance, isolation, status,
  and acceptance requirements are documented in `docs/lean_backend.md`.
- The exact LeanDojo cache object was confirmed unavailable and recorded as an
  operational blocker. A pre-outcome amendment was explicitly approved on
  2026-09-13. It preserves the prepared corpus and protocol while using the
  canonical Mathlib commit, its official Azure build cache, Lean rc1, and the
  matching Comparator revision.
- The observed Colab kernel cannot enforce Landlock and remains rejected as a
  native verifier environment. A pre-outcome runtime addendum records the
  hardened local Linux/arm64 Docker path instead.
- The accepted Docker image is pinned by image ID and uses the same canonical
  Mathlib, Lean, LeanDojo, Comparator, Landrun, lean4export and Lean4Checker
  revisions. Its one-line Comparator patch only inserts the child-command
  separator required by the pinned Landrun CLI.
- Docker runs networkless and read-only with dropped capabilities, resource
  limits, a non-root user, a read-only cache and a pinned seccomp profile. The
  inner Landrun filesystem boundary is accepted only after concrete write,
  TCP and Unix-socket denial probes pass.
- Real preflight and all seven registered acceptance cases passed: valid,
  invalid, self-reference, `sorry`, unauthorized axiom, sandbox escape and
  disposable-cache mutation.

Current local verification in the pinned Python 3.12 environment:

```text
191 passed, 7 real tests skipped
```

The seven real cases also passed separately against the accepted Docker image.
The post-addendum suite includes regression tests proving that
the native Comparator command is launched inside Landrun with an explicit
argument boundary, the required runtime environment, and the exact hashed
`lean4export` path. It also checks failure-artifact labeling, upload isolation,
and the post-smoke cache-integrity gate. The real cases are no longer pending.
Their final receipt binds the Linux/arm64 image ID, seccomp profile,
compatibility patch, cache and built tool binaries. H1-H3 remain untouched.

The redundant per-candidate full-cache hash was removed while retaining the
full preflight and post-run hashes, the read-only cache mount and exact target
source hashing. A registered five-second known-valid control then fell from
40.75 to 6.61 seconds but still timed out. The same proof was accepted with a
long timeout in 40.53 seconds. The local verifier is therefore correct but not
fast enough for the registered five-second utility schedule; this is not a
candidate-yield or hypothesis result.

## Still unverified

- The notebook provisioning path has not completed from a blank Colab runtime.
- The notebook has not yet been adapted to hand generated candidates to the
  accepted local verifier without violating the later H3 cost accounting.
- No real Gemma forward pass or candidate activation receipt exists for this
  study.
- The 128-candidate development smoke has not run.
- Three-Reader's training adaptation is not yet frozen closely enough to support
  H2.
- No protected monitor training, H1/H2 evaluation, equal-budget H3 run, figures,
  or final report exists.

Colab's kernel limitation is operational and not a scientific feasibility
result. The notebook must not rerun the rejected native-verifier path.

## Next gate

1. Keep the accepted local Docker verifier immutable and revalidate the
   addendum, acceptance record and preserved-corpus hashes.
2. Locate a verifier runtime that reproduces acceptance and completes the
   known-valid control within five seconds, or record resource infeasibility
   under the frozen budget. Do not extend the deadline.
3. Only then run one natural Gemma candidate through generation, activation
   persistence and trusted Lean verification without exposing verifier metadata
   to Gemma.
4. Continue through the 32 by 4 development smoke only after that receipt is
   complete and resumable.
5. Continue to H1-H3 only if the frozen feasibility thresholds pass.

Before a remote Colab generation run, publish the reviewed execution commit and
place its exact hash in `PROJECT_GIT_REV`. Do not use a branch name or mutable
tag for experiment identity.
