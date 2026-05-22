# selected_measures_lookup.md Changelog

## Purpose

This file tracks version changes made to `selected_measures_lookup.md`.

The `selected_measures_lookup.md` file controls measure names, normalized names, table mapping, dependencies, and DAX/measure definitions used by the Copilot NL2SQL Finance Agent.

Changes to this file can affect which KPI or measure the AI selects for a user question.

---

## Versioning Rules

| Version Type | Meaning | Example |
|---|---|---|
| MAJOR | Breaking or business-critical measure logic change | Changing revenue or margin measure definition |
| MINOR | New measure, KPI, dependency, or mapping added | Adding EBITDA measure |
| PATCH | Small correction, typo, or naming clarification | Fixing normalized measure wording |

---

## Current Version

Current approved version: `v1.0.0`

---

## Changelog

### v1.0.0

Date: 2026-05-22  
Status: Initial version  

#### Added
- Initial selected measures lookup file.
- Initial measure names and normalized names.
- Initial table mapping and dependency references.
- Initial measure formula references.

#### Impact
- Establishes the first approved version of measure lookup logic used by the NL2SQL backend.

#### Approved By
- Technical Owner: TBD
- Data/Business Owner: TBD