# txn-screener — Vayu Functions demo

Sample function for the **Vayu Functions Demo and Test Runbook**. It scores a UPI-style payment as `LOW` or `HIGH` risk against a threshold (runbook section 0: a bank's UPI team screening every transaction).

The function follows the [Knative Functions Python HTTP template](https://github.com/knative/func/blob/main/docs/function-templates/python.md): a `function/` package exporting `new()`, which returns a `Function` with an async `handle(scope, receive, send)`.

## Layout

```text
txn-screener/
├── func.yaml            # function config (name, runtime)
├── pyproject.toml       # package "function" + dependencies
├── function/
│   ├── __init__.py      # exports new()
│   ├── func.py          # Function class: handle, start, stop, alive, ready
│   └── screener.py      # business logic, no HTTP code
├── tests/test_func.py   # pytest, template style
├── events/              # saved test events (runbook D17)
├── container/           # U4 only: Flask app + Dockerfile
└── node/                # Node.js variant (second-runtime check)
```

## Deploy settings (Vayu Functions console)

| Field | Value |
| --- | --- |
| Branch | `main` |
| Source directory | `/` (repo root) |
| Runtime | Python 3.11 (or nearest) |
| Function name | `txn-screener-u1-py` (GitHub), `-u2-py` (Vayu GitLab), `-u3-py` (zip), `-u4-py` (registry) |
| Min / max replicas | `0` / `5` |

If the console rejects `func.yaml` (for example a spec-version error), delete it and redeploy; the platform generates its own.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `RISK_THRESHOLD` | `50000` | Amounts at or above this are `HIGH` |
| `APP_VERSION` | `v1` | Shown in responses; used for version and traffic-split tests |
| `PARTNER_API_KEY` | unset | Link to Vayu Vault secret `demo/partner-api-key` (test D6). Only `secret_loaded: true/false` is returned |

Variables are read from the `cfg` dict passed to `start()`, as the template recommends.

## Test behaviour (query parameters)

| Parameter | Effect | Runbook test |
| --- | --- | --- |
| `fail=1` | HTTP 500 | D2 |
| `sleep_ms=N` | Non-blocking wait of N ms | D3, D5 |
| `alloc_mb=N` | Allocates N MB | D4 |
| `egress=1` | Returns the outbound IP | D12 |

Health probes: `/health/liveness`, `/health/readiness`.

## Run locally

```bash
pip install -e .            # installs the package and test dependencies
python -m pytest -q         # 12 tests

# With the Knative func CLI, if installed:
func run --builder=host
curl -s -X POST localhost:8080 -H 'Content-Type: application/json' -d @events/high-risk.json
```

## Upload option U3: zip

```bash
zip -r txn-screener-u3-py.zip func.yaml pyproject.toml README.md function
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
for e in high-risk low-risk boundary malformed empty; do
  printf '%-10s ' "$e"
  curl -s -o /dev/null -w 'HTTP %{http_code}  %{time_total}s\n' \
    -X POST "$FN_URL" -H 'Content-Type: application/json' -d @events/$e.json
done
```

| Event | Expected |
| --- | --- |
| `high-risk` | 200, `HIGH` |
| `low-risk` | 200, `LOW` |
| `boundary` | 200, `HIGH` (threshold is inclusive) |
| `malformed` | 500, error in logs |
| `empty` | 200, `LOW`, `txn_id` null |
| `gitlab-push` | 200 (send with header `X-Gitlab-Event: Push Hook`) |

`kafka-record` and `cron-tick` are not included: copy their shapes from the D9 logs.

Internal demo material; not for customer distribution as-is.
