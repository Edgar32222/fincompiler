import pytest

from fincompiler.pipeline import compile_pack
from fincompiler.run_state import read_state, sign_off, verify_run
from fincompiler.scenario import generate_scenario


def test_signed_run_is_verified_and_cannot_be_overwritten(tmp_path):
    scenario = tmp_path / "scenario"
    output = tmp_path / "run"
    generate_scenario(scenario, seed=7, invoice_count=5)
    report = compile_pack(scenario, output, tmp_path / "memory.json")
    assert read_state(output)["status"] == "DRAFT"
    state = sign_off(output, "Finance Reviewer", "Synthetic golden run")
    assert state["run_id"] == report["run_manifest"]["run_id"]
    assert verify_run(output)["valid"] is True
    with pytest.raises(RuntimeError, match="cannot be overwritten"):
        compile_pack(scenario, output, tmp_path / "memory.json")


def test_signed_artifact_tampering_is_detected(tmp_path):
    scenario = tmp_path / "scenario"
    output = tmp_path / "run"
    generate_scenario(scenario, seed=8, invoice_count=5)
    compile_pack(scenario, output, tmp_path / "memory.json")
    sign_off(output, "Reviewer")
    pack = output / "management_pack.json"
    pack.write_text(pack.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    result = verify_run(output)
    assert result["valid"] is False
    assert result["mismatches"][0]["artifact"] == "management_pack.json"


def test_blocked_run_cannot_be_signed_off(demo_dir, tmp_path):
    output = tmp_path / "blocked-run"
    report = compile_pack(demo_dir, output, tmp_path / "memory.json")
    assert report["output_readiness"] == "BLOCKED"
    with pytest.raises(RuntimeError, match="cannot be signed off"):
        sign_off(output, "Finance Reviewer")
