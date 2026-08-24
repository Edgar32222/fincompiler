import hashlib
from pathlib import Path


def _stage_uploads(files: dict[str, object]) -> Path:
    payloads = {name: upload.getvalue() for name, upload in files.items() if upload is not None}
    digest = hashlib.sha256(b"".join(name.encode() + payloads[name] for name in sorted(payloads))).hexdigest()[:16]
    workspace = Path(".fincompiler") / "uploads" / digest
    workspace.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (workspace / name).write_bytes(payload)
    return workspace


def render() -> None:
    import streamlit as st

    from .lineage_store import LineageStore
    from .mapping import MappingMemory, SCHEMAS
    from .pipeline import compile_pack
    from .run_state import sign_off, verify_run

    st.set_page_config(page_title="FinCompiler", layout="wide")
    st.title("FinCompiler v0.4.0-alpha.1")
    st.caption("Turn monthly finance files into explainable decisions. Uncertain mappings and rates are never silently accepted.")
    with st.expander("Choose this month's files", expanded="report" not in st.session_state):
        source_mode = st.radio("How would you like to start?", ["Try the sample company", "Upload monthly files", "Use a prepared local folder"], horizontal=True)
        uploaded_files = {}
        if source_mode == "Upload monthly files":
            uploaded_files["sales.csv"] = st.file_uploader("Sales detail", type=["csv"])
            uploaded_files["gl.csv"] = st.file_uploader("General ledger", type=["csv"])
            uploaded_files["budget.csv"] = st.file_uploader("Budget", type=["csv"])
            uploaded_files["company_config.json"] = st.file_uploader("Company policy (optional)", type=["json"])
            uploaded_files["fx_rates.csv"] = st.file_uploader("Approved exchange-rate book (optional)", type=["csv"], key="fx-upload")
            input_dir = ""
        elif source_mode == "Use a prepared local folder":
            input_dir = st.text_input("Folder containing Sales, GL and Budget files", "demo/multicurrency_close")
        else:
            input_dir = "demo/multicurrency_close"
        memory_file = st.text_input("Saved mapping memory", "mappings/memory.json")
        output_folder = st.text_input("Local run folder", "output/demo-run")
    if st.button("Check this month", type="primary"):
        try:
            if source_mode == "Upload monthly files":
                missing = [name for name in ("sales.csv", "gl.csv", "budget.csv") if uploaded_files.get(name) is None]
                if missing:
                    raise ValueError("Upload Sales, GL and Budget before running the check.")
                input_dir = str(_stage_uploads(uploaded_files))
            st.session_state.report = compile_pack(Path(input_dir), Path(output_folder), Path(memory_file))
            st.session_state.run_output_folder = output_folder
            st.session_state.active_input_dir = input_dir
        except Exception as exc:
            st.error(str(exc))
    if "report" not in st.session_state:
        return
    report = st.session_state.report
    active_output = Path(st.session_state.run_output_folder)
    active_input = Path(st.session_state.get("active_input_dir", input_dir))
    workflow = report["close_workflow"]
    st.subheader("What needs your attention this month")
    headline = st.columns(3)
    headline[0].metric("Publish readiness", report["output_readiness"])
    headline[1].metric("Tasks complete", f"{workflow['completed_tasks']} / {workflow['total_tasks']}")
    headline[2].metric("Unresolved items", len(report["exceptions"]) + len(report["reconciliation"].get("causes", [])))
    for task in workflow["tasks"]:
        icon = "✅" if task["status"] in {"COMPLETE", "NOT_NEEDED"} else "⚠️"
        with st.expander(f"{icon} {task['question']} — {task['status']}", expanded=task["status"] == "NEEDS_ACTION"):
            st.write(task["outcome"])
            st.info(task["next_action"])
    st.caption("Detected systems: " + ", ".join(f"{name}={profile}" for name, profile in report.get("source_profiles", {}).items()))
    if report["exceptions"]:
        st.subheader("Items that block publishing")
        for item in report["exceptions"]:
            with st.expander(f"{item['severity']} · {item['code']} — {item['message']}"):
                st.json(item["context"])
    st.subheader("Currency basis and applied rates")
    fx = report["fx"]
    fx_columns = st.columns(3)
    fx_columns[0].metric("Base currency", fx["base_currency"])
    fx_columns[1].metric("Converted records", fx["converted_records"])
    fx_columns[2].metric("Missing rates", fx["missing_records"])
    if fx["applications"]:
        st.dataframe(fx["applications"], use_container_width=True, hide_index=True)
    review_sets = {dataset: [proposal for proposal in proposals if proposal["status"] == "NEEDS_REVIEW"] for dataset, proposals in report["mapping_proposals"].items()}
    review_sets = {dataset: proposals for dataset, proposals in review_sets.items() if proposals}
    if review_sets:
        st.subheader("Fields that need your decision")
    for dataset, proposals in review_sets.items():
        st.markdown(f"**{dataset.title()}**")
        fields = [proposal["source_field"] for proposal in report["mapping_proposals"][dataset]]
        for index, proposal in enumerate(proposals):
            columns = st.columns([3, 3, 2, 2])
            columns[0].write(proposal["source_field"])
            options = ["(leave unmapped)"] + sorted(SCHEMAS[dataset])
            default = options.index(proposal["canonical_field"]) if proposal["canonical_field"] in options else 0
            selected = columns[1].selectbox("Canonical field", options, index=default, key=f"{dataset}-{index}", label_visibility="collapsed")
            columns[2].write(f"{proposal['status']} ({proposal['confidence']})")
            if columns[3].button("Confirm", key=f"confirm-{dataset}-{index}", disabled=selected.startswith("(")):
                MappingMemory(memory_file).confirm(dataset, proposal["source_field"], selected, fields)
                st.success(f"Saved {proposal['source_field']} → {selected} locally")
                st.session_state.report = compile_pack(active_input, active_output, Path(memory_file))
                st.rerun()
    with st.expander("Mappings used in this run"):
        mapping_rows = []
        for dataset, proposals in report["mapping_proposals"].items():
            mapping_rows.extend({"dataset": dataset, "source field": item["source_field"], "mapped field": item["canonical_field"], "status": item["status"], "confidence": item["confidence"]} for item in proposals)
        st.dataframe(mapping_rows, use_container_width=True, hide_index=True)
    st.subheader("Sales vs GL investigator")
    reconciliation = report["reconciliation"]
    recon_columns = st.columns(3)
    recon_columns[0].metric("Sales", reconciliation["sales_total"]["value"])
    recon_columns[1].metric("GL revenue", reconciliation["gl_total"]["value"])
    recon_columns[2].metric("Difference", reconciliation["variance"])
    attribution = reconciliation.get("attribution", {})
    if attribution:
        st.caption(f"Deterministically attributed: {attribution.get('percent', '0.00')}% · unexplained: {attribution.get('unexplained', '0.00')}")
    if reconciliation.get("causes"):
        st.dataframe(reconciliation["causes"], use_container_width=True, hide_index=True)
    if reconciliation.get("match_groups"):
        with st.expander(f"Matched groups ({len(reconciliation['match_groups'])})"):
            st.dataframe(reconciliation["match_groups"], use_container_width=True, hide_index=True)
    st.subheader("Budget vs Actual / PVM")
    st.dataframe(report["pvm"]["segments"], use_container_width=True, hide_index=True)
    st.caption(f"Bridge check: {report['pvm']['totals']['bridge_check']}")
    st.subheader("Source trace")
    lineage_id = st.text_input("Lineage ID", value=report["reconciliation"]["sales_total"].get("lineage_id", ""))
    trace_limit = st.number_input("Rows to retrieve", min_value=1, max_value=500, value=25)
    if st.button("Trace sources") and lineage_id:
        try:
            with LineageStore(active_output / report["lineage_store"]) as lineage:
                st.json(lineage.trace(lineage_id, int(trace_limit)))
        except KeyError as exc:
            st.error(str(exc))
    st.subheader("Finance sign-off")
    reviewer = st.text_input("Reviewer")
    signoff_notes = st.text_area("Sign-off notes")
    signoff_columns = st.columns(2)
    if signoff_columns[0].button("Sign off run"):
        try:
            st.json(sign_off(active_output, reviewer, signoff_notes))
        except Exception as exc:
            st.error(str(exc))
    if signoff_columns[1].button("Verify signed artifacts"):
        st.json(verify_run(active_output))


if __name__ == "__main__":
    render()
