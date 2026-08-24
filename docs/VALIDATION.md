# v0.2 validation record

## Acceptance scenarios

1. Unknown `其他费用2` remains unmapped and raises review; no value is folded into another amount.
2. A confirmed mapping survives process restart in `mappings/memory.json`.
3. A new header changes the fingerprint and raises `SCHEMA_DRIFT`.
4. Sales and revenue GL differ by AED 2,706; the investigator attributes it to `INV-1003` as `AMOUNT_MISMATCH`.
5. Sales totals expose file/sheet/row/field/raw-value lineage.
6. Budget-vs-Actual variance equals volume + price + mix/residual exactly to two decimals; every segment includes its source records and formula chain.
7. Output readiness is blocked while the reconciliation variance exists.
8. Xero-style repeated invoice headers and multiple lines reconcile against one aggregated GL reference.
9. Dynamics debit/credit columns derive revenue as `credit - debit` and expose both cells in the calculation lineage.
10. A locale-ambiguous date such as `01/02/2026` raises `TYPE_VALIDATION_FAILED` rather than being guessed.
11. Seeded generator scenario `7301` reproduces split posting, amount mismatch, missing GL, unmatched GL and credit note truth without false positives for valid split/credit transactions.
12. Initial 5,000-invoice scale baseline is recorded in `DATA_STRATEGY.md`; it identifies embedded lineage output size as the limiting factor.
13. Indexed-lineage rerun reduces Management Pack from 28.98 MB to 0.08 MB and stores full trace data in a 16.13 MB paginated SQLite index.
14. Every run emits SHA-256 source hashes, configuration hash, engine version and a content-deterministic run ID.
15. Identical canonical Sales/GL records block readiness with `POTENTIAL_DUPLICATE_RECORD`.

## Boundaries

The investigator currently uses invoice-reference exact matching. Credit-note allocation, fuzzy bank/reference matching, FX decomposition, returns/rebates, multi-period mix methodology and user authentication remain outside the current development build.
