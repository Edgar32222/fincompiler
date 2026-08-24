# v0.4.0-alpha.1 release checklist

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

## Alpha limitations disclosed

- [x] Exact-reference reconciliation only.
- [x] No FX conversion without an explicit company policy and approved basis.
- [x] ECB reference rates are opt-in cached evidence and remain informational.
- [x] Mix remains a disclosed residual component.
- [x] No authentication or multi-user workflow.
- [x] No real-enterprise compatibility claim before anonymized pilots.
- [x] Recommended evaluation ceiling documented from the current benchmark.
