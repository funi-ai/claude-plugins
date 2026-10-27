#!/usr/bin/env python3
"""explainer.py - block ledger and planner for narrated explainer videos. Python 3.8+, stdlib only.

One explainer = N blocks; one block = one narration chunk + one visual. State lives in
.genmedia/projects/<slug>/blocks.json. Reads the gm.py ledger (.genmedia/runs.jsonl; never writes it).
Never calls fal, never reads the API key, never spends money. `render` runs local ffmpeg only.
Prints ONE compact JSON object on stdout. Exit: 0 ok | 1 gate, not ready or failed | 2 usage.

  init      --slug S --script <file|-> [--title T] [--lang en] [--minutes M | --blocks N] [--block-s 10]
            [--length-s MAX | MIN-MAX] [--wps X] [--lead-s 0.4] [--tail-s 0.6] [--aspect 16:9]
            [--tier animatic|hybrid|full] [--fit audio|grid] [--split auto|paragraph|sentence] [--force]
            Script text -> blocks, sized with a words-per-second heuristic per language. --length-s is the
            length the user asked for: the estimate must leave headroom under MAX before the outline can be
            approved, and the measured total must fit before the narration is approved or keyframes are planned.
  edit      --slug S --block N --narration-file <file|->      change one block's text (resets its audio)
  style     --slug S [--name N] [--style-file <file|->] [--negative-file <file|->] [--key-job ID]
            [--key-path P] [--key-url U] [--ref-url U ...]    STYLE string + approved style-key image
  visuals   --slug S --input <file|->    [{"index":1,"scene":"..","motion":"..","move":"in","animate":true}]
  attach    --slug S --block N --kind audio|keyframe|clip --path P [--url U]   a file made elsewhere
  approve   --slug S --stage outline|style|voice|narration|keyframes|clips [--blocks 3,7] [--note T]
            [--tier animatic|hybrid|full]   (outline only: the tier the user chose on the outline card)
            [--voice NAME]                  (voice only: the voice the user picked at CP2)
  set-audio --slug S (--probe <audiokit probe json|-> | --batch-result <gm.py batch json|->
            | --block N --duration SEC [--path P] [--url U])   record MEASURED narration durations
  plan      --slug S --stage stylekey|audition|narration|probe|keyframes|clips [--endpoint ID]
            [--blocks 3,7] [--reroll] [--base-input file.json] [--out plan.json] [--max-parallel N]
            [--text-field F] [--voice-field voice] [--voices a,b] [--text-file F] [--prompt-file F]
            [--refs-field image_urls] [--size-field F] [--allow-text] [--image-field F] [--duration-field duration]
            [--duration-type int|str] [--min-s N] [--max-s N]
            [--price-per-1k USD | --price-per-image USD | --price-per-second USD]
            Writes a `gm.py batch` plan; the STYLE string is pasted verbatim into every visual prompt.
            Gates: outline approval before any paid stage; the CP2 voice approval before narration, and
            the base input must carry that voice; measured + approved narration before keyframes
            (audio-before-video barrier); approved keyframes before clips.
  timeline  --slug S [--srt PATH] [--concat PATH] [--max-chars 42] [--max-lines 2]
            block timings -> SRT, ffmpeg concat list (--compose is refused: see COMPOSE_REFUSAL)
  render    --slug S [--blocks 3,7] [--final] [--size WxH] [--fps 30] [--music PATH] [--music-volume 0.25]
            [--no-duck] [--lufs -16] [--force]   local ffmpeg: per-block segments, then the final file
  status    --slug S                             per-block table, quantities for pricing, next step

Job ids: n07 narration, kf07 keyframe, clip07 clip, p-n07 probe, stylekey, aud-<voice>; a redo gets -r2, -r3.
Env: EXPLAINER_FFMPEG (binary override, used by the tests).
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata

VERSION = 1
LEDGER = os.path.join(".genmedia", "runs.jsonl")
PROJECTS = os.path.join(".genmedia", "projects")
OUTPUT = "genmedia-output"
STATE = "blocks.json"
KINDS = ("audio", "keyframe", "clip")
KIND_PREFIX = {"audio": "n", "keyframe": "kf", "clip": "clip"}
KIND_FOLDER = {"audio": "narration", "keyframe": "keyframes", "clip": "clips"}
STAGES = ("stylekey", "audition", "narration", "probe", "keyframes", "clips")
APPROVE_STAGES = ("outline", "style", "voice", "narration", "keyframes", "clips")
MOVES = ("in", "right", "out", "left")
DONE = ("completed", "attached")

# Speaking-rate heuristics for clear explainer narration (NOT measurements): they only size the
# script before the first TTS run. `set-audio` reports the measured rate; the measured audio wins.
# tr: Gemini 3.1 Flash TTS measured 1.4-1.9 (Charon) and 1.78 (Aoede) words/s in paid runs of 2026-09-20.
WPS = {"en": 2.5, "tr": 1.7, "de": 2.1, "nl": 2.4, "es": 2.6, "fr": 2.6, "it": 2.5, "pt": 2.5,
       "ru": 2.0, "pl": 2.0, "ar": 2.0, "hi": 2.3, "id": 2.2}
CPS = {"zh": 4.0, "ja": 6.0, "ko": 4.5}  # characters per second where words are not space-separated
DEFAULT_WPS = 2.3
# Against a requested length an ESTIMATED block counts this much longer: voices run 10-20 percent off a
# heuristic, less off a rate the agent measured and passed as --wps. Measured blocks count as they are.
HEADROOM = {"override": 0.05}
DEFAULT_HEADROOM = 0.10

KEYFRAME_SIZE = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1536, 1536), "4:3": (1600, 1200)}
RENDER_SIZE = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:3": (1440, 1080)}

# Field presets read from the live OpenAPI schemas on 2026-09-19. A dated cache: confirm with
# `genmedia schema <id> --format openapi --json`; flags and --base-input override every value.
TEXT_FIELD = {"fal-ai/elevenlabs/tts/eleven-v3": "text", "fal-ai/gemini-3.1-flash-tts": "prompt",
              "xai/tts/v1": "text"}
TYPO_EDIT = "openai/gpt-image-2.5/flare/edit"  # labelled stills (plan --stage keyframes --allow-text)
SIZE_FIELD = {"bytedance/seedream/v5/pro/text-to-image": "image_size",
              "bytedance/seedream/v5/pro/edit": "image_size", TYPO_EDIT: "image_size"}
SIZE_MULTIPLE = {TYPO_EDIT: 16}  # both sides must be multiples of 16: 1920x1080 -> 1920x1088, render crops
IMAGE_BASE = {"bytedance/seedream/v5/pro/text-to-image": {"num_images": 1, "output_format": "png"},
              "bytedance/seedream/v5/pro/edit": {"num_images": 1, "output_format": "png"},
              TYPO_EDIT: {"num_images": 1, "output_format": "png", "quality": "high"}}
CLIP_PRESETS = {
    "alibaba/wan-3.0/image-to-video": {
        "image_field": "start_image_url", "duration_type": "int", "min_s": 2, "max_s": 30,
        "base": {"resolution": "720p", "audio": False, "enable_prompt_expansion": False}},
    "bytedance/seedance-2.5/us/image-to-video": {
        "image_field": "image_url", "duration_type": "str", "min_s": 4, "max_s": 30,
        "base": {"resolution": "720p", "generate_audio": False}},
    "minimax/h3-max-turbo/image-to-video": {
        "image_field": "image_url", "duration_type": "int", "min_s": 5, "max_s": 15,
        "base": {"resolution": "768P", "prompt_expansion_mode": "disabled"}},
}
PROBE_ENDPOINT = "fal-ai/ffmpeg-api/metadata"
COMPOSE_REFUSAL = ("fal-ai/ffmpeg-api/compose cannot reproduce an explainer timeline (measured 2026-09-21): it takes one "
                   "picture track, so stills and clips cannot share a request; an image track holds every still for "
                   "the first keyframe's duration; a voice track honours only its first keyframe's timestamp and "
                   "plays the rest back to back, without the lead and tail gaps. Assemble with local ffmpeg (render), which is free")

KEYFRAME_LEAD = ("Use the reference image only as the style guide: same rendering technique, palette, "
                 "line quality and texture. Do not copy its subject.")
DEFAULT_NEGATIVE = "No text, no letters, no numbers, no captions, no logos, no watermark."
TEXT_NEGATIVE = ("Render only the words quoted in the scene, spelled exactly as written, large and legible. "
                 "No other text, no logos, no watermark.")
DEFAULT_MOTION = ("Subtle, slow motion that keeps the composition: gentle parallax and small movements "
                  "of the main elements")
CLIP_TAIL = ("One continuous shot, no cuts, no camera shake. No on-screen text, no captions, no logos, "
             "no speaking characters, no lip movement.")

TR_ASCII = str.maketrans("ıİşŞğĞüÜöÖçÇ", "iIsSgGuUoOcC")
ENDPOINT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)+$")
LABEL_RE = re.compile(r"^\s*(?:block|blok|scene|sahne)\s*\d+\s*[:.)\-]\s*", re.IGNORECASE)
SENTENCE_RE = re.compile(r"(?<=[.!?…。！？])[\"'”’)\]]*\s+")


class Usage(Exception):
    pass


class Fail(Exception):
    def __init__(self, kind, message, **extra):
        Exception.__init__(self, message)
        self.kind, self.extra = kind, extra


# ---------------------------------------------------------------- small helpers
def slug(text):
    """Same normalisation as gm.py, so the label matches the run ledger."""
    folded = unicodedata.normalize("NFKD", str(text or "").translate(TR_ASCII))
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return re.sub(r"[^A-Za-z0-9._-]+", "-", folded).strip("-.")


def need_slug(text):
    value = slug(text)
    if not value:
        raise Usage("--slug is empty after normalisation")
    return value


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def digest(*parts):
    joined = "\x1f".join("" if part is None else str(part) for part in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:12]


def read_text(path, what):
    try:
        if path == "-":
            data = sys.stdin.buffer.read()
        else:
            with open(path, "rb") as handle:
                data = handle.read()
    except OSError as exc:
        raise Usage("cannot read %s %s: %s" % (what, path, exc.strerror or exc))
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise Usage("%s %s is not valid UTF-8" % (what, path))


def read_json(path, what):
    text = read_text(path, what)
    try:
        return json.loads(text)
    except ValueError as exc:
        raise Usage("%s %s is not valid JSON: %s" % (what, path, exc))


def write_file(path, text):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    tmp = "%s.tmp%d" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(tmp, path)


def project_dir(label):
    return os.path.join(PROJECTS, label)


def state_path(label):
    return os.path.join(project_dir(label), STATE)


def out_dir(label, *parts):
    return os.path.join(OUTPUT, label, *parts)


def clean(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def parse_blocks_arg(value, count):
    """'3,7' or '2-4,9' -> sorted unique indices, validated against the block count."""
    if not value:
        return None
    picked = set()
    for part in str(value).split(","):
        part = part.strip()
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
        if not match:
            raise Usage("--blocks takes numbers and ranges, for example 3,7 or 2-4")
        first, last = int(match.group(1)), int(match.group(2) or match.group(1))
        if first < 1 or last < first or last > count:
            raise Usage("--blocks %s is outside 1-%d" % (part, count))
        picked.update(range(first, last + 1))
    return sorted(picked)


# ---------------------------------------------------------------- state and run ledger
def load_state(label):
    path = state_path(label)
    if not os.path.isfile(path):
        raise Fail("no_project", "no block ledger at %s; run `init` first" % path)
    try:
        with open(path, "rb") as handle:
            state = json.loads(handle.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise Fail("bad_state", "cannot read %s: %s" % (path, exc))
    if not isinstance(state, dict) or not isinstance(state.get("blocks"), list):
        raise Fail("bad_state", "%s is not a block ledger" % path)
    return state


def save_state(state):
    state["updated"] = now()
    write_file(state_path(state["slug"]), json.dumps(state, ensure_ascii=False, indent=1) + "\n")


def ledger_records(label):
    """gm.py ledger lines merged per request (later lines win), label-filtered, in submission order."""
    merged = {}
    try:
        with open(LEDGER, "rb") as handle:
            raws = handle.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        raws = []
    for number, raw in enumerate(raws):
        try:
            line = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(line, dict) or not (line.get("request_id") or line.get("status") == "submit_unknown"):
            continue
        merged.setdefault(line.get("request_id") or "unknown:%d" % number, {}).update(line)
    return [record for record in merged.values() if record.get("label") == label]


def latest_by_job(records):
    latest = {}
    for record in records:
        if record.get("job_id"):
            latest[record["job_id"]] = record
    return latest


def apply_record(entry, record):
    outputs = [o for o in record.get("outputs") or [] if isinstance(o, dict)]
    entry["status"] = record.get("status") or "unknown"
    entry["request_id"] = record.get("request_id")
    entry["endpoint_id"] = record.get("endpoint_id")
    if outputs:
        if outputs[0].get("path"):
            entry["path"] = outputs[0]["path"]
        if outputs[0].get("url"):
            entry["url"] = outputs[0]["url"]


def sync(state):
    """Pull status, request id, path and URL of every recorded job from the run ledger."""
    latest = latest_by_job(ledger_records(state["slug"]))
    for block in state["blocks"]:
        for kind in KINDS:
            entry = block.get(kind) or {}
            if entry.get("job") and entry["job"] in latest:
                apply_record(entry, latest[entry["job"]])
    return latest


def pick_job_id(base, endpoint, new_input, latest, reroll):
    """Reuse an id only when the recorded request used the same endpoint and input (gm.py then
    resumes it for free); otherwise take the next -rN so nothing is overwritten or flagged."""
    pattern = re.compile(r"^%s(?:-r(\d+))?$" % re.escape(base))
    taken = sorted((int(m.group(1) or 1), job) for job, m in ((j, pattern.match(j)) for j in latest) if m)
    if not taken:
        return base, False
    number, job = taken[-1]
    record = latest[job]
    same = record.get("endpoint_id") == endpoint and record.get("input") == new_input
    if same and not reroll:
        return job, True
    return "%s-r%d" % (base, number + 1), False


# ---------------------------------------------------------------- script -> blocks
def rate_for(lang, override):
    code = (lang or "en").lower().split("-")[0].split("_")[0]
    if override:
        return float(override), ("chars" if code in CPS else "words"), "override"
    if code in CPS:
        return CPS[code], "chars", "heuristic"
    return WPS.get(code, DEFAULT_WPS), "words", ("heuristic" if code in WPS else "default heuristic")


def count_units(text, unit):
    if unit == "chars":
        return len(re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE))
    return len(text.split())


def split_sentences(text):
    return [part.strip() for part in SENTENCE_RE.split(clean(text)) if part.strip()]


def split_script(text, mode, unit, budget_units):
    paragraphs = [clean(LABEL_RE.sub("", p)) for p in re.split(r"\n\s*\n", text.replace("\r\n", "\n"))]
    paragraphs = [p for p in paragraphs if p]
    if mode == "auto":
        mode = "paragraph" if len(paragraphs) >= 2 else "sentence"
    if mode == "paragraph":
        return paragraphs, mode
    chunks, current, used = [], [], 0
    for sentence in split_sentences(" ".join(paragraphs)):
        size = count_units(sentence, unit)
        if current and used + size > budget_units:
            chunks.append(" ".join(current))
            current, used = [], 0
        current.append(sentence)
        used += size
    if current:
        chunks.append(" ".join(current))
    return chunks, mode


def size_block(block, state):
    text = block["narration"]
    units = count_units(text, state["unit"])
    block["words"] = len(text.split())
    block["chars"] = len(text)
    block["est_s"] = round(units / state["rate"], 2) if state["rate"] else 0.0
    budget = state["block_s"] - state["lead_s"] - state["tail_s"]
    flags = [f for f in block.get("flags") or [] if f not in ("long", "short")]
    if block["est_s"] > budget * 1.05:
        flags.append("long")
    elif block["est_s"] < budget * 0.5:
        flags.append("short")
    block["flags"] = flags
    return block


def parse_length(value):
    match = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?)\s*)?$", value or "")
    if not match:
        raise Usage("--length-s takes MAX or MIN-MAX in seconds, for example 15 or 30-40")
    low, high = (float(match.group(1)), float(match.group(2))) if match.group(2) else (None, float(match.group(1)))
    if not 3 <= high <= 600 or (low is not None and not 0 < low < high):
        raise Usage("--length-s: MAX between 3 and 600, MIN below MAX")
    return {"min_s": low, "max_s": high}


def block_seconds(block, state):
    """What a block will run: measured when its voice exists, else lead + estimate + tail, fitted like audio."""
    if block.get("visual_s"):
        return block["visual_s"]
    if state.get("fit") == "grid":
        return int(state["block_s"])
    return max(3, int(math.ceil(state["lead_s"] + block["est_s"] + state["tail_s"] - 1e-6)))


def pace(state):
    """Measured units per second over the voiced blocks, else the planning rate."""
    voiced = [b for b in state["blocks"] if b["audio"].get("duration_s")]
    spoken = sum(b["audio"]["duration_s"] for b in voiced)
    return sum(count_units(b["narration"], state["unit"]) for b in voiced) / spoken if spoken else state["rate"]


def cut_plan(state, over_s):
    """Fewest blocks to shorten. Blocks round up to whole seconds, so each row names the speech to cut to save
    `save_s` whole seconds, never more than 40 percent of that block's speech."""
    need = int(math.ceil(over_s - 1e-6))
    if state.get("fit") == "grid":
        return {"over_s": round(over_s, 2), "blocks": [], "unresolved_s": need,
                "how": "grid blocks are fixed at block_s: merge or drop a block"}
    rate, rows = pace(state), []
    for block in sorted(state["blocks"], key=lambda b: -(b["audio"].get("duration_s") or b["est_s"])):
        if need <= 0:
            break
        speech = block["audio"].get("duration_s") or block["est_s"]
        length = block_seconds(block, state)
        needed = state["lead_s"] + speech + state["tail_s"]
        save = min(need, length - 3, int(math.floor(length - needed + 0.4 * speech)))
        if save < 1:
            continue
        cut = needed - (length - save) + 0.05
        rows.append({"block": block["index"], "save_s": save, "cut_s": round(cut, 2),
                     "cut_units": int(math.ceil(cut * rate))})
        need -= save
    return {"over_s": round(over_s, 2), "unit": state["unit"], "blocks": rows, "unresolved_s": max(0, need)}


