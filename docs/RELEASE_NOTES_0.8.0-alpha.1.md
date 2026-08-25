# FinCompiler v0.8.0-alpha.1

This release adds a Chinese-first cross-border seller workflow alongside the existing Finance month-end workflow.

## What a seller can do

- Import official-shape Amazon Settlement V2, Shopify order and Shopify payout exports.
- Match each paid platform payout to one bank transaction using explicit references first, then conservative unique amount/date rules.
- See the exact platform-to-bank residual and the specific source records involved; FinCompiler never inserts a balancing adjustment.
- Calculate SKU profit from ex-tax revenue, refunds, platform fees and effective-dated landed unit cost.
- Block profit when cost is missing, an Amazon activity is unknown or a fee cannot be attributed safely.
- Convert platform, bank and cost amounts through a dated local rate book. The UI can cache ECB reference rates, but applies them only after explicit user approval.
- Download a values-only Excel review pack and complete JSON/source-lineage evidence.

## Evidence and safety

The included HarborLight dataset is synthetic but uses fields documented by Amazon and Shopify. Amazon locale-ambiguous comma decimals are blocked rather than guessed. Every mapped value retains file, sheet/CSV marker, row, original field and raw value.

All monetary logic uses Python `Decimal`. No LLM calculates, classifies an unknown fee or adjusts an amount.

## Validation

- 45 automated tests pass.
- The cross-border sample reconciles two platform payouts to two bank rows and produces two SKU profit results with zero exceptions.
- A USD 5.00 bank difference is traced to one Amazon settlement and one bank transaction.
- USD platform and cost values convert to AED from approved dated evidence and still reconcile.
- The generated Excel pack was imported and rendered independently; its formula scan returned no formulas.

## Alpha boundaries

This release consumes exports; it does not yet connect to Amazon/Shopify APIs. Advertising spend, FBA inventory ledger, VAT/GST obligations and allocations of store-level charges without a SKU key remain outside the confident profit result. The Windows executable is not code-signed.
