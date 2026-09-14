# Third-party notices

The verifier image builds and runs pinned third-party components. Their own
licenses continue to apply.

## Moby seccomp profile

`src/vrm/seccomp-no-connect-v0.2.1.json` is derived from Moby's default
seccomp profile at tag `seccomp/v0.2.1`. This project removes `connect` and
`socketcall` from its allowlist. The upstream project is licensed under the
Apache License 2.0:

https://github.com/moby/profiles/tree/seccomp/v0.2.1

## Landrun

The verifier image builds Landrun at commit
`811cfff51ceaf3d9843708aa6d22e9b84ccac8b4`. Landrun is distributed under
the MIT License:

https://github.com/Zouuup/landrun

## Comparator

The verifier image builds Lean Comparator at commit
`ae061f79cdf7af458a26348177cfbd62da0123f6`. The local compatibility patch
`runtime/comparator-landrun-separator.patch` inserts the command separator
expected by the pinned Landrun CLI. It does not change Comparator's proof or
axiom checks:

https://github.com/leanprover/comparator
