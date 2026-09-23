# Reference Sources and Licenses

What external material may inform this skill's guidance, and how. Rule of thumb: **adapt ideas with attribution; never copy text**. When you draw on an external source for a pattern, structure, or definition, record it as `observed` evidence with the source name and a locator (URL or document section), and restate the idea in your own words for the bank's context. If a source's license is unclear or its terms forbid reuse, do not reproduce it — describe the concept generically instead.

## Usable sources and their licenses

| Source | License | What to take from it |
|---|---|---|
| FIBO (EDM Council financial industry ontology) | MIT | Conceptual patterns: parties, roles, agreements, instruments; how finance domains separate contracts from products from accounts |
| Apache Fineract | Apache-2.0 | Open-source core banking: vocabulary and structure for loan accounts, savings accounts, charges, transactions; field naming conventions as examples |
| Open Data Contract Standard (ODCS, Bitol) | Apache-2.0 | How to structure data contracts and field-level descriptions; informs the artifact contracts |
| DBML (dbdiagram) | Apache-2.0 | Concise model notation ideas; readable relationship syntax for drafts |
| dbt-agent-skills | Apache-2.0 | Workflow patterns for analytics engineering with AI agents: staged SQL authoring, review discipline, project layout habits |
| dbt-audit-helper | Apache-2.0 | Comparison/reconciliation query patterns: comparing old vs new or source vs target row sets, symmetric-difference style controls |
| Wren engine (core) | Apache-2.0 — note: its RLS/CLS capabilities are separately **commercially licensed** | Semantic-layer and modeling-over-SQL concepts from the Apache-2.0 core only. Do not reproduce or rely on RLS/CLS material without a license check |
| GLEIF (Legal Entity Identifier data and docs) | CC0 | Entity-identification concepts, LEI as counterparty identifier; CC0 data/documentation may be reused with attribution as good practice |

## Use-with-care (conceptual reference only)

- **BIAN** — service and domain definitions are widely referenced, but terms of use are membership/licence-governed; reference the idea of banking service domains conceptually, do not copy definitions or diagrams.
- **ISO standards** (ISO 20022, ISO 4217, ISO 3166, ISO 8583) — standards text is copyrighted. Referring to a code or concept ("ISO 4217 currency codes") is fine; reproducing tables or spec text is not. Use the bank's own licensed copies for details.
- **UK Open Banking** — specifications carry their own licence terms; cite conceptually, do not copy payloads or text.

## Excluded entirely — do not reproduce or paraphrase

- **Vendor core-banking internals** (e.g., Temenos T24 tables/fields): work only from documentation the bank itself is licensed to share with you.
- **SWIFT MT/MX message specifications** and **card-network specifications / ISO 8583** layouts: proprietary; describe flows in generic terms only.
- **IFRS 9 / EBA / Basel regulatory text**: no unlicensed reproduction. Work from the bank's own documented definitions of default, provisioning, and impairment; treat standards concepts generically.

## Practical workflow

1. Need a pattern or definition? Prefer this skill's own references first; they already adapt the sources above.
2. If you must consult an external source, check the license in this file or look it up; when uncertain, treat as restricted.
3. Record the borrow: evidence row (`observed`), source + locator, and a note on how the idea was adapted.
4. Never paste restricted text into artifacts, code comments, or the evidence ledger itself.
