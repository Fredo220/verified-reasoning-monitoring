import json
import pytest

from vrm.core import digest
from vrm.integration_probe import generate, verify
from vrm.handoff import DevelopmentHandoff
from test_handoff import CONFIG, request, candidate
from test_workflow import Runner, tasks


def test_generate_is_one_candidate_and_resume_does_not_reload_model(tmp_path):
    req = request()
    calls = []
    class Model(Runner):
        def generate(self, task, seed, remaining, **kwargs):
            calls.append((task, seed, remaining))
            return candidate(req)
    receipt = generate(req, CONFIG, tmp_path, gpu_started=990, clock=lambda: 1000,
                       runner_factory=lambda c: Model())
    assert len(calls) == 1 and calls[0][2] == 180
    assert receipt['scientific_gate_evaluated'] is False
    again = generate(req, CONFIG, tmp_path, gpu_started=990, clock=lambda: 1001,
                     runner_factory=lambda c: pytest.fail('resume reloaded model'))
    assert again == receipt
    assert DevelopmentHandoff(tmp_path / 'candidates', req, expected_sha256=digest(req)).manifest()['completed_candidates'] == 1


def test_stale_configuration_or_exhausted_gpu_budget_never_loads_model(tmp_path):
    req = request()
    forbidden = lambda c: pytest.fail('model loaded')
    with pytest.raises(ValueError, match='configuration'):
        generate(req, {**CONFIG, 'config_sha256': 'bad'}, tmp_path, gpu_started=990,
                 clock=lambda: 1000, runner_factory=forbidden)
    with pytest.raises(TimeoutError):
        generate(req, CONFIG, tmp_path, gpu_started=0, clock=lambda: 3601, runner_factory=forbidden)


def test_verify_rejects_late_handoff_before_executing_proof(tmp_path):
    req = request()
    class Model(Runner):
        def generate(self, *args, **kwargs):
            return candidate(req)
    generate(req, CONFIG, tmp_path / 'returns', gpu_started=990,
             clock=lambda: 1000, runner_factory=lambda c: Model())
    class Backend:
        def preflight(self):
            pytest.fail('late proof submitted')
    result = verify(req, tasks()[1], tmp_path / 'returns', Backend(), tmp_path / 'result', clock=lambda: 1200)
    assert result['status'] == 'budget_exhausted'
    assert result['prospective_h3'] is False


def test_hash_mismatch_never_loads_model(tmp_path):
    req = request()
    req['model']['model_revision'] = 'f' * 40
    with pytest.raises(ValueError, match='pins'):
        generate(req, CONFIG, tmp_path, gpu_started=990, clock=lambda: 1000,
                 runner_factory=lambda c: pytest.fail('model loaded'))


@pytest.mark.parametrize('verdict', ['valid', 'invalid', 'timeout', 'infrastructure_error'])
def test_verification_uses_remaining_budget_and_preserves_distinct_verdicts(tmp_path, verdict):
    from test_workflow import Verifier
    req = request()
    class Model(Runner):
        def generate(self, *args, **kwargs):
            return candidate(req)
    generate(req, CONFIG, tmp_path / 'returns', gpu_started=990,
             clock=lambda: 1000, runner_factory=lambda c: Model())
    calls = []
    class Backend(Verifier):
        def preflight(self):
            return {'ready': True}
        def verify(self, task, proof, timeout_s):
            calls.append((task, timeout_s))
            return {'status': verdict, 'elapsed_s': 1}
    result = verify(req, tasks()[1], tmp_path / 'returns', Backend(), tmp_path / 'result', clock=lambda: 1080)
    assert calls[0][1] == 95  # 180 minus 80 seconds elapsed and the 5-second guard
    assert 'reference_proof' not in json.dumps(calls[0][0])
    assert result['status'] == ('integration_probe_completed' if verdict in {'valid', 'invalid'} else verdict)
    again = verify(req, tasks()[1], tmp_path / 'returns', Backend(), tmp_path / 'result', clock=lambda: 1300)
    assert again == result and len(calls) == 1


def test_budget_constants_match_approved_development_record():
    from pathlib import Path
    from vrm.integration_probe import ACTIVE_SECONDS, CHECK_SECONDS, GPU_SECONDS, CLOCK_GUARD_SECONDS
    record = json.loads(Path('protocol/development_probe_budget_2026-09-16.json').read_text())
    assert record['status'] == 'approved_pre_outcome'
    assert (ACTIVE_SECONDS, CHECK_SECONDS, GPU_SECONDS, CLOCK_GUARD_SECONDS) == (
        record['active_limit_s'], record['verifier_limit_s'], record['gpu_allocation_limit_s'], record['clock_guard_s'])
    assert record['study_budgets_changed'] is False
