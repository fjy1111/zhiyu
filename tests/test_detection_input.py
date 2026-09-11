import json
from zhiyu.models.detection import DetectionInput

def test_no_ground_truth_leakage():
    value=DetectionInput('d','c','payload',{'request_id':'r'}); serialized=json.dumps(value.to_dict())
    forbidden=('label','original_label','facts','expected','poison','split','attack_type')
    assert all(key not in value.to_dict() for key in forbidden)
    assert all(key not in serialized.lower() for key in forbidden)
