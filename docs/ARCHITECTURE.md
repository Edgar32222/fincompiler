# Architecture

```text
CSV/XLSX
   │
   ▼
ingestion ── source refs (file/sheet/row/field/raw value)
   │
   ▼
profile detection ── deterministic mapping proposals
   │
   ▼
mapping review + persistent memory + schema drift
   │
   ▼
canonical records ── type validation ── duplicate checks
   │
   ├── approved FX policy + immutable rate evidence
   ├── Sales ↔ GL reconciliation investigator
   └── Budget ↔ Actual Decimal PVM bridge
              │
              ▼
user close workflow + persistent exception handling + indexed lineage SQLite
              │
              ▼
Excel/HTML/JSON Management Pack → Finance sign-off → immutable hash verification
```

The finance engine owns every numeric result. An LLM may be added later as a read-only explanation layer consuming signed deterministic outputs; it must never map uncertain fields, change amounts or clear exceptions.

## Trust boundaries

- Source profile recognition is deterministic and signature-based.
- Exact documented aliases may be proposed automatically; unknown fields remain unmapped.
- Derived values retain formulas and all source cells.
- Reconciliation compares only explicitly configured revenue accounts on a common currency basis. It applies explicit references before deterministic grouped matching and refuses ambiguous amount-only allocations.
- FX matching is deterministic by currency pair, rate type, requested date, lookback policy and triangulation currency; missing evidence blocks the run.
- Online reference-rate refresh is an explicit cache operation, never a hidden calculation-time network dependency.
- Signed artifacts are content-hashed and cannot be overwritten by the pipeline.
