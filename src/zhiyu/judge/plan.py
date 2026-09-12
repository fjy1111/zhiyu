from __future__ import annotations
from zhiyu.models.factual import FactualRelation
from zhiyu.models.judge import Ablation, AnalysisStatusRecord, Component, DocumentEvidence, StatusKind
from zhiyu.models.semantic import SKIP_RULE_HIGH

LEGAL_SEMANTIC_SKIP = {SKIP_RULE_HIGH}


def expected_components(ablation: Ablation) -> frozenset[Component]:
    if ablation is Ablation.RULE_ONLY:
        return frozenset({Component.RULE})
    if ablation is Ablation.RULE_SEMANTIC:
        return frozenset({Component.RULE, Component.SEMANTIC})
    if ablation is Ablation.FULL_EVIDENCE:
        return frozenset({
            Component.RULE, Component.SEMANTIC, Component.FACTUAL_CLAIM,
            Component.FACTUAL_RETRIEVAL, Component.FACTUAL_COMPARE,
        })
    return frozenset({
        Component.RULE, Component.SEMANTIC, Component.FACTUAL_CLAIM,
        Component.FACTUAL_RETRIEVAL, Component.FACTUAL_COMPARE, Component.UNIFIED_JUDGE,
    })


def _status(doc: DocumentEvidence, component: Component, chunk_id: str | None = None, claim_id: str | None = None):
    hits = [
        item for item in doc.statuses
        if item.component is component
        and (chunk_id is None or item.chunk_id == chunk_id)
        and (claim_id is None or item.claim_id == claim_id)
    ]
    return hits


def unexpected_missing(doc: DocumentEvidence, ablation: Ablation) -> tuple[str, ...]:
    expected = expected_components(ablation)
    missing: list[str] = []
    if Component.RULE in expected:
        for chunk_id in doc.expected_chunk_ids:
            if not _status(doc, Component.RULE, chunk_id):
                missing.append(f"RULE:{chunk_id}")
    if Component.SEMANTIC in expected:
        for chunk_id in doc.expected_chunk_ids:
            recs = _status(doc, Component.SEMANTIC, chunk_id)
            if not recs:
                missing.append(f"SEMANTIC:{chunk_id}")
            else:
                rec = recs[0]
                if rec.status is StatusKind.SKIPPED:
                    if rec.skip_reason not in LEGAL_SEMANTIC_SKIP:
                        missing.append(f"SEMANTIC_ILLEGAL_SKIP:{chunk_id}")
    if Component.FACTUAL_CLAIM in expected:
        for chunk_id in doc.expected_chunk_ids:
            recs = _status(doc, Component.FACTUAL_CLAIM, chunk_id)
            if not recs:
                missing.append(f"FACTUAL_CLAIM:{chunk_id}")
                continue
            claim_status = recs[0]
            if claim_status.status is StatusKind.NO_CLAIM:
                continue
            if claim_status.status is StatusKind.OK and Component.FACTUAL_RETRIEVAL in expected:
                claim_ids = [ev.claim_id for ev in doc.factual_evidence if ev.chunk_id == chunk_id]
                # retrieval expected per atomic claim; if OK claims produced evidence or retrieval statuses
                retrievals = _status(doc, Component.FACTUAL_RETRIEVAL, chunk_id)
                if not retrievals and not claim_ids:
                    # OK but no claims materialized unexpectedly
                    missing.append(f"FACTUAL_RETRIEVAL:{chunk_id}")
                for rec in retrievals:
                    if rec.status is StatusKind.OK and Component.FACTUAL_COMPARE in expected:
                        if rec.claim_id and not _status(doc, Component.FACTUAL_COMPARE, chunk_id, rec.claim_id):
                            missing.append(f"FACTUAL_COMPARE:{rec.claim_id}")
                    # NO_EVIDENCE: compare not expected
    if Component.UNIFIED_JUDGE in expected:
        if not _status(doc, Component.UNIFIED_JUDGE):
            missing.append("UNIFIED_JUDGE")
    return tuple(missing)
