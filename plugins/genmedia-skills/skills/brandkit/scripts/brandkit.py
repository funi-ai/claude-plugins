#!/usr/bin/env python3
"""brandkit.py - approval ledger, review boards and SVG hygiene for a staged brand identity.
Python 3.8+, stdlib only, no network, no paid calls. Prints ONE compact JSON object on stdout.
Exit: 0 ok | 1 failed | 2 usage.

State lives in the project cwd: .genmedia/projects/<brand>/brandkit/state.json (atomic writes, a version
counter, never hand-edited). Review boards, the brandbook and the package go to genmedia-output/<brand>/.

  tools
      Which converter exists: a Chromium-family browser (PNG + PDF) or macOS qlmanage (PNG fallback).
  init --brand "<Brand Name>"
  status [--brand <slug>]
      Slots, approved revisions, open candidates, re-rolls left, invalidated slots, stale assets, `next`.
  add-candidate --brand <slug> --slot <slot> --id <id> [--file <path>]... [--data <file.json>]
      [--prompt-file <txt> | --plan-file <plan.json> [--job <id>]] [--origin generated|local|user]
      [--expect-text-file <txt> --read-text-file <txt> | --no-text]
      [--endpoint <id>] [--request-id <id>] [--cost <usd>] [--note <text>]
      Slots: strategy, palette, logo, typography, app-<name> (lock and brandbook register themselves).
      Stage order is enforced: logo needs an approved palette, app-* an approved lock (origin user is
      exempt). Refuses wrong text, an unchanged prompt, duplicate ideas, unsafe SVG, a missing lock.
  new-round --brand <slug> --slot <slot> --change "<what is different>" [--user-asked "<their words>"]
      A re-roll: closes the open round, opens r<n+1>. At most 2 per slot unless the user asked.
  add-asset --brand <slug> --slot <slot> --role <role> --file <path>
      Production file derived from the APPROVED revision (recoloured logo, mono, PNG size, icon, PDF). Logo SVG
      roles must keep the approved geometry; clearing or deleting the full-canvas background plate is allowed.
  approve --brand <slug> --slot <slot> --candidate <id> --note "<the user's own words>" [--revision N]
      Returns `invalidated`: downstream slots built from another revision. Nothing is regenerated.
  invalidate --brand <slug> --slot <slot> --reason "<text>"
  lock --brand <slug> [--data <lock.json>] [--out <file>]
      With --data: compose the BRAND LOCK block from the approved slots and register it as a candidate.
      Without: print the APPROVED block (fails while the lock is unapproved or invalidated).
  plan --brand <slug> --spec <spec.json> --out <plan.json>
      Build a gm.py batch plan from prompt FILES before anything is paid: jobs carry `prompt_file` instead of
      input.prompt; in app-* prompts the line {{BRAND_LOCK}} becomes the approved block, verbatim. Refuses a
      wrong round number, an unapproved lock or palette, leftover placeholders, duplicate or unchanged prompts
      and a job id the run ledger already knows with another prompt.
  board --brand <slug> --slot <slot> [--slot <slot>...] [--revision N] [--out <file.html>] [--png] [--webfonts]
  book --brand <slug> [--out <dir>] [--pdf]
      Built from approved slots only, so it inherits their approval (status approved, derived): no separate review.
  export-list --brand <slug> [--out <dir>] [--copy]
  palette-check --input <palette.json>
  text-check (--expected-file <txt> | --expected "<s>") (--read-file <txt> | --read "<s>")
  svg-check <file.svg> [--palette <palette.json>]
  svg-recolor <in.svg> --out <out.svg> --map "#from=#to" [--map ...] [--transparent-background]
  svg-variants <in.svg> --out-dir <dir> [--ink "#111111"] [--paper "#ffffff"] [--keep-background]
  icon <logo.svg> --out <icon.svg> --background "#hex" [--padding 0.2] [--radius 0.22]
  png <in.svg|in.html> --out <file.png> [--size N | --width W --height H] [--background transparent|"#hex"]
  icon-export <icon.svg> [--brand <slug>] [--out-dir <dir>] [--platform ios|play|android|web|macos]...
      [--background "#hex"] [--padding 0.18] [--name "<App Name>"] [--short-name "<Short>"] [--jobs 4]
      Platform files from ONE approved icon, never regenerated per size: the plate colour and the untouched
      mark are split, the mark's ink is measured in rendered pixels, and every file is a browser render of
      the same geometry. ios: opaque 1024 master without an alpha channel. play: 512 with alpha, full square.
      android: adaptive foreground and monochrome layers per density, plate colour resource, XML. web:
      favicon.ico (PNG entries), favicon.svg, apple-touch-icon, any and maskable PWA icons, manifest and link
      snippet. macos: AppIcon.iconset (+ AppIcon.icns when iconutil exists). Sizes and safe zones come from
      scripts/icon-targets.json (dated, with source URLs). Checks: exact size, alpha as the platform demands,
      byte cap, ink inside the adaptive and maskable safe circles. Writes icon-export.json and
      icon-sheet.png (256 down to 16 px on light and dark, platform masks). With --brand the input must be the
      approved `app-icon` file and the export is attached to that slot. Needs a Chromium-family browser.
  sting <logo.svg> --out <file.mp4> --background "#hex" [--brand <slug>] [--size 1920x1080] [--seconds 2.5]
      [--fps 30] [--style rise|pop|wipe] [--span 0.5] [--keep-frames] [--jobs 4]
      A short logo reveal for intros and end cards. Every frame is the real SVG under a transform, an opacity
      or a clip, rendered by the browser; ffmpeg joins the frames. No model redraws the mark. Silent.

Never depends on Pillow, ImageMagick, rsvg-convert or LibreOffice. Without a converter `png`, `icon-export`,
`sting` and `book --pdf` answer kind "tool_missing": deliver SVG and HTML and say so.
Env: GM_BROWSER_BIN, GM_QLMANAGE_BIN, GM_FFMPEG_BIN, GM_ICONUTIL_BIN (binary override; "none" disables that tool).
"""
import argparse
import base64
import concurrent.futures
import copy
import datetime
import difflib
import hashlib
import html
import json
import math
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import unicodedata
import xml.etree.ElementTree as ET
import zlib

SCHEMA = 1
HERE = os.path.dirname(os.path.abspath(__file__))
TR_ASCII = str.maketrans("ıİşŞğĞüÜöÖçÇ", "iIsSgGuUoOcC")  # same folding as gm.py: labels become folder names
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
MAX_SVG_BYTES = 8 * 1024 * 1024  # vector model outputs of 1-2 MB are normal
BROWSER_TIMEOUT_S = 60
FOUNDATION = ["strategy", "palette", "logo", "typography", "lock"]
DEPS = {"strategy": [], "palette": ["strategy"], "logo": ["strategy", "palette"], "typography": ["strategy"],
        "lock": ["strategy", "palette", "logo", "typography"]}
STAGE_GATE = {"logo": ["palette"], "brandbook": ["lock"]}  # add-candidate refuses until these are approved
LETTERED = {"palette": "palette", "logo": "logo", "typography": "type"}
ORIGINS = ("generated", "local", "user")
MAX_REROLLS = 2
LOCK_TOKEN = "{{BRAND_LOCK}}"  # `plan` replaces this line of a prompt file with the approved block, verbatim
JOB_ID = re.compile(r"(?:(?P<logo>logo-[A-F])|(?P<app>app-[a-z0-9]+(?:-[a-z0-9]+)*)(?:-(?P<letter>[A-F]))?)"
                    r"-r(?P<rev>[1-9][0-9]?)(?:-t[23])?")
PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}|<[A-Za-z][^<>\n]{0,60}>|\{[A-Z_]{3,}\}")
ROLES = ("primary", "secondary", "accent", "background", "surface", "text", "neutral", "support")
GENERIC_FONTS = ("serif", "sans-serif", "monospace", "cursive", "system-ui")
PAINT_ATTRS = ("fill", "stroke", "stop-color", "flood-color", "lighting-color", "color")
GEOMETRY_ATTRS = ("d", "points", "x", "y", "width", "height", "cx", "cy", "r", "rx", "ry", "x1", "y1", "x2", "y2",
                  "transform", "viewBox", "gradientTransform", "gradientUnits", "offset", "fx", "fy",
                  "preserveAspectRatio", "patternTransform", "clip-path", "mask")
SHAPES = ("path", "rect", "circle", "ellipse", "polygon", "polyline", "line")
FORBIDDEN_ELEMENTS = ("script", "foreignObject", "iframe", "object", "embed", "audio", "video", "handler", "set",
                      "animate", "animateTransform", "animateMotion")  # a mark is static: animation can rewrite href
NAMED_COLORS = {"black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000", "blue": "#0000ff",
                "yellow": "#ffff00", "gray": "#808080", "grey": "#808080", "silver": "#c0c0c0", "maroon": "#800000",
                "purple": "#800080", "fuchsia": "#ff00ff", "lime": "#00ff00", "olive": "#808000", "navy": "#000080",
                "teal": "#008080", "aqua": "#00ffff", "orange": "#ffa500"}
NON_COLORS = ("none", "transparent", "currentcolor", "inherit", "initial", "unset", "context-fill", "context-stroke")
EDITABLE_EXT = (".svg", ".html", ".css", ".json", ".txt", ".md")
BROWSER_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge",
                 "microsoft-edge", "brave-browser")
BROWSER_PATHS = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium",
                 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                 "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                 "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                 "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe")
PNG_SIG = b"\x89PNG\r\n\x1a\n"
ICON_PLATFORMS = ("ios", "play", "android", "web", "macos")
MEASURE_PX = 256            # the mark is measured on a render of this size: one pixel is 0.4 percent of the side
ALPHA_FLOOR = 8             # alpha at or below this is an antialias fringe, not ink
ALPHA_TABLE = bytes(1 if value > ALPHA_FLOOR else 0 for value in range(256))
SHEET_SIZES = (256, 128, 64, 48, 32, 16)
STING_STYLES = ("rise", "pop", "wipe")
STING_IN_S = 0.9            # the reveal; the rest of the clip holds the finished logo
MISSING_HINT = ("no Chromium-family browser (and no macOS qlmanage for PNG): deliver the SVG files and the HTML "
                "board or book as they are and say that PNG or PDF export was not possible on this machine")

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


class Fail(Exception):
    def __init__(self, kind, message, hint=None, code=1, extra=None):
        Exception.__init__(self, message)
        self.kind, self.message, self.hint, self.code, self.extra = kind, message, hint, code, extra or {}


def emit(obj, code=0):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False) + "\n")
    sys.stdout.flush()
    return code


def usage(message):
    return Fail("usage", message, code=2)


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slug(text, fallback="brand"):
    folded = unicodedata.normalize("NFKD", str(text or "").translate(TR_ASCII))
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return re.sub(r"[^A-Za-z0-9._-]+", "-", folded).strip("-.") or fallback


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prompt_hash(text):
    """One normal form for prompts, so a prompt file and the same prompt inside a plan hash alike."""
    return sha256_text(text.replace("\r\n", "\n").strip())


def read_text_file(path, what):
    try:
        with open(path, "rb") as handle:
            return handle.read().decode("utf-8-sig")
    except OSError as exc:
        raise usage("cannot read %s %r: %s" % (what, path, exc.strerror or exc))
    except UnicodeDecodeError:
        raise usage("%s %r is not UTF-8 text" % (what, path))


def read_json_file(path, what):
    try:
        value = json.loads(read_text_file(path, what))
    except ValueError as exc:
        raise usage("%s %r is not valid JSON: %s" % (what, path, exc))
    if not isinstance(value, dict):
        raise usage("%s %r must be a JSON object" % (what, path))
    return value


def rel(path):
    """Paths inside the project are stored relative to the cwd so the ledger survives a moved folder."""
    absolute = os.path.abspath(path)
    try:
        relative = os.path.relpath(absolute, os.getcwd())
    except ValueError:
        return absolute
    return absolute if relative.startswith(os.pardir) else relative


def write_atomic(path, data):
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    handle, temp = tempfile.mkstemp(prefix=".tmp-", dir=folder)
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data if isinstance(data, bytes) else data.encode("utf-8"))
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
    except BaseException:
        if os.path.exists(temp):
            os.remove(temp)
        raise


# ----------------------------------------------------------------------------------------------- state

def project_dir(brand):
    return os.path.join(".genmedia", "projects", brand, "brandkit")


def state_path(brand):
    return os.path.join(project_dir(brand), "state.json")


def output_dir(brand):
    return os.path.join("genmedia-output", brand)


def resolve_brand(value):
    if value:
        return slug(value)
    root = os.path.join(".genmedia", "projects")
    found = sorted(name for name in (os.listdir(root) if os.path.isdir(root) else [])
                   if os.path.isfile(state_path(name)))
    if len(found) == 1:
        return found[0]
    raise usage("--brand is required (%s)" % ("ledgers here: " + ", ".join(found) if found else "no ledger here: run init"))


def new_slot():
    return {"status": "draft", "approved_revision": None, "revisions": [], "assets": [], "rerolls": 0, "attempts": {}}


def load_state(brand):
    path = state_path(brand)
    if not os.path.isfile(path):
        raise Fail("no_state", "no ledger at %s" % path,
                   hint="run init; if the conversation claims earlier approvals, stop and ask the user")
    try:
        with open(path, "rb") as handle:
            state = json.loads(handle.read().decode("utf-8"))
    except ValueError as exc:
        raise Fail("state_corrupt", "%s is not valid JSON: %s" % (path, exc), hint="never hand-edit state.json")
    if not isinstance(state, dict) or (state.get("schema") == SCHEMA and not (
            isinstance(state.get("slots"), dict) and isinstance(state.get("brand"), dict) and state["brand"].get("slug")
            and all(isinstance(v, dict) and isinstance(v.get("revisions"), list) and "status" in v for v in state["slots"].values()))):
        raise Fail("state_corrupt", "%s does not have the shape this script writes" % path, hint="never hand-edit state.json")
    if state.get("schema") != SCHEMA:
        raise Fail("state_schema", "%s has schema %r, this script writes %r" % (path, state.get("schema"), SCHEMA))
    for name, slot_state in state["slots"].items():
        if slot_state["status"] == "approved":
            require_approved(state, name)
    return state


