# Privacy and data handling

FinCompiler processes files locally. The core engine has no network calls, telemetry or LLM dependency. Streamlit usage statistics are disabled in the included configuration.

Generated artifacts can still contain sensitive information:

- source values and customer/product identifiers;
- local source paths;
- mapping decisions and financial exceptions;
- reviewer names and sign-off notes.

Users are responsible for filesystem access controls, retention and secure deletion. Share only anonymized packs. A signed pack proves local artifact integrity; it does not provide encryption, identity assurance or regulatory compliance.

