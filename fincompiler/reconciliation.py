from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from itertools import combinations

from .lineage import aggregate
from .models import CanonicalRecord, ExceptionItem, money


def _period(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return date.fromisoformat(raw[:10]).strftime("%Y-%m")
    except ValueError:
        return raw[:7] if len(raw) >= 7 else ""


def _record_amounts(records: list[CanonicalRecord], field: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for record in records:
        totals[record.record_id] += money(record.values.get(field))
    return dict(totals)


def _component_reason(expected: Decimal, posted: Decimal, records: list[CanonicalRecord], tolerance: Decimal) -> tuple[str, dict]:
    difference = (expected - posted).quantize(Decimal("0.01"))
    components = {
        "tax": sum((money(record.values.get("tax_amount")) for record in records), Decimal("0")),
        "discount": sum((money(record.values.get("discount_amount")) for record in records), Decimal("0")),
        "freight": sum((money(record.values.get("freight_amount")) for record in records), Decimal("0")),
    }
    checks = (
        ("TAX_INCLUDED_IN_GL", -components["tax"], "tax"),
        ("TAX_MISSING_FROM_GL", components["tax"], "tax"),
        ("DISCOUNT_COMPONENT_MISMATCH", components["discount"], "discount"),
        ("DISCOUNT_COMPONENT_MISMATCH", -components["discount"], "discount"),
        ("FREIGHT_COMPONENT_MISMATCH", components["freight"], "freight"),
        ("FREIGHT_COMPONENT_MISMATCH", -components["freight"], "freight"),
    )
    for reason, candidate, component in checks:
        if candidate and abs(difference - candidate) <= tolerance:
            return reason, {"component": component, "component_amount": str(abs(candidate).quantize(Decimal("0.01")))}
    return ("MISSING_GL_ENTRY" if posted == 0 else "AMOUNT_MISMATCH"), {}


def _unique_amount_group(target: Decimal, candidates: list[str], sales_totals: dict[str, Decimal], max_group_size: int = 4) -> tuple[str, ...] | None:
    """Return a unique invoice subset matching target, otherwise refuse to guess."""
    if len(candidates) > 30:
        return None
    matches: list[tuple[str, ...]] = []
    for size in range(2, min(max_group_size, len(candidates)) + 1):
        for group in combinations(sorted(candidates), size):
            if sum((sales_totals[item] for item in group), Decimal("0")) == target:
                matches.append(group)
                if len(matches) > 1:
                    return None
    return matches[0] if len(matches) == 1 else None


def investigate_sales_gl(
    sales: list[CanonicalRecord],
    gl: list[CanonicalRecord],
    tolerance: Decimal = Decimal("0.01"),
    revenue_accounts: tuple[str, ...] = ("Revenue", "Sales Revenue", "4000"),
    base_currency: str = "AED",
) -> dict:
    allowed_accounts = {account.strip().lower() for account in revenue_accounts}
    sales_total = aggregate(sales, "net_sales", "sales_subledger")
    revenue_gl = [record for record in gl if str(record.values.get("account", "")).strip().lower() in allowed_accounts]
    gl_total = aggregate(revenue_gl, "amount", "gl_revenue")
    sales_currencies = {str(record.values.get("currency", base_currency)).upper() for record in sales}
    gl_currencies = {str(record.values.get("currency", base_currency)).upper() for record in revenue_gl}
    if sales_currencies != {base_currency} or gl_currencies != {base_currency}:
        exception = ExceptionItem("CURRENCY_BASIS_REQUIRED", "BLOCKING", "Sales and GL must be compared on an explicitly converted common currency basis", {"base_currency": base_currency, "sales_currencies": sorted(sales_currencies), "gl_currencies": sorted(gl_currencies)})
        return {"status": "NEEDS_REVIEW", "sales_total": sales_total.jsonable(), "gl_total": gl_total.jsonable(), "variance": "NOT_COMPARABLE", "causes": [], "match_groups": [], "attribution": {"explained": "0.00", "unexplained": "NOT_COMPARABLE", "percent": "0.00"}, "exceptions": [exception.__dict__]}

    variance = (sales_total.value - gl_total.value).quantize(Decimal("0.01"))
    sales_by_invoice: dict[str, list[CanonicalRecord]] = defaultdict(list)
    for record in sales:
        sales_by_invoice[record.record_id].append(record)
    sales_totals = _record_amounts(sales, "net_sales")
    gl_by_ref: dict[str, list[CanonicalRecord]] = defaultdict(list)
    for record in revenue_gl:
        gl_by_ref[str(record.values.get("reference", "")).strip()].append(record)

    causes: list[dict] = []
    match_groups: list[dict] = []
    unmatched_sales = set(sales_totals)
    used_gl: set[str] = set()
    explained = Decimal("0")

    # Explicit references take precedence. Multiple GL lines with one reference
    # are a split posting, not duplicate revenue.
    for invoice_id in sorted(sales_totals):
        records = gl_by_ref.get(invoice_id, [])
        if not records:
            continue
        expected = sales_totals[invoice_id]
        posted = sum((money(record.values.get("amount")) for record in records), Decimal("0"))
        difference = (expected - posted).quantize(Decimal("0.01"))
        used_gl.update(record.record_id for record in records)
        unmatched_sales.discard(invoice_id)
        sales_periods = {_period(record.values.get("date")) for record in sales_by_invoice[invoice_id]} - {""}
        gl_periods = {_period(record.values.get("date")) for record in records} - {""}
        if sales_periods and gl_periods and sales_periods != gl_periods:
            causes.append({"reference": invoice_id, "sales": str(expected), "gl": str(posted), "difference": str(difference), "reason": "CROSS_PERIOD_CUTOFF", "sales_periods": sorted(sales_periods), "gl_periods": sorted(gl_periods)})
            explained += abs(difference)
        elif abs(difference) <= tolerance:
            match_groups.append({"group_id": f"reference:{invoice_id}", "method": "SPLIT_REFERENCE" if len(records) > 1 else "EXACT_REFERENCE", "sales_references": [invoice_id], "sales_record_ids": [record.record_id for record in sales_by_invoice[invoice_id]], "gl_record_ids": [record.record_id for record in records], "sales": str(expected), "gl": str(posted), "residual": str(difference)})
        else:
            reason, detail = _component_reason(expected, posted, sales_by_invoice[invoice_id], tolerance)
            cause = {"reference": invoice_id, "sales": str(expected), "gl": str(posted), "difference": str(difference), "reason": reason}
            cause.update(detail)
            causes.append(cause)
            explained += abs(difference)

    remaining_gl = [record for record in revenue_gl if record.record_id not in used_gl]

    # Accept a multi-invoice batch when its source text names every invoice.
    for record in list(remaining_gl):
        searchable = " | ".join(str(record.values.get(field, "")) for field in ("reference", "description", "batch_id"))
        named = tuple(sorted(invoice_id for invoice_id in unmatched_sales if invoice_id and invoice_id in searchable))
        if len(named) < 2:
            continue
        expected = sum((sales_totals[item] for item in named), Decimal("0"))
        posted = money(record.values.get("amount"))
        difference = (expected - posted).quantize(Decimal("0.01"))
        if abs(difference) <= tolerance:
            match_groups.append({"group_id": f"batch:{record.record_id}", "method": "EXPLICIT_BATCH_REFERENCES", "sales_references": list(named), "sales_record_ids": [item.record_id for ref in named for item in sales_by_invoice[ref]], "gl_record_ids": [record.record_id], "sales": str(expected), "gl": str(posted), "residual": str(difference)})
        else:
            causes.append({"reference": str(record.values.get("batch_id") or record.record_id), "sales": str(expected), "gl": str(posted), "difference": str(difference), "reason": "BATCH_AMOUNT_MISMATCH", "sales_references": list(named)})
            explained += abs(difference)
        unmatched_sales.difference_update(named)
        used_gl.add(record.record_id)

    remaining_gl = [record for record in revenue_gl if record.record_id not in used_gl]

    # Amount-only matching is allowed only for a unique, small invoice subset.
    for record in remaining_gl:
        posted = money(record.values.get("amount"))
        gl_period = _period(record.values.get("date"))
        same_period = [invoice_id for invoice_id in unmatched_sales if not gl_period or _period(sales_by_invoice[invoice_id][0].values.get("date")) == gl_period]
        group = _unique_amount_group(posted, same_period, sales_totals)
        if not group:
            continue
        expected = sum((sales_totals[item] for item in group), Decimal("0"))
        match_groups.append({"group_id": f"batch:{record.record_id}", "method": "UNIQUE_AMOUNT_BATCH", "sales_references": list(group), "sales_record_ids": [item.record_id for ref in group for item in sales_by_invoice[ref]], "gl_record_ids": [record.record_id], "sales": str(expected), "gl": str(posted), "residual": "0.00"})
        unmatched_sales.difference_update(group)
        used_gl.add(record.record_id)

    for invoice_id in sorted(unmatched_sales):
        expected = sales_totals[invoice_id]
        causes.append({"reference": invoice_id, "sales": str(expected), "gl": "0", "difference": str(expected.quantize(Decimal("0.01"))), "reason": "MISSING_GL_ENTRY"})
        explained += abs(expected)
    for record in revenue_gl:
        if record.record_id in used_gl:
            continue
        posted = money(record.values.get("amount"))
        if posted:
            reference = str(record.values.get("reference", "")).strip() or "(blank)"
            causes.append({"reference": reference, "sales": "0.00", "gl": str(posted), "difference": str(-posted), "reason": "UNMATCHED_GL_ENTRY", "gl_record_ids": [record.record_id]})
            explained += abs(posted)

    causes.sort(key=lambda item: (str(item.get("reference", "")), str(item.get("reason", ""))))
    match_groups.sort(key=lambda item: item["group_id"])
    status = "PASS" if abs(variance) <= tolerance and not causes else "NEEDS_REVIEW"
    unexplained = max(Decimal("0"), abs(variance) - explained).quantize(Decimal("0.01"))
    attribution_percent = Decimal("100.00") if variance == 0 and not causes else ((min(explained, abs(variance)) / abs(variance) * Decimal("100")).quantize(Decimal("0.01")) if variance else Decimal("0.00"))
    exceptions = [] if status == "PASS" else [ExceptionItem("SALES_GL_VARIANCE", "BLOCKING", "Sales and GL revenue do not reconcile or contain a timing exception", {"variance": str(variance), "causes": causes, "unexplained": str(unexplained)})]
    return {"status": status, "sales_total": sales_total.jsonable(), "gl_total": gl_total.jsonable(), "variance": str(variance), "causes": causes, "match_groups": match_groups, "attribution": {"explained": str(min(explained, abs(variance)).quantize(Decimal("0.01"))), "unexplained": str(unexplained), "percent": str(attribution_percent)}, "exceptions": [exception.__dict__ for exception in exceptions]}
