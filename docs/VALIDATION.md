# v0.5 validation record

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
16. Exchange-rate precision is not rounded to money precision during normalization.
17. Direct, inverse and EUR-triangulated rates match deterministically within the configured date lookback.
18. Every applied rate retains provider, date, formula, raw hash and source URI evidence.
19. Missing approved rates raise `FX_RATE_REQUIRED` and become a visible month-end action.
20. Dynamics-style accounting-currency amounts can establish the GL base while transaction amounts remain preserved.
21. `demo/multicurrency_close` converts USD and CNY to AED, reconciles to zero and marks all five user tasks complete.
22. The Streamlit sample workflow was browser-checked for first-run onboarding, task visibility, FX evidence and removal of non-actionable mapping noise.
23. Multiple GL records carrying one invoice reference reconcile as a split posting without duplicate revenue.
24. A merged posting naming multiple invoice references reconciles as one deterministic group.
25. An amount-only batch is allocated only when one unique invoice subset balances; ambiguous subsets remain blocking missing/unmatched items.
26. Tax, discount and freight-sized differences receive explicit component cause codes while preserving the residual.
27. A matching invoice and GL reference in different periods raises `CROSS_PERIOD_CUTOFF` even when the total variance is zero.
28. Mixed CSV and XLSX inputs compile in one run while preserving the actual source filename in the manifest.
29. More than one explicitly named Sales, GL or Budget file is blocked rather than chosen silently.
30. Excel uploads retain their workbook extension when staged under their selected business role.
31. A blocked Management Pack cannot be signed off through the engine or web interface.
32. Every run produces a self-contained HTML Management Pack containing readiness, deterministic differences and its run ID.

## v0.5 local-product acceptance

- `Start FinCompiler.cmd` launched the local app on a clean alternate port and returned HTTP 200.
- `Stop FinCompiler.cmd` stopped only the recorded FinCompiler Python process.
- The redesigned sample workflow was browser-checked from first screen to `READY`, including the five result tabs and both report downloads.
- The full automated suite passes: 32 tests.

## Boundaries

The investigator now covers explicit split/merged postings, credit notes, bounded unique amount batches, component-sized differences and cross-period cut-off. It intentionally does not auto-allocate ambiguous subsets. General many-to-many optimization across large batches, credit-note application chains, full FX variance decomposition, returns/rebates, multi-period mix methodology and user authentication remain outside the current development build. ECB reference-rate refresh requires explicit use and is not an accounting-policy recommendation.
