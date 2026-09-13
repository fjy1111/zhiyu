from __future__ import annotations

import json
from pathlib import Path

PRESCAN_MODE = "真实预扫描结果复现"
ALLOWED_DECISIONS = {"SAFE", "REVIEW", "POISON", "CURATED_TRUSTED_SEED"}
JSONL_PATH = Path("demo/demo_knowledge_base_v2.jsonl")
CATALOG_PATH = Path("demo/final_live_scenarios.json")
TRUSTED_SEED_PATH = Path("demo/trusted_seed_manifest.json")
SCAN_PATHS = (
    Path("experiments/phase7/prescan_final.json"),
    Path("experiments/phase7/demo_synthetic_scan.json"),
)
SYNTHETIC_RUNTIME_FILES = {
    "syn-ft-library": Path("demo/attack_samples/syn-ft-library.txt"),
    "syn-ft-scholarship": Path("demo/attack_samples/syn-ft-scholarship.txt"),
    "syn-conf-exam": Path("demo/attack_samples/syn-conf-exam.txt"),
    "syn-conf-dorm": Path("demo/attack_samples/syn-conf-dorm.txt"),
    "syn-conf-scholarship": Path("demo/attack_samples/syn-conf-scholarship.txt"),
}


class MissingRuntimeDocumentError(LookupError):
    def __init__(self, scenario_id: str | None, missing: list[str]):
        self.scenario_id = scenario_id
        self.missing = tuple(missing)
        super().__init__(
            f"final scenario {scenario_id!r} references missing runtime documents: {list(self.missing)}"
        )


def repo_root(start: Path | str | None = None) -> Path:
    if start is None:
        return Path(__file__).resolve().parents[3]
    return Path(start)


def load_final_scenarios(root: Path | str | None = None) -> list[dict]:
    path = repo_root(root) / CATALOG_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise TypeError("final_live_scenarios.json must be a list")
    return payload


def load_trusted_seed_ids(root: Path | str | None = None) -> set[str]:
    payload = json.loads((repo_root(root) / TRUSTED_SEED_PATH).read_text(encoding="utf-8"))
    return {item["document_id"] for item in payload["documents"]}


def load_frozen_scan_records(root: Path | str | None = None) -> dict[str, dict]:
    root_path = repo_root(root)
    records: dict[str, dict] = {}
    for rel in SCAN_PATHS:
        payload = json.loads((root_path / rel).read_text(encoding="utf-8"))
        for item in payload["documents"]:
            document_id = item["document_id"]
            decision = item["decision"]
            if not isinstance(decision, str):
                raise TypeError(f"frozen scan decision must be a string: {document_id}")
            records[document_id] = item
    return records


def load_frozen_decisions(root: Path | str | None = None) -> dict[str, str]:
    return {document_id: item["decision"] for document_id, item in load_frozen_scan_records(root).items()}


def load_runtime_documents(root: Path | str | None = None) -> dict[str, dict]:
    root_path = repo_root(root)
    documents: dict[str, dict] = {}
    jsonl_path = root_path / JSONL_PATH
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        documents[row["demo_document_id"]] = row
    scans = load_frozen_scan_records(root_path)
    for document_id, rel in SYNTHETIC_RUNTIME_FILES.items():
        path = root_path / rel
        if not path.is_file():
            raise FileNotFoundError(f"missing Phase7 synthetic runtime document: {path}")
        if document_id not in documents:
            documents[document_id] = {
                "demo_document_id": document_id,
                "runtime_text": path.read_text(encoding="utf-8"),
                "source_path": rel.as_posix(),
                "source_category": "DEMO_SYNTHETIC",
                "mechanism": (scans.get(document_id) or {}).get("mechanism"),
                "scenario": document_id.split("-")[-1],
                "source_derived": False,
                "source_kind": "DEMO_SYNTHETIC",
            }
    return documents


def scenario_document_ids(spec: dict) -> list[str]:
    ids: list[str] = []
    for key in ("trusted_seed_document_ids", "distractor_document_ids"):
        ids.extend(spec.get(key) or [])
    incoming = spec.get("incoming_document_id")
    if incoming:
        ids.append(incoming)
    unique: list[str] = []
    for document_id in ids:
        if document_id not in unique:
            unique.append(document_id)
    return unique


def resolve_scenario_documents(spec: dict, documents: dict[str, dict]) -> list[dict]:
    ids = scenario_document_ids(spec)
    missing = [document_id for document_id in ids if document_id not in documents]
    if missing:
        raise MissingRuntimeDocumentError(spec.get("scenario_id"), missing)
    rows = []
    for document_id in ids:
        row = documents[document_id]
        if not row.get("runtime_text"):
            raise MissingRuntimeDocumentError(spec.get("scenario_id"), [document_id])
        rows.append(row)
    return rows


def build_scan_response(document_id: str, documents: dict[str, dict], scans: dict[str, dict]) -> dict | None:
    if not document_id or document_id not in documents or document_id not in scans:
        return None
    record = scans[document_id]
    document = documents[document_id]
    decision = record["decision"]
    if not isinstance(decision, str):
        raise TypeError(f"actual_decision must be a string: {document_id}")
    return {
        "document_id": document_id,
        "mechanism": record.get("mechanism") or record.get("intended_mechanism") or document.get("mechanism"),
        "actual_decision": decision,
        "prescan_mode": PRESCAN_MODE,
        "component_statuses": record.get("component_statuses"),
        "factual_evidence_summary": record.get("factual_evidence_summary"),
        "judge_status": record.get("judge_status"),
    }
