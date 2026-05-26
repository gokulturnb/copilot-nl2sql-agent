# Security & Compliance Guardrails

## Purpose

This document defines the security and compliance rules for the Copilot NL2SQL Finance Agent.

The goal is to protect secrets, financial data, customer/tenant information, AI prompts, SQL generation logic, and deployment workflows.

---

## Project Security Context

This project uses:

- Copilot Studio as the front-end chat interface
- Azure Function as the backend API
- Python backend logic in `main.py`
- Finance context files for SQL generation
- Microsoft Fabric Warehouse as the data source
- OpenAI / Azure OpenAI for question understanding, SQL generation, and summarization

Because the system can generate SQL and access finance data, all changes must be reviewed carefully.

---

## Secrets Management Rules

The following files must never be committed to GitHub:

- `.env`
- `local.settings.json`
- database connection strings
- Azure OpenAI keys
- OpenAI API keys
- Fabric credentials
- service principal secrets
- access tokens
- refresh tokens

Secrets must be stored in approved secure locations only.

---

## Approved Secret Storage

| Environment | Recommended Secret Storage |
|---|---|
| Local development | Local `.env` file only |
| Azure Function runtime | Azure App Settings or Azure Key Vault |
| Production | Azure Key Vault + Managed Identity |
| GitHub Actions | GitHub Secrets or OIDC-based authentication |

For production, prefer Managed Identity instead of storing passwords or long-lived credentials.

---

## GitHub Repository Guardrails

The repository must follow these controls:

- Repository should be private.
- `main` branch should be protected.
- Pull Request review should be required.
- CI tests should pass before merge.
- Direct push to `main` should not be allowed.
- Force push should be disabled.
- Branch deletion should be disabled.
- CODEOWNERS should be used for important files.

---

## Data Protection Rules

The following must not be stored in GitHub:

- production data exports
- real customer/tenant records
- confidential finance extracts
- raw database dumps
- personal information
- screenshots containing sensitive data
- Fabric query results with confidential values

Only approved schema information, business rules, synthetic examples, and non-sensitive documentation should be committed.

---

## AI and SQL Safety Rules

Changes to the following files require careful review:

- `main.py`
- `function_app.py`
- `finance_context.md`
- `selected_measures_lookup.md`
- SQL validation logic
- prompt construction logic
- answer summarization logic

Reason: these files can affect generated SQL, finance calculations, and final answers shown to users.

---

## Pull Request Requirements

All security-sensitive or AI-sensitive changes must include:

- summary of change
- reason for change
- files changed
- expected AI/SQL impact
- test evidence
- confirmation that no secrets were committed
- required reviewer approval

---

## Dependency Security

Dependabot should be enabled for:

- Python dependencies in `requirements.txt`
- GitHub Actions workflow dependencies

Dependency updates should be reviewed and tested before merging.

---

## Deployment Guardrails

Deployment should follow these rules:

- deployment should happen through GitHub Actions
- deployment workflow should run only after tests pass
- production deployment should require approval
- secrets should not be printed in logs
- failed deployments should be reviewed before retrying

---

## Compliance Classification

| Area | Classification |
|---|---|
| Finance rules | Confidential |
| SQL generation logic | Internal |
| Schema/context files | Confidential/Internal |
| Production data | Restricted |
| Secrets/credentials | Restricted |
| Governance documents | Internal |

---

## Incident Handling

If a secret is accidentally committed:

1. Remove it from the repository.
2. Rotate the exposed secret immediately.
3. Check Git history and GitHub logs.
4. Inform the technical/security owner.
5. Update `.gitignore` or guardrails if needed.

Removing a secret from the latest commit is not enough. The secret must be rotated because it may still exist in Git history.

---

## Current Guardrails Implemented

- `.gitignore` excludes `.env`, `local.settings.json`, `.venv`, and cache folders.
- Pull Request template added.
- CODEOWNERS added.
- Dependabot configuration added.
- Basic unit tests added.
- CI pipeline added for automated testing.

---

## Version History

| Version | Date | Change | Approved By |
|---|---|---|---|
| v1.0.0 | 2026-05-22 | Initial security and compliance guardrails document created | TBD |