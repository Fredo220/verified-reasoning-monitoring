import ast
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


def _code_cells() -> list[str]:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return [
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    ]


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
    assert "study_env = dict(os.environ)" in source
    assert "'--preserve-environment'" in source
    assert "exported = [" not in source
    assert not re.search(r"hf_[A-Za-z0-9]{20,}", source)


def test_notebook_provisions_and_preflights_verifier_before_smoke():
    source = _source()
    provision = source.index("provision-verifier")
    preflight = source.index("'preflight', '--execution-mode'")
    smoke = source.index("'smoke', '--config'")
    assert provision < preflight < smoke


def test_notebook_runs_the_study_under_python_312_when_colab_kernel_is_newer():
    source = _source()
    assert "STUDY_BASE_PYTHON = Path('/usr/bin/python3.12')" in source
    assert "STUDY_VENV = RUNTIME / 'python3.12'" in source
    assert "STUDY_PYTHON = STUDY_VENV / 'bin' / 'python'" in source
    assert "'-m', 'venv', str(STUDY_VENV)" in source
    assert "env['PATH'] = f\"{STUDY_VENV / 'bin'}:" in source
    assert "str(STUDY_PYTHON), '-m', 'pip'" in source
    assert "str(STUDY_PYTHON), '-I', '-m', 'vrm.cli'" in source
    assert "str(STUDY_PYTHON), '-I', '-m', 'pytest'" in source
    assert "study-python-runtime.json" in source
    assert "pip_freeze" in source
    assert "project checkout changed during provisioning" in source
    assert "'vrm', 'preflight'" not in source
    assert "'vrm', 'smoke'" not in source
    assert "'python', '-m', 'pytest'" not in source


def test_notebook_kernel_does_not_import_project_code_directly():
    for source in _code_cells():
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.Import):
                assert all(not alias.name.startswith("vrm") for alias in node.names)
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("vrm")


def test_notebook_runs_validation_and_cache_hashing_in_study_runtime():
    source = _source()
    assert "def study_json(" in source
    assert "def study_cache_digest(" in source
    assert "validate_prepared_artifacts" in source
    assert "post_smoke_cache_sha256 = study_cache_digest(CACHE)" in source


def test_notebook_uses_approved_runtime_amendment_and_official_mathlib_cache():
    source = _source()
    assert "v4.29.0-rc1" in source
    assert "ae061f79cdf7af458a26348177cfbd62da0123f6" in source
    assert "lake', 'exe', 'cache', 'get'" in source
    assert "is_available_in_cache" not in source
    assert "get_traced_repo_path" not in source
    assert "runtime_provenance_amendment_2026-09-13.json" in source


def test_notebook_rejects_dirty_source_checkouts():
    source = _source()
    assert "'status', '--porcelain=v1', '--untracked-files=all'" in source
    assert "source checkout is not clean" in source


def test_notebook_does_not_redownload_the_unused_benchmark_archive():
    source = _source()
    assert "zenodo.org/api/records" not in source
    assert "BENCHMARK_RELEASE" not in source


def test_notebook_exports_hash_manifested_native_evidence_and_smoke_artifacts():
    source = _source()
    assert "VRM_LEAN_REAL_RESULTS" in source
    assert "artifact-manifest.json" in source
    assert "shutil.make_archive" in source
    assert "files.download" in source
    assert "'verifier-acceptance' if verifier_passed else 'verifier-failure'" in source
    assert "export_artifacts('development-smoke')" in source


def test_notebook_uploads_preserved_corpus_outside_project_checkout():
    source = _source()
    upload = source.index("uploaded = files.upload()")
    assert "os.chdir('/content')" in source[upload - 200 : upload]
    assert "os.chdir(previous_directory)" in source[upload : upload + 200]
    assert "uploaded_archive = Path('/content') / PREPARED_ARCHIVE_NAME" in source


def test_notebook_labels_verifier_evidence_only_after_acceptance_checks():
    source = _source()
    decision = source.index("verifier_passed =")
    export = source.index("verifier_export = export_artifacts")
    assert decision < export
    assert "assert verifier_passed" in source[export:]


def test_notebook_rechecks_cache_after_smoke_before_accepting_summary():
    source = _source()
    smoke = source.index("smoke = run_vrm_as_study_user")
    summary = source.index("summary = json.loads", smoke)
    assert "post_smoke_cache_sha256 = study_cache_digest(CACHE)" in source[smoke:summary]
    assert "assert post_smoke_cache_sha256 == CACHE_SHA256" in source[smoke:summary]


def test_notebook_runs_registered_real_verifier_suite_before_smoke():
    source = _source()
    real_suite = source.index("VRM_RUN_REAL_LEAN_TESTS")
    smoke = source.index("'smoke', '--config'")
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


def test_notebook_runs_one_in_process_smoke_after_real_verifier_suite():
    source = _source()
    real_suite = source.index("VRM_RUN_REAL_LEAN_TESTS")
    smoke = source.index("'smoke', '--config'")
    assert real_suite < smoke
    assert source.count("'smoke', '--config'") == 1
    assert "'vrm', 'probe-candidate'" not in source
