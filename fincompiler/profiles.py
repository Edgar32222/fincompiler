from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceProfile:
    name: str
    dataset: str
    signature: frozenset[str]
    aliases: dict[str, str]
    ignored_fields: frozenset[str] = frozenset()


PROFILES = (
    SourceProfile("amazon_settlement_v2", "amazon_settlements", frozenset({"settlement-id", "amount-type", "amount-description", "amount", "currency"}), {
        "settlement-id": "settlement_id", "settlement-start-date": "settlement_start_date", "settlement-end-date": "settlement_end_date",
        "deposit-date": "payout_date", "total-amount": "settlement_total", "currency": "currency",
        "transaction-type": "transaction_type", "order-id": "order_id", "marketplace-name": "marketplace",
        "amount-type": "amount_type", "amount-description": "amount_description", "amount": "amount",
        "posted-date": "date", "posted-date-time": "posted_at", "order-item-code": "order_item_id",
        "sku": "sku", "quantity-purchased": "quantity",
    }, frozenset({"merchant-order-id", "adjustment-id", "shipment-id", "fulfillment-id", "merchant-order-item-id", "merchant-adjustment-item-id", "promotion-id"})),
    SourceProfile("shopify_orders_csv", "shopify_orders", frozenset({"name", "financial status", "currency", "total", "lineitem quantity", "lineitem sku"}), {
        "Name": "order_id", "Financial Status": "financial_status", "Created at": "date", "Paid at": "paid_date",
        "Currency": "currency", "Total": "gross_sales", "Discount Amount": "discount_amount",
        "Shipping": "shipping_income", "Taxes": "tax_amount", "Lineitem quantity": "quantity",
        "Lineitem SKU": "sku", "Lineitem name": "description", "Lineitem price": "unit_price",
    }, frozenset({"phone", "email", "fulfillment status", "fulfilled at", "discount code", "shipping method", "payment method", "notes", "location", "source", "tags"})),
    SourceProfile("shopify_payments_payout_csv", "shopify_payouts", frozenset({"transaction date", "type", "order", "payout status", "payout date", "amount", "fee", "net"}), {
        "Transaction Date": "date", "Type": "transaction_type", "Order": "order_id", "Payout Status": "payout_status",
        "Payout Date": "payout_date", "Amount": "gross_amount", "Fee": "fee_amount", "Net": "net_amount",
        "Currency": "currency", "Payout ID": "payout_id", "Transfer Reference": "bank_reference",
    }),
    SourceProfile("bank_statement", "bank", frozenset({"transaction id", "value date", "reference", "amount", "currency"}), {
        "Transaction ID": "bank_transaction_id", "Value Date": "date", "Reference": "bank_reference",
        "Amount": "amount", "Currency": "currency", "Description": "description",
    }),
    SourceProfile("sku_cost_master", "sku_costs", frozenset({"sku", "effective date", "unit purchase cost", "currency"}), {
        "SKU": "sku", "Effective Date": "effective_date", "Unit Purchase Cost": "unit_purchase_cost",
        "Unit Freight Cost": "unit_freight_cost", "Unit Duty Cost": "unit_duty_cost",
        "Other Unit Cost": "other_unit_cost", "Currency": "currency",
    }),
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
