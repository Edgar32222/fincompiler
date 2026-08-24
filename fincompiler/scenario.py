from __future__ import annotations

import csv
import json
import random
from decimal import Decimal
from pathlib import Path


SALES_FIELDS = ["InvoiceNumber", "Date", "DueDate", "ContactName", "ItemCode", "Description", "Quantity", "UnitAmount", "DiscountAmount", "LineAmount", "TaxAmount", "CurrencyCode", "CurrencyRate", "Status", "AccountCode"]
GL_FIELDS = ["VOUCHER", "TRANSDATE", "ACCOUNTDISPLAYVALUE", "DESCRIPTION", "INVOICEREFERENCE", "CURRENCYCODE", "DEBITAMOUNT", "CREDITAMOUNT", "EXCHANGERATE", "ACCOUNTINGCURRENCYAMOUNT", "REPORTINGCURRENCYAMOUNT", "JOURNALBATCHNUMBER", "LEGALENTITY", "FINANCIALDIMENSION"]
BUDGET_FIELDS = ["Period", "Customer", "SKU", "Qty", "Unit Price", "Revenue"]
SUPPORTED_ANOMALIES = {"split_posting", "batch_posting", "amount_mismatch", "missing_gl", "unmatched_gl", "credit_note", "tax_in_gl", "cross_period"}


