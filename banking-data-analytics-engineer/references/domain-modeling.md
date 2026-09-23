# New-Domain Discovery and Data Modeling

Workstream A: the bank wants analytics over a banking domain that is new to this project — there is no existing product model to reverse-engineer (that is Workstream B). Route here from SKILL.md. Use `banking-semantic-starter.md` for candidate term definitions; they are hypotheses to validate against the bank, never ground truth.

## Order of work

1. **Business question first.** Confirm `business_question` and `intended_decision` in `analysis-spec.json`. A model exists to answer decisions; the decision bounds the scope. "Model our lending data" is not a business question; "which segments drive month-end overdue balances" is.
2. **Harvest evidence before structuring.** Collect business glossaries, process documents, existing report definitions, table/column metadata, redacted sample records, and interview notes. Register sources in `source-inventory.csv`; log claims in `evidence-ledger.csv` as you read.
3. **Conceptual model.** Entities, events, relationships, cardinalities in business language.
4. **Logical model.** Attributes, keys, reference data, and a grain statement per entity in `model-spec.json`.
5. **Physical layer.** Only after the platform is confirmed by evidence.

## Conceptual layer

- Model events over statuses. "Loan application", "disbursement", "repayment", "write-off" are events; "active", "closed" are states that usually belong to a status history, not a single column.
- Separate balance snapshots from movements. A balance is a measure at a point in time for a grain; a transaction is an event. Confusing them is among the most common banking modeling errors; a monthly sum of events is a flow and must never be named or reported as an outstanding balance.
- Name relationships with verb phrases in business terms ("party holds account", "transaction posts to account"), not bare foreign keys.
- Candidate entities come from the evidence: every noun that appears in the business question, the glossary, or report headers is a candidate; every candidate needs at least one evidence row or it stays on the open-questions list.

## Logical layer

- Write a one-sentence grain statement per entity: "one row per account per business date", "one row per transaction event". If you cannot state the grain, the entity is not understood yet.
- Attributes get platform-neutral logical types and clear definitions; add nullability, classification, and per-attribute `evidence_ids[]` when the supplied evidence supports them. Entity-level evidence is mandatory. An unsupported attribute must not be presented as fact—either omit it or link it to an explicit `assumed`/`question` entry.
- Reference data (status codes, product types, currencies) is evidence-mapped too: record the observed code list and its source. If only some values are documented, say which.
- Keys: state the natural business key and the proposed surrogate separately; never assume a bank system's "ID" column is unique without a uniqueness rule or evidence.

## Physical layer

- Confirm platform and dialect first. While `platform.dialect` is empty (`""`), keep the model logical and set `dialect_validation: DIALECT_UNVALIDATED` in downstream query work.
- Naming follows the bank's observed conventions when evidence shows them; otherwise propose one convention, state it as `assumed`, and stay consistent.
- You may sketch physical datatypes and indexing ideas for discussion, but do not author production DDL and never execute anything (see `safety-and-evidence.md`).

## Evidence mapping and completeness

- Every entity, relationship, and attribute in `model-spec.json` carries `evidence_ids[]`. A reviewer must be able to trace any element to a document, table, or person in under a minute.
- Keep a standing open-questions list (from `question`-state evidence) in `review-summary.md`, each with a proposed owner.
- Validate against the business question: can every metric implied by `business_question` and `intended_decision` be computed from the modeled grain? If not, the model is incomplete — say where.

## Validation pass before handoff

- Terms in `glossary.csv` match entity and attribute names; no synonym drift ("client" vs "customer") without an alias entry.
- Each entity has one grain, non-empty `business_keys[]`, and evidence.
- Relationship cardinalities are justified ("a party may hold many accounts" — observed where?).
- Banking term definitions borrowed from `banking-semantic-starter.md` are marked for validation, not presented as the bank's definitions.

## Common traps

- Modeling reports or dashboards instead of the underlying domain.
- One "account" entity blending deposits, loans, and external accounts with incompatible grains — split by product family unless evidence shows one grain.
- Status columns read as lifecycle ("STATUS='A' means active") without a documented code list.
- Inventing rate accrual, fee, or delinquency rules — these are always bank-specific; capture them as questions.
