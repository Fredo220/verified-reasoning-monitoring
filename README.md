# Verified Reasoning Monitoring

> "What if only a machine could defeat another machine?"
>
> Alan Turing, as portrayed in *The Imitation Game* (2014)

The line is fictionalized, but the question behind it has become increasingly relevant. Modern language models perform billions of internal computations for every answer. Researchers cannot inspect each of them by hand.

This project asks a narrower, testable version of that question:

**Can a machine help us monitor another machine, and can that monitoring produce more externally verified solutions within the same compute budget?**

Research is in progress. No results from this study are available yet.

## The problem

A language model can produce several plausible solutions to the same problem. Some are correct; others only look convincing.

We could check every attempt, but generation, monitoring and verification all consume time. Under a fixed budget, checking an unpromising attempt may prevent us from reaching a valid one.

The model's internal activations may contain useful information that is not obvious from its final text or token confidence. If a small monitor can read that information, it might help decide which attempt should be checked first.

That is the practical idea behind this study:

~~~text
internal activations -> candidate ranking -> external verification
~~~

The final judge is not the monitor. It is [Lean 4](https://lean-lang.org/), a formal proof checker.

## Where the question came from

My earlier project, [Answerability x Familiarity](https://github.com/Fredo220/Answerability-x-Familarity-), investigated whether a language model distinguishes familiarity with an entity from having enough evidence to answer a particular question.

The predicted behavioral effect was not supported. However, the model's internal activations contained information about whether an answer was available in the prompt. The subsequent causal evidence was mixed.

This raised a more useful question: even when internal information does not appear reliably in a model's behavior, can it still help us make better decisions?

During that work, I encountered Anthropic's [Constitutional Classifiers research](https://arxiv.org/abs/2501.18837) and [Constitutional Classifiers++](https://arxiv.org/abs/2601.04603). These systems use inexpensive classifiers, including classifiers that read internal activations, to identify suspicious exchanges before applying more expensive safeguards.

This project transfers that general monitoring principle to a different, externally verifiable setting. Instead of detecting potentially harmful conversations, the monitor ranks mathematical proof attempts. Instead of a safety policy determining the label, Lean determines whether the proof is formally valid.

This is not a replication of Anthropic's jailbreak defense. The task, labels, baselines and success criterion are different.

## The research question

**Do internal activation monitors help find more Lean-verifiable proof candidates than token likelihood, text-based selection and direct checking when every method receives the same total time?**

A frozen [google/gemma-2-2b-it](https://huggingface.co/google/gemma-2-2b-it) model generates short, complete proof candidates. Small external monitors examine its internal activations. Gemma itself is not retrained.

This makes the experiment a concrete test of machine-assisted interpretability: another computational system reads the model's internal state, but its usefulness is judged against independent external evidence.

The project tests two stages of that idea: lightweight monitoring in the primary study, followed by mechanistic circuit analysis only if the monitor proves useful.

## Three levels of evidence

The study separates three questions that are easy to conflate:

1. **Prediction:** Can internal activations distinguish valid from invalid proof candidates better than token likelihood and simple text features?
2. **Dynamics:** Does the full Three-Reader representation of motion, region and direction add information beyond static multi-layer probes and a Motion-only monitor?
3. **Practical utility:** Under the same end-to-end time budget, does the best internal monitor lead to more fully verified solutions than the strongest non-internal method and direct checking?

The third question is the primary endpoint. Strong prediction without improved verified yield would mean that the signal is decodable but has not demonstrated practical value under the tested budget.

## The experiment

1. **Generate attempts.** Frozen Gemma 2 proposes short Lean proofs.
2. **Verify training examples.** Lean labels complete candidates as valid or invalid.
3. **Train small monitors.** The monitors learn from selected activation states without changing Gemma.
4. **Freeze the selection.** Monitor and baseline choices are made on validation data before the protected test.
5. **Test on new problems.** The selected systems rank or directly check newly generated candidates.
6. **Count verified solutions.** Every system receives the same total time, including generation, monitoring, data transfers and Lean verification.

~~~mermaid
flowchart LR
    A[Lean problem] --> B[Gemma generates candidates]
    B --> C[Monitor ranks candidates]
    C --> D[Lean checks candidates]
    D --> E[Verified solutions within the same budget]
~~~

The monitor may see the problem, a completed candidate and selected internal activations. It never sees Lean's verdict, a reference proof or future attempts. The independent statistical unit is the problem, not an individual token or candidate.

## What is being compared

The internal methods include a regularized static activation probe, a Motion-only monitor and the full [Three-Reader method](https://arxiv.org/abs/2608.05660), which models motion, region and direction in a residual-stream trajectory.

They are compared against:

- generation order and immediate checking;
- summed and length-normalized token likelihood;
- text features such as TF-IDF and candidate length;
- the strongest non-internal selector chosen on validation data.

Label shuffles, length controls, component ablations and transfer tests are included to reveal shortcuts and fragile gains.

## Why this matters

Interpretability results are often evaluated by whether an internal state can be decoded. That is useful, but it does not establish that the signal improves a real decision.

This study adds an operational test: after accounting for the monitor's own cost, does it help find more externally verified solutions?

A positive result would support a narrow but important claim: internal activations can help allocate verification effort among solutions the model has already generated. A negative result would also be informative by showing that decodability did not translate into practical benefit under the tested conditions.

## Mechanistic follow-up

Circuit tracing is a gated follow-up, not a substitute for the main result. If an internal monitor proves useful on unseen problems, Anthropic's [open-source circuit-tracing tools](https://www.anthropic.com/research/open-source-circuit-tracing) can be applied offline to matched valid, invalid and difficult examples from the training and validation sets.

The follow-up would ask:

- Which feature paths does the monitor rely on?
- Do those paths reflect proof-relevant computation or shortcuts such as length and formatting?
- Do perturbations of the proposed mechanism change the original Gemma model in the predicted direction?
- Do those effects survive evaluation on fresh held-out examples?

Full attribution graphs will not run for every candidate. They are too expensive for the live selection loop and capture only part of the original computation. Graphs generate hypotheses; causal tests in the original model must evaluate them. Circuit evidence cannot rescue a negative primary experiment.

## What this study cannot establish

Even a positive result would not show that the monitor creates reasoning ability or finds a proof Gemma never generated. It would show better selection among existing candidates.

The study also does not claim:

- online error detection during generation;
- general metacognition or a universal correctness signal;
- hallucination or jailbreak detection;
- validity beyond the formal statement supplied to Lean;
- transfer to larger models or non-mathematical domains.

Those are separate research questions.

## Current status

The protocol and local implementation are being checked. No result from this study has been opened or reported.

The first empirical milestone is a development-only feasibility run: 32 tasks with four natural Gemma candidates each. The larger study proceeds only if this run produces enough valid candidates, invalid candidates and tasks containing both outcomes for a meaningful comparison.

The project is designed around an 8 GB RAM laptop and free Colab access where available. The public release will include code, frozen configurations, tests, provenance, runtime measurements, protocol amendments and unsuccessful or inconclusive findings.

## License

Available under the [PolyForm Noncommercial License 1.0.0](LICENSE.md). Noncommercial research, experimentation and study are permitted under its terms. Commercial use requires separate permission. This is a source-available license.

Required Notice: Copyright 2026 Friedrich Reichelt.

The opening quotation is presented as dialogue from *The Imitation Game* and not as a verified historical quotation by Alan Turing.
