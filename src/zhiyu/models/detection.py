from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True)
class DetectionInput:
    document_id: str
    chunk_id: str
    text: str
    runtime: dict[str, Any] | None = None

    def to_dict(self):
        return asdict(self)
