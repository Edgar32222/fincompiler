import json

from fincompiler.mapping import MappingMemory


def test_uncertain_mapping_is_never_silent(tmp_path):
    memory = MappingMemory(tmp_path / "memory.json")
    proposals, _ = memory.propose("sales", ["Invoice No", "其他费用2"])
    assert proposals[1].status == "NEEDS_REVIEW"
    assert proposals[1].canonical_field is None


def test_memory_and_schema_drift(tmp_path):
    path = tmp_path / "memory.json"
    memory = MappingMemory(path)
    fields = ["Invoice No", "Net Sales"]
    memory.confirm("sales", "Invoice No", "invoice_id", fields)
    proposals, exceptions = MappingMemory(path).propose("sales", fields + ["New Column"])
    assert proposals[0].status == "CONFIRMED"
    assert exceptions[0].code == "SCHEMA_DRIFT"
    assert json.loads(path.read_text())["datasets"]["sales"]["mappings"]["Invoice No"] == "invoice_id"

