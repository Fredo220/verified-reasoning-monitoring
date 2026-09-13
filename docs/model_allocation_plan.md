# GPT-6 / GPT-5.6 Sol Research Execution Plan

> For agentic workers: use subagent-driven-development or executing-plans. Complete and verify one bounded deliverable before expanding scope. Checkboxes record accepted work, not intentions.

**Date:** 2026-09-07
**Goal:** Execute the approved Verified Reasoning Monitoring study with economical implementation and concentrated expert review.
**Architecture:** GPT-5.6 Sol owns implementation, routine scientific decisions, testing, execution and reporting. GPT-6 performs only two bundled, read-only audits at points where an unnoticed mistake could invalidate the study. Both work against the same frozen protocol; neither changes hypotheses to obtain a positive result.
**Tech stack:** Python, PyTorch, Transformers, scikit-learn, LeanDojo/Lean, Jupyter, free Colab.
**Governing documents:** [Approved research protocol](research_plan.md) defines the scientific study; this model-allocation plan defines task ownership, audit timing and cost controls. Both documents are binding during execution. If they appear to conflict, the research protocol governs scientific decisions and this document governs model assignment. Neither document may be silently changed after protected outcomes are opened.

## 1. Model Assignment and Cost Assumptions

Use `gpt-6-astra` for the GPT-6 role and `gpt-5.6-sol` for the Sol role when those identifiers are actually available in the execution tool. This is a proposed allocation, not a claim that the current task or existing agents have already switched models.

Verify the selected model from tool-visible execution metadata before recording model usage. If GPT-5.6 Sol is unavailable, pause that delegated task or assign it to an independently identified permitted model and record the deviation before work begins. Do not silently substitute GPT-6 for Sol or claim that Sol performed work when model identity cannot be verified.

The allocation is based on task risk, not a measured benchmark of these models on this repository. OpenAI's current token-based Work/Codex rate card lists GPT-6 Astra at 2.5 times the GPT-5.6 Sol input, cached-input and output rates. This rate card may not govern the user's plan, so actual billing and included usage must be checked before dispatch. No paid API fallback is authorized.

| Role | Default reasoning | Work | Why assign it here? |
|---|---|---|---|
| GPT-5.6 Sol: primary worker | Medium | Repository work, CLI, serialization, notebook, plots, tests and reports | Most work is constrained by the frozen protocol and executable checks |
| GPT-5.6 Sol: specialist mode | High | Lean integration, split/leakage checks, Three-Reader adaptation and statistics | These tasks are demanding but can be reviewed through explicit evidence |
| GPT-6: Audit A | High | One pre-collection validity review covering verifier safety, leakage, monitor boundaries and budget accounting | Finds study-invalidating design defects before protected data are opened |
| GPT-6: Audit B | High | One final evidence-and-claims review after results are sealed | Checks statistics, controls, interpretation and publication claims |

Use one Sol worker by default. A second Sol worker is useful only for non-overlapping files after interfaces are agreed. GPT-6 does not implement modules, watch jobs or reread the full project history. Each GPT-6 audit receives a compact evidence packet containing the frozen protocol, relevant diff, test results, unresolved risks and exact decisions requested.

**Absolute minimum-cost variant:** run the entire project with Sol and replace both GPT-6 audits with an independent qualified human review using the same audit packets. GPT-6 is risk reduction, not a scientific requirement.

## 2. Starting State: Preserve Existing Work

The separate repository already contains the protocol, configuration, core receipts/statistics, budget engine, Gemma runtime and a partial monitor module. Tests for data and Lean exist, but their implementation modules were absent at this inventory. CLI, notebook and empirical artifacts were also absent. Files are currently uncommitted; no publication is established by this plan.

The previous checkpoint reported 16 passing core/runtime tests. This is historical implementation evidence, not a fresh full-suite result and not a real Gemma/Lean experiment.

Before editing, reconcile existing agents Huygens (monitors), Feynman (Lean) and Euclid (data). Their names do not establish their underlying model. Read their state and changes; retain valid work. Do not assign a second writer to their files while they are running.

Earlier permission-review credit failures and browser startup failures are infrastructure blockers, not scientific failures. Do not bypass denied writes, recreate the project elsewhere, or start paid services to work around them.

## 3. Non-Negotiable Study Boundaries

