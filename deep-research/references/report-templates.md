# Report Templates

Pick the skeleton that matches the research type. Every report shares the conventions below, then follows its skeleton. Adapt section titles to the topic — these are shapes, not forms to fill in blindly.

## Shared conventions (all reports)

- **Header block** at the top:

  ```
  # <Report title>
  **Research question:** <one or two sentences>
  **Date:** <YYYY-MM-DD> · **Mode:** <quick|deep|exhaustive> · **Assumptions:** <language, recency cutoff, scoping choices>
  ```

- **Executive summary**: 5–10 sentences, answer first. A reader who stops here leaves with the conclusion and its confidence level.
- **Contradictions** get their own subsection whenever sources disagree — never resolved silently.
- **Open questions**: what you could not establish and why (paywalls, thin coverage, conflicting data).
- **Sources**: numbered entries — title, publisher/author, publish date, URL, accessed date.
- **As-of labels** on fast-moving facts: "(as of 2026-08)".

## 1. State-of-the-art survey

For "what's the current state of X" / "where is Y heading" questions.

```markdown
# <Topic>: State of the Art
<Header block>

## Executive summary

## Background
Why this exists; the problem being solved. Keep short — 2–3 paragraphs.

## Current landscape
Group by approach / vendor / school of thought, not by source. Cite per claim.

## What works today
Concrete capabilities with evidence: benchmarks, shipped products, production usage.

## Limitations and open problems

## Recent developments
Dated, newest first. Label each with its as-of date.

## Outlook
Your synthesis, clearly marked as analysis. Distinguish extrapolation from citation.

## Open questions
## Sources
```

## 2. Option comparison

For "X vs Y vs Z, which should I choose" questions. Judge against the user's stated context; if they gave none, compare on general criteria and say so.

```markdown
# Comparing <options>
<Header block>

## Executive summary
Include the conditional recommendation: "If you <situation>, choose <option> because <reason>."

## Criteria
Table of what matters and why (drawn from the user's context).

## Comparison table
| Criterion | Option A | Option B | Option C |
One row per criterion; keep cells short — details go in prose below.

## Option profiles
### <Option A>
What it is · strengths · weaknesses · evidence (benchmarks, case studies, pricing).

## Head-to-head on the deciding criteria
Prose for the 2–3 criteria that actually drive the decision.

## Open questions
## Sources
```

## 3. Due diligence / fact investigation

For "is X true" / "what actually happened" / "should we trust X" questions. Verdict-first structure.

```markdown
# <Question under investigation>
<Header block>

## Verdict
The answer and confidence (high / medium / low) in 2–4 sentences.

## Key claims and evidence
### Claim 1: <statement>
Status: <supported | contested | unsupported>. Evidence per source, with dates.

## What holds up, what doesn't
Weigh the claims; explain the confidence level.

## Contradictions
Each disagreement: who says what, which is better supported and why.

## Open questions
## Sources
```

## 4. Event / news timeline

For "how did X unfold" / "history of Y" questions. Build the timeline from dated claims; undated claims go in a separate "context" section, never interleaved.

```markdown
# <Event>: Timeline
<Header block>

## Executive summary

## Timeline
| Date | Event | Source |
Newest first or oldest first — pick one and stay consistent.

## Context
Background that isn't itself dated.

## Disputed events
Where accounts differ.

## Open questions
## Sources
```

## 5. Explainer ("how does X work")

For mechanism/concept questions. The survey's structure minus the outlook; add a worked example.

```markdown
# How <X> works
<Header block>

## Executive summary

## The problem it solves
## How it works, step by step
Numbered mechanism, one concept per step, cite the authoritative description.

## Worked example
A concrete instance walked through the steps above.

## Common misconceptions
What people get wrong, with the correction.

## Variants and trade-offs
## Open questions
## Sources
```
