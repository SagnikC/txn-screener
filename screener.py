"""txn-screener business logic: UPI-style payment risk check.

Scores a payment LOW or HIGH against RISK_THRESHOLD. No HTTP or platform code
here, so func.py and the unit tests call the same function.

Query parameters that switch on test behaviour (runbook section 3.3):

  fail=1       -> raise, which the function runtime returns as HTTP 500 (D2)
  sleep_ms=N   -> wait N ms (D3 load, D5 timeout)
  alloc_mb=N   -> allocate N MB (D4 out-of-memory)
  egress=1     -> return the outbound IP (D12 network)

The response never contains the partner API key, only whether it was loaded.
"""
import os
import socket
import time
import urllib.request

_COLD = True
_BOOT = time.time()
BUILD = "v3-cloudevents"


class ForcedFailure(Exception):
    """Raised for fail=1 so the runtime returns HTTP 500."""


def screen(payload, params):
    """Return the result dict. Raises on fail=1 or a non-numeric amount."""
    global _COLD
    cold, _COLD = _COLD, False
    payload = payload if isinstance(payload, dict) else {}
    params = params or {}

    if params.get("fail") == "1":
        raise ForcedFailure("forced failure (test D2)")

    if "sleep_ms" in params:
        time.sleep(int(params["sleep_ms"]) / 1000)

    hog = bytearray(int(params["alloc_mb"]) * 1024 * 1024) if "alloc_mb" in params else None

    egress_ip = None
    if params.get("egress") == "1":
        egress_ip = urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()

    threshold = float(os.getenv("RISK_THRESHOLD", "50000"))
    amount = float(payload.get("amount", 0))  # "abc" raises ValueError -> HTTP 500

    return {
        "txn_id": payload.get("txn_id"),
        "risk": "HIGH" if amount >= threshold else "LOW",
        "amount": amount,
        "threshold": threshold,
        "version": os.getenv("APP_VERSION", "v1"),
        "build": BUILD,
        "secret_loaded": bool(os.getenv("PARTNER_API_KEY")),
        "cold_start": cold,
        "instance": socket.gethostname(),
        "uptime_s": round(time.time() - _BOOT, 1),
        "allocated_mb": len(hog) // (1024 * 1024) if hog else 0,
        "egress_ip": egress_ip,
    }
