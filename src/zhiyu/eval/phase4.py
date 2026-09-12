"""Phase 4 evaluator. Ground truth stays out of extractor/retriever/comparer."""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
from zhiyu.factual.corpus import load_jsonl, load_references
from zhiyu.factual.pipeline import FactualEvidencePipeline
from zhiyu.models.detection import DetectionInput
from zhiyu.models.factual import ClaimStatus, ComparisonStatus, RetrievalStatus

PHASE4 = Path("datasets/processed/phase4")


def load_phase4_split(project: Path, split: str) -> list[tuple[str, DetectionInput, str, str]]:
    if split not in {"development_tune", "development_generalization"}:
        raise PermissionError(f"split not allowed: {split}")
    root = Path(project)
    docs = {row["document_id"]: row for row in load_jsonl(root / "datasets/processed/phase4" / f"candidate_{split}_documents.jsonl")}
    rows = []
    for chunk in load_jsonl(root / "datasets/processed/phase4" / f"candidate_{split}_chunks.jsonl"):
        parent = docs[chunk["document_id"]]
        item = DetectionInput(chunk["document_id"], chunk["chunk_id"], chunk["text"])
        dumped = item.to_dict()
        for forbidden in ("original_label", "facts", "attack_type", "target_answer"):
            if forbidden in dumped:
                raise RuntimeError("ground truth leaked into DetectionInput")
        rows.append((chunk["document_id"], item, parent.get("relative_path", ""), parent.get("content_hash", "")))
    return rows


def summarize_phase4(results: list[dict]) -> dict:
    extract = Counter()
    retrieval = Counter()
    pairwise = Counter()
    comparison = Counter()
    relations = Counter()
    claims = overlap = llm = 0
    for row in results:
        extract[row["extraction_status"]] += 1
        claims += row["claim_count"]
        llm += row["llm_calls"]
        for item in row["retrievals"]:
            retrieval[item["status"]] += 1
            overlap += item.get("overlap_rejected", 0)
        for item in row["comparisons"]:
            comparison[item["status"]] += 1
            if item["status"] == ComparisonStatus.OK.value:
                for pair in item["pairs"]:
                    pairwise[pair["relation"]] += 1
        for evidence in row["factual_evidence"]:
            relations[evidence["relation"]] += 1
    return {
        "documents": len(results),
        "claim_extraction_status_counts": dict(extract),
        "claim_count": claims,
        "retrieval_status_counts": dict(retrieval),
        "overlap_rejection_count": overlap,
        "pairwise_relation_counts": dict(pairwise),
        "comparison_status_counts": dict(comparison),
        "factual_evidence_relation_counts": dict(relations),
        "llm_call_count": llm,
    }


def evaluate_split(project: Path, split: str, pipeline: FactualEvidencePipeline) -> dict:
    include_details = split == "development_tune"
    rows = []
    for document_id, item, path, digest in load_phase4_split(project, split):
        result = pipeline.process_chunk(item, path, digest)
        row = {
            "document_id": document_id,
            "extraction_status": result.extraction.status.value,
            "claim_count": len(result.extraction.claims),
            "llm_calls": result.llm_calls,
            "retrievals": [item.to_dict() for item in result.retrievals],
            "comparisons": [item.to_dict() for item in result.comparisons],
            "factual_evidence": [item.to_dict() for item in result.factual_evidence],
        }
        rows.append(row)
    summary = summarize_phase4(rows)
    if include_details:
        summary["details"] = [
            {
                "document_id": row["document_id"],
                "extraction_status": row["extraction_status"],
                "claim_count": row["claim_count"],
                "relations": [item["relation"] for item in row["factual_evidence"]],
            }
            for row in rows
        ]
    return summary
