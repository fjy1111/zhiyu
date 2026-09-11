from pathlib import Path
import pytest
from zhiyu.dataset import DatasetPolicy, build_records, FROZEN, EVALUATION
ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize("split", FROZEN + EVALUATION)
def test_blocked(split):
    policy = DatasetPolicy(ROOT)
    with pytest.raises(PermissionError):
        list(policy.files(split))
    with pytest.raises(PermissionError):
        policy.metadata(split)

def test_build_read_boundary(monkeypatch):
    # Instrument all pathlib reads: no held-out or aggregate metadata may be opened.
    original = Path.open
    accessed = []
    raw = ROOT / "datasets/raw/trusted_provenance"
    def guarded(path, *args, **kwargs):
        if path.is_relative_to(raw):
            rel = path.relative_to(raw).as_posix()
            assert rel.startswith(("demo_set/", "dev_set/")) or rel in {
                "metadata/demo_set_metadata.json", "metadata/dev_set_metadata.json"}
            accessed.append(rel)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    documents, chunks = build_records(ROOT)
    assert len(documents) == 180
    assert {d.source_split for d in documents} == {"demo_set", "dev_set"}
    assert all(d.metadata["attack_type"] is None for d in documents)
    ids = {d.document_id for d in documents}
    assert all(c.document_id in ids for c in chunks)
    assert accessed

def test_policy_tampering(tmp_path):
    import yaml
    config = yaml.safe_load((ROOT / "configs/dataset_policy.yaml").read_text(encoding="utf-8"))
    config["development"].append("blind_test_set")
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/dataset_policy.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError):
        DatasetPolicy(tmp_path)

