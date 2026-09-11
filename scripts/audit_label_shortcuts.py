import json,re
from collections import defaultdict
from _common import ROOT
from zhiyu.dataset import build_records
from zhiyu.datasets.trusted_provenance_adapter import adapt

def audit(rows):
    labels=sorted({x[1] for x in rows}); buckets={"token":defaultdict(lambda:defaultdict(set)),"line":defaultdict(lambda:defaultdict(set)),"prefix":defaultdict(lambda:defaultdict(set))}
    for doc,label,text in rows:
        for token in set(re.findall(r'[\w\u4e00-\u9fff]{2,}',text.lower())): buckets['token'][token][label].add(doc)
        for line in text.splitlines():
            line=re.sub(r'\s+',' ',line.strip())
            if not line: continue
            buckets['line'][line][label].add(doc)
            match=re.match(r'^([^:：]{1,30})\s*[:：]',line)
            if match: buckets['prefix'][match.group(1).strip()][label].add(doc)
    def make(data,key):
        result=[]
        for value,by in sorted(data.items()):
            counts={label:len(by.get(label,set())) for label in labels}; total=sum(counts.values()); concentration=max(counts.values(),default=0)/total if total else 0
            result.append({key:value,'label_counts':counts,'total_documents':total,'concentration':round(concentration,6)})
        return result
    tokens=make(buckets['token'],'token')
    return {'high_frequency_tokens':sorted(tokens,key=lambda x:(-x['total_documents'],x['token']))[:100],'label_concentrated_tokens':[x for x in tokens if x['concentration']>=.8],'label_exclusive_tokens':[x for x in tokens if sum(v>0 for v in x['label_counts'].values())==1],'fixed_line_templates':make(buckets['line'],'line'),'field_prefixes':make(buckets['prefix'],'prefix')}

def main():
    docs,_=build_records(ROOT)
    for name,rows in [('raw',[(d.document_id,d.metadata.get('original_label'),d.text) for d in docs]),('benchmark',[(d.document_id,d.metadata.get('original_label'),adapt(d).benchmark_text) for d in docs])]:
        result=audit(rows); result['documents']=len(rows); (ROOT/f'datasets/manifests/label_shortcut_audit_{name}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'datasets/manifests/label_shortcut_audit.md').write_text('# Label shortcut audit\n\nDocument frequency, label concentration and exclusive token statistics are generated from development only.\n',encoding='utf-8')
if __name__=='__main__': raise SystemExit(main())
