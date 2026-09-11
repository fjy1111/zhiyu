import json
from pathlib import Path
def test_group_isolation():
    rows=json.loads((Path(__file__).resolve().parents[1]/'datasets/manifests/development_group_split.json').read_text(encoding='utf-8'))
    a={x['group_id'] for x in rows if x['assigned_split']=='development_tune'}; b={x['group_id'] for x in rows if x['assigned_split']=='development_generalization'}
    assert not a&b and len(rows)==180
