from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class FinanceConfig:
    company_name: str = "Demo company"
    base_currency: str = "AED"
    revenue_accounts: tuple[str, ...] = ("Revenue", "Sales Revenue", "4000")
    reconciliation_tolerance: Decimal = Decimal("0.01")

    @classmethod
    def load(cls, path: str | Path | None = None) -> "FinanceConfig":
        if path is None:
            return cls()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        currency = str(data.get("base_currency", "")).upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("base_currency must be a three-letter code")
        accounts = tuple(str(value).strip() for value in data.get("revenue_accounts", []) if str(value).strip())
        if not accounts:
            raise ValueError("revenue_accounts must contain at least one explicit account")
        return cls(
            company_name=str(data.get("company_name", "Unnamed company")),
            base_currency=currency,
            revenue_accounts=accounts,
            reconciliation_tolerance=Decimal(str(data.get("reconciliation_tolerance", "0.01"))),
        )

    def jsonable(self) -> dict:
        result = asdict(self)
        result["revenue_accounts"] = list(self.revenue_accounts)
        result["reconciliation_tolerance"] = str(self.reconciliation_tolerance)
        return result

