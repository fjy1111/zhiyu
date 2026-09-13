from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from zhiyu.models.detection import Decision
from zhiyu.models.rag import (BuiltIndexes, GeneratorConfig, IndexedChunk, RetrieverConfig, RuntimeQuery)
from zhiyu.rag.admission import build_indexes
from zhiyu.rag.cic import ContextIntegrityChecker
from zhiyu.rag.generate import SharedGenerator, run_protected_path, run_vanilla_path
from zhiyu.rag.retriever import SharedRetriever
from zhiyu.demo.runtime_documents import (
    load_final_scenarios,
    load_frozen_decisions,
    load_runtime_documents,
    load_trusted_seed_ids,
    repo_root,
    resolve_scenario_documents,
)

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
    truth_file=Path(__file__).resolve().parents[3]/"experiments/phase7/prescan_final.json"
    truth={x["document_id"]:x for x in json.loads(truth_file.read_text(encoding="utf-8"))["documents"]}
    chunks=tuple(IndexedChunk(r["demo_document_id"], r["demo_document_id"]+":0", r["runtime_text"]) for r in rows)
    seed_file=Path(__file__).resolve().parents[3]/"demo/trusted_seed_manifest.json"
    trusted={r["document_id"] for r in json.loads(seed_file.read_text(encoding="utf-8"))["documents"]}
    decisions={r["demo_document_id"]: ("SAFE" if r["demo_document_id"] in trusted else truth.get(r["demo_document_id"],{}).get("decision","REVIEW")) for r in rows}
    indexes=build_indexes(chunks,{k:Decision(v) for k,v in decisions.items()},RetrieverConfig(k=3))
    return DemoKnowledgeBase("DEMO", indexes)

def _index_decision(document_id: str, trusted_ids: set[str], truth: dict[str, str]) -> str:
    if document_id in trusted_ids:
        return "SAFE"
    value = truth.get(document_id, "REVIEW")
    if not isinstance(value, str):
        raise TypeError(f"frozen decision must be a string: {document_id}")
    return value

def build_scenario_knowledge_base(rows, trusted_ids, truth):
    chunks=tuple(IndexedChunk(r['demo_document_id'], r['demo_document_id']+':0', r['runtime_text']) for r in rows)
    decisions={r['demo_document_id']: _index_decision(r['demo_document_id'], trusted_ids, truth) for r in rows}
    return DemoKnowledgeBase('SCENARIO', build_indexes(chunks,{k:Decision(v) for k,v in decisions.items()},RetrieverConfig(k=5)))

def materialize_scenario(scenario_id: str, root: Path | str | None = None) -> tuple[dict, DemoKnowledgeBase]:
    root_path = repo_root(root)
    spec = next((item for item in load_final_scenarios(root_path) if item["scenario_id"] == scenario_id), None)
    if spec is None:
        raise ValueError("scenario_id is required and must be valid")
    rows = resolve_scenario_documents(spec, load_runtime_documents(root_path))
    kb = build_scenario_knowledge_base(rows, load_trusted_seed_ids(root_path), load_frozen_decisions(root_path))
    return spec, kb

class DemoApplication:
    def __init__(self, kb: DemoKnowledgeBase | None = None):
        config=GeneratorConfig("demo-deterministic", "Answer only from retrieved evidence.")
        self.generator=SharedGenerator(config, DemoProvider())
        self.cic=ContextIntegrityChecker()
    def run(self, query_text: str, scenario_id: str | None = None) -> dict:
        if not isinstance(query_text,str) or not query_text.strip(): raise ValueError("query_text must be non-empty")
        if not scenario_id:
            raise ValueError("scenario_id is required and must be valid")
        spec, kb = materialize_scenario(scenario_id)
        retriever=SharedRetriever(kb.indexes.config)
        q=RuntimeQuery("demo-query",query_text.strip())
        result={"scenario_id":spec["scenario_id"], "query":query_text.strip(), "vanilla":self._path(q,"vanilla",kb,retriever), "protected":self._path(q,"protected",kb,retriever), "admission":{"protected_documents":len(kb.indexes.protected.document_ids),"quarantined_documents":len(kb.indexes.vanilla.document_ids-kb.indexes.protected.document_ids)}}
        return result
    def _path(self,q,path,kb,retriever):
        index=getattr(kb.indexes,path); retrieval=retriever.retrieve(q,index)
        outcome=(run_vanilla_path(q,retrieval,self.generator) if path=="vanilla" else run_protected_path(q,retrieval,self.generator,self.cic))
        docs=[]
        for h in retrieval.hits: docs.append({"document_id":h.document_id,"chunk_id":h.chunk_id,"text":h.text,"score":h.score})
        payload={"retrieval_status":retrieval.status.value,"chunks":docs,"generation":outcome.to_runtime_dict()}
        if path=="protected": payload["cic"]=outcome.cic.to_runtime_dict() if outcome.cic else None
        return payload
