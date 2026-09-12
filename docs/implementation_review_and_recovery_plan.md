# Verified Reasoning Monitoring: implementation audit and execution plan

> **For agentic workers:** Read `docs/research_plan.md` first. It is the
> scientific authority. Use this document to continue the existing
> implementation without changing the research question, gates, protected
> splits, or model. Prefer test-driven, minimal repairs. Do not restart the
> repository.

**Reviewed:** 2026-09-09

**Repository:** `/Users/friedrichreichelt/Documents/verified-reasoning-monitoring`

**Goal:** Determine whether internal activation monitors help select more
Lean-verifiable proof candidates than likelihood, text-based selection, and
direct checking under the same end-to-end time budget.

**Governing specification:** [`docs/research_plan.md`](research_plan.md)

**Review scope:** Current source, tests, configuration, notebook, prepared data,
and the relevant methods in Constitutional Classifiers++ and Three-Reader. This
is a code-and-protocol audit. It is not an empirical result, a security
certification, or evidence for H1-H3.

---

## 1. Executive conclusion

The repository should be continued, not rebuilt. Its local software foundation
is now substantial: data preparation, the single chat-template boundary,
activation capture, hashed candidate artifacts, interruption recovery, a minimal
CLI, monitor fitting APIs, and core budget/statistics helpers are implemented and
covered by tests.

The study is nevertheless **not yet empirically underway**. No real
Gemma-to-Comparator development smoke has completed, the seven real verifier
tests remain skipped, and no H1, H2, or H3 outcome exists. The next scientific
deliverable is therefore still the registered 32-task by four-candidate
development smoke. More monitor engineering must not delay that test.

Current evidence supports this precise status:

> The local pipeline is largely unit-tested and a full prepared task population
> exists. Real Linux verifier acceptance, fresh-runtime Colab reproducibility,
> real Gemma activation receipts, and all hypothesis tests remain open.

The largest pre-evaluation risk after the smoke is Three-Reader fidelity. The
current architecture resembles the paper, but its training objective and recipe
do not yet match the published selection method closely enough to call it a
faithful full Three-Reader implementation without an explicit adaptation record.

## 2. Non-negotiable scientific target

Every agent must preserve these three separate questions:

| Hypothesis | Required comparison | Maximum permitted claim |
| --- | --- | --- |
| H1 | Internal monitors versus likelihood and text baselines | Internal activations add predictive information about candidate validity on this task/model distribution |
| H2 | Full Three-Reader versus static all-layer and Motion-only readers | Region and Direction add useful information beyond static state and cross-layer motion under the registered adaptation |
| H3, primary | Frozen internal champion versus frozen non-internal champion and direct checking | Internal ranking increases fully verified solutions under the same measured time budget |

H1 and H2 do not imply H3. H3 does not imply that Gemma learned to reason better;
the base model is frozen and the system only reorders generated candidates. The
monitor observes a completed proposal, so this study is retrospective candidate
selection, not mid-generation error detection.

Never broaden the claim to intuition, metacognition, hidden truth, general
hallucination detection, jailbreak prevention, deception detection, autonomous
learning, or improved base-model reasoning. Those are possible later research
directions, not outcomes of this study.

## 3. Authority order and anti-drift rules

Read project documents in this order:

1. [`docs/research_plan.md`](research_plan.md): hypotheses, protocol, gates,
   budget, statistics, and interpretation.
2. [`configs/study.json`](../configs/study.json): executable frozen identities
   and numerical settings.
3. This document: current implementation status and ordered repairs.
4. [`docs/data_contract.md`](data_contract.md): public/private task boundary.
5. [`docs/lean_backend.md`](lean_backend.md): verifier threat model and runtime.
6. [`docs/model_allocation_plan.md`](model_allocation_plan.md): model-cost policy,
   not scientific authority.

Rules for every subsequent change:

- Preserve `google/gemma-2-2b-it` and its pinned revision.
- Preserve FP16, batch size one, 512 prompt tokens, 64 proposal tokens,
  temperature 0.7, and top-p 0.95.
- Preserve the 32x4 development gate: at least 20 valid candidates, 20 invalid
  candidates, and eight tasks with both outcomes.
- Preserve the approved full and reduced split sizes. Only the one registered
  pretest reduction may be used, after measured smoke timing and before protected
  outcomes are opened.
- Keep reference proofs, verifier metadata, Lean output, and future attempts out
  of model and monitor inputs.
- Keep task groups disjoint across splits. Candidates and tokens are not
  independent statistical units.