def save_state(state, read_version):
    path = state_path(state["brand"]["slug"])
    if os.path.isfile(path):
        with open(path, "rb") as handle:
            on_disk = json.loads(handle.read().decode("utf-8")).get("version")
        if on_disk != read_version:
            raise Fail("state_conflict", "state.json changed while this command ran (version %r, expected %r)"
                       % (on_disk, read_version), hint="run the command again; one writer at a time")
    state["version"] = int(state.get("version") or 0) + 1
    state["updated_at"] = now()
    write_atomic(path, json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def log(state, action, slot=None, **fields):
    entry = {"ts": now(), "action": action}
    if slot:
        entry["slot"] = slot
    entry.update({k: v for k, v in fields.items() if v is not None})
    state.setdefault("log", []).append(entry)


def check_slot_name(name):
    if name in FOUNDATION or name == "brandbook" or re.fullmatch(r"app-[a-z0-9]+(-[a-z0-9]+)*", name or ""):
        return name
    raise usage("slot must be one of %s, brandbook or app-<name> (lowercase, hyphens)" % ", ".join(FOUNDATION))


def deps_of(state, slot):
    if slot in DEPS:
        return list(DEPS[slot])
    if slot == "brandbook":
        return ["lock"] + sorted(name for name, value in state["slots"].items()
                                 if name.startswith("app-") and value.get("approved_revision"))
    return ["lock"]


def closure(state, slot):
    seen, queue = [], deps_of(state, slot)
    while queue:
        name = queue.pop(0)
        if name not in seen:
            seen.append(name)
            queue.extend(deps_of(state, name))
    return seen


def current_revision(slot_state):
    return slot_state["revisions"][-1] if slot_state["revisions"] else None


def approved_candidate(slot_state):
    number = slot_state.get("approved_revision")
    for revision in slot_state["revisions"]:
        if revision["rev"] == number:
            for candidate in revision["candidates"]:
                if candidate["id"] == revision.get("approved_candidate"):
                    return revision, candidate
    return None, None


def require_approved(state, slot):
    """(revision, candidate) of a slot already known to be approved; a dangling approval is a damaged ledger."""
    revision, candidate = approved_candidate(state["slots"].get(slot) or new_slot())
    if revision is None or candidate is None:
        raise Fail("state_corrupt", "slot %s is marked approved but its approved candidate is missing" % slot,
                   hint="never hand-edit state.json")
    return revision, candidate


def stamp_built_from(state, slot, origin):
    if origin == "user" and slot in ("palette", "logo", "typography", "strategy"):
        return {}  # official assets are authoritative: no upstream change can make them stale
    stamp = {}
    for name in closure(state, slot):
        number = state["slots"].get(name, {}).get("approved_revision")
        if number:
            stamp[name] = number
    return stamp


def mark_invalid(state, name, cause):
    slot_state = state["slots"][name]
    revision = current_revision(slot_state)
    if revision is None or slot_state["status"] == "invalidated":
        return False
    revision["status"] = "invalidated"
    slot_state.update({"status": "invalidated", "approved_revision": None, "rerolls": 0, "attempts": {},
                       "invalidated": {"by": cause, "ts": now(), "was_revision": revision["rev"]}})
    return True


def propagate(state, changed):
    """Downstream slots record the upstream revisions they were built from; a different one makes them stale."""
    invalidated, queue = [], [changed]
    while queue:
        source = queue.pop(0)
        approved = state["slots"][source].get("approved_revision")
        for name, slot_state in state["slots"].items():
            revision = current_revision(slot_state)
            if name == source or revision is None or slot_state["status"] == "invalidated":
                continue
            built = revision.get("built_from", {}).get(source)
            if built is not None and built != approved and mark_invalid(state, name, source):
                invalidated.append(name)
                queue.append(name)
    return invalidated


def stage_order(state):
    apps = sorted(name for name in state["slots"] if name.startswith("app-"))
    return FOUNDATION + apps + ["brandbook"]


def next_step(state):
    for name in stage_order(state):
        slot_state = state["slots"].get(name) or new_slot()
        revision = current_revision(slot_state)
        if slot_state["status"] == "invalidated":
            return {"slot": name, "do": "rebuild or re-approve after telling the user what became stale"}
        if revision and revision["status"] == "candidate":
            return {"slot": name, "do": "review is open: show the board, stop, wait for the user's decision"}
        if slot_state["status"] != "approved" and name in FOUNDATION:
            return {"slot": name, "do": "create candidates, show them, stop"}
    return {"slot": None, "do": "every registered slot is approved: add applications, build the book or hand off"}


def stale_assets(state):
    stale = []
    for name, slot_state in state["slots"].items():
        for asset in slot_state.get("assets", []):
            reasons = []
            if asset.get("from_revision") != slot_state.get("approved_revision"):
                reasons.append("%s revision changed" % name)
            for upstream, number in (asset.get("upstream") or {}).items():
                if state["slots"].get(upstream, {}).get("approved_revision") != number:
                    reasons.append("%s revision changed" % upstream)
            if not os.path.isfile(asset["path"]):
                reasons.append("file missing")
            if reasons:
                stale.append({"slot": name, "role": asset["role"], "path": asset["path"], "why": reasons})
    return stale


def summary(state):
    slots = {}
    for name in stage_order(state):
        slot_state = state["slots"].get(name)
        if slot_state is None:
            slots[name] = {"status": "draft"}
            continue
        revision = current_revision(slot_state)
        row = {"status": slot_state["status"], "approved_revision": slot_state.get("approved_revision"),
               "rerolls_left": MAX_REROLLS - int(slot_state.get("rerolls") or 0)}
        _, chosen = approved_candidate(slot_state)
        if chosen:
            row["approved_candidate"] = chosen["id"]
        if revision and revision["status"] == "candidate":
            row["open_revision"] = revision["rev"]
            row["candidates"] = [c["id"] for c in revision["candidates"]]
        if slot_state.get("invalidated") and slot_state["status"] == "invalidated":
            row["invalidated_by"] = slot_state["invalidated"]["by"]
        if slot_state.get("assets"):
            row["assets"] = [a["role"] for a in slot_state["assets"]]
        slots[name] = row
    result = {"ok": True, "brand": state["brand"], "version": state["version"], "slots": slots,
              "invalidated": [n for n, s in state["slots"].items() if s["status"] == "invalidated"],
              "stale_assets": stale_assets(state), "next": next_step(state),
              "state": state_path(state["brand"]["slug"]), "output_dir": output_dir(state["brand"]["slug"])}
    _, palette = approved_candidate(state["slots"].get("palette") or new_slot())
    if palette:
        result["palette"] = [{"hex": c["hex"], "role": c["role"], "name": c.get("name"), "rgb": c["rgb"]}
                             for c in palette["data"]["colors"]]
    return result


# ----------------------------------------------------------------------------------------------- colour

def parse_color(value):
    """-> '#rrggbb' (lowercase), or None when the value is not a plain colour (none, url(#g), currentColor)."""
    text = (value or "").strip().lower()
    if not text or text in NON_COLORS or text.startswith("url(") or text.startswith("var("):
        return None
    if text in NAMED_COLORS:
        return NAMED_COLORS[text]
    match = re.fullmatch(r"#([0-9a-f]{3,8})", text)
    if match:
        digits = match.group(1)
        if len(digits) in (3, 4):
            return "#" + "".join(ch * 2 for ch in digits[:3])
        if len(digits) in (6, 8):
            return "#" + digits[:6]
        return None
    match = re.fullmatch(r"rgba?\(\s*([0-9.]+%?)\s*[, ]\s*([0-9.]+%?)\s*[, ]\s*([0-9.]+%?)\s*(?:[,/]\s*[0-9.]+%?\s*)?\)", text)
    if match:
        parts = []
        for token in match.groups():
            number = float(token[:-1]) * 2.55 if token.endswith("%") else float(token)
            parts.append(max(0, min(255, int(round(number)))))
        return "#%02x%02x%02x" % tuple(parts)
    return "?" + text  # a colour keyword this script does not know: reported, never substituted


def strict_hex(value, what):
    parsed = parse_color(value)
    if not parsed or parsed.startswith("?") or not re.fullmatch(r"\s*#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?\s*", str(value)):
        raise usage("%s must be a hex colour like #1f3d2b, got %r" % (what, value))
    return parsed


def rgb_of(hex_color):
    return {"r": int(hex_color[1:3], 16), "g": int(hex_color[3:5], 16), "b": int(hex_color[5:7], 16)}


def luminance(hex_color):
    def channel(value):
        value /= 255.0
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4
    rgb = rgb_of(hex_color)
    return 0.2126 * channel(rgb["r"]) + 0.7152 * channel(rgb["g"]) + 0.0722 * channel(rgb["b"])


def contrast(first, second):
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def grade(ratio):
    return "AAA" if ratio >= 7 else "AA" if ratio >= 4.5 else "AA-large" if ratio >= 3 else "fail"


def distance(first, second):
    a, b = rgb_of(first), rgb_of(second)
    return math.sqrt(sum((a[k] - b[k]) ** 2 for k in "rgb"))


def check_palette(data):
    problems, notes = [], []
    colors = data.get("colors")
    if not isinstance(colors, list) or not 3 <= len(colors) <= 8:
        raise usage("palette needs `colors`: a list of 3 to 8 {hex, name, role} objects")
    normal = []
    for index, item in enumerate(colors):
        if not isinstance(item, dict):
            raise usage("colors[%d] must be an object" % index)
        hex_color = strict_hex(item.get("hex"), "colors[%d].hex" % index)
        role = str(item.get("role") or "").strip().lower()
        if role not in ROLES:
            raise usage("colors[%d].role must be one of %s" % (index, ", ".join(ROLES)))
        normal.append({"hex": hex_color, "name": str(item.get("name") or hex_color).strip(), "role": role,
                       "rgb": rgb_of(hex_color), "use": str(item.get("use") or "").strip() or None})
    hexes = [c["hex"] for c in normal]
    for hex_color in sorted(set(h for h in hexes if hexes.count(h) > 1)):
        problems.append("%s appears twice" % hex_color)
    by_role = {role: [c for c in normal if c["role"] == role] for role in ROLES}
    if len(by_role["primary"]) != 1:
        problems.append("exactly one colour must have the role primary (found %d)" % len(by_role["primary"]))
    for role in ("background", "text"):
        if not by_role[role]:
            problems.append("no colour has the role %s" % role)
    pairs = []
    for i, first in enumerate(normal):
        for second in normal[i + 1:]:
            ratio = contrast(first["hex"], second["hex"])
            pairs.append({"a": first["hex"], "b": second["hex"], "ratio": round(ratio, 2), "grade": grade(ratio)})
            if distance(first["hex"], second["hex"]) < 18 and first["hex"] != second["hex"]:
                notes.append("%s and %s are nearly identical: merge them or push them apart" % (first["hex"], second["hex"]))
    for text in by_role["text"]:
        for ground in by_role["background"] + by_role["surface"]:
            ratio = contrast(text["hex"], ground["hex"])
            if ratio < 4.5:
                problems.append("text %s on %s %s is %.2f:1, below 4.5:1 for body text" % (text["hex"], ground["role"], ground["hex"], ratio))
    for accent in by_role["primary"] + by_role["accent"] + by_role["secondary"]:
        for ground in by_role["background"]:
            ratio = contrast(accent["hex"], ground["hex"])
            if ratio < 3:
                notes.append("%s %s on background %s is %.2f:1: shapes only, never text or thin lines" % (accent["role"], accent["hex"], ground["hex"], ratio))
    for item in normal:
        item["label"] = "#000000" if contrast(item["hex"], "#000000") >= contrast(item["hex"], "#ffffff") else "#ffffff"
    text_pairs = sorted((p for p in pairs if p["ratio"] >= 4.5), key=lambda p: -p["ratio"])
    return {"name": str(data.get("name") or "").strip() or None, "rationale": str(data.get("rationale") or "").strip() or None,
            "colors": normal, "pairs": pairs, "text_pairs": text_pairs[:6], "problems": problems, "notes": notes}


# ----------------------------------------------------------------------------------------------- text

def text_lines(text):
    lines = []
    for raw in unicodedata.normalize("NFC", text or "").replace("\r", "\n").split("\n"):
        line = " ".join(raw.split())
        if line:
            lines.append(line)
    return lines


def compare_text(expected, read):
    want, got = text_lines(expected), text_lines(read)
    missing, extra = list(want), []
    for line in got:
        if line in missing:
            missing.remove(line)
        else:
            extra.append(line)
    diffs = []
    for line in missing:
        close = difflib.get_close_matches(line, extra, n=1, cutoff=0.5)
        entry = {"expected": line, "closest_read": close[0] if close else None}
        if close:
            other = close[0]
            index = next((i for i, (a, b) in enumerate(zip(line, other)) if a != b), min(len(line), len(other)))
            entry["first_difference_at"] = index + 1
            entry["expected_char"] = "%s U+%04X" % (line[index], ord(line[index])) if index < len(line) else "(end)"
            entry["read_char"] = "%s U+%04X" % (other[index], ord(other[index])) if index < len(other) else "(end)"
        diffs.append(entry)
    return {"ok": not missing and not extra, "expected": want, "read": got, "missing": missing,
            "unexpected": extra, "diff": diffs}


# ----------------------------------------------------------------------------------------------- svg

def local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def load_svg(path):
    if not os.path.isfile(path):
        raise usage("no such file: %s" % path)
    size = os.path.getsize(path)
    if size > MAX_SVG_BYTES:
        raise Fail("svg_too_large", "%s is %d bytes (limit %d)" % (path, size, MAX_SVG_BYTES))
    with open(path, "rb") as handle:
        raw = handle.read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff") or b"\x00" in raw[:4096]:
        raise Fail("svg_unsafe", "%s is not UTF-8 text (UTF-16/32 or binary): its content cannot be screened" % path,
                   extra={"reasons": ["not UTF-8"]})
    text = raw.decode("utf-8-sig", errors="replace")
    if re.search(r"<!ENTITY", text, re.I):
        raise Fail("svg_unsafe", "%s declares XML entities" % path, extra={"reasons": ["entity declaration"]})
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise Fail("svg_invalid", "%s is not well-formed XML: %s" % (path, exc),
                   hint="a truncated download or an HTML error page; fetch the file again")
    if local(root.tag) != "svg":
        raise Fail("svg_invalid", "%s: the root element is <%s>, not <svg>" % (path, local(root.tag)))
    return root, size


def style_declarations(text):
    for match in re.finditer(r"([a-zA-Z-]+)\s*:\s*([^;{}]+)", text or ""):
        yield match.group(1).strip().lower(), match.group(2).strip()


def unsafe_reasons(root):
    reasons = []
    for element in root.iter():
        name = local(element.tag)
        if name in FORBIDDEN_ELEMENTS:
            reasons.append("<%s> element" % name)
        for key, value in element.attrib.items():
            attr = local(key)
            if attr.lower().startswith("on"):
                reasons.append("event handler %s on <%s>" % (attr, name))
            if attr == "href" and not value.strip().startswith("#"):
                kind = "embedded raster image" if value.strip().lower().startswith("data:image") else "external reference"
                reasons.append("%s in <%s>" % (kind, name))
            if re.search(r"url\(\s*['\"]?(?!#)", value):
                reasons.append("external url() in attribute %s" % attr)
            if re.match(r"\s*(javascript|vbscript)\s*:", value, re.I):
                reasons.append("script URL in attribute %s" % attr)
        if name == "style" and re.search(r"@import|url\(\s*['\"]?(?!#)", element.text or ""):
            reasons.append("@import or external url() in <style>")
    return sorted(set(reasons))


def iter_paints(root):
    """Yield (element, where, key, raw value) for every paint: attributes, style attributes, <style> text."""
    for element in root.iter():
        for key in list(element.attrib):
            if local(key) in PAINT_ATTRS:
                yield element, "attr", key, element.attrib[key]
        if "style" in element.attrib:
            for prop, value in style_declarations(element.attrib["style"]):
                if prop in PAINT_ATTRS:
                    yield element, "style", prop, value
        if local(element.tag) == "style":
            for prop, value in style_declarations(element.text):
                if prop in PAINT_ATTRS:
                    yield element, "css", prop, value


def view_box(root):
    numbers = re.findall(r"-?[0-9.]+(?:e-?[0-9]+)?", root.get("viewBox") or "")
    if len(numbers) == 4:
        return [float(n) for n in numbers]
    try:
        return [0.0, 0.0, float(re.sub(r"[a-z%]+$", "", root.get("width") or "")),
                float(re.sub(r"[a-z%]+$", "", root.get("height") or ""))]
    except ValueError:
        return None


def straight_path_box(data):
    """Bounding box of a path made only of M/L/H/V/Z segments (what a background plate looks like)."""
    if re.search(r"[^MmLlHhVvZz0-9eE.,\s+-]", data or ""):
        return None
    x = y = 0.0
    xs, ys = [], []
    for command, body in re.findall(r"([MmLlHhVvZz])([^MmLlHhVvZz]*)", data or ""):
        numbers = [float(n) for n in re.findall(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", body)]
        if command in "Zz":
            continue
        if command in "Hh":
            for value in numbers:
                x = value if command == "H" else x + value
                xs.append(x); ys.append(y)
        elif command in "Vv":
            for value in numbers:
                y = value if command == "V" else y + value
                xs.append(x); ys.append(y)
        else:
            for px, py in zip(numbers[0::2], numbers[1::2]):
                x, y = (px, py) if command in "ML" else (x + px, y + py)
                xs.append(x); ys.append(y)
    if len(xs) < 3:
        return None
    return [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]


def plain_transform(value):
    """(sx, sy, tx, ty) of a transform list made only of translate, scale and axis-aligned matrix steps, None for
    anything that rotates or skews. Vector models write `translate(0,0)` on every shape."""
    sx, sy, tx, ty, end = 1.0, 1.0, 0.0, 0.0, 0
    text = (value or "").strip()
    for match in re.finditer(r"\s*([a-zA-Z]+)\s*\(([^)]*)\)\s*,?", text):
        if match.start() != end:
            return None
        end = match.end()
        name = match.group(1)
        try:
            n = [float(v) for v in re.findall(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", match.group(2))]
        except ValueError:
            return None
        if name == "translate" and len(n) in (1, 2):
            a, d, e, f = 1.0, 1.0, n[0], n[1] if len(n) == 2 else 0.0
        elif name == "scale" and len(n) in (1, 2):
            a, d, e, f = n[0], n[-1], 0.0, 0.0
        elif name == "matrix" and len(n) == 6 and n[1] == 0 and n[2] == 0:
            a, d, e, f = n[0], n[3], n[4], n[5]
        else:
            return None
        tx, ty, sx, sy = tx + sx * e, ty + sy * f, sx * a, sy * d  # later steps apply first: M = M_before . M_step
    return (sx, sy, tx, ty) if end == len(text) else None


NOT_DRAWN = ("defs", "style", "title", "desc", "metadata", "linearGradient", "radialGradient", "clipPath", "mask",
             "pattern", "symbol", "marker", "filter")


def drawn(element):
    """Elements in painting order, skipping subtrees that are never painted (C2PA manifests live in <metadata>)."""
    yield element
    for child in element:
        if local(child.tag) not in NOT_DRAWN:
            for item in drawn(child):
                yield item


def background_element(root):
    """The first drawn shape when it covers the whole viewBox: the plate vector models put behind a mark."""
    box = view_box(root)
    if not box or box[2] <= 0 or box[3] <= 0:
        return None
    for element in drawn(root):
        name = local(element.tag)
        if name in ("svg", "g"):
            if name == "g" and plain_transform(element.get("transform")) != (1.0, 1.0, 0.0, 0.0):
                return None
            continue
        move = plain_transform(element.get("transform"))
        if name not in SHAPES or move is None:
            return None
        if name == "rect":
            def number(key, full):
                value = (element.get(key) or "0").strip()
                return full if value == "100%" else float(re.sub(r"[a-z]+$", "", value) or 0)
            try:
                shape = [number("x", 0), number("y", 0), number("width", box[2]), number("height", box[3])]
            except ValueError:
                return None
        elif name == "path":
            shape = straight_path_box(element.get("d"))
        else:
            return None
        if not shape:
            return None
        xs = sorted((move[0] * shape[0] + move[2], move[0] * (shape[0] + shape[2]) + move[2]))
        ys = sorted((move[1] * shape[1] + move[3], move[1] * (shape[1] + shape[3]) + move[3]))
        shape = [xs[0], ys[0], xs[1] - xs[0], ys[1] - ys[0]]
        tolerance = 0.01 * max(box[2], box[3])
        covers = (shape[0] <= box[0] + tolerance and shape[1] <= box[1] + tolerance
                  and shape[0] + shape[2] >= box[0] + box[2] - tolerance
                  and shape[1] + shape[3] >= box[1] + box[3] - tolerance)
        return element if covers else None
    return None


def geometry_fingerprint(root):
    """Hash of structure and geometry only. Paint changes keep it; any redraw, removal or reorder changes it."""
    parts = []
    for element in root.iter():
        name = local(element.tag)
        if name in ("title", "desc", "metadata", "style"):
            continue
        attrs = ["%s=%s" % (local(k), " ".join(v.split())) for k, v in sorted(element.attrib.items())
                 if local(k) in GEOMETRY_ATTRS]
        parts.append(name + "[" + ";".join(attrs) + "]" + (" ".join((element.text or "").split()) if name in ("text", "tspan") else ""))
    return sha256_text("\n".join(parts))


def plate_free_fingerprint(root):
    """Geometry fingerprint with the background plate deleted outright, or None when there is no plate. A file
    whose plate was removed instead of cleared is still the approved mark."""
    plate = background_element(root)
    if plate is None:
        return None
    root = copy.deepcopy(root)
    plate = background_element(root)
    parent = next(p for p in root.iter() if plate in list(p))
    parent.remove(plate)
    return geometry_fingerprint(root)


def has_implicit_black(root):
    if any(local(e.tag) == "style" for e in root.iter()):
        return False
    parents = {child: parent for parent in root.iter() for child in parent}

    def painted(element):
        while element is not None:
            if element.get("fill") or "fill" in dict(style_declarations(element.get("style"))):
                return True
            element = parents.get(element)
        return False
    inside_defs = set()
    for element in root.iter():
        if local(element.tag) in ("defs", "clipPath", "mask"):
            inside_defs.update(element.iter())
    return any(local(e.tag) in SHAPES and e not in inside_defs and not painted(e) for e in root.iter())


def inspect_svg(path, palette=None):
    root, size = load_svg(path)
    reasons = unsafe_reasons(root)
    counts, unknown = {}, set()
    for _element, _where, _key, value in iter_paints(root):
        parsed = parse_color(value)
        if parsed and parsed.startswith("?"):
            unknown.add(parsed[1:])
        elif parsed:
            counts[parsed] = counts.get(parsed, 0) + 1
    names = [local(e.tag) for e in root.iter()]
    background = background_element(root)
    background_color = None
    if background is not None:
        background_color = parse_color(background.get("fill") or dict(style_declarations(background.get("style"))).get("fill"))
    info = {"path": rel(path), "bytes": size, "elements": len(names), "paths": names.count("path"),
            "shapes": sum(names.count(n) for n in SHAPES), "gradients": names.count("linearGradient") + names.count("radialGradient"),
            "text_elements": names.count("text"), "view_box": view_box(root),
            "colors": [{"hex": h, "uses": n} for h, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))],
            "unknown_color_keywords": sorted(unknown), "implicit_black": has_implicit_black(root),
            "full_canvas_background": background is not None, "background_color": background_color,
            "geometry_sha256": geometry_fingerprint(root), "unsafe": reasons, "warnings": []}
    if info["text_elements"]:
        info["warnings"].append("live <text>: it renders with whatever font the viewer has; ask for outlined letters")
    if info["paths"] + info["shapes"] == 0:
        info["warnings"].append("no drawable shapes found")
    if info["paths"] > 400:
        info["warnings"].append("%d paths: heavy for a logo; small sizes and embroidery will suffer" % info["paths"])
    if len(counts) > 6:
        info["warnings"].append("%d colours: more than a mark needs; expect a lossy mono variant" % len(counts))
    if palette:
        targets = [c["hex"] for c in palette["colors"]]
        info["nearest_palette"] = []
        for used in counts:
            target = min(targets, key=lambda t: distance(used, t))
            info["nearest_palette"].append({"from": used, "to": target, "distance": round(distance(used, target), 1)})
        info["off_palette"] = [h for h in counts if h not in targets]
    return root, info


def replace_paint(element, where, key, mapping):
    """Exact substitution of one normalised colour by another; returns the source hex when it replaced."""
    def swap(value):
        parsed = parse_color(value)
        if parsed in mapping:
            alpha = re.fullmatch(r"\s*#[0-9a-fA-F]{6}([0-9a-fA-F]{2})\s*", value)
            return mapping[parsed] + (alpha.group(1) if alpha else ""), parsed
        return value, None
    if where == "attr":
        element.attrib[key], hit = swap(element.attrib[key])
        return [hit] if hit else []
    hits = []

    def rewrite(match):
        if match.group(1).strip().lower() != key:
            return match.group(0)
        new, hit = swap(match.group(2).strip())
        if hit:
            hits.append(hit)
        return "%s:%s" % (match.group(1), new)
    pattern = r"([a-zA-Z-]+)\s*:\s*([^;{}]+)"
    if where == "style":
        element.attrib["style"] = re.sub(pattern, rewrite, element.attrib["style"])
    else:
        element.text = re.sub(pattern, rewrite, element.text or "")
    return hits


def recolor(root, mapping, implicit_to=None):
    replaced = {}
    for element, where, key, _value in list(iter_paints(root)):
        for hit in replace_paint(element, where, key, mapping):
            replaced[hit] = replaced.get(hit, 0) + 1
    if implicit_to and has_implicit_black(root):
        root.set("fill", implicit_to)  # shapes without any fill draw black by default: make that explicit
        replaced["#000000 (implicit)"] = 1
    return replaced


def set_fill(element, value):
    if "fill" in dict(style_declarations(element.get("style"))):
        element.set("style", re.sub(r"(^|;)\s*fill\s*:\s*[^;]+", lambda m: m.group(1) + "fill:" + value, element.get("style")))
    element.set("fill", value)


def clear_background(root):
    element = background_element(root)
    if element is None:
        return False
    set_fill(element, "none")
    return True


def write_svg(root, path):
    body = ET.tostring(root, encoding="unicode")
    write_atomic(path, '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n")


def data_uri(path):
    with open(path, "rb") as handle:
        return "data:image/svg+xml;base64," + base64.b64encode(handle.read()).decode("ascii")


# ----------------------------------------------------------------------------------------------- converters

def find_tool(env_name, names, paths=()):
    override = os.environ.get(env_name)
    if override:
        if override.strip().lower() == "none":
            return None
        return override if os.path.isfile(override) and os.access(override, os.X_OK) else None
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    for path in paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def converters():
    return {"browser": find_tool("GM_BROWSER_BIN", BROWSER_NAMES, BROWSER_PATHS),
            "qlmanage": find_tool("GM_QLMANAGE_BIN", ("qlmanage",))}


def need_browser(what):
    if not converters()["browser"]:
        raise Fail("tool_missing", "%s needs a Chromium-family browser, and none was found" % what, hint=MISSING_HINT)


def file_complete(path):
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError:
        return False
    if path.lower().endswith(".pdf"):
        return data.startswith(b"%PDF") and b"%%EOF" in data[-2048:]
    return data.startswith(b"\x89PNG\r\n\x1a\n") and data[-12:-4] == b"\x00\x00\x00\x00IEND"


def run_browser(binary, flag, out, url, extra):
    """Some headless browsers write the file and never exit: wait for a complete file, then stop the process."""
    profile = tempfile.mkdtemp(prefix="brandkit-browser-")
    if os.path.exists(out):
        os.remove(out)
    argv = [binary, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
            "--force-device-scale-factor=1", "--user-data-dir=" + profile] + list(extra) + ["%s=%s" % (flag, out), url]
    try:
        process = subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        shutil.rmtree(profile, ignore_errors=True)
        raise Fail("tool_failed", "cannot start %s: %s" % (binary, exc), hint=MISSING_HINT)
    started = time.time()
    try:
        while time.time() - started < BROWSER_TIMEOUT_S:
            if file_complete(out):
                break
            if process.poll() is not None:
                break
            time.sleep(0.25)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(5)
            except subprocess.TimeoutExpired:
                process.kill()
        shutil.rmtree(profile, ignore_errors=True)
    if not file_complete(out):
        raise Fail("tool_failed", "%s wrote no complete file within %d s" % (os.path.basename(binary), BROWSER_TIMEOUT_S),
                   hint="deliver the SVG or HTML instead and say the export failed")


def png_size(path):
    with open(path, "rb") as handle:
        head = handle.read(24)
    return list(struct.unpack(">II", head[16:24])) if head.startswith(b"\x89PNG") else None


def png_header(path):
    """(width, height, bit depth, colour type) from the IHDR chunk; colour type 6 carries alpha, 2 does not."""
    with open(path, "rb") as handle:
        head = handle.read(26)
    if not head.startswith(PNG_SIG) or len(head) < 26:
        raise Fail("png_invalid", "%s is not a PNG" % path)
    return struct.unpack(">IIBB", head[16:26])


def png_read(path):
    """Decode an 8-bit RGB or RGBA, non-interlaced PNG (what a headless browser writes): (width, height, channels, rows)."""
    with open(path, "rb") as handle:
        data = handle.read()
    if not data.startswith(PNG_SIG):
        raise Fail("png_invalid", "%s is not a PNG" % path)
    header, idat, pos = None, [], 8
    while pos + 8 <= len(data):
        length, tag = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            idat.append(body)
        elif tag == b"IEND":
            break
        pos += 12 + length
    if not header or header[2] != 8 or header[3] not in (2, 6) or header[6]:
        raise Fail("png_unsupported", "%s: only 8-bit RGB or RGBA PNG without interlacing can be measured" % path)
    width, height, channels = header[0], header[1], 3 if header[3] == 2 else 4
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error as exc:
        raise Fail("png_invalid", "%s: damaged image data (%s)" % (path, exc))
    stride = width * channels
    if len(raw) < (stride + 1) * height:
        raise Fail("png_invalid", "%s: image data is shorter than its header says" % path)
    rows, previous, offset = [], bytearray(stride), 0
    for _ in range(height):
        kind = raw[offset]
        line = bytearray(raw[offset + 1:offset + 1 + stride])
        offset += 1 + stride
        if kind == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 255
        elif kind == 2:
            for i in range(stride):
                line[i] = (line[i] + previous[i]) & 255
        elif kind == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + previous[i]) >> 1)) & 255
        elif kind == 4:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                above = previous[i]
                corner = previous[i - channels] if i >= channels else 0
                guess = left + above - corner
                d_left, d_above, d_corner = abs(guess - left), abs(guess - above), abs(guess - corner)
                line[i] = (line[i] + (left if d_left <= d_above and d_left <= d_corner else above if d_above <= d_corner else corner)) & 255
        elif kind != 0:
            raise Fail("png_invalid", "%s: unknown row filter %d" % (path, kind))
        rows.append(line)
        previous = line
    return width, height, channels, rows


def png_write(path, width, height, channels, rows):
    """8-bit RGB or RGBA PNG, `Up` row filter, tagged sRGB."""
    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xffffffff)
    raw, previous = bytearray(), bytes(width * channels)
    for line in rows:
        raw.append(2)
        raw += bytes((a - b) & 255 for a, b in zip(line, previous))
        previous = line
    write_atomic(path, PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6 if channels == 4 else 2, 0, 0, 0))
                 + chunk(b"sRGB", b"\x00") + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def ensure_alpha_channel(path):
    """A browser drops the alpha channel of a fully opaque screenshot. A store that asks for 32-bit PNG gets it back: same pixels, alpha 255."""
    width, height, channels, rows = png_read(path)
    if channels == 4:
        return False
    out = []
    for line in rows:
        wide = bytearray(b"\xff" * (width * 4))
        wide[0::4], wide[1::4], wide[2::4] = line[0::3], line[1::3], line[2::3]
        out.append(wide)
    png_write(path, width, height, 4, out)
    return True


