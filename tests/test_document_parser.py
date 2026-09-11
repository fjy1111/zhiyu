import pytest
from zhiyu.parser.document_parser import DocumentParser
from zhiyu.parser.base import UnsupportedFormatError

@pytest.mark.parametrize("suffix,name", [(".txt","TextParser"),(".md","MarkdownParser"),(".html","HTMLParser")])
def test_routes(tmp_path, suffix, name):
    p = tmp_path / ("a" + suffix)
    p.write_text("hello", encoding="utf-8")
    assert DocumentParser().parse(p).parser_name == name

def test_unsupported(tmp_path):
    with pytest.raises(UnsupportedFormatError):
        DocumentParser().parse(tmp_path / "a.csv")

def test_url():
    with pytest.raises(ValueError):
        DocumentParser().parse("https://example.invalid/a.txt")

def test_unc_path():
    with pytest.raises(ValueError):
        DocumentParser().parse("//server/share/document.txt")

def test_ids(make_document, tmp_path):
    first = make_document("content")
    assert first == make_document("content")
    assert first.document_id != make_document("changed").document_id
