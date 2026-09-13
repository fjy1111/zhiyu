from __future__ import annotations
import json, re
from dataclasses import dataclass
from pathlib import Path
from zhiyu.models.rag import (BuiltIndexes, GeneratorConfig, IndexedChunk, RetrieverConfig, RuntimeQuery, GenerationOutcome)
from zhiyu.rag.admission import build_indexes
from zhiyu.rag.cic import ContextIntegrityChecker
from zhiyu.rag.generate import SharedGenerator, run_protected_path, run_vanilla_path
from zhiyu.rag.retriever import SharedRetriever

FIELD_NAMES=('知识主题','报名截止时间','申请截止时间','初赛地点','考试地点','活动地点','开放时间','办理地点','申请条件','申请材料','联系方式')
def parse_fields(text):
    out={}
    for line in text.splitlines():
        if '：' in line:
            k,v=line.split('：',1); k=k.strip(); v=v.strip()
            if k in FIELD_NAMES: out[k]=v
    return out
def compare_fields(trusted,incoming):
    a,b=parse_fields(trusted),parse_fields(incoming); keys=set(a)|set(b)
    return {'identical_fields':sorted(k for k in keys if k in a and k in b and a[k]==b[k]),'changed_fields':sorted(k for k in keys if k in a and k in b and a[k]!=b[k]),'missing_fields':sorted(k for k in a if k not in b),'added_fields':sorted(k for k in b if k not in a)}

@dataclass(frozen=True)
class DemoKnowledgeBase:
    name: str
    indexes: BuiltIndexes

class DemoProvider:
    def complete(self, system_prompt: str, payload: str) -> str:
        data=json.loads(payload); chunks=data.get("chunks", [])
        if not chunks: return ""
        # Deterministic demo provider summarizes retrieved evidence; it does not inspect labels.
        text=" ".join(c["text"] for c in chunks)
        return "根据检索证据：" + text[:240]

def load_demo_knowledge_base(path: Path | str | None = None, scenario: str = "normal") -> DemoKnowledgeBase:
    path=Path(path or Path(__file__).resolve().parents[3]/"demo/demo_knowledge_base_v2.jsonl")
    rows=[json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    truth_path=path.parent / "../experiments/phase7/prescan_final.json"
    truth_file=Path(__file__).resolve().parents[3]/"experiments/phase7/prescan_final.json"
    truth={x["document_id"]:x for x in json.loads(truth_file.read_text(encoding="utf-8"))["documents"]}
    chunks=tuple(IndexedChunk(r["demo_document_id"], r["demo_document_id"]+":0", r["runtime_text"]) for r in rows)
    seed_file=Path(__file__).resolve().parents[3]/"demo/trusted_seed_manifest.json"
    trusted={r["document_id"] for r in json.loads(seed_file.read_text(encoding="utf-8"))["documents"]}
    decisions={r["demo_document_id"]: ("SAFE" if r["demo_document_id"] in trusted else truth.get(r["demo_document_id"],{}).get("decision","REVIEW")) for r in rows}
    from zhiyu.models.detection import Decision
    indexes=build_indexes(chunks,{k:Decision(v) for k,v in decisions.items()},RetrieverConfig(k=3))
    return DemoKnowledgeBase("DEMO", indexes)

def build_scenario_knowledge_base(rows, trusted_ids, truth):
    from zhiyu.models.detection import Decision
    chunks=tuple(IndexedChunk(r['demo_document_id'], r['demo_document_id']+':0', r['runtime_text']) for r in rows)
    decisions={r['demo_document_id']: ('SAFE' if r['demo_document_id'] in trusted_ids else truth.get(r['demo_document_id'],'REVIEW')) for r in rows}
    return DemoKnowledgeBase('SCENARIO', build_indexes(chunks,{k:Decision(v) for k,v in decisions.items()},RetrieverConfig(k=5)))

class DemoApplication:
    def __init__(self, kb: DemoKnowledgeBase | None = None):
        config=GeneratorConfig("demo-deterministic", "Answer only from retrieved evidence.")
        self.generator=SharedGenerator(config, DemoProvider())
        self.cic=ContextIntegrityChecker()
    def run(self, query_text: str, scenario_id: str | None = None) -> dict:
        if not isinstance(query_text,str) or not query_text.strip(): raise ValueError("query_text must be non-empty")
        q=RuntimeQuery("demo-query",query_text.strip())
        scenario = scenario_id
        catalog= json.loads((Path(__file__).resolve().parents[3]/"demo/final_live_scenarios.json").read_text(encoding="utf8"))
        spec=next((x for x in catalog if x["scenario_id"]==scenario), None)
        if spec:
            allrows=[json.loads(x) for x in (Path(__file__).resolve().parents[3]/"demo/demo_knowledge_base_v2.jsonl").read_text(encoding="utf8").splitlines()]
            ids=set(spec["trusted_seed_document_ids"]+([spec["incoming_document_id"]] if spec.get("incoming_document_id") else [])+spec.get("distractor_document_ids",[]))
            rows=[r for r in allrows if r["demo_document_id"] in ids]
            seed_file=Path(__file__).resolve().parents[3]/"demo/trusted_seed_manifest.json"
            trusted_ids={x['document_id'] for x in json.loads(seed_file.read_text(encoding='utf8'))['documents']}
            truth_file=Path(__file__).resolve().parents[3]/"experiments/phase7/prescan_final.json"
            truth={x['document_id']:x['decision'] for x in json.loads(truth_file.read_text(encoding='utf8'))['documents']}
            kb=build_scenario_knowledge_base(rows,trusted_ids,truth)
            scenario=spec["scenario_id"]
        else: raise ValueError("scenario_id is required and must be valid")
        self.retriever = SharedRetriever(self.kb.indexes.config)
        retriever=SharedRetriever(kb.indexes.config)
        result={"scenario_id":scenario, "query":query_text.strip(), "vanilla":self._path(q,"vanilla",kb,retriever), "protected":self._path(q,"protected",kb,retriever), "admission":{"protected_documents":len(kb.indexes.protected.document_ids),"quarantined_documents":len(kb.indexes.vanilla.document_ids-kb.indexes.protected.document_ids)}}
        return result
    def _path(self,q,path,kb,retriever):
        index=getattr(kb.indexes,path); retrieval=retriever.retrieve(q,index)
        outcome=(run_vanilla_path(q,retrieval,self.generator) if path=="vanilla" else run_protected_path(q,retrieval,self.generator,self.cic))
        docs=[]
        for h in retrieval.hits: docs.append({"document_id":h.document_id,"chunk_id":h.chunk_id,"text":h.text,"score":h.score})
        payload={"retrieval_status":retrieval.status.value,"chunks":docs,"generation":outcome.to_runtime_dict()}
        if path=="protected": payload["cic"]=outcome.cic.to_runtime_dict() if outcome.cic else None
        return payload
