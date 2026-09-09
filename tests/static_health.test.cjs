const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const code = fs.readFileSync('app/static/app.js', 'utf8');
function functionSource(name, async = false) {
  const start = code.indexOf(`${async ? 'async ' : ''}function ${name}(`);
  return code.slice(start, code.indexOf('\n}\n', start) + 2);
}
const now = Date.now();
function manifest() {
  return { snapshotId: 'good', health: { status: 'degraded', snapshot_id: 'good',
    generated_at: new Date(now - 10000).toISOString(), valid_until: new Date(now + 3600000).toISOString() } };
}
const context = vm.createContext({ Date, staticManifest: null });
vm.runInContext(functionSource('staticTrustIssue'), context);
test('a recent matching degraded report remains usable with its limitations', () => {
  assert.equal(context.staticTrustIssue(manifest()), null);
});
for (const [label, mutate] of [
  ['blocked', m => { m.health.status = 'blocked'; }],
  ['snapshot mismatch', m => { m.health.snapshot_id = 'failed-new-run'; }],
  ['future generation', m => { m.health.generated_at = new Date(now + 60000).toISOString(); }],
  ['stale generation', m => { m.health.generated_at = new Date(now - 2 * 86400000).toISOString(); }],
  ['new completed session due', m => { m.health.valid_until = new Date(now - 1000).toISOString(); }],
  ['unknown expiry', m => { delete m.health.valid_until; }],
]) {
  test(`${label} cannot show current signal status`, () => {
    const m = manifest(); mutate(m);
    assert.ok(context.staticTrustIssue(m));
  });
}
test('mixed endpoint JSON withholds labels and position sizing', async () => {
  const m = manifest();
  const ctx = vm.createContext({ Date, staticManifest: m,
    loadStaticManifest: async () => m,
    fetchStaticJson: async () => ({ snapshotId: 'old-data', rows: [{ signal: 'BUY', positionPct: 10, stopLossPct: 5 }] }) });
  vm.runInContext(functionSource('staticTrustIssue') + '\n' + functionSource('trustedStaticJson', true), ctx);
  const result = await ctx.trustedStaticJson('technical-indicators-watchlist.json');
  assert.equal(result.rows[0].signal, 'WITHHELD');
  assert.equal(result.rows[0].positionPct, null);
  assert.equal(result.rows[0].stopLossPct, null);
  assert.equal(result.coverage.coveredCount, 0);
});

test('withheld indicators cannot keep favorable color interpretation', () => {
  const ctx = vm.createContext({});
  vm.runInContext(functionSource('technicalIndicatorStatus'), ctx);
  assert.equal(ctx.technicalIndicatorStatus('rsi14', 20, { withheldReason: 'stale source' }), 'missing');
});
