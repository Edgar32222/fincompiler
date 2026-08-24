# Finance user pilot guide

The next product milestone is evidence that FinCompiler reduces month-end work without weakening control. Do not ask pilots whether they “like AI.” Ask them to complete their normal reconciliation and reporting work.

## Ideal pilot profile

- Finance Manager, Controller, FP&A Manager or senior management accountant.
- Monthly sales subledger, GL and budget exports are available in CSV/XLSX.
- At least one recurring reconciliation currently uses Excel lookups, Power Query or manual filtering.
- Data can remain local and can be anonymized before the session.

## Three-session protocol

### Session 1 — first month

1. User imports sales, GL and budget files.
2. User reviews every proposed mapping and explains rejected fields.
3. Record setup time, number of confirmations, unknown fields and type failures.
4. Compare FinCompiler totals with the user's signed-off workbook.

Success gate: every difference is explained; no silent mapping; total setup under 45 minutes for one entity.

### Session 2 — schema drift

1. Import the following month's exports.
2. Introduce only changes that actually occurred in the source system.
3. Observe mapping reuse, drift detection and false alarms.

Success gate: at least 80% of previously confirmed mappings are reused, while every material changed field is surfaced.

### Session 3 — investigation value

1. Select one known Sales-to-GL exception.
2. Ask the user to investigate with their existing process and with FinCompiler.
3. Capture time-to-cause, records inspected, confidence and whether the proposed reason was actionable.

Success gate: median investigation time falls by at least 50%, with zero unexplained adjustments created by the product.

## Metrics to retain locally

| Metric | Definition |
| --- | --- |
| Mapping precision | Confirmed correct proposals / all deterministic proposals |
| Memory reuse | Reused confirmed mappings / eligible prior mappings |
| Drift recall | Material schema changes surfaced / material schema changes present |
| Reconciliation attribution | Absolute variance assigned to concrete causes / total absolute variance |
| Time to cause | Minutes from opening files to identifying responsible records |
| Bridge integrity | PVM bridges with exact zero deterministic check / bridges generated |
| Trust violations | Silent field coercions or unexplained auto-adjustments; target is always zero |

## Data handling

Use synthetic or anonymized copies during early pilots. Do not upload pilot files to issue trackers. Store mapping memories per company/entity and exclude them from source control. Record only field shapes, failure categories and aggregate timing metrics in product research notes.

