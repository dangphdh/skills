---
name: kids-illustrations
description: How to create illustrations and diagrams for children's educational content and storybooks — two tracks, inline SVG diagrams (fractions, bar models, geometry, arrays, simple scenes) and image-generation prompts for full-color pictures, with a bundled script (scripts/zai_image_gen.sh) that calls the Z.ai GLM-Image / CogView-4 API directly when a ZAI_API_KEY is available. Use whenever the user wants pictures, images, artwork, or visual aids for kids' materials — a workbook diagram, a storybook illustration, a cover, character art, or scene art — even if they don't say "illustration" (e.g., "make the worksheet prettier," "draw the fraction," "pictures for my story"). Bilingual English/Vietnamese labels supported.
---

# Kids Illustrations (SVG + Image Generation)

Two tracks, chosen by what the art is for:

| Track | Use when | Output |
|---|---|---|
| **A. Inline SVG** | Instructional diagrams — fraction bars, bar/tape models, number lines, geometry, arrays, area grids, simple labeled scenes | A fenced ` ```svg ` block that renders in markdown/PDF/DOCX and on the web |
| **B. Image-gen prompt** | Full-color artwork — storybook scenes, characters, covers, decorative art | A ready-to-paste prompt for the user's image tool |

**Default to Track A** when the picture must be *accurate* (a wrong diagram teaches the wrong thing). **Track B** when the picture must be *beautiful*. They combine: an SVG diagram inside a storybook page whose scene art comes from Track B.

## Track A — inline SVG

### When SVG is the right call

- Math models: fraction bars/number lines, tape diagrams, arrays, area grids, 10×10 decimal grids, angles and shapes
- Simple labeled scenes (a character at a market, a before/after pair)
- Anything that must render reliably in PDF/DOCX export with no external dependency

### SVG rules

1. **Basic shapes only:** `rect`, `line`, `circle`, `polygon`, `polyline`, `path`, `text`. No filters, no gradients, no external fonts, no scripts.
2. **One accent fill** per diagram — `#3B82F6` (blue) or `#F59E0B` (amber) — with thin dark strokes (`#111827`, stroke-width 1–2) on a white background. A calm palette keeps attention on the math.
3. **Labels in the student's language** (English or Vietnamese). Font-family `sans-serif`; font-size ≥ 14 in a viewBox of ~400–600 wide so text stays readable when scaled.
4. **One model per diagram.** Two models = two SVGs.
5. **Always include `viewBox`** so it scales. Keep width/height proportional.
6. **Test the math IN the coordinates**: 3/4 shaded means 3 of 4 equal rects; a 4×3 array means 12 cells; 90° must look like 90°. Coordinate errors are content errors.
7. Add `role="img"` and `<title>` for accessibility.

### Recipes (steal these)

- **Fraction bar 3/4:** one `rect` outline split by 3 `line`s into 4 equal cells; fill 3 cells; label `3/4`.
- **Number line 0–1 in fourths:** horizontal `line`, ticks every 1/4, labels `0, 1/4, 2/4, 3/4, 1`; a dot on `3/4`.
- **Tape model "2/5 of 15":** a bar of 5 equal cells, a bracket/arc over 2 cells labeled `? = 6`, whole labeled `15`.
- **Array 4×3:** 4 columns × 3 rows of small rects (12 total), optional grouping arcs.
- **Right angle:** two `line`s meeting + small `rect` (3×3) at the vertex as the angle mark.
- **10×10 decimal grid:** 100 small squares; shade exactly the count needed (27 squares for 0.27).

### Embedding

Fenced block in markdown:

````markdown
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 120" role="img">
  <title>Fraction bar showing three quarters</title>
  ...
