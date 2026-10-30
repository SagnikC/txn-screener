# txn-screener — Vayu Functions demo

Sample function for the **Vayu Functions Demo and Test Runbook**. It scores a UPI-style payment as `LOW` or `HIGH` risk against a threshold (runbook section 0: a bank's UPI team screening every transaction).

The function follows the [Knative func release-1.17 Python CloudEvents template](https://github.com/knative/func/tree/release-1.17/templates/python/cloudevents): `func.py` at the root with a `main(context)` function decorated with `@event`, served by `parliament`.

## Layout

```text
txn-screener/
├── func.py            # main(context): the function (template entry point)
├── screener.py        # business logic, no HTTP code
├── test_func.py       # unit tests (unittest, template style)
├── requirements.txt   # parliament-functions, cloudevents>=1.6.0,<2.0
├── constraints.txt    # cloudevents<2
├── func.yaml          # function config: name, runtime, invoke=cloudevent
├── Procfile           # pack builder:  web: python -m parliament .
├── app.sh             # s2i builder start script
├── manifest.yaml      # template manifest (invoke: cloudevent)
├── events/            # saved test events (runbook D17)
├── container/         # U4 only: Dockerfile running the same func.py
└── node/              # Node.js variant (second-runtime check, optional)
```

## Deploy settings (Vayu Functions console)

| Field | Value |
| --- | --- |
| Branch | `main` |
| Source directory | `/` (repo root) |
| Runtime | Python |
| Function name | `txn-screener-u1-py` (GitHub), `-u2-py` (Vayu GitLab), `-u3-py` (zip), `-u4-py` (registry) |
| Min / max replicas | `0` / `5` |

## How it handles requests

| Caller sends | Example | Function reads the transaction from |
| --- | --- | --- |
| Binary CloudEvent (`ce-*` headers) | Kafka source, broker trigger | CloudEvent `data` |
| Structured CloudEvent (`application/cloudevents+json`) | `events/cloudevent-txn.json` | CloudEvent `data` |
| Plain JSON, no CloudEvent headers | curl, GitLab webhook | Request body |

The response is a CloudEvent with `ce-type: vayu.txn.screened` and `ce-source: /vayu/functions/txn-screener`; its data is the result JSON. Any exception returns HTTP 500 (`parliament` behaviour).

## Configuration (environment variables)

| Variable | Default | Purpose |
| --- | --- | --- |
| `RISK_THRESHOLD` | `50000` | Amounts at or above this are `HIGH` |
| `APP_VERSION` | `v1` | Shown in responses; used for version and traffic-split tests |
| `PARTNER_API_KEY` | unset | Link to Vayu Vault secret `demo/partner-api-key` (test D6). Only `secret_loaded: true/false` is returned |

## Test behaviour (query parameters)

| Parameter | Effect | Runbook test |
| --- | --- | --- |
| `fail=1` | HTTP 500 | D2 |
| `sleep_ms=N` | Waits N ms | D3, D5 |
| `alloc_mb=N` | Allocates N MB | D4 |
| `egress=1` | Returns the outbound IP | D12 |

Health probes: `/health/liveness`, `/health/readiness`.

## Run locally

```bash
pip install -r requirements.txt -c constraints.txt
python test_func.py               # 7 tests
python -m parliament .            # serves on http://localhost:8080
```

## Upload option U3: zip

```bash
zip txn-screener-u3-py.zip func.py screener.py requirements.txt constraints.txt func.yaml Procfile app.sh manifest.yaml
unzip -l txn-screener-u3-py.zip     # files must sit at the archive root
```

## Upload option U4: container image

```bash
docker build -f container/Dockerfile -t <registry host>/demo/txn-screener:1.0.0 .
docker push <registry host>/demo/txn-screener:1.0.0
```

## Fire the test events (D17 fallback)

```bash
export FN_URL="<endpoint from the function page>"

# Plain JSON
for e in high-risk low-risk boundary malformed empty; do
  printf '%-10s ' "$e"
  curl -s -o /dev/null -w 'HTTP %{http_code}  %{time_total}s\n' \
    -X POST "$FN_URL" -H 'Content-Type: application/json' -d @events/$e.json
done

# Binary CloudEvent (as a Kafka source would send it)
curl -s -i -X POST "$FN_URL" -H 'Content-Type: application/json' \
  -H 'ce-specversion: 1.0' -H 'ce-type: vayu.txn.created' \
  -H 'ce-source: /upi/switch' -H 'ce-id: evt-001' -d @events/high-risk.json

# Structured CloudEvent
curl -s -X POST "$FN_URL" -H 'Content-Type: application/cloudevents+json' \
  -d @events/cloudevent-txn.json
```

| Event | Expected |
| --- | --- |
| `high-risk` | 200, `HIGH` |
| `low-risk` | 200, `LOW` |
| `boundary` | 200, `HIGH` (threshold is inclusive) |
| `malformed` | 500, error in logs |
| `empty` | 200, `LOW`, `txn_id` null |
| `cloudevent-txn` | 200, `HIGH`, `source_event_id` evt-0001 |
| `gitlab-push` | 200 (send with header `X-Gitlab-Event: Push Hook`) |

Internal demo material; not for customer distribution as-is.
