import re
from abc import ABC, abstractmethod

class UnsupportedFormatError(ValueError):
    pass

class ParseError(ValueError):
    pass

def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def decode_text(data: bytes) -> tuple[str, list[str]]:
    try:
        return data.decode("utf-8-sig"), []
    except UnicodeDecodeError:
        return data.decode("utf-8-sig", errors="replace"), ["INVALID_UTF8_REPLACED"]

class BaseParser(ABC):
    version = "1.0"
    @abstractmethod
    def extract(self, data: bytes) -> tuple[str, list[str]]:
        """Extract local bytes without executing content or fetching resources."""

