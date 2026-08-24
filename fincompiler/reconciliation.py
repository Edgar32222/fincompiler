from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from .lineage import aggregate
from .models import CanonicalRecord, ExceptionItem, money


def investigate_sales_gl(sales: list[CanonicalRecord], gl: list[CanonicalRecord], tolerance: Decimal = Decimal("0.01"), revenue_accounts: tuple[str, ...] = ("Revenue", "Sales Revenue", "4000"), base_currency: str = "AED") -> dict:
    allowed_accounts = {account.strip().lower() for account in revenue_accounts}
    sales_total = aggregate(sales, "net_sales", "sales_subledger")
    revenue_gl = [r for r in gl if str(r.values.get("account", "")).strip().lower() in allowed_accounts]
    gl_total = aggregate(revenue_gl, "amount", "gl_revenue")
    sales_currencies = {str(record.values.get("currency", base_currency)).upper() for record in sales}
    gl_currencies = {str(record.values.get("currency", base_currency)).upper() for record in revenue_gl}
    if sales_currencies != {base_currency} or gl_currencies != {base_currency}:
        exception = ExceptionItem("CURRENCY_BASIS_REQUIRED", "BLOCKING", "Sales and GL must be compared on an explicitly converted common currency basis", {"base_currency": base_currency, "sales_currencies": sorted(sales_currencies), "gl_currencies": sorted(gl_currencies)})
        return {"status": "NEEDS_REVIEW", "sales_total": sales_total.jsonable(), "gl_total": gl_total.jsonable(), "variance": "NOT_COMPARABLE", "causes": [], "exceptions": [exception.__dict__]}
    variance = (sales_total.value - gl_total.value).quantize(Decimal("0.01"))
    gl_by_ref = defaultdict(lambda: Decimal("0"))
    for record in revenue_gl:
        gl_by_ref[str(record.values.get("reference", ""))] += money(record.values.get("amount"))
    sales_by_invoice = defaultdict(lambda: Decimal("0"))
    for record in sales:
        sales_by_invoice[record.record_id] += money(record.values.get("net_sales"))
    causes = []
    for invoice_id, expected in sales_by_invoice.items():
        posted = gl_by_ref.pop(invoice_id, Decimal("0"))
        difference = (expected - posted).quantize(Decimal("0.01"))
        if abs(difference) > tolerance:
            cause = "MISSING_GL_ENTRY" if posted == 0 else "AMOUNT_MISMATCH"
            causes.append({"reference": invoice_id, "sales": str(expected), "gl": str(posted), "difference": str(difference), "reason": cause})
    for reference, posted in gl_by_ref.items():
        if posted:
            causes.append({"reference": reference or "(blank)", "sales": "0.00", "gl": str(posted), "difference": str(-posted), "reason": "UNMATCHED_GL_ENTRY"})
    status = "PASS" if abs(variance) <= tolerance and not causes else "NEEDS_REVIEW"
    exceptions = [] if status == "PASS" else [ExceptionItem("SALES_GL_VARIANCE", "BLOCKING", "Sales and GL revenue do not reconcile", {"variance": str(variance), "causes": causes})]
    return {"status": status, "sales_total": sales_total.jsonable(), "gl_total": gl_total.jsonable(), "variance": str(variance), "causes": causes, "exceptions": [e.__dict__ for e in exceptions]}
