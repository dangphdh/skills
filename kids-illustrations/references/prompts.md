# Image-Generation Prompt Recipes

Ready-to-adapt templates for kids' educational artwork. Fill the `{braces}`; keep the fixed parts verbatim within a series.

## The 6-part anatomy (every prompt has all six)

1. **Medium & style** — the single strongest lever; decide once per project
2. **Subject & action** — one clear action, nameable in a sentence
3. **Setting & light** — where, when, mood
4. **Composition** — framing, focal point, negative space for text
5. **Palette** — 2–4 named colors
6. **Constraints** — no text; aspect ratio

## Style menu (pick one, stay consistent per project)

| Style | Prompt phrase | Good for |
|---|---|---|
| Flat vector | "flat vector children's book illustration, clean shapes, bold outlines" | Workbooks, diagrams-adjacent art, youngest ages |
| Soft watercolor | "soft watercolor children's illustration, gentle textures" | Bedtime stories, gentle narratives |
| Crayon / paper | "children's crayon and paper-cut collage illustration" | Playful early-reader material |
| Anime-lite | "gentle anime-inspired children's illustration, rounded features" | Ages 8–11 adventure |
| Folk (Vietnam) | "Vietnamese folk-art inspired illustration, indigo and ochre palette" | Truyện cổ tích, cultural stories |

## Base template

```
{style}, {subject doing one action}, {setting, time of day, mood}.
{composition — e.g., "wide shot, character center-left, generous
negative space at top for title"}. Palette: {2–4 colors}.
No text, no letters, no words in the image. {aspect ratio}.
```

## Worked examples

**Storybook scene (age 6–8):**
```
Soft watercolor children's illustration: a small girl in a red raincoat
chasing a paper boat along a rain-glossed village street, joyful mood,
overcast morning light. Wide shot, girl center-left, generous sky space
at top. Palette: muted blue, warm red, cream. No text in the image.
Aspect ratio 3:4, portrait picture-book page.
```

**Math workbook mascot (flat vector):**
```
Flat vector children's illustration: a friendly round owl holding a
pencil, waving one wing, cheerful. Centered bust shot, plain background,
space around the figure. Palette: teal, amber, off-white. No text in
the image. Square 1:1.
```

**Vietnamese folk-tale scene:**
```
Vietnamese folk-art inspired children's illustration: a brave young
boy in a conical hat crossing a bamboo bridge over a river, mountains
in morning mist, determined mood. Wide establishing shot, small figure
in a big landscape. Palette: indigo, ochre, jade green. No text in the
image. Aspect ratio 3:4.
```

## Character sheet pattern (series consistency)

Define once, repeat verbatim in every prompt:

```
CHARACTER BLOCK — "Mai: 8-year-old Vietnamese girl, chin-length black
hair with a yellow hairpin, red raincoat, yellow rain boots, freckles,
cheerful and curious expression"
```

Then every scene prompt starts: `{style}. {CHARACTER BLOCK verbatim}. In this scene, {new action/setting}…`

Rules:
- The block is **frozen** — same wording, same order, every time.
- Keep the block short (one line of core visual identity). Long blocks dilute.
- Expect approximate consistency. To improve odds: same style phrase, same palette, same "camera" tendencies across scenes.
- If a character must appear small in a wide shot, add "Mai is recognizable by her red raincoat and yellow hairpin."

## Aspect ratios by use

| Use | Ratio |
|---|---|
| Picture-book page | 3:4 portrait |
| Spread | 16:9 or 2:1 |
| Cover | 2:3 portrait, focal center, title space top |
| Workbook mascot / card | 1:1 square |
| Banner / header | 2:1 or 3:1 |

## Negative-space planning for text overlay

If the layout will put text on the image, say so in the prompt: "generous negative space at {top/bottom/left}" — then place text there in the document tool. Never ask the model to render the text itself.

## Common failure modes

| Failure | Fix |
|---|---|
| Garbled letters in image | You asked for text — remove all text requests |
| Character drifts across pages | Freeze and repeat the character block verbatim |
| Busy, cluttered scene | Name ONE action; move extras to setting |
| Style drift across a series | Repeat the exact style phrase every prompt |
| Unusable crop | State aspect ratio and composition explicitly |
| Creepy/uncanny kids | Prefer flat vector or watercolor styles; "rounded friendly features" |
| Cultural caricature | Describe specific visual elements (áo dài, non lá) rather than ethnic labels; keep mood respectful |

## Delivery format

Number prompts to match the pages/spreads they belong to, one fenced block each — **bare ``` fences only** (` ```svg ` blocks are ignored by the generator):

```
Page 1 (cover):
{prompt}

Page 2–3 (spread — Mai meets the problem):
{prompt}
```

Offer both the numbered list and, if the user's tool supports it, direct generation.

If `ZAI_API_KEY` is set, generate directly instead of handing off:

```bash
bash scripts/zai_image_gen.sh -f prompts.md -o images/   # one image per bare fence
python scripts/zai_image_gen.py -f prompts.md -o images/ --parallel 4      # + manifest.json
python scripts/zai_image_gen.py --character mai.yaml -f scenes.md           # frozen block injected
python scripts/zai_image_gen.py -i cover.png --text "Trang 1"               # overlay text afterwards
```

See the "Generating directly via the Z.ai scripts" section in SKILL.md for the size mapping and workflow.
