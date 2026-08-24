from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator

from .models import SourceRef


def _csv_rows(path: Path) -> Iterator[tuple[str, int, dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row_no, row in enumerate(csv.DictReader(handle), start=2):
            yield "CSV", row_no, {str(k).strip(): (v or "").strip() for k, v in row.items()}


def _xlsx_rows(path: Path) -> Iterator[tuple[str, int, dict[str, str]]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("Excel input requires the optional 'excel' dependency") from exc
    workbook = load_workbook(path, read_only=True, data_only=True)
    for sheet in workbook.worksheets:
        rows = sheet.iter_rows(values_only=True)
        headers = [str(value).strip() if value is not None else "" for value in next(rows)]
        for row_no, values in enumerate(rows, start=2):
            yield sheet.title, row_no, {
                header: "" if value is None else str(value)
                for header, value in zip(headers, values)
                if header
            }


def read_tabular(path: str | Path) -> list[tuple[dict[str, str], dict[str, SourceRef]]]:
    source = Path(path)
    iterator = _csv_rows(source) if source.suffix.lower() == ".csv" else _xlsx_rows(source)
    output = []
    for sheet, row_no, row in iterator:
        refs = {
            field: SourceRef(str(source.resolve()), sheet, row_no, field, value)
            for field, value in row.items()
        }
        output.append((row, refs))
    return output

