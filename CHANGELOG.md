# Changelog

## 0.6.0-alpha.1 — 2026-08-24

- Added first-run company policy setup for entity name, base currency, GL revenue accounts and reconciliation tolerance.
- Added an explicit foreign-currency basis choice: block, upload a company-approved book, or fetch an ECB reference cache.
- Added a 90-day ECB download workflow with daily-feed fallback that retains the failure reason.
- Required a visible company-policy approval checkbox before cached ECB reference rates can enter a run.
- Preserved rate provider, source URL, fetch time, raw hash, effective date and matching formula in the run evidence.
- Expanded automated coverage to 35 tests and browser-validated a live 1,885-observation ECB cache.

## 0.5.0-alpha.1 — 2026-08-24

- Rebuilt the local web workflow around choose, review, investigate, audit and sign-off steps.
- Added role-based CSV/XLSX/XLSM upload staging without corrupting Excel files or requiring source filenames to be changed.
- Added conservative input discovery, clear missing/duplicate file errors, empty-table checks and inconsistent-sheet blocking.
- Prevented blocked runs from being signed off in both the UI and engine.
- Added a self-contained readable HTML Management Pack alongside the JSON and SQLite evidence outputs.
- Added double-click Windows start/stop launchers with first-run setup and hidden local server management.
- Expanded automated coverage from 27 to 32 tests and browser-checked the redesigned sample workflow.

## 0.4.0-alpha.1 — 2026-08-24

- Reframed the application around five month-end Finance user questions.
- Added deterministic currency validation, direct/inverse/cross-rate matching and dated fallback.
- Added approved local rate books, rate-source hashing and record-level applied-rate evidence.
- Added explicit ECB reference-rate cache refresh without calculation-time network dependence.
- Added a multi-currency USD/CNY/AED close scenario that reconciles to zero.
- Added a month-end action workflow and simplified Streamlit onboarding, upload and mapping-review views.
- Added a durable user-problem product strategy report and pilot success measures.

## 0.3.0-alpha.1 — 2026-08-24

- Added deterministic Xero, QuickBooks, Business Central and Dynamics source profiles.
- Added persistent mapping memory and schema-drift detection.
- Added source lineage indexed by stable IDs in local SQLite.
- Added invoice-level Sales-to-GL reconciliation investigation.
- Added Decimal-based Budget-vs-Actual volume/price/residual bridge.
- Added explicit company revenue-account, currency and tolerance configuration.
- Added seeded synthetic scenarios with machine-readable truth manifests.
- Added source/config hashes, deterministic run IDs and duplicate detection.
- Added Finance sign-off, artifact integrity verification and overwrite protection.

This is an alpha release for local evaluation with synthetic or anonymized data. It is not a substitute for financial review or an accounting system of record.
