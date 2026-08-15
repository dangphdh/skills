---
name: deep-research
description: How to conduct multi-round, source-cited deep research on any topic using parallel research subagents with web search. Use whenever the user asks to research, investigate, deep-dive, survey the state of, find out about, or compare options with evidence — even if they don't say "research". Covers quick lookups to exhaustive multi-round studies; produces a cited markdown report plus a chat summary.
---

# Deep Research

Multi-round, source-cited research using parallel subagents. Deliverables: (1) a markdown report saved to disk, (2) an executive summary in chat, (3) an honest list of open questions.

## What to confirm before starting

Ask one batched question, then proceed — don't interrogate:

- **Depth**: quick / deep / exhaustive? Default to **deep** and say so.
- **Recency**: if the topic is fast-moving (models, prices, versions, regulations), ask for a cutoff. Default: facts from the last 12 months, older OK for background.
- **Language**: default to the language of the user's question.

If the user skips answering, run deep mode with these defaults and state the assumptions in the report header.

## Depth modes

All modes run the same workflow; they differ in breadth:

| Mode | Round-1 subagents | Gap rounds | When |
|---|---|---|---|
| quick | 2 | none | Simple lookup, user in a hurry |
| deep (default) | 3–5 | 1 | Normal research request |
| exhaustive | up to 6 | up to 2 | High-stakes decisions, user wants everything |

Never start exhaustive mode without explicit confirmation — it is expensive.

## Workflow

1. **Restate the question** in one or two sentences and confirm depth + deliverable. If the question is vague, narrow it with the user before spending subagents.

2. **Plan the decomposition.** Break the question into 3–6 sub-questions that together cover it. For each, list 2–4 search phrasings — different keywords, and a second language when the topic has strong non-English coverage. Show the plan to the user in 3–5 lines before fanning out.

3. **Fan out.** Launch all round-1 subagents in parallel in a single message. Each subagent prompt must be self-contained — subagents start fresh and cannot see this conversation. Include:
   - The sub-question with enough context to research it standalone
   - Tool guidance: WebSearch first, then WebFetch or the web-reader MCP tool to open promising results. WebSearch skews US-region, so try multiple phrasings.
   - The recency cutoff, if any
   - This required return format:

     ```
     ## Findings
     - <claim — specific, quantitative where possible> — Source: "<title>" (<publisher>, <publish date>) <URL> [confidence: high|medium|low]
     ## Gaps
     - <what you could not establish, and why>
     ```

   - An instruction NOT to use browser automation (it is main-agent-only). If a page truly needs a real browser, the subagent reports that as a gap.

4. **Review the returns.** Read all findings and mark three things: gaps (sub-questions with thin coverage), contradictions (sources that disagree), and load-bearing claims (facts your conclusion depends on).

5. **Fill the gaps.** In deep and exhaustive modes, launch a second round of parallel subagents covering only the gaps and contradictions. In exhaustive mode, repeat once more if still thin. Stop when a round produces no new information.

6. **Verify.** Every load-bearing claim needs at least two independent sources — two outlets that reported it separately, not one citing the other. Fetch the actual page for each; a search snippet is not evidence. If unsure how much to trust a source, read `references/source-quality.md` before weighting it.

7. **Synthesize.** Read `references/report-templates.md` and pick the skeleton matching the research type (survey / comparison / due-diligence / timeline / explainer). Write the report yourself — subagent output is raw material, not the report. Save it as `research-<topic-slug>-<YYYY-MM-DD>.md` in the current workspace; if the repo already has a notes/docs convention, follow it instead and say where you put the file.

8. **Report back.** In chat: a 5–10 sentence executive summary, the file path, and the open questions.

## Citations

- Number sources `[1]…[n]` in order of first use; inline citations point into a Sources section at the end.
- Each Sources entry: title, publisher/author, publish date, URL, and date accessed.
- Cite every non-trivial claim. Uncited text is limited to your own analysis and transitions.
- When sources disagree, present both with citations and say which is better supported and why. Never average away a contradiction.

## Tool constraints

- Subagents use web search + page fetching only. Browser automation (browser-use) is main-agent-only — if a key page needs it, handle it in the main thread between rounds.
- Paywalled or JS-only pages: note as a gap rather than guessing at content.

## Quality checks before you call it done

- [ ] Every non-trivial claim has a citation
- [ ] Every load-bearing claim verified against ≥2 independent sources, or flagged as single-source inline
- [ ] Publication dates checked; stale facts labeled with their as-of date
- [ ] Contradictions presented openly, not smoothed over
- [ ] Gaps and open questions listed honestly
- [ ] Report saved to disk; file path given in chat
- [ ] Executive summary delivered in chat

## What NOT to do

- Don't fabricate or guess URLs — cite only pages actually fetched.
- Don't cite search snippets for load-bearing claims — fetch the page.
- Don't launch exhaustive mode without confirmation.
- Don't paste raw subagent output as the report — synthesize.
- Don't let subagents use browser automation.
- Don't keep running rounds when findings stop changing — depth is not thoroughness.
