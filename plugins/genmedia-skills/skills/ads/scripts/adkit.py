#!/usr/bin/env python3
"""adkit.py - deterministic ad-script arithmetic for the genmedia-skills `ads` skill.

Python 3.8+, standard library only. Never calls fal, never needs a key, never spends money.
Prints ONE compact JSON object on stdout. Exit: 0 ok | 1 problems | 2 usage.

  budget --duration <seconds> [--lang en] [--wps <words per second>] [--beats hook,problem,...]
      Word budget for a spoken ad: speech window, total words, words and time window per beat,
      estimated characters (for TTS cost). Rates are planning heuristics; the measured voice file decides.
  check  --script <script.json|-> [--tolerance 0.10]
      Lint a script: words per beat against the budget, estimated speech seconds, on-camera seconds
      (talking-head cost), characters (TTS cost), and claim flags (number, offer, superlative, absolute,
      health, money, urgency, social_proof; numbers also when written as words, English always, Turkish
      for lang "tr"). A flagged beat without a non-empty "source" is a problem.
      script.json: {"lang":"tr","duration_s":15,"wps":null,
                    "beats":[{"beat":"hook","text":"...","on_camera":true,"source":""}]}
      "source" is a string or a list of fact ids ("F1"); empty means unsourced.
      "store_listing": true (top level, or per beat) marks copy that also appears on an App Store or Google Play
      asset (listing screenshots, custom product pages that Apple Ads shows, the Play feature graphic). There a
      source does not help: ranking, superlative, price, offer, urgency and award wording is a problem
      (store_listing_claim). Both stores keep such talk out of listing assets.
      This is a lint, not legal advice: it finds wording that needs a source, it cannot tell whether
      the source is true.
  matrix --hooks N --visuals N --ctas N [--cost-hook USD --cost-visual USD --cost-cta USD
         --cost-assembly USD] [--max 6] [--have-base]
      Size an A/B matrix: components produced once, variants assembled from them, shared-component
      total next to the naive total. --have-base: variant h1-v1-c1 already exists and is not repaid.
"""
import argparse
import json
import math
import re
import sys
import unicodedata

# Planning heuristics (words per second of comfortable ad delivery). Agglutinative languages carry
# more syllables per word, so fewer words fit. The measured voice file always wins.
WPS = {"en": 2.5, "tr": 2.0, "de": 2.0, "es": 2.6, "fr": 2.6, "it": 2.5, "pt": 2.5, "nl": 2.4,
       "ar": 2.0, "ru": 2.0, "pl": 2.0, "ja": 2.2, "ko": 2.2}
WPS_DEFAULT = 2.2
CHARS_PER_WORD = {"en": 6.0, "tr": 7.5, "de": 7.5}
CHARS_PER_WORD_DEFAULT = 6.5

LEAD_IN_S = 0.3
SHORT_MAX_S = 8
LONG_MIN_S = 21
SHARES = {
    "short": [("hook", 0.45), ("product", 0.35), ("cta", 0.20)],
    "medium": [("hook", 0.20), ("problem", 0.20), ("product", 0.25), ("proof", 0.15), ("cta", 0.20)],
    "long": [("hook", 0.12), ("problem", 0.20), ("product", 0.28), ("proof", 0.22), ("cta", 0.18)],
}
HOOK_WARN_WORDS = 10
BEAT_WARN_RATIO = 1.35

_FOLD_MAP = str.maketrans({"ı": "i", "İ": "i", "I": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
                           "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
                           "’": "'", "`": "'"})

