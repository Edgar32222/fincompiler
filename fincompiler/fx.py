from __future__ import annotations

import csv
import hashlib
import io
import ssl
import urllib.request
from urllib.error import URLError
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from .models import CanonicalRecord, ExceptionItem, decimal_value, money


# Common active ISO 4217 currencies and their minor units. Unknown codes are blocked,
# not guessed. This can be extended from the ISO maintenance data without changing
# calculation logic.
CURRENCY_MINOR_UNITS = {
    "AED": 2, "ARS": 2, "AUD": 2, "BDT": 2, "BHD": 3, "BRL": 2, "CAD": 2, "CHF": 2, "CLP": 0, "CNY": 2, "COP": 2,
    "CZK": 2, "DKK": 2, "EUR": 2, "GBP": 2, "HKD": 2, "HUF": 2,
    "IDR": 2, "ILS": 2, "INR": 2, "ISK": 0, "JPY": 0, "KRW": 0, "KWD": 3,
    "MXN": 2, "MYR": 2, "NOK": 2, "NZD": 2, "OMR": 3, "PEN": 2, "PHP": 2, "PKR": 2, "PLN": 2,
    "QAR": 2, "RON": 2, "SAR": 2, "SEK": 2, "SGD": 2, "THB": 2, "TRY": 2, "TWD": 2,
    "USD": 2, "VND": 0, "ZAR": 2,
}


def validate_currency(code: str) -> str:
    normalized = str(code).strip().upper()
    if normalized not in CURRENCY_MINOR_UNITS:
        raise ValueError(f"unsupported or unknown ISO 4217 currency code: {normalized}")
    return normalized


def quantize_currency(value: Decimal, currency: str) -> Decimal:
    places = CURRENCY_MINOR_UNITS[validate_currency(currency)]
    quantum = Decimal(1).scaleb(-places)
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class RatePolicy:
    rate_type: str = "transaction"
    max_lookback_days: int = 7
    allow_inverse: bool = True
    allow_cross: bool = True
    triangulation_currency: str = "EUR"
    prefer_accounting_currency_amount: bool = True

    @classmethod
    def from_dict(cls, data: dict | None) -> "RatePolicy":
        raw = data or {}
        lookback = int(raw.get("max_lookback_days", 7))
        if lookback < 0 or lookback > 31:
            raise ValueError("fx_policy.max_lookback_days must be between 0 and 31")
        return cls(
            rate_type=str(raw.get("rate_type", "transaction")).strip().lower(),
            max_lookback_days=lookback,
            allow_inverse=bool(raw.get("allow_inverse", True)),
            allow_cross=bool(raw.get("allow_cross", True)),
            triangulation_currency=validate_currency(raw.get("triangulation_currency", "EUR")),
            prefer_accounting_currency_amount=bool(raw.get("prefer_accounting_currency_amount", True)),
        )


@dataclass(frozen=True)
class RateObservation:
    effective_date: date
    base_currency: str
    quote_currency: str
    rate: Decimal
    rate_type: str
    provider: str
    source_url: str
    fetched_at: str
    raw_sha256: str

    @property
    def observation_id(self) -> str:
        identity = "|".join((self.effective_date.isoformat(), self.base_currency, self.quote_currency, str(self.rate), self.rate_type, self.provider, self.raw_sha256))
        return hashlib.sha256(identity.encode()).hexdigest()[:20]

    def jsonable(self) -> dict:
        result = asdict(self)
        result["effective_date"] = self.effective_date.isoformat()
        result["rate"] = str(self.rate)
        result["observation_id"] = self.observation_id
        return result


@dataclass(frozen=True)
class RateMatch:
    source_currency: str
    target_currency: str
    requested_date: date
    effective_date: date
    rate: Decimal
    formula: str
    observations: tuple[RateObservation, ...]

    def jsonable(self) -> dict:
        return {
            "source_currency": self.source_currency,
            "target_currency": self.target_currency,
            "requested_date": self.requested_date.isoformat(),
            "effective_date": self.effective_date.isoformat(),
            "rate": str(self.rate),
            "formula": self.formula,
            "observations": [item.jsonable() for item in self.observations],
        }


