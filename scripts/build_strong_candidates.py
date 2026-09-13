import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from zhiyu.demo.application import parse_fields,compare_fields
root=Path(__file__).parents[1]; rows=[json.loads(x) for x in (root/'demo/demo_knowledge_base_v2.jsonl').read_text(encoding='utf8').splitlines()]; by={r['demo_document_id']:r for r in rows}; seeds={r['scenario']:r for r in rows if r.get('mechanism')=='SAFE'}; truth={x['document_id']:x['decision'] for x in json.loads((root/'experiments/phase7/prescan_final.json').read_text(encoding='utf8'))['documents']}
out=[]
for r in rows:
 if r.get('mechanism')=='FACT_TAMPERING' and r.get('scenario') in seeds:
  s=seeds[r['scenario']]; diff=compare_fields(s['runtime_text'],r['runtime_text']); valid=bool(diff['changed_fields']); field=diff['changed_fields'][0] if valid else None
  out.append({'scenario_id':'strong-'+r['demo_document_id'],'mechanism':'FACT_TAMPERING','trusted_seed_document_id':s['demo_document_id'],'incoming_document_id':r['demo_document_id'],'source_kind':'SOURCE_DERIVED','topic_display_name':parse_fields(s['runtime_text']).get('知识主题',r['scenario']),'queried_field':field,'trusted_value':parse_fields(s['runtime_text']).get(field) if field else None,'incoming_value':parse_fields(r['runtime_text']).get(field) if field else None,'primary_question':(parse_fields(s['runtime_text']).get('知识主题','')+'的'+field+'是什么？') if field else None,'actual_decision':truth.get(r['demo_document_id']),'field_diff_valid':valid,'candidate_status':'STRONG_CANDIDATE' if valid and truth.get(r['demo_document_id']) in ('REVIEW','POISON') else 'REJECTED'})
for r in rows:
 if r.get('mechanism')=='KNOWLEDGE_CONFLICT' and r.get('scenario') in seeds:
  s=seeds[r['scenario']]; diff=compare_fields(s['runtime_text'],r['runtime_text']); out.append({'scenario_id':'strong-'+r['demo_document_id'],'mechanism':'KNOWLEDGE_CONFLICT','trusted_seed_document_id':s['demo_document_id'],'incoming_document_id':r['demo_document_id'],'source_kind':'SOURCE_DERIVED','topic_display_name':parse_fields(s['runtime_text']).get('知识主题',r['scenario']),'queried_field':None,'trusted_value':None,'incoming_value':None,'primary_question':None,'actual_decision':truth.get(r['demo_document_id']),'field_diff_valid':bool(diff['changed_fields']),'candidate_status':'REJECTED'})
(root/'demo/strong_demo_candidates.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'total':len(out),'strong':sum(x['candidate_status']=='STRONG_CANDIDATE' for x in out)},ensure_ascii=False))
