# Pull Request Summary

## What changed?

Briefly explain what was changed in this PR.

Examples:
- Added a new finance rule
- Updated SQL validation logic
- Changed Azure Function code
- Updated documentation
- Modified measure lookup file

---

## Why was this change needed?

Explain the reason for the change.

Examples:
- To fix incorrect YTD calculation
- To add a new KPI
- To improve SQL safety
- To update governance documentation

---

## Files Changed

Select all that apply:

- [ ] function_app.py
- [ ] main.py
- [ ] finance_context.md
- [ ] selected_measures_lookup.md
- [ ] requirements.txt
- [ ] GitHub Actions workflow
- [ ] Governance/documentation file
- [ ] Other

---

## AI / SQL Impact

Does this change affect AI behavior, SQL generation, finance logic, or answer summarization?

- [ ] Yes
- [ ] No

If yes, explain the impact:

Describe how this change may affect generated SQL, selected measures, business rules, or final answers.

---

## Test Evidence

Add sample questions tested, if applicable.

Example:

Question tested:
What is total revenue YTD for EWIG?

Expected behavior:
Uses approved revenue rule, EWIG filter, and correct YTD DateID logic.

Result:
Passed / Failed / Not tested

---

## Security Checklist

Confirm the following:

- [ ] No .env file committed
- [ ] No local.settings.json committed
- [ ] No API keys committed
- [ ] No database passwords committed
- [ ] No Fabric credentials committed
- [ ] No Azure OpenAI keys committed
- [ ] No production data committed
- [ ] No real customer/tenant confidential data committed

---

## Review Type Required

Select all that apply:

- [ ] Technical review
- [ ] Data/business rule review
- [ ] Security review
- [ ] Deployment review
- [ ] Documentation review

---

## Final Checklist

- [ ] Code runs locally
- [ ] Existing functionality is not broken
- [ ] Important files are updated
- [ ] Documentation is updated if needed
- [ ] Changelog is updated if needed
- [ ] PR is ready for review