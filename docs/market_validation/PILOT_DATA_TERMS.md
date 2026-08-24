# FinCompiler private-pilot data terms

Draft for validation use; this is not legal advice and should be reviewed before a paid or production pilot.

## Scope

The pilot covers one named recurring Finance reconciliation for two close cycles. FinCompiler is an evaluation tool, not an accounting system of record, tax service, audit opinion or substitute for Finance approval.

## Data minimization

- The discovery conversation requires no financial files.
- The pilot should use synthetic data first, then anonymized headers and the smallest representative row set capable of reproducing the workflow.
- Remove names, addresses, bank details, tax identifiers, payroll/personnel data, free-text notes and other personal or commercially identifying fields unless they are strictly required and explicitly approved.
- Record trusted control totals separately so the deterministic output can be verified.

## Local processing

- Source files, mapping memory, approved rate evidence, lineage databases and outputs remain on the pilot machine or another location expressly agreed in writing.
- Source financial data is not uploaded to an LLM, analytics service, public repository or hosted FinCompiler service.
- An LLM, if enabled later, may explain already-calculated and deliberately redacted deterministic outputs; it must not calculate, map or adjust amounts.

## Access and retention

Before the pilot starts, record:

- the local storage location;
- the people allowed to access it;
- the two pilot periods;
- the deletion or return date;
- whether anonymized failure cases may be retained as regression fixtures;
- the Finance reviewer authorized to accept results.

Default to deletion at the end of the agreed validation window. Do not retain a sample as a product fixture without separate written permission.

## Control rules

- Uncertain or low-confidence mappings stop for explicit review.
- Missing currency policy or exchange-rate evidence blocks comparable totals.
- Duplicate records and unresolved reconciliation differences remain visible.
- FinCompiler does not create silent balancing adjustments.
- Every material output must retain source and calculation lineage.
- The Finance reviewer remains responsible for deciding whether the result can be used.

## Incident handling

If unexpected personal, payroll, credential, banking or other sensitive data is found, stop processing, isolate the file, notify the pilot owner and agree deletion or a safer replacement before continuing.

## Pilot exit

Either party may stop the pilot. On exit, provide the user with their local outputs and delete or return any copy outside the agreed pilot machine according to the recorded retention decision.
