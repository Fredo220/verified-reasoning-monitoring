# Verified Reasoning Monitoring

> **Coming soon:** A compute-conscious mechanistic-interpretability study of
> whether internal activation signals can help select Lean-verifiable proof
> candidates under a fixed end-to-end time budget.

## The idea

Give a language model the same problem several times and it may produce several
plausible solutions. Some are correct, some are not, and checking every attempt
costs time. This project asks:

> Can we use the model's internal activations to recognize which solution
> attempts are promising, and therefore reach more externally verified correct
> answers with the same compute budget?

We use short mathematical proofs because Lean 4 can check them automatically.
The language model stays frozen. We are not teaching it to reason better; we
are testing whether its internal state helps us decide which completed attempt
to verify first.

## Where the idea came from

This project began with
[Answerability x Familiarity](https://github.com/Fredo220/Answerability-x-Familarity-).
That study asked whether a small language model internally distinguishes
between recognizing an entity and actually having enough evidence to answer a
question. The predicted behavioral effect was not supported. Answerability was
decodable in the tested representation setting, but the causal evidence was
mixed and non-confirmatory.

That result led to a more practical question: even when internal information is
decodable, can it help make a better decision?

While working on that experiment, I came across Anthropic's
[Constitutional Classifiers red-team study](https://www.anthropic.com/news/constitutional-classifiers)
and the follow-up
[Constitutional Classifiers++ paper](https://arxiv.org/abs/2601.04603).
Anthropic uses classifiers to identify potentially harmful exchanges, tests
them against attempted jailbreaks, and measures both protection and practical
cost. The newer system uses a cheap probe over internal activations as an early
screen and sends suspicious cases to a stronger classifier.

I wondered whether we could reverse-engineer that experimental logic for a
different, easier-to-verify question. Instead of looking for a jailbreak, we
look for a potentially incorrect proof. Instead of asking whether a safety
classifier blocks harm, we ask whether an internal monitor helps us select a
candidate that Lean verifies as correct sooner. This is an adaptation of the
research pattern, not a replication of Anthropic's safeguard system.

## What the experiment does

1. Gemma 2 generates several short proof attempts for the same Lean problem.
2. Lean checks which completed attempts are actually valid.
3. Small monitors learn to predict validity from the model's activations alone.
4. We compare them with token confidence, text features, and checking attempts
   in the order they were generated.
5. Finally, every method receives the same total time budget. We measure which
   method solves more tasks, including all monitoring and verification costs.

The study asks three separate questions:

- **Can internal activations predict validity?**
- **Does the way activations change across layers add useful information?**
- **Does that information produce more verified solutions at equal cost?**

The last question is the main result. A monitor is not practically useful just
because it achieves a strong classification score.

## Why this matters

A monitor can score well on a benchmark and still be useless in practice. Here,
it must improve a concrete decision: which proof should be checked first? Every
accepted proof must pass the same frozen Lean verifier, and every method gets
the same measured budget.

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