# Patterns run on folded text (lowercase, Turkish letters mapped to ASCII, accents stripped).
CLAIM_PATTERNS = [
    ("number", r"\d+(?:[.,]\d+)*|[%₺$€£]|\b(?:percent|yuzde|lira|tl)\b"),
    ("offer", r"\b(?:free|discount\w*|sale|% ?off|coupon|promo code|free shipping|ucretsiz|bedava|"
              r"indirim\w*|kampanya\w*|kupon\w*|hediye\w*)\b"),
    ("superlative", r"\b(?:best|number one|no\.? ?1|#1|leading|world'?s|unbeatable|en iyi\w*|en cok|"
                    r"bir numara\w*|1 numara\w*|lider\w*|essiz|rakipsiz)\b|#1"),
    ("absolute", r"\b(?:guarantee\w*|always|never|instant\w*|permanent\w*|proven|miracle\w*|risk-?free|"
                 r"garanti\w*|kesin\w*|aninda|kalici\w*|kanitlanmis|mucize\w*|risksiz)\b"),
    ("health", r"\b(?:cure\w*|heal\w*|treat\w*|clinical\w*|dermatolog\w*|doctor\w*|medical\w*|fda|"
               r"anti-?aging|weight loss|lose weight|tedavi\w*|iyilestir\w*|klinik\w*|doktor\w*|"
               r"dermatolojik\w*|zayifla\w*|kilo ver\w*|sifa\w*|hastalik\w*)\b"),
    ("money", r"\b(?:earn\w*|income|profit\w*|returns?|get rich|roi|kazanc\w*|para kazan\w*|gelir\w*|"
              r"getiri\w*|zengin\w*|yatirim\w*)\b"),
    ("urgency", r"\b(?:today only|last chance|ends (?:today|tonight|soon)|limited (?:time|stock)|"
                r"hurry|selling out|while (?:stocks?|supplies) last|son (?:gun|sans|firsat)\w*|"
                r"sadece bugun|bugune ozel|stoklar? (?:tukeniyor|sinirli)|sinirli (?:sure|stok)\w*|"
                r"acele et\w*|kacirma\w*|tukenmeden)\b"),
    ("social_proof", r"\b(?:customers?|reviews?|rated|ratings?|stars?|users?|trusted by|bestsell\w*|"
                     r"sold|award\w*|recommended by|musteri\w*|yorum\w*|yildiz\w*|kullanici\w*|"
                     r"cok satan\w*|satildi|odul\w*|tavsiye e\w*)\b"),
]
CLAIM_RES = [(kind, re.compile(pattern)) for kind, pattern in CLAIM_PATTERNS]
# Wording the stores keep out of listing assets whatever its source: Play's preview-asset rules name ranking, price and
# promotion talk; Apple Ads refuses pricing, offers, rankings and awards in Today tab assets (read 2026-09-20).
STORE_LISTING_KINDS = ("offer", "superlative", "urgency")
STORE_LISTING_RE = re.compile(r"[₺$€£]\s?\d|\d[\d.,]*\s?(?:[₺$€£]|(?:tl|lira|usd|eur)\b)|\b(?:price\w*|fiyat\w*|award\w*|odul\w*|winner|app of the (?:day|year)|"
                              r"editor'?s choice|top (?:rated|free|paid|grossing|\d+)|ranked|bestsell\w*|cok satan\w*|"
                              r"install now|download now|hemen indir|simdi indir)\b")
# Numbers written as words ("twenty-four hours", "yirmi dört saat", "thousands of people") are the same
# claim as digits. English words always run; Turkish ones only for lang "tr". "one" / "bir" and the
# ambiguous "double", "altı", "yüz" are left out; "on" and "bin" match the unfolded text ("ön" is not ten).
NUMBER_WORDS_EN = re.compile(
    r"\b(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|(?:thir|four|fif|six|seven|eigh|nine)teen|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundreds?|thousands?|millions?|billions?|half|"
    r"twice)\b")
NUMBER_WORDS_TR = re.compile(
    r"\b(?:iki|uc|dort|bes|yedi|sekiz|dokuz|yirmi|otuz|kirk|elli|altmis|yetmis|seksen|doksan|milyon|milyar|"
    r"onlarca|yuzlerce|binlerce|milyonlarca|yari|yarisi)\b")
NUMBER_WORDS_TR_RAW = re.compile(r"\b(?:on|bin)\b")
TOKEN_RE = re.compile(r"[^\W_]+(?:['\-][^\W_]+)*", re.UNICODE)


class UsageError(Exception):
    pass


def emit(obj, code):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
    return code


def fold(text):
    text = text.translate(_FOLD_MAP).lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def norm_lang(lang):
    return re.split(r"[-_ ]", (lang or "en").strip().lower())[0] or "en"


def spoken_words(token):
    """Words a token takes when read aloud. Digits expand: 1999 is five words, 50 is one."""
    digits = re.sub(r"\D", "", token)
    if not digits:
        return 1
    nonzero = sum(1 for ch in digits if ch != "0")
    return max(1, nonzero) + (1 if len(digits) >= 4 else 0)


