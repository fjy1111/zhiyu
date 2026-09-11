"""Capture and compare raw file hashes without decoding sample contents."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'datasets/raw/trusted_provenance'
MANIFESTS = ROOT / 'datasets/manifests'

def snapshot():
    return {p.relative_to(RAW).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(RAW.rglob('*')) if p.is_file()}

def compare(before, after):
    return {'before_files': len(before), 'after_files': len(after),
            'modified': sorted(k for k in before.keys() & after.keys() if before[k] != after[k]),
            'deleted': sorted(before.keys() - after.keys()),
            'added': sorted(after.keys() - before.keys()), 'pass': before == after}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['before', 'after'])
    args = parser.parse_args()
    target = MANIFESTS / f'raw_snapshot_{args.phase}.json'
    data = snapshot()
    if args.phase == 'before' and target.exists():
        raise FileExistsError('Baseline already exists; refusing to overwrite')
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    if args.phase == 'after':
        result = compare(json.loads((MANIFESTS / 'raw_snapshot_before.json').read_text(encoding='utf-8')), data)
        (MANIFESTS / 'raw_integrity.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result))
        return 0 if result['pass'] else 1
    print(f'Baseline captured: {len(data)} files')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
