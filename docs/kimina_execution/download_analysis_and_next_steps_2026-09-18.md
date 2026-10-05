# Kimina pilot: recovered results and the next decision

Date: 2026-09-18. Status: development analysis, not a hypothesis test.
This document proposes follow-up work; it does not authorize another run.

## Bottom line

We recovered all four recorded attempts and their activation files. The two
download folders are parts of one run, not two replications. Data recovery
worked. Proof generation did not produce a finished answer: three attempts
reached 8,096 output tokens and one reached the operational deadline. All
four remain inside an unclosed `<think>` section.

The right conclusion is **unresolved generation in this development condition**,
not four Lean-invalid proofs, not a failed monitoring hypothesis, and not
evidence that Kimina cannot prove these statements under other conditions.
Do not train a correctness monitor on these four outputs.

The immediate bottleneck is obtaining finished, verifiable candidates. More
monitor architecture, a larger corpus, or longer output limits would not yet
address the demonstrated problem.

## 1. Evidence and preservation

- Inputs: `/Users/friedrichreichelt/Downloads/results/` and
  `/Users/friedrichreichelt/Downloads/results 2/`.
- 36 unique files, 3,578,592,995 bytes in total, about 3.58 GB.
- Four activation-file SHA-256 values agree with their candidate receipts.
- All 262 listed backup-inventory entries agree with the downloaded files.
  These are repeated entries across 14 checkpoints, not 262 independent files.
- Source identities and receipt payload hashes agree with the frozen source.
- Array headers match full prompt plus response, 28 layers, width 2,048, FP16.
  This audit did not reread every numerical array value or independently
  revalidate replay accuracy. The source checks finiteness and boundary equality
  before saving, but a source check is not a new local numerical audit.
- No final export/remount receipt was found in these folders. The downloaded
  bytes and recorded per-attempt backups are available; a missing receipt is
  not evidence that those bytes were lost.

Frozen request SHA-256:
`c07b94efeef8b868592c99ebd71f4c27a8d0d75b312ba7f3c12df8b3f505f56e`.
Frozen source ZIP SHA-256:
`cbd0a9edffb765c853b3318d4a8d69683bba0b8785c5ffca91c4443159734d27`.

Keep both download folders and the existing Drive copy. Do not add 3.58 GB of
arrays to Git or regenerate samples to replace historical evidence. The older
lost archives remain a separate, documented loss.

Supporting files:
[download audit](download_audit_2026-09-18.json),
[outcome and cost calculations](outcome_analysis_2026-09-18.json), and
[read-only analysis script](analyze_downloaded_outcomes.py).
The script uses the local download paths and writes a derived report to
`/private/tmp/kimina-outcome-analysis.json`; it does not alter source artifacts.

## 2. What the model actually returned

| Development task | Attempt | Input tokens | Output tokens | Stop | Usable final proof |
|---|---:|---:|---:|---|---|
| `complEDS₂_three` | 0 | 726 | 8,096 | Length guard | No |
| `complEDS₂_three` | 1 | 726 | 8,096 | Length guard | No |
| `PLift.up_inj` | 0 | 243 | 8,096 | Length guard | No |
| `PLift.up_inj` | 1 | 243 | 7,345 | Operational timeout | No |

The returned `summary.status = completed` means that four attempt receipts were
stored. It does not mean four EOS completions, four verified proofs, or a
successful feasibility gate. Under the current extraction/repair policy there
are zero finalized proofs and zero repair-eligible outputs. Do not extract a
promising intermediate code fragment from unfinished reasoning after seeing it.

The visible text contains substantial repetition. One sentence appears 133
times in the first attempt. A descriptive repeated-word-12-gram measure ranges
from 0.676 to 0.869 across the four attempts. Its definition is one minus the
number of unique contiguous whitespace-word 12-grams divided by all such
12-grams. This is a post-hoc text diagnostic, not a preregistered collapse
threshold or evidence about an internal reasoning mechanism.

No new candidate was passed to Lean in this analysis. Unfinished generation is
not a valid/invalid Lean label. The two tasks are already exposed development
tasks and must never become independent test examples.

