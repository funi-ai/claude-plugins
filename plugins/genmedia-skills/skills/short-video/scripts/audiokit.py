#!/usr/bin/env python3
# GENERATED from shared/scripts/audiokit.py — edit the source, then run scripts/sync_shared.py
"""audiokit.py - local, free audio utilities for the genmedia-skills `audio` skill.

Python 3.8+, standard library only. Never calls fal, never needs a key, never spends money.
Prints ONE compact JSON object on stdout. Exit: 0 ok | 1 failed | 2 usage.

  chunk    --input <script.txt|-> --max-chars N [--unit sentence|line] [--endpoint <id> --text-field text
           --base-input base.json --label <slug> --plan-out <path> --price-per-1k <usd> --continuity]
           Split a long script at sentence (or line) boundaries, every chunk <= N characters, nothing lost.
           --unit line: a dialogue line above N is split and every piece keeps its speaker prefix (`Ayşe: `, `[S1] `).
           With --endpoint it writes a `gm.py batch` plan (jobs c001, c002, ...) instead of printing the text.
  captions --input <gm.py output.json|result.json|-> [--job <id>] [--out-base <path without extension>]
           [--formats srt,vtt,txt] [--max-chars 42] [--max-lines 2] [--max-duration 6] [--max-gap 0.8]
           [--offset 0] [--speakers] [--speaker-names speaker_0=Name,...] [--keep-events]
           Word timestamps (Scribe v2, forced alignment) or Wizper segments -> SRT / VTT / transcript files.
           A negative --offset drops the words it moves before 0:00 (reported as dropped_words).
           A failed or pending gm.py object on stdin is passed through unchanged (exit 1 / 0).
           A `gm.py batch` result works too: --job names the transcription job when there are several.
  concat   <file>... | --label <slug> [--plan <plan.json>]   --out <file> [--gap-ms 0] [--force]
           Join audio files in order with local ffmpeg (re-encodes, so mixed formats are fine).
           --label collects the chunk files of a finished `gm.py batch` from .genmedia/runs.jsonl and refuses to
           build an incomplete narration.
  probe    <file>...
           Duration, codec, sample rate and channels through ffprobe (WAV files work without it).
  extract  <media> --out <file> [--start S] [--duration S] [--mono] [--rate HZ] [--force]
           Audio track of a video, or a trimmed / mono / resampled copy of an audio file (voice samples, STT).
  loudnorm <audio> --out <file> [--lufs -16] [--true-peak -1.0] [--lra 11] [--force]
           EBU R128 loudness normalization with local ffmpeg (single pass).

Env: AUDIOKIT_FFMPEG / AUDIOKIT_FFPROBE override the binaries (tests).
"""
import argparse
import json
import math
import os
import re
import unicodedata
import shutil
import subprocess
import sys
import wave

LEDGER = os.path.join(".genmedia", "runs.jsonl")
SENTENCE_END = ".!?…"
CLOSERS = "\"'”’»)]}"
OPENERS = "\"'“‘«([{-—–"
# Tokens after which a full stop does not end a sentence (compared lowercased, without the dot).
ABBREVIATIONS = {
    "dr", "prof", "doç", "yrd", "av", "sn", "no", "bkz", "örn", "vb", "vs", "mr", "mrs", "ms",
    "st", "jr", "sr", "mt", "e.g", "i.e", "approx", "ca", "fig", "op", "cf", "tel", "müh", "uzm",
}
CLAUSE_BREAK = ",;:—–"
# Dialogue line prefix: `Name: ` (short, no colon inside) or a bracket tag such as `[S1]`.
SPEAKER_PREFIX = re.compile(r"(\[[^\]\n]{1,24}\][ \t]*|[^\s:\[\]][^:\n]{0,31}:[ \t]+)(?=\S)")
CODECS = {".mp3": ["-c:a", "libmp3lame", "-q:a", "2"], ".wav": ["-c:a", "pcm_s16le"],
          ".m4a": ["-c:a", "aac", "-b:a", "192k"], ".aac": ["-c:a", "aac", "-b:a", "192k"],
          ".flac": ["-c:a", "flac"], ".ogg": ["-c:a", "libopus", "-b:a", "128k"],
          ".opus": ["-c:a", "libopus", "-b:a", "128k"]}
AUDIO_EXTS = set(CODECS) | {".mpga", ".webm", ".aiff"}


class Fail(Exception):
    def __init__(self, kind, message, code=1, **extra):
        Exception.__init__(self, message)
        self.payload = dict({"ok": False, "kind": kind, "message": message}, **extra)
        self.code = code


def usage(message):
    return Fail("usage", message, 2)


