# Cross-border cash and true-profit workflow

## User problem

Small cross-border teams often have platform sales, settlement deductions, payment-provider payouts, bank receipts and SKU costs in separate exports. A dashboard can repeat those totals without proving whether the cash arrived or whether a profitable-looking SKU remains profitable after fees, refunds and landed cost.

FinCompiler builds this evidence chain locally:

`platform activity → paid payout → one bank receipt → deterministic SKU economics`

## Matching order

1. Use an explicit settlement/payout reference when exactly one bank row contains it.
2. Otherwise use a unique equal amount within the configured date window.
3. If there is only one date-window candidate, show it with the exact difference and mark `BANK_OR_PROCESSOR_DEDUCTION`.
4. Refuse to choose when multiple bank rows remain possible.

The engine never creates an adjustment entry or changes source values.

## Profit calculation

- Shopify order totals exclude tax and are allocated across lines by `quantity × unit price` weights. Order-linked refund gross and fees are allocated by the same weights.
- Amazon settlement activity uses an explicit category allowlist. Principal, Shipping and GiftWrap enter revenue; tax is excluded; ItemFees and ServiceFees enter platform fees. Unknown categories remain visible and block a confident SKU result.
- Landed unit cost is the latest effective record on or before the activity date: purchase + freight + duty + other unit cost.
- `profit = revenue - platform fees - landed COGS`.

Every output retains the source file, worksheet/CSV marker, row, original field and raw value. JSON is the complete evidence artifact; Excel is a values-only review pack.

## Current boundary

This alpha directly supports Amazon Settlement V2 and Shopify order/payout CSV shapes. It does not yet call Amazon or Shopify APIs, import advertising/FBA inventory ledger reports, model VAT/GST obligations, or allocate store-level fees to SKU without an explicit key. These boundaries are intentional: missing evidence stays visible instead of becoming an estimated profit.
