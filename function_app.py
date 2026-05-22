"""
Azure Functions HTTP entrypoint for FinanceAgent.

POST /api/ask
Body JSON:
{
  "user_query": "..."
}

Response:
- 200 text/plain: final answer only
- 4xx/5xx text/plain: error message
"""

from __future__ import annotations

import logging
from pathlib import Path

import azure.functions as func

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env", override=True)
except ImportError:
    pass

from main import run_pipeline

logger = logging.getLogger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
_TEXT = "text/plain; charset=utf-8"


@app.route(route="ask", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def ask(req: func.HttpRequest) -> func.HttpResponse:
    try:
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse("Invalid JSON body.", mimetype=_TEXT, status_code=400)

        if not isinstance(body, dict):
            return func.HttpResponse("Body must be a JSON object.", mimetype=_TEXT, status_code=400)

        user_query = str(body.get("user_query", "")).strip()
        if not user_query:
            return func.HttpResponse("user_query is required.", mimetype=_TEXT, status_code=400)

        result = run_pipeline(user_query, verbose=False, log=logger.info)
        answer = str(result["answer"]).strip()
        return func.HttpResponse(answer, mimetype=_TEXT, status_code=200)
    except Exception as exc:
        logger.exception("ask failed")
        return func.HttpResponse(str(exc), mimetype=_TEXT, status_code=500)
