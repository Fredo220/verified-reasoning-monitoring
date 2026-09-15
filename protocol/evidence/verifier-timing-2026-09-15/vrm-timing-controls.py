"""Bounded known-fixture runtime controls only; no model candidates."""
import hashlib
import json
from pathlib import Path
import time
from vrm import lean

output = Path("/private/tmp/vrm-timing-controls-20260915.json")
cases = json.loads(Path("/private/tmp/vrm-real-verifier-20260914/cases-c.json").read_text())
backend = lean.LeanDojoBackend(
    execution_mode="docker",
    image="sha256:0c1ed089532fdb118749ec6033e634282344766c923c57738f82ee07b62ce21c",
    cache_dir="/private/tmp/vrm-mathlib4-official",
    cache_sha256=cases["valid"]["task"]["verifier"]["cache_sha256"],
    landrun_sha256="177fa7db952b2542135c373474c7c5263f8a0607e68fe22fa5fbcc4fae5a320b",
)
record = {"scientific_outcome": False,
          "purpose": "infrastructure controls; CPU alternative is not an adopted runtime",
          "source_sha256": hashlib.sha256(Path(lean.__file__).read_bytes()).hexdigest(),
          "preflight": backend.preflight(), "runs": []}
if not record["preflight"]["ready"]:
    raise RuntimeError(record)
original = backend._command
for cpus, label, timeout in [("1", "valid", 180), ("2", "valid", 180),
                              ("1", "valid", 5), ("1", "invalid", 180)]:
    def command(name):
        command = original(name)
        command[command.index("--cpus=1")] = "--cpus=" + cpus
        return command
    backend._command = command
    case = cases[label]
    result = backend.verify(case["task"], case["proof"], timeout)
    record["runs"].append({"cpus": cpus, "case": label, "timeout_s": timeout, "result": result})
    output.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"cpus": cpus, "case": label, "timeout_s": timeout,
                      "status": result["status"], "elapsed_s": result["elapsed_s"]}), flush=True)
record["post_cache_sha256"] = lean.cache_digest(backend.cache_dir)
record["cache_unchanged"] = record["post_cache_sha256"] == backend.cache_sha256
output.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"cache_unchanged": record["cache_unchanged"], "path": str(output)}), flush=True)
