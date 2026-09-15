import json
from types import SimpleNamespace

import pytest

from vrm import auth
from vrm.config import load_study_config


CONFIG = load_study_config("configs/study.json")


def test_colab_rereads_secret_and_removes_stale_environment_token():
    env = {"HF_TOKEN": "stale-credential"}
    assert auth.read_colab_token(lambda name: "replacement-credential", env) is None
    assert env == {"HF_TOKEN": "replacement-credential"}


@pytest.mark.parametrize("failure", ["missing", "denied", "expired_session", "empty"])
def test_colab_failure_does_not_keep_old_credentials(failure):
    env = {"HF_TOKEN": "stale-credential"}
    def getter(name):
        if failure == "empty":
            return ""
        raise RuntimeError("raw message containing stale-credential")
    with pytest.raises(auth.AccessError) as caught:
        auth.read_colab_token(getter, env)
    assert "HF_TOKEN" not in env
    assert "stale-credential" not in str(caught.value)
    assert caught.value.code == "colab_secret_unavailable"


def install_api(monkeypatch, *, status=None, fail_at="identity", network=False):
    import huggingface_hub
    calls = []
    class Failure(Exception):
        response = SimpleNamespace(status_code=status)
    class API:
        def __init__(self, **kwargs):
            calls.append(("endpoint", kwargs))
        def whoami(self, *, token, cache):
            assert token == "test-credential" and cache is False
            calls.append(("whoami", cache))
            if fail_at == "identity" and (status or network):
                raise Failure("private token test-credential")
            return {"name": "private-account-name"}
    def metadata(url, **kwargs):
        assert kwargs["token"] == "test-credential"
        assert kwargs["timeout"] == 10
        calls.append(("metadata", url))
        if fail_at == "metadata" and (status or network):
            raise Failure("private token test-credential")
        return SimpleNamespace(commit_hash=CONFIG["model_revision"])
    monkeypatch.setattr(huggingface_hub, "HfApi", API)
    monkeypatch.setattr(huggingface_hub, "get_hf_file_metadata", metadata)
    return calls


def test_missing_token_stops_before_network(monkeypatch):
    calls = install_api(monkeypatch)
    with pytest.raises(auth.AccessError, match="HF_TOKEN"):
        auth.check_hf_access(CONFIG, token=None)
    assert not calls


@pytest.mark.parametrize("status,stage,code", [
    (401, "identity", "token_rejected"),
    (403, "identity", "token_rejected"),
    (403, "metadata", "model_access_denied"),
    (401, "metadata", "model_access_denied"),
    (404, "metadata", "model_revision_unavailable"),
    (429, "identity", "service_unavailable"),
    (500, "metadata", "service_unavailable"),
])
def test_access_failure_is_specific_and_redacted(monkeypatch, status, stage, code):
    install_api(monkeypatch, status=status, fail_at=stage)
    with pytest.raises(auth.AccessError) as caught:
        auth.check_hf_access(CONFIG, token="test-credential")
    assert caught.value.code == code
    assert "test-credential" not in str(caught.value)


def test_network_failure_is_not_reported_as_expired_token(monkeypatch):
    install_api(monkeypatch, network=True)
    with pytest.raises(auth.AccessError) as caught:
        auth.check_hf_access(CONFIG, token="test-credential")
    assert caught.value.code == "service_unavailable"


def test_success_checks_pinned_files_and_does_not_return_account_or_token(monkeypatch):
    calls = install_api(monkeypatch)
    result = auth.check_hf_access(CONFIG, token="test-credential")
    assert result["ready"] is True
    text = json.dumps(result)
    assert "test-credential" not in text and "private-account-name" not in text
    assert result["model_revision"] == CONFIG["model_revision"]
    urls = [value for kind, value in calls if kind == "metadata"]
    assert len(urls) == 3
    assert all(CONFIG["model_revision"] in url for url in urls)


def test_rejected_token_can_be_retried_without_cached_negative_result(monkeypatch):
    install_api(monkeypatch, status=401)
    with pytest.raises(auth.AccessError):
        auth.check_hf_access(CONFIG, token="test-credential")
    install_api(monkeypatch)
    assert auth.check_hf_access(CONFIG, token="test-credential")["ready"]


def test_cli_auth_check_does_not_load_gemma_or_verifier(monkeypatch, capsys):
    from vrm import cli
    monkeypatch.setenv("HF_TOKEN", "test-credential")
    install_api(monkeypatch)
    def forbidden(*args, **kwargs):
        raise AssertionError("Auth-only check must not initialize model or verifier")
    monkeypatch.setattr(cli, "HFRunner", forbidden)
    monkeypatch.setattr(cli, "LeanDojoBackend", forbidden)
    assert cli.main(["auth-check"]) == 0
    assert json.loads(capsys.readouterr().out)["ready"]


def test_cli_rejection_is_redacted_json_without_traceback(monkeypatch, capsys):
    from vrm import cli
    monkeypatch.setenv("HF_TOKEN", "test-credential")
    install_api(monkeypatch, status=401)
    assert cli.main(["auth-check"]) == 2
    output = capsys.readouterr()
    assert json.loads(output.out)["code"] == "token_rejected"
    assert "test-credential" not in output.out + output.err


def test_runner_rechecks_auth_before_any_model_or_tokenizer_download(monkeypatch):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from vrm.runtime import HFRunner
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setenv("HF_TOKEN", "test-credential")
    install_api(monkeypatch, status=401)
    def forbidden(*args, **kwargs):
        pytest.fail("download attempted after rejected authentication")
    monkeypatch.setattr(AutoTokenizer, "from_pretrained", forbidden)
    monkeypatch.setattr(AutoModelForCausalLM, "from_pretrained", forbidden)
    with pytest.raises(auth.AccessError) as caught:
        HFRunner(CONFIG)
    assert caught.value.code == "token_rejected"


def test_offline_runner_does_not_check_or_send_cached_credentials(monkeypatch):
    from transformers import AutoTokenizer
    from vrm.runtime import HFRunner
    monkeypatch.setenv("HF_TOKEN", "stale-credential")
    monkeypatch.setattr(auth, "check_hf_access", lambda *a, **kw: pytest.fail("offline network check"))
    class CacheAbsent(Exception):
        pass
    def local_load(*args, **kwargs):
        assert kwargs["local_files_only"] is True and kwargs["token"] is False
        raise CacheAbsent()
    monkeypatch.setattr(AutoTokenizer, "from_pretrained", local_load)
    with pytest.raises(CacheAbsent):
        HFRunner(CONFIG, allow_cpu=True, local_files_only=True)


def test_rejected_revision_is_not_reported_as_success(monkeypatch):
    import huggingface_hub
    install_api(monkeypatch)
    monkeypatch.setattr(huggingface_hub, "get_hf_file_metadata",
                        lambda *a, **kw: SimpleNamespace(commit_hash="0" * 40))
    with pytest.raises(auth.AccessError) as caught:
        auth.check_hf_access(CONFIG, token="test-credential")
    assert caught.value.code == "revision_mismatch"
