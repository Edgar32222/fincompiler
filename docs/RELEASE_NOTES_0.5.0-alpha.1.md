# FinCompiler v0.5.0-alpha.1

This release turns the deterministic v0.4 engine into a private-pilot product that a Finance user can start and navigate locally without learning the CLI.

## What a user can do

- Double-click the Windows launcher and open FinCompiler in a browser.
- Try a complete multi-currency sample or upload Sales, GL and Budget as CSV/XLSX/XLSM.
- Review uncertain mappings without silent field coercion.
- See blocking controls as an action plan rather than raw engine output.
- Investigate Sales-vs-GL causes, inspect the deterministic PVM bridge and trace totals to source rows.
- Download both machine-readable JSON and a readable, printable HTML Management Pack.
- Sign off only a `READY` run and later verify that its evidence was not changed.

## Control changes

- Excel files retain their real type during upload staging.
- Missing, empty, duplicated or structurally inconsistent source tables fail with explicit guidance.
- Prepared folders never choose silently when both CSV and Excel candidates exist.
- Blocked runs cannot be signed off through either the UI or the engine.

## Validation

- 32 automated tests pass.
- CLI multi-currency sample returns `READY` with zero Sales/GL variance.
- Windows start/stop launchers were exercised on a separate local port.
- The redesigned sample workflow was checked in a browser.

This remains a private alpha for synthetic or anonymized pilot data. It is not an accounting system of record and does not replace Finance review.