def count_words(text):
    return sum(spoken_words(tok) for tok in TOKEN_RE.findall(text.replace("’", "'")))


def tier_for(duration):
    if duration <= SHORT_MAX_S:
        return "short"
    if duration >= LONG_MIN_S:
        return "long"
    return "medium"


def speech_window(duration):
    tail = 0.5 if duration <= SHORT_MAX_S else 1.2
    return max(1.0, round(duration - LEAD_IN_S - tail, 2))


def shares_for(duration, names=None):
    table = SHARES[tier_for(duration)]
    if not names:
        return table
    known = dict(table)
    average = 1.0 / len(names)
    raw = [(name, known.get(name, average)) for name in names]
    total = sum(share for _, share in raw) or 1.0
    return [(name, share / total) for name, share in raw]


def split_words(total, shares):
    exact = [share * total for _, share in shares]
    floors = [int(math.floor(value)) for value in exact]
    remainder = total - sum(floors)
    order = sorted(range(len(exact)), key=lambda i: exact[i] - floors[i], reverse=True)
    for i in order[:max(0, remainder)]:
        floors[i] += 1
    return floors


def build_budget(duration, lang, wps=None, names=None):
    lang = norm_lang(lang)
    rate = float(wps) if wps else WPS.get(lang, WPS_DEFAULT)
    speech = speech_window(duration)
    total = max(len(names or []) or 1, int(math.floor(speech * rate)))
    shares = shares_for(duration, names)
    words = split_words(total, shares)
    beats, cursor = [], LEAD_IN_S
    for (name, _), count in zip(shares, words):
        length = count / rate
        beats.append({"beat": name, "words": count, "start_s": round(cursor, 1),
                      "end_s": round(cursor + length, 1)})
        cursor += length
    if float(duration).is_integer():
        duration = int(duration)
    return {"duration_s": duration, "lang": lang, "wps": rate, "speech_s": speech, "words_total": total,
            "est_chars": int(math.ceil(total * CHARS_PER_WORD.get(lang, CHARS_PER_WORD_DEFAULT))),
            "beats": beats}


def cmd_budget(args):
    if args.duration <= 0 or args.duration > 180:
        raise UsageError("--duration must be between 1 and 180 seconds")
    if args.wps is not None and not 0.5 <= args.wps <= 5:
        raise UsageError("--wps must be between 0.5 and 5")
    names = [n.strip() for n in args.beats.split(",") if n.strip()] if args.beats else None
    out = {"ok": True}  # type: dict
    out.update(build_budget(args.duration, args.lang, args.wps, names))
    out["note"] = ("planning heuristic: measure the generated voice file and trim words, never speed "
                   "the voice up; the spoken hook should stay within 3 to 8 words")
    return emit(out, 0)


def load_script(path):
    try:
        if path == "-":
            raw = sys.stdin.read()
        else:
            with open(path, "r", encoding="utf-8") as fh:
                raw = fh.read()
    except OSError as exc:
        raise UsageError("cannot read %s: %s" % (path, exc.strerror or exc))
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise UsageError("script is not valid JSON: %s" % exc)
    if not isinstance(data, dict) or not isinstance(data.get("beats"), list) or not data["beats"]:
        raise UsageError('script must be an object with a non-empty "beats" list')
    duration = data.get("duration_s")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not 0 < duration <= 180:
        raise UsageError('"duration_s" must be a number between 1 and 180')
    if data.get("lang") is not None and not isinstance(data["lang"], str):
        raise UsageError('"lang" must be a language code string such as "en" or "tr"')
    seen = set()
    for index, beat in enumerate(data["beats"]):
        if not isinstance(beat, dict) or not isinstance(beat.get("beat"), str) or not beat["beat"].strip():
            raise UsageError('beats[%d] needs a "beat" name' % index)
        if not isinstance(beat.get("text"), str):
            raise UsageError('beats[%d] needs a "text" string (may be empty for a silent beat)' % index)
        if beat["beat"] in seen:
            raise UsageError('duplicate beat name "%s"' % beat["beat"])
        seen.add(beat["beat"])
    return data


