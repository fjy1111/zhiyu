from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT
sys.path.insert(0, str(ROOT / "src"))
from zhiyu.demo.application import DemoApplication
from zhiyu.demo.runtime_documents import (
    build_scan_response,
    load_final_scenarios,
    load_frozen_scan_records,
    load_runtime_documents,
    load_trusted_seed_ids,
)

CAT = load_final_scenarios(ROOT)
DOCS = load_runtime_documents(ROOT)
SCANS = load_frozen_scan_records(ROOT)
TRUST = load_trusted_seed_ids(ROOT)
STATE = {"incoming": None, "scans": {}}
app = DemoApplication()
STATIC = {
    "/": (ROOT / "demo/index.html", "text/html; charset=utf-8"),
    "/index.html": (ROOT / "demo/index.html", "text/html; charset=utf-8"),
    "/styles.css": (ROOT / "demo/styles.css", "text/css; charset=utf-8"),
    "/app.js": (ROOT / "demo/app.js", "text/javascript; charset=utf-8"),
}


def send(handler, payload, status=200, content_type="application/json; charset=utf-8"):
    body = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def build_state():
    review = {key for key, value in STATE["scans"].items() if value == "REVIEW"}
    poison = {key for key, value in STATE["scans"].items() if value == "POISON"}
    protected = set(TRUST) | {key for key, value in STATE["scans"].items() if value == "SAFE"}

    def rows(ids):
        return [DOCS[document_id] for document_id in ids if document_id in DOCS]

    return {
        "trusted_documents": rows(TRUST),
        "protected_documents": rows(protected),
        "review_documents": rows(review),
        "poison_documents": rows(poison),
        "incoming_document": STATE["incoming"],
        "counts": {
            "trusted": len(TRUST),
            "protected": len(protected),
            "review": len(review),
            "poison": len(poison),
        },
    }


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0)) or b"{}"
        data = json.loads(raw)
        try:
            path = urlparse(self.path).path
            if path == "/api/run":
                if "scenario_id" not in data or "scenario" in data:
                    raise ValueError("scenario_id required")
                return send(self, app.run(data["query_text"], data["scenario_id"]))
            if path == "/api/reset":
                STATE.update(incoming=None, scans={})
                return send(self, {"ok": True})
            if path == "/api/scan":
                payload = build_scan_response(data.get("document_id"), DOCS, SCANS)
                if payload is None:
                    return send(self, {"error": "unknown document"}, 404)
                STATE["scans"][payload["document_id"]] = payload["actual_decision"]
                STATE["incoming"] = {**DOCS[payload["document_id"]], **payload}
                return send(self, payload)
            return send(self, {"error": "not found"}, 404)
        except Exception as exc:
            return send(self, {"error": str(exc)}, 400)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/scenarios":
            return send(self, CAT)
        if path == "/api/presets":
            return send(
                self,
                [
                    {
                        "scenario_id": item["scenario_id"],
                        "mechanism": item["mechanism"],
                        "primary_question": item["primary_question"],
                    }
                    for item in CAT
                ],
            )
        if path == "/api/state":
            return send(self, build_state())
        if path in STATIC:
            file_path, content_type = STATIC[path]
            return send(self, file_path.read_bytes(), 200, content_type)
        return send(self, {"error": "not found"}, 404)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
