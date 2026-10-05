# Publication audit: what is ready, and what is not?

The score-level deception analysis is reproducible. The full activation-to-score audit is **not complete**, and a fresh generalization experiment has not been run. These are different levels of evidence.

## 1. Source verification

All 2,075 saved score pairs and their frozen input/probe identities are checked. The original raw projection audit logged 300 successful records before failing a numerical comparison. That log does not identify record 301 as the failure: any subsequent record before the next 100-record progress message could have failed.

We retrieved `alpaca-3646` through the connected Drive tool. It passes the original full-response reference and was already among the 32 locally checked captures, so retrieving it does not increase coverage.

A blockwise reader now checks large FP16 captures without allocating the full token-by-layer matrix. It preserves all tokens, all 28 layers, original FP32 normalization and the original tolerance `1e-4 + 1e-5 * abs(reference)`. The additional `alpaca-3653` (3,080 tokens), `alpaca-3664` (529 tokens) and `alpaca-3744` (318 tokens) comparisons pass in this diagnostic. Those successes do not explain or erase the original failure. Blockwise numerical replay is explicitly distinguished from rerunning the original full-response oracle.

Independent code review identified two audit defects: a consistently changed score/receipt pair was not tied to the historical score manifest in projection mode, and nonfinite normalization could evade failure counting. Both were repaired with negative regression tests. The first diagnostics are retained; stronger, separately versioned receipts bind historical hashes before and after streaming. These repairs affect the auditor, not detector weights, scores, labels or thresholds.

**Not established:** rounding as the cause of the original failure, model incapacity as the explanation for missed deception, or verification of every original source capture. The complete source-audit gate remains open.

### Resumable CPU audit

A separate wrapper saves one receipt per verified record directly to Drive and stops with a named failure and numerical diagnostic if the unchanged original oracle disagrees. Resume requires the same source, score, probe, code and runtime identities; it does not retrain or rescore the detector. Its [receipt ZIP](../../../artifacts/deception/focused-replication-v1/ccpp-probe-v1/publication-source-audit-v1/publication-source-audit-v1.zip) was retrieved privately on 2026-10-04. The run **stopped, not fully verified**: it verified 23 records in the prioritized historical failure interval, then stopped at calibration record `alpaca-3883`. This is not 23/2,075 records in ordinary order, and the number must not be added to earlier coverage without deduplicating identities.

The archive is 23,566 bytes, SHA-256 `237041c0ad076aaa9557ecfbca31b7505ce46ab32289adf26f3f10d3439d5c92`. Local checks verified its CRC, safe paths, all 23 receipt identities, the named failure, the unchanged script/probe/design hashes, and its binding to all 2,075 historical score/receipt pairs. This verifies the retrieved evidence package, not every raw capture. The summary records zero new model calls and unchanged tolerances.

At `alpaca-3883`, one CC++-style token comparison has absolute error `0.00010825596`, exceeding its original tolerance `0.00010193981`. The all-layer mean-BCE readout passes its tolerance on that same capture. The diagnostic reports that CPU FP32 replay is not bit-identical to the saved FP32 scores. Numerical cancellation/reduction order is a plausible explanation, not an established cause: the failed capture and original computation backend still require a decisive replay. Do not loosen the old gate or interpret this numerical mismatch as evidence about model understanding, deception labels or detector recall. The full source-audit gate remains open.

The private-download fallback encountered an expired rclone token, a shared OAuth-project quota error and unavailable in-app browser control. The temporary authentication helper initially changed the wrong platform's timeout; its macOS path was corrected, without changing the installed tool. After the user signed in, the isolated browser's visible account label verified `frederic.reichelt@gmail.com`, and the exact ZIP was downloaded from its study folder. Temporary cookie exports were deleted. These operational failures did not require restarting the Colab study or changing scientific results.

## 2. Layers 8 and 22, without 14

Yes: the earlier fixed grid includes max-fusion of layer-8 and layer-22 scores without layer 14. We independently replayed its cutoffs and case-level flags, alongside each single layer, three-head fusion and the trained 8/14/22 concatenation head: 24 settings across four fixed calibration allowances.

| Calibration allowance | 8+22 deceptive /32 | 8+22 honest alerts /21 | Layer 22 deceptive /32 | Layer 22 honest alerts /21 |
| --- | ---: | ---: | ---: | ---: |
| 1% | 16 | 5 | 22 | 2 |
| 2% | 19 | 7 | 25 | 2 |
| 5% | 28 | 13 | 26 | 4 |
| 10% | 28 | 15 | 29 | 6 |

