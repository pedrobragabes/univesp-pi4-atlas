from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, jsonify, render_template

from atlas.pipeline import ARTIFACTS, RAW_PATH, run_pipeline


def load_artifacts(artifacts: Path = ARTIFACTS) -> tuple[dict, list[dict]]:
    if not (artifacts / "metrics.json").exists() or not (artifacts / "territories.json").exists():
        run_pipeline(RAW_PATH, artifacts)
    metrics = json.loads((artifacts / "metrics.json").read_text(encoding="utf-8"))
    territories = json.loads((artifacts / "territories.json").read_text(encoding="utf-8"))
    return metrics, territories


def create_app(artifacts: Path = ARTIFACTS) -> Flask:
    app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / "templates"), static_folder=str(Path(__file__).resolve().parents[1] / "static"))

    @app.after_request
    def security_headers(response):
        response.headers["Content-Security-Policy"] = "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; img-src 'self' data:; object-src 'none'; style-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.get("/")
    def dashboard():
        metrics, territories = load_artifacts(artifacts)
        maximum = max((item["pressao_alta_pct"] for item in territories), default=1) or 1
        return render_template("dashboard.html", metrics=metrics, territories=territories, maximum=maximum)

    @app.get("/metodo")
    def method():
        return render_template("method.html")

    @app.get("/api/resumo")
    def api_summary():
        metrics, territories = load_artifacts(artifacts)
        return jsonify({"metrics": metrics, "territories": territories})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3003, debug=False)