- Do not change a threshold, model, corpus, timeout policy, or objective to make
  a gate pass.
- Treat unavailable Colab, missing binaries, authentication, and browser failure
  as operational blockers, not scientific failure.
- Fix implementation defects in place. Do not create a new repository, corpus
  version, or framework unless the approved protocol genuinely requires it.
- Do not commit, push, purchase compute, or open protected results without the
  user's explicit authorization and the preceding gate.

## 4. Evidence inspected on 2026-09-09

### 4.1 Fresh local test result

Command:

```bash
/tmp/vrm-venv/bin/python -m pytest -q -ra
```

Observed result:

```text
154 passed, 7 skipped, 1 warning in 4.62s
```

The seven skipped tests are the opt-in real Linux Comparator/Landrun checks in
`tests/test_lean.py`. The warning is a sandbox permission failure while pytest
tries to create `.pytest_cache`; it is not a test failure, but a fresh Colab
environment must not rely on this temporary local venv.

### 4.2 Real prepared-data evidence

A real preparation run with the pinned Gemma tokenizer produced a full population
under `/tmp/vrm-prepared-v2`:

```text
dev=32, train=384, val=64, id_test=80, ood_test=40
status=ready
archive provenance=verified_md5
source checkout=verified_clean_git
```

The manifest records Benchmark 4 v3, DOI `10.5281/zenodo.18815372`, Mathlib
commit `1bc7728a050fc18ca2683f614c531cd7050ff063`, and tokenizer snapshot
`299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8`. The prepared path is temporary and
is not yet a portable or published experiment artifact.

The prompt contract was also exercised with the real tokenizer: the public task
contains raw user content, the runtime applies the chat template once, and the
result contains exactly one initial BOS token. This is integration evidence for
the tokenizer boundary, not a real Gemma forward pass.

### 4.3 Git and publication state

The branch is `codex/initial-study`, has no commits, and all project files are
untracked. There is no reproducible code commit or established remote publication.
This does not invalidate local work, but protected collection must be tied to an
immutable code identity.

### 4.4 Empirical evidence that does not yet exist

The following have not been established:

- a successful real Linux Lean/Comparator/Landrun preflight;
- one accepted known-valid proof through the actual pinned verifier;
- one real Gemma candidate and activation receipt for this study;
- a completed 128-candidate development smoke;
- measured Colab peak memory, disk, setup time, warm verification time, or resume;
- monitor training on actual study activations;
- frozen validation champions;
- ID or novel-premises H1/H2 results;
- prospective equal-budget H3 results;
- the four required result figures or final report.

No README or agent summary may imply otherwise.

## 5. Requirement-by-requirement implementation assessment

Status meanings:

- **Accepted locally:** implementation and relevant local tests pass.
- **Provisional:** code exists, but a real runtime or scientific acceptance test
  is missing.
- **Missing:** required end-to-end capability does not exist yet.
- **Deferred by protocol:** intentionally occurs only after an earlier gate.

| Protocol requirement | Status | Current evidence | Remaining acceptance evidence |
| --- | --- | --- | --- |
| Separate project and narrow H1-H3 scope | Accepted locally | Research plan and package are isolated from Familiarity x Answerability | Keep all later claims within the protocol |
| Frozen Gemma/tokenizer identity | Accepted locally | Config and `HFRunner` reject mutable revisions | Record real runtime identity in a receipt |
| Chat template exactly once | Accepted locally | Raw public prompt plus one runtime template; unit and real-tokenizer checks | Confirm in first real candidate receipt |
| Official task source and deterministic splits | Accepted locally | Full prepared population and manifest exist | Persist hashes outside `/tmp`; Audit A checks group provenance |
| Reference-proof/model boundary | Accepted locally | Public/private schemas and workflow checks | Spy/integration evidence in final audit packet |
| Activation extraction | Provisional | Hooks capture candidate-token post-block states and prompt boundary in FP16 | Real Gemma tensor shape, token alignment, memory, and timing |
| Atomic candidate receipts and resume | Accepted locally | Corruption, interruption, identity mismatch, and infrastructure retry tests pass | Interrupt/resume once on actual Colab storage |
| Safe Lean validity label | Provisional | Comparator/Landrun adapter and fail-closed tests exist | Seven real security tests pass in intended Linux runtime |
| Minimal CLI | Accepted for smoke | `prepare`, `preflight`, and `smoke` exist and are tested | Fresh-runtime invocation succeeds |
| Package-backed Colab notebook | Provisional | Thin 10-cell notebook calls the CLI | It must provision all pinned prerequisites from a fresh runtime |
| Feasibility smoke | Missing | No 128 real candidates | Complete receipts and mechanical gate result |
| Likelihood/text/static baselines | Accepted as local APIs | Fit, validation selection, save/load, and split tests pass | Train on real study records and freeze artifacts |
| Motion-only reader | Provisional | Architecture and training path exist | Paper mapping, real training, code/data-order checks |
| Full Three-Reader | Provisional, fidelity gap | Motion/Region/Direction structures exist | Resolve the deviations in Section 7 before H2 |
| Champion selection | Provisional | Small helper selects by validation loss | End-to-end artifact, seed aggregation, calibration, and tie rules |
| Offline H1/H2 metrics and controls | Missing | No evaluation/report module | Task-clustered diagnostics, nulls, calibration, transfer |
| Prospective H3 engine | Provisional | `run_task` enforces an outer wall clock in unit tests | Complete controller, serialization, system-order rotation, real timing |
| Exact Colab dependency profile | Missing | Broad package requirements only | Lock file/profile tested in a fresh runtime |
| Audit A | Deferred by protocol | Cannot occur before smoke/fidelity work | Explicit pass before protected collection |
| Audit B and public report | Deferred by protocol | No outcomes exist | Claims-to-artifacts audit after sealed results |