def ink_spans(rows, width, channels):
    """Per row that carries ink: (y, first column, last column). Without an alpha channel every pixel is ink."""
    spans = []
    for y, line in enumerate(rows):
        if channels == 4:
            mask = bytes(line[3::4]).translate(ALPHA_TABLE)
            first = mask.find(1)
            if first >= 0:
                spans.append((y, first, mask.rfind(1)))
        else:
            spans.append((y, 0, width - 1))
    return spans


def ink_box(spans):
    return [min(s[1] for s in spans), spans[0][0], max(s[2] for s in spans) + 1, spans[-1][0] + 1]


def ink_reach(spans, cx, cy):
    """Distance in pixels from (cx, cy) to the farthest ink, measured to the outer pixel edges."""
    return math.sqrt(max(max((first - cx) ** 2, (last + 1 - cx) ** 2) + max((y - cy) ** 2, (y + 1 - cy) ** 2)
                         for y, first, last in spans))


def file_url(path):
    return pathlib.Path(os.path.abspath(path)).as_uri()


def export_png(source, out, width, height, background):
    tools = converters()
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    is_svg = source.lower().endswith(".svg")
    if is_svg:
        root, _info = inspect_svg(source)
        if unsafe_reasons(root):
            raise Fail("svg_unsafe", "%s is not safe to render" % source, extra={"reasons": unsafe_reasons(root)})
        box = view_box(root)
        if not height:
            height = int(round(width * box[3] / box[2])) if box and box[2] > 0 else width
    if tools["browser"]:
        workdir = tempfile.mkdtemp(prefix="brandkit-png-")
        try:
            if is_svg:
                page = os.path.join(workdir, "page.html")
                css_bg = "transparent" if background == "transparent" else background
                with open(page, "w", encoding="utf-8") as handle:
                    # Pixel sizes, not 100vw: a headless window narrower than 500 px keeps a 500 px viewport and the
                    # screenshot is its top-left corner, so viewport units would push a small icon out of the picture.
                    handle.write('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;'
                                 'background:%s}img{display:block;position:absolute;left:0;top:0;width:%dpx;height:%dpx;'
                                 'object-fit:contain}</style></head><body><img alt="" src="%s"></body></html>'
                                 % (css_bg, width, height, data_uri(source)))
                url = file_url(page)
            else:
                url = file_url(source)
            extra = ["--window-size=%d,%d" % (width, height)]
            if background == "transparent" and is_svg:
                extra.append("--default-background-color=00000000")
            run_browser(tools["browser"], "--screenshot", os.path.abspath(out), url, extra)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)
        return {"tool": "browser", "fallback": False, "transparent": background == "transparent" and is_svg}
    if tools["qlmanage"] and is_svg:
        workdir = tempfile.mkdtemp(prefix="brandkit-ql-")
        try:
            subprocess.run([tools["qlmanage"], "-t", "-s", str(max(width, height)), "-o", workdir, os.path.abspath(source)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=BROWSER_TIMEOUT_S, check=False)
            made = [name for name in os.listdir(workdir) if name.lower().endswith(".png")]
            if not made:
                raise Fail("tool_failed", "qlmanage produced no PNG for %s" % source, hint=MISSING_HINT)
            shutil.move(os.path.join(workdir, made[0]), out)
        except subprocess.TimeoutExpired:
            raise Fail("tool_failed", "qlmanage timed out", hint=MISSING_HINT)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)
        return {"tool": "qlmanage", "fallback": True, "transparent": "unknown",
                "note": "Quick Look thumbnail: size and background are not guaranteed; fine as a model reference, label it in a hand-off"}
    raise Fail("tool_missing", "no converter for %s" % ("PNG" if is_svg else "a screenshot of HTML"), hint=MISSING_HINT)


# ----------------------------------------------------------------------------------------------- html

BOARD_CSS = """
:root{--ink:#16181d;--muted:#5d6470;--line:#d9dce3;--paper:#f6f6f3;--card:#ffffff}
*{box-sizing:border-box}body{margin:0;padding:32px;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:0 0 8px}h3{font-size:13px;margin:16px 0 6px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.sub{color:var(--muted);margin:0 0 24px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;break-inside:avoid}
.tag{display:inline-block;font-weight:700;font-size:13px;border:1px solid var(--ink);border-radius:999px;padding:1px 10px;margin-right:8px}
.sw{display:flex;flex-wrap:wrap;gap:8px}.chip{width:104px;height:88px;border-radius:8px;padding:8px;font-size:11px;line-height:1.3;border:1px solid rgba(0,0,0,.12);display:flex;flex-direction:column;justify-content:flex-end}
table{border-collapse:collapse;width:100%;font-size:12px}td,th{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left}
.dot{display:inline-block;width:12px;height:12px;border-radius:50%;border:1px solid rgba(0,0,0,.2);vertical-align:-1px;margin-right:4px}
.stage{display:flex;gap:8px;flex-wrap:wrap}.plate{flex:1 1 150px;height:170px;border-radius:8px;border:1px solid var(--line);display:flex;align-items:center;justify-content:center;padding:14px}
.svg{background-position:center;background-repeat:no-repeat;background-size:contain;width:100%;height:100%;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.small{display:flex;gap:14px;align-items:flex-end;margin-top:10px}.small div.svg{flex:none}
img.shot{max-width:100%;border-radius:8px;border:1px solid var(--line);display:block}
pre{white-space:pre-wrap;background:#f0f1f4;border-radius:8px;padding:12px;font-size:12px;overflow:auto}
.note{color:var(--muted);font-size:13px}.warn{color:#9a3412;font-size:13px}.kv td:first-child{color:var(--muted);width:32%}
.spec{border:1px solid var(--line);border-radius:8px;padding:16px;margin-top:8px}.miss{color:#9a3412;font-weight:600}
@media print{body{background:#fff;padding:0}.card{border:0;padding:0 0 24px}}
"""

FONT_PROBE_JS = """
(function(){function width(f){var s=document.createElement('span');s.textContent='mmmmmmmmmmlliWQ@';s.style.cssText='position:absolute;left:-9999px;font-size:72px;font-family:'+f;document.body.appendChild(s);var w=s.getBoundingClientRect().width;s.remove();return w}
function run(){document.querySelectorAll('[data-font]').forEach(function(el){var n=el.getAttribute('data-font');var ok=['serif','sans-serif','monospace'].some(function(g){return width('"'+n+'",'+g)!==width(g)});el.textContent=ok?'renders in the real font here':'NOT available in this browser: the sample shows a fallback face';if(!ok)el.className='miss'})}
if(document.fonts&&document.fonts.ready){document.fonts.ready.then(run)}else{window.addEventListener('load',run)}})();
"""


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


class Page:
    def __init__(self, title, base_dir):
        self.title, self.base_dir, self.body, self.svg_classes, self.scripts, self.links = title, base_dir, [], {}, [], []

    def svg_class(self, path):
        key = "s" + sha256_file(path)[:10]
        self.svg_classes[key] = data_uri(path)
        return key

    def svg_box(self, path, label, width=None, height=None, hide_plate=False):
        size = "" if width is None else ' style="width:%dpx;height:%dpx"' % (width, height or width)
        key = self.svg_class(path)
        if hide_plate:  # preview only: the candidate file itself is never touched
            root, _size = load_svg(path)
            if clear_background(root):
                body = ET.tostring(root, encoding="utf-8")
                key = "p" + hashlib.sha256(body).hexdigest()[:10]
                self.svg_classes[key] = "data:image/svg+xml;base64," + base64.b64encode(body).decode("ascii")
        return '<div class="svg %s" role="img" aria-label="%s"%s></div>' % (key, esc(label), size)

    def media(self, path, label):
        if not os.path.isfile(path):
            return '<p class="miss">missing file: %s</p>' % esc(path)
        if path.lower().endswith(".svg"):
            return '<div class="plate" style="height:320px">%s</div>' % self.svg_box(path, label)
        if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            return '<img class="shot" alt="%s" src="%s">' % (esc(label), esc(os.path.relpath(os.path.abspath(path), str(self.base_dir)).replace(os.sep, "/")))
        return '<p class="note">file: %s</p>' % esc(path)

    def render(self, extra_css=""):
        classes = "".join(".%s{background-image:url(%s)}" % item for item in self.svg_classes.items())
        scripts = "".join("<script>%s</script>" % s for s in self.scripts)
        return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                "<title>%s</title>%s<style>%s%s%s</style></head><body>%s%s</body></html>\n"
                % (esc(self.title), "".join(self.links), BOARD_CSS, extra_css, classes, "".join(self.body), scripts))


def swatches(colors):
    return '<div class="sw">' + "".join(
        '<div class="chip" style="background:%s;color:%s"><b>%s</b><span>%s</span><span>%s</span></div>'
        % (c["hex"], c["label"], esc(c["name"]), c["hex"].upper(), esc(c["role"])) for c in colors) + "</div>"


def pairs_table(palette, minimum=3.0):
    rows = "".join('<tr><td><span class="dot" style="background:%s"></span>%s</td><td><span class="dot" style="background:%s"></span>%s</td>'
                   '<td>%.2f:1</td><td>%s</td></tr>' % (p["a"], p["a"].upper(), p["b"], p["b"].upper(), p["ratio"], p["grade"])
                   for p in sorted(palette["pairs"], key=lambda p: -p["ratio"]) if p["ratio"] >= minimum)
    return ("<table><tr><th>Colour</th><th>with</th><th>Contrast</th><th>Grade</th></tr>%s</table>"
            '<p class="note">AA 4.5:1 body text · AA-large 3:1 large type and UI shapes · pairs under 3:1 are left out: never text.</p>' % rows)


def role_color(palette, roles, default):
    for role in roles:
        for color in palette["colors"]:
            if color["role"] == role:
                return color["hex"]
    return default


def font_stack(font):
    return '"%s", %s' % (str(font.get("family", "")).replace('"', ""), font.get("fallback") or "sans-serif")


def section_palette(page, candidate, brand):
    palette = candidate["data"]
    ground, ink = role_color(palette, ("background", "surface"), "#ffffff"), role_color(palette, ("text",), "#111111")
    primary, accent = role_color(palette, ("primary",), ink), role_color(palette, ("accent", "secondary"), ink)
    label = next((c["label"] for c in palette["colors"] if c["hex"] == primary), "#ffffff")
    sample = ('<div class="spec" style="background:%s;color:%s"><div style="font-size:26px;font-weight:700;color:%s">%s</div>'
              "<p style=\"margin:6px 0 12px\">Body text on the background colour. Judge comfort, not just the numbers.</p>"
              '<span style="background:%s;color:%s;border-radius:6px;padding:6px 14px;font-weight:600">Primary action</span> '
              '<span style="border-bottom:3px solid %s;padding-bottom:2px">accent detail</span></div>'
              % (ground, ink, primary if contrast(primary, ground) >= 3 else ink, esc(brand), primary, label, accent))
    notes = "".join('<p class="warn">%s</p>' % esc(n) for n in palette.get("notes", []))
    return ('<div class="card"><h2><span class="tag">%s</span>%s</h2><p class="note">%s</p>%s%s<h3>Contrast pairs</h3>%s%s</div>'
            % (esc(candidate["id"]), esc(palette.get("name") or ""), esc(palette.get("rationale") or ""),
               swatches(palette["colors"]), sample, pairs_table(palette), notes))