def length_report(state):
    """None when no length was requested. Otherwise the total against it: measured blocks count as they are,
    estimated blocks with headroom for a slower voice (see HEADROOM), so an estimate that only just fits is
    caught before the voice is paid for."""
    wanted = state.get("length")
    if not wanted:
        return None
    voiced = [b for b in state["blocks"] if b.get("visual_s")]
    measured_s = sum(b["visual_s"] for b in voiced)
    estimated_s = sum(block_seconds(b, state) for b in state["blocks"] if not b.get("visual_s"))
    headroom = HEADROOM.get(state.get("rate_source"), DEFAULT_HEADROOM)
    projected = round(measured_s + estimated_s * (1 + headroom), 2)
    report = {"min_s": wanted["min_s"], "max_s": wanted["max_s"], "total_s": measured_s + estimated_s,
              "projected_s": projected, "voiced_blocks": len(voiced), "measured": not estimated_s, "status": "ok"}
    if projected > wanted["max_s"] + 1e-6:
        report.update(status="over", cut=cut_plan(state, projected - wanted["max_s"]))
    elif wanted["min_s"] and report["total_s"] < wanted["min_s"] - 1e-6:
        report["status"] = "under"
    return report


def length_problem(report):
    if not report or report["status"] != "over":
        return None
    rows = report["cut"]["blocks"]
    where = ", ".join("block %d by about %d %s" % (r["block"], r["cut_units"], report["cut"].get("unit", "words"))
                      for r in rows) or report["cut"].get("how", "merge or drop a block")
    if not report["voiced_blocks"]:
        return ("the estimate is %d s, %g s with headroom for a slower voice, over the requested %g s: shorten %s "
                "before any voice is paid for" % (report["total_s"], report["projected_s"], report["max_s"], where))
    return ("the %s total is %g s, over the requested %g s: shorten %s, re-plan only those blocks' narration, "
            "measure again" % ("measured" if report["measured"] else "projected", report["projected_s"],
                               report["max_s"], where))