def read_text_arg(value):
    try:
        if value == "-":
            data = sys.stdin.buffer.read()
        else:
            with open(value, "rb") as handle:
                data = handle.read()
        return data.decode("utf-8-sig")
    except OSError as exc:
        raise usage("cannot read %s: %s" % (value, exc.strerror or exc))
    except UnicodeDecodeError:
        raise usage("%s is not valid UTF-8" % value)


def read_json_arg(value, what):
    text = read_text_arg(value)
    start = text.find("{")  # tolerate shell noise before the object
    try:
        doc = json.loads(text[start:] if start > 0 else text)
    except ValueError as exc:
        raise usage("%s is not valid JSON: %s" % (what, exc))
    if not isinstance(doc, dict):
        raise usage("%s must be a JSON object" % what)
    return doc


def write_text(path, text):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


TR_ASCII = str.maketrans("ıİşŞğĞüÜöÖçÇ", "iIsSgGuUoOcC")


def slug(value):
    # same rule as gm.py (transliterate, then strip), so a label names the same ledger rows and folder
    folded = unicodedata.normalize("NFKD", str(value or "").translate(TR_ASCII))
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    out = re.sub(r"[^A-Za-z0-9._-]+", "-", folded).strip("-.")
    return out[:60].strip("-.") or "narration"  # idempotent under gm.py's own slug rule


