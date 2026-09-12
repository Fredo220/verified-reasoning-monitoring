"""Contract tests; miniature fixtures are not benchmark evidence."""

import copy
import hashlib
import json
import random
from types import SimpleNamespace

import pytest

from vrm import data


LOCAL_CACHE_URL = (
    "/scratch/lean_dojo/.cache/lean_dojo/"
    f"leanprover-community-mathlib4-{data.UPSTREAM['repo_commit']}/mathlib4_d"
)


class Tokenizer:
    name_or_path = "test-character-tokenizer"

    def encode(self, text, *, add_special_tokens):
        return ([0] if add_special_tokens else []) + [ord(c) for c in text]


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def record(i, origin="train", **extra):
    return dict(task_id=f"task-{i}", group_id=f"group-{i}",
                upstream_split=origin, prompt=f"goal {i}", **extra)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def fixture_source(tmp_path, count=4, test_count=1):
    root = tmp_path / "source"
    metadata = []
    originals = {"train": [], "test": []}
    source_hashes = {}
    for i in range(count + test_count):
        origin = "train" if i < count else "test"
        name = f"Example.target_{i}"
        proof = "by\n  exact True.intro"
        head = f"theorem target_{i} : True := "
        source = head + proof + "\n"
        path = f"Mathlib/Example{i}.lean"
        original = dict(url=data.UPSTREAM["repo_url"],
                        commit=data.UPSTREAM["repo_commit"], file_path=path,
                        full_name=name, theorem_statement=head.rstrip(),
                        start=[1, 1], end=[2, 19],
                        traced_tactics=[dict(tactic="exact True.intro",
                                            state_before=f"n : Nat\n\u22a2 n = {i}",
                                            state_after="no goals",
                                            annotated_tactic=["exact True.intro", []])])
        originals[origin].append(original)
        local = root / "sources" / path
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(source, encoding="utf-8")
        source_hashes[path] = digest(source)
        metadata.append(dict(url=original["url"], commit=original["commit"],
                             file_path=path, full_name=name,
                             start=original["start"], end=original["end"],
                             proof_start=[1, len(head) + 1], proof_end=[2, 19],
                             source_sha256=digest(source),
                             initial_state=original["traced_tactics"][0]["state_before"],
                             initial_state_origin="pretraced_proof_root",
                             trace_sha256="a" * 64))
    for origin, rows in originals.items():
        write_json(root / "novel_premises" / f"{origin}.json", rows)
    write_json(root / "metadata.json", dict(
        from_repo=dict(url=data.UPSTREAM["repo_url"], commit=data.UPSTREAM["repo_commit"]),
        leandojo_version=data.UPSTREAM["leandojo_version"],
        trusted_fixture_provenance=dict(
            archive_checksum=data.UPSTREAM["archive_checksum"], source_files=source_hashes)))
    save_metadata(root, metadata)
    return root, originals, metadata


