#!/usr/bin/env python3
"""zai_image_gen.py — Z.ai image generation (GLM-Image / CogView-4), dynamic edition.

Python companion to zai_image_gen.sh (which stays the simple path). Adds:
parallel batch, retry with backoff, content-filter reporting, a JSON manifest,
character-sheet prompt injection, and Pillow text/SVG overlay onto images.

Usage:
  zai_image_gen.py "prompt" [-o out.png] [-m MODEL] [-s SIZE | --aspect 3:4]
  zai_image_gen.py -f prompts.md [-o outdir/] [--parallel 4] [--retries 2]
  zai_image_gen.py --character mai.yaml -f scenes.md      # frozen block injected
  zai_image_gen.py -i page1.png --text "Trang 1"          # overlay on existing
  ... plus --text/--text-file/--text-pos/--svg on any generate/overlay run
  zai_image_gen.py "prompt" --dry-run                     # print requests only

API key (same rules as the bash edition): ZAI_API_KEY env var, then .env in
the skill folder (this script's parent directory), then .env next to the
script, then ./.env. Never commit .env.

Stdlib-only for the API path (urllib). Pillow is optional (overlay);
PyYAML optional (character files fall back to a flat "key: value" parser).
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import textwrap
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ENDPOINT = "https://api.z.ai/api/paas/v4/images/generations"

SIZES = {
    "glm-image": ["1280x1280", "1568x1056", "1056x1568", "1472x1088",
                  "1088x1472", "1728x960", "960x1728"],
    "cogview-4-250304": ["1024x1024", "768x1344", "864x1152", "1344x768",
                         "1152x864", "1440x720", "720x1440"],
}

ASPECT_TO_SIZE = {
    "glm-image":        {"1:1": "1280x1280", "3:4": "1056x1568",
                         "4:3": "1568x1056", "2:1": "1728x960",
                         "9:16": "960x1728"},
    "cogview-4-250304": {"1:1": "1024x1024", "3:4": "768x1344",
                         "4:3": "1344x768", "2:1": "1440x720",
                         "9:16": "720x1440"},
}

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


# ─── API key / .env ───────────────────────────────────────────────────────

_ENV_LINE = re.compile(r'^\s*(?:export\s+)?ZAI_API_KEY\s*=\s*(.*)$')


def _clean_env_value(raw: str) -> str:
    val = raw.strip().rstrip("\r").strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
        val = val[1:-1]
    return val.strip()


def load_api_key() -> str | None:
    env = os.environ.get("ZAI_API_KEY", "").strip()
    if env:
        return env
    here = Path(__file__).resolve().parent
    for candidate in (here.parent / ".env", here / ".env", Path.cwd() / ".env"):
        try:
            for line in candidate.read_text(encoding="utf-8-sig").splitlines():
                m = _ENV_LINE.match(line)
                if m:
                    val = _clean_env_value(m.group(1))
                    if val:
                        return val
        except OSError:
            continue
    return None


# ─── prompt extraction & composition ──────────────────────────────────────

def extract_prompts(md_text: str) -> list[str]:
    """One prompt per bare ``` fence; tagged fences (```svg, ```python…) skipped."""
    prompts: list[str] = []
    buf: list[str] = []
    infence = collecting = False
    for line in md_text.splitlines():
        if line.lstrip().startswith("```"):
            tag = line.strip()[3:].strip()
            if not infence:
                infence, collecting, buf = True, tag == "", []
            else:
                was_collecting = collecting
                infence = collecting = False
                text = "\n".join(buf).strip()
                if was_collecting and text:
                    prompts.append(text)
                buf = []
            continue
        if collecting:
            buf.append(line)
    return prompts


def load_character(path: Path) -> dict:
    """Flat character sheet: name / block / style / palette (+ free extras)."""
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
        return {k: str(v).strip() for k, v in data.items()} if data else {}
    except ImportError:
        pass
    sheet: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        sheet[key.strip()] = val.strip()
    return sheet


def compose_prompt(scene: str, ch: dict) -> str:
    parts = [ch.get("style"), ch.get("block"), scene.strip()]
    prompt = ". ".join(p.strip().rstrip(".") for p in parts if p and p.strip())
    if ch.get("palette"):
        prompt += f". Palette: {ch['palette']}"
    return prompt + ". No text, no letters, no words in the image."


# ─── API call ─────────────────────────────────────────────────────────────

class ApiError(RuntimeError):
    pass


def build_body(prompt: str, model: str, size: str, quality: str) -> str:
    return json.dumps(
        {"model": model, "prompt": prompt, "size": size, "quality": quality},
        ensure_ascii=False, separators=(",", ":"),
    )


def api_generate(prompt: str, model: str, size: str, quality: str,
                 key: str, retries: int = 2, timeout: int = 180) -> dict:
    body = build_body(prompt, model, size, quality).encode("utf-8")
    last_err = ""
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            ENDPOINT, data=body, method="POST",
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            url = (data.get("data") or [{}])[0].get("url")
            if not url:
                raise ApiError(f"no image URL in response: "
                               f"{json.dumps(data)[:300]}")
            cf = data.get("content_filter") or []
            return {"url": url,
                    "filter_level": cf[0].get("level") if cf else None}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", "replace")[:300]
            last_err = f"HTTP {e.code}: {err_body}"
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(3 * (2 ** attempt))
                continue
            raise ApiError(last_err) from None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = f"network/parse error: {e}"
            if attempt < retries:
                time.sleep(3 * (2 ** attempt))
                continue
            raise ApiError(last_err) from None
    raise ApiError(last_err or "unreachable")