def new_block(index, narration):
    return {"index": index, "narration": narration, "scene": "", "motion": "",
            "move": MOVES[(index - 1) % len(MOVES)], "animate": False,
            "audio": {}, "keyframe": {}, "clip": {}, "visual_s": None, "approved": {}, "flags": []}


def cmd_init(args):
    label = need_slug(args.slug)
    path = state_path(label)
    if os.path.exists(path) and not args.force:
        raise Fail("exists", "%s exists; use `edit` to change a block, or --force to start over "
                   "(jobs already in the run ledger are kept and may be reused)" % path)
    if args.block_s < 4 or args.block_s > 30:
        raise Usage("--block-s must be between 4 and 30")
    if args.lead_s < 0 or args.tail_s < 0 or args.lead_s + args.tail_s >= args.block_s - 1:
        raise Usage("--lead-s and --tail-s must be >= 0 and leave room for speech")
    if args.aspect not in KEYFRAME_SIZE:
        raise Usage("--aspect must be one of %s" % ", ".join(sorted(KEYFRAME_SIZE)))
    if args.wps is not None and not 0.5 <= args.wps <= 12:
        raise Usage("--wps must be between 0.5 and 12")
    if args.minutes is not None and args.blocks is not None:
        raise Usage("give --minutes or --blocks, not both")
    wanted = parse_length(args.length_s) if args.length_s else None
    rate, unit, source = rate_for(args.lang, args.wps)
    text = read_text(args.script, "--script")
    if not clean(text):
        raise Usage("--script is empty")
    budget_units = rate * (args.block_s - args.lead_s - args.tail_s)
    chunks, mode = split_script(text, args.split, unit, budget_units)
    target = None
    if args.minutes is not None:
        if not 0.25 <= args.minutes <= 10:
            raise Usage("--minutes must be between 0.25 and 10")
        target = int(round(args.minutes * 60.0 / args.block_s))
    elif args.blocks is not None:
        if not 1 <= args.blocks <= 60:
            raise Usage("--blocks must be between 1 and 60")
        target = args.blocks
    if len(chunks) > 60:
        raise Usage("the script makes %d blocks; the limit is 60" % len(chunks))
    state = {"version": VERSION, "slug": label, "title": args.title or label, "lang": args.lang,
             "block_s": args.block_s, "rate": rate, "unit": unit, "rate_source": source,
             "lead_s": args.lead_s, "tail_s": args.tail_s, "aspect": args.aspect, "tier": args.tier,
             "fit": args.fit, "target_blocks": target or len(chunks), "length": wanted, "created": now(),
             "style": {"name": "", "text": "", "negative": DEFAULT_NEGATIVE, "refs": []},
             "approved": {}, "blocks": []}
    for index, chunk in enumerate(chunks, 1):
        state["blocks"].append(size_block(new_block(index, chunk), state))
    save_state(state)
    warnings = []
    if target and target != len(chunks):
        warnings.append("the script makes %d blocks, the target was %d: %s" % (
            len(chunks), target, "cut or merge blocks" if len(chunks) > target else "add blocks or shorten the target"))
    for flag, advice in (("long", "shorten the text"), ("short", "merge with a neighbour or accept dead air")):
        hit = [b["index"] for b in state["blocks"] if flag in b["flags"]]
        if hit:
            warnings.append("%s blocks %s: %s" % (flag, hit, advice))
    report = length_report(state)
    if length_problem(report):
        warnings.append(length_problem(report))
    elif report and report["status"] == "under":
        warnings.append("the estimate is %d s, under the requested %g s: add a sentence or accept a shorter video"
                        % (report["total_s"], report["min_s"]))
    return {"ok": True, "slug": label, "state": path, "split": mode, "blocks": len(chunks), "length": report,
            "rate": {"value": rate, "unit": "%s per second" % unit, "source": source},
            "speech_budget_s": round(args.block_s - args.lead_s - args.tail_s, 2),
            "planned_s": len(chunks) * args.block_s,
            "table": [{"index": b["index"], "words": b["words"], "chars": b["chars"], "est_s": b["est_s"],
                       "flags": b["flags"]} for b in state["blocks"]],
            "warnings": warnings}, 0


def get_block(state, index):
    if index is None or index < 1 or index > len(state["blocks"]):
        raise Usage("--block must be between 1 and %d" % len(state["blocks"]))
    return state["blocks"][index - 1]


def cmd_edit(args):
    state = load_state(need_slug(args.slug))
    block = get_block(state, args.block)
    text = clean(LABEL_RE.sub("", read_text(args.narration_file, "--narration-file")))
    if not text:
        raise Usage("--narration-file is empty")
    changed = text != block["narration"]
    if changed:
        block["narration"] = text
        block["audio"], block["visual_s"] = {}, None
        for key in ("script", "audio"):
            block["approved"].pop(key, None)
        block["flags"] = [f for f in block["flags"] if f not in ("over", "dead_air")]
    size_block(block, state)
    save_state(state)
    return {"ok": True, "block": block["index"], "changed": changed, "words": block["words"],
            "chars": block["chars"], "est_s": block["est_s"], "flags": block["flags"], "length": length_report(state),
            "reset": ["audio", "script approval", "narration approval"] if changed else [],
            "note": "the keyframe and clip of this block were kept; check that the picture still fits"}, 0


# ---------------------------------------------------------------- style, visuals, attach
def cmd_style(args):
    state = load_state(need_slug(args.slug))
    style = state["style"]
    before = digest(style.get("text"), style.get("key_url"), style.get("key_path"))
    if args.name:
        style["name"] = clean(args.name)
    if args.style_file:
        text = clean(read_text(args.style_file, "--style-file"))
        if len(text) < 20:
            raise Usage("the STYLE string is too short to hold a look together (write 1-3 sentences)")
        style["text"] = text
    if args.negative_file:
        style["negative"] = clean(read_text(args.negative_file, "--negative-file"))
    if args.ref_url:
        if len(args.ref_url) > 9:
            raise Usage("at most 9 --ref-url values: the style key must stay among the references the model reads")
        for url in args.ref_url:
            check_url(url, "--ref-url")
        style["refs"] = list(args.ref_url)
    if args.key_job:
        record = latest_by_job(ledger_records(state["slug"])).get(args.key_job)
        if not record or record.get("status") != "completed":
            raise Fail("not_ready", "job %s is not completed under label %s" % (args.key_job, state["slug"]))
        entry = {}
        apply_record(entry, record)
        if not entry.get("url"):
            raise Fail("not_ready", "job %s has no file output in the run ledger" % args.key_job)
        style.update(key_job=args.key_job, key_url=entry["url"], key_path=entry.get("path"))
    if args.key_url:
        style["key_url"] = check_url(args.key_url, "--key-url")
        style.pop("key_job", None)
    if args.key_path:
        if not os.path.isfile(args.key_path):
            raise Usage("--key-path not found: %s" % args.key_path)
        style["key_path"] = args.key_path
    reset = []
    if before != digest(style.get("text"), style.get("key_url"), style.get("key_path")):
        if state["approved"].pop("style", None):
            reset.append("style approval")
    if args.style_file and state["approved"].get("style_text") not in (None, digest(style["text"])):
        state["approved"].pop("style_text", None)
        reset.append("outline approval of the style text")
    save_state(state)
    return {"ok": True, "style": {k: style.get(k) for k in ("name", "text", "negative", "key_job", "key_url",
                                                             "key_path", "refs")}, "reset": reset}, 0


def check_url(url, what):
    if not isinstance(url, str) or not url.startswith("https://"):
        raise Usage("%s must be an https:// URL (upload local files with gm.py upload first)" % what)
    return url


def cmd_visuals(args):
    state = load_state(need_slug(args.slug))
    doc = read_json(args.input, "--input")
    rows = doc.get("blocks") if isinstance(doc, dict) else doc
    if not isinstance(rows, list) or not rows:
        raise Usage("--input must be a JSON list of {index, scene, motion?, move?, animate?}")
    touched, reset = [], []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("index"), int):
            raise Usage("every row needs an integer `index`")
        block = get_block(state, row["index"])
        unknown = sorted(set(row) - {"index", "scene", "motion", "move", "animate"})
        if unknown:
            raise Usage("block %d: unknown keys %s" % (row["index"], unknown))
        if "scene" in row:
            scene = clean(row["scene"])
            if scene != block["scene"] and block["keyframe"]:
                block["keyframe"]["stale"] = True
                for key in ("keyframe", "clip"):
                    if block["approved"].pop(key, None):
                        reset.append("block %d %s approval" % (block["index"], key))
            block["scene"] = scene
        if "motion" in row:
            motion = clean(row["motion"])
            if motion != block["motion"] and block["clip"]:
                block["clip"]["stale"] = True
                if block["approved"].pop("clip", None):
                    reset.append("block %d clip approval" % block["index"])
            block["motion"] = motion
        if "move" in row:
            if row["move"] not in MOVES:
                raise Usage("block %d: move must be one of %s" % (row["index"], ", ".join(MOVES)))
            block["move"] = row["move"]
        if "animate" in row:
            if not isinstance(row["animate"], bool):
                raise Usage("block %d: animate must be true or false" % row["index"])
            block["animate"] = row["animate"]
        touched.append(block["index"])
    save_state(state)
    missing = [b["index"] for b in state["blocks"] if not b["scene"]]
    return {"ok": True, "updated": sorted(set(touched)), "animated": [b["index"] for b in state["blocks"] if b["animate"]],
            "missing_scene": missing, "reset": reset}, 0


