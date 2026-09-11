import json
from raw_integrity import snapshot, compare, MANIFESTS

def test_raw_unchanged():
    before = json.loads((MANIFESTS / "raw_snapshot_before.json").read_text(encoding="utf-8"))
    assert compare(before, snapshot())["pass"]
    after_path = MANIFESTS / "raw_snapshot_after.json"
    if after_path.exists():
        assert before == json.loads(after_path.read_text(encoding="utf-8"))

def test_change_detection():
    result = compare({"a":"1", "b":"2"}, {"a":"3","c":"2"})
    assert result["modified"] == ["a"]
    assert result["deleted"] == ["b"]
    assert result["added"] == ["c"]
    assert not result["pass"]
