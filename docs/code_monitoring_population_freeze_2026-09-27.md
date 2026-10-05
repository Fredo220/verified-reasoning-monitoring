# Code-monitoring population freeze (2026-09-27)

This amendment was written after the open 32-task development smoke and before
any protected train, validation or test candidate was generated or labeled.
It changes no model, prompt, sampling rule, verifier, feature, metric or
analysis gate in `docs/code_monitoring_protocol.md`.

## Open development evidence

- Frozen public handoff manifest: `1a31453cb71346e0f030c91a083d4e386b9e25f9898e5a37ccdc79386b3b6f65`.
- Qwen2.5-Coder-1.5B-Instruct generated all 128 planned natural candidates
  (32 tasks x 4 samples) on a free Colab T4. Every completed receipt had an
  independently read-back, byte-identical Google Drive mirror.
- The downloaded 128-receipt archive and its Drive copy both hash to
  `d67109100b32d3caa4e6d1c804c0afb2861af0cc0f534755b260280f0cb411b1`.
- The pinned, isolated EvalPlus verifier returned 128 complete labels: 73
  `pass`, 43 `test_fail`, and 12 `extraction_fail`; no missing verdicts.
- There were 13 tasks with both outcomes among all candidates, and 9 with
  both outcomes among the 116 activation-scorable candidates. The 12
  extraction failures remain in all-candidate reporting.
- Measured generation and activation replay summed to 353.1 and 12.5 seconds
  respectively. Colab host RAM was about 4.1/12.7 GB while generating. Peak
  GPU memory was not measured and is not claimed. Colab startup, model loading,
  Drive I/O and local verification add wall time beyond these timings.

## Frozen population and operational choices

- Keep the exact model/tokenizer revision, FP16, prompt, four samples per
  task, temperature 0.7, top-p 0.95, extraction and activation positions.
  Keep the 4,096-token operational guard: all 128 development generations
  ended at EOS; none hit it.
- Allocate 144 train, 64 validation and 120 test **groups**, once, by the
  preregistered deterministic hash assignment and registered prompt-variant
  grouping. The actual public source gives 145, 65 and 122 tasks because
  grouped variants stay together. Eleven independent groups remain unused;
  14 task IDs are unassigned, and three variants of development tasks are
  excluded. No task was selected by its verifier result.
- Protected manifest SHA-256:
  `39f94d582471af971f80781b251dfd8418dba1d58f14e1066a24710fc6cfb7b1`.
  Source compressed and content hashes remain those in the config. The
  previous tentative 200/50/96 allocation exceeded the available 339
  independent protected groups, so it could not be used.
- On the open scorable mixed-task rate of 9/32, the 120-group test split has
  roughly 34 expected mixed tasks, above the registered 12-task minimum.
  This is a planning estimate, not a protected outcome or a power guarantee.
  The 64-group validation split similarly has roughly 18 expected mixed
  tasks; if a gate misses its required count, that component is not evaluable.
- The estimated additional GPU generation-plus-replay work is about one hour
  at the observed development rate, before model loading, backup, local
  verification or analysis. Free Colab availability is not guaranteed.
  Resume uses immutable per-candidate receipts and a Drive mirror; exhausted
  quota is an operational interruption, not a negative H1 result.

Train and validation can now be generated and labeled. The test split is
opened only once after model, baseline, control and threshold choices have
been frozen on train/validation. Negative and inconclusive outcomes remain
reportable without another corpus redesign.
