# FinCompiler 0.3.0-alpha.1

FinCompiler is ready for public technical-preview release and design-partner evaluation using synthetic or anonymized data.

## What this release proves

- Messy, vendor-shaped Sales, GL and Budget files can be mapped into a canonical model without silently accepting uncertain fields.
- Every reported total can be traced to original source cells through a paginated local index.
- Sales-to-GL exceptions can be attributed to invoice references and classified as missing, unmatched or amount mismatch.
- Budget-vs-Actual volume/price/residual calculations balance exactly using Decimal arithmetic.
- Signed runs are content-hashed, tamper-evident and protected from overwrite.
- Seeded synthetic scenarios provide repeatable truth without customer data.

## Validation evidence

- 17 automated tests pass, including CSV, real XLSX, mapping memory, schema drift, reconciliation causes, PVM balance, currency blocking, duplicate detection, lineage pagination, sign-off and tamper detection.
- Wheel and source distribution build successfully.
- A clean environment installed only the wheel and completed generate → compile → READY → sign-off → verify.
- The packaged `fincompiler-web` command started successfully and returned HTTP 200.
- A 5,000-invoice baseline is documented. The alpha recommendation is no more than roughly 25,000 combined source rows.

## Known limitations

- This is not an accounting system of record.
- Reconciliation uses exact references; fuzzy matching and credit-note allocation across invoices are not included.
- Foreign currencies require an explicit common basis; the engine will not invent FX rates.
- Mix is currently a disclosed residual balancing component.
- There is no authentication or multi-user authorization.
- Real ERP compatibility remains unproven until anonymized design-partner pilots.
- Docker files are provided but were not executed in the current Windows environment because Docker was unavailable.

## Recommended launch scope

Publish as an open technical preview, recruit 3–5 Finance design partners, and ask them first for schema-only samples or anonymized exports. Do not market this alpha as autonomous close software or production-ready financial reporting.

