# Security policy

## Supported release

Only the latest alpha is supported. FinCompiler is local-first and does not transmit files by design. It has no built-in authentication and must not be exposed directly to an untrusted network.

## Deployment rules

- Bind Streamlit to localhost unless an authenticated reverse proxy is configured.
- Keep source files, mapping memory, output packs and lineage databases outside shared folders.
- Do not commit customer files, mapping memories or generated outputs.
- Treat XLSX files as untrusted input. FinCompiler reads stored values and does not execute macros.
- Review dependencies and container images before production-like deployment.

## Reporting a vulnerability

Do not open a public issue containing financial data, credentials or exploitable details. Contact the repository owner privately. Include the affected version, reproduction steps using synthetic data and expected impact.

