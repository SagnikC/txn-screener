from parliament import Context, event

from screener import screen


def _payload(context):
    """Transaction from the CloudEvent data, or from a plain JSON body when
    the caller sends no CloudEvent headers (curl, webhooks)."""
    if context.cloud_event is not None:
        data = context.cloud_event.data
        if isinstance(data, (bytes, bytearray)):
            import json
            data = json.loads(data or b"{}")
        return data or {}
    req = context.request
    if req is None:
        return {}
    return req.get_json(silent=True) or {}


@event(event_source="/vayu/functions/txn-screener", event_type="vayu.txn.screened")
def main(context: Context):
    """
    Function template (Knative func release-1.17, Python CloudEvents).
    The context parameter contains the Flask request object and any
    CloudEvent received with the request.

    Business logic: score the UPI transaction LOW or HIGH risk.
    The return value is applied as the data attribute of the CloudEvent
    returned to the invoker. Exceptions are returned as HTTP 500.
    """
    params = context.request.args.to_dict() if context.request is not None else {}
    result = screen(_payload(context), params)
    if context.cloud_event is not None:
        result["source_event_id"] = context.cloud_event["id"]
        result["source_event_type"] = context.cloud_event["type"]
    print(f"txn-screener {result.get('txn_id')} -> {result['risk']}", flush=True)
    return result
