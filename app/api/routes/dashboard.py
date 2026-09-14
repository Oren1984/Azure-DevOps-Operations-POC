"""Server-rendered local demonstration dashboard.

This is a thin presentation layer only: the page itself contains no business
logic and calls the same `/api/v1/demo/run` and `/api/v1/audit` endpoints a
`curl` command or Swagger UI would. It exists purely to make the deterministic
demo easier to see for local learning/demonstration - it is not an
operations portal and has no write path of its own.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["dashboard"])

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "dashboard.html")
