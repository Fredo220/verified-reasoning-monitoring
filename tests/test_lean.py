"""Unit transport tests plus explicitly provisioned real Comparator tests."""

import json
import os
from pathlib import Path
import subprocess
import hashlib

import pytest

from vrm import lean
from vrm.data import _render_prompt


SHA = {
    "source": "1" * 64,
    "trace": "2" * 64,
    "cache": "3" * 64,
    "landrun": "4" * 64,
}
TASK = {
    "task_id": "benchmark-4/example",
    "repo_url": lean.MATHLIB_REPO_URL,
    "repo_commit": lean.MATHLIB_COMMIT,
    "file_path": "Mathlib/Example.lean",
    "full_name": "Example.target",
    "verifier": {
        "benchmark_doi": lean.BENCHMARK_DOI,
        "source_sha256": SHA["source"],
        "trace_sha256": SHA["trace"],
        "cache_sha256": SHA["cache"],
        "start": [1, 1],
        "end": [2, 19],
        "proof_start": [1, 27],
        "proof_end": [2, 19],
        "theorem_statement": "theorem target : True :=",
    },
}
IMAGE = "vrm-lean@sha256:" + "b" * 64


@pytest.fixture
def backend(tmp_path):
    return lean.LeanDojoBackend(
        execution_mode="docker",
        image=IMAGE,
        cache_dir=tmp_path,
        cache_sha256=SHA["cache"],
        landrun_sha256=SHA["landrun"],
    )


def runtime_ready(monkeypatch, backend):
    monkeypatch.setattr(
        backend,
        "_runtime_preflight",
        lambda deadline: {
            "runtime_ready": True,
            "audit_ready": True,
            "reasons": [],
            "checks": {"sandbox": True, "cache": True, "proof_audit": True},
            "observation": {
                "kind": "probe_ok",
                "audit": backend._probe_receipt(),
            },
        },
    )


class TestPinnedContract:
    def test_frozen_versions_are_exact(self):
        assert lean.BENCHMARK_DOI == "10.5281/zenodo.18815372"
        assert lean.MATHLIB_REPO_URL == "https://github.com/leanprover-community/mathlib4"
        assert lean.MATHLIB_COMMIT == "1bc7728a050fc18ca2683f614c531cd7050ff063"
        assert lean.LEAN_DOJO_VERSION == "4.20.0"
        assert lean.LEAN_VERSION == "v4.29.0-rc2"
        assert lean.COMPARATOR_COMMIT == "3090445149fbaba51d8177df4eb2121573788341"
        assert lean.COMPARATOR_REPO_URL == "https://github.com/leanprover/comparator"
        assert lean.LANDRUN_REPO_URL == "https://github.com/Zouuup/landrun"
        assert lean.LANDRUN_COMMIT == "811cfff51ceaf3d9843708aa6d22e9b84ccac8b4"
        assert lean.LEAN4EXPORT_COMMIT == "048394e1afeeb52b0fa27bcf3f1ade2ff0f0ab6d"
        assert lean.LEAN4CHECKER_COMMIT == "b7398199245524275543dec6113229c9bb4902e5"
        assert lean.ALLOWED_AXIOMS == ("propext", "Quot.sound", "Classical.choice")

    def test_verifier_metadata_is_not_part_of_public_task_projection(self):
        validated = lean._validated_task(TASK)
        assert validated["verifier"] == TASK["verifier"]
        assert lean.public_task(TASK) == {
            key: TASK[key]
            for key in ("task_id", "repo_url", "repo_commit", "file_path", "full_name")
        }

    def test_identity_is_available_only_after_successful_preflight(
        self, backend, monkeypatch
    ):
        with pytest.raises(RuntimeError, match="preflight"):
            _ = backend.identity
        runtime_ready(monkeypatch, backend)
        assert backend.preflight()["ready"] is True
        identity = backend.identity
        assert identity["benchmark_doi"] == lean.BENCHMARK_DOI
        assert identity["cache_sha256"] == SHA["cache"]

    @pytest.mark.parametrize(
        "change",
        [
            {"repo_commit": "a" * 40},
            {"repo_url": "file:///tmp/repo"},
            {"file_path": "../escape.lean"},
            {"file_path": "/etc/escape.lean"},
            {"file_path": "Foo\\escape.lean"},
            {"full_name": ""},
            {"verifier": {}},
            {"verifier": {**TASK["verifier"], "benchmark_doi": "old"}},
            {"verifier": {**TASK["verifier"], "source_sha256": "f" * 63}},
        ],
    )
    def test_unpinned_task_fails_before_runtime(self, backend, monkeypatch, change):
        monkeypatch.setattr(
            backend, "_runtime_preflight", lambda *args: pytest.fail("runtime queried")
        )
        result = backend.verify({**TASK, **change}, "exact True.intro", 10)
        assert result["status"] == "infrastructure_error"