## 6. Accepted work that must not be discarded

The following repairs from the earlier review are complete at the local-test
level and should be preserved:

1. **Single-template prompt path.** `data.py` counts the rendered token sequence
   while publishing raw user content; `runtime.py` applies the template once.
2. **Production-shaped verifier boundary.** Workflow validates nested private
   wrappers, content hashes, split/task identity, and trusted verifier pins.
3. **Preflight-backed verifier identity.** The verifier cannot advertise a trusted
   identity before successful preflight.
4. **Resumable smoke artifacts.** Completed candidates are immutable;
   infrastructure attempts are retained and retried without deleting prior cost.
5. **Minimal smoke CLI.** Preflight occurs before model loading, avoiding wasted
   GPU allocation when Lean infrastructure is unavailable.
6. **Thin notebook.** Experiment logic remains in tested package code rather than
   being duplicated in cells.
7. **Monitor fitting and persistence APIs.** Linear and neural monitor bundles,
   registered seeds, early stopping, and strict train/validation split names now
   pass their local tests.

Do not reopen these areas unless a real integration test exposes a specific bug.

## 7. Current findings and required minimal repairs

### F1. Critical: the real trusted verifier path is still unproven

**Evidence:** Seven opt-in tests are skipped. No observation proves that the
pinned Benchmark 4 v3 cache, Lean 4.29 RC2, Comparator, `lean4export`, Landrun,
and non-root sandbox operate together in free Colab. The implementation may be
correct in isolation and still fail because of kernel, toolchain, filesystem, or
runtime incompatibility.

**Minimal repair:** Use one Linux environment and one transport first. Provision
the exact native toolchain, run `vrm preflight`, then run the six registered proof
cases plus cache-mutation rejection. Do not perfect both Docker and native paths.

**Acceptance:** `154 passed` remains green and all seven real tests pass with
saved JSON output, hashes, versions, elapsed times, and the actual host/runtime
identity. Known-valid returns `valid`; invalid, self-reference, `sorry`, and
unauthorized axiom do not. Sandbox escape and cache mutation fail closed.

### F2. Critical operational gap: the notebook is not fresh-runtime complete

**Evidence:** The notebook assumes that the repository, prepared source/cache,
Comparator build, Landrun binary, and their SHA-256 values already exist. It asks
for manual hash insertion and installs broad dependencies. A new collaborator
cannot run it from a blank Colab runtime without undocumented steps.

**Minimal repair:** Add one setup section that clones or uploads a specific code
revision, installs an exact tested dependency profile, obtains only official
source artifacts, verifies every checksum, builds/pins Comparator and Landrun,
and stores non-secret runtime metadata. Keep `HF_TOKEN` exclusively in Colab
Secrets and never print it. The notebook must still call package functions/CLI.

**Acceptance:** Restart a fresh runtime, execute setup and preflight in order,
and reach a clear `ready` result without editing Python source in cells. If free
Colab cannot provide the required isolation, save the exact blocker and evaluate
one approved equivalent Linux runtime; do not weaken the verifier.

### F3. Critical next experiment: the 32x4 smoke has not run

