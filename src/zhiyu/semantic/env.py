"""Load project .env into os.environ without logging values."""
from __future__ import annotations
import os
from pathlib import Path

ALLOWED = ("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL")


def load_project_env(root: Path) -> None:
    path = Path(root) / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if key not in ALLOWED:
            continue
        value = value.strip().strip('"').strip("'")
        if key not in os.environ:
            os.environ[key] = value


def public_llm_config() -> dict:
    return {
        "provider": "deepseek",
        "model": os.environ.get("DEEPSEEK_MODEL"),
        "base_url": os.environ.get("DEEPSEEK_BASE_URL"),
        "api_key_present": bool(os.environ.get("DEEPSEEK_API_KEY")),
    }
