"""Minimal real-LLM Phase 4 smoke tests. Never prints secrets."""
from zhiyu.factual.corpus import load_references
from zhiyu.factual.pipeline import FactualEvidencePipeline
from zhiyu.models.detection import DetectionInput
from zhiyu.models.factual import AtomicClaim, EvidenceRetrievalResult, RetrievalStatus, TrustedEvidenceCandidate
from zhiyu.semantic.env import load_project_env, public_llm_config
from zhiyu.factual.provider import DeepSeekFactualProvider
from _common import ROOT


def main() -> int:
    load_project_env(ROOT)
    cfg = public_llm_config()
    if not cfg["api_key_present"] or not cfg["model"]:
        print("SMOKE BLOCKED: missing DEEPSEEK_API_KEY or DEEPSEEK_MODEL")
        return 2
    provider = DeepSeekFactualProvider(temperature=0.0, max_tokens=400, timeout_sec=60, retries=1)
    refs = load_references(ROOT / "datasets/processed/phase4/references.jsonl")
    pipeline = FactualEvidencePipeline(provider, refs[:3])
    extraction = pipeline.extract(DetectionInput("smoke", "c0", "The library opens at 09:00 every weekday."))
    print("claim_smoke", extraction.status.value, len(extraction.claims))
    claim = AtomicClaim("smoke-claim", "smoke", "c0", 0, 27, "The library opens at 09:00", "The library opening time is 09:00")
    cands = []
    for ref in refs[:2]:
        cands.append(TrustedEvidenceCandidate(
            ref.reference_id, ref.document_id, ref.relative_path, ref.content_hash, 0.1,
            0, len(ref.text), ref.text,
        ))
    retrieval = EvidenceRetrievalResult(claim.claim_id, RetrievalStatus.OK, tuple(cands))
    comparison = pipeline.compare_claim(claim, retrieval)
    print("compare_smoke", comparison.status.value, len(comparison.pairs))
    print("SMOKE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
