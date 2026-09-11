import json
from collections import defaultdict
from _common import ROOT
from zhiyu.dataset import DatasetPolicy
from zhiyu.parser.document_parser import DocumentParser
from zhiyu.datasets.template_similarity import (
    build_template_groups,
    load_benchmark_audit_config,
    template_fingerprint,
)

def audit_template_records(rows, ngram_size, threshold):
    groups, pairs = build_template_groups(rows, ngram_size, threshold)
    buckets = defaultdict(list)
    for r in rows:
        buckets[template_fingerprint(r.get('text', ''))].append(r['path'])
    exact = {h: ps for h, ps in buckets.items() if len(ps) > 1}
    template_clusters = []
    cross_split = 0
    for i, group in enumerate(groups):
        paths = [r['path'] for r in group]
        template_clusters.append({'cluster_id': str(i), 'paths': paths})
        if len({path.split('/')[0] for path in paths}) > 1:
            cross_split += 1
    near = [
        {'paths': [rows[j]['path'], rows[i]['path']], 'similarity': round(score, 6)}
        for j, i, score in pairs
    ]
    return {
        'exact_skeleton_overlap_groups': len(exact),
        'near_template_pairs': near,
        'connected_template_groups': len(groups),
        'cross_split_template_overlap': cross_split,
        'template_clusters': template_clusters,
    }

def main():
    cfg = load_benchmark_audit_config(ROOT / 'configs/benchmark_audit.yaml')
    ngram_size = cfg['ngram_size']
    threshold = cfg['near_template_threshold']
    policy, parser = DatasetPolicy(ROOT), DocumentParser()
    rows, stats = [], {}
    for split in ('demo_set', 'dev_set', 'stress_set', 'blind_test_set', 'third_party_blind_set'):
        paths = list(policy.files(split, 'audit'))
        stats[split] = {'files': len(paths)}
        for path in paths:
            if path.suffix.lower() not in parser.routes:
                continue
            rel = path.relative_to(policy.raw).as_posix()
            doc = parser.parse(path, relative_path=rel)
            rows.append({
                'path': rel,
                'hash': template_fingerprint(doc.text),
                'cluster_id': None,
                'text': doc.text,
            })
    report = audit_template_records(rows, ngram_size, threshold)
    report['splits'] = stats
    (ROOT / 'datasets/manifests/template_similarity_audit.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print({k: report[k] for k in ('exact_skeleton_overlap_groups', 'cross_split_template_overlap')})
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
