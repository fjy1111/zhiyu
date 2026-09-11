import json
import pytest
from zhiyu.models.detection import DetectionInput, RuntimeContext

def test_no_ground_truth_leakage():
    value=DetectionInput('d','c','payload',RuntimeContext(request_id='r')); serialized=json.dumps(value.to_dict())
    forbidden=('label','original_label','facts','expected','poison','split','attack_type')
    assert all(key not in value.to_dict() for key in forbidden)
    assert all(key not in serialized.lower() for key in forbidden)

@pytest.mark.parametrize('bad', [dict(original_label='normal'),dict(facts={}),dict(expected_answer='x'),dict(attack_type='x'),dict(is_poison=True),dict(metadata={'facts':{}})])
def test_runtime_rejects_ground_truth(bad):
    with pytest.raises(TypeError):
        DetectionInput('d','c','x',bad)