def has_source(source):
    """A non-empty string, or a list of fact ids with at least one non-empty string."""
    if isinstance(source, str):
        return bool(source.strip())
    if isinstance(source, list):
        return any(isinstance(item, str) and item.strip() for item in source)
    return False


def find_flags(text, lang=None):
    folded = fold(text)
    checks = [(kind, regex, folded) for kind, regex in CLAIM_RES]
    checks.insert(1, ("number", NUMBER_WORDS_EN, folded))
    if norm_lang(lang) == "tr":
        checks.insert(2, ("number", NUMBER_WORDS_TR, folded))
        checks.insert(3, ("number", NUMBER_WORDS_TR_RAW, text.replace("İ", "i").replace("I", "ı").lower()))
    flags, seen = [], set()
    for kind, regex, haystack in checks:
        for match in regex.finditer(haystack):
            key = (kind, match.group(0))
            if key not in seen:
                seen.add(key)
                flags.append({"kind": kind, "match": match.group(0)})
    return flags


def cmd_check(args):
    if not 0 <= args.tolerance <= 0.5:
        raise UsageError("--tolerance must be between 0 and 0.5")
    script = load_script(args.script)
    wps = script.get("wps")
    if wps is not None and (not isinstance(wps, (int, float)) or isinstance(wps, bool) or not 0.5 <= wps <= 5):
        raise UsageError('"wps" must be null or a number between 0.5 and 5')
    names = [beat["beat"] for beat in script["beats"]]
    budget = build_budget(script["duration_s"], script.get("lang"), wps, names)
    rate = budget["wps"]
    per_beat = {b["beat"]: b["words"] for b in budget["beats"]}

    problems, warnings, rows = [], [], []
    words_total = chars_total = 0
    on_camera_s = 0.0
    for beat in script["beats"]:
        name, text = beat["beat"], beat["text"]
        words = count_words(text)
        est = round(words / rate, 1)
        sourced = has_source(beat.get("source"))
        flags = find_flags(text, script.get("lang"))
        for flag in flags:
            flag["sourced"] = sourced
        if bool(beat.get("store_listing", script.get("store_listing"))):
            banned = sorted({f["match"] for f in flags if f["kind"] in STORE_LISTING_KINDS}
                            | {m.group(0) for m in STORE_LISTING_RE.finditer(fold(text))})
            if banned:
                problems.append({"kind": "store_listing_claim", "beat": name,
                                 "message": "%s: ranking, price, offer, award and call-to-action wording stays off assets that "
                                            "also sit on a store listing, sourced or not; keep it for the ad-only version"
                                            % ", ".join(banned[:5])})
        if flags and not sourced:
            kinds = sorted({f["kind"] for f in flags})
            problems.append({"kind": "unsourced_claim", "beat": name,
                             "message": "%s wording (%s) has no source: add the user's fact as \"source\" "
                                        "or rewrite the line" % (", ".join(kinds),
                                                                 ", ".join(f["match"] for f in flags[:4]))})
        if per_beat[name] and words > per_beat[name] * BEAT_WARN_RATIO:
            warnings.append({"kind": "beat_long", "beat": name,
                             "message": "%d words against a share of %d" % (words, per_beat[name])})
        if name == "hook" and words > HOOK_WARN_WORDS:
            warnings.append({"kind": "hook_long", "beat": name,
                             "message": "%d words; a spoken hook works at 3 to 8" % words})
        if bool(beat.get("on_camera")):
            on_camera_s += words / rate
        words_total += words
        chars_total += len(text)
        rows.append({"beat": name, "words": words, "budget": per_beat[name], "est_s": est,
                     "on_camera": bool(beat.get("on_camera")), "chars": len(text), "flags": flags})

    limit = budget["words_total"] * (1 + args.tolerance)
    if words_total > limit:
        problems.insert(0, {"kind": "over_budget",
                            "message": "%d words against a budget of %d (%.1f s of speech in a %.1f s window): "
                                       "cut %d words" % (words_total, budget["words_total"],
                                                         words_total / rate, budget["speech_s"],
                                                         words_total - budget["words_total"])})
    out = {"ok": not problems, "lang": budget["lang"], "duration_s": script["duration_s"], "wps": rate,
           "words_total": words_total, "budget_total": budget["words_total"],
           "est_speech_s": round(words_total / rate, 1), "speech_budget_s": budget["speech_s"],
           "on_camera_s": round(on_camera_s, 1), "chars_total": chars_total, "beats": rows,
           "problems": problems, "warnings": warnings,
           "note": "lint only: a source makes a claim traceable, not true; numbers count as spoken words"}
    return emit(out, 0 if not problems else 1)


