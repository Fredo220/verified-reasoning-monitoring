# Verified Reasoning Monitoring

> **Coming soon:** A compute-conscious mechanistic-interpretability study of
> whether internal activation signals can help select Lean-verifiable proof
> candidates under a fixed end-to-end time budget.

## The question

Give a language model the same proof problem several times and it may produce
several plausible answers. The difficult part is deciding which candidate is
worth checking first: token confidence alone does not reliably identify the
correct one. This project asks a deliberately narrow question:

> Can internal activation monitors rank complete proof candidates well enough
> to produce more externally verified solutions than token likelihood, text
> features, or direct checking under the same total time budget?

Lean 4 provides an external, machine-checkable answer. The language model stays
frozen throughout the study. We are testing candidate selection, not claiming
that the model has learned to reason better.

## Research design

The first study uses `google/gemma-2-2b-it` and short Lean proof tasks. It
separates three hypotheses:

1. **Prediction:** Internal activations predict whether a complete candidate is
   Lean-valid better than token likelihood and text-only baselines.
2. **Dynamics:** Motion, Region, and Direction across layers add useful
   information beyond static activation probes.
3. **Practical utility:** A monitor selected only on validation data increases
   fully verified solutions under the same measured end-to-end time budget.

The primary result is the third comparison. Strong classification metrics alone
will not be presented as practical success.

## Foundation: Answerability x Familiarity

This work grew out of
[Answerability x Familiarity](https://github.com/Fredo220/Answerability-x-Familarity-),
a preregistered study of whether a small language model distinguishes exposure
to an entity from having enough evidence to answer a specific question.

The earlier project gave us a useful negative result: it did **not** support the
predicted behavioral familiarity effect. Answerability was decodable in the
tested representation setting, but the causal evidence was mixed and
non-confirmatory. That left a more practical question open. Can internal
information improve an actual decision, rather than merely be decoded? This
study moves that question into a domain with an external correctness signal.

## Why this matters

A monitor can score well on a benchmark and still be useless in practice. Here,
it has to survive controls and improve a concrete decision: which proof should
be checked first? Formal verification makes that test measurable. Every
accepted proof must satisfy the same frozen Lean verifier, and every selection
method receives the same total budget.

The study is designed to report positive, negative, inconclusive, and
feasibility results. It does not claim online error detection, general
metacognition, hallucination detection, jailbreak prevention, or improved base
model reasoning.

## Status

The protocol and local implementation are under validation. Code, frozen
configuration, tests, run instructions, artifacts, and results will be released
after the development feasibility gate and provenance audit are complete.

## License

This repository is source-available under the
[PolyForm Noncommercial License 1.0.0](LICENSE.md). Noncommercial research,
experimentation, and study are permitted under its terms. Commercial use
requires separate permission from the copyright holder.

Required Notice: Copyright 2026 Friedrich Reichelt.
