from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from .models import CanonicalRecord, ExceptionItem, MappingProposal, SourceRef


SCHEMAS = {
    "sales": {"invoice_id", "line_id", "document_type", "date", "due_date", "status", "customer", "customer_id", "sku", "description", "quantity", "unit_price", "discount_amount", "tax_amount", "tax_rate", "gross_amount", "net_sales", "revenue_account", "unit_cost_local", "currency", "exchange_rate"},
    "gl": {"entry_id", "batch_id", "date", "account", "description", "reference", "amount", "debit_amount", "credit_amount", "currency", "exchange_rate", "accounting_currency_amount", "reporting_currency_amount", "legal_entity", "dimension"},
    "budget": {"period", "customer", "sku", "quantity", "unit_price", "revenue"},
}

ALIASES = {
    "invoice": "invoice_id", "invoice no": "invoice_id", "invoice_id": "invoice_id",
    "entry": "entry_id", "entry_id": "entry_id", "journal id": "entry_id",
    "date": "date", "period": "period", "customer": "customer", "client": "customer",
    "sku": "sku", "product": "sku", "qty": "quantity", "quantity": "quantity",
    "price": "unit_price", "unit price": "unit_price", "unit_price": "unit_price",
    "sales": "net_sales", "net sales": "net_sales", "net_sales": "net_sales",
    "amount": "amount", "value": "amount", "revenue": "revenue", "account": "account",
    "reference": "reference", "invoice ref": "reference", "currency": "currency",
}


def schema_fingerprint(fields: list[str]) -> str:
    normalized = "|".join(sorted(field.strip().lower() for field in fields))
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


class MappingMemory:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data = {"version": 1, "datasets": {}}
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)

    def confirm(self, dataset: str, source_field: str, canonical_field: str, fields: list[str]) -> None:
        if canonical_field not in SCHEMAS[dataset]:
            raise ValueError(f"Unknown canonical field: {canonical_field}")
        block = self.data["datasets"].setdefault(dataset, {"mappings": {}, "fingerprints": []})
        block["mappings"][source_field] = canonical_field
        fingerprint = schema_fingerprint(fields)
        if fingerprint not in block["fingerprints"]:
            block["fingerprints"].append(fingerprint)
        self.save()

    def propose(self, dataset: str, fields: list[str], profile_aliases: dict[str, str] | None = None, profile_name: str = "generic") -> tuple[list[MappingProposal], list[ExceptionItem]]:
        block = self.data["datasets"].get(dataset, {"mappings": {}, "fingerprints": []})
        current = schema_fingerprint(fields)
        exceptions = []
        if block["fingerprints"] and current not in block["fingerprints"]:
            exceptions.append(ExceptionItem("SCHEMA_DRIFT", "HIGH", "Source schema differs from previously confirmed schema", {"dataset": dataset, "fingerprint": current, "fields": fields}))
        proposals = []
        used = set()
        effective_aliases = {**ALIASES, **(profile_aliases or {})}
        for source in fields:
            if source in block["mappings"]:
                target, confidence, status, reason = block["mappings"][source], Decimal("1"), "CONFIRMED", "persistent memory"
            else:
                target = effective_aliases.get(source) or effective_aliases.get(source.strip().lower())
                confidence = Decimal("0.99") if source in (profile_aliases or {}) else (Decimal("0.95") if target else Decimal("0"))
                status = "PROPOSED" if target else "NEEDS_REVIEW"
                reason = f"exact {profile_name} field" if source in (profile_aliases or {}) else ("exact alias" if target else "no deterministic alias")
            if target in used:
                status, reason = "NEEDS_REVIEW", "ambiguous duplicate canonical target"
            if target:
                used.add(target)
            proposals.append(MappingProposal(dataset, source, target, confidence, status, reason))
        return proposals, exceptions


def apply_mapping(dataset: str, rows, proposals: list[MappingProposal]) -> tuple[list[CanonicalRecord], list[ExceptionItem]]:
    approved = {p.source_field: p.canonical_field for p in proposals if p.status in {"CONFIRMED", "PROPOSED"} and p.confidence >= Decimal("0.90")}
    blocked = [asdict(p) for p in proposals if p.source_field not in approved]
    exceptions = []
    if blocked:
        exceptions.append(ExceptionItem("MAPPING_REVIEW_REQUIRED", "HIGH", "One or more fields were not mapped; no silent coercion was performed", {"fields": blocked}))
    records = []
    for index, (row, refs) in enumerate(rows, start=1):
        values, lineage = {}, {}
        for source, canonical in approved.items():
            values[canonical] = row.get(source, "")
            lineage[canonical] = refs[source]
        records.append(CanonicalRecord(dataset, values.get("invoice_id") or values.get("entry_id") or f"{dataset}-{index}", values, lineage))
    return records, exceptions
