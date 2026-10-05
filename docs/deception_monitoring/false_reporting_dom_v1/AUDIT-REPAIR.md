# Safe audit compatibility repair

On 2026-10-04, all 456 captures and the raw-method analysis completed. The original audit then stopped because the TF-IDF feature-name array was saved with NumPy's object dtype. `allow_pickle=False` correctly rejected that array. This was an artifact-serialization defect, not a failed detection result.

The original kit, frozen source files, capture receipts, heads, continuous scores, selections and results remain unchanged. We did not rerun capture or fitting and did not enable loading pickles.

The separate `scripts/audit_false_reporting_text_vocab_v1.py` adapter reconstructs each vocabulary from training text alone using the registered unigram/bigram TF-IDF recipe. Before supplying a safe Unicode array to the original auditor, it requires that the reconstructed vocabulary serialize to exactly the bytes of the frozen `vocabulary.npy` member. A different vocabulary or an unexpected object payload fails closed. All other NPZ fields still use `allow_pickle=False`.

This changes only how the auditor reads the known string field. The original auditor still independently checks capture hashes, directions, validation selection, text and activation projections, held-out scores, metrics and cutoffs. The adapter writes a separate hash-bound receipt and is included in the private result archive.

Local regression tests cover unchanged artifact bytes, mismatched vocabularies, Unicode vocabularies, prohibited object weights, and a malicious pickle that must never execute. Five tests passed before uploading the adapter. Adapter SHA256: `a99c87384b702811eb6cc416d9d71e3f32f29568fa221fc2528864368bbedf3b`.

This operational repair neither changes the scientific protocol nor repairs any older study's failed audit. The result report must state whether the real repaired audit and the independent local replay actually passed.
