# Colab runtime repair: 2026-09-14

## Scope and current result

The Lean version-probe defect is fixed and verified in the existing Colab T4
session. The native verifier is still unavailable because that session's kernel
does not support Landlock. This is an operational blocker, not a study outcome.
No model candidates or H1-H3 outcomes were generated during this repair.

## Evidence observed directly in Colab

- Existing runtime and Python variables survived reconnecting; no dependency
  rebuild was needed.
- Under `vrmrunner`, `lean --version` returned exit code 0 and Lean 4.29.0-rc1,
  commit `985f350dcd18fc7814dfa677cac09933f44f3215`.
- The subsequent native preflight failed its filesystem confinement test.
- A diagnostic using the old `--best-effort` command returned exit code 0 and
  `write_escaped: True` when writing outside the writable allowlist.
- Removing `--best-effort` returned exit code 1 with:

```text
Failed to apply sandbox: failed to apply Landlock restrictions:
missing kernel Landlock support. Got Landlock ABI v0,
wanted {Landlock V9; FS: all; Net: all; Scoped: all}
```

These are transcribed observations from the Colab diagnostic output, not an
exported verifier acceptance artifact. The seven acceptance tests have not passed.

## Repairs

1. Probe Lean directly in the pinned toolchain directory. `lake env` needlessly
   resolves dependencies during a version check. Lake's pinned source also shows
   that failed Git metadata reads can trigger an apparent URL-change/reclone path;
   cross-user ownership is a plausible explanation for the previous `plausible`
   error, but its exact Git stderr was not recovered.
2. Preserve the version command's stderr on failure.
3. Remove Landrun's permissive `--best-effort` option and retain the real positive
   and negative sandbox tests.
4. Run sandbox checks before cache hashing, and in notebook provisioning before
   the expensive Comparator/Mathlib steps.

Targeted local validation: 82 passed, 7 real-Linux tests skipped. These local
results are not evidence of native sandbox acceptance.

## Instructions for continuation

- Do not repeat Mathlib downloads, rebuild the corpus, change thresholds, or
  bypass the sandbox on this Colab session. Python packages cannot enable a
  missing host-kernel Landlock facility.
- Preserve the prepared archive and existing runtime files while deciding where
  verification can run. A Linux environment must pass the real sandbox tests.
- A different Colab allocation might have different capabilities; test the small
  sandbox check first. Do not assume support or repeatedly allocate GPUs hoping
  for a different outcome.
- Alternatively, investigate the existing Docker verifier on a compatible host.
  Moving verification outside Colab requires a documented execution arrangement;
  H3 must still account for transfers and all arm costs consistently.
- Only after successful sandbox acceptance run the seven registered verifier
  tests, then the one-candidate integration check and 32x4 development smoke.
- The public notebook must pin a source commit containing the strict sandbox
  repair. Opening an old commit URL does not automatically update its source pin.

The research protocol and corpus remain unchanged. No scientific feasibility
stop or successful experiment can be claimed from the runtime failure.
