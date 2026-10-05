# Real development run: September 16, 2026

## What happened

We generated all **128 natural candidates for the frozen 32 development
problems**, saved their activations, and completed a diagnostic inventory of
every unchanged answer. No candidate was regenerated to improve the result.

**This setup is not ready for H1-H3.** Most answers used Markdown code blocks,
which the owner explicitly chose not to strip. The local verifier also exposed
three infrastructure errors and three timeouts. These are development findings,
not a test of whether internal monitors improve proof selection.

## Results

| Outcome on the unchanged raw answer | Candidates | Interpretation |
| --- | ---: | --- |
| Rejected at the proof-format boundary | 114 | All begin with Markdown fences; their enclosed proofs were not checked. |
| Rejected by Comparator | 8 | Rejected candidates with a successful pinned-original diagnostic check. |
| Timed out | 3 | No completed validity verdict; not counted as invalid proofs. |
| Infrastructure error | 3 | The verifier could not establish a trustworthy verdict. |
| Confirmed valid | 0 | No candidate obtained an acceptance receipt in this run. |
| Total | 128 | 32 tasks, four candidates each. |

The machine-level `invalid` count is 122: 114 format rejections plus eight
Comparator rejections. It must not be described as 122 mathematically incorrect
proofs. There were no observed tasks containing both a valid and invalid
candidate. Also, 61 outputs reached the 64-token limit; reaching that limit
alone does not prove the proof was incomplete.

The unchanged development requirements are at least 20 valid candidates,
20 invalid candidates, and eight mixed tasks. Under the approved raw-output
policy, even accepting all 14 non-format-rejected candidates would leave fewer
than 20 valid candidates. This batch therefore cannot release H1-H3 under that
policy, independently of the unresolved verifier errors.

### Primary stop and diagnostic continuation are different

The primary verifier stopped at candidate 16 with `infrastructure_error`.
It recorded 15 invalid results and one infrastructure failure, then preserved
its stop receipt with `scientific_gate_evaluated: false`.

A separate **post-stop diagnostic continuation** reused those 16 verdicts
unchanged and inspected the remaining 112 candidates. It did not resample,
repair outputs, change the verifier, or replace the primary receipt. Its status
is `diagnostic_completed`, not `feasibility_pass`. Its count-based feasibility
summary has `passed: false`, while both `scientific_gate_evaluated` and
`continue_to_H1_H3` remain false. The continuation is an instrument audit, not
a successful completion of the registered scientific smoke.

## What was preserved

- The existing public request, task corpus, private-verifier boundary and
  sampling settings were unchanged. Only the open development split was used.
- The pinned `google/gemma-2-2b-it` revision was
  `299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8`, with FP16 on a free Colab T4.
- The previously observed first candidate was retained byte-for-byte; 127
  additional candidates were generated. All 128 returned activation records
  passed the handoff's hash and shape checks.
- The user approved a separate development allowance of one new GPU hour and
  120 seconds per local verification. The five/30-second H1-H3 budgets were not
  amended. This offline split execution is not a prospective utility test.
- Raw answers, token IDs, costs and activation hashes are retained. No Markdown
  fences were removed and no generated proof was rewritten.
- Both local preflights passed. Both postflight full-cache hashes matched the
  same pinned cache. This establishes those integrity checks, not universal
  verifier compatibility across all tasks.

See the [approval record](../protocol/development_split_smoke_2026-09-16.json)
and [evidence manifest](../protocol/evidence/development-smoke-2026-09-16/manifest.json).

## Errors and limitations

**Controller ordering error, corrected before candidate verification.**
The first local invocation requested the verifier identity before running its
mandatory preflight. It failed before checking a candidate. The original
traceback is retained. A regression test now exercises a backend that withholds
its identity until preflight; the ordering was corrected without regenerating
any model output.

**Two theorem lookup failures.**
Comparator compiled the pinned original but could not export these requested
names: `LinearOrder.LinearLocallyFiniteOrder.toZ_nonneg` and
`Finset.Multiset.mem_sup`. These observed lookup failures require a trusted check
of the verifier-only declaration metadata. They are not evidence that the
model's candidate proofs are wrong. No names were patched in this run.

