from __future__ import annotations

import argparse
import os
import struct
import sys
from pathlib import Path
from typing import Any
import re
import csv
import io
import json

import pyodbc
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

SQL_COPT_SS_ACCESS_TOKEN = 1256
CONTEXT_FILE = Path(__file__).resolve().parent / "finance_context.md"
MEASURE_LOOKUP_FILE = Path(__file__).resolve().parent / "selected_measures_lookup.md"
TABLE_DISPLAY_THRESHOLD = 15
TABLE_PREVIEW_MAX_ROWS = 50
MEASURE_CONTEXT_MAX_ROWS = 40
MEASURE_RETRIEVAL_SHORTLIST_MAX_ROWS = 140
FINANCE_RETRIEVAL_MAX_SECTIONS = 10
DEBUG_RETRIEVER = (os.getenv("DEBUG_RETRIEVER") or "").strip().lower() in {"1", "true", "yes", "on"}
REPHRASE_USER_QUESTION = (os.getenv("REPHRASE_USER_QUESTION") or "1").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}


def _build_llm_client() -> tuple[Any, str]:
    llm_provider = (os.getenv("LLM_PROVIDER") or "openai").strip().lower()
    if llm_provider == "azure_openai":
        client = AzureOpenAI(
            api_key=(os.getenv("AZURE_OPENAI_API_KEY") or "").strip(),
            azure_endpoint=(os.getenv("AZURE_OPENAI_ENDPOINT") or "").strip(),
            api_version=(os.getenv("AZURE_OPENAI_API_VERSION") or "2024-08-01-preview").strip(),
        )
        model = (os.getenv("AZURE_OPENAI_DEPLOYMENT") or "").strip()
        if not model:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT is required when LLM_PROVIDER=azure_openai.")
        return client, model

    client = OpenAI(api_key=(os.getenv("OPENAI_API_KEY") or "").strip())
    model = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    return client, model


def _generate_text(prompt: str, temperature: float = 0.0) -> str:
    client, model = _build_llm_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("LLM returned an empty response.")
    return content.strip()


def _rephrase_user_question(raw_question: str) -> str:
    text = (raw_question or "").strip()
    if not text:
        return text
    prompt = f"""
You rewrite informal analytics / finance questions into one clear, professional question (or two short sentences max).

Hard rules:
- Keep every explicit calendar year, date, entity name, account/community/segment label, and KPI or measure wording the user gave; do not rename or drop them.
- Preserve time-intelligence words exactly when present (YTD, MTD, WTD, QTD, YoY, MoM, variance, %, etc.).
- Do not add new filters, breakdowns, or metrics the user did not imply.
- Do not answer the question; output only the rewritten question.
- Plain text only: no quotes, bullets, or markdown.

USER QUESTION:
{text}
""".strip()
    polished = _generate_text(prompt, temperature=0.0)
    single_line = " ".join(polished.splitlines()).strip()
    return single_line or text


