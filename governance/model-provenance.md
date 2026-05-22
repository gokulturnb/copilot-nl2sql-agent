# Model Provenance

## Purpose

This document records the AI model, context files, prompt behavior, and governance controls used in the Copilot NL2SQL Finance Agent.

The goal is to make AI behavior traceable, explainable, and auditable.

---

## Application Role of AI

The AI model is used for:

- Rewriting informal user finance questions into clear business questions.
- Retrieving relevant finance context and measure definitions.
- Generating SQL queries for Microsoft Fabric Warehouse.
- Regenerating SQL when validation issues are found.
- Summarizing SQL results into a user-friendly answer.

The AI model does not directly access the database. SQL execution is handled by the backend application.

---

## Current Model Configuration

| Item | Value |
|---|---|
| LLM Provider | OpenAI / Azure OpenAI |
| Model / Deployment Name | Configured through environment variables |
| Main Provider Variable | `LLM_PROVIDER` |
| OpenAI Model Variable | `OPENAI_MODEL` |
| Azure OpenAI Deployment Variable | `AZURE_OPENAI_DEPLOYMENT` |
| Temperature | 0.0 for SQL generation and most deterministic tasks |

No API keys or secrets should be stored in this document.

---

## AI Context Files

The AI behavior is mainly controlled by these files:

| File | Purpose |
|---|---|
| `finance_context.md` | Finance schema, table rules, joins, business logic, date logic, and KPI rules |
| `selected_measures_lookup.md` | Measure names, normalized names, table mapping, dependencies, and DAX formulas |
| `main.py` | Prompt construction, SQL generation, validation, execution, and summarization logic |
| `function_app.py` | Azure Function HTTP entry point for Copilot/backend integration |

---

## SQL Generation Controls

The backend includes SQL validation rules to reduce unsafe or incorrect SQL.

Current validation areas include:

- Invalid nested CTE detection.
- Duplicate CTE detection.
- Invalid `CROSS JOIN ... ON` detection.
- Duplicate alias detection.
- Invalid community column detection.
- YTD and explicit-year logic checks.
- Rolling 12-month logic checks.
- Invalid nested aggregate patterns such as `AVG(SUM(...))`.

---

## Data Usage

This system does not train a custom model using production data.

The model receives approved context such as:

- Table descriptions.
- Column mappings.
- Join rules.
- KPI definitions.
- Business logic.
- Measure lookup metadata.
- User’s natural language question.

Production data should not be stored in GitHub.

---

## Model Change Governance

Any change to the model, prompt, context files, or SQL generation behavior must go through a Pull Request.

Changes requiring review include:

- Changing the deployed model name.
- Changing `finance_context.md`.
- Changing `selected_measures_lookup.md`.
- Changing SQL validation logic.
- Changing prompt construction logic.
- Changing summarization behavior.

---

## Version History

| Version | Date | Change | Approved By |
|---|---|---|---|
| v1.0.0 | 2026-05-22 | Initial model provenance document created | TBD |

---

## Notes

Secrets, API keys, Fabric credentials, connection strings, `.env`, and `local.settings.json` must not be committed to GitHub.