**One file-descriptor failure.**
The pinned-original diagnostic for `ProbabilityTheory.gammaPDF_of_neg` failed
with `Too many open files`. The container currently caps open descriptors at
256. A narrowly bounded limit change needs its own sandbox acceptance check;
the error was not converted into an invalid label.

**Three timeouts.**
The 120-second deadline terminated verification. Measured wall times were
121.35, 121.75 and 123.39 seconds including process/container cleanup. This
overhead is counted, not hidden or treated as a successful within-budget check.
The existing verifier still does not establish five-second H3 readiness.

**No validity estimate for the enclosed fenced proofs.**
The raw-output choice makes this an interface-sensitive test. We cannot infer
that all fenced answers would fail Lean, nor that stripping the fences would
produce enough valid candidates. Zero acceptance receipts are not a general
claim that Gemma cannot reason or prove statements.

## Resource accounting

| Measurement | Observed value |
| --- | ---: |
| Generation for all 128 candidates | 237.24 s |
| Activation extraction for all 128 candidates | 9.57 s |
| Primary plus new diagnostic candidate verification, without double-counting reused verdicts | 1,217.59 s |
| Primary and diagnostic preflight | 44.07 s and 61.44 s |
| New Colab allocation, conservative UI-observed upper bound including setup, loading, idle time and download | 959 s (about 16 min) |
| Previous first-candidate session, separate conservative upper bound | 1,968 s |
| Known two-session allocation upper bound | 2,927 s (about 49 min) |
| New local activation archive | 557,198,482 bytes |

The session bounds are observations, not provider billing records or an account
of all historical project compute. Loading, transfers, security checks,
postflight hashing and controller work are not included in the candidate
generation/verification totals. No overall H3 speed claim is calculated from
these separate development timings. No paid compute was purchased. The new
runtime was deleted after download and local archive-hash verification.

## Evidence and reproducibility

The [manifest](../protocol/evidence/development-smoke-2026-09-16/manifest.json)
links all 128 task/index pairs to generation and activation hashes. The small
evidence package contains raw verdict rows, generation receipts, the unchanged
primary stop, the diagnostic summary, integrity checks, logs and exact
controller source snapshots. The exporter independently reconciled candidate
coverage, raw-text equality, receipt integrity, counts and postflight hashes.

The 557 MB activation archive remains local at
`~/Downloads/vrm-development-smoke.zip`, with SHA-256
`6dcb2cf4510c6b2b86ff9ba11588dbbea12b6e3beff6176f8fc0219b1a7f2ffd`.
It is not added to this result commit. The original one-candidate archive is
referenced separately in the manifest. Raw activation publication still needs
an explicit decision; without those local artifacts the Git evidence package
alone is not a complete activation-reanalysis release.

`python -m vrm.dev_smoke` is the narrow execution entry point. It retains the
original request, output policy, candidate identity and separate diagnostic
namespace. A completed inventory or a successful process exit must not be
mistaken for a scientific gate pass.

Final local verification: **257 tests passed, seven integration tests skipped**.
The skips are not presented as executed acceptance tests. Real preflight,
candidate-verification and postflight evidence is recorded separately. Unlazy's
local software checks passed, but its scientific smoke gate remains an explicit
handoff rather than being relabeled as complete.

## Smallest next step

1. Preserve this result and the saved candidates. Do not rebuild the corpus or
   spend another GPU session regenerating this batch.
2. Check the two declaration names against the pinned Lean environment and fix
   only independently verified metadata defects. Test a bounded descriptor
   limit repair against the sandbox controls. Reuse the affected saved answers
   under a new diagnostic identity and retain the original verdicts.
3. Keep raw scoring unchanged unless the owner explicitly approves an additional
   format-normalized analysis. Such an analysis can reuse these saved outputs,
   but must be reported separately as post hoc; it cannot overwrite this result
   or rewrite incomplete proofs. Even after approval, success is not assumed.
4. Resolve the candidate-yield and five-second runtime limitations before any
   protected monitor comparison. H1, H2 and H3 remain unanswered.

The practical outcome is a measured diagnosis of the current interface and
verifier, with real model artifacts available for targeted repairs. It is not
confirmation or refutation of the research hypothesis.
