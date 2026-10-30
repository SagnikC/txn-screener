"""
Unit tests in the Knative Functions template style: drive the ASGI handler
with mocked receive/send and check status and body for each test event.
"""
import json
import os

import pytest

from function import new
from function.screener import screen

EVENTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "events")


def load(name):
    with open(os.path.join(EVENTS, f"{name}.json"), "rb") as f:
        return f.read()


async def call(body=b"", query=b"", cfg=None):
    f = new()
    if cfg is not None:
        f.start(cfg)
    sent = []

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        sent.append(message)

    await f.handle({"type": "http", "query_string": query}, receive, send)
    start = next(m for m in sent if m["type"] == "http.response.start")
    body_msg = next(m for m in sent if m["type"] == "http.response.body")
    return start["status"], json.loads(body_msg["body"])


@pytest.mark.asyncio
async def test_function_handle():
    status, body = await call(load("high-risk"))
    assert status == 200 and body["risk"] == "HIGH"


@pytest.mark.asyncio
async def test_low_risk():
    status, body = await call(load("low-risk"))
    assert status == 200 and body["risk"] == "LOW"


@pytest.mark.asyncio
async def test_boundary_is_high():
    status, body = await call(load("boundary"))
    assert status == 200 and body["risk"] == "HIGH"


@pytest.mark.asyncio
async def test_empty_is_low():
    status, body = await call(load("empty"))
    assert status == 200 and body["risk"] == "LOW" and body["txn_id"] is None


@pytest.mark.asyncio
async def test_no_body():
    status, body = await call(b"")
    assert status == 200 and body["risk"] == "LOW"


@pytest.mark.asyncio
async def test_malformed_returns_500():
    status, body = await call(load("malformed"))
    assert status == 500 and "error" in body


@pytest.mark.asyncio
async def test_forced_failure():
    status, _ = await call(load("high-risk"), b"fail=1")
    assert status == 500


@pytest.mark.asyncio
async def test_sleep_param():
    status, _ = await call(load("high-risk"), b"sleep_ms=10")
    assert status == 200


@pytest.mark.asyncio
async def test_threshold_from_start_cfg():
    status, body = await call(load("high-risk"), cfg={"RISK_THRESHOLD": "80000"})
    assert body["risk"] == "LOW" and body["threshold"] == 80000.0


@pytest.mark.asyncio
async def test_secret_never_returned():
    status, body = await call(load("high-risk"), cfg={"PARTNER_API_KEY": "s3cr3t-value"})
    assert body["secret_loaded"] is True
    assert "s3cr3t-value" not in json.dumps(body)


def test_health_probes():
    f = new()
    assert f.alive() == (True, "Alive")
    assert f.ready() == (True, "Ready")


def test_screen_directly():
    assert screen({"amount": 72000}, {}, {})[1]["risk"] == "HIGH"
