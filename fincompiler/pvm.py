from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from decimal import Decimal

from .models import CanonicalRecord, money


def _group(records: list[CanonicalRecord], revenue_field: str) -> dict[tuple[str, str], dict]:
    grouped = defaultdict(lambda: {"quantity": Decimal("0"), "revenue": Decimal("0"), "inputs": []})
    for record in records:
        key = (str(record.values.get("customer", "")), str(record.values.get("sku", "")))
        grouped[key]["quantity"] += money(record.values.get("quantity"))
        revenue = record.values.get(revenue_field)
        grouped[key]["revenue"] += money(revenue if revenue not in {None, ""} else money(record.values.get("quantity")) * money(record.values.get("unit_price")))
        grouped[key]["inputs"].append({
            "record_id": record.record_id,
            "quantity_source": asdict(record.lineage["quantity"]) if "quantity" in record.lineage else None,
            "revenue_source": asdict(record.lineage[revenue_field]) if revenue_field in record.lineage else None,
            "unit_price_source": asdict(record.lineage["unit_price"]) if "unit_price" in record.lineage else None,
        })
    return grouped


def investigate_pvm(actual: list[CanonicalRecord], budget: list[CanonicalRecord]) -> dict:
    a, b = _group(actual, "net_sales"), _group(budget, "revenue")
    rows = []
    totals = defaultdict(lambda: Decimal("0"))
    for customer, sku in sorted(set(a) | set(b)):
        av, bv = a[(customer, sku)], b[(customer, sku)]
        aq, bq, ar, br = av["quantity"], bv["quantity"], av["revenue"], bv["revenue"]
        ap = ar / aq if aq else Decimal("0")
        bp = br / bq if bq else Decimal("0")
        volume = (aq - bq) * bp
        price = aq * (ap - bp)
        variance = ar - br
        residual = variance - volume - price
        row = {"customer": customer, "sku": sku, "actual_revenue": ar, "budget_revenue": br, "variance": variance, "volume": volume, "price": price, "mix_residual": residual}
        rendered = {k: (str(v.quantize(Decimal('0.01'))) if isinstance(v, Decimal) else v) for k, v in row.items()}
        rendered["calculation_chain"] = {
            "actual_price": "actual_revenue / actual_quantity",
            "budget_price": "budget_revenue / budget_quantity",
            "volume": "(actual_quantity - budget_quantity) * budget_price",
            "price": "actual_quantity * (actual_price - budget_price)",
            "mix_residual": "variance - volume - price",
        }
        rendered["actual_inputs"] = av["inputs"]
        rendered["budget_inputs"] = bv["inputs"]
        rows.append(rendered)
        for key in ("actual_revenue", "budget_revenue", "variance", "volume", "price", "mix_residual"):
            totals[key] += row[key]
    result_totals = {k: str(v.quantize(Decimal("0.01"))) for k, v in totals.items()}
    result_totals["bridge_check"] = str((totals["volume"] + totals["price"] + totals["mix_residual"] - totals["variance"]).quantize(Decimal("0.01")))
    return {"method": "Revenue variance = volume + price + mix/residual; computed with Decimal", "totals": result_totals, "segments": rows}
