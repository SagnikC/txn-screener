"""Entry point for Vayu Functions (upload options U1 GitHub, U2 Vayu GitLab, U3 zip).

The exact handler signature Vayu Functions expects is open item 2 in the runbook.
This file supports the two common shapes:

  1. handle(body, query)  -> (status, json_string)      simple FaaS style
  2. new() -> object with handle(scope, receive, send)  ASGI style used by some
     Kubernetes-native function templates

If the console's Python template generates a different handler, keep screener.py
as is and call screen() from that handler instead.
"""
import json
from urllib.parse import parse_qs

from screener import screen


def handle(body=b"", query=None):
    """Simple style: raw request body (bytes or str) and a dict of query params."""
    if isinstance(body, (bytes, bytearray)):
        body = body.decode() if body else ""
    data = json.loads(body) if body else {}
    try:
        status, result = screen(data, query or {})
    except Exception as exc:  # malformed input -> 500 with the reason, visible in logs
        print(f"ERROR txn-screener: {exc!r}", flush=True)
        status, result = 500, {"error": str(exc)}
    return status, json.dumps(result)


class _AsgiFunction:
    """ASGI style: platform calls handle(scope, receive, send)."""

    async def handle(self, scope, receive, send):
        body = b""
        more = True
        while more:
            msg = await receive()
            body += msg.get("body", b"")
            more = msg.get("more_body", False)
        query = {k: v[0] for k, v in parse_qs(scope.get("query_string", b"").decode()).items()}
        status, text = handle(body, query)
        await send({"type": "http.response.start", "status": status,
                    "headers": [[b"content-type", b"application/json"]]})
        await send({"type": "http.response.body", "body": text.encode()})

    def alive(self):
        return True, "alive"

    def ready(self):
        return True, "ready"


def new():
    return _AsgiFunction()
