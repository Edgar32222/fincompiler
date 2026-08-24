from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class LineageStore:
    def __init__(self, path: str | Path, reset: bool = False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self._file_ids: dict[str, int] = {}
        if reset:
            self.connection.executescript("DROP TABLE IF EXISTS lineage_sources; DROP TABLE IF EXISTS lineage_records; DROP TABLE IF EXISTS lineage_groups; DROP TABLE IF EXISTS source_files;")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS lineage_groups (
                lineage_id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                name TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                input_count INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS lineage_records (
                lineage_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                role TEXT NOT NULL,
                record_id TEXT NOT NULL,
                value TEXT,
                formula TEXT,
                PRIMARY KEY (lineage_id, seq, role)
            );
            CREATE TABLE IF NOT EXISTS source_files (
                file_id INTEGER PRIMARY KEY,
                file TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS lineage_sources (
                lineage_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                role TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                file_id INTEGER NOT NULL,
                sheet TEXT NOT NULL,
                row_number INTEGER NOT NULL,
                field TEXT NOT NULL,
                raw_value TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_lineage_records_group ON lineage_records(lineage_id, seq);
            CREATE INDEX IF NOT EXISTS idx_lineage_sources_group ON lineage_sources(lineage_id, seq);
            CREATE INDEX IF NOT EXISTS idx_lineage_sources_file ON lineage_sources(file_id, row_number);
            """
        )

    def _reset_group(self, lineage_id: str) -> None:
        self.connection.execute("DELETE FROM lineage_sources WHERE lineage_id = ?", (lineage_id,))
        self.connection.execute("DELETE FROM lineage_records WHERE lineage_id = ?", (lineage_id,))
        self.connection.execute("DELETE FROM lineage_groups WHERE lineage_id = ?", (lineage_id,))

    def store_calculation(self, lineage_id: str, category: str, calculation: dict, preview_size: int = 3) -> dict:
        inputs = calculation.get("inputs", [])
        self._reset_group(lineage_id)
        metadata = {key: value for key, value in calculation.items() if key != "inputs"}
        self.connection.execute("INSERT INTO lineage_groups VALUES (?, ?, ?, ?, ?)", (lineage_id, category, calculation.get("name", lineage_id), json.dumps(metadata, ensure_ascii=False), len(inputs)))
        for seq, item in enumerate(inputs):
            derivation = item.get("derivation", {})
            self.connection.execute("INSERT INTO lineage_records VALUES (?, ?, ?, ?, ?, ?)", (lineage_id, seq, "input", str(item.get("record_id", "")), str(item.get("value", "")), derivation.get("formula")))
            sources = [item["source"]] if item.get("source") else derivation.get("sources", [])
            for source in sources:
                self._insert_source(lineage_id, seq, "input", "value", source)
        return {**metadata, "lineage_id": lineage_id, "input_count": len(inputs), "input_preview": inputs[:preview_size]}

    def store_pvm_segment(self, lineage_id: str, segment: dict, preview_size: int = 2) -> dict:
        actual, budget = segment.get("actual_inputs", []), segment.get("budget_inputs", [])
        self._reset_group(lineage_id)
        metadata = {key: value for key, value in segment.items() if key not in {"actual_inputs", "budget_inputs"}}
        self.connection.execute("INSERT INTO lineage_groups VALUES (?, ?, ?, ?, ?)", (lineage_id, "pvm_segment", f"{segment.get('customer')} / {segment.get('sku')}", json.dumps(metadata, ensure_ascii=False), len(actual) + len(budget)))
        seq = 0
        for role, items in (("actual", actual), ("budget", budget)):
            for item in items:
                self.connection.execute("INSERT INTO lineage_records VALUES (?, ?, ?, ?, ?, ?)", (lineage_id, seq, role, str(item.get("record_id", "")), None, None))
                for source_kind in ("quantity_source", "revenue_source", "unit_price_source"):
                    if item.get(source_kind):
                        self._insert_source(lineage_id, seq, role, source_kind, item[source_kind])
                seq += 1
        return {**metadata, "lineage_id": lineage_id, "actual_input_count": len(actual), "budget_input_count": len(budget), "actual_input_preview": actual[:preview_size], "budget_input_preview": budget[:preview_size]}

    def _insert_source(self, lineage_id: str, seq: int, role: str, source_kind: str, source: dict) -> None:
        file_id = self._file_ids.get(source["file"])
        if file_id is None:
            self.connection.execute("INSERT OR IGNORE INTO source_files(file) VALUES (?)", (source["file"],))
            file_id = self.connection.execute("SELECT file_id FROM source_files WHERE file = ?", (source["file"],)).fetchone()[0]
            self._file_ids[source["file"]] = file_id
        self.connection.execute(
            "INSERT INTO lineage_sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (lineage_id, seq, role, source_kind, file_id, source["sheet"], int(source["row"]), source["field"], str(source["raw_value"])),
        )

    def trace(self, lineage_id: str, limit: int = 100, offset: int = 0) -> dict:
        group = self.connection.execute("SELECT category, name, metadata_json, input_count FROM lineage_groups WHERE lineage_id = ?", (lineage_id,)).fetchone()
        if not group:
            raise KeyError(f"Unknown lineage id: {lineage_id}")
        rows = self.connection.execute("SELECT seq, role, record_id, value, formula FROM lineage_records WHERE lineage_id = ? ORDER BY seq LIMIT ? OFFSET ?", (lineage_id, limit, offset)).fetchall()
        records = []
        for seq, role, record_id, value, formula in rows:
            sources = self.connection.execute("SELECT s.source_kind, f.file, s.sheet, s.row_number, s.field, s.raw_value FROM lineage_sources s JOIN source_files f ON f.file_id = s.file_id WHERE s.lineage_id = ? AND s.seq = ? AND s.role = ? ORDER BY s.source_kind", (lineage_id, seq, role)).fetchall()
            records.append({"seq": seq, "role": role, "record_id": record_id, "value": value, "formula": formula, "sources": [{"source_kind": item[0], "file": item[1], "sheet": item[2], "row": item[3], "field": item[4], "raw_value": item[5]} for item in sources]})
        return {"lineage_id": lineage_id, "category": group[0], "name": group[1], "metadata": json.loads(group[2]), "input_count": group[3], "offset": offset, "limit": limit, "records": records}

    def close(self) -> None:
        self.connection.commit()
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
