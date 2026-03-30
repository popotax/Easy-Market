"""Process raw scraped CSV files into a clean training dataset."""

from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.preprocessing.cleaner import DataCleaner


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> int:
    config = load_config(ROOT / "config" / "config.yaml")

    output_cfg = config["output"]
    proc_cfg = config["processing"]
    outlier_cfg = proc_cfg.get("outlier_removal", {})

    raw_dir = ROOT / output_cfg["raw_data_dir"].replace("./", "")
    processed_dir = ROOT / output_cfg["processed_data_dir"].replace("./", "")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Exclude synthetic merged files and only process site-specific snapshots.
    raw_files = sorted(
        p
        for p in raw_dir.glob("*.csv")
        if not p.name.startswith("all_sites_")
    )

    if not raw_files:
        print(f"[ERROR] No raw CSV files found in {raw_dir}")
        return 1

    cleaner = DataCleaner(
        min_price_usd=float(outlier_cfg.get("min_price_usd", 5)),
        max_price_usd=float(outlier_cfg.get("max_price_usd", 5000)),
    )

    raw_df = cleaner.load_raw_files(raw_files)
    cleaned_df, report = cleaner.clean(raw_df)

    output_file = processed_dir / output_cfg.get("processed_csv_name", "training_data.csv")
    cleaned_df.to_csv(output_file, index=False)

    print("[OK] Processing completed")
    print(f"[INFO] Raw input files: {len(raw_files)}")
    print(f"[INFO] Input rows: {report.input_rows}")
    print(f"[INFO] After dropna: {report.after_dropna_rows}")
    print(f"[INFO] After dedup: {report.after_dedup_rows}")
    print(f"[INFO] After outlier filters: {report.after_outlier_rows}")
    print(f"[OK] Output rows: {report.output_rows}")
    print(f"[OK] Saved: {output_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
