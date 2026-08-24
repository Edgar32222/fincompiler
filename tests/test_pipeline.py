import json

from fincompiler.pipeline import compile_pack


def test_end_to_end_pack_is_blocked_by_reconciliation(demo_dir, tmp_path):
    report = compile_pack(demo_dir, tmp_path / "out", tmp_path / "mappings.json")
    assert report["output_readiness"] == "BLOCKED"
    assert report["reconciliation"]["variance"] == "2706.00"
    saved = json.loads((tmp_path / "out" / "management_pack.json").read_text())
    assert saved["pvm"]["totals"]["bridge_check"] == "0.00"
    rendered = (tmp_path / "out" / "management_pack.html").read_text(encoding="utf-8")
    assert "FinCompiler Management Pack" in rendered
    assert "2706.00" in rendered
    assert saved["run_manifest"]["run_id"] in rendered
