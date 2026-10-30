// txn-screener, Node.js variant (runbook U3 step 7: second runtime check).
// Same behaviour and query parameters as screener.py.
const os = require('os');

let cold = true;
const boot = Date.now();

async function screen(payload = {}, params = {}) {
  const wasCold = cold;
  cold = false;
  if (params.fail === '1') return [500, { error: 'forced failure (test D2)' }];
  if (params.sleep_ms) await new Promise((r) => setTimeout(r, Number(params.sleep_ms)));
  const hog = params.alloc_mb ? Buffer.alloc(Number(params.alloc_mb) * 1024 * 1024, 1) : null;
  let egressIp = null;
  if (params.egress === '1') egressIp = await (await fetch('https://api.ipify.org')).text();
  const threshold = Number(process.env.RISK_THRESHOLD || 50000);
  const amount = Number(payload.amount || 0);
  if (Number.isNaN(amount)) throw new Error(`amount is not a number: ${payload.amount}`);
  return [200, {
    txn_id: payload.txn_id ?? null,
    risk: amount >= threshold ? 'HIGH' : 'LOW',
    amount,
    threshold,
    version: process.env.APP_VERSION || 'v1',
    secret_loaded: Boolean(process.env.PARTNER_API_KEY),
    cold_start: wasCold,
    instance: os.hostname(),
    uptime_s: (Date.now() - boot) / 1000,
    allocated_mb: hog ? hog.length / (1024 * 1024) : 0,
    egress_ip: egressIp,
  }];
}

module.exports = { screen };
