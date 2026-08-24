from __future__ import annotations

import json
from pathlib import Path

from .config import FinanceConfig
from .integrity import duplicate_record_exceptions, duplicate_source_exceptions
from .ingestion import read_tabular
from .lineage_store import LineageStore
from .mapping import MappingMemory, apply_mapping
from .normalization import normalize_records
from .pvm import investigate_pvm
from .profiles import detect_profile
from .reconciliation import investigate_sales_gl
from .run_manifest import build_manifest
from .run_state import assert_writable, initialize_draft


def compile_pack(input_dir: str | Path, output_dir: str | Path, memory_path: str | Path, config_path: str | Path | None = None) -> dict:
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    assert_writable(output_dir)
    discovered_config = Path(config_path) if config_path else input_dir / "company_config.json"
    config = FinanceConfig.load(discovered_config if discovered_config.exists() else None)
    manifest = build_manifest(input_dir, config.jsonable(), discovered_config if discovered_config.exists() else None)
    memory = MappingMemory(memory_path)
    all_records, all_exceptions, proposal_dump, source_profiles = {}, [], {}, {}
    for dataset in ("sales", "gl", "budget"):
        path = input_dir / f"{dataset}.csv"
        rows = read_tabular(path)
        fields = list(rows[0][0]) if rows else []
        profile = detect_profile(dataset, fields)
        source_profiles[dataset] = profile.name if profile else "generic"
        proposals, exceptions = memory.propose(dataset, fields, profile.aliases if profile else None, profile.name if profile else "generic")
        records, mapping_exceptions = apply_mapping(dataset, rows, proposals)
        records, type_exceptions = normalize_records(records)
        all_records[dataset] = records
        all_exceptions.extend(exceptions + mapping_exceptions + type_exceptions)
        proposal_dump[dataset] = [{**p.__dict__, "confidence": str(p.confidence)} for p in proposals]
    all_exceptions.extend(duplicate_source_exceptions(manifest))
    all_exceptions.extend(duplicate_record_exceptions(all_records))
    reconciliation = investigate_sales_gl(all_records["sales"], all_records["gl"], config.reconciliation_tolerance, config.revenue_accounts, config.base_currency)
    pvm = investigate_pvm(all_records["sales"], all_records["budget"])
    output_dir.mkdir(parents=True, exist_ok=True)
    lineage_name = f"lineage-{manifest['run_id']}.sqlite"
    with LineageStore(output_dir / lineage_name, reset=True) as lineage:
        reconciliation["sales_total"] = lineage.store_calculation(f"{manifest['run_id']}:reconciliation:sales", "reconciliation", reconciliation["sales_total"])
        reconciliation["gl_total"] = lineage.store_calculation(f"{manifest['run_id']}:reconciliation:gl", "reconciliation", reconciliation["gl_total"])
        pvm["segments"] = [lineage.store_pvm_segment(f"{manifest['run_id']}:pvm:{index}", segment) for index, segment in enumerate(pvm["segments"])]
    report = {"version": "0.3.0-alpha.1", "run_manifest": manifest, "lineage_store": lineage_name, "configuration": config.jsonable(), "source_profiles": source_profiles, "mapping_proposals": proposal_dump, "exceptions": [e.__dict__ for e in all_exceptions], "reconciliation": reconciliation, "pvm": pvm, "output_readiness": "BLOCKED" if all_exceptions or reconciliation["status"] != "PASS" else "READY"}
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "management_pack.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    initialize_draft(output_dir, manifest["run_id"])
    return report
