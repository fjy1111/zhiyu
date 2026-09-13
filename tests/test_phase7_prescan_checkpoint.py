from pathlib import Path
import json
import pytest

from zhiyu.demo.prescan_checkpoint import (
    CheckpointError,
    CheckpointHeader,
    append_jsonl_record,
    encode_jsonl_record,
    initialize_checkpoint,
    load_checkpoint,
    recover_literal_backslash_n_records,
)

HEADER = CheckpointHeader(
    demo_kb_sha256="kb" * 32,
    manifest_sha256="mf" * 32,
    model="deepseek-flash",
    base_url="https://api.deepseek.com",
)


def _write_valid(path: Path, records, header=HEADER):
    append_jsonl_record(path, header.to_record())
    for record in records:
        append_jsonl_record(path, record)


def test_two_records_create_two_real_jsonl_lines(tmp_path):
    path = tmp_path / "prescan_checkpoint.jsonl"
    _write_valid(
        path,
        [
            {"document_id": "doc-a", "decision": "REVIEW"},
            {"document_id": "doc-b", "decision": "SAFE"},
        ],
    )
    raw = path.read_bytes()
    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.split("\n") if line != ""]
    assert raw.count(b"\n") == 3
    assert len(lines) == 3
    assert all(json.loads(line) for line in lines)
    assert [json.loads(line)["document_id"] for line in lines[1:]] == ["doc-a", "doc-b"]


def test_chinese_text_round_trips(tmp_path):
    path = tmp_path / "prescan_checkpoint.jsonl"
    record = {
        "document_id": "dv2-\u4e2d\u6587-001",
        "title": "\u56fe\u4e66\u9986\u5f00\u653e\u65f6\u95f4",
        "note": "\u7b2c\u4e00\u884c\n\u7b2c\u4e8c\u884c",
        "literal": "\u5b57\u9762\\n\u4fdd\u6301",
    }
    _write_valid(path, [record])
    loaded = load_checkpoint(path, HEADER)
    assert loaded[record["document_id"]]["title"] == "\u56fe\u4e66\u9986\u5f00\u653e\u65f6\u95f4"
    assert loaded[record["document_id"]]["note"] == "\u7b2c\u4e00\u884c\n\u7b2c\u4e8c\u884c"
    assert loaded[record["document_id"]]["literal"] == "\u5b57\u9762\\n\u4fdd\u6301"
    file_text = path.read_text(encoding="utf-8")
    assert "\u56fe\u4e66\u9986\u5f00\u653e\u65f6\u95f4" in file_text


def test_resume_skips_completed_document_ids(tmp_path):
    path = tmp_path / "prescan_checkpoint.jsonl"
    initialize_checkpoint(path, HEADER)
    append_jsonl_record(path, {"document_id": "dv2-conflict_dorm_017", "decision": "REVIEW"})
    done = load_checkpoint(path, HEADER)
    pending = [doc_id for doc_id in ("dv2-conflict_dorm_017", "dv2-conflict_exam_014") if doc_id not in done]
    assert "dv2-conflict_dorm_017" in done
    assert pending == ["dv2-conflict_exam_014"]


def test_malformed_checkpoint_fails_safely(tmp_path):
    path = tmp_path / "prescan_checkpoint.jsonl"
    malformed = (
        json.dumps({"document_id": "doc-a"}, ensure_ascii=False)
        + "\\n"
        + json.dumps({"document_id": "doc-b"}, ensure_ascii=False)
        + "\\n"
    )
    path.write_text(malformed, encoding="utf-8")
    assert b"\n" not in path.read_bytes()
    with pytest.raises(CheckpointError, match="malformed"):
        load_checkpoint(path, HEADER)


def test_duplicate_document_id_rejected(tmp_path):
    path = tmp_path / "prescan_checkpoint.jsonl"
    append_jsonl_record(path, HEADER.to_record())
    append_jsonl_record(path, {"document_id": "doc-a", "decision": "REVIEW"})
    append_jsonl_record(path, {"document_id": "doc-a", "decision": "SAFE"})
    with pytest.raises(CheckpointError, match="duplicate document_id"):
        load_checkpoint(path, HEADER)


def test_literal_backslash_n_bug_cannot_recur(tmp_path):
    path = tmp_path / "prescan_checkpoint.jsonl"
    encoded = encode_jsonl_record({"document_id": "doc-a", "decision": "REVIEW"})
    assert encoded.endswith("\n")
    assert encoded.count("\n") == 1
    assert not encoded.endswith("\\n")
    append_jsonl_record(path, HEADER.to_record())
    append_jsonl_record(path, {"document_id": "doc-a"})
    append_jsonl_record(path, {"document_id": "doc-b"})
    raw = path.read_bytes()
    assert raw.count(b"\n") == 3
    assert b"}\\n{" not in raw
    source = Path("scripts/run_phase7_prescan.py").read_text(encoding="utf-8")
    assert r"+'\\n'" not in source
    assert r'+"\\n"' not in source
    assert "append_jsonl_record" in source


def test_incompatible_header_rejected(tmp_path):
    path = tmp_path / "prescan_checkpoint.jsonl"
    _write_valid(path, [{"document_id": "doc-a"}])
    other = CheckpointHeader(
        demo_kb_sha256="other-kb",
        manifest_sha256=HEADER.manifest_sha256,
        model=HEADER.model,
        base_url=HEADER.base_url,
    )
    with pytest.raises(CheckpointError, match="incompatible"):
        load_checkpoint(path, other)


def test_blank_lines_ignored(tmp_path):
    path = tmp_path / "prescan_checkpoint.jsonl"
    path.write_bytes(
        (
            encode_jsonl_record(HEADER.to_record())
            + "\n"
            + encode_jsonl_record({"document_id": "doc-a"})
            + "\n"
        ).encode("utf-8")
    )
    loaded = load_checkpoint(path, HEADER)
    assert list(loaded) == ["doc-a"]


def test_recovery_does_not_blindly_replace_backslash_n_inside_strings():
    rec1 = {"document_id": "doc-a", "note": "\u7b2c\u4e00\u884c\n\u7b2c\u4e8c\u884c"}
    rec2 = {"document_id": "doc-b", "note": "\u5b57\u9762\\n\u4fdd\u6301"}
    text = (
        json.dumps(rec1, ensure_ascii=False)
        + "\\n"
        + json.dumps(rec2, ensure_ascii=False)
        + "\\n"
    )
    recovered = recover_literal_backslash_n_records(text)
    assert recovered == [rec1, rec2]
    json.loads(json.dumps(recovered[0], ensure_ascii=False))
    assert recovered[0]["note"] == "\u7b2c\u4e00\u884c\n\u7b2c\u4e8c\u884c"
    assert recovered[1]["note"] == "\u5b57\u9762\\n\u4fdd\u6301"


def test_recovery_rejects_ambiguous_garbage():
    with pytest.raises(CheckpointError, match="unrecoverable"):
        recover_literal_backslash_n_records('{"document_id": "doc-a"} NOT-JSON')
