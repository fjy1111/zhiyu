from zhiyu.parser.document_parser import DocumentParser

def test_preserves_syntax(tmp_path):
    path = tmp_path / "a.md"
    body = "# title\n\n<!-- comment -->\n[link](https://example.invalid)\n```\ncode\n```"
    path.write_text(body, encoding="utf-8")
    assert DocumentParser().parse(path).text == body

