from fincompiler.ingestion import read_tabular


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

