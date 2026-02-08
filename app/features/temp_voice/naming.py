from __future__ import annotations

import re


def _sanitize_name(name: str) -> str:
    collapsed = re.sub(r"\s+", " ", name).strip()
    return collapsed or "Room"


def owner_room_name(display_name: str) -> str:
    base = _sanitize_name(display_name)
    room_name = f"{base}'s room"
    return room_name[:100]


def numbered_room_name(number: int) -> str:
    return f"Talk {number}"
