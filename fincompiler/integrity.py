from __future__ import annotations

import json
from collections import defaultdict

from .models import CanonicalRecord, ExceptionItem


def duplicate_source_exceptions(manifest: dict) -> list[ExceptionItem]:
    by_hash = defaultdict(list)
    for source in manifest["sources"]:
        if source["dataset"] not in {"sales", "gl", "budget"}:
            continue
        by_hash[source["sha256"]].append(source["dataset"])
    return [ExceptionItem("DUPLICATE_SOURCE_FILE", "BLOCKING", "The same file content was supplied for multiple datasets", {"datasets": datasets, "sha256": digest}) for digest, datasets in by_hash.items() if len(datasets) > 1]


def duplicate_record_exceptions(records_by_dataset: dict[str, list[CanonicalRecord]]) -> list[ExceptionItem]:
    exceptions = []
    for dataset, records in records_by_dataset.items():
        if dataset == "budget":
            continue  # repeated dimensional budget rows can be legitimate before aggregation
        signatures = defaultdict(list)
        for record in records:
            signature = json.dumps(record.values, sort_keys=True, default=str, ensure_ascii=False)
            source_rows = sorted({(source.file, source.sheet, source.row) for source in record.lineage.values()})
            signatures[signature].append({"record_id": record.record_id, "source_rows": source_rows})
        duplicates = [items for items in signatures.values() if len(items) > 1]
        if duplicates:
            exceptions.append(ExceptionItem("POTENTIAL_DUPLICATE_RECORD", "BLOCKING", "Identical canonical records require review before publishing", {"dataset": dataset, "duplicate_groups": duplicates}))
    return exceptions
