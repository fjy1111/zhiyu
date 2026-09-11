from pypdf import PdfWriter
from zhiyu.parser.document_parser import DocumentParser
from zhiyu.parser.base import ParseError
import pytest

def test_blank_pdf_no_ocr(tmp_path):
    path = tmp_path / "blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with path.open("wb") as stream:
        writer.write(stream)
    doc = DocumentParser().parse(path)
    assert not doc.text
    assert "NO_EXTRACTABLE_TEXT" in doc.warnings

def test_corrupt_pdf(tmp_path):
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"not a pdf")
    with pytest.raises(ParseError):
        DocumentParser().parse(path)

