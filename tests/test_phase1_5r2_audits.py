from zhiyu.datasets.template_similarity import build_template_groups,character_ngrams,jaccard_similarity
from scripts.audit_label_shortcuts import audit
def test_connected_components_transitive():
    records=[{'text':'alpha common template '*5},{'text':'alpha common template '*5+' B'},{'text':'alpha common template '*5+' C'}]
    groups,pairs=build_template_groups(records,5,0.8); assert len(groups)==1
def test_unrelated_templates_separate():
    assert jaccard_similarity(character_ngrams('alpha '*20),character_ngrams('zzzz '*20)) < .8
def test_shortcut_categories_and_lines():
    result=audit([('a','A','alpha_only\n知识主题：数学\ncommon'),('b','B','beta_only\n知识主题：数学\ncommon')])
    assert any(x['token']=='alpha_only' for x in result['label_exclusive_tokens'])
    assert not any(x['token']=='common' for x in result['label_exclusive_tokens'])
    assert any(x['line']=='知识主题：数学' for x in result['fixed_line_templates'])
    assert any(x['prefix']=='知识主题' for x in result['field_prefixes'])
