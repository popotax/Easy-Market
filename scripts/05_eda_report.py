"""Generate exploratory data analysis artifacts from processed training data."""

from __future__ import annotations

from pathlib import Path
import json

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def save_plot_price_distribution(df: pd.DataFrame, out_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(df["price_usd"], bins=20, color="#2a9d8f", edgecolor="#1f2937")
    ax.set_title("Price Distribution (USD)")
    ax.set_xlabel("price_usd")
    ax.set_ylabel("count")
    fig.tight_layout()
    out = out_dir / "price_distribution.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def save_plot_price_by_site(df: pd.DataFrame, out_dir: Path) -> Path:
    site_order = df.groupby("site_source")["price_usd"].median().sort_values().index
    plot_df = df[["site_source", "price_usd"]].copy()

    fig, ax = plt.subplots(figsize=(9, 5))
    data = [plot_df.loc[plot_df["site_source"] == s, "price_usd"] for s in site_order]
    ax.boxplot(data, tick_labels=site_order, patch_artist=True)
    ax.set_title("Price by Marketplace")
    ax.set_xlabel("site_source")
    ax.set_ylabel("price_usd")
    fig.autofmt_xdate(rotation=20)
    fig.tight_layout()
    out = out_dir / "price_by_site_boxplot.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def save_plot_scatter(df: pd.DataFrame, x_col: str, out_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df[x_col], df["price_usd"], alpha=0.65, color="#264653")
    ax.set_title(f"price_usd vs {x_col}")
    ax.set_xlabel(x_col)
    ax.set_ylabel("price_usd")
    fig.tight_layout()
    out = out_dir / f"scatter_price_vs_{x_col}.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def build_summary(df: pd.DataFrame, out_dir: Path) -> dict:
    numeric_cols = [
        "num_brawlers",
        "avg_brawler_level",
        "total_trophies",
        "rare_skins_count",
        "price_usd",
    ]
    corr = df[numeric_cols].corr(numeric_only=True)["price_usd"].drop("price_usd")

    summary = {
        "row_count": int(len(df)),
        "site_counts": df["site_source"].value_counts().to_dict(),
        "price_stats": df["price_usd"].describe().to_dict(),
        "correlation_with_price": corr.sort_values(ascending=False).to_dict(),
        "top_correlated_feature": corr.abs().sort_values(ascending=False).index[0],
    }

    json_out = out_dir / "eda_summary.json"
    json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# EDA Summary",
        "",
        f"- Rows: {summary['row_count']}",
        f"- Top correlated feature with price: {summary['top_correlated_feature']}",
        "",
        "## Site Counts",
    ]
    for site, count in summary["site_counts"].items():
        lines.append(f"- {site}: {count}")

    lines.extend([
        "",
        "## Correlation With Price",
    ])
    for feat, value in summary["correlation_with_price"].items():
        lines.append(f"- {feat}: {value:.4f}")

    md_out = out_dir / "eda_summary.md"
    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return summary


def main() -> int:
    processed_path = ROOT / "data" / "processed" / "training_data.csv"
    if not processed_path.exists():
        print(f"[ERROR] Missing file: {processed_path}")
        print("[INFO] Run: python scripts/02_process_data.py")
        return 1

    out_dir = ROOT / "artifacts" / "eda"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(processed_path)
    if df.empty:
        print("[ERROR] training_data.csv is empty")
        return 1

    save_plot_price_distribution(df, out_dir)
    save_plot_price_by_site(df, out_dir)
    for col in ["num_brawlers", "total_trophies", "rare_skins_count", "avg_brawler_level"]:
        save_plot_scatter(df, col, out_dir)

    summary = build_summary(df, out_dir)

    print("[OK] EDA artifacts generated")
    print(f"[INFO] Rows analyzed: {summary['row_count']}")
    print(f"[INFO] Top correlated feature: {summary['top_correlated_feature']}")
    print(f"[OK] Output directory: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
