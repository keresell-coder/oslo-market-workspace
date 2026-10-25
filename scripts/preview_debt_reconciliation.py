"""Read-only preview of new audit disclosures beside unchanged saved outputs."""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parents[1]
BASE='d7b0a34c8e475c31712c59ac609d95c3aa1c223c'
output={}
saved=json.loads((ROOT/'docs/data/fundamentals-watchlist.json').read_text())
for ticker in ['DOFG.OL','PUBLI.OL']:
    path=f'data/reconciliation/{ticker.split(".")[0]}_definition_component_mapping.json'
    old=subprocess.run(['git','show',f'{BASE}:{path}'],cwd=ROOT,capture_output=True,text=True)
    provider=next((row for row in saved['rows'] if row.get('symbol')==ticker),None)
    output[ticker]={'baseline':BASE,'scope':'Audit-only disclosure preview; provider financial values, historical observations and valuation gates are unchanged. No live recalculation.','saved_provider_fields':{key:provider.get(key) for key in ['symbol','enterpriseToEbitda','enterpriseToRevenue','evToEbit','currency','financialCurrency']} if provider else None,'before_reconciliation':json.loads(old.stdout) if old.returncode==0 else None,'after_reconciliation':json.loads((ROOT/path).read_text())}
out=ROOT/'docs/review-evidence/debt-reconciliation';out.mkdir(parents=True,exist_ok=True)
(out/'audit-before-after.json').write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n')
print('Wrote audit-only preview without changing generated data')