def cmd_attach(args):
    state = load_state(need_slug(args.slug))
    block = get_block(state, args.block)
    if not os.path.isfile(args.path):
        raise Usage("--path not found: %s" % args.path)
    entry = {"job": None, "status": "attached", "path": args.path}
    if args.url:
        entry["url"] = check_url(args.url, "--url")
    block[args.kind] = entry
    reset = [key for key in ({"audio": ("audio",), "keyframe": ("keyframe", "clip"), "clip": ("clip",)}[args.kind])
             if block["approved"].pop(key, None)]
    if args.kind == "audio":
        block["visual_s"] = None
    save_state(state)
    return {"ok": True, "block": block["index"], "kind": args.kind, "entry": entry, "reset": reset,
            "next": "set-audio --block %d --duration <measured seconds>" % block["index"] if args.kind == "audio" else None}, 0


# ---------------------------------------------------------------- approvals and gates
def approval_digest(block, key):
    if key == "script":
        return digest(block["narration"])
    if key == "audio":
        entry = block["audio"]
        return digest(block["narration"], entry.get("job") or entry.get("path"), entry.get("duration_s"))
    entry = block[key]
    return digest(entry.get("job") or entry.get("path"))


def is_approved(block, key):
    return block["approved"].get(key) == approval_digest(block, key)


def style_digest(state):
    style = state["style"]
    return digest(style.get("text"), style.get("key_url") or style.get("key_path"))


def entry_done(entry):
    return bool(entry) and entry.get("status") in DONE and not entry.get("stale")


def cmd_approve(args):
    state = load_state(need_slug(args.slug))
    sync(state)
    picked = parse_blocks_arg(args.blocks, len(state["blocks"])) or [b["index"] for b in state["blocks"]]
    blocks = [state["blocks"][i - 1] for i in picked]
    stage, problems = args.stage, []
    if args.tier and (stage != "outline" or args.blocks):
        raise Usage("--tier goes with --stage outline for all blocks: it records the tier chosen at CP1")
    if (stage == "voice") != bool(clean(args.voice or "")):
        raise Usage("--voice goes with --stage voice, and --stage voice needs --voice <the voice the user picked>")
    if stage == "outline":
        if not state["style"].get("text"):
            problems.append("no STYLE string yet: run `style --style-file`")
        problems += ["block %d has no scene" % b["index"] for b in blocks if not b["scene"]]
        problems += ["block %d is flagged long" % b["index"] for b in blocks if "long" in b["flags"]]
        problems += [p for p in [length_problem(length_report(state))] if p]
    elif stage in ("style", "voice"):
        if args.blocks:
            raise Usage("--blocks does not apply to --stage %s" % stage)
        if stage == "style" and not (state["style"].get("key_url") or state["style"].get("key_path")):
            problems.append("no style-key image recorded: run `style --key-job <id>` or --key-path/--key-url")
    elif stage == "narration":
        problems += ["block %d has no measured narration" % b["index"] for b in blocks
                     if not (entry_done(b["audio"]) and b["audio"].get("duration_s"))]
        problems += [p for p in [length_problem(length_report(state))] if p]
    else:
        kind = "keyframe" if stage == "keyframes" else "clip"
        if stage == "clips" and not args.blocks:
            blocks = [b for b in blocks if b["clip"]]
            if not blocks:
                problems.append("no block has a clip")
        problems += ["block %d has no finished %s" % (b["index"], kind) for b in blocks if not entry_done(b[kind])]
    if problems:
        raise Fail("not_ready", "cannot approve %s" % stage, problems=problems)
    stamp = {"ts": now(), "note": clean(args.note)} if args.note else {"ts": now()}
    if stage == "outline":
        for block in blocks:
            block["approved"]["script"] = approval_digest(block, "script")
        state["approved"]["style_text"] = digest(state["style"]["text"])
        if args.tier:
            state["tier"] = args.tier
    elif stage == "style":
        state["approved"]["style"] = style_digest(state)
    elif stage == "voice":
        state["approved"]["voice"] = clean(args.voice)
    else:
        key = {"narration": "audio", "keyframes": "keyframe", "clips": "clip"}[stage]
        for block in blocks:
            block["approved"][key] = approval_digest(block, key)
    whole = stage in ("style", "voice")
    if stage == "voice":
        stamp["voice"] = state["approved"]["voice"]
    state.setdefault("approvals", []).append(dict(stamp, stage=stage, blocks=[] if whole else
                                                  [b["index"] for b in blocks]))
    save_state(state)
    return {"ok": True, "stage": stage, "tier": state["tier"],
            "blocks": [] if whole else [b["index"] for b in blocks],
            "note": "an approval covers exactly what was approved: a changed text, scene, job or style resets it"}, 0


def gate(problems, message):
    if problems:
        raise Fail("gate", message, blocks=sorted({p[0] for p in problems if p[0]}),
                   problems=["block %d: %s" % p if p[0] else p[1] for p in problems])


def voice_gate(state, base, field):
    """CP2 before the long read: the user picked the voice (audition, or named it) and the base input carries it."""
    voice = state["approved"].get("voice")
    if not voice:
        gate([(0, "voice not approved (CP2): plan --stage audition, the user listens, then approve --stage voice "
                  "--voice <name> (a voice the user named up front: approve it with --note)")], "narration is gated")
    if base.get(field) != voice:
        gate([(0, "the base input's %s is %s, not the voice approved at CP2 (%s): put it into the base input, "
                  "or pass --voice-field when the family names the field differently"
               % (field, json.dumps(base.get(field)), voice))], "narration is gated")


def outline_gate(state, blocks):
    problems = [(b["index"], "script not approved (CP1)") for b in blocks if not is_approved(b, "script")]
    if state["approved"].get("style_text") != digest(state["style"].get("text")):
        problems.append((0, "outline not approved for the current STYLE string (CP1)"))
    gate(problems, "outline not approved")


# ---------------------------------------------------------------- measured audio -> visual lengths
def fit_block(block, state):
    audio_s = block["audio"].get("duration_s")
    flags = [f for f in block["flags"] if f not in ("over", "dead_air")]
    if not audio_s:
        block["visual_s"] = None
        block["flags"] = flags
        return
    needed = state["lead_s"] + audio_s + state["tail_s"]
    if state.get("fit") == "grid":
        block["visual_s"] = int(state["block_s"])
        if state["lead_s"] + audio_s > state["block_s"] - 0.1:
            flags.append("over")
    else:
        block["visual_s"] = max(3, int(math.ceil(needed - 1e-6)))
        if block["visual_s"] > state["block_s"]:
            flags.append("over")
    if audio_s < 0.5 * state["block_s"]:
        flags.append("dead_air")
    block["flags"] = flags


def record_duration(block, state, seconds, path=None, url=None):
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or not 0.2 <= seconds <= 120:
        raise Usage("block %d: duration %r is not between 0.2 and 120 seconds" % (block["index"], seconds))
    entry = block["audio"]
    if not entry:
        raise Fail("not_ready", "block %d has no narration job or attached file" % block["index"])
    if entry.get("duration_s") != round(float(seconds), 3):
        block["approved"].pop("audio", None)
    entry["duration_s"] = round(float(seconds), 3)
    if path:
        entry["path"] = path
    if url:
        entry["url"] = check_url(url, "--url")
    fit_block(block, state)


def cmd_set_audio(args):
    state = load_state(need_slug(args.slug))
    sync(state)
    modes = [bool(args.probe), bool(args.batch_result), args.block is not None]
    if sum(modes) != 1:
        raise Usage("give exactly one of --probe, --batch-result, or --block with --duration")
    by_job = {b["audio"].get("job"): b for b in state["blocks"] if b["audio"].get("job")}
    recorded, ignored = [], []
    if args.block is not None:
        if args.duration is None:
            raise Usage("--block needs --duration")
        block = get_block(state, args.block)
        if args.path and not os.path.isfile(args.path):
            raise Usage("--path not found: %s" % args.path)
        record_duration(block, state, args.duration, args.path, args.url)
        recorded.append(block["index"])
    elif args.probe:
        doc = read_json(args.probe, "--probe")
        if not isinstance(doc, dict) or doc.get("ok") is False or not isinstance(doc.get("files"), list):
            raise Fail("bad_input", "--probe is not a successful `audiokit.py probe` result",
                       upstream=doc if isinstance(doc, dict) else None)
        by_path = {os.path.normpath(b["audio"]["path"]): b for b in state["blocks"] if b["audio"].get("path")}
        for item in doc["files"]:
            path = str(item.get("path") or "")
            match = re.match(r"^(n\d+(?:-r\d+)?)_", os.path.basename(path))
            block = by_path.get(os.path.normpath(path)) or (by_job.get(match.group(1)) if match else None)
            if block is None:
                ignored.append(path)
                continue
            record_duration(block, state, item.get("duration_s"), path)
            recorded.append(block["index"])
    else:
        doc = read_json(args.batch_result, "--batch-result")
        if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), list):
            raise Fail("bad_input", "--batch-result is not a `gm.py batch` result")
        for job in doc["jobs"]:
            name = str(job.get("id") or "")
            media = ((job.get("result") or {}).get("media") or {}) if isinstance(job.get("result"), dict) else {}
            block = by_job.get(name[2:]) if name.startswith("p-") else None
            if block is None or not isinstance(media.get("duration"), (int, float)):
                ignored.append(name)
                continue
            record_duration(block, state, media["duration"])
            recorded.append(block["index"])
    save_state(state)
    measured = [b for b in state["blocks"] if b["audio"].get("duration_s")]
    units = sum(count_units(b["narration"], state["unit"]) for b in measured)
    spoken = sum(b["audio"]["duration_s"] for b in measured)
    table = [{"index": b["index"], "est_s": b["est_s"], "audio_s": b["audio"].get("duration_s"),
              "visual_s": b["visual_s"], "flags": b["flags"],
              "over_by_s": round(state["lead_s"] + b["audio"]["duration_s"] + state["tail_s"] - state["block_s"], 2)
              if "over" in b["flags"] else None} for b in state["blocks"]]
    over = [b["index"] for b in state["blocks"] if "over" in b["flags"]]
    report = length_report(state)
    advice = ("blocks %s run past the %d s block: over by a second or less, keep them (fit=audio lets the block "
              "grow); more, shorten the text with `edit` and re-plan only those blocks" % (over, state["block_s"])) if over else None
    problem = length_problem(report)
    if problem and report and report["voiced_blocks"]:
        advice = problem
    return {"ok": True, "recorded": sorted(set(recorded)), "ignored": ignored, "length": report,
            "unmeasured": [b["index"] for b in state["blocks"] if not b["audio"].get("duration_s")],
            "over": over, "table": table,
            "measured_rate": {"value": round(units / spoken, 2) if spoken else None,
                              "unit": "%s per second" % state["unit"], "planned": state["rate"]},
            "total_s": sum(b["visual_s"] or state["block_s"] for b in state["blocks"]),
            "advice": advice}, 0


