import json
from _common import ROOT
from zhiyu.datasets.template_similarity import template_fingerprint,ngrams
def main():
    folder=ROOT/'datasets/processed/trusted_provenance'
    tune=[json.loads(x) for x in (folder/'benchmark_tune_documents.jsonl').read_text(encoding='utf-8').splitlines()]; gen=[json.loads(x) for x in (folder/'benchmark_generalization_documents.jsonl').read_text(encoding='utf-8').splitlines()]
    allrows=tune+gen; exact=lambda key: len(set(x[key] for x in tune)&set(x[key] for x in gen))
    norm=lambda r: ' '.join(r['benchmark_text'].split())
    near=sum(len(ngrams(a['benchmark_text'])&ngrams(b['benchmark_text']))/len(ngrams(a['benchmark_text'])|ngrams(b['benchmark_text']))>=.8 for a in tune for b in gen if ngrams(a['benchmark_text'])|ngrams(b['benchmark_text']))
    result={'documents':len(allrows),'document_id_overlap':exact('document_id'),'exact_text_overlap':len(set(x['benchmark_text'] for x in tune)&set(x['benchmark_text'] for x in gen)),'normalized_exact_overlap':len({norm(x) for x in tune}&{norm(x) for x in gen}),'exact_template_fingerprint_overlap':len({template_fingerprint(x['benchmark_text']) for x in tune}&{template_fingerprint(x['benchmark_text']) for x in gen}),'near_template_pair_overlap':near,'connected_template_group_overlap':len({template_fingerprint(x['benchmark_text']) for x in tune}&{template_fingerprint(x['benchmark_text']) for x in gen})}
    result['pass']=all(result[k]==0 for k in result if k.endswith('overlap') or k=='near_template_pair_overlap')
    (ROOT/'datasets/manifests/development_group_split_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(result); return 0
if __name__=='__main__': raise SystemExit(main())