def _clean_sql(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        inner = lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
        cleaned = "\n".join(inner).strip()
    if cleaned.endswith(";"):
        return cleaned
    return f"{cleaned};"


def _has_on_token_at_depth_zero(fragment: str) -> bool:
    """True if ON appears as a token at paren depth 0 (not inside a subquery)."""
    depth = 0
    i = 0
    frag = fragment.lower()
    n = len(frag)
    while i < n:
        ch = frag[i]
        if ch == "(":
            depth += 1
            i += 1
            continue
        if ch == ")":
            depth = max(0, depth - 1)
            i += 1
            continue
        if depth == 0 and re.match(r"\bon\b", frag[i:]):
            return True
        i += 1
    return False


def _cross_join_followed_by_illegal_on(sql_lower: str) -> bool:
    """
    T-SQL: CROSS JOIN has no ON. Flag only when ON belongs to that join, not a later INNER/LEFT JOIN.
    """
    pos = 0
    boundary_re = re.compile(
        r"\s*(?:(?:inner|left|right|full)(?:\s+outer)?\s+|cross\s+)?join\b"
        r"|\s*where\b"
        r"|\s*group\s+by\b"
        r"|\s*having\b"
        r"|\s*order\s+by\b"
        r"|\s*union\b",
        re.IGNORECASE,
    )
    while True:
        m = re.search(r"\bcross\s+join\b", sql_lower[pos:], flags=re.IGNORECASE)
        if not m:
            return False
        start = pos + m.end()
        i = start
        depth = 0
        n = len(sql_lower)
        while i < n:
            ch = sql_lower[i]
            if ch == "(":
                depth += 1
                i += 1
                continue
            if ch == ")":
                depth = max(0, depth - 1)
                i += 1
                continue
            if depth == 0:
                b = boundary_re.match(sql_lower[i:])
                if b:
                    break
            i += 1
        if _has_on_token_at_depth_zero(sql_lower[start:i]):
            return True
        pos = i


def _validate_sql_query(sql_query: str, user_query: str) -> list[str]:
    errors: list[str] = []
    normalized = sql_query.lower()
    user_q = user_query.lower()
    explicit_year_match = re.search(r"\b(20\d{2})\b", user_q)
    explicit_year = int(explicit_year_match.group(1)) if explicit_year_match else None

    if re.search(r"\bwith\s+[a-z0-9_]+\s+as\s*\(\s*with\b", normalized):
        errors.append("Invalid nested/duplicated WITH CTE declaration detected at query start.")
    if re.search(r"\bwith\s+(?P<cte>[a-z0-9_]+)\s+as\s*\(\s*with\s+(?P=cte)\s+as\s*\(", normalized):
        errors.append("Duplicate CTE declaration detected (same CTE defined twice consecutively).")
    if re.search(r"as\s+decimal\s*\(\s*\d+\s*,\s*\d+\s*\)\s*\)\s*as\s+decimal\s*\(", normalized):
        errors.append("Malformed CAST detected: duplicated `AS DECIMAL(...)` in one expression.")

    if _cross_join_followed_by_illegal_on(normalized):
        errors.append("CROSS JOIN cannot have an ON clause.")

    if re.search(r"\bavg\s*\(\s*sum\s*\(", normalized) or re.search(
        r"\bavg\s*\(\s*cast\s*\(\s*sum\s*\(", normalized
    ):
        errors.append(
            "Invalid nested aggregate AVG(SUM(...)) in one SELECT (SQL Server Msg 130). "
            "Use a CTE: SUM per day (or per grain), then AVG in an outer query."
        )

    # Conservative duplicate-alias guard: detect only local reuse inside the same
    # FROM/JOIN segment to avoid false positives across nested scopes/CTEs.
    local_alias_reuse = re.search(
        r"\bfrom\s+[a-z0-9_\[\]\.]+\s+([a-z][a-z0-9_]*)\b[\s\S]{0,240}\bjoin\s+[a-z0-9_\[\]\.]+\s+\1\b",
        normalized,
    ) or re.search(
        r"\bjoin\s+[a-z0-9_\[\]\.]+\s+([a-z][a-z0-9_]*)\b[\s\S]{0,240}\bjoin\s+[a-z0-9_\[\]\.]+\s+\1\b",
        normalized,
    )
    if local_alias_reuse:
        errors.append(f"Duplicate table aliases detected: {local_alias_reuse.group(1)}.")

    if "community.community" in normalized or re.search(r"\bcm\.community\b", normalized):
        errors.append("Invalid community label column. Use Community.Code or Community.Name.")

    if "ytd" in user_q:
        if explicit_year is None:
            if re.search(r"datefromparts\(\s*20\d{2}\s*,", normalized):
                errors.append("YTD query is hardcoding a calendar year; use dynamic GETDATE()-based boundaries.")
        else:
            if re.search(r"\bgetdate\s*\(", normalized):
                errors.append(
                    f"User asked for explicit year {explicit_year}; SQL must not use GETDATE()-anchored YTD bounds."
                )
            if str(explicit_year) not in normalized:
                errors.append(f"User asked for explicit year {explicit_year}; SQL does not reference that year.")
            if str(explicit_year - 1) not in normalized:
                errors.append(
                    f"User asked for explicit year {explicit_year}; variance baseline should reference {explicit_year - 1}."
                )

    if ("12 month" in user_q or "12-month" in user_q or "12 months" in user_q) and "avg(" in normalized:
        if re.search(r"\bcurryear\s*-\s*1\b", normalized) and "startym" in normalized and "currym" in normalized:
            errors.append(
                "12-month average window appears to use same-month-last-year to current month (13 months). "
                "Use current month start and subtract 11 months."
            )
        if re.search(r"avg\s*\(\s*[^)]*round\s*\(", normalized):
            errors.append("Average is computed on rounded values. Average raw monthly values, round only final output.")

    is_rolling_request = (
        ("rolling" in user_q or "trailing" in user_q or "moving average" in user_q)
        and (
            "12 month" in user_q or "12-month" in user_q or "12 months" in user_q
            or "3 month" in user_q or "3-month" in user_q or "3 months" in user_q
            or "6 month" in user_q or "6-month" in user_q or "6 months" in user_q
        )
    )
    if is_rolling_request and "rows between" in normalized and explicit_year is not None:
        prior_year = str(explicit_year - 1)
        monthperiods_match = re.search(r"monthperiods\b[\s\S]{0,400}", normalized)
        if monthperiods_match and prior_year not in monthperiods_match.group(0):
            errors.append(
                f"Rolling/trailing N-month query for {explicit_year}: MonthPeriods must extend N-1 months "
                f"before {explicit_year} (include {prior_year}). Start MonthPeriods at "
                f"{prior_year}01 and filter the display window only in the final SELECT."
            )

    return errors


def _regenerate_sql_with_feedback(
    user_query: str,
    finance_context: str,
    measure_context: str,
    prior_sql: str,
    issues: list[str],
) -> str:
    feedback = "\n".join(f"- {issue}" for issue in issues)
    retry_prompt = f"""
You previously generated SQL that failed validation.
Regenerate a corrected SQL query for SQL Server.

Return ONLY one executable SQL query.
No markdown, no explanation.

Validation issues to fix:
{feedback}

Previous SQL:
{prior_sql}

Use ONLY the contexts below.

RETRIEVED_FINANCE_CONTEXT:
{finance_context}

RETRIEVED_MEASURE_CONTEXT:
{measure_context}

USER QUESTION:
{user_query}
""".strip()
    return _clean_sql(_generate_text(retry_prompt))


def _time_intelligence_glossary() -> str:
    return """
Time-intelligence definitions (apply exactly):
- YTD: Jan 1 of target year through target end date.
- Prior YTD: same aligned date window in previous year.
- Explicit-year YTD:
  - if target year is current year: Jan 1 to today.
  - if target year is a past year: use full year Jan 1 to Dec 31.
- YOY: compare a period against same period last year.
- MTD: first day of target month through target end date.
- Prior MTD: aligned day-of-month window in comparison month.
- MOM: compare target month period vs immediately previous month period.
- WTD: first day of target week through target end date.
- Prior WTD: aligned week/day window in comparison period.
- QTD: first day of target quarter through target end date.
- Prior QTD: aligned quarter-to-date window in comparison period.
- Variance: current period minus comparison period.
- Variance %: variance / NULLIF(comparison period, 0); multiply by 100 only when percent scale is requested.
""".strip()


def _require_context() -> str:
    if not CONTEXT_FILE.exists():
        raise FileNotFoundError(
            f"Missing context file: {CONTEXT_FILE}. Add your schema/business rules here first."
        )
    context = CONTEXT_FILE.read_text(encoding="utf-8").strip()
    if not context:
        raise ValueError(f"{CONTEXT_FILE.name} is empty. Add schema/business rules first.")
    return context


def _require_measure_lookup_context() -> str:
    if not MEASURE_LOOKUP_FILE.exists():
        raise FileNotFoundError(
            f"Missing measure lookup file: {MEASURE_LOOKUP_FILE}. Add selected_measures_lookup.md."
        )
    context = MEASURE_LOOKUP_FILE.read_text(encoding="utf-8").strip()
    if not context:
        raise ValueError(f"{MEASURE_LOOKUP_FILE.name} is empty. Add measure mappings first.")
    return context


def _normalize_text(value: str) -> str:
    normalized = (value or "").lower()
    normalized = normalized.replace("%", " percent ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _extract_json_object(raw: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            return {}
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}


def _split_markdown_sections(markdown_text: str) -> list[dict[str, str]]:
    lines = markdown_text.splitlines()
    sections: list[dict[str, str]] = []
    current_title = "Document Root"
    current_lines: list[str] = []

    def _flush() -> None:
        nonlocal current_title, current_lines
        body = "\n".join(current_lines).strip()
        if body:
            sections.append({"title": current_title, "content": body})
        current_lines = []

    for line in lines:
        if line.lstrip().startswith("#"):
            _flush()
            current_title = line.strip().lstrip("#").strip() or "Untitled"
        else:
            current_lines.append(line)
    _flush()
    return sections


def _extract_measure_tsv_block(raw_text: str) -> str:
    start = raw_text.find("```tsv")
    if start == -1:
        raise ValueError(f"{MEASURE_LOOKUP_FILE.name} is missing a ```tsv block.")
    start += len("```tsv")
    end = raw_text.find("```", start)
    if end == -1:
        raise ValueError(f"{MEASURE_LOOKUP_FILE.name} has an unterminated ```tsv block.")
    return raw_text[start:end].strip()


def _load_measure_lookup() -> tuple[str, list[dict[str, str]]]:
    if not MEASURE_LOOKUP_FILE.exists():
        raise FileNotFoundError(
            f"Missing measure lookup file: {MEASURE_LOOKUP_FILE}. Add selected_measures_lookup.md."
        )
    raw = MEASURE_LOOKUP_FILE.read_text(encoding="utf-8")
    if not raw.strip():
        raise ValueError(f"{MEASURE_LOOKUP_FILE.name} is empty.")

    header_instructions = raw.split("## Measures Table", 1)[0].strip()
    tsv_block = _extract_measure_tsv_block(raw)

    reader = csv.DictReader(io.StringIO(tsv_block), delimiter="\t")
    rows = [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in reader]
    if not rows:
        raise ValueError(f"{MEASURE_LOOKUP_FILE.name} has no measure rows.")
    return header_instructions, rows


def _measure_match_score(query_norm: str, query_tokens: set[str], row: dict[str, str]) -> float:
    measure_name = row.get("measure_name", "")
    normalized_name = row.get("normalized_name", "")
    measure_norm = _normalize_text(measure_name)
    normalized_norm = _normalize_text(normalized_name)

    if not measure_norm and not normalized_norm:
        return 0.0

    score = 0.0
    if measure_norm == query_norm or normalized_norm == query_norm:
        score += 20.0
    if measure_norm and measure_norm in query_norm:
        score += 8.0
    if normalized_norm and normalized_norm in query_norm:
        score += 8.0

    candidate_tokens = set((measure_norm + " " + normalized_norm).split())
    overlap = query_tokens & candidate_tokens
    if overlap:
        score += (len(overlap) / max(1, len(candidate_tokens))) * 6.0
        score += len(overlap) * 0.2

    if "percent" in query_tokens and "percent" in candidate_tokens:
        score += 2.0
    if "ytd" in query_tokens and "ytd" in candidate_tokens:
        score += 2.0
    if "variance" in query_tokens and "variance" in candidate_tokens:
        score += 2.0
    return score


def _build_measure_shortlist(user_query: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    query_norm = _normalize_text(user_query)
    query_tokens = set(query_norm.split())
    scored_rows: list[tuple[float, dict[str, str]]] = []
    for row in rows:
        score = _measure_match_score(query_norm, query_tokens, row)
        if score > 0:
            scored_rows.append((score, row))
    scored_rows.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored_rows[:MEASURE_RETRIEVAL_SHORTLIST_MAX_ROWS]]


def _retrieve_seed_measures_with_llm(user_query: str, rows: list[dict[str, str]]) -> list[str]:
    retrieval_columns = ["measure_name", "normalized_name", "table_name", "depends_on"]
    retrieval_lines = ["\t".join(retrieval_columns)]
    shortlist_rows = _build_measure_shortlist(user_query, rows)
    candidate_rows = shortlist_rows if shortlist_rows else rows[:MEASURE_RETRIEVAL_SHORTLIST_MAX_ROWS]
    for row in candidate_rows:
        retrieval_lines.append(
            "\t".join((row.get(col, "") or "").replace("\n", " ").strip() for col in retrieval_columns)
        )
    retrieval_tsv = "\n".join(retrieval_lines)

    retrieval_prompt = f"""
You are a strict measure retriever.
Your job is retrieval only; do not generate SQL.

Given:
1) USER QUESTION
2) A MEASURE LOOKUP TABLE with columns:
   measure_name, normalized_name, table_name, depends_on

Task:
- Identify the most relevant measure(s) to answer the question.
- Prefer exact semantic match to the KPI intent in the question.
- If question asks for percent/ %, pick the percent measure when available.
- If question asks YTD/MTD/WTD/YOY/variance, prioritize matching those qualifiers.
- Return at most 8 seed measures by name.
- Do not include dependency-only measures unless they are directly asked.

Output format:
Return ONLY JSON:
{{"seed_measures":["<measure_name>", "..."]}}

USER QUESTION:
{user_query}

MEASURE LOOKUP CANDIDATES (TSV):
{retrieval_tsv}
""".strip()

    raw = _generate_text(retrieval_prompt, temperature=0.0)
    parsed = _extract_json_object(raw)

    seed_measures = parsed.get("seed_measures", []) if isinstance(parsed, dict) else []
    if not isinstance(seed_measures, list):
        return []
    return [str(x).strip() for x in seed_measures if str(x).strip()][:8]


def _resolve_measure_context(user_query: str) -> tuple[str, list[str]]:
    instructions, rows = _load_measure_lookup()
    by_name = {_normalize_text(row.get("measure_name", "")): row for row in rows}
    by_normalized_name = {_normalize_text(row.get("normalized_name", "")): row for row in rows}

    seed_measure_names = _retrieve_seed_measures_with_llm(user_query, rows)
    selected_seed_rows: list[dict[str, str]] = []
    for seed_name in seed_measure_names:
        key = _normalize_text(seed_name)
        row = by_name.get(key) or by_normalized_name.get(key)
        if row:
            selected_seed_rows.append(row)

    resolved: dict[str, dict[str, str]] = {}
    queue = list(selected_seed_rows)
    while queue and len(resolved) < MEASURE_CONTEXT_MAX_ROWS:
        row = queue.pop(0)
        key = _normalize_text(row.get("measure_name", ""))
        if not key or key in resolved:
            continue
        resolved[key] = row

        depends_on = row.get("depends_on", "")
        if not depends_on:
            continue
        for dep_name in [x.strip() for x in depends_on.split(";") if x.strip()]:
            dep_row = by_name.get(_normalize_text(dep_name))
            if dep_row and _normalize_text(dep_row.get("measure_name", "")) not in resolved:
                queue.append(dep_row)

    if not resolved:
        return (
            "No measure could be retrieved from selected_measures_lookup.md for this query. "
            "In this case, rely on finance_context.md only."
        ), []

    columns = [
        "measure_name",
        "normalized_name",
        "table_name",
        "display_folder",
        "depends_on",
        "dax_formula",
    ]
    lines = ["\t".join(columns)]
    for row in resolved.values():
        lines.append("\t".join((row.get(col, "") or "").replace("\n", " ").strip() for col in columns))

    resolved_measure_names = [row.get("measure_name", "") for row in resolved.values() if row.get("measure_name", "")]
    return (
        f"{instructions}\n\n"
        "Resolved measure rows relevant to the user question:\n"
        "```tsv\n"
        + "\n".join(lines)
        + "\n```"
    ), resolved_measure_names


def _retrieve_finance_context_with_llm(user_query: str, finance_context: str) -> tuple[str, list[str]]:
    sections = _split_markdown_sections(finance_context)
    if not sections:
        return "No finance context sections available."

    catalog_lines: list[str] = []
    for idx, section in enumerate(sections, start=1):
        snippet = section["content"][:700].replace("\n", " ").strip()
        catalog_lines.append(f"{idx}\t{section['title']}\t{snippet}")
    catalog_text = "\n".join(catalog_lines)

    retrieval_prompt = f"""
You are a strict finance-context retriever.
Your job is retrieval only; do not generate SQL.

Given the user question and section catalog, select only the sections needed
for SQL generation (tables, joins, dimensions, date logic, business filters, KPI mapping).

Return ONLY JSON:
{{"section_ids":[1,2], "reason":"short reason"}}

Rules:
- Pick up to {FINANCE_RETRIEVAL_MAX_SECTIONS} section IDs.
- Prefer precision over recall.
- If unsure, pick the minimum set that is still sufficient.

USER QUESTION:
{user_query}

FINANCE SECTION CATALOG (TSV: id, title, snippet):
{catalog_text}
""".strip()

    parsed = _extract_json_object(_generate_text(retrieval_prompt, temperature=0.0))
    raw_ids = parsed.get("section_ids", [])
    if not isinstance(raw_ids, list):
        raw_ids = []

    selected_ids: list[int] = []
    for value in raw_ids:
        try:
            candidate = int(value)
        except (TypeError, ValueError):
            continue
        if 1 <= candidate <= len(sections):
            selected_ids.append(candidate)
    deduped_ids = list(dict.fromkeys(selected_ids))[:FINANCE_RETRIEVAL_MAX_SECTIONS]

    if not deduped_ids:
        # Safe fallback: first two sections usually contain high-level rules/schema.
        deduped_ids = list(range(1, min(3, len(sections) + 1)))

    retrieved_sections: list[str] = []
    retrieved_titles: list[str] = []
    for section_id in deduped_ids:
        section = sections[section_id - 1]
        retrieved_titles.append(section["title"])
        retrieved_sections.append(
            f"## {section['title']}\n{section['content']}".strip()
        )
    return "\n\n".join(retrieved_sections).strip(), retrieved_titles


def _build_sql_prompt(user_query: str, finance_context: str, measure_context: str) -> str:
    explicit_year_match = re.search(r"\b(20\d{2})\b", user_query)
    explicit_year_line = (
        f"Explicit year requested by user: {explicit_year_match.group(1)}."
        if explicit_year_match
        else "Explicit year requested by user: none."
    )
    date_default_line = (
        "User named a calendar year: honor it for DateID bounds (see finance_context.md)."
        if explicit_year_match
        else "No calendar year in the user question: if the question also omits any other date range, month, quarter, or period keyword (YTD, MTD, QTD, WTD, last month, etc.), "
        "default DateID filter to current calendar year Jan 1 through today: "
        "BETWEEN YEAR(GETDATE())*10000+101 AND CAST(CONVERT(char(8),GETDATE(),112) AS INT)."
    )
    time_glossary = _time_intelligence_glossary()
    return f"""
You are a strict SQL generator for Microsoft SQL Server / Fabric Warehouse.

Use ONLY the information in RETRIEVED_FINANCE_CONTEXT and RETRIEVED_MEASURE_CONTEXT.
Do not invent tables or columns.
Return ONLY one executable SQL query and nothing else.
No markdown, no explanation, no JSON.
Prefer explicit column names over SELECT *.
Apply LIMIT/TOP where sensible for listing questions.
Critical schema rule: in `Community` table, valid label columns are `Code` and `Name`.
Never use `Community.Community` because it does not exist.
Payables due bucket rule: for **payables due analysis by buckets** (AP aging on `PayablesStateTransactions`, not generic due analysis), use `DueAnalysis.DueDays` (`da.DueDays` with join on `DueAnalysisID`) and bucket logic from RETRIEVED_FINANCE_CONTEXT; do not use DueAnalysis Group1/Group2/Group3 for bucket mapping for now.
Payables Balance snapshot: `PayablesBalance` is closing balance per `DateID`. For balance by quarter/month/year, take **latest `DateID` in each grain** then sum `PayablesBalance` for that date only — never `SUM(PayablesBalance)` over every day in the grain. **Average Payables** by quarter: average **daily** balances within the quarter, not the quarter-end `PayablesBalance` snapshot.
Performance rule: never self-join `GLTransactions` (for example `GLTransactions t2`) for time comparisons.
Use explicit fixed date boundaries derived from GETDATE() for current and prior YTD.
GL `GLNetChangeACY` sign: use `-SUM(t.GLNetChangeACY)` **only** for **revenue**; for cost, expense, and other non-revenue GL totals use `SUM(t.GLNetChangeACY)` (no unary minus). See RETRIEVED_FINANCE_CONTEXT.
Turnover days: if the question does **not** mention payables, AP, vendor, or vendor purchase on credit, use **Receivables Turnover Days** from RETRIEVED_FINANCE_CONTEXT (`ReceivablesStateTransactions` + `ReceivablesTransactions`, column `[CustomerSalesonCredit]`). Use **Payables Turnover Days** only when payables/AP/vendor is explicit.
Monthly receivables turnover: **NumberOfDays** = calendar days in month (`MonthPeriods` / `EOMONTH`), not `COUNT(DISTINCT DateID)` from facts.
Net sales (invoice subledger): use `SalesInvoiceTransactions` + `SalesInvoiceMiscChargesTransactions` per finance_context; do **not** use GL `Revenue Main Group` for net sales totals.
Total expenses (total / overall / total cost and expenses): GL `GLTransactions` with `a.[mainaccounthierarchy-1_L1-Name] IN ('Cost', 'Gen & Adm Expenses')` and **raw** `SUM(t.GLNetChangeACY)` (no unary minus). See `## Total Expenses rule` in RETRIEVED_FINANCE_CONTEXT.
Executive KPIs (net profit margin, profit after direct cost, current ratio, working capital) follow `# Executive Finance KPI rules`: numeric-only output (millions + DECIMAL(18,4) ratios), revenue uses `-SUM`, non-revenue uses raw `SUM`, profitability KPIs use `BETWEEN` period bounds, balance-sheet KPIs use `t.DateID <= <AsOfDateID>`, do NOT emit string labels like 'Improving' / 'Shrinking' / 'Cannot determine' unless the user explicitly asks for interpretation.
Item-level net sales: filter `ItemName` on both facts; aggregate each table separately (no row-level join between the two); skip `Item` join unless extra attributes needed.
`SalesInvoiceTransactions` has `CustomerName` and `VendorName` on the fact—use for filters/grouping without Customer/Vendor joins when names suffice.
Vendor Purchase on Credit physical column: use `pt.VendorPurchaseonCredit` on `PayablesTransactions` (no spaces, lowercase `on`). Never emit `pt.[Vendor Purchase on Credit]`, `VendorPurchaseOnCredit` (camelCase `On`), or any `[col_Payables Transactions_...]` semantic prefix. ACY variant: `VendorPurchaseonCreditACY`.
SQL syntax rules:
- Never nest AVG(SUM(...)) in one SELECT level (SQL Server error). Sum daily facts in an inner CTE, then AVG in the outer query.
- CROSS JOIN never has an ON clause.
- Do not reuse the same table alias more than once in a query.
- Never duplicate a CTE declaration (for example `WITH agg AS ( WITH agg AS (...) )`).
- When using CTEs, define each CTE once, then reference it in the final SELECT.
- In CAST expressions, use only one type clause (for example `CAST(ROUND(x, 4) AS DECIMAL(18,4))`), never duplicate `AS DECIMAL(...)`.
- For YTD questions without an explicit year in the user question, do not hardcode 20XX in DATEFROMPARTS.
- For 12-month average questions (including current month), window must be current month start minus 11 months through current month end.
- For **rolling / trailing N-month** monthly KPIs (any fact), **`MonthPeriods`** and the fact aggregation window must extend **N − 1** months **before** the first display month so `AVG(...) OVER (ORDER BY YearMonth ROWS BETWEEN N-1 PRECEDING AND CURRENT ROW)` actually has lookback rows; filter to the display window only in the final `SELECT`. See **### Monthly rolling-N pattern** in RETRIEVED_FINANCE_CONTEXT.
- Do not average pre-rounded monthly values; aggregate raw monthly values first, then round only the final projection.
Year rules:
- If user explicitly mentions a year (for example 2023), anchor the "current" YTD to that year, not GETDATE().
- For variance against prior year, use explicit year and explicit year minus 1.
- For explicit-year YTD:
  - if explicit year is current year, use current-year YTD to today and prior-year YTD aligned to today.
  - if explicit year is in the past, use full-year bounds for explicit year and explicit year-1.
- If no date or period is specified, default `DateID` to current year Jan 1 through today (see DATE WINDOW below).

TIME-INTELLIGENCE GLOSSARY:
{time_glossary}

RETRIEVED_FINANCE_CONTEXT:
{finance_context}

RETRIEVED_MEASURE_CONTEXT:
{measure_context}

USER QUESTION:
{user_query}

YEAR SIGNAL:
{explicit_year_line}

DATE WINDOW:
{date_default_line}
""".strip()


def _build_summary_prompt(user_query: str, sql_query: str, db_result_tsv: str) -> str:
    return f"""
You are a finance analyst assistant.
Write a concise answer to the user based on SQL output.
If there are no rows, clearly say no matching data was found.
Do not mention internal prompts or system details.
If the question is **payables due analysis by buckets** (AP aging / overdue buckets; not generic due analysis) and results include bucket rows, present them in the Due Overdue layout from finance_context.md: title Due Overdue, parent Before due then Overdue with exact DueBucket labels and sort order, then Total (sum of amounts).

User question:
{user_query}

SQL used:
{sql_query}

Result rows (TSV):
{db_result_tsv}
""".strip()


def _rows_to_tsv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "(no rows returned)"
    headers = list(rows[0].keys())
    lines = ["\t".join(headers)]
    for row in rows:
        lines.append("\t".join(str(row.get(h, "")) for h in headers))
    return "\n".join(lines)


def _format_rows_as_table(rows: list[dict[str, Any]], max_rows: int = TABLE_PREVIEW_MAX_ROWS) -> str:
    if not rows:
        return "(no rows returned)"

    preview_rows = rows[:max_rows]
    headers = [str(h) for h in preview_rows[0].keys()]
    body = [[str(row.get(h, "")) for h in headers] for row in preview_rows]

    widths = [len(h) for h in headers]
    for row in body:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def _line(sep: str = "+", fill: str = "-") -> str:
        return sep + sep.join(fill * (w + 2) for w in widths) + sep

    def _fmt_row(cols: list[str]) -> str:
        return "|" + "|".join(f" {c:<{widths[i]}} " for i, c in enumerate(cols)) + "|"

    lines = [_line(), _fmt_row(headers), _line()]
    for row in body:
        lines.append(_fmt_row(row))
    lines.append(_line())

    if len(rows) > max_rows:
        lines.append(f"(showing first {max_rows} of {len(rows)} rows)")

    return "\n".join(lines)


def _conn_str_token_auth(server: str, database: str) -> str:
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=60;"
    )


