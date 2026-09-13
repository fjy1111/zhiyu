"""Sparse-clone official PoisonedRAG files and freeze byte-identical copies."""
from __future__ import annotations

import hashlib
import json
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_URL = "https://github.com/sleeepeer/PoisonedRAG.git"
REQUIRED_FILES = ("nq.json", "hotpotqa.json", "msmarco.json")
DEST_ROOT = ROOT / "datasets" / "external_frozen" / "poisonedrag"
PROVENANCE_PATH = ROOT / "datasets" / "manifests" / "poisonedrag_provenance.json"
SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")
GIT_IDENTITY = ("-c", "core.autocrlf=false", "-c", "core.eol=lf")
BLOB_PATHS = {
    "nq.json": "results/adv_targeted_results/nq.json",
    "hotpotqa.json": "results/adv_targeted_results/hotpotqa.json",
    "msmarco.json": "results/adv_targeted_results/msmarco.json",
    "LICENSE": "LICENSE",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now_shanghai() -> datetime:
    return datetime.now(SHANGHAI)


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def _run_git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed ({result.returncode}): {detail}")
    return result


def _git_blob(repo: Path, relative: str) -> bytes:
    posix = relative.replace("\\", "/")
    oid = _run_git(["rev-parse", f"HEAD:{posix}"], cwd=repo).stdout.strip()
    result = subprocess.run(
        ["git", "cat-file", "blob", oid],
        cwd=repo,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or b"").decode("utf-8", "replace").strip()
        raise RuntimeError(f"git cat-file blob {oid} failed ({result.returncode}): {detail}")
    return result.stdout


def _read_upstream_file(upstream_root: Path, relative: str) -> bytes:
    if _is_git_repo(upstream_root):
        return _git_blob(upstream_root, relative)
    return (upstream_root / relative).read_bytes()


def copy_frozen_files(upstream_root: Path, dest_root: Path) -> dict:
    upstream_root = Path(upstream_root)
    dest_root = Path(dest_root)
    raw_dir = dest_root / "raw"
    existing = [name for name in REQUIRED_FILES if (raw_dir / name).exists()]
    if existing:
        raise FileExistsError(
            f"Refusing to overwrite existing frozen files: {existing}"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, dict] = {}
    for name in REQUIRED_FILES:
        data = _read_upstream_file(upstream_root, BLOB_PATHS[name])
        (raw_dir / name).write_bytes(data)
        result[name] = {
            "sha256": _sha256(data),
            "bytes": len(data),
            "cases": len(json.loads(data)),
        }

    license_bytes = _read_upstream_file(upstream_root, BLOB_PATHS["LICENSE"])
    (dest_root / "SOURCE_LICENSE").write_bytes(license_bytes)
    return result


def verify_copied_blobs(upstream_root: Path, dest_root: Path) -> None:
    dest_root = Path(dest_root)
    for name in REQUIRED_FILES:
        copied = (dest_root / "raw" / name).read_bytes()
        blob = _git_blob(upstream_root, BLOB_PATHS[name])
        if copied != blob:
            raise RuntimeError(
                f"{name} is not byte-identical to git blob {BLOB_PATHS[name]}"
            )
    copied_license = (dest_root / "SOURCE_LICENSE").read_bytes()
    license_blob = _git_blob(upstream_root, BLOB_PATHS["LICENSE"])
    if copied_license != license_blob:
        raise RuntimeError("SOURCE_LICENSE is not byte-identical to git blob LICENSE")


def write_provenance(
    path: Path,
    *,
    upstream_commit: str,
    files: dict,
    downloaded_at: str | None = None,
    upstream_repository_url: str = UPSTREAM_URL,
) -> dict:
    payload = {
        "upstream_repository_url": upstream_repository_url,
        "upstream_commit": upstream_commit,
        "downloaded_at": downloaded_at or _now_shanghai().isoformat(),
        "license": "MIT License",
        "files": files,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return payload


def write_source_md(path: Path, *, upstream_commit: str, downloaded_at: datetime) -> None:
    date = downloaded_at.date().isoformat()
    path.write_text(
        "\n".join(
            [
                "# PoisonedRAG 外部冻结数据来源",
                "",
                f"- 数据来源仓库 URL：<{UPSTREAM_URL}>",
                "- 仓库名称：`PoisonedRAG`",
                f"- 下载时的 commit hash：`{upstream_commit}`",
                f"- 下载日期：{date}（Asia/Shanghai）",
                "- 原仓库 LICENSE 类型：MIT License（许可证副本见同目录 `SOURCE_LICENSE`）",
                "- 冻结文件：",
                "  - `results/adv_targeted_results/nq.json`",
                "  - `results/adv_targeted_results/hotpotqa.json`",
                "  - `results/adv_targeted_results/msmarco.json`",
                "",
                "本目录仅作为知御 Phase 1.6 的 external_frozen 评估数据。",
                "原始 JSON 按下载时字节原样保留，禁止改写；不得写入 datasets/raw/trusted_provenance。",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _rmtree(path: Path) -> None:
    if not path.exists():
        return

    def _onexc(func, item, exc):
        try:
            Path(item).chmod(stat.S_IWRITE)
            func(item)
        except OSError:
            pass

    shutil.rmtree(path, onexc=_onexc)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def sparse_clone(url: str, dest: Path) -> str:
    _run_git([*GIT_IDENTITY, "clone", "--filter=blob:none", "--sparse", url, str(dest)])
    _run_git([*GIT_IDENTITY, "config", "core.autocrlf", "false"], cwd=dest)
    _run_git([*GIT_IDENTITY, "config", "core.eol", "lf"], cwd=dest)
    # Cone mode already includes root files such as LICENSE. Passing LICENSE to
    # sparse-checkout set fails because Git treats it as a directory.
    _run_git(
        [*GIT_IDENTITY, "sparse-checkout", "set", "results/adv_targeted_results"],
        cwd=dest,
    )
    return _run_git(["rev-parse", "HEAD"], cwd=dest).stdout.strip()


def main() -> int:
    raw_dir = DEST_ROOT / "raw"
    existing = [name for name in REQUIRED_FILES if (raw_dir / name).exists()]
    if existing:
        raise FileExistsError(
            f"Refusing to overwrite existing frozen files: {existing}"
        )

    tmp = Path(tempfile.mkdtemp(prefix="poisonedrag-upstream-"))
    clone_dir = tmp / "PoisonedRAG"
    try:
        commit = sparse_clone(UPSTREAM_URL, clone_dir)
        files = copy_frozen_files(clone_dir, DEST_ROOT)
        verify_copied_blobs(clone_dir, DEST_ROOT)
        downloaded_at = _now_shanghai()
        write_source_md(
            DEST_ROOT / "SOURCE.md",
            upstream_commit=commit,
            downloaded_at=downloaded_at,
        )
        write_provenance(
            PROVENANCE_PATH,
            upstream_commit=commit,
            files=files,
            downloaded_at=downloaded_at.isoformat(),
        )
        license_bytes = (DEST_ROOT / "SOURCE_LICENSE").read_bytes()
        print(
            json.dumps(
                {
                    "upstream_commit": commit,
                    "files": files,
                    "license": {
                        "sha256": _sha256(license_bytes),
                        "bytes": len(license_bytes),
                    },
                },
                ensure_ascii=False,
            )
        )
        return 0
    finally:
        _rmtree(tmp)


if __name__ == "__main__":
    raise SystemExit(main())
