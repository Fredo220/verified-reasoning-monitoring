# Unresolved questions

1. **Which original capture failed the strict projection oracle?** All 32 manageable local captures pass. The original full run failed after its 300-check progress message; it did not print the failing ID. Rounding is plausible but has not been established for that record.
2. **Do all remaining source captures reproduce the scores?** 2,041 are absent locally and two are deferred for memory safety. This is a private-storage access/resource blocker, not evidence that those captures are defective.
3. **Can the 3B model extract the relevant scenario facts?** No fresh matched comprehension test has been executed. A missed probe flag does not answer this question. The requested bounded diagnostic is awaiting permission.
4. **How accurate are the full behavioral labels?** Separate AI rubric review identifies boundary cases but is not independent human ground truth. Frozen labels remain unchanged. Intent is not established by a false statement alone.
5. **Does lower-cutoff recall transfer?** The observed trade-off is on already opened responses. Test a frozen recall-first policy on new scenario families before calling it an improvement.
6. **Do training size, context masks or supervision explain the misses?** Validation losses suggest poor logit calibration/generalization, but controlled comparisons are needed to identify a cause. Ordinary-control padding differs from roleplay padding; no causal masking ablation has been run.

The investigation can report supported individual findings without claiming that these questions or the original end-to-end audit are complete.
