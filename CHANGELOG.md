# Changelog

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
