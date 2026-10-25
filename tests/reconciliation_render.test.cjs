const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/static/app.js','utf8');
function fn(name) {
 const start=source.indexOf(`function ${name}(`);
 assert.ok(start>=0);
 return source.slice(start,source.indexOf('\n}\n',start)+2);
}
const ctx=vm.createContext({value:v=>v===null||v===undefined?'n/a':String(v)});
vm.runInContext(fn('escapeHtml')+'\n'+fn('renderFinancialReconciliation'),ctx);
const load=t=>JSON.parse(fs.readFileSync(`data/reconciliation/${t}_definition_component_mapping.json`,'utf8'));
const dof=ctx.renderFinancialReconciliation(load('DOFG'));
const publi=ctx.renderFinancialReconciliation(load('PUBLI'));
test('DOF full TTM/debt limitations and real sources are rendered alongside legacy quarter',()=>{
 for(const text of ['874','936','923','-13','347','142000000','160000000','rounded','EV remains unresolved','not confirmation of provider methodology','4c6b78e60ad994ce341bab18affaad2e8487df90b05e0f64f6233183684cd1d2']) assert.ok(dof.includes(text),text);
 assert.ok(dof.includes('not filled with an implied 189m'));
 assert.ok(!dof.includes('SHA-256 unknown'));
});
test('PUBLI uses its own schema and exposes translation/revenue/maturity caveats',()=>{
 for(const text of ['Public Property','IAS21','0.915048512','not confirmed provider','1089000000','15000000','1104000000','other income','483','825','51714','NOK4m/1m','no provider/primary hybrid ratios','No unmatched','6643e28a4a69e62250e2b9973a0ffc86bf5bcf620f3102bf7c2deb09875ada22']) {
  assert.ok(publi.includes(text),text);
 }
 assert.ok(!publi.includes('quarterly EBITDA'));
 assert.ok(!publi.includes('SHA-256 unknown'));
});
test('legacy schema still renders and unsupported schema stays explicit',()=>{
 const note=load('DOFG');delete note.additional_annual_debt_and_TTM_reconciliation;
 assert.ok(ctx.renderFinancialReconciliation(note).includes('332'));
 assert.ok(!ctx.renderFinancialReconciliation(note).includes('936'));
 assert.ok(ctx.renderFinancialReconciliation({issuer:'OTHER'}).includes('schema not supported'));
 assert.equal(ctx.renderFinancialReconciliation(null),'');
});
test('notes are escaped and source links require HTTPS',()=>{
 const note=load('PUBLI');note.disclosure_scope_conflicts=['<img onerror=alert(1)>'];note.sources.PUBLISEK.url='javascript:alert(1)';
 const text=ctx.renderFinancialReconciliation(note);
 assert.ok(text.includes('&lt;img'));
 assert.ok(!text.includes('<img'));
 assert.ok(!text.includes('href="javascript:'));
});
test('frontend copies are byte-identical',()=>assert.equal(source,fs.readFileSync('docs/app.js','utf8')));
const output='docs/review-evidence/debt-reconciliation/reconciliation-ui.html';
fs.writeFileSync(output,'<!doctype html><meta charset="utf-8"><title>Audit disclosure review</title><style>body{font:15px system-ui;margin:24px}td,th{border:1px solid #ccc;padding:8px}table{border-collapse:collapse}p{max-width:1100px}li{overflow-wrap:anywhere}</style><h1>Offline actual renderer — audit disclosures only; valuations unchanged</h1>'+dof.replace('<details class="compact-details">','<details class="compact-details" open>')+publi.replace('<details class="compact-details">','<details class="compact-details" open>'));
