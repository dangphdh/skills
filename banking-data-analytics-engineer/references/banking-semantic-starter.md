# Banking Semantic Starter

Candidate definitions for common banking terms, to seed glossaries and models. **These are generic seeds, not the bank's definitions.** Banks and jurisdictions differ; regulation-specific definitions vary; vendor systems overload terms. Every definition adopted from here must be validated against the bank's own glossary or owners and logged in `evidence-ledger.csv` as `assumed` until confirmed. This file contains no regulatory text and no vendor-specific semantics.

## Party and relationships

- **Party** — a person or organization the bank has a record of. A party may play many roles.
- **Customer** — a party with an established relationship; banks differ on whether prospect and closed relationships count.
- **Role** — how a party relates to an arrangement: holder, borrower/co-borrower, guarantor, beneficial owner, counterparty, signatory. Roles are per-arrangement, not global.

## Agreements and accounts

- **Arrangement/agreement** — a contract between party and bank; "account" is usually a specialization. Vendor systems often model deposit and lending accounts in different tables with different grains — verify, do not assume one table.
- **Current/checking account** — demand deposit with transactional access. **Savings account** — interest-bearing deposit, often with withdrawal constraints. **Term deposit** — fixed term and maturity.
- **Loan/facility** — lent amount under an agreement; one facility may have multiple drawdowns. **Credit card account** (generic) — revolving facility with statement and payment cycles; avoid card-network internals, which are proprietary.
- **Product** — the template an arrangement instantiates; product-to-arrangement is usually 1:N.

## Money movement and balances

- **Transaction/posting** — a movement event. Distinguish **posting date** (when recorded) from **value date** (when effective); both exist in most systems and analytics differ by which governs.
- **Ledger balance vs available balance** — recorded balance vs balance net of holds/pending items. Confirm the bank's exact definitions; they vary.
- **Principal outstanding** — remaining lent principal. **Accrued interest** — earned/owed but not yet paid; accrual rules are bank-specific.
- **Fee event** — charge posted under a schedule; fee codes are bank-defined reference data.
- **Settlement** — the exchange of value completing a transaction; timing depends on scheme and rails, which are bank/scheme-specific.

## Lifecycle and risk (generic concepts only)

- **Origination** — application through disbursement. **Maturity** — contractual end. **Restructuring/refinancing** — changed terms; banks define eligibility differently.
- **Delinquency/overdue** — payment past due; aging buckets are bank-defined. **Default** — a regulated, bank/jurisdiction-specific definition; never assume one. **Write-off** — accounting recognition; timing is policy-specific. **Provision/impairment** — regulated accounting constructs; this skill works only from the bank's own documented definitions and never reproduces standards text.

## Organization and reference data

- **Branch/unit** — organizational node; hierarchies change over time, so capture effective dates.
- **GL account / chart of accounts** — the bank's accounting taxonomy; control accounts aggregate sub-ledgers, which is what reconciliations exploit.
- **Currency** — ISO 4217 codes as reference data; conversion policy is bank-specific (see `mapping-quality-and-reconciliation.md`).
- **Business calendar / holiday center** — determines business dates and cutoffs; bank-defined.

## Using this file

1. Propose the seed definition in `glossary.csv` with the glossary status `proposed` (validation pending; see `artifact-contracts.md` for the glossary status vocabulary).
2. Ask the owner to confirm or correct; record the answer as `observed` evidence and update the definition.
3. Where the bank's definition conflicts with the seed, the bank wins; note the divergence.
4. Never map a vendor field to one of these terms from its name alone — that is Workstream B's undocumented-field rule.
