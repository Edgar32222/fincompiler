from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from .models import CanonicalRecord, ExceptionItem, money


NUMERIC_FIELDS = {"quantity", "unit_price", "net_sales", "gross_amount", "discount_amount", "tax_amount", "tax_rate", "exchange_rate", "unit_cost_local", "amount", "debit_amount", "credit_amount", "accounting_currency_amount", "reporting_currency_amount", "revenue"}
DATE_FIELDS = {"date", "due_date", "period"}


def _date(value: str) -> str:
    raw = value.strip()
    if len(raw) == 7 and raw[4] == "-":
        return datetime.strptime(raw, "%Y-%m").date().isoformat()
    for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(raw, pattern).date().isoformat()
        except ValueError:
            pass
    raise ValueError("ambiguous or unsupported date; use ISO YYYY-MM-DD")


def normalize_records(records: list[CanonicalRecord]) -> tuple[list[CanonicalRecord], list[ExceptionItem]]:
    exceptions = []
    for record in records:
        for field, value in list(record.values.items()):
            if value in {None, ""}:
                continue
            try:
                if field in NUMERIC_FIELDS:
                    record.values[field] = money(value)
                elif field in DATE_FIELDS:
                    record.values[field] = _date(str(value))
                elif field == "currency":
                    currency = str(value).strip().upper()
                    if len(currency) != 3 or not currency.isalpha():
                        raise ValueError("currency must be a three-letter code")
                    record.values[field] = currency
            except (ValueError, InvalidOperation) as exc:
                exceptions.append(ExceptionItem("TYPE_VALIDATION_FAILED", "HIGH", f"Invalid {field} value", {"record_id": record.record_id, "field": field, "value": str(value), "reason": str(exc)}))
        if record.dataset == "gl" and "amount" not in record.values and ({"debit_amount", "credit_amount"} & record.values.keys()):
            debit, credit = money(record.values.get("debit_amount")), money(record.values.get("credit_amount"))
            record.values["amount"] = (credit - debit).quantize(Decimal("0.01"))
            record.derivations["amount"] = {"formula": "credit_amount - debit_amount", "sources": [record.lineage[name] for name in ("credit_amount", "debit_amount") if name in record.lineage]}
        if record.dataset == "sales" and "net_sales" not in record.values and {"quantity", "unit_price"} <= record.values.keys():
            discount = money(record.values.get("discount_amount"))
            record.values["net_sales"] = (money(record.values["quantity"]) * money(record.values["unit_price"]) - discount).quantize(Decimal("0.01"))
            record.derivations["net_sales"] = {"formula": "quantity * unit_price - discount_amount", "sources": [record.lineage[name] for name in ("quantity", "unit_price", "discount_amount") if name in record.lineage]}
    return records, exceptions