</svg>
```
````

The `docx`/`pdf` export tools render it. If the export target can't render SVG, rasterize once (any converter) and embed the PNG.

## Track B — image-generation prompts

### Anatomy of a good kids' image prompt

Read `references/prompts.md` for the full recipe and ready-made templates. The short version — every prompt states:

1. **Medium & style** — children's picture-book illustration, flat vector style, soft watercolor…
2. **Subject & action** — who, doing what, one clear action
3. **Setting & light** — where, when, mood
4. **Composition** — close-up / wide, focal point, negative space for text
5. **Palette** — 2–4 named colors, warm and calm for young kids
6. **Constraints** — no text in image (AI text renders garbled); aspect ratio matched to use (square for scenes, 3:4 portrait for pages, 2:1 for banners)

### The no-text rule

AI image models render text badly. **Never ask for words in the image.** Add labels afterward in the document (SVG overlay or the layout tool). The one exception: single large letters/numerals for letter-recognition cards — and even then, expect retries.

### Consistency across a series (characters, covers)

For a storybook with the same character on every page, the prompt must pin the character with a **fixed descriptor block** repeated verbatim in every prompt, plus scene changes. See `references/prompts.md` → "Character sheet pattern." Expect to regenerate and pick; consistency is approximate, never guaranteed.

### Handing off

Deliver prompts as a copy-paste block per image, numbered to match pages/spreads. If the user's environment has an image tool available, use it directly; otherwise the prompts are the deliverable.

### Generating directly via the Z.ai scripts

When real images (not just prompts) are wanted, this skill ships two generators that share one `.env`:

- **`scripts/zai_image_gen.sh`** — the simple path (single image or batch from a prompts file).
- **`scripts/zai_image_gen.py`** — the dynamic edition (Python 3): parallel batch, retry with backoff, content-filter reporting, a `manifest.json` of results, character-sheet prompt injection, and Pillow text/SVG overlay onto images. Same flags as the bash edition, plus more.

**API key** — read in this order: the `ZAI_API_KEY` environment variable, then `.env` in the skill folder (see `.env.example`), then `.env` next to the script, then `./.env`. The user keeps the key in `.env`; **never commit, copy, or paste `.env` contents anywhere** — it is a secret.

```bash
# simple path (bash)
bash scripts/zai_image_gen.sh "<full prompt>" -o cover.png -s 1056x1568
bash scripts/zai_image_gen.sh -f prompts.md -o images/          # every bare ``` block = 1 image

# dynamic path (python)
python scripts/zai_image_gen.py "<prompt>" --aspect 3:4 -o page.png
python scripts/zai_image_gen.py -f prompts.md -o images/ --parallel 4        # batch song song + manifest.json
python scripts/zai_image_gen.py --character mai.yaml -f scenes.md            # frozen character block injected into every scene
python scripts/zai_image_gen.py -i page.png --text "Trang 1"                 # overlay text (Pillow, TTF, tiếng Việt OK)
python scripts/zai_image_gen.py -i page.png --svg diagram.svg                # composite an SVG (needs cairosvg; degrades gracefully)
```

A character sheet (`mai.yaml`) is flat: `name / block / style / palette`. The `block` is injected verbatim into every scene prompt — that is the consistency mechanism from `references/prompts.md`, automated.

The **overlay** solves the no-text rule end-to-end: generate clean art, then stamp titles/page numbers/labels with `--text` (or `--text-file`), position `--text-pos top|center|bottom`.

Aspect-ratio → size mapping (`glm-image`): 1:1 → `1280x1280`, 3:4 portrait page → `1056x1568`, 4:3 landscape → `1568x1056`, 2:1 banner → `1728x960`, tall phone-page → `960x1728` — or just pass `--aspect 3:4`. Use `-q standard` for faster drafts, default `hd` for finals.

Workflow for the model:
1. Check `ZAI_API_KEY` is set (`[[ -n "${ZAI_API_KEY:-}" ]]`). If not, tell the user how to set it and deliver prompts as the fallback — don't fail silently.
2. Show the user the prompts first (they may want edits before spending generations).
3. Run the script (bash for one-offs; python for batches ≥3, character series, or overlays). `--dry-run` previews the exact requests.
4. The API URL expires in 30 days — both scripts download to a local file; reference the file, not the URL.

Costs apply per generation — batch only on request.

## Vietnam / Vietnamese context

- SVG labels in tiếng Việt with proper diacritics — check them character by character; diacritics are content.
- Track B: name the aesthetic when wanted — Vietnamese folk-art palette (indigo, ochre), áo dài, non lá, Tết scenes — but as descriptors in the prompt, letting the model interpret, not as cultural caricature.
- Currency, food, and settings follow the story's locale (see `kids-storytelling` for narrative consistency).

## Quality checks

- [ ] Track chosen for the right reason (accuracy → SVG; beauty → image-gen)?
- [ ] SVG: math verified in coordinates; one model; viewBox present; labels in the student's language; diacritics correct?
- [ ] Image prompt: all 6 anatomy parts present; **no text requested in image**; aspect ratio matches use?
- [ ] Series: character descriptor block repeated verbatim?
- [ ] Export path known (renders in target format / prompts delivered as blocks)?