class TestContentProvenance:
    def test_cache_digest_covers_paths_content_and_symlinks(self, tmp_path):
        root = tmp_path / "cache"
        root.mkdir()
        (root / "source.lean").write_text("theorem x : True := by trivial\n")
        (root / "trace").mkdir()
        (root / "trace" / "x.ast.json").write_text("{}")
        (root / "source-link").symlink_to("source.lean")
        first = lean.cache_digest(root)

        (root / "trace" / "x.ast.json").write_text('{"mutated": true}')
        assert lean.cache_digest(root) != first

    def test_cache_digest_ignores_git_metadata_but_not_tracked_tree(self, tmp_path):
        root = tmp_path / "cache"
        (root / ".git").mkdir(parents=True)
        (root / ".git" / "index").write_bytes(b"one")
        (root / "lakefile.toml").write_bytes(b"name='mathlib'")
        first = lean.cache_digest(root)
        (root / ".git" / "index").write_bytes(b"two")
        assert lean.cache_digest(root) == first
        (root / "lakefile.toml").write_bytes(b"changed")
        assert lean.cache_digest(root) != first

    def test_cache_digest_rejects_symlink_escape(self, tmp_path):
        root = tmp_path / "cache"
        root.mkdir()
        (root / "escape").symlink_to(tmp_path / "outside")
        with pytest.raises(ValueError, match="escapes cache root"):
            lean.cache_digest(root)

