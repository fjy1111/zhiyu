import json
from pathlib import Path
r=Path(__file__).parents[1]; c=json.loads((r/'demo/strong_demo_candidates.json').read_text(encoding='utf8')); scans={x['document_id']:x for x in json.loads((r/'experiments/phase7/demo_synthetic_scan.json').read_text(encoding='utf8'))['documents']}; rh=json.loads((r/'experiments/phase7/rh_rank_validation.json').read_text(encoding='utf8'))
for x in c:
 if x['incoming_document_id'] in scans:
  s=scans[x['incoming_document_id']];x['actual_decision']=s['decision'];x['candidate_status']='STRONG_CANDIDATE' if s['decision'] in ('REVIEW','POISON') and x['field_diff_valid'] else 'REJECTED'
for z in rh:c.append({'scenario_id':'rh-'+z['incoming_document_id'],'mechanism':'RETRIEVAL_HIJACKING','source_kind':'SOURCE_DERIVED','trusted_seed_document_id':None,'incoming_document_id':z['incoming_document_id'],'topic_display_name':z['incoming_document_id'],'queried_field':'','trusted_value':None,'incoming_value':None,'primary_question':z['query'],'actual_decision':'REVIEW','field_diff_valid':False,'vanilla_rank':z['incoming_rank'],'vanilla_score':z['incoming_score'],'vanilla_topk_document_ids':z['vanilla_topk_document_ids'],'protected_topk_document_ids':z['protected_topk_document_ids'],'protected_absent':z['protected_absent'],'candidate_status':'STRONG_CANDIDATE' if z['passed'] else 'REJECTED'})
(r/'demo/strong_demo_candidates.json').write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf8')
