# Ordered DoM and CC++ comparison

Approved by the user's 2026-10-04 request to test both methodologies against prior methods. No new captures or outcomes have been opened. Run the raw DoM study and its audit first. Then use the same frozen reporting fixtures, captures and group assignments in a separate `ccpp-comparison/` namespace. Do not refit or rewrite any earlier study.

## What is comparable

The primary [DoM recipe](https://arxiv.org/html/2609.19101v1#S3.SS1) is the unnormalized difference of class token means. The [CC++ recipe](https://arxiv.org/html/2601.04603v1#S5.SS1) uses a learned linear map with bias, 16-token sliding-window means and softmax-weighted window BCE. Its inference EMA coefficient and optimizer settings are not fully specified there. Reuse our documented coefficient 2/17 and optimizer settings; do not describe these as author-supplied values.

Both are adapted to false verification reporting, not their original models, datasets or target behavior. The fixtures have explicit hard consistency labels; they do not provide the external Constitutional Classifier's soft labels. There is no external-classifier ensemble, probe-to-monitor cascade or claim of production jailbreak defense. Short reports use the available-token mean during training, as stated in CC++ section 5.1.

## Controlled, ordered comparisons

Freeze one single-layer site: the DoM-selected validation layer. Train four heads on exactly the same training captures, with no test-dependent choices:

1. `single_mean_bce`: optimized single-layer classifier, uniform token BCE.
2. `all_mean_bce`: same optimizer and objective over all 28 concatenated layers. Compare 2 against 1 to assess feature coverage.
3. `all_swim_uniform`: all layers, 16-token sliding-window logits, uniform window BCE. Compare 3 against 2 to assess training smoothing.
4. `all_swim_softmax`: all layers and sliding-window logits, softmax-weighted window BCE with temperature 1 and gradients through weights. Compare 4 against 3 to assess weighting.

Score each frozen head with mean raw logit, maximum raw logit and maximum causal EMA logit. Readout changes do not retrain the head. Compare raw maximum and EMA maximum from the same head to assess inference smoothing. Publish every registered result; no best-readout claim selected on test. Use the same validation-negative 90th-percentile cutoff rule as the DoM study, separately for each registered readout.

Reuse train-only StandardScaler, seed 11, zero-initialized weights and bias, one complete report per optimizer step, AdamW learning rate .001 and weight decay .01. At most ten epochs with early stopping after two non-improving validation-loss epochs. Save epoch weights, optimizer state, validation loss and source identities atomically. Freeze each chosen head and all cutoffs before scoring held-out rows. Fit one head and load one capture at a time, CPU only after the model is released.

After scoring, independently replay the concatenated dot products in FP64 using the saved FP32-normalized inputs. With u=2^-24 and gamma_d=d*u/(1-d*u), each token's forward error bound is (1+u)*gamma_d*sum_j(abs(x'_tj*w_j)) + u*abs(z_t) + 1e-12. Mean, maximum and EMA are bounded by the largest token bound because their weights are nonnegative and sum to one. Verify all selected head checksums, reconstruct cutoffs from validation only, and recalculate every condition count and interval. This new, pre-capture bound does not amend the failed source audit of the previous CC++ experiment.

Save and hash every validation readout before freezing selection. Replay its projection within the bound above, but reconstruct the exact frozen cutoff from the saved validation values, not a newly rounded local reduction. Held-out reported cutoffs must still equal the frozen values exactly. The raw DoM comparison likewise preserves hashed validation arrays for all internal and text comparators. Capture must run in a fresh CLI process; path and disk hashes alone cannot certify an already cached notebook module.

## Reporting limits

Compare these arms with raw single-layer DoM, newly fitted token logistic, the label null, both TF-IDF baselines and the visible consistency parser on the identical held-out rows. The prior natural-deception experiments get a separate context table, not a pooled ranking: they use different labels, masks, training populations and calibration sets, and their earlier source-projection audit remains incomplete.

Report recall and honest-failure/nonexecution/discussion false alarms, not only AUROC. Identifier-level intervals are conditional on one fixed task template; they do not measure semantic generalization. DoM-versus-optimized-head contrasts also change fitting and normalization, so only the matched four-head ablations isolate the named components. A good result on these fixtures is not evidence of intent, real cheating, prevention or a universally reliable monitor.
