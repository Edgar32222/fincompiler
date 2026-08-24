# FinCompiler v0.6.0-alpha.1

This release closes the first-run company-policy and exchange-rate gap in the local Finance workflow.

## Company setup in the UI

Users no longer need to author JSON for a first evaluation. The upload page collects:

- company or legal-entity name;
- accounting base currency;
- explicit GL revenue account names or codes;
- Sales-to-GL reconciliation tolerance.

The generated policy is stored locally and hashed into the deterministic run manifest.

## Controlled rate retrieval

For foreign-currency records, the user must choose one of three policies:

1. block records that do not already have an accounting-currency basis;
2. use an uploaded company-approved rate book;
3. fetch an ECB reference cache, review the evidence and explicitly approve it for the analytical run.

Downloading never equals approval. FinCompiler records the provider, source URL, retrieval time, raw-response hash, rate date, direct/inverse/cross formula and observations used. A 90-day feed timeout falls back to the daily feed with a visible warning; historical rows without a compliant date remain blocked.

## Validation

- 35 automated tests pass.
- The live UI cached 1,885 ECB 90-day observations and displayed the approval gate.
- v0.5 CSV/XLSX upload, readable Management Pack, Finance sign-off and Windows launcher acceptance remain passing.

This remains a private alpha for synthetic or anonymized pilot data. Reference-rate suitability is a company accounting-policy decision, not a FinCompiler recommendation.
