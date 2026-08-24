from pathlib import Path


def render() -> None:
    import streamlit as st

    from .lineage_store import LineageStore
    from .mapping import MappingMemory, SCHEMAS
    from .pipeline import compile_pack
    from .run_state import sign_off, verify_run

    st.set_page_config(page_title="FinCompiler", layout="wide")
    st.title("FinCompiler v0.3.0-alpha.1")
    st.caption("Local-first finance compilation. Uncertain mappings are never silently accepted.")
    input_dir = st.text_input("Input folder", "demo/nova_appliances")
    memory_file = st.text_input("Mapping memory", "mappings/memory.json")
    config_file = st.text_input("Company configuration (optional)", "")
    output_folder = st.text_input("Output folder", "output/demo-run")
    if st.button("Compile and investigate"):
        try:
            st.session_state.report = compile_pack(Path(input_dir), Path(output_folder), Path(memory_file), Path(config_file) if config_file else None)
            st.session_state.run_output_folder = output_folder
        except Exception as exc:
            st.error(str(exc))
    if "report" not in st.session_state:
        return
    report = st.session_state.report
    active_output = Path(st.session_state.run_output_folder)
    st.metric("Output readiness", report["output_readiness"])
    st.caption("Detected source profiles: " + ", ".join(f"{name}={profile}" for name, profile in report.get("source_profiles", {}).items()))
    if report["exceptions"]:
        st.subheader("Blocking and review exceptions")
        st.json(report["exceptions"])
    st.subheader("Mapping review")
    for dataset, proposals in report["mapping_proposals"].items():
        st.markdown(f"**{dataset}**")
        fields = [proposal["source_field"] for proposal in proposals]
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
                st.session_state.report = compile_pack(Path(input_dir), active_output, Path(memory_file), Path(config_file) if config_file else None)
                st.rerun()
    st.subheader("Sales vs GL investigator")
    st.json(report["reconciliation"])
    st.subheader("Budget vs Actual / PVM")
    st.json(report["pvm"])
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