- H1 predicts validity; H2 tests dynamic information; H3 tests verified solutions under equal total time. Report them separately.
- Keep Gemma-2-2B-it, FP16, batch 1, 512 input / 64 output tokens and pinned revisions.
- Maximum twelve allocated free-Colab GPU hours; laptop has 8 GB system RAM. Agent-token costs and experimental GPU costs are separate ledgers.
- Feasibility precedes large collection: 32 development tasks, four proposals each, at least 20 valid, 20 invalid and eight mixed-validity tasks.
- A temporary lack of a free Colab GPU, browser access or notebook connectivity is an infrastructure availability event. Preserve resumable state and retry when access returns; do not classify it as evidence that the scientific design is infeasible.
- Preserve task-group splits, training-only transforms, validation-only selection and untouched test outcomes.
- Lean completion alone is not proof of safe, trustworthy verification. Require isolation and final proof/axiom checks.
- No steering, SAE expansion, new models, self-learning, old-study data or additional research frameworks on the critical path.
- Negative or inconclusive findings are legitimate outcomes. No model is tasked with making the hypothesis pass.

## 4. Ordered Work Packages

### P0. Reconcile State and Freeze Interfaces

**Lead: Sol medium. No routine GPT-6 review.**

Files: existing `src/vrm/*.py`, `tests/*.py`, `docs/status.md`, `configs/study.json`.

- [ ] Check agent ownership, current files and test collection; distinguish missing implementations from regressions.
- [ ] Sol resolves split-name inconsistencies and the task/candidate/verifier contracts against the frozen protocol.
- [ ] Record one minimal backlog with owner, dependency and acceptance condition per item.

Acceptance: one agreed interface contract and no duplicate writers. No wholesale rewrite.

### P1. Establish Trustworthy Lean Verification

**Lead: Sol high. Included later in GPT-6 Audit A.**

Files: `src/vrm/lean.py`, `tests/test_lean.py`, `docs/lean_backend.md`.

- [x] Resolve the benchmark/runtime provenance blocker through the approved
  pre-outcome amendment: preserve Benchmark 4 v3 and its canonical Mathlib
  commit, use the matching rc1 toolchain and Comparator, and replace the
  unavailable LeanDojo object only with Mathlib's official Azure build cache.
  Native-Linux acceptance remains a separate unchecked gate.
- [ ] Specify the sandbox and proof/axiom audit before implementing the worker.
- [ ] Implement valid, invalid, timeout and infrastructure-error results without conflating them.
- [ ] Exercise known valid, invalid, self-referencing, `sorry` and unauthorized-assumption cases in the real backend.
- [ ] Prepare verifier threat-boundary evidence for Audit A: what establishes validity and what prevents untrusted code from accessing the host.

Acceptance: real safe verification works in the intended free runtime. A permanently fail-closed placeholder is not completion. If the backend cannot fit that environment, stop GPU collection and report the concrete feasibility blocker.

### P2. Finish Data Preparation

**Lead: Sol high. Included later in GPT-6 Audit A.**

Files: `src/vrm/data.py`, `tests/test_data.py`, `docs/data_contract.md`.

- [ ] Implement official-source provenance, complete-proof eligibility and exact tokenizer-length checks.
- [ ] Group duplicates and variants before deterministic split assignment.
- [ ] Ensure reference proofs never appear in generated prompts or monitor inputs.
- [ ] Check insufficient-pool handling without silently changing quotas or selecting by outcomes.

Acceptance: reproducible development tasks with validated source identity; protected tasks remain unopened. Do not reconstruct complete proofs by concatenating arbitrary nested tactic traces.

### P3. Connect Runtime, Receipts and Notebook

**Lead: Sol medium. Included later in GPT-6 Audit A.**

Files: `src/vrm/runtime.py`, `src/vrm/core.py`, `src/vrm/engine.py`, new `src/vrm/cli.py`, related tests, `notebooks/verified_reasoning_monitoring.ipynb`.

- [ ] Wire `prepare`, `smoke`, `collect`, `train`, `evaluate`, `report` to actual implementations; unfinished commands must fail clearly.
- [ ] Save activation arrays separately from JSON metadata, including prompt-boundary arrays.
- [ ] Verify receipt identity and atomic resume on the actual storage filesystem, not just a temporary local directory.
- [ ] Build a short notebook that calls the tested package rather than duplicating its implementation.
- [ ] Test exactly one BOS, post-layer positions, raw likelihoods and all charged overhead.

Acceptance: runnable development smoke command/notebook with honest prerequisite errors and interruption recovery. Toy-tensor tests do not substitute for the real forward pass.

