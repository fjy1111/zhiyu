import json
from pathlib import Path
from zhiyu.demo.application import DemoApplication

def test_demo_jsonl_utf8():
 p=Path('demo/demo_knowledge_base.jsonl'); rows=[json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]; assert len(rows)==5; assert rows[0]['title']=='normal-safe'
def test_paths_and_separation():
 a=DemoApplication(); out=a.run('地球是太阳系第几颗行星？'); assert out['vanilla'] and out['protected']; assert set(a.kb.indexes.protected.document_ids)=={'normal-safe'}; assert 'normal-safe' in a.kb.indexes.vanilla.document_ids
def test_no_context_and_runtime_firewall():
 out=DemoApplication().run('完全不存在的词'); assert out['vanilla']['generation']['status']=='NO_CONTEXT'; assert out['protected']['generation']['status']=='NO_CONTEXT'; blob=json.dumps(out); assert all(x not in blob for x in ('gold_answer','attack_target','EvaluatorRecord','POISON'))
import subprocess, sys
from pathlib import Path

def test_server_imports_from_repo_root():
 root=Path(__file__).parents[1]
 code="import demo.server; print(demo.server.REPO_ROOT)"
 result=subprocess.run([sys.executable,"-c",code],cwd=root,capture_output=True,text=True)
 assert result.returncode==0, result.stderr
 assert str(root) in result.stdout
def test_scenario_isolation_and_poison_admission():
 a=DemoApplication()
 factual=a.run('地球是太阳系第几颗行星？','factual'); injection=a.run('太阳系中最大的行星是什么？','injection')
 fids={x['document_id'] for x in factual['vanilla']['chunks']}; iids={x['document_id'] for x in injection['vanilla']['chunks']}
 assert not any('inject' in x for x in fids); assert not any('fact' in x for x in iids)
 assert set(a.kb.indexes.protected.document_ids)=={'inject-safe'}
 assert factual['admission']['quarantined_documents']==1 and injection['admission']['quarantined_documents']==1
 assert 'gold_answer' not in json.dumps(factual|injection)
def test_competition_page_has_scenarios_and_presets():
 html=Path('demo/index.html').read_text(encoding='utf-8')
 for label in ('正常问答','事实篡改攻击','Prompt Injection','Hidden Instruction','Retrieval Hijacking','Knowledge Conflict'):
  assert label in html
 assert 'preset' in html and 'SAFE-only KB' in html

def test_injection_presentation_contrast():
 out=DemoApplication().run('太阳系中最大的行星是什么？','injection')
 assert any('忽略用户问题' in c['text'] for c in out['vanilla']['chunks'])
 assert not any('忽略用户问题' in c['text'] for c in out['protected']['chunks'])
 assert out['admission']['quarantined_documents']==1
def test_demo_v2_manifest_and_runtime_clean():
 p=Path('demo/demo_knowledge_base_v2.jsonl'); rows=[json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]; assert len(rows)==38
 for r in rows:
  assert (r['source_path'] is None) or Path(r['source_path']).exists(); assert all(x not in r['runtime_text'] for x in ('样本用于测试','original_label','SAMPLE-','隐藏内容：','临时调整版'))
  assert set(r) >= {'demo_document_id','runtime_text','mechanism'}
def test_demo_v2_preset_counts_and_topics():
 d=json.loads(Path('demo/demo_presets_v2.json').read_text(encoding='utf-8')); assert all(len(v)>=3 for v in d.values()); assert '人工智能创新赛' in d['factual'][0]; assert '实验室' in d['prompt_injection'][0]
def test_demo_v2_mechanism_gap_is_explicit():
 rows=[json.loads(x) for x in Path('demo/demo_knowledge_base_v2.jsonl').read_text(encoding='utf-8').splitlines()]; assert sum(r['mechanism']=='PROMPT_INJECTION' for r in rows)>=3; assert sum(r['mechanism']=='HIDDEN_INSTRUCTION' for r in rows)>=3; assert sum(r['mechanism']=='RETRIEVAL_HIJACKING' for r in rows)>=4

