from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO_ROOT=ROOT;sys.path.insert(0,str(ROOT/'src'))
from zhiyu.demo.application import DemoApplication
ROWS=[json.loads(x) for x in (ROOT/'demo/demo_knowledge_base_v2.jsonl').read_text(encoding='utf8').splitlines()]
CAT=json.loads((ROOT/'demo/final_live_scenarios.json').read_text(encoding='utf8'))
TRUST={x['document_id'] for x in json.loads((ROOT/'demo/trusted_seed_manifest.json').read_text(encoding='utf8'))['documents']}
TRUTH={x['document_id']:x for x in json.loads((ROOT/'experiments/phase7/prescan_final.json').read_text(encoding='utf8'))['documents']};STATE={'incoming':None,'scans':{}};app=DemoApplication()
def send(h,x,s=200):
 b=json.dumps(x,ensure_ascii=False).encode();h.send_response(s);h.send_header('Content-Type','application/json; charset=utf-8');h.send_header('Content-Length',str(len(b)));h.end_headers();h.wfile.write(b)
class Handler(BaseHTTPRequestHandler):
 def do_POST(self):
  d=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or '{}')
  try:
   if self.path=='/api/run':
    if 'scenario_id' not in d or 'scenario' in d: raise ValueError('scenario_id required')
    return send(self,app.run(d['query_text'],d['scenario_id']))
   if self.path=='/api/reset': STATE.update(incoming=None,scans={});return send(self,{'ok':True})
   if self.path=='/api/scan':
    x=next((r for r in ROWS if r['demo_document_id']==d.get('document_id')),None)
    if not x:return send(self,{'error':'unknown document'},404)
    t=TRUTH.get(x['demo_document_id'],{});dec=t.get('decision','REVIEW');STATE['scans'][x['demo_document_id']]=dec;STATE['incoming']={**x,'actual_decision':dec,'prescan_mode':'真实预扫描结果复现'};return send(self,{'document_id':x['demo_document_id'],'actual_decision':dec,'prescan_mode':'真实预扫描结果复现'})
   return send(self,{'error':'not found'},404)
  except Exception as e:return send(self,{'error':str(e)},400)
 def do_GET(self):
  if self.path=='/api/scenarios':return send(self,CAT)
  if self.path=='/api/presets':return send(self,[{'scenario_id':x['scenario_id'],'questions':x['generated_preset_questions']} for x in CAT])
  if self.path=='/api/state':
   ids=lambda s:[r for r in ROWS if r['demo_document_id'] in s];rev={k for k,v in STATE['scans'].items() if v=='REVIEW'};poi={k for k,v in STATE['scans'].items() if v=='POISON'};pro=TRUST|{k for k,v in STATE['scans'].items() if v=='SAFE'};return send(self,{'trusted_documents':ids(TRUST),'protected_documents':ids(pro),'review_documents':ids(rev),'poison_documents':ids(poi),'incoming_document':STATE['incoming'],'counts':{'trusted':len(TRUST),'protected':len(pro),'review':len(rev),'poison':len(poi)}})
  if self.path in ('/','/index.html'):
   b=(ROOT/'demo/index.html').read_bytes();self.send_response(200);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
  return send(self,{'error':'not found'},404)
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()
