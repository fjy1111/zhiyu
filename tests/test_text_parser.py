from zhiyu.parser.document_parser import DocumentParser

def test_bom_and_bad_character(tmp_path):
    path = tmp_path / "t.txt"
    path.write_bytes(b"\xef\xbb\xbfA\r\nB\xff")
    doc = DocumentParser().parse(path)
    assert doc.text == "A\nB\ufffd"
    assert "INVALID_UTF8_REPLACED" in doc.warnings

def test_normalization(make_document):
    assert make_document("  中文\r\n\r\n\r\ntext  ").text == "中文\n\ntext"

