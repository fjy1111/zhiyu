from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True)
class RuntimeContext:
    request_id: str | None = None
    file_format: str | None = None

@dataclass(frozen=True)
class DetectionInput:
    document_id: str
    chunk_id: str
    text: str
    runtime: RuntimeContext | None = None

    def __post_init__(self):
        if self.runtime is not None and not isinstance(self.runtime, RuntimeContext):
            raise TypeError("runtime must be RuntimeContext")

    def to_dict(self):
        return asdict(self)
