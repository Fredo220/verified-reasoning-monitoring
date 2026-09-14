# Colab runtime repair: 2026-09-14

## Scope and superseding result

The Lean version-probe defect was fixed and verified in the existing Colab T4
session. That session's native verifier remains unavailable because its kernel
does not support Landlock. A later pre-outcome addendum accepted a hardened
local Linux/arm64 Docker verifier, which passed all registered real cases. See
`docs/docker_verifier_runtime_addendum_2026-09-14.md`. No model candidates or
H1-H3 outcomes were generated during either repair.

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
acceptance artifact for Colab. They do not invalidate the separately recorded
local Docker acceptance.

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

## Historical instructions

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
- The accepted local Docker verifier now satisfies the registered security-case
  gate. The next step is the one-candidate integration check and then the 32x4
  development smoke.
- The public notebook must pin a source commit containing the strict sandbox
  repair. Opening an old commit URL does not automatically update its source pin.

The research protocol and corpus remain unchanged. No scientific feasibility
stop or successful experiment can be claimed from the runtime failure.