def _conn_str_interactive(server: str, database: str) -> str:
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Authentication=ActiveDirectoryInteractive;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )


def _normalize_sql_server(raw_server: str) -> str:
    """
    Normalize server value for SQL client reliability.
    Forces tcp endpoint with explicit port and strips accidental protocol prefixes.
    """
    server = raw_server.strip()
    if not server:
        return server
    server = re.sub(r"^tcp:", "", server, flags=re.IGNORECASE)
    server = server.rstrip("/")
    if "," not in server:
        server = f"{server},1433"
    return f"tcp:{server}"


def _get_db_connection() -> pyodbc.Connection:
    server = _normalize_sql_server((os.getenv("FABRIC_SERVER") or "").strip())
    database = (os.getenv("FABRIC_DATABASE") or "").strip()
    auth = (os.getenv("FABRIC_AUTH") or "aad").strip().lower()

    if not server or not database:
        raise ValueError("FABRIC_SERVER and FABRIC_DATABASE are required.")

    if auth in ("interactive", "aad_interactive"):
        return pyodbc.connect(_conn_str_interactive(server, database))

    try:
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:
        raise RuntimeError(
            "azure-identity package is required for FABRIC_AUTH=aad. "
            "Either install dependencies or set FABRIC_AUTH=interactive."
        ) from exc

    credential = DefaultAzureCredential()
    token = credential.get_token("https://database.windows.net/.default").token
    token_bytes = token.encode("utf-16-le")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
    return pyodbc.connect(
        _conn_str_token_auth(server, database),
        attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct},
    )


