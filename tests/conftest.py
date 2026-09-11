import pytest
from zhiyu.parser.document_parser import DocumentParser

@pytest.fixture
def make_document(tmp_path):
    def make(text):
        path = tmp_path / "sample.txt"
        path.write_text(text, encoding="utf-8")
        return DocumentParser().parse(path)
    return make

