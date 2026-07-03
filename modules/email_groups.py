"""Agentic OS — Email Groups Module
Manage email distribution groups for Grand Rounds and Resident Conference.
Stored in data/email_groups.json, consumed by send_grand_rounds_email.py
and send_monday_sasp_email.py."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/email-groups", tags=["email-groups"])

GROUPS_FILE = Path(__file__).resolve().parent.parent / "data" / "email_groups.json"

DEFAULT_GROUPS = {
    "grand_rounds": {
        "label": "Grand Rounds (Fridays)",
        "emails": [],
        "test_mode": True,
        "test_email": "sfrasier@montefiore.org",
    },
    "resident_conference": {
        "label": "Resident Conference (Mondays)",
        "emails": [],
        "test_mode": True,
        "test_email": "sfrasier@montefiore.org",
    },
}


def _load():
    if GROUPS_FILE.exists():
        with open(GROUPS_FILE) as f:
            return json.load(f)
    _save(DEFAULT_GROUPS)
    return dict(DEFAULT_GROUPS)


def _save(data):
    GROUPS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GROUPS_FILE, "w") as f:
        json.dump(data, f, indent=2)


class GroupUpdate(BaseModel):
    emails: list[str] | None = None
    test_mode: bool | None = None
    test_email: str | None = None


@router.get("")
def get_groups():
    return _load()


@router.put("/{group_key}")
def update_group(group_key: str, update: GroupUpdate):
    if group_key not in DEFAULT_GROUPS:
        raise HTTPException(404, f"Unknown group: {group_key}")
    data = _load()
    if update.emails is not None:
        data[group_key]["emails"] = update.emails
    if update.test_mode is not None:
        data[group_key]["test_mode"] = update.test_mode
    if update.test_email is not None:
        data[group_key]["test_email"] = update.test_email
    _save(data)
    return data[group_key]
