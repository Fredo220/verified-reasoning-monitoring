# Verifier repair and approved format diagnostic

Historical checkpoint, superseded by the [completed development diagnostic](development_outcome_2026-09-16.md).
The pending permission and execution statements below describe that earlier state.

**Status: partial repair; not ready for a scientific restart.** No new model
outputs were generated. The original 128-candidate run and its verdicts remain
unchanged. H1-H3 are still unopened.

## What is fixed

Two benchmark records contain theorem names with namespaces that had already
closed in the pinned Lean source. The verifier now resolves only these two
source-identified records to their actual declarations:

| Benchmark name | Comparator name |
| --- | --- |
| `LinearOrder.LinearLocallyFiniteOrder.toZ_nonneg` | `toZ_nonneg` |
| `Finset.Multiset.mem_sup` | `Multiset.mem_sup` |

The correction requires the exact repository commit, file path and source
hash. It changes neither the public task nor the model prompt, and does not
guess names for other tasks. Both reference proofs passed in two real Linux
acceptance attempts. The final implementation retains the original descriptor
limit of 256; these repair acceptance attempts used the diagnostic limits below,
so they are not a complete live acceptance of the final configuration.

The owner also approved a separate, post-hoc format analysis. Its implemented
rule removes exactly one complete outer `lean` Markdown fence. It preserves
the original output and every byte inside the fence. Incomplete blocks,
multiple blocks, explanations and other fence languages are not repaired.
The analysis has its own identity and cannot inherit raw-policy verdicts or
automatically open H1-H3, even if its descriptive yield counts pass.

## What the saved outputs tell us so far

The format-only check was run on all 128 saved outputs and independently
cross-checked with a regular-expression implementation:

- 41 outputs match the exact removable-fence rule.
- 54 outputs satisfy the verifier's proof framing after that operation.
- 74 still fail the proof-framing rule.

These are **format counts, not valid-proof counts**. One of the 41 unwrapped
blocks still fails proof framing. The previous 114 format rejections must not
be interpreted as 114 complete, otherwise valid proofs inside removable fences.
No missing proof text was filled in and no model answer was resampled.

## What still fails

The official reference for `ProbabilityTheory.gammaPDF_of_neg` still fails
inside the proof exporter, independently of any model answer.

| Diagnostic runtime | Corrected references | Six proof/security controls | Gamma reference |
| --- | --- | --- | --- |
| Host-mounted cache, descriptor limit 2,048 | 2/2 pass | 6/6 pass | Infrastructure error |
| Host-mounted cache, descriptor limit 16,384 | 2/2 pass | 6/6 pass | Infrastructure error |
| Existing identical-content Linux cache volume, limit 16,384 | Not rerun | Not rerun | Timeout at 120 s |

The six controls cover a valid proof, an invalid proof, self-reference,
`sorry`, an unauthorized axiom and a sandbox escape. Each full nine-case
acceptance attempt failed honestly at 8/9. Cache hashes remained unchanged.

Raising the descriptor limit did **not** fix the reported "Too many open files"
error. Sampled exporter processes held at most 13 descriptors under the 16,384
limit; this sampling does not rule out brief unobserved spikes. A different
cache transport changed the observed failure to a timeout, not to an accepted
proof. The root cause is therefore unresolved. The production limit was
restored to 256; no isolation or verifier checks were disabled.

The volume control took 121.13 seconds including timeout cleanup. It used an
existing volume, not a new cache copy. No GPU time was allocated for this work.

## Verification and next action

The local suite reports **273 passed, 7 skipped**. Unit tests cover exact
format handling, unchanged receipts, resume, pinned lookup corrections and
the prohibition on automatic H1-H3 release. Skipped integration tests are not
counted as live runs; the real Linux receipts above are separate evidence.

The full 128-output post-hoc **Lean re-verification has not run**. Its format
precheck is complete, but the instrument acceptance is not. A question has
been sent for permission to diagnose only the known Gamma reference for up to
300 seconds. That diagnostic would not change the 120-second candidate limit
or the five/30-second H3 budgets. It must not be started without that approval.

After resolving this instrument failure, run the already implemented separate
format diagnostic on the saved outputs, audit the actual verdicts, and report
the result without rewriting the original outcome. Passing an offline yield
check would still not establish feasibility under H3's time budget.

Evidence: [repair manifest](../protocol/evidence/verifier-repair-2026-09-16/manifest.json),
[approval](../protocol/development_format_diagnostic_2026-09-16.json),
[original run](development_smoke_2026-09-16.md).
