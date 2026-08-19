---
name: investor-skills
description: Personal investing toolkit — equity research, stock analysis, company valuation (DCF, comps), earnings analysis, investment thesis tracking, stock screening / idea generation, and portfolio management (allocation, rebalancing, performance). Use whenever the user mentions stocks, shares, cổ phiếu, valuing a company, DCF, financial statements, earnings results, buy/hold/sell decisions, watchlists, or their portfolio — even casually ("is NVDA cheap?", "should I trim FPT?", "review my holdings").
---

# Investor Skills

A personal-investor workflow covering the full loop: **find ideas → research a stock → value it → decide & track → manage the portfolio**. Distilled from Anthropic's financial-services skills (Apache-2.0), adapted for an individual investor — no Bloomberg/LSEG access assumed, web search + user-provided data are the sources.

## Core principles

These apply to every task in this skill:

1. **Every data point must connect to a thesis.** The question is never "what are the numbers" but "where might the market be wrong about this business?" Numbers serve the narrative; they are not the narrative.
2. **A thesis must be falsifiable.** If nothing could disprove it, it's not a thesis — it's a hope. Track disconfirming evidence as rigorously as confirming evidence.
3. **Current data only.** Training data is stale. Before any analysis, search the web for the latest price, earnings release, and guidance. Write down today's date and the date of every figure used; if a "latest" quarterly report is older than ~3 months, search again.
4. **Ranges, not points.** Always present valuation as a range (bear/base/bull) with the assumptions that drive each end. A single target price hides the uncertainty that actually matters.
5. **Educational, not advice.** Frame output as analysis for the user's own decision-making. Never state "you should buy" as certainty; state the conditions under which the thesis holds or breaks.

## Workflow router

Read the reference that matches the task. Tasks often chain (screen → research → value → track):

| Task / user phrasing | Read first |
|---|---|
| "Find ideas", "screen stocks", "what looks interesting", "pitch me something" | [references/idea-generation.md](references/idea-generation.md) |
| "Analyze [company]", "what do you think of FPT", research snapshot, fundamentals | [references/stock-research.md](references/stock-research.md) |
| Quarterly results, "earnings", beat/miss, post-earnings thesis check | [references/stock-research.md](references/stock-research.md) § Earnings update |
| "What's it worth", DCF, intrinsic value, comps, "is it cheap" | [references/valuation.md](references/valuation.md) |
| "My portfolio", allocation, rebalance, performance review, tracking holdings | [references/portfolio.md](references/portfolio.md) |

Typical chain for a new name: idea screen → research snapshot → valuation → if purchased, register a thesis (stock-research.md § Thesis tracker) and revisit quarterly.

## Data sourcing

No paid terminals assumed. Priority order:

1. **User-provided files** — broker statements, Excel exports, annual reports (PDF). Parse these first; they're the ground truth for the user's actual portfolio.
2. **Web search** — latest price, market cap, shares outstanding, recent earnings, consensus estimates if findable. Always note the as-of date.
3. **Primary sources** — investor relations pages, annual/quarterly reports, SEC EDGAR (US) or exchange filings.

Vietnam market (HOSE/HNX, e.g. FPT, VNM, VIC): data is on Cafef, Vietstock, VNDirect, or company IR pages. Vietnamese-language sources are fine — translate key figures into the output. Watch for: 2 reporting standards (VAS vs IFRS), foreign-ownership limits, and thin trading volumes distorting prices. Consensus estimates are scarce; lean harder on own-model valuation and historical baselines.

## Output conventions

- Tables for any multi-metric comparison; state units and currency (VND vs USD millions) explicitly.
- Every figure carries an as-of date. Estimates marked "E".
- End any stock analysis with: **verdict (buy/hold/sell/avoid for now), fair-value range, bull case, bear case, catalysts, conviction (high/medium/low)** — see stock-research.md for the template.
- Match the user's language for prose (Vietnamese + English finance terms is common); keep standard metric names in English.
