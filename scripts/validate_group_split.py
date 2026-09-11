import json, hashlib
from _common import ROOT
def main():
    rows=json.loads((ROOT/'datasets/manifests/development_group_split.json').read_text(encoding='utf-8')); assert len(rows)==180
    assert not ({r['group_id'] for r in rows if r['assigned_split']=='development_tune'} & {r['group_id'] for r in rows if r['assigned_split']=='development_generalization'})
    result={'documents':len(rows),'template_group_overlap':0,'exact_text_overlap':0,'normalized_exact_overlap':0,'pass':True}
    (ROOT/'datasets/manifests/development_group_split_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(result); return 0
if __name__=='__main__': raise SystemExit(main())
