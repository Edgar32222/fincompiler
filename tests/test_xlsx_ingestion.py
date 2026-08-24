import csv
import shutil

import pytest

from fincompiler.ingestion import discover_dataset_files, read_tabular
from fincompiler.pipeline import compile_pack


def test_xlsx_preserves_sheet_row_field_and_raw_value(tmp_path):
    openpyxl = __import__("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Invoice Lines"
    sheet.append(["InvoiceNumber", "LineAmount"])
    sheet.append(["INV-XLSX-1", 123.45])
    path = tmp_path / "sales.xlsx"
    workbook.save(path)
    rows = read_tabular(path)
    row, refs = rows[0]
    assert row["InvoiceNumber"] == "INV-XLSX-1"
    assert refs["LineAmount"].sheet == "Invoice Lines"
    assert refs["LineAmount"].row == 2
    assert refs["LineAmount"].raw_value == "123.45"


def test_pipeline_accepts_mixed_csv_and_xlsx_inputs(demo_dir, tmp_path):
    openpyxl = __import__("openpyxl")
    input_dir = tmp_path / "mixed"
    input_dir.mkdir()
    shutil.copy2(demo_dir / "gl.csv", input_dir / "GL.CSV")
    shutil.copy2(demo_dir / "budget.csv", input_dir / "budget.csv")
    with (demo_dir / "sales.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Sales detail"
    for row in rows:
        sheet.append(row)
    workbook.save(input_dir / "Sales.xlsx")

    discovered = discover_dataset_files(input_dir)
    assert discovered["sales"].name == "Sales.xlsx"
    report = compile_pack(input_dir, tmp_path / "out", tmp_path / "memory.json")
    assert report["reconciliation"]["variance"] == "2706.00"
    assert report["run_manifest"]["sources"][0]["file"].endswith("Sales.xlsx")


def test_discovery_rejects_ambiguous_sales_files(demo_dir, tmp_path):
    input_dir = tmp_path / "ambiguous"
    input_dir.mkdir()
    for dataset in ("sales", "gl", "budget"):
        shutil.copy2(demo_dir / f"{dataset}.csv", input_dir / f"{dataset}.csv")
    (input_dir / "sales.xlsx").write_bytes(b"placeholder")
    with pytest.raises(ValueError, match="Multiple Sales files"):
        discover_dataset_files(input_dir)
