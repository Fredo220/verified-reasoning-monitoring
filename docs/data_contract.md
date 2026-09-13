# Data preparation contract

`vrm.data.prepare` is the only supported path from the pinned LeanDojo input
to study task files. Miniature `traced_metadata.jsonl` inputs used by unit tests
exercise this contract but are not benchmark evidence.

## Frozen source

Preparation is pinned to LeanDojo Benchmark 4 v3, DOI
`10.5281/zenodo.18815372`, archive MD5
`b58af89599d5bbc792abc3744e5d37d9`, Mathlib repository
`https://github.com/leanprover-community/mathlib4` at commit
`1bc7728a050fc18ca2683f614c531cd7050ff063`, LeanDojo `4.20.0`, and Lean
`v4.29.0-rc1`. This corrects the earlier rc2 declaration under the approved,
hash-bound [runtime provenance amendment](runtime_provenance_amendment_2026-09-13.md).
The already prepared corpus is preserved byte-for-byte: its historical
manifest and every public and private artifact must match the hashes recorded
in that amendment before use. Any conflicting declared provenance blocks
preparation or execution. The
archive checksum must be verified when the archive is acquired; the extracted
benchmark's `metadata.json`, every benchmark row, and every traced metadata row
must identify the exact pinned repository and commit.

Only `novel_premises/train.json` supplies `dev`, `train`, `val`, and `id_test`.
Only `novel_premises/test.json` supplies `ood_test`. The upstream validation
file is never read. Source text is read from `source_root` when supplied and
otherwise from `<benchmark_root>/sources`.

## Eligibility

A task is eligible only when all of the following hold:

- Its benchmark identity has one exact, unambiguous traced-metadata match.
- Any present `theorem_statement` is non-null and non-empty.
- Its initial state is the root state of the pretraced proof and does not expose
  the target theorem name.
- It has at most six recorded tactics.
- A complete reference proof is recovered from an exact source span or from a
  trusted `TracedTheorem.get_tactic_proof` export. Tactic trace entries are
  never concatenated. When both sources exist, their strings must match exactly.
- The complete reference proof is at most 64 tokenizer tokens.
- The final rendered Gemma user/chat prompt is at most 512 tokenizer tokens.
  Chat rendering is performed before counting, tokenization adds no second BOS,
  and neither input is truncated.

Source positions are one-based Unicode character positions with an exclusive
end column. Source hashes, declaration boundaries, proof boundaries, repository
identity, trace hashes, and any exported-proof origin are validated before a
task can enter the pool.

## Splits and variants

Full counts are `32/384/64/80/40` for
`dev/train/val/id_test/ood_test`; reduced counts are `32/192/32/40/20`.
Reduced preparation additionally requires a valid `budget_decision.json` made
before protected test access and showing that the full plan exceeds the budget
while the reduced plan fits it.

Task identities are hashes of pinned repository and declaration identity.
Variant grouping uses explicit group identity when supplied and normalized
theorem prompts otherwise. Group and normalized-prompt links are closed
transitively. Components spanning upstream train and test are excluded; one
stable representative is retained from each remaining component. Representatives
are assigned by a versioned SHA-256 ordering, independent of input order.
Insufficient independent groups block preparation; tasks are never reused and
quotas are never silently changed.

## Information boundary

Each public `<split>.jsonl` row contains exactly:

`task_id`, `group_id`, `split`, `repo_url`, `repo_commit`, `file_path`,
`full_name`, and the raw Gemma user-message `prompt`. Preparation applies the
pinned chat template only to enforce the 512-token eligibility limit. Inference
applies that same pinned template exactly once to the stored user message.

It contains no reference proof, separately named initial state, verifier label,
or source position. `eligibility_audit.jsonl` contains only task/group identity,
eligibility reasons, token/tactic counts, and content hashes. It contains no
proof or initial-state text.

`verifier_metadata.jsonl` is a separate trusted-verifier artifact. It contains
the reference proof, source positions, source and trace hashes, and other
verification-only metadata. Every payload has a canonical SHA-256 content hash,
and the manifest hashes the complete artifact. This file must never be supplied
to the generator, monitor, ranker, or training feature pipeline.

## Failure and reproducibility

Missing, malformed, ambiguous, mismatched, or insufficient inputs return a
manifest with `status: "blocked"`, explicit blockers, and rejection counts. A
blocked destination contains only `manifest.json`; no protected split or private
metadata file is emitted.

Outputs use sorted canonical JSON and deterministic row ordering. Files are
staged and renamed as one directory. An existing output path raises
`FileExistsError` and is never overwritten.
