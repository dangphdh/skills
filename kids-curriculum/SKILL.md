---
name: kids-curriculum
description: How to design and write a math and language-arts curriculum, workbook, and lesson plans for kids ages 9–11 (Grades 3–5; maps to Vietnam Lớp 3–5 / Chương trình GDPT 2018). Use whenever the user wants to build, outline, or write educational material for upper-elementary children — a lesson, a unit, a chapter, a full workbook, worksheets, exercises, or answer keys — in English or Vietnamese (tiếng Việt) — even if they don't say "curriculum." Covers both math and language arts, produces teacher lesson plans plus illustrated student workbook pages (with inline SVG diagrams for fractions, geometry, and bar models), and exports to PDF or DOCX.
---

# Kids Curriculum (Grades 3–5, Math & English)

This skill designs and writes curriculum content for **upper-elementary students (ages 9–11, US Grades 3–5)** in **Mathematics** and **English Language Arts (ELA)**. For each unit it produces three artifacts:

1. **Teacher lesson plan** — objectives, pacing, teaching notes, differentiation
2. **Student workbook page** — explanation + practice problems the kid works through
3. **Answer key** — solutions and brief notes for the teacher/parent

## What to confirm before writing

If the user hasn't specified these, ask briefly (one batched message), then proceed. Don't interrogate.

- **Subject** — math or English for this unit? (this skill does both, one unit at a time)
- **Grade / level** — Grade 3, 4, or 5? If unclear, default to Grade 4 and say so.
- **Topic** — e.g. "fractions," "main idea in reading," "long division"
- **Scope** — a single lesson (~45 min), a multi-lesson unit, or a full chapter?
- **Language / locale** — English (US, CCSS) by default. If the user writes in or asks for Vietnamese, produce **all student-facing content in Vietnamese** and map the grade to **Vietnam's Chương trình GDPT 2018 (Lớp 3/4/5 = Grade 3/4/5)**. See the mapping note at the top of each concept reference. Other curricula (UK, IB PYP) map by age — same bands.

Keep these in a short "Plan" note at the top of the output so the user can correct quickly.

## How to use the reference files

Before writing content for a unit, read the relevant reference to get age-appropriate scope and avoid pitching the material too easy or too hard:

- **Math content** → read `references/math-concepts.md`. It lists what each grade should cover so you don't put long division in a Grade 3 unit or single-digit addition in a Grade 5 unit.
- **English content** → read `references/english-concepts.md`. Same idea: grammar, reading skills, and writing genres by grade.
- **Pedagogy** → read `references/pedagogy.md` when writing the lesson plan's **Differentiation** or **Notes-for-Teacher** sections, or whenever the topic has a well-known misconception. It covers the three-tier differentiation model (teach-up, not water-down), UDL as barrier analysis, and anticipated misconceptions.
- **Output formatting** → read `references/templates.md` for the exact structure of the three artifacts and how to assemble them into a printable document.

Read only the reference(s) you need for the current unit — don't load all four every time.

## Pedagogical rules (Grades 3–5)

These shape how content reads, regardless of topic.

1. **One concept per lesson.** Upper-elementary kids struggle when two new ideas land at once. If a topic has sub-skills, split across lessons.
2. **Explain with concrete first, abstract second.** Show a picture/model or a real-world example before introducing the rule or formula. For ELA, show a short example sentence before defining a grammar term.
3. **Worked example → guided practice → independent practice.** Every workbook page follows this arc. The student should never face blank independent problems without seeing at least one fully solved example.
4. **Reading load matters — use these concrete targets.**
   - **Grade 3:** short, simple sentences (5–10 words). Lots of white space. Avoid words above a Grade 3 reading level in instruction prose.
   - **Grade 4:** simple-to-moderate sentences (8–15 words). A short instructional paragraph is fine; never a wall of text.
   - **Grade 5:** moderate sentences (10–20 words). Can sustain a full short paragraph of explanation and a brief reading passage (~150–250 words) for ELA.
   - Across all grades: never write a wall of unbroken text as an "explanation." Break it up with the worked example, a line break, or a question.
5. **Vocabulary: teach Tier 2 words, define inline.** Target words worth teaching are *Tier 2* — useful across subjects (e.g., "summarize," "evidence," "equivalent," "represent"), not rare Tier 3 jargon. When a content word appears for the first time, define it inline in plain language. Don't assume a 9-year-old knows "numerator."
6. **Practice set sizing.** 5–8 independent problems is a full lesson's worth. More than 10 fatigues this age group. Mixed review ("spiral review") can add 2–3 older-concept problems at the end.
7. **Answer keys show the method, not just the number.** For math, show one line of work. For ELA, quote the relevant text. A parent or substitute teacher should be able to follow it.
8. **Differentiation is teach-up, not water-down.** All three tiers (Support / Core / Extension) aim at the *same grade-level objective* — you scaffold the grade-level task, you don't swap in lower-grade content. Support scaffolds **fade** across the set (2→1→0) so independence grows. Extension requires *new thinking*, not more-of-the-same. Full detail in `references/pedagogy.md`.
9. **Invisible scaffolds.** A Support-tier worksheet never tells the student it's the "easy version." No "(no organizer this time)," no remedial framing. The scaffolds are simply present. Equity requires this.

## Language and tone

- **Workbook voice (to the student):** warm, encouraging, second person ("Now try these!"). Short sentences. No condescension — a 10-year-old is not a toddler.
- **Lesson plan voice (to the teacher):** professional, concise, imperative ("Model…", "Have students…"). Use standard teacher vocabulary (objective, modeling, check for understanding, exit ticket).
- **Vocabulary control:** avoid words above a ~Grade 5 reading level in the student-facing text unless the word *is* the vocabulary being taught. When teaching a content word, define it inline the first time.

