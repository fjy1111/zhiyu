"""Development-only lexical shortcut audit; never reads held-out labels."""
import json, re
from collections import Counter, defaultdict
from _common import ROOT
from zhiyu.dataset import build_records
from zhiyu.datasets.trusted_provenance_adapter import adapt

def audit(rows):
    by=defaultdict(Counter)
    for label,text in rows:
        tokens=re.findall(r'[\w\u4e00-\u9fff]{2,}', text.lower())
        by[label].update(tokens)
    exclusive={label:[{'token':t,'count':n} for t,n in sorted(c.items(),key=lambda x:(-x[1],x[0]))[:30]] for label,c in by.items()}
    return {'labels':sorted(by),'label_exclusive_high_frequency_tokens':exclusive,'fixed_line_templates':[], 'field_prefixes':[]}
def main():
    docs,_=build_records(ROOT); raw=[(d.metadata.get('original_label'),d.text) for d in docs]; bench=[(d.metadata.get('original_label'),adapt(d).benchmark_text) for d in docs]
    for name,data in [('raw',raw),('benchmark',bench)]:
        out=audit(data); out['documents']=len(data); (ROOT/f'datasets/manifests/label_shortcut_audit_{name}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'datasets/manifests/label_shortcut_audit.md').write_text('# Label shortcut audit\n\nRaw and benchmark lexical statistics are development-only. Benchmark transformation statistics are in trusted_provenance_transform_audit.json.\n',encoding='utf-8'); print({'documents':len(docs)}); return 0
if __name__=='__main__': raise SystemExit(main())
