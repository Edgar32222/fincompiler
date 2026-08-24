from decimal import Decimal

from fincompiler.ingestion import read_tabular
from fincompiler.mapping import MappingMemory, apply_mapping
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

