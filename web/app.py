from __future__ import annotations

import os
from pathlib import Path
import sys

from flask import Flask, render_template, request
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.brawlstars_api import BrawlStarsClient
from src.services.valuation import (
    build_row_from_player_data,
    load_model_artifacts,
    predict_account_value,
)


app = Flask(__name__, template_folder="templates", static_folder="static")

MODEL = None
FEATURE_COLUMNS = None


def load_runtime() -> tuple[object, list[str]]:
    global MODEL, FEATURE_COLUMNS
    if MODEL is None or FEATURE_COLUMNS is None:
        MODEL, FEATURE_COLUMNS = load_model_artifacts(ROOT)
    return MODEL, FEATURE_COLUMNS


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    input_tag = ""

    if request.method == "POST":
        input_tag = (request.form.get("tag") or "").strip()
        token = (os.getenv("BRAWL_API_TOKEN") or "").strip()

        if not input_tag:
            error = "Please enter a player tag."
        elif not token:
            error = "Missing BRAWL_API_TOKEN environment variable."
        else:
            try:
                model, feature_columns = load_runtime()
                client = BrawlStarsClient(token=token)
                player_data = client.get_player(input_tag)
                row = build_row_from_player_data(player_data)
                estimated_value = predict_account_value(model, feature_columns, row)

                low = round(estimated_value * 0.85, 2)
                high = round(estimated_value * 1.15, 2)

                result = {
                    "tag": player_data.get("tag", f"#{input_tag.upper().replace('#', '')}"),
                    "name": player_data.get("name", "Unknown"),
                    "trophies": row["total_trophies"],
                    "num_brawlers": row["num_brawlers"],
                    "avg_level": row["avg_brawler_level"],
                    "account_progress_score": row["rare_skins_count"],
                    "estimated_value": estimated_value,
                    "range_low": low,
                    "range_high": high,
                }
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status == 404:
                    error = "Player tag not found. Check the tag and try again."
                elif status == 403:
                    error = "API token is invalid or does not have access."
                else:
                    error = f"Brawl API error ({status})."
            except Exception as exc:
                error = f"Unexpected error: {exc}"

    return render_template("index.html", result=result, error=error, input_tag=input_tag)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
