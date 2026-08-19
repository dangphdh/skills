#!/usr/bin/env bash
# zai_image_gen.sh — generate images via the Z.ai API (GLM-Image / CogView-4).
#
# Requires ZAI_API_KEY in the environment (get one at https://z.ai).
#
# Usage:
#   zai_image_gen.sh "prompt text" [-o out.png] [-s SIZE] [-m MODEL] [-q QUALITY]
#   zai_image_gen.sh -f prompts.md [-o outdir/]     # batch: one prompt per bare ``` block
#   zai_image_gen.sh "prompt text" --dry-run        # print request, don't call the API
#
# Models:  glm-image (default) | cogview-4-250304
# Sizes (glm-image):        1280x1280 1568x1056 1056x1568 1472x1088 1088x1472 1728x960 960x1728
# Sizes (cogview-4-250304): 1024x1024 768x1344 864x1152 1344x768 1152x864 1440x720 720x1440
# Quality (glm-image):      hd (default, ~20s) | standard (~5-10s)
#
# The API returns a temporary URL (expires in 30 days); this script downloads
# the image locally immediately, so the file is permanent.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# API key precedence: real environment > .env in the skill folder (script's
# parent) > .env next to the script > ./.env
# The .env loader parses (doesn't source) the file, so arbitrary shell in it
# never executes, and Windows CRLF line endings are handled.
load_env_file() {
  local f="$1" val
  [[ -f "$f" ]] || return 1
  val="$(sed -n 's/^[[:space:]]*\(export[[:space:]]\{1,\}\)\{0,1\}ZAI_API_KEY=//p' "$f" | tail -n1)"
  val="${val%%$'\r'}"
  val="${val%\"}"; val="${val#\"}"
  val="${val%\'}"; val="${val#\'}"
  [[ -n "$val" ]] && ZAI_API_KEY="$val"
}
if [[ -z "${ZAI_API_KEY:-}" ]]; then
  load_env_file "$SCRIPT_DIR/../.env" \
    || load_env_file "$SCRIPT_DIR/.env" \
    || load_env_file "./.env" \
    || true
fi

ENDPOINT="https://api.z.ai/api/paas/v4/images/generations"
MODEL="glm-image"
SIZE="1280x1280"
QUALITY="hd"
OUT=""
BATCHFILE=""
DRYRUN=0
PROMPT=""

usage() {
  cat <<'EOF'
Usage:
  zai_image_gen.sh "prompt text" [-o out.png] [-s SIZE] [-m MODEL] [-q QUALITY]
  zai_image_gen.sh -f prompts.md [-o outdir/]     # batch: one prompt per bare ``` block
  zai_image_gen.sh "prompt text" --dry-run

Env: ZAI_API_KEY  (required for real calls)
EOF
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o) OUT="$2"; shift 2 ;;
    -s) SIZE="$2"; shift 2 ;;
    -m) MODEL="$2"; shift 2 ;;
    -q) QUALITY="$2"; shift 2 ;;
    -f) BATCHFILE="$2"; shift 2 ;;
    --dry-run) DRYRUN=1; shift ;;
    -h|--help) usage 0 ;;
    -*) echo "unknown flag: $1" >&2; usage 1 ;;
    *) PROMPT="$1"; shift ;;
  esac
done

# Escape a string for embedding in JSON: backslash, quote; collapse whitespace.
json_escape() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | tr '\n\r\t' '   '
}

build_body() {
  printf '{"model":"%s","prompt":"%s","size":"%s","quality":"%s"}' \
    "$MODEL" "$(json_escape "$1")" "$SIZE" "$QUALITY"
}

# generate_one <prompt> <output-file>
generate_one() {
  local body resp url
  body="$(build_body "$1")"

  if [[ $DRYRUN -eq 1 ]]; then
    echo "[dry-run] POST $ENDPOINT"
    echo "[dry-run] Authorization: Bearer \$ZAI_API_KEY"
    echo "[dry-run] body: $body"
    echo "[dry-run] output: $2"
    return 0
  fi

  if [[ -z "${ZAI_API_KEY:-}" ]]; then
    echo "ERROR: ZAI_API_KEY is not set." >&2
    echo "  Option 1: put it in .env next to this script (see .env.example)" >&2
    echo "  Option 2: export ZAI_API_KEY=..." >&2
    echo "  Get a key at https://z.ai" >&2
    exit 1
  fi

  resp="$(curl -sS -X POST "$ENDPOINT" \
    -H "Authorization: Bearer $ZAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$body")"

  if command -v jq >/dev/null 2>&1; then
    url="$(printf '%s' "$resp" | jq -r '.data[0].url // empty')"
  else
    url="$(printf '%s' "$resp" | sed -n 's/.*"url"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
  fi

  if [[ -z "$url" ]]; then
    echo "ERROR: no image URL in API response (first 500 chars):" >&2
    printf '%s' "$resp" | head -c 500 >&2
    echo >&2
    exit 1
  fi

  curl -sSL -o "$2" "$url"
  echo "saved: $2"
  echo "  (API source URL, valid 30 days: $url)"
}

if [[ -n "$BATCHFILE" ]]; then
  [[ -f "$BATCHFILE" ]] || { echo "no such file: $BATCHFILE" >&2; exit 1; }
  OUTDIR="${OUT:-images}"
  mkdir -p "$OUTDIR"
  TMPD="$(mktemp -d)"
  trap 'rm -rf "$TMPD"' EXIT

  # Collect bare-fenced blocks (plain ```), skipping tagged fences like ```svg.
  awk -v d="$TMPD/" '
    /^```/ {
      if (!infence) {
        infence = 1
        tag = $0; sub(/^```/, "", tag); gsub(/[[:space:]]/, "", tag)
        if (tag == "") { n++; fn = sprintf("%s%03d", d, n); collecting = 1 } else { collecting = 0 }
      } else { infence = 0; collecting = 0 }
      next
    }
    collecting { print > fn }
  ' "$BATCHFILE"

  shopt -s nullglob
  files=("$TMPD"/*)
  [[ ${#files[@]} -gt 0 ]] || { echo "no fenced prompt blocks found in $BATCHFILE" >&2; exit 1; }

  i=0
  for f in "${files[@]}"; do
    i=$((i + 1))
    p="$(cat "$f")"
    [[ -z "${p// /}" ]] && continue
    printf -v out "%s/image-%03d.png" "$OUTDIR" "$i"
    generate_one "$p" "$out"
  done
  echo "generated $i image(s) into $OUTDIR/"
else
  [[ -n "$PROMPT" ]] || { echo "need a prompt (or -f FILE for batch mode)" >&2; usage 1; }
  generate_one "$PROMPT" "${OUT:-image.png}"
fi