def _execute_sql(sql_query: str) -> list[dict[str, Any]]:
    try:
        with _get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            if cursor.description is None:
                return []
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    except pyodbc.OperationalError as exc:
        raise RuntimeError(
            "DB connection failed. Check FABRIC_SERVER/FABRIC_DATABASE, ensure DNS+port 1433 are reachable, "
            "and try FABRIC_AUTH=interactive if AAD token login fails."
        ) from exc


def run_pipeline(
    user_query: str,
    *,
    verbose: bool = True,
    log: Any | None = None,
) -> dict[str, Any]:
    def _log(message: str) -> None:
        if log:
            log(message)
        if verbose:
            try:
                print(message)
            except UnicodeEncodeError:
                safe_message = message.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
                    sys.stdout.encoding or "utf-8",
                    errors="replace",
                )
                print(safe_message)

    finance_context = _require_context()
    measure_context = _require_measure_lookup_context()

    original_query = user_query.strip()
    if REPHRASE_USER_QUESTION and original_query:
        _log("\n[1/5] Polishing user question...")
        user_query = _rephrase_user_question(original_query)
        if user_query != original_query:
            _log(f"Original: {original_query}")
            _log(f"Polished: {user_query}")
        else:
            _log("(unchanged after polish)")
    else:
        user_query = original_query

    _log("\n[2/5] Generating SQL from question + full finance context + full measure lookup...")
    sql_prompt = _build_sql_prompt(user_query, finance_context, measure_context)
    sql_query = _clean_sql(_generate_text(sql_prompt))
    sql_issues = _validate_sql_query(sql_query, user_query)
    if sql_issues:
        _log("\n[sql-guard] Initial SQL failed validation. Regenerating...")
        sql_query = _regenerate_sql_with_feedback(
            user_query=user_query,
            finance_context=finance_context,
            measure_context=measure_context,
            prior_sql=sql_query,
            issues=sql_issues,
        )
        retry_issues = _validate_sql_query(sql_query, user_query)
        if retry_issues:
            raise RuntimeError("Generated SQL failed validation: " + "; ".join(retry_issues))
    _log(sql_query)

    _log("\n[3/5] Executing SQL...")
    rows = _execute_sql(sql_query)
    _log(f"Rows returned: {len(rows)}")
    if len(rows) >= TABLE_DISPLAY_THRESHOLD:
        _log("\nResult table preview:")
        _log(_format_rows_as_table(rows))

    _log("\n[4/5] Summarizing result...")
    db_result_text = _rows_to_tsv(rows)
    summary_prompt = _build_summary_prompt(user_query, sql_query, db_result_text)
    answer = _generate_text(summary_prompt)

    _log("\n[5/5] Final answer:\n")
    _log(answer)

    return {
        "answer": answer,
        "sql": sql_query,
        "row_count": len(rows),
        "rows": rows,
        "original_query": original_query,
        "polished_query": user_query,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FinanceAgent: single-file NL2SQL runner (no router, no RLS, no Azure Function)."
    )
    parser.add_argument(
        "query_text",
        nargs="*",
        help='Natural language question (positional). Example: python main.py "total revenue for EWIG"',
    )
    parser.add_argument("--query", type=str, help="Natural language question (legacy flag)")
    args = parser.parse_args()

    inline_query = " ".join(args.query_text).strip() if args.query_text else ""
    final_query = args.query.strip() if args.query else inline_query

    if final_query:
        run_pipeline(final_query)
        return

    print("FinanceAgent CLI")
    print("Type your finance question (or 'exit' to quit):")
    while True:
        try:
            user_query = input("\nQuery> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_query:
            continue
        if user_query.lower() in {"exit", "quit"}:
            break

        run_pipeline(user_query)


if __name__ == "__main__":
    main()