## 3. Measured cost and accounting defects

| Recorded component | Seconds |
|---|---:|
| Previous work carried into the allowance | 1,845.00 |
| New model load | 41.09 |
| New generation | 1,406.95 |
| Activation replay | 31.01 |
| Compression and local storage/hash work | 185.81 |
| Backup checkpoints, including the final one | 232.07 |
| Reconstructed cumulative total | 3,741.93 |

The cumulative allowance was 3,600 seconds. Recorded components exceed it by
141.93 seconds. The summary reports 3,706.58 seconds, omitting approximately
35.35 seconds of final backup. There is also a roughly 0.004-second timing
boundary difference in the reconstructed load accounting.

The new wrapper ran for 1,909.49 seconds, excluding final export. This is about
12.57 seconds above the sum of new recorded components. Do not add the wrapper
time to those components: they overlap. These elapsed pipeline measurements
are not GPU utilization measurements, and missing export time prevents a
claim of complete end-to-end cost accounting.

Source review of `src/vrm/kimina.py:generate` explains the mismatch:

1. Generation receives a deadline, but replay and persistence still run after
   generation finishes or times out. No explicit reserve protects those costs.
2. Backups repeatedly scan and hash old large files, increasing overhead.
3. The summary is written before its final backup and is not a final cost ledger.
4. Saving the requested number of attempts can produce `completed` even when
   a timeout occurred and the operational allowance was exceeded.

Preserving an already-produced answer is preferable to losing it. The repair
should therefore reserve and report persistence time, not discard results at
the deadline. Full activation replay cost only 31 seconds here; it was not the
main bottleneck and does not justify silently dropping tokens or layers.

## 4. Causes: what is known and what remains a hypothesis

**Observed:** long repetition and no final answer. In one EDS attempt the model
claims a definition is missing beyond its base cases, although the prompt
includes the recursive branch. Missing context alone therefore does not explain
all failures.

**Plausible context problem:** in the PLift task, the output treats `up` as an
arbitrary function and refers to an unrelated `f` in the context. The prompt
does not explicitly show the core PLift structure definition. Irrelevant
context or insufficiently explicit dependencies could contribute. The text
does not establish that this caused the loop.

**Plausible model/task mismatch:** these are arbitrary Mathlib development
lemmas. The pinned model card describes competition mathematics and reports
results under a different benchmark and sampling setup. Its success rates
cannot be transferred to two Mathlib tasks with two samples each.

**Runtime/prompt mismatch remains to be tested:** our Transformers path and
proof-body prompt are adaptations, not the model card's vLLM example. Check
them before assuming a model limitation. The published example already uses
8,096 output tokens, temperature 0.6 and top-p 0.95; our guard is not, by itself,
evidence of an incorrect implementation. The pinned tokenizer has no BOS token
and uses the Qwen chat template. Do not import Gemma's BOS handling or add a BOS
because the generation configuration happens to contain a BOS ID.

