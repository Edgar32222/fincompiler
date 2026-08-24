from __future__ import annotations

import hashlib
import json
from pathlib import Path


DATASET_LABELS = {"sales": "Sales detail", "gl": "General ledger", "budget": "Budget"}


def _upload_target(logical_name: str, upload: object) -> str:
    if logical_name in DATASET_LABELS:
        suffix = Path(getattr(upload, "name", "")).suffix.lower()
        if suffix not in {".csv", ".xlsx", ".xlsm"}:
            raise ValueError(f"{DATASET_LABELS[logical_name]} must be a CSV or Excel workbook.")
        return f"{logical_name}{suffix}"
    if logical_name == "company_config":
        return "company_config.json"
    if logical_name == "fx_rates":
        return "fx_rates.csv"
    raise ValueError(f"Unknown upload role: {logical_name}")


def _stage_uploads(files: dict[str, object]) -> Path:
    present = {name: upload for name, upload in files.items() if upload is not None}
    payloads = {name: upload.getvalue() for name, upload in present.items()}
    identity = b"".join(
        name.encode() + _upload_target(name, present[name]).encode() + payloads[name]
        for name in sorted(payloads)
    )
    digest = hashlib.sha256(identity).hexdigest()[:16]
    workspace = Path(".fincompiler") / "uploads" / digest
    workspace.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (workspace / _upload_target(name, present[name])).write_bytes(payload)
    return workspace


def _exception_action(code: str) -> str:
    actions = {
        "MAPPING_REVIEW_REQUIRED": "Confirm only the flagged source fields below, then run the check again.",
        "SCHEMA_DRIFT": "Compare the new headers with last month's export and confirm intentional changes.",
        "TYPE_VALIDATION_FAILED": "Correct the listed date, currency or amount cells in the source export; FinCompiler did not guess them.",
        "FX_RATE_REQUIRED": "Add an approved dated rate to the company rate book, then rerun this month.",
        "POTENTIAL_DUPLICATE_RECORD": "Check the listed source rows and remove or explain duplicates before publishing.",
        "DUPLICATE_SOURCE_FILE": "Use distinct source files for Sales, GL and Budget; identical files are blocked.",
    }
    return actions.get(code, "Review the evidence and resolve the source item before publishing.")


def _status_icon(status: str) -> str:
    return "✅" if status in {"COMPLETE", "NOT_NEEDED"} else "⚠️"


