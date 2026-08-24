# v0.7.0-alpha.1 release checklist

## Required and passing

- [x] Local editable installation.
- [x] CSV ingestion and optional XLSX ingestion path.
- [x] No silent low-confidence mapping.
- [x] Persistent mapping memory and schema drift.
- [x] Source-level lineage with pagination.
- [x] Sales-to-GL cause attribution.
- [x] Deterministic PVM bridge check.
- [x] Explicit company COA/currency/tolerance configuration.
- [x] Seeded truth scenarios for six reconciliation patterns.
- [x] Input/config hashes and deterministic run IDs.
- [x] Duplicate-record blocking.
- [x] Finance sign-off and tamper verification.
- [x] ISO-code validation for supported currencies and preserved FX precision.
- [x] Direct, inverse, cross and dated-fallback rate matching.
- [x] Applied-rate audit evidence and local rate-book hashing.
- [x] User-oriented month-end decision workflow.
- [x] Sample, upload and prepared-folder onboarding modes.
- [x] Tests, Docker definition, CI definition and security/privacy documentation.
- [x] Role-based CSV/XLSX/XLSM upload without filename changes.
- [x] Conservative missing/duplicate/inconsistent input blocking.
- [x] Engine-enforced prevention of blocked-run sign-off.
- [x] Self-contained readable HTML Management Pack.
- [x] Double-click Windows start and stop launchers.
- [x] First-run company policy fields without requiring JSON authoring.
- [x] Explicit block/upload/ECB foreign-currency basis selection.
- [x] ECB cache fetch with source evidence and no calculation-time network call.
- [x] Company approval gate before reference rates can be used.
- [x] Self-contained Windows x64 portable folder with no end-user Python dependency.
- [x] Double-click control window, automatic browser open and local-server stop control.
- [x] Packaged resource/data-root separation and end-to-end sample acceptance.
- [x] Persistent exception owner/status/note/evidence history.
- [x] System-only exception clearing after a clean deterministic rerun.
- [x] Finance-ready values-only Excel Management Pack.
- [x] Visible model-status and decomposed control checks.
- [x] Excel reconciliation match groups and unresolved causes.
- [x] Compact applied-FX table plus one-row-per-observation source evidence.
- [x] Excel preview lineage to source file, sheet, row, field and raw value.
- [x] Independent workbook import, formula/error scan and all-sheet visual render.

## Alpha limitations disclosed

- [x] Reconciliation is limited to documented deterministic patterns; general many-to-many optimization remains out of scope.
- [x] No FX conversion without an explicit company policy and approved basis.
- [x] ECB reference rates are opt-in cached evidence and remain informational.
- [x] Mix remains a disclosed residual component.
- [x] No authentication or multi-user workflow.
- [x] No real-enterprise compatibility claim before anonymized pilots.
- [x] Recommended evaluation ceiling documented from the current benchmark.
- [x] Unsigned-executable SmartScreen risk disclosed before public distribution.
