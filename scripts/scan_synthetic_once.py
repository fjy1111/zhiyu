import json,subprocess,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).parents[1];sys.path.insert(0,str(ROOT/'src'))
from zhiyu.semantic.env import load_project_env,public_llm_config
from zhiyu.detector.scanner import RuleScanner
from zhiyu.semantic.analyzer import SemanticAnalyzer
from zhiyu.semantic.provider import DeepSeekSemanticProvider
from zhiyu.factual.provider import DeepSeekFactualProvider
from zhiyu.factual.pipeline import FactualEvidencePipeline
from zhiyu.factual.corpus import load_references,sha256_text
from zhiyu.judge.materialize import materialize_document
from zhiyu.judge.provider import DeepSeekJudgeProvider
from zhiyu.judge.judge import UnifiedJudge
from zhiyu.judge.engine import decide
from zhiyu.models.detection import DetectionInput
from zhiyu.models.judge import Ablation
load_project_env(ROOT);cfg=public_llm_config(); refs=load_references(ROOT/'datasets/processed/phase4/references.jsonl')
semantic=SemanticAnalyzer(DeepSeekSemanticProvider(model=cfg['model'],base_url=cfg['base_url'],temperature=0,max_tokens=800,timeout_sec=60,retries=1)); factual=FactualEvidencePipeline(DeepSeekFactualProvider(model=cfg['model'],base_url=cfg['base_url'],temperature=0,max_tokens=800,timeout_sec=60,retries=1),refs); judge=UnifiedJudge(DeepSeekJudgeProvider(model=cfg['model'],base_url=cfg['base_url'],temperature=0,max_tokens=800,timeout_sec=60,retries=1)); scanner=RuleScanner()
ids=['syn-ft-library','syn-ft-scholarship','syn-conf-exam','syn-conf-dorm','syn-conf-scholarship']; parents={'syn-ft-library':'dv2-normal_library_003','syn-ft-scholarship':'dv2-normal_scholarship_004','syn-conf-exam':'dv2-normal_exam_002','syn-conf-dorm':'dv2-normal_dorm_005','syn-conf-scholarship':'dv2-normal_scholarship_004'}; mechs={'syn-ft-library':'FACT_TAMPERING','syn-ft-scholarship':'FACT_TAMPERING','syn-conf-exam':'KNOWLEDGE_CONFLICT','syn-conf-dorm':'KNOWLEDGE_CONFLICT','syn-conf-scholarship':'KNOWLEDGE_CONFLICT'};out=[]
for docid in ids:
 text=(ROOT/'demo/attack_samples'/(docid+'.txt')).read_text(encoding='utf8'); item=DetectionInput(docid,docid+':0',text); doc=materialize_document(docid,[item],'',sha256_text(text),scanner,semantic,factual); status,assessment=judge.assess(doc); dec=decide(doc,Ablation.FULL_JUDGE,assessment,status); counts=Counter(x.status.value for x in doc.statuses);out.append({'document_id':docid,'mechanism':mechs[docid],'parent_trusted_document_id':parents[docid],'runtime_text_sha256':sha256_text(text),'model':cfg['model'],'base_url':cfg['base_url'],'decision':dec.decision.value,'component_statuses':dict(counts),'rule_event_count':len(doc.rule_events),'behavior_evidence_count':len(doc.behavior_evidence),'factual_evidence_summary':dict(Counter(x.relation.value for x in doc.factual_evidence)),'judge_status':status.status.value,'provider_errors_invalid':sum(v for k,v in counts.items() if k in ('ERROR','INVALID_OUTPUT'))})
(ROOT/'experiments/phase7/demo_synthetic_scan.json').write_text(json.dumps({'kind':'phase7_demo_synthetic_scan_real_llm','model':cfg['model'],'base_url':cfg['base_url'],'documents':out},ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(out,ensure_ascii=False))
