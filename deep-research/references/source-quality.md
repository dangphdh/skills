# Source Quality & Search Strategy

Read this when weighting evidence or deciding whether a source deserves a citation. Apply it during verification (workflow step 6), not as a reason to stall the research.

## Source tiers

| Tier | Examples | How to treat |
|---|---|---|
| 1 — Primary | Official docs, specs, standards, filings, source code, first-party APIs, peer-reviewed papers, raw datasets | Best available. Prefer even when a secondary write-up is more convenient. |
| 2 — Reputable press & technical press | Major outlets, established tech/industry publications | Solid for facts and reporting; watch editorial slant on opinions. |
| 3 — Vendor & interested parties | Vendor blogs, analyst reports, lobbyists, PR | Evidence of what the vendor claims, not of what is true. Attribute: "according to <vendor>…". |
| 4 — Individual experts | Practitioner blogs, personal sites | Weight by track record and whether claims are checkable. |
| 5 — Communities | Reddit, HN, Stack Overflow, forums, social | Leads and signal for what to investigate — not citation-grade evidence. |
| Avoid | SEO content farms, undisclosed AI-generated sites, scrapers republishing others' work | If a page's only value is restating a tier-1/2 source, cite the original instead. |

Two rules that follow:

- **"Independent" means independently reported.** Two outlets running the same wire story or republishing one press release count as one source. Near-identical headlines across outlets usually mean a PR cycle — find the original press release and treat it as tier 3.
- **A tier-5 lead that checks out at tier 1–2 becomes a tier 1–2 citation.** Cite where it was verified, not where it was found.

## Red flags

Downgrade or discard a source that:

- Has no author and no date
- Republishes a press release with minimal editing
- States numbers without units, denominators, or a source
- Attributes to "experts" or "studies say" without naming them
- Predates a major correction and hasn't been updated (see verification below)

## Search strategy

Use during decomposition and gap rounds:

- **Multiple phrasings**: synonyms, jargon vs plain language, full names vs abbreviations. WebSearch skews US-region — for topics with strong coverage elsewhere, add a query in the relevant language.
- **Domain targeting**: `site:gov`, `site:edu`, `site:arxiv.org`, `site:docs.<vendor>.com`, or a specific outlet for its coverage.
- **Recency**: for fast-moving topics, restrict to recent results (or include a year in the query) and prefer pages with visible publish dates.
- **Adversarial queries**: deliberately search the opposing view — "<claim> criticism", "<option> problems", "<claim> debunked". A survey that only found confirming sources missed half the picture.
- **Citation chaining**: from one good source, follow its references backward (what it builds on) and search cited-by / coverage forward (who reacted to it).

## Verification techniques

Apply to load-bearing claims:

- **Claim-level cross-check**: ≥2 independent sources (per the independence rule above). One source + its republishers = single-source; flag it inline as such.
- **Statistics sanity checks**: What are the units? Absolute vs per-capita vs percentage? What's the denominator and base rate? Does the number hold against a rough estimate? A figure that "feels big" often isn't once normalized.
- **Later corrections**: search `"<claim>" correction OR retracted OR updated` before repeating a surprising fact — it may have been walked back after you first found it.
- **Date the claim, not just the page**: a 2026 article can cite 2019 data. Label fast-moving facts with their as-of date.
- **Fetch before citing**: search snippets truncate and paraphrase; open the page and confirm the claim actually appears as stated. If you can't fetch it (paywall, JS-only), either drop the claim or mark it unverified.
