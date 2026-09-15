"""One approved development candidate across Colab and the local verifier.

This is an offline engineering check, never the prospective H3 scheduler.
The original study/smoke budgets are deliberately untouched.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import time
import zipfile

from vrm.config import load_study_config
from vrm.core import canonical, digest
from vrm.engine import candidate_seed
from vrm.handoff import DevelopmentHandoff
from vrm.runtime import HFRunner
from vrm.workflow import _joined_task, _validate_population, _write_bytes_atomic


ACTIVE_SECONDS = 180.0
CHECK_SECONDS = 120.0
GPU_SECONDS = 3600.0
CLOCK_GUARD_SECONDS = 5.0


def generate(request, config, output, *, gpu_started, clock=time.time,
             runner_factory=HFRunner, source_commit=None):
    if request['config_sha256'] != config['config_sha256']:
        raise ValueError('handoff configuration mismatch')
    if any(request['model'][key] != config[key] for key in request['model']):
        raise ValueError('handoff model pins mismatch')
    root = Path(output)
    store = DevelopmentHandoff(root / 'candidates', request, expected_sha256=digest(request))
    task = request['tasks'][0]
    result_path = root / 'generation.json'
    if result_path.exists():
        previous = json.loads(result_path.read_text())
        if previous['request_sha256'] != digest(request) or store.read(task['task_id'], 0) is None:
            raise ValueError('inconsistent generation resume')
        return previous
    elapsed = clock() - gpu_started
    if not math.isfinite(elapsed) or not 0 <= elapsed < GPU_SECONDS:
        raise TimeoutError('GPU allocation budget unavailable or exhausted')
    _write_bytes_atomic(root / 'attempt.json', canonical({
        'request_sha256': digest(request), 'source_commit': source_commit,
        'gpu_started_unix_s': gpu_started, 'first_candidate_only': True,
    }))
    loading_started = clock()
    runner = runner_factory(config)
    started = clock()
    remaining = min(ACTIVE_SECONDS, GPU_SECONDS - (started - gpu_started))
    if remaining <= 0:
        raise TimeoutError('GPU allocation exhausted during loading')
    candidate = runner.generate(task, candidate_seed(task['task_id'], 0), remaining, capture=True)
    ended = clock()
    if candidate['deadline_exceeded'] or ended - gpu_started > GPU_SECONDS:
        _write_bytes_atomic(root / 'failure.json', canonical({
            'status': 'generation_budget_exhausted', 'request_sha256': digest(request),
            'gpu_allocated_s': ended - gpu_started, 'scientific_gate_evaluated': False,
        }))
        raise TimeoutError('generation exhausted the approved budget')
    store.write(task['task_id'], 0, candidate, runner.identity)
    receipt = {
        'request_sha256': digest(request), 'task_id': task['task_id'], 'candidate_index': 0,
        'source_commit': source_commit, 'status': 'generation_completed',
        'model_loading_s': started - loading_started,
        'candidate_started_unix_s': started, 'generated_unix_s': ended,
        'gpu_started_unix_s': gpu_started, 'gpu_allocated_through_generation_s': ended - gpu_started,
        'active_limit_s': ACTIVE_SECONDS, 'verifier_limit_s': CHECK_SECONDS,
        'prospective_h3': False, 'scientific_gate_evaluated': False,
    }
    _write_bytes_atomic(result_path, canonical(receipt))
    return receipt


def verify(request, verifier_rows, returns, backend, output, *, clock=time.time):
    root, out = Path(returns), Path(output)
    store = DevelopmentHandoff(root / 'candidates', request, expected_sha256=digest(request))
    public, private = _validate_population(request['tasks'], verifier_rows)[0]
    generation = json.loads((root / 'generation.json').read_text())
    if (generation['request_sha256'] != digest(request) or generation['task_id'] != public['task_id']
            or generation['candidate_index'] != 0 or generation['status'] != 'generation_completed'):
        raise ValueError('generation receipt mismatch')
    candidate = store.read(public['task_id'], 0)
    if candidate is None:
        raise ValueError('complete candidate required')
    identity = {'request_sha256': digest(request), 'generation_sha256': digest(generation),
                'candidate_receipt_sha256': digest(json.loads(next((root / 'candidates').glob('*/receipt.json')).read_text()))}
    _write_bytes_atomic(out / 'identity.json', canonical(identity))
    if (out / 'result.json').exists():
        return json.loads((out / 'result.json').read_text())
    arrived = clock()
    started, generated = generation['candidate_started_unix_s'], generation['generated_unix_s']
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in (started, generated)):
        raise ValueError('invalid remote clock receipt')
    if generated < started or arrived < generated - CLOCK_GUARD_SECONDS:
        raise ValueError('clock mismatch; cannot establish the budget')
    def charged():
        return max(candidate['elapsed_s'], clock() - started + CLOCK_GUARD_SECONDS)
    verification = None
    status = 'budget_exhausted'
    if charged() < ACTIVE_SECONDS:
        preflight = backend.preflight()
        _write_bytes_atomic(out / 'preflight.json', canonical(preflight))
        if not preflight.get('ready'):
            status = 'infrastructure_error'
        else:
            remaining = ACTIVE_SECONDS - charged()
            if remaining > 0:
                task = _joined_task(public, private, backend.identity)
                verification = backend.verify(task, candidate['text'], min(CHECK_SECONDS, remaining))
                status = ('integration_probe_completed' if verification['status'] in {'valid', 'invalid'}
                          and charged() <= ACTIVE_SECONDS else verification['status'])
                if charged() > ACTIVE_SECONDS:
                    status = 'budget_exhausted'
    result = {
        **identity, 'status': status, 'verification': verification,
        'charged_wall_s_including_clock_guard': charged(),
        'clock_guard_s': CLOCK_GUARD_SECONDS,
        'handoff_and_wait_s': max(0, arrived - generated),
        'active_limit_s': ACTIVE_SECONDS, 'verifier_limit_s': CHECK_SECONDS,
        'prospective_h3': False, 'scientific_gate_evaluated': False,
    }
    _write_bytes_atomic(out / 'result.json', canonical(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('generate', 'verify'))
    parser.add_argument('--request', required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--config', default='configs/study.json')
    parser.add_argument('--gpu-started', type=float)
    parser.add_argument('--returns')
    parser.add_argument('--prepared-dir')
    args = parser.parse_args()
    config = load_study_config(args.config)
    request = json.loads(Path(args.request).read_text())
    if digest(request) != args.request_sha256 or request['config_sha256'] != config['config_sha256']:
        raise ValueError('request or configuration hash mismatch')
    if args.mode == 'generate':
        if args.gpu_started is None:
            parser.error('--gpu-started is required for generation')
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        if subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip():
            raise ValueError('execution source checkout must be clean')
        result = generate(request, config, args.output, gpu_started=args.gpu_started, source_commit=head)
        root = Path(args.output)
        archive = root.with_suffix('.zip')
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED) as z:
            for path in sorted(root.rglob('*')):
                if path.is_file() and not any(p.startswith('.partial-') for p in path.parts):
                    z.write(path, path.relative_to(root))
        print(json.dumps({**result, 'archive': str(archive)}))
    else:
        if not args.prepared_dir or not args.returns:
            parser.error('--prepared-dir and --returns are required for local verification')
        from vrm.cli import _read_jsonl
        from vrm.config import load_protocol_amendment
        from vrm.data import validate_prepared_artifacts
        from vrm.lean import LeanDojoBackend, cache_digest
        prepared = Path(args.prepared_dir)
        validate_prepared_artifacts(prepared, load_protocol_amendment(config['protocol_amendment'], args.config))
        from vrm.handoff import development_request
        private = [r for r in _read_jsonl(prepared / 'verifier_metadata.jsonl') if r['split'] == 'dev']
        if development_request(_read_jsonl(prepared / 'dev.jsonl'), private, config) != request:
            raise ValueError('handoff differs from the frozen development corpus')
        backend = LeanDojoBackend(execution_mode='docker',
            image='sha256:0c1ed089532fdb118749ec6033e634282344766c923c57738f82ee07b62ce21c',
            cache_dir='/private/tmp/vrm-mathlib4-official',
            cache_sha256='14f2b096ac58afa54b625ac64c281bdfc112f9f327b3c196df46bfccf5473fd1',
            landrun_sha256='177fa7db952b2542135c373474c7c5263f8a0607e68fe22fa5fbcc4fae5a320b')
        result = verify(request, private, args.returns, backend, args.output)
        post = cache_digest(backend.cache_dir)
        _write_bytes_atomic(Path(args.output) / 'post-cache.json', canonical({'sha256': post, 'unchanged': post == backend.cache_sha256}))
        if post != backend.cache_sha256:
            raise ValueError('post-run cache integrity failed')
        print(json.dumps(result))
        return 0 if result['status'] == 'integration_probe_completed' else 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
