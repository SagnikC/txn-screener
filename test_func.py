from cloudevents.http import CloudEvent
from parliament import Context

import os
import unittest

func = __import__("func")


def make_event(data):
    # - The CloudEvent "id" is generated if omitted. "specversion" defaults to "1.0".
    attributes = {
        "type": "dev.knative.function",
        "source": "https://knative.dev/python.event",
    }
    context = Context(req=None)
    context.cloud_event = CloudEvent(attributes, data)
    return context


class TestFunc(unittest.TestCase):

  def setUp(self):
    os.environ.pop("RISK_THRESHOLD", None)
    os.environ.pop("PARTNER_API_KEY", None)

  def test_func(self):
    body = func.main(make_event({"txn_id": "T-0001", "amount": 72000}))
    self.assertEqual(body.data["risk"], "HIGH")
    self.assertEqual(body["type"], "vayu.txn.screened")

  def test_low_risk(self):
    body = func.main(make_event({"txn_id": "T-0002", "amount": 1200}))
    self.assertEqual(body.data["risk"], "LOW")

  def test_boundary_is_high(self):
    body = func.main(make_event({"txn_id": "T-0003", "amount": 50000}))
    self.assertEqual(body.data["risk"], "HIGH")

  def test_empty_is_low(self):
    body = func.main(make_event({}))
    self.assertEqual(body.data["risk"], "LOW")
    self.assertIsNone(body.data["txn_id"])

  def test_malformed_raises(self):
    with self.assertRaises(ValueError):
      func.main(make_event({"txn_id": "T-0004", "amount": "abc"}))

  def test_threshold_from_env(self):
    os.environ["RISK_THRESHOLD"] = "80000"
    body = func.main(make_event({"amount": 72000}))
    self.assertEqual(body.data["risk"], "LOW")

  def test_secret_never_returned(self):
    os.environ["PARTNER_API_KEY"] = "s3cr3t-value"
    body = func.main(make_event({"amount": 72000}))
    self.assertTrue(body.data["secret_loaded"])
    self.assertNotIn("s3cr3t-value", str(body.data))


if __name__ == "__main__":
  unittest.main()
