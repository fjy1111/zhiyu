from dataclasses import asdict
import pytest
from zhiyu.models.document import ChunkRecord

def test_generic_schema(make_document):
    doc = make_document("中文 and English")
    assert doc.text_length == len(doc.text)
    assert isinstance(doc.metadata, dict)
    assert "scenario" not in asdict(doc)
    other = make_document("another")
    doc.metadata["arbitrary"] = 1
    assert other.metadata == {}

def test_bad_offset():
    with pytest.raises(ValueError):
        ChunkRecord("c", "d", 0, "abc", 0, 2, 3)

