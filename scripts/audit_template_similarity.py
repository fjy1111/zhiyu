import hashlib,json,re
from collections import Counter,defaultdict
from _common import ROOT
from zhiyu.dataset import DatasetPolicy
from zhiyu.parser.document_parser import DocumentParser
def skeleton(text):
    text=re.sub(r'\b(?:https?://|www\.)\S+','URL',text,flags=re.I); text=re.sub(r'[\w.+-]+@[\w.-]+','EMAIL',text); text=re.sub(r'(?<!\w)\d{1,4}(?:[-:/]\d{1,4})+(?!\w)','DATE_TIME',text); text=re.sub(r'\d+','NUM',text); return re.sub(r'\s+',' ',text).strip()
def main():
    p,parser=DatasetPolicy(ROOT),DocumentParser(); rows=[]; stats={}
    for split in ('demo_set','dev_set','stress_set','blind_test_set','third_party_blind_set'):
        paths=list(p.files(split,'audit')); stats[split]={'files':len(paths)}
        for path in paths:
            if path.suffix.lower() not in parser.routes: continue
            rel=path.relative_to(p.raw).as_posix(); doc=parser.parse(path,relative_path=rel); sk=skeleton(doc.text); rows.append({'path':rel,'hash':hashlib.sha256(sk.encode()).hexdigest(),'cluster_id':None})
    buckets=defaultdict(list)
    for r in rows: buckets[r['hash']].append(r['path'])
    clusters={h:ps for h,ps in buckets.items() if len(ps)>1}; ids={h:str(i) for i,h in enumerate(sorted(clusters))}
    report={'splits':stats,'exact_skeleton_overlap_groups':len(clusters),'cross_split_template_overlap':sum(1 for ps in clusters.values() if len({x.split('/')[0] for x in ps})>1),'template_clusters':[{'cluster_id':ids[h],'paths':ps} for h,ps in clusters.items()]}
    (ROOT/'datasets/manifests/template_similarity_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print({k:report[k] for k in ('exact_skeleton_overlap_groups','cross_split_template_overlap')}); return 0
if __name__=='__main__': raise SystemExit(main())
