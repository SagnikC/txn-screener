# txn-screener — Vayu Functions demo

Sample function for the **Vayu Functions Demo and Test Runbook**. It scores a UPI-style payment as `LOW` or `HIGH` risk against a threshold, the use case in runbook section 0 (a bank's UPI team screening every transaction).

The same code is deployed through all four Vayu Functions upload options, so results line up across them.

| Option | What to use from this repo |
| --- | --- |
| U1 GitHub (external) | Push this repo; point the function at branch `main`, folder `/` |
| U2 Vayu GitLab | Push this repo to `demo/txn-screener`; same settings |
| U3 Zip file | Run `make-zip.sh` and upload `txn-screener-u3-py.zip` |
| U4 Vayu Container Registry | `docker build` with the `Dockerfile`, push, deploy by digest |

## Files

| Path | Purpose |
| --- | --- |
| `screener.py` | The logic. Standard library only |
| `handler.py` | Function entry point for U1–U3 (`handle(body, query)`, plus an ASGI `new()` form) |
| `requirements.txt` | Function dependencies (empty for v1) |
| `app.py`, `Dockerfile`, `requirements-container.txt` | U4 container image (Flask + gunicorn on port 8080) |
| `events/` | Saved test events for runbook test D17 |
| `tests/` | Unit tests (`pytest`) |
| `node/` | Node.js variant for the second-runtime check (U3 step 7) |
| `make-zip.sh` | Builds the U3 zip with files at the archive root |

> The exact handler file name and signature Vayu Functions expects is open item 2 in the runbook. If the console's Python template generates a different handler, keep `screener.py` and call `screen()` from it.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `RISK_THRESHOLD` | `50000` | Amounts at or above this are `HIGH` |
| `APP_VERSION` | `v1` | Shown in responses; used for version and traffic-split tests |
| `PARTNER_API_KEY` | unset | Link to Vayu Vault secret `demo/partner-api-key` in test D6. Only `secret_loaded: true/false` is ever returned |

## Test behaviour (query parameters)

| Parameter | Effect | Runbook test |
| --- | --- | --- |
| `fail=1` | Returns HTTP 500 | D2 |
| `sleep_ms=N` | Waits N ms | D3, D5 |
| `alloc_mb=N` | Allocates N MB | D4 |
| `egress=1` | Returns the outbound IP | D12 |

## Run locally

```bash
pip install pytest && python -m pytest -q          # unit tests

pip install -r requirements-container.txt
python app.py                                       # http://localhost:8080
curl -s -X POST localhost:8080 -H 'Content-Type: application/json' -d @events/high-risk.json
```

## Push to GitHub (U1)

```bash
git init && git add . && git commit -m "txn-screener v1"
git branch -M main
git remote add origin https://github.com/<org>/txn-screener.git
git push -u origin main
```

Then in GitHub create a fine-grained token for this repository only, with **Contents: Read-only**, and paste it into the Vayu Functions console (runbook section 4.1).

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

`kafka-record` and `cron-tick` events are not included: copy their exact shapes from the D9 logs, because they depend on how Vayu Functions wraps those triggers.

Internal demo material; not for customer distribution as-is.
