# Currency and exchange-rate policy

FinCompiler converts a foreign-currency record only when the company configuration provides an approved basis. It never searches the internet and silently substitutes a rate while compiling a Finance pack.

## Selection order

1. A GL `accounting_currency_amount` is treated as the posted accounting amount when `prefer_accounting_currency_amount` is enabled.
2. Otherwise, the approved local rate book is searched for the configured `rate_type`, currency pair and transaction date.
3. A direct rate is preferred. An inverse rate is allowed only when `allow_inverse` is enabled.
4. A cross rate is allowed only when `allow_cross` is enabled and both legs exist through `triangulation_currency`.
5. The newest effective date on or before the transaction date may be used only within `max_lookback_days`.
6. If no compliant basis exists, the record raises `FX_RATE_REQUIRED` and publishing remains blocked.

## Quote convention

Every rate-book row uses:

```text
rate = quote_currency units per 1 base_currency unit
```

For example, `USD,AED,3.67` means AED 3.67 per USD 1.00. FinCompiler records whether it used this rate directly, inverted it or multiplied two rate legs.

## Rate-book fields

```text
effective_date,base_currency,quote_currency,rate,rate_type,provider,source_url,fetched_at,raw_sha256
```

- `effective_date` uses ISO `YYYY-MM-DD`.
- `rate` retains its supplied decimal precision and must be positive.
- `rate_type` must match company policy, such as `transaction` or `reference`.
- `provider` and `source_url` identify the approved evidence.
- `raw_sha256` is optional. When supplied it must be a real 64-character hexadecimal SHA-256; otherwise FinCompiler hashes the canonical row.

The rate-book file itself is also included in the deterministic run manifest and hashed with the Finance inputs.

## External reference rates

`fincompiler refresh-ecb-rates` downloads an explicit local cache. The default 90-day cache is small enough for monthly close work and does not make a calculation-time network call.

ECB states that its euro reference rates are informational and generally published on working days around 16:00 CET. A company must decide whether `reference` rates are suitable for the intended analysis; FinCompiler does not make that policy decision. See the [ECB reference-rate methodology](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html).

Accounting, reporting, budget and revaluation uses may require different rate types. This is also reflected in [Microsoft Dynamics ledger currency configuration](https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/configure-ledger).

## Current boundary

The current catalog covers the currencies used by ECB reference data, the GCC and common trading markets. Unknown or unsupported codes are blocked. Provider-specific CBUAE VAT, ERP API and commercial-rate adapters remain future work; their rates must not be treated as interchangeable.
