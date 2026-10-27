#!/usr/bin/env python3
"""cardkit.py - facts, copy and read-back checks for marketplace card sets. Python 3.8+, stdlib only, no network.

Prints ONE compact JSON object on stdout. Exit: 0 ok | 1 failed | 2 usage.

  tools
      Which local image tool exists (ffmpeg, macOS sips) and which commands can run here.
  facts --file <facts.json>
      Which facts the user supplied, which card types they unlock, which are blocked and by what.
      Never fills a gap: a blocked card is left off the set.
  text --plan <cards.json> [--facts <facts.json>]
      Every on-card string against the text budget of its card type, the numbers gate (each number on a
      card must occur in facts.json), claim words, symbols; returns a locale-correct `upper` (Turkish
      i/ı), the letters to `watch` and a `spelled` form for re-rolls. Errors -> exit 1.
  contrast <#text-hex> <#background-hex>
      WCAG contrast ratio of a text colour on a background colour. Below 4.5 -> exit 1.
  tiles <image> [--grid CxR] [--overlap 0.12] [--out-dir <dir>]
      Cut a card into overlapping zoom tiles so small type can be READ at full resolution.
      8-bit PNG needs no tool at all; other formats need ffmpeg or sips.
  readback --plan <cards.json> --card <id> (--seen-file <file> | --seen "<text>"...) [--numbers-only]
      Compare what was transcribed from the image with what was requested, character by character
      (NFC, whitespace collapsed, straight and curly quotes equal). Classifies each miss (case,
      diacritic, digit, spacing_or_punct, misspelt, missing) and every stray string (extra).
      Any miss or stray string -> exit 1, kind "check_failed". --numbers-only compares only the
      numbers (for a renderer that formats labels itself).
  probe <image>... [--expect WxH]
      Pixel size, format, file size from the file header (PNG, JPEG, WebP, GIF). No tool needed.
  fit <image> --size WxH [--out <file.jpg|.png>] [--max-kb N] [--quality 92] [--replace]
      Exact delivery size by pure scaling. NEVER crops: a ratio mismatch above 1 percent is an error,
      because a crop can cut text. Needs ffmpeg or sips. Alpha is not flattened: send opaque cards.
  convert <image> [--out <file.jpg|.png>] [--max-side 3000] [--replace]
      A phone photo (HEIC, AVIF, TIFF, CMYK JPEG, very large files) as an sRGB JPEG or PNG the models
      accept, longest side bounded, aspect kept. Needs sips or ffmpeg; sips is tried first for HEIC.
  order --out-dir <dir> --item <name>=<path>... [--replace]
      Copy approved files to listing-order names (01-main.jpg, 02-benefits.png, ...) and write
      listing.json. Never overwrites a different file unless --replace.

Without a local tool `fit` and `convert` (and `tiles` on non-PNG files) answer {ok:false, kind:"tool_missing", hint}.
Never draws text: no drawtext, Pillow or ImageMagick is assumed.
Env: GM_FFMPEG_BIN, GM_SIPS_BIN (binary override; the value "none" disables that tool).
"""
import argparse
import difflib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unicodedata
import zlib

TIMEOUT_S = 120
KB = 1000
PNG_SIG = b"\x89PNG\r\n\x1a\n"
RATIO_TOLERANCE = 0.01
MAX_TILE_PIXELS = 64 * 1000 * 1000   # pure-Python PNG decode: refuse anything a listing image never is
TILE_TARGET_PX = 1100          # a tile this size is shown 1:1 by an image viewer that caps at ~1568 px
FFMPEG_JPEG_Q = (2, 3, 4, 5, 6, 8, 10, 13, 16, 20)
SIPS_JPEG_Q = (92, 88, 84, 80, 75, 70, 65, 60, 50, 40)
TR_LANGS = ("tr", "az")
TR_UPPER = {ord("i"): "\u0130", ord("\u0131"): "I"}
TR_LOWER = {ord("\u0130"): "i", ord("I"): "\u0131"}
FOLD_EXTRA = {ord("\u0131"): "i", ord("\u00df"): "ss", ord("\u00f8"): "o", ord("\u00d8"): "O", ord("\u00e6"): "ae",
              ord("\u00c6"): "AE", ord("\u0111"): "d", ord("\u0110"): "D", ord("\u0142"): "l", ord("\u0141"): "L"}
TYPO_EQUAL = {ord("\u2019"): "'", ord("\u2018"): "'", ord("\u201c"): '"', ord("\u201d"): '"', ord("\u2013"): "-",
              ord("\u2014"): "-", ord("\u2212"): "-", ord("\u00a0"): " ", ord("\u202f"): " ", ord("\u00d7"): "x"}
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")
ORDINAL_RE = re.compile(r"^[#(]?\d{1,2}[.)]?$")

# max strings (headline excluded), max words per string, max characters per string, max words on the card
BUDGETS = {
    "main": (0, 0, 0, 0), "benefits": (5, 4, 28, 26), "dimensions": (5, 3, 18, 16), "materials": (4, 4, 28, 24),
    "howto": (4, 5, 32, 28), "inuse": (2, 5, 32, 14), "inbox": (6, 3, 24, 24), "range": (12, 3, 18, 40),
    "trust": (3, 4, 28, 18), "banner": (1, 8, 48, 14),
}
HEADLINE_WORDS, HEADLINE_CHARS = 6, 36
LISTING_ORDER = ("main", "benefits", "inuse", "dimensions", "materials", "howto", "inbox", "range", "trust", "banner")
FACT_KEYS = ("product_name", "brand", "marketplace", "language", "dimensions", "weight", "capacity", "materials",
             "ingredients", "included", "benefits", "how_to_use", "variants", "certifications", "warranty",
             "origin", "care", "other_facts", "sources")
LIST_KEYS = ("dimensions", "materials", "ingredients", "included", "benefits", "how_to_use", "variants",
             "certifications", "care", "other_facts")
CLAIM_WORDS = ("best seller", "bestseller", "best-selling", "#1", "no. 1", "number one", "award", "guaranteed",
               "clinically", "doctor", "dermatolog", "fda", "approved", "certified", "organic", "patented",
               "çok satan", "en iyi", "1 numara", "bir numara", "ödüllü", "garantili", "klinik", "doktor",
               "onaylı", "sertifikalı", "organik", "patentli", "%100", "100%")
