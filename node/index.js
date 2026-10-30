// Entry point for the Node.js variant. Exports handle(context, body) and a
// plain HTTP server fallback (node index.js) for local testing on port 8080.
const http = require('http');
const { screen } = require('./screener');

async function handle(context = {}, body = {}) {
  const query = context.query || {};
  try {
    const [statusCode, result] = await screen(body || {}, query);
    return { statusCode, headers: { 'content-type': 'application/json' }, body: result };
  } catch (err) {
    console.error('ERROR txn-screener:', err.message);
    return { statusCode: 500, headers: { 'content-type': 'application/json' }, body: { error: err.message } };
  }
}

module.exports = { handle };

if (require.main === module) {
  http.createServer((req, res) => {
    let raw = '';
    req.on('data', (c) => { raw += c; });
    req.on('end', async () => {
      const url = new URL(req.url, 'http://localhost');
      let body = {};
      try { body = raw ? JSON.parse(raw) : {}; } catch { body = {}; }
      const out = await handle({ query: Object.fromEntries(url.searchParams) }, body);
      res.writeHead(out.statusCode, out.headers);
      res.end(JSON.stringify(out.body));
    });
  }).listen(Number(process.env.PORT || 8080));
}
