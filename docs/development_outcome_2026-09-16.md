# Development outcome: not ready for monitor evaluation

**The saved-candidate diagnostic is complete. H1, H2 and H3 were not run.**
The existing Gemma/Lean setup did not supply the verified proof candidates
needed to train and evaluate a monitor. This is a feasibility finding about
this setup, not a finding that internal monitoring fails.

## The result in plain language

We reused all 128 original answers from 32 development tasks. We did not ask
the model to try again, add reference proofs to its answers, change the
corpus, or lower the success thresholds. A separately approved diagnostic
removed only a complete outer Lean Markdown fence. Every byte inside the
fence and every original generation receipt was preserved.

After the full diagnostic and five targeted metadata rechecks:

| Outcome | Candidates | What it means |
| --- | ---: | --- |
| Verified valid | 0 | No model answer was accepted by the complete verifier. |
| Format rejected | 74 | The answer still did not meet the proof-input format. |
| Comparator rejected | 36 | The answer failed checking and the reference diagnostic passed. |
| Timeout | 14 | Checking did not finish within 120 seconds; correctness is unresolved. |
| Infrastructure error | 4 | The reference comparison also failed; correctness is unresolved. |
| Total | 128 | No candidate was dropped. |

There are zero tasks with a confirmed valid and invalid candidate pair.
The unchanged requirement is at least 20 valid candidates, 20 invalid
candidates, and eight mixed tasks.

**Even if all 18 unresolved answers were valid, the batch would still fall
short of the 20-valid-candidate requirement.** This is a deterministic upper
bound, not a statistical confidence interval or an estimate of Gemma's
general mathematical ability. It explains why more repairs to the remaining
verdicts cannot make this particular batch meet the frozen yield requirement.

The machine artifacts retain `scientific_gate_evaluated: false`: this was a
post-hoc diagnostic, not a replacement confirmatory run. Its descriptive
counts and upper bound justify stopping this development path. They do not
change the original failed run or authorize H1-H3.

## What was actually done

1. Tested the already failing Gamma reference once with the authorized
   300-second diagnostic cap. It still timed out, returning after 302.10
   seconds including cleanup. Candidate limits stayed at 120 seconds.
2. Used the existing, identical-content Linux cache volume read-only. Two
   corrected reference proofs and six proof/security controls passed on the
   actual 256-descriptor runtime. Network, filesystem, memory, process and
   kernel checks were retained. This was not full instrument acceptance:
   the expensive Gamma reference was still unresolved.
3. Rechecked all 128 saved answers. The first complete post-hoc inventory was
   74 format rejections, 32 Comparator rejections, 14 timeouts and eight
   infrastructure errors, with no confirmed valid answer.
4. Read the pinned Mathlib source for four newly discovered declaration-name
   defects. Regression tests failed before these source-hash-bound corrections
   and passed afterward. Public prompts and proof text were not changed.
5. Checked the four corrected references and rechecked only the five affected
   answers under a separate identity. Three references passed; one still failed
   Comparator. Four answers became confirmed rejections and one remained an
   infrastructure error. The earlier 128-row inventory remains immutable.
6. Independently audited receipt hashes, original text, exact fence removal,
   activation-file hashes, counts, control outcomes, and cache pre/post checks.

A setup-only metadata-wrapper error occurred before the targeted reference
checks. It was corrected using the existing population-validation helper.
Its preflight receipts are retained separately; it generated no candidate or
reference verdicts and is not counted as a scientific run.

## What we learned, and what remains unknown

- **Formatting is only part of the problem.** Of 114 initially fenced outputs,
  only 41 matched the exact removable-fence rule. One still failed proof
  framing after unwrapping. The resulting 54 frame-eligible answers were not
  54 valid proofs.
- **The output cap is a plausible limitation.** 61 answers reached 64 tokens.
  Hitting the cap alone does not prove truncation or that more tokens would
  produce a correct proof. No longer answers were sampled in this analysis.
- **Some proof content is genuinely incompatible with the checker.** Observed
  errors include unknown tactics and malformed `rewrite` syntax. Those were
  not repaired by hand.
- **Some verifier problems remain.** Three candidates still encounter a
  reference-constant mismatch involving `SemidirectProduct.ext`; one encounters
  a mismatch involving `BoxIntegral.Prepartition.split._proof_6`. These are
  not counted as model mistakes. Fourteen further verdicts remain timeouts.
- **The utility budget is still unmet.** Reference acceptance and this offline
  120-second diagnostic do not establish the frozen five-second check and
  30-second end-to-end H3 schedule. Neither a bigger timeout nor a manual
  Colab-to-laptop handoff can be presented as within-budget H3 performance.

The post-hoc comparison includes format handling, metadata corrections and a
different cache transport. It does not isolate the effect of any single change.
None of these observations establishes or refutes H1, H2 or H3.

## Resources and verification

No new model generation, GPU allocation or paid service was used in this
continuation. The original Colab generation and earlier failed checks remain
reported in their own records.

| Measured stage | Wall time |
| --- | ---: |
| Full 128-answer post-hoc verification | 3,478.40 s |
| Five targeted candidate rechecks | 382.45 s |
| Four new reference checks | 186.91 s |
| Eight initial reference/security controls | 268.62 s |
| One 300-second Gamma diagnostic, including cleanup | 302.10 s |
| Six recorded pre/postflight checks, including the failed setup | 261.84 s |

These are stage wall times, not a claim about pure CPU time or total human
elapsed time. They exclude editing, unit tests and report preparation.
Cleanup after a timeout is included rather than hidden.

Final local suite: **277 passed, 7 skipped**. Skipped integrations are not
claimed as executions. The real Docker receipts are separate evidence.
No protected monitor training, validation selection or test evaluation occurred.

## What should happen next

Do not launch the large study or keep resampling this batch until it passes.
Do not lower the gate to make the current data appear sufficient.

The next useful step would be one explicitly approved, bounded development
amendment addressing two prerequisites: a candidate-generation setup that
actually produces complete Lean proofs, and a verifier placement/budget that
can support a fair utility test. A Lean-specialized generator or a changed
prompt/output allowance would be new development conditions, not repairs to
these saved answers. Their usefulness remains untested here.

Reuse the existing corpus, generation/activation storage, authentication,
provenance, tests and analysis infrastructure. Keep this completed batch as
evidence. Only after a new condition passes a prespecified feasibility check
should it be considered for H1-H3. A successful study under a later condition
would not retroactively turn this batch into a success.

## Evidence

- [Original raw-policy report](development_smoke_2026-09-16.md)
- [Earlier instrument-repair checkpoint](verifier_repair_2026-09-16.md)
- [Full post-hoc audit](../protocol/evidence/development-format-check-2026-09-16/summary.json)
- [Full post-hoc manifest](../protocol/evidence/development-format-check-2026-09-16/manifest.json)
- [Five-candidate recheck audit](../protocol/evidence/development-name-recheck-2026-09-16/summary.json)
- [Targeted recheck manifest](../protocol/evidence/development-name-recheck-2026-09-16/manifest.json)

The two evidence directories include execution/audit scripts, worker-source
snapshots and hash-bound receipts. The large original activation archive stays
local. No commit, push or publication was performed in this continuation.
