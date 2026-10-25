from copy import deepcopy
from datetime import datetime, timezone
import pytest
from app import server
from app.comparison_contracts import target_comparison, estimate_status
NOW = datetime(2026, 10, 25, tzinfo=timezone.utc)
PRICE = dict(price=100, currency='NOK', priceObservedAt='2026-10-23T14:30:00Z')
ROW = dict(source='fixture', target_mean=150, target_low=130, target_high=170, target_currency='NOK', as_of_date='2026-10-20', target_horizon_date='2027-10-20', valid_until='2026-11-01', review_status='reviewed', source_url='https://example.com/report')

def test_compatible_target():
    result = target_comparison(PRICE, [ROW], NOW)
    assert result['targetUpsidePct'] == 50
    assert result['eligibleRows'] == 1

@pytest.mark.parametrize('field,value', [('target_currency', 'USD'), ('target_currency', ''), ('as_of_date',''), ('as_of_date','2020-01-01'), ('as_of_date','2026-10-26'), ('as_of_date','oops'), ('target_horizon_date',''), ('target_horizon_date','2020-01-01'), ('valid_until','2026-10-24'), ('valid_until',''), ('review_status','provider-row'), ('source_url',''), ('target_mean',float('nan')), ('target_mean',0)])
def test_missing_stale_and_incompatible_target(field,value):
    row = {**ROW, field:value}
    # Older vintage with an explicit current validity requires a fresh source
    # review; do not infer that review just from a long expiry window.
    if field == 'as_of_date' and value == '2020-01-01':
        row['valid_until'] = '2020-02-01'
    assert target_comparison(PRICE,[row],NOW)['targetUpsidePct'] is None

@pytest.mark.parametrize('field,value',[('price',0),('price',-1),('price',float('inf')),('priceObservedAt',None),('priceObservedAt','2026-10-26'),('priceObservedAt','2020-01-01')])
def test_price_contract(field,value):
    assert target_comparison({**PRICE,field:value},[ROW],NOW)['targetUpsidePct'] is None

def test_no_mixed_horizon_or_vintage_aggregation():
    for extra in ({'target_horizon_date':'2027-11-20'}, {'as_of_date':'2026-10-21'}):
        assert target_comparison(PRICE,[ROW,{**ROW,**extra}],NOW)['target'] is None

def test_collection_never_becomes_estimate_date():
    assert estimate_status({'collected_at':'2026-10-25'}, NOW) == 'estimate-date-unknown'
    assert server.consensus_target_summary(PRICE,{'targetMeanAcrossSources':150, 'sources':[]})['target'] is None

METRIC = {'key':'trailingPE','label':'P/E','unit':'x','positiveOnly':True,'positionNote':'context'}
def peer(value=10, **basis_changes):
    basis = dict(periodEnd='2026-06-30',periodBasis='TTM',accountingScope='consolidated-reported',economicGroup='reviewed-salmon',sourceUrl='https://example.com/report',reviewStatus='reviewed')
    basis.update(basis_changes)
    return {'trailingPE':value,'multipleSourceMetadata':{'trailingPE':{'comparisonBasis':basis}}}

def test_comparable_peers_do_not_need_matching_currency():
    focus, a, b = peer(12),peer(10),peer(14)
    focus['currency']='NOK';a['currency']='USD';b['currency']='EUR'
    result=server.metric_summary(focus,[a,b,peer(12)],METRIC)
    assert result['peerMedian']==12
    assert result['minimumDataMet']

@pytest.mark.parametrize('changes',[{'periodEnd':'2020-06-30'},{'periodBasis':'forward'},{'accountingScope':'adjusted'},{'economicGroup':'shipping'},{'sourceUrl':''},{'reviewStatus':'draft'}])
def test_peer_incompatible_basis(changes):
    result=server.metric_summary(peer(),[peer(11,**changes),peer(12,**changes)],METRIC)
    assert result['peerMedian'] is None
    assert result['vsPeerMedianPct'] is None
    assert result['percentileInGroup'] is None
    assert not result['minimumDataMet']

def test_unannotated_provider_peers_withheld():
    result=server.metric_summary({'trailingPE':12},[{'trailingPE':10},{'trailingPE':14}],METRIC)
    assert not result['minimumDataMet']

def test_saved_real_undated_rows_cannot_become_fresh():
    import json
    from pathlib import Path
    rows=json.loads((Path(__file__).parents[1]/'docs/data/consensus.json').read_text())['sources']
    undated=[row for row in rows if not row.get('as_of_date')]
    assert len(undated)==66
    assert all(estimate_status(row,NOW)=='estimate-date-unknown' for row in undated)
    assert target_comparison(PRICE,undated,NOW)['target'] is None

@pytest.mark.parametrize('value',[float('nan'),float('inf'),-float('inf'),True])
def test_invalid_peer_number(value):
    result=server.metric_summary(peer(),[peer(value),peer(value),peer(value)],METRIC)
    assert result['peerMedian'] is None
    assert not result['minimumDataMet']

def test_manual_schema_preserves_explicit_target_dates():
    from scripts.build_static_site_data import validate_manual_consensus
    result=validate_manual_consensus({'rows':[{**ROW,'symbol':'TEST.OL'}]})[0]
    assert result['target_horizon_date']==ROW['target_horizon_date']
    assert result['valid_until']==ROW['valid_until']

@pytest.mark.parametrize('bounds',[{'target_low':160}, {'target_high':140}, {'target_low':170,'target_high':130}, {'target_low':float('nan')}, {'target_high':float('inf')}, {'target_low':-1}])
def test_target_interval_contradictions_or_invalid_bounds(bounds):
    result=target_comparison(PRICE,[{**ROW,**bounds}],NOW)
    assert result['targetUpsidePct'] is None
    assert result['eligibleRows']==0
    assert result['excludedRows'][0]['reason'] in {'contradictory-target-interval','invalid-target-interval'}

def test_missing_optional_bounds_allowed():
    result=target_comparison(PRICE,[{**ROW,'target_low':None,'target_high':None}],NOW)
    assert result['targetUpsidePct']==50
    assert result['targetLow'] is None and result['targetHigh'] is None

def test_finite_inputs_cannot_produce_infinite_target_gap():
    result=target_comparison({**PRICE,'price':1e-308},[{**ROW,'target_mean':1e308,'target_low':None,'target_high':None}],NOW)
    assert result['target'] is None and result['targetUpsidePct'] is None
    assert result['excludedRows'][0]['reason']=='nonfinite-target-price-gap'

def test_large_finite_target_median_does_not_overflow():
    row={**ROW,'target_mean':1e308,'target_low':None,'target_high':None}
    result=target_comparison({**PRICE,'price':1e308},[row,row],NOW)
    assert result['target']==1e308 and result['targetUpsidePct']==0
