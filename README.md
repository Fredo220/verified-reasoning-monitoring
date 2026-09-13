# Verified Reasoning Monitoring

> "What if only a machine can defeat another machine?"
>
> Alan Turing, as portrayed in *The Imitation Game* (2014)

The line comes from the film rather than the historical record, but the question behind it has become increasingly relevant. Modern language models perform billions of internal computations for every answer. Researchers cannot inspect each of them by hand.

This project asks a narrower version of that question:

**Can a machine help us monitor another machine, and can that monitoring produce more externally verified solutions within the same end-to-end time budget?**

Research is in progress. No results from this study are available yet.

## The problem

A language model can produce several plausible solutions to the same problem. Some are correct; others only look convincing.

We can check every attempt, but generation, monitoring and verification all consume time. Under a fixed budget, checking an unpromising attempt may prevent us from reaching a valid one.

The model's internal activations may contain information that is not obvious from its final text or token confidence. If a small monitor can read that information, it might help us decide which attempt should be checked first.

That is the practical idea behind this study:

~~~text
internal activations -> candidate ranking -> external verification
~~~

The final judge is not the monitor. It is [Lean 4](https://lean-lang.org/), a formal proof checker.

## Where the question came from

My earlier project, [Answerability x Familiarity](https://github.com/Fredo220/Answerability-x-Familarity-), investigated whether a language model distinguishes familiarity with an entity from having enough evidence to answer a particular question.

The predicted behavioral effect was not supported. However, the model's internal activations contained information about whether an answer was available in the prompt. The subsequent causal evidence was mixed.

This raised a more useful question. Even if internal information does not appear reliably in the model's behavior, can it still help us make better decisions?

During that work, I encountered Anthropic's [Constitutional Classifiers research](https://arxiv.org/abs/2501.18837), which established a defense based on input and output classifiers. Its follow-up, [Constitutional Classifiers++](https://arxiv.org/abs/2601.04603), adds efficient linear probes over internal activations and combines them with external classifiers in a two-stage cascade.

This project transfers that general monitoring principle to a different and externally verifiable setting. Instead of detecting potentially harmful conversations, the monitor ranks mathematical proof attempts. Instead of a safety policy determining the label, Lean determines whether the proof is formally valid.

This is not a replication of Anthropic's jailbreak defense. The task, labels, baselines and success criterion are different.

## The research question

**Do internal activation monitors help find more Lean-verifiable proof candidates than token likelihood, text-based selection and direct checking when every method receives the same total time?**

The model is not retrained. A frozen [google/gemma-2-2b-it](https://huggingface.co/google/gemma-2-2b-it) model generates short proof candidates, while small external monitors examine its internal activations.

This makes the experiment a concrete test of machine-assisted interpretability: another computational system reads the model's internal state, but its usefulness is judged against independent external evidence.

## Three levels of evidence

The study separates three questions that are often mistakenly treated as one.

### H1: Prediction

Can internal activations distinguish valid from invalid proof candidates better than token likelihood and simple text features?

A positive result would show that validity-related information is decodable from the model. It would not yet show that the information is useful in practice.

### H2: Dynamics

Does the way activations change across layers add information beyond a static snapshot?

We compare static probes and a Motion-only monitor with a planned Gemma adaptation of the full [Three-Reader architecture](https://arxiv.org/abs/2608.05660). Three-Reader combines information about motion, region and direction in the residual-stream trajectory. The adaptation will be described as full only if its fidelity to all three components is documented before protected evaluation.

A positive result would suggest that the development of the internal representation matters, not only its final location.

### H3: Practical utility

Does the best internal monitor find more verified solutions under the same total time budget than both:

- the strongest selection method without internal activations; and
- checking candidates immediately as they are generated?

This is the main result. Strong prediction without an improvement in verified solutions would be reported as decodable information without demonstrated practical value.

## The experiment

1. **Generate proof attempts.**
   A frozen Gemma 2 model produces several natural proof candidates for short Lean problems.

2. **Verify every candidate.**
   Lean checks each completed candidate. Invalid proofs, infrastructure failures and timeouts are recorded separately.

3. **Train small monitors.**
   The monitors receive the problem, the completed candidate and selected internal activations. They never receive Lean output, reference proofs or information from later attempts.

4. **Compare methods.**
   Internal monitors are compared with token likelihood, text features and direct checking.

5. **Freeze the selection rule.**
   Models and settings are selected using training and validation data before protected test results are opened.

6. **Run the equal-budget test.**
   Every method receives the same total time, including generation, monitoring, data transfer and Lean verification.

7. **Count externally verified solutions.**
   The independent unit is the proof problem, not an activation, token or individual candidate.

~~~mermaid
flowchart LR
    A[Lean problem] --> B[Gemma generates candidates]
    B --> C[Monitor ranks candidates]
    C --> D[Lean checks candidates]
    D --> E[Verified solutions within the same budget]
~~~

## What the monitor can and cannot do

The monitor cannot create a correct proof that Gemma never generated. Its immediate purpose is to improve selection and compute allocation.

A positive result would mean:

> Among the proof attempts already available, internal signals helped us reach valid ones sooner.

It would not establish that:

- Gemma developed stronger reasoning abilities;
- the monitor detects errors during generation;
- internal activations provide a complete explanation of the model;
- the method generalizes to arbitrary natural-language answers;
- it detects hallucinations, deception or jailbreaks.

Lean verifies the formal statement it receives. It cannot determine whether an incorrectly formalized statement faithfully represents an original natural-language problem.

Negative and inconclusive findings remain valid outcomes of the study.

## Mechanistic follow-up

Prediction alone does not explain what the monitor has learned. It could rely on genuine proof-relevant computation, but it could also exploit candidate length, formatting or another shortcut.

Circuit tracing is therefore a follow-up, not a substitute for the main experiment.

If an internal monitor performs usefully on unseen problems, Anthropic's [open-source circuit-tracing tools](https://www.anthropic.com/research/open-source-circuit-tracing) can be applied offline to matched valid, invalid and difficult examples from the training and validation sets.

The follow-up would ask:

1. Which internal feature paths influence the monitor?
2. Do those paths correspond to proof-relevant computation?
3. Do they survive controls for length and formatting?
4. Does perturbing them in the original Gemma model produce the predicted effect?
5. Can robust circuit features improve a small runtime monitor on fresh problems?

Full attribution graphs would not run for every candidate. They are too expensive and represent only part of the original computation. Any graph-based hypothesis must therefore be tested in the original model and on held-out data.

Circuit evidence may explain or improve a successful monitor. It cannot rescue a negative primary result.

## Why this matters

Current interpretability research often asks whether information can be extracted from a model or whether a particular internal mechanism can be reconstructed.

This project adds a practical requirement:

> Does the internal signal improve an externally verified outcome after its computational cost is included?

That distinction matters for reliable AI systems. A monitor can have excellent prediction scores and still be too slow, too fragile or too poorly calibrated to help in practice.

If the approach works, a lightweight external monitor could help allocate expensive verification or additional computation without modifying the underlying model. The same principle might later be tested in other domains, but such transfer would require new evidence and new validation.

## Current status

The protocol and local implementation are being checked. The first empirical milestone is a development-only feasibility run with real Gemma candidates and real Lean verification.

The study proceeds to its protected tests only if the development run produces enough valid candidates, invalid candidates and problems containing both.

The project is designed around an 8 GB RAM laptop and free Colab access where available. The public release will include:

- source code and pinned configurations;
- tests and run instructions;
- model, tokenizer and verifier provenance;
- runtime and compute measurements;
- successful and unsuccessful runs;
- protocol changes;
- negative or inconclusive findings.

Limited compute reduces the scale of the study, but not the requirement for external verification, held-out evaluation or honest reporting.

## License

Available under the [PolyForm Noncommercial License 1.0.0](LICENSE.md).

Noncommercial research, experimentation and study are permitted under its terms. Commercial use requires separate permission. This is a source-available license.

Required Notice: Copyright 2026 Friedrich Reichelt.
