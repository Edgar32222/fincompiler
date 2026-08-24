from __future__ import annotations


def build_close_workflow(exceptions: list[dict], reconciliation: dict, pvm: dict, fx_summary: dict, output_readiness: str) -> dict:
    codes = {item["code"] for item in exceptions}
    data_codes = {"MAPPING_REVIEW_REQUIRED", "SCHEMA_DRIFT", "TYPE_VALIDATION_FAILED", "DUPLICATE_SOURCE_FILE", "POTENTIAL_DUPLICATE_RECORD"}
    data_status = "NEEDS_ACTION" if codes & data_codes else "COMPLETE"
    fx_status = "NEEDS_ACTION" if fx_summary["missing_records"] else ("COMPLETE" if fx_summary["converted_records"] else "NOT_NEEDED")
    reconciliation_status = "COMPLETE" if reconciliation["status"] == "PASS" else "NEEDS_ACTION"
    pvm_status = "COMPLETE" if pvm.get("totals", {}).get("bridge_check") == "0.00" else "NEEDS_ACTION"
    publish_status = "COMPLETE" if output_readiness == "READY" else "NEEDS_ACTION"
    tasks = [
        {"id": "trust_inputs", "question": "Can I trust the files and mappings?", "status": data_status, "outcome": "All required fields are typed, mapped and free of unexplained duplicates.", "next_action": "Review only the flagged fields or duplicate groups." if data_status == "NEEDS_ACTION" else "No input action required."},
        {"id": "common_currency", "question": "Are amounts comparable in one currency?", "status": fx_status, "outcome": f"{fx_summary['converted_records']} records converted with stored rate evidence; {fx_summary['missing_records']} remain blocked.", "next_action": "Add or approve the missing dated rates." if fx_status == "NEEDS_ACTION" else "Review applied-rate evidence when material."},
        {"id": "explain_reconciliation", "question": "Why do Sales and GL differ?", "status": reconciliation_status, "outcome": f"{len(reconciliation.get('causes', []))} record-level causes identified; variance {reconciliation.get('variance')}.", "next_action": "Resolve the listed invoice or journal causes; no balancing entry is created." if reconciliation_status == "NEEDS_ACTION" else "Sales and configured revenue accounts reconcile."},
        {"id": "explain_performance", "question": "What drove performance versus budget?", "status": pvm_status, "outcome": "The deterministic Price/Volume/residual bridge balances to the reported variance.", "next_action": "Review the largest drivers and validate business context." if pvm_status == "COMPLETE" else "Resolve the PVM bridge before using the explanation."},
        {"id": "publish", "question": "Can I publish the management pack?", "status": publish_status, "outcome": "The pack is ready for Finance review and sign-off." if publish_status == "COMPLETE" else "Publishing remains blocked by unresolved control items.", "next_action": "Sign off and preserve the immutable run." if publish_status == "COMPLETE" else "Complete the NEEDS_ACTION tasks above."},
    ]
    complete = sum(item["status"] in {"COMPLETE", "NOT_NEEDED"} for item in tasks)
    return {"title": "Month-end decision workflow", "status": "READY_FOR_REVIEW" if output_readiness == "READY" else "NEEDS_ACTION", "completed_tasks": complete, "total_tasks": len(tasks), "tasks": tasks}
