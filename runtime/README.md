# Local verifier image

This directory builds the hardened Linux/arm64 verifier accepted on
2026-09-14. It does not contain the 6.7 GB Mathlib cache.

Build from the repository root:

```bash
docker build \
  --file runtime/Dockerfile.verifier-arm64 \
  --tag vrm-verifier-arm64:20260914 \
  runtime
```

Record the immutable local image ID:

```bash
docker image inspect vrm-verifier-arm64:20260914 --format '{{.Id}}'
```

The accepted run used:

```text
sha256:0c1ed089532fdb118749ec6033e634282344766c923c57738f82ee07b62ce21c
```

That local ID is evidence for the recorded run, not a downloadable image
reference. A rebuild with a different ID must repeat preflight and all seven
real acceptance cases before use. Set `VRM_LEAN_IMAGE` to the exact image ID;
do not use a mutable tag as experiment identity.

The build applies `comparator-landrun-separator.patch`, which only adds the
command boundary required by the pinned Landrun CLI. Its digest and the built
Comparator and lean4export binary digests are checked at runtime.
