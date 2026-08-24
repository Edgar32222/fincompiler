from decimal import Decimal

from fincompiler.ingestion import read_tabular
from fincompiler.mapping import MappingMemory, apply_mapping
from fincompiler.normalization import normalize_records
from fincompiler.pipeline import compile_pack
from fincompiler.profiles import detect_profile


def test_detects_xero_and_dynamics_profiles():
    assert detect_profile("sales", ["InvoiceNumber", "LineAmount", "CurrencyCode", "ItemCode"]).name == "xero_invoice_lines"
    assert detect_profile("gl", ["VOUCHER", "TRANSDATE", "ACCOUNTDISPLAYVALUE", "CURRENCYCODE"]).name == "dynamics_general_journal"
    assert detect_profile("sales", ["InvoiceNumber"]) is None


def test_dynamics_debit_credit_derivation_keeps_formula_and_sources(tmp_path):
    path = tmp_path / "gl.csv"
    path.write_text("VOUCHER,TRANSDATE,ACCOUNTDISPLAYVALUE,CURRENCYCODE,DEBITAMOUNT,CREDITAMOUNT\nJE-1,2026-07-01,Revenue,AED,0,125.50\n", encoding="utf-8")
    rows = read_tabular(path)
    profile = detect_profile("gl", list(rows[0][0]))
    proposals, _ = MappingMemory(tmp_path / "memory.json").propose("gl", list(rows[0][0]), profile.aliases, profile.name)
    records, _ = apply_mapping("gl", rows, proposals)
    records, exceptions = normalize_records(records)
    assert not exceptions
    assert records[0].values["amount"] == Decimal("125.50")
    assert records[0].derivations["amount"]["formula"] == "credit_amount - debit_amount"
    assert {source.field for source in records[0].derivations["amount"]["sources"]} == {"DEBITAMOUNT", "CREDITAMOUNT"}


def test_realistic_multisystem_pack_aggregates_invoice_lines(tmp_path):
    demo = __import__("pathlib").Path(__file__).parents[1] / "demo" / "realistic_multisystem"
    report = compile_pack(demo, tmp_path / "out", tmp_path / "memory.json")
    assert report["source_profiles"] == {"sales": "xero_invoice_lines", "gl": "dynamics_general_journal", "budget": "generic"}
    assert report["reconciliation"]["variance"] == "2706.00"
    assert report["reconciliation"]["causes"][0]["reference"] == "INV-X1003"
    gl_lineage = report["reconciliation"]["gl_total"]["input_preview"][0]["derivation"]
    assert gl_lineage["formula"] == "credit_amount - debit_amount"
    assert report["pvm"]["totals"]["bridge_check"] == "0.00"


def test_ambiguous_numeric_date_is_blocked(tmp_path):
    path = tmp_path / "sales.csv"
    path.write_text("Invoice No,Date,Net Sales\nINV-1,01/02/2026,100\n", encoding="utf-8")
    rows = read_tabular(path)
    proposals, _ = MappingMemory(tmp_path / "memory.json").propose("sales", list(rows[0][0]))
    records, _ = apply_mapping("sales", rows, proposals)
    _, exceptions = normalize_records(records)
    assert exceptions[0].code == "TYPE_VALIDATION_FAILED"