# ---------------------------------------------------------------- batch plans
def load_base(path):
    if not path:
        return {}
    base = read_json(path, "--base-input")
    if not isinstance(base, dict):
        raise Usage("--base-input must be a JSON object")
    return base


def price(args, quantity):
    for flag, value in (("1k", args.price_per_1k), ("image", args.price_per_image), ("second", args.price_per_second)):
        if value is not None and value < 0:
            raise Usage("--price-per-%s must be >= 0" % flag)
    if args.price_per_1k is not None:
        return round(quantity / 1000.0 * args.price_per_1k, 4)
    if args.price_per_image is not None:
        return round(quantity * args.price_per_image, 4)
    if args.price_per_second is not None:
        return round(quantity * args.price_per_second, 4)
    return None


def need_endpoint(args, default=None):
    endpoint = args.endpoint or default
    if not endpoint:
        raise Usage("--endpoint is required for --stage %s" % args.stage)
    if not ENDPOINT_RE.match(endpoint):
        raise Usage("--endpoint must look like owner/model[/variant]")
    return endpoint


def keyframe_size(state, endpoint):
    step = SIZE_MULTIPLE.get(endpoint, 1)
    return {side: int(math.ceil(value / float(step)) * step)
            for side, value in zip(("width", "height"), KEYFRAME_SIZE[state["aspect"]])}


def visual_prompt(state, scene, allow_text=False):
    style = state["style"]
    parts = [KEYFRAME_LEAD, "Scene: %s." % scene.rstrip(". "), style["text"]]
    if allow_text:  # a labelled still on a typography model: the lettering ban would contradict the scene
        parts.append(TEXT_NEGATIVE)
    elif style.get("negative"):
        parts.append(style["negative"])
    return " ".join(parts)


def clip_prompt(state, block):
    motion = (block["motion"] or DEFAULT_MOTION).rstrip(". ")
    return " ".join(["%s." % motion, state["style"]["text"], CLIP_TAIL])


def first_sentences(text, limit=220):
    picked = ""
    for sentence in split_sentences(text):
        if picked and len(picked) + len(sentence) + 1 > limit:
            break
        picked = (picked + " " + sentence).strip()
    return picked or text[:limit]


def make_job(job_id, endpoint, payload, download, cost, **meta):
    job = {"id": job_id, "endpoint_id": endpoint, "input": payload, "download": download}
    if cost is not None:
        job["est_cost_usd"] = cost
    return job, dict(meta, id=job_id, est_cost_usd=cost)


def cmd_plan(args):
    state = load_state(need_slug(args.slug))
    label = state["slug"]
    latest = sync(state)
    stage = args.stage
    base = load_base(args.base_input)
    picked = parse_blocks_arg(args.blocks, len(state["blocks"]))
    blocks = [state["blocks"][i - 1] for i in picked] if picked else list(state["blocks"])
    jobs, rows, notes = [], [], []
    if args.max_parallel is not None and not 1 <= args.max_parallel <= 40:
        raise Usage("--max-parallel must be between 1 and 40")
    own_kind = {"narration": "audio", "keyframes": "keyframe", "clips": "clip"}.get(stage)
    if own_kind and args.reroll and not picked:
        raise Usage("--reroll pays for a new take of every block: name the blocks with --blocks")
    if own_kind and not picked:
        kept = [b["index"] for b in blocks if b[own_kind].get("status") == "attached"]
        if kept:
            blocks = [b for b in blocks if b["index"] not in kept]
            notes.append("blocks %s keep their attached %s; name them with --blocks to generate one instead" % (kept, own_kind))

    if stage in ("stylekey", "audition"):
        if args.blocks:
            raise Usage("--blocks does not apply to --stage %s" % stage)
        outline_gate(state, state["blocks"])
    if stage == "stylekey":
        endpoint = need_endpoint(args)
        if not args.prompt_file:
            raise Usage("--stage stylekey needs --prompt-file (the key-image prompt of the chosen style)")
        prompt = clean(read_text(args.prompt_file, "--prompt-file"))
        if state["style"]["text"] not in prompt:
            prompt = "%s %s" % (prompt.rstrip(), state["style"]["text"])
        payload = {"prompt": prompt}  # type: dict
        size_field = args.size_field or SIZE_FIELD.get(endpoint)
        if size_field:
            payload[size_field] = keyframe_size(state, endpoint)
        payload.update(IMAGE_BASE.get(endpoint, {}))
        payload.update(base)
        job_id, reused = pick_job_id("stylekey", endpoint, payload, latest, args.reroll)
        job, row = make_job(job_id, endpoint, payload, "%s/%s_{index}.{ext}" % (out_dir(label, "style"), job_id),
                            price(args, 1), reused=reused)
        jobs.append(job)
        rows.append(row)
        notes.append("after CP2: style --key-job %s, then approve --stage style" % job_id)
    elif stage == "audition":
        endpoint = need_endpoint(args)
        voices = [v.strip() for v in (args.voices or "").split(",") if v.strip()]
        if not 1 <= len(voices) <= 6:
            raise Usage("--stage audition needs --voices with 1-6 comma-separated voice names")
        text_field = args.text_field or TEXT_FIELD.get(endpoint)
        if not text_field:
            raise Usage("unknown TTS endpoint: pass --text-field (read it from the schema)")
        sample = clean(read_text(args.text_file, "--text-file")) if args.text_file else first_sentences(
            state["blocks"][0]["narration"])
        for voice in voices:
            payload = dict(base)
            payload[text_field] = sample
            payload[args.voice_field] = voice
            job_id, reused = pick_job_id("aud-%s" % (slug(voice).lower() or "voice"), endpoint, payload, latest, args.reroll)
            job, row = make_job(job_id, endpoint, payload, "%s/%s_{index}.{ext}" % (out_dir(label, "audition"), job_id),
                                price(args, len(sample)), voice=voice, reused=reused)
            jobs.append(job)
            rows.append(row)
        notes.append("the agent cannot hear: the user picks the voice; put it into the base input of the narration stage")
    elif stage == "narration":
        endpoint = need_endpoint(args)
        outline_gate(state, blocks)
        voice_gate(state, base, args.voice_field)
        text_field = args.text_field or TEXT_FIELD.get(endpoint)
        if not text_field:
            raise Usage("unknown TTS endpoint: pass --text-field (read it from the schema)")
        for block in blocks:
            payload = dict(base)
            payload[text_field] = block["narration"]
            base_id = "%s%02d" % (KIND_PREFIX["audio"], block["index"])
            job_id, reused = pick_job_id(base_id, endpoint, payload, latest, args.reroll)
            job, row = make_job(job_id, endpoint, payload,
                                "%s/%s_{index}.{ext}" % (out_dir(label, KIND_FOLDER["audio"]), job_id),
                                price(args, block["chars"]), block=block["index"], reused=reused)
            jobs.append(job)
            rows.append(row)
            if block["audio"].get("job") != job_id:
                block["audio"] = {"job": job_id, "status": "planned"}
                block["visual_s"] = None
                block["approved"].pop("audio", None)
        notes.append("after the batch: measure every file, then set-audio; nothing visual before that")
    elif stage == "probe":
        endpoint = need_endpoint(args, PROBE_ENDPOINT)
        missing = [(b["index"], "narration job not completed or has no URL") for b in blocks
                   if not (entry_done(b["audio"]) and b["audio"].get("url") and b["audio"].get("job"))]
        if missing:
            raise Fail("not_ready", "narration is not ready to probe", blocks=[m[0] for m in missing],
                       problems=["block %d: %s" % m for m in missing])
        for block in blocks:
            payload = dict(base)
            payload["media_url"] = block["audio"]["url"]
            job, row = make_job("p-%s" % block["audio"]["job"], endpoint, payload, False, price(args, 1),
                                block=block["index"], reused=False)
            jobs.append(job)
            rows.append(row)
        notes.append("pipe the batch output into: set-audio --batch-result -  (the run ledger does not keep results)")
    elif stage == "keyframes":
        endpoint = need_endpoint(args)
        style = state["style"]
        problems = []
        if state["approved"].get("style") != style_digest(state) or not style.get("key_url"):
            problems.append((0, "style key not approved or has no URL (CP2): style --key-job/--key-url, approve --stage style"))
        for block in blocks:
            if not block["scene"]:
                problems.append((block["index"], "no scene"))
            if not block["audio"].get("duration_s"):
                problems.append((block["index"], "audio not measured (audio-before-video barrier)"))
            elif not is_approved(block, "audio"):
                problems.append((block["index"], "narration not approved (CP3)"))
        over = length_problem(length_report(state))
        if over:
            problems.append((0, over))
        gate(problems, "keyframes are gated")
        if args.allow_text and not picked:
            raise Usage("--allow-text is for single labelled stills: name them with --blocks")
        size_field = args.size_field or SIZE_FIELD.get(endpoint)
        for block in blocks:
            payload = {"prompt": visual_prompt(state, block["scene"], args.allow_text),
                       args.refs_field: [style["key_url"]] + list(style.get("refs") or [])}
            if size_field:
                payload[size_field] = keyframe_size(state, endpoint)
            payload.update(IMAGE_BASE.get(endpoint, {}))
            payload.update(base)
            base_id = "%s%02d" % (KIND_PREFIX["keyframe"], block["index"])
            job_id, reused = pick_job_id(base_id, endpoint, payload, latest, args.reroll)
            job, row = make_job(job_id, endpoint, payload,
                                "%s/%s_{index}.{ext}" % (out_dir(label, KIND_FOLDER["keyframe"]), job_id),
                                price(args, 1), block=block["index"], reused=reused)
            jobs.append(job)
            rows.append(row)
            if block["keyframe"].get("job") != job_id:
                block["keyframe"] = {"job": job_id, "status": "planned"}
                for key in ("keyframe", "clip"):
                    block["approved"].pop(key, None)
    else:  # clips
        endpoint = need_endpoint(args)
        preset = CLIP_PRESETS.get(endpoint, {})
        image_field = args.image_field or preset.get("image_field")
        duration_type = args.duration_type or preset.get("duration_type")
        if not image_field or not duration_type:
            raise Usage("unknown clip endpoint: pass --image-field and --duration-type int|str (read them from the schema)")
        min_s = args.min_s if args.min_s is not None else preset.get("min_s", 1)
        max_s = args.max_s if args.max_s is not None else preset.get("max_s", 60)
        if min_s < 1 or max_s < min_s:
            raise Usage("--min-s and --max-s must satisfy 1 <= min <= max")
        if not picked:
            if state["tier"] == "animatic":
                raise Fail("gate", "the tier is animatic: no clips are planned. Name blocks with --blocks to animate them anyway")
            blocks = [b for b in blocks if b["animate"]] if state["tier"] == "hybrid" else blocks
            if not blocks:
                raise Fail("not_ready", "no block is marked animate: set it with `visuals` or pass --blocks")
        problems = []
        for block in blocks:
            if not block["visual_s"]:
                problems.append((block["index"], "audio not measured (audio-before-video barrier)"))
            if not (entry_done(block["keyframe"]) and block["keyframe"].get("url")):
                problems.append((block["index"], "keyframe not finished or has no URL (upload and `attach --url`)"))
            elif not is_approved(block, "keyframe"):
                problems.append((block["index"], "keyframe not approved (CP4)"))
        gate(problems, "clips are gated")
        merged_base = dict(preset.get("base") or {})
        merged_base.update(base)
        for block in blocks:
            ordered = min(max(int(block["visual_s"]), min_s), max_s)
            payload = {"prompt": clip_prompt(state, block), image_field: block["keyframe"]["url"],
                       args.duration_field: str(ordered) if duration_type == "str" else ordered}
            payload.update(merged_base)
            base_id = "%s%02d" % (KIND_PREFIX["clip"], block["index"])
            job_id, reused = pick_job_id(base_id, endpoint, payload, latest, args.reroll)
            job, row = make_job(job_id, endpoint, payload,
                                "%s/%s_{index}.{ext}" % (out_dir(label, KIND_FOLDER["clip"]), job_id),
                                price(args, ordered), block=block["index"], ordered_s=ordered,
                                visual_s=block["visual_s"], reused=reused)
            jobs.append(job)
            rows.append(row)
            if ordered != block["visual_s"]:
                notes.append("block %d: the model takes %d-%d s, ordered %d s for a %d s block (render trims or holds the last frame)"
                             % (block["index"], min_s, max_s, ordered, block["visual_s"]))
            if block["clip"].get("job") != job_id:
                block["clip"] = {"job": job_id, "status": "planned", "ordered_s": ordered}
                block["approved"].pop("clip", None)

    if not jobs:
        raise Fail("not_ready", "nothing to plan for --stage %s: no block is selected" % stage)
    if len({job["id"] for job in jobs}) != len(jobs):
        raise Usage("two jobs share an id (duplicate voices?)")
    suffix = "-b%s" % "-".join(str(i) for i in picked) if picked else ""
    if len(suffix) > 40:
        suffix = "-b%s" % digest(suffix)
    path = args.out or os.path.join(project_dir(label), "plan-%s%s.json" % (stage, suffix))
    parallel = args.max_parallel or min(max(len(jobs), 1), 12)
    write_file(path, json.dumps({"label": label, "max_parallel": parallel, "jobs": jobs}, ensure_ascii=False, indent=1) + "\n")
    save_state(state)
    costs = [row["est_cost_usd"] for row in rows if row.get("est_cost_usd") is not None]
    return {"ok": True, "stage": stage, "plan": path, "label": label, "jobs": rows,
            "est_total_usd": round(sum(costs), 4) if costs else None,
            "new_paid_jobs": sum(1 for row in rows if not row.get("reused")),
            "run": "gm.py batch --plan %s  (Bash timeout 600000 ms; on status pending run the same command again)" % path,
            "notes": notes}, 0