def section_logo(page, candidate, palette):
    svgs = [f["path"] for f in candidate["files"] if f["path"].lower().endswith(".svg") and os.path.isfile(f["path"])]
    data = candidate.get("data") or {}
    head = '<h2><span class="tag">%s</span>%s</h2><p class="note">%s</p>' % (
        esc(candidate["id"]), esc(data.get("mark_type") or ""), esc(data.get("idea") or candidate.get("note") or ""))
    if not svgs:
        return '<div class="card">%s%s</div>' % (head, "".join(page.media(f["path"], candidate["id"]) for f in candidate["files"]))
    path = svgs[0]
    light = role_color(palette, ("background", "surface"), "#f4f1ea") if palette else "#f4f1ea"
    dark = role_color(palette, ("text", "primary"), "#14161a") if palette else "#14161a"
    stats = next((f.get("svg") for f in candidate["files"] if f["path"] == path), None) or {}
    plated = bool(stats.get("full_canvas_background")) or background_element(load_svg(path)[0]) is not None
    plates = "".join('<div class="plate" style="background:%s">%s</div>' % (bg, page.svg_box(path, candidate["id"], hide_plate=hide))
                     for bg, hide in (("#ffffff", False), (light, True), (dark, True)))
    small = "".join(page.svg_box(path, "%s at %d px" % (candidate["id"], size), size, hide_plate=True) for size in (96, 48, 24))
    chips = "".join('<span class="dot" style="background:%s"></span>%s ' % (c["hex"], c["hex"].upper()) for c in stats.get("colors", [])[:8])
    warn = "".join('<p class="warn">%s</p>' % esc(w) for w in stats.get("warnings", []))
    text = candidate.get("text") or {}
    read = ('<p class="note">Text read back: %s</p>' % esc(" / ".join(text.get("expected") or [])) if text.get("expected")
            else '<p class="note">No text in this mark.</p>' if text.get("none") else "")
    return ('<div class="card">%s<div class="stage">%s</div><div class="small">%s<span class="note">96 · 48 · 24 px: does it survive small?</span></div>'
            "%s<p class=\"note\">First plate: as returned, unedited%s. %s paths · %s KB · colours: %s</p>%s</div>"
            % (head, plates, small, read, "; the other previews hide its background plate" if plated else "", stats.get("paths", "?"), max(1, int(round((stats.get("bytes") or 0) / 1000.0))), chips or "-", warn))


def section_type(page, candidate, brand, palette):
    data = candidate["data"]
    ground = role_color(palette, ("background", "surface"), "#ffffff") if palette else "#ffffff"
    ink = role_color(palette, ("text",), "#111111") if palette else "#111111"
    rows = ""
    for role in ("display", "body", "mono"):
        font = data.get(role)
        if font:
            rows += ('<tr><td>%s</td><td><b>%s</b> %s</td><td>%s</td><td data-font="%s">not checked (scripts off)</td></tr>'
                     % (role, esc(font["family"]), esc(font.get("weight") or ""), esc(font.get("traits") or ""), esc(font["family"])))
    display, body = data["display"], data["body"]
    sample = ('<div class="spec" style="background:%s;color:%s"><div style="font:%s 40px/1.1 %s">%s</div>'
              '<div style="font:%s 22px/1.25 %s;margin:10px 0">Iİıi Şş Ğğ Üü Öö Çç — 0123456789</div>'
              '<p style="font:%s 16px/1.55 %s;margin:0">Body copy sets the everyday voice. Read a paragraph, not a word: rhythm, '
              "spacing and the shapes of a, g, e and the numerals decide whether the pairing holds.</p></div>"
              % (ground, ink, esc(display.get("weight") or "700"), esc(font_stack(display)), esc(brand),
                 esc(display.get("weight") or "700"), esc(font_stack(display)), esc(body.get("weight") or "400"), esc(font_stack(body))))
    return ('<div class="card"><h2><span class="tag">%s</span>%s</h2><p class="note">%s</p>%s'
            "<table><tr><th>Role</th><th>Family</th><th>Traits</th><th>On this machine</th></tr>%s</table>"
            '<p class="note">Families are names, not files: nothing is bundled. Check the licence of the version you download '
            "and that it covers the letters you need.</p></div>"
            % (esc(candidate["id"]), esc(data.get("name") or ""), esc(data.get("rationale") or ""), sample, rows))


def section_generic(page, candidate):
    data = candidate.get("data") or {}
    media = "".join(page.media(f["path"], candidate["id"]) for f in candidate["files"])
    text = candidate.get("text") or {}
    expected = ("<h3>Text requested and read back</h3><pre>%s</pre>" % esc("\n".join(text["expected"]))) if text.get("expected") else ""
    block = "<pre>%s</pre>" % esc(candidate["text_block"]) if candidate.get("text_block") else ""
    rows = "".join("<tr><td>%s</td><td>%s</td></tr>" % (esc(k), esc(", ".join(map(str, v)) if isinstance(v, list) else v))
                   for k, v in data.items() if isinstance(v, (str, int, float, list)) and not isinstance(v, bool))
    table = '<table class="kv">%s</table>' % rows if rows and not block else ""
    return ('<div class="card"><h2><span class="tag">%s</span></h2><p class="note">%s</p>%s%s%s%s</div>'
            % (esc(candidate["id"]), esc(candidate.get("note") or ""), media, block, table, expected))


def approved_data(state, slot):
    _, candidate = approved_candidate(state["slots"].get(slot) or new_slot())
    return candidate["data"] if candidate else None


def google_fonts_link(families):
    query = "&".join("family=" + re.sub(r"\s+", "+", f.strip()) + ":wght@400;500;600;700" for f in sorted(set(families)) if f.strip())
    return '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?%s&amp;display=swap">' % query if query else ""


def build_board(state, slots, revision_number, out, webfonts):
    brand = state["brand"]["name"]
    page = Page("%s: review board" % brand, os.path.dirname(os.path.abspath(out)))
    palette = approved_data(state, "palette")
    page.body.append("<h1>%s</h1>" % esc(brand))
    shown, families = [], []
    for slot in slots:
        slot_state = state["slots"].get(slot)
        if not slot_state or not slot_state["revisions"]:
            raise Fail("nothing_to_show", "slot %s has no candidates yet" % slot)
        revision = next((r for r in slot_state["revisions"] if r["rev"] == revision_number), None) if revision_number else current_revision(slot_state)
        if revision is None:
            raise usage("slot %s has no revision %s" % (slot, revision_number))
        page.body.append('<p class="sub">%s · revision r%d · %s · %d candidate(s)</p><div class="grid">'
                         % (esc(slot), revision["rev"], esc(revision["status"]), len(revision["candidates"])))
        for candidate in revision["candidates"]:
            if slot == "palette":
                page.body.append(section_palette(page, candidate, brand))
            elif slot == "logo":
                page.body.append(section_logo(page, candidate, palette))
            elif slot == "typography":
                page.body.append(section_type(page, candidate, brand, palette))
                families += [candidate["data"][r]["family"] for r in ("display", "body", "mono") if candidate["data"].get(r)]
            else:
                page.body.append(section_generic(page, candidate))
            shown.append(candidate["id"])
        page.body.append("</div>")
    if families:
        page.scripts.append(FONT_PROBE_JS)
        if webfonts:
            page.links.append(google_fonts_link(families))
    write_atomic(out, page.render())
    return shown


BOOK_CSS = """
body{padding:0;background:#fff}.sheet{padding:40px 48px;border-bottom:1px solid var(--line);break-after:page}
.cover{display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:24px;min-height:560px}.cover .plate{width:420px;height:260px;border:0}
.cover h1{font-size:44px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:28px}ul{margin:6px 0 0 18px;padding:0}
.apps{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px}.apps figure{margin:0;max-width:560px}.apps figcaption{font-size:12px;color:var(--muted);margin-top:4px}
@page{size:A4 landscape;margin:12mm}@media print{.sheet{border:0;min-height:0;padding:0}}
"""


def asset_path(state, slot, role):
    slot_state = state["slots"].get(slot) or new_slot()
    for asset in reversed(slot_state.get("assets", [])):
        if asset["role"] == role and asset.get("from_revision") == slot_state.get("approved_revision") and os.path.isfile(asset["path"]):
            return asset["path"]
    return None


def build_book(state, out_dir):
    brand = state["brand"]["name"]
    missing = [name for name in FOUNDATION if state["slots"].get(name, {}).get("status") != "approved"]
    if missing:
        raise Fail("upstream_missing", "the brandbook is built from approved slots only; not approved: %s" % ", ".join(missing),
                   extra={"missing": missing})
    strategy, palette, typography = (require_approved(state, n)[1]["data"] for n in ("strategy", "palette", "typography"))
    _, lock = require_approved(state, "lock")
    _, logo = require_approved(state, "logo")
    rules = lock["data"]
    os.makedirs(os.path.join(out_dir, "assets"), exist_ok=True)
    out = os.path.join(out_dir, "brandbook.html")
    page = Page("%s: brand guidelines" % brand, os.path.abspath(out_dir))
    logo_files = [f["path"] for f in logo["files"] if f["path"].lower().endswith(".svg") and os.path.isfile(f["path"])]
    primary = asset_path(state, "logo", "primary") or (logo_files[0] if logo_files else None)
    placed = asset_path(state, "logo", "nobg") or primary  # the mark without the model's plate
    light, dark = role_color(palette, ("background", "surface"), "#ffffff"), role_color(palette, ("text", "primary"), "#111111")

    def plate(path, background, label, height=200):
        if not path:
            return '<div class="plate" style="height:%dpx"><span class="note">%s: not produced</span></div>' % (height, esc(label))
        if not path.lower().endswith(".svg"):
            return page.media(path, label)
        return '<div><div class="plate" style="background:%s;height:%dpx">%s</div><p class="note">%s</p></div>' % (
            background, height, page.svg_box(path, label, hide_plate=True), esc(label))

    def bullets(items):
        return "<ul>%s</ul>" % "".join("<li>%s</li>" % esc(i) for i in items or [])
    stamp = ", ".join("%s r%s" % (n, state["slots"][n]["approved_revision"]) for n in FOUNDATION)
    page.body.append('<section class="sheet cover">%s<h1>%s</h1><p class="sub">Brand guidelines · %s</p></section>'
                     % ('<div class="plate">%s</div>' % page.svg_box(placed, brand + " logo", hide_plate=True)
                        if placed and placed.lower().endswith(".svg") else "",
                        esc(brand), esc(stamp)))
    rows = "".join("<tr><td>%s</td><td>%s</td></tr>" % (esc(k.replace("_", " ")), esc(", ".join(v) if isinstance(v, list) else v))
                   for k, v in strategy.items() if isinstance(v, (str, list)) and v)
    page.body.append('<section class="sheet"><h2>1 · Strategy snapshot</h2><table class="kv">%s</table>'
                     '<p class="note">Facts on this page were supplied by the brand owner.</p></section>' % rows)
    page.body.append('<section class="sheet"><h2>2 · Logo</h2><div class="cols"><div>%s</div><div>%s</div></div><div class="cols">%s%s</div>'
                     '<div class="cols"><div><h3>Construction</h3><p>%s</p><h3>Clear space</h3><p>%s</p><h3>Minimum size</h3><p>%s</p></div>'
                     "<div><h3>Never</h3>%s</div></div></section>"
                     % (plate(placed, "#ffffff", "Primary, on white"), plate(placed, light, "Primary, on the brand background"),
                        plate(asset_path(state, "logo", "mono"), "#ffffff", "One colour"),
                        plate(asset_path(state, "logo", "reversed"), dark, "Reversed, on dark"),
                        esc(rules.get("logo_construction")), esc(rules.get("clear_space")), esc(rules.get("min_size") or "Not set."),
                        bullets(rules.get("misuse"))))
    table = "".join("<tr><td>%s</td><td>%s</td><td>%s</td><td>rgb(%d, %d, %d)</td><td>%s</td></tr>"
                    % (esc(c["name"]), esc(c["role"]), c["hex"].upper(), c["rgb"]["r"], c["rgb"]["g"], c["rgb"]["b"], esc(c.get("use") or ""))
                    for c in palette["colors"])
    page.body.append('<section class="sheet"><h2>3 · Colour</h2>%s<h3>Values</h3><table><tr><th>Name</th><th>Role</th><th>Hex</th><th>RGB</th>'
                     "<th>Use</th></tr>%s</table><h3>Contrast</h3>%s<p class=\"note\">Screen values. Print conversions (CMYK, spot) are set "
                     "with the print shop, not here.</p></section>" % (swatches(palette["colors"]), table, pairs_table(palette)))
    fonts = "".join('<div class="spec"><div style="font:%s 34px/1.15 %s">%s</div><p class="note">%s: <b>%s</b> %s · %s · fallback %s</p></div>'
                    % (esc(f.get("weight") or "400"), esc(font_stack(f)), esc(brand if role == "display" else "The quick brown fox · Iİıi Şş Ğğ Üü Öö Çç"),
                       role, esc(f["family"]), esc(f.get("weight") or ""), esc(f.get("use") or ""), esc(f.get("fallback") or "sans-serif"))
                    for role, f in ((r, typography.get(r)) for r in ("display", "body", "mono")) if f)
    page.body.append('<section class="sheet"><h2>4 · Typography</h2>%s<p class="note">%s</p><p class="note">Font families are named, not '
                     "bundled. The samples above use the real face only where it is installed. Check the licence of each family before use."
                     "</p></section>" % (fonts, esc(typography.get("rationale") or "")))
    page.body.append('<section class="sheet"><h2>5 · Imagery, tone and layout</h2><div class="cols"><div><h3>Imagery</h3><p>%s</p><h3>Layout</h3><p>%s</p>'
                     "<h3>Tone</h3><p>%s</p></div><div><h3>Do</h3>%s<h3>Don't</h3>%s</div></div></section>"
                     % (esc(rules.get("imagery_style")), esc(rules.get("layout") or "Not set."), esc(", ".join(strategy.get("tone_words") or [])),
                        bullets(rules.get("do")), bullets(rules.get("dont"))))
    figures, used = [], []
    for name in sorted(n for n in state["slots"] if n.startswith("app-")):
        _, candidate = approved_candidate(state["slots"][name])
        if not candidate:
            continue
        used.append(name)
        for item in candidate["files"]:
            if not os.path.isfile(item["path"]):
                continue
            if item["path"].lower().endswith(".svg"):
                figures.append("<figure>%s<figcaption>%s</figcaption></figure>" % (page.media(item["path"], name), esc(name[4:].replace("-", " "))))
                continue
            copy_to = os.path.join(out_dir, "assets", "%s-%s" % (name, os.path.basename(item["path"])))
            shutil.copyfile(item["path"], copy_to)
            figures.append("<figure>%s<figcaption>%s</figcaption></figure>" % (page.media(copy_to, name), esc(name[4:].replace("-", " "))))
    if figures:
        page.body.append('<section class="sheet"><h2>6 · Applications</h2><div class="apps">%s</div><p class="note">Visualisations generated '
                         "with AI from the approved logo; not print-ready artwork.</p></section>" % "".join(figures))
    page.body.append('<section class="sheet"><h2>%d · Brand lock and notes</h2><pre>%s</pre><p class="note">Paste this block unchanged into any '
                     "later generation prompt. A generated mark can resemble existing trademarks: a trademark search before use is the "
                     "owner's responsibility. Logo candidates and applications were generated with AI models and approved by the owner.</p></section>"
                     % (7 if figures else 6, esc(lock["text_block"])))
    write_atomic(out, page.render(BOOK_CSS))
    return out, used


# ----------------------------------------------------------------------------------------------- lock

def compose_lock(state, rules):
    for key in ("logo_construction", "clear_space", "imagery_style"):
        if not str(rules.get(key) or "").strip():
            raise usage("lock data needs a non-empty %r" % key)
    for key, least in (("misuse", 3), ("dont", 2), ("do", 1)):
        if not isinstance(rules.get(key), list) or len([v for v in rules[key] if str(v).strip()]) < least:
            raise usage("lock data needs %r: a list with at least %d entries" % (key, least))
    strategy, palette, typography = (require_approved(state, n)[1]["data"] for n in ("strategy", "palette", "typography"))
    _, logo = require_approved(state, "logo")
    revs = {n: state["slots"][n]["approved_revision"] for n in ("strategy", "palette", "logo", "typography")}
    number = len(state["slots"].get("lock", new_slot())["revisions"]) + 1
    colors = "; ".join('%s %s "%s"' % (c["role"], c["hex"].upper(), c["name"]) for c in palette["colors"])
    pairs = "; ".join("%s on %s (%.1f:1)" % (p["a"].upper(), p["b"].upper(), p["ratio"]) for p in palette["text_pairs"][:4])

    def font_line(role, label):
        font = typography.get(role)
        if not font:
            return None
        return "%s: %s %s, %s" % (label, font["family"], font.get("weight") or "", font.get("traits") or "no traits given")
    lines = [
        "=== BRAND LOCK: %s (lock r%d; strategy r%d, palette r%d, logo r%d, typography r%d) - FROZEN, APPLY AS WRITTEN ==="
        % (state["brand"]["name"], number, revs["strategy"], revs["palette"], revs["logo"], revs["typography"]),
        'Brand name, exact spelling: "%s". Never translate, abbreviate, re-case or re-letter it.' % state["brand"]["name"],
        "Logo: the supplied logo image is the approved mark (%s). Reproduce it exactly: same shapes, proportions and colours. "
        "Never redraw, restyle, outline, tilt, stretch, add effects to it or add words to it." % (logo["data"].get("mark_type") or "mark"),
        "Logo construction: %s" % rules["logo_construction"].strip(),
        "Clear space: %s" % rules["clear_space"].strip(),
    ]
    if str(rules.get("min_size") or "").strip():
        lines.append("Minimum size: %s" % rules["min_size"].strip())
    lines += ["Logo misuse, never: %s." % "; ".join(str(v).strip().rstrip(".") for v in rules["misuse"] if str(v).strip()),
              "Palette, exact values: %s. Brand elements use only these colours." % colors]
    if pairs:
        lines.append("Text colour pairs that pass contrast: %s." % pairs)
    lines += [line for line in (font_line("display", "Headline type"), font_line("body", "Body type"), font_line("mono", "Mono type")) if line]
    lines.append("Imagery style: %s" % rules["imagery_style"].strip())
    if str(rules.get("layout") or "").strip():
        lines.append("Layout: %s" % rules["layout"].strip())
    lines += ["Tone: %s." % ", ".join(strategy.get("tone_words") or []),
              "Do: %s." % "; ".join(str(v).strip().rstrip(".") for v in rules["do"] if str(v).strip()),
              "Don't: %s." % "; ".join(str(v).strip().rstrip(".") for v in rules["dont"] if str(v).strip()),
              "=== END BRAND LOCK ==="]
    return "\n".join(lines), number


# ----------------------------------------------------------------------------------------------- commands

def cmd_tools(_args):
    tools = converters()
    ffmpeg, iconutil = find_tool("GM_FFMPEG_BIN", ("ffmpeg",)), find_tool("GM_ICONUTIL_BIN", ("iconutil",))
    return emit({"ok": True, "browser": tools["browser"], "qlmanage": tools["qlmanage"], "ffmpeg": ffmpeg, "iconutil": iconutil,
                 "png": "browser" if tools["browser"] else "qlmanage" if tools["qlmanage"] else None,
                 "pdf": "browser" if tools["browser"] else None,
                 "can": {"board_png": bool(tools["browser"]), "logo_png": bool(tools["browser"] or tools["qlmanage"]),
                         "book_pdf": bool(tools["browser"]), "icon_export": bool(tools["browser"]),
                         "icns": bool(tools["browser"] and iconutil), "sting": bool(tools["browser"] and ffmpeg)},
                 "hint": None if tools["browser"] else MISSING_HINT if not tools["qlmanage"] else
                 "qlmanage only: PNG references work (labelled fallback), board screenshots and PDF do not"})


def cmd_init(args):
    name = " ".join((args.brand or "").split())
    if not name:
        raise usage("--brand needs the brand name in its exact spelling")
    brand = slug(args.slug or name)
    if os.path.isfile(state_path(brand)):
        result = summary(load_state(brand))
        result["existing"] = True
        return emit(result)
    state = {"schema": SCHEMA, "version": 0, "brand": {"name": name, "slug": brand}, "created_at": now(),
             "slots": {slot: new_slot() for slot in FOUNDATION + ["brandbook"]}, "log": []}
    log(state, "init")
    save_state(state, None)
    result = summary(state)
    result["existing"] = False
    return emit(result)


def cmd_status(args):
    return emit(summary(load_state(resolve_brand(args.brand))))


def validate_data(slot, data, origin):
    if slot == "palette":
        checked = check_palette(data)
        if origin == "user":  # official colours are authoritative: a contrast failure is reported, never "fixed"
            failing = [p for p in checked["problems"] if "below 4.5:1" in p]
            checked["notes"] += ["official palette: " + p for p in failing]
            checked["problems"] = [p for p in checked["problems"] if p not in failing]
        if checked["problems"]:
            raise Fail("palette_problems", "fix the palette before it is shown", extra={"problems": checked["problems"], "notes": checked["notes"]})
        return checked
    if slot == "strategy":
        for key in ("offer", "audience"):
            if not str(data.get(key) or "").strip():
                raise usage("strategy data needs %r (write \"not stated\" when the user did not say)" % key)
        words = data.get("tone_words")
        if not isinstance(words, list) or not 3 <= len(words) <= 5:
            raise usage("strategy data needs tone_words: a list of 3 to 5 words")
    if slot == "typography":
        for role in ("display", "body"):
            font = data.get(role)
            if not isinstance(font, dict) or not str(font.get("family") or "").strip():
                raise usage("typography data needs %s.family (a font family NAME)" % role)
            if (font.get("fallback") or "sans-serif") not in GENERIC_FONTS:
                raise usage("%s.fallback must be one of %s" % (role, ", ".join(GENERIC_FONTS)))
            if not str(font.get("traits") or "").strip():
                raise usage("%s.traits is required: the visual description the BRAND LOCK gives to image models" % role)
    if slot == "logo" and origin == "generated":
        for key in ("mark_type", "idea"):
            if not str(data.get(key) or "").strip():
                raise usage("logo data needs %r so that three candidates can be told apart" % key)
    return data


def prompt_of(args):
    if args.prompt_file:
        return read_text_file(args.prompt_file, "--prompt-file")
    if args.plan_file:
        plan = read_json_file(args.plan_file, "--plan-file")
        wanted = args.job or args.id
        jobs = [job for job in plan.get("jobs") or [] if isinstance(job, dict)]
        for job in sorted(jobs, key=lambda j: str(j.get("id") or "") != wanted):  # the exact id wins over a prefix
            if str(job.get("id") or "").startswith(wanted):
                prompt = (job.get("input") or {}).get("prompt")
                if isinstance(prompt, str):
                    return prompt
        raise usage("no job whose id starts with %r and has input.prompt in %s" % (wanted, args.plan_file))
    return None


def open_round(state, slot, slot_state, origin, change=None, user_asked=None):
    previous = current_revision(slot_state)
    if previous is not None and previous["status"] == "candidate":
        previous["status"] = "superseded"
    revision = {"rev": len(slot_state["revisions"]) + 1, "status": "candidate", "origin": origin, "created_at": now(),
                "built_from": stamp_built_from(state, slot, origin), "candidates": [], "change": change,
                "user_asked": user_asked, "approved_candidate": None, "approval_note": None}
    slot_state["revisions"].append(revision)
    if slot_state["status"] != "approved":
        slot_state["status"] = "candidate"
    return revision


def cmd_new_round(args):
    brand = resolve_brand(args.brand)
    state = load_state(brand)
    read_version = state["version"]
    slot = check_slot_name(args.slot)
    slot_state = state["slots"].get(slot)
    revision = current_revision(slot_state) if slot_state else None
    if revision is None or revision["status"] != "candidate":
        raise usage("new-round replaces an OPEN review round; %s has none (add-candidate opens a round by itself)" % slot)
    change = " ".join((args.change or "").split())
    if len(change) < 3:
        raise usage("--change must say what is different this time (idea, wording, route)")
    asked = " ".join((args.user_asked or "").split()) or None
    if not asked and int(slot_state.get("rerolls") or 0) >= MAX_REROLLS:
        raise Fail("reroll_limit", "slot %s already had %d re-roll rounds" % (slot, MAX_REROLLS),
                   hint="change the route or the idea, or ask the user; a round they ask for is opened with --user-asked \"<their words>\"")
    if not asked:
        slot_state["rerolls"] = int(slot_state.get("rerolls") or 0) + 1
    fresh = open_round(state, slot, slot_state, revision["origin"], change, asked)
    log(state, "new_round", slot, revision=fresh["rev"], change=change, user_asked=asked)
    save_state(state, read_version)
    return emit({"ok": True, "slot": slot, "revision": fresh["rev"], "superseded": revision["rev"],
                 "rerolls_left": MAX_REROLLS - int(slot_state.get("rerolls") or 0),
                 "hint": "job ids for this round end in -r%d; a candidate carried over unchanged is registered again with its old file" % fresh["rev"]})


def cmd_add_candidate(args):
    brand = resolve_brand(args.brand)
    state = load_state(brand)
    read_version = state["version"]
    slot = check_slot_name(args.slot)
    origin = args.origin
    if slot in ("lock", "brandbook"):
        raise usage("the %s candidate is registered by `%s`, not by add-candidate" % (slot, "lock --data" if slot == "lock" else "book"))
    lettered = LETTERED.get(slot)
    if lettered and not re.fullmatch(r"%s-[A-F]" % lettered, args.id):
        raise usage("candidate ids in slot %s are %s-A, %s-B, %s-C (stable across rounds)" % (slot, lettered, lettered, lettered))
    if not lettered and not re.fullmatch(r"[a-z][a-z0-9]*(-[A-Za-z0-9]+)*", args.id):
        raise usage("--id must be a short stable slug such as card-A or strategy")
    slot_state = state["slots"].setdefault(slot, new_slot())
    if origin != "user":
        gate = STAGE_GATE.get(slot, ["lock"] if slot.startswith("app-") else [])
        missing = [name for name in gate if state["slots"].get(name, {}).get("status") != "approved"]
        if missing:
            raise Fail("upstream_missing", "stage order: %s needs an approved %s first" % (slot, " and ".join(missing)),
                       hint="finish that review and get the user's approval; do not generate ahead", extra={"missing": missing})
    if slot in ("strategy", "palette", "typography") and not args.data:
        raise usage("slot %s needs --data <file.json>" % slot)
    data = validate_data(slot, read_json_file(args.data, "--data") if args.data else {}, origin)
    if not args.file and slot not in ("strategy", "palette", "typography"):
        raise usage("slot %s needs at least one --file" % slot)
    prompt = prompt_of(args)
    prompt_sha = prompt_hash(prompt) if prompt is not None else None
    text_record = None
    if args.no_text:
        text_record = {"none": True}
    elif args.expect_text_file or args.read_text_file:
        if not (args.expect_text_file and args.read_text_file):
            raise usage("--expect-text-file and --read-text-file go together")
        text_record = compare_text(read_text_file(args.expect_text_file, "--expect-text-file"),
                                   read_text_file(args.read_text_file, "--read-text-file"))
    elif origin == "generated" and (slot == "logo" or slot.startswith("app-")):
        raise usage("generated %s candidates need the text read back: --expect-text-file + --read-text-file, or --no-text" % slot)
    files = []
    for path in args.file or []:
        if not os.path.isfile(path):
            raise usage("no such file: %s" % path)
        item = {"path": rel(path), "sha256": sha256_file(path), "bytes": os.path.getsize(path)}
        if path.lower().endswith(".svg"):
            _root, info = inspect_svg(path)
            if info["unsafe"]:
                raise Fail("svg_unsafe", "%s must not be shown or shipped" % path, extra={"reasons": info["unsafe"]},
                           hint="re-roll the candidate; never hand-clean a returned SVG during review")
            item["svg"] = {k: info[k] for k in ("bytes", "paths", "shapes", "colors", "geometry_sha256", "text_elements",
                                                 "full_canvas_background", "warnings")}
        files.append(item)

    revision = current_revision(slot_state)
    if revision is None or revision["status"] != "candidate":
        revision = open_round(state, slot, slot_state, origin)
    earlier = slot_state["revisions"][-2] if len(slot_state["revisions"]) > 1 else None
    carried = earlier is not None and any(c["id"] == args.id and [f["sha256"] for f in c["files"]] == [f["sha256"] for f in files]
                                          for c in earlier["candidates"]) and bool(files)
    attempts = slot_state.setdefault("attempts", {}).setdefault(args.id, [])
    if prompt_sha and not carried and prompt_sha in [a.get("prompt_sha256") for a in attempts]:
        raise Fail("prompt_unchanged", "%s was already tried with exactly this prompt" % args.id,
                   hint="a re-roll must change what the failure names: the wording, the size of the text, the idea, or the route")
    failed = [a for a in attempts if a.get("failed") and a.get("rev") == revision["rev"]]
    if len(failed) > MAX_REROLLS:
        raise Fail("reroll_limit", "%s failed %d times in round r%d" % (args.id, len(failed), revision["rev"]),
                   hint="drop this direction or change the route, and say so to the user")
    if slot.startswith("app-") and origin == "generated":
        _, lock = require_approved(state, "lock")
        if prompt is None:
            raise usage("generated applications need --prompt-file or --plan-file so the BRAND LOCK can be verified")
        if lock["text_block"].replace("\r\n", "\n") not in prompt.replace("\r\n", "\n"):
            raise Fail("lock_missing_in_prompt", "the prompt for %s does not contain the approved BRAND LOCK verbatim" % args.id,
                       hint="paste the block printed by `lock --brand %s` unchanged; never paraphrase or trim it" % brand)
    if text_record is not None and not text_record.get("none") and not text_record["ok"]:
        attempts.append({"ts": now(), "rev": revision["rev"], "prompt_sha256": prompt_sha, "failed": "text_mismatch"})
        log(state, "candidate_refused", slot, candidate=args.id, reason="text_mismatch")
        save_state(state, read_version)
        raise Fail("text_mismatch", "the words in %s differ from the requested ones: a failed output, never shown as a candidate" % args.id,
                   hint="re-roll with the prompt changed (spell the string letter by letter, fewer words, larger type)",
                   extra={"diff": text_record["diff"], "missing": text_record["missing"], "unexpected": text_record["unexpected"],
                          "failed_attempts": len(failed) + 1, "attempts_left": max(0, MAX_REROLLS - len(failed))})
    for other in revision["candidates"]:
        if other["id"] == args.id:
            raise Fail("duplicate_candidate", "%s already exists in %s r%d" % (args.id, slot, revision["rev"]),
                       hint="ids are stable: another attempt at the same letter belongs to a new round (new-round)")
        if prompt_sha and other.get("prompt_sha256") == prompt_sha:
            raise Fail("duplicate_prompt", "%s uses exactly the prompt of %s" % (args.id, other["id"]),
                       hint="three candidates are three different ideas, not three runs of one prompt")
        if slot == "logo" and origin == "generated" and all(
                " ".join(str(other["data"].get(k, "")).lower().split()) == " ".join(str(data.get(k, "")).lower().split())
                for k in ("mark_type", "idea")):
            raise Fail("duplicate_direction", "%s repeats the mark type and idea of %s" % (args.id, other["id"]))
        if slot == "palette" and sorted(c["hex"] for c in other["data"]["colors"]) == sorted(c["hex"] for c in data["colors"]):
            raise Fail("duplicate_palette", "%s has the same colours as %s" % (args.id, other["id"]))
        if slot == "typography" and sorted(other["data"][r]["family"].lower() for r in ("display", "body")) == sorted(
                data[r]["family"].lower() for r in ("display", "body")):
            raise Fail("duplicate_pairing", "%s pairs the same families as %s" % (args.id, other["id"]))
    candidate = {"id": args.id, "files": files, "data": data, "note": args.note, "prompt_sha256": prompt_sha, "text": text_record,
                 "carried_from": earlier["rev"] if carried and earlier is not None else None, "endpoint_id": args.endpoint, "request_id": args.request_id,
                 "est_cost_usd": args.cost, "added_at": now()}
    revision["candidates"].append(candidate)
    attempts.append({"ts": now(), "rev": revision["rev"], "prompt_sha256": prompt_sha, "failed": None})
    log(state, "add_candidate", slot, candidate=args.id, revision=revision["rev"])
    save_state(state, read_version)
    result = {"ok": True, "slot": slot, "revision": revision["rev"], "candidate": args.id, "carried_over": carried,
              "candidates": [c["id"] for c in revision["candidates"]], "built_from": revision["built_from"],
              "rerolls_left": MAX_REROLLS - int(slot_state.get("rerolls") or 0), "warnings": []}
    if slot == "palette":
        result.update({"notes": data["notes"], "text_pairs": data["text_pairs"]})
    if slot == "logo" and origin == "generated" and prompt is None:
        result["warnings"].append("no prompt recorded: an unchanged re-roll cannot be detected; pass --prompt-file or --plan-file")
    for item in files:
        result["warnings"] += ["%s: %s" % (item["path"], w) for w in (item.get("svg") or {}).get("warnings", [])]
    return emit(result)


def cmd_add_asset(args):
    brand = resolve_brand(args.brand)
    state = load_state(brand)
    read_version = state["version"]
    slot = check_slot_name(args.slot)
    slot_state = state["slots"].get(slot)
    if not slot_state or slot_state["status"] != "approved":
        raise Fail("not_approved", "assets are derived from an approved revision; %s is %s" % (slot, (slot_state or {}).get("status", "draft")))
    if not re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", args.role):
        raise usage("--role is a slug such as primary, mono, reversed, nobg, png-1024, icon, pdf")
    if not os.path.isfile(args.file):
        raise usage("no such file: %s" % args.file)
    item = {"role": args.role, "path": rel(args.file), "sha256": sha256_file(args.file), "bytes": os.path.getsize(args.file),
            "from_revision": slot_state["approved_revision"], "added_at": now(),
            "upstream": {n: state["slots"][n]["approved_revision"] for n in ("palette", "logo")
                         if n != slot and state["slots"].get(n, {}).get("approved_revision")}}
    if args.file.lower().endswith(".svg"):
        _root, info = inspect_svg(args.file)
        if info["unsafe"]:
            raise Fail("svg_unsafe", "%s must not be shipped" % args.file, extra={"reasons": info["unsafe"]})
        _, approved = require_approved(state, slot)
        origin = next((f for f in approved["files"] if f.get("svg")), None)
        source = origin["svg"]["geometry_sha256"] if origin else None
        accepted = {source}
        if origin and source and os.path.isfile(origin["path"]):
            original, _size = load_svg(origin["path"])
            if geometry_fingerprint(original) == source:
                accepted.add(plate_free_fingerprint(original))
        if slot == "logo" and args.role in ("primary", "mono", "reversed", "nobg") and source and info["geometry_sha256"] not in accepted:
            raise Fail("geometry_changed", "%s does not have the geometry of the approved %s" % (args.file, approved["id"]),
                       hint="variants are made by colour substitution or by removing the background plate (svg-recolor, "
                            "svg-variants); a redrawn mark is a new candidate")
        item["geometry_sha256"] = info["geometry_sha256"]
    slot_state["assets"] = [a for a in slot_state.get("assets", []) if a["role"] != args.role] + [item]
    log(state, "add_asset", slot, role=args.role)
    save_state(state, read_version)
    return emit({"ok": True, "slot": slot, "role": args.role, "path": item["path"], "from_revision": item["from_revision"]})


def cmd_approve(args):
    brand = resolve_brand(args.brand)
    state = load_state(brand)
    read_version = state["version"]
    slot = check_slot_name(args.slot)
    note = " ".join((args.note or "").split())
    if not note:
        raise usage("--note must quote the user's own words of approval; silence or a successful job is not approval")
    slot_state = state["slots"].get(slot)
    if not slot_state or not slot_state["revisions"]:
        raise Fail("nothing_to_approve", "slot %s has no candidates" % slot)
    wanted = [r for r in slot_state["revisions"] if (args.revision is None or r["rev"] == args.revision)
              and any(c["id"] == args.candidate for c in r["candidates"])]
    if not wanted:
        raise Fail("unknown_candidate", "no candidate %s in slot %s%s" % (args.candidate, slot, " r%d" % args.revision if args.revision else ""),
                   extra={"candidates": [c["id"] for c in slot_state["revisions"][-1]["candidates"]]})
    revision = wanted[-1]
    if revision["origin"] != "user":
        missing = [name for name in deps_of(state, slot) if name in FOUNDATION and state["slots"].get(name, {}).get("status") != "approved"]
        if missing:
            raise Fail("upstream_missing", "stage order: approve %s before %s" % (" and ".join(missing), slot), extra={"missing": missing})
    if revision["status"] == "approved" and revision.get("approved_candidate") == args.candidate:
        return emit({"ok": True, "slot": slot, "revision": revision["rev"], "candidate": args.candidate, "already": True,
                     "invalidated": [], "next": next_step(state)})
    kept = revision["status"] in ("invalidated", "superseded")
    fresh = stamp_built_from(state, slot, revision["origin"])
    if kept:
        revision["built_from"] = fresh  # the user looked at it against the current upstream and keeps it
    else:
        for name, number in fresh.items():  # upstream approved after this round opened (strategy + palette share a review)
            revision["built_from"].setdefault(name, number)
    for other in slot_state["revisions"]:
        if other is not revision and other["status"] in ("approved", "candidate"):
            other["status"] = "superseded"
    revision.update({"status": "approved", "approved_candidate": args.candidate, "approval_note": note, "approved_at": now()})
    slot_state.update({"status": "approved", "approved_revision": revision["rev"], "rerolls": 0, "attempts": {}})
    slot_state.pop("invalidated", None)
    order = stage_order(state)
    invalidated = sorted(propagate(state, slot), key=order.index)
    log(state, "approve", slot, candidate=args.candidate, revision=revision["rev"], note=note, invalidated=invalidated or None, kept=kept or None)
    save_state(state, read_version)
    still = [n for n, s in state["slots"].items() if s["status"] == "approved" and n != slot]
    return emit({"ok": True, "slot": slot, "revision": revision["rev"], "candidate": args.candidate, "kept_after_upstream_change": kept,
                 "invalidated": invalidated, "still_valid": still, "stale_assets": stale_assets(state), "next": next_step(state),
                 "hint": "tell the user what became stale and what rebuilding costs; rebuild only what they confirm" if invalidated else None})


def cmd_invalidate(args):
    brand = resolve_brand(args.brand)
    state = load_state(brand)
    read_version = state["version"]
    slot = check_slot_name(args.slot)
    if not (args.reason or "").strip():
        raise usage("--reason is required")
    if slot not in state["slots"] or not mark_invalid(state, slot, "manual: " + args.reason.strip()):
        raise Fail("nothing_to_invalidate", "slot %s has no live revision" % slot)
    invalidated = [slot] + sorted(propagate(state, slot), key=stage_order(state).index)
    log(state, "invalidate", slot, reason=args.reason.strip(), invalidated=invalidated)
    save_state(state, read_version)
    return emit({"ok": True, "invalidated": invalidated, "next": next_step(state)})


def cmd_lock(args):
    brand = resolve_brand(args.brand)
    state = load_state(brand)
    read_version = state["version"]
    if args.data:
        missing = [n for n in ("strategy", "palette", "logo", "typography") if state["slots"][n]["status"] != "approved"]
        if missing:
            raise Fail("upstream_missing", "the lock freezes approved slots; not approved: %s" % ", ".join(missing), extra={"missing": missing})
        rules = read_json_file(args.data, "--data")
        text, number = compose_lock(state, rules)
        path = os.path.join(project_dir(brand), "lock-r%d.txt" % number)
        write_atomic(path, text + "\n")
        slot_state = state["slots"]["lock"]
        for other in slot_state["revisions"]:
            if other["status"] == "candidate":
                other["status"] = "superseded"
        slot_state["revisions"].append({
            "rev": number, "status": "candidate", "origin": "local", "created_at": now(), "built_from": stamp_built_from(state, "lock", "local"),
            "candidates": [{"id": "lock", "files": [{"path": rel(path), "sha256": sha256_file(path), "bytes": os.path.getsize(path)}],
                            "data": rules, "text_block": text, "note": None, "added_at": now()}],
            "change": None, "user_asked": None, "approved_candidate": None, "approval_note": None})
        if slot_state["status"] != "approved":
            slot_state["status"] = "candidate"
        log(state, "lock_composed", "lock", revision=number)
        save_state(state, read_version)
        return emit({"ok": True, "status": "candidate", "revision": number, "path": rel(path), "text": text,
                     "hint": "show a plain-language summary, stop, then approve --slot lock --candidate lock"})
    revision, candidate = approved_candidate(state["slots"]["lock"])
    if revision is None or candidate is None:
        raise Fail("lock_not_approved", "the BRAND LOCK is %s" % state["slots"]["lock"]["status"],
                   hint="no application is generated without an approved lock; rebuild it with --data and get it approved",
                   extra={"invalidated_by": (state["slots"]["lock"].get("invalidated") or {}).get("by")})
    if args.out:
        write_atomic(args.out, candidate["text_block"] + "\n")
    return emit({"ok": True, "status": "approved", "revision": revision["rev"], "built_from": revision["built_from"],
                 "text": candidate["text_block"], "out": rel(args.out) if args.out else None})


def ledger_prompts(label):
    """job id -> last submitted prompt under this label, read from gm.py's ledger (read only, local)."""
    known = {}
    try:
        with open(os.path.join(".genmedia", "runs.jsonl"), "rb") as handle:
            lines = handle.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return known
    for raw in lines:
        try:
            line = json.loads(raw)
        except ValueError:
            continue
        if isinstance(line, dict) and line.get("label") == label and line.get("job_id") and isinstance(line.get("input"), dict):
            known[line["job_id"]] = line["input"].get("prompt")
    return known


def at_references(node):
    """Whole-string "@job" values that pipeline.py fill still has to resolve ("@@x" is its escape for a literal)."""
    if isinstance(node, str):
        return [node] if node.startswith("@") and not node.startswith("@@") else []
    children = node.values() if isinstance(node, dict) else node if isinstance(node, list) else []
    return [found for child in children for found in at_references(child)]


def cmd_plan(args):
    """Build a gm.py batch plan from prompt FILES, before any money is spent: the approved BRAND LOCK is
    substituted for the token by the script (verbatim by construction), and everything add-candidate would
    refuse after the spend is refused here instead."""
    brand = resolve_brand(args.brand)
    state = load_state(brand)
    spec = read_json_file(args.spec, "--spec")
    if not isinstance(spec.get("jobs"), list) or not spec["jobs"]:
        raise usage('--spec must be {"label": "...", "jobs": [{"id", "endpoint_id", "prompt_file", "input"}, ...]}')
    label = slug(spec.get("label") or brand)
    _, lock = approved_candidate(state["slots"].get("lock") or new_slot())
    ledger, jobs, seen, warnings, total = ledger_prompts(label), [], {}, [], 0.0
    for index, item in enumerate(spec["jobs"]):
        where = "jobs[%d]" % index
        if not isinstance(item, dict) or not isinstance(item.get("input", {}), dict):
            raise usage("%s must be an object whose `input` is an object" % where)
        job_id = str(item.get("id") or "")
        match = JOB_ID.fullmatch(job_id)
        if not match:
            raise usage("%s.id %r: use logo-A-r1, app-business-card-r1, app-social-post-B-r1; a retry inside a round adds -t2 or -t3" % (where, job_id))
        if not re.fullmatch(r"[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)+", str(item.get("endpoint_id") or "")):
            raise usage("%s.endpoint_id must be a full endpoint ID" % where)
        if job_id in seen.values():
            raise usage("duplicate job id %r" % job_id)
        slot = "logo" if match.group("logo") else match.group("app")
        gate = ["palette"] if slot == "logo" else ["lock"]
        missing = [name for name in gate if state["slots"].get(name, {}).get("status") != "approved"]
        if missing:
            raise Fail("lock_not_approved" if slot != "logo" else "upstream_missing",
                       "stage order: %s needs an approved %s before anything is generated" % (slot, " and ".join(missing)),
                       hint="finish that review and get the user's approval; do not generate ahead", extra={"missing": missing})
        slot_state = state["slots"].get(slot) or new_slot()
        revision = current_revision(slot_state)
        expected = revision["rev"] if revision and revision["status"] == "candidate" else len(slot_state["revisions"]) + 1
        if int(match.group("rev")) != expected:
            raise Fail("round_mismatch", "%s: slot %s is in round r%d" % (job_id, slot, expected),
                       hint="job ids end in the round number; gm.py resumes a known id instead of submitting it again")
        if not item.get("prompt_file") or "prompt" in item.get("input", {}):
            raise usage("%s: give the prompt as `prompt_file` (plain text), never inside `input`" % where)
        source = item["prompt_file"]
        prompt = read_text_file(source, "%s.prompt_file" % where).replace("\r\n", "\n").strip()
        if slot != "logo":
            if prompt.count(LOCK_TOKEN) != 1:
                raise Fail("lock_missing_in_prompt", "%s must contain the line %s exactly once" % (source, LOCK_TOKEN),
                           hint="role line for the references, then %s on its own line, then the application block" % LOCK_TOKEN)
            prompt = prompt.replace(LOCK_TOKEN, require_approved(state, "lock")[1]["text_block"])
        elif LOCK_TOKEN in prompt:
            raise usage("%s: a logo prompt cannot carry the BRAND LOCK; the lock is built from the approved logo" % source)
        left = [m.group(0) for m in PLACEHOLDER.finditer(prompt.replace(lock["text_block"], "") if lock else prompt)]
        if left:
            raise Fail("placeholder_left", "%s still contains %s" % (source, ", ".join(sorted(set(left))[:5])),
                       hint="a placeholder that reaches the model is a wasted job; fill it or delete it")
        digest = prompt_hash(prompt)
        if digest in seen:
            raise Fail("duplicate_prompt", "%s uses exactly the prompt of %s" % (job_id, seen[digest]),
                       hint="three candidates are three different ideas, not three runs of one prompt")
        if any(digest == a.get("prompt_sha256") for tries in slot_state.get("attempts", {}).values() for a in tries):
            raise Fail("prompt_unchanged", "%s: slot %s was already tried with exactly this prompt" % (job_id, slot),
                       hint="a re-roll must change what the failure names: the wording, the size of the text, the idea, or the route")
        if job_id in ledger:
            if ledger[job_id] != prompt:
                raise Fail("job_id_reused", "%s is already in the run ledger with another prompt" % job_id,
                           hint="gm.py resumes a known id and submits nothing: name the retry %s-t2 (or open a new round)" % job_id.split("-t")[0])
            warnings.append("%s is already in the run ledger: gm.py batch resumes it and submits nothing new" % job_id)
        if slot == "logo" and re.search(r"#[0-9a-fA-F]{6}\b", prompt):
            warnings.append("%s: hex codes in a vector prompt are ignored or drawn as text; pass colours in `colors`" % job_id)
        resolved = os.path.join(project_dir(brand), "prompts", "resolved", job_id + ".txt")
        write_atomic(resolved, prompt + "\n")
        seen[digest] = job_id
        job = {"id": job_id, "endpoint_id": item["endpoint_id"], "input": dict(item.get("input") or {}, prompt=prompt)}
        for key in ("est_cost_usd", "download"):
            if item.get(key) is not None:
                job[key] = item[key]
        total += float(item.get("est_cost_usd") or 0)
        jobs.append(job)
    plan = {"label": label, "max_parallel": int(spec.get("max_parallel") or min(4, len(jobs))), "jobs": jobs}
    write_atomic(args.out, json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    references = sorted(set(found for job in jobs for found in at_references({k: v for k, v in job["input"].items() if k != "prompt"})))
    return emit({"ok": True, "plan": rel(args.out), "label": label, "jobs": [j["id"] for j in jobs],
                 "lock_injected": [j["id"] for j in jobs if not j["id"].startswith("logo-")],
                 "est_cost_usd": round(total, 4), "unresolved_references": references, "warnings": warnings,
                 "next": ("pipeline.py fill --template %s --out <plan.json>, then gm.py batch --plan <plan.json>" % rel(args.out))
                 if references else "gm.py batch --plan %s" % rel(args.out)})


def cmd_board(args):
    brand = resolve_brand(args.brand)
    state = load_state(brand)
    slots = [check_slot_name(s) for s in args.slot]
    first = state["slots"].get(slots[0]) or new_slot()
    number = args.revision or (current_revision(first) or {}).get("rev") or 1
    out = args.out or os.path.join(output_dir(brand), "boards", "%s-r%d.html" % (slots[0], number))
    shown = build_board(state, slots, args.revision, out, args.webfonts)
    result = {"ok": True, "board": rel(out), "slots": slots, "candidates": shown, "png": None,
              "self_contained": not args.webfonts, "open": file_url(out)}
    if args.png:
        target = os.path.splitext(out)[0] + ".png"
        try:
            rows = max(1, math.ceil(len(shown) / 3.0))
            made = export_png(out, target, 1400, min(12000, 260 + rows * (900 if slots[0] != "logo" else 620)), "opaque")
            result.update({"png": rel(target), "png_tool": made["tool"]})
        except Fail as exc:
            result["png_reason"] = exc.message if exc.kind != "tool_missing" else "no browser: you cannot look at this board; say so"
    return emit(result)


def cmd_book(args):
    brand = resolve_brand(args.brand)
    state = load_state(brand)
    read_version = state["version"]
    out_dir = args.out or os.path.join(output_dir(brand), "brandbook")
    out, used = build_book(state, out_dir)
    digest = sha256_file(out)
    slot_state = state["slots"].setdefault("brandbook", new_slot())
    revision = current_revision(slot_state)
    same = revision is not None and revision["status"] in ("candidate", "approved") and revision["candidates"][0]["files"][0]["sha256"] == digest
    if revision is None or not same:
        revision = {"rev": len(slot_state["revisions"]) + 1, "status": "candidate", "origin": "local", "created_at": now(),
                    "built_from": stamp_built_from(state, "brandbook", "local"), "change": None, "user_asked": None,
                    "approved_candidate": None, "approval_note": None,
                    "candidates": [{"id": "brandbook", "files": [{"path": rel(out), "sha256": digest, "bytes": os.path.getsize(out)}],
                                    "data": {"applications": used}, "note": None, "added_at": now()}]}
        slot_state["revisions"].append(revision)
    if revision["status"] != "approved":
        # The book only arranges what the user already approved: it inherits that approval instead of asking again.
        lock_revision, _ = require_approved(state, "lock")
        for other in slot_state["revisions"]:
            if other is not revision and other["status"] in ("candidate", "approved"):
                other["status"] = "superseded"
        revision.update({"status": "approved", "approved_candidate": "brandbook", "approved_at": now(),
                         "approval_note": 'derived from approved slots only; lock r%d approved as "%s"'
                                          % (lock_revision["rev"], lock_revision.get("approval_note") or "")})
        slot_state.update({"status": "approved", "approved_revision": revision["rev"]})
        slot_state.pop("invalidated", None)
        log(state, "book_built", "brandbook", revision=revision["rev"], derived=True)
        save_state(state, read_version)
    result = {"ok": True, "book": rel(out), "revision": revision["rev"], "status": revision["status"], "derived": True,
              "new_revision": not same, "applications": used, "pdf": None, "open": file_url(out)}
    if args.pdf:
        browser = converters()["browser"]
        if not browser:
            result["pdf_reason"] = "no Chromium-family browser here: deliver the HTML; printing it to PDF from any browser gives the same pages"
        else:
            pdf = os.path.join(out_dir, "brandbook.pdf")
            run_browser(browser, "--print-to-pdf", os.path.abspath(pdf), file_url(out), ["--no-pdf-header-footer", "--print-to-pdf-no-header"])
            result["pdf"] = rel(pdf)
    return emit(result)


def cmd_export_list(args):
    brand = resolve_brand(args.brand)
    state = load_state(brand)
    files, problems, pending = [], [], []
    for name in stage_order(state):
        slot_state = state["slots"].get(name) or new_slot()
        if slot_state["status"] == "invalidated":
            problems.append("%s is invalidated (by %s): rebuild, re-approve, or leave it out and say so" % (name, slot_state["invalidated"]["by"]))
            continue
        revision, candidate = approved_candidate(slot_state)
        if revision is None or candidate is None:
            pending.append(name)
            continue
        folder = {"logo": "logo", "palette": "palette", "typography": "typography", "strategy": "strategy", "lock": "",
                  "brandbook": "brandbook"}.get(name, "applications/" + name[4:])
        for item in candidate["files"]:
            if name in ("lock", "brandbook"):
                continue
            files.append({"slot": name, "revision": revision["rev"], "candidate": candidate["id"], "role": "approved-candidate",
                          "path": item["path"], "to": "/".join(p for p in (folder, "source" if name == "logo" else "", os.path.basename(item["path"])) if p)})
        for asset in slot_state.get("assets", []):
            entry = {"slot": name, "revision": asset["from_revision"], "role": asset["role"], "path": asset["path"],
                     "to": "/".join(p for p in (folder, os.path.basename(asset["path"])) if p)}
            if asset.get("dir"):                # a platform export is a folder: it travels whole, next to its record
                entry.update({"dir": asset["dir"], "to": name + "/" + os.path.basename(asset["path"])})
            files.append(entry)
    for entry in stale_assets(state):
        problems.append("asset %s/%s is stale: %s" % (entry["slot"], entry["role"], ", ".join(entry["why"])))
    for entry in files:
        entry["exists"] = os.path.isfile(entry["path"])
        entry["kind"] = "editable" if entry["path"].lower().endswith(EDITABLE_EXT) else "flattened"
        if not entry["exists"]:
            problems.append("missing file: %s" % entry["path"])
    result = {"ok": not problems, "brand": state["brand"], "files": files, "pending": pending, "problems": problems, "package": None}
    if args.copy:
        package = args.out or os.path.join(output_dir(brand), "package")
        os.makedirs(package, exist_ok=True)
        for entry in files:
            if entry["exists"]:
                target = os.path.join(package, *entry["to"].split("/"))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                if entry.get("dir") and os.path.isdir(entry["dir"]):
                    shutil.copytree(entry["dir"], os.path.dirname(target), dirs_exist_ok=True)
                shutil.copyfile(entry["path"], target)
                entry["sha256"] = sha256_file(target)
        palette, typography = approved_data(state, "palette"), approved_data(state, "typography")
        _, lock = approved_candidate(state["slots"].get("lock") or new_slot())
        _, book = approved_candidate(state["slots"].get("brandbook") or new_slot())
        extras = []
        if palette:
            css = ":root {\n" + "".join("  --brand-%s-%s: %s; /* %s */\n" % (c["role"], slug(c["name"], "colour").lower(), c["hex"], c["name"])
                                         for c in palette["colors"]) + "}\n"
            write_atomic(os.path.join(package, "palette", "palette.css"), css)
            write_atomic(os.path.join(package, "palette", "palette.json"), json.dumps(palette, ensure_ascii=False, indent=2) + "\n")
            extras += ["palette/palette.css", "palette/palette.json"]
        if typography:
            note = dict(typography, licence="Font families are named, not bundled. Check the licence of each family before use.")
            write_atomic(os.path.join(package, "typography", "typography.json"), json.dumps(note, ensure_ascii=False, indent=2) + "\n")
            extras.append("typography/typography.json")
        if lock:
            write_atomic(os.path.join(package, "BRAND-LOCK.txt"), lock["text_block"] + "\n")
            extras.append("BRAND-LOCK.txt")
        if book:
            source = os.path.dirname(book["files"][0]["path"])
            if os.path.isdir(source):
                shutil.copytree(source, os.path.join(package, "brandbook"), dirs_exist_ok=True)
                extras.append("brandbook/brandbook.html")
        manifest = {"brand": state["brand"], "generated_at": now(), "state_version": state["version"],
                    "revisions": {n: s.get("approved_revision") for n, s in state["slots"].items() if s.get("approved_revision")},
                    "files": [{k: e[k] for k in ("slot", "revision", "role", "to", "kind", "sha256") if k in e} for e in files if e["exists"]],
                    "generated_files": extras, "pending": pending, "problems": problems,
                    "notes": ["Applications are AI-generated visualisations, not print-ready artwork.",
                              "Font families are names; check each licence.",
                              "A trademark search for the mark is the owner's responsibility."]}
        write_atomic(os.path.join(package, "manifest.json"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        result["package"] = rel(package)
    return emit(result, 0 if not problems else 1)


def cmd_palette_check(args):
    checked = check_palette(read_json_file(args.input, "--input"))
    checked["ok"] = not checked["problems"]
    return emit(checked, 0 if checked["ok"] else 1)


def cmd_text_check(args):
    expected = read_text_file(args.expected_file, "--expected-file") if args.expected_file else args.expected
    read = read_text_file(args.read_file, "--read-file") if args.read_file else args.read
    if expected is None or read is None:
        raise usage("give the expected text and the text you read back (files or inline)")
    result = compare_text(expected, read)
    return emit(result, 0 if result["ok"] else 1)


def cmd_svg_check(args):
    palette = check_palette(read_json_file(args.palette, "--palette")) if args.palette else None
    _root, info = inspect_svg(args.file, palette)
    info["ok"] = not info["unsafe"]
    if info["unsafe"]:
        info.update({"kind": "svg_unsafe", "hint": "do not show or ship this file; re-roll the candidate"})
    return emit(info, 0 if info["ok"] else 1)


def guarded_root(path):
    root, info = inspect_svg(path)
    if info["unsafe"]:
        raise Fail("svg_unsafe", "%s must not be processed or shipped" % path, extra={"reasons": info["unsafe"]})
    return root, info


def cmd_svg_recolor(args):
    mapping = {}
    for pair in args.map:
        if "=" not in pair:
            raise usage("--map takes \"#from=#to\"")
        source, target = pair.split("=", 1)
        mapping[strict_hex(source, "--map source")] = strict_hex(target, "--map target")
    root, info = guarded_root(args.file)
    replaced = recolor(root, mapping, implicit_to=mapping.get("#000000"))
    background_cleared = clear_background(root) if args.transparent_background else False
    if geometry_fingerprint(root) != info["geometry_sha256"]:
        raise Fail("geometry_changed", "internal error: recolouring altered geometry; nothing written")
    write_svg(root, args.out)
    _root, after = inspect_svg(args.out)
    targets = set(mapping.values())
    return emit({"ok": True, "out": rel(args.out), "replaced": replaced, "not_found": sorted(set(mapping) - set(k.split(" ")[0] for k in replaced)),
                 "left_unmapped": [c["hex"] for c in after["colors"] if c["hex"] not in targets],
                 "background_cleared": background_cleared, "geometry_unchanged": True, "geometry_sha256": after["geometry_sha256"]})


def cmd_svg_variants(args):
    ink, paper = strict_hex(args.ink, "--ink"), strict_hex(args.paper, "--paper")
    _root, info = guarded_root(args.file)
    stem = os.path.splitext(os.path.basename(args.file))[0]
    os.makedirs(args.out_dir, exist_ok=True)
    made = {}
    for name, paint, ground in (("mono", ink, paper), ("reversed", paper, ink)):
        root, _ = load_svg(args.file)
        plate = background_element(root)
        mapping = {c["hex"]: paint for c in info["colors"]}
        recolor(root, mapping, implicit_to=paint)
        if plate is not None:
            if args.keep_background:
                set_fill(plate, ground)
            else:
                clear_background(root)
        if geometry_fingerprint(root) != info["geometry_sha256"]:
            raise Fail("geometry_changed", "internal error: the %s variant altered geometry; nothing written" % name)
        made[name] = os.path.join(args.out_dir, "%s-%s.svg" % (stem, name))
        write_svg(root, made[name])
    if info["full_canvas_background"]:
        root, _ = load_svg(args.file)
        clear_background(root)
        made["nobg"] = os.path.join(args.out_dir, "%s-nobg.svg" % stem)
        write_svg(root, made["nobg"])
    warnings = []
    if info["gradients"]:
        warnings.append("gradients were flattened to one colour in mono and reversed")
    if len(info["colors"]) > 1:
        warnings.append("several colours collapsed into one: shapes that touched may merge; look at the result before shipping")
    return emit({"ok": True, "variants": {k: rel(v) for k, v in made.items()}, "ink": ink, "paper": paper,
                 "background": "kept" if args.keep_background else "cleared" if info["full_canvas_background"] else "none found",
                 "geometry_unchanged": True, "warnings": warnings})


def cmd_icon(args):
    background = strict_hex(args.background, "--background")
    if not 0 <= args.padding < 0.45 or not 0 <= args.radius <= 0.5:
        raise usage("--padding is 0 to 0.45 of the side, --radius 0 to 0.5")
    root, _info = guarded_root(args.file)
    clear_background(root)
    box = view_box(root) or [0, 0, 1024, 1024]
    side = 1024
    inner = side * (1 - 2 * args.padding)
    icon = ET.Element("{%s}svg" % SVG_NS, {"viewBox": "0 0 %d %d" % (side, side), "width": str(side), "height": str(side)})
    ET.SubElement(icon, "{%s}rect" % SVG_NS, {"width": str(side), "height": str(side), "rx": "%g" % (args.radius * side), "fill": background})
    nested = ET.SubElement(icon, "{%s}svg" % SVG_NS, {"x": "%g" % (side * args.padding), "y": "%g" % (side * args.padding), "width": "%g" % inner,
                                                      "height": "%g" % inner, "viewBox": "%g %g %g %g" % tuple(box),
                                                      "preserveAspectRatio": "xMidYMid meet"})
    for key in ("fill", "stroke", "style"):
        value = root.get(key)
        if value:
            nested.set(key, value)
    nested.extend(copy.deepcopy(list(root)))
    write_svg(icon, args.out)
    wide = box[2] / box[3] if box[3] else 1
    return emit({"ok": True, "out": rel(args.out), "background": background, "aspect_of_mark": round(wide, 2),
                 "warnings": ["the mark is %.1f times wider than tall: it will be tiny in a square icon; use a compact symbol instead" % wide] if wide > 1.8 else []})


def cmd_png(args):
    if not os.path.isfile(args.file):
        raise usage("no such file: %s" % args.file)
    is_svg = args.file.lower().endswith(".svg")
    if not is_svg and not args.file.lower().endswith((".html", ".htm")):
        raise usage("png converts .svg or .html")
    background = "transparent" if args.background == "transparent" else strict_hex(args.background, "--background")
    width = args.width or args.size or (1024 if is_svg else 1400)
    height = args.height or (None if is_svg else 2000)
    if not 16 <= width <= 8192 or (height and not 16 <= height <= 16384):
        raise usage("sizes: 16 to 8192 px wide, up to 16384 px tall")
    made = export_png(args.file, args.out, width, height, background)
    made.update({"ok": True, "out": rel(args.out), "size": png_size(args.out), "bytes": os.path.getsize(args.out)})
    return emit(made)


# ----------------------------------------------------------------------------------------------- app icon exports

def icon_targets():
    data = read_json_file(os.path.join(HERE, "icon-targets.json"), "icon-targets.json")
    if not isinstance(data, dict) or not isinstance(data.get("platforms"), dict) or not data.get("verified_on"):
        raise Fail("internal", "icon-targets.json next to this script is damaged: restore it from the skill")
    return data


def split_icon(path, background=None):
    """The approved icon as its two ingredients: the plate colour and the mark with the plate cleared. Geometry is untouched."""
    root, info = guarded_root(path)
    plate = strict_hex(background, "--background") if background else info["background_color"] if info["full_canvas_background"] else None
    if not plate or not plate.startswith("#"):
        raise usage("%s has no full-canvas plate to take the colour from: pass --background \"#hex\"" % path)
    clear_background(root)
    box = view_box(root)
    if not box or box[2] <= 0 or box[3] <= 0:
        raise Fail("svg_invalid", "%s has neither a viewBox nor a size: its drawing area is unknown" % path)
    return root, plate, box, info


def measure_mark(root, box, workdir):
    """Render the mark alone and read where its ink is: the crop in user units, and how far the farthest ink lies from
    the crop's centre as a share of the crop's larger side. Pixels, not path maths: strokes, transforms and nested
    viewBoxes all count."""
    source, shot = os.path.join(workdir, "mark.svg"), os.path.join(workdir, "mark.png")
    write_svg(root, source)
    export_png(source, shot, MEASURE_PX, MEASURE_PX, "transparent")
    width, height, channels, rows = png_read(shot)
    spans = ink_spans(rows, width, channels) if channels == 4 else []
    if not spans:
        raise Fail("icon_empty", "the mark rendered empty (or the render carries no alpha): nothing to place",
                   hint="open the SVG: white-on-transparent is fine, an empty or fully opaque canvas is not")
    x0, y0, x1, y1 = ink_box(spans)
    reach = ink_reach(spans, (x0 + x1) / 2.0, (y0 + y1) / 2.0) / max(x1 - x0, y1 - y0)
    x0, y0, x1, y1 = max(0, x0 - 1), max(0, y0 - 1), min(width, x1 + 1), min(height, y1 + 1)   # one pixel of slack
    scale = MEASURE_PX / max(box[2], box[3])
    left, top = (MEASURE_PX - box[2] * scale) / 2.0, (MEASURE_PX - box[3] * scale) / 2.0
    crop = [box[0] + (x0 - left) / scale, box[1] + (y0 - top) / scale, (x1 - x0) / scale, (y1 - y0) / scale]
    return crop, reach


def nest_mark(parent, mark, crop, x, y, width, height):
    nested = copy.deepcopy(mark)
    for key in ("x", "y", "width", "height"):
        nested.attrib.pop(key, None)
    nested.attrib.update({"x": "%g" % x, "y": "%g" % y, "width": "%g" % width, "height": "%g" % height, "overflow": "visible",
                          "viewBox": "%g %g %g %g" % tuple(crop), "preserveAspectRatio": "xMidYMid meet"})
    parent.append(nested)
    return nested


def compose_icon(mark, crop, plate, radius, span, side=1024):
    """One square icon: an optional plate, then the untouched mark nested by viewBox so that its ink spans `span` of the side."""
    icon = ET.Element("{%s}svg" % SVG_NS, {"viewBox": "0 0 %d %d" % (side, side), "width": str(side), "height": str(side)})
    if plate:
        ET.SubElement(icon, "{%s}rect" % SVG_NS, {"width": str(side), "height": str(side), "rx": "%g" % (radius * side), "fill": plate})
    inner = side * span
    nest_mark(icon, mark, crop, (side - inner) / 2.0, (side - inner) / 2.0, inner, inner)
    return icon


def mono_mark(mark, paint="#ffffff"):
    """Every paint of the mark becomes one colour (gradients flatten): Android themes an icon from this layer's alpha."""
    root = copy.deepcopy(mark)
    colors = set()
    for _element, _where, _key, value in iter_paints(root):
        parsed = parse_color(value)
        if parsed and parsed.startswith("#"):
            colors.add(parsed)
    recolor(root, {c: paint for c in colors}, implicit_to=paint)
    return root


def write_ico(path, entries):
    """ICO container with PNG entries: (side, png bytes). A width byte of 0 stands for 256."""
    header = struct.pack("<HHH", 0, 1, len(entries))
    offset, table, blobs = 6 + 16 * len(entries), b"", b""
    for side, blob in entries:
        table += struct.pack("<BBBBHHII", side % 256, side % 256, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
        blobs += blob
    write_atomic(path, header + table + blobs)


def render_all(jobs, workers):
    """jobs: [{svg|html, out, width, height, background}] -> failures. Every render is its own browser run."""
    def one(job):
        try:
            export_png(job["source"], job["out"], job["width"], job["height"], job["background"])
            return None
        except Fail as exc:
            return {"file": rel(job["out"]), "kind": exc.kind, "message": exc.message}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(8, workers))) as pool:
        return [failure for failure in pool.map(one, jobs) if failure]


def sheet_html(name, uris, plate, targets):
    """Review sheet: true pixel sizes on a light and a dark ground, then what each platform mask leaves of the icon."""
    play, web, android = (targets["platforms"][k] for k in ("play", "web", "android"))
    sizes = "".join('<figure><img alt="" src="%s" width="%d" height="%d"><figcaption>%d</figcaption></figure>' % (uris["rounded"], n, n, n)
                    for n in SHEET_SIZES)
    masks = "".join('<figure><img alt="" src="%s" width="112" height="112" style="border-radius:%s"><figcaption>%s</figcaption></figure>'
                    % (uris["square"], radius, esc(label))
                    for label, radius in (("square master", "0"), ("Play mask %d%%" % round(play["mask_radius"] * 100), "%g%%" % (play["mask_radius"] * 100))))
    layer = 112.0 * android["layer_dp"] / android["viewport_dp"]          # the mask shows the inner viewport of the 108 dp layers
    masks += ('<figure><div style="position:relative;width:112px;height:112px;border-radius:50%%;overflow:hidden;background:%s">'
              '<img alt="" src="%s" width="%g" height="%g" style="position:absolute;left:%gpx;top:%gpx"></div><figcaption>adaptive, circle</figcaption></figure>'
              % (plate, uris["foreground"], layer, layer, (112 - layer) / 2, (112 - layer) / 2))
    masks += ('<figure><div style="position:relative;width:112px;height:112px"><img alt="" src="%s" width="112" height="112">'
              '<div style="position:absolute;inset:%g%%;border-radius:50%%;outline:1px dashed #ff2d95"></div></div>'
              '<figcaption>maskable + safe circle</figcaption></figure>' % (uris["maskable"], (0.5 - web["maskable_safe_radius"]) * 100))
    strip = '<div class="strip" style="background:%s;color:%s"><div class="row">%s</div><div class="row">%s</div></div>'
    return ('<!doctype html><html><head><meta charset="utf-8"><title>%s icon sheet</title><style>body{margin:0;font:12px/1.4 system-ui,'
            '-apple-system,"Segoe UI",sans-serif;background:#fff}.pair{display:flex}.strip{flex:1;padding:28px 32px}.row{display:flex;gap:24px;'
            'align-items:flex-end;margin-bottom:24px}figure{margin:0;text-align:center}figcaption{margin-top:6px;opacity:.7;white-space:nowrap}'
            'img{display:block}h1{font-size:15px;margin:0;padding:18px 32px;color:#16181d}</style></head><body><h1>%s app icon, plate %s: true pixel '
            'sizes, then the platform masks. The 1024 and 512 masters are files of their own.</h1><div class="pair">%s%s</div></body></html>'
            % (esc(name), esc(name), esc(plate), strip % ("#f4f4f1", "#16181d", sizes, masks), strip % ("#16181d", "#f4f4f1", sizes, masks)))


ANDROID_ICON_XML = ('<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                    '    <background android:drawable="@color/ic_launcher_background" />\n'
                    '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n'
                    '    <monochrome android:drawable="@mipmap/ic_launcher_monochrome" />\n</adaptive-icon>\n')
FAVICON_SNIPPET = ('<!-- Files go to the site root. The SVG is declared last: among equally fitting icons the last one wins. -->\n'
                   '<link rel="icon" href="/favicon.ico" sizes="%s">\n<link rel="icon" href="/favicon.svg" sizes="any" type="image/svg+xml">\n'
                   '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n<link rel="manifest" href="/site.webmanifest">\n')


def cmd_icon_export(args):
    targets = icon_targets()
    platforms = list(dict.fromkeys(args.platform or ICON_PLATFORMS))
    if not 0 <= args.padding < 0.45:
        raise usage("--padding is 0 to 0.45 of the side")
    if not os.path.isfile(args.file) or not args.file.lower().endswith(".svg"):
        raise usage("icon-export takes the approved icon as an .svg file (a raster icon cannot be split into plate and mark)")
    state = read_version = slot_state = None
    brand = resolve_brand(args.brand) if args.brand else None
    if brand:
        state = load_state(brand)
        read_version = state["version"]
        slot_state = state["slots"].get("app-icon")
        _revision, approved = approved_candidate(slot_state) if slot_state and slot_state["status"] == "approved" else (None, None)
        if not approved:
            raise Fail("not_approved", "platform files are made from the APPROVED icon; the app-icon slot is %s"
                       % ((slot_state or {}).get("status") or "empty"), hint="register the icon in slot app-icon, show it, get it approved, then export")
        if sha256_file(args.file) not in [item.get("sha256") for item in approved["files"]]:
            raise Fail("not_approved", "%s is not the file approved as %s" % (args.file, approved["id"]),
                       hint="export the approved file, or register this one as a new candidate first")
    out_dir = args.out_dir or (os.path.join(output_dir(brand), "app-icon") if brand else None)
    if not out_dir:
        raise usage("--out-dir is required without --brand")
    need_browser("icon-export")
    mark, plate, box, info = split_icon(args.file, args.background)
    workdir = tempfile.mkdtemp(prefix="brandkit-icon-")
    try:
        crop, reach = measure_mark(mark, box, workdir)
        android, web, macos = (targets["platforms"][k] for k in ("android", "web", "macos"))
        span = 1 - 2 * args.padding
        layer = float(android["layer_dp"])
        adaptive_span = min(android["safe_dp"] / layer, max(android["min_logo_dp"] / layer, android["safe_dp"] / layer / 2.0 / reach))
        maskable_span = min(span, web["maskable_safe_radius"] / reach)
        masters = {"square": compose_icon(mark, crop, plate, 0, span), "rounded": compose_icon(mark, crop, plate, macos["radius"], span),
                   "foreground": compose_icon(mark, crop, None, 0, adaptive_span), "monochrome": compose_icon(mono_mark(mark), crop, None, 0, adaptive_span),
                   "maskable": compose_icon(mark, crop, plate, 0, maskable_span), "maskable-ink": compose_icon(mark, crop, None, 0, maskable_span)}
        sources = {}
        for name, element in masters.items():
            sources[name] = os.path.join(workdir, name + ".svg")
            write_svg(element, sources[name])
        jobs, files = [], []

        def add(platform, path, master, side, background, alpha):
            out = os.path.join(out_dir, *path.split("/"))
            jobs.append({"source": sources[master], "out": out, "width": side, "height": side, "background": background})
            files.append({"platform": platform, "path": path, "size": side, "alpha": alpha, "master": master})
        if "ios" in platforms:
            for item in targets["platforms"]["ios"]["files"]:
                add("ios", item["path"], "square", item["size"], plate, False)
        if "play" in platforms:
            for item in targets["platforms"]["play"]["files"]:
                add("play", item["path"], "square", item["size"], "transparent", True)
        if "android" in platforms:
            for density, factor in android["densities"].items():
                side = int(round(layer * factor))
                add("android", "android/res/mipmap-%s/ic_launcher_foreground.png" % density, "foreground", side, "transparent", True)
                add("android", "android/res/mipmap-%s/ic_launcher_monochrome.png" % density, "monochrome", side, "transparent", True)
        if "web" in platforms:
            add("web", "web/apple-touch-icon.png", "square", web["apple_touch"], plate, False)
            for side in web["any_sizes"]:
                add("web", "web/icon-%d.png" % side, "rounded", side, "transparent", True)
            for side in web["maskable_sizes"]:
                add("web", "web/maskable-%d.png" % side, "maskable", side, plate, False)
        if "macos" in platforms:
            for points, factor in macos["iconset"]:
                name = "icon_%dx%d%s.png" % (points, points, "@2x" if factor == 2 else "")
                add("macos", "macos/AppIcon.iconset/" + name, "rounded", points * factor, "transparent", True)
        hidden = [{"source": sources["rounded"], "out": os.path.join(workdir, "ico-%d.png" % side), "width": side, "height": side,
                   "background": "transparent"} for side in (web["ico_sizes"] if "web" in platforms else [])]
        if "web" in platforms:
            hidden.append({"source": sources["maskable-ink"], "out": os.path.join(workdir, "maskable-ink.png"), "width": 512, "height": 512,
                           "background": "transparent"})
        sheet_page = os.path.join(out_dir, "icon-sheet.html")
        write_atomic(sheet_page, sheet_html(args.name or (state or {}).get("brand") or "App", {k: data_uri(v) for k, v in sources.items()}, plate, targets))
        sheet = {"source": sheet_page, "out": os.path.join(out_dir, "icon-sheet.png"), "width": 1500, "height": 600, "background": "opaque"}
        failures = render_all(jobs + hidden + [sheet], args.jobs)
        if failures:
            raise Fail("tool_failed", "%d of %d renders failed; nothing is registered" % (len(failures), len(jobs) + len(hidden) + 1),
                       hint="run the command again; if it repeats, lower --jobs", extra={"failed": failures[:8]})
        written = []
        if "android" in platforms:
            for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
                write_atomic(os.path.join(out_dir, "android", "res", "mipmap-anydpi-v26", name), ANDROID_ICON_XML)
                written.append("android/res/mipmap-anydpi-v26/" + name)
            write_atomic(os.path.join(out_dir, "android", "res", "values", "ic_launcher_background.xml"),
                         '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">%s</color>\n</resources>\n' % plate.upper())
            written.append("android/res/values/ic_launcher_background.xml")
        if "web" in platforms:
            entries = []
            for side in web["ico_sizes"]:
                with open(os.path.join(workdir, "ico-%d.png" % side), "rb") as handle:
                    entries.append((side, handle.read()))
            write_ico(os.path.join(out_dir, "web", "favicon.ico"), entries)
            shutil.copyfile(sources["rounded"], os.path.join(out_dir, "web", "favicon.svg"))
            manifest = {"icons": [{"src": "/icon-%d.png" % n, "sizes": "%dx%d" % (n, n), "type": "image/png", "purpose": "any"} for n in web["any_sizes"]]
                        + [{"src": "/maskable-%d.png" % n, "sizes": "%dx%d" % (n, n), "type": "image/png", "purpose": "maskable"} for n in web["maskable_sizes"]],
                        "theme_color": plate, "background_color": plate}
            if args.name:
                manifest = dict({"name": args.name, "short_name": args.short_name or args.name}, **manifest)
            write_atomic(os.path.join(out_dir, "web", "site.webmanifest"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
            write_atomic(os.path.join(out_dir, "web", "favicon-snippet.html"), FAVICON_SNIPPET % " ".join("%dx%d" % (n, n) for n in web["ico_sizes"]))
            written += ["web/favicon.ico", "web/favicon.svg", "web/site.webmanifest", "web/favicon-snippet.html"]
        icns = None
        iconutil = find_tool("GM_ICONUTIL_BIN", ("iconutil",))
        if "macos" in platforms and iconutil:
            target = os.path.join(out_dir, "macos", "AppIcon.icns")
            done = subprocess.run([iconutil, "-c", "icns", "-o", target, os.path.join(out_dir, "macos", "AppIcon.iconset")],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=BROWSER_TIMEOUT_S, check=False)
            if done.returncode == 0 and os.path.isfile(target):
                icns = "macos/AppIcon.icns"
                written.append(icns)
        problems, warnings = [], []
        for item in files:
            full = os.path.join(out_dir, *item["path"].split("/"))
            if item["alpha"] and item["master"] == "square":
                ensure_alpha_channel(full)
            width, height, depth, kind = png_header(full)
            item.update({"bytes": os.path.getsize(full), "sha256": sha256_file(full), "has_alpha_channel": kind == 6})
            if (width, height) != (item["size"], item["size"]):
                problems.append({"code": "wrong_size", "file": item["path"], "message": "rendered %dx%d, the target is %d" % (width, height, item["size"])})
            if depth != 8 or kind != (6 if item["alpha"] else 2):
                problems.append({"code": "alpha" if not item["alpha"] else "no_alpha", "file": item["path"],
                                 "message": "colour type %d at %d bit; this file must %s an alpha channel" % (kind, depth, "carry" if item["alpha"] else "not carry")})
            cap = targets["platforms"][item["platform"]].get("max_bytes")
            if cap and item["bytes"] > cap:
                problems.append({"code": "bytes_over_cap", "file": item["path"], "message": "%d bytes, the cap is %d" % (item["bytes"], cap)})
        safe = {}
        if "android" in platforms:
            density = max(android["densities"], key=lambda k: android["densities"][k])
            factor = android["densities"][density]
            width, height, channels, rows = png_read(os.path.join(out_dir, "android", "res", "mipmap-" + density, "ic_launcher_foreground.png"))
            spans = ink_spans(rows, width, channels)
            reach_dp = ink_reach(spans, width / 2.0, height / 2.0) / factor if spans and channels == 4 else None
            box_dp = max(ink_box(spans)[2] - ink_box(spans)[0], ink_box(spans)[3] - ink_box(spans)[1]) / factor if spans else None
            safe["android"] = {"ink_radius_dp": round(reach_dp, 1) if reach_dp else None, "safe_radius_dp": android["safe_dp"] / 2.0,
                               "viewport_radius_dp": android["viewport_dp"] / 2.0, "logo_dp": round(box_dp, 1) if box_dp else None}
            if reach_dp is None:
                problems.append({"code": "icon_empty", "file": "android foreground", "message": "the foreground layer rendered empty"})
            elif reach_dp > android["viewport_dp"] / 2.0 + 0.5:
                problems.append({"code": "clipped_by_mask", "file": "android foreground",
                                 "message": "ink reaches %.1f dp from the centre; the masked viewport ends at %.0f dp" % (reach_dp, android["viewport_dp"] / 2.0)})
            elif reach_dp > android["safe_dp"] / 2.0 + 0.5:
                warnings.append({"code": "outside_safe_circle", "file": "android foreground",
                                 "message": "ink reaches %.1f dp from the centre; the never-clipped circle ends at %.0f dp (corners of a blocky mark: "
                                            "a circular mask may touch them)" % (reach_dp, android["safe_dp"] / 2.0)})
        if "web" in platforms:
            width, height, channels, rows = png_read(os.path.join(workdir, "maskable-ink.png"))
            spans = ink_spans(rows, width, channels)
            share = ink_reach(spans, width / 2.0, height / 2.0) / width if spans and channels == 4 else None
            safe["maskable"] = {"ink_radius_share": round(share, 3) if share else None, "safe_radius_share": web["maskable_safe_radius"]}
            if share is None or share > web["maskable_safe_radius"] + 0.004:
                problems.append({"code": "outside_safe_circle", "file": "web/maskable-*.png",
                                 "message": "ink reaches %s of the side from the centre; the maskable safe circle ends at %.2f"
                                            % ("%.3f" % share if share else "nothing", web["maskable_safe_radius"])})
        wide = crop[2] / crop[3] if crop[3] else 1
        if wide > 1.8 or wide < 0.55:
            warnings.append({"code": "mark_not_compact", "message": "the mark is %.1f times %s: it will be tiny in a square icon; use a compact symbol"
                             % (wide if wide > 1 else 1 / wide, "wider than tall" if wide > 1 else "taller than wide")})
        if "macos" in platforms and not icns:
            warnings.append({"code": "icns_not_made", "message": "no iconutil here (macOS only): deliver AppIcon.iconset; "
                                                                  "`iconutil -c icns AppIcon.iconset` on a Mac makes the .icns"})
        record = {"schema": SCHEMA, "made_at": now(), "verified_on": targets["verified_on"], "source": {"file": rel(args.file), "sha256": sha256_file(args.file),
                  "geometry_sha256": info["geometry_sha256"]}, "plate": plate, "padding": args.padding, "mark_crop": [round(v, 3) for v in crop],
                  "platforms": {name: {"notes": targets["platforms"][name]["notes"], "source_urls": targets["platforms"][name]["source_urls"]} for name in platforms},
                  "files": files, "written": written, "safe_zones": safe, "problems": problems, "warnings": warnings, "unverified": targets["unverified"]}
        manifest_path = os.path.join(out_dir, "icon-export.json")
        write_atomic(manifest_path, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    attached = None
    if state is not None and slot_state is not None and not problems:
        item = {"role": "icon-export", "path": rel(manifest_path), "dir": rel(out_dir), "sha256": sha256_file(manifest_path),
                "bytes": os.path.getsize(manifest_path), "from_revision": slot_state["approved_revision"], "added_at": now(),
                "upstream": {n: state["slots"][n]["approved_revision"] for n in ("palette", "logo") if state["slots"].get(n, {}).get("approved_revision")}}
        slot_state["assets"] = [a for a in slot_state.get("assets", []) if a["role"] != "icon-export"] + [item]
        log(state, "icon_export", "app-icon", files=len(files))
        save_state(state, read_version)
        attached = "app-icon"
    by_platform = {}
    for item in files:
        by_platform.setdefault(item["platform"], []).append(item["path"])
    for path in written:
        by_platform.setdefault(path.split("/")[0], []).append(path)
    return emit({"ok": not problems, "out_dir": rel(out_dir), "plate": plate, "files": by_platform, "count": len(files) + len(written),
                 "sheet": rel(os.path.join(out_dir, "icon-sheet.png")), "manifest": rel(manifest_path), "icns": bool(icns), "safe_zones": safe,
                 "problems": problems, "warnings": warnings, "attached_to": attached, "verified_on": targets["verified_on"]}, 0 if not problems else 1)


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_back(t):
    return 1 + 2.70158 * (t - 1) ** 3 + 1.70158 * (t - 1) ** 2


def sting_frame(mark, crop, plate, width, height, span, style, progress):
    """One frame: the untouched mark under a transform, an opacity or a clip. progress runs 0..1 over the reveal."""
    frame = ET.Element("{%s}svg" % SVG_NS, {"viewBox": "0 0 %d %d" % (width, height), "width": str(width), "height": str(height)})
    ET.SubElement(frame, "{%s}rect" % SVG_NS, {"width": str(width), "height": str(height), "fill": plate})
    box_w = width * span
    box_h = min(height * 0.6, box_w * crop[3] / crop[2])
    box_w = box_h * crop[2] / crop[3]
    x, y, cx, cy = (width - box_w) / 2.0, (height - box_h) / 2.0, width / 2.0, height / 2.0
    eased = ease_out(progress)
    attrs = {}
    if style == "rise":
        scale = 0.94 + 0.06 * eased
        attrs = {"opacity": "%.4f" % eased, "transform": "translate(%g %g) scale(%.5f) translate(%g %g)" % (cx, cy + (1 - eased) * 0.05 * height, scale, -cx, -cy)}
    elif style == "pop":
        scale = 0.7 + 0.3 * ease_back(progress)
        attrs = {"opacity": "%.4f" % min(1.0, progress / 0.4), "transform": "translate(%g %g) scale(%.5f) translate(%g %g)" % (cx, cy, scale, -cx, -cy)}
    else:
        clip = ET.SubElement(ET.SubElement(frame, "{%s}defs" % SVG_NS), "{%s}clipPath" % SVG_NS, {"id": "bk-wipe"})
        ET.SubElement(clip, "{%s}rect" % SVG_NS, {"x": "%g" % (x - 4), "y": "%g" % (y - 4), "width": "%g" % ((box_w + 8) * eased), "height": "%g" % (box_h + 8)})
        attrs = {"clip-path": "url(#bk-wipe)"}
    nest_mark(ET.SubElement(frame, "{%s}g" % SVG_NS, attrs), mark, crop, x, y, box_w, box_h)
    return frame


def cmd_sting(args):
    plate = strict_hex(args.background, "--background")
    size = re.fullmatch(r"(\d{3,4})x(\d{3,4})", args.size or "")
    if not size or int(size.group(1)) % 2 or int(size.group(2)) % 2:
        raise usage("--size is WIDTHxHEIGHT in even pixels, such as 1920x1080, 1080x1920 or 1080x1080")
    width, height = int(size.group(1)), int(size.group(2))
    if not 1.5 <= args.seconds <= 6 or not 12 <= args.fps <= 60 or not 0.1 <= args.span <= 0.9:
        raise usage("--seconds 1.5 to 6, --fps 12 to 60, --span 0.1 to 0.9 of the frame width")
    if not args.out.lower().endswith(".mp4"):
        raise usage("--out is an .mp4 file")
    state = read_version = slot_state = None
    if args.brand:
        brand = resolve_brand(args.brand)
        state = load_state(brand)
        read_version = state["version"]
        slot_state = state["slots"].get("logo")
        _revision, approved = approved_candidate(slot_state) if slot_state and slot_state["status"] == "approved" else (None, None)
        known = [item.get("sha256") for item in (approved or {}).get("files", [])] + [a.get("sha256") for a in (slot_state or {}).get("assets", [])]
        if not approved or sha256_file(args.file) not in known:
            raise Fail("not_approved", "%s is neither the approved logo nor one of its registered variants" % args.file,
                       hint="a sting shows the approved mark: approve the logo, or add-asset the variant first")
    need_browser("sting")
    ffmpeg = find_tool("GM_FFMPEG_BIN", ("ffmpeg",))
    if not ffmpeg:
        raise Fail("tool_missing", "sting needs a local ffmpeg to join the frames, and none was found",
                   hint="say that the sting was not made on this machine; the logo SVG and PNG exports are unaffected")
    root, _info = guarded_root(args.file)
    clear_background(root)
    box = view_box(root)
    if not box or box[2] <= 0 or box[3] <= 0:
        raise Fail("svg_invalid", "%s has neither a viewBox nor a size" % args.file)
    total = int(round(args.seconds * args.fps))
    moving = min(total - 1, int(round(STING_IN_S * args.fps)))
    frames_dir = os.path.splitext(args.out)[0] + "-frames"
    if os.path.isdir(frames_dir):
        shutil.rmtree(frames_dir)
    os.makedirs(frames_dir)
    workdir = tempfile.mkdtemp(prefix="brandkit-sting-")
    try:
        crop, _reach = measure_mark(root, box, workdir)
        jobs = []
        for index in range(moving + 1):
            source = os.path.join(workdir, "frame-%04d.svg" % index)
            write_svg(sting_frame(root, crop, plate, width, height, args.span, args.style, index / float(moving)), source)
            jobs.append({"source": source, "out": os.path.join(frames_dir, "frame-%04d.png" % index), "width": width, "height": height, "background": plate})
        failures = render_all(jobs, args.jobs)
        if failures:
            raise Fail("tool_failed", "%d of %d frames failed to render" % (len(failures), len(jobs)), hint="run the command again; if it repeats, lower --jobs",
                       extra={"failed": failures[:8]})
        for index in range(moving + 1, total):      # the hold: the finished frame, copied
            shutil.copyfile(os.path.join(frames_dir, "frame-%04d.png" % moving), os.path.join(frames_dir, "frame-%04d.png" % index))
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        done = subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(args.fps), "-i", os.path.join(frames_dir, "frame-%04d.png"),
                               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-movflags", "+faststart", args.out],
                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=300, check=False)
        if done.returncode != 0 or not os.path.isfile(args.out):
            raise Fail("tool_failed", "ffmpeg could not join the frames: %s" % done.stderr.decode("utf-8", "replace").strip()[-300:],
                       hint="the frames are kept in %s" % rel(frames_dir))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    last = os.path.splitext(args.out)[0] + "-last.png"
    shutil.copyfile(os.path.join(frames_dir, "frame-%04d.png" % (total - 1)), last)
    if not args.keep_frames:
        shutil.rmtree(frames_dir, ignore_errors=True)
    if state is not None and slot_state is not None:
        item = {"role": "sting", "path": rel(args.out), "sha256": sha256_file(args.out), "bytes": os.path.getsize(args.out),
                "from_revision": slot_state["approved_revision"], "added_at": now(),
                "upstream": {"palette": state["slots"]["palette"]["approved_revision"]} if state["slots"].get("palette", {}).get("approved_revision") else {}}
        slot_state["assets"] = [a for a in slot_state.get("assets", []) if a["role"] != "sting"] + [item]
        log(state, "sting", "logo", style=args.style)
        save_state(state, read_version)
    return emit({"ok": True, "out": rel(args.out), "last_frame": rel(last), "frames": rel(frames_dir) if args.keep_frames else None,
                 "size": [width, height], "seconds": round(total / float(args.fps), 3), "fps": args.fps, "style": args.style, "audio": False,
                 "rendered_frames": moving + 1, "attached_to": "logo" if state is not None else None,
                 "note": "every frame is the approved SVG under a transform, an opacity or a clip; nothing was redrawn. Silent: add sound in the edit"})


# ----------------------------------------------------------------------------------------------- cli

class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise usage(message)


def build_parser():
    parser = Parser(prog="brandkit.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>", parser_class=Parser)

    def command(name, handler, text, brand=True):
        item = sub.add_parser(name, help=text)
        item.set_defaults(handler=handler)
        if brand:
            item.add_argument("--brand")
        return item
    command("tools", cmd_tools, "which converter exists here", brand=False)
    item = command("init", cmd_init, "create the ledger for a brand")
    item.add_argument("--slug")
    command("status", cmd_status, "slots, approvals, open reviews, invalidated slots, next step")
    item = command("add-candidate", cmd_add_candidate, "register a candidate for review")
    item.add_argument("--slot", required=True)
    item.add_argument("--id", required=True)
    item.add_argument("--file", action="append")
    item.add_argument("--data")
    item.add_argument("--prompt-file")
    item.add_argument("--plan-file")
    item.add_argument("--job")
    item.add_argument("--origin", choices=ORIGINS, default="generated")
    item.add_argument("--expect-text-file")
    item.add_argument("--read-text-file")
    item.add_argument("--no-text", action="store_true")
    item.add_argument("--endpoint")
    item.add_argument("--request-id")
    item.add_argument("--cost", type=float)
    item.add_argument("--note")
    item = command("new-round", cmd_new_round, "close the open review round and open the next one (a re-roll)")
    item.add_argument("--slot", required=True)
    item.add_argument("--change", required=True)
    item.add_argument("--user-asked")
    item = command("add-asset", cmd_add_asset, "attach a production file to an approved slot")
    item.add_argument("--slot", required=True)
    item.add_argument("--role", required=True)
    item.add_argument("--file", required=True)
    item = command("approve", cmd_approve, "record the user's approval; returns what became stale")
    item.add_argument("--slot", required=True)
    item.add_argument("--candidate", required=True)
    item.add_argument("--note", required=True)
    item.add_argument("--revision", type=int)
    item = command("invalidate", cmd_invalidate, "mark a slot and everything built from it as stale")
    item.add_argument("--slot", required=True)
    item.add_argument("--reason", required=True)
    item = command("lock", cmd_lock, "compose (--data) or print the approved BRAND LOCK block")
    item.add_argument("--data")
    item.add_argument("--out")
    item = command("plan", cmd_plan, "build a gm.py batch plan from prompt files; injects the BRAND LOCK verbatim")
    item.add_argument("--spec", required=True)
    item.add_argument("--out", required=True)
    item = command("board", cmd_board, "write an HTML review board")
    item.add_argument("--slot", action="append", required=True)
    item.add_argument("--revision", type=int)
    item.add_argument("--out")
    item.add_argument("--png", action="store_true")
    item.add_argument("--webfonts", action="store_true")
    item = command("book", cmd_book, "write the HTML brandbook from approved slots")
    item.add_argument("--out")
    item.add_argument("--pdf", action="store_true")
    item = command("export-list", cmd_export_list, "approved files, problems, optional package copy")
    item.add_argument("--out")
    item.add_argument("--copy", action="store_true")
    item = command("palette-check", cmd_palette_check, "normalise a palette and compute contrast", brand=False)
    item.add_argument("--input", required=True)
    item = command("text-check", cmd_text_check, "compare requested text with the text read back", brand=False)
    item.add_argument("--expected-file")
    item.add_argument("--expected")
    item.add_argument("--read-file")
    item.add_argument("--read")
    item = command("svg-check", cmd_svg_check, "parse an SVG: size, paths, colours, safety", brand=False)
    item.add_argument("file")
    item.add_argument("--palette")
    item = command("svg-recolor", cmd_svg_recolor, "exact colour substitution", brand=False)
    item.add_argument("file")
    item.add_argument("--out", required=True)
    item.add_argument("--map", action="append", required=True)
    item.add_argument("--transparent-background", action="store_true")
    item = command("svg-variants", cmd_svg_variants, "mono and reversed variants by substitution", brand=False)
    item.add_argument("file")
    item.add_argument("--out-dir", required=True)
    item.add_argument("--ink", default="#111111")
    item.add_argument("--paper", default="#ffffff")
    item.add_argument("--keep-background", action="store_true")
    item = command("icon", cmd_icon, "square app icon: background plate plus the mark", brand=False)
    item.add_argument("file")
    item.add_argument("--out", required=True)
    item.add_argument("--background", required=True)
    item.add_argument("--padding", type=float, default=0.2)
    item.add_argument("--radius", type=float, default=0.22)
    item = command("png", cmd_png, "PNG of an SVG or an HTML page (needs a converter)", brand=False)
    item.add_argument("file")
    item.add_argument("--out", required=True)
    item.add_argument("--size", type=int)
    item.add_argument("--width", type=int)
    item.add_argument("--height", type=int)
    item.add_argument("--background", default="transparent")
    item = command("icon-export", cmd_icon_export, "platform icon files from the approved icon (needs a browser)")
    item.add_argument("file")
    item.add_argument("--out-dir")
    item.add_argument("--platform", action="append", choices=ICON_PLATFORMS)
    item.add_argument("--background")
    item.add_argument("--padding", type=float, default=0.18)
    item.add_argument("--name")
    item.add_argument("--short-name")
    item.add_argument("--jobs", type=int, default=4)
    item = command("sting", cmd_sting, "logo reveal clip from the real SVG (needs a browser and ffmpeg)")
    item.add_argument("file")
    item.add_argument("--out", required=True)
    item.add_argument("--background", required=True)
    item.add_argument("--size", default="1920x1080")
    item.add_argument("--seconds", type=float, default=2.5)
    item.add_argument("--fps", type=int, default=30)
    item.add_argument("--style", choices=STING_STYLES, default="rise")
    item.add_argument("--span", type=float, default=0.5)
    item.add_argument("--keep-frames", action="store_true")
    item.add_argument("--jobs", type=int, default=4)
    return parser


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        if not getattr(args, "handler", None):
            raise usage("missing command; see --help")
        return args.handler(args)
    except Fail as exc:
        payload = {"ok": False, "kind": exc.kind, "message": exc.message}
        if exc.hint:
            payload["hint"] = exc.hint
        payload.update(exc.extra)
        return emit(payload, exc.code)
    except (OSError, KeyError, TypeError, ValueError, AttributeError, IndexError) as exc:  # still ONE JSON object
        return emit({"ok": False, "kind": "internal", "message": "%s: %s" % (type(exc).__name__, exc),
                     "hint": "unexpected input or a damaged ledger; nothing was written by this call unless it says so"}, 1)


if __name__ == "__main__":
    sys.exit(main())
