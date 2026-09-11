"""Domain-independent records; offsets use Python Unicode character indices."""
from dataclasses import dataclass, field
from typing import Any

@dataclass
class DocumentRecord:
    document_id: str
    source_dataset: str
    source_split: str
    relative_path: str
    file_name: str
    file_format: str
    sha256: str
    text: str
    text_length: int
    parser_name: str
    parser_version: str
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.text_length != len(self.text):
            raise ValueError("text_length must match text")

@dataclass
class ChunkRecord:
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    start_char: int
    end_char: int
    text_length: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if (self.chunk_index < 0 or self.start_char < 0 or
                self.end_char <= self.start_char or not self.text.strip() or
                self.text_length != len(self.text) or
                self.end_char - self.start_char != self.text_length):
            raise ValueError("Invalid chunk offsets or text")

