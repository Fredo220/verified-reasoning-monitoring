# What two monitoring papers suggest for our next study

**Methodological guidance, 30 September 2026. Not a new result or an amendment
to the completed test.**

The fresh live study is [complete and inconclusive](streaming_live_result_2026-09-30.md).
Its 42 tasks are now opened data. These papers cannot justify changing its
weights, thresholds, primary checkpoint or interpretation after the fact.

## 1. Reward-hacking monitoring

[Monitoring and Discovering Reward Hacking with Internal Representations during
LLM Evaluations, v1](https://arxiv.org/html/2609.19101v1) builds difference-of-means
directions from matched synthetic hacking/honest interactions, scores token
activations, and selects probes separately from evaluation. Sections 3.1 and
4.1 compare detection at matched false-alarm rates and combine probes with text
monitors. Section 4.2 resamples continuations from retrospectively selected
high-scoring locations against length/position-matched controls. That is not
prospective detection of arbitrary code errors.

**Transfer we propose, not a reported finding:** use natural passing/failing
attempts at the same coding problem to learn a cheap contrastive direction.
Matched-task comparisons reduce the opportunity to learn task identity instead
of attempt quality. A future continuation experiment must choose its trigger
using only the available prefix, not the eventual peak of a completed trace.
Complementary monitors should earn their place through measured disagreements,
not merely be added together.

## 2. Strategic-deception probes

[Detecting Strategic Deception Using Linear Probes,
v1](https://arxiv.org/html/2502.03407v1) uses standardized activations and
regularized logistic regression (Section 3.1). It tests layer and token-pooling
choices in Appendix D. Sections 4.1 and 5 warn that a probe can respond to a
deception-related situation even when the response is honest; low false alarms
on unrelated chat do not imply equally low false alarms within that situation.

**Transfer we propose:** successful solutions to difficult coding tasks must be
negative controls. Compare a last-token readout with a small rolling window,
using training-derived normalization only. Calibrate alerts on representative
successful code, and report recall, false alarms and lead time alongside AUROC.
Whole-response pooling is unsuitable for a warning that must precede completion.

## The smallest useful follow-up

Our strongest prompt-only control already captures some task difficulty, while
the live monitor did not rank attempts better within the seven eligible mixed
tasks. The next question is therefore narrower:

> Does a live prefix contain information about this particular attempt's eventual
> test outcome, beyond what we knew from the problem before generation?

1. **Development only:** reuse opened traces to compare the current monitor,
   a task-balanced contrastive baseline and a regularized linear probe. At each
   registered prefix length, average passing and failing activations separately
   within each mixed training task, subtract those means, then average differences
   equally across tasks. Report the number of contributing tasks. Do not force
   balanced outcomes by inserting reference solutions or synthetic mistakes.
2. **Causal inputs:** fit any normalization, layer and rolling-window choice on
   training/validation tasks only. All features and trigger rules must use the
   current prefix. A final test label supervises eventual-outcome prediction; it
   does not identify the exact token where an error occurred.
3. **Fair evaluation:** retain the prompt forecast, text and likelihood controls.
   Report task-equal probability loss, within-task ranking and warning rates on
   the complete eligible population, including tasks with no passing attempt.
   Report short-output coverage rather than silently discarding it.
4. **New test:** freeze one selected configuration before collecting unused tasks,
   preferably with stronger private tests. Reusing the current 42 tasks can diagnose
   a weakness but cannot confirm an improvement. Fix and fault-test the documented
   staging-resume window before another collection.

This is a recommendation, not a newly approved frozen protocol. It requires no
new model, paid judge, SAE training, steering or full Three-Reader implementation.
Whether the direction transfers to natural code failures remains untested.

## Evidence boundary

The inspected sources were the two v1 HTML papers, including the relevant
methods, results and appendices. Their experiments were not reproduced here;
source code, checkpoints and supplements were not audited. The reward-hacking
appendix lists projected variants without enough inspected detail to treat our
implementation as an exact reproduction. Their models, labels and datasets
differ from ours. Published deception/hacking scores are not target accuracies
or evidence that the same representation exists in our 1.5B code model.
