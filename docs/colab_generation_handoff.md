# One-candidate Colab handoff

This path is generation-only in Colab and verification-only on the local
approved Docker backend. Do not provision Lean or run the old native-verifier
notebook cells on the rejected Colab kernel. The existing corpus is reused.

The owner approved one development candidate at 120 seconds per verification
and 180 seconds from generation start to completion, after model loading.
The implementation conservatively includes transfer/manual waiting and adds
a five-second clock guard. Clocks inconsistent by more than that require a
stop. This is not a prospective H3 measurement and does not approve larger
study budgets. See the [budget record](../protocol/development_probe_budget_2026-09-16.json).

## Colab

1. Connect a free T4 and record connection time. Setup/loading/idle time all
   count against one GPU hour. Read `HF_TOKEN` from Secrets, never code or chat.
2. Check out the reviewed exact branch commit in the existing notebook.
   Use Python 3.12 and the pinned `requirements-colab.txt`, then install the
   package with `--no-deps`. Do not silently reuse mismatched base packages.
3. Run `python -m vrm.cli auth-check`. Proceed only on success.
4. Run the command below. `GPU_CONNECTION_UNIX_TIME` must be the actual
   connection time or an earlier conservative bound, not model-load time.

```sh
python -m vrm.integration_probe generate \
  --request protocol/evidence/verifier-readiness-2026-09-16/public-request.json \
  --request-sha256 ca9a20453798dee9bff58482214f0f95046cf0149503aa3832e886aad5e81c12 \
  --gpu-started GPU_CONNECTION_UNIX_TIME \
  --output /content/vrm-integration-probe
```

Download `/content/vrm-integration-probe.zip` promptly. It contains only one
candidate, its activations, runtime identity and generation timing. No verifier
metadata is needed in Colab. Preserve interrupted/failed attempts. A completed
matching generation is reused, not regenerated for a better answer. Disconnect
the GPU and record its total allocation when it is no longer needed.

## Local verifier

Extract into a fresh directory after rejecting absolute paths, `..` paths,
symlinks and oversized members. Do not execute generated proof code outside
the approved verifier. Then run:

```sh
python -m vrm.integration_probe verify \
  --request protocol/evidence/verifier-readiness-2026-09-16/public-request.json \
  --request-sha256 ca9a20453798dee9bff58482214f0f95046cf0149503aa3832e886aad5e81c12 \
  --returns /path/to/extracted-return \
  --prepared-dir /private/tmp/vrm-prepared-v2 \
  --output /path/to/new-verification-receipt
```

The prepared corpus is independently validated. Only the corresponding local
verifier metadata is joined. `valid` and `invalid` are both useful engineering
outcomes; timeout and infrastructure error are not proof-correctness labels.
The original budgets in `configs/study.json` are deliberately unchanged.
Do not run the full smoke until its resource plan is separately resolved.
