"""Policy-enforced dataset access. Audit is the only held-out text-hash path."""
import json
from pathlib import Path
import yaml
from .parser.document_parser import DocumentParser

DEVELOPMENT = ("demo_set", "dev_set")
EVALUATION = ("stress_set",)
FROZEN = ("blind_test_set", "third_party_blind_set", "third_party_blind_process_validation_set")
FORMAT = ("file_format_test",)

class DatasetPolicy:
    def __init__(self, project):
        self.project = Path(project).resolve()
        self.raw = self.project / "datasets/raw/trusted_provenance"
        self.config = yaml.safe_load((self.project / "configs/dataset_policy.yaml").read_text(encoding="utf-8"))
        for key, expected in [("development", DEVELOPMENT), ("evaluation_only", EVALUATION),
                              ("frozen_holdout", FROZEN), ("format_test", FORMAT)]:
            if self.config[key] != list(expected):
                raise ValueError(f"Phase 1 policy change requires review: {key}")
        expected_metadata = {s: f"metadata/{s}_metadata.json" for s in DEVELOPMENT}
        if self.config["metadata"] != expected_metadata:
            raise ValueError("Only split-specific development metadata is permitted")

    def checked(self, path):
        path = Path(path)
        rel = path.relative_to(self.raw)
        current = self.raw
        if current.is_symlink():
            raise ValueError("Symlink raw roots are forbidden")
        for part in rel.parts:
            current = current / part
            if current.is_symlink():
                raise ValueError("Symlinks are forbidden")
        if not path.resolve().is_relative_to(self.raw.resolve()):
            raise ValueError("Path escapes dataset")
        return path

    def files(self, split, purpose="development"):
        allowed = {"development": DEVELOPMENT, "validation": DEVELOPMENT + FORMAT,
                   "audit": DEVELOPMENT + EVALUATION + FROZEN + FORMAT}
        if purpose not in allowed or split not in allowed[purpose]:
            raise PermissionError("Split is not allowed for this operation")
        directory = self.checked(self.raw / split)
        if not directory.is_dir():
            raise FileNotFoundError(split)
        # Do not follow symlink directories; reject them even if their files are absent.
        for p in sorted(directory.rglob("*")):
            self.checked(p)
            if p.is_file():
                yield p

    def metadata(self, split):
        if split not in DEVELOPMENT:
            raise PermissionError("Held-out metadata access forbidden")
        path = self.checked(self.raw / self.config["metadata"][split])
        rows = json.loads(path.read_text(encoding="utf-8"))
        records = {}
        for row in rows:
            rel = row["relative_path"]
            if row["split"] != split or Path(rel).parts[0] != split or ".." in Path(rel).parts:
                raise ValueError("Metadata split/path mismatch")
            if rel in records:
                raise ValueError("Duplicate metadata path")
            records[rel] = row
        return records

def build_records(project):
    from .parser.chunker import Chunker
    policy = DatasetPolicy(project)
    config = yaml.safe_load((policy.project / "configs/chunking.yaml").read_text(encoding="utf-8"))
    chunker = Chunker(**config)
    parser = DocumentParser()
    documents, chunks = [], []
    for split in DEVELOPMENT:
        metadata = policy.metadata(split)
        for path in policy.files(split):
            if path.suffix.lower() not in parser.routes:
                continue
            rel = path.relative_to(policy.raw).as_posix()
            document = parser.parse(path, source_dataset="trusted_provenance",
                                    source_split=split, relative_path=rel)
            row = metadata.get(rel)
            if row is None:
                raise ValueError(f"Missing development metadata: {rel}")
            document.metadata = {k: v for k, v in row.items()
                                 if k not in {"label", "split", "relative_path"}}
            document.metadata["original_label"] = row.get("label")
            document.metadata["attack_type"] = None
            documents.append(document)
            chunks.extend(chunker.chunk(document))
    return documents, chunks

