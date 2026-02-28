from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

app = FastAPI(title="JW Publisher Transfer Tool")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


class ExportRequest(BaseModel):
    selected_ids: list[int]
    data: dict[str, Any]


def filter_export(data: dict[str, Any], selected_ids: list[int]) -> dict[str, Any]:
    """Return a copy of the Hourglass export containing only the selected publishers
    and their associated field service reports."""
    selected_set = set(selected_ids)
    return {
        "congregation": data["congregation"],
        "publishers": [p for p in data["publishers"] if p["id"] in selected_set],
        "reports": [
            r for r in data.get("reports", []) if r["user"]["id"] in selected_set
        ],
    }


def build_filename(publishers: list[dict[str, Any]]) -> str:
    today = date.today().isoformat()
    if len(publishers) == 1:
        pub = publishers[0]
        last = pub.get("lastname", "Unknown").replace(" ", "_")
        first = pub.get("firstname", "").replace(" ", "_")
        return f"Transfer_{last}_{first}_{today}.json"
    return f"Transfer_{len(publishers)}_Publishers_{today}.json"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/export")
async def export_publishers(payload: ExportRequest):
    filtered = filter_export(payload.data, payload.selected_ids)
    filename = build_filename(filtered["publishers"])
    content = json.dumps(filtered, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
