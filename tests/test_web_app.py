from fincompiler.web_app import _exception_action, _stage_uploads


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
