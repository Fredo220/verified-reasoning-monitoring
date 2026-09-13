import json

from vrm import cli


def test_smoke_stops_before_loading_model_when_verifier_preflight_fails(
    tmp_path, monkeypatch
):
    class Backend:
        def __init__(self, **kwargs):
            pass

        def preflight(self):
            return {"ready": False, "status": "infrastructure_error"}

    monkeypatch.setattr(cli, "LeanDojoBackend", Backend)
    monkeypatch.setattr(
        cli, "HFRunner", lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("model loaded before verifier was ready")
        )
    )
    code = cli.main([
        "smoke", "--config", "configs/study.json",
        "--prepared-dir", str(tmp_path), "--output", str(tmp_path / "run"),
        "--cache-dir", str(tmp_path), "--cache-sha256", "c" * 64,
        "--landrun-sha256", "d" * 64,
    ])
    assert code == 2


def test_smoke_loads_only_development_verifier_rows(tmp_path, monkeypatch):
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    (prepared / "dev.jsonl").write_text(
        json.dumps({"task_id": "dev-1", "split": "dev"}) + "\n"
    )
    (prepared / "verifier_metadata.jsonl").write_text(
        json.dumps({"task_id": "dev-1", "split": "dev"}) + "\n"
        + json.dumps({"task_id": "train-1", "split": "train"}) + "\n"
    )

    class Backend:
        identity = {"backend": "test"}

        def __init__(self, **kwargs):
            pass

        def preflight(self):
            return {"ready": True, "status": "ready"}

    seen = {"calls": []}

    runner = object()

    def probe(public, private, candidate_runner, verifier, output, *, request):
        seen["calls"].append("probe")
        seen["probe_runner"] = candidate_runner
        return {"status": "integration_probe_completed"}

    def run(public, private, candidate_runner, verifier, output, *, request):
        seen["calls"].append("smoke")
        seen["public"] = public
        seen["private"] = private
        seen["smoke_runner"] = candidate_runner
        return {"status": "completed"}

    monkeypatch.setattr(cli, "LeanDojoBackend", Backend)
    monkeypatch.setattr(cli, "load_protocol_amendment", lambda *args: {})
    monkeypatch.setattr(cli, "validate_prepared_artifacts", lambda *args: {})
    monkeypatch.setattr(cli, "HFRunner", lambda *args, **kwargs: runner)
    monkeypatch.setattr(cli, "run_single_candidate_probe", probe)
    monkeypatch.setattr(cli, "run_development_smoke", run)
    code = cli.main([
        "smoke", "--config", "configs/study.json",
        "--prepared-dir", str(prepared), "--output", str(tmp_path / "run"),
        "--cache-dir", str(tmp_path), "--cache-sha256", "c" * 64,
        "--landrun-sha256", "d" * 64, "--local-files-only",
    ])
    assert code == 0
    assert seen["calls"] == ["probe", "smoke"]
    assert seen["probe_runner"] is runner
    assert seen["smoke_runner"] is runner
    assert [row["task_id"] for row in seen["public"]] == ["dev-1"]
    assert [row["task_id"] for row in seen["private"]] == ["dev-1"]


def test_probe_candidate_uses_the_smoke_identity_without_running_the_gate(
    tmp_path, monkeypatch
):
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    (prepared / "dev.jsonl").write_text(
        json.dumps({"task_id": "dev-1", "split": "dev"}) + "\n"
    )
    (prepared / "verifier_metadata.jsonl").write_text(
        json.dumps({"task_id": "dev-1", "split": "dev"}) + "\n"
    )

    class Backend:
        identity = {"backend": "test"}

        def __init__(self, **kwargs):
            pass

        def preflight(self):
            return {"ready": True, "status": "ready"}

    seen = {}

    def probe(public, private, runner, verifier, output, *, request):
        seen["request"] = request
        seen["output"] = output
        return {"status": "integration_probe_completed"}

    monkeypatch.setattr(cli, "LeanDojoBackend", Backend)
    monkeypatch.setattr(cli, "load_protocol_amendment", lambda *args: {})
    monkeypatch.setattr(cli, "validate_prepared_artifacts", lambda *args: {})
    monkeypatch.setattr(cli, "HFRunner", lambda *args, **kwargs: object())
    monkeypatch.setattr(cli, "run_single_candidate_probe", probe)
    monkeypatch.setattr(
        cli, "run_development_smoke",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("registered smoke ran during the integration probe")
        ),
    )

    output = tmp_path / "run"
    code = cli.main([
        "probe-candidate", "--config", "configs/study.json",
        "--prepared-dir", str(prepared), "--output", str(output),
        "--cache-dir", str(tmp_path), "--cache-sha256", "c" * 64,
        "--landrun-sha256", "d" * 64,
    ])

    assert code == 0
    assert seen["output"] == str(output)
    assert seen["request"]["candidates_per_task"] == 4


def test_smoke_stops_when_single_candidate_probe_fails(tmp_path, monkeypatch):
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    (prepared / "dev.jsonl").write_text(
        json.dumps({"task_id": "dev-1", "split": "dev"}) + "\n"
    )
    (prepared / "verifier_metadata.jsonl").write_text(
        json.dumps({"task_id": "dev-1", "split": "dev"}) + "\n"
    )

    class Backend:
        def __init__(self, **kwargs):
            pass

        def preflight(self):
            return {"ready": True, "status": "ready"}

    monkeypatch.setattr(cli, "LeanDojoBackend", Backend)
    monkeypatch.setattr(cli, "load_protocol_amendment", lambda *args: {})
    monkeypatch.setattr(cli, "validate_prepared_artifacts", lambda *args: {})
    monkeypatch.setattr(cli, "HFRunner", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        cli, "run_single_candidate_probe",
        lambda *args, **kwargs: {"status": "infrastructure_error"},
    )
    monkeypatch.setattr(
        cli, "run_development_smoke",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("registered smoke ran after a failed integration probe")
        ),
    )

    code = cli.main([
        "smoke", "--config", "configs/study.json",
        "--prepared-dir", str(prepared), "--output", str(tmp_path / "run"),
        "--cache-dir", str(tmp_path), "--cache-sha256", "c" * 64,
        "--landrun-sha256", "d" * 64,
    ])

    assert code == 2
