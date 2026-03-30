"""Compare model metrics before and after scraping/parser improvements."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "data" / "models"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pct_change(new: float, old: float) -> float:
    if old == 0:
        return 0.0
    return ((new - old) / abs(old)) * 100.0


def main() -> int:
    before_path = MODELS_DIR / "model_config_before_improvements.json"
    after_path = MODELS_DIR / "model_config.json"

    if not before_path.exists() or not after_path.exists():
        print("[ERROR] Missing comparison files in data/models")
        return 1

    before = load_json(before_path)
    after = load_json(after_path)

    b = before["best_metrics"]
    a = after["best_metrics"]

    report = {
        "before": b,
        "after": a,
        "delta": {
            "mae": a["mae"] - b["mae"],
            "rmse": a["rmse"] - b["rmse"],
            "r2": a["r2"] - b["r2"],
        },
        "delta_percent": {
            "mae": pct_change(a["mae"], b["mae"]),
            "rmse": pct_change(a["rmse"], b["rmse"]),
        },
    }

    out_json = MODELS_DIR / "model_improvement_report.json"
    out_md = MODELS_DIR / "model_improvement_report.md"

    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Model Improvement Report",
        "",
        "## Before",
        f"- MAE: {b['mae']:.4f}",
        f"- RMSE: {b['rmse']:.4f}",
        f"- R2: {b['r2']:.4f}",
        "",
        "## After",
        f"- MAE: {a['mae']:.4f}",
        f"- RMSE: {a['rmse']:.4f}",
        f"- R2: {a['r2']:.4f}",
        "",
        "## Delta",
        f"- MAE: {report['delta']['mae']:.4f} ({report['delta_percent']['mae']:.2f}%)",
        f"- RMSE: {report['delta']['rmse']:.4f} ({report['delta_percent']['rmse']:.2f}%)",
        f"- R2: {report['delta']['r2']:.4f}",
    ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("[OK] Comparison report generated")
    print(f"[OK] {out_json}")
    print(f"[OK] {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
