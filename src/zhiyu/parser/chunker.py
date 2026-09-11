import hashlib
from ..models.document import ChunkRecord

class Chunker:
    def __init__(self, chunk_size_chars=1200, chunk_overlap_chars=200,
                 prefer_paragraph_boundary=True):
        if not 0 <= chunk_overlap_chars < chunk_size_chars:
            raise ValueError("Require 0 <= overlap < size")
        self.size = chunk_size_chars
        self.overlap = chunk_overlap_chars
        self.paragraphs = prefer_paragraph_boundary

    def chunk(self, document):
        text = document.text
        result = []
        start = 0
        while start < len(text):
            end = min(start + self.size, len(text))
            if self.paragraphs and end < len(text):
                boundary = text.rfind("\n\n", start + self.overlap + 1, end)
                if boundary >= 0:
                    end = boundary + 2
            fragment = text[start:end]
            if fragment.strip():
                index = len(result)
                identity = f"{document.document_id}:{index}:{start}:{end}:{self.size}:{self.overlap}:{self.paragraphs}"
                result.append(ChunkRecord(
                    hashlib.sha256(identity.encode()).hexdigest(),
                    document.document_id, index, fragment, start, end, len(fragment)))
            if end == len(text):
                break
            start = end - self.overlap
        return result

