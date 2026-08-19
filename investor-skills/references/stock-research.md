# Stock Research

Two jobs: build a **research snapshot** for a name, and keep it current through **earnings updates** and the **thesis tracker**. The snapshot answers "what is this business and what does the market expect"; the tracker answers "is my reason for owning it still true".

## Research snapshot

Collect five blocks, then synthesize. If the user provides only a ticker, search the web for each block and cite as-of dates.

**1. Expectations (what's priced in).** Consensus estimates if findable (EPS, revenue, growth). If no consensus exists (common for VN small/mid caps), use sell-side notes, company guidance, or your own base case from history — and say which it is. High dispersion = genuine disagreement = opportunity if you have a differentiated view.

**2. Fundamentals (business quality).** Last 3-5 fiscal years:

| Metric | FY-2 | FY-1 | FY0 | Trend |
|---|---|---|---|---|
| Revenue | | | | |
| Gross margin | | | | |
| Operating margin | | | | |
| ROE / ROIC | | | | |
| Net debt / EBITDA | | | | |
| FCF margin | | | | |

Quality signals: revenue growth with stable/expanding margins, ROIC consistently above cost of capital, FCF conversion near net income. Degradation signals: receivables/inventory growing faster than sales, margin propped by one-offs, rising leverage against flat EBITDA.

**3. Price context.** Current price, 52-week range position, 1Y return vs local index, beta, dividend yield. Momentum is context, never a thesis by itself.

**4. Macro/sector backdrop.** One short paragraph: policy rates, sector cycle, regulation. Tailwind or headwind for this specific business — not generic macro commentary.

**5. Synthesis — the snapshot output:**

```
[Company] — [one-line business description] — [verdict for now]

Valuation: P/E [x] vs sector [x] | EV/EBITDA [x] | Div yield [x]%
Thesis (bull): ...
Thesis (bear): ...
Catalysts next 12M: ...
Fair-value range: [low–high] (method: DCF/comps/mixed, see valuation.md)
Conviction: high/medium/low — and what would raise or break it
```

## Earnings update (post-results check)

Run this whenever a holding or watchlist name reports. Keep it to one page — what's NEW, not a re-hash of the company.

1. **Verify freshness first.** Search "[company] latest quarterly results", confirm the report is within ~3 months. Training-data numbers are stale; today's date goes at the top.
2. **Beat/miss vs expectations**, quantified: "Revenue +8% YoY, ~3% above guidance" — then WHY (price vs volume, one-offs, FX…).
3. **Key metrics vs trend**: revenue, margins, and the 2-3 business KPIs that matter for this company (subscribers, backlog, same-store sales, NIM for banks…). One-off gains get normalized.
4. **Guidance**: raised / maintained / cut — this usually moves the stock more than the print.
5. **Thesis impact**: does the result strengthen, weaken, or not touch each pillar of the thesis (see tracker below)? State the action: no change / add / trim / exit.

## Thesis tracker

Every position gets a falsifiable thesis, registered at purchase and re-scored quarterly (even when nothing dramatic happened — drift kills).

**Register:**

```markdown
## [Ticker] — [Long] — opened [date] @ [price]
Thesis (1-2 sentences): e.g. "FPT: margin expansion from digital-transformation mix shift + Global IT services growth"
Pillars: 3-5 testable claims, each with "on track / behind / broken"
Invalidation: what specifically makes me exit (thesis broken ≠ price down)
Catalysts: dated events that prove/disprove pillars
Value if right: fair-value range from valuation.md
```

**Scorecard (update each quarter or each material event):**

| Pillar | Expectation | Status | Trend |
|---|---|---|---|
| Revenue growth >20% | Q3: 22% | On track | Stable |
| Margin expansion | Flat YoY | Behind | Concerning |

Log format per event: date → what changed → which pillar it hits → action taken → conviction now (H/M/L).

Rules: a pillar "broken" with price still up is still broken — act on the thesis, not the price. Distinguish "thesis wrong" from "thesis early" (catalyst delayed but intact). Store theses as markdown files in the user's workspace so they persist across sessions; one file per ticker.
