import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from import_poisonedrag_raw import REQUIRED_FILES, copy_frozen_files, write_provenance


def _write_json(path: Path, payload: dict) -> bytes:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    path.write_bytes(data)
    return data


def _seed_upstream(src: Path) -> dict[str, bytes]:
    results = src / "results" / "adv_targeted_results"
    results.mkdir(parents=True)
    originals = {
        "nq.json": _write_json(
            results / "nq.json",
            {
                "c1": {"id": "c1", "question": "Q1"},
                "c2": {"id": "c2", "question": "Q2"},
            },
        ),
        "hotpotqa.json": _write_json(
            results / "hotpotqa.json",
            {"h1": {"id": "h1", "question": "H1"}},
        ),
        "msmarco.json": _write_json(
            results / "msmarco.json",
            {"m1": {"id": "m1", "question": "M1"}},
        ),
    }
    license_bytes = b"MIT License\nCopyright (c) test\n"
    (src / "LICENSE").write_bytes(license_bytes)
    originals["LICENSE"] = license_bytes
    return originals


def test_copy_is_byte_identical_and_records_sha256(tmp_path: Path) -> None:
    src = tmp_path / "upstream"
    dest = tmp_path / "poisonedrag"
    originals = _seed_upstream(src)

    result = copy_frozen_files(src, dest)

    assert REQUIRED_FILES == ("nq.json", "hotpotqa.json", "msmarco.json")
    for name in REQUIRED_FILES:
        copied = (dest / "raw" / name).read_bytes()
        original = originals[name]
        assert copied == original
        row = result[name]
        assert row["sha256"] == hashlib.sha256(original).hexdigest()
        assert row["bytes"] == len(original)
        assert row["cases"] == len(json.loads(original))
    assert result["nq.json"]["cases"] == 2
    assert (dest / "SOURCE_LICENSE").read_bytes() == originals["LICENSE"]

    provenance_path = tmp_path / "poisonedrag_provenance.json"
    payload = write_provenance(
        provenance_path,
        upstream_commit="abc123",
        files=result,
        downloaded_at="2026-09-11T12:00:00+08:00",
    )
    written = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert written == payload
    assert payload["upstream_repository_url"] == "https://github.com/sleeepeer/PoisonedRAG.git"
    assert payload["upstream_commit"] == "abc123"
    assert payload["downloaded_at"] == "2026-09-11T12:00:00+08:00"
    assert payload["license"] == "MIT License"
    assert payload["files"] == result


def test_copy_refuses_overwrite(tmp_path: Path) -> None:
    src = tmp_path / "upstream"
    dest = tmp_path / "poisonedrag"
    _seed_upstream(src)
    copy_frozen_files(src, dest)
    with pytest.raises(FileExistsError):
        copy_frozen_files(src, dest)


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result


def test_copy_pins_git_blob_identity_despite_crlf_working_tree(tmp_path: Path) -> None:
    src = tmp_path / "upstream"
    dest = tmp_path / "poisonedrag"
    results = src / "results" / "adv_targeted_results"
    results.mkdir(parents=True)
    blobs = {
        "nq.json": b'{\n"c1": {"id": "c1"},\n"c2": {"id": "c2"}\n}\n',
        "hotpotqa.json": b'{"h1":{"id":"h1"}}',
        "msmarco.json": b'{"m1":{"id":"m1"}}',
        "LICENSE": b"MIT License\n",
    }
    for name in REQUIRED_FILES:
        (results / name).write_bytes(blobs[name])
    (src / "LICENSE").write_bytes(blobs["LICENSE"])
    _git(["-c", "core.autocrlf=false", "init", "-b", "main"], src)
    _git(["-c", "core.autocrlf=false", "add", "LICENSE", "results/adv_targeted_results"], src)
    _git(
        [
            "-c",
            "core.autocrlf=false",
            "-c",
            "user.email=task1@zhiyu",
            "-c",
            "user.name=task1",
            "commit",
            "-m",
            "init",
        ],
        src,
    )
    (results / "nq.json").write_bytes(blobs["nq.json"].replace(b"\n", b"\r\n"))
    (src / "LICENSE").write_bytes(blobs["LICENSE"].replace(b"\n", b"\r\n"))
    assert (results / "nq.json").read_bytes() != blobs["nq.json"]
    result = copy_frozen_files(src, dest)
    assert (dest / "raw" / "nq.json").read_bytes() == blobs["nq.json"]
    assert (dest / "SOURCE_LICENSE").read_bytes() == blobs["LICENSE"]
    assert result["nq.json"]["sha256"] == hashlib.sha256(blobs["nq.json"]).hexdigest()
    assert result["nq.json"]["cases"] == 2