def download(url: str, dest: Path, timeout: int = 300) -> Path:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        dest.write_bytes(resp.read())
    return dest


# ─── overlay (Pillow, optional) ───────────────────────────────────────────

def _save(img, path: Path) -> None:
    if path.suffix.lower() in (".jpg", ".jpeg"):
        img.convert("RGB").save(path, quality=92)
    else:
        img.save(path)


def overlay_text(path: Path, text: str, pos: str = "bottom",
                 size: int | None = None, margin: int = 40) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("WARNING: Pillow not installed — skipping text overlay "
              "(pip install pillow)", file=sys.stderr)
        return
    img = Image.open(path).convert("RGBA")
    if not size:
        size = max(24, img.width // 24)
    font = None
    for cand in FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(cand, size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    max_chars = max(16, int(img.width / (size * 0.55)))
    lines: list[str] = []
    for para in text.splitlines():
        lines.extend(textwrap.wrap(para, max_chars) or [""])
    label = "\n".join(lines)

    draw = ImageDraw.Draw(img)
    sw = max(2, size // 14)
    x0, y0, x1, y1 = draw.textbbox((0, 0), label, font=font, stroke_width=sw)
    tw, th = x1 - x0, y1 - y0
    x = (img.width - tw) // 2 - x0
    if pos == "top":
        y = margin - y0
    elif pos == "center":
        y = (img.height - th) // 2 - y0
    else:  # bottom
        y = img.height - th - margin - y0
    draw.text((x, y), label, font=font, fill="white",
              stroke_width=sw, stroke_fill="black")
    _save(img, path)


def composite_svg(path: Path, svg: Path, pos: str = "bottom-right",
                  scale: float = 0.35, margin: int = 40) -> None:
    try:
        import cairosvg  # type: ignore
        from PIL import Image
    except ImportError:
        print("WARNING: cairosvg/Pillow not installed — skipping SVG overlay "
              "(pip install cairosvg pillow)", file=sys.stderr)
        return
    img = Image.open(path).convert("RGBA")
    target_w = int(img.width * scale)
    png = cairosvg.svg2png(url=str(svg), output_width=target_w)
    layer = Image.open(io.BytesIO(png)).convert("RGBA")
    x = img.width - layer.width - margin if "right" in pos else margin
    y = img.height - layer.height - margin if "bottom" in pos else margin
    img.alpha_composite(layer, (x, y))
    _save(img, path)


# ─── main ─────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    p = argparse.ArgumentParser(
        prog="zai_image_gen.py",
        description="Z.ai image generation (GLM-Image / CogView-4) — dynamic edition.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1].split("API key")[0] if __doc__ else None,
    )
    p.add_argument("prompt", nargs="?", help="single prompt (or omit with -f)")
    p.add_argument("-f", "--file", help="markdown file: one prompt per bare ``` fence")
    p.add_argument("-o", "--output", help="output file (single) or directory (batch)")
    p.add_argument("-m", "--model", default="glm-image", choices=list(SIZES))
    p.add_argument("-s", "--size", default=None, help="e.g. 1280x1280")
    p.add_argument("--aspect", default=None, choices=["1:1", "3:4", "4:3", "2:1", "9:16"],
                   help="convenience: pick a size from the aspect ratio")
    p.add_argument("-q", "--quality", default="hd", choices=["hd", "standard"])
    p.add_argument("--parallel", type=int, default=1, help="batch concurrency (default 1)")
    p.add_argument("--retries", type=int, default=2)
    p.add_argument("--character", type=Path, help="character sheet (.yaml) for prompt injection")
    p.add_argument("--dry-run", action="store_true")
    # overlay options (work in generate mode and with -i)
    p.add_argument("-i", "--input", type=Path, help="overlay mode: edit this existing image")
    p.add_argument("--text", help="text to overlay")
    p.add_argument("--text-file", type=Path, help="file with text to overlay (.txt)")
    p.add_argument("--text-pos", default="bottom", choices=["top", "center", "bottom"])
    p.add_argument("--text-size", type=int, default=None)
    p.add_argument("--margin", type=int, default=40)
    p.add_argument("--svg", type=Path, help="SVG file to composite onto the image")
    p.add_argument("--svg-pos", default="bottom-right",
                   choices=["top-left", "top-right", "bottom-left", "bottom-right"])
    p.add_argument("--svg-scale", type=float, default=0.35)
    args = p.parse_args(argv)

    # resolve size
    size = args.size or (
        ASPECT_TO_SIZE[args.model][args.aspect] if args.aspect
        else ("1280x1280" if args.model == "glm-image" else "1024x1024"))
    if size not in SIZES[args.model]:
        print(f"WARNING: size {size} not in documented sizes for {args.model}; "
              "sending anyway (API may reject it).", file=sys.stderr)

    # overlay-only mode (-i): no API call
    if args.input:
        if not (args.text or args.text_file or args.svg):
            p.error("-i needs --text / --text-file / --svg")
        text = args.text
        if args.text_file:
            text = args.text_file.read_text(encoding="utf-8-sig").strip()
        if text:
            overlay_text(args.input, text, args.text_pos, args.text_size, args.margin)
        if args.svg:
            composite_svg(args.input, args.svg, args.svg_pos, args.svg_scale)
        print(f"overlay done: {args.input}")
        return 0

    # gather prompts
    prompts: list[str] = []
    if args.file:
        md = Path(args.file).read_text(encoding="utf-8-sig")
        prompts = extract_prompts(md)
        if not prompts:
            print(f"ERROR: no bare-fenced prompt blocks in {args.file}", file=sys.stderr)
            return 1
    elif args.prompt:
        prompts = [args.prompt]
    else:
        p.error("need a prompt, or -f FILE (or -i for overlay-only mode)")

    if args.character:
        ch = load_character(args.character)
        if not ch.get("block"):
            print(f"ERROR: {args.character} has no 'block:' field", file=sys.stderr)
            return 1
        prompts = [compose_prompt(s, ch) for s in prompts]

    # dry-run
    if args.dry_run:
        for i, pr in enumerate(prompts, 1):
            out = (Path(args.output) / f"image-{i:03d}.png" if args.file
                   else Path(args.output or "image.png"))
            print(f"[dry-run {i}/{len(prompts)}] POST {ENDPOINT}")
            print(f"[dry-run {i}/{len(prompts)}] body: {build_body(pr, args.model, size, args.quality)}")
            print(f"[dry-run {i}/{len(prompts)}] output: {out}")
            if args.text or args.text_file:
                print(f"[dry-run {i}/{len(prompts)}] overlay text ({args.text_pos})")
            if args.svg:
                print(f"[dry-run {i}/{len(prompts)}] composite svg: {args.svg} ({args.svg_pos})")
        print(f"[dry-run] {len(prompts)} request(s) planned, parallel={min(args.parallel, 8)}")
        return 0

    key = load_api_key()
    if not key:
        print("ERROR: ZAI_API_KEY is not set.", file=sys.stderr)
        print("  Option 1: put it in .env in the skill folder (see .env.example)",
              file=sys.stderr)
        print("  Option 2: export ZAI_API_KEY=...", file=sys.stderr)
        print("  Get a key at https://z.ai", file=sys.stderr)
        return 1

    def overlay_if_requested(path: Path) -> None:
        if args.text or args.text_file:
            text = args.text or args.text_file.read_text(encoding="utf-8-sig").strip()
            overlay_text(path, text, args.text_pos, args.text_size, args.margin)
        if args.svg:
            composite_svg(path, args.svg, args.svg_pos, args.svg_scale)

    # single image
    if len(prompts) == 1 and not args.file:
        out = Path(args.output or "image.png")
        res = api_generate(prompts[0], args.model, size, args.quality,
                           key, args.retries)
        download(res["url"], out)
        overlay_if_requested(out)
        print(f"saved: {out}")
        print(f"  (API source URL, valid 30 days: {res['url']})")
        if res["filter_level"] is not None and res["filter_level"] <= 1:
            print(f"  NOTE: content_filter level {res['filter_level']} "
                  "(0–1 = strong filter hit) — review the image.", file=sys.stderr)
        return 0

    # batch
    outdir = Path(args.output or "images")
    outdir.mkdir(parents=True, exist_ok=True)
    workers = max(1, min(args.parallel, 8, len(prompts)))
    manifest = {"model": args.model, "size": size, "images": [], "errors": []}

    def job(i: int, pr: str):
        res = api_generate(pr, args.model, size, args.quality, key, args.retries)
        dest = outdir / f"image-{i:03d}.png"
        download(res["url"], dest)
        return i, pr, dest, res

    if workers == 1:
        results = [job(i, pr) for i, pr in enumerate(prompts, 1)]
    else:
        results = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(job, i, pr): i
                    for i, pr in enumerate(prompts, 1)}
            for fut in as_completed(futs):
                results.append(fut.result())

    failed = 0
    for i, pr, dest, res in sorted(results):
        manifest["images"].append(
            {"file": str(dest), "url": res["url"],
             "filter_level": res["filter_level"], "prompt": pr})
        print(f"saved: {dest}")
        if res["filter_level"] is not None and res["filter_level"] <= 1:
            print(f"  NOTE: image {i} content_filter level "
                  f"{res['filter_level']} — review it.", file=sys.stderr)

    # overlay after generation so batch text can vary per index later
    for _, _, dest, _ in results:
        overlay_if_requested(dest)

    (outdir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if failed:
        print(f"done with {failed} failure(s); see {outdir}/manifest.json",
              file=sys.stderr)
        return 1
    print(f"generated {len(results)} image(s) into {outdir}/ "
          f"(manifest: {outdir}/manifest.json)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ApiError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
