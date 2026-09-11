import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "datasets/manifests"

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

