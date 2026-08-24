from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


USER_STATUSES = ("OPEN", "INVESTIGATING", "WAITING_FOR_SOURCE_FIX", "READY_TO_RERUN")
SYSTEM_CLEARED_STATUS = "CLEARED_BY_RERUN"
WORKFLOW_FILENAME = "exception_workflow.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def exception_id(item: dict[str, Any]) -> str:
    """Return a stable ID for the same engine exception and source evidence."""
    identity = {
        "code": item.get("code"),
        "severity": item.get("severity"),
        "message": item.get("message"),
        "context": item.get("context", {}),
    }
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:20]


def read_exception_workflow(run_dir: str | Path) -> dict[str, Any] | None:
    path = Path(run_dir) / WORKFLOW_FILENAME
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def initialize_exception_workflow(
    run_dir: str | Path,
    run_id: str,
    exceptions: list[dict[str, Any]],
    *,
    now: str | None = None,
) -> dict[str, Any]:
    """Merge engine exceptions with local handling state without letting users clear controls."""
    directory = Path(run_dir)
    timestamp = now or _utc_now()
    previous = read_exception_workflow(directory)
    previous_items = {
        item["exception_id"]: item
        for item in (previous or {}).get("items", [])
        if item.get("exception_id")
    }
    active_ids: set[str] = set()
    merged: list[dict[str, Any]] = []

    for source in exceptions:
        item_id = exception_id(source)
        active_ids.add(item_id)
        existing = previous_items.get(item_id, {})
        status = existing.get("status")
        history = list(existing.get("history", []))
        reopened = status == SYSTEM_CLEARED_STATUS
        if status not in USER_STATUSES:
            status = "OPEN"
        if reopened:
            history.append(
                {
                    "at_utc": timestamp,
                    "actor": "FinCompiler",
                    "from_status": SYSTEM_CLEARED_STATUS,
                    "to_status": "OPEN",
                    "owner": existing.get("owner", ""),
                    "note": "The deterministic exception appeared again on rerun.",
                    "evidence_reference": existing.get("evidence_reference", ""),
                }
            )
        merged.append(
            {
                "exception_id": item_id,
                "active": True,
                "status": status,
                "owner": existing.get("owner", ""),
                "note": existing.get("note", ""),
                "evidence_reference": existing.get("evidence_reference", ""),
                "code": source.get("code"),
                "severity": source.get("severity"),
                "message": source.get("message"),
                "context": source.get("context", {}),
                "first_seen_at_utc": existing.get("first_seen_at_utc", timestamp),
                "updated_at_utc": timestamp if reopened else existing.get("updated_at_utc", timestamp),
                "cleared_at_utc": None,
                "history": history,
            }
        )

    for item_id, existing in previous_items.items():
        if item_id in active_ids:
            continue
        cleared = dict(existing)
        history = list(existing.get("history", []))
        if existing.get("status") != SYSTEM_CLEARED_STATUS:
            history.append(
                {
                    "at_utc": timestamp,
                    "actor": "FinCompiler",
                    "from_status": existing.get("status", "OPEN"),
                    "to_status": SYSTEM_CLEARED_STATUS,
                    "owner": existing.get("owner", ""),
                    "note": "The exception was absent from the deterministic rerun.",
                    "evidence_reference": existing.get("evidence_reference", ""),
                }
            )
        cleared.update(
            {
                "active": False,
                "status": SYSTEM_CLEARED_STATUS,
                "cleared_at_utc": existing.get("cleared_at_utc") or timestamp,
                "updated_at_utc": timestamp,
                "history": history,
            }
        )
        merged.append(cleared)

    merged.sort(key=lambda item: (not item["active"], item.get("severity", ""), item["exception_id"]))
    payload = {
        "run_id": run_id,
        "trust_rule": "Only a deterministic rerun can clear an exception.",
        "active_count": sum(item["active"] for item in merged),
        "cleared_count": sum(not item["active"] for item in merged),
        "updated_at_utc": timestamp,
        "items": merged,
    }
    _atomic_json(directory / WORKFLOW_FILENAME, payload)
    return payload


def update_exception_item(
    run_dir: str | Path,
    item_id: str,
    *,
    status: str,
    owner: str = "",
    note: str = "",
    evidence_reference: str = "",
    actor: str = "",
    now: str | None = None,
) -> dict[str, Any]:
    if status not in USER_STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(USER_STATUSES)}")
    owner = owner.strip()
    if status != "OPEN" and not owner:
        raise ValueError("Assign an owner before moving an exception out of OPEN.")
    path = Path(run_dir) / WORKFLOW_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"{WORKFLOW_FILENAME} not found; compile the run first")
    payload = json.loads(path.read_text(encoding="utf-8"))
    item = next((candidate for candidate in payload.get("items", []) if candidate.get("exception_id") == item_id), None)
    if item is None:
        raise KeyError(f"Unknown exception ID: {item_id}")
    if not item.get("active"):
        raise RuntimeError("A cleared exception is read-only. Rerun the source data to create a new active item.")

    timestamp = now or _utc_now()
    action = {
        "at_utc": timestamp,
        "actor": actor.strip(),
        "from_status": item.get("status", "OPEN"),
        "to_status": status,
        "owner": owner,
        "note": note.strip(),
        "evidence_reference": evidence_reference.strip(),
    }
    item.update(
        {
            "status": status,
            "owner": owner,
            "note": note.strip(),
            "evidence_reference": evidence_reference.strip(),
            "updated_at_utc": timestamp,
        }
    )
    item.setdefault("history", []).append(action)
    payload["updated_at_utc"] = timestamp
    _atomic_json(path, payload)
    return item
