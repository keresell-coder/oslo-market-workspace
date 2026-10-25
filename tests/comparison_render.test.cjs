const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('app/static/app.js','utf8');
function fn(name){const start=source.indexOf(`function ${name}(`);assert.ok(start>=0);return source.slice(start,source.indexOf('\n}\n',start)+2);}
class FixedDate extends Date { constructor(...args) { super(...(args.length ? args : ['2026-10-25T16:00:00Z'])); } }
const ctx=vm.createContext({Date:FixedDate,value:v=>v==null?'n/a':String(v), shortDate:v=>v?String(v).slice(0,10):'n/a',signedPctValue:v=>v==null?'n/a':`${v}%`});
vm.runInContext(['escapeHtml','renderPriceCell','consensusFreshness','targetUpsideClass','targetComparisonUsable','renderConsensusTargetCell'].map(fn).join('\n'),ctx);
test('quote date is not collection date and unknown stays unknown',()=>{
 let html=ctx.renderPriceCell({price:100,currency:'NOK',priceObservedAt:'2026-10-23T14:00Z',fetchedAt:'2026-10-25'});
 assert.ok(html.includes('Quote 2026-10-23'));assert.ok(!html.includes('2026-10-25'));
 html=ctx.renderPriceCell({price:100,fetchedAt:'2026-10-25'});assert.ok(html.includes('date unknown'));assert.ok(!html.includes('2026-10-25'));
});
test('legacy fresh collection cannot claim fresh estimates',()=>{
 assert.equal(ctx.consensusFreshness([{staleStatus:'fresh',collected_at:'2026-10-25'}]),'estimate date unknown');
});
test('legacy target summary cannot leak unsupported percentage',()=>{
 const html=ctx.renderConsensusTargetCell({symbol:'X',consensusTargetSummary:{target:150,targetUpsidePct:50,status:'single-provider-row'}});
 assert.ok(!html.includes('50%'));assert.ok(!html.includes('<strong>150</strong>'));
});
test('compatible source target remains visible',()=>{
 const html=ctx.renderConsensusTargetCell({symbol:'X',consensusTargetSummary:{target:150,targetUpsidePct:50,status:'source-reviewed-comparable-targets',estimateAsOf:'2026-10-20',validUntil:'2026-11-01',horizonDate:'2027-10-20'}});
 assert.ok(html.includes('50%'));assert.ok(html.includes('<strong>150</strong>'));
});
test('empty source list has no affirmative validity claim',()=>assert.equal(ctx.consensusFreshness([]),'no source rows; estimate validity unknown'));
test('missing quote currency is explicit',()=>assert.ok(ctx.renderPriceCell({price:100}).includes('currency unknown')));
vm.runInContext(fn('renderFundamentalConsensus'),ctx);
test('fundamental target uses gated value, raw target kept explicitly separate',()=>{
 const html=ctx.renderFundamentalConsensus({targetMeanPrice:150,targetUpsidePct:50});
 assert.ok(html.includes('Comparable source target</span><b>n/a</b>'));
 assert.ok(html.includes('Raw provider target (unqualified)</span><b>150</b>'));
 assert.ok(!html.includes('50%'));
});
test('a saved eligible target expires without needing a new collection',()=>{
 assert.equal(ctx.targetComparisonUsable({status:'source-reviewed-comparable-targets',estimateAsOf:'2020-01-01',validUntil:'2020-02-01',horizonDate:'2021-01-01'}),false);
});
test('cached contradictory intervals and nonfinite target gaps are withheld',()=>{
 const base={status:'source-reviewed-comparable-targets',estimateAsOf:'2026-10-20',validUntil:'2026-11-01',horizonDate:'2027-10-20',target:150,targetUpsidePct:50};
 for (const change of [{targetLow:160},{targetHigh:140},{targetLow:170,targetHigh:130},{targetUpsidePct:Infinity},{target:Infinity},{targetLow:NaN}]) {
  assert.equal(ctx.targetComparisonUsable({...base,...change}),false);
  assert.ok(!ctx.renderConsensusTargetCell({symbol:'X',consensusTargetSummary:{...base,...change}}).includes('50%'));
 }
 assert.equal(ctx.targetComparisonUsable(base),true);
});
