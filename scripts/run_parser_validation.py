"""Validate real format fixtures and one development TXT without held-out reads."""
from collections import Counter
from _common import ROOT, MANIFESTS, write_json
from zhiyu.dataset import DatasetPolicy
from zhiyu.parser.document_parser import DocumentParser

def main():
    policy, parser = DatasetPolicy(ROOT), DocumentParser()
    paths = [p for p in policy.files("file_format_test", "validation")
             if p.parent.name == "documents" and p.suffix.lower() in parser.routes]
    paths.append(next(p for p in policy.files("demo_set", "validation") if p.suffix == ".txt"))
    results, formats, warnings = [], {}, Counter()
    for path in paths:
        rel = path.relative_to(policy.raw).as_posix()
        counts = formats.setdefault(path.suffix, {"total": 0, "success": 0, "failed": 0, "empty_text": 0})
        counts["total"] += 1
        try:
            doc = parser.parse(path, relative_path=rel)
            counts["success"] += 1
            counts["empty_text"] += int(not doc.text)
            warnings.update(doc.warnings)
            results.append({"path": rel, "success": True, "text_length": len(doc.text),
                            "warnings": doc.warnings})
        except Exception as exc:
            counts["failed"] += 1
            results.append({"path": rel, "success": False, "error": type(exc).__name__})
    report = {k: sum(f[k] for f in formats.values()) for k in ("total", "success", "failed", "empty_text")}
    report.update(warnings=dict(warnings), by_format=formats, files=results)
    write_json(MANIFESTS / "parser_validation.json", report)
    print({k: v for k, v in report.items() if k != "files"})
    return int(report["failed"] > 0)

if __name__ == "__main__":
    raise SystemExit(main())

