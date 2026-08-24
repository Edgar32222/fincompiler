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
   ├── Sales ↔ GL reconciliation investigator
   └── Budget ↔ Actual Decimal PVM bridge
              │
              ▼
management_pack.json + indexed lineage SQLite
              │
              ▼
draft → Finance sign-off → immutable hash verification
```

The finance engine owns every numeric result. An LLM may be added later as a read-only explanation layer consuming signed deterministic outputs; it must never map uncertain fields, change amounts or clear exceptions.

## Trust boundaries

- Source profile recognition is deterministic and signature-based.
- Exact documented aliases may be proposed automatically; unknown fields remain unmapped.
- Derived values retain formulas and all source cells.
- Reconciliation compares only explicitly configured revenue accounts on a common currency basis.
- Signed artifacts are content-hashed and cannot be overwritten by the pipeline.

