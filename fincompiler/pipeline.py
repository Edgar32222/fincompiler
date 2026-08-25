from __future__ import annotations

import json
from pathlib import Path

from . import __version__
from .config import FinanceConfig
from .exception_workflow import initialize_exception_workflow
from .fx import RateBook, establish_currency_basis
from .integrity import duplicate_record_exceptions, duplicate_source_exceptions
from .ingestion import discover_dataset_files, read_tabular
from .lineage_store import LineageStore
from .mapping import MappingMemory, apply_mapping
from .normalization import normalize_records
from .pvm import investigate_pvm
from .profiles import detect_profile
from .reconciliation import investigate_sales_gl
from .reporting import write_management_pack_excel, write_management_pack_html
from .run_manifest import build_manifest
from .run_state import assert_writable, initialize_draft
from .workflow import build_close_workflow


def compile_pack(input_dir: str | Path, output_dir: str | Path, memory_path: str | Path, config_path: str | Path | None = None) -> dict:
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    assert_writable(output_dir)
    dataset_files = discover_dataset_files(input_dir)
    discovered_config = Path(config_path) if config_path else input_dir / "company_config.json"
    config = FinanceConfig.load(discovered_config if discovered_config.exists() else None)
    rate_book_path = None
    if config.fx_rate_book:
        candidate = Path(config.fx_rate_book)
        rate_book_path = candidate if candidate.is_absolute() else (discovered_config.parent if discovered_config.exists() else input_dir) / candidate
        if not rate_book_path.exists():
            raise FileNotFoundError(f"Configured FX rate book not found: {rate_book_path}")
    manifest = build_manifest(
        input_dir,
        config.jsonable(),
        discovered_config if discovered_config.exists() else None,
        [("fx_rate_book", rate_book_path)] if rate_book_path else None,
        dataset_files,
    )
    memory = MappingMemory(memory_path)
    all_records, all_exceptions, proposal_dump, source_profiles = {}, [], {}, {}
    for dataset in ("sales", "gl", "budget"):
        path = dataset_files[dataset]
        rows = read_tabular(path)
        fields = list(rows[0][0]) if rows else []
        inconsistent = sorted({tuple(row.keys()) for row, _ in rows if list(row.keys()) != fields})
        if inconsistent:
            raise ValueError(
                f"{path.name} contains inconsistent column layouts across rows or worksheets. "
                "Keep one table with one header layout per Sales, GL or Budget file."
            )
        profile = detect_profile(dataset, fields)
        source_profiles[dataset] = profile.name if profile else "generic"
        proposals, exceptions = memory.propose(dataset, fields, profile.aliases if profile else None, profile.name if profile else "generic", profile.ignored_fields if profile else None)
        records, mapping_exceptions = apply_mapping(dataset, rows, proposals)
        records, type_exceptions = normalize_records(records)
        all_records[dataset] = records
        all_exceptions.extend(exceptions + mapping_exceptions + type_exceptions)
        proposal_dump[dataset] = [{**p.__dict__, "confidence": str(p.confidence)} for p in proposals]
    all_exceptions.extend(duplicate_source_exceptions(manifest))
    all_exceptions.extend(duplicate_record_exceptions(all_records))
    rate_book = RateBook.load(rate_book_path) if rate_book_path else None
    fx_applications = []
    for dataset in ("sales", "gl"):
        all_records[dataset], fx_exceptions, applications = establish_currency_basis(all_records[dataset], dataset, config.base_currency, rate_book, config.fx_policy)
        all_exceptions.extend(fx_exceptions)
        fx_applications.extend(applications)
    reconciliation = investigate_sales_gl(all_records["sales"], all_records["gl"], config.reconciliation_tolerance, config.revenue_accounts, config.base_currency)
    pvm = investigate_pvm(all_records["sales"], all_records["budget"])
    output_dir.mkdir(parents=True, exist_ok=True)
    lineage_name = f"lineage-{manifest['run_id']}.sqlite"
    with LineageStore(output_dir / lineage_name, reset=True) as lineage:
        reconciliation["sales_total"] = lineage.store_calculation(f"{manifest['run_id']}:reconciliation:sales", "reconciliation", reconciliation["sales_total"])
        reconciliation["gl_total"] = lineage.store_calculation(f"{manifest['run_id']}:reconciliation:gl", "reconciliation", reconciliation["gl_total"])
        pvm["segments"] = [lineage.store_pvm_segment(f"{manifest['run_id']}:pvm:{index}", segment) for index, segment in enumerate(pvm["segments"])]
    exception_dump = [e.__dict__ for e in all_exceptions] + list(reconciliation.get("exceptions", []))
    output_readiness = "BLOCKED" if all_exceptions or reconciliation["status"] != "PASS" else "READY"
    fx_summary = {"base_currency": config.base_currency, "rate_type": config.fx_policy.rate_type, "rate_book": str(rate_book_path.resolve()) if rate_book_path else None, "converted_records": len(fx_applications), "missing_records": sum(item["code"] == "FX_RATE_REQUIRED" for item in exception_dump), "applications": fx_applications}
    workflow = build_close_workflow(exception_dump, reconciliation, pvm, fx_summary, output_readiness)
    exception_workflow = initialize_exception_workflow(output_dir, manifest["run_id"], exception_dump)
    report = {"version": __version__, "run_manifest": manifest, "lineage_store": lineage_name, "management_pack_html": "management_pack.html", "management_pack_excel": "management_pack.xlsx", "exception_workflow_file": "exception_workflow.json", "exception_workflow_summary": {"active_count": exception_workflow["active_count"], "cleared_count": exception_workflow["cleared_count"], "trust_rule": exception_workflow["trust_rule"]}, "configuration": config.jsonable(), "source_profiles": source_profiles, "mapping_proposals": proposal_dump, "exceptions": exception_dump, "fx": fx_summary, "reconciliation": reconciliation, "pvm": pvm, "close_workflow": workflow, "output_readiness": output_readiness}
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "management_pack.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_management_pack_html(output_dir, report)
    write_management_pack_excel(output_dir, report, exception_workflow)
    initialize_draft(output_dir, manifest["run_id"])
    return report
