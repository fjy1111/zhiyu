"""Expand official PoisonedRAG cases into evaluator records."""
from __future__ import annotations

from zhiyu.models.detection import DetectionInput

DATASETS = ("nq", "hotpotqa", "msmarco")
ATTACK_FAMILY = "KNOWLEDGE_CORRUPTION"
SOURCE = "poisonedrag"
REQUIRED_FIELDS = ("question", "correct answer", "incorrect answer", "adv_texts")


def external_sample_id(dataset: str, case_id: str, index: int) -> str:
    return f"poisonedrag:{dataset}:{case_id}:{index}"


def expand_case(dataset: str, case_id: str, case: dict) -> list[dict]:
    if not isinstance(case, dict):
        raise ValueError(f"PoisonedRAG case {dataset}:{case_id} must be an object")

    missing = [name for name in REQUIRED_FIELDS if name not in case]
    if missing:
        raise ValueError(
            f"PoisonedRAG case {dataset}:{case_id} missing required fields: {missing}"
        )

    adv_texts = case["adv_texts"]
    if not isinstance(adv_texts, list):
        raise ValueError(
            f"PoisonedRAG case {dataset}:{case_id} adv_texts must be a list"
        )

    upstream_case_id = case.get("id") or case_id
    metadata = dict(case)
    rows: list[dict] = []
    for index, text in enumerate(adv_texts):
        if not isinstance(text, str):
            raise ValueError(
                f"PoisonedRAG case {dataset}:{case_id} adv_texts[{index}] must be a str"
            )
        rows.append(
            {
                "external_sample_id": external_sample_id(dataset, upstream_case_id, index),
                "upstream_dataset": dataset,
                "upstream_case_id": upstream_case_id,
                "adv_text_index": index,
                "text": text,
                "question": case["question"],
                "correct_answer": case["correct answer"],
                "target_answer": case["incorrect answer"],
                "source": SOURCE,
                "attack_family": ATTACK_FAMILY,
                "upstream_metadata": metadata,
            }
        )
    return rows


def expand_dataset(dataset: str, data: dict) -> list[dict]:
    if not isinstance(data, dict):
        raise ValueError(f"PoisonedRAG dataset {dataset} must be an object of cases")
    rows: list[dict] = []
    for case_id in sorted(data):
        rows.extend(expand_case(dataset, case_id, data[case_id]))
    return rows


def to_detection_input(record: dict) -> DetectionInput:
    sample_id = record["external_sample_id"]
    return DetectionInput(sample_id, sample_id, record["text"])
