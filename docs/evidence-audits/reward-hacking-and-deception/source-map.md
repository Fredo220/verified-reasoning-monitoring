# Source map

This is a scoped methods-and-reproducibility audit, dated 30 September 2026. The two papers are reconstructed in order. Published performance remains author-reported. The code-correctness study is outside this audit's write boundary.

## 1. Reward-hacking paper

**RH-PAPER:** Bergen et al., *Monitoring and Discovering Reward Hacking with Internal Representations during LLM Evaluations*, arXiv:2609.19101v1, 16 September 2026. [Versioned HTML](https://arxiv.org/html/2609.19101v1), [PDF](https://arxiv.org/pdf/2609.19101v1).

Inspected: definitions and labeling in sections 2.1-2.2; DoM extraction in section 3.1 and Equation 1; representation/steering checks in section 3.2; selection, resampling, monitor replacement and false-positive checks in section 4; non-SWE discovery in section 5; discussion/limitations in sections 7-8; taxonomy in Appendix A; synthetic-condition tables in Appendix B; judge rubrics in Appendix C. PDF page references in the records are one-based.

Dependency chain:

`matched synthetic conversations -> specified activation spans -> fixed-layer DoM -> probe selection -> threshold calibration -> held-out rollout labels -> detection/continuation/discovery analyses`

Required but not located sufficiently: complete conversation files and span masks; exact projected-vector transformation; hook/indexing and layer-search manifest; passage aggregation; reconciliation of raw-dot scoring with the cosine-similarity axis in Figure 14; immutable runtime/model identities; row-level outputs and exact selection/calibration IDs. Appendix B lists projected variants without supplying a complete projection recipe.

**RH-RELEASE-SEARCH:** A bounded inspection of paper links and focused title/identifier searches on GitHub, Hugging Face and author-associated sources did not identify an attributable code/data/probe release. A paper-summary issue is not an author release. Some author-site fetches failed. This is a search outcome, not proof that no release exists; reproducing the full study remains blocked on obtaining the missing material.

## 2. Deception paper

**DE-PAPER:** Nicholas Goldowsky-Dill, Bilal Chughtai, Stefan Heimersheim and Marius Hobbhahn, Apollo Research, *Detecting Strategic Deception Using Linear Probes*, arXiv:2502.03407v1, 5 February 2025. [Versioned HTML](https://arxiv.org/html/2502.03407v1), [PDF](https://arxiv.org/pdf/2502.03407v1).

Inspected: sections 3.1-3.3, 4.1-4.2 and 5; additional evaluation/ambiguity results in Appendices A and E; method variants in Appendix D; dataset and grading descriptions in Appendix G. This does not constitute a row-by-row relabeling of the released transcripts.

**DE-CODE:** [ApolloResearch/deception-detection at f8ec4010e74927394709dffa22b97bdf8cd5a62f](https://github.com/ApolloResearch/deception-detection/tree/f8ec4010e74927394709dffa22b97bdf8cd5a62f). Read as source text only; no upstream code, pickle or model checkpoint was executed or loaded.

| Source ID | Pinned path and inspected component |
| --- | --- |
| DE-DETECTOR | [deception_detection/detectors.py](https://github.com/ApolloResearch/deception-detection/blob/f8ec4010e74927394709dffa22b97bdf8cd5a62f/deception_detection/detectors.py), `LogisticRegressionDetector.fit`, `get_score_tensor`, `DirectionDetector.score` |
| DE-TRAINING-DATA | [deception_detection/data/repe.py](https://github.com/ApolloResearch/deception-detection/blob/f8ec4010e74927394709dffa22b97bdf8cd5a62f/deception_detection/data/repe.py), true-fact filtering, paired directives, `_split_statement` and detection masks |
| DE-TOKENIZATION | [deception_detection/tokenized_data.py](https://github.com/ApolloResearch/deception-detection/blob/f8ec4010e74927394709dffa22b97bdf8cd5a62f/deception_detection/tokenized_data.py), chat-template and character-to-token mask handling |
| DE-ACTIVATIONS | [deception_detection/activations.py](https://github.com/ApolloResearch/deception-detection/blob/f8ec4010e74927394709dffa22b97bdf8cd5a62f/deception_detection/activations.py), `Activations.from_model`, hidden-state indexing |
| DE-SCORES | [deception_detection/scores.py](https://github.com/ApolloResearch/deception-detection/blob/f8ec4010e74927394709dffa22b97bdf8cd5a62f/deception_detection/scores.py), response aggregation and serialized labels/scores |
| DE-METRICS | [deception_detection/metrics.py](https://github.com/ApolloResearch/deception-detection/blob/f8ec4010e74927394709dffa22b97bdf8cd5a62f/deception_detection/metrics.py), threshold/recall/FPR and AUROC helpers |
| DE-THRESHOLD | [deception_detection/prompt_scorer.py](https://github.com/ApolloResearch/deception-detection/blob/f8ec4010e74927394709dffa22b97bdf8cd5a62f/deception_detection/prompt_scorer.py), `PromptScorer`, control quantile and strict threshold comparison |
| DE-POSTPROCESS | [deception_detection/postprocess.py](https://github.com/ApolloResearch/deception-detection/blob/f8ec4010e74927394709dffa22b97bdf8cd5a62f/deception_detection/postprocess.py), separate honest/deceptive scenario positive rates |
| DE-CONFIG | [example_results/instructed_pairs/cfg.yaml](https://github.com/ApolloResearch/deception-detection/blob/f8ec4010e74927394709dffa22b97bdf8cd5a62f/example_results/instructed_pairs/cfg.yaml), published run configuration |
| DE-RESULTS | [example_results/instructed_pairs/results_table.csv](https://github.com/ApolloResearch/deception-detection/blob/f8ec4010e74927394709dffa22b97bdf8cd5a62f/example_results/instructed_pairs/results_table.csv), reported counts, AUROC, recall and FPR columns |
| DE-REUSE | Pinned repository tree, README and `pyproject.toml`; no LICENSE file or explicit grant identified in the inspected tree |

Dependency chain:

`paired instructions + identical fact prefixes -> token masks -> Llama residual activations -> training-only scaling -> L2 logistic direction -> mean response score -> Alpaca threshold -> separately labeled on-policy scenario responses`

Unresolved: complete reproducible environment and model revision, independent row-level label re-audit, exact correspondence of published paper figures to each released example run, reuse permissions, and paper-versus-code resolution for excluding five tokens versus five words. Existing probe weights are tied to the original model's representation space.

## 3. Local context and execution boundary

**LOCAL-CONFIG:** `configs/code_monitoring.json` in `/Users/friedrichreichelt/Documents/verified-reasoning-monitoring`, read at repository HEAD `0037ad19901b8ee2f350b2a9e0061c9aebe634d3` with existing uncommitted work. It pins `Qwen/Qwen2.5-Coder-1.5B-Instruct` and tokenizer to `2e1fd397ee46e1388853d2af2c993145b0f1098a`. This identifies a possible reusable capture runtime, not a validated deception or reward-hacking detector.

**LOCAL-BOUNDARY:** `docs/streaming_live_plan_2026-09-30.md`, inspected only to preserve the separate code-success/prefix-monitoring study. No labels, thresholds, test tasks, outcomes or trained probe weights from that study are transferred into these proposed pilots.

**COLAB-UI:** The visible Google account button at `https://colab.research.google.com/?authuser=1` showed `frederic.reichelt@gmail.com`. No new notebook or model run was started. This confirms the selected account, not GPU availability or experiment readiness.

All eight audit files belong only to this folder. Empirical execution, dependency changes, upstream-code reuse and public publication are separate actions. A future active tool-using agent experiment requires a separate security review; this audit does not assess that branch.
