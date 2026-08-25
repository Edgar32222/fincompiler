# FinCompiler v0.8.0-alpha.1

> **Alpha release:** suitable for local evaluation with synthetic or anonymized data. It is not an accounting system of record and does not replace Finance review.

FinCompiler is a local-first cash and profit compiler for finance teams and cross-border sellers. It now has two workflows:

- **Cross-border cash & true profit:** Amazon Settlement V2 / Shopify orders and payouts → bank receipt matching → landed-cost SKU profit.
- **Finance month-end:** Sales detail → GL revenue reconciliation → deterministic Budget-vs-Actual/PVM.

Source data, mapping memory, approved rate evidence and outputs stay on the machine.

## Cross-border seller quick start

Open the Windows app and keep the default **跨境卖家真实利润** mode. Run the built-in HarborLight sample first, or upload:

- `Amazon Settlement V2` and/or `Shopify payout CSV`;
- a bank statement with transaction ID, value date, reference, amount and currency;
- Shopify order CSV for order/SKU economics;
- an effective-dated SKU landed-cost table for purchase, freight, duty and other unit cost.

The result identifies each paid platform payout, the specific bank row used, the matching method, the exact residual and the reason when it does not balance. SKU profit is `revenue - platform fees - landed COGS`; missing cost and unattributable fees block a confident profit conclusion.

Foreign-currency records never use a live rate silently. A user can upload an approved dated rate book or fetch an ECB reference-rate cache; provider, effective date, formula, source URL and raw-response hash are retained, and an explicit approval is required before an ECB cache enters the run.

For a source checkout, the same workflow is available as:

```powershell
fincompiler run-commerce demo\cross_border_seller --output output\cross-border-demo
```

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
- Exception handling is persisted locally with owner, status, note, evidence reference and audit history. A user can prepare an item for rerun but cannot mark a failed control as cleared.
- Every run produces a Finance-ready values-only Excel Management Pack with visible control checks, matched and unmatched reconciliation records, PVM, FX source evidence, mapping decisions and file/sheet/row/field lineage.

## Start on Windows — no Python required

1. Download the latest FinCompiler Windows portable ZIP and extract the whole ZIP to a local folder.
2. Double-click `FinCompiler.exe`. Keep the small FinCompiler control window open while you work.
3. Your browser opens automatically. Choose the sample company or upload one Sales, one GL and one Budget file.
4. Click **Stop and close** in the control window when you finish.

The portable build includes its own runtime and dependencies. It does not install Python, does not require administrator access and binds only to `127.0.0.1`. User files, mapping memory, approved rate evidence and outputs are written under `FinCompiler Data` beside the executable; bundled demo resources remain separate.

CSV, XLSX and XLSM input tables are supported. Uploads are selected by business role, so original filenames do not need to be changed. Prepared local folders use one explicitly named `sales`, `gl` and `budget` file; if both CSV and Excel versions exist, FinCompiler blocks the run instead of choosing silently.

The result page provides an action plan, persistent exception ownership, Sales-vs-GL investigation, deterministic Budget-vs-Actual bridge, applied FX evidence, paginated source trace, controlled sign-off and downloadable Excel, JSON plus a self-contained readable HTML Management Pack.

When uploading files without a prepared company-policy JSON, the UI now collects the entity name, accounting base currency, explicit GL revenue accounts and reconciliation tolerance. Foreign-currency rows remain blocked unless the user uploads a company-approved rate book or explicitly fetches, reviews and approves an ECB reference-rate cache for that analytical run. Fetching rates alone never approves or applies them.

## Command-line setup (advanced)

Source contributors can use `powershell -ExecutionPolicy Bypass -File scripts\setup.ps1`. This Python-based route is no longer the default end-user startup method.

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

Build the self-contained Windows folder from a prepared contributor environment with `scripts\build_windows_portable.ps1`. The resulting `dist-windows\FinCompiler` folder must be distributed intact, not as the executable alone.

See [Currency and exchange-rate policy](docs/FX_POLICY.md) for quote conventions, matching order, evidence fields and blocking behavior.

`demo/realistic_multisystem` adds Xero-style multi-line invoices and a Dynamics-style general journal with separate debit/credit and reporting-currency fields. Its values are synthetic; the field shapes are documented in [docs/FIELD_EVIDENCE.md](docs/FIELD_EVIDENCE.md).

## Mapping confirmation

Review a proposal, then explicitly save a mapping:

```powershell
fincompiler confirm-mapping sales "Invoice No" invoice_id --fields "Invoice No" Date Customer SKU Qty "Unit Price" "Net Sales" Currency
```

Re-running the same schema uses persistent memory. New, removed or renamed columns raise schema drift.

## Outputs

`management_pack.xlsx` is the primary Finance review pack. It contains a visible control-check sheet, action plan, persistent exception register, matched and unmatched Sales-vs-GL records, deterministic Budget-vs-Actual/PVM, applied rate evidence, rate-source hashes, mapping decisions and preview lineage down to file, sheet, row, field and raw value. Amounts are values produced by the deterministic engine; the workbook contains no formulas that can silently change them.

`management_pack.json` contains the complete machine-readable workflow, while `management_pack.html` is a self-contained readable review pack that can be opened or printed without FinCompiler. `exception_workflow.json` preserves local owner/status/note/evidence history across reruns. No source data leaves the machine.

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