class TestSourceConstruction:
    def test_only_proof_span_is_replaced(self):
        source = "import Mathlib\n\ntheorem target : True := by\n  trivial\n\ntheorem keep : True := by trivial\n"
        start = (3, 26)
        end = (5, 1)
        challenge, solution = lean._source_variants(source, start, end, "by\n  exact True.intro")
        prefix = "import Mathlib\n\ntheorem target : True := "
        suffix = "\ntheorem keep : True := by trivial\n"
        assert challenge == prefix + "by\n  sorry\n" + suffix
        assert solution == prefix + "by\n  exact True.intro\n" + suffix

    def test_candidate_is_not_filtered_or_executed_while_constructing_source(self):
        proof = 'by\n  run_tac IO.FS.writeFile "/work/escape" "x"\n  exact True.intro'
        _, solution = lean._source_variants("theorem x : True := by trivial\n", (1, 21), (2, 1), proof)
        assert 'run_tac IO.FS.writeFile "/work/escape" "x"' in solution
        assert "exact True.intro" in solution

    @pytest.mark.parametrize(
        "proof",
        [
            "exact True.intro",
            " by\n  exact True.intro",
            "```lean\nby\n  exact True.intro\n```",
            "Here is the proof:\nby\n  exact True.intro",
            "by",
            "by   ",
        ],
    )
    def test_only_a_complete_unfenced_by_proof_is_accepted(self, proof):
        with pytest.raises(ValueError, match="complete proof beginning with by"):
            lean._complete_proof_body(proof)

    def test_data_prompt_and_verifier_agree_on_complete_proof_boundary(self):
        class Tokenizer:
            chat_template = None
            bos_token = None

            @staticmethod
            def encode(value, add_special_tokens=False):
                return value.split()

        prompt, _ = _render_prompt(Tokenizer(), "Example.target : True\n⊢ True")
        assert "Return only a complete proof beginning with `by`." in prompt
        assert lean._complete_proof_body("by\n  exact True.intro") == "  exact True.intro"

    def test_comparator_configuration_is_exact(self):
        assert lean._comparator_config("Example.target") == {
            "challenge_module": "Challenge",
            "solution_module": "Solution",
            "theorem_names": ["Example.target"],
            "permitted_axioms": ["propext", "Quot.sound", "Classical.choice"],
            "enable_nanoda": False,
        }

    def test_source_record_is_revalidated_before_replacement(self):
        source = "theorem target : True := by\n  exact True.intro"
        task = {
            **TASK,
            "verifier": {
                **TASK["verifier"],
                "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "start": [1, 1],
                "end": [2, 19],
                "proof_start": [1, 26],
                "proof_end": [2, 19],
                "theorem_statement": "theorem target : True :=",
            },
        }
        challenge, solution, original = lean._reconstruct_sources(
            task, source, "by\n  exact True.intro"
        )
        assert original == source
        assert challenge.endswith("by\n  sorry")
        assert solution == source

    def test_statement_or_declaration_boundary_mismatch_fails_closed(self):
        source = "theorem target : True := by\n  exact True.intro"
        task = {
            **TASK,
            "verifier": {
                **TASK["verifier"],
                "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "start": [1, 1],
                "end": [2, 19],
                "proof_start": [1, 26],
                "proof_end": [2, 19],
                "theorem_statement": "theorem target : False :=",
            },
        }
        with pytest.raises(ValueError, match="theorem statement boundary"):
            lean._reconstruct_sources(task, source, "by\n  exact True.intro")