def cmd_matrix(args):
    counts = {"hooks": args.hooks, "visuals": args.visuals, "ctas": args.ctas}
    for key, value in counts.items():
        if value < 1 or value > 12:
            raise UsageError("--%s must be between 1 and 12" % key)
    costs = {"hook": args.cost_hook, "visual": args.cost_visual, "cta": args.cost_cta,
             "assembly": args.cost_assembly}
    for key, value in costs.items():
        if value < 0:
            raise UsageError("--cost-%s must not be negative" % key)
    if args.max < 1:
        raise UsageError("--max must be at least 1")

    variants = ["h%d-v%d-c%d" % (h, v, c) for h in range(1, args.hooks + 1)
                for v in range(1, args.visuals + 1) for c in range(1, args.ctas + 1)]
    base = 1 if args.have_base else 0
    produce = {"hooks": args.hooks - base, "visuals": args.visuals - base, "ctas": args.ctas - base}
    assemble = len(variants) - base
    components = (produce["hooks"] * costs["hook"] + produce["visuals"] * costs["visual"]
                  + produce["ctas"] * costs["cta"])
    assembly = assemble * costs["assembly"]
    naive = assemble * (costs["hook"] + costs["visual"] + costs["cta"] + costs["assembly"])
    axes = [name for name, value in counts.items() if value > 1]

    problems, warnings = [], []
    if len(variants) > args.max:
        problems.append({"kind": "over_cap",
                         "message": "%d variants exceed the cap of %d: drop an axis or raise --max after the "
                                    "user agreed" % (len(variants), args.max)})
    if len(axes) > 1:
        warnings.append({"kind": "multi_axis",
                         "message": "%s vary together: a full grid needs more spend and traffic per cell; "
                                    "one axis per test unless the user asked for the grid" % " and ".join(axes)})
    out = {"ok": not problems, "variants": variants, "variant_count": len(variants), "axes_varied": axes,
           "produce_once": produce, "assemble": assemble, "have_base": bool(args.have_base),
           "cost": {"components_usd": round(components, 2), "assembly_usd": round(assembly, 2),
                    "total_usd": round(components + assembly, 2), "naive_total_usd": round(naive, 2)},
           "problems": problems, "warnings": warnings,
           "note": "ids read h<hook>-v<visual>-c<cta>; each component is generated once and reused"}
    return emit(out, 0 if not problems else 1)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def build_parser():
    parser = Parser(prog="adkit.py", description=__doc__,
                    formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>", parser_class=Parser)
    p = sub.add_parser("budget", help="word budget per beat for a duration and language")
    p.add_argument("--duration", type=float, required=True)
    p.add_argument("--lang", default="en")
    p.add_argument("--wps", type=float, default=None)
    p.add_argument("--beats", default=None)
    p.set_defaults(func=cmd_budget)
    p = sub.add_parser("check", help="lint a script.json: budget, timings, unsourced claims")
    p.add_argument("--script", required=True)
    p.add_argument("--tolerance", type=float, default=0.10)
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("matrix", help="size an A/B matrix and its cost with shared components")
    p.add_argument("--hooks", type=int, required=True)
    p.add_argument("--visuals", type=int, required=True)
    p.add_argument("--ctas", type=int, required=True)
    p.add_argument("--cost-hook", type=float, default=0.0)
    p.add_argument("--cost-visual", type=float, default=0.0)
    p.add_argument("--cost-cta", type=float, default=0.0)
    p.add_argument("--cost-assembly", type=float, default=0.0)
    p.add_argument("--max", type=int, default=6)
    p.add_argument("--have-base", action="store_true")
    p.set_defaults(func=cmd_matrix)
    return parser


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if not getattr(args, "func", None):
            raise UsageError("a command is required: budget | check | matrix")
        return args.func(args)
    except UsageError as exc:
        return emit({"ok": False, "kind": "usage", "message": str(exc)}, 2)


if __name__ == "__main__":
    sys.exit(main())
