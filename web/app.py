from __future__ import annotations

import os
from pathlib import Path
import sys

from flask import Flask, jsonify, request
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


app = Flask(__name__)

MODEL = None
FEATURE_COLUMNS = None


def _allowed_origins() -> list[str]:
    raw = (os.getenv("ALLOWED_ORIGINS") or "*").strip()
    if raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


def _cors_origin_for_request() -> str:
    origins = _allowed_origins()
    if "*" in origins:
        return "*"

    incoming = request.headers.get("Origin", "")
    if incoming and incoming in origins:
        return incoming

    return origins[0] if origins else "*"


@app.after_request
def _apply_cors_headers(resp):
    origin = _cors_origin_for_request()
    resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


def load_runtime() -> tuple[object, list[str]]:
    global MODEL, FEATURE_COLUMNS
    if MODEL is None or FEATURE_COLUMNS is None:
        MODEL, FEATURE_COLUMNS = load_model_artifacts(ROOT)
    return MODEL, FEATURE_COLUMNS


@app.get("/healthz")
def healthz():
    return {"status": "ok"}, 200


@app.route("/api/estimate", methods=["POST", "OPTIONS"])
def api_estimate():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    input_tag = str(payload.get("tag") or "").strip()
    token = (os.getenv("BRAWL_API_TOKEN") or "").strip()

    if not input_tag:
        return jsonify({"ok": False, "error": "Missing tag"}), 400
    if not token:
        return jsonify({"ok": False, "error": "Missing BRAWL_API_TOKEN on backend"}), 500

    try:
        model, feature_columns = load_runtime()
        client = BrawlStarsClient(token=token)
        player_data = client.get_player(input_tag)
        row = build_row_from_player_data(player_data)
        estimated_value = predict_account_value(model, feature_columns, row)

        low = round(estimated_value * 0.85, 2)
        high = round(estimated_value * 1.15, 2)

        return jsonify(
            {
                "ok": True,
                "result": {
                    "tag": player_data.get("tag", f"#{input_tag.upper().replace('#', '')}"),
                    "name": player_data.get("name", "Unknown"),
                    "trophies": row["total_trophies"],
                    "num_brawlers": row["num_brawlers"],
                    "avg_level": row["avg_brawler_level"],
                    "account_progress_score": row["rare_skins_count"],
                    "estimated_value": estimated_value,
                    "range_low": low,
                    "range_high": high,
                },
            }
        )
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status == 404:
            return jsonify({"ok": False, "error": "Player tag not found"}), 404
        if status == 403:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "Brawl API denied access (403). Check token and IP whitelist.",
                    }
                ),
                403,
            )
        return jsonify({"ok": False, "error": f"Brawl API error ({status})"}), 502
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Unexpected error: {exc}"}), 500


@app.get("/")
def index():
    return jsonify(
        {
            "ok": True,
            "message": "Backend online. Use POST /api/estimate with JSON {tag: ...}",
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
