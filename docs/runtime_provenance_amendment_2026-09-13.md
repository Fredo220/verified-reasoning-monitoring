# Runtime provenance amendment: 2026-09-13

**Status:** approved before any development or protected model outcomes were
opened.

The frozen Mathlib commit
`1bc7728a050fc18ca2683f614c531cd7050ff063` declares Lean
`v4.29.0-rc1`. The original study configuration incorrectly recorded rc2, and
the exact official LeanDojo pretraced-cache object is no longer retrievable.
The operational evidence is preserved in
`protocol/evidence/lean-dojo-cache-blocker.json`.

The approved correction uses the unchanged Mathlib commit with its declared
rc1 toolchain, Comparator commit
`ae061f79cdf7af458a26348177cfbd62da0123f6`, and Mathlib's official Azure
build cache. Audit projects use pre-resolved path dependencies into that
read-only cache. Candidate and reference-diagnostic builds keep separate,
disposable writable metadata and never run an online dependency update.

The prepared corpus is not rewritten. The machine-readable amendment binds the
historical manifest and every public and private artifact by SHA-256. All task
identities, prompts, splits, verifier metadata, hypotheses, thresholds,
endpoints, and budgets remain unchanged. Receipts carrying the superseded rc2
verifier identity are rejected.

Local amd64 emulation on Apple Silicon reproduced a file-descriptor failure
even after raising the process limit. The required acceptance tests therefore
remain pending on native Linux x86_64; that operational limitation is not a
scientific result.

Machine-readable authority:
`protocol/runtime_provenance_amendment_2026-09-13.json`.