### P4. Run the Critical-Path Smoke

**Lead: Sol high. The go/no-go rule is mechanical and protocol-defined.**

- [ ] Restore supported browser access or obtain the active notebook link; use HF_TOKEN only as a Colab secret.
- [ ] Execute the real 32-by-4 development smoke within the one-hour allowance.
- [ ] Measure correctness yield, mixed tasks, extraction cost, peak memory, disk and resume.
- [ ] Project total cost and sampling uncertainty; retain the target size or make the one permitted pretest reduction.
- [ ] Record the evidence supporting go/no-go before training or test collection.

Acceptance: empirical feasibility, not an assumption based on model size. If it fails, diagnose the actual failure before proposing any protocol amendment. Do not spend the remaining GPU budget on a nonviable pipeline.

The smoke must run as soon as P1-P3 provide the minimum trustworthy path: one real Gemma forward pass, safe Lean verification, complete receipts and resume. Do not wait for full Three-Reader implementation, production-quality reporting or all optional documentation. A failed feasibility gate may close the feasibility pilot, but it does not test or answer H1, H2 or H3.

### P5. Finish Readers and Baselines

**Lead: Sol high. Paper fidelity and monitor boundaries are included in Audit A.**

Files: `src/vrm/monitors.py`, `tests/test_monitors.py`, `docs/three_reader_implementation.md`.

- [ ] Implement raw likelihood, TF-IDF/length/likelihood, all-layer static, Motion-only and full Three-Reader baselines.
- [ ] Document the exact published architecture and every Gemma adaptation; settle missing details before training.
- [ ] Test padding, layer/token order, training-only normalization/codebook updates and genuinely independent shuffled controls.
- [ ] Implement seeds 11/22/33, registered regularization search, early stopping and saved training diagnostics.
- [ ] Record an implementation matrix proving which published components are present; a reduced architecture must be named as reduced.

Acceptance: tested readers with reproducible save/load and no label/reference leakage. Complete large neural-training work only after P4 passes; existing implementation need not be discarded while waiting.

### P6. Collect, Train and Freeze Selection

**Lead: Sol runs deterministic jobs and validates the frozen selection artifact.**

- [ ] Collect the approved training/validation candidates with resumable shards and measured costs.
- [ ] Train baselines/readers without opening test labels.
- [ ] Apply the documented validation selection rule to internal and non-internal champions.
- [ ] Seal model identities, preprocessing, seeds and evaluation configuration.

Acceptance: reproducible selection without manual cherry-picking. Infrastructure errors remain distinct from invalid proofs. No premium model is needed to watch routine training logs.

### P7. Prospective Evaluation and Statistics

**Lead: Sol implementation and execution. Audit A must already have passed before protected collection; Audit B occurs only after results are sealed.**

Files: budget engine, evaluation/report modules and their tests.

- [ ] Verify paired tasks/seeds, rotating system order, 30-second inclusive budgets, eight-candidate cap and per-check timeout.
- [ ] Evaluate the frozen internal champion, non-internal champion and direct verifier policy.
- [ ] Audit generated candidates afterwards without counting late discoveries as budgeted successes.
- [ ] Compute task-level paired intervals with 10,000 bootstrap draws; report ID and novel-premises results separately.
- [ ] Retain zero-success tasks, technical missingness, components, shuffle and wording/length controls.

Acceptance: H3 supported only when both registered comparisons have positive lower confidence bounds. H1/H2 cannot rescue H3. No tuning on opened outcomes.

### P8. Communicate and Publish

**Lead: Sol drafts and plots. GPT-6 Audit B reviews claims and evidence links once.**

Files: `README.md`, report, four result figures, notebook, dependency/provenance records.

- [ ] Produce prediction, verified utility, cost and transfer figures directly from audited artifacts.
- [ ] Explain the question, result and limitations in plain English; distinguish completed evidence from future work.
- [ ] Report one-time training costs, failed runs, amendments and hardware limitations.
- [ ] Run the full tests plus documented real-runtime checks and inspect the final diff.
- [ ] Commit and publish only with working authorization; verify the remote branch and public artifact links before claiming publication.
- [ ] Add reciprocal project links without reopening or rewriting the old study.

Acceptance: an independently understandable report, including a negative/unclear result if that is what happened. Fellowship selection is not an acceptance test for this code.

## 5. Execution Order and Parallelism

