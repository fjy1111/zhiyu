from io import BytesIO
from pypdf import PdfReader
from .base import BaseParser

class PDFParser(BaseParser):
    def extract(self, data):
        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        warnings = [f"PAGE_{i + 1}_NO_EXTRACTABLE_TEXT"
                    for i, text in enumerate(pages) if not text.strip()]
        if not any(text.strip() for text in pages):
            warnings.append("NO_EXTRACTABLE_TEXT")
        return "\n\n".join(pages), warnings

