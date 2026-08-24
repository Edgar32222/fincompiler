import json

import pytest

from fincompiler.config import FinanceConfig
from fincompiler.web_app import _data_root, _exception_action, _refresh_ecb_with_fallback, _resource_root, _stage_uploads, _write_company_config


class FakeUpload:
    def __init__(self, name: str, payload: bytes):
        self.name = name
        self.payload = payload

    def getvalue(self) -> bytes:
        return self.payload


def test_staged_excel_upload_preserves_workbook_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    folder = _stage_uploads(
        {
            "sales": FakeUpload("July Invoice Export.XLSX", b"excel-sales"),
            "gl": FakeUpload("ledger.csv", b"csv-gl"),
            "budget": FakeUpload("FY26 Plan.csv", b"csv-budget"),
        }
    )
    assert (folder / "sales.xlsx").read_bytes() == b"excel-sales"
    assert (folder / "gl.csv").read_bytes() == b"csv-gl"
    assert (folder / "budget.csv").read_bytes() == b"csv-budget"


def test_exception_actions_are_user_directed():
    assert "Confirm" in _exception_action("MAPPING_REVIEW_REQUIRED")
    assert "approved dated rate" in _exception_action("FX_RATE_REQUIRED")


def test_generated_company_policy_is_valid_and_explicit(tmp_path):
    path = _write_company_config(tmp_path, "Pilot Co", "USD", "4000; 4010", "0.50", "fx_rates.csv", "reference")
    config = FinanceConfig.load(path)
    assert config.company_name == "Pilot Co"
    assert config.base_currency == "USD"
    assert config.revenue_accounts == ("4000", "4010")
    assert config.fx_rate_book == "fx_rates.csv"
    assert config.fx_policy.rate_type == "reference"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["reconciliation_tolerance"] == "0.50"


def test_generated_company_policy_rejects_negative_tolerance(tmp_path):
    with pytest.raises(ValueError, match="cannot be negative"):
        _write_company_config(tmp_path, "Pilot Co", "USD", "4000", "-0.01", None, "transaction")


def test_ecb_refresh_falls_back_to_daily_without_hiding_reason(tmp_path):
    calls = []

    def fake_refresh(target, history):
        calls.append(history)
        if history == "90d":
            raise RuntimeError("90-day timeout")
        return {"history": "daily", "file": str(target), "observations": 2, "fetched_at": "now"}

    result = _refresh_ecb_with_fallback(tmp_path / "rates.csv", fake_refresh)
    assert calls == ["90d", "daily"]
    assert result["history"] == "daily"
    assert "timeout" in result["fallback_reason"]


def test_packaged_path_overrides_keep_resources_and_user_data_separate(tmp_path, monkeypatch):
    resources = tmp_path / "program"
    user_data = tmp_path / "user-data"
    monkeypatch.setenv("FINCOMPILER_RESOURCE_DIR", str(resources))
    monkeypatch.setenv("FINCOMPILER_DATA_DIR", str(user_data))
    assert _resource_root() == resources.resolve()
    assert _data_root() == user_data.resolve()