**Evidence:** A full source population exists, but there are no real Gemma
candidate receipts. Unit-test candidates are synthetic and cannot establish
proof yield, activation viability, runtime cost, or the mixture needed to train
monitors.

**Minimal repair:** Once F1-F2 pass, run exactly 32 development tasks with four
natural sampled candidates each. Use the registered candidate seeds and existing
resume directory. Do not train a monitor first.

**Acceptance:** There are 128 immutable completed candidate receipts and matching
activation files, no infrastructure errors, and a generated summary reports the
registered counts. Proceed only if valid >=20, invalid >=20, and mixed tasks >=8.
Otherwise publish a bounded feasibility result; H1-H3 remain untested.

### F4. High before H2: current Three-Reader training is not paper-faithful

The architecture captures important components from the paper:

- raw adjacent-layer displacements;
- a two-layer bidirectional LSTM with 128 hidden units;
- six normalized location depths with shared per-depth projection;
- an 8-dimensional Direction projection;
- a 64-dimensional Region projection;
- a 128-entry EMA codebook with straight-through gradients;
- final-token plus mean answer summaries for Direction;
- concatenation of Motion, Direction, and Region embeddings.

However, the following deviations are material:

1. The paper trains candidates jointly with a **pairwise selection objective**;
   current code uses pointwise binary cross-entropy.
2. The paper uses Adam with learning rate `1e-3`, cosine schedule, batch size 16,
   gradient accumulation 4, seven epochs, and best validation selection accuracy.
   Current defaults are batch size 8, accumulation 1, no cosine schedule, up to
   ten epochs, and best validation log-loss.
3. The paper says each seed controls weight initialization and shuffled data
   order. Current training sets the torch seed but iterates fixed row slices.
4. The exact six-layer relative mapping from the paper's 32/48-layer models to
   Gemma-2-2B has not been documented or acceptance-tested.
5. The paper reports codebook usage/perplexity because a collapsed Region reader
   is not meaningful. Current metadata does not publish this health evidence.
6. The paper's primary task contains one correct candidate and one or more
   incorrect candidates. Natural Lean proposals may contain zero, one, or
   multiple valid candidates. The objective adaptation has not been frozen.

**Minimal repair:** Before any protected monitor training, create
`docs/three_reader_implementation.md` with a row for each paper component,
current implementation, deliberate Gemma/Lean adaptation, and test. Decide one
of two scientifically honest paths:

- implement task-grouped pairwise ranking wherever valid/invalid pairs exist,
  with a preregistered policy for all-invalid/all-valid tasks; or
- retain pointwise validity training and rename the method
  `Three-Reader-inspired pointwise monitor`, weakening H2 accordingly through a
  pre-outcome amendment.

Do not call the current pointwise model a faithful replication. The first path
best preserves the approved H2.

**Acceptance:** The mapping cites the original methods and appendices; data-order
shuffle is seed-controlled; the frozen optimizer/schedule/selection recipe is
recorded; codebook occupancy/perplexity is emitted; pair construction never
crosses task groups; tests cover all-valid/all-invalid tasks and save/load.

Primary method references:

