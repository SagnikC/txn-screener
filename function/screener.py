"""txn-screener business logic: UPI-style payment risk check.

Scores a payment LOW or HIGH against RISK_THRESHOLD. Kept free of any HTTP or
platform code so func.py (Vayu Functions), container/app.py (U4 image) and the
unit tests all call the same function.

Query parameters that switch on test behaviour (runbook section 3.3):

  fail=1       -> HTTP 500 (D2 errors)
  sleep_ms=N   -> wait N ms; handled in func.py with a non-blocking sleep (D3, D5)
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
BUILD = "v2-knative"


def screen(payload: dict, params: dict, env=None):
    """Return (status_code, body_dict). Raises ValueError on a non-numeric amount."""
    global _COLD
    cold, _COLD = _COLD, False
    payload = payload or {}
    params = params or {}
    env = env if env is not None else os.environ

    if params.get("fail") == "1":
        return 500, {"error": "forced failure (test D2)"}

    hog = bytearray(int(params["alloc_mb"]) * 1024 * 1024) if "alloc_mb" in params else None

    egress_ip = None
    if params.get("egress") == "1":
        egress_ip = urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()

    threshold = float(env.get("RISK_THRESHOLD", "50000"))
    amount = float(payload.get("amount", 0))  # "abc" raises -> 500 (event 'malformed')

    return 200, {
        "txn_id": payload.get("txn_id"),
        "risk": "HIGH" if amount >= threshold else "LOW",
        "amount": amount,
        "threshold": threshold,
        "version": env.get("APP_VERSION", "v1"),
        "build": BUILD,
        "secret_loaded": bool(env.get("PARTNER_API_KEY")),
        "cold_start": cold,
        "instance": socket.gethostname(),
        "uptime_s": round(time.time() - _BOOT, 1),
        "allocated_mb": len(hog) // (1024 * 1024) if hog else 0,
        "egress_ip": egress_ip,
    }
