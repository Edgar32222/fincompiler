# FinCompiler pilot discovery

Last reviewed: 2026-08-24

## Initial design-partner profile

FinCompiler should initially serve a finance manager, controller, or small FP&A/accounting team that:

- prepares monthly reporting from Excel/CSV exports rather than a clean warehouse;
- reconciles sales, AR, inventory, payroll, or another subledger back to the GL;
- has multiple entities, currencies, accounting systems, or changing source schemas;
- cannot justify a large close-management implementation;
- will share anonymized headers, 20-50 representative rows, and expected totals for a private pilot;
- values an auditable explanation and source lineage more than an opaque automatic adjustment.

## Public demand signals

These are public research signals, not verified CRM contacts. A handle or public profile does not establish identity, budget, authority, or consent to receive marketing.

| Signal | Observed problem | FinCompiler fit | Confidence / next validation |
| --- | --- | --- | --- |
| [FPA-Trogdor, r/FPandA](https://www.reddit.com/r/FPandA/comments/1twllle/167_excel_books_and_15_powerpoints/) | First dedicated FP&A hire; inherited 167 workbooks and 15 presentations, needs an AR view, and reports that software budget is blocked. | Very strong local-first and low-friction pilot fit: consolidate recurring exports, preserve formulas/lineage, and produce a reviewable pack. | High pain signal; company, systems, period volume, and willingness to test are unknown. |
| [SlightMetal51, r/Accounting](https://www.reddit.com/r/Accounting/comments/1sv9p97/multicountry_payroll_reconciliation_what_tools/) | Describes 23-country payroll, changing provider formats, and spreadsheet maintenance becoming a full-time job. | Strong schema-drift, persistent-mapping, normalization, and GL-reconciliation fit. | High problem fit but likely enterprise complexity; payroll/privacy scope may be too broad for the first pilot. |
| [ukmike92, r/smallbusinessuk](https://www.reddit.com/r/smallbusinessuk/comments/1vc6n4p/accountant_charging_10kyear_despite_xero_am_i/) | Publicly reports a six-figure UK business with multiple-currency accounts and substantial bookkeeping/reconciliation cost despite Xero. | Strong small-business multi-currency and exception-explanation fit. | Strong cost signal; transaction volume appears modest and the user may need bookkeeping workflow rather than management reporting. |
| [EvilLipgloss, r/Accounting](https://www.reddit.com/r/Accounting/comments/1r8eikp/monthend_closing_average_time/) | Reports an 8-10 day close while merging companies with two charts of accounts, two ERPs, and two accounting teams. | Strong multi-entity mapping, schema-drift, reconciliation, and lineage fit. | High fit; no company or buying-role verification. |
| [Seamike79, r/Accounting](https://www.reddit.com/r/Accounting/comments/1r8eikp/monthend_closing_average_time/) | Reports a small team, a recent 12-day close, and a five-week year-end close with significant non-recurring work. | Good exception-workflow and close-readiness fit. | Medium fit; the exact bottleneck and systems are unknown. |
| [hazzard623, r/Accounting](https://www.reddit.com/r/Accounting/comments/1r8eikp/monthend_closing_average_time/) | Says intercompany issues and late support from sister companies prevent a four-day close. | Good future intercompany matching and ownership/evidence workflow fit. | Medium fit today because intercompany elimination is not yet a mature FinCompiler feature. |
| [Character_Physics713, r/CRMSoftware](https://www.reddit.com/r/CRMSoftware/comments/1nhfyxl/how_do_people_handle_multicurrency_invoicing_and/) | Reports CRM and accounting sync timing causing FX-rate mismatches and reconciliation problems. | Direct fit for approved rate books, rate evidence, deterministic conversion, and exception blocking. | Strong feature signal but older and identity/role are unknown. |

## Best public channels for learning and recruiting

1. r/Accounting and r/FPandA: ask for three private design partners after sharing a concrete reconciliation teardown, not a generic product pitch.
2. r/Bookkeeping and Xero/QuickBooks communities: focus on multi-currency, marketplace payout, and external-Excel reconciliation workflows.
3. X finance and accounting discussions: publish evidence-led reconciliation examples from a product-only account and invite people with a specific close bottleneck to a private workflow review.
4. UAE finance and accounting communities that permit pseudonymous or product-brand participation: validate AED reporting, CBUAE/ERP rate policies, VAT evidence, Tally/QuickBooks/Xero exports, and Arabic/English headers.
5. Fractional CFO and accounting advisory communities on Reddit and X: one partner can expose several anonymized client data shapes and repeated close problems.

LinkedIn is explicitly out of scope for pilot recruitment. Do not view, follow, connect with, message, or otherwise engage prospects there from the founder's personal identity.

## Ethical outreach rule

- Engage only through the public channel the person chose or through an address they explicitly publish for business contact.
- Mention the exact public problem that made the invitation relevant.
- Ask for a discovery conversation or anonymized sample, not a sale.
- Never scrape or infer personal email addresses, phone numbers, employer identity, or sensitive financial details.
- Do not send bulk messages. Track opt-out and do not re-contact after a decline.
- Use a FinCompiler product identity or pseudonymous founder identity; do not connect outreach activity to the founder's employer, colleagues, or personal LinkedIn profile.
- Treat account login and recovery email addresses as private credentials. Never publish them in repository files, issues, posts, profiles, or outreach copy.

## Pilot offer

The private-alpha offer should be:

> Bring three anonymized monthly exports and the totals you currently trust. FinCompiler will map them locally, show every uncertain field for review, reconcile the detail to the GL, preserve source lineage and FX evidence, and produce an exception-led management pack. No source data is uploaded to a hosted service.

The pilot is successful only when two consecutive monthly cycles meet all of these conditions:

- first trusted result in less than 30 minutes after setup;
- at least 50% reduction in repeat-month preparation time;
- at least 95% of reconciliation variance assigned a deterministic cause;
- zero silent mapping or FX corrections;
- no manual rebuilding of the management pack in the second cycle.

## Information still required before outreach

- a product landing page or public demo link;
- a pseudonymous founder or FinCompiler product profile on X and Reddit;
- a short privacy statement and pilot data-handling agreement;
- supported system/export list and explicit alpha limitations;
- a privacy-preserving direct-message or product contact route for interested design partners;
- user approval of each first outreach batch.

## Coverage limitation

This scan is intentionally bounded to public discussions found during the 2026-08-24 review. It is not an exhaustive market or contact database. Public posts validate pain patterns but do not replace sales-intelligence verification of company, role, region, authority, or current intent.
