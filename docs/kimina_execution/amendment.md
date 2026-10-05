# Kimina execution amendment: reduced reader, repairs included

Approved by the project owner on 2026-09-16 before any real Kimina generation.
This supersedes the full-reader and original-attempt-only proposals in the
2026-09-16 goal draft. It does not modify the closed Gemma experiment.
The owner's subsequent instruction below supersedes the proposed token-storage
reduction. No real Kimina generation ran under that discarded proposal.

## Approved choices

1. Only free Colab for inference and neural monitor training; no paid API,
   subscription, credits, or GPU purchase. Existing laptop tests, reports and
   isolated Lean verification remain in place. Free quota is not guaranteed.
2. A reduced Motion + Region + Direction reader is the primary dynamic method.
   This is a transfer/adaptation, not a full Three-Reader reproduction.
3. Originals and at most one eligible model-generated repair are included in
   the primary study. Repair lineage and separate round-level results remain
   mandatory. All comparison arms receive the same repair policy and pay all
   generation, monitoring and verification costs.

## Full capture; no arbitrary token-storage limit

On 2026-09-16 the owner rejected the proposed last-128-response-token storage
limit. That limit and the proposed 64-position prompt sampling are withdrawn
before collection. Store every prompt and generated response token at all 28
post-block layers. No silent downsampling, tail-only retention, or truncation
to fit available memory. Raw token IDs give the sequence position of every
activation; `answer_start` and `answer_end` delimit the generated response.

`capture_chunk_tokens=128` is only the replay batch size. All chunks are processed
with the preceding KV cache; this setting does not discard tokens or context.
The existing input/output generation guards remain unchanged and separately
reported. Full capture means every token of the actual permitted sequence,
not unbounded output generation.

An 8096-token response alone needs 928,514,048 bytes of FP16 states. With the
maximum 16384-token input, the complete shard needs 2,807,562,240 bytes before
compression. Peak memory, replay time and downstream reader training must be
measured on the small real Colab pilot. If this is infeasible, retain partial
receipts and report the measured constraint; do not silently restore a token cap.

The previously authorized reduced-reader option concerns the downstream monitor,
not permission to discard the source activation records. Its precise reduction
must be documented and frozen before training; this collection change does not
claim full Three-Reader fidelity or feasibility. Region/Direction's paper-specific
last-64-token input is a reader design, not a storage limit on the raw activations.

## Repair information boundary

The existing fixed-category feedback policy remains: one repair after a proven
formal failure or extraction failure; no reference proof or unrestricted logs.
No repair of timeout/infrastructure failure as though it were an incorrect proof.
The prior feedback is part of the repair prompt and therefore visible to all
text/internal comparators. It is not the label of the current repaired candidate.
Never claim repair-context features are independent of previous verification.
Report original and repair strata, a round/feedback-only control, and task-family
weighted prediction metrics, alongside the combined primary policy result.

Repairs stay with their original theorem in every split and bootstrap sample.
A theorem is solved if any permitted original or repair is verified within that
arm's frozen resource allowance. Verify both originals in a candidate group,
unless the task is already solved, before forming the next group of eligible
repairs; never repair only for the internal arm. Do not insert reference proofs
or silently replace failed originals. Fix detailed resource/dispatch accounting
on development before protected outcomes. No obsolete 5s/30s deadline.

## Execution order and status

Reference/sandbox acceptance -> two tasks x two originals plus eligible repairs
-> measured development expansion and reader training feasibility -> frozen
H1/H2/H3 protocol and audit -> protected evaluation -> honest report.

The first development allowance remains 3600 measured pipeline seconds, not a
new allocation on every resume or repair. The historical twelve-hour envelope
is a ceiling; subsequent allocations require a measured cost plan. The owner
has authorized end-to-end execution on free resources, not unbounded retries.
No commit or push is authorized by this amendment.

H1 remains validity prediction; H2 now concerns the explicitly reduced reader;
H3 remains additional verified solutions at matched compute, now with repairs.
A feasibility stop is not a completed evaluation of these hypotheses. No
Kimina results or protected outcomes existed when this amendment was written.

## Post-pilot correction, authorized 2026-09-16

The owner approved continuing the revised repair plan after the two-task pilot.
The following changes were designed after viewing its open-development outputs;
they are not preregistered explanations of those outputs or a new protected test.
Historical results, extraction decisions and source identity stay unchanged.

The separate `kimina-development-context-v2` profile includes the source module,
fully qualified target and explicitly reviewed public source excerpts. Each
excerpt is bound to the pinned source hash and line range. Target proofs are
excluded. The two-task line plan is diagnostic, not a representative corpus.
Range/hash tests are not proof that the context is semantically sufficient:
real Lean context acceptance and reference-leakage review remain required.

The separate extractor permits only enumerated outer wrappers: one completed
reasoning block, one final Lean fence, approved redundant import lines and the
exact target declaration. Raw output and transformation hashes are retained;
proof content is not repaired by the parser. Imports not present in the reviewed
allowlist remain rejected. In particular, this does not retroactively accept the
historical `import Mathlib` outputs or make their invalid bodies valid.

Corrected preparation requires explicit prior-pipeline cost accounting. The
3600-second config field remains a cumulative ceiling, not another free hour.
Before collection, reconcile previous costs and agree a measured scope. Do not
upload the earlier planning-only request prepared without that carry-in.
No corrected generation, reader training or H1-H3 evaluation has run.

The original source ZIP is preserved at
`artifacts/kimina-development-20260916/kimina-source-full-capture.zip`, SHA256
`d7e9731f6c3388c7781dafd9f1cdf3de83643398b2876036ac50980e432c14f9`.
Validate historical returned artifacts using that frozen source/config, not
the edited package's new source identity. Returned activation ZIPs still need
local handoff and hash verification; the source backup is not their substitute.
