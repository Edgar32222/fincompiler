# FinCompiler v0.7.0-alpha.1

This release turns the deterministic run output into a more complete Finance operating workflow: the result can be assigned, investigated, rerun and reviewed in Excel without weakening the trust gate.

## Finance-ready Excel Management Pack

Every run now produces `management_pack.xlsx` as the primary human review deliverable. Its 11 sheets cover:

- summary and publish readiness;
- decomposed control checks with actual, expected, tolerance, status and fix location;
- month-end action plan;
- persistent exception handling;
- unresolved Sales-vs-GL causes and successfully matched record groups;
- deterministic Budget-vs-Actual/PVM;
- compact applied exchange rates and separate one-row-per-observation source evidence;
- calculation/source lineage to local file, worksheet, row, source field and raw value;
- source-file integrity hashes and canonical mapping decisions.

The workbook is values-only. Amounts are calculated by the Decimal-based Finance engine before export; Excel formulas cannot recalculate or adjust them.

## Persistent exception workflow

Each deterministic exception receives a stable local ID. Finance can record an owner, working status, note, evidence reference and updater history. A user can move an item through investigation and prepare it for rerun, but cannot mark it cleared. Only a subsequent deterministic run where the control no longer fails records `CLEARED_BY_RERUN`.

## Guided first run

The local web interface now recommends the prepared sample, states its expected result and labels the first action `Run sample check`. Upload mode explains the minimum Sales, General Ledger and Budget exports before the user selects files. Excel is the first download option after a run.

## Validation

- 39 automated tests pass.
- The multicurrency sample completes 5/5 controls, returns `READY` and reconciles Sales to GL at 0.00.
- An independent spreadsheet engine imported the Management Pack, found no formulas or spreadsheet error values and rendered all 11 sheets for visual inspection.
- The blocked Nova demo still exposes the deliberate AED 2,706 difference and cannot be signed off.

This remains an alpha for synthetic, anonymized or explicitly approved pilot data. The Windows executable is not code-signed, multi-user access control is not implemented and real-enterprise compatibility claims still require design-partner exports.
