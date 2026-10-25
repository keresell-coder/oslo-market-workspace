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
Object.assign(ctx, {
 metricValue:(v)=>v==null?'n/a':String(v), peerStatusClass:()=>'', renderPeerGroupEditor:()=>'',
 renderPeerReviewChecklist:()=>'', renderSectorContext:()=>'',
});
vm.runInContext(['renderMinimumData','renderBenchmarkGroup'].map(fn).join('\n') + '\n' + source.slice(source.indexOf('function renderBenchmark(data)'), source.indexOf('function renderPeerReviewChecklist()')),ctx);
test('saved MOWI legacy coverage is withheld both inside group and top-level benchmark',()=>{
 const saved=JSON.parse(fs.readFileSync('docs/data/benchmarks/MOWI.OL.json','utf8'));
 assert.ok(saved.minimumData.checks.some(c=>c.key==='peer_metric_coverage' && c.met));
 const original=JSON.stringify(saved);
 for(const html of [ctx.renderBenchmarkGroup(saved.groups[0]),ctx.renderBenchmark(saved)]) {
  assert.ok(!html.includes('6 metric(s) have focus value plus enough peer observations.'));
  assert.ok(html.includes('0 metric(s) have source-reviewed compatible basis and enough peer observations.'));
  assert.match(html, /class="missing">\s*<strong>Peer metric coverage<\/strong>/);
  assert.ok(html.includes('Valuation score enabled: no'));
 }
 assert.equal(JSON.stringify(saved),original,'guard must not mutate saved source evidence');
});
test('minimum-data guard keeps known compatible coverage and unrelated checks',()=>{
 const minimum={status:'minimum context available',valuationScoreEnabled:true,checks:[
  {key:'peer_metric_coverage',label:'Peer metric coverage',met:true,detail:'legacy count'},
  {key:'price_history',label:'Price-history observations',met:true,detail:'251 observed days'},
 ]};
 const metric={comparisonStatus:'compatible-reviewed-basis',minimumDataMet:true,focusValue:12,peerMedian:10,minimumPeerCount:3,peerCount:3};
 const html=ctx.renderMinimumData(minimum,[metric]);
 assert.match(html,/class="met">\s*<strong>Peer metric coverage<\/strong>/);
 assert.ok(html.includes('1 metric(s) have source-reviewed compatible basis'));
 assert.ok(html.includes('251 observed days'));
 assert.ok(html.includes('minimum context available'));
 for(const change of [{comparisonStatus:undefined},{minimumDataMet:false},{peerCount:2},{peerMedian:Infinity},{minimumPeerCount:undefined}]) {
  const guarded=ctx.renderMinimumData(minimum,[{...metric,...change}]);
  assert.match(guarded,/class="missing">\s*<strong>Peer metric coverage<\/strong>/);
  assert.ok(guarded.includes('not considered'));
 }
});
