"""Development-only diagnostic; never generates or scores model candidates."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import uuid

from vrm import lean

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
parser.add_argument("--cpus", default="1")
args = parser.parse_args()
case = json.loads(Path("/private/tmp/vrm-real-verifier-20260914/cases-c.json").read_text())["valid"]
backend = lean.LeanDojoBackend(
    execution_mode="docker",
    image="sha256:0c1ed089532fdb118749ec6033e634282344766c923c57738f82ee07b62ce21c",
    cache_dir="/private/tmp/vrm-mathlib4-official",
    cache_sha256=case["task"]["verifier"]["cache_sha256"],
    landrun_sha256="177fa7db952b2542135c373474c7c5263f8a0607e68fe22fa5fbcc4fae5a320b",
)
started = time.monotonic()
preflight = backend.preflight()
if not preflight["ready"]:
    raise RuntimeError(preflight)
instrumentation = '''
import threading
_profile_events = []
_profile_start = time.monotonic()
def _profile_wrap(name):
    original = globals()[name]
    def wrapped(*args, **kwargs):
        start = time.monotonic()
        try:
            return original(*args, **kwargs)
        finally:
            _profile_events.append({"phase": name, "start_s": start - _profile_start,
                                    "elapsed_s": time.monotonic() - start})
    globals()[name] = wrapped
for _name in ("_sandbox_check", "_check_cache", "_check_leandojo_install",
              "_check_comparator_source", "_check_landrun", "_target_sources",
              "_write_audit_project", "_run_comparator"):
    _profile_wrap(_name)
_original_worker = _worker
def _worker(request):
    stop = threading.Event()
    samples = []
    def sample():
        previous = None
        while not stop.is_set():
            commands = []
            for path in Path("/proc").glob("[0-9]*/cmdline"):
                try:
                    raw = path.read_bytes().replace(b"\\0", b" ").decode(errors="replace")
                    if raw and "python" not in raw and "landrun" not in raw:
                        commands.append(raw[:300])
                except OSError:
                    pass
            current = sorted(commands)
            if current != previous:
                samples.append({"at_s": time.monotonic() - _profile_start, "commands": current})
                previous = current
            stop.wait(.2)
    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    try:
        result = _original_worker(request)
        result["profile"] = _profile_events
        result["process_samples"] = samples
        return result
    finally:
        stop.set()
        thread.join()
'''
source = Path(lean.__file__).read_text()
instrumented = source.replace('if __name__ == "__main__":', instrumentation + '\nif __name__ == "__main__":')
original_command = backend._command
def command(name):
    command = original_command(name)
    command[-1] = instrumented
    command[command.index("--cpus=1")] = "--cpus=" + args.cpus
    return command
backend._command = command
result = backend.verify(case["task"], case["proof"], 180)
record = {"scientific_outcome": False, "purpose": "known-valid development infrastructure profiling",
          "cpus": args.cpus, "preflight": preflight, "result": result,
          "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
          "instrumentation_sha256": hashlib.sha256(instrumentation.encode()).hexdigest(),
          "elapsed_s": time.monotonic() - started}
output = Path(args.output)
output.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"path": str(output), "status": result["status"], "elapsed_s": result["elapsed_s"],
                  "phases": result["details"].get("observation", {}).get("profile")}))
