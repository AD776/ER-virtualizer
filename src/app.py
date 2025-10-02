"""Flask application exposing the entity-relationship visualiser."""

from __future__ import annotations

from typing import Optional

from flask import Flask, jsonify, render_template, request

from .cli import build_pipeline
from .pipeline import Pipeline

_pipeline: Optional[Pipeline] = None


def _get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    @app.get("/")
    def homepage():  # pragma: no cover - exercised via manual usage
        return render_template("index.html")

    @app.post("/api/triplets")
    def generate_triplets():
        payload = request.get_json(silent=True) or {}
        text = payload.get("text", "") if isinstance(payload, dict) else ""
        if not isinstance(text, str) or not text.strip():
            return (
                jsonify({"error": "Input text must be a non-empty string.", "triplets": []}),
                400,
            )

        triplets = _get_pipeline().generate_triplets(text)
        return jsonify({"triplets": triplets})

    @app.get("/healthz")
    def healthcheck():  # pragma: no cover - trivial endpoint
        return jsonify({"status": "ok"})

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover - manual launch helper
    app.run(debug=True, host="127.0.0.1", port=8000)
