"""Run Phase 2 rule-only evaluation on development_tune and development_generalization."""
from _common import ROOT, write_json
from zhiyu.eval.phase2 import evaluate_phase2, render_markdown


def main() -> int:
    report = evaluate_phase2(ROOT)
    out_dir = ROOT / "experiments" / "phase2"
    write_json(out_dir / "rule_only_baseline.json", report)
    (out_dir / "rule_only_baseline.md").write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
