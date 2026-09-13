from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from zhiyu.demo.application import DemoApplication
from datetime import datetime, timezone
DEMO_ROWS = [json.loads(x) for x in (REPO_ROOT/'demo/demo_knowledge_base_v2.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
PRESCAN = {x['document_id']: x for x in json.loads((REPO_ROOT/'experiments/phase7/prescan_final.json').read_text(encoding='utf-8'))['documents']}
STATE = {'incoming': None, 'scans': {}}

app = DemoApplication()
class Handler(BaseHTTPRequestHandler):
 def do_POST(self):
  if self.path not in ("/api/run", "/api/scan", "/api/reset"):
   self.send_error(404); return
  try:
   data=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0)))) if self.headers.get("Content-Length") else {}
   out=app.run(data.get("query_text", ""), data.get("scenario", "DEMO")) if self.path=="/api/run" else {}
   body=json.dumps(out,ensure_ascii=False).encode()
  
  except Exception as e: self.send_error(400,str(e)); return
  if self.path == '/api/reset': STATE.update(incoming=None, scans={}); body=json.dumps({'ok':True},ensure_ascii=False).encode()
  elif self.path == '/api/scan':
   doc=next((r for r in DEMO_ROWS if r['demo_document_id']==data.get('document_id')), None)
   if not doc: self.send_error(404); return
   truth=PRESCAN.get(doc['demo_document_id'], {}); decision=truth.get('decision','REVIEW'); STATE['incoming']={**doc,'decision':decision,'prescan_mode':'真实预扫描结果复现','scanned_at':datetime.now(timezone.utc).isoformat()}; STATE['scans'][doc['demo_document_id']]=decision
   body=json.dumps({'document_id':doc['demo_document_id'],'decision':decision,'mechanism':doc.get('mechanism'),'prescan_mode':'真实预扫描结果复现','component_statuses':truth.get('component_statuses',{}),'rule_event_count':truth.get('rule_event_count',0),'behavior_evidence_count':truth.get('behavior_evidence_count',0),'factual_evidence_summary':truth.get('factual_evidence_summary',{}),'judge_status':truth.get('judge_status'),'action': '自动准入 Protected KB' if decision=='SAFE' else ('自动阻断 / 隔离' if decision=='POISON' else '隔离等待复核')},ensure_ascii=False).encode()
  self.send_response(200); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
 def do_GET(self):
  if self.path in ("/", "/index.html"):
   body=(REPO_ROOT / "demo" / "index.html").read_text(encoding="utf-8").encode(); self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
  elif self.path in ('/styles.css','/app.js'):
   p=REPO_ROOT/'demo'/self.path.lstrip('/'); body=p.read_bytes(); self.send_response(200); self.send_header('Content-Type','text/javascript' if self.path.endswith('js') else 'text/css'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
  elif self.path == '/attack_samples/manifest.json':
   body=(REPO_ROOT/'demo/attack_samples/manifest.json').read_bytes(); self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
  elif self.path == '/api/state':
   body=json.dumps({'trusted_seed_count':sum(r.get('is_trusted_seed',False) for r in DEMO_ROWS),'incoming_count':len(STATE['scans']),'review_count':sum(v=='REVIEW' for v in STATE['scans'].values()),'poison_count':sum(v=='POISON' for v in STATE['scans'].values()),'protected_count':sum(r.get('decision')=='SAFE' or r.get('is_trusted_seed',False) for r in DEMO_ROWS if r['demo_document_id'] not in STATE['scans'] or STATE['scans'][r['demo_document_id']]=='SAFE'),'incoming':STATE['incoming']},ensure_ascii=False).encode(); self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
  elif self.path == '/api/presets':
   body=json.dumps(json.loads((REPO_ROOT/'demo/demo_presets_v2.json').read_text(encoding='utf-8')),ensure_ascii=False).encode(); self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
  else: self.send_error(404)
if __name__=="__main__": ThreadingHTTPServer(("127.0.0.1",8000),Handler).serve_forever()




