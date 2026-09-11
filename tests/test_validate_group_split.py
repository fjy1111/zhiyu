from zhiyu.datasets.template_similarity import template_fingerprint
from validate_group_split import validate_group_records

BASE = "shared campus notice template body for students and faculty " * 12

def test_connected_overlap_is_not_fingerprint_overlap():
    tune = [{"document_id": "t1", "benchmark_text": BASE + " AAA"}]
    gen = [{"document_id": "g1", "benchmark_text": BASE + " BBB"}]
    assert template_fingerprint(tune[0]["benchmark_text"]) != template_fingerprint(gen[0]["benchmark_text"])
    result = validate_group_records(tune, gen, 5, 0.8)
    assert result["exact_template_fingerprint_overlap"] == 0
    assert result["connected_template_group_overlap"] == 1
    assert result["pass"] is False

def test_separated_unrelated_templates_have_zero_connected_overlap():
    tune = [{"document_id": "t1", "benchmark_text": ("alpha-poison-") * 25}]
    gen = [{"document_id": "g1", "benchmark_text": ("hotel-normal-") * 25}]
    result = validate_group_records(tune, gen, 5, 0.8)
    assert result["connected_template_group_overlap"] == 0
    assert result["exact_template_fingerprint_overlap"] == 0
    assert result["pass"] is True
