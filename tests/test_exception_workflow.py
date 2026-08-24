import pytest

from fincompiler.exception_workflow import (
    SYSTEM_CLEARED_STATUS,
    exception_id,
    initialize_exception_workflow,
    read_exception_workflow,
    update_exception_item,
)


def sample_exception(message="Sales field needs review"):
    return {
        "code": "MAPPING_REVIEW_REQUIRED",
        "severity": "BLOCKING",
        "message": message,
        "context": {"dataset": "sales", "field": "Net Amount"},
    }


def test_exception_id_is_stable_for_equivalent_context_order():
    first = sample_exception()
    second = {**first, "context": {"field": "Net Amount", "dataset": "sales"}}
    assert exception_id(first) == exception_id(second)


def test_workflow_preserves_handling_and_only_rerun_clears(tmp_path):
    source = sample_exception()
    state = initialize_exception_workflow(tmp_path, "run-1", [source], now="2026-08-24T00:00:00+00:00")
    item_id = state["items"][0]["exception_id"]

    updated = update_exception_item(
        tmp_path,
        item_id,
        status="INVESTIGATING",
        owner="Finance Manager",
        note="Checking July source export",
        evidence_reference="Close checklist 7.2",
        actor="Controller",
        now="2026-08-24T00:05:00+00:00",
    )
    assert updated["status"] == "INVESTIGATING"
    assert updated["history"][0]["from_status"] == "OPEN"

    same = initialize_exception_workflow(tmp_path, "run-1", [source], now="2026-08-24T00:10:00+00:00")
    assert same["items"][0]["status"] == "INVESTIGATING"
    assert same["items"][0]["owner"] == "Finance Manager"

    cleared = initialize_exception_workflow(tmp_path, "run-1", [], now="2026-08-24T00:15:00+00:00")
    assert cleared["active_count"] == 0
    assert cleared["cleared_count"] == 1
    assert cleared["items"][0]["status"] == SYSTEM_CLEARED_STATUS
    assert cleared["items"][0]["history"][-1]["actor"] == "FinCompiler"
    assert cleared["items"][0]["history"][-1]["to_status"] == SYSTEM_CLEARED_STATUS
    assert read_exception_workflow(tmp_path) == cleared

    reopened = initialize_exception_workflow(tmp_path, "run-2", [source], now="2026-08-24T00:20:00+00:00")
    assert reopened["items"][0]["status"] == "OPEN"
    assert reopened["items"][0]["history"][-1]["from_status"] == SYSTEM_CLEARED_STATUS


def test_user_cannot_mark_an_exception_cleared_or_unowned(tmp_path):
    state = initialize_exception_workflow(tmp_path, "run-1", [sample_exception()])
    item_id = state["items"][0]["exception_id"]
    with pytest.raises(ValueError, match="Status must be"):
        update_exception_item(tmp_path, item_id, status=SYSTEM_CLEARED_STATUS)
    with pytest.raises(ValueError, match="Assign an owner"):
        update_exception_item(tmp_path, item_id, status="READY_TO_RERUN")
