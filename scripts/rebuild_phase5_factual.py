"""Rebuild only the factual layer of an existing Phase 5 bundle (LLM when executed)."""
from __future__ import annotations
import argparse, json, subprocess, yaml
from pathlib import Path
from collections import defaultdict
from _common import ROOT, write_json
from zhiyu.eval.phase4 import load_phase4_split
from zhiyu.factual.corpus import load_references, sha256_file
from zhiyu.factual.pipeline import FactualEvidencePipeline
from zhiyu.factual.provider import DeepSeekFactualProvider
from zhiyu.judge.bundle import load_bundle
from zhiyu.models.detection import DetectionInput
from zhiyu.models.judge import AnalysisStatusRecord, Component, DocumentEvidence, StatusKind

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='datasets/processed/phase5/evidence_bundle_replacement.jsonl'); parser.add_argument('--manifest',default='datasets/manifests/phase5_evidence_bundle_replacement_manifest.json'); args=parser.parse_args()
    old_path=ROOT/'datasets/processed/phase5/evidence_bundle.jsonl'; old=load_bundle(old_path)
    by_id={d.document_id:d for d in old}; refs=load_references(ROOT/'datasets/processed/phase4/references.jsonl')
    factual=FactualEvidencePipeline(DeepSeekFactualProvider(temperature=0.0,max_tokens=800,timeout_sec=60,retries=1),refs)
    rows=[]; grouped=defaultdict(list); meta={}
    for split in ('development_tune','development_generalization'):
        for did,item,path,digest in load_phase4_split(ROOT,split): grouped[did].append(item); meta[did]=(path,digest)
    for did, chunks in grouped.items():
        if did not in by_id: continue
        old_doc=by_id[did]; path,digest=meta[did]; facts=[]; new_status=[]
        for item in chunks:
            result=factual.process_chunk(item,path,digest); facts.extend(result.factual_evidence)
            new_status.extend([AnalysisStatusRecord(Component.FACTUAL_CLAIM,StatusKind(result.extraction.status.value),result.extraction.status.value!='NO_CLAIM',error_code=result.extraction.error_code,chunk_id=item.chunk_id)])
            new_status.extend(AnalysisStatusRecord(Component.FACTUAL_RETRIEVAL,StatusKind(x.status.value),True,error_code=x.error_code,chunk_id=item.chunk_id,claim_id=x.claim_id) for x in result.retrievals)
            new_status.extend(AnalysisStatusRecord(Component.FACTUAL_COMPARE,StatusKind(x.status.value),True,error_code=x.error_code,chunk_id=item.chunk_id,claim_id=x.claim_id) for x in result.comparisons)
        statuses=tuple(s for s in old_doc.statuses if s.component not in {Component.FACTUAL_CLAIM,Component.FACTUAL_RETRIEVAL,Component.FACTUAL_COMPARE})+tuple(new_status)
        rows.append(DocumentEvidence(did,old_doc.expected_chunk_ids,old_doc.rule_events,old_doc.behavior_evidence,tuple(facts),statuses).to_runtime_dict())
    out=ROOT/args.output; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    p3=yaml.safe_load((ROOT/'configs/phase3_eval.yaml').read_text(encoding='utf8')); p4=json.loads((ROOT/'experiments/phase4/factual_evidence.json').read_text(encoding='utf8')); p4c=p4['config']
    write_json(ROOT/args.manifest,{'supersedes_bundle_sha':sha256_file(old_path),'bundle_sha256':sha256_file(out),'phase2_frozen_commit':p3['phase2_commit'],'phase3':{'commit':p3['phase2_commit'],'model':p3.get('model'),'prompt_version':p3['prompt_version'],'config':'configs/phase3_eval.yaml'},'phase4':{'implementation_commit':p4c['evaluation_code_commit'],'model':p4c['model'],'claim_prompt_version':p4c['claim_prompt_version'],'compare_prompt_version':p4c['compare_prompt_version'],'config':'experiments/phase4/factual_evidence.json','reference_corpus_sha256':p4c['reference_corpus_sha256']},'reused_layers':['rule','semantic'],'recomputed_layers':['factual'],'execution_plan_version':'phase5.execution_plan.v1','rule_event_ref_version':'phase5.rule_event_ref.v1'})
    return 0

if __name__ == '__main__': raise SystemExit(main())
