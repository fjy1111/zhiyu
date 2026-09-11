import json
from dataclasses import asdict
from _common import ROOT
from zhiyu.dataset import build_records
from zhiyu.datasets.trusted_provenance_adapter import adapt
from zhiyu.parser.chunker import Chunker
import yaml

def main():
    documents, _ = build_records(ROOT)
    records = [adapt(d) for d in documents]
    config = yaml.safe_load((ROOT/'configs/chunking.yaml').read_text(encoding='utf-8'))
    chunker = Chunker(**config)
    # Create a lightweight document copy with benchmark_text for offsets.
    from zhiyu.models.document import DocumentRecord
    output = ROOT/'datasets/processed/trusted_provenance'; output.mkdir(parents=True, exist_ok=True)
    chunks=[]
    for r in records:
        d = DocumentRecord(r.document_id, 'trusted_provenance', 'development', '', '', '.txt', '', r.benchmark_text, len(r.benchmark_text), 'BenchmarkAdapter', '1.0', r.metadata, [])
        chunks.extend(chunker.chunk(d))
    (output/'benchmark_documents.jsonl').write_text(''.join(json.dumps(asdict(r),ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    (output/'benchmark_chunks.jsonl').write_text(''.join(json.dumps(asdict(c),ensure_ascii=False)+'\n' for c in chunks),encoding='utf-8')
    audit={'documents_total':len(records),'documents_changed':sum(r.parsed_text!=r.benchmark_text for r in records),'documents_unchanged':sum(r.parsed_text==r.benchmark_text for r in records)}
    for key, typ in [('sample_id_removed','REMOVE_SAMPLE_ID'),('dataset_note_removed','REMOVE_DATASET_NOTE'),('hidden_prefix_removed','REMOVE_HIDDEN_PREFIX'),('temporary_marker_removed','REMOVE_TEMPORARY_MARKER')]: audit[key]=sum(x['count'] for r in records for x in r.transformations if x['type']==typ)
    audit['other_transformations']=sorted({x['type'] for r in records for x in r.transformations if x['type'] not in {'REMOVE_SAMPLE_ID','REMOVE_DATASET_NOTE','REMOVE_HIDDEN_PREFIX','REMOVE_TEMPORARY_MARKER'}})
    (ROOT/'datasets/manifests/trusted_provenance_transform_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit)); return 0
if __name__=='__main__': raise SystemExit(main())
