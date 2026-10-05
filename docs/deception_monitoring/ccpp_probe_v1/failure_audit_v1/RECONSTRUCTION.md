# What the current experiment measures

1. The frozen Llama-3.2-3B-Instruct responses were retained. No answer was regenerated during this audit.
2. User-confirmed, AI-assisted ratings of 371 roleplays were split by the existing normalized scenario/question groups. Ambiguous cases remained outside binary fitting and ranking metrics.
3. Two linear all-layer probes were trained on 169 binary training responses: 119 deceptive and 50 honest. Epoch selection used 58 binary validation responses.
4. The probe receives 28 layers times 3,072 features, or 86,016 features per captured token. Training-only scaling is shared by the two probes.
5. Frozen token scores were smoothed with the original gap-reset EMA. A response's score is its maximum smoothed token score.
6. The cutoff was fixed at the 99th percentile of 1,000 ordinary calibration responses. Flags use strict `score > cutoff`.
7. Evaluation contains 32 deceptive, 21 honest and 22 ambiguous roleplays, plus 1,000 ordinary responses. Ordinary responses were not individually certified honest.

The score-file audit verifies the closed calculation. A separate source audit must reproduce each raw score from its original activation array and frozen weights.

## Relation to the papers

The deception paper studies larger models and multiple elicitation/transfer settings. Its rubric concerns deceptive behavior given scenario evidence; a false statement alone does not establish strategic intent. Our smaller-model, user-reviewed cohort is not interchangeable with its cohort or prevalence.

The Constitutional Classifiers++ paper provides the SWiM idea and examines a broader, context-aware classifier cascade. Our hard-label roleplay probe is an adaptation, not a reproduction of its complete data, soft-label supervision or cascade. The frozen plan also documents which context positions were captured. A score on a completed response is offline detection, not demonstrated live prevention.

Sources: [deception paper](https://arxiv.org/html/2502.03407v1), [Constitutional Classifiers++](https://arxiv.org/html/2601.04603v1).
