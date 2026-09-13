# Execution status

**Updated:** 2026-09-14

The study has not evaluated H1, H2, or H3. The current deliverable is still the
registered 32-task by four-candidate development smoke.

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
- The package-backed Colab notebook now requires an exact project commit, reads
  `HF_TOKEN` only from Colab Secrets, provisions the verifier before Gemma, and
  runs the registered real verifier suite before the smoke. The smoke uses one
  loaded model process: it first persists one complete integration candidate
  without evaluating the scientific gate, then resumes the same immutable run
  through all 128 candidates. Its cache-mutation test restores the disposable
  cache in a `finally` path. Corpus uploads occur outside the pinned Git
  checkout, failed verifier suites receive a failure label, and the cache is
  rechecked after the smoke before its summary is accepted.
- The verifier contract and its exact runtime, provenance, isolation, status,
  and acceptance requirements are documented in `docs/lean_backend.md`.
- The exact LeanDojo cache object was confirmed unavailable and recorded as an
  operational blocker. A pre-outcome amendment was explicitly approved on
  2026-09-13. It preserves the prepared corpus and protocol while using the
  canonical Mathlib commit, its official Azure build cache, Lean rc1, and the
  matching Comparator revision.
- The amended offline audit-project layout reaches the real Comparator build in
  an isolated Linux/amd64 container. The remaining local failure is the already
  documented `EMFILE` problem under macOS emulation, so native Linux remains
  the required acceptance environment.

Current local verification:

```text
177 passed, 7 skipped
```

This result was reproduced under Python 3.12.1 with the exact pinned Colab
requirements. The post-amendment suite includes regression tests proving that
the native Comparator command is launched inside Landrun with an explicit
argument boundary, the required runtime environment, and the exact hashed
`lean4export` path. It also checks failure-artifact labeling, upload isolation,
and the post-smoke cache-integrity gate. The preserved Linux/amd64 emulation
probe reaches the real Lean build through that path before stopping at the
documented emulation-only file-descriptor failure.

The seven skips are the six real Linux Comparator/Landrun security cases plus
the disposable-cache mutation check. They are the next gate, not optional
evidence.

## Still unverified

- The amended pinned native Linux verifier has not completed preflight in a
  real target runtime.
- The notebook provisioning path has not completed from a blank Colab runtime.
- No real Gemma forward pass or candidate activation receipt exists for this
  study.
- The 128-candidate development smoke has not run.
- Three-Reader's training adaptation is not yet frozen closely enough to support
  H2.
- No protected monitor training, H1/H2 evaluation, equal-budget H3 run, figures,
  or final report exists.

The browser automation service was unavailable during the latest Colab attempt.
That is an operational limitation and is not a scientific feasibility result.

## Next gate

1. Run the amended notebook's verifier-only cells in a blank native-Linux
   runtime and verify the amendment and preserved-corpus hashes.
2. Pass preflight plus the seven real adversarial tests, including TCP and Unix
   socket isolation.
3. Only then run the single-process Gemma smoke: require the first complete
   candidate integration receipt before continuing through the 32 by 4 run.
4. Continue to H1-H3 only if the frozen feasibility thresholds pass.

The local branch has immutable baseline commits, but the execution revision is
not yet available from a configured remote. Before a remote Colab run, publish
the reviewed execution commit only with explicit authorization and place its
exact hash in `PROJECT_GIT_REV`. Do not use a branch name or mutable tag for
experiment identity.