def _write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate_scenario(output_dir: str | Path, seed: int = 42, invoice_count: int = 50, anomalies: list[str] | None = None) -> dict:
    anomalies = anomalies or []
    unknown = set(anomalies) - SUPPORTED_ANOMALIES
    if unknown:
        raise ValueError(f"Unsupported anomalies: {sorted(unknown)}")
    if invoice_count < 5:
        raise ValueError("invoice_count must be at least 5")
    rng, output = random.Random(seed), Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    customers = ["Orion Retail", "Atlas Stores", "Cedar Trading", "Northstar LLC"]
    products = [("KETTLE-A", "Electric kettle"), ("TOASTER-B", "Four slice toaster"), ("BLENDER-C", "Countertop blender")]
    sales, budget, invoice_totals, invoice_taxes = [], [], {}, {}
    for index in range(1, invoice_count + 1):
        invoice = f"INV-S{index:05d}"
        customer = rng.choice(customers)
        invoice_total = Decimal("0")
        for sku, description in rng.sample(products, rng.randint(1, 3)):
            quantity = rng.randint(5, 60)
            unit_price = Decimal(rng.randrange(8000, 30001)) / 100
            discount = (Decimal(quantity) * unit_price * Decimal(rng.choice([0, 0, 0, 5, 10])) / 100).quantize(Decimal("0.01"))
            line_amount = (Decimal(quantity) * unit_price - discount).quantize(Decimal("0.01"))
            invoice_total += line_amount
            sales.append({"InvoiceNumber": invoice, "Date": "2026-07-15", "DueDate": "2026-08-14", "ContactName": customer, "ItemCode": sku, "Description": description, "Quantity": quantity, "UnitAmount": unit_price, "DiscountAmount": discount, "LineAmount": line_amount, "TaxAmount": (line_amount * Decimal("0.05")).quantize(Decimal("0.01")), "CurrencyCode": "AED", "CurrencyRate": "1.000000", "Status": "AUTHORISED", "AccountCode": "4000"})
            budget_qty = max(1, quantity + rng.randint(-8, 8))
            budget_price = (unit_price * Decimal("0.97")).quantize(Decimal("0.01"))
            budget.append({"Period": "2026-07", "Customer": customer, "SKU": sku, "Qty": budget_qty, "Unit Price": budget_price, "Revenue": (Decimal(budget_qty) * budget_price).quantize(Decimal("0.01"))})
        invoice_totals[invoice] = invoice_total.quantize(Decimal("0.01"))
        invoice_taxes[invoice] = sum((Decimal(str(row["TaxAmount"])) for row in sales if row["InvoiceNumber"] == invoice), Decimal("0")).quantize(Decimal("0.01"))

    truth_causes = []
    gl = []
    invoice_ids = sorted(invoice_totals)
    mismatch_id, missing_id = invoice_ids[-1], invoice_ids[-2]
    batch_ids = set(invoice_ids[1:3]) if "batch_posting" in anomalies else set()
    tax_id = invoice_ids[3]
    cutoff_id = invoice_ids[4]
    for index, invoice in enumerate(invoice_ids, start=1):
        amount = invoice_totals[invoice]
        if invoice in batch_ids:
            continue
        if "missing_gl" in anomalies and invoice == missing_id:
            truth_causes.append({"reference": invoice, "reason": "MISSING_GL_ENTRY", "difference": str(amount)})
            continue
        if "amount_mismatch" in anomalies and invoice == mismatch_id:
            adjustment = min(Decimal("2706.00"), (amount / 2).quantize(Decimal("0.01")))
            amount -= adjustment
            truth_causes.append({"reference": invoice, "reason": "AMOUNT_MISMATCH", "difference": str(adjustment)})
        if "tax_in_gl" in anomalies and invoice == tax_id:
            amount += invoice_taxes[invoice]
            truth_causes.append({"reference": invoice, "reason": "TAX_INCLUDED_IN_GL", "difference": str(-invoice_taxes[invoice])})
        posting_date = "2026-08-01" if "cross_period" in anomalies and invoice == cutoff_id else "2026-07-15"
        if "cross_period" in anomalies and invoice == cutoff_id:
            truth_causes.append({"reference": invoice, "reason": "CROSS_PERIOD_CUTOFF", "difference": "0.00"})
        pieces = [amount]
        if "split_posting" in anomalies and invoice == invoice_ids[0]:
            first = (amount * Decimal("0.60")).quantize(Decimal("0.01"))
            pieces = [first, amount - first]
        for part, piece in enumerate(pieces, start=1):
            gl.append({"VOUCHER": f"JE-{index:05d}-{part}", "TRANSDATE": posting_date, "ACCOUNTDISPLAYVALUE": "4000", "DESCRIPTION": "Synthetic sales posting", "INVOICEREFERENCE": invoice, "CURRENCYCODE": "AED", "DEBITAMOUNT": "0", "CREDITAMOUNT": piece, "EXCHANGERATE": "1.000000", "ACCOUNTINGCURRENCYAMOUNT": piece, "REPORTINGCURRENCYAMOUNT": (piece / Decimal("4")).quantize(Decimal("0.01")), "JOURNALBATCHNUMBER": "SYNTH-0726", "LEGALENTITY": "NOVA", "FINANCIALDIMENSION": "BU-RETAIL"})
    if batch_ids:
        references = sorted(batch_ids)
        amount = sum((invoice_totals[invoice] for invoice in references), Decimal("0"))
        gl.append({"VOUCHER": "JE-BATCH-MERGED", "TRANSDATE": "2026-07-15", "ACCOUNTDISPLAYVALUE": "4000", "DESCRIPTION": f"Merged sales batch {' + '.join(references)}", "INVOICEREFERENCE": "+".join(references), "CURRENCYCODE": "AED", "DEBITAMOUNT": "0", "CREDITAMOUNT": amount, "EXCHANGERATE": "1.000000", "ACCOUNTINGCURRENCYAMOUNT": amount, "REPORTINGCURRENCYAMOUNT": (amount / Decimal("4")).quantize(Decimal("0.01")), "JOURNALBATCHNUMBER": "SYNTH-MERGED-0726", "LEGALENTITY": "NOVA", "FINANCIALDIMENSION": "BU-RETAIL"})
    if "unmatched_gl" in anomalies:
        gl.append({"VOUCHER": "JE-ORPHAN", "TRANSDATE": "2026-07-31", "ACCOUNTDISPLAYVALUE": "4000", "DESCRIPTION": "Orphan synthetic posting", "INVOICEREFERENCE": "UNKNOWN-REF", "CURRENCYCODE": "AED", "DEBITAMOUNT": "0", "CREDITAMOUNT": "777.00", "EXCHANGERATE": "1.000000", "ACCOUNTINGCURRENCYAMOUNT": "777.00", "REPORTINGCURRENCYAMOUNT": "194.25", "JOURNALBATCHNUMBER": "SYNTH-0726", "LEGALENTITY": "NOVA", "FINANCIALDIMENSION": "BU-RETAIL"})
        truth_causes.append({"reference": "UNKNOWN-REF", "reason": "UNMATCHED_GL_ENTRY", "difference": "-777.00"})
    if "credit_note" in anomalies:
        sales.append({"InvoiceNumber": "CN-S00001", "Date": "2026-07-20", "DueDate": "2026-07-20", "ContactName": "Orion Retail", "ItemCode": "KETTLE-A", "Description": "Returned kettle", "Quantity": -2, "UnitAmount": "100.00", "DiscountAmount": "0", "LineAmount": "-200.00", "TaxAmount": "-10.00", "CurrencyCode": "AED", "CurrencyRate": "1.000000", "Status": "AUTHORISED", "AccountCode": "4000"})
        gl.append({"VOUCHER": "JE-CREDIT", "TRANSDATE": "2026-07-20", "ACCOUNTDISPLAYVALUE": "4000", "DESCRIPTION": "Credit note", "INVOICEREFERENCE": "CN-S00001", "CURRENCYCODE": "AED", "DEBITAMOUNT": "200.00", "CREDITAMOUNT": "0", "EXCHANGERATE": "1.000000", "ACCOUNTINGCURRENCYAMOUNT": "-200.00", "REPORTINGCURRENCYAMOUNT": "-50.00", "JOURNALBATCHNUMBER": "SYNTH-0726", "LEGALENTITY": "NOVA", "FINANCIALDIMENSION": "BU-RETAIL"})

    _write(output / "sales.csv", SALES_FIELDS, sales)
    _write(output / "gl.csv", GL_FIELDS, gl)
    _write(output / "budget.csv", BUDGET_FIELDS, budget)
    config = {"company_name": "Synthetic Nova Appliances", "base_currency": "AED", "revenue_accounts": ["4000"], "reconciliation_tolerance": "0.01"}
    (output / "company_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    manifest = {"generator_version": 1, "seed": seed, "invoice_count": invoice_count, "anomalies": anomalies, "expected_causes": truth_causes, "synthetic": True}
    (output / "truth_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
