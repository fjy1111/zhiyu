import json
from pathlib import Path
root=Path(__file__).parents[1]
rows=[json.loads(x) for x in (root/'demo/demo_knowledge_base_v2.jsonl').read_text(encoding='utf8').splitlines()]
truth={x['document_id']:x['decision'] for x in json.loads((root/'experiments/phase7/prescan_final.json').read_text(encoding='utf8'))['documents']}
normal={}
for r in rows:
    if r.get('mechanism')=='SAFE' and r.get('scenario') not in normal: normal[r['scenario']]=r
seed={'kind':'CURATED_TRUSTED_SEED','label':'预先审核可信基线','documents':[{'document_id':r['demo_document_id'],'topic':topic,'source_path':r.get('source_path'),'runtime_text':r['runtime_text'],'curation':'预先审核可信基线'} for topic,r in normal.items()]}
(root/'demo/trusted_seed_manifest.json').write_text(json.dumps(seed,ensure_ascii=False,indent=2),encoding='utf8')
mechs={'FACT_TAMPERING','PROMPT_INJECTION','HIDDEN_INSTRUCTION','RETRIEVAL_HIJACKING','KNOWLEDGE_CONFLICT'}
out=[]
for i,r in enumerate([x for x in rows if x.get('mechanism') in mechs],1):
    parent=normal.get(r.get('scenario'))
    out.append({'scenario_id':f"live-{r['mechanism'].lower()}-{i:02d}",'mechanism':r['mechanism'],'display_name':r['demo_document_id'],'trusted_seed_document_ids':[parent['demo_document_id']] if parent else [],'incoming_document_id':r['demo_document_id'],'distractor_document_ids':[],'actual_decision':truth.get(r['demo_document_id'],'REVIEW'),'generated_preset_questions':[f"{r.get('scenario')}主题的相关信息是什么？"],'queried_field':'知识主题','source_kind':'SOURCE_DERIVED' if not r['demo_document_id'].startswith('syn-') else 'DEMO_SYNTHETIC','topic':r.get('scenario')})
(root/'demo/live_scenarios.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(len(seed['documents']),len(out))
