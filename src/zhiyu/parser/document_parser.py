import hashlib
from pathlib import Path
from ..models.document import DocumentRecord
from .base import ParseError, UnsupportedFormatError, normalize
from .text_parser import TextParser
from .markdown_parser import MarkdownParser
from .html_parser import HTMLParser
from .pdf_parser import PDFParser
from .docx_parser import DOCXParser

class DocumentParser:
    routes = {".txt": TextParser, ".md": MarkdownParser, ".html": HTMLParser,
              ".pdf": PDFParser, ".docx": DOCXParser}

    def parse(self, path, *, source_dataset="", source_split="", relative_path=None):
        path_string = str(path)
        if "://" in path_string or path_string.startswith(("//", "\\\\")):
            raise ValueError("Only local file paths are accepted")
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix not in self.routes:
            raise UnsupportedFormatError(suffix)
        data = path.read_bytes()
        parser = self.routes[suffix]()
        try:
            text, warnings = parser.extract(data)
        except Exception as exc:
            # Do not include document body or third-party exception messages.
            raise ParseError(f"{parser.__class__.__name__}: {type(exc).__name__}") from None
        text = normalize(text)
        if not text and "NO_EXTRACTABLE_TEXT" not in warnings:
            warnings.append("NO_EXTRACTABLE_TEXT")
        sha = hashlib.sha256(data).hexdigest()
        rel = relative_path or path.name
        identity = "\0".join((source_dataset, source_split, rel, sha))
        return DocumentRecord(hashlib.sha256(identity.encode()).hexdigest(),
                              source_dataset, source_split, rel, path.name,
                              suffix, sha, text, len(text), type(parser).__name__,
                              parser.version, warnings=warnings)