class RateBook:
    def __init__(self, observations: list[RateObservation]):
        self.observations = observations

    @classmethod
    def load(cls, path: str | Path) -> "RateBook":
        source = Path(path)
        observations = []
        with source.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                base = validate_currency(row["base_currency"])
                quote = validate_currency(row["quote_currency"])
                rate = decimal_value(row["rate"])
                if rate <= 0:
                    raise ValueError("exchange rates must be positive")
                canonical = "|".join(str(row.get(key, "")) for key in sorted(row))
                supplied_hash = str(row.get("raw_sha256", "")).strip().lower()
                if supplied_hash and (len(supplied_hash) != 64 or any(character not in "0123456789abcdef" for character in supplied_hash)):
                    raise ValueError("raw_sha256 must be a 64-character hexadecimal SHA-256 value when supplied")
                observations.append(RateObservation(
                    effective_date=date.fromisoformat(row["effective_date"]),
                    base_currency=base,
                    quote_currency=quote,
                    rate=rate,
                    rate_type=str(row.get("rate_type", "transaction")).strip().lower(),
                    provider=str(row.get("provider", "company-approved")).strip(),
                    source_url=str(row.get("source_url", "")).strip(),
                    fetched_at=str(row.get("fetched_at", "")).strip(),
                    raw_sha256=supplied_hash or hashlib.sha256(canonical.encode()).hexdigest(),
                ))
        return cls(observations)

    def _direct(self, source: str, target: str, requested: date, policy: RatePolicy) -> RateMatch | None:
        candidates = [item for item in self.observations if item.rate_type == policy.rate_type and item.effective_date <= requested and (requested - item.effective_date).days <= policy.max_lookback_days]
        direct = [item for item in candidates if item.base_currency == source and item.quote_currency == target]
        inverse = [item for item in candidates if policy.allow_inverse and item.base_currency == target and item.quote_currency == source]
        if direct:
            item = max(direct, key=lambda value: value.effective_date)
            return RateMatch(source, target, requested, item.effective_date, item.rate, f"{target} per 1 {source}", (item,))
        if inverse:
            item = max(inverse, key=lambda value: value.effective_date)
            return RateMatch(source, target, requested, item.effective_date, Decimal(1) / item.rate, f"1 / ({source} per 1 {target})", (item,))
        return None

    def find(self, source_currency: str, target_currency: str, requested_date: date, policy: RatePolicy) -> RateMatch:
        source, target = validate_currency(source_currency), validate_currency(target_currency)
        if source == target:
            return RateMatch(source, target, requested_date, requested_date, Decimal(1), "same currency", ())
        direct = self._direct(source, target, requested_date, policy)
        if direct:
            return direct
        pivot = policy.triangulation_currency
        if policy.allow_cross and source != pivot and target != pivot:
            first = self._direct(source, pivot, requested_date, policy)
            second = self._direct(pivot, target, requested_date, policy)
            if first and second:
                return RateMatch(source, target, requested_date, min(first.effective_date, second.effective_date), first.rate * second.rate, f"({pivot} per 1 {source}) * ({target} per 1 {pivot})", first.observations + second.observations)
        raise LookupError(f"no approved {policy.rate_type} rate for {source}/{target} on or before {requested_date.isoformat()} within {policy.max_lookback_days} days")


