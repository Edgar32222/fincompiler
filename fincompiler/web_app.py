from __future__ import annotations

import hashlib
import json
import os
import shutil
from decimal import Decimal
from pathlib import Path


DATASET_LABELS = {
    "sales": "Sales detail", "gl": "General ledger", "budget": "Budget",
    "amazon_settlements": "Amazon Settlement V2", "shopify_orders": "Shopify orders",
    "shopify_payouts": "Shopify payouts", "bank": "Bank statement", "sku_costs": "SKU landed costs",
}


def _resource_root() -> Path:
    return Path(os.environ.get("FINCOMPILER_RESOURCE_DIR", ".")).resolve()


def _data_root() -> Path:
    return Path(os.environ.get("FINCOMPILER_DATA_DIR", ".")).resolve()


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
    workspace = _data_root() / ".fincompiler" / "uploads" / digest
    workspace.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (workspace / _upload_target(name, present[name])).write_bytes(payload)
    return workspace


def _write_company_config(
    workspace: Path,
    company_name: str,
    base_currency: str,
    revenue_accounts_text: str,
    tolerance_text: str,
    fx_rate_book: str | None,
    rate_type: str,
) -> Path:
    accounts = [item.strip() for item in revenue_accounts_text.replace(";", ",").replace("\n", ",").split(",") if item.strip()]
    if not accounts:
        raise ValueError("Enter at least one GL revenue account name or code.")
    tolerance = Decimal(tolerance_text)
    if tolerance < 0:
        raise ValueError("Reconciliation tolerance cannot be negative.")
    payload = {
        "company_name": company_name.strip() or "Unnamed company",
        "base_currency": base_currency,
        "revenue_accounts": accounts,
        "reconciliation_tolerance": str(tolerance),
        "fx_rate_book": fx_rate_book,
        "fx_policy": {
            "rate_type": rate_type,
            "max_lookback_days": 7,
            "allow_inverse": True,
            "allow_cross": True,
            "triangulation_currency": "EUR",
            "prefer_accounting_currency_amount": True,
        },
    }
    path = workspace / "company_config.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _refresh_ecb_with_fallback(target: Path, refresh_fn) -> dict:
    try:
        return refresh_fn(target, "90d")
    except RuntimeError as exc:
        result = refresh_fn(target, "daily")
        result["fallback_reason"] = str(exc)
        return result


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


