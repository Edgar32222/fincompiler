# FinCompiler v0.6.0-alpha.1

> **Alpha release:** suitable for local evaluation with synthetic or anonymized data. It is not an accounting system of record and does not replace Finance review.

FinCompiler helps a Finance Manager answer five month-end questions: can I trust the files, are amounts comparable, why do Sales and GL differ, what drove performance, and can I publish the pack? It is local-first: source data, mapping memory, approved rates and outputs stay on the machine.

## Trust rules

- Unknown or ambiguous fields are placed in `MAPPING_REVIEW_REQUIRED`; they are never silently coerced.
- Confirmed mappings persist in a local JSON memory. A changed header set raises `SCHEMA_DRIFT`.
- Every aggregate carries file, sheet, row, source field and raw value lineage.
- Recognized Xero, QuickBooks, Business Central and Dynamics field sets use explicit source profiles backed by public vendor schemas.
- Dates, currencies and numeric values are type-checked; locale-ambiguous dates are blocked rather than guessed.
- Sales-to-GL reconciliation supports exact references, split postings, explicit merged batches, uniquely identifiable amount batches, credit notes, component differences and cross-period cut-off. Ambiguous allocations remain blocking exceptions.
- Budget-vs-Actual PVM uses Python `Decimal`. An LLM may explain the resulting JSON, but never calculates or adjusts amounts.
- A blocking reconciliation or unresolved mapping prevents output readiness.
- Foreign-currency records use an explicit dated rate policy. Direct, inverse and cross-rate formulas retain provider, effective date, source and raw-response hash evidence.
- ERP accounting-currency amounts can be used as posted accounting evidence when company policy explicitly allows it.

## Start on Windows without using a terminal

1. Keep the FinCompiler folder on your local drive.
2. Double-click `Start FinCompiler.cmd`.
3. On first use, FinCompiler creates its private Python environment, installs the required packages and runs its validation tests.
4. Your browser opens at `http://127.0.0.1:8511`. Choose the sample company or upload one Sales, one GL and one Budget file.
5. Double-click `Stop FinCompiler.cmd` when you finish.

CSV, XLSX and XLSM input tables are supported. Uploads are selected by business role, so original filenames do not need to be changed. Prepared local folders use one explicitly named `sales`, `gl` and `budget` file; if both CSV and Excel versions exist, FinCompiler blocks the run instead of choosing silently.

The result page provides an action plan, Sales-vs-GL investigation, deterministic Budget-vs-Actual bridge, applied FX evidence, paginated source trace, controlled sign-off and downloadable JSON plus a self-contained readable HTML Management Pack.

When uploading files without a prepared company-policy JSON, the UI now collects the entity name, accounting base currency, explicit GL revenue accounts and reconciliation tolerance. Foreign-currency rows remain blocked unless the user uploads a company-approved rate book or explicitly fetches, reviews and approves an ECB reference-rate cache for that analytical run. Fetching rates alone never approves or applies them.

## Command-line setup (advanced)

The simplest path is `powershell -ExecutionPolicy Bypass -File scripts\setup.ps1`. It detects the standard Python launcher, `python`, or the Codex bundled Python runtime.

```powershell
py -m venv .venv
.venv\Scripts\pip install -e .[dev,excel,web]
.venv\Scripts\pytest
.venv\Scripts\fincompiler run demo\nova_appliances --output output
.venv\Scripts\fincompiler-web
```

The demo deliberately contains an AED 2,706 difference on `INV-1003`, plus an unmapped Chinese OPEX field in `opex_dirty.csv` for review scenarios.

`demo/multicurrency_close` demonstrates a completed user workflow: USD direct conversion, CNY-to-AED conversion through EUR, previous-effective-date fallback, use of posted accounting-currency GL amounts, zero Sales/GL variance and stored rate evidence.

Refresh an ECB reference-rate cache explicitly when company policy permits it:

```powershell
fincompiler refresh-ecb-rates .fincompiler\rates\ecb-reference.csv --history 90d
```

ECB rates are informational reference rates. Downloading them never silently changes an existing run or makes them an approved accounting policy.

See [Currency and exchange-rate policy](docs/FX_POLICY.md) for quote conventions, matching order, evidence fields and blocking behavior.

`demo/realistic_multisystem` adds Xero-style multi-line invoices and a Dynamics-style general journal with separate debit/credit and reporting-currency fields. Its values are synthetic; the field shapes are documented in [docs/FIELD_EVIDENCE.md](docs/FIELD_EVIDENCE.md).

## Mapping confirmation

Review a proposal, then explicitly save a mapping:

```powershell
fincompiler confirm-mapping sales "Invoice No" invoice_id --fields "Invoice No" Date Customer SKU Qty "Unit Price" "Net Sales" Currency
```

Re-running the same schema uses persistent memory. New, removed or renamed columns raise schema drift.

## Outputs

`management_pack.json` contains a user-oriented month-end workflow, applied FX evidence, mapping proposals, exceptions, output readiness, source-backed reconciliation match groups/attribution and the balanced PVM bridge. `management_pack.html` is a self-contained readable review pack that can be opened or printed without FinCompiler. No source data leaves the machine.

Full lineage is stored in an indexed `lineage-<run_id>.sqlite` file. Management Pack totals contain a stable lineage ID, input count and small preview. Retrieve a page without loading the entire history:

```powershell
fincompiler trace output\lineage-<run_id>.sqlite "<run_id>:reconciliation:sales" --limit 25 --offset 0
```

Each run also writes `run_manifest.json` with SHA-256 hashes for Sales, GL and Budget, a configuration hash, engine version and deterministic run ID. Exact duplicate canonical Sales/GL records block output readiness.

## Finance sign-off

After resolving exceptions and reviewing the pack:

```powershell
fincompiler sign-off output\demo-run --reviewer "Finance Manager" --notes "Reviewed against July close workbook"
fincompiler verify-run output\demo-run
```

A signed run cannot be overwritten. Any later artifact change causes verification to fail.

## Current capacity boundary

The recorded baseline covers 9,994 Sales lines plus 5,002 GL lines. Use the alpha for evaluation packs up to roughly 25,000 combined source rows; larger runs may work but are not yet a release claim. See [docs/DATA_STRATEGY.md](docs/DATA_STRATEGY.md).

For evidence behind vendor-specific fields, see [docs/FIELD_EVIDENCE.md](docs/FIELD_EVIDENCE.md). For structured finance-user validation, see [docs/PILOT_GUIDE.md](docs/PILOT_GUIDE.md).

The product direction and pilot success measures are maintained in the portable [user-problem strategy report](docs/product_strategy/report.html).

Market validation is now managed as a measured product workflow. See the [design-partner playbook](docs/market_validation/PLAYBOOK.md), [channel setup and privacy checklist](docs/market_validation/CHANNEL_SETUP.md), [prepared outreach drafts](docs/market_validation/OUTREACH_DRAFTS.md), [private-pilot data terms](docs/market_validation/PILOT_DATA_TERMS.md), and the portable [market wedge report](docs/market_validation/report.html). No outreach draft is authorization to post or message; every external action requires founder approval immediately before sending.

When real enterprise exports are not available, use the seeded scenario generator and truth manifest described in [docs/DATA_STRATEGY.md](docs/DATA_STRATEGY.md). Company-specific revenue accounts, base currency and reconciliation tolerance belong in `company_config.json`; see [demo/company_config.example.json](demo/company_config.example.json).
