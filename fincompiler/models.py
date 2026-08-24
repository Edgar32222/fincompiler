from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any


def money(value: Any) -> Decimal:
    if value is None or str(value).strip() == "":
        return Decimal("0")
    raw = str(value).strip().replace(",", "").replace(" ", "")
    negative = raw.startswith("(") and raw.endswith(")")
    if negative:
        raw = raw[1:-1]
    if raw.endswith("-"):
        raw = "-" + raw[:-1]
    for symbol in ("$", "€", "£", "¥", "AED"):
        raw = raw.replace(symbol, "")
    result = Decimal(raw).quantize(Decimal("0.01"))
    return -result if negative else result


@dataclass(frozen=True)
class SourceRef:
    file: str
    sheet: str
    row: int
    field: str
    raw_value: str


@dataclass
class CanonicalRecord:
    dataset: str
    record_id: str
    values: dict[str, Any]
    lineage: dict[str, SourceRef]
    derivations: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class MappingProposal:
    dataset: str
    source_field: str
    canonical_field: str | None
    confidence: Decimal
    status: str
    reason: str


@dataclass
class ExceptionItem:
    code: str
    severity: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class Calculation:
    name: str
    value: Decimal
    formula: str
    inputs: list[dict[str, Any]]

    def jsonable(self) -> dict[str, Any]:
        result = asdict(self)
        result["value"] = str(self.value)
        return result
