"""Web server wrapper for upload option U4 (image from Vayu Container Registry).

Uses the same business logic as the function (function/screener.py).
Listens on $PORT (default 8080). Build from the repo root:
    docker build -f container/Dockerfile -t <registry>/demo/txn-screener:1.0.0 .
"""
import os
import time

from flask import Flask, jsonify, request

from function.screener import screen

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def handle():
    params = request.args.to_dict()
    try:
        if "sleep_ms" in params:
            time.sleep(int(params["sleep_ms"]) / 1000)
        status, body = screen(request.get_json(silent=True) or {}, params)
    except Exception as exc:
        app.logger.error("txn-screener: %r", exc)
        status, body = 500, {"error": str(exc)}
    return jsonify(body), status


@app.route("/health/liveness")
@app.route("/health/readiness")
def health():
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
