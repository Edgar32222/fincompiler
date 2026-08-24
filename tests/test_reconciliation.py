from decimal import Decimal

from fincompiler.ingestion import read_tabular
from fincompiler.mapping import MappingMemory, apply_mapping
from fincompiler.models import CanonicalRecord
from fincompiler.reconciliation import investigate_sales_gl


def mapped(dataset, path, tmp_path):
    rows = read_tabular(path)
    proposals, _ = MappingMemory(tmp_path / "m.json").propose(dataset, list(rows[0][0]))
    return apply_mapping(dataset, rows, proposals)[0]


def test_finds_exact_2706_variance_and_record(demo_dir, tmp_path):
    result = investigate_sales_gl(mapped("sales", demo_dir / "sales.csv", tmp_path), mapped("gl", demo_dir / "gl.csv", tmp_path))
    assert result["variance"] == "2706.00"
    assert result["status"] == "NEEDS_REVIEW"
    assert result["causes"] == [{"reference": "INV-1003", "sales": "3600.00", "gl": "894.00", "difference": "2706.00", "reason": "AMOUNT_MISMATCH"}]
    assert result["sales_total"]["inputs"][0]["source"]["file"].endswith("sales.csv")


def sales_record(invoice_id: str, amount: str, when: str = "2026-07-15", **components) -> CanonicalRecord:
    return CanonicalRecord("sales", invoice_id, {"net_sales": amount, "currency": "AED", "date": when, **components}, {})


def gl_record(entry_id: str, amount: str, reference: str = "", when: str = "2026-07-15", **values) -> CanonicalRecord:
    return CanonicalRecord("gl", entry_id, {"amount": amount, "account": "4000", "currency": "AED", "date": when, "reference": reference, **values}, {})


def test_split_reference_and_credit_note_are_grouped_without_double_counting():
    sales = [sales_record("INV-1", "100.00"), sales_record("CN-1", "-20.00")]
    gl = [gl_record("JE-1A", "60.00", "INV-1"), gl_record("JE-1B", "40.00", "INV-1"), gl_record("JE-CN", "-20.00", "CN-1")]

    result = investigate_sales_gl(sales, gl, revenue_accounts=("4000",))

    assert result["status"] == "PASS"
    assert result["variance"] == "0.00"
    assert result["causes"] == []
    assert {group["method"] for group in result["match_groups"]} == {"SPLIT_REFERENCE", "EXACT_REFERENCE"}


def test_unique_amount_batch_matches_multiple_invoices_deterministically():
    sales = [sales_record("INV-1", "100.00"), sales_record("INV-2", "250.00"), sales_record("INV-3", "90.00")]
    gl = [gl_record("JE-BATCH", "350.00", batch_id="BATCH-7")]

    result = investigate_sales_gl(sales, gl, revenue_accounts=("4000",))

    assert result["status"] == "NEEDS_REVIEW"
    assert result["match_groups"] == [{
        "group_id": "batch:JE-BATCH",
        "method": "UNIQUE_AMOUNT_BATCH",
        "sales_references": ["INV-1", "INV-2"],
        "sales_record_ids": ["INV-1", "INV-2"],
        "gl_record_ids": ["JE-BATCH"],
        "sales": "350.00",
        "gl": "350.00",
        "residual": "0.00",
    }]
    assert result["causes"] == [{"reference": "INV-3", "sales": "90.00", "gl": "0", "difference": "90.00", "reason": "MISSING_GL_ENTRY"}]


def test_tax_component_and_cross_period_are_explicit_causes():
    tax = investigate_sales_gl(
        [sales_record("INV-TAX", "100.00", tax_amount="5.00")],
        [gl_record("JE-TAX", "105.00", "INV-TAX")],
        revenue_accounts=("4000",),
    )
    cutoff = investigate_sales_gl(
        [sales_record("INV-CUT", "100.00", when="2026-07-31")],
        [gl_record("JE-CUT", "100.00", "INV-CUT", when="2026-08-01")],
        revenue_accounts=("4000",),
    )

    assert tax["causes"][0]["reason"] == "TAX_INCLUDED_IN_GL"
    assert tax["causes"][0]["component_amount"] == "5.00"
    assert cutoff["variance"] == "0.00"
    assert cutoff["causes"][0]["reason"] == "CROSS_PERIOD_CUTOFF"
    assert cutoff["status"] == "NEEDS_REVIEW"


def test_ambiguous_amount_batch_is_never_silently_allocated():
    sales = [sales_record("INV-1", "100.00"), sales_record("INV-2", "100.00"), sales_record("INV-3", "100.00")]
    gl = [gl_record("JE-BATCH", "200.00")]

    result = investigate_sales_gl(sales, gl, revenue_accounts=("4000",))

    assert result["match_groups"] == []
    assert {cause["reason"] for cause in result["causes"]} == {"MISSING_GL_ENTRY", "UNMATCHED_GL_ENTRY"}
