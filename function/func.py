# Function
# Follows the Knative Functions Python HTTP template:
# https://github.com/knative/func/blob/main/docs/function-templates/python.md
import asyncio
import json
import logging
import os
from urllib.parse import parse_qs

from .screener import screen


def new():
    """ New is the only method that must be implemented by a Function.
    The instance returned can be of any name.
    """
    return Function()


class Function:
    def __init__(self):
        """ Default to the process environment; start() replaces it with the
        platform's configuration dict when the instance starts.
        """
        self.cfg = dict(os.environ)

    async def handle(self, scope, receive, send):
        """ Handle all HTTP requests to this Function other than readiness
        and liveness probes."""
        query = {k: v[0] for k, v in
                 parse_qs((scope.get("query_string") or b"").decode()).items()}

        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break

        try:
            payload = json.loads(body) if body.strip() else {}
            # Non-blocking wait so one slow call does not stall the instance (D3, D5)
            if "sleep_ms" in query:
                await asyncio.sleep(int(query["sleep_ms"]) / 1000)
            status, result = await asyncio.to_thread(screen, payload, query, self.cfg)
        except Exception as exc:  # malformed input -> 500 with the reason in logs
            logging.error("txn-screener error: %r", exc)
            status, result = 500, {"error": str(exc)}

        logging.info("txn-screener %s -> %s %s", result.get("txn_id"), status,
                     result.get("risk", result.get("error")))

        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [
                [b'content-type', b'application/json'],
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': json.dumps(result).encode(),
        })

    def start(self, cfg):
        """ Called when a new instance starts (scale-up or update). cfg is the
        environment configuration: RISK_THRESHOLD, APP_VERSION, PARTNER_API_KEY.
        """
        self.cfg = dict(cfg or {})
        logging.info("txn-screener starting: threshold=%s version=%s secret_loaded=%s",
                     self.cfg.get("RISK_THRESHOLD", "50000"),
                     self.cfg.get("APP_VERSION", "v1"),
                     bool(self.cfg.get("PARTNER_API_KEY")))

    def stop(self):
        """ Called when the instance is scaled down, updated or cancelled. """
        logging.info("txn-screener stopping")

    def alive(self):
        """ Exposed at /health/liveness. """
        return True, "Alive"

    def ready(self):
        """ Exposed at /health/readiness. """
        return True, "Ready"
