# Verified Reasoning Monitoring: approved protocol

Approved 2026-09-07. Status: implementation; no empirical outcomes yet.

## Question and hypotheses

Can internal activation signals select short complete Lean proofs well enough
to produce more verified solutions under the same total inference-time budget?
Selection is not improved underlying reasoning, intuition or general safety.

- H1: internal signals predict validity beyond likelihood and text baselines.
- H2: Three-Reader improves over static multilayer and motion-only probes.
- H3 (primary): the validation-selected internal ranker solves more tasks than
  both the frozen non-internal champion and direct checking at equal total cost.

H1/H2 may hold without H3. Negative or inconclusive results complete the study.
The prior Familiarity x Answerability study remains closed and unchanged.

## Literature and reuse

[Constitutional Classifiers++](https://arxiv.org/html/2601.04603v1): contextual
internal probes and joint measurement of utility, cost and false alarms.
Jailbreak labels and token-weighted safety losses are not blindly transferred.
[Three-Reader](https://arxiv.org/html/2608.05660v1): Motion, Region and Direction
plus ablations. Read a completed proposal before verification; do not claim
mid-generation detection. Record all Gemma adaptations before training.

Reuse tokenizer, hook, checkpoint and test patterns from
[the parent repository](https://github.com/Fredo220/Answerability-x-Familarity-)
at commit `f8ddad10df72155454cdc0aedf0f3e72bd0f1600`. No old labels, datasets,
trained probes, layer choices, thresholds or protected outcomes are reused.

## Resources and feasibility

Separate repository and English documentation; notebook-first. Frozen
`google/gemma-2-2b-it`, exact revision, FP16 on T4, batch 1, prompt <=512 tokens,
proposal <=64 tokens, temperature 0.7, top-p 0.95. No paid APIs or automatic
quantization/model changes. Laptop has 8 GB system RAM, not 8 GB VRAM.

Twelve allocated GPU hours maximum: estimates of 1 smoke, 4 collection, 2 reader
training, 4 utility testing, 1 reserve. Free Colab availability is not guaranteed.
Run a real 32-task development smoke with 4 proposals each. Require >=20 valid,
>=20 invalid and >=8 mixed-validity tasks, with complete receipts. These are
feasibility conditions, not evidence for H1-H3. Record timeouts separately.

Use existing LeanDojo/pretraced infrastructure, not full Mathlib tracing. Check
real tokenizer/forward, activation positions, memory, disk and interrupt/resume.
Do not start large runs if safe verification or informative model outputs are
unavailable. Do not fabricate candidates or restart corpora until a gate passes.

## Dataset and information boundary

Original LeanDojo Benchmark 4 novel_premises with compatible pinned source,
toolchain, checksum and licenses. No unverified third-party mirror. Eligible
complete reference proofs have <=6 recorded tactics and <=64 Gemma tokens;
the exact rendered prompt fits 512 tokens. References are never model inputs.
Concatenating nested tactic traces does not reconstruct a complete proof.

Targets: dev32, train384, validation64, ID80, OOD40. Reduced minimum: dev32,
train192, validation32, ID40, OOD20. Train/dev/validation/ID use original train;
OOD uses original test. Group normalized duplicates/variants and assign by stable
hash. Do not filter by model outcome. Pretraining contamination is a limitation.
After smoke estimate time and uncertainty; allow one pretest reduction, never
increase sample size after seeing significance. If reduced study cannot fit,
report feasibility only.

Check generated proofs only in the fixed task and an isolated environment with
no network or unrestricted filesystem. Reject new axioms, sorry and target
self-reference. Check final proof and allowed axiom dependencies. Regex filtering
or Dojo ProofFinished alone is not a trustworthy sandbox or full audit. Keep
valid, invalid, timeout and infrastructure_error distinct. Lean validates the
formal statement, not a natural-language interpretation.

## Monitors and training

Generation order/direct checking; sum/mean raw token log-probability; TF-IDF plus
length and likelihood; normalized final-token all-layer linear probe;
Motion-only; full Three-Reader. Candidate activations plus needed prompt boundary
states only; FP16 shards; no base-model gradients. Any extra extraction costs
count toward inference time. Document reduced variants as reduced.

All readers see the same task/candidate, no verifier responses, references or
future proposals. Bidirectional processing of a complete proposal is permitted.
Seeds 11/22/33, C=.01/.1/1/10, train-only transforms/codebooks; neural maximum 10
epochs, patience 2 on validation log-loss. Log codebook health and freeze
unspecified paper implementation details before training.

## Utility and statistics

Offline diagnostics use identical unfiltered candidates, including tasks with no
valid proposal. Report log-loss, AUROC/AUPRC, calibration, first-valid rank,
false alarms, components, label-shuffle and length/wording controls.

Freeze internal and non-internal champions on validation, then compare both
against direct checking prospectively. Per task/system: 30 seconds, <=8 proposals;
include generation, scoring, transfers, verification. Report preloading separately.
Each check gets min(5 seconds, remaining time). Late successes never count.
Rankers generate pairs and check the higher score first, retaining the second;
direct checks each arriving candidate. Use task/index seeds and rotate system
order. No steering or hard rejection. Audit all generated proposals afterwards
without counting extra verification as budgeted success.

Independent unit is a task. Paired rate differences, 10,000 task-bootstrap draws,
95% intervals. H3 support requires a positive lower bound against BOTH baselines.
Report all comparisons, wide intervals and missing technical data honestly. OOD
is separate, with no recalibration; preselected renaming/paraphrase variants
stay clustered. No inference to deception or other unverifiable domains.

## Deliverables and progression

prepare -> smoke -> collect -> train -> evaluate -> report. Atomic request-bound
receipts bind splits, revisions, prompts/tokens, activations, reader, timing and
verifier status. Resume only compatible complete data. Notebook is the primary UI.

Tests cover BOS, leakage, duplicate splits, alignment, independent nulls, valid/
invalid/untrusted Lean, timeouts, overhead, resume and real model forward. Fake
tests alone are never empirical evidence. Four plots: prediction, verified utility,
cost and transfer. Publish limitations, failed runs, changes and training cost.

Future only: SAE analysis, steering, larger models, stepwise search and separately
labeled open domains. None can rescue this study. No promised fellowship score.
