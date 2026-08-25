from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from . import __version__


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    input_dir: str | Path,
    config: dict,
    config_path: str | Path | None = None,
    evidence_files: list[tuple[str, str | Path]] | None = None,
    dataset_files: dict[str, str | Path] | None = None,
) -> dict:
    input_dir = Path(input_dir)
    sources = []
    resolved_dataset_files = dataset_files or {dataset: input_dir / f"{dataset}.csv" for dataset in ("sales", "gl", "budget")}
    for dataset in resolved_dataset_files:
        path = Path(resolved_dataset_files[dataset])
        sources.append({"dataset": dataset, "file": str(path.resolve()), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    for dataset, raw_path in evidence_files or []:
        path = Path(raw_path)
        sources.append({"dataset": dataset, "file": str(path.resolve()), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    identity = json.dumps({"engine_version": __version__, "sources": [(item["dataset"], item["sha256"]) for item in sources], "config_sha256": config_hash}, sort_keys=True)
    run_id = hashlib.sha256(identity.encode()).hexdigest()[:16]
    return {"run_id": run_id, "created_at_utc": datetime.now(timezone.utc).isoformat(), "engine_version": __version__, "sources": sources, "config_file": str(Path(config_path).resolve()) if config_path else None, "config_sha256": config_hash}