def save_metadata(root, rows):
    (root / "traced_metadata.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def make_v3_fixture(tmp_path, count=4, test_count=1):
    root, originals, metadata = fixture_source(tmp_path, count=count, test_count=test_count)
    (root / "traced_metadata.jsonl").unlink()
    for rows in originals.values():
        for row in rows:
            row["url"] = LOCAL_CACHE_URL
    for split, rows in originals.items():
        write_json(root / "novel_premises" / f"{split}.json", rows)
    document = json.loads((root / "metadata.json").read_text())
    document["from_repo"]["url"] = LOCAL_CACHE_URL
    write_json(root / "metadata.json", document)
    return root, originals, metadata


@pytest.fixture
def small_sizes(monkeypatch):
    sizes = dict(dev=1, train=1, val=1, id_test=1, ood_test=1)
    monkeypatch.setattr(data, "FULL_SIZES", sizes)
    return sizes


def test_split_sizes_are_frozen():
    assert data.FULL_SIZES == dict(dev=32, train=384, val=64, id_test=80, ood_test=40)
    assert data.REDUCED_SIZES == dict(dev=32, train=192, val=32, id_test=40, ood_test=20)


def test_assign_is_pure_order_independent_and_origin_isolated():
    rows = [record(i) for i in range(20)] + [record(i, "test") for i in range(20, 25)]
    before = copy.deepcopy(rows)
    sizes = dict(dev=2, train=4, val=2, id_test=2, ood_test=2)
    result = data.assign_splits(rows, sizes)
    random.Random(17).shuffle(rows)
    assert result == data.assign_splits(rows, dict(reversed(list(sizes.items()))))
    assert sorted(rows, key=lambda r: r["task_id"]) == sorted(before, key=lambda r: r["task_id"])
    assert {k: len(v) for k, v in result.items()} == sizes
    for split, tasks in result.items():
        assert all(t["split"] == split for t in tasks)
        assert all(t["upstream_split"] == ("test" if split == "ood_test" else "train") for t in tasks)


def test_duplicates_and_transitive_variants_never_cross_splits():
    rows = [record(i) for i in range(20)] + [record(30, "test")]
    rows += [dict(record(21), group_id="group-0", prompt="shared goal"),
             dict(record(22), prompt=" shared   goal\n"),
             dict(record(23, "test"), group_id="group-22")]
    result = data.assign_splits(rows, dict(dev=2, train=2, val=2, id_test=2, ood_test=1))
    selected = [r for split in result.values() for r in split]
    assert not {"task-0", "task-21", "task-22", "task-23"} & {r["task_id"] for r in selected}
    assert len({r["group_id"] for r in selected}) == len(selected)


@pytest.mark.parametrize("rows,sizes", [
    ([record(1, "val")], {"dev": 1}),
    ([record(1)], {"train": -1}),
    ([record(1)], {"train": True}),
    ([record(1)], {"unknown": 1}),
    ([record(1), dict(record(1), prompt="different")], {"train": 1}),
])
def test_assign_rejects_invalid_input(rows, sizes):
    with pytest.raises(ValueError):
        data.assign_splits(rows, sizes)


def test_insufficient_groups_raise_without_reuse():
    with pytest.raises(data.PreparationError, match="insufficient"):
        data.assign_splits([record(1), dict(record(2), prompt="goal 1")], {"train": 2})


def test_prepare_reproducible_public_schema_private_hash_only_audit(tmp_path, small_sizes):
    root, _, _ = fixture_source(tmp_path)
    one, two = tmp_path / "one", tmp_path / "two"
    manifest = data.prepare(root, Tokenizer(), one)
    assert manifest["status"] == "ready"
    assert manifest == data.prepare(root, Tokenizer(), two)
    assert manifest["counts"] == small_sizes
    assert manifest["upstream"]["archive_checksum"] == "md5:b58af89599d5bbc792abc3744e5d37d9"
    for path in one.iterdir():
        assert path.read_bytes() == (two / path.name).read_bytes()
    expected = {"task_id", "group_id", "split", "repo_url", "repo_commit", "file_path", "full_name", "prompt"}
    for split in small_sizes:
        row = json.loads((one / f"{split}.jsonl").read_text())
        assert set(row) == expected
        assert "True.intro" not in row["prompt"]
        assert "target_" not in row["prompt"]
    audit = (one / "eligibility_audit.jsonl").read_text()
    assert "True.intro" not in audit and "initial_state" not in audit
    item = json.loads(audit.splitlines()[0])
    assert item["reference_tokens"] == len("by\n  exact True.intro")
    assert item["reference_sha256"] == digest("by\n  exact True.intro")


def test_actual_v3_rows_prepare_without_traced_metadata(tmp_path, small_sizes):
    root, _, _ = make_v3_fixture(tmp_path)
    out = tmp_path / "out"
    manifest = data.prepare(root, Tokenizer(), out)
    assert manifest["status"] == "ready"
    assert manifest["provenance"]["archive_verification"] == "trusted_fixture"
    public = json.loads((out / "dev.jsonl").read_text())
    assert public["repo_url"] == data.UPSTREAM["repo_url"]
    private = [json.loads(line) for line in (out / "verifier_metadata.jsonl").read_text().splitlines()]
    assert all(row["metadata"]["reference_proof"] == "by\n  exact True.intro" for row in private)


def test_wrong_archive_bytes_block_before_source_checkout(tmp_path, small_sizes):
    root, _, _ = make_v3_fixture(tmp_path)
    document = json.loads((root / "metadata.json").read_text())
    document.pop("trusted_fixture_provenance")
    write_json(root / "metadata.json", document)
    archive = tmp_path / "benchmark.tar.gz"
    archive.write_bytes(b"not the official archive")
    result = data.prepare(
        root, Tokenizer(), tmp_path / "out", source_root=root / "sources", archive_path=archive)
    assert result["status"] == "blocked"
    assert "archive md5" in json.dumps(result["blockers"]).lower()


def test_production_source_checkout_provenance_is_verified(tmp_path, monkeypatch, small_sizes):
    root, _, _ = make_v3_fixture(tmp_path)
    document = json.loads((root / "metadata.json").read_text())
    document.pop("trusted_fixture_provenance")
    write_json(root / "metadata.json", document)
    archive = tmp_path / "benchmark.tar.gz"
    archive.write_bytes(b"fixture archive")
    monkeypatch.setattr(data, "_md5_file", lambda path: data.UPSTREAM["archive_checksum"].split(":", 1)[1])

    source_root = (root / "sources").resolve()
    responses = {
        ("rev-parse", "--show-toplevel"): str(source_root),
        ("rev-parse", "HEAD"): data.UPSTREAM["repo_commit"],
        ("config", "--get", "remote.origin.url"): data.UPSTREAM["repo_url"] + ".git",
        ("status", "--porcelain", "--untracked-files=no"): "",
    }

    def fake_run(command, **kwargs):
        key = tuple(command[3:])
        return SimpleNamespace(returncode=0, stdout=responses[key] + "\n", stderr="")

    monkeypatch.setattr(data.subprocess, "run", fake_run)
    result = data.prepare(
        root, Tokenizer(), tmp_path / "clean", source_root=source_root, archive_path=archive)
    assert result["status"] == "ready"
    assert result["provenance"]["source_checkout"] == "verified_clean_git"

    responses[("status", "--porcelain", "--untracked-files=no")] = " M Mathlib/Example0.lean"
    result = data.prepare(
        root, Tokenizer(), tmp_path / "dirty", source_root=source_root, archive_path=archive)
    assert result["status"] == "blocked"
    assert "tracked modifications" in json.dumps(result["blockers"])


def test_dependency_rows_are_rejected_without_blocking_viable_pool(tmp_path, small_sizes):
    root, originals, _ = make_v3_fixture(tmp_path, count=5)
    originals["train"][0]["file_path"] = ".lake/packages/aesop/Aesop.lean"
    write_json(root / "novel_premises" / "train.json", originals["train"])
    result = data.prepare(root, Tokenizer(), tmp_path / "out")
    assert result["status"] == "ready"
    assert result["rejections"]["unsupported_dependency_path"] == 1


def test_missing_originals_reports_blocker_without_fake_tasks(tmp_path):
    result = data.prepare(tmp_path / "absent", Tokenizer(), tmp_path / "out")
    assert result["status"] == "blocked"
    assert "novel_premises/train.json" in json.dumps(result["blockers"])
    assert not list((tmp_path / "out").glob("*test.jsonl"))


def test_recorded_nested_tactics_are_not_a_complete_reference(tmp_path, small_sizes):
    root, originals, metadata = fixture_source(tmp_path)
    originals["train"][0]["traced_tactics"] *= 2
    write_json(root / "novel_premises/train.json", originals["train"])
    metadata[0].pop("proof_start")
    (root / "sources" / metadata[0]["file_path"]).unlink()
    save_metadata(root, metadata)
    result = data.prepare(root, Tokenizer(), tmp_path / "out")
    assert result["status"] == "blocked"
    assert result["rejections"]["source_unavailable"] == 1
    assert not (tmp_path / "out/train.jsonl").exists()


@pytest.mark.parametrize("change,reason", [
    ({"source_sha256": "b" * 64}, "source_sha256"),
    ({"proof_end": [2, 8]}, "proof_end"),
    ({"proof_start": [0, 1]}, "position"),
    ({"initial_state_origin": "first_recorded_tactic"}, "initial_state_origin"),
    ({"initial_state": "\u22a2 Example.target_0"}, "self_reference"),
    ({"initial_state": "h : target_0\n\u22a2 True"}, "self_reference"),
])
def test_bad_metadata_fails_closed(tmp_path, small_sizes, change, reason):
    root, _, metadata = fixture_source(tmp_path)
    metadata[0].update(change)
    save_metadata(root, metadata)
    result = data.prepare(root, Tokenizer(), tmp_path / "out")
    assert result["status"] == "blocked"
    assert reason in json.dumps(result["blockers"])


def test_pretraced_complete_proof_export_without_source(tmp_path, small_sizes):
    root, _, metadata = fixture_source(tmp_path)
    for row in metadata:
        row["reference_proof"] = "by\n  exact True.intro"
        row["reference_origin"] = "TracedTheorem.get_tactic_proof"
        (root / "sources" / row["file_path"]).unlink()
    save_metadata(root, metadata)
    assert data.prepare(root, Tokenizer(), tmp_path / "out")["status"] == "ready"


def test_source_and_pretraced_reference_mismatch_blocks(tmp_path, small_sizes):
    root, _, metadata = fixture_source(tmp_path)
    metadata[0].update(reference_proof="by trivial", reference_origin="TracedTheorem.get_tactic_proof")
    save_metadata(root, metadata)
    assert data.prepare(root, Tokenizer(), tmp_path / "out")["status"] == "blocked"


def test_token_limits_measure_complete_proof_and_final_prompt(tmp_path, small_sizes):
    root, _, _ = fixture_source(tmp_path)

    class BoundaryTokenizer(Tokenizer):
        def encode(self, text, *, add_special_tokens):
            if text.startswith("by"):
                return [0] * 65
            return [0] * 512

    result = data.prepare(root, BoundaryTokenizer(), tmp_path / "out")
    assert result["status"] == "blocked"
    assert result["rejections"]["reference_tokens"] == 5


@pytest.mark.parametrize("reference_tokens,prompt_tokens,ready", [(64, 512, True), (64, 513, False)])
def test_inclusive_limits_without_truncation(tmp_path, small_sizes, reference_tokens, prompt_tokens, ready):
    root, _, _ = fixture_source(tmp_path)

    class BoundaryTokenizer(Tokenizer):
        def encode(self, text, *, add_special_tokens):
            return [0] * (reference_tokens if text.startswith("by") else prompt_tokens)

    result = data.prepare(root, BoundaryTokenizer(), tmp_path / "out")
    assert (result["status"] == "ready") == ready


def test_recorded_tactic_threshold(tmp_path, small_sizes):
    root, originals, _ = fixture_source(tmp_path)
    for rows in originals.values():
        for row in rows:
            row["traced_tactics"] *= 6
    for split, rows in originals.items():
        write_json(root / "novel_premises" / f"{split}.json", rows)
    assert data.prepare(root, Tokenizer(), tmp_path / "six")["status"] == "ready"
    originals["train"][0]["traced_tactics"].append(originals["train"][0]["traced_tactics"][0])
    write_json(root / "novel_premises/train.json", originals["train"])
    result = data.prepare(root, Tokenizer(), tmp_path / "seven")
    assert result["rejections"]["recorded_tactics"] == 1


def test_reduced_requires_pretest_budget_evidence(tmp_path, monkeypatch, small_sizes):
    root, _, _ = fixture_source(tmp_path)
    monkeypatch.setattr(data, "REDUCED_SIZES", small_sizes)
    assert data.prepare(root, Tokenizer(), tmp_path / "missing", reduced=True)["status"] == "blocked"
    write_json(root / "budget_decision.json", dict(
        made_before_test=True, full_estimated_seconds=20,
        reduced_estimated_seconds=10, budget_seconds=12, pretest_measurement_sha256="b" * 64))
    assert data.prepare(root, Tokenizer(), tmp_path / "valid", reduced=True)["status"] == "ready"


def test_existing_output_is_never_overwritten(tmp_path, small_sizes):
    root, _, _ = fixture_source(tmp_path)
    out = tmp_path / "out"
    data.prepare(root, Tokenizer(), out)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    with pytest.raises(FileExistsError):
        data.prepare(root, Tokenizer(), out)
    assert before == {p.name: p.read_bytes() for p in out.iterdir()}


def test_unicode_source_columns_are_characters_not_bytes(tmp_path, small_sizes):
    root, originals, metadata = fixture_source(tmp_path)
    row = metadata[0]
    path = root / "sources" / row["file_path"]
    source = path.read_text().replace(": True :=", ": \u22a4 :=")
    path.write_text(source)
    originals["train"][0]["theorem_statement"] = "theorem target_0 : \u22a4 :="
    write_json(root / "novel_premises" / "train.json", originals["train"])
    row["proof_start"][1] -= 3
    row["source_sha256"] = digest(source)
    document = json.loads((root / "metadata.json").read_text())
    document["trusted_fixture_provenance"]["source_files"][row["file_path"]] = digest(source)
    write_json(root / "metadata.json", document)
    save_metadata(root, metadata)
    assert data.prepare(root, Tokenizer(), tmp_path / "out")["status"] == "ready"


def test_official_source_url_is_pinned_and_rejects_unresolved_dependencies():
    row = dict(url=data.UPSTREAM["repo_url"], commit=data.UPSTREAM["repo_commit"],
               file_path="Mathlib/Algebra/Group/Basic.lean")
    assert data.official_source_url(row) == (
        "https://raw.githubusercontent.com/leanprover-community/mathlib4/"
        + data.UPSTREAM["repo_commit"] + "/Mathlib/Algebra/Group/Basic.lean")
    for path in ("../secret", "/etc/passwd", ".lake/packages/aesop/Aesop.lean"):
        with pytest.raises(data.PreparationError):
            data.official_source_url(dict(row, file_path=path))


def test_chat_prompt_is_counted_but_public_prompt_remains_raw(tmp_path, small_sizes):
    root, _, _ = fixture_source(tmp_path)

    class ChatTokenizer(Tokenizer):
        chat_template = "test-template"
        bos_token_id = 2

        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            assert tokenize is True and add_generation_prompt is True
            assert messages[0]["content"].startswith("Prove this Lean 4 theorem.")
            return [2, 10, 11]

    result = data.prepare(root, ChatTokenizer(), tmp_path / "out")
    assert result["status"] == "ready"
    row = json.loads((tmp_path / "out" / "dev.jsonl").read_text())
    assert row["prompt"].startswith("Prove this Lean 4 theorem.")
    assert "<bos>" not in row["prompt"]
    assert "<user>" not in row["prompt"]


def test_rendered_chat_prompt_token_limit_is_enforced(tmp_path, small_sizes):
    root, _, _ = fixture_source(tmp_path)

    class ChatTokenizer(Tokenizer):
        chat_template = "test-template"
        bos_token_id = 2

        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            assert tokenize is True and add_generation_prompt is True
            return [2] + list(range(512))

    result = data.prepare(root, ChatTokenizer(), tmp_path / "out")
    assert result["status"] == "blocked"
    assert result["rejections"]["prompt_tokens"] == 5