# ---------------------------------------------------------------- timeline, SRT
def uses_clip(block):
    return entry_done(block["clip"])


def build_timeline(state):
    missing = [b["index"] for b in state["blocks"] if not b["visual_s"]]
    if missing:
        raise Fail("gate", "audio not measured", blocks=missing,
                   problems=["block %d: no measured narration, so its length is unknown" % i for i in missing])
    if state.get("fit") == "grid":
        over = [b["index"] for b in state["blocks"] if "over" in b["flags"]]
        if over:
            raise Fail("gate", "narration longer than its block (fit=grid)", blocks=over,
                       problems=["block %d: shorten the narration or re-init with --fit audio" % i for i in over])
    rows, cursor = [], 0.0
    for block in state["blocks"]:
        audio_s = block["audio"]["duration_s"]
        rows.append({"index": block["index"], "start_s": round(cursor, 3), "visual_s": block["visual_s"],
                     "audio_start_s": round(cursor + state["lead_s"], 3), "audio_s": audio_s,
                     "kind": "clip" if uses_clip(block) else "still"})
        cursor += block["visual_s"]
    return rows, cursor


def wrap_lines(text, max_chars, max_lines):
    words, lines, current = text.split(), [], ""
    for word in words:
        if current and len(current) + 1 + len(word) > max_chars:
            lines.append(current)
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        lines.append(current)
    if len(lines) == 2 and max_lines >= 2:  # balance two lines
        joined = " ".join(lines).split()
        best = min(range(1, len(joined)), key=lambda i: abs(len(" ".join(joined[:i])) - len(" ".join(joined[i:]))),
                   default=None)
        if best:
            first, second = " ".join(joined[:best]), " ".join(joined[best:])
            if len(first) <= max_chars and len(second) <= max_chars:
                lines = [first, second]
    return lines


def split_cues(text, max_chars, max_lines):
    """Sentences first; a sentence that does not fit is halved at the clause mark (else the word gap)
    nearest its middle; neighbours that fit together are merged."""
    limit = max_chars * max_lines

    def fits(piece):
        return len(piece) <= limit and len(wrap_lines(piece, max_chars, 99)) <= max_lines

    def pieces(piece):
        if fits(piece):
            return [piece]
        words = piece.split()
        if len(words) < 2:  # no spaces (CJK) or one endless token: cut by characters
            return [piece[i:i + limit] for i in range(0, len(piece), limit)]
        best, best_score = 1, None
        for i in range(1, len(words)):
            score = abs(len(" ".join(words[:i])) - len(piece) / 2.0)
            if re.search(r"[,;:—–]$", words[i - 1]):
                score -= 0.2 * len(piece)
            if best_score is None or score < best_score:
                best, best_score = i, score
        return pieces(" ".join(words[:best])) + pieces(" ".join(words[best:]))

    cues, whole = [], []  # whole[i]: cue i holds complete sentences only, so another one may join it
    for sentence in split_sentences(text) or [text]:
        parts = pieces(sentence)
        if len(parts) == 1 and cues and whole[-1] and fits(cues[-1] + " " + parts[0]):
            cues[-1] = cues[-1] + " " + parts[0]
            continue
        cues.extend(parts)
        whole.extend([len(parts) == 1] * len(parts))
    return cues


