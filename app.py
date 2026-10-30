"""Web server wrapper for upload option U4 (image from Vayu Container Registry).

Built into the image by the Dockerfile. Listens on $PORT (default 8080).
"""
import os

from flask import Flask, jsonify, request

from screener import screen

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def handle():
    try:
        status, body = screen(request.get_json(silent=True) or {}, request.args.to_dict())
    except Exception as exc:
        app.logger.error("txn-screener: %r", exc)
        status, body = 500, {"error": str(exc)}
    return jsonify(body), status


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
