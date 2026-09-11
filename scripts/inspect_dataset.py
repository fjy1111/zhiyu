#!/usr/bin/env python3
"""Read-only inventory and integrity checks for the trusted_provenance dataset.

The scanner never changes files below the raw-data directory.  By default,
project provenance files (SOURCE.md, SOURCE_LICENSE) and .gitkeep scaffolding
are reported as scanned metadata but excluded from dataset statistics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


PROVENANCE_FILES = {"SOURCE.md", "SOURCE_LICENSE"}
SCAFFOLD_FILES = {".gitkeep"}


def default_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def iter_files(root: Path) -> list[Path]:
    """Return regular files below *root* in deterministic relative order."""
    files: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root, followlinks=False):
        base = Path(dirpath)
        for filename in filenames:
            path = base / filename
            # A symlink to a regular file is still scanned, but broken links
            # are skipped and surfaced through the normal filesystem errors.
            if path.is_file() or path.is_symlink():
                files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix().casefold())


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_project_metadata(path: Path, root: Path) -> bool:
    """Identify files created for project bookkeeping, not source samples."""
    rel = path.relative_to(root)
    return (len(rel.parts) == 1 and rel.name in PROVENANCE_FILES) or (
        rel.name in SCAFFOLD_FILES
    )


def root_label(root: Path) -> str:
    """Use a portable project-relative root in manifests when possible."""
    project_root = default_project_root().resolve()
    try:
        return root.relative_to(project_root).as_posix()
    except ValueError:
        return root.as_posix()


def infer_source_metadata(root: Path) -> tuple[str | None, str | None]:
    """Read provenance values without touching any dataset sample."""
    source_note = root / "SOURCE.md"
    try:
        text = source_note.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None, None
    commit_match = re.search(r"commit hash[^`]*`([0-9a-fA-F]{40})`", text)
    date_match = re.search(r"下载日期：([0-9]{4}-[0-9]{2}-[0-9]{2})", text)
    commit = commit_match.group(1).lower() if commit_match else None
    date = date_match.group(1) if date_match else None
    return commit, date


def extension_for(path: Path) -> str:
    suffix = path.suffix.lower()
    return suffix if suffix else "[no_extension]"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_inventory(root: Path, source_commit: str | None = None, download_date: str | None = None) -> dict:
    if not root.exists():
        raise FileNotFoundError(f"Dataset root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Dataset root is not a directory: {root}")

    all_files = iter_files(root)
    metadata_files: list[str] = []
    dataset_files: list[Path] = []
    for path in all_files:
        rel = relative_path(path, root)
        if is_project_metadata(path, root):
            metadata_files.append(rel)
        else:
            dataset_files.append(path)

    directories: set[str] = {"."}
    for dirpath, dirnames, _filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        directories.add(relative_path(current, root) if current != root else ".")
        for dirname in dirnames:
            directories.add(relative_path(current / dirname, root))

    directory_counts: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    empty_files: list[str] = []
    hash_groups: defaultdict[str, list[str]] = defaultdict(list)
    scan_errors: list[dict[str, str]] = []

    for path in dataset_files:
        rel = relative_path(path, root)
        try:
            size = path.stat().st_size
            if size == 0:
                empty_files.append(rel)
            extension_counts[extension_for(path)] += 1
            directory_counts["."] += 1
            parent = path.parent
            while parent != root and root in parent.parents:
                directory_counts[relative_path(parent, root)] += 1
                parent = parent.parent
            hash_groups[sha256_file(path)].append(rel)
        except (OSError, ValueError) as exc:
            scan_errors.append({"file": rel, "error": str(exc)})

    duplicate_groups = {
        digest: sorted(paths)
        for digest, paths in sorted(hash_groups.items())
        if len(paths) > 1
    }
    directory_counts = Counter({name: directory_counts.get(name, 0) for name in directories})

    inventory = {
        "source": "trusted_provenance",
        "source_commit": source_commit,
        "download_date": download_date,
        "root": root_label(root),
        # total_files and the following two maps describe copied source data;
        # scanned_files makes the treatment of provenance metadata explicit.
        "total_files": len(dataset_files),
        "scanned_files": len(all_files),
        "metadata_files": sorted(metadata_files),
        "directories": dict(sorted(directory_counts.items())),
        "extensions": dict(sorted(extension_counts.items())),
        "empty_files": sorted(empty_files),
        "duplicate_sha256": duplicate_groups,
        "scan_errors": scan_errors,
    }
    return inventory


def print_report(inventory: dict) -> None:
    print(f"Dataset root: {inventory['root']}")
    print(f"Scanned files (all): {inventory['scanned_files']}")
    print(
        "Dataset files (excluding provenance/scaffolding): "
        f"{inventory['total_files']}"
    )
    metadata = inventory.get("metadata_files", [])
    print(f"Metadata/scaffolding excluded from dataset counts: {len(metadata)}")

    print("Files by top-level directory (recursive):")
    top_level = {
        name: count
        for name, count in inventory["directories"].items()
        if name != "." and "/" not in name
    }
    for name, count in top_level.items():
        print(f"  {name}: {count}")

    print("Files by extension:")
    for extension, count in inventory["extensions"].items():
        print(f"  {extension}: {count}")

    empty_files = inventory.get("empty_files", [])
    print(f"Empty dataset files: {len(empty_files)}")
    if empty_files:
        for name in empty_files:
            print(f"  {name}")

    duplicate_groups = inventory.get("duplicate_sha256", {})
    duplicate_file_count = sum(len(paths) for paths in duplicate_groups.values())
    print(
        "Duplicate SHA256 groups: "
        f"{len(duplicate_groups)} (files in groups: {duplicate_file_count})"
    )
    if duplicate_groups:
        for digest, paths in duplicate_groups.items():
            print(f"  {digest}: {len(paths)} files")

    errors = inventory.get("scan_errors", [])
    print(f"Scan errors: {len(errors)}")
    for error in errors:
        print(f"  {error['file']}: {error['error']}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=default_project_root() / "datasets" / "raw" / "trusted_provenance",
        help="raw dataset directory (default: project datasets/raw/trusted_provenance)",
    )
    parser.add_argument("--source-commit", help="commit hash to record in a manifest")
    parser.add_argument("--download-date", help="download date to record in a manifest")
    parser.add_argument(
        "--manifest",
        type=Path,
        help="optional JSON path to write the generated inventory; raw data is never written",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    inferred_commit, inferred_date = infer_source_metadata(root)
    source_commit = args.source_commit or inferred_commit
    download_date = args.download_date or inferred_date
    try:
        inventory = build_inventory(root, source_commit, download_date)
    except (OSError, ValueError) as exc:
        print(f"Dataset inspection failed: {exc}", file=sys.stderr)
        return 1

    print_report(inventory)
    if args.manifest:
        manifest = args.manifest.expanduser().resolve()
        try:
            if root == manifest or root in manifest.parents:
                raise ValueError("manifest must be outside the raw dataset directory")
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(
                json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Inventory written: {manifest}")
        except OSError as exc:
            print(f"Could not write manifest: {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"Could not write manifest: {exc}", file=sys.stderr)
            return 1
    return int(bool(inventory["scan_errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
