import json
from pathlib import Path
root=Path(__file__).parents[1]
c=json.loads((root/'demo/live_scenarios.json').read_text(encoding='utf8'))
out=[]
for mech in ['FACT_TAMPERING','PROMPT_INJECTION','HIDDEN_INSTRUCTION','RETRIEVAL_HIJACKING','KNOWLEDGE_CONFLICT']:
    out += [x for x in c if x['mechanism']==mech][:3]
seeds=json.loads((root/'demo/trusted_seed_manifest.json').read_text(encoding='utf8'))['documents']
for i,s in enumerate(seeds[:3],1):
    out.append({'scenario_id':f'normal-{i:02d}','mechanism':'NORMAL','display_name':s['topic'],'trusted_seed_document_ids':[s['document_id']],'incoming_document_id':None,'distractor_document_ids':[],'actual_decision':'CURATED_TRUSTED_SEED','generated_preset_questions':[f"{s['topic']}的知识主题是什么？"],'queried_field':'知识主题','source_kind':'CURATED_TRUSTED_SEED','topic':s['topic'],'demo_status':'GOOD_DEMO'})
for x in out: x.setdefault('demo_status','GOOD_DEMO')
(root/'demo/final_live_scenarios.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(len(out))
