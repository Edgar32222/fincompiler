# FinCompiler market-validation playbook

Last reviewed: 2026-08-24

## Decision

FinCompiler's first design-partner segment should be a Finance Manager, Financial Controller, or hands-on Head of Finance in a 10-200 employee trading, distribution, light-manufacturing, or multi-entity services business.

The qualifying workflow is specific:

- monthly close depends on three or more Excel/CSV exports;
- at least two accounting, sales, inventory, marketplace, or subsidiary systems must be reconciled;
- source columns, account mappings, currencies, or posting patterns change often enough to break a workbook;
- the user personally owns the tie-out or reviews the final management pack;
- replacing the ERP or buying a large close-management suite is not an immediate option;
- the user can test locally with anonymized headers, 20-50 representative rows, and trusted control totals.

The initial promise is not "AI finance automation." It is:

> Bring the exports that currently make month-end painful. FinCompiler runs locally, stops on uncertain mappings, traces every number to the source, identifies the records and controlled reasons behind a variance, and produces a reviewable pack without a silent plug.

## Segment hypotheses

| Segment | Repeated pain | Product fit now | Access for learning | Decision |
| --- | --- | --- | --- | --- |
| Finance teams in trading, distribution and light manufacturing | Multiple exports, legacy ERPs, Sales/GL/inventory differences, currency and management packs | High | Medium through Reddit, X and accounting advisers | Primary |
| Fractional CFOs and small accounting/advisory firms | Same reconciliation pattern repeated across several clients | High, with strong referral leverage | Medium | Partner lane |
| Multi-channel e-commerce finance/bookkeeping | Payouts bundle sales, fees, refunds, chargebacks and timing differences | Medium-high, but specialized connectors already exist | High | Secondary problem test; do not build a connector yet |
| Multi-country payroll teams | Provider schema drift, account mapping and multi-currency reconciliation | Partial | Low; enterprise security and payroll semantics are substantial | Defer until the core is proven |
| Businesses wanting tax filing or general bookkeeping | Broad compliance and service need | Low | High | Disqualify; not the current product |

## Qualification score

A candidate is qualified when at least five of the following seven statements are true, including the first two:

1. The workflow repeats monthly or more often.
2. The candidate owns, prepares, reviews, or approves the reconciliation.
3. Three or more source files are involved.
4. At least two systems, entities, currencies, or sales channels are involved.
5. A recent close took more than four working days or the target reconciliation took more than four active hours.
6. The current workbook has broken because headers, accounts, timing, or source structure changed.
7. The candidate will commit to two cycles and can provide anonymized sample rows plus trusted totals.

Do not recruit someone merely because they dislike Excel. The product needs a repeated, controlled reconciliation with a verifiable before-and-after outcome.

## Discovery interview: 30 minutes

### 1. Reconstruct the last close, not the ideal process

- Walk me through the last monthly close from the first export to the final pack.
- Which files and systems were involved? Who produced each file?
- Where did you wait, copy/paste, reformat, or re-key data?
- Which reconciliation or report took the longest active time?

### 2. Examine the last real exception

- Tell me about the last difference that did not tie. What was the amount and how did you investigate it?
- Was it caused by timing, a split or merged posting, fees, refunds, tax, FX, duplicate rows, an account mapping, or something else?
- What evidence did the reviewer require before accepting the explanation?
- What happened to unresolved small differences?

### 3. Test schema and currency risk

- What changed in a source file during the last six months?
- How did the workbook fail, and how did you notice?
- Which currency amount is authoritative: transaction, accounting/base, or reporting currency?
- Who approves exchange-rate sources and cutoff policy?

### 4. Establish the buying and adoption boundary

- What have you already tried, and why did it not stick?
- What would make you refuse to use a new tool even if it saved time?
- Do you need the result in Excel, PDF, the ERP, or a close-management tool?
- If a local pilot solved one reconciliation, who would approve using it for a second month?

### 5. Ask for evidence, not praise

- May we use anonymized headers, 20-50 representative rows, and the totals you trust to reproduce this workflow locally?
- Can we time the current process once, then repeat the same measurement with FinCompiler?
- What result would make this pilot a failure?

Avoid asking "Would you use this?" or "Do you like the idea?" Those questions reward politeness rather than reveal behavior.

## Evidence capture template

Record one page per conversation:

- Public source or referral channel; no inferred private identity.
- Role in the workflow and decision influence.
- Company shape: approximate employee band, entities, currencies, channels and systems.
- Trigger event and most recent close period.
- Files, row counts and recurring transformations.
- Current active time, elapsed close time and review/rework time.
- Last concrete variance and investigation steps.
- Current workaround and annual or monthly cost if volunteered.
- Required controls, lineage and deliverable format.
- Security and local-data constraints.
- Anonymized sample availability and two-cycle commitment.
- Exact language used to describe the pain.
- Strongest disconfirming evidence.
- Next step, owner and date; or explicit reason disqualified.

Never record a login/recovery email, personal employer details that the person did not provide for the pilot, or scraped contact information.

## Pilot contract and success measures

The pilot unit is one recurring reconciliation workflow across two monthly cycles, not a product tour.

Activation requires:

- at least three source exports;
- anonymized rows and trusted control totals;
- an explicit mapping and currency policy;
- a baseline time measurement;
- a named Finance reviewer.

Success requires all of the following:

- first trusted result in under 30 minutes after company setup;
- at least 50% less active preparation time in the second cycle;
- at least 95% of reconciliation variance attributed to deterministic record-level causes;
- zero silent mapping, FX, duplicate or balancing corrections;
- no manual rebuilding of the output pack in the second cycle;
- reviewer signs off or documents the exact missing evidence preventing sign-off.

## Market-validation KPI framework

### 14-day learning sprint

- 20 relevance-screened public candidates or referral introductions.
- 5 completed problem interviews.
- 2 candidates willing to provide anonymized sample structure and trusted totals.
- 1 locally activated pilot.
- At least 3 interviews in the primary segment before changing the target segment.

### 30-day evidence gate

- 10 qualified problem interviews.
- 3 activated pilots.
- 2 pilots complete cycle one.
- At least 2 of 3 activated pilots return for a second monthly cycle.
- One repeated pain pattern accounts for at least 4 of the 10 qualified interviews.

### Guardrails

- Zero LinkedIn activity.
- Zero founder employer or colleague exposure.
- Zero unsolicited bulk messages.
- Zero source financial data uploaded to a hosted service.
- Zero silent financial corrections.

Reply rate, follower count, page views and compliments are diagnostic only. They are not proof of product value.

## Fourteen-day execution plan

### Days 1-2: make the invitation credible

1. Finalize a product-only X and Reddit identity.
2. Publish a minimal public landing page with the local-first promise, a two-minute synthetic workflow, limitations and privacy terms.
3. Provide one privacy-safe contact route controlled by the product identity.
4. Prepare a 90-second screen recording using only synthetic data.

### Days 3-7: problem-first recruiting

1. Publish one evidence-led Reddit post in a community whose rules permit it.
2. Reply helpfully to relevant public discussions without inserting a pitch where promotion is prohibited.
3. Send no more than five individually relevant invitations that cite the person's public problem and ask for a workflow interview, not a sale.
4. Publish one X thread showing how a small Sales/GL difference is traced without a plug.
5. Stop any channel that produces spam complaints or low-fit conversations.

Every external post, reply or direct message requires the founder's approval immediately before sending.

### Days 8-10: turn conversations into evidence

1. Run five interviews with the guide above.
2. Ask for anonymized structure only after the workflow and trust boundary are clear.
3. Score every conversation, including disqualifications.
4. Select at most two pilot workflows; do not accept a broad ERP replacement project.

### Days 11-14: activate one pilot

1. Reproduce the current workflow locally.
2. Record unsupported mappings and missing reason rules as product evidence.
3. Compare the result with the trusted totals and baseline active time.
4. Agree the second-cycle date before calling the pilot activated.

## Product decisions driven by discovery

Build a feature only when it is supported by one of these evidence levels:

- **Level 1 — public signal:** useful for interview questions, not a roadmap commitment.
- **Level 2 — verified workflow:** a user reconstructs the problem and current workaround in detail.
- **Level 3 — sample reproduced:** FinCompiler reproduces the issue with anonymized data and trusted totals.
- **Level 4 — repeated pilot:** the feature reduces measured work across two cycles without weakening controls.

The current roadmap should prioritize features reaching Level 3 or 4. A loud public post alone is not enough.

## Founder input required before outreach starts

1. Create or confirm product-only X and Reddit profile handles; do not use a personal or employer-linked identity.
2. Choose a privacy-safe contact route for pilot applicants.
3. Approve the exact first batch: one Reddit post, one X thread and up to five targeted invitations.
4. Be available for five 30-minute discovery calls, or authorize a pseudonymous text-only interview format.
5. Decide whether the pilot will be free for two cycles or use a refundable commitment deposit. Start free only if the user commits data, time and a second cycle.
