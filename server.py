"""
Simple backend service that issues user-scoped Coze OAuth tokens.

Run:
    pip install -r requirements.txt
    uvicorn server:app --reload
or
    flask --app server run
"""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, render_template_string

from coze_oauth import OAuthConfig

config = OAuthConfig.from_env()
BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

# Load Bot ID from environment variable
BOT_ID = os.getenv("COZE_BOT_ID", "7574314241218904100")


def _ensure_user_id() -> str:
    data = request.get_json(silent=True) or {}
    user_id = data.get("userId") or data.get("uid") or request.args.get("userId")
    if not user_id:
        raise ValueError("Missing userId in request body")
    return str(user_id)


@app.post("/api/chat-token")
def issue_chat_token():
    try:
        user_id = _ensure_user_id()
        token_payload = config.issue_access_token(session_name=user_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # pylint: disable=broad-except
        return jsonify({"error": str(exc)}), 500

    return jsonify(
        {
            "token": token_payload.get("access_token"),
            "token_type": token_payload.get("token_type"),
            "expires_in": token_payload.get("expires_in"),
            "expires_at": token_payload.get("expires_at"),
        }
    )


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}


@app.get("/")
def serve_index():
    # Read HTML and inject BOT_ID
    html_path = Path(app.static_folder) / "index.html"
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Inject BOT_ID as a global variable before other scripts
    injection = f'<script>window.COZE_BOT_ID = "{BOT_ID}";</script>'
    html_content = html_content.replace('</head>', f'{injection}\n</head>')
    
    return html_content


@app.get("/<path:asset>")
def serve_static(asset: str):
    if asset.endswith((".js", ".css", ".html")):
        return send_from_directory(app.static_folder, asset)
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)

