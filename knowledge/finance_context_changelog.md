# finance_context.md Changelog

## Purpose

This file tracks version changes made to `finance_context.md`.

The `finance_context.md` file controls finance schema context, business rules, joins, date logic, KPI logic, and SQL generation guidance for the Copilot NL2SQL Finance Agent.

Changes to this file can affect generated SQL and final business answers.

---

## Versioning Rules

| Version Type | Meaning | Example |
|---|---|---|
| MAJOR | Breaking or business-critical logic change | Changing revenue calculation logic |
| MINOR | New rule, table, KPI, join, or business area added | Adding payables aging rules |
| PATCH | Small correction, wording, typo, or clarification | Fixing a column description typo |

---

## Current Version

Current approved version: `v1.0.0`

---

## Changelog

### v1.0.0

Date: 2026-05-22  
Status: Initial version  

#### Added
- Initial finance context file.
- Initial schema and business rule documentation.
- Initial SQL generation guidance.
- Initial finance KPI and date logic rules.

#### Impact
- Establishes the first approved version of finance rules used by the NL2SQL backend.

#### Approved By
- Technical Owner: TBD
- Data/Business Owner: TBD