# ------------------------------------------------------------------ chunk
def split_sentences(paragraph):
    """Sentence spans of one paragraph. Conservative: when unsure, do not split."""
    sentences, start, i, n = [], 0, 0, len(paragraph)
    while i < n:
        if paragraph[i] in SENTENCE_END:
            j = i + 1
            while j < n and (paragraph[j] in SENTENCE_END or paragraph[j] in CLOSERS):
                j += 1
            k = j
            while k < n and paragraph[k].isspace():
                k += 1
            if k == n:
                break
            if k > j and starts_sentence(paragraph[k]) and not is_abbreviation(paragraph, start, i):
                sentences.append(paragraph[start:j].strip())
                start = k
            i = max(j, i + 1)
        else:
            i += 1
    tail = paragraph[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def starts_sentence(char):
    return char.isupper() or char.isdigit() or char in OPENERS or not char.isalpha()


def is_abbreviation(text, start, dot):
    if text[dot] != ".":
        return False
    token = re.split(r"\s", text[start:dot])[-1].lstrip(OPENERS)
    if not token:
        return False
    if len(token) == 1 and token.isalpha() and token.isupper():
        return True  # initials: J. K. Rowling
    return token.lower() in ABBREVIATIONS


def split_long(unit, limit):
    """A single unit above the limit: break at clause punctuation, then at spaces, never inside a word
    unless one word alone exceeds the limit."""
    pieces, rest = [], unit
    while len(rest) > limit:
        window = rest[:limit + 1]
        cut = max(window.rfind(mark + " ") for mark in CLAUSE_BREAK)
        if cut >= limit // 3:
            cut += 1
        else:
            cut = window.rfind(" ")
        if cut <= 0:
            cut = limit
        pieces.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    if rest:
        pieces.append(rest)
    return pieces


def dialogue_lines(text, limit):
    """Line mode. A line above the limit is split like any long unit, and every piece repeats the line's
    speaker prefix, so a dialogue model still knows whose line a continuation is."""
    lines = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = line.strip()
        match = SPEAKER_PREFIX.match(line)
        if len(line) <= limit or not match or len(match.group(0)) > limit // 3:
            if line:
                lines.append(line)
            continue
        prefix, body = match.group(0), line[match.end():]
        pieces = split_long(body, limit - len(prefix))
        if squash("".join(pieces)) != squash(body):
            raise Fail("internal", "splitting a dialogue line lost or changed text; do not use this result")
        lines.extend(prefix + piece for piece in pieces)
    return lines


def make_chunks(text, limit, unit):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if unit == "line":
        paragraphs = [dialogue_lines(text, limit)]
        joiner = "\n"
    else:
        paragraphs = [split_sentences(re.sub(r"\s+", " ", block).strip())
                      for block in re.split(r"\n\s*\n", text) if block.strip()]
        joiner = " "
    chunks, current = [], ""
    for p_index, units in enumerate(paragraphs):
        for u_index, item in enumerate(units):
            glue = "" if not current else ("\n\n" if u_index == 0 and unit != "line" else joiner)
            new_paragraph = u_index == 0 and p_index > 0
            if current and (len(current) + len(glue) + len(item) > limit
                            or (new_paragraph and len(current) >= 0.7 * limit)):
                chunks.append(current)
                current, glue = "", ""
            if len(item) > limit:
                if current:
                    chunks.append(current)
                    current = ""
                parts = split_long(item, limit)
                chunks.extend(parts[:-1])
                current = parts[-1]
            else:
                current = current + glue + item
    if current:
        chunks.append(current)
    return chunks


def squash(text):
    return re.sub(r"\s+", "", text)


def cmd_chunk(args):
    if args.max_chars < 50:
        raise usage("--max-chars must be >= 50")
    text = read_text_arg(args.input)
    if not text.strip():
        raise usage("the script is empty")
    chunks = make_chunks(text, args.max_chars, args.unit)
    # line mode may repeat a speaker prefix on a split line; the text around it must still be untouched
    expected = "".join(dialogue_lines(text, args.max_chars)) if args.unit == "line" else text
    if squash("".join(chunks)) != squash(expected):
        raise Fail("internal", "chunking lost or changed text; do not use this result")
    over = [i + 1 for i, c in enumerate(chunks) if len(c) > args.max_chars]
    if over:
        raise Fail("internal", "chunks %s exceed --max-chars" % over)
    total = sum(len(c) for c in chunks)
    out = {"ok": True, "unit": args.unit, "max_chars": args.max_chars, "count": len(chunks), "total_chars": total,
           "source_chars": len(text), "largest": max(len(c) for c in chunks)}
    rate = args.price_per_1k
    if rate is not None:
        if not (math.isfinite(rate) and rate >= 0):
            raise usage("--price-per-1k must be a finite number >= 0")
        out["est_cost_usd"] = round(total / 1000.0 * rate, 4)
    if not args.endpoint:
        out["chunks"] = [{"id": "c%03d" % (i + 1), "chars": len(c), "text": c} for i, c in enumerate(chunks)]
        return out
    base = read_json_arg(args.base_input, "--base-input") if args.base_input else {}
    if args.text_field in base:
        raise usage("--base-input already contains %r; leave the text to this tool" % args.text_field)
    label = slug(args.label)
    jobs = []
    for i, chunk in enumerate(chunks):
        payload = dict(base)
        payload[args.text_field] = chunk
        if args.continuity:  # only endpoints whose schema lists previous_text / next_text
            if i:
                payload["previous_text"] = chunks[i - 1][-300:]
            if i + 1 < len(chunks):
                payload["next_text"] = chunks[i + 1][:300]
        job = {"id": "c%03d" % (i + 1), "endpoint_id": args.endpoint, "input": payload}
        if rate is not None:
            job["est_cost_usd"] = round(len(chunk) / 1000.0 * rate, 4)
        jobs.append(job)
    plan_path = args.plan_out or os.path.join(".genmedia", "tmp", "%s-plan.json" % label)
    write_text(plan_path, json.dumps({"label": label, "max_parallel": 4, "jobs": jobs},
                                     ensure_ascii=False, indent=1) + "\n")
    out.update(label=label, plan_path=plan_path, endpoint_id=args.endpoint, text_field=args.text_field,
               chunks=[{"id": j["id"], "chars": len(c), "starts": c[:48]} for j, c in zip(jobs, chunks)],
               next="gm.py batch --plan %s" % plan_path)
    return out


# ------------------------------------------------------------------ captions
def number(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def load_tokens(result, keep_events):
    """-> (source, tokens[{text,start,end,speaker,space}], approximate)"""
    words, chunks = result.get("words"), result.get("chunks")
    if isinstance(words, list) and words:
        typed = any(isinstance(w, dict) and w.get("type") == "spacing" for w in words)
        source = "scribe" if any(isinstance(w, dict) and "type" in w for w in words) else "alignment"
        tokens, pending_space = [], ""
        for word in words:
            if not isinstance(word, dict) or not isinstance(word.get("text"), str):
                continue
            kind = word.get("type") or "word"
            if kind == "spacing":
                pending_space = word["text"]
                continue
            if kind == "audio_event" and not keep_events:
                continue
            text = word["text"].strip()
            if not text:
                continue
            tokens.append({"text": text, "start": number(word.get("start")), "end": number(word.get("end")),
                           "speaker": word.get("speaker_id"), "space": pending_space if typed else " "})
            pending_space = ""
        return source, fill_times(tokens), False
    if isinstance(chunks, list) and chunks:
        tokens = []
        for chunk in chunks:
            stamp = chunk.get("timestamp") if isinstance(chunk, dict) else None
            text = (chunk.get("text") or "").strip() if isinstance(chunk, dict) else ""
            if not text or not isinstance(stamp, list) or len(stamp) != 2:
                continue
            start, end = number(stamp[0]), number(stamp[1])
            if start is None:
                continue
            end = end if end is not None and end > start else start + max(1.0, len(text) / 15.0)
            pieces = text.split()
            weights = [len(p) + 1 for p in pieces]
            cursor, span = start, (end - start) / float(sum(weights))
            for piece, weight in zip(pieces, weights):  # spread the segment time over its words
                tokens.append({"text": piece, "start": cursor, "end": cursor + span * weight,
                               "speaker": None, "space": " "})
                cursor += span * weight
        return "wizper", tokens, True
    raise Fail("no_timestamps", "no `words[]` or `chunks[]` with timestamps in the result (keys: %s)"
               % (", ".join(sorted(result)) or "none"))


def fill_times(tokens):
    for i, token in enumerate(tokens):
        if token["start"] is None:
            token["start"] = tokens[i - 1]["end"] if i and tokens[i - 1]["end"] is not None else None
    for i in range(len(tokens) - 1, -1, -1):
        token = tokens[i]
        if token["end"] is None:
            later = tokens[i + 1]["start"] if i + 1 < len(tokens) else None
            token["end"] = later if later is not None else token["start"]
        if token["start"] is None:
            token["start"] = token["end"]
    return [t for t in tokens if t["start"] is not None and t["end"] is not None]


def build_cues(tokens, max_chars, max_lines, max_duration, max_gap):
    budget, cues, current = max_chars * max_lines, [], []

    def text_of(items):
        return "".join((t["space"] if i else "") + t["text"] for i, t in enumerate(items)).strip()

    def close():
        if current:
            cues.append({"start": current[0]["start"], "end": max(current[-1]["end"], current[0]["start"]),
                         "speaker": current[0]["speaker"], "text": re.sub(r"\s+", " ", text_of(current))})
            del current[:]

    for token in tokens:
        if current:
            last = current[-1]
            if (token["speaker"] != last["speaker"] or token["start"] - last["end"] > max_gap
                    or len(text_of(current + [token])) > budget
                    or token["end"] - current[0]["start"] > max_duration):
                close()
        current.append(token)
        ending = token["text"].rstrip(CLOSERS)[-1:]
        if ending and ending in SENTENCE_END:
            close()
    close()
    for i, cue in enumerate(cues):  # readable minimum, never overlapping the next cue
        floor = cue["start"] + 0.7
        ceiling = cues[i + 1]["start"] - 0.04 if i + 1 < len(cues) else floor
        cue["end"] = max(cue["end"], min(floor, ceiling))
        if cue["end"] <= cue["start"]:
            cue["end"] = cue["start"] + 0.05
    return cues


def wrap(text, max_chars, max_lines):
    if len(text) <= max_chars or max_lines < 2:
        return [text]
    words, lines = text.split(" "), []
    if max_lines == 2:  # balanced two-liner: the break closest to the middle that fits
        best = None
        for i in range(1, len(words)):
            left, right = " ".join(words[:i]), " ".join(words[i:])
            if len(left) <= max_chars and len(right) <= max_chars:
                score = abs(len(left) - len(right))
                if best is None or score < best[0]:
                    best = (score, [left, right])
        if best:
            return best[1]
    line = ""
    for word in words:
        if line and len(line) + 1 + len(word) > max_chars:
            lines.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    lines.append(line)
    return lines


def vtt_text(text):
    # WebVTT cue text: `&` and `<` start entities and tags, and `-->` must never appear in a cue
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def stamp(seconds, separator):
    ms = int(round(max(0.0, seconds) * 1000))
    return "%02d:%02d:%02d%s%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, separator, ms % 1000)


def batch_job(doc, job_id):
    """One job of a `gm.py batch` result: --job picks it; without it there must be exactly one with a result."""
    jobs = [job for job in doc["jobs"] if isinstance(job, dict)]
    if job_id:
        picked = [job for job in jobs if job.get("id") == job_id]
    else:
        picked = [job for job in jobs if isinstance(job.get("result"), dict) or job.get("result_path")]
    if len(picked) != 1:
        raise usage("--input is a `gm.py batch` result: name one job with --job (ids: %s)"
                    % ", ".join(str(job.get("id")) for job in jobs))
    return dict(picked[0], label=doc.get("label"))


def cmd_captions(args):
    doc = read_json_arg(args.input, "--input")
    if isinstance(doc.get("jobs"), list):
        doc = batch_job(doc, args.job)
    result = doc.get("result") if isinstance(doc.get("result"), dict) else None
    if result is None and isinstance(doc.get("result_path"), str):  # gm.py stashed a large result
        result = read_json_arg(doc["result_path"], "result_path")
    if result is None and (doc.get("ok") is False or doc.get("status") in ("pending", "submitted", "failed")):
        return doc, (1 if doc.get("ok") is False or doc.get("status") == "failed" else 0)  # pass gm.py through
    result = result if result is not None else doc
    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    if not formats or any(f not in ("srt", "vtt", "txt") for f in formats):
        raise usage("--formats takes a comma list of srt, vtt, txt")
    if args.max_chars < 10 or args.max_lines < 1 or args.max_duration <= 0 or args.max_gap < 0:
        raise usage("--max-chars >= 10, --max-lines >= 1, --max-duration > 0, --max-gap >= 0")
    names = {}
    for pair in (args.speaker_names or "").split(","):
        if pair.strip():
            if "=" not in pair:
                raise usage("--speaker-names takes speaker_0=Name,speaker_1=Name")
            key, value = pair.split("=", 1)
            names[key.strip()] = value.strip()
    source, tokens, approximate = load_tokens(result, args.keep_events)
    if not tokens:
        raise Fail("no_timestamps", "the result has no timed words")
    before = len(tokens)
    if args.offset < 0:  # words moved before 0:00 are cut off, not stacked at 0:00
        tokens = [t for t in tokens if t["end"] + args.offset > 0]
        if not tokens:
            raise Fail("no_timestamps", "--offset %g moves every word before 0:00" % args.offset)
    for token in tokens:
        token["start"] = max(0.0, token["start"] + args.offset)
        token["end"] = max(0.0, token["end"] + args.offset)
    cues = build_cues(tokens, args.max_chars, args.max_lines, args.max_duration, args.max_gap)
    speakers = sorted({c["speaker"] for c in cues if c["speaker"]})
    label_speakers = args.speakers and len(speakers) > 1
    previous, blocks = None, []
    for cue in cues:
        text = cue["text"]
        if label_speakers and cue["speaker"] != previous:
            text = "%s: %s" % (names.get(cue["speaker"], cue["speaker"]), text)
        previous = cue["speaker"]
        blocks.append((cue, wrap(text, args.max_chars, args.max_lines)))
    base = args.out_base or os.path.join("genmedia-output", "captions", "captions")
    files = {"json": base + ".result.json"}
    write_text(files["json"], json.dumps(result, ensure_ascii=False) + "\n")
    if "srt" in formats:
        files["srt"] = base + ".srt"
        write_text(files["srt"], "".join("%d\n%s --> %s\n%s\n\n" % (
            i + 1, stamp(c["start"], ","), stamp(c["end"], ","), "\n".join(lines))
            for i, (c, lines) in enumerate(blocks)))
    if "vtt" in formats:
        files["vtt"] = base + ".vtt"
        write_text(files["vtt"], "WEBVTT\n\n" + "".join("%s --> %s\n%s\n\n" % (
            stamp(c["start"], "."), stamp(c["end"], "."), "\n".join(vtt_text(l) for l in lines))
            for c, lines in blocks))
    if "txt" in formats:
        files["txt"] = base + ".txt"
        paragraphs, previous = [], object()
        for cue in cues:
            if cue["speaker"] != previous or not paragraphs:
                head = "%s: " % names.get(cue["speaker"], cue["speaker"]) if len(speakers) > 1 else ""
                paragraphs.append(head + cue["text"])
            else:
                paragraphs[-1] += " " + cue["text"]
            previous = cue["speaker"]
        write_text(files["txt"], "\n\n".join(paragraphs) + "\n")
    out = {"ok": True, "source": source, "approximate_timing": approximate, "cues": len(cues),
           "duration_s": round(cues[-1]["end"], 3), "language": result.get("language_code") or
           (result.get("languages") or [None])[0], "speakers": speakers, "files": files,
           "preview": [{"start": stamp(c["start"], ","), "end": stamp(c["end"], ","), "text": " / ".join(lines)}
                       for c, lines in blocks[:2]]}
    if before > len(tokens):
        out["dropped_words"] = before - len(tokens)
    for key in ("request_id", "endpoint_id", "label", "est_cost_usd"):
        if doc.get(key) is not None:
            out[key] = doc[key]
    if isinstance(result.get("loss"), (int, float)):
        out["alignment_loss"] = result["loss"]
    return out


# ------------------------------------------------------------------ concat / probe
def find_tool(env_name, binary):
    return os.environ.get(env_name) or shutil.which(binary)


def ledger_chunks(label, plan_path):
    if not os.path.isfile(LEDGER):
        raise Fail("no_ledger", "%s not found; pass the files explicitly" % LEDGER)
    jobs = {}
    with open(LEDGER, "r", encoding="utf-8") as handle:
        for raw in handle:
            try:
                line = json.loads(raw)
            except ValueError:
                continue
            if isinstance(line, dict) and line.get("label") == label and line.get("request_id"):
                entry = jobs.setdefault(line["request_id"], {})
                entry.update({k: v for k, v in line.items() if v is not None})
    done = {}
    for entry in jobs.values():  # later requests of the same job id win (retries)
        if entry.get("status") == "completed" and entry.get("job_id"):
            paths = [o["path"] for o in entry.get("outputs") or [] if isinstance(o, dict) and o.get("path")]
            audio = [p for p in paths if os.path.splitext(p)[1].lower() in AUDIO_EXTS]
            if paths:
                done[entry["job_id"]] = (audio or paths)[0]
    expected = None
    if plan_path:
        plan = read_json_arg(plan_path, "--plan")
        expected = [j.get("id") for j in plan.get("jobs") or [] if isinstance(j, dict)]
    elif done:
        numbered = sorted(k for k in done if re.match(r"^c\d+$", k))
        expected = ["c%03d" % n for n in range(1, int(numbered[-1][1:]) + 1)] if numbered else sorted(done)
    missing = [job_id for job_id in expected or [] if job_id not in done]
    if not done or missing:
        raise Fail("incomplete", "label %r is not complete; rerun the same `gm.py batch` command first"
                   % label, missing=missing, completed=sorted(done))
    return [done[job_id] for job_id in expected or []]


def probe_one(path, ffprobe):
    info = {"path": path, "size_bytes": os.path.getsize(path)}
    if ffprobe:
        proc = subprocess.run([ffprobe, "-v", "error", "-show_entries",
                               "format=duration:stream=codec_type,codec_name,sample_rate,channels",
                               "-of", "json", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        try:
            doc = json.loads(proc.stdout.decode("utf-8", "replace") or "{}")
        except ValueError:
            doc = {}
        if proc.returncode != 0 or not doc.get("format"):
            raise Fail("probe_failed", "ffprobe could not read %s: %s"
                       % (path, proc.stderr.decode("utf-8", "replace").strip()[-300:]))
        audio = next((s for s in doc.get("streams") or [] if s.get("codec_type") == "audio"), {})
        info.update(duration_s=round(float(doc["format"].get("duration") or 0), 3), codec=audio.get("codec_name"),
                    sample_rate=int(audio["sample_rate"]) if audio.get("sample_rate") else None,
                    channels=audio.get("channels"), has_audio=bool(audio))
        return info
    if path.lower().endswith(".wav"):
        try:
            with wave.open(path, "rb") as handle:
                info.update(duration_s=round(handle.getnframes() / float(handle.getframerate()), 3), codec="pcm",
                            sample_rate=handle.getframerate(), channels=handle.getnchannels(), has_audio=True)
            return info
        except (wave.Error, EOFError, ZeroDivisionError) as exc:
            raise Fail("probe_failed", "cannot read %s as WAV: %s" % (path, exc))
    raise Fail("ffprobe_missing", "ffprobe is not installed; use the duration fields of the model result or "
               "fal-ai/ffmpeg-api/metadata (media_url -> result.media.duration)")


def cmd_probe(args):
    for path in args.files:
        if not os.path.isfile(path):
            raise usage("file not found: %s" % path)
    ffprobe = find_tool("AUDIOKIT_FFPROBE", "ffprobe")
    files = [probe_one(path, ffprobe) for path in args.files]
    return {"ok": True, "files": files, "total_duration_s": round(sum(f["duration_s"] for f in files), 3)}


def cmd_concat(args):
    if bool(args.files) == bool(args.label):
        raise usage("give either files or --label")
    if args.gap_ms < 0 or args.gap_ms > 10000:
        raise usage("--gap-ms must be between 0 and 10000")
    files = args.files or ledger_chunks(slug(args.label), args.plan)
    for path in files:
        if not os.path.isfile(path):
            raise usage("file not found: %s" % path)
    if len(files) < 2:
        raise usage("need at least two files to join")
    if os.path.exists(args.out) and not args.force:
        raise usage("%s exists; choose another --out or pass --force" % args.out)
    ffmpeg = find_tool("AUDIOKIT_FFMPEG", "ffmpeg")
    if not ffmpeg:
        raise Fail("ffmpeg_missing", "ffmpeg is not installed; join on fal instead with "
                   "fal-ai/ffmpeg-api/merge-audios (audio_urls: 2-5 URLs per call, in order)")
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y" if args.force else "-n"]
    for path in files:
        command += ["-i", path]
    graph, labels = [], []
    for index in range(len(files)):
        pad = "apad=pad_dur=%.3f" % (args.gap_ms / 1000.0) if args.gap_ms and index + 1 < len(files) else "anull"
        graph.append("[%d:a:0]%s[a%d]" % (index, pad, index))
        labels.append("[a%d]" % index)
    graph.append("%sconcat=n=%d:v=0:a=1[out]" % ("".join(labels), len(files)))
    command += ["-filter_complex", ";".join(graph), "-map", "[out]"]
    command += CODECS.get(os.path.splitext(args.out)[1].lower(), []) + [args.out]
    folder = os.path.dirname(args.out)
    if folder:
        os.makedirs(folder, exist_ok=True)
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1800)
    if proc.returncode != 0 or not os.path.isfile(args.out) or os.path.getsize(args.out) == 0:
        raise Fail("ffmpeg_failed", proc.stderr.decode("utf-8", "replace").strip()[-600:] or "ffmpeg failed")
    out = {"ok": True, "out": args.out, "inputs": len(files), "order": files, "gap_ms": args.gap_ms,
           "size_bytes": os.path.getsize(args.out)}
    try:
        out["duration_s"] = probe_one(args.out, find_tool("AUDIOKIT_FFPROBE", "ffprobe"))["duration_s"]
    except Fail:
        out["duration_s"] = None
    return out


def run_ffmpeg(source, out_path, force, middle, fallback_hint):
    """ffmpeg -i <source> <middle...> <codec for the extension> <out>; returns size and duration."""
    if not os.path.isfile(source):
        raise usage("file not found: %s" % source)
    if os.path.exists(out_path) and not force:
        raise usage("%s exists; choose another --out or pass --force" % out_path)
    if os.path.abspath(source) == os.path.abspath(out_path):
        raise usage("--out must differ from the input")
    ffmpeg = find_tool("AUDIOKIT_FFMPEG", "ffmpeg")
    if not ffmpeg:
        raise Fail("ffmpeg_missing", "ffmpeg is not installed; %s" % fallback_hint)
    folder = os.path.dirname(out_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    command = ([ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y" if force else "-n"] + middle
               + CODECS.get(os.path.splitext(out_path)[1].lower(), []) + [out_path])
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1800)
    if proc.returncode != 0 or not os.path.isfile(out_path) or os.path.getsize(out_path) == 0:
        raise Fail("ffmpeg_failed", proc.stderr.decode("utf-8", "replace").strip()[-600:] or "ffmpeg failed")
    out = {"ok": True, "out": out_path, "size_bytes": os.path.getsize(out_path)}
    try:
        out["duration_s"] = probe_one(out_path, find_tool("AUDIOKIT_FFPROBE", "ffprobe"))["duration_s"]
    except Fail:
        out["duration_s"] = None
    return out


def cmd_extract(args):
    if args.start < 0 or (args.duration is not None and args.duration <= 0):
        raise usage("--start must be >= 0 and --duration > 0")
    if args.rate is not None and not 8000 <= args.rate <= 96000:
        raise usage("--rate must be between 8000 and 96000")
    middle = (["-ss", "%.3f" % args.start] if args.start else []) + ["-i", args.media]
    middle += ["-t", "%.3f" % args.duration] if args.duration is not None else []
    middle += ["-vn", "-map", "0:a:0"] + (["-ac", "1"] if args.mono else [])
    middle += ["-ar", str(args.rate)] if args.rate else []
    return run_ffmpeg(args.media, args.out, args.force, middle,
                      "fal-ai/elevenlabs/audio-isolation accepts a video_url and returns its speech as audio")


def cmd_loudnorm(args):
    if not (-70 <= args.lufs <= -5 and -9 <= args.true_peak <= 0 and 1 <= args.lra <= 50):
        raise usage("--lufs -70..-5, --true-peak -9..0, --lra 1..50")
    graph = "loudnorm=I=%g:TP=%g:LRA=%g" % (args.lufs, args.true_peak, args.lra)
    out = run_ffmpeg(args.audio, args.out, args.force, ["-i", args.audio, "-vn", "-af", graph],
                     "normalize on fal instead with fal-ai/ffmpeg-api/loudnorm (audio_url, integrated_loudness)")
    out.update(target_lufs=args.lufs, true_peak=args.true_peak, lra=args.lra)
    return out


# ------------------------------------------------------------------ cli
class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise usage(message)


def build_parser():
    parser = Parser(prog="audiokit.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>", parser_class=Parser)
    p = sub.add_parser("chunk", help="split a script at sentence boundaries; optional gm.py batch plan")
    p.add_argument("--input", required=True, metavar="FILE|-")
    p.add_argument("--max-chars", required=True, type=int, metavar="N")
    p.add_argument("--unit", choices=("sentence", "line"), default="sentence",
                   help="line: never split inside a line (speaker-prefixed dialogue)")
    p.add_argument("--endpoint", metavar="ID", help="write a batch plan for this endpoint")
    p.add_argument("--text-field", default="text", help="input field that takes the text: text | prompt | ...")
    p.add_argument("--base-input", metavar="FILE", help="JSON object with every other input field (voice, language)")
    p.add_argument("--label", default="narration")
    p.add_argument("--plan-out", metavar="FILE", help="default .genmedia/tmp/<label>-plan.json")
    p.add_argument("--price-per-1k", type=float, metavar="USD", help="unit price per 1000 characters (gm.py price)")
    p.add_argument("--continuity", action="store_true",
                   help="add previous_text/next_text (only for endpoints whose schema lists them)")
    p.set_defaults(func=cmd_chunk)
    p = sub.add_parser("captions", help="word timestamps -> SRT / VTT / transcript")
    p.add_argument("--input", required=True, metavar="FILE|-")
    p.add_argument("--job", metavar="ID", help="job id inside a `gm.py batch` result")
    p.add_argument("--out-base", metavar="PATH", help="path without extension (default genmedia-output/captions/captions)")
    p.add_argument("--formats", default="srt,vtt,txt")
    p.add_argument("--max-chars", type=int, default=42, help="per line")
    p.add_argument("--max-lines", type=int, default=2)
    p.add_argument("--max-duration", type=float, default=6.0, help="seconds per cue")
    p.add_argument("--max-gap", type=float, default=0.8, help="a longer silence starts a new cue")
    p.add_argument("--offset", type=float, default=0.0, help="shift every cue by this many seconds")
    p.add_argument("--speakers", action="store_true", help="prefix a cue with the speaker when it changes")
    p.add_argument("--speaker-names", metavar="speaker_0=Name,...")
    p.add_argument("--keep-events", action="store_true", help="keep audio events such as (laughter)")
    p.set_defaults(func=cmd_captions)
    p = sub.add_parser("concat", help="join audio files in order with local ffmpeg")
    p.add_argument("files", nargs="*")
    p.add_argument("--label", help="collect the chunk files of a finished gm.py batch from the ledger")
    p.add_argument("--plan", metavar="FILE", help="with --label: the plan that defines the expected job ids")
    p.add_argument("--out", required=True)
    p.add_argument("--gap-ms", type=int, default=0, help="silence between files")
    p.add_argument("--force", action="store_true", help="overwrite --out")
    p.set_defaults(func=cmd_concat)
    p = sub.add_parser("probe", help="duration and format of local files")
    p.add_argument("files", nargs="+")
    p.set_defaults(func=cmd_probe)
    p = sub.add_parser("extract", help="audio track of a video, or a trimmed/mono/resampled copy")
    p.add_argument("media")
    p.add_argument("--out", required=True)
    p.add_argument("--start", type=float, default=0.0, help="seconds")
    p.add_argument("--duration", type=float, help="seconds")
    p.add_argument("--mono", action="store_true")
    p.add_argument("--rate", type=int, metavar="HZ")
    p.add_argument("--force", action="store_true", help="overwrite --out")
    p.set_defaults(func=cmd_extract)
    p = sub.add_parser("loudnorm", help="EBU R128 loudness normalization with local ffmpeg")
    p.add_argument("audio")
    p.add_argument("--out", required=True)
    p.add_argument("--lufs", type=float, default=-16.0, help="integrated loudness target")
    p.add_argument("--true-peak", type=float, default=-1.0, help="dBTP ceiling")
    p.add_argument("--lra", type=float, default=11.0, help="loudness range target")
    p.add_argument("--force", action="store_true", help="overwrite --out")
    p.set_defaults(func=cmd_loudnorm)
    return parser


def main(argv=None):
    code = 0
    try:
        parser = build_parser()
        args = parser.parse_args(argv)
        if not getattr(args, "func", None):
            raise usage("missing command: chunk | captions | concat | probe | extract | loudnorm")
        out = args.func(args)
        if isinstance(out, tuple):
            out, code = out
    except Fail as exc:
        out, code = exc.payload, exc.code
    except subprocess.TimeoutExpired as exc:
        out, code = {"ok": False, "kind": "timeout", "message": "%s timed out" % exc.cmd[0]}, 1
    sys.stdout.write(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
