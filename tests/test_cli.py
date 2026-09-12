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

    seen = {}

    def run(public, private, runner, verifier, output, *, request):
        seen["public"] = public
        seen["private"] = private
        return {"status": "completed"}

    monkeypatch.setattr(cli, "LeanDojoBackend", Backend)
    monkeypatch.setattr(cli, "HFRunner", lambda *args, **kwargs: object())
    monkeypatch.setattr(cli, "run_development_smoke", run)
    code = cli.main([
        "smoke", "--config", "configs/study.json",
        "--prepared-dir", str(prepared), "--output", str(tmp_path / "run"),
        "--cache-dir", str(tmp_path), "--cache-sha256", "c" * 64,
        "--landrun-sha256", "d" * 64, "--local-files-only",
    ])
    assert code == 0
    assert [row["task_id"] for row in seen["public"]] == ["dev-1"]
    assert [row["task_id"] for row in seen["private"]] == ["dev-1"]