class TestMockedTransport:
    def test_preflight_advertises_audit_only_after_exact_probe(self, backend, monkeypatch):
        runtime_ready(monkeypatch, backend)
        result = backend.preflight()
        assert result["ready"] is True
        assert result["runtime_ready"] is True
        assert result["checks"]["proof_audit"] is True
        assert result["reasons"] == []

    def test_valid_requires_exact_comparator_audit_receipt(self, backend, monkeypatch):
        runtime_ready(monkeypatch, backend)
        response = {"kind": "valid", "audit": backend._audit_receipt(TASK)}
        monkeypatch.setattr(backend, "_request", lambda request, deadline: response)
        result = backend.verify(TASK, "by\n  exact True.intro", 10)
        assert result["status"] == "valid"
        assert result["details"]["proof_audit"] == "comparator"

    @pytest.mark.parametrize(
        "response",
        [
            {"kind": "finished"},
            {"kind": "valid"},
            {"kind": "valid", "audit": {"trusted_judge": "Comparator"}},
            {"kind": "valid", "audit": {"trusted_judge": "Comparator", "cache_sha256": "0" * 64}},
        ],
    )
    def test_proof_finished_or_forged_receipt_cannot_grant_validity(
        self, backend, monkeypatch, response
    ):
        runtime_ready(monkeypatch, backend)
        monkeypatch.setattr(backend, "_request", lambda request, deadline: response)
        assert backend.verify(TASK, "by\n  exact True.intro", 10)["status"] == "infrastructure_error"

    @pytest.mark.parametrize(
        ("kind", "status"),
        [("invalid", "invalid"), ("timeout", "timeout"), ("infrastructure_error", "infrastructure_error")],
    )
    def test_worker_result_mapping(self, backend, monkeypatch, kind, status):
        runtime_ready(monkeypatch, backend)
        monkeypatch.setattr(backend, "_request", lambda request, deadline: {"kind": kind})
        assert backend.verify(TASK, "by\n  skip", 10)["status"] == status

    @pytest.mark.parametrize("response", [None, [], "valid", {}, {"kind": 12}])
    def test_malformed_worker_response_fails_closed(self, backend, monkeypatch, response):
        runtime_ready(monkeypatch, backend)
        monkeypatch.setattr(backend, "_request", lambda request, deadline: response)
        assert backend.verify(TASK, "by\n  skip", 10)["status"] == "infrastructure_error"

    def test_preflight_deadline_is_infrastructure_not_candidate_timeout(self, backend, monkeypatch):
        monkeypatch.setattr(
            backend,
            "_runtime_preflight",
            lambda deadline: (_ for _ in ()).throw(TimeoutError("probe deadline")),
        )
        assert backend.verify(TASK, "by\n  skip", 10)["status"] == "infrastructure_error"

    def test_transport_deadline_is_infrastructure_not_candidate_timeout(self, backend, monkeypatch):
        runtime_ready(monkeypatch, backend)
        monkeypatch.setattr(
            backend,
            "_request",
            lambda request, deadline: (_ for _ in ()).throw(TimeoutError("worker deadline")),
        )
        assert backend.verify(TASK, "by\n  skip", 10)["status"] == "infrastructure_error"

    def test_only_worker_candidate_deadline_maps_to_timeout(self, backend, monkeypatch):
        runtime_ready(monkeypatch, backend)
        monkeypatch.setattr(
            backend, "_request", lambda request, deadline: {"kind": "timeout", "phase": "candidate"}
        )
        assert backend.verify(TASK, "by\n  skip", 0.01)["status"] == "timeout"

    def test_unavailable_runtime_never_submits_candidate(self, backend, monkeypatch):
        monkeypatch.setattr(
            backend,
            "_runtime_preflight",
            lambda deadline: {
                "runtime_ready": False,
                "audit_ready": False,
                "reasons": ["cache_digest_mismatch"],
                "checks": {},
            },
        )
        monkeypatch.setattr(backend, "_request", lambda *args: pytest.fail("candidate submitted"))
        result = backend.verify(TASK, 'by\n  run_tac IO.println "untrusted"', 10)
        assert result["status"] == "infrastructure_error"
        assert "cache_digest_mismatch" in result["details"]["reasons"]

    @pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), True, "5"])
    def test_invalid_candidate_deadline_stops_before_runtime(self, backend, monkeypatch, timeout):
        monkeypatch.setattr(
            backend, "_runtime_preflight", lambda *args: pytest.fail("runtime queried")
        )
        assert backend.verify(TASK, "skip", timeout)["status"] == "infrastructure_error"

    def test_request_contains_complete_proof_and_verifier_record(self, backend, monkeypatch):
        runtime_ready(monkeypatch, backend)
        received = []
        monkeypatch.setattr(
            backend,
            "_request",
            lambda request, deadline: received.append(request) or {"kind": "invalid"},
        )
        proof = "by\n  intro n\n  exact Nat.add_zero n"
        backend.verify(TASK, proof, 10)
        assert received[0]["proof"] == proof
        assert received[0]["task"] == TASK
        assert received[0]["candidate_timeout_s"] == 10.0

    def test_docker_command_has_no_network_or_host_writable_mount(self, backend):
        command = backend._command("vrm-" + "c" * 32)
        assert command[:2] == ["docker", "run"]
        for flag in [
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges=true",
            "--user=65534:65534",
            "--pids-limit=128",
            "--memory=4g",
            "--memory-swap=4g",
            "--cpus=1",
            "--pull=never",
            "--ipc=none",
            "--pid=private",
        ]:
            assert flag in command
        mount = command[command.index("--mount") + 1]
        assert mount.endswith(",dst=/cache,readonly")
        assert "/var/run/docker.sock" not in " ".join(command)
        assert IMAGE in command

    def test_missing_docker_is_reported_not_raised(self, backend, monkeypatch):
        monkeypatch.setattr(lean.shutil, "which", lambda *args: None)
        result = backend.preflight()
        assert result["ready"] is False
        assert "docker_cli_missing" in result["reasons"]

    def test_cli_presence_is_not_daemon_readiness(self, backend, monkeypatch):
        monkeypatch.setattr(lean.shutil, "which", lambda *args: "/bin/docker")
        monkeypatch.setattr(
            lean.subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "", "daemon unreachable"),
        )
        result = backend.preflight()
        assert result["runtime_ready"] is False
        assert "docker_daemon_unavailable" in result["reasons"]


