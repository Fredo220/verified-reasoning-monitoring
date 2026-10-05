# Trajectory follow-up: pre-target resource amendment

Recorded after one opened-candidate trace replay and before reserve candidate
generation, reserve verdicts, monitor fitting or target predictions. The
original protocol and manifest remain immutable. This amendment changes only
the neural-reader implementation and its training sampling, not the target
population, labels, primary comparator or primary endpoint.

The local 8-GB Mac replayed 18 answer tokens over all 28 layers in 1.43 s.
A 100-token, two-candidate, full-sequence Three-Reader backward pass took
8.14 s on CPU and 5.94 s on MPS, with MPS forward taking 4.75 s. Training
all within-task pass/fail pairs for three seeds, two models and seven epochs
would exceed the available free-compute window. This is a measured compute
constraint, not an observed target result.

Both Motion-only and combined readers will therefore receive **all recorded
answer tokens** through deterministic, contiguous, approximately equal-sized
token windows. Each window averages its tokens at each of the 28 post-block
layers; the Motion LSTM processes the 27 adjacent-layer differences for each
of eight windows, in token-major/depth-minor order. If a candidate has fewer
than eight tokens, use one window per token. No token is discarded from the
raw saved trace. Region and Direction keep their existing final-64-token
summaries. This is a reduced Three-Reader adaptation, not a replication of
the paper's unpooled Motion stream; it may miss brief local errors.

Each training epoch draws one pass/fail pair per mixed training task using a
fixed seed and task-specific deterministic shuffle of all possible pairs.
Pairs rotate across epochs. Validation pairwise loss always uses **all**
available pass/fail pairs. The previously registered three seeds, seven-epoch
maximum and two-epoch patience remain. No target labels may choose pooling,
pair schedule or checkpoints. The unpooled class remains available for
contract tests but is not a tested study arm.

## Validation tie-break implementation correction

The reused non-internal helper breaks equal validation pairwise ranks by
method name. The registered protocol instead specifies validation log-loss.
This was found before reserve generation or labels. A separate immutable
selection record therefore applies the registered rule to text and to
train-fitted, C=1 logistic calibrations of sum/mean log-likelihood. Calibration
changes no within-task rank; it makes log-loss comparable. The original helper
pickle remains archived. On the opened validation tasks, text and mean
log-likelihood both rank 0.8889; text log-loss is 0.4814 versus 0.6363 for
task-weighted, calibrated mean log-likelihood. The registered tie-break selects text. No
target data informed this correction.
