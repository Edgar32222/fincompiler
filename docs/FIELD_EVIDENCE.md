# Field evidence and simulation policy

FinCompiler uses synthetic values, but its field names, types and accounting distinctions are grounded in public vendor documentation. No customer or personal financial data is copied into the repository.

| Source profile | Publicly documented fields represented | Canonical treatment | Evidence |
| --- | --- | --- | --- |
| Xero invoice lines | InvoiceNumber, Date, DueDate, CurrencyCode, CurrencyRate, Status; Quantity, UnitAmount, ItemCode, AccountCode, TaxAmount, LineAmount, DiscountAmount | Header fields repeat per exported line; line amounts are aggregated by invoice before GL reconciliation; tax and discount remain separate | [Official Xero OpenAPI](https://github.com/XeroAPI/Xero-OpenAPI), [official generated line-item model](https://github.com/XeroAPI/xero-php-oauth2/blob/master/lib/Models/Accounting/LineItem.php), [official invoice model](https://github.com/XeroAPI/xero-python/blob/master/xero_python/accounting/models/invoice.py) |
| QuickBooks Online invoice lines | DocNumber, TxnDate, CustomerRef, Line.Amount, SalesItemLineDetail.ItemRef, Qty, UnitPrice | Flattened path names are mapped without guessing; description/subtotal/discount lines can remain unmapped until explicitly handled | [Official Intuit PHP SDK guide](https://github.com/intuit/QuickBooks-V3-PHP-SDK/blob/master/docs/_sources/quickstart.rst.txt), [Intuit developer example](https://gist.github.com/IntuitDeveloperRelations/6500373) |
| Dynamics general journal | VOUCHER, TRANSDATE, ACCOUNTDISPLAYVALUE, CURRENCYCODE, DEBITAMOUNT, CREDITAMOUNT, EXCHANGERATE, reporting/accounting currency amounts | Revenue amount is deterministically derived as credit minus debit and retains both source cells in lineage | [Microsoft general journal entity](https://learn.microsoft.com/en-us/dynamics365/fin-ops-core/dev-itpro/data-entities/entity-general-journal), [Microsoft dual-currency documentation](https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/dual-currency) |
| Business Central sales invoice lines | Document No., customer number, Quantity, Unit Price, Line Discount Amount, Amount, Amount Including VAT, VAT %, Unit Cost (LCY) | Ex-tax, tax-inclusive and local-currency cost values are distinct canonical fields | [Microsoft Sales Invoice Line table](https://learn.microsoft.com/en-us/dynamics365/business-central/application/base-application/table/microsoft.sales.history.sales-invoice-line), [Business Central API line resource](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/api-reference/v2.0/resources/dynamics_salesinvoiceline) |
| Amazon Settlement V2 | settlement-id, settlement dates, deposit-date, total-amount, currency, transaction-type, order-id, marketplace-name, amount-type, amount-description, amount, posted-date, SKU and quantity | Repeated settlement totals are consistency-checked; payout totals reconcile to a specific bank row; only explicit amount-type/description categories enter SKU profit; locale-ambiguous comma decimals are blocked | [Official SP-API settlement report types](https://developer-docs.amazon.com/sp-api/docs/report-type-values-settlement), [official legacy-removal notice](https://developer-docs.amazon.com/sp-api/changelog/update-removal-of-xml-settlement-report-and-flat-file-settlement-report-date-changed-to-november-11-2026) |
| Shopify orders CSV | Name, Financial Status, Created at, Currency, Total, Shipping, Taxes, Discount Amount, Lineitem quantity/SKU/name/price | Order-level total and tax are consistency-checked across repeated line rows; ex-tax order value is allocated to SKU lines by deterministic line-value weights | [Official Shopify order export documentation](https://help.shopify.com/en/manual/fulfillment/managing-orders/exporting-orders) |
| Shopify Payments payout CSV | Transaction Date, Type, Order, Payout Status, Payout Date, Amount, Fee and Net | Only paid payout groups enter bank matching; Net is summed by payout ID or payout date/currency; order-linked fees and refunds feed SKU economics without an LLM | [Official Shopify payout export documentation](https://help.shopify.com/en/manual/payments/shopify-payments/payouts/view-details), [payout activity report guidance](https://help.shopify.com/en/manual/payments/shopify-payments/payouts/payouts-activity-report) |

## Community-derived failure modes

Public accounting discussions repeatedly describe monthly CSV work involving header renaming, date reformatting, encoding cleanup, separate debit/credit columns, and exact-match requirements for contacts, tax rates and account codes. These observations inform test scenarios only; community answers are not treated as accounting authority.

- [Stripe-to-QuickBooks CSV reformatting discussion](https://www.reddit.com/r/QuickBooks/comments/1rn2zbw/spent_15_minutes_every_week_reformatting_stripe/)
- [Xero multi-line CSV import discussion](https://www.reddit.com/r/xero/comments/1fwm7on)
- [Xero line grouping and distinct tax/account treatment](https://www.reddit.com/r/xero/comments/1plrd8w/invoice_line_item_grouping/)

## Guardrails

- Profile recognition requires a multi-field signature, not one coincidental header.
- Exact documented fields receive deterministic proposals; unfamiliar fields still require review.
- Dates that are not ISO, `YYYY/MM/DD`, or an unambiguous `DD-Mon-YYYY` form are rejected rather than locale-guessed.
- Currency must be a supported ISO 4217 code. Foreign-currency calculations require dated rate evidence under an explicit policy.
- Derived amounts expose their formula and source cells.