def render() -> None:
    import streamlit as st

    from . import __version__
    from .lineage_store import LineageStore
    from .mapping import MappingMemory, SCHEMAS
    from .pipeline import compile_pack
    from .run_state import sign_off, verify_run

    st.set_page_config(page_title="FinCompiler", page_icon="✓", layout="wide")
    st.title("FinCompiler")
    st.caption(f"Month-end reconciliation and performance investigation · v{__version__}")
    st.info("Local-first: your files, mapping decisions, exchange-rate evidence and outputs stay on this computer.")

    if "report" not in st.session_state:
        st.markdown("### 1 · Choose this month's files")
    with st.container(border=True):
        source_mode = st.radio(
            "How would you like to start?",
            ["Try the sample company", "Upload monthly files", "Use a prepared local folder"],
            horizontal=True,
        )
        uploaded_files: dict[str, object] = {}
        if source_mode == "Upload monthly files":
            st.caption("Choose each file by business role. Original filenames do not need to match FinCompiler names.")
            upload_columns = st.columns(3)
            uploaded_files["sales"] = upload_columns[0].file_uploader(
                "Sales detail · required", type=["csv", "xlsx", "xlsm"], help="Invoice or sales line detail."
            )
            uploaded_files["gl"] = upload_columns[1].file_uploader(
                "General ledger · required", type=["csv", "xlsx", "xlsm"], help="Revenue-account journal detail."
            )
            uploaded_files["budget"] = upload_columns[2].file_uploader(
                "Budget · required", type=["csv", "xlsx", "xlsm"], help="Customer/SKU plan used for the deterministic bridge."
            )
            with st.expander("Optional company policy and exchange rates"):
                uploaded_files["company_config"] = st.file_uploader("Company policy", type=["json"])
                uploaded_files["fx_rates"] = st.file_uploader("Approved exchange-rate book", type=["csv"], key="fx-upload")
            input_dir = ""
        elif source_mode == "Use a prepared local folder":
            input_dir = st.text_input(
                "Folder containing Sales, GL and Budget",
                "demo/multicurrency_close",
                help="Use sales.csv/xlsx, gl.csv/xlsx and budget.csv/xlsx. FinCompiler blocks duplicates instead of guessing.",
            )
        else:
            input_dir = "demo/multicurrency_close"
            st.caption("The sample contains multi-currency Sales, Dynamics-style GL, Budget and approved rate evidence.")

        with st.expander("Advanced local storage options"):
            memory_file = st.text_input("Saved mapping memory", "mappings/memory.json")
            output_folder = st.text_input("Local run folder", "output/demo-run")
        run_clicked = st.button("Run month-end check", type="primary", width="stretch")

    if run_clicked:
        try:
            if source_mode == "Upload monthly files":
                missing = [DATASET_LABELS[name] for name in DATASET_LABELS if uploaded_files.get(name) is None]
                if missing:
                    raise ValueError("Choose all three required files: " + ", ".join(missing))
                input_dir = str(_stage_uploads(uploaded_files))
            with st.spinner("Reading source files and running deterministic controls…"):
                st.session_state.report = compile_pack(Path(input_dir), Path(output_folder), Path(memory_file))
            st.session_state.run_output_folder = output_folder
            st.session_state.active_input_dir = input_dir
        except Exception as exc:
            st.error(f"This run was not changed or published: {exc}")
            with st.expander("What to check"):
                st.write("Use one Sales, one GL and one Budget table. Keep one consistent header row per file. CSV and XLSX are supported.")

    if "report" not in st.session_state:
        st.markdown("### What FinCompiler will do")
        value_columns = st.columns(4)
        value_columns[0].write("**1. Validate**\n\nHeaders, dates, amounts, currencies and duplicates")
        value_columns[1].write("**2. Reconcile**\n\nSales detail to configured GL revenue")
        value_columns[2].write("**3. Explain**\n\nRecord-level causes and deterministic budget bridge")
        value_columns[3].write("**4. Preserve**\n\nSource lineage, rate evidence and Finance sign-off")
        return

    report = st.session_state.report
    active_output = Path(st.session_state.run_output_folder)
    active_input = Path(st.session_state.get("active_input_dir", input_dir))
    workflow = report["close_workflow"]
    readiness = report["output_readiness"]

    st.markdown("### 2 · Review the result")
    if readiness == "READY":
        st.success("READY FOR FINANCE REVIEW — all blocking controls passed. No balancing entry was created.")
    else:
        st.warning("BLOCKED — resolve the items below before sign-off or publishing.")
    headline = st.columns(4)
    headline[0].metric("Publish readiness", readiness)
    headline[1].metric("Controls complete", f"{workflow['completed_tasks']} / {workflow['total_tasks']}")
    headline[2].metric("Blocking items", len(report["exceptions"]))
    headline[3].metric("Sales / GL difference", report["reconciliation"]["variance"])

    download_columns = st.columns([1, 1, 2])
    pack_bytes = json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")
    download_columns[0].download_button(
        "Download Management Pack",
        pack_bytes,
        file_name=f"fincompiler-{report['run_manifest']['run_id']}.json",
        mime="application/json",
        width="stretch",
    )
    html_bytes = (active_output / report["management_pack_html"]).read_bytes()
    download_columns[1].download_button(
        "Download readable HTML",
        html_bytes,
        file_name=f"fincompiler-{report['run_manifest']['run_id']}.html",
        mime="text/html",
        width="stretch",
    )
    download_columns[2].caption(f"Run ID: {report['run_manifest']['run_id']}")

    action_tab, reconciliation_tab, performance_tab, audit_tab, signoff_tab = st.tabs(
        ["Action plan", "Sales vs GL", "Budget vs Actual", "Audit trail", "Finance sign-off"]
    )

    with action_tab:
        for task in workflow["tasks"]:
            with st.expander(
                f"{_status_icon(task['status'])} {task['question']} — {task['status']}",
                expanded=task["status"] == "NEEDS_ACTION",
            ):
                st.write(task["outcome"])
                st.info(task["next_action"])

        review_sets = {
            dataset: [proposal for proposal in proposals if proposal["status"] == "NEEDS_REVIEW"]
            for dataset, proposals in report["mapping_proposals"].items()
        }
        review_sets = {dataset: proposals for dataset, proposals in review_sets.items() if proposals}
        if review_sets:
            st.subheader("Fields that need your decision")
            st.caption("Nothing is mapped until you choose a canonical finance field and confirm it.")
        for dataset, proposals in review_sets.items():
            st.markdown(f"**{DATASET_LABELS[dataset]}**")
            fields = [proposal["source_field"] for proposal in report["mapping_proposals"][dataset]]
            for index, proposal in enumerate(proposals):
                columns = st.columns([3, 3, 2, 2])
                columns[0].write(proposal["source_field"])
                options = ["(leave unmapped)"] + sorted(SCHEMAS[dataset])
                default = options.index(proposal["canonical_field"]) if proposal["canonical_field"] in options else 0
                selected = columns[1].selectbox(
                    "Canonical field",
                    options,
                    index=default,
                    key=f"{dataset}-{index}",
                    label_visibility="collapsed",
                )
                columns[2].write(f"{proposal['status']} ({proposal['confidence']})")
                if columns[3].button("Confirm", key=f"confirm-{dataset}-{index}", disabled=selected.startswith("(")):
                    MappingMemory(memory_file).confirm(dataset, proposal["source_field"], selected, fields)
                    st.success(f"Saved {proposal['source_field']} → {selected} locally")
                    st.session_state.report = compile_pack(active_input, active_output, Path(memory_file))
                    st.rerun()

        if report["exceptions"]:
            st.subheader("Blocking control items")
            for item in report["exceptions"]:
                with st.expander(f"{item['severity']} · {item['code']} — {item['message']}"):
                    st.warning(_exception_action(item["code"]))
                    st.json(item["context"])

        st.subheader("Currency basis")
        fx = report["fx"]
        fx_columns = st.columns(3)
        fx_columns[0].metric("Base currency", fx["base_currency"])
        fx_columns[1].metric("Converted records", fx["converted_records"])
        fx_columns[2].metric("Missing approved rates", fx["missing_records"])
        if fx["applications"]:
            st.dataframe(fx["applications"], width="stretch", hide_index=True)

    with reconciliation_tab:
        reconciliation = report["reconciliation"]
        recon_columns = st.columns(3)
        recon_columns[0].metric("Sales", reconciliation["sales_total"]["value"])
        recon_columns[1].metric("GL revenue", reconciliation["gl_total"]["value"])
        recon_columns[2].metric("Difference", reconciliation["variance"])
        attribution = reconciliation.get("attribution", {})
        if attribution:
            st.caption(
                f"Deterministically attributed: {attribution.get('percent', '0.00')}% · "
                f"unexplained: {attribution.get('unexplained', '0.00')}"
            )
        if reconciliation.get("causes"):
            st.subheader("Records and causes to investigate")
            st.dataframe(reconciliation["causes"], width="stretch", hide_index=True)
        else:
            st.success("Configured Sales and GL revenue reconcile.")
        if reconciliation.get("match_groups"):
            with st.expander(f"Matched groups ({len(reconciliation['match_groups'])})"):
                st.dataframe(reconciliation["match_groups"], width="stretch", hide_index=True)

    with performance_tab:
        st.caption("All amounts are calculated with Decimal. Any later narrative can explain these results but cannot change them.")
        pvm_totals = report["pvm"]["totals"]
        pvm_columns = st.columns(4)
        pvm_columns[0].metric("Revenue variance", pvm_totals.get("variance", "0.00"))
        pvm_columns[1].metric("Volume", pvm_totals.get("volume", "0.00"))
        pvm_columns[2].metric("Price", pvm_totals.get("price", "0.00"))
        pvm_columns[3].metric("Mix / residual", pvm_totals.get("mix_residual", "0.00"))
        st.dataframe(report["pvm"]["segments"], width="stretch", hide_index=True)
        st.caption(f"Bridge check (must be zero): {pvm_totals['bridge_check']}")

    with audit_tab:
        st.caption("Every total can be traced to local file, worksheet, row, source field and raw value.")
        lineage_id = st.text_input(
            "Lineage ID",
            value=report["reconciliation"]["sales_total"].get("lineage_id", ""),
        )
        trace_limit = st.number_input("Rows to retrieve", min_value=1, max_value=500, value=25)
        if st.button("Trace source rows") and lineage_id:
            try:
                with LineageStore(active_output / report["lineage_store"]) as lineage:
                    st.json(lineage.trace(lineage_id, int(trace_limit)))
            except KeyError as exc:
                st.error(str(exc))
        with st.expander("Mappings used in this run"):
            mapping_rows = []
            for dataset, proposals in report["mapping_proposals"].items():
                mapping_rows.extend(
                    {
                        "dataset": DATASET_LABELS[dataset],
                        "source field": item["source_field"],
                        "mapped field": item["canonical_field"],
                        "status": item["status"],
                        "confidence": item["confidence"],
                    }
                    for item in proposals
                )
            st.dataframe(mapping_rows, width="stretch", hide_index=True)
        with st.expander("Source files and evidence hashes"):
            st.dataframe(report["run_manifest"]["sources"], width="stretch", hide_index=True)

    with signoff_tab:
        if readiness != "READY":
            st.warning("Sign-off is disabled until every blocking control passes.")
        reviewer = st.text_input("Reviewer", disabled=readiness != "READY")
        signoff_notes = st.text_area("Sign-off notes", disabled=readiness != "READY")
        signoff_columns = st.columns(2)
        if signoff_columns[0].button("Sign off immutable run", disabled=readiness != "READY"):
            try:
                st.json(sign_off(active_output, reviewer, signoff_notes))
            except Exception as exc:
                st.error(str(exc))
        if signoff_columns[1].button("Verify signed artifacts"):
            st.json(verify_run(active_output))


if __name__ == "__main__":
    render()