class TestNativeLinuxTransport:
    def test_native_comparator_command_has_no_direct_lean_or_solution_execution(self, tmp_path):
        comparator = tmp_path / "comparator"
        config = tmp_path / "audit" / "comparator.json"
        command = lean._native_comparator_command(comparator, config)
        assert command == ["lake", "env", str(comparator), str(config)]
        assert "Solution.lean" not in command
        assert command[2] == str(comparator)

    def test_native_setup_command_is_landrun_confined_and_network_denied(self, tmp_path):
        command = lean._landrun_command(
            tmp_path / "landrun", tmp_path / "audit", ["lake", "update"]
        )
        assert "--best-effort" in command
        assert "--rwx" in command
        assert str(tmp_path / "audit") in command
        assert "--unrestricted-network" not in command
        assert command[-2:] == ["lake", "update"]

    def test_landrun_probes_both_tcp_and_unix_socket_connections(self):
        tcp = lean._connection_probe_command("tcp", "43123")
        unix = lean._connection_probe_command("unix", "/tmp/vrm-probe.sock")
        assert "AF_INET" in tcp[2]
        assert "AF_UNIX" in unix[2]
        assert tcp[-1] == "43123"
        assert unix[-1] == "/tmp/vrm-probe.sock"

    def test_landrun_rejects_unknown_connection_probe_family(self):
        with pytest.raises(ValueError, match="unknown connection probe family"):
            lean._connection_probe_command("udp", "1")

    def test_native_preflight_fails_closed_when_landrun_probe_fails(
        self, tmp_path, monkeypatch
    ):
        backend = lean.LeanDojoBackend(
            execution_mode="native",
            cache_dir=tmp_path / "cache",
            comparator_root=tmp_path / "comparator",
            cache_sha256=SHA["cache"],
            landrun_sha256=SHA["landrun"],
        )
        monkeypatch.setattr(
            backend,
            "_native_preflight",
            lambda deadline: (_ for _ in ()).throw(
                RuntimeError("Landrun network isolation probe failed")
            ),
        )
        result = backend.preflight()
        assert result["ready"] is False
        assert result["status"] == "infrastructure_error"
        assert "Landrun network isolation probe failed" in result["error"]


@pytest.mark.skipif(
    os.environ.get("VRM_RUN_REAL_LEAN_TESTS") != "1",
    reason="requires the documented pinned Linux image, cache, Comparator, and Landrun",
)
class TestRealComparatorOptIn:
    @pytest.mark.parametrize(
        "case_name",
        ["valid", "invalid", "self_reference", "sorry", "unauthorized_axiom", "sandbox_escape"],
    )
    def test_real_security_case(self, case_name):
        cases = _real_cases()
        case = cases[case_name]
        backend = lean.LeanDojoBackend()
        readiness = backend.preflight()
        assert readiness["ready"], readiness
        result = backend.verify(case["task"], case["proof"], float(case.get("timeout_s", 180)))
        assert result["status"] == case["expected"], result

    def test_real_disposable_cache_mutation_is_rejected(self):
        case = _real_cases()["cache_mutation"]
        cache = Path(case["disposable_cache_dir"])
        mutation = cache / case["relative_path"]
        assert case.get("allow_mutation") is True and mutation.is_file()
        mutation.write_bytes(mutation.read_bytes() + b"\n-- VRM mutation probe\n")
        backend = lean.LeanDojoBackend(
            cache_dir=cache,
            cache_sha256=case["original_cache_sha256"],
        )
        readiness = backend.preflight()
        assert not readiness["ready"], readiness
        assert "cache_digest_mismatch" in readiness["reasons"], readiness


def _real_cases():
    value = os.environ["VRM_LEAN_REAL_CASES"]
    path = Path(value)
    return json.loads(path.read_text() if path.is_file() else value)
