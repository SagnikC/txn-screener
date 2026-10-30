import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from handler import handle  # noqa: E402
from screener import screen  # noqa: E402

EVENTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "events")


def load(name):
    with open(os.path.join(EVENTS, f"{name}.json")) as f:
        return json.load(f)


def test_high_risk():
    assert screen(load("high-risk"), {})[1]["risk"] == "HIGH"


def test_low_risk():
    assert screen(load("low-risk"), {})[1]["risk"] == "LOW"


def test_boundary_is_high():
    assert screen(load("boundary"), {})[1]["risk"] == "HIGH"


def test_empty_is_low():
    status, body = screen(load("empty"), {})
    assert status == 200 and body["risk"] == "LOW" and body["txn_id"] is None


def test_forced_failure():
    assert screen({}, {"fail": "1"})[0] == 500


def test_malformed_returns_500_via_handler():
    status, text = handle(json.dumps(load("malformed")).encode(), {})
    assert status == 500 and "error" in json.loads(text)


def test_threshold_from_env(monkeypatch):
    monkeypatch.setenv("RISK_THRESHOLD", "80000")
    assert screen(load("high-risk"), {})[1]["risk"] == "LOW"


def test_secret_never_returned(monkeypatch):
    monkeypatch.setenv("PARTNER_API_KEY", "s3cr3t-value")
    body = screen(load("high-risk"), {})[1]
    assert body["secret_loaded"] is True
    assert "s3cr3t-value" not in json.dumps(body)


def test_handler_simple_style():
    status, text = handle(json.dumps(load("high-risk")).encode(), {})
    assert status == 200 and json.loads(text)["risk"] == "HIGH"


@pytest.mark.parametrize("name", ["high-risk", "low-risk", "boundary", "empty"])
def test_events_are_valid_json(name):
    assert isinstance(load(name), dict)