def _render_commerce(st, resource_root: Path, data_root: Path) -> None:
    from .commerce import compile_commerce_pack
    from .fx import CURRENCY_MINOR_UNITS, refresh_ecb_rate_book

    st.title("FinCompiler · 跨境卖家真实利润")
    st.caption("平台订单 / 结算 → 收款 → 银行到账 → SKU 落地利润")
    st.info("本地优先：文件、汇率依据、字段确认和输出都留在这台电脑。计算使用确定性引擎，AI 只能解释结果。")
    source_mode = st.radio("从哪里开始？", ["运行内置示例", "上传我的导出文件", "使用本地文件夹"], horizontal=True)
    input_dir: Path
    workspace: Path | None = None
    if source_mode == "运行内置示例":
        input_dir = resource_root / "demo" / "cross_border_seller"
        st.success("示例包含 Amazon Settlement V2、Shopify 订单/payout、银行流水和 SKU 落地成本。预期：全部通过。")
    elif source_mode == "使用本地文件夹":
        input_dir = Path(st.text_input("数据文件夹", str(resource_root / "demo" / "cross_border_seller")))
        st.caption("文件名可为 amazon_settlements、shopify_orders、shopify_payouts、bank、sku_costs；支持 CSV/XLSX。银行文件必需，Amazon 或 Shopify 至少一种。")
    else:
        st.markdown("#### 选择平台、银行和成本文件")
        cols = st.columns(2)
        uploaded = {
            "amazon_settlements": cols[0].file_uploader("Amazon Settlement V2（可选）", type=["csv", "xlsx", "xlsm"]),
            "shopify_orders": cols[1].file_uploader("Shopify 订单 CSV（建议）", type=["csv", "xlsx", "xlsm"]),
            "shopify_payouts": cols[0].file_uploader("Shopify payout CSV（可选）", type=["csv", "xlsx", "xlsm"]),
            "bank": cols[1].file_uploader("银行流水（必需）", type=["csv", "xlsx", "xlsm"]),
            "sku_costs": cols[0].file_uploader("SKU 落地成本（建议）", type=["csv", "xlsx", "xlsm"]),
        }
        currencies = sorted(CURRENCY_MINOR_UNITS)
        base_currency = cols[1].selectbox("管理报表币种", currencies, index=currencies.index("USD"))
        business_name = cols[0].text_input("店铺 / 公司名称", "My cross-border business")
        match_window = cols[1].number_input("到账匹配窗口（天）", min_value=0, max_value=31, value=7)
        rate_source = st.selectbox("外币换算依据", ["外币时先拦截，由我提供汇率", "上传公司认可的汇率表", "获取并审核 ECB 参考汇率"])
        rate_book_value = None
        rate_type = "transaction"
        if rate_source == "上传公司认可的汇率表":
            uploaded["fx_rates"] = st.file_uploader("公司认可的汇率表", type=["csv"])
            if uploaded["fx_rates"] is None:
                st.warning("请上传汇率表；未提供的外币记录将被拦截。")
        elif rate_source == "获取并审核 ECB 参考汇率":
            st.caption("FinCompiler 可自动下载 ECB 参考汇率并保留来源、日期和原始响应哈希；参考汇率是否适合你的管理口径仍需你确认。")
            if st.button("获取最新 90 天 ECB 参考汇率"):
                try:
                    st.session_state.commerce_ecb = _refresh_ecb_with_fallback(data_root / ".fincompiler" / "rates" / "ecb-reference.csv", refresh_ecb_rate_book)
                except Exception as exc:
                    st.error(str(exc))
            if "commerce_ecb" in st.session_state:
                evidence = st.session_state.commerce_ecb
                st.success(f"已缓存 {evidence['observations']} 条汇率观察值，获取时间 {evidence['fetched_at']}")
                approved = st.checkbox("我确认本次经营分析允许使用该 ECB 参考汇率。")
                if approved:
                    rate_book_value = str((data_root / ".fincompiler" / "rates" / "ecb-reference.csv").resolve())
                    rate_type = "reference"
        if uploaded["bank"] is None or not (uploaded["amazon_settlements"] or uploaded["shopify_payouts"]):
            st.warning("请先上传银行流水，并至少上传 Amazon Settlement 或 Shopify payout。")
            return
        workspace = _stage_uploads(uploaded)
        if uploaded.get("fx_rates") is not None:
            rate_book_value = "fx_rates.csv"
        (workspace / "commerce_config.json").write_text(json.dumps({
            "business_name": business_name,
            "base_currency": base_currency,
            "reconciliation_tolerance": "0.01",
            "bank_match_window_days": int(match_window),
            "fx_rate_book": rate_book_value,
            "fx_policy": {"rate_type": rate_type, "max_lookback_days": 7, "allow_inverse": True, "allow_cross": True, "triangulation_currency": "EUR"},
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        input_dir = workspace
    if st.button("开始核对并计算真实利润", type="primary", width="stretch"):
        try:
            identity = hashlib.sha256(str(input_dir.resolve()).encode()).hexdigest()[:12]
            output_dir = data_root / ".fincompiler" / "commerce-runs" / identity
            report = compile_commerce_pack(input_dir, output_dir, data_root / ".fincompiler" / "mappings" / "commerce-memory.json")
            st.session_state.commerce_report = report
            st.session_state.commerce_output_dir = str(output_dir)
        except Exception as exc:
            st.error(str(exc))
    report = st.session_state.get("commerce_report")
    if not report:
        return
    st.markdown("### 核对结果")
    readiness = report["output_readiness"]
    (st.success if readiness == "READY" else st.error)("可以用于经营复核" if readiness == "READY" else "存在必须处理的差异，系统没有自动修正")
    metrics = st.columns(4)
    metrics[0].metric("到账批次", len(report["payout_reconciliation"]))
    metrics[1].metric("已核对通过", sum(item["status"] == "PASS" for item in report["payout_reconciliation"]))
    metrics[2].metric("待处理异常", len(report["exceptions"]))
    metrics[3].metric("SKU 结果", len(report["sku_profitability"]))
    st.markdown("#### 平台结算 ↔ 银行到账")
    st.dataframe(report["payout_reconciliation"], width="stretch", hide_index=True)
    st.markdown("#### SKU 真实利润")
    st.dataframe(report["sku_profitability"], width="stretch", hide_index=True)
    if report["exceptions"]:
        st.markdown("#### 需要你处理")
        st.dataframe(report["exceptions"], width="stretch", hide_index=True)
    output_dir = Path(st.session_state.commerce_output_dir)
    download_cols = st.columns(2)
    download_cols[0].download_button("下载 Excel 复核包", (output_dir / "commerce_pack.xlsx").read_bytes(), "FinCompiler-commerce-pack.xlsx")
    download_cols[1].download_button("下载完整 JSON 证据", (output_dir / "commerce_pack.json").read_bytes(), "FinCompiler-commerce-pack.json")


def render() -> None:
    import streamlit as st

    from . import __version__
    from .exception_workflow import USER_STATUSES, read_exception_workflow, update_exception_item
    from .fx import CURRENCY_MINOR_UNITS, refresh_ecb_rate_book
    from .lineage_store import LineageStore
    from .mapping import MappingMemory, SCHEMAS
    from .pipeline import compile_pack
    from .reporting import write_management_pack_excel
    from .run_state import sign_off, verify_run

    st.set_page_config(page_title="FinCompiler", page_icon="✓", layout="wide")
    resource_root = _resource_root()
    data_root = _data_root()
    workflow_mode = st.sidebar.radio("工作模式 / Workflow", ["跨境卖家真实利润", "企业月结 Sales ↔ GL"])
    if workflow_mode == "跨境卖家真实利润":
        _render_commerce(st, resource_root, data_root)
        return
    st.title("FinCompiler")
    st.caption(f"Month-end reconciliation and performance investigation · v{__version__}")
    st.info("Local-first: your files, mapping decisions, exchange-rate evidence and outputs stay on this computer.")
    sample_input = resource_root / "demo" / "multicurrency_close"

    if "report" not in st.session_state:
        st.markdown("### 1 · Choose this month's files")
    with st.container(border=True):
        source_mode = st.radio(
            "How would you like to start?",
            ["Try the sample company", "Upload monthly files", "Use a prepared local folder"],
            horizontal=True,
        )
        uploaded_files: dict[str, object] = {}
        generated_company: dict[str, str] | None = None
        rate_source = "Block foreign-currency records without an approved rate book"
        approve_ecb_reference = False
        if source_mode == "Upload monthly files":
            st.caption("Choose each file by business role. Original filenames do not need to match FinCompiler names.")
            with st.expander("What exports do I need?"):
                st.markdown(
                    "- **Sales detail:** one row per invoice or sales line, with date, customer, amount and a reference.\n"
                    "- **General ledger:** revenue-account journal detail, including debit/credit or signed amount and reference.\n"
                    "- **Budget:** customer/SKU plan with period, quantity, unit price or revenue.\n\n"
                    "CSV, XLSX and XLSM are accepted. FinCompiler shows uncertain fields for review and never guesses them silently."
                )
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
            with st.expander("Company policy and exchange rates", expanded=True):
                uploaded_files["company_config"] = st.file_uploader("Company policy", type=["json"])
                if uploaded_files["company_config"] is not None:
                    st.caption("The uploaded policy controls base currency, revenue accounts, tolerance and rate-book use.")
                    uploaded_files["fx_rates"] = st.file_uploader("Rate book referenced by that policy", type=["csv"], key="fx-upload")
                else:
                    policy_columns = st.columns(2)
                    company_name = policy_columns[0].text_input("Company / entity name", "My company")
                    currencies = sorted(CURRENCY_MINOR_UNITS)
                    base_currency = policy_columns[1].selectbox("Accounting base currency", currencies, index=currencies.index("AED"))
                    revenue_accounts = policy_columns[0].text_input("GL revenue accounts", "Revenue, Sales Revenue, 4000", help="Comma-separated names or codes.")
                    tolerance = policy_columns[1].text_input("Reconciliation tolerance", "0.01")
                    rate_source = st.selectbox(
                        "Foreign-currency basis",
                        [
                            "Block foreign-currency records without an approved rate book",
                            "Use an uploaded company-approved rate book",
                            "Use a reviewed ECB reference-rate cache",
                        ],
                    )
                    if rate_source == "Use an uploaded company-approved rate book":
                        uploaded_files["fx_rates"] = st.file_uploader("Approved exchange-rate book", type=["csv"], key="fx-upload")
                    elif rate_source == "Use a reviewed ECB reference-rate cache":
                        st.warning("ECB rates are informational reference rates. Fetching them does not approve them for accounting use.")
                        if st.button("Fetch latest 90-day ECB reference cache"):
                            try:
                                st.session_state.ecb_reference = _refresh_ecb_with_fallback(
                                    data_root / ".fincompiler" / "rates" / "ecb-reference.csv", refresh_ecb_rate_book
                                )
                            except Exception as exc:
                                st.error(str(exc))
                        if "ecb_reference" in st.session_state:
                            evidence = st.session_state.ecb_reference
                            st.success(
                                f"Cached {evidence['observations']} {evidence['history']} observations locally · "
                                f"fetched {evidence['fetched_at']}"
                            )
                            if evidence.get("fallback_reason"):
                                st.warning("The 90-day feed timed out, so only the daily feed was cached. Older transaction dates will remain blocked.")
                            approve_ecb_reference = st.checkbox(
                                "I confirm this company permits ECB reference rates for this analytical run.",
                                help="This explicit approval is stored in the run configuration and evidence manifest.",
                            )
                    generated_company = {
                        "company_name": company_name,
                        "base_currency": base_currency,
                        "revenue_accounts": revenue_accounts,
                        "tolerance": tolerance,
                    }
            input_dir = ""
        elif source_mode == "Use a prepared local folder":
            input_dir = st.text_input(
                "Folder containing Sales, GL and Budget",
                str(sample_input),
                help="Use sales.csv/xlsx, gl.csv/xlsx and budget.csv/xlsx. FinCompiler blocks duplicates instead of guessing.",
            )
        else:
            input_dir = str(sample_input)
            st.success("Recommended first step: run this prepared sample. Expected result: 5/5 controls complete and Sales/GL difference 0.00.")
            st.caption("The sample contains multi-currency Sales, Dynamics-style GL, Budget and approved rate evidence.")

        with st.expander("Advanced local storage options"):
            memory_file = st.text_input("Saved mapping memory", str(data_root / "mappings" / "memory.json"))
            output_folder = st.text_input("Local run folder", str(data_root / "output" / "demo-run"))
        run_label = "Run sample check" if source_mode == "Try the sample company" else "Run month-end check"
        run_clicked = st.button(run_label, type="primary", width="stretch")

    if run_clicked:
        try:
            if source_mode == "Upload monthly files":
                missing = [DATASET_LABELS[name] for name in DATASET_LABELS if uploaded_files.get(name) is None]
                if missing:
                    raise ValueError("Choose all three required files: " + ", ".join(missing))
                workspace = _stage_uploads(uploaded_files)
                if generated_company is not None:
                    fx_rate_book = None
                    rate_type = "transaction"
                    if rate_source == "Use an uploaded company-approved rate book":
                        if uploaded_files.get("fx_rates") is None:
                            raise ValueError("Choose the company-approved exchange-rate book or select the blocking option.")
                        fx_rate_book = "fx_rates.csv"
                    elif rate_source == "Use a reviewed ECB reference-rate cache":
                        evidence = st.session_state.get("ecb_reference")
                        if not evidence or not approve_ecb_reference:
                            raise ValueError("Fetch the ECB cache and explicitly approve its use for this analytical run.")
                        shutil.copy2(evidence["file"], workspace / "fx_rates.csv")
                        fx_rate_book = "fx_rates.csv"
                        rate_type = "reference"
                    _write_company_config(
                        workspace,
                        generated_company["company_name"],
                        generated_company["base_currency"],
                        generated_company["revenue_accounts"],
                        generated_company["tolerance"],
                        fx_rate_book,
                        rate_type,
                    )
                input_dir = str(workspace)
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

    download_columns = st.columns([1, 1, 1, 2])
    excel_bytes = (active_output / report["management_pack_excel"]).read_bytes()
    download_columns[0].download_button(
        "Download Excel pack",
        excel_bytes,
        file_name=f"fincompiler-{report['run_manifest']['run_id']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )
    pack_bytes = json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")
    download_columns[1].download_button(
        "Download audit JSON",
        pack_bytes,
        file_name=f"fincompiler-{report['run_manifest']['run_id']}.json",
        mime="application/json",
        width="stretch",
    )
    html_bytes = (active_output / report["management_pack_html"]).read_bytes()
    download_columns[2].download_button(
        "Download readable HTML",
        html_bytes,
        file_name=f"fincompiler-{report['run_manifest']['run_id']}.html",
        mime="text/html",
        width="stretch",
    )
    download_columns[3].caption(f"Run ID: {report['run_manifest']['run_id']}")

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
            st.caption(
                "Assign and document the work here. A user status never clears a Finance control; "
                "only a deterministic rerun without the exception can clear it."
            )
            exception_state = read_exception_workflow(active_output) or {"items": []}
            active_exception_items = [item for item in exception_state.get("items", []) if item.get("active")]
            for item in active_exception_items:
                item_id = item["exception_id"]
                with st.expander(
                    f"{item['severity']} · {item['code']} — {item['message']}",
                    expanded=item.get("status") != "READY_TO_RERUN",
                ):
                    st.warning(_exception_action(item["code"]))
                    tracker_columns = st.columns([2, 2, 2])
                    status = tracker_columns[0].selectbox(
                        "Handling status",
                        USER_STATUSES,
                        index=USER_STATUSES.index(item.get("status", "OPEN")),
                        key=f"exception-status-{item_id}",
                    )
                    owner = tracker_columns[1].text_input(
                        "Owner",
                        value=item.get("owner", ""),
                        key=f"exception-owner-{item_id}",
                    )
                    actor = tracker_columns[2].text_input(
                        "Updated by",
                        key=f"exception-actor-{item_id}",
                        help="Used only in the local exception audit history.",
                    )
                    note = st.text_area(
                        "Working note",
                        value=item.get("note", ""),
                        key=f"exception-note-{item_id}",
                    )
                    evidence_reference = st.text_input(
                        "Evidence reference",
                        value=item.get("evidence_reference", ""),
                        key=f"exception-evidence-{item_id}",
                        help="For example: corrected workbook name, ticket ID, journal batch or reviewer note. Do not paste secrets.",
                    )
                    if st.button("Save handling update", key=f"exception-save-{item_id}"):
                        try:
                            update_exception_item(
                                active_output,
                                item_id,
                                status=status,
                                owner=owner,
                                note=note,
                                evidence_reference=evidence_reference,
                                actor=actor,
                            )
                            write_management_pack_excel(
                                active_output,
                                report,
                                read_exception_workflow(active_output),
                            )
                            st.success("Saved locally. The blocking control remains active until a clean rerun.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                    with st.expander("Source evidence"):
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
