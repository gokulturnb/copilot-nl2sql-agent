# Copilot NL2SQL Agent

This project uses Copilot Studio as the front-end chat interface and Azure Functions as the backend API.

The Azure Function receives a user question, sends it to the NL2SQL pipeline, generates SQL, validates the SQL, executes it against the Fabric Warehouse, and returns a summarized answer.

## Main Files

- `function_app.py` - Azure Function HTTP endpoint
- `main.py` - NL2SQL pipeline, SQL validation, Fabric execution, and answer generation
- `finance_context.md` - finance schema and business rules
- `selected_measures_lookup.md` - measure and KPI lookup context