Primary references:
[pinned Kimina model card](https://huggingface.co/AI-MO/Kimina-Prover-RL-1.7B/blob/1dfd2228afcc35b16eb008a81dfc2b2707750f78/README.md),
[generation configuration](https://huggingface.co/AI-MO/Kimina-Prover-RL-1.7B/blob/1dfd2228afcc35b16eb008a81dfc2b2707750f78/generation_config.json),
[tokenizer configuration](https://huggingface.co/AI-MO/Kimina-Prover-RL-1.7B/blob/1dfd2228afcc35b16eb008a81dfc2b2707750f78/tokenizer_config.json).

## 5. Smallest justified next steps

### A. Repair accounting and inspect the inference contract locally

Keep the current model, verifier, corpus, activation retention and receipts.
Make narrow changes only, after approval to implement:

- Separate attempt storage, EOS completion, extractability, verification and
  budget status. Preserve old receipts; generate a new derived status report.
- Reserve measured replay/save costs before admitting another generation.
  Use one monotonic work deadline and explicitly budget a bounded durability
  tail. Record actual overrun if it occurs; never call it within-budget success.
- Produce a final cost receipt that includes the final backup and reports
  separately any unmeasured export/idle overhead.
- Back up each completed immutable large shard once. Retain initial/resume
  integrity checks, verification of each new shard, and a final full manifest
  check. Do not replace integrity checks with blind existence checks.
- Compare saved prompt IDs and rendering with the pinned chat template, EOS
  rules, generation settings and raw response IDs. Check that instrumentation
  does not modify generation. A short real comparison is needed if local
  inspection cannot settle this; fake tensors cannot establish equivalence.
- Add targeted timeout/final-backup/resume/status regression tests. Preserve the
  old source ZIP. Rerun the approved local suite in its pinned environment;
  the former temporary test interpreter is currently unavailable, and its
  historical pass must not be presented as a fresh pass.

Acceptance: no known mismatch in tokenization/stopping; all elapsed stages
accounted for without double counting; raw output survives interruption; no
new attempt admitted without a persistence reserve; explicit unresolved status.

### B. One bounded, informative development diagnostic

Before spending more GPU time, freeze a small diagnostic request and its stop
conditions. Obtain a new free-Colab allowance: the previous hour is consumed.
Do not silently reset the ledger. A provisional envelope is 45 minutes of
work plus up to 5 minutes of separately reported durability work, to be checked
against measured costs and explicitly approved, not assumed available.

1. Run one fixed, independently verifiable sanity task compatible with the
   existing Lean environment. Verify its reference privately first. A public
   model-card task can be a plumbing control, never independent research
   evidence. Never include its answer in the model prompt.
2. Use the pinned model's intended prompt structure, adapted only to the
   existing supported proof extraction contract. Do not copy unrelated imports,
   disable sandboxing, or introduce unlimited verifier heartbeats from an example.
3. If the sanity task does not yield a finished candidate, investigate that
   condition and stop the batch. Do not launch a larger collection automatically.
4. If the contract is working, apply one predefined prompt/context correction
   rule to the same two open development tasks, with two fixed seeds each.
   Keep model, sampling and output guard unchanged. Do not change the runtime
   backend at the same time unless a demonstrated defect requires it; in that
   case finish that repair diagnostic before studying prompt differences.
5. Preserve all failures and verify every eligible finalized candidate. Apply
   the existing one-repair policy only to eligible attempts, retaining the
   original, feedback, repair and their separate costs. Any repair requires
   explicit budget headroom; an unrun repair stays pending, not unsuccessful.

This is a descriptive development comparison with an already-seen condition,
not a causal replication or an independent test of H1-H3. Do not add repetition
penalties, force an answer, increase limits, or select intermediate proof blocks
without a separately documented change. If generation still fails, publish the
bounded diagnostic and choose one next change explicitly; do not repeatedly
rebuild the corpus until a favorable outcome appears.

### C. Only then assess whether training is possible

A few finished proofs establish pipeline readiness, not sufficient training data.
On a fixed open-development task pool, measure genuine valid and invalid
candidate yield, task diversity, repair yield, activation storage and reader
training cost. Select tasks by a reproducible rule independent of their outcomes.
Unresolved attempts remain visible as coverage failures and costs, never invented
negative correctness labels. Report any candidate-level metric's coverage.

Only if this is feasible should we freeze a task-disjoint training/validation/test
protocol, baselines, reduced-reader details and resource accounting. Fit all
normalization and model selection on training/validation. Keep repaired attempts
grouped with their original task; the monitor must not see verification feedback
for the candidate it predicts. Training and the protected study need separate
authorization. Utility must compare against direct checking and non-internal
selection, not just report that a probe can classify these development outputs.

## 6. What we are not changing

No new research framework, model switch, SAE work, circuit tracing, paid API,
expanded dataset, relaxed scientific threshold, or claim of general reasoning
quality. Keep the existing Gemma/Kimina infrastructure and verifier safety work.
Do not launch H1-H3 with these four unresolved outputs. Do not commit or push
this analysis without an explicit request.

## Decision requested before execution

Approve A first: narrow local repairs and tests. Review their measured results
before authorizing B and its new free-Colab allowance. C remains a later decision.
The current analysis is complete; the empirical investigation is not.
