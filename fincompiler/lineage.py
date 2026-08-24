from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal

from .models import Calculation, CanonicalRecord


def aggregate(records: list[CanonicalRecord], field: str, name: str) -> Calculation:
    total = Decimal("0")
    inputs = []
    for record in records:
        if field not in record.values:
            continue
        value = Decimal(str(record.values[field]).replace(",", "") or "0")
        total += value
        item = {"record_id": record.record_id, "value": str(value)}
        if field in record.lineage:
            item["source"] = asdict(record.lineage[field])
        elif field in record.derivations:
            item["derivation"] = {"formula": record.derivations[field]["formula"], "sources": [asdict(source) for source in record.derivations[field]["sources"]]}
        inputs.append(item)
    return Calculation(name, total.quantize(Decimal("0.01")), f"SUM({field})", inputs)


def trace_calculation(calculation: Calculation) -> dict:
    return calculation.jsonable()
