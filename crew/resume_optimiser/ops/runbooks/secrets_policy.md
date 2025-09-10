# Secrets Policy (Week 1)

- Do not commit secrets. Never add `.env` or keys/tokens to Git.
- Local development:
  - Copy `.env.example` to `.env` and fill only local values.
  - Keep `.env` out of Git; it is ignored by `.gitignore`.
- Cloud environments (dev/staging/prod):
  - Store secrets in Azure Key Vault; access via Managed Identity or CSI driver.
  - Do not inject secrets via plain env vars from CI; fetch from Key Vault at runtime.
- Rotation: rotate credentials at least quarterly and on any suspected leak.
- Logging: do not log PII or secrets. Mask tokens/keys/IDs in all logs.
- Reviews: PR reviewers must check for accidental secret leaks before merging.

