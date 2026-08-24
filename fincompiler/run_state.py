from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .run_manifest import sha256_file


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def read_state(run_dir: str | Path) -> dict | None:
    path = Path(run_dir) / "run_state.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def assert_writable(run_dir: str | Path) -> None:
    state = read_state(run_dir)
    if state and state.get("status") == "SIGNED_OFF":
        raise RuntimeError(f"Run {state.get('run_id')} is signed off and cannot be overwritten. Choose a new output directory.")


def initialize_draft(run_dir: str | Path, run_id: str) -> dict:
    state = {"run_id": run_id, "status": "DRAFT", "updated_at_utc": datetime.now(timezone.utc).isoformat()}
    _atomic_json(Path(run_dir) / "run_state.json", state)
    return state


def sign_off(run_dir: str | Path, reviewer: str, notes: str = "") -> dict:
    directory = Path(run_dir)
    reviewer = reviewer.strip()
    if not reviewer:
        raise ValueError("reviewer is required")
    state = read_state(directory)
    if not state:
        raise FileNotFoundError("run_state.json not found; compile the run before sign-off")
    if state.get("status") == "SIGNED_OFF":
        raise RuntimeError("run is already signed off")
    manifest = json.loads((directory / "run_manifest.json").read_text(encoding="utf-8"))
    pack = json.loads((directory / "management_pack.json").read_text(encoding="utf-8"))
    if manifest["run_id"] != state["run_id"] or pack["run_manifest"]["run_id"] != state["run_id"]:
        raise RuntimeError("run ID mismatch between state, manifest and management pack")
    artifacts = {}
    for path in sorted(directory.glob("*")):
        if path.is_file() and path.name not in {"run_state.json"} and not path.name.endswith(".tmp"):
            artifacts[path.name] = sha256_file(path)
    signed = {**state, "status": "SIGNED_OFF", "reviewer": reviewer, "notes": notes, "signed_at_utc": datetime.now(timezone.utc).isoformat(), "artifact_sha256": artifacts}
    _atomic_json(directory / "run_state.json", signed)
    return signed


def verify_run(run_dir: str | Path) -> dict:
    directory = Path(run_dir)
    state = read_state(directory)
    if not state:
        return {"valid": False, "reason": "run_state.json not found"}
    if state.get("status") != "SIGNED_OFF":
        return {"valid": False, "reason": "run is not signed off", "status": state.get("status")}
    mismatches = []
    for name, expected in state.get("artifact_sha256", {}).items():
        path = directory / name
        actual = sha256_file(path) if path.exists() else None
        if actual != expected:
            mismatches.append({"artifact": name, "expected": expected, "actual": actual})
    return {"valid": not mismatches, "run_id": state.get("run_id"), "reviewer": state.get("reviewer"), "mismatches": mismatches}

