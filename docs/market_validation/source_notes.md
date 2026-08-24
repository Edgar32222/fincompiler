# Market-validation report source notes

- Audience: product stakeholders and founder.
- Decision: select the first design-partner segment, define a falsifiable acquisition/learning funnel, and identify the minimum founder actions needed before external outreach.
- Evidence window: public discussions reviewed on 2026-08-24, primarily posts published from 2025 through August 2026, plus the current FinCompiler repository and test-backed product boundary.
- Coverage: bounded public web scan of Reddit and a search of public X results. X search results were too sparse and noisy to support pain-pattern counts, so the evidence chart uses Reddit discussions only. This is not an exhaustive market or contact database.
- Identity limitation: public handles, roles, employers, authority, budgets and willingness to receive marketing were not independently verified. Public posts are discovery signals, not sales-intelligence records.
- Signal coding: 13 distinct public discussions were tagged into overlapping pain themes. A discussion may count in more than one theme, so counts do not sum to 13. Coding is directional and intended to shape interviews, not estimate market prevalence.
- Chart map: "Pain themes in the bounded public scan"; analytical question is which repeated problems should shape discovery; horizontal comparison bar; fields are pain_theme and signal_count; single blue root, no legend; source is the coded public-discussion inventory below.
- Required executive structure mapping: title; Executive Summary; key findings with a coded signal chart; recommended 14-day sprint; further questions; caveats and assumptions.
- Omitted quantitative claims: market size, conversion benchmark, willingness to pay and competitor share are not supported by the available evidence. These require interviews, pilot behavior or paid/connected market data.
- Portable-report QA: artifact validation and packaging passed. Verification is `structural_only` because the packaged verifier found no installed Chromium headless shell; application browser automation also blocks local `file:` URLs by policy, so desktop/narrow visual QA remains an explicit follow-up.

## Coded public-discussion inventory

1. FPA-Trogdor, inherited 167 workbooks and 15 presentations with no software budget: https://www.reddit.com/r/FPandA/comments/1twllle/167_excel_books_and_15_powerpoints/
2. SlightMetal51, payroll-to-ERP mapping across providers, countries and currencies with recurring schema changes: https://www.reddit.com/r/Accounting/comments/1tf39fc/anyone_solved_the_payrolltoerp_reconciliation/
3. ukmike92, multi-currency Xero workflow and material accounting cost: https://www.reddit.com/r/smallbusinessuk/comments/1vc6n4p/accountant_charging_10kyear_despite_xero_am_i/
4. EvilLipgloss and peers, close duration under merger, multi-ERP and intercompany complexity: https://www.reddit.com/r/Accounting/comments/1r8eikp/monthend_closing_average_time/
5. Diligent-Food4130, manual reconciliation, older ERP and Excel workarounds: https://www.reddit.com/r/CFO/comments/1valngc/monthend_close_is_slowly_killing_my_team/
6. Multiple-ERP controller discussion, manual transfers and a large unresolved financial difference: https://www.reddit.com/r/Accounting/comments/1vtwrbp/i_just_found_out_my_controller_exclusively_uses_a/
7. QuickBooks manufacturing workflow, manual transfer into management-report templates and fragility when line items change: https://www.reddit.com/r/Accounting/comments/1ok4dvm/how_to_automate_monthend_reporting/
8. NetSuite close discussion, manual pulls and the time spent investigating differences after they are found: https://www.reddit.com/r/Netsuite/comments/1t7yktt/why_is_monthend_closing_so_painful_a_data/
9. Balance-sheet reconciliation discussion, rolling account workbooks and need to prove balances: https://www.reddit.com/r/Accounting/comments/1plarlx/how_does_everyone_reconcile_and_monitor_balance/
10. Multi-channel e-commerce discussion, sales, fees and ads across Shopify, Amazon and Etsy: https://www.reddit.com/r/ecommerce/comments/1oa8mo9/how_do_you_mange_financials_across_multiple_sales/
11. Shopify/Amazon with QuickBooks, lump-sum payouts, refunds, fees, adjustments and tax: https://www.reddit.com/r/quickbooksonline/comments/1rvx6ak/how_do_you_handle_amazon_and_shopify/
12. Shopify payout bookkeeping, bundled refunds, chargebacks and fees with price sensitivity: https://www.reddit.com/r/AskAccounting/comments/1vaab8h/any_bookkeeping_service_that_handles_shopify/
13. E-commerce seller stack, marketplace payouts, refunds, ad spend, supplier payments and international suppliers: https://www.reddit.com/r/ecommerce/comments/1t729nb/best_small_business_accounting_software_for/

## Theme counts

- Reconciliation and exception investigation: 11 signals.
- Spreadsheet/report fragility: 5 signals.
- Multiple systems or schema drift: 5 signals.
- Cost or implementation friction: 5 signals.
- Payout components, fees, refunds or cutoff: 4 signals.
- Multi-currency or cross-border complexity: 4 signals.

## Reproducibility note

Counts were manually coded from the bounded inventory above. To update the report, re-open every source, confirm it remains available, add or remove inventory items, re-code all themes consistently, update the artifact snapshot and regenerate the portable report. Do not compare future counts as a trend unless the search method, time window and inclusion criteria are held constant.
