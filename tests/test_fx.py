import json
from datetime import date
from decimal import Decimal

from fincompiler.fx import RateBook, RatePolicy, parse_ecb_history
from fincompiler.pipeline import compile_pack
from fincompiler.scenario import generate_scenario


def _rate_book(path):
    path.write_text(
        "effective_date,base_currency,quote_currency,rate,rate_type,provider,source_url,fetched_at,raw_sha256\n"
        "2026-07-14,EUR,USD,1.200000,transaction,Treasury,approved://treasury,2026-07-15T08:00:00Z,\n"
        "2026-07-14,EUR,AED,4.400000,transaction,Treasury,approved://treasury,2026-07-15T08:00:00Z,\n",
        encoding="utf-8",
    )


def test_rate_book_supports_inverse_cross_and_dated_fallback(tmp_path):
    path = tmp_path / "rates.csv"
    _rate_book(path)
    match = RateBook.load(path).find("USD", "AED", date(2026, 7, 15), RatePolicy(max_lookback_days=3))
    assert match.rate == Decimal("3.666666666666666666666666667")
    assert match.effective_date == date(2026, 7, 14)
    assert len(match.observations) == 2
    assert "EUR" in match.formula


def test_pipeline_converts_foreign_sales_and_preserves_rate_evidence(tmp_path):
    scenario = tmp_path / "scenario"
    generate_scenario(scenario, seed=22, invoice_count=5)
    sales = scenario / "sales.csv"
    sales.write_text(sales.read_text(encoding="utf-8").replace(",AED,1.000000,", ",USD,0.2727272727,"), encoding="utf-8")
    sales_lines = len(sales.read_text(encoding="utf-8").splitlines()) - 1
    gl = scenario / "gl.csv"
    # Keep the accounting-currency amount in AED while the transaction currency is USD.
    gl.write_text(gl.read_text(encoding="utf-8").replace(",AED,", ",USD,"), encoding="utf-8")
    rate_book = scenario / "fx_rates.csv"
    rate_book.write_text(
        "effective_date,base_currency,quote_currency,rate,rate_type,provider,source_url,fetched_at,raw_sha256\n"
        "2026-07-15,USD,AED,3.670000,transaction,Treasury,approved://treasury,2026-07-15T08:00:00Z,\n",
        encoding="utf-8",
    )
    config = json.loads((scenario / "company_config.json").read_text(encoding="utf-8"))
    config.update({"fx_rate_book": "fx_rates.csv", "fx_policy": {"rate_type": "transaction", "max_lookback_days": 3}})
    (scenario / "company_config.json").write_text(json.dumps(config), encoding="utf-8")
    report = compile_pack(scenario, tmp_path / "output", tmp_path / "memory.json")
    assert report["fx"]["converted_records"] == sales_lines + 5
    assert report["fx"]["missing_records"] == 0
    assert report["fx"]["applications"][0]["rate"] == "3.670000"
    assert report["fx"]["applications"][0]["observations"][0]["provider"] == "Treasury"
    assert any(item["dataset"] == "fx_rate_book" for item in report["run_manifest"]["sources"])
    assert report["close_workflow"]["tasks"][1]["status"] == "COMPLETE"


def test_missing_rate_is_an_actionable_blocker(tmp_path):
    scenario = tmp_path / "scenario"
    generate_scenario(scenario, seed=23, invoice_count=5)
    sales = scenario / "sales.csv"
    sales.write_text(sales.read_text(encoding="utf-8").replace(",AED,", ",USD,"), encoding="utf-8")
    sales_lines = len(sales.read_text(encoding="utf-8").splitlines()) - 1
    report = compile_pack(scenario, tmp_path / "output", tmp_path / "memory.json")
    fx_items = [item for item in report["exceptions"] if item["code"] == "FX_RATE_REQUIRED"]
    assert len(fx_items) == sales_lines
    assert "no approved local rate book" in fx_items[0]["context"]["reason"]
    assert report["close_workflow"]["tasks"][1]["next_action"] == "Add or approve the missing dated rates."


def test_ecb_parser_retains_full_precision_and_raw_hash():
    xml = b'''<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref"><Cube><Cube time="2026-07-15"><Cube currency="USD" rate="1.123456"/><Cube currency="JPY" rate="170.25"/></Cube></Cube></gesmes:Envelope>'''
    observations = parse_ecb_history(xml, "2026-07-15T16:00:00Z")
    assert observations[0].rate == Decimal("1.123456")
    assert observations[0].provider == "ECB"
    assert len(observations[0].raw_sha256) == 64


def test_claimed_rate_hash_must_be_real_sha256(tmp_path):
    path = tmp_path / "rates.csv"
    path.write_text("effective_date,base_currency,quote_currency,rate,rate_type,provider,source_url,fetched_at,raw_sha256\n2026-07-15,USD,AED,3.67,transaction,Treasury,approved://treasury,2026-07-15T08:00:00Z,not-a-hash\n", encoding="utf-8")
    try:
        RateBook.load(path)
    except ValueError as exc:
        assert "raw_sha256" in str(exc)
    else:
        raise AssertionError("invalid claimed rate hash was accepted")