Critical path: **P0 -> minimum trustworthy P1/P2/P3 path -> P4 -> complete P5/P6 -> P7 -> P8**.

P1 and P2 can run concurrently when file ownership and interfaces are fixed. P3 can reuse existing code during that work. P4 begins immediately after the minimum trustworthy end-to-end path exists. Remaining hardening that is unnecessary for the smoke can continue only after the empirical bottleneck is measured. Do not parallelize work that repeatedly changes shared interfaces. Do not launch protected collection or full monitor training before P4 passes.

GPT-6 is used at exactly two scheduled checkpoints:

1. **Audit A, pre-collection validity gate:** after the real development smoke and monitor implementation, but before protected candidate collection. Review the verifier boundary, source/split provenance, leakage controls, monitor information boundary, Three-Reader fidelity, budget accounting and frozen selection/test rules. Explicitly verify that the transferred Constitutional Classifiers++ principles remain limited to contextual internal monitoring plus joint measurement of utility, cost and false alarms, without importing its jailbreak labels or safety-specific loss design into the Lean experiment.
2. **Audit B, final evidence gate:** after results and audit artifacts are sealed, but before public claims. Review statistical units, controls, missingness, cost accounting, claim strength and evidence links.

Audit A returns `pass`, `repair_before_collection` or `not_evaluable`. Audit B returns `claims_supported`, `revise_claims` or `not_evaluable`. Sol performs any repairs. A failed audit never authorizes changing hypotheses or test outcomes.

## 6. Compact Handoff Format

Give each worker only the protocol sections it needs, current interfaces, relevant files and its acceptance tests. Do not resend the entire historical conversation.

```text
Task: P3 / activation serialization and resume
Owner/model: GPT-5.6 Sol, medium
Allowed files: runtime/core/engine and their targeted tests
Inputs: current task/candidate contract and config
Do not change: hypotheses, split rules, model revision, protected artifacts
Acceptance: arrays stored separately; immutable metadata; resume tested
Return: changed paths, test command/results, remaining risks, next dependency
```

Reviewers read the diff and executable evidence, not just the implementer's summary. Each review returns actionable findings with file/line references. Fix a concrete finding; do not regenerate an entire module for stylistic preference.

## 7. Cost Controls and Escalation

- Default to Sol for every work package. GPT-6 receives only the two compact audit packets above. Do not promise a percentage saving without measured usage and the user's applicable pricing.
- Keep at most two implementers active. Prefer one when serial dependencies dominate.
- After two unsuccessful attempts at the same bug, Sol must first use a minimal reproducer and systematic debugging. GPT-6 escalation is allowed only when the unresolved issue could invalidate the study and cannot be settled by a test, protocol text or independent human review.
- An unscheduled GPT-6 escalation must be a narrow question with a minimal evidence packet; it does not transfer ownership of the work package.
- Read a paper's relevant methods once per component and store a concise cited implementation mapping; no repeated broad literature search.
- Record per-package model, available token/usage data, retries and accepted deliverables. Missing usage information is reported as unavailable, not zero.
- Never buy credits, switch to paid inference or redeem a reset without explicit authorization.
- If tooling cannot select an agent's model, disclose that limitation. Manual task/model selection is preferable to claiming an unsupported automatic routing setup.

**Dispatch rule:** deterministic checks use code, not another model. Routine prose cleanup, inventory and test fixes stay with Sol. Do not run duplicate model reviews "for confidence," and do not keep an agent active while Colab is merely computing.

Official pricing references checked on 2026-09-07:

- [ChatGPT Work and Codex token-based rate card](https://help.openai.com/en/articles/20001415-chatgpt-rate-card-enterprise-token-based-pricing)
- [GPT-5.6 Sol model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
- [Current model guidance](https://developers.openai.com/api/docs/guides/latest-model)

## 8. Immediate Next Work

1. Reconcile the existing three workers and partial files (P0).
2. Complete only the minimum trustworthy Gemma -> activation receipt -> Lean verification -> resume path required for the development smoke.
3. Run the 32-task, four-proposal real smoke before completing full Three-Reader training or publication infrastructure.
4. If free Colab is temporarily unavailable, preserve the ready-to-run state and record an infrastructure blocker; do not report scientific infeasibility.
5. If the empirical smoke itself fails a registered gate, publish a feasibility result and state explicitly that H1-H3 remain untested.

This document is the allocation plan only. Creating it does not start agents, change their models, run Colab, or establish any empirical result.
