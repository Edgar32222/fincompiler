from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path

from .fx import RatePolicy, validate_currency


@dataclass(frozen=True)
class FinanceConfig:
    company_name: str = "Demo company"
    base_currency: str = "AED"
    revenue_accounts: tuple[str, ...] = ("Revenue", "Sales Revenue", "4000")
    reconciliation_tolerance: Decimal = Decimal("0.01")
    fx_rate_book: str | None = None
    fx_policy: RatePolicy = RatePolicy()

    @classmethod
    def load(cls, path: str | Path | None = None) -> "FinanceConfig":
        if path is None:
            return cls()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        currency = validate_currency(data.get("base_currency", ""))
        accounts = tuple(str(value).strip() for value in data.get("revenue_accounts", []) if str(value).strip())
        if not accounts:
            raise ValueError("revenue_accounts must contain at least one explicit account")
        return cls(
            company_name=str(data.get("company_name", "Unnamed company")),
            base_currency=currency,
            revenue_accounts=accounts,
            reconciliation_tolerance=Decimal(str(data.get("reconciliation_tolerance", "0.01"))),
            fx_rate_book=str(data["fx_rate_book"]).strip() if data.get("fx_rate_book") else None,
            fx_policy=RatePolicy.from_dict(data.get("fx_policy")),
        )

    def jsonable(self) -> dict:
        result = asdict(self)
        result["revenue_accounts"] = list(self.revenue_accounts)
        result["reconciliation_tolerance"] = str(self.reconciliation_tolerance)
        result["fx_policy"] = asdict(self.fx_policy)
        return result


@dataclass(frozen=True)
class CommerceConfig:
    business_name: str = "Cross-border seller"
    base_currency: str = "USD"
    reconciliation_tolerance: Decimal = Decimal("0.01")
    bank_match_window_days: int = 7
    fx_rate_book: str | None = None
    fx_policy: RatePolicy = RatePolicy()

    @classmethod
    def load(cls, path: str | Path | None = None) -> "CommerceConfig":
        if path is None:
            return cls()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        window = int(data.get("bank_match_window_days", 7))
        if window < 0 or window > 31:
            raise ValueError("bank_match_window_days must be between 0 and 31")
        tolerance = Decimal(str(data.get("reconciliation_tolerance", "0.01")))
        if tolerance < 0:
            raise ValueError("reconciliation_tolerance cannot be negative")
        return cls(
            business_name=str(data.get("business_name", "Cross-border seller")),
            base_currency=validate_currency(data.get("base_currency", "USD")),
            reconciliation_tolerance=tolerance,
            bank_match_window_days=window,
            fx_rate_book=str(data["fx_rate_book"]).strip() if data.get("fx_rate_book") else None,
            fx_policy=RatePolicy.from_dict(data.get("fx_policy")),
        )

    def jsonable(self) -> dict:
        result = asdict(self)
        result["reconciliation_tolerance"] = str(self.reconciliation_tolerance)
        result["fx_policy"] = asdict(self.fx_policy)
        return result
