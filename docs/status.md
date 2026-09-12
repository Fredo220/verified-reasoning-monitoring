# Execution status

**Updated:** 2026-09-13

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
- Data preparation produced a complete frozen population in a temporary local
  directory: 32 development, 384 training, 64 validation, 80 ID-test, and 40
  novel-premises tasks.
- The smoke CLI, baseline monitor APIs, Motion-only reader, Three-Reader-shaped
  monitor, budget helpers, and paired-statistics primitives exist.
- The package-backed Colab notebook now requires an exact project commit, reads
  `HF_TOKEN` only from Colab Secrets, provisions the verifier before Gemma, and
  runs the smoke through the package CLI.
- The verifier contract and its exact runtime, provenance, isolation, status,
  and acceptance requirements are documented in `docs/lean_backend.md`.

Current local verification:

```text
159 passed, 7 skipped
```

The seven skips are the six real Linux Comparator/Landrun security cases plus
the disposable-cache mutation check. They are the next gate, not optional
evidence.

## Still unverified

- The pinned native Linux verifier has not completed preflight in a real target
  runtime.
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

1. Run the notebook's verifier-only cells in a blank Linux runtime.
2. Pass preflight plus the seven real adversarial tests, including TCP and Unix
   socket isolation.
3. Only then load Gemma and run the 32 by 4 development smoke.
4. Continue to H1-H3 only if the frozen feasibility thresholds pass.

The repository currently has no commit. Before a remote Colab run, create one
reviewed immutable commit and place its exact hash in `PROJECT_GIT_REV`. Do not
use a branch name or a mutable tag for experiment identity.
