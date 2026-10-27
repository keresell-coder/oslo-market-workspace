from copy import deepcopy
import importlib.util
from pathlib import Path
import pytest
from app import server

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('static_builder_coverage', ROOT / 'scripts/build_static_site_data.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
REQUIRED = {'VSAT','NOD.OL','PUBLI.OL','SCATC.OL','DOFG.OL','COSH.OL','NORBT.OL','MOWI.OL','CMBTO.OL','ODL.OL','KOG.OL','ORK.OL'}


def test_exact_coverage_and_us_identity(tmp_path):
    inputs = builder.load_inputs(ROOT / 'data')
    rows = inputs['watchlist']['items']
    assert len(rows) == 20
    assert REQUIRED <= {row['symbol'] for row in rows}
    assert server.normalize_symbol(' vsat ') == 'VSAT'
    assert server.normalize_symbol('NOD') == 'NOD.OL'
    us = next(row for row in rows if row['symbol'] == 'VSAT')
    assert (us['exchange'], us['price_currency']) == ('NASDAQ','USD')
    assert all((r['exchange'], r['price_currency']) == ('Euronext Oslo','NOK') for r in rows if r['symbol'].endswith('.OL'))
    app = builder.import_app_server(tmp_path / 'test.sqlite3')
    app.init_db()
    builder.install_inputs(app, inputs)
    payload = builder.watchlist_payload(app, inputs['watchlist']['watchlist'])
    assert REQUIRED <= {r['symbol'] for r in payload['items']}
    with app.connect() as con:
        assert con.execute("select exchange from tickers where symbol='VSAT'").fetchone()[0] == 'NASDAQ'
        assert con.execute("select count(*) from tickers where symbol='VSAT.OL'").fetchone()[0] == 0


def test_us_cannot_be_assigned_nok_or_oslo():
    for field,value in [('price_currency','NOK'),('exchange','Euronext Oslo')]:
        raw = {'watchlist':'test','items':[{'symbol':'VSAT',field:value}]}
        with pytest.raises(builder.SchemaError):
            builder.validate_watchlist(raw)


def test_oslo_news_source_explicitly_unsupported_for_us(monkeypatch):
    class NoNetwork:
        def post(self,*a,**k):
            raise AssertionError('US ticker must not query NewsWeb')
    monkeypatch.setattr(server,'requests',NoNetwork())
    assert server.newsweb_fetch_status('VSAT')['status'] == 'unsupported'
    rows,error = server.fetch_newsweb_symbol_events('VSAT',refresh=True)
    assert rows == [] and 'NASDAQ:VSAT' in error


def test_us_missing_quote_currency_is_never_nok(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(server,'ttm_statement_value',lambda *a: (None,None,None))
    monkeypatch.setattr(server,'yfinance_fx_rate',lambda source,target: {'rate':None})
    result=server.enterprise_to_ebitda_summary(SimpleNamespace(ticker='VSAT'),{},'2026-10-26')
    assert result['value'] is None
    assert 'NOK' not in str(result)


@pytest.mark.parametrize('ticker,currency,exchange',[('VSAT','USD','NASDAQ'),('NOD','NOK','Oslo Bors')])
def test_fundamental_success_and_retained_failure_keep_identity(tmp_path,monkeypatch,ticker,currency,exchange):
    app=builder.import_app_server(tmp_path/'cache.sqlite3')
    app.init_db()
    expected='VSAT' if ticker=='VSAT' else 'NOD.OL'
    calls=[]
    def good(symbol):
        calls.append(symbol)
        return dict(symbol=symbol,currency=currency,price=42.,fetchedAt='2026-10-26T21:00:00Z')
    monkeypatch.setattr(app,'fetch_yfinance',good)
    monkeypatch.setattr(app,'enrich_fundamental_payload',lambda p:p)
    success=app.cached_fundamental(ticker,refresh=True)
    assert success['symbol']==expected and success['currency']==currency
    def failed(symbol):
        calls.append(symbol)
        raise RuntimeError('provider offline')
    monkeypatch.setattr(app,'fetch_yfinance',failed)
    retained=app.cached_fundamental(ticker,refresh=True)
    assert retained['symbol']==expected and retained['currency']==currency
    assert retained['cacheStatus']=='stale-after-error'
    assert calls==[expected,expected]
    with app.connect() as con:
        assert con.execute('select exchange from tickers where symbol=?',(expected,)).fetchone()[0]==exchange
    with pytest.raises(RuntimeError): app.cached_fundamental('VSAT' if ticker=='NOD' else 'NOD',refresh=True)


def test_us_observation_label_cannot_claim_session_validation(monkeypatch):
    monkeypatch.setattr(server,'normalize_enterprise_to_ebitda_fields',lambda p:p)
    monkeypatch.setattr(server,'normalize_fundamental_multiple_fields',lambda p:p)
    monkeypatch.setattr(server,'record_consensus_source',lambda p:None)
    monkeypatch.setattr(server,'consensus_for_symbol',lambda s:{'sourceCount':0,'confidence':'unverified'})
    monkeypatch.setattr(server,'consensus_target_summary',lambda p,c:{'targetUpsidePct':None,'status':'withheld','method':'unverified'})
    monkeypatch.setattr(server,'historical_pricing_context',lambda s,p:{})
    row={'symbol':'VSAT','currency':'USD','priceObservedAt':'2026-10-26T20:00:01Z','multipleSourceMetadata':{'targetUpsidePct':{}}}
    assert server.enrich_fundamental_payload(row)['priceObservationStatus']=='provider-observed USD quote date; Nasdaq session not validated'
