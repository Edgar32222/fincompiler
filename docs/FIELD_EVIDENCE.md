# Field evidence and simulation policy

FinCompiler uses synthetic values, but its field names, types and accounting distinctions are grounded in public vendor documentation. No customer or personal financial data is copied into the repository.

| Source profile | Publicly documented fields represented | Canonical treatment | Evidence |
| --- | --- | --- | --- |
| Xero invoice lines | InvoiceNumber, Date, DueDate, CurrencyCode, CurrencyRate, Status; Quantity, UnitAmount, ItemCode, AccountCode, TaxAmount, LineAmount, DiscountAmount | Header fields repeat per exported line; line amounts are aggregated by invoice before GL reconciliation; tax and discount remain separate | [Official Xero OpenAPI](https://github.com/XeroAPI/Xero-OpenAPI), [official generated line-item model](https://github.com/XeroAPI/xero-php-oauth2/blob/master/lib/Models/Accounting/LineItem.php), [official invoice model](https://github.com/XeroAPI/xero-python/blob/master/xero_python/accounting/models/invoice.py) |
| QuickBooks Online invoice lines | DocNumber, TxnDate, CustomerRef, Line.Amount, SalesItemLineDetail.ItemRef, Qty, UnitPrice | Flattened path names are mapped without guessing; description/subtotal/discount lines can remain unmapped until explicitly handled | [Official Intuit PHP SDK guide](https://github.com/intuit/QuickBooks-V3-PHP-SDK/blob/master/docs/_sources/quickstart.rst.txt), [Intuit developer example](https://gist.github.com/IntuitDeveloperRelations/6500373) |
| Dynamics general journal | VOUCHER, TRANSDATE, ACCOUNTDISPLAYVALUE, CURRENCYCODE, DEBITAMOUNT, CREDITAMOUNT, EXCHANGERATE, reporting/accounting currency amounts | Revenue amount is deterministically derived as credit minus debit and retains both source cells in lineage | [Microsoft general journal entity](https://learn.microsoft.com/en-us/dynamics365/fin-ops-core/dev-itpro/data-entities/entity-general-journal), [Microsoft dual-currency documentation](https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/dual-currency) |
| Business Central sales invoice lines | Document No., customer number, Quantity, Unit Price, Line Discount Amount, Amount, Amount Including VAT, VAT %, Unit Cost (LCY) | Ex-tax, tax-inclusive and local-currency cost values are distinct canonical fields | [Microsoft Sales Invoice Line table](https://learn.microsoft.com/en-us/dynamics365/business-central/application/base-application/table/microsoft.sales.history.sales-invoice-line), [Business Central API line resource](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/api-reference/v2.0/resources/dynamics_salesinvoiceline) |

## Community-derived failure modes

Public accounting discussions repeatedly describe monthly CSV work involving header renaming, date reformatting, encoding cleanup, separate debit/credit columns, and exact-match requirements for contacts, tax rates and account codes. These observations inform test scenarios only; community answers are not treated as accounting authority.

- [Stripe-to-QuickBooks CSV reformatting discussion](https://www.reddit.com/r/QuickBooks/comments/1rn2zbw/spent_15_minutes_every_week_reformatting_stripe/)
- [Xero multi-line CSV import discussion](https://www.reddit.com/r/xero/comments/1fwm7on)
- [Xero line grouping and distinct tax/account treatment](https://www.reddit.com/r/xero/comments/1plrd8w/invoice_line_item_grouping/)

## Guardrails

- Profile recognition requires a multi-field signature, not one coincidental header.
- Exact documented fields receive deterministic proposals; unfamiliar fields still require review.
- Dates that are not ISO, `YYYY/MM/DD`, or an unambiguous `DD-Mon-YYYY` form are rejected rather than locale-guessed.
- Currency must be a three-letter alphabetic code.
- Derived amounts expose their formula and source cells.