def establish_currency_basis(records: list[CanonicalRecord], dataset: str, base_currency: str, rate_book: RateBook | None, policy: RatePolicy) -> tuple[list[CanonicalRecord], list[ExceptionItem], list[dict]]:
    base_currency = validate_currency(base_currency)
    amount_field = "net_sales" if dataset == "sales" else "amount"
    exceptions, applications = [], []
    for record in records:
        source_currency = validate_currency(record.values.get("currency", base_currency))
        record.values["transaction_currency"] = source_currency
        if source_currency == base_currency:
            record.values["basis_currency"] = base_currency
            continue
        original_amount = money(record.values.get(amount_field))
        if dataset == "gl" and policy.prefer_accounting_currency_amount and record.values.get("accounting_currency_amount") not in {None, ""}:
            converted = quantize_currency(money(record.values["accounting_currency_amount"]), base_currency)
            record.values[f"transaction_{amount_field}"] = original_amount
            record.values[amount_field] = converted
            record.values["currency"] = base_currency
            record.values["basis_currency"] = base_currency
            record.derivations[amount_field] = {"formula": "source accounting_currency_amount", "sources": [record.lineage["accounting_currency_amount"]] if "accounting_currency_amount" in record.lineage else []}
            applications.append({"dataset": dataset, "record_id": record.record_id, "source_currency": source_currency, "target_currency": base_currency, "source_amount": str(original_amount), "converted_amount": str(converted), "method": "SOURCE_ACCOUNTING_CURRENCY_AMOUNT"})
            continue
        try:
            requested = date.fromisoformat(str(record.values.get("date", "")))
            if rate_book is None:
                raise LookupError("no approved local rate book configured")
            match = rate_book.find(source_currency, base_currency, requested, policy)
            converted = quantize_currency(original_amount * match.rate, base_currency)
            record.values[f"transaction_{amount_field}"] = original_amount
            record.values[amount_field] = converted
            record.values["currency"] = base_currency
            record.values["basis_currency"] = base_currency
            record.values["applied_exchange_rate"] = match.rate
            record.derivations[amount_field] = {"formula": f"transaction_{amount_field} * applied_exchange_rate", "sources": [record.lineage[amount_field]] if amount_field in record.lineage else [], "rate_evidence": match.jsonable()}
            applications.append({"dataset": dataset, "record_id": record.record_id, "source_amount": str(original_amount), "converted_amount": str(converted), "method": "RATE_BOOK", **match.jsonable()})
        except (LookupError, ValueError) as exc:
            exceptions.append(ExceptionItem("FX_RATE_REQUIRED", "BLOCKING", "A foreign-currency record has no approved conversion basis", {"dataset": dataset, "record_id": record.record_id, "currency": source_currency, "base_currency": base_currency, "date": str(record.values.get("date", "")), "reason": str(exc)}))
    return records, exceptions, applications


ECB_HISTORY_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"
ECB_90_DAY_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
ECB_DAILY_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


def parse_ecb_history(payload: bytes, fetched_at: str | None = None, source_url: str = ECB_HISTORY_URL) -> list[RateObservation]:
    digest = hashlib.sha256(payload).hexdigest()
    timestamp = fetched_at or datetime.now(timezone.utc).isoformat()
    root = ET.fromstring(payload)
    observations = []
    for time_node in root.iter():
        effective = time_node.attrib.get("time")
        if not effective:
            continue
        for child in time_node:
            currency, raw_rate = child.attrib.get("currency"), child.attrib.get("rate")
            if not currency or not raw_rate or currency not in CURRENCY_MINOR_UNITS:
                continue
            observations.append(RateObservation(date.fromisoformat(effective), "EUR", currency, decimal_value(raw_rate), "reference", "ECB", source_url, timestamp, digest))
    return observations


def refresh_ecb_rate_book(output_path: str | Path, history: str = "90d", timeout_seconds: int = 30) -> dict:
    urls = {"daily": ECB_DAILY_URL, "90d": ECB_90_DAY_URL, "full": ECB_HISTORY_URL}
    if history not in urls:
        raise ValueError("history must be one of: daily, 90d, full")
    source_url = urls[history]
    request = urllib.request.Request(source_url, headers={"User-Agent": "FinCompiler/0.6"})
    try:
        import certifi

        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(request, timeout=timeout_seconds, context=context) as response:
            payload = response.read()
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"ECB rate refresh failed; the existing local cache was not changed: {exc}") from exc
    fetched_at = datetime.now(timezone.utc).isoformat()
    observations = parse_ecb_history(payload, fetched_at, source_url)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    columns = ["effective_date", "base_currency", "quote_currency", "rate", "rate_type", "provider", "source_url", "fetched_at", "raw_sha256"]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for item in observations:
        row = item.jsonable()
        writer.writerow({key: row[key] for key in columns})
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(buffer.getvalue(), encoding="utf-8")
    temporary.replace(target)
    return {"provider": "ECB", "history": history, "file": str(target.resolve()), "observations": len(observations), "fetched_at": fetched_at, "raw_sha256": hashlib.sha256(payload).hexdigest(), "usage_warning": "ECB reference rates are informational; company policy must explicitly approve their use."}
