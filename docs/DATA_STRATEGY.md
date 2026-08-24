# Development strategy without customer data

FinCompiler can reach private-alpha quality before receiving enterprise files, but it cannot claim broad compatibility until real, anonymized exports are tested. Development therefore uses an evidence ladder.

## Evidence ladder

1. **Vendor schema contracts** — source profiles are derived from public vendor documentation, with exact field signatures and canonical targets under test.
2. **Seeded synthetic scenarios** — realistic monthly files are generated from a recorded seed. Every injected anomaly is written to `truth_manifest.json` before the pipeline runs.
3. **Golden regression packs** — representative scenario folders are retained with expected outputs for mapping, lineage, reconciliation and PVM.
4. **Schema-only contributions** — prospective users may initially share headers, data types and redacted example values rather than transactions.
5. **Private pilots** — anonymized full exports are tested locally under the protocol in `PILOT_GUIDE.md`.

## v0.3 work sequence

### Gate A — deterministic trust harness

- Company-specific revenue accounts, base currency and tolerance are explicit configuration.
- Perfect, split-posting, amount-mismatch, missing-GL, unmatched-GL and credit-note scenarios have machine-readable truth.
- Foreign-currency files without a common conversion basis are blocked.
- A fixed seed reproduces the same source files and expected causes.

### Gate B — compatibility breadth

- Golden packs for Xero, QuickBooks, Business Central and Dynamics.
- Credit-note and discount/subtotal line semantics per source system.
- AR open-item and inventory movement canonical schemas.
- At least 100 source-profile contract tests.

### Gate C — operational robustness

- 100,000-line benchmark with bounded memory and a recorded runtime.
- Duplicate-file and duplicate-transaction detection.
- Period/entity boundary validation.
- Immutable run manifest with source hashes, configuration hash and engine version.

## Initial scale baseline — 2026-08-24

Seed `20260824`, 5,000 invoices, 9,994 sales lines and 5,002 GL lines:

| Measurement | Result |
| --- | ---: |
| Synthetic generation | 0.245 seconds |
| Full compile and JSON output | 18.536 seconds |
| Management pack size | 28.98 MB |

The main constraint is not Decimal finance calculation; it is embedding every source reference inside one management-pack JSON. Before claiming 100,000-line readiness, lineage must move to a separate indexed store with paginated retrieval. The management pack should retain counts, previews and stable lineage IDs. This is the next P0 architecture task.

Implementation status: the indexed SQLite lineage store, stable lineage IDs and paginated CLI/UI trace are implemented.

### Indexed-lineage rerun

The same 5,000-invoice scenario produced:

| Measurement | Before | Indexed lineage |
| --- | ---: | ---: |
| Full compile | 18.536 seconds | 18.689 seconds |
| Management Pack | 28.98 MB | 0.08 MB |
| Separate lineage store | none | 16.13 MB |

The user-facing pack is 99% smaller and total stored output is about 44% smaller. Runtime is effectively unchanged, so the next performance task is bulk/streaming ingestion and batched lineage writes rather than further JSON formatting work.

### Gate D — pilot readiness

- One-click local setup and sample run.
- Mapping review export/import for finance sign-off.
- Exception ownership, notes and resolution state.
- Re-runs never overwrite a previously signed-off pack.

## Claims we will not make yet

- “Works with every ERP.”
- “Automatically fixes reconciliations.”
- “AI replaces finance review.”
- “Mix is fully explained” while it remains a residual balancing component.

## Synthetic generator

```powershell
fincompiler generate-demo demo\generated --seed 7301 --invoices 100 `
  --anomalies split_posting amount_mismatch missing_gl unmatched_gl credit_note

fincompiler run demo\generated --output output\generated
```

The generator creates Xero-shaped invoice lines, Dynamics-shaped journal lines, a generic budget, `company_config.json` and `truth_manifest.json`. The manifest is the expected truth; the finance engine must rediscover it without reading the manifest.