The exact comparisons are in `layer-comparison.json`. At 5%, the pair catches two more deceptive responses than layer 22 but creates nine more honest alerts. Elsewhere it catches fewer. This does not support dropping layer 14 as a general improvement.

**Fusion is not concatenation:** fusion combines separately trained probe scores. A jointly trained two-layer 8+22 concatenation probe has not been run. Another fitted configuration on these opened cases would remain exploratory, not resolve generalization.

## 3. Lightweight reproduction

The [release instructions](RELEASE_README.md) explain a small package that contains derived scores, complete 514-setting results, the figure, layer comparison, source attribution, the existing project license and a hash manifest. Its standard-library runner reproduces normalization, thresholds, alert counts, case flags and single-head/length-control AUROCs without model weights, a GPU, private responses or API credentials.

Bootstrap intervals and permutations remain in the complete result but are not rerun by this compact reproduction. The original analysis code provides that larger replay. Neither replay verifies model intent or human labels, and neither replaces a raw activation audit.

No upstream raw prompts/dataset code or private captures are bundled. The upstream repository's redistribution permission remains unresolved; linking it is not a license grant. The existing project license is not applied to third-party materials. Publication must use the explicit release allowlist rather than the entire dirty research worktree.

The second packaging revision rejects unexpected files and symlinks and binds the packaged result to one retained historically pinned byte snapshot. The first attempt/release is retained, not silently overwritten. The eight-member v2 ZIP is 288,000 bytes, SHA-256 `2a02e66786526755805ff7c64ede8499553e95305ea1e8c9cd03ddeb24fc1f06`. Its isolated standard-library replay verifies all 514 settings. The earlier local suite passed **875 tests, with 7 skipped**. A fresh run on 2026-10-04 in the restricted runtime passed **874 tests, with 8 skipped**: the Apple-MPS checkpoint test is unavailable there, alongside the seven opt-in Linux/Lean checks. The layer comparison and all 514 release settings also passed fresh replays. These software results do not validate the human labels or replace source verification. The runnable Unlazy gates remain unchecked until their separately requested checker approval is received; direct successful checks are not substituted for checker-bound evidence.

## 4. The next scientific test

Finish the source audit first. Then freeze one high-recall rule and its comparators before testing unused scenario families, with independent score-blind ratings. Preserve ambiguous responses and report separate alert counts; do not force labels to make recall improve.

The current high-recall candidate caught 31/32 with 6/21 honest alerts. It was selected from the inspected grid. A low false-alarm rate cannot be established from 21 honest responses, and a low miss rate cannot be established robustly from 32 deceptive responses. More tuning on these same cases would not remove either limitation.

If we specifically want to test whether misses come from the small model misunderstanding the scenario, that requires a separate comprehension diagnostic on new examples. A probe score alone cannot answer that question. Such a diagnostic is not a substitute for independently evaluating the detector.

## 5. What the reward-hacking paper contributes

The [versioned reward-hacking paper](https://arxiv.org/html/2609.19101v1#S3) uses matched hacking/honest activation spans and a difference-of-means direction, rather than Three-Reader. Honest failure and nonexecution are controls. Probe selection and final evaluation are separate. See the existing [method reconstruction](../../evidence-audits/reward-hacking-and-deception/RECONSTRUCTION.md) for source locations and missing specifications.

For our next deception study, the useful adaptation is to preserve the surrounding context while contrasting misleading reports with truthful reports of the same outcome. Evaluate a frozen high-recall probe alongside score-blind contextual review on fresh scenario families. An OR rule and a review-after-probe cascade are different systems: compare their misses, honest alerts and review workload separately. Reviewing alerts may discover rubric gaps, but cannot automatically turn the current false positives into correct detections. No reward-hacking model, new labels, new dataset or new empirical finding is introduced by this comparison.

## Publication claim

We found a useful-looking deception signal and some complementary readouts on this small roleplay sample. Higher recall can require more review. We have not established general-purpose deception detection, a causal mechanism, prevention, robust real-world transfer or parity with the larger models in the original studies.

The protected results remain unchanged. No response regeneration, new training or label modification is part of this audit. No commit, push or public upload is implied by preparation of the package. [Verification ledger](GATES.md).