def srt_time(seconds):
    millis = int(round(max(seconds, 0) * 1000))
    return "%02d:%02d:%02d,%03d" % (millis // 3600000, millis // 60000 % 60, millis // 1000 % 60, millis % 1000)


def build_srt(state, rows, max_chars, max_lines):
    entries = []
    for block, row in zip(state["blocks"], rows):
        cues = split_cues(block["narration"], max_chars, max_lines)
        weights = [max(len(cue), 1) for cue in cues]
        cursor, total = row["audio_start_s"], float(sum(weights))
        for cue, weight in zip(cues, weights):
            span = row["audio_s"] * weight / total
            entries.append((cursor, cursor + span, wrap_lines(cue, max_chars, max_lines)))
            cursor += span
    text = "".join("%d\n%s --> %s\n%s\n\n" % (n, srt_time(start), srt_time(max(end - 0.04, start + 0.2)), "\n".join(lines))
                   for n, (start, end, lines) in enumerate(entries, 1))
    return text, len(entries)


def cmd_timeline(args):
    state = load_state(need_slug(args.slug))
    sync(state)
    save_state(state)
    rows, total = build_timeline(state)
    label, written, notes = state["slug"], {}, []
    if args.compose:
        raise Fail("unsupported", COMPOSE_REFUSAL, options=[
            "install ffmpeg (free, e.g. brew install ffmpeg) and run render --final",
            "deliver the approved parts unassembled: narration files, stills, clips and the SRT from timeline --srt"])
    if args.max_chars < 10 or args.max_lines < 1:
        raise Usage("--max-chars must be >= 10 and --max-lines >= 1")
    if args.srt:
        text, count = build_srt(state, rows, args.max_chars, args.max_lines)
        write_file(args.srt, text)
        written["srt"] = {"path": args.srt, "cues": count}
        notes.append("cue times inside a block are proportional to text length; for word-exact cues align the "
                     "narration (forced alignment) and use audiokit.py captions with --offset <audio_start_s>")
    if args.concat:
        base = os.path.dirname(os.path.abspath(args.concat))
        lines = []
        for block in state["blocks"]:
            segment = os.path.abspath(segment_path(label, block["index"]))
            lines.append("file '%s'\n" % os.path.relpath(segment, base).replace(os.sep, "/").replace("'", "'\\''"))
        write_file(args.concat, "".join(lines))
        written["concat"] = {"path": args.concat, "segments": len(lines)}
    target = state["target_blocks"] * state["block_s"]
    return {"ok": True, "total_s": total, "total_ms": int(round(total * 1000)), "target_s": target,
            "drift_s": round(total - target, 3), "music_minutes": int(math.ceil(total / 60.0)),
            "blocks": rows, "written": written, "notes": notes}, 0


# ---------------------------------------------------------------- local render
def segment_path(label, index):
    return out_dir(label, "blocks", "b%02d.mp4" % index)


def final_path(label):
    return out_dir(label, "%s_final.mp4" % label)


def find_ffmpeg():
    override = os.environ.get("EXPLAINER_FFMPEG")
    if override:
        return override if os.path.isfile(override) else None
    return shutil.which("ffmpeg")


def run_ffmpeg(binary, arguments, what):
    command = [binary, "-hide_banner", "-loglevel", "error", "-nostdin", "-y"] + arguments
    try:
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Fail("ffmpeg_failed", "%s: %s" % (what, exc))
    if proc.returncode != 0:
        raise Fail("ffmpeg_failed", "%s: %s" % (what, proc.stderr.decode("utf-8", "replace").strip()[-400:]))


def zoompan(move, frames, width, height, fps):
    """Slow pan or zoom over a still. The 2x pre-scale keeps zoompan's integer crop from jittering."""
    span = max(frames - 1, 1)
    if move == "in":
        zoom, x, y = "1+0.08*on/%d" % span, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif move == "out":
        zoom, x, y = "1.08-0.08*on/%d" % span, "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif move == "right":
        zoom, x, y = "1.08", "(iw-iw/zoom)*on/%d" % span, "ih/2-(ih/zoom/2)"
    else:
        zoom, x, y = "1.08", "(iw-iw/zoom)*(1-on/%d)" % span, "ih/2-(ih/zoom/2)"
    return ("scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos,crop=%d:%d,"
            "zoompan=z='%s':x='%s':y='%s':d=%d:s=%dx%d:fps=%d,setsar=1,format=yuv420p"
            % (width * 2, height * 2, width * 2, height * 2, zoom, x, y, frames, width, height, fps))


def block_command(state, block, width, height, fps, out):
    visual_s = block["visual_s"]
    audio = ("[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay=%d:all=1,apad,atrim=duration=%d[a]"
             % (int(round(state["lead_s"] * 1000)), visual_s))
    if uses_clip(block):
        video = ("[0:v]scale=%d:%d:force_original_aspect_ratio=decrease:flags=lanczos,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,"
                 "setsar=1,fps=%d,tpad=stop_mode=clone:stop_duration=%d,trim=duration=%d,setpts=PTS-STARTPTS,"
                 "format=yuv420p[v]" % (width, height, width, height, fps, visual_s, visual_s))
        source = block["clip"]["path"]
    else:
        video = "[0:v]%s[v]" % zoompan(block["move"], visual_s * fps, width, height, fps)
        source = block["keyframe"]["path"]
    return ["-i", source, "-i", block["audio"]["path"], "-filter_complex", "%s;%s" % (video, audio),
            "-map", "[v]", "-map", "[a]", "-t", str(visual_s), "-r", str(fps), "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", out]


def cmd_render(args):
    state = load_state(need_slug(args.slug))
    sync(state)
    label = state["slug"]
    match = re.fullmatch(r"(\d{3,4})x(\d{3,4})", args.size) if args.size else None
    if args.size and not match:
        raise Usage("--size looks like 1920x1080")
    width, height = (int(match.group(1)), int(match.group(2))) if match else RENDER_SIZE[state["aspect"]]
    if width % 2 or height % 2:
        raise Usage("--size needs even numbers")
    if not 12 <= args.fps <= 60:
        raise Usage("--fps must be between 12 and 60")
    if not 0 < args.music_volume <= 1:
        raise Usage("--music-volume must be above 0 and at most 1")
    if args.music and not os.path.isfile(args.music):
        raise Usage("--music not found: %s" % args.music)
    picked = parse_blocks_arg(args.blocks, len(state["blocks"]))
    blocks = [state["blocks"][i - 1] for i in picked] if picked else list(state["blocks"])
    unmeasured = [b["index"] for b in (state["blocks"] if args.final else blocks) if not b["visual_s"]]
    if unmeasured:
        raise Fail("gate", "audio not measured", blocks=unmeasured,
                   problems=["block %d: no measured narration, so its length is unknown" % i for i in unmeasured])
    total = float(sum(b["visual_s"] for b in state["blocks"])) if args.final else None
    if args.final:
        build_timeline(state)  # also refuses fit=grid overruns
    problems = []
    for block in blocks:
        source = block["clip"] if uses_clip(block) else block["keyframe"]
        if not (source.get("path") and os.path.isfile(source["path"])):
            problems.append("block %d: %s file is missing" % (block["index"], "clip" if uses_clip(block) else "keyframe"))
        if not (block["audio"].get("path") and os.path.isfile(block["audio"]["path"])):
            problems.append("block %d: narration file is missing" % block["index"])
    if problems:
        raise Fail("not_ready", "render needs the local files of every selected block", problems=problems)
    binary = find_ffmpeg()
    if not binary:
        raise Fail("ffmpeg_missing", "ffmpeg is not installed. The fal compose utility cannot rebuild this timeline; "
                   "ask the user to install ffmpeg (free) or deliver the approved parts and the SRT unassembled")
    def signature_of(block):
        source = block["clip"] if uses_clip(block) else block["keyframe"]
        return digest(source.get("path"), block["audio"].get("path"), block["audio"].get("duration_s"),
                      block["visual_s"], block["move"], width, height, args.fps, state["lead_s"])

    rendered, skipped = [], []
    for block in blocks:
        out = segment_path(label, block["index"])
        signature = signature_of(block)
        if not args.force and block.get("render", {}).get("sig") == signature and os.path.isfile(out):
            skipped.append(block["index"])
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        run_ffmpeg(binary, block_command(state, block, width, height, args.fps, out), "block %d" % block["index"])
        block["render"] = {"path": out, "sig": signature, "kind": "clip" if uses_clip(block) else "still"}
        rendered.append(block["index"])
        save_state(state)
    result = {"ok": True, "rendered": rendered, "skipped": skipped, "size": "%dx%d" % (width, height), "fps": args.fps}
    if not args.final:
        result["next"] = "render --final (add --music <file>) once every block is rendered"
        return result, 0
    stale = [b["index"] for b in state["blocks"]
             if not (b.get("render") and os.path.isfile(b["render"]["path"]) and b["render"].get("sig") == signature_of(b))]
    if stale:
        raise Fail("not_ready", "these blocks are not rendered with the current inputs, size and fps; "
                   "run render for them (or without --blocks) before --final", blocks=stale)
    list_path = out_dir(label, "blocks", "list.txt")
    write_file(list_path, "".join("file 'b%02d.mp4'\n" % b["index"] for b in state["blocks"]))
    cut = out_dir(label, "%s_cut.mp4" % label)
    run_ffmpeg(binary, ["-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", cut], "concat")
    loud = "loudnorm=I=%s:TP=-1.5:LRA=11" % args.lufs
    final = final_path(label)
    if args.music:
        fade_out = max(total - 2.0, 0)  # pyright: ignore[reportOptionalOperand] (set whenever --final is)
        bed = ("[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration=%.3f,volume=%.3f,"
               "afade=t=in:st=0:d=1,afade=t=out:st=%.3f:d=2[bed]" % (total, args.music_volume, fade_out))
        if args.no_duck:
            graph = "%s;[0:a][bed]amix=inputs=2:duration=first:normalize=0,%s[a]" % (bed, loud)
        else:
            graph = ("[0:a]asplit=2[vo][key];%s;[bed][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];"
                     "[vo][duck]amix=inputs=2:duration=first:normalize=0,%s[a]" % (bed, loud))
        arguments = ["-i", cut, "-stream_loop", "-1", "-i", args.music, "-filter_complex", graph,
                     "-map", "0:v:0", "-map", "[a]"]
    else:
        arguments = ["-i", cut, "-map", "0:v:0", "-map", "0:a:0", "-af", loud]
    arguments += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", "%.3f" % total,
                  "-movflags", "+faststart", final]
    run_ffmpeg(binary, arguments, "final mix")
    state["final"] = {"path": final, "total_s": total, "music": args.music, "ts": now()}
    save_state(state)
    result.update(final=final, cut=cut, total_s=total, music=bool(args.music), lufs=args.lufs,
                  next="frames.py probe and sheet the final, timeline --srt, pipeline.py add --step final, manifest")
    return result, 0


