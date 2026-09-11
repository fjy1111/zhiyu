from zhiyu.parser.document_parser import DocumentParser

def test_inert_html(tmp_path, monkeypatch):
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError("Network access")
    monkeypatch.setattr(socket, "socket", forbidden)
    path = tmp_path / "a.html"
    path.write_text('<script>EXECUTE_ME</script><style>STYLE_ME</style><p>中文 &amp; visible</p><img src="https://example.invalid/x">', encoding="utf-8")
    doc = DocumentParser().parse(path)
    assert doc.text == "中文 & visible"

