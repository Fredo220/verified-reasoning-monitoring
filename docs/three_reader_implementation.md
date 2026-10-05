# Three-Reader implementation audit

Status: Kimina source review began 2026-09-16; the separate full-context code
reader follow-up completed open-validation training on 2026-09-29. No Kimina
reader has been trained. This document is not a fidelity certificate or a
frozen architecture selection for a new protected test.

## Sources and scope

Pinned reference: [Three-Reader, v1, Sections 4 and Appendices A/C](https://arxiv.org/html/2608.05660v1).
It scores supplied candidates. Our task instead uses naturally generated Lean
proof attempts, which may contain no successful candidate, and includes repairs.
That changes the candidate distribution and evaluation, not just model size.

[Constitutional Classifiers++, v1](https://arxiv.org/html/2601.04603v1) motivates
contextual internal monitoring and evaluating cost alongside performance.
We do not transfer its safety labels or interpret its jailbreak results as
evidence for our proof-validity hypotheses.

## Existing code versus the paper

| Component | Published design | Existing `src/vrm/monitors.py` |
| --- | --- | --- |
| Motion | Whole token/layer displacement sequence; two-layer, 128-unit bidirectional LSTM | Same broad structure; token-major ordering; no embedding-to-first-block displacement |
| State readers | Six relative depths; unit-normalized states; final 64 answer tokens | Half-up rounding gives Kimina post-block depths 7, 11, 14, 18, 21, 25 (one-based) |
| Direction | Per-depth 8D projection, token MLP, final/mean summaries | Implemented; intermediate/head dimensions are our choices |
| Region | 64D projection; hard 128-entry codebook, EMA, commitment loss | Implemented with explicit local EMA/reseeding defaults |
| Fusion | Concatenate reader embeddings, MLP | Implemented |
| Training | Pairwise objective; seven epochs; validation selection accuracy | Existing code uses pointwise BCE, up to ten epochs and validation log-loss: a substantive deviation |

The local recipe must be called an adaptation, not an exact reproduction.

## Required before Kimina monitor training

The raw collector retains every prompt and generated token at all 28 layers.
The final-64-token state-reader window does not authorize truncating that record
or the Motion sequence. The answer span is the entire assistant continuation;
an extracted Lean-only span is separate metadata, not a silently selected input.

The existing training API eagerly materializes float32 arrays and runs on CPU.
It is not ready for long-trace, free-Colab training. Adapt only the necessary
data-loading/device path after real collection measurements. Measure a batch-one
forward/backward with the base model unloaded. Prefer a smaller recurrent width
or a documented feature projection to token/layer deletion; apply the identical
Motion change to Motion-only and combined readers. Record dimensions, seeds,
memory, runtime and input coverage before freezing the choice.

For repairs, add task-family weighting, original/repair strata and a
round/feedback-only control. Provide exactly the same public generation context
to text and internal comparators. Fit transforms only on training tasks; never
select on protected outcomes. Keep unresolved verifier failures out of binary
labels while reporting coverage. These requirements are not yet implemented by
the existence of the current `ThreeReader` class.

The tiny two-task pilot validates collection and verification only. It cannot
establish generalization, H1, H2 or H3, and it is not a training dataset for a
claim of useful monitoring.

## Separate full-context implementation (2026-09-28)

The completed `trajectory-followup-v1` result remains closed. The new
`vrm.full_three_reader` path is an architectural follow-up, not a re-scoring
of its opened reserve tasks. `vrm.full_three_reader_capture` stores its
receipts under `data/code_monitoring/full-three-reader-v2/`, with a distinct
study name and the v1 source-receipt hash. It captures every prompt and
non-EOS answer position at all 28 post-block layers. The answer span is
retained separately so Region and Direction still see only the final 64
answer tokens, as in Appendix A of the paper. Motion sees the complete
unpooled prompt-plus-answer displacement grid. The original answer-only
traces and checkpoints are not rewritten.

The new Region codebook is initialized from at least 128 distinct training
candidate embeddings, never by repeating a two-candidate minibatch. Its
reseed pool is refreshed from training candidates each epoch. Usage and
perplexity are recorded for train and validation; low usage must be
reported, not hidden by selecting a favorable test seed. Motion-only and
the full reader use the same full-context captures and three fixed seeds.

This is still **not an exact paper replication**. The base model is a 1.5B
instruction-tuned code model, not one of the paper's 8B/14B/30B base models.
Candidates are naturally generated code solutions and can all pass or fail;
the paper's items provide a correct option. The code reader retains the
local task-paired pass/fail objective and single-pair optimizer updates,
whereas Appendix C reports batch-16 training with gradient accumulation.
Seven epochs and selection by validation task-pair rank are an adaptation
of the paper's seven-epoch validation-selection recipe. Head widths and
flattening details not fully specified in the paper are local choices.
No claimed gain from the paper transfers automatically to this setting.

Readiness checks before a new protected test:

1. Complete all 896 opened full-context captures with matching source,
   runtime, study and file hashes. Resume never overwrites a completed trace.
2. Fit all six reader checkpoints on opened training/validation tasks only;
   publish validation rank and train/validation codebook usage for each seed.
   Measure peak memory and wall time on the actual device. A collapsed
   codebook or an infeasible full-token LSTM is a feasibility finding, not a
   negative scientific result.
3. Freeze a **new, unused** target population, evaluation metric and
   strongest text/likelihood comparator before its labels are opened. The
   76 v1 reserve tasks are no longer an independent target. Compare methods
   on the same candidates and at task-level uncertainty, with no test-time
   choice of pooling, seed or codebook threshold.

Local commands, from the repository root:

```bash
.venv/bin/python -m vrm.full_three_reader_capture capture-opened --max-new 1
.venv/bin/python -m vrm.full_three_reader_capture capture-opened
.venv/bin/python -m vrm.full_three_reader_capture train-opened --max-new 1
.venv/bin/python -m vrm.full_three_reader_stage build
.venv/bin/python -m vrm.full_three_reader_stage extract --archive stage.zip --folder stage
.venv/bin/python -m vrm.full_three_reader_stage train --folder stage --models models --device cuda
```

The first command is a resumable smoke. The second processes only opened
sources and can be interrupted between receipts. Training requires the full
opened inventory. No command here samples or scores a new protected test.

All **896/896** opened full-context traces were captured and verified again
from their saved receipts (`restored=896`, `remaining=0`). The 800 training and
96 validation rows load with their original task splits. The first replay had
86 prompt and 28 answer tokens; its answer-state tensor matched the old
answer-only capture exactly (maximum absolute delta 0). This checks
extraction alignment, not correctness prediction. The traces occupy about
15 GiB on disk (15,963,280 KiB, about 16.35 GB decimal). This exceeds a
fresh 15-GB free Google Drive allocation before accounting for the notebook,
checkpoints, or other files. The present local trace format therefore cannot
simply be copied to a free Drive account for Colab training. Lossless staging
or another verified transport path is still required; truncating or pooling
Motion tokens would change the tested architecture.

Before training, the new codebook uses 126/128 codes on the 800 training
candidates (perplexity 100.76) and 27 on the 96 validation candidates
(perplexity 19.46). These numbers are **initialization diagnostics**, not
trained-reader results. Reading only the last answer state at six depths
reduced training-bank preparation from 62 seconds to 1.8 seconds on the
local MPS device, without changing Motion's input. A real unpooled pair
forward/backward with 241- and 316-token candidates took 35.7 seconds on
the 8-GB Mac; a CPU attempt exceeded 90 seconds and was interrupted. There
are 80 mixed-label training task pairs per epoch, so six seven-epoch fits
would require 3,360 pair updates, plus validation. Multiplying one pair's
timing by that count is not a reliable runtime forecast because sequence
lengths vary; it does show why a short local smoke cannot stand in for
completed training.

The training path saves an atomic progress checkpoint every ten pairs and
at epoch boundaries. A test interrupted it after the third pair and verified
that resuming from the second pair produced the same final state as an
uninterrupted CPU run. A separate test verifies recovery if finalization is
interrupted after the weights are written but before metadata is committed.
The lossless stage includes all 320 training candidates used by the fixed
pair schedules across three seeds and seven epochs, all 96 validation
candidates, and final answer states at six Region depths for all 800 training
candidates. No selected candidate loses Motion tokens or layers. The resulting
archive is 8,576,469,951 bytes with SHA-256
`85284371ded3547c3b6bb71e9c5719dff2b994560bab126954050dabc428b073`.
The source archive and each transferred part remain separate from the
original captures; extraction verifies every staged trace against its source
hash. This storage reduction is exact, not activation quantization.

On 2026-09-29, a free Colab T4 executed a real CUDA forward/backward with the
full Motion-only and Three-Reader architectures at 100 tokens, 28 layers, and
1,536 dimensions. The measured times were 1.31 and 0.79 seconds respectively,
with 0.369 GiB peak allocated PyTorch GPU memory. These are synthetic-tensor
resource checks, not trained-reader performance and not an estimate for all
candidate lengths. The local suite passed with 521 tests and 7 skips.

The lossless stage was transferred and verified on a free Colab T4. The free
GPU session disconnected during `motion_seed33`; its epoch-3, pair-80/80
progress file was downloaded and verified locally (SHA-256
`cd9cce315542b0b251c40d4ac29ab0a32015fc80604ef3a5504a0e1f9fb6bf34`).
The resumed run and the remaining full-reader fit then completed on Frederic's
free T4. All six selected checkpoints were downloaded, SHA-256 checked against
their metadata, and reloaded locally. The selected results on **open
validation**, not on an independent test, are:

| Reader | Seed | Selected epoch | Task-pair rank | Validation codes used / 128 |
| --- | ---: | ---: | ---: | ---: |
| Motion-only | 11 | 2 | 0.8148 | n/a |
| Motion-only | 22 | 5 | 0.8519 | n/a |
| Motion-only | 33 | 5 | 0.7778 | n/a |
| Full Three-Reader | 11 | 1 | 0.7500 | 2 |
| Full Three-Reader | 22 | 1 | 0.7407 | 2 |
| Full Three-Reader | 33 | 3 | 0.7407 | 15 |

The full reader ranked below Motion-only for every seed. Its selected Region
codebook used only two validation codes for seeds 11 and 22 and 15 for seed
33. Later epochs used more codes but did not improve the registered checkpoint
selection metric. This is a feasibility and model-selection warning, not proof
that internal dynamics lack useful information. The final Colab session reported
1.772 GiB peak PyTorch GPU allocation; that is not total runtime memory.
The seed-33 selected weight hashes are
`d63403d9f10ea7c4ec8472e57d0d64e27369a2a624393449612c75c2cb76febc`
(Motion-only) and
`f3aa5ffd064f3eb2b39b8fe26d902c639a05f8a6b8fc0b86b7812118da680904`
(full reader). The local `models/` folders retain the machine-readable epoch
histories and checkpoint identities.

No new protected population, metric, or strongest non-internal comparator was
frozen before these validation results. The opened v1 reserve tasks cannot be
reused as a confirmatory target. Therefore no independent v2 test was run and
no superiority, practical-utility, or generalization claim is supported.
