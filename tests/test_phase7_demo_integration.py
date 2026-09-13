import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ALLOWED_DECISIONS = {'SAFE', 'REVIEW', 'POISON', 'CURATED_TRUSTED_SEED'}
SYNTHETIC_SCAN_IDS = (
    'syn-ft-library',
    'syn-ft-scholarship',
    'syn-conf-exam',
    'syn-conf-dorm',
    'syn-conf-scholarship',
)


def _load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))


def _catalog():
    catalog = _load_json('demo/final_live_scenarios.json')
    assert isinstance(catalog, list)
    return catalog


def _expected_rh_distractors(incoming_document_id, seeds):
    topic = incoming_document_id.removeprefix('syn-rh-')
    target = next(item['document_id'] for item in seeds if item['topic'] == topic)
    distractors = [item['document_id'] for item in seeds if item['document_id'] != target][:3]
    return target, distractors


def test_runtime_loader_resolves_all_final_scenario_documents():
    from zhiyu.demo.runtime_documents import load_runtime_documents, resolve_scenario_documents

    catalog = _catalog()
    assert len(catalog) == 18
    documents = load_runtime_documents(ROOT)
    for spec in catalog:
        rows = resolve_scenario_documents(spec, documents)
        assert rows
        assert all(row.get('runtime_text') for row in rows)


def test_actual_decision_is_string_schema():
    catalog = _catalog()
    assert len(catalog) == 18
    for spec in catalog:
        decision = spec['actual_decision']
        assert isinstance(decision, str), spec['scenario_id']
        assert decision in ALLOWED_DECISIONS, spec['scenario_id']


def test_rh_runtime_matches_rank_validation_composition():
    from zhiyu.demo.application import materialize_scenario

    catalog = _catalog()
    validation = _load_json('experiments/phase7/rh_rank_validation.json')
    seeds = _load_json('demo/trusted_seed_manifest.json')['documents']
    rh_specs = [item for item in catalog if item['mechanism'] == 'RETRIEVAL_HIJACKING']
    passed = [item for item in validation if item.get('passed')][:3]
    assert len(rh_specs) == 3
    assert len(passed) == 3
    for spec, row in zip(rh_specs, passed):
        assert spec['incoming_document_id'] == row['incoming_document_id']
        target, distractors = _expected_rh_distractors(row['incoming_document_id'], seeds)
        assert spec['trusted_seed_document_ids'] == [target]
        assert spec['distractor_document_ids'] == distractors
        _, kb = materialize_scenario(spec['scenario_id'], ROOT)
        vanilla_ids = set(kb.indexes.vanilla.document_ids)
        protected_ids = set(kb.indexes.protected.document_ids)
        assert vanilla_ids == set([target, spec['incoming_document_id'], *distractors])
        assert protected_ids == set([target, *distractors])
        assert spec['incoming_document_id'] not in protected_ids


class _Server:
    def __enter__(self):
        import demo.server as demo_server
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), demo_server.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.host, self.port = self.httpd.server_address
        return self

    def __exit__(self, exc_type, exc, tb):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)

    def request(self, method, path, body=None):
        conn = HTTPConnection(self.host, self.port, timeout=10)
        try:
            payload = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
            headers = {'Content-Type': 'application/json; charset=utf-8'} if payload else {}
            conn.request(method, path, body=payload, headers=headers)
            response = conn.getresponse()
            data = response.read()
            content_type = response.getheader('Content-Type')
            return response.status, content_type, data
        finally:
            conn.close()


def test_synthetic_scan_reproduces_frozen_records():
    with _Server() as server:
        for document_id in SYNTHETIC_SCAN_IDS:
            status, content_type, data = server.request('POST', '/api/scan', {'document_id': document_id})
            assert status == 200, document_id
            assert content_type.startswith('application/json')
            payload = json.loads(data.decode('utf-8'))
            assert payload['document_id'] == document_id
            assert isinstance(payload['actual_decision'], str)
            assert payload['prescan_mode'] == '真实预扫描结果复现'
            assert 'mechanism' in payload
            assert 'component_statuses' in payload
            assert 'factual_evidence_summary' in payload
            assert 'judge_status' in payload


def test_static_css_and_js_routes():
    with _Server() as server:
        status, content_type, data = server.request('GET', '/styles.css')
        assert status == 200
        assert content_type.startswith('text/css')
        assert data
        status, content_type, data = server.request('GET', '/app.js')
        assert status == 200
        assert 'javascript' in content_type
        assert data


def test_scenario_isolation_across_concurrent_runs():
    catalog = {item['scenario_id']: item for item in _catalog()}
    left_id = 'ft-01'
    right_id = 'prompt_injection-01'
    left_docs = set(catalog[left_id]['trusted_seed_document_ids'] + [catalog[left_id]['incoming_document_id']])
    right_docs = set(catalog[right_id]['trusted_seed_document_ids'] + [catalog[right_id]['incoming_document_id']])
    assert left_docs.isdisjoint(right_docs)

    def _run(server, scenario_id):
        status, _, data = server.request(
            'POST',
            '/api/run',
            {'scenario_id': scenario_id, 'query_text': catalog[scenario_id]['primary_question']},
        )
        assert status == 200, data
        payload = json.loads(data.decode('utf-8'))
        vanilla = {chunk['document_id'] for chunk in payload['vanilla']['chunks']}
        protected = {chunk['document_id'] for chunk in payload['protected']['chunks']}
        return payload['scenario_id'], vanilla | protected

    with _Server() as server:
        with ThreadPoolExecutor(max_workers=2) as pool:
            future_left = pool.submit(_run, server, left_id)
            future_right = pool.submit(_run, server, right_id)
            left_scenario, left_seen = future_left.result()
            right_scenario, right_seen = future_right.result()
        assert left_scenario == left_id
        assert right_scenario == right_id
        assert left_seen <= left_docs
        assert right_seen <= right_docs
        assert left_seen.isdisjoint(right_docs)
        assert right_seen.isdisjoint(left_docs)
