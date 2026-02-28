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


PUBLISHER_ARRAY_FIELDS = ("permissionusergroups", "tags")

# Every privilege key NW Scheduler expects in the privileges dict.
PRIVILEGE_KEYS = (
    "attendant", "aux_chairman", "cbs", "cbs_reader", "chairman",
    "chairman2", "chairman3", "cleaning", "closeprayer", "conductFS",
    "console", "dfg", "fm_discussion", "fs_assistant", "hh", "host",
    "initcall", "interpreter", "lac", "localneeds", "mics", "mm_chairman",
    "none", "openprayer", "prayer", "pt", "pt_out", "publicMinistry",
    "reading", "rv", "security_attendant", "stage", "stream", "study",
    "stutalk", "treasures", "video", "wm_chairman", "wm_reader",
    "wt_conductor", "zoom_attendant",
)


def _sanitize_publisher(pub: dict[str, Any]) -> dict[str, Any]:
    """Prepare a publisher record for NW Scheduler import.

    - Ensures array fields are never null/missing (avoids C# ArgumentNullException)
    - Removes emergencycontacts (NW Scheduler doesn't use this field on publishers)
    """
    out = dict(pub)
    out.pop("emergencycontacts", None)
    for field in PUBLISHER_ARRAY_FIELDS:
        if not isinstance(out.get(field), list):
            out[field] = []
    return out


def _build_empty_privileges() -> dict[str, list]:
    return {k: [] for k in PRIVILEGE_KEYS}


def _build_empty_attendance() -> dict[str, list]:
    return {"attendance": [], "attendanceGroups": []}


def filter_export(data: dict[str, Any], selected_ids: list[int]) -> dict[str, Any]:
    """Return an NW-Scheduler-compatible Hourglass export containing only the
    selected publishers and their associated data."""
    selected_set = set(selected_ids)

    publishers = [
        _sanitize_publisher(p)
        for p in data["publishers"]
        if p["id"] in selected_set
    ]

    # Addresses referenced by selected publishers
    needed_addr_ids = {p["address_id"] for p in publishers if p.get("address_id")}
    if "addresses" in data:
        addresses = [a for a in data["addresses"] if a["id"] in needed_addr_ids]
    else:
        addresses = []

    # Reports belonging to selected publishers
    reports = [
        r for r in data.get("reports", [])
        if r["user"]["id"] in selected_set
    ]

    # Privileges: filter to only selected publisher IDs, or empty
    if "privileges" in data:
        src_priv = data["privileges"]
        privileges = {
            k: [pid for pid in src_priv.get(k, []) if pid in selected_set]
            for k in PRIVILEGE_KEYS
        }
    else:
        privileges = _build_empty_privileges()

    return {
        "congregation": data["congregation"],
        "publishers": publishers,
        "addresses": addresses,
        "fsGroups": data.get("fsGroups", []),
        "attendance": data.get("attendance", _build_empty_attendance()),
        "reports": reports,
        "notPublishers": data.get("notPublishers", []),
        "monthlyTotals": data.get("monthlyTotals", []),
        "privileges": privileges,
        "territories": data.get("territories", []),
        "territoryRecords": data.get("territoryRecords", []),
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
