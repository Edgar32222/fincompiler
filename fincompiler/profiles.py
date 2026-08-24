from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceProfile:
    name: str
    dataset: str
    signature: frozenset[str]
    aliases: dict[str, str]


PROFILES = (
    SourceProfile("xero_invoice_lines", "sales", frozenset({"invoicenumber", "lineamount", "currencycode", "itemcode"}), {
        "InvoiceNumber": "invoice_id", "Date": "date", "DueDate": "due_date", "ContactName": "customer",
        "ContactID": "customer_id", "ItemCode": "sku", "Description": "description", "Quantity": "quantity",
        "UnitAmount": "unit_price", "DiscountAmount": "discount_amount", "LineAmount": "net_sales",
        "TaxAmount": "tax_amount", "CurrencyCode": "currency", "CurrencyRate": "exchange_rate",
        "Status": "status", "AccountCode": "revenue_account", "Type": "document_type",
    }),
    SourceProfile("quickbooks_invoice_lines", "sales", frozenset({"docnumber", "txndate", "line.amount", "salesitemlinedetail.qty"}), {
        "DocNumber": "invoice_id", "TxnDate": "date", "DueDate": "due_date", "CustomerRef": "customer",
        "CurrencyRef": "currency", "ExchangeRate": "exchange_rate", "Line.Id": "line_id",
        "Line.Description": "description", "Line.Amount": "net_sales", "SalesItemLineDetail.ItemRef": "sku",
        "SalesItemLineDetail.Qty": "quantity", "SalesItemLineDetail.UnitPrice": "unit_price",
        "SalesItemLineDetail.DiscountAmt": "discount_amount", "TxnTaxDetail.TotalTax": "tax_amount",
    }),
    SourceProfile("business_central_sales_invoice_lines", "sales", frozenset({"document no.", "sell-to customer no.", "unit price", "amount including vat"}), {
        "Document No.": "invoice_id", "Posting Date": "date", "Sell-to Customer No.": "customer_id",
        "Sell-to Customer Name": "customer", "No.": "sku", "Description": "description", "Quantity": "quantity",
        "Unit Price": "unit_price", "Line Discount Amount": "discount_amount", "Amount": "net_sales",
        "Amount Including VAT": "gross_amount", "VAT %": "tax_rate", "Unit Cost (LCY)": "unit_cost_local",
        "Currency Code": "currency",
    }),
    SourceProfile("dynamics_general_journal", "gl", frozenset({"voucher", "transdate", "accountdisplayvalue", "currencycode"}), {
        "VOUCHER": "entry_id", "TRANSDATE": "date", "ACCOUNTDISPLAYVALUE": "account", "DESCRIPTION": "description",
        "INVOICEREFERENCE": "reference", "DOCUMENTNUMBER": "reference", "CURRENCYCODE": "currency",
        "DEBITAMOUNT": "debit_amount", "CREDITAMOUNT": "credit_amount", "EXCHANGERATE": "exchange_rate",
        "ACCOUNTINGCURRENCYAMOUNT": "accounting_currency_amount", "REPORTINGCURRENCYAMOUNT": "reporting_currency_amount",
        "JOURNALBATCHNUMBER": "batch_id", "LEGALENTITY": "legal_entity", "FINANCIALDIMENSION": "dimension",
    }),
)


def detect_profile(dataset: str, fields: list[str]) -> SourceProfile | None:
    normalized = {field.strip().lower() for field in fields}
    candidates = [profile for profile in PROFILES if profile.dataset == dataset and profile.signature <= normalized]
    return max(candidates, key=lambda profile: len(profile.signature), default=None)

