from fincompiler.ingestion import read_tabular
from fincompiler.mapping import MappingMemory, apply_mapping
from fincompiler.pvm import investigate_pvm


def mapped(dataset, path, tmp_path):
    rows = read_tabular(path)
    proposals, _ = MappingMemory(tmp_path / "m.json").propose(dataset, list(rows[0][0]))
    return apply_mapping(dataset, rows, proposals)[0]


def test_pvm_bridge_is_deterministic_and_balances(demo_dir, tmp_path):
    result = investigate_pvm(mapped("sales", demo_dir / "sales.csv", tmp_path), mapped("budget", demo_dir / "budget.csv", tmp_path))
    assert result["totals"]["bridge_check"] == "0.00"
    assert result["totals"]["variance"] == "-725.00"

