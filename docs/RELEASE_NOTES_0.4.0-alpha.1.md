# FinCompiler 0.4.0-alpha.1

This release moves FinCompiler from a technical feature inventory toward a user task: completing month-end faster without weakening Finance control.

## Delivered user outcome

A Finance Manager can load a multi-currency Sales/GL/Budget pack and see whether the files are trustworthy, whether amounts have a common basis, why systems differ, what drove performance and whether the pack is ready to publish.

## New capabilities

- Supported ISO currency validation and currency-specific minor-unit rounding.
- Full-precision exchange-rate parsing.
- Direct, inverse and EUR-triangulated rate matching.
- Explicit effective-date lookback and rate-type policy.
- Approved local rate-book hashing and applied-rate evidence.
- Explicit ECB reference-rate refresh command with local immutable cache.
- Month-end decision workflow with user-facing outcomes and next actions.
- Sample, upload and prepared-folder onboarding modes.
- Multi-currency synthetic close scenario and deterministic truth checks.

## Validation

- 22 automated tests pass.
- Multi-currency demo result: Sales AED 767.00, GL AED 767.00, difference AED 0.00.
- Local Streamlit first-run and completed-workflow views were browser checked.

## Remaining alpha boundaries

- Exact invoice-reference reconciliation remains the primary matching method.
- External reference rates are not automatically approved for accounting use.
- Exception ownership and maker-checker resolution are not yet persistent.
- Excel Management Pack export and real design-partner validation remain required for beta.
