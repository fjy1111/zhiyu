import json, hashlib
from collections import Counter, defaultdict
from _common import ROOT
from zhiyu.parser.chunker import Chunker
from zhiyu.models.document import DocumentRecord
import yaml
from zhiyu.datasets.template_similarity import template_fingerprint
from zhiyu.datasets.template_similarity import ngrams

def main():
    source=ROOT/'datasets/processed/trusted_provenance/benchmark_documents.jsonl'
    rows=[json.loads(x) for x in source.read_text(encoding='utf-8').splitlines() if x.strip()]
    parent=list(range(len(rows)))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[b]=a
    vectors=[ngrams(r['benchmark_text']) for r in rows]
    for i in range(len(rows)):
        for j in range(i):
            u=vectors[i]|vectors[j]
            if u and len(vectors[i]&vectors[j])/len(u)>=0.8: union(i,j)
    groups=defaultdict(list)
    for i,r in enumerate(rows): groups[find(i)].append(r)
    groups={hashlib.sha256('|'.join(sorted(x['document_id'] for x in members)).encode()).hexdigest()[:16]:members for _,members in groups.items()}
    ordered=sorted(groups.items(), key=lambda x: x[0]); target=round(len(rows)*.7); tune=0; out=[]
    for gid, members in ordered:
        assigned='development_tune' if tune < target else 'development_generalization'
        tune += len(members) if assigned=='development_tune' else 0
        out.extend({'document_id':r['document_id'],'original_label':r.get('original_label'),'group_id':gid,'assigned_split':assigned} for r in members)
    path=ROOT/'datasets/manifests/development_group_split.json'; path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assignments={x['document_id']:x['assigned_split'] for x in out}; config=yaml.safe_load((ROOT/'configs/chunking.yaml').read_text()); chunker=Chunker(**config)
    for split in ('development_tune','development_generalization'):
        selected=[r for r in rows if assignments[r['document_id']]==split]; chunks=[]
        for r in selected:
            d=DocumentRecord(r['document_id'],'trusted_provenance','development','', '', '.txt','',r['benchmark_text'],len(r['benchmark_text']),'BenchmarkAdapter','1.0',r.get('metadata',{}),[]); chunks.extend(chunker.chunk(d))
        folder=ROOT/'datasets/processed/trusted_provenance'; folder.joinpath(f'benchmark_{split.split("_")[-1]}_documents.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in selected),encoding='utf-8'); folder.joinpath(f'benchmark_{split.split("_")[-1]}_chunks.jsonl').write_text(''.join(json.dumps(c.__dict__,ensure_ascii=False)+'\n' for c in chunks),encoding='utf-8')
    print(Counter(x['assigned_split'] for x in out)); return 0
if __name__=='__main__': raise SystemExit(main())
