"""Offline review preview; never writes published data or refetches provider inputs."""
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.primary_financials import load_primary
from app.server import normalize_fundamental_multiple_fields


def build_preview():
    data=json.loads((ROOT/'docs/data/fundamentals-watchlist.json').read_text())
    original=next(r for r in data['rows'] if r['symbol']=='NOD.OL')
    current=copy.deepcopy(original)
    current['primaryFinancials']=load_primary('NOD.OL',ROOT/'data/primary',download=False)
    current=normalize_fundamental_multiple_fields(current)
    return {'baseline_commit':'d295ac610882219815c5f6128e1cbb45075c4aff','baseline_snapshot':data['snapshotId'],
            'provider_values_unchanged':original['quarterlyStatements']==current['quarterlyStatements'],
            'before':{'statement_period':original['financialFilingCoverage']['latest_period_end'],
                      'enterpriseToEbitda':original['enterpriseToEbitda'],'priceToSalesTrailing12Months':original['priceToSalesTrailing12Months']},
            'after':{'provider_coverage':current['financialFilingCoverage'],'enterpriseToEbitda':current['enterpriseToEbitda'],
                     'priceToSalesTrailing12Months':current['priceToSalesTrailing12Months'],'primary':current['primaryFinancials']}}


if __name__=='__main__':
    print(json.dumps(build_preview(),indent=2))