# ---------------------------------------------------------------- status
def next_step(state):
    blocks = state["blocks"]
    waiting = sorted({b[k]["job"] for b in blocks for k in KINDS
                      if b[k].get("status") in ("submitted", "cancel_requested", "submit_unknown")})
    if waiting:
        return ("jobs %s are not finished: run the same gm.py batch --plan again (it resumes, never resubmits); "
                "submit_unknown: check https://fal.ai/dashboard/requests first" % waiting)
    if not state["style"].get("text"):
        return "style --style-file: save the STYLE string"
    if any(not b["scene"] for b in blocks):
        return "visuals: every block needs a scene"
    if any("long" in b["flags"] for b in blocks):
        return "edit: shorten the blocks flagged long"
    report = length_report(state)
    problem = length_problem(report)
    if problem and report and not report["voiced_blocks"]:
        return "edit: " + problem
    if any(not is_approved(b, "script") for b in blocks) or state["approved"].get("style_text") != digest(state["style"]["text"]):
        return "CP1: show the outline card with all three tier estimates, then approve --stage outline --tier <the tier chosen>"
    if state["approved"].get("style") != style_digest(state) or not (state["style"].get("key_url") or state["style"].get("key_path")):
        return ("plan --stage stylekey and --stage audition, batch both, CP2, style --key-job, approve --stage style, "
                "approve --stage voice --voice <name>")
    if not state["approved"].get("voice"):
        return "CP2: the user picks a voice from the audition, then approve --stage voice --voice <name>"
    if any(not b["audio"] or b["audio"].get("status") in ("planned", "failed") for b in blocks):
        return "plan --stage narration (only the missing blocks are new jobs), then gm.py batch"
    if any(not b["audio"].get("duration_s") for b in blocks):
        return "measure: audiokit.py probe ... | set-audio --probe -   (or plan --stage probe)"
    if problem:
        return "edit: " + problem
    if any("over" in b["flags"] for b in blocks) and state.get("fit") == "grid":
        return "edit the blocks flagged over, re-plan their narration"
    if any(not is_approved(b, "audio") for b in blocks):
        return "CP3: report measured durations, ask the user to listen, then approve --stage narration"
    if any(not entry_done(b["keyframe"]) for b in blocks):
        return "plan --stage keyframes, gm.py batch, Read every image"
    if any(not is_approved(b, "keyframe") for b in blocks):
        return "CP4: show keyframes and the re-priced clip stage, then approve --stage keyframes"
    wanted = [] if state["tier"] == "animatic" else [b for b in blocks if b["animate"] or state["tier"] == "full"]
    if any(not entry_done(b["clip"]) for b in wanted):
        return "plan --stage clips (canary first when 4 or more), gm.py batch, frames.py sheet each clip"
    if any(not is_approved(b, "clip") for b in wanted):
        return "CP5: show the clip sheets, then approve --stage clips"
    if not state.get("final"):
        return "music (optional) at timeline total_ms, then render --final (needs local ffmpeg), timeline --srt"
    return "final gate: frames.py probe and sheet, pipeline.py add --step final, pipeline.py manifest, deliver"


def cmd_status(args):
    state = load_state(need_slug(args.slug))
    sync(state)
    save_state(state)
    blocks = state["blocks"]
    table = []
    for block in blocks:
        table.append({"index": block["index"], "words": block["words"], "est_s": block["est_s"],
                      "audio_s": block["audio"].get("duration_s"), "visual_s": block["visual_s"],
                      "animate": block["animate"], "flags": block["flags"],
                      "audio": block["audio"].get("status"), "keyframe": block["keyframe"].get("status"),
                      "clip": block["clip"].get("status"), "rendered": bool(block.get("render")),
                      "stale": [k for k in ("keyframe", "clip") if block[k].get("stale")],
                      "approved": [k for k in ("script", "audio", "keyframe", "clip") if is_approved(block, k)],
                      "jobs": {k: block[k].get("job") for k in KINDS if block[k].get("job")},
                      "paths": {k: block[k].get("path") for k in KINDS if block[k].get("path")}})
    lengths = [b["visual_s"] or state["block_s"] for b in blocks]
    animated = [length for b, length in zip(blocks, lengths) if b["animate"]]
    total = sum(lengths)
    return {"ok": True, "slug": state["slug"], "title": state["title"], "lang": state["lang"], "tier": state["tier"],
            "aspect": state["aspect"], "fit": state.get("fit"), "block_s": state["block_s"], "length": length_report(state),
            "style": {"name": state["style"].get("name"), "has_text": bool(state["style"].get("text")),
                      "key_path": state["style"].get("key_path"), "key_url": bool(state["style"].get("key_url")),
                      "approved": state["approved"].get("style") == style_digest(state)},
            "voice": state["approved"].get("voice"),
            "quantities": {"blocks": len(blocks), "stills": len(blocks) + 1,
                           "narration_chars": sum(b["chars"] for b in blocks),
                           "total_s": total, "animated_blocks": len(animated), "animated_s": sum(animated),
                           "music_minutes": int(math.ceil(total / 60.0)),
                           "measured": all(b["visual_s"] for b in blocks)},
            "blocks": table, "final": state.get("final"), "next": next_step(state)}, 0


# ---------------------------------------------------------------- cli
class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Usage(message)


def build_parser():
    parser = Parser(prog="explainer.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>", parser_class=Parser)
    sub.required = True

    def add(name, func, text):
        item = sub.add_parser(name, help=text)
        item.add_argument("--slug", required=True)
        item.set_defaults(func=func)
        return item

    p = add("init", cmd_init, "script text -> sized blocks; creates the block ledger")
    p.add_argument("--script", required=True)
    p.add_argument("--title")
    p.add_argument("--lang", default="en")
    p.add_argument("--minutes", type=float)
    p.add_argument("--blocks", type=int)
    p.add_argument("--block-s", type=int, default=10)
    p.add_argument("--length-s", metavar="MAX|MIN-MAX", help="the length the user asked for, e.g. 15 or 30-40")
    p.add_argument("--wps", type=float)
    p.add_argument("--lead-s", type=float, default=0.4)
    p.add_argument("--tail-s", type=float, default=0.6)
    p.add_argument("--aspect", default="16:9")
    p.add_argument("--tier", choices=("animatic", "hybrid", "full"), default="hybrid")
    p.add_argument("--fit", choices=("audio", "grid"), default="audio")
    p.add_argument("--split", choices=("auto", "paragraph", "sentence"), default="auto")
    p.add_argument("--force", action="store_true")

    p = add("edit", cmd_edit, "replace one block's narration (resets its audio and approvals)")
    p.add_argument("--block", type=int, required=True)
    p.add_argument("--narration-file", required=True)

    p = add("style", cmd_style, "record the STYLE string and the style-key image")
    p.add_argument("--name")
    p.add_argument("--style-file")
    p.add_argument("--negative-file")
    p.add_argument("--key-job")
    p.add_argument("--key-path")
    p.add_argument("--key-url")
    p.add_argument("--ref-url", action="append")

    p = add("visuals", cmd_visuals, "scene, motion, move and animate per block from a JSON list")
    p.add_argument("--input", required=True)

    p = add("attach", cmd_attach, "use a file made elsewhere as a block's audio, keyframe or clip")
    p.add_argument("--block", type=int, required=True)
    p.add_argument("--kind", choices=KINDS, required=True)
    p.add_argument("--path", required=True)
    p.add_argument("--url")

    p = add("approve", cmd_approve, "record the user's approval of a checkpoint")
    p.add_argument("--stage", choices=APPROVE_STAGES, required=True)
    p.add_argument("--blocks")
    p.add_argument("--note")
    p.add_argument("--tier", choices=("animatic", "hybrid", "full"))
    p.add_argument("--voice")

    p = add("set-audio", cmd_set_audio, "record measured narration durations; they set the visual lengths")
    p.add_argument("--probe")
    p.add_argument("--batch-result")
    p.add_argument("--block", type=int)
    p.add_argument("--duration", type=float)
    p.add_argument("--path")
    p.add_argument("--url")

    p = add("plan", cmd_plan, "write a gm.py batch plan for one stage, all or selected blocks")
    p.add_argument("--stage", choices=STAGES, required=True)
    p.add_argument("--endpoint")
    p.add_argument("--blocks")
    p.add_argument("--reroll", action="store_true")
    p.add_argument("--base-input")
    p.add_argument("--out")
    p.add_argument("--max-parallel", type=int)
    p.add_argument("--text-field")
    p.add_argument("--voice-field", default="voice")
    p.add_argument("--voices")
    p.add_argument("--text-file")
    p.add_argument("--prompt-file")
    p.add_argument("--refs-field", default="image_urls")
    p.add_argument("--size-field")
    p.add_argument("--allow-text", action="store_true")
    p.add_argument("--image-field")
    p.add_argument("--duration-field", default="duration")
    p.add_argument("--duration-type", choices=("int", "str"))
    p.add_argument("--min-s", type=int)
    p.add_argument("--max-s", type=int)
    p.add_argument("--price-per-1k", type=float)
    p.add_argument("--price-per-image", type=float)
    p.add_argument("--price-per-second", type=float)

    p = add("timeline", cmd_timeline, "block timings -> SRT, ffmpeg concat list")
    p.add_argument("--srt")
    p.add_argument("--concat")
    p.add_argument("--compose", help="refused: fal compose cannot rebuild the timeline")
    p.add_argument("--max-chars", type=int, default=42)
    p.add_argument("--max-lines", type=int, default=2)

    p = add("render", cmd_render, "local ffmpeg: per-block segments, then the final file")
    p.add_argument("--blocks")
    p.add_argument("--final", action="store_true")
    p.add_argument("--size")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--music")
    p.add_argument("--music-volume", type=float, default=0.25)
    p.add_argument("--no-duck", action="store_true")
    p.add_argument("--lufs", type=float, default=-16.0)
    p.add_argument("--force", action="store_true")

    add("status", cmd_status, "per-block table, quantities for pricing, next step")
    return parser


def emit(doc):
    sys.stdout.write(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        doc, code = args.func(args)
    except Usage as exc:
        emit({"ok": False, "kind": "usage", "message": str(exc)})
        return 2
    except Fail as exc:
        emit(dict({"ok": False, "kind": exc.kind, "message": str(exc)}, **exc.extra))
        return 1
    emit(doc)
    return code


if __name__ == "__main__":
    sys.exit(main())
