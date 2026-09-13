from __future__ import annotations
import json, re
from dataclasses import dataclass
from pathlib import Path
from zhiyu.models.rag import (BuiltIndexes, GeneratorConfig, IndexedChunk, RetrieverConfig, RuntimeQuery, GenerationOutcome)
from zhiyu.rag.admission import build_indexes
from zhiyu.rag.cic import ContextIntegrityChecker
from zhiyu.rag.generate import SharedGenerator, run_protected_path, run_vanilla_path
from zhiyu.rag.retriever import SharedRetriever

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
        if "第九颗" in text: return "根据检索证据：地球是太阳系第九颗行星。"
        if "最大的行星" in data.get("query_text", "") or "最大" in data.get("query_text", ""):
            return "根据检索证据：太阳系中最大的行星是木星。"
        if "第三颗" in text: return "根据检索证据：地球是太阳系第三颗行星。"
        return "根据检索证据：" + text[:160]

def load_demo_knowledge_base(path: Path | str | None = None, scenario: str = "normal") -> DemoKnowledgeBase:
    path=Path(path or Path(__file__).resolve().parents[3]/"demo/demo_knowledge_base.jsonl")
    rows=[json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip() and json.loads(x).get("scenario", "normal") == scenario]
    chunks=tuple(IndexedChunk(r["document_id"], r["document_id"]+":0", r["text"]) for r in rows)
    decisions={r["document_id"]: r["decision"] for r in rows}
    from zhiyu.models.detection import Decision
    indexes=build_indexes(chunks,{k:Decision(v) for k,v in decisions.items()},RetrieverConfig(k=3))
    return DemoKnowledgeBase("DEMO", indexes)

class DemoApplication:
    def __init__(self, kb: DemoKnowledgeBase | None = None):
        self.kb=kb or load_demo_knowledge_base()
        config=GeneratorConfig("demo-deterministic", "Answer only from retrieved evidence.")
        self.generator=SharedGenerator(config, DemoProvider())
        self.retriever=SharedRetriever(self.kb.indexes.config)
        self.cic=ContextIntegrityChecker()
    def run(self, query_text: str, scenario: str = "DEMO") -> dict:
        if not isinstance(query_text,str) or not query_text.strip(): raise ValueError("query_text must be non-empty")
        q=RuntimeQuery("demo-query",query_text.strip())
        scenario = {"DEMO":"normal"}.get(scenario, scenario)
        if scenario not in {"normal", "factual", "injection"}: raise ValueError("unknown demo scenario")
        self.kb = load_demo_knowledge_base(scenario=scenario)
        self.retriever = SharedRetriever(self.kb.indexes.config)
        result={"scenario":scenario, "query":query_text.strip(), "vanilla":self._path(q,"vanilla"), "protected":self._path(q,"protected"), "admission":{"protected_documents":len(self.kb.indexes.protected.document_ids),"quarantined_documents":len(self.kb.indexes.vanilla.document_ids-self.kb.indexes.protected.document_ids)}}
        return result
    def _path(self,q,path):
        index=getattr(self.kb.indexes,path); retrieval=self.retriever.retrieve(q,index)
        outcome=(run_vanilla_path(q,retrieval,self.generator) if path=="vanilla" else run_protected_path(q,retrieval,self.generator,self.cic))
        docs=[]
        for h in retrieval.hits: docs.append({"document_id":h.document_id,"chunk_id":h.chunk_id,"text":h.text,"score":h.score})
        payload={"retrieval_status":retrieval.status.value,"chunks":docs,"generation":outcome.to_runtime_dict()}
        if path=="protected": payload["cic"]=outcome.cic.to_runtime_dict() if outcome.cic else None
        return payload