REPAIR = {
    "case": "write the exact casing yourself and say 'exact casing, do not change capitalisation'; never ask the "
            "model to uppercase",
    "diacritic": "re-roll with this string spelled letter by letter (text -> spelled), name the lost mark, larger type",
    "digit": "digits are facts: re-roll with the number alone in quotes and larger; never deliver a wrong digit",
    "spacing_or_punct": "re-roll; put the string on its own TEXT line and forbid line breaks and added punctuation",
    "misspelt": "shorten the string or split it into two callouts; larger type; fewer strings on the card",
    "missing": "check the string is in the TEXT block; fewer callouts or larger type so it fits",
    "extra": "stray text: name it in the prompt ('do not write \"...\"') and repeat the no-other-text clause; a filler "
             "claim fails the card even when it sounds true",
    "label_suspect": "the product's own label drifted: add the label close-up as a reference or make the product "
                     "larger on the card",
    "number": "a number on the card differs from the facts: re-render; never deliver",
}


class Fail(Exception):
    def __init__(self, kind, message, hint=None, code=1, extra=None):
        Exception.__init__(self, message)
        self.kind, self.message, self.hint, self.code, self.extra = kind, message, hint, code, extra or {}


def emit(obj, code=0):
    text = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    sys.stdout.buffer.write(text.encode("utf-8", "backslashreplace") + b"\n")
    sys.stdout.buffer.flush()
    return code


def usage(message):
    return Fail("usage", message, code=2)


def load_json(path, what):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError as exc:
        raise Fail("not_found", "%s: cannot read %s (%s)" % (what, path, exc.strerror or exc))
    except ValueError as exc:
        raise Fail("invalid_json", "%s: %s is not valid JSON (%s)" % (what, path, exc))
    if not isinstance(data, dict):
        raise Fail("invalid_json", "%s: %s must hold one JSON object" % (what, path))
    return data


# ---------------------------------------------------------------------------------------------- text helpers

def norm(text):
    text = unicodedata.normalize("NFC", text).translate(TYPO_EQUAL)
    return " ".join(text.split())


def ascii_fold(text):
    text = unicodedata.normalize("NFKD", text.translate(FOLD_EXTRA))
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def loose(text):
    return "".join(ch for ch in ascii_fold(text).casefold() if ch.isalnum())


def upper_for(text, lang):
    return text.translate(TR_UPPER).upper() if lang in TR_LANGS else text.upper()


def lower_for(text, lang):
    return text.translate(TR_LOWER).lower() if lang in TR_LANGS else text.lower()


def canon_number(token):
    """'6,5' -> '6.5', '6.50' -> '6.5', '1.000' stays ambiguous: both '1' and '1000' are offered."""
    out = set()
    plain = token.replace(",", ".")
    if plain.count(".") <= 1:
        try:
            out.add(("%.6f" % float(plain)).rstrip("0").rstrip("."))
        except ValueError:
            pass
    digits = re.sub(r"[.,]", "", token)
    if digits != token and re.search(r"[.,]\d{3}(?:[.,]|$)", token):
        out.add(digits.lstrip("0") or "0")
    return out or {token}


def numbers_in(text):
    return [m.group(0) for m in NUMBER_RE.finditer(text)]


def fact_numbers(value, acc):
    if isinstance(value, bool) or value is None:
        return acc
    if isinstance(value, (int, float)):
        acc.update(canon_number(repr(value) if isinstance(value, int) else ("%r" % value)))
    elif isinstance(value, str):
        for token in numbers_in(value):
            acc.update(canon_number(token))
    elif isinstance(value, dict):
        for item in value.values():
            fact_numbers(item, acc)
    elif isinstance(value, (list, tuple)):
        for item in value:
            fact_numbers(item, acc)
    return acc


# ---------------------------------------------------------------------------------------------------- facts