## Workflow per unit

1. **Plan.** Read the relevant concept reference. Write the 4-point Plan note (subject, grade, topic, scope) and confirm or proceed.
2. **Name the misconception.** Before drafting, decide: what's the one wrong-but-reasonable idea a student will form here? Write it down. It drives the exit ticket and the teacher's circulating questions. (See `references/pedagogy.md` if the topic isn't obvious.)
3. **Draft the lesson plan.** Use the Teacher Lesson Plan template from `references/templates.md`. Fill objectives, materials, pacing, the instructional arc, differentiation (three tiers — read `references/pedagogy.md`), anticipated responses, and an exit ticket that catches the misconception.
4. **Draft the workbook page.** Same topic. Worked example → guided practice → independent practice → spiral review. Age-appropriate reading load per rule 4.
5. **Draft the answer key.** Solutions with one line of method shown, for both guided and independent practice. Then **verify it**: actually work each math problem fresh against the key; for ELA, check every scoring criterion is satisfiable. Mismatched or un-checkable answers are a critical failure — fix before showing output.
6. **Export.** Hand off to the `docx` or `pdf` skill to produce the final file. Details in the next section.

## Exporting to PDF / DOCX

The user wants finished documents, so always plan to export. The choice of tool depends on the document:

- **Student workbook and lesson plan** (text + tables, needs editing) → use the **`docx`** skill. Good for printable worksheets with fill-in space.
- **Polished, print-ready workbook or full chapter** (precise layout, ready to print/share) → use the **`pdf`** skill (report workflow).
- **Both formats** → produce DOCX as the working master, then PDF for distribution.

Assemble order for a multi-lesson unit:
1. One title/cover section (unit title, grade, subject, "Table of Contents").
2. For each lesson: lesson plan first (teacher section), then the workbook page, then the answer key — OR keep teacher material and student material in separate sections if the user prefers. Ask once, then stay consistent.
3. Number pages and add a simple footer ("Grade X · [Subject] · Page N").

**Before exporting**, confirm with the user which format(s) they want for that unit. Don't silently produce only one.

## Formatting the student workbook page

Upper-elementary kids need space to work. In the document:

- Leave a blank line / box after each open-response math problem for work.
- For multiple choice, put options A–D on separate lines.
- Keep one concept's practice together on a page where possible; avoid orphaning the last 1–2 problems onto a new page.
- Use a clear visual hierarchy: **Lesson title → "Today you will learn…" → Worked Example (boxed) → Practice sections with bold headers.**

### Draw it: generate simple SVG diagrams (math, especially grades 3–4)

A picture beats a text placeholder, and this age band is still very visual. Where a model would aid understanding — **fractions** (bars, number lines), **bar / tape models** for word problems, **geometry** shapes, **area grids**, **multiplication arrays** — **generate a clean inline SVG diagram** instead of leaving blank space. The docx/pdf export tools will render it.

SVG rules:
- Use only basic shapes: `rect`, `line`, `circle`, `polygon`, `path`, `text`.
- One calm, kid-friendly accent fill (e.g. `#3B82F6` or `#F59E0B`), thin dark strokes (`#111`), white background.
- Label parts in the **student's language** (English or Vietnamese).
- Keep it small and focused — one model per diagram, large enough to read. Include a `viewBox` so it scales.
- Embed as a fenced ` ```svg ` block in the markdown; the export step places it.

Defaults to reach for:
- Fraction 3/4 → a bar split into 4, 3 parts shaded, `3/4` labeled.
- "2/5 of 15" → a tape diagram of 5 boxes, 2 grouped, `= 6`.
- Area of a 4×3 rectangle → a 4×3 grid with `Area = 12`.
- Right angle → two rays meeting, square angle mark.

If a correct SVG can't be produced reliably for a case, **fall back** to: (a) an image-generation prompt the user can run, or (b) a simple Unicode sketch (█ for shaded parts). **A wrong or garbled diagram is worse than none** — when unsure, omit the diagram and leave labeled work space instead.

## Quality checks before you call it done

Run through these mentally for every unit:

- [ ] Reading level matches the grade (rule 4)?
- [ ] One concept only (rule 1)? Worked example present (rule 3)?
- [ ] 5–8 independent problems, not 15 (rule 6)?
- [ ] Answer key shows method, not just final answers (rule 7) — **and you verified every answer by re-working it**?
- [ ] Lesson plan has all three tiers — Support / Core / Extension — all aimed at the *same* objective (rule 8)? Support fades 2→1→0? Extension passes the "new thinking" test?
- [ ] Exit ticket would catch a student holding the day's main misconception? (If that student would still pass, the exit ticket is too easy — swap it.)
- [ ] Any Support-tier worksheet is **invisible** to the student (no remedial labels, rule 9)?
- [ ] Export format agreed with user and file produced?

If any check fails, fix it before showing the result to the user. The exit-ticket check and the answer-key verification are the two that most often get skipped and most often embarrass — prioritize them.

## What NOT to do

- Don't produce college-style lectures in the student voice.
- Don't skip the worked example to save space — it's the most important part.
- Don't write answer keys that are just a bare list of numbers with no method.
- Don't dump two grades' worth of content into one lesson because "it's related."
- Don't rescue struggling students with lower-grade content — scaffold the grade-level task instead (that widens the gap).
- Don't label or format the Support tier as "easy" or "for kids who need help."
- Don't invent a standards code. If unsure, describe the cluster in plain language and offer to look it up.
- Don't export a file format the user didn't ask for, or forget to export at all.
