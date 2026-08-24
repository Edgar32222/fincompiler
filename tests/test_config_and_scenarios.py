import json

from fincompiler.config import FinanceConfig
from fincompiler.lineage_store import LineageStore
from fincompiler.pipeline import compile_pack
from fincompiler.scenario import generate_scenario


def test_company_config_requires_explicit_revenue_accounts(tmp_path):
    path = tmp_path / "company.json"
    path.write_text(json.dumps({"company_name": "Test", "base_currency": "AED", "revenue_accounts": []}), encoding="utf-8")
    try:
        FinanceConfig.load(path)
    except ValueError as exc:
        assert "revenue_accounts" in str(exc)
    else:
        raise AssertionError("empty revenue account configuration was accepted")


def test_seeded_scenario_reproduces_truth_manifest(tmp_path):
    scenario_dir = tmp_path / "scenario"
    anomalies = ["split_posting", "amount_mismatch", "missing_gl", "unmatched_gl", "credit_note"]
    manifest = generate_scenario(scenario_dir, seed=7301, invoice_count=25, anomalies=anomalies)
    report = compile_pack(scenario_dir, tmp_path / "output", tmp_path / "memory.json")
    actual = [{key: cause[key] for key in ("reference", "reason", "difference")} for cause in report["reconciliation"]["causes"]]
    assert actual == manifest["expected_causes"]
    assert report["configuration"]["revenue_accounts"] == ["4000"]
    assert report["source_profiles"]["sales"] == "xero_invoice_lines"
    assert report["pvm"]["totals"]["bridge_check"] == "0.00"
    assert json.loads((scenario_dir / "truth_manifest.json").read_text()) == manifest


def test_perfect_scenario_is_reconciliation_ready(tmp_path):
    scenario_dir = tmp_path / "perfect"
    generate_scenario(scenario_dir, seed=11, invoice_count=10)
    report = compile_pack(scenario_dir, tmp_path / "output", tmp_path / "memory.json")
    assert report["reconciliation"]["status"] == "PASS"
    assert report["reconciliation"]["variance"] == "0.00"
    assert report["output_readiness"] == "READY"
    lineage_path = tmp_path / "output" / report["lineage_store"]
    assert lineage_path.exists()
    lineage_id = report["reconciliation"]["sales_total"]["lineage_id"]
    with LineageStore(lineage_path) as lineage:
        traced = lineage.trace(lineage_id, limit=2)
    assert traced["input_count"] >= 10
    assert len(traced["records"]) == 2
    assert traced["records"][0]["sources"][0]["file"].endswith("sales.csv")
    assert report["run_manifest"]["run_id"] in report["lineage_store"]


def test_run_id_is_content_deterministic_and_duplicates_block(tmp_path):
    scenario_dir = tmp_path / "duplicate"
    generate_scenario(scenario_dir, seed=99, invoice_count=5)
    sales_path = scenario_dir / "sales.csv"
    lines = sales_path.read_text(encoding="utf-8").splitlines()
    sales_path.write_text("\n".join(lines + [lines[1]]) + "\n", encoding="utf-8")
    first = compile_pack(scenario_dir, tmp_path / "output-1", tmp_path / "memory-1.json")
    second = compile_pack(scenario_dir, tmp_path / "output-2", tmp_path / "memory-2.json")
    assert first["run_manifest"]["run_id"] == second["run_manifest"]["run_id"]
    assert "POTENTIAL_DUPLICATE_RECORD" in {item["code"] for item in first["exceptions"]}
    assert first["output_readiness"] == "BLOCKED"


def test_foreign_currency_is_not_compared_without_conversion_basis(tmp_path):
    scenario_dir = tmp_path / "fx"
    generate_scenario(scenario_dir, seed=12, invoice_count=5)
    sales_path = scenario_dir / "sales.csv"
    sales_path.write_text(sales_path.read_text(encoding="utf-8").replace(",AED,", ",USD,"), encoding="utf-8")
    report = compile_pack(scenario_dir, tmp_path / "output", tmp_path / "memory.json")
    assert report["reconciliation"]["variance"] == "NOT_COMPARABLE"
    assert report["reconciliation"]["exceptions"][0]["code"] == "CURRENCY_BASIS_REQUIRED"
