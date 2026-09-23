# Review Summary — Retail Loan Principal Movement Analysis (Synthetic Example)

Project ID: PRJ-0001
Status: draft
Last updated: 2026-09-23

## Purpose

Structural example project for the banking-data-analytics-engineer skill: a
monthly net principal movement and principal event count analysis over a
synthetic retail-loan extract, kept partitioned by currency. All names,
identifiers, codes, amounts, and dates are synthetic placeholders created for
template and test use; nothing here describes a real bank, person, or account.

## Workstream notes

- domain-modeling: PARTY (effective-dated), LOAN_ACCOUNT (currency and portfolio segment), and LOAN_EVENT (signed amounts, posting and effective dates, reversal linkage) drafted from the synthetic extracts.
- product-discovery: glossary drafted from extract headers; reversal, effective-date, and posting-date terms marked proposed pending owner confirmation.
- data-mining: account-month net principal movement and principal event count query drafted; reversals handled by matched-pair removal, fees excluded, duplicate rows guarded by dedup stages; PostgreSQL named but unconfirmed, so the draft stays DIALECT_UNVALIDATED.
- quality-reconciliation: event-to-ledger reconciliation drafted for two currencies with count, amount, and no-double-count controls; monetary controls grouped by the currency field; results stay partitioned by currency.

## Evidence summary

- Observed: synthetic extract headers and sample rows for the party, loan account, and loan event files, including fee rows (EVD-0007) and two reversal pairs (EVD-0008).
- Inferred: reversal rows negate their original event through reversal_link_id with the negated amount (EVD-0003).
- Assumed: calendar-month effective-date grain (EVD-0004) and the example late-arrival rule (EVD-0009).
- Open questions: FX conversion policy for non-VND amounts (EVD-0005, cited by the query spec and reconciliation plan; no conversion is applied while it is open) and whether a repayment-schedule source exists for any days-past-due analysis (EVD-0010). The event extract intentionally contains one duplicated event row so the duplicate guard and QR-001 have something to catch.

## Validation status

Structural validator run from the installed skill's scripts directory (not
project-relative) against this project directory is expected to pass clean at
draft. Structural validation checks artifact shape and internal consistency
only; it does not check banking correctness.

## Human validation

- Reviewer: not yet assigned
- Date: (none — no validation has occurred)
- Outcome: pending
- No evidence row is confirmed_by_human; every validation_state is pending, consistent with the unassigned reviewer.

## Known limitations

All data is synthetic and structurally motivated; signs and code lists
demonstrate the artifact contracts, not a real product. The analysis is a flow
analysis only: no balance, outstanding-principal, or delinquency figure can be
produced from these extracts (there is no balance snapshot and no
repayment-schedule source; see EVD-0010). FX conversion policy is unresolved
(EVD-0005), so monetary results stay partitioned by currency with no
conversion and no rate is asserted anywhere. Reconciliation tolerances remain
template placeholders; zero tolerance is not an approved value. The
late-arrival rule is a labeled example assumption (EVD-0009).
This summary records structure and process only. It is not a business,
financial, regulatory, or compliance certification, and the underlying data is
not real.