- [Three-Reader Sections 4-5 and Appendix C](https://arxiv.org/html/2608.05660v1)
- [Constitutional Classifiers++ Section 5](https://arxiv.org/html/2601.04603v1)

### F5. High before training: group separation is not enforced at fit time

**Evidence:** `_validate_splits` now correctly requires explicit `train` and
`val` values and rejects task-ID overlap. It does not require or compare
`group_id`, so normalized theorem variants with different task IDs could cross
the fitting boundary if records are assembled incorrectly downstream.

**Minimal repair:** Require `group_id` in monitor records, validate that each
group appears in exactly one split, and bind the source split/group manifest hash
to every training request. Do not rely only on preparation having done the right
thing; the training boundary must fail closed when passed malformed data.

**Acceptance:** Tests reject missing group IDs, group overlap with distinct task
IDs, protected test rows, and data whose manifest identity differs from the
training request.

### F6. High before training: verifier statuses are not yet a complete label policy

**Evidence:** Monitor fitting expects binary `label` values. No end-to-end
assembler currently specifies how `valid`, `invalid`, `timeout`, and
`infrastructure_error` receipts become training/evaluation records. A timeout is
not evidence of invalidity, and infrastructure failure is not a candidate label.

**Minimal repair:** Freeze and implement the status policy before collection.
Recommended interpretation consistent with the protocol:

- `valid` -> positive label;
- `invalid` after successful Comparator audit -> negative label;
- `timeout` -> unknown for H1/H2 and retained as unsolved/cost in H3;
- `infrastructure_error` -> non-evaluable run event, never a label.

Publish counts for every status. Do not silently discard entire difficult tasks
from H3. If H1/H2 omit unknown-label candidates, cluster-level sample sizes and
task coverage must be reported.

**Acceptance:** One tested assembler creates monitor records and a missingness
report from immutable receipts; no unknown status is coerced to zero.

### F7. High: collect/train/evaluate/report orchestration is absent

**Evidence:** The CLI exposes only `prepare`, `preflight`, and `smoke`. Core
classes and helpers exist, but no command assembles full train/validation
receipts, trains and freezes champions, opens protected splits once, computes
H1/H2, executes H3, or generates the report and four figures.

**Minimal repair after the smoke:** Add commands in protocol order, each backed
by a small package function and immutable request identity:

```text
vrm collect --split train|val
vrm train
vrm freeze-selection
vrm evaluate-offline --split id_test|ood_test
vrm evaluate-utility --split id_test|ood_test
vrm report
```

Do not build a generic workflow framework. Each command should consume the prior
stage's manifest, verify hashes, write atomically, and stop on mismatched state.

**Acceptance:** An end-to-end fixture test runs the stage sequence without
protected leakage; reruns are deterministic or resume only missing work; test
artifacts cannot be loaded by training/selection code before the selection seal.

### F8. High before H1/H2: metric and champion rules remain underspecified

Resolve these decisions once, before protected outcomes:

1. Candidate-level AUROC/AUPRC/log-loss must be accompanied by task-clustered
   uncertainty; candidate counts cannot be presented as independent sample size.
2. Raw `sum_logp` and `mean_logp` are ranking scores, not probabilities. Use them
   raw for ranking and fit any probability calibration on train only.
3. Specify whether the three neural seeds are averaged, one fixed seed is used,
   or validation selects a seed. Charge ensemble scoring if used. Publish all
   seeds regardless.
4. Freeze the internal/non-internal champion metric and tie breaker. The current
   helper uses validation loss and lexical name tie-breaking; the protocol and
   artifact must state this exactly.
5. Define H1 and H2 support thresholds or present effect estimates and intervals
   without a binary support claim. Do not infer support from AUROC alone.
6. Report selection accuracy/first-valid rank per task, because the Three-Reader
   paper is a candidate-selection method rather than an absolute correctness
   judge.
7. Keep ID and novel-premises transfer separate and never recalibrate on OOD.

**Acceptance:** A sealed analysis specification defines estimands, clustering,
missingness, seed aggregation, calibration, champion selection, and all planned
plots before test access.

### F9. High before H3: prospective engine is not end-to-end safe yet

**Evidence:** `engine.run_task` has a useful monotonic deadline, deterministic
candidate seeds, pair ranking, direct checking, and late-success exclusion.
However, it is not wired to the CLI/artifact layer. It removes `activations` from
public candidate JSON but leaves `prompt_boundary`, which is a NumPy array and
can break serialization or leak large tensors into metadata. System-order
rotation, cumulative allocated GPU accounting, champion identity, and post-hoc
audit separation are not implemented end to end.

**Minimal repair:** Remove both activation arrays from JSON, persist them through
the established activation store, bind monitor and verifier identities to each
run, rotate system order deterministically by task, and keep three ledgers:

- allocated session/GPU time;
- measured end-to-end task time;
- per-event generation, scoring, transfer, and verification time.

Direct checking and both rankers must receive identical task/index seeds. No
hard monitor rejection is allowed. Post-hoc verification must be written to a
separate namespace and never change prospective success.

**Acceptance:** Tests cover boundary equality, overrun, serialization, same
candidate streams, rotation, infrastructure failure, and immutable late audit.
Then run a real development timing trial before protected H3.

### F10. Medium: dependency and runtime provenance is not reproducible yet

**Evidence:** `pyproject.toml` uses broad lower-unbounded dependency names. The
paper reports PyTorch 2.7, Transformers 4.52, and HDF5 storage; this project may
adapt those choices, but the actual tested Colab versions must be recorded.

**Minimal repair:** Keep broad library constraints for developers if desired,
but add an exact Colab requirements/lock profile generated from the successful
fresh runtime. Record Python, CUDA, GPU, torch, transformers, accelerate,
scikit-learn, Lean, Comparator, Landrun, source, model, and tokenizer identities
inside the run manifest.

**Acceptance:** A fresh runtime can install from the exact profile and reproduce
the preflight plus one candidate receipt. Never infer an unreported version as
zero or default.

### F11. Medium: monitor bundles are not atomically published

**Evidence:** `_write_bundle` creates the final directory first and writes files
into it. Interruption can leave a partial directory that blocks a clean retry.
This is less urgent than the smoke because monitor training is gated after it.

**Minimal repair:** Write each bundle to a sibling temporary directory, fsync
metadata/model, then rename without clobber. Bind training request, data manifest,
configuration, and code identity to metadata.

**Acceptance:** An injected interruption leaves no accepted partial bundle;
resume creates byte-consistent predictions and refuses incompatible data.

### F12. Medium: project documentation contradicts current code and pins

**Evidence:** `docs/status.md` still describes missing modules and ten tests.
`docs/lean_backend.md` describes the old Benchmark 4 v10/Lean 4.10 state and says
Comparator validity is unimplemented, while `configs/study.json` and `lean.py`
now target Benchmark 4 v3/Lean 4.29 RC2 and contain Comparator code.

**Minimal repair:** Update both documents from accepted evidence only. Preserve a
short historical note rather than deleting the prior engineering history. State
that Comparator is implemented locally but operationally unverified.

**Acceptance:** Config, data contract, backend document, notebook, and status use
the same DOI, repository commit, toolchain, test count, and empirical-status
language.

### F13. Medium but mandatory before collection: no immutable code identity

**Evidence:** The repository has no commits and all files are untracked. Artifact
hashes cannot yet identify a reviewable source revision.

**Minimal repair:** After the smoke-critical implementation is locally verified,
review secrets and generated data, create an initial local commit, and record its
commit hash in every run request. Publishing remains separately authorized.

**Acceptance:** Clean or explicitly documented working tree, no token or private
artifact in Git, and a source commit embedded in preflight/smoke manifests.

## 8. Ordered execution plan

The order below is mandatory because it minimizes wasted Colab time and prevents
paper-fidelity work from delaying the real feasibility bottleneck.

### Stage A: reconcile documents and make Colab setup executable

**Files:** `docs/status.md`, `docs/lean_backend.md`, exact Colab requirements,
`notebooks/verified_reasoning_monitoring.ipynb`, narrow setup helpers if needed.

- [ ] Update stale Benchmark/toolchain/status text without changing the protocol.
- [ ] Add reproducible official-source/cache/tool provisioning with checksums.
- [ ] Make repository/code revision an explicit notebook input.
- [ ] Keep all secrets in Colab Secrets and add a test that notebook source does
      not contain token-shaped values.
- [ ] Validate notebook JSON and Python syntax locally.

**Gate A:** A blank Linux runtime can reach verifier preflight without loading
Gemma. Failure produces one concrete operational diagnostic and preserves logs.

### Stage B: establish the trusted verifier

**Files:** `src/vrm/lean.py`, `tests/test_lean.py`, `docs/lean_backend.md` only if a
real failure identifies a specific defect.

- [ ] Run `vrm preflight` with exact cache/tool hashes.
- [ ] Run known-valid, invalid, self-reference, `sorry`, unauthorized-axiom,
      sandbox-escape, and disposable-cache-mutation cases.
- [ ] Save structured outputs and elapsed times.
- [ ] Fix only reproduced failures; rerun targeted test, then full suite.

**Gate B:** All seven real opt-in tests pass. Instantiation or mocked tests do not
substitute for this gate.

### Stage C: run the real 32x4 development smoke

**Files:** existing CLI/notebook/workflow; change only on reproduced defects.

- [ ] Load pinned Gemma only after Gate B.
- [ ] Use the existing prepared development population and verify its manifest.
- [ ] Generate four proposals per task using registered seeds.
- [ ] Capture candidate activations and prompt boundary; verify exact token spans.
- [ ] Interrupt once after several accepted receipts and resume in place.
- [ ] Record peak memory, disk, generation, extraction, verification, and total
      elapsed time.
- [ ] Evaluate only the mechanical feasibility gate.

**Gate C:** `completed_candidates=128`, no infrastructure errors, and registered
valid/invalid/mixed thresholds pass. If not, stop the large study and publish the
bounded feasibility result. Do not change the corpus or gate.

### Stage D: freeze post-smoke design decisions

**Files:** new `docs/three_reader_implementation.md`, new sealed analysis
specification, `configs/study.json` only through an explicit pre-outcome amendment.

- [ ] Choose full or reduced sample size from measured time and precomputed
      precision, once.
- [ ] Resolve the pairwise objective for zero/multiple-valid Lean candidate sets.
- [ ] Freeze layer mapping, optimizer, schedule, epochs, batch/accumulation,
      checkpoint metric, seed aggregation, status policy, calibration, and
      champion tie-breaker.
- [ ] Define task-clustered H1/H2 uncertainty and H3's two-comparison joint rule.

**Gate D:** Every unspecified decision has one written value and rationale before
protected collection. No test outcome has been opened.

### Stage E: finish only the required monitor and artifact gaps

**Files:** `src/vrm/monitors.py`, record assembler, CLI stages, focused tests.

- [ ] Enforce `group_id` at fitting boundaries.
- [ ] Implement status-to-label/missingness assembly.
- [ ] Implement the frozen Three-Reader training recipe and data-order shuffle.
- [ ] Emit codebook usage/perplexity and all seed histories.
- [ ] Publish monitor bundles atomically with full provenance.
- [ ] Add genuinely independent label-shuffle and surface/length controls.

**Gate E:** Real development records can train, save, reload, and reproduce every
monitor score; paper correspondence and adaptations are reviewable.

### Stage F: Audit A before protected collection

Provide the reviewer only:

- frozen protocol and amendments;
- code commit and exact environment profile;
- prepared-data manifest and split/group audit;
- real verifier security receipts;
- development smoke result and cost projection;
- Three-Reader implementation table and tests;
- information-boundary and label/missingness tests;
- frozen analysis and champion-selection specification.

Audit A returns `pass`, `repair_before_collection`, or `not_evaluable`. Repairs
must address concrete findings and cannot change hypotheses to improve outcomes.

### Stage G: collect, train, and freeze champions

- [ ] Collect train and validation candidates with immutable resumable shards.
- [ ] Train all registered baselines and internal readers on the same records.
- [ ] Publish all seeds, failures, codebook health, and validation diagnostics.
- [ ] Select and seal exactly one internal and one non-internal policy according
      to the frozen rule.
- [ ] Store a selection manifest that cannot be changed after test opening.

**Gate G:** Protected test access is authorized only after the selection seal.

### Stage H: evaluate H1 and H2 once

- [ ] Score identical unfiltered ID and OOD candidate populations.
- [ ] Report log-loss, AUROC, AUPRC, calibration, selection accuracy, first-valid
      rank, false alarms, missing labels, and task-clustered intervals.
- [ ] Run component, label-shuffle, length/wording, paraphrase, and identifier
      controls without counting variants as independent tasks.
- [ ] Keep ID and novel-premises findings separate.

**Gate H:** H1 and H2 receive separate supported/unsupported/unclear statements
under the sealed interpretation rules. They do not authorize H3 claims.

### Stage I: evaluate H3 prospectively

- [ ] Run frozen internal ranker, frozen non-internal ranker, and direct checking
      on the same tasks and task/index sampling seeds.
- [ ] Rotate system order and include generation, scoring, transfers, and Lean
      checks in each 30-second task budget.
- [ ] Never count late success.
- [ ] Audit all generated candidates later in a separate namespace.
- [ ] Compute paired task-level differences with 10,000 bootstrap draws.

**Gate I:** H3 is supported only if the lower 95% interval is positive against
both baselines. Otherwise report negative or unclear without adding steering.

### Stage J: Audit B and reporting

- [ ] Generate four figures directly from audited artifacts: predictive quality,
      verified solutions under budget, end-to-end cost, and transfer.
- [ ] Link every headline number to a machine-readable artifact.
- [ ] Distinguish development, validation, ID test, OOD test, and post-hoc audit.
- [ ] Report one-time training cost, timeouts, infrastructure failures, negative
      controls, and all deviations.
- [ ] Run full local and real-runtime verification before claiming completion.

Audit B returns `claims_supported`, `revise_claims`, or `not_evaluable`.
Publication and remote push remain explicit user decisions.

## 9. Minimal file plan for remaining work

Avoid inventing a broad framework. The smallest coherent additions are:

| File | Single responsibility |
| --- | --- |
| `requirements-colab.txt` or an equivalent lock file | Exact successful Colab Python environment |
| `docs/three_reader_implementation.md` | Paper-to-code mapping and frozen adaptations |
| `docs/analysis_spec.md` | H1/H2/H3 estimands, missingness, seeds, selection, and claim rules |
| `src/vrm/records.py` | Convert verified immutable receipts to monitor records without leakage |
| `src/vrm/evaluation.py` | Offline metrics, task clustering, controls, and frozen champion artifact |
| `src/vrm/report.py` | Figures and report from sealed artifacts only |
| existing `src/vrm/cli.py` | Thin commands delegating to those package functions |

Do not split files further until one becomes difficult to understand or test.
Do not add SAE, steering, RL, agent trajectories, databases, web services, or a
general experiment scheduler.

## 10. Test strategy

For each defect or missing behavior:

1. Write one failing test that reproduces the risk.
2. Run only that test and confirm the expected failure.
3. Implement the smallest change.
4. Run the targeted test.
5. Run the related module tests.
6. Run the full suite.
7. For runtime claims, run the real opt-in test; mocks are insufficient.

Required new test groups:

### Fresh-runtime and notebook

- notebook contains no embedded credential;
- notebook source parses and delegates to CLI;
- missing prerequisite fails before Gemma loading;
- checksums and code revision mismatches stop execution.

### Monitor data boundary

- missing/overlapping `group_id` rejected;
- test split rejected from fitting/selection;
- timeout/infrastructure status never becomes a binary label;
- model records contain no reference proof or verifier response;
- label-shuffle control changes labels independently within the intended unit.

### Three-Reader fidelity

- exact Gemma layer sites frozen;
- task-grouped pairs never cross tasks;
- data order changes deterministically by seed;
- cosine schedule and checkpoint rule match the frozen adaptation;
- codebook usage/perplexity is finite and persisted;
- collapsed codebook triggers warning/fail rule defined before test;
- Motion-only and full reader use identical candidate records.

### Prospective utility

- both activation arrays excluded from JSON;
- rankers and direct checking receive the same task/index candidates;
- scoring and transfer time count against the budget;
- success at/after the exact deadline follows one tested convention;
- late post-hoc verification cannot mutate prospective outcome;
- task/system order rotation is deterministic;
- infrastructure failure leaves the task non-evaluable and preserves cost;
- task-level paired bootstrap uses each task once per draw.

## 11. Agent handoff contract

Every agent receives one bounded task and returns this exact information:

```text
Task and protocol section:
Actual model/agent identity, if tool-visible:
Allowed files:
Current reproduced defect or missing evidence:
Minimal change made:
Targeted test command and result:
Full-suite command and result:
Real-runtime command and result, or explicitly absent:
Scientific decision changed: no / amendment path
Artifacts and hashes:
Remaining blocker:
Next single task:
```

Agents must not:

- infer completion from a prior agent's prose;
- treat passing mocks as empirical evidence;
- edit protected splits while fixing infrastructure;
- silently loosen a security check or feasibility threshold;
- rename a reduced/inspired model as full Three-Reader;
- run literature searches repeatedly instead of recording one implementation map;
- launch parallel writers against runtime/workflow/verifier interfaces;
- restart the corpus after an inconvenient result;
- add future-work features to rescue a negative result.

After two failed attempts on one issue, stop broad edits and produce a minimal
reproducer. Diagnose the root cause before changing code again.

## 12. Completion conditions

The study is complete in exactly one of two ways:

1. **Scientific feasibility stop:** the real 32x4 development smoke completes
   and fails a registered feasibility condition, with complete artifacts and an
   honest report that H1-H3 were not tested.
2. **Full study:** the smoke passes, Audit A permits protected collection, H1-H3
   are evaluated once under the frozen protocol, Audit B reconciles claims with
   artifacts, and the report/figures are generated.

The following do not count as completion:

- unit tests alone;
- synthetic candidates or fake activations;
- a prepared dataset without model outputs;
- a verifier class that has not passed real security tests;
- high AUROC without equal-budget verified utility;
- an unavailable Colab session;
- a favorable Fellowship rating by another model;
- a README claim unsupported by sealed artifacts.

## 13. Immediate next actions

Execute only these actions now, in order:

1. Update stale `docs/status.md` and `docs/lean_backend.md` to the current pins and
   accepted local evidence.
2. Make the notebook provision a fresh pinned Linux verifier environment without
   loading Gemma first.
3. Run and preserve the seven real Comparator/Landrun tests.
4. Run the real 32x4 development smoke and apply its mechanical gate.
5. Only if the gate passes, freeze the Three-Reader/analysis adaptations and
   implement the remaining training/evaluation stages.

This sequence is intentionally narrow. It preserves completed work, reaches the
highest-uncertainty real-world dependency quickly, and prevents additional local
engineering from being mistaken for scientific progress.
