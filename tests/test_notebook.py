import json
import re
from pathlib import Path


NOTEBOOK = Path("notebooks/verified_reasoning_monitoring.ipynb")


def _source() -> str:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )


def test_notebook_requires_an_immutable_project_revision():
    source = _source()
    assert "PROJECT_GIT_URL" in source
    assert "PROJECT_GIT_REV" in source
    assert "'git', 'clone'" in source
    assert "'checkout', '--detach', PROJECT_GIT_REV" in source
    assert "'rev-parse', 'HEAD'" in source
    assert "^[0-9a-f]{40}$" in source


def test_notebook_reads_hugging_face_token_from_colab_secrets_only():
    source = _source()
    assert 'userdata.get("HF_TOKEN")' in source
    assert "env=study_env" in source
    assert "exported = [" not in source
    assert not re.search(r"hf_[A-Za-z0-9]{20,}", source)


def test_notebook_provisions_and_preflights_verifier_before_smoke():
    source = _source()
    provision = source.index("provision-verifier")
    preflight = source.index("'vrm', 'preflight'")
    smoke = source.index("'vrm', 'smoke'")
    assert provision < preflight < smoke


def test_notebook_runs_registered_real_verifier_suite_before_smoke():
    source = _source()
    real_suite = source.index("VRM_RUN_REAL_LEAN_TESTS")
    smoke = source.index("'vrm', 'smoke'")
    assert real_suite < smoke
    for case_name in (
        "valid",
        "invalid",
        "self_reference",
        "sorry",
        "unauthorized_axiom",
        "sandbox_escape",
        "cache_mutation",
    ):
        assert case_name in source
    assert "native_decide" in source
    assert "--junitxml" in source
    test_run = source.index("real_tests = subprocess.run")
    restore = source.index("shutil.rmtree(CACHE)")
    assert "finally:" in source[test_run:restore]
