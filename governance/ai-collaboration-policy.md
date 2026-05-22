# AI Collaboration Policy

## Purpose

This document defines how AI-related files and logic must be reviewed before being merged into the project.

The goal is to prevent accidental changes that may affect SQL generation, finance calculations, business rules, or final answers shown to users.

---

## Files Covered by This Policy

This policy applies to changes in:

- `finance_context.md`
- `selected_measures_lookup.md`
- `main.py`
- `function_app.py`
- prompt construction logic
- SQL validation logic
- model configuration
- summarization logic
- GitHub workflow files related to testing or deployment

---

## Why Review Is Required

In this project, AI behavior is controlled by both code and non-code files.

A change in `finance_context.md` or `selected_measures_lookup.md` can change:

- which table the AI uses
- which join the AI applies
- how revenue, expense, YTD, MTD, or variance is calculated
- which KPI or measure is selected
- how final answers are summarized

Because of this, AI-related changes must go through Pull Request review.

---

## Pull Request Rules

All AI-related changes must follow this process:

1. Create a feature branch.
2. Make the required change.
3. Add a clear commit message.
4. Open a Pull Request into `develop`.
5. Explain what changed and why.
6. Include sample test questions when business logic is affected.
7. Get approval before merging.

Direct changes to `main` are not allowed.

---

## Review Requirements by Change Type

| Change Type | Required Review |
|---|---|
| Finance rules change | Business/Data owner review |
| Measure lookup change | Data owner review |
| Prompt logic change | Technical owner review |
| SQL validation change | Technical owner review |
| Model/provider change | Technical + Security review |
| Deployment workflow change | Technical review |
| Security/secrets change | Security review |

---

## Required PR Evidence

For AI-related changes, the Pull Request should include:

- Summary of the change
- Reason for the change
- Files changed
- Sample user question
- Expected SQL behavior
- Expected answer behavior
- Any risks or limitations

Example:

User question:
"What is total revenue YTD for EWIG?"

Expected behavior:
The system should use the approved revenue rule and EWIG community filter.

---

## Rules for Context Files

Changes to `finance_context.md` must be reviewed carefully because this file controls schema, joins, business rules, date logic, and KPI behavior.

Changes to `selected_measures_lookup.md` must be reviewed carefully because this file controls measure selection and KPI mapping.

Do not add:

- production data
- real customer data
- passwords
- API keys
- Fabric credentials
- Azure OpenAI keys
- private tenant information

---

## Rules for Prompt and SQL Logic

Changes to prompt construction, SQL generation, SQL validation, or answer summarization must include testing.

At minimum, test:

- one normal question
- one YTD or date-based question
- one finance KPI question
- one invalid or risky SQL case if validator logic is changed

---

## Model Change Rules

Any change to the LLM provider, model name, deployment name, or temperature must be recorded in:

`governance/model-provenance.md`

Examples of model-related changes:

- switching from OpenAI to Azure OpenAI
- changing model deployment name
- changing temperature
- changing prompt strategy
- changing from full-context prompting to RAG

---

## Approval Rule

No AI-related change should be merged unless:

- the Pull Request explains the impact
- required reviewers have approved
- tests or sample checks are completed
- no secrets or production data are included

---

## Version History

| Version | Date | Change | Approved By |
|---|---|---|---|
| v1.0.0 | 2026-05-22 | Initial AI collaboration policy created | TBD |