def filled(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def cmd_facts(args):
    facts = load_json(args.file, "facts")
    warnings = ["unknown key %r (typo? known keys: %s)" % (key, ", ".join(FACT_KEYS))
                for key in facts if key not in FACT_KEYS]
    for key in LIST_KEYS:
        if key in facts and facts[key] is not None and not isinstance(facts[key], list):
            raise Fail("facts_invalid", "facts.%s must be a list" % key)
    have = lambda key: filled(facts.get(key))  # noqa: E731
    count = lambda key: len(facts.get(key) or [])  # noqa: E731
    possible, blocked = [{"type": "main", "because": "needs only the product photo"}], []

    def gate(card, ok, because, needs):
        (possible if ok else blocked).append({"type": card, "because": because} if ok else {"type": card, "needs": needs})

    gate("benefits", count("benefits") >= 2, "%d benefit statements" % count("benefits"),
         "3 to 5 benefit statements in the user's words (benefits)")
    gate("inuse", True, "needs only the product photo; a caption needs a benefit or use the user stated", "")
    gate("dimensions", have("dimensions"), "%d measurements" % count("dimensions"),
         "measurements with units (dimensions); weight and capacity are optional extras")
    gate("materials", have("materials") or have("ingredients"), "materials or ingredients supplied",
         "materials or ingredients (materials, ingredients)")
    gate("howto", count("how_to_use") >= 2, "%d steps" % count("how_to_use"), "2 to 4 short usage steps (how_to_use)")
    gate("inbox", have("included"), "%d kit items" % count("included"), "the kit contents, item by item (included)")
    gate("range", count("variants") >= 2, "%d own variants" % count("variants"),
         "at least 2 of the user's own variants (variants); never a competitor")
    gate("trust", any(have(k) for k in ("warranty", "certifications", "origin", "other_facts")),
         "user-supplied warranty, certification, origin or other facts",
         "a provable trust fact: warranty, certification, origin (warranty, certifications, origin, other_facts)")
    gate("banner", have("product_name") and (have("benefits") or have("brand")), "name plus a benefit or brand",
         "the product name and one benefit or the brand (product_name, benefits, brand)")
    if 0 < count("benefits") < 3:
        warnings.append("only %d benefit statements: the infographic works best with 3 to 5" % count("benefits"))
    if count("benefits") > 5:
        warnings.append("%d benefit statements: keep the strongest 5 on the card, the rest go in the listing text"
                        % count("benefits"))
    for item in facts.get("included") or []:
        if isinstance(item, dict) and not filled(item.get("photo")):
            warnings.append("kit item %r has no photo: list it as text with a plain icon, never draw it photoreal"
                            % (item.get("item"),))
    if have("certifications"):
        warnings.append("certifications are written as plain words; never draw a certification mark unless the user "
                        "supplies the artwork and confirms the licence")
    if not have("product_name"):
        warnings.append("product_name is missing")
    order = {name: i for i, name in enumerate(LISTING_ORDER)}
    possible.sort(key=lambda row: order[row["type"]])
    blocked.sort(key=lambda row: order[row["type"]])
    return {"ok": True, "product_name": facts.get("product_name"),
            "fields": {"present": [k for k in FACT_KEYS if have(k)],
                       "missing": [k for k in FACT_KEYS if not have(k) and k != "sources"]},
            "cards": {"possible": possible, "blocked": blocked},
            "numbers": sorted(fact_numbers(facts, set())), "warnings": warnings}, 0


# ----------------------------------------------------------------------------------------------------- text

def load_plan(path):
    plan = load_json(path, "plan")
    cards = plan.get("cards")
    if not isinstance(cards, list) or not cards:
        raise Fail("plan_invalid", "plan.cards must be a non-empty list")
    seen = set()
    for card in cards:
        if not isinstance(card, dict) or not isinstance(card.get("id"), str) or not card["id"]:
            raise Fail("plan_invalid", "every card needs a string id")
        if card["id"] in seen:
            raise Fail("plan_invalid", "duplicate card id %r" % card["id"])
        seen.add(card["id"])
        strings = card.get("strings", [])
        if not isinstance(strings, list) or any(not isinstance(s, str) for s in strings):
            raise Fail("plan_invalid", "card %s: strings must be a list of strings" % card["id"])
        if card.get("headline") is not None and not isinstance(card["headline"], str):
            raise Fail("plan_invalid", "card %s: headline must be a string" % card["id"])
        allowed = card.get("allowed") or []
        if not isinstance(allowed, list) or any(not isinstance(s, str) for s in allowed):
            raise Fail("plan_invalid", "card %s: allowed must be a list of strings" % card["id"])
    labels = plan.get("label_strings") or []
    if not isinstance(labels, list) or any(not isinstance(s, str) for s in labels):
        raise Fail("plan_invalid", "plan.label_strings must be a list of strings")
    return plan


def card_strings(card):
    rows = []
    if card.get("headline"):
        rows.append(("headline", card["headline"]))
    rows.extend(("string", s) for s in card.get("strings", []))
    return rows


def describe_string(role, text, lang):
    clean = norm(text)
    watch = sorted({ch for ch in clean if ord(ch) > 127 and ch.isalpha()})
    if lang in TR_LANGS and clean == upper_for(clean, lang) and "I" in clean:
        watch.append("I (dotless, must stay without a dot)")
    row = {"role": role, "text": text, "words": len(clean.split()), "chars": len(clean),
           "upper": upper_for(clean, lang), "watch": watch}
    if watch or numbers_in(clean):
        row["spelled"] = "  ".join("-".join(word) for word in clean.split())
    return row


def cmd_text(args):
    plan = load_plan(args.plan)
    lang = str(plan.get("language") or "en").lower()[:2]
    allowed_numbers = fact_numbers(load_json(args.facts, "facts"), set()) if args.facts else None
    cards, errors, warnings = [], 0, 0
    for card in plan["cards"]:
        ctype, issues = card.get("type"), []

        def issue(code, message, string=None, level="error"):
            issues.append({"code": code, "level": level, "message": message, **({"string": string} if string else {})})

        rows = [describe_string(role, text, lang) for role, text in card_strings(card)]
        if ctype not in BUDGETS:
            issue("unknown_type", "type %r is not one of %s" % (ctype, ", ".join(LISTING_ORDER)))
            budget = None
        else:
            budget = dict(zip(["max_strings", "max_words_per_string", "max_chars_per_string", "max_words_total"],
                              BUDGETS[ctype]))
            budget.update({"headline_words": HEADLINE_WORDS, "headline_chars": HEADLINE_CHARS})
            body = [r for r in rows if r["role"] == "string"]
            if ctype == "main" and rows:
                issue("text_on_main", "the main image carries no text at all")
            elif len(body) > budget["max_strings"]:
                issue("too_many_strings", "%d strings, budget %d: drop the weakest or split into two cards"
                      % (len(body), budget["max_strings"]))
            total = sum(r["words"] for r in rows)
            if ctype != "main" and total > budget["max_words_total"]:
                issue("total_words", "%d words on the card, budget %d" % (total, budget["max_words_total"]))
            for r in rows:
                if not norm(r["text"]):
                    issue("empty_string", "empty string", r["text"])
                    continue
                if ctype == "main":
                    continue
                max_w, max_c = ((HEADLINE_WORDS, HEADLINE_CHARS) if r["role"] == "headline"
                                else (budget["max_words_per_string"], budget["max_chars_per_string"]))
                if r["words"] > max_w or r["chars"] > max_c:
                    issue("headline_too_long" if r["role"] == "headline" else "string_too_long",
                          "%d words / %d chars, budget %d / %d: drop words, never change a fact"
                          % (r["words"], r["chars"], max_w, max_c), r["text"])
        for r in rows:
            clean = norm(r["text"])
            if any(unicodedata.category(ch) in ("So", "Sk", "Cs", "Co") or ord(ch) > 0xFFFF for ch in clean):
                issue("symbol", "symbols and emoji are drawn as icons by the layout, not typed: remove them", r["text"])
            if r["text"] != unicodedata.normalize("NFC", r["text"]).translate(TYPO_EQUAL):
                issue("typographic_char", "curly quote, long dash, multiplication sign or no-break space: use the "
                      "plain character, the read-back treats them as equal", r["text"], "warning")
            if r["words"] > 2 and clean == upper_for(clean, lang) and clean != lower_for(clean, lang):
                issue("all_caps", "all caps beyond 2 words is where dotted and dotless I fail most: prefer "
                      "sentence case", r["text"], "warning")
            low = lower_for(clean, lang)
            for word in CLAIM_WORDS:
                if word in low:
                    issue("claim_word", "claim word %r: keep only if the user stated it and can prove it" % word,
                          r["text"], "warning")
                    break
            if allowed_numbers is not None:
                for token in numbers_in(clean):
                    if canon_number(token) & allowed_numbers:
                        continue
                    if ctype == "howto" and ORDINAL_RE.match(token) and int(token) <= len(card.get("strings", [])):
                        continue
                    issue("number_not_in_facts", "number %r is not in facts.json: remove it or have the user "
                          "confirm it" % token, r["text"])
        card_errors = sum(1 for i in issues if i["level"] == "error")
        errors += card_errors
        warnings += len(issues) - card_errors
        cards.append({"id": card["id"], "type": ctype, "ok": card_errors == 0,
                      "words": sum(r["words"] for r in rows), "budget": budget, "strings": rows, "issues": issues})
    result = {"ok": errors == 0, "language": lang, "numbers_gate": allowed_numbers is not None, "cards": cards,
              "errors": errors, "warnings": warnings}
    if errors:
        result.update({"kind": "check_failed", "message": "%d copy problems: fix the strings, then run text again"
                       % errors})
    if allowed_numbers is None:
        result["hint"] = "pass --facts so every number on a card is checked against the facts sheet"
    return result, int(bool(errors))


# ------------------------------------------------------------------------------------------------- contrast

def parse_hex(value):
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", text):
        raise usage("colour %r is not #RGB or #RRGGBB" % value)
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))


def luminance(rgb):
    def channel(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def cmd_contrast(args):
    fg, bg = parse_hex(args.text), parse_hex(args.background)
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    ratio = round((hi + 0.05) / (lo + 0.05), 2)
    result = {"ok": ratio >= 4.5, "ratio": ratio, "text": "#%02X%02X%02X" % fg, "background": "#%02X%02X%02X" % bg,
              "small_text_ok": ratio >= 4.5, "large_text_ok": ratio >= 3.0}
    if ratio < 4.5:
        result.update({"kind": "check_failed", "message": "contrast %.2f:1 is below 4.5:1" % ratio,
                       "hint": "darken the text or lighten the background; card text is read on a phone"})
    return result, int(ratio < 4.5)


# ------------------------------------------------------------------------------------------ image plumbing

def find_tool(env, name):
    override = os.environ.get(env)
    if override is not None:
        if override.strip().lower() in ("", "none"):
            return None
        return override if os.path.isfile(override) and os.access(override, os.X_OK) else shutil.which(override)
    return shutil.which(name)


def tools():
    return find_tool("GM_FFMPEG_BIN", "ffmpeg"), find_tool("GM_SIPS_BIN", "sips")


def run_tool(argv):
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        raise Fail("tool_failed", "%s timed out after %d s" % (os.path.basename(argv[0]), TIMEOUT_S))
    except OSError as exc:
        raise Fail("tool_failed", "%s could not start (%s)" % (argv[0], exc.strerror or exc))
    if proc.returncode != 0:
        tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-3:]
        raise Fail("tool_failed", "%s failed: %s" % (os.path.basename(argv[0]), " | ".join(tail) or "no message"))


def missing_tool(what, hint):
    return Fail("tool_missing", "%s needs ffmpeg or macOS sips, and neither was found" % what, hint=hint)


def probe_file(path):
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            head = fh.read(64)
            fmt, width, height = None, None, None
            if head[:8] == PNG_SIG and head[12:16] == b"IHDR":
                fmt, (width, height) = "png", struct.unpack(">II", head[16:24])
            elif head[:6] in (b"GIF87a", b"GIF89a"):
                fmt, (width, height) = "gif", struct.unpack("<HH", head[6:10])
            elif head[:4] == b"RIFF" and head[8:12] == b"WEBP":
                fmt, kind = "webp", head[12:16]
                if kind == b"VP8X":
                    width = 1 + int.from_bytes(head[24:27], "little")
                    height = 1 + int.from_bytes(head[27:30], "little")
                elif kind == b"VP8 ":
                    width, height = (v & 0x3FFF for v in struct.unpack("<HH", head[26:30]))
                elif kind == b"VP8L":
                    bits = int.from_bytes(head[21:25], "little")
                    width, height = 1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF)
            elif head[:2] == b"\xff\xd8":
                fmt = "jpeg"
                fh.seek(2)
                while True:
                    marker = fh.read(2)
                    if len(marker) < 2 or marker[0] != 0xFF:
                        break
                    if marker[1] == 0xFF:          # fill byte before a marker
                        fh.seek(-1, 1)
                        continue
                    if marker[1] in (0xD8, 0x01) or 0xD0 <= marker[1] <= 0xD7:
                        continue
                    seg = fh.read(2)
                    if len(seg) < 2:
                        break
                    length = struct.unpack(">H", seg)[0]
                    if 0xC0 <= marker[1] <= 0xCF and marker[1] not in (0xC4, 0xC8, 0xCC):
                        height, width = struct.unpack(">HH", fh.read(5)[1:5])
                        break
                    fh.seek(length - 2, 1)
    except OSError as exc:
        raise Fail("not_found", "cannot read %s (%s)" % (path, exc.strerror or exc))
    if not fmt or not width or not height:
        raise Fail("unsupported", "%s is not a PNG, JPEG, WebP or GIF this tool can measure" % path,
                   hint="HEIC, AVIF or TIFF: convert to PNG or JPEG first")
    return {"path": path, "format": fmt, "width": int(width), "height": int(height),
            "kb": int(math.ceil(size / float(KB))), "ratio": round(width / float(height), 4)}


def parse_size(value):
    match = re.fullmatch(r"(\d{2,5})[xX\u00d7](\d{2,5})", value.strip())
    if not match:
        raise usage("size %r is not WxH, for example 1200x1800" % value)
    return int(match.group(1)), int(match.group(2))


def cmd_tools(_args):
    ffmpeg, sips = tools()
    any_tool = bool(ffmpeg or sips)
    return {"ok": True, "ffmpeg": {"found": bool(ffmpeg), "path": ffmpeg}, "sips": {"found": bool(sips), "path": sips},
            "can": {"facts": True, "text": True, "contrast": True, "readback": True, "probe": True, "order": True,
                    "tiles_png": True, "tiles_other_formats": any_tool, "fit": any_tool, "convert": any_tool},
            "hint": None if any_tool else "no ffmpeg and no sips: deliver master sizes, say that exact-size copies "
                                          "were not made; everything else works"}, 0


def cmd_probe(args):
    images = [probe_file(path) for path in args.images]
    result = {"ok": True, "images": images}
    if args.expect:
        want = parse_size(args.expect)
        bad = [i["path"] for i in images if (i["width"], i["height"]) != want]
        if bad:
            result.update({"ok": False, "kind": "check_failed", "failed": bad,
                           "message": "%d file(s) are not %dx%d" % (len(bad), want[0], want[1])})
    return result, int(not result["ok"])


# ---------------------------------------------------------------------------------------------------- tiles

def png_rows(path):
    with open(path, "rb") as fh:
        data = fh.read()
    pos, idat, header = 8, [], None
    while pos + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            if len(chunk) != 13:
                raise Fail("unsupported", "%s: PNG header is damaged" % path)
            header = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"IDAT":
            idat.append(chunk)
        elif ctype == b"IEND":
            break
    if not header:
        raise Fail("unsupported", "%s has no PNG header" % path)
    width, height, depth, color, _comp, _filt, interlace = header
    if depth != 8 or color not in (0, 2, 4, 6) or interlace:
        return None
    if not width or not height or width * height > MAX_TILE_PIXELS:
        raise Fail("unsupported", "%s: %dx%d is outside what tiles decodes (up to %d megapixels)"
                   % (path, width, height, MAX_TILE_PIXELS // 1000000))
    bpp = {0: 1, 2: 3, 4: 2, 6: 4}[color]
    stride = width * bpp
    try:
        # bounded: a small header in front of a huge compressed stream must not fill the memory
        raw = zlib.decompressobj().decompress(b"".join(idat), (stride + 1) * height)
    except zlib.error as exc:
        raise Fail("unsupported", "%s: PNG data is damaged (%s)" % (path, exc))
    if len(raw) < (stride + 1) * height:
        raise Fail("unsupported", "%s: PNG data is truncated" % path)
    rows, prev, pos = [], bytearray(stride), 0
    for _ in range(height):
        ftype, line = raw[pos], bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if ftype == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif ftype == 2:
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif ftype == 3:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 255
        elif ftype == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 255
        elif ftype != 0:
            raise Fail("unsupported", "%s: unknown PNG filter %d" % (path, ftype))
        rows.append(line)
        prev = line
    return width, height, color, bpp, rows


def png_write(path, width, height, color, rows):
    def chunk(ctype, body):
        return struct.pack(">I", len(body)) + ctype + body + struct.pack(">I", zlib.crc32(ctype + body) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(row) for row in rows)
    with open(path, "wb") as fh:
        fh.write(PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def tile_boxes(width, height, cols, rows, overlap):
    boxes = []
    tile_w = width if cols == 1 else min(width, int(math.ceil(width / float(cols) * (1 + overlap))))
    tile_h = height if rows == 1 else min(height, int(math.ceil(height / float(rows) * (1 + overlap))))
    for r in range(rows):
        for c in range(cols):
            x = 0 if cols == 1 else int(round((width - tile_w) * c / float(cols - 1)))
            y = 0 if rows == 1 else int(round((height - tile_h) * r / float(rows - 1)))
            boxes.append((r + 1, c + 1, x, y, tile_w, tile_h))
    return boxes


def cmd_tiles(args):
    info = probe_file(args.image)
    width, height = info["width"], info["height"]
    if args.grid:
        match = re.fullmatch(r"([1-6])[xX]([1-6])", args.grid)
        if not match:
            raise usage("--grid is COLSxROWS with 1 to 6 each, for example 2x2")
        cols, rows = int(match.group(1)), int(match.group(2))
    else:
        cols = max(1, min(4, int(math.ceil(width / float(TILE_TARGET_PX)))))
        rows = max(1, min(4, int(math.ceil(height / float(TILE_TARGET_PX)))))
    if not 0 <= args.overlap <= 0.5:
        raise usage("--overlap must be between 0 and 0.5")
    stem = os.path.splitext(os.path.basename(args.image))[0]
    out_dir = args.out_dir or os.path.join(os.path.dirname(os.path.abspath(args.image)), "tiles", stem)
    os.makedirs(out_dir, exist_ok=True)
    boxes = tile_boxes(width, height, cols, rows, args.overlap)
    ffmpeg, sips = tools()
    tiles, method = [], None
    if ffmpeg:
        method = "ffmpeg"
        for r, c, x, y, w, h in boxes:
            out = os.path.join(out_dir, "r%dc%d.png" % (r, c))
            run_tool([ffmpeg, "-v", "error", "-y", "-i", args.image, "-vf", "crop=%d:%d:%d:%d" % (w, h, x, y),
                      "-frames:v", "1", out])
            tiles.append({"path": out, "box": [x, y, w, h]})
    else:
        source, temp = args.image, None
        decoded = png_rows(source) if info["format"] == "png" else None
        if decoded is None:
            if not sips:
                raise missing_tool("tiles on a %s file" % info["format"],
                                   "Read the full image instead, judge small type strictly, and say in the delivery "
                                   "that it was checked at reduced scale; PNG outputs need no tool")
            temp = tempfile.mkdtemp(prefix="cardkit-")
            source = os.path.join(temp, "source.png")
            run_tool([sips, "-s", "format", "png", args.image, "--out", source])
            decoded = png_rows(source)
            method = "sips+python"
        else:
            method = "python"
        try:
            if decoded is None:
                raise Fail("unsupported", "%s: only 8-bit non-interlaced PNG can be tiled without ffmpeg" % args.image)
            _w, _h, color, bpp, pixel_rows = decoded
            for r, c, x, y, w, h in boxes:
                out = os.path.join(out_dir, "r%dc%d.png" % (r, c))
                png_write(out, w, h, color, [row[x * bpp:(x + w) * bpp] for row in pixel_rows[y:y + h]])
                tiles.append({"path": out, "box": [x, y, w, h]})
        finally:
            if temp:
                shutil.rmtree(temp, ignore_errors=True)
    return {"ok": True, "image": args.image, "width": width, "height": height, "grid": "%dx%d" % (cols, rows),
            "method": method, "tiles": tiles,
            "hint": "Read every tile and write down ALL text you see, one string per line, BEFORE you look at the "
                    "expected strings again; then run readback"}, 0


# ------------------------------------------------------------------------------------------------- readback

def first_diff(expected, seen):
    for i, (a, b) in enumerate(zip(expected, seen)):
        if a != b:
            return {"at": i, "expected_char": a, "seen_char": b,
                    "expected_name": unicodedata.name(a, "?"), "seen_name": unicodedata.name(b, "?")}
    if len(expected) != len(seen):
        i = min(len(expected), len(seen))
        return {"at": i, "expected_char": expected[i:i + 1] or None, "seen_char": seen[i:i + 1] or None,
                "note": "length differs: expected %d characters, saw %d" % (len(expected), len(seen))}
    return None


def classify(expected, seen):
    if expected.casefold() == seen.casefold() or lower_for(expected, "tr") == lower_for(seen, "tr"):
        return "case"
    if ascii_fold(expected).casefold() == ascii_fold(seen).casefold():
        return "diacritic"
    if re.sub(r"\d", "", expected) == re.sub(r"\d", "", seen):
        return "digit"
    if loose(expected) == loose(seen):
        return "spacing_or_punct"
    return "misspelt" if difflib.SequenceMatcher(None, expected, seen).ratio() >= 0.6 else "missing"


def read_seen(args):
    lines = list(args.seen or [])
    if args.seen_file:
        try:
            with open(args.seen_file, "r", encoding="utf-8-sig") as fh:
                lines.extend(fh.read().splitlines())
        except OSError as exc:
            raise Fail("not_found", "cannot read %s (%s)" % (args.seen_file, exc.strerror or exc))
        except UnicodeDecodeError:
            raise Fail("seen_invalid", "%s is not UTF-8 text" % args.seen_file,
                       hint="write the transcription again with the Write tool, one string per line")
    lines = [norm(line) for line in lines]
    return [line for line in lines if line and not line.startswith("# ")]


def number_forms(strings):
    """One entry per number found: (token as written, set of canonical readings)."""
    return [(token, canon_number(token)) for text in strings for token in numbers_in(text)]


def unmatched(left, right):
    return sorted({token for token, forms in left if not any(forms & other for _t, other in right)})


def cmd_readback(args):
    if not args.seen and not args.seen_file:
        raise usage("give --seen-file <file> (one transcribed string per line) or one --seen per string")
    plan = load_plan(args.plan)
    card = next((c for c in plan["cards"] if c["id"] == args.card), None)
    if card is None:
        raise Fail("plan_invalid", "card %r is not in the plan (ids: %s)"
                   % (args.card, ", ".join(c["id"] for c in plan["cards"])))
    expected = [(role, norm(text)) for role, text in card_strings(card) if norm(text)]
    seen = read_seen(args)
    if args.numbers_only:
        want, got = number_forms([t for _r, t in expected]), number_forms(seen)
        missing_numbers, extra_numbers = unmatched(want, got), unmatched(got, want)
        ok = bool(want) and not missing_numbers and not extra_numbers
        result = {"ok": ok, "card": card["id"], "mode": "numbers_only", "verdict": "pass" if ok else "fail",
                  "expected_numbers": [t for t, _f in want], "seen_numbers": [t for t, _f in got],
                  "missing_numbers": missing_numbers, "extra_numbers": extra_numbers, "seen": seen,
                  "note": "only numbers were compared: check units and words by eye against the facts sheet"}
        if not ok:
            result.update({"kind": "check_failed", "message": "numbers on the card differ from the plan",
                           "repair": REPAIR["number"]})
        return result, int(not ok)
    used, rows = set(), []
    windows = []   # (first index, last index, joined text): single lines first, then 2 and 3 joined lines
    for span in (1, 2, 3):
        for i in range(0, len(seen) - span + 1):
            windows.append((i, i + span - 1, " ".join(seen[i:i + span])))
    for role, text in expected:
        hit = next((w for w in windows if w[2] == text and not used & set(range(w[0], w[1] + 1))), None)
        if hit:
            used.update(range(hit[0], hit[1] + 1))
            rows.append({"role": role, "text": text, "status": "match", **({"joined_lines": True} if hit[1] > hit[0] else {})})
        else:
            rows.append({"role": role, "text": text, "status": None})
    for row in rows:
        if row["status"]:
            continue
        best, best_ratio = None, 0.0
        for w in windows:
            if used & set(range(w[0], w[1] + 1)):
                continue
            ratio = difflib.SequenceMatcher(None, row["text"].casefold(), w[2].casefold()).ratio()
            if ratio > best_ratio:
                best, best_ratio = w, ratio
        if best is None or best_ratio < 0.5:
            row.update({"status": "missing", "repair": REPAIR["missing"]})
            continue
        status = classify(row["text"], best[2])
        if status == "missing":
            row.update({"status": "missing", "repair": REPAIR["missing"]})
            continue
        used.update(range(best[0], best[1] + 1))
        row.update({"status": status, "seen": best[2], "diff": first_diff(row["text"], best[2]), "repair": REPAIR[status]})
    labels = [norm(s) for s in (plan.get("label_strings") or []) + (card.get("allowed") or []) if norm(s)]
    extra, ignored = [], []
    for i, line in enumerate(seen):
        if i in used:
            continue
        if card.get("type") == "howto" and ORDINAL_RE.match(line):
            ignored.append({"seen": line, "why": "step number"})
            continue
        # equal to a label line, or a fragment of one (a label half hidden by the product's curve)
        if any(line == lab or (len(line) >= 3 and line in lab) for lab in labels):
            ignored.append({"seen": line, "why": "product label or allowed string"})
            continue
        near = next((lab for lab in labels
                     if difflib.SequenceMatcher(None, line.casefold(), lab.casefold()).ratio() >= 0.75), None)
        if near:
            extra.append({"seen": line, "status": "label_suspect", "label": near, "diff": first_diff(near, line),
                          "repair": REPAIR["label_suspect"]})
        else:
            extra.append({"seen": line, "status": "extra", "repair": REPAIR["extra"]})
    misses = [r for r in rows if r["status"] != "match"]
    ok = not misses and not extra
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    result = {"ok": ok, "card": card["id"], "verdict": "pass" if ok else "fail", "expected": rows, "extra": extra,
              "ignored": ignored, "counts": counts}
    if not ok:
        result.update({"kind": "check_failed",
                       "message": "%d of %d strings differ, %d stray: do not deliver this card"
                                  % (len(misses), len(rows), len(extra)),
                       "hint": "re-roll under a new id with the prompt changed as each repair line says; never edit "
                               "the expected strings to match the image"})
    return result, int(not ok)


# ------------------------------------------------------------------------------------------------------ fit

def cmd_fit(args):
    want_w, want_h = parse_size(args.size)
    info = probe_file(args.image)
    have, want = info["width"] / float(info["height"]), want_w / float(want_h)
    if abs(have - want) / want > RATIO_TOLERANCE:
        raise Fail("ratio_mismatch", "%s is %dx%d (ratio %.3f) but %dx%d needs ratio %.3f"
                   % (args.image, info["width"], info["height"], have, want_w, want_h, want),
                   hint="fit never crops a card, because a crop can cut text: render the card again at a master "
                        "size of this ratio (see marketplaces.md)")
    stem = os.path.splitext(args.image)[0]
    out = args.out or "%s-%dx%d.jpg" % (stem, want_w, want_h)
    ext = os.path.splitext(out)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        raise usage("--out must end in .jpg, .jpeg or .png")
    if os.path.exists(out) and not args.replace:
        raise Fail("exists", "%s already exists" % out, hint="choose another --out or pass --replace")
    if args.max_kb is not None and args.max_kb <= 0:
        raise usage("--max-kb must be positive")
    if not 1 <= args.quality <= 100:
        raise usage("--quality must be between 1 and 100")
    ffmpeg, sips = tools()
    if not ffmpeg and not sips:
        raise missing_tool("fit", "deliver the master files as they are, state their pixel sizes (probe works "
                                  "without tools) and say the exact-size copy was not made")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    jpeg = ext != ".png"
    if ffmpeg:
        steps = [q for q in FFMPEG_JPEG_Q] if jpeg else [None]
        if jpeg and args.quality < 92:
            steps = [q for q in FFMPEG_JPEG_Q if q >= max(2, int(round((100 - args.quality) / 4.0)))] or [FFMPEG_JPEG_Q[-1]]
    else:
        steps = ([q for q in SIPS_JPEG_Q if q <= args.quality] or [SIPS_JPEG_Q[-1]]) if jpeg else [None]
    final = None
    for step in steps:
        if ffmpeg:
            argv = [ffmpeg, "-v", "error", "-y", "-i", args.image, "-vf",
                    "scale=%d:%d:flags=lanczos" % (want_w, want_h), "-frames:v", "1"]
            argv += (["-q:v", str(step)] if jpeg else []) + [out]
        else:
            argv = [sips, "-z", str(want_h), str(want_w), "-s", "format", "jpeg" if jpeg else "png"]
            argv += (["-s", "formatOptions", str(step)] if jpeg else []) + [args.image, "--out", out]
        run_tool(argv)
        final = probe_file(out)
        if args.max_kb is None or final["kb"] <= args.max_kb or not jpeg:
            break
    if final is None:
        raise Fail("tool_failed", "no quality step was tried for %s" % out)
    if (final["width"], final["height"]) != (want_w, want_h):
        raise Fail("tool_failed", "%s came out as %dx%d, not %dx%d" % (out, final["width"], final["height"], want_w, want_h))
    result = {"ok": True, "source": args.image, "source_size": [info["width"], info["height"]], "out": out,
              "width": want_w, "height": want_h, "kb": final["kb"], "tool": "ffmpeg" if ffmpeg else "sips",
              "upscaled": want_w > info["width"]}
    if args.max_kb is not None and final["kb"] > args.max_kb:
        result.update({"ok": False, "kind": "check_failed",
                       "message": "%d KB is still above --max-kb %d at the lowest quality step" % (final["kb"], args.max_kb)})
    if result["upscaled"]:
        result["note"] = "the target is larger than the master: text edges soften; prefer rendering a larger master"
    return result, int(not result["ok"])


# -------------------------------------------------------------------------------------------------- convert

def cmd_convert(args):
    if not os.path.isfile(args.image):
        raise Fail("not_found", "cannot read %s" % args.image)
    if not 256 <= args.max_side <= 8000:
        raise usage("--max-side must be between 256 and 8000")
    out = args.out or os.path.splitext(args.image)[0] + "-srgb.jpg"
    ext = os.path.splitext(out)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        raise usage("--out must end in .jpg, .jpeg or .png")
    if os.path.abspath(out) == os.path.abspath(args.image):
        raise usage("--out must differ from the source file")
    if os.path.exists(out) and not args.replace:
        raise Fail("exists", "%s already exists" % out, hint="choose another --out or pass --replace")
    ffmpeg, sips = tools()
    if not ffmpeg and not sips:
        raise missing_tool("convert", "ask the user to export the photo as JPEG or PNG (on a phone: share or export "
                                      "as 'most compatible') and send that file")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    jpeg = ext != ".png"
    heic = os.path.splitext(args.image)[1].lower() in (".heic", ".heif", ".avif")
    order = [("sips", sips), ("ffmpeg", ffmpeg)] if heic or not ffmpeg else [("ffmpeg", ffmpeg), ("sips", sips)]
    errors = []
    for name, binary in order:
        if not binary:
            continue
        if name == "sips":
            argv = [binary, "-s", "format", "jpeg" if jpeg else "png", "-m",
                    "/System/Library/ColorSync/Profiles/sRGB Profile.icc", "-Z", str(args.max_side)]
            argv += (["-s", "formatOptions", "92"] if jpeg else []) + [args.image, "--out", out]
            if not os.path.isfile(argv[5]):
                argv = argv[:4] + argv[6:]            # no system sRGB profile here: convert without matching
        else:
            scale = "scale='min(%d,iw)':'min(%d,ih)':force_original_aspect_ratio=decrease:flags=lanczos" % (
                args.max_side, args.max_side)
            argv = [binary, "-v", "error", "-y", "-i", args.image, "-vf", scale, "-frames:v", "1"]
            argv += (["-q:v", "2", "-pix_fmt", "yuvj420p"] if jpeg else []) + [out]
        try:
            run_tool(argv)
            info = probe_file(out)
            return {"ok": True, "source": args.image, "out": out, "width": info["width"], "height": info["height"],
                    "kb": info["kb"], "tool": name,
                    "hint": "Read the converted file before planning; upload this copy, not the original"}, 0
        except Fail as exc:
            errors.append("%s: %s" % (name, exc.message))
    raise Fail("tool_failed", "could not convert %s (%s)" % (args.image, "; ".join(errors)),
               hint="ask the user to export the photo as JPEG or PNG and send that file")


# ---------------------------------------------------------------------------------------------------- order

def slug(name):
    text = ascii_fold(name).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if not text:
        raise usage("item name %r has no letters or digits" % name)
    return text[:40]


def same_bytes(a, b):
    if os.path.getsize(a) != os.path.getsize(b):
        return False
    with open(a, "rb") as fa, open(b, "rb") as fb:
        while True:
            x, y = fa.read(1 << 16), fb.read(1 << 16)
            if x != y:
                return False
            if not x:
                return True


def cmd_order(args):
    items = []
    for raw in args.item:
        name, sep, path = raw.partition("=")
        if not sep or not name.strip() or not path.strip():
            raise usage("--item is <name>=<path>, got %r" % raw)
        items.append((slug(name), path.strip()))
    if len({name for name, _p in items}) != len(items):
        raise usage("item names must be unique")
    probed = [(name, path, probe_file(path)) for name, path in items]   # fails before anything is copied
    os.makedirs(args.out_dir, exist_ok=True)
    width = max(2, len(str(len(items))))
    files = []
    for n, (name, path, info) in enumerate(probed, 1):
        ext = {"jpeg": ".jpg"}.get(info["format"], "." + info["format"])
        target = os.path.join(args.out_dir, "%0*d-%s%s" % (width, n, name, ext))
        state = "copied"
        if os.path.exists(target):
            if same_bytes(path, target):
                state = "unchanged"
            elif not args.replace:
                raise Fail("exists", "%s exists with different content" % target,
                           hint="pass --replace to overwrite it, or use a new --out-dir (listing-v2)")
            else:
                state = "replaced"
        if state != "unchanged":
            shutil.copyfile(path, target)
        files.append({"n": n, "name": name, "path": target, "source": path, "width": info["width"],
                      "height": info["height"], "kb": info["kb"], "state": state})
    listing = os.path.join(args.out_dir, "listing.json")
    with open(listing, "w", encoding="utf-8") as fh:
        json.dump({"order": files}, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return {"ok": True, "out_dir": args.out_dir, "files": files, "listing": listing}, 0


# ----------------------------------------------------------------------------------------------------- main

class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise usage(message)


def build_parser():
    parser = Parser(prog="cardkit.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>", parser_class=Parser)
    sub.add_parser("tools", help="which local image tools exist").set_defaults(func=cmd_tools)
    p = sub.add_parser("facts", help="which cards the supplied facts unlock")
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_facts)
    p = sub.add_parser("text", help="check every on-card string before generating")
    p.add_argument("--plan", required=True)
    p.add_argument("--facts")
    p.set_defaults(func=cmd_text)
    p = sub.add_parser("contrast", help="WCAG contrast of text on background")
    p.add_argument("text")
    p.add_argument("background")
    p.set_defaults(func=cmd_contrast)
    p = sub.add_parser("tiles", help="zoom tiles for reading small type")
    p.add_argument("image")
    p.add_argument("--grid")
    p.add_argument("--overlap", type=float, default=0.12)
    p.add_argument("--out-dir")
    p.set_defaults(func=cmd_tiles)
    p = sub.add_parser("readback", help="compare transcribed text with the requested strings")
    p.add_argument("--plan", required=True)
    p.add_argument("--card", required=True)
    p.add_argument("--seen-file")
    p.add_argument("--seen", action="append")
    p.add_argument("--numbers-only", action="store_true")
    p.set_defaults(func=cmd_readback)
    p = sub.add_parser("probe", help="pixel size and file size from the header")
    p.add_argument("images", nargs="+")
    p.add_argument("--expect")
    p.set_defaults(func=cmd_probe)
    p = sub.add_parser("fit", help="exact delivery size by pure scaling, never a crop")
    p.add_argument("image")
    p.add_argument("--size", required=True)
    p.add_argument("--out")
    p.add_argument("--max-kb", type=int)
    p.add_argument("--quality", type=int, default=92)
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=cmd_fit)
    p = sub.add_parser("convert", help="phone photo to an sRGB JPEG or PNG the models accept")
    p.add_argument("image")
    p.add_argument("--out")
    p.add_argument("--max-side", type=int, default=3000)
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=cmd_convert)
    p = sub.add_parser("order", help="copy approved files to listing-order names")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--item", action="append", required=True)
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=cmd_order)
    return parser


def main(argv=None):
    try:
        parser = build_parser()
        args = parser.parse_args(argv)
        if not getattr(args, "func", None):
            raise usage("a command is required: tools, facts, text, contrast, tiles, readback, probe, fit, convert, order")
        result, code = args.func(args)
        return emit(result, code)
    except Fail as exc:
        body = {"ok": False, "kind": exc.kind, "message": exc.message}
        if exc.hint:
            body["hint"] = exc.hint
        body.update(exc.extra)
        return emit(body, exc.code)
    except Exception as exc:   # noqa: BLE001 - one JSON object on stdout, whatever the input was
        return emit({"ok": False, "kind": "internal", "message": "%s: %s" % (type(exc).__name__, exc),
                     "hint": "unexpected input; check the file named in the command"}, 1)


if __name__ == "__main__":
    sys.exit(main())
