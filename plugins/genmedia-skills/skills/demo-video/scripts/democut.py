#!/usr/bin/env python3
"""democut.py - cut, frame, caption and deliver a product demo from the user's real screen recording.
Python 3.8+, stdlib only, local ffmpeg/ffprobe only: no network, no key, no paid call. Prints ONE
compact JSON object on stdout. Exit: 0 ok | 1 failed | 2 usage.

The interface is never regenerated. One `cut.json` names the recordings, the ordered scenes (in/out,
speed, zoom, device frame, voice, overlays) and the variants (target, size, fps, fit); every command
reads or writes that file. State lives in the project cwd:
.genmedia/projects/<slug>/demo-video/ (cut.json, build/), deliverables in genmedia-output/<slug>/demo-video/.

  tools
      Which ffmpeg exists and what it can do here: filters (zoompan, drawtext, subtitles, sidechaincompress,
      scdet, freezedetect, ebur128, palettegen), encoders (libx264, libvpx-vp9, aac, gif), and a `can` block
      (cut, zoom, frame, burn_captions, gif, webm, loudness, analyze). No ffmpeg -> kind "ffmpeg_missing"
      with the fal utility route in the hint.
  specs [--target <id>]... [--store app-store|play|product-hunt|web]
      Rows of video-surfaces.json: pixel size, accepted sizes, duration range, codec profile, byte caps,
      source URL, `verified_on`, `unverified`. `official: false` marks this project's own defaults.
      A null is a number nobody read from the official page: never fill it from memory.
  init --slug <name> [--name "<Product>"] [--target <id>]... [--locale en]...
      Folder tree and a cut.json skeleton with one variant per target. Never overwrites (created: false).
  source add --slug <s> --id <id> --file <path> [--os ios|android|web|desktop] [--replace]
      Probe a recording and register it: size, fps, duration, audio, codec, bytes, sha256, detected
      letterboxing, and `suggest`, the targets whose aspect it fits. The file is referenced where it
      lies (recordings are large) - moving it later is `source_changed`.
  analyze --slug <s> --source <id> [--from S] [--to S] [--scene-threshold 10] [--freeze-seconds 1.5]
      Edit without watching: scene changes (scdet), frozen stretches (freezedetect), silence, black
      frames, loudness of the recording's own audio and a crop suggestion. Returns `dead_spans` (frozen
      or black) and `keep_spans` (what is left) as candidate in/out pairs.
  sheet --slug <s> --source <id> [--from S] [--to S] [--count 12] [--cols 4] [--width 1600] [--grid] [--out <png>]
      Contact sheet to LOOK at, reading order left to right, top to bottom, plus `tiles`: the source
      time of every tile. --grid draws tenth lines so a zoom region can be read off as fractions.
  grab --slug <s> --source <id> --at S [--grid] [--out <png>]
      One full-size frame as PNG: read the interface, pick a zoom region, choose a poster frame.
  time --slug <s> [--variant <id>]
      The gate before anything is rendered: validates every scene against its source, measures each
      voice file, lays out the timeline and checks it against the target's duration range, sizes and
      frame rates. Errors (exit 1) include scene_shorter_than_voice, and duration_out_of_range,
      wrong_size and fps_not_allowed on an official target. Warnings carry a placement's pacing and
      sound rules (quick_cut, fast_motion, narration_muted, audio_never_heard).
  build --slug <s> [--variant <id>] [--scene <id>]... [--force]
      Render. Per scene one cached intermediate (hash of that scene's inputs), then the concat or
      xfade pass, then overlays and audio in one pass, then the poster frame. Unchanged scenes are
      reused; --scene re-renders only those; --force ignores the cache. Writes manifest.json.
  captions --slug <s> [--variant <id>] [--formats srt,vtt] [--max-chars 42] [--max-lines 2] [--burn]
      Cue files from the timeline and the scenes' `say` lines. --burn needs libass (`can.burn_captions`);
      without it the answer names the paid route instead of pretending.
  gif --slug <s> --variant <id> [--budget-mb 3] [--seconds 6] [--start S] [--width N] [--fps N] [--webm]
      Loop export with a MEASURED byte budget: the ladder is rendered and weighed, never estimated.
      Also writes the first frame as PNG, because a GIF thumbnail is judged by it.
  validate --slug <s> [--variant <id>]
      Re-measure what was delivered: exact size, fps, duration inside the platform range, codec and
      profile, byte cap, audio configuration, integrated loudness and true peak, poster frame present,
      and on a looping target the seam (SSIM of the last frame against the first).

Rules the script enforces:
  - Paths are relative to the project cwd or absolute; a parent component is refused (path_escape).
  - A registered recording is hashed; if the file changed, every command that reads it fails with
    source_changed rather than cutting the wrong footage.
  - A zoom region is given in FRACTIONS of the source frame; the script adjusts it to the destination
    aspect (never a stretch) and reports the adjustment.
  - Device frames come from `launch-graphics layers` (*.layers.json + the alpha PNG). The geometry is
    read, never re-derived.
  - Speed is 0.25x to 4x; audio follows through chained atempo.
  - Every duration is computed from measured files, never from a guess about speaking rate.

Env: GM_FFMPEG_BIN, GM_FFPROBE_BIN override the binaries (used by the tests).
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
import time as time_mod

VERSION = "0.1.0"
SCHEMA = 1
HERE = os.path.dirname(os.path.abspath(__file__))
SURFACES = os.path.join(HERE, "video-surfaces.json")
STATE = os.path.join(".genmedia", "projects")
OUTPUT = "genmedia-output"
FF_TIMEOUT = 1800
MAX_SPEED, MIN_SPEED = 4.0, 0.25
MIN_REGION = 0.12                      # a zoom tighter than this asks more of the pixels than they have
ZOOM_UPSCALE = 2                       # pre-upscale before zoompan: halves its integer-step jitter
LOOP_SEAM_SSIM = 0.95                  # measured 2026-10-07: a cut to another screen 0.52-0.85, one button 0.99
FALLBACK_HINT = ("no local ffmpeg/ffprobe: the fal ffmpeg-api utilities in references/routing-utility.md "
                 "do trim, concat, mux and loudnorm for cents, or the user installs ffmpeg")


class Fail(Exception):
    def __init__(self, kind, message, hint=None, code=1, **extra):
        Exception.__init__(self, message)
        self.kind, self.message, self.hint, self.code, self.extra = kind, message, hint, code, extra


def usage(message, **extra):
    return Fail("usage", message, code=2, **extra)


def emit(obj, code=0):
    sys.stdout.write(json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n")
    return code


def now():
    return time_mod.strftime("%Y-%m-%dT%H:%M:%SZ", time_mod.gmtime())


# --------------------------------------------------------------------------
# tools
# --------------------------------------------------------------------------

def find_bin(env_name, default, required=True):
    override = os.environ.get(env_name)
    if override:
        if os.path.isfile(override) and os.access(override, os.X_OK):
            return override
        raise Fail("ffmpeg_missing", "%s points to %r, which is not an executable file" % (env_name, override), FALLBACK_HINT)
    found = shutil.which(default)
    if not found and required:
        raise Fail("ffmpeg_missing", "%s was not found on PATH" % default, FALLBACK_HINT)
    return found


def ffmpeg_bin():
    return find_bin("GM_FFMPEG_BIN", "ffmpeg")


def ffprobe_bin():
    return find_bin("GM_FFPROBE_BIN", "ffprobe")


def run(argv, timeout=FF_TIMEOUT):
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise Fail("timeout", "%s did not finish within %d s" % (os.path.basename(argv[0]), timeout))
    except OSError as exc:
        raise Fail("ffmpeg_missing", "cannot start %s: %s" % (argv[0], exc), FALLBACK_HINT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


def run_raw(argv, timeout=FF_TIMEOUT):
    """Same as run(), but stdout stays bytes: pixel data must not go through a text decoder."""
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise Fail("timeout", "%s did not finish within %d s" % (os.path.basename(argv[0]), timeout))
    except OSError as exc:
        raise Fail("ffmpeg_missing", "cannot start %s: %s" % (argv[0], exc), FALLBACK_HINT)
    return proc.returncode, proc.stdout, proc.stderr.decode("utf-8", "replace")


def tail(text, lines=4):
    return " | ".join([ln.strip() for ln in text.strip().splitlines() if ln.strip()][-lines:])[:500]


def ff(args, what, timeout=FF_TIMEOUT):
    code, out, err = run([ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error"] + args, timeout)
    if code != 0:
        raise Fail("tool_failed", "ffmpeg could not %s: %s" % (what, tail(err)))
    return err


def ff_report(args, timeout=FF_TIMEOUT):
    """Run ffmpeg keeping stderr: the detector filters print their findings there."""
    code, out, err = run([ffmpeg_bin(), "-hide_banner", "-nostats"] + args, timeout)
    return code, err


_CAPS = {}


def caps():
    """capabilities(), computed once per process."""
    if not _CAPS:
        _CAPS.update(capabilities())
    return _CAPS


def capabilities():
    binary = find_bin("GM_FFMPEG_BIN", "ffmpeg", required=False)
    probe = find_bin("GM_FFPROBE_BIN", "ffprobe", required=False)
    info = {"ffmpeg": {"found": bool(binary), "path": binary, "version": None},
            "ffprobe": {"found": bool(probe), "path": probe},
            "filters": {}, "encoders": {}}
    wanted_filters = ["zoompan", "crop", "overlay", "concat", "xfade", "drawtext", "subtitles",
                      "sidechaincompress", "amix", "loudnorm", "ebur128", "scdet", "freezedetect",
                      "silencedetect", "blackdetect", "cropdetect", "palettegen", "paletteuse", "atempo", "tpad"]
    wanted_encoders = ["libx264", "libvpx-vp9", "aac", "gif", "png"]
    if binary:
        code, out, err = run([binary, "-version"], 60)
        first = (out or err).splitlines()
        if first:
            match = re.search(r"ffmpeg version (\S+)", first[0])
            info["ffmpeg"]["version"] = match.group(1) if match else first[0][:40]
        code, filters, err = run([binary, "-hide_banner", "-filters"], 60)
        for name in wanted_filters:
            info["filters"][name] = re.search(r"\s%s\s" % re.escape(name), filters) is not None
        code, encoders, err = run([binary, "-hide_banner", "-encoders"], 60)
        for name in wanted_encoders:
            info["encoders"][name] = re.search(r"\s%s\s" % re.escape(name), encoders) is not None
    else:
        for name in wanted_filters:
            info["filters"][name] = False
        for name in wanted_encoders:
            info["encoders"][name] = False
    f, e = info["filters"], info["encoders"]
    info["can"] = {
        "cut": bool(binary) and e["libx264"],
        "zoom": f["zoompan"] and f["crop"],
        "frame": f["overlay"],
        "burn_captions": f["subtitles"],
        "gif": f["palettegen"] and f["paletteuse"] and e["gif"],
        "webm": e["libvpx-vp9"],
        "loudness": f["loudnorm"] and f["ebur128"],
        "duck": f["sidechaincompress"],
        "analyze": f["scdet"] and f["freezedetect"] and f["silencedetect"],
    }
    return info


def cmd_tools(args):
    info = capabilities()
    if not info["ffmpeg"]["found"] or not info["ffprobe"]["found"]:
        raise Fail("ffmpeg_missing", "local ffmpeg and ffprobe are needed for every cut", FALLBACK_HINT,
                   **{"can": info["can"]})
    hints = []
    if not info["can"]["burn_captions"]:
        hints.append("no libass: captions ship as a sidecar SRT/VTT, or through the paid subtitle route")
    if not info["can"]["duck"]:
        hints.append("no sidechaincompress: music sits at a fixed level under the narration")
    if not info["can"]["webm"]:
        hints.append("no libvpx-vp9: loops ship as MP4 and GIF only")
    out = {"ok": True, "script": VERSION}
    out.update(info)
    out["hint"] = "; ".join(hints) or "every local edit this skill needs is available"
    return out, 0


# --------------------------------------------------------------------------
# paths, state, media
# --------------------------------------------------------------------------

def need_slug(value):
    if not value or not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$", value):
        raise usage("--slug must be a short ASCII name (letters, digits, dot, dash, underscore)")
    return value


def project_dir(slug):
    return os.path.join(STATE, slug, "demo-video")


def output_dir(slug):
    return os.path.join(OUTPUT, slug, "demo-video")


def cut_path(slug):
    return os.path.join(project_dir(slug), "cut.json")


def safe_path(path, what="path"):
    if not path:
        raise usage("%s is empty" % what)
    if path.startswith(("http://", "https://")):
        raise usage("%s must be a local file; download it first (gm.py downloads results for you)" % what)
    parts = os.path.normpath(path).split(os.sep)
    if ".." in parts:
        raise Fail("path_escape", "%s %r leaves the project" % (what, path))
    return path


def read_json(path, what):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise Fail("not_found", "no %s at %s" % (what, path))
    except ValueError as exc:
        raise Fail("cut_invalid", "%s at %s is not valid JSON: %s" % (what, path, exc))


def write_json_atomic(path, doc):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(doc, handle, ensure_ascii=False, indent=2, sort_keys=False)
        handle.write("\n")
    os.replace(tmp, path)


def sha256_file(path, limit=None):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        read = 0
        while True:
            block = handle.read(1 << 20)
            if not block:
                break
            digest.update(block)
            read += len(block)
            if limit and read >= limit:
                break
    return digest.hexdigest()


def probe_media(path):
    if not os.path.isfile(path):
        raise Fail("not_found", "no such file: %s" % path)
    code, out, err = run([ffprobe_bin(), "-v", "error", "-print_format", "json",
                          "-show_format", "-show_streams", path], 300)
    if code != 0:
        raise Fail("tool_failed", "ffprobe could not read %s: %s" % (path, tail(err)))
    doc = json.loads(out or "{}")
    video = next((s for s in doc.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in doc.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = doc.get("format", {})
    fps = None
    if video and video.get("r_frame_rate", "0/0") != "0/0":
        num, den = (video["r_frame_rate"].split("/") + ["1"])[:2]
        fps = round(float(num) / float(den), 3) if float(den) else None
    duration = fmt.get("duration") or (video or {}).get("duration") or (audio or {}).get("duration")
    return {
        "path": path,
        "bytes": int(fmt.get("size") or os.path.getsize(path)),
        "duration_s": round(float(duration), 3) if duration else None,
        "width": video.get("width") if video else None,
        "height": video.get("height") if video else None,
        "fps": fps,
        "video_codec": video.get("codec_name") if video else None,
        "profile": (video.get("profile") or "").lower() or None if video else None,
        "pix_fmt": video.get("pix_fmt") if video else None,
        "has_audio": audio is not None,
        "audio_codec": audio.get("codec_name") if audio else None,
        "audio_channels": int(audio.get("channels") or 0) if audio else 0,
        "audio_rate": int(audio.get("sample_rate") or 0) if audio else 0,
    }


def surfaces():
    return read_json(SURFACES, "video-surfaces.json")


def target_spec(target_id):
    rows = surfaces()["targets"]
    if target_id not in rows:
        raise usage("unknown target %r; `specs` lists them (%s)" % (target_id, ", ".join(sorted(rows))))
    return rows[target_id]


def size_accepted(spec, width, height):
    """A listed size, or one inside the row's size_range at its exact ratio with even sides."""
    if not width or not height:
        return False
    if [width, height] in (spec.get("accepted_sizes") or [[spec["width"], spec["height"]]]):
        return True
    span = spec.get("size_range")
    if not span:
        return False
    ratio_w, ratio_h = span["ratio"]
    return (span["min"][0] <= width <= span["max"][0] and span["min"][1] <= height <= span["max"][1]
            and width * ratio_h == height * ratio_w and width % 2 == 0 and height % 2 == 0)


def sizes_text(spec):
    text = ", ".join("%dx%d" % tuple(s) for s in (spec.get("accepted_sizes") or [[spec["width"], spec["height"]]]))
    span = spec.get("size_range")
    if span:
        text += ", or any exact %d:%d from %dx%d to %dx%d with even sides" % (
            span["ratio"][0], span["ratio"][1], span["min"][0], span["min"][1], span["max"][0], span["max"][1])
    return text


def fps_problem(spec, fps):
    """The frame-rate rule a rate breaks, or None."""
    allowed = spec.get("fps_allowed")
    if allowed and not any(abs(fps - rate) <= 0.01 for rate in allowed):
        return {"kind": "fps_not_allowed", "message": "%.2f fps: this target takes exactly %s fps"
                % (fps, " or ".join("%d" % rate for rate in allowed))}
    if spec.get("fps_max") and fps > spec["fps_max"] + 0.01:
        return {"kind": "fps_too_high", "message": "%.2f fps is above the %s fps this target allows" % (fps, spec["fps_max"])}
    return None


def require_cut(slug):
    doc = read_json(cut_path(slug), "cut.json")
    if doc.get("schema") != SCHEMA:
        raise Fail("cut_invalid", "cut.json has schema %r, this script writes %d" % (doc.get("schema"), SCHEMA))
    return doc


def save_cut(slug, doc):
    doc["updated"] = now()
    write_json_atomic(cut_path(slug), doc)


def even(value):
    value = int(round(value))
    return value - (value % 2)


def fmt_seconds(value):
    return round(float(value) + 0.0, 3)


# --------------------------------------------------------------------------
# specs / init / source
# --------------------------------------------------------------------------

def cmd_specs(args):
    doc = surfaces()
    rows = doc["targets"]
    chosen = dict(rows)
    if args.store:
        chosen = {k: v for k, v in chosen.items() if v.get("store") == args.store}
    if args.target:
        args.target = [t.strip() for value in args.target for t in value.split(",") if t.strip()]
        missing = [t for t in args.target if t not in rows]
        if missing:
            raise usage("unknown target(s): %s" % ", ".join(missing))
        chosen = {k: rows[k] for k in args.target}
    return {"ok": True, "verified_on": doc["verified_on"], "about": doc["about"],
            "unverified": doc["unverified"], "count": len(chosen), "targets": chosen}, 0


def default_variant(target_id, index):
    spec = target_spec(target_id)
    return {"id": target_id, "target": target_id, "width": spec["width"], "height": spec["height"],
            "fps": spec.get("fps") or 30, "fit": "pad", "scenes": ["*"],
            "audio": bool(spec.get("audio_channels", 2)) and not spec.get("autoplay_muted"),
            "background": "#0E1116",
            "formats": [spec["formats"][0] if spec.get("formats") else "mp4"], "poster_at": 0.0}


def cmd_init(args):
    slug = need_slug(args.slug)
    path = cut_path(slug)
    if os.path.isfile(path):
        doc = require_cut(slug)
        return {"ok": True, "created": False, "cut": path, "slug": slug,
                "sources": sorted(doc.get("sources", {})), "scenes": [s["id"] for s in doc.get("scenes", [])],
                "variants": [v["id"] for v in doc.get("variants", [])],
                "hint": "a cut already exists for this slug: continue from it, never start a second one"}, 0
    targets = [t.strip() for value in (args.target or ["web-16x9"]) for t in value.split(",") if t.strip()]
    for target in targets:
        target_spec(target)
    doc = {
        "schema": SCHEMA, "script": VERSION, "slug": slug, "name": args.name or slug,
        "created": now(), "updated": now(), "locales": args.locale or ["en"],
        "sources": {}, "scenes": [],
        "audio": {"keep_source": False, "source_gain_db": -8.0, "music": None, "duck_db": -12.0,
                  "lufs": -16.0, "true_peak": -1.5, "sample_rate": 48000},
        "variants": [default_variant(t, i) for i, t in enumerate(targets)],
    }
    os.makedirs(os.path.join(project_dir(slug), "build"), exist_ok=True)
    os.makedirs(output_dir(slug), exist_ok=True)
    save_cut(slug, doc)
    return {"ok": True, "created": True, "cut": path, "slug": slug, "output": output_dir(slug),
            "variants": [v["id"] for v in doc["variants"]],
            "next": "register the recordings with `source add`, then `analyze` them"}, 0


def detect_letterbox(path, duration):
    """cropdetect over a few seconds: a recording that already carries black bars."""
    start = max(0.0, min(2.0, (duration or 4.0) / 4.0))
    code, err = ff_report(["-ss", "%.2f" % start, "-t", "3", "-i", path, "-vf", "cropdetect=limit=24:round=2:reset=0",
                           "-an", "-f", "null", "-"], 300)
    crops = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", err)
    if not crops:
        return None
    w, h, x, y = [int(v) for v in crops[-1]]
    return {"w": w, "h": h, "x": x, "y": y}


def cmd_source_add(args):
    slug = need_slug(args.slug)
    doc = require_cut(slug)
    if not re.match(r"^[a-z0-9][a-z0-9_-]{0,31}$", args.id or ""):
        raise usage("--id must be lowercase letters, digits, dash or underscore")
    if args.id in doc["sources"] and not args.replace:
        raise usage("source %r is already registered; pass --replace to point it at another file" % args.id)
    path = safe_path(args.file, "--file")
    info = probe_media(path)
    if not info["width"] or not info["duration_s"]:
        raise Fail("not_a_video", "%s has no video stream this ffprobe can read" % path,
                   hint="a screen recording is expected; a still image belongs in a scene's `still` field")
    crop = detect_letterbox(path, info["duration_s"])
    letterbox = None
    if crop and (crop["w"] < info["width"] - 4 or crop["h"] < info["height"] - 4):
        letterbox = crop
    aspect = info["width"] / float(info["height"])
    suggest = []
    for tid, spec in surfaces()["targets"].items():
        for size in spec.get("accepted_sizes") or [[spec["width"], spec["height"]]]:
            if abs(size[0] / float(size[1]) - aspect) <= 0.03:
                suggest.append(tid)
                break
    record = {"file": path, "sha256": sha256_file(path, limit=64 << 20), "bytes": info["bytes"],
              "width": info["width"], "height": info["height"], "fps": info["fps"],
              "duration_s": info["duration_s"], "has_audio": info["has_audio"],
              "video_codec": info["video_codec"], "audio_codec": info["audio_codec"],
              "os": args.os, "letterbox": letterbox, "added": now()}
    doc["sources"][args.id] = record
    save_cut(slug, doc)
    answer = {"ok": True, "id": args.id, "source": record, "aspect": round(aspect, 4), "suggest": suggest}
    notes = []
    if letterbox:
        notes.append("this recording already carries bars (content %dx%d at %d,%d): crop it in the scene's "
                     "zoom region or the delivered file will have bars inside bars"
                     % (letterbox["w"], letterbox["h"], letterbox["x"], letterbox["y"]))
    if info["fps"] and info["fps"] > 60.5:
        notes.append("%.0f fps source: every target here caps at 60 and App Store previews at 30" % info["fps"])
    if not info["has_audio"]:
        notes.append("no audio track: narration or music has to come from somewhere else")
    answer["notes"] = notes
    return answer, 0


def source_file(doc, source_id, check=True):
    if source_id not in doc.get("sources", {}):
        raise usage("cut.json has no source %r (it has %s)" % (source_id, ", ".join(sorted(doc.get("sources", {}))) or "none"))
    record = doc["sources"][source_id]
    path = record["file"]
    if check:
        if not os.path.isfile(path):
            raise Fail("source_changed", "the recording registered as %r is not at %s any more" % (source_id, path),
                       hint="put the file back or run `source add --replace` with the new path")
        if sha256_file(path, limit=64 << 20) != record["sha256"]:
            raise Fail("source_changed", "the file at %s is not the recording that was registered as %r" % (path, source_id),
                       hint="re-register it with `source add --replace`; cutting it blind would use the wrong footage")
    return path, record


# --------------------------------------------------------------------------
# analyze / sheet / grab
# --------------------------------------------------------------------------

def spans_from(starts, ends, total):
    spans = []
    for i, start in enumerate(starts):
        end = ends[i] if i < len(ends) else total
        if end - start > 0.01:
            spans.append({"start": round(start, 2), "end": round(end, 2), "seconds": round(end - start, 2)})
    return spans


def invert_spans(spans, total, pad=0.15):
    keep, cursor = [], 0.0
    for span in sorted(spans, key=lambda s: s["start"]):
        start = max(0.0, span["start"] - pad)
        if start - cursor > 0.4:
            keep.append({"start": round(cursor, 2), "end": round(start, 2), "seconds": round(start - cursor, 2)})
        cursor = max(cursor, span["end"])
    if total - cursor > 0.4:
        keep.append({"start": round(cursor, 2), "end": round(total, 2), "seconds": round(total - cursor, 2)})
    return keep


def cmd_analyze(args):
    slug = need_slug(args.slug)
    doc = require_cut(slug)
    path, record = source_file(doc, args.source)
    start = max(0.0, args.start or 0.0)
    end = args.end if args.end else record["duration_s"]
    if end <= start:
        raise usage("--to must be greater than --from")
    window = end - start
    argv = ["-ss", "%.3f" % start, "-t", "%.3f" % window, "-i", path,
            "-vf", "scdet=threshold=%.1f,freezedetect=n=-58dB:d=%.2f,blackdetect=d=0.4:pic_th=0.98"
            % (args.scene_threshold, args.freeze_seconds), "-an", "-f", "null", "-"]
    code, err = ff_report(argv)
    if code != 0:
        raise Fail("tool_failed", "the detector pass failed: %s" % tail(err))
    scenes = sorted({round(float(t) + start, 2) for t in re.findall(r"lavfi\.scd\.time:\s*([0-9.]+)", err)})
    freeze_starts = [float(t) + start for t in re.findall(r"freeze_start:\s*([0-9.]+)", err)]
    freeze_ends = [float(t) + start for t in re.findall(r"freeze_end:\s*([0-9.]+)", err)]
    black_starts = [float(t) + start for t in re.findall(r"black_start:\s*([0-9.]+)", err)]
    black_ends = [float(t) + start for t in re.findall(r"black_end:\s*([0-9.]+)", err)]
    freezes = spans_from(freeze_starts, freeze_ends, end)
    blacks = spans_from(black_starts, black_ends, end)
    silences, loudness = [], None
    if record["has_audio"]:
        code, err2 = ff_report(["-ss", "%.3f" % start, "-t", "%.3f" % window, "-i", path,
                                "-af", "silencedetect=noise=-45dB:d=0.8,ebur128=peak=true", "-vn", "-f", "null", "-"])
        s_starts = [float(t) + start for t in re.findall(r"silence_start:\s*(-?[0-9.]+)", err2)]
        s_ends = [float(t) + start for t in re.findall(r"silence_end:\s*([0-9.]+)", err2)]
        silences = spans_from(s_starts, s_ends, end)
        summary = err2.split("Summary:")[-1]
        integrated = re.search(r"I:\s*(-?[0-9.]+) LUFS", summary)
        peak = re.search(r"Peak:\s*(-?[0-9.]+) dBFS", summary)
        loudness = {"integrated_lufs": float(integrated.group(1)) if integrated else None,
                    "true_peak_dbfs": float(peak.group(1)) if peak else None}
    dead = sorted(freezes + blacks, key=lambda s: s["start"])
    merged = []
    for span in dead:
        if merged and span["start"] - merged[-1]["end"] < 0.3:
            merged[-1]["end"] = max(merged[-1]["end"], span["end"])
            merged[-1]["seconds"] = round(merged[-1]["end"] - merged[-1]["start"], 2)
        else:
            merged.append(dict(span))
    keep = invert_spans(merged, end)
    return {"ok": True, "source": args.source, "window": [round(start, 2), round(end, 2)],
            "scene_changes": scenes, "freezes": freezes, "black": blacks, "silences": silences,
            "loudness": loudness, "dead_spans": merged, "keep_spans": keep,
            "hint": "dead_spans are frozen or black stretches (nothing is happening); keep_spans are candidate "
                    "in/out pairs. Look at a sheet before trusting any of them: a still screen can be the point "
                    "of the shot."}, 0


def grid_filter(width, height, cells=10):
    """Tenth lines so a region can be read off the picture as fractions; the middle line is brighter."""
    parts = []
    for i in range(1, cells):
        x = int(round(width * i / float(cells)))
        y = int(round(height * i / float(cells)))
        colour = "white@0.55" if i == cells // 2 else "white@0.22"
        thick = 3 if i == cells // 2 else 1
        parts.append("drawbox=x=%d:y=0:w=%d:h=%d:color=%s:t=fill" % (x, thick, height, colour))
        parts.append("drawbox=x=0:y=%d:w=%d:h=%d:color=%s:t=fill" % (y, width, thick, colour))
    return ",".join(parts)


def cmd_grab(args):
    slug = need_slug(args.slug)
    doc = require_cut(slug)
    path, record = source_file(doc, args.source)
    at = max(0.0, min(args.at, max(0.0, (record["duration_s"] or 0) - 0.05)))
    out = safe_path(args.out or os.path.join(project_dir(slug), "build", "grab-%s-%.2f.png" % (args.source, at)), "--out")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    chain = []
    if args.grid:
        chain.append(grid_filter(record["width"], record["height"]))
    argv = ["-ss", "%.3f" % at, "-i", path, "-frames:v", "1", "-update", "1"]
    if chain:
        argv += ["-vf", ",".join(chain)]
    ff(argv + [out], "grab a frame")
    return {"ok": True, "file": out, "at": round(at, 3), "size": [record["width"], record["height"]],
            "grid": bool(args.grid),
            "hint": "Read this file. A zoom region is [x, y, w, h] as fractions of the frame: with the grid, "
                    "each cell is 0.1."}, 0


def cmd_sheet(args):
    slug = need_slug(args.slug)
    doc = require_cut(slug)
    path, record = source_file(doc, args.source)
    total = record["duration_s"] or 0.0
    start = max(0.0, args.start or 0.0)
    end = min(total, args.end if args.end else total)
    if end <= start:
        raise usage("--to must be greater than --from")
    count = max(2, min(36, args.count))
    cols = max(1, min(8, args.cols))
    rows = int(math.ceil(count / float(cols)))
    step = (end - start - 0.04) / float(count - 1) if count > 1 else 0.0
    times = [round(start + step * i, 3) for i in range(count)]
    build = os.path.join(project_dir(slug), "build")
    os.makedirs(build, exist_ok=True)
    tile_w = even(max(160, args.width / float(cols)))
    tile_h = even(tile_w * record["height"] / float(record["width"]))
    tiles = []
    for i, at in enumerate(times):
        tile = os.path.join(build, "sheet-%s-%02d.png" % (args.source, i))
        chain = "scale=%d:%d:flags=lanczos" % (tile_w, tile_h)
        if args.grid:
            chain += "," + grid_filter(tile_w, tile_h)
        chain += ",drawbox=x=0:y=0:w=%d:h=%d:color=white@0.35:t=2" % (tile_w, tile_h)
        ff(["-ss", "%.3f" % at, "-i", path, "-frames:v", "1", "-vf", chain, "-update", "1", tile],
           "extract the frame at %.2f s" % at)
        tiles.append({"index": i, "row": i // cols, "col": i % cols, "time_s": at, "file": tile})
    out = safe_path(args.out or os.path.join(build, "sheet-%s.png" % args.source), "--out")
    inputs = []
    for tile in tiles:
        inputs += ["-i", tile["file"]]
    layout = "|".join("%d_%d" % ((i % cols) * tile_w, (i // cols) * tile_h) for i in range(len(tiles)))
    if len(tiles) > 1:
        chain = "%sxstack=inputs=%d:layout=%s:fill=black" % (
            "".join("[%d:v]" % i for i in range(len(tiles))), len(tiles), layout)
        ff(inputs + ["-filter_complex", chain, "-frames:v", "1", "-update", "1", out], "tile the contact sheet")
    else:
        shutil.copyfile(tiles[0]["file"], out)
    for tile in tiles:
        os.remove(tile["file"])
        tile.pop("file")
    return {"ok": True, "sheet": out, "source": args.source, "count": len(tiles), "cols": cols, "rows": rows,
            "tile_size": [tile_w, tile_h], "source_size": [record["width"], record["height"]],
            "window": [round(start, 2), round(end, 2)], "tiles": tiles, "grid": bool(args.grid),
            "hint": "Read the sheet. Reading order is left to right, top to bottom; `tiles` gives each tile's "
                    "source time. Pick in/out points and zoom regions from what you see, not from the clock."}, 0


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

def fit_box(src_w, src_h, dst_w, dst_h, fit):
    """Scale factor and offsets that map source pixels into the destination box."""
    if fit == "crop":
        scale = max(dst_w / float(src_w), dst_h / float(src_h))
    else:
        scale = min(dst_w / float(src_w), dst_h / float(src_h))
    new_w, new_h = src_w * scale, src_h * scale
    return scale, (dst_w - new_w) / 2.0, (dst_h - new_h) / 2.0


def adjust_region(region, src_w, src_h, dst_w, dst_h):
    """A region in fractions -> a rectangle in source pixels with the destination aspect, inside the frame."""
    x, y, w, h = [float(v) for v in region]
    for value, name in ((x, "x"), (y, "y"), (w, "w"), (h, "h")):
        if value < 0 or value > 1:
            raise usage("zoom region %s must be a fraction between 0 and 1 (got %r)" % (name, value))
    if w < MIN_REGION or h < MIN_REGION:
        raise usage("zoom region is tighter than %.2f of the frame: the pixels are not there" % MIN_REGION)
    px, py, pw, ph = x * src_w, y * src_h, w * src_w, h * src_h
    want = dst_w / float(dst_h)
    adjusted = False
    if pw / ph > want:
        new_h = pw / want
        py -= (new_h - ph) / 2.0
        ph, adjusted = new_h, True
    elif pw / ph < want:
        new_w = ph * want
        px -= (new_w - pw) / 2.0
        pw, adjusted = new_w, True
    if pw > src_w or ph > src_h:
        shrink = min(src_w / pw, src_h / ph)
        pw, ph = pw * shrink, ph * shrink
        adjusted = True
    px = max(0.0, min(px, src_w - pw))
    py = max(0.0, min(py, src_h - ph))
    return {"x": px, "y": py, "w": pw, "h": ph, "adjusted": adjusted,
            "fraction": [round(px / src_w, 4), round(py / src_h, 4), round(pw / src_w, 4), round(ph / src_h, 4)],
            "zoom": round(src_w / pw, 3)}


def atempo_chain(rate):
    """atempo takes 0.5-2.0; chain it for anything outside that."""
    parts, remaining = [], float(rate)
    while remaining > 2.0:
        parts.append(2.0)
        remaining /= 2.0
    while remaining < 0.5:
        parts.append(0.5)
        remaining /= 0.5
    parts.append(remaining)
    return ",".join("atempo=%.6f" % p for p in parts)


def alpha_max(path):
    """The largest alpha value in an image, or None when it has no alpha channel.
    A PNG whose alpha is 0 everywhere composites to nothing: that silent failure is worth catching."""
    info = probe_media(path)
    if not (info["pix_fmt"] or "").endswith(("a", "argb", "rgba", "abgr", "bgra")) and "a" not in (info["pix_fmt"] or ""):
        return None
    code, out, err = run_raw([ffmpeg_bin(), "-v", "error", "-i", path, "-vf", "alphaextract", "-frames:v", "1",
                              "-f", "rawvideo", "-pix_fmt", "gray", "-"], 120)
    if code != 0 or not out:
        return None
    return max(bytearray(out))


def aformat(sample_rate):
    """Every audio branch is forced to one format so concat and amix never see a mismatch."""
    return "aformat=sample_fmts=fltp:sample_rates=%d:channel_layouts=stereo" % sample_rate


def load_layers(path):
    doc = read_json(path, "layers file")
    for key in ("canvas", "screen", "fg"):
        if key not in doc:
            raise Fail("frame_invalid", "%s is not a launch-graphics layers file (no %r)" % (path, key),
                       hint="run `launchkit.py layers` in launch-graphics and pass the .layers.json it writes")
    fg = os.path.join(os.path.dirname(os.path.abspath(path)), os.path.basename(doc["fg"]))
    if not os.path.isfile(fg):
        raise Fail("not_found", "the alpha layer %s named by %s is missing" % (doc["fg"], path))
    doc["_fg"] = fg
    return doc


# --------------------------------------------------------------------------
# timeline
# --------------------------------------------------------------------------

def variant_by_id(doc, variant_id):
    found = [v for v in doc.get("variants", []) if v["id"] == variant_id]
    if not found:
        raise usage("cut.json has no variant %r (it has %s)"
                    % (variant_id, ", ".join(v["id"] for v in doc.get("variants", [])) or "none"))
    return found[0]


def variant_scenes(doc, variant):
    wanted = variant.get("scenes") or ["*"]
    scenes = doc.get("scenes", [])
    if wanted == ["*"]:
        return list(scenes)
    index = {s["id"]: s for s in scenes}
    missing = [w for w in wanted if w not in index]
    if missing:
        raise usage("variant %r lists scenes that are not in the cut: %s" % (variant["id"], ", ".join(missing)))
    return [index[w] for w in wanted]


def variant_size(variant):
    spec = target_spec(variant["target"])
    width = int(variant.get("width") or spec["width"])
    height = int(variant.get("height") or spec["height"])
    fps = int(variant.get("fps") or spec.get("fps") or 30)
    return width, height, fps


def scene_seconds(scene, fps=None):
    if scene.get("still"):
        base = float(scene["still"].get("seconds") or scene.get("seconds") or 3.0)
    else:
        base = (float(scene["out"]) - float(scene["in"])) / float(scene.get("speed") or 1.0)
    return base + float(scene.get("hold_last") or 0.0)


def measure_voice(scene, cache):
    voice = scene.get("voice")
    if not voice:
        return None
    path = safe_path(voice["file"], "voice file")
    if path not in cache:
        info = probe_media(path)
        if not info["has_audio"]:
            raise Fail("not_found", "%s has no audio stream" % path)
        cache[path] = info["duration_s"] or 0.0
    return {"file": path, "seconds": cache[path], "lead": float(voice.get("lead") or 0.0),
            "tail": float(voice.get("tail") or 0.0), "gain_db": float(voice.get("gain_db") or 0.0)}


def build_timeline(doc, variant, strict=True):
    """Scene-by-scene layout with every check that must pass before a pixel is rendered."""
    width, height, fps = variant_size(variant)
    spec = target_spec(variant["target"])
    scenes = variant_scenes(doc, variant)
    errors, warnings, rows = [], [], []
    voice_cache, cursor, overlap_total = {}, 0.0, 0.0
    official = bool(spec.get("official"))
    if not scenes:
        errors.append({"kind": "no_scenes", "message": "variant %r has no scenes" % variant["id"]})
    if not size_accepted(spec, width, height):
        (errors if official else warnings).append({"kind": "wrong_size", "message": "%dx%d is not a size %s takes: %s"
                                                   % (width, height, variant["target"], sizes_text(spec))})
    problem = fps_problem(spec, fps)
    if problem:
        (errors if official or problem["kind"] == "fps_too_high" else warnings).append(problem)
    for index, scene in enumerate(scenes):
        row = {"id": scene["id"], "index": index}
        seconds = 0.0
        if scene.get("still"):
            still = safe_path(scene["still"]["file"], "still file")
            if not os.path.isfile(still):
                errors.append({"kind": "not_found", "scene": scene["id"], "message": "still %s is missing" % still})
            seconds = scene_seconds(scene)
            row["kind"] = "still"
        else:
            try:
                path, record = source_file(doc, scene.get("source"), check=strict)
            except Fail as exc:
                errors.append({"kind": exc.kind, "scene": scene["id"], "message": exc.message})
                rows.append(row)
                continue
            except SystemExit:
                raise
            start, stop = float(scene["in"]), float(scene["out"])
            speed = float(scene.get("speed") or 1.0)
            if stop <= start:
                errors.append({"kind": "bad_span", "scene": scene["id"],
                               "message": "out (%.2f) must be after in (%.2f)" % (stop, start)})
            if record.get("duration_s") and stop > record["duration_s"] + 0.05:
                errors.append({"kind": "bad_span", "scene": scene["id"],
                               "message": "out %.2f s is past the end of %s (%.2f s)"
                                          % (stop, scene["source"], record["duration_s"])})
            if speed < MIN_SPEED or speed > MAX_SPEED:
                errors.append({"kind": "bad_speed", "scene": scene["id"],
                               "message": "speed %.2f is outside %.2f-%.1f" % (speed, MIN_SPEED, MAX_SPEED)})
            seconds = scene_seconds(scene)
            row["kind"] = "footage"
            row["source"] = scene["source"]
            row["span"] = [round(start, 3), round(stop, 3)]
            row["speed"] = speed
            if spec.get("max_scene_speed") and speed > spec["max_scene_speed"] + 0.001:
                warnings.append({"kind": "fast_motion", "scene": scene["id"],
                                 "message": "%.2fx reads as fast-moving footage, which %s asks to avoid; keep it at "
                                            "%sx or below, or cut the wait instead" % (speed, variant["target"], spec["max_scene_speed"])})
            dest_w, dest_h = width, height
            if scene.get("frame"):
                try:
                    layers = load_layers(safe_path(scene["frame"]["layers"], "layers file"))
                    dest_w, dest_h = layers["screen"]["w"], layers["screen"]["h"]
                    row["frame"] = {"canvas": layers["canvas"], "screen": [dest_w, dest_h]}
                    source_aspect = record["width"] / float(record["height"])
                    hole_aspect = dest_w / float(dest_h)
                    drift = abs(source_aspect - hole_aspect) / hole_aspect
                    if drift > 0.3:
                        errors.append({"kind": "frame_aspect_mismatch", "scene": scene["id"],
                                       "message": "the recording is %.3f and the frame's screen %.3f (%.0f%% apart): "
                                                  "a phone recording needs a phone frame" % (source_aspect, hole_aspect, drift * 100)})
                    elif drift > 0.08:
                        warnings.append({"kind": "frame_aspect_mismatch", "scene": scene["id"],
                                         "message": "the recording and the frame's screen are %.0f%% apart; the "
                                                    "difference is padded with the background" % (drift * 100)})
                except Fail as exc:
                    errors.append({"kind": exc.kind, "scene": scene["id"], "message": exc.message})
            zoom = scene.get("zoom") or {}
            kind = zoom.get("kind") or "none"
            if kind not in ("none", "hold", "push", "pull"):
                errors.append({"kind": "bad_zoom", "scene": scene["id"], "message": "zoom kind %r is not one of none, hold, push, pull" % kind})
            elif kind != "none":
                try:
                    region = adjust_region(zoom["region"], record["width"], record["height"], dest_w, dest_h)
                    row["zoom"] = {"kind": kind, "region": region["fraction"], "zoom": region["zoom"],
                                   "adjusted": region["adjusted"]}
                    if region["adjusted"]:
                        warnings.append({"kind": "region_adjusted", "scene": scene["id"],
                                         "message": "the region was reshaped to the destination aspect: %s" % region["fraction"]})
                    if region["zoom"] > 4.0:
                        warnings.append({"kind": "zoom_deep", "scene": scene["id"],
                                         "message": "%.1fx zoom: soft pixels unless the recording is bigger than the target" % region["zoom"]})
                except KeyError:
                    errors.append({"kind": "bad_zoom", "scene": scene["id"], "message": "a %s zoom needs a region" % kind})
                except Fail as exc:
                    errors.append({"kind": exc.kind, "scene": scene["id"], "message": exc.message})
        if spec.get("min_scene_seconds") and 0 < seconds < spec["min_scene_seconds"] - 0.01:
            warnings.append({"kind": "quick_cut", "scene": scene["id"],
                             "message": "a %.2f s scene is a quick cut, which %s asks to avoid; hold each scene at "
                                        "least %s s" % (seconds, variant["target"], spec["min_scene_seconds"])})
        for overlay in scene.get("overlays") or []:
            path = safe_path(overlay["file"], "overlay file")
            if not os.path.isfile(path):
                errors.append({"kind": "not_found", "scene": scene["id"], "message": "overlay %s is missing" % path})
            elif strict:
                try:
                    peak = alpha_max(path)
                except Fail:
                    peak = None
                if peak == 0:
                    errors.append({"kind": "overlay_invisible", "scene": scene["id"],
                                   "message": "%s is transparent everywhere: it would composite to nothing" % path})
            if float(overlay.get("end") or seconds) > seconds + 0.01:
                warnings.append({"kind": "overlay_past_scene", "scene": scene["id"],
                                 "message": "an overlay ends after the scene does; it is clipped"})
        try:
            voice = measure_voice(scene, voice_cache)
        except Fail as exc:
            errors.append({"kind": exc.kind, "scene": scene["id"], "message": exc.message})
            voice = None
        if voice:
            needed = voice["seconds"] + voice["lead"] + voice["tail"]
            row["voice"] = {"seconds": round(voice["seconds"], 3), "needed": round(needed, 3)}
            if seconds + 0.05 < needed:
                errors.append({"kind": "scene_shorter_than_voice", "scene": scene["id"],
                               "message": "the scene is %.2f s and its narration needs %.2f s: lengthen the span, "
                                          "slow it down, or cut words" % (seconds, needed)})
            elif seconds > needed + 2.0:
                warnings.append({"kind": "scene_longer_than_voice", "scene": scene["id"],
                                 "message": "%.1f s of picture over %.1f s of narration" % (seconds, needed)})
        say = (scene.get("say") or "").strip()
        if say and seconds > 0:
            words = len(say.split())
            if words / seconds > 3.2:
                warnings.append({"kind": "say_too_fast", "scene": scene["id"],
                                 "message": "%d words in %.1f s is above 3.2 words per second" % (words, seconds)})
        transition = scene.get("transition") or {}
        overlap = float(transition.get("seconds") or 0.0) if transition.get("kind") == "dissolve" else 0.0
        if overlap and index == len(scenes) - 1:
            overlap = 0.0
        if overlap:
            previous = seconds
            following = scene_seconds(scenes[index + 1]) if index + 1 < len(scenes) else 0.0
            if overlap > min(previous, following) / 2.0:
                errors.append({"kind": "transition_too_long", "scene": scene["id"],
                               "message": "a %.2f s dissolve does not fit between scenes of %.2f s and %.2f s"
                                          % (overlap, previous, following)})
                overlap = 0.0
        row["seconds"] = round(seconds, 3)
        row["start"] = round(cursor, 3)
        row["end"] = round(cursor + seconds, 3)
        row["transition"] = {"kind": transition.get("kind") or "cut", "seconds": round(overlap, 3)}
        cursor = cursor + seconds - overlap
        overlap_total += overlap
        rows.append(row)
    total = round(cursor, 3)
    checks = []
    aim = spec.get("aim_seconds")
    if spec.get("autoplay_muted"):
        unmute = "the viewer may unmute it" if spec.get("can_unmute") else "nobody can unmute it"
        voiced = [scene["id"] for scene in scenes if scene.get("voice")]
        if voiced:
            warnings.append({"kind": "narration_muted",
                             "message": "%s plays muted (%s) and scene(s) %s carry narration: it has to work silent, "
                                        "so what is said goes on screen and sound stays texture"
                                        % (variant["target"], unmute, ", ".join(voiced))})
        if variant.get("audio", True) and spec.get("can_unmute") is False:
            warnings.append({"kind": "audio_never_heard",
                             "message": "%s is muted and cannot be unmuted: the audio track is never heard; "
                                        "set the variant's audio to false" % variant["target"]})
    if spec.get("min_seconds") and total < spec["min_seconds"] - 0.01:
        (errors if official else warnings).append({"kind": "duration_out_of_range",
            "message": "%s wants at least %s s; the cut is %.2f s" % (variant["target"], spec["min_seconds"], total)})
    if spec.get("max_seconds") and total > spec["max_seconds"] + 0.01:
        (errors if official else warnings).append({"kind": "duration_out_of_range",
            "message": "%s allows at most %s s; the cut is %.2f s" % (variant["target"], spec["max_seconds"], total)})
    if aim and (total < aim[0] - 0.01 or total > aim[1] + 0.01):
        warnings.append({"kind": "duration_off_aim",
                         "message": "%s reads best between %s and %s s; the cut is %.2f s" % (variant["target"], aim[0], aim[1], total)})
    if spec.get("store") == "play" and total > 30.0:
        warnings.append({"kind": "autoplay_window",
                         "message": "only the first 30 s of a Play promo video autoplays; %.1f s means the rest is a click away" % total})
    checks.append({"target": variant["target"], "size": [width, height], "fps": fps,
                   "official": official, "aim_seconds": aim, "loops": bool(spec.get("loops"))})
    return {"variant": variant["id"], "target": variant["target"], "size": [width, height], "fps": fps,
            "total_seconds": total, "dissolve_seconds": round(overlap_total, 3), "scenes": rows,
            "errors": errors, "warnings": warnings, "checks": checks}


def cmd_time(args):
    slug = need_slug(args.slug)
    doc = require_cut(slug)
    variants = [variant_by_id(doc, args.variant)] if args.variant else doc.get("variants", [])
    if not variants:
        raise usage("cut.json has no variants")
    lines, errors, warnings = [], 0, 0
    for variant in variants:
        line = build_timeline(doc, variant)
        errors += len(line["errors"])
        warnings += len(line["warnings"])
        lines.append(line)
    answer = {"ok": errors == 0, "slug": slug, "variants": lines, "errors": errors, "warnings": warnings}
    if errors:
        answer["kind"] = "check_failed"
        answer["hint"] = "fix the cut and run `time` again; nothing is rendered while an error stands"
        return answer, 1
    answer["hint"] = "the timeline holds: `build` renders it"
    return answer, 0


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def scene_hash(scene, doc, width, height, fps, fit, background):
    payload = {"scene": scene, "w": width, "h": height, "fps": fps, "fit": fit, "bg": background, "v": VERSION}
    if scene.get("source"):
        payload["src"] = doc["sources"][scene["source"]]["sha256"]
    if scene.get("frame"):
        try:
            layers = load_layers(scene["frame"]["layers"])
            payload["fg"] = layers.get("fg_sha256") or os.path.getmtime(layers["_fg"])
        except Fail:
            payload["fg"] = None
    if scene.get("still"):
        payload["still_mtime"] = os.path.getmtime(scene["still"]["file"]) if os.path.isfile(scene["still"]["file"]) else None
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:10]


def hex_to_ffmpeg(colour):
    value = (colour or "#000000").lstrip("#")
    if not re.match(r"^[0-9A-Fa-f]{6}$", value):
        raise usage("background %r is not a #RRGGBB colour" % colour)
    return "0x" + value.upper()


def scene_video_chain(scene, record, width, height, fps, fit, background, layers):
    """The filter chain for one scene, from the decoded source to the variant canvas."""
    dest_w, dest_h = (layers["screen"]["w"], layers["screen"]["h"]) if layers else (width, height)
    zoom = scene.get("zoom") or {}
    kind = zoom.get("kind") or "none"
    speed = float(scene.get("speed") or 1.0)
    steps = ["trim=start=%.3f:end=%.3f" % (float(scene["in"]), float(scene["out"])),
             "setpts=(PTS-STARTPTS)/%.6f" % speed, "fps=%d" % fps]
    seconds = scene_seconds(scene)
    if kind == "hold":
        region = adjust_region(zoom["region"], record["width"], record["height"], dest_w, dest_h)
        steps.append("crop=%d:%d:%d:%d" % (even(region["w"]), even(region["h"]), int(region["x"]), int(region["y"])))
        steps.append("scale=%d:%d:flags=lanczos" % (dest_w, dest_h))
    elif kind in ("push", "pull"):
        region = adjust_region(zoom["region"], record["width"], record["height"], dest_w, dest_h)
        up_w, up_h = even(dest_w * ZOOM_UPSCALE), even(dest_h * ZOOM_UPSCALE)
        if fit == "crop":
            steps.append("scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos" % (up_w, up_h))
            steps.append("crop=%d:%d" % (up_w, up_h))
        else:
            steps.append("scale=%d:%d:force_original_aspect_ratio=decrease:flags=lanczos" % (up_w, up_h))
            steps.append("pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=%s" % (up_w, up_h, hex_to_ffmpeg(background)))
        scale, off_x, off_y = fit_box(record["width"], record["height"], up_w, up_h, fit)
        rect = {"x": region["x"] * scale + off_x, "y": region["y"] * scale + off_y,
                "w": region["w"] * scale, "h": region["h"] * scale}
        full = {"x": 0.0, "y": 0.0, "w": float(up_w), "h": float(up_h)}
        start_rect, end_rect = (full, rect) if kind == "push" else (rect, full)
        frames = max(2, int(round(seconds * fps)))
        ease = "min(on/%d,1)" % (frames - 1)
        if (zoom.get("ease") or "in-out") == "in-out":
            ease = "(1-cos(PI*%s))/2" % ease
        z = "%.6f/(%.4f+(%.4f)*(%s))" % (up_w, start_rect["w"], end_rect["w"] - start_rect["w"], ease)
        x = "%.4f+(%.4f)*(%s)" % (start_rect["x"], end_rect["x"] - start_rect["x"], ease)
        y = "%.4f+(%.4f)*(%s)" % (start_rect["y"], end_rect["y"] - start_rect["y"], ease)
        steps.append("zoompan=z='%s':x='%s':y='%s':d=1:s=%dx%d:fps=%d" % (z, x, y, dest_w, dest_h, fps))
    else:
        if fit == "crop":
            steps.append("scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos" % (dest_w, dest_h))
            steps.append("crop=%d:%d" % (dest_w, dest_h))
        else:
            steps.append("scale=%d:%d:force_original_aspect_ratio=decrease:flags=lanczos" % (dest_w, dest_h))
            steps.append("pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=%s" % (dest_w, dest_h, hex_to_ffmpeg(background)))
    if float(scene.get("hold_last") or 0.0) > 0:
        steps.append("tpad=stop_mode=clone:stop_duration=%.3f" % float(scene["hold_last"]))
    steps.append("setsar=1")
    return ",".join(steps), dest_w, dest_h


def render_scene(scene, doc, out_path, width, height, fps, fit, background):
    """One scene to one intermediate file (video only)."""
    layers = load_layers(safe_path(scene["frame"]["layers"], "layers file")) if scene.get("frame") else None
    seconds = scene_seconds(scene)
    bg = hex_to_ffmpeg(background)
    if scene.get("still"):
        still = safe_path(scene["still"]["file"], "still file")
        chain = ("scale=%d:%d:force_original_aspect_ratio=decrease:flags=lanczos,"
                 "pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=%s,fps=%d,setsar=1" % (width, height, width, height, bg, fps))
        fade = float(scene["still"].get("fade") or 0.0)
        if fade > 0:
            chain += ",fade=t=in:st=0:d=%.3f,fade=t=out:st=%.3f:d=%.3f" % (fade, max(0.0, seconds - fade), fade)
        ff(["-loop", "1", "-framerate", "%d" % fps, "-t", "%.3f" % seconds, "-i", still,
            "-vf", chain, "-frames:v", "%d" % max(1, int(round(seconds * fps))),
            "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", out_path],
           "render the still scene %r" % scene["id"])
        return out_path
    path, record = source_file(doc, scene["source"])
    chain, dest_w, dest_h = scene_video_chain(scene, record, width, height, fps, fit, background, layers)
    if layers:
        canvas_w, canvas_h = layers["canvas"]
        graph = ("color=c=%s:s=%dx%d:r=%d[canvas];[0:v]%s[rec];"
                 "[canvas][rec]overlay=%d:%d:shortest=1[under];"
                 "[under][1:v]overlay=0:0:format=auto[framed];"
                 "[framed]scale=%d:%d:force_original_aspect_ratio=decrease:flags=lanczos,"
                 "pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=%s,setsar=1,format=yuv420p[v]"
                 % (bg, canvas_w, canvas_h, fps, chain, layers["screen"]["x"], layers["screen"]["y"],
                    width, height, width, height, bg))
        argv = ["-i", path, "-loop", "1", "-framerate", "%d" % fps, "-i", layers["_fg"],
                "-filter_complex", graph, "-map", "[v]"]
    else:
        argv = ["-i", path, "-filter_complex", "[0:v]%s,format=yuv420p[v]" % chain, "-map", "[v]"]
    ff(argv + ["-t", "%.3f" % seconds, "-an", "-c:v", "libx264", "-crf", "16", "-preset", "veryfast",
               "-pix_fmt", "yuv420p", out_path], "render scene %r" % scene["id"])
    return out_path


def join_scenes(parts, rows, out_path, width, height, fps, background):
    """Cuts join with concat; a dissolve joins with xfade, which overlaps the two scenes.

    Every branch is normalised first (fps, timebase, SAR, pixel format): xfade refuses to configure
    when two links carry different timebases, which is exactly what concat hands it otherwise.
    """
    if len(parts) == 1 and not rows[0]["transition"]["seconds"]:
        shutil.copyfile(parts[0], out_path)
        return out_path
    inputs = []
    for part in parts:
        inputs += ["-i", part]
    steps = ["[%d:v]fps=%d,settb=AVTB,setsar=1,format=yuv420p[n%d]" % (i, fps, i) for i in range(len(parts))]
    dissolves = [row["transition"]["seconds"] for row in rows[:-1]]
    if not any(dissolves):
        steps.append("".join("[n%d]" % i for i in range(len(parts))) + "concat=n=%d:v=1:a=0[v]" % len(parts))
    else:
        label, offset = "[n0]", 0.0
        for i in range(1, len(parts)):
            overlap = rows[i - 1]["transition"]["seconds"]
            offset += rows[i - 1]["seconds"] - overlap
            raw, normal = "[x%d]" % i, "[s%d]" % i
            if overlap > 0:
                steps.append("%s[n%d]xfade=transition=fade:duration=%.3f:offset=%.3f%s"
                             % (label, i, overlap, offset, raw))
            else:
                steps.append("%s[n%d]concat=n=2:v=1:a=0%s" % (label, i, raw))
            steps.append("%ssettb=AVTB%s" % (raw, normal))
            label = normal
        steps.append("%sformat=yuv420p[v]" % label)
    ff(inputs + ["-filter_complex", ";".join(steps), "-map", "[v]", "-r", "%d" % fps, "-an",
                 "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", out_path],
       "join the scenes")
    return out_path


OVERLAY_X = {"left": "%d", "center": "(W-w)/2", "right": "W-w-%d"}
OVERLAY_Y = {"top": "%d", "center": "(H-h)/2", "bottom": "H-h-%d"}


def overlay_position(overlay):
    margin = int(overlay.get("margin") or 0)
    x = overlay.get("x", "center")
    y = overlay.get("y", "bottom")
    if isinstance(x, (int, float)):
        x_expr = "%d" % int(x)
    elif x in OVERLAY_X:
        x_expr = OVERLAY_X[x] % margin if "%d" in OVERLAY_X[x] else OVERLAY_X[x]
    else:
        raise usage("overlay x must be left, center, right or a pixel number (got %r)" % x)
    if isinstance(y, (int, float)):
        y_expr = "%d" % int(y)
    elif y in OVERLAY_Y:
        y_expr = OVERLAY_Y[y] % margin if "%d" in OVERLAY_Y[y] else OVERLAY_Y[y]
    else:
        raise usage("overlay y must be top, center, bottom or a pixel number (got %r)" % y)
    return x_expr, y_expr


def audio_graph(doc, rows, scenes, total, sample_rate, inputs, first_index):
    """Source audio, per-scene narration and music -> one normalised track. Returns (graph, label) or None."""
    settings = doc.get("audio") or {}
    parts, mix_labels = [], []
    index = first_index
    keep_source = bool(settings.get("keep_source"))
    src_labels = []
    if keep_source:
        for row, scene in zip(rows, scenes):
            if scene.get("still") or scene.get("mute"):
                parts.append("anullsrc=r=%d:cl=stereo,atrim=0:%.3f,asetpts=PTS-STARTPTS[as%d]" % (sample_rate, row["seconds"], row["index"]))
                src_labels.append("[as%d]" % row["index"])
                continue
            record = doc["sources"][scene["source"]]
            if not record["has_audio"]:
                parts.append("anullsrc=r=%d:cl=stereo,atrim=0:%.3f,asetpts=PTS-STARTPTS[as%d]" % (sample_rate, row["seconds"], row["index"]))
                src_labels.append("[as%d]" % row["index"])
                continue
            inputs.append(record["file"])
            speed = float(scene.get("speed") or 1.0)
            chain = "atrim=start=%.3f:end=%.3f,asetpts=PTS-STARTPTS" % (float(scene["in"]), float(scene["out"]))
            if abs(speed - 1.0) > 0.001:
                chain += "," + atempo_chain(speed)
            chain += ",%s,apad=pad_dur=%.3f,atrim=0:%.3f,asetpts=PTS-STARTPTS" % (aformat(sample_rate), 0.5, row["seconds"])
            parts.append("[%d:a]%s[as%d]" % (index, chain, row["index"]))
            src_labels.append("[as%d]" % row["index"])
            index += 1
    if src_labels:
        gain = float(settings.get("source_gain_db") or 0.0)
        parts.append("%sconcat=n=%d:v=0:a=1,volume=%.2fdB[src]" % ("".join(src_labels), len(src_labels), gain))
    voice_labels = []
    for row, scene in zip(rows, scenes):
        voice = scene.get("voice")
        if not voice:
            continue
        inputs.append(safe_path(voice["file"], "voice file"))
        delay = int(round((row["start"] + float(voice.get("lead") or 0.0)) * 1000))
        parts.append("[%d:a]%s,volume=%.2fdB,adelay=%d|%d[vo%d]"
                     % (index, aformat(sample_rate), float(voice.get("gain_db") or 0.0), delay, delay, row["index"]))
        voice_labels.append("[vo%d]" % row["index"])
        index += 1
    if len(voice_labels) > 1:
        parts.append("%samix=inputs=%d:dropout_transition=0:normalize=0[voice]" % ("".join(voice_labels), len(voice_labels)))
        voice_label = "[voice]"
    elif voice_labels:
        parts.append("%sanull[voice]" % voice_labels[0])
        voice_label = "[voice]"
    else:
        voice_label = None
    music = settings.get("music")
    music_label = None
    if music and music.get("file"):
        inputs.append(safe_path(music["file"], "music file"))
        fade_in = float(music.get("fade_in") or 0.0)
        fade_out = float(music.get("fade_out") or 0.0)
        chain = "%s,atrim=0:%.3f,asetpts=PTS-STARTPTS,volume=%.2fdB" % (aformat(sample_rate), total, float(music.get("gain_db") or -18.0))
        if fade_in > 0:
            chain += ",afade=t=in:st=0:d=%.3f" % fade_in
        if fade_out > 0:
            chain += ",afade=t=out:st=%.3f:d=%.3f" % (max(0.0, total - fade_out), fade_out)
        parts.append("[%d:a]%s[mus]" % (index, chain))
        music_label = "[mus]"
        index += 1
    bed = [label for label in ("[src]" if src_labels else None, music_label) if label]
    if len(bed) == 2:
        parts.append("%samix=inputs=2:dropout_transition=0:normalize=0[bed]" % "".join(bed))
        bed_label = "[bed]"
    elif bed:
        bed_label = bed[0]
    else:
        bed_label = None
    duck_db = doc.get("audio", {}).get("duck_db")
    if bed_label and voice_label and duck_db is not None and caps()["can"]["duck"]:
        parts.append("%sasplit=2[voiceA][voiceB]" % voice_label)
        parts.append("%s[voiceB]sidechaincompress=threshold=0.05:ratio=%.1f:attack=20:release=400[ducked]"
                     % (bed_label, max(2.0, min(20.0, abs(float(duck_db)) / 2.0))))
        bed_label, voice_label = "[ducked]", "[voiceA]"
    finals = [label for label in (voice_label, bed_label) if label]
    if not finals:
        return None, None, index
    if len(finals) > 1:
        parts.append("%samix=inputs=%d:dropout_transition=0:normalize=0[mixed]" % ("".join(finals), len(finals)))
        label = "[mixed]"
    else:
        label = finals[0]
    lufs = float(doc.get("audio", {}).get("lufs") or -16.0)
    peak = float(doc.get("audio", {}).get("true_peak") or -1.5)
    parts.append("%sloudnorm=I=%.1f:TP=%.1f:LRA=11,%s,atrim=0:%.3f,asetpts=PTS-STARTPTS[a]"
                 % (label, lufs, peak, aformat(sample_rate), total))
    return ";".join(parts), "[a]", index


def encode_args(spec, variant, fps):
    codec = spec.get("video_codec") or "h264"
    args = ["-r", "%d" % fps, "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    if codec == "h264":
        args = ["-c:v", "libx264", "-preset", "slow", "-profile:v", spec.get("profile") or "high"] + args
        if spec.get("level_max"):
            args += ["-level", spec["level_max"]]
        if spec.get("video_bitrate"):
            rate = spec["video_bitrate"]
            args += ["-b:v", rate, "-maxrate", spec.get("video_bitrate_max") or rate, "-bufsize", "20M"]
        else:
            args += ["-crf", "18"]
    else:
        args = ["-c:v", "libx264", "-crf", "18", "-preset", "slow"] + args
    return args


def cmd_build(args):
    slug = need_slug(args.slug)
    doc = require_cut(slug)
    variants = [variant_by_id(doc, args.variant)] if args.variant else doc.get("variants", [])
    if not variants:
        raise usage("cut.json has no variants")
    built, warnings = [], []
    for variant in variants:
        line = build_timeline(doc, variant)
        if line["errors"]:
            return {"ok": False, "kind": "check_failed", "variant": variant["id"], "errors": line["errors"],
                    "hint": "run `time` and fix the cut; nothing was rendered"}, 1
        warnings += [dict(w, variant=variant["id"]) for w in line["warnings"]]
        width, height, fps = variant_size(variant)
        spec = target_spec(variant["target"])
        if (spec.get("video_codec") or "") == "gif":
            raise Fail("gif_target", "%s is a GIF target: build a video variant, then export the loop with `gif`"
                       % variant["target"],
                       hint="point this variant at loop-1x1, loop-16x9 or web-16x9 and run `gif --budget-mb 3`")
        fit = variant.get("fit") or "pad"
        background = variant.get("background") or "#0E1116"
        scenes = variant_scenes(doc, variant)
        build = os.path.join(project_dir(slug), "build", variant["id"])
        os.makedirs(build, exist_ok=True)
        parts, reused = [], 0
        for scene, row in zip(scenes, line["scenes"]):
            digest = scene_hash(scene, doc, width, height, fps, fit, background)
            part = os.path.join(build, "sc-%s-%s.mp4" % (scene["id"], digest))
            forced = args.scene and scene["id"] in args.scene
            if os.path.isfile(part) and not args.force and not forced:
                reused += 1
            else:
                # Exact match only: a scene id is a prefix of another id often enough
                # ("confirm" and "confirm-approach") that a prefix sweep deletes the wrong cache.
                stale_re = re.compile(r"^sc-%s-[0-9a-f]{10}\.mp4$" % re.escape(scene["id"]))
                for stale in os.listdir(build):
                    if stale_re.match(stale):
                        os.remove(os.path.join(build, stale))
                render_scene(scene, doc, part, width, height, fps, fit, background)
            parts.append(part)
        picture = os.path.join(build, "picture.mp4")
        join_scenes(parts, line["scenes"], picture, width, height, fps, background)
        out_dir = os.path.join(output_dir(slug), variant["id"])
        os.makedirs(out_dir, exist_ok=True)
        extension = (variant.get("formats") or spec.get("formats") or ["mp4"])[0]
        out_file = os.path.join(out_dir, "%s.%s" % (slug, extension))
        inputs = [picture]
        graph_parts, video_label = [], "[0:v]"
        overlay_index = 1
        for scene, row in zip(scenes, line["scenes"]):
            for overlay in scene.get("overlays") or []:
                inputs.append(overlay["file"])
                start = row["start"] + float(overlay.get("start") or 0.0)
                end = row["start"] + float(overlay.get("end") or row["seconds"])
                fade = float(overlay.get("fade") or 0.0)
                x_expr, y_expr = overlay_position(overlay)
                chain = "[%d:v]format=rgba" % overlay_index
                scale = float(overlay.get("scale") or 1.0)
                if abs(scale - 1.0) > 0.001:
                    chain += ",scale=iw*%.4f:-1:flags=lanczos" % scale
                if fade > 0:
                    chain += ",fade=t=in:st=%.3f:d=%.3f:alpha=1,fade=t=out:st=%.3f:d=%.3f:alpha=1" % (
                        start, fade, max(start, end - fade), fade)
                chain += "[ov%d]" % overlay_index
                graph_parts.append(chain)
                out_label = "[vo%d]" % overlay_index
                graph_parts.append("%s[ov%d]overlay=x=%s:y=%s:enable='between(t,%.3f,%.3f)':format=auto%s"
                                   % (video_label, overlay_index, x_expr, y_expr, start, end, out_label))
                video_label = out_label
                overlay_index += 1
        if video_label != "[0:v]":
            graph_parts.append("%sformat=yuv420p[v]" % video_label)
            video_label = "[v]"
        audio_inputs = []
        audio_part, audio_label, _ = (None, None, 0)
        if variant.get("audio", True):
            audio_part, audio_label, _ = audio_graph(doc, line["scenes"], scenes, line["total_seconds"],
                                                     int(doc.get("audio", {}).get("sample_rate") or 48000),
                                                     audio_inputs, len(inputs))
        graph = ";".join([p for p in graph_parts + ([audio_part] if audio_part else []) if p])
        argv = []
        for path in inputs + audio_inputs:
            if path == picture:
                argv += ["-i", path]
            elif path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                argv += ["-loop", "1", "-framerate", "%d" % fps, "-i", path]
            else:
                argv += ["-i", path]
        if graph:
            argv += ["-filter_complex", graph]
        argv += ["-map", video_label if video_label != "[0:v]" else "0:v"]
        if audio_label:
            argv += ["-map", audio_label, "-c:a", spec.get("audio_codec") or "aac",
                     "-b:a", spec.get("audio_bitrate") or "192k", "-ac", "%d" % (spec.get("audio_channels") or 2),
                     "-ar", "%d" % ((spec.get("audio_rates") or [48000])[-1])]
        else:
            argv += ["-an"]
        argv += ["-t", "%.3f" % line["total_seconds"]] + encode_args(spec, variant, fps) + [out_file]
        ff(argv, "assemble variant %r" % variant["id"])
        poster_at = float(variant.get("poster_at") or 0.0)
        poster = os.path.join(out_dir, "%s-poster.png" % slug)
        ff(["-ss", "%.3f" % poster_at, "-i", out_file, "-frames:v", "1", "-update", "1", poster], "write the poster frame")
        info = probe_media(out_file)
        built.append({"variant": variant["id"], "target": variant["target"], "file": out_file, "poster": poster,
                      "size": [info["width"], info["height"]], "fps": info["fps"],
                      "duration_s": info["duration_s"], "bytes": info["bytes"],
                      "scenes": len(parts), "reused": reused, "audio": bool(audio_label)})
    manifest_path = os.path.join(output_dir(slug), "manifest.json")
    kept = []
    if os.path.isfile(manifest_path):                    # a run of one variant never drops the others
        fresh = {row["variant"] for row in built}
        kept = [row for row in read_json(manifest_path, "manifest").get("files") or []
                if row.get("variant") not in fresh and os.path.isfile(row.get("file", ""))]
    manifest = {"schema": SCHEMA, "script": VERSION, "slug": slug, "name": doc.get("name"),
                "built_at": now(), "files": kept + built}
    write_json_atomic(manifest_path, manifest)
    return {"ok": True, "slug": slug, "built": built, "manifest": manifest_path,
            "warnings": warnings,
            "hint": "LOOK at the poster frame and a contact sheet of the result before delivering it; "
                    "then run `validate`"}, 0


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------

def split_cue(text, max_chars, max_lines):
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    chunks = [lines[i:i + max_lines] for i in range(0, len(lines), max_lines)]
    return ["\n".join(chunk) for chunk in chunks]


def stamp(seconds, separator):
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    whole = int(seconds % 60)
    milli = int(round((seconds - int(seconds)) * 1000))
    if milli == 1000:
        whole, milli = whole + 1, 0
    return "%02d:%02d:%02d%s%03d" % (hours, minutes, whole, separator, milli)


def cmd_captions(args):
    slug = need_slug(args.slug)
    doc = require_cut(slug)
    variant = variant_by_id(doc, args.variant) if args.variant else (doc.get("variants") or [None])[0]
    if not variant:
        raise usage("cut.json has no variants")
    line = build_timeline(doc, variant)
    if line["errors"]:
        return {"ok": False, "kind": "check_failed", "errors": line["errors"],
                "hint": "run `time` first: cue times come from a timeline that holds"}, 1
    scenes = variant_scenes(doc, variant)
    cues = []
    for scene, row in zip(scenes, line["scenes"]):
        say = (scene.get("say") or "").strip()
        if not say:
            continue
        chunks = split_cue(say, args.max_chars, args.max_lines)
        lead = float((scene.get("voice") or {}).get("lead") or 0.0)
        span = max(0.4, row["seconds"] - lead)
        weights = [max(1, len(chunk)) for chunk in chunks]
        total_weight = float(sum(weights))
        cursor = row["start"] + lead
        for chunk, weight in zip(chunks, weights):
            length = span * weight / total_weight
            cues.append({"start": round(cursor, 3), "end": round(cursor + max(0.8, length - 0.05), 3),
                         "text": chunk, "scene": scene["id"]})
            cursor += length
    for i in range(len(cues) - 1):                      # a dissolve overlaps two scenes; cues must not overlap
        if cues[i]["end"] > cues[i + 1]["start"] - 0.04:
            cues[i]["end"] = round(max(cues[i]["start"] + 0.4, cues[i + 1]["start"] - 0.04), 3)
    if not cues:
        return {"ok": False, "kind": "no_captions", "message": "no scene carries a `say` line",
                "hint": "write `say` per scene (the words the narration speaks) or generate word timings with "
                        "audiokit.py captions from the narration audio"}, 1
    out_dir = os.path.join(output_dir(slug), variant["id"])
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, "%s" % slug)
    written = {}
    formats = [f.strip() for f in (args.formats or "srt,vtt").split(",") if f.strip()]
    for fmt in formats:
        if fmt not in ("srt", "vtt", "txt"):
            raise usage("--formats takes srt, vtt or txt (got %r)" % fmt)
        path = "%s.%s" % (base, fmt)
        with open(path, "w", encoding="utf-8") as handle:
            if fmt == "vtt":
                handle.write("WEBVTT\n\n")
            for i, cue in enumerate(cues, 1):
                if fmt == "txt":
                    handle.write(cue["text"].replace("\n", " ") + "\n")
                    continue
                separator = "." if fmt == "vtt" else ","
                if fmt == "srt":
                    handle.write("%d\n" % i)
                handle.write("%s --> %s\n%s\n\n" % (stamp(cue["start"], separator), stamp(cue["end"], separator), cue["text"]))
        written[fmt] = path
    answer = {"ok": True, "variant": variant["id"], "cues": len(cues), "files": written,
              "hint": "a sidecar file is the default: the platform draws the captions and they stay editable"}
    if args.burn:
        can = caps()["can"]["burn_captions"]
        if not can:
            answer["burn"] = {"ok": False, "kind": "burn_unavailable",
                              "message": "this ffmpeg has no libass, so it cannot burn captions",
                              "hint": "deliver the SRT, or burn them through the paid subtitle route in "
                                      "references/routing-utility.md (auto-subtitle / veed with srt_content)"}
        else:
            source = os.path.join(out_dir, "%s.mp4" % slug)
            if not os.path.isfile(source):
                raise Fail("not_built", "no built file at %s" % source, hint="run `build` first")
            burned = os.path.join(out_dir, "%s-captioned.mp4" % slug)
            style = "FontSize=%d,Outline=1,Shadow=0,MarginV=%d" % (args.font_size, args.margin)
            srt = written.get("srt", base + ".srt").replace("\\", "/").replace(":", "\\:")
            ff(["-i", source, "-vf", "subtitles='%s':force_style='%s'" % (srt, style),
                "-c:a", "copy", "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p", burned],
               "burn the captions in")
            answer["burn"] = {"ok": True, "file": burned}
    return answer, 0


# --------------------------------------------------------------------------
# gif / validate
# --------------------------------------------------------------------------

GIF_LADDER = [(1080, 20), (960, 18), (900, 15), (800, 15), (720, 12), (640, 12), (540, 10), (480, 10), (400, 8), (320, 8)]


def cmd_gif(args):
    slug = need_slug(args.slug)
    doc = require_cut(slug)
    variant = variant_by_id(doc, args.variant)
    source = os.path.join(output_dir(slug), variant["id"], "%s.%s" % (slug, (variant.get("formats") or ["mp4"])[0]))
    if not os.path.isfile(source):
        raise Fail("not_built", "no built file at %s" % source, hint="run `build --variant %s` first" % variant["id"])
    info = probe_media(source)
    start = max(0.0, args.start or 0.0)
    seconds = min(float(args.seconds), max(0.5, (info["duration_s"] or 0) - start))
    budget = int(args.budget_mb * 1024 * 1024)
    out_dir = os.path.join(output_dir(slug), variant["id"])
    out = safe_path(args.out or os.path.join(out_dir, "%s-loop.gif" % slug), "--out")
    palette = os.path.join(project_dir(slug), "build", "palette-%s.png" % variant["id"])
    os.makedirs(os.path.dirname(palette), exist_ok=True)
    spec = target_spec(variant["target"])
    if spec.get("max_bytes") and spec["kind"] == "loop":
        budget = min(budget, spec["max_bytes"])
    ladder = [(args.width, args.fps)] if args.width and args.fps else \
             [(w, f) for (w, f) in GIF_LADDER if w <= (args.width or info["width"] or 1920)]
    tried, chosen = [], None
    for width, fps in ladder:
        chain = "fps=%d,scale=%d:-2:flags=lanczos" % (fps, even(width))
        ff(["-ss", "%.3f" % start, "-t", "%.3f" % seconds, "-i", source, "-vf", chain + ",palettegen=stats_mode=diff",
            "-update", "1", palette], "build the GIF palette")
        ff(["-ss", "%.3f" % start, "-t", "%.3f" % seconds, "-i", source, "-i", palette,
            "-lavfi", chain + "[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3", "-loop", "0", out],
           "render the GIF")
        size = os.path.getsize(out)
        tried.append({"width": even(width), "fps": fps, "bytes": size, "mb": round(size / 1048576.0, 3)})
        if size <= budget:
            chosen = tried[-1]
            break
    if os.path.isfile(palette):
        os.remove(palette)
    first = os.path.join(out_dir, "%s-loop-first.png" % slug)
    ff(["-ss", "%.3f" % start, "-i", source, "-frames:v", "1", "-update", "1", first], "write the first frame")
    answer = {"ok": chosen is not None, "file": out, "first_frame": first, "seconds": round(seconds, 3),
              "start": round(start, 3), "budget_mb": round(budget / 1048576.0, 2), "tried": tried,
              "chosen": chosen}
    if args.webm:
        if not caps()["can"]["webm"]:
            answer["webm"] = {"ok": False, "kind": "tool_missing", "message": "this ffmpeg has no libvpx-vp9"}
        else:
            webm = os.path.join(out_dir, "%s-loop.webm" % slug)
            ff(["-ss", "%.3f" % start, "-t", "%.3f" % seconds, "-i", source, "-an", "-c:v", "libvpx-vp9",
                "-crf", "34", "-b:v", "0", "-row-mt", "1", webm], "render the WebM loop")
            answer["webm"] = {"ok": True, "file": webm, "bytes": os.path.getsize(webm)}
    if chosen is None:
        answer["kind"] = "budget_unreachable"
        answer["hint"] = "even the smallest step is over the budget: shorten the loop, hold the picture still, " \
                         "or deliver WebM or MP4 instead"
        return answer, 1
    answer["hint"] = "Read the first frame: a GIF thumbnail animates only on hover, so that frame has to carry the post"
    return answer, 0


def measure_loudness(path):
    code, err = ff_report(["-i", path, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"])
    summary = err.split("Summary:")[-1]
    integrated = re.search(r"I:\s*(-?[0-9.]+) LUFS", summary)
    peak = re.search(r"Peak:\s*(-?[0-9.]+) dBFS", summary)
    return {"integrated_lufs": float(integrated.group(1)) if integrated else None,
            "true_peak_dbfs": float(peak.group(1)) if peak else None}


def measure_loop_seam(path, fps):
    """SSIM of the last frame against the first, both at 640 px wide: how hard the loop jumps."""
    tail_s = max(0.1, 3.0 / (fps or 30.0))             # a few frames, decoded from the end only
    graph = ("[0:v]trim=end_frame=1,scale=640:-2,setpts=PTS-STARTPTS[first];"
             "[1:v]scale=640:-2,reverse,trim=end_frame=1,setpts=PTS-STARTPTS[last];[first][last]ssim")
    code, err = ff_report(["-i", path, "-sseof", "-%.3f" % tail_s, "-i", path, "-filter_complex", graph,
                           "-an", "-f", "null", "-"])
    match = re.search(r"SSIM .*All:\s*([0-9.]+)", err)
    return round(float(match.group(1)), 4) if code == 0 and match else None


def cmd_validate(args):
    slug = need_slug(args.slug)
    doc = require_cut(slug)
    manifest_path = os.path.join(output_dir(slug), "manifest.json")
    if not os.path.isfile(manifest_path):
        raise Fail("not_built", "no manifest at %s" % manifest_path, hint="run `build` first")
    manifest = read_json(manifest_path, "manifest")
    rows = manifest.get("files") or []
    if args.variant:
        rows = [r for r in rows if r["variant"] == args.variant]
        if not rows:
            raise usage("the manifest has no variant %r" % args.variant)
    results, errors, warnings = [], 0, 0
    for row in rows:
        spec = target_spec(row["target"])
        path = row["file"]
        bad, warn = [], []
        if not os.path.isfile(path):
            results.append({"variant": row["variant"], "file": path, "errors": [{"kind": "not_found", "message": "the file is gone"}], "warnings": []})
            errors += 1
            continue
        info = probe_media(path)
        if not size_accepted(spec, info["width"], info["height"]):
            entry = {"kind": "wrong_size", "message": "%sx%s is not a size this target takes: %s"
                     % (info["width"], info["height"], sizes_text(spec))}
            (bad if spec.get("official") else warn).append(entry)
        problem = fps_problem(spec, info["fps"]) if info["fps"] else None
        if problem:
            (bad if spec.get("official") or problem["kind"] == "fps_too_high" else warn).append(problem)
        duration = info["duration_s"] or 0.0
        if spec.get("min_seconds") and duration < spec["min_seconds"] - 0.05:
            (bad if spec.get("official") else warn).append({"kind": "duration_out_of_range",
                "message": "%.2f s is under the %s s minimum" % (duration, spec["min_seconds"])})
        if spec.get("max_seconds") and duration > spec["max_seconds"] + 0.05:
            (bad if spec.get("official") else warn).append({"kind": "duration_out_of_range",
                "message": "%.2f s is over the %s s maximum" % (duration, spec["max_seconds"])})
        if spec.get("max_bytes") and info["bytes"] > spec["max_bytes"]:
            bad.append({"kind": "bytes_over_cap", "message": "%.1f MB is over the %.1f MB cap"
                        % (info["bytes"] / 1048576.0, spec["max_bytes"] / 1048576.0)})
        if spec.get("video_codec") == "h264" and info["video_codec"] != "h264":
            bad.append({"kind": "wrong_codec", "message": "the picture is %s, not h264" % info["video_codec"]})
        if spec.get("profile") and info["profile"] and spec["profile"] not in (info["profile"] or ""):
            warn.append({"kind": "profile", "message": "profile is %r, the target names %r" % (info["profile"], spec["profile"])})
        if info["has_audio"]:
            if spec.get("audio_codec") and info["audio_codec"] != spec["audio_codec"]:
                warn.append({"kind": "audio_codec", "message": "audio is %s, the target names %s" % (info["audio_codec"], spec["audio_codec"])})
            if spec.get("audio_rates") and info["audio_rate"] and info["audio_rate"] not in spec["audio_rates"]:
                warn.append({"kind": "audio_rate", "message": "%d Hz is not one of %s" % (info["audio_rate"], spec["audio_rates"])})
            if spec.get("audio_channels") and info["audio_channels"] != spec["audio_channels"]:
                warn.append({"kind": "audio_channels", "message": "%d channel(s), the target names %d" % (info["audio_channels"], spec["audio_channels"])})
            loud = measure_loudness(path)
            want = float(doc.get("audio", {}).get("lufs") or -16.0)
            peak_limit = float(doc.get("audio", {}).get("true_peak") or -1.5)
            if loud["integrated_lufs"] is not None and abs(loud["integrated_lufs"] - want) > 2.0:
                warn.append({"kind": "loudness", "message": "%.1f LUFS against a %.1f LUFS target" % (loud["integrated_lufs"], want)})
            if loud["true_peak_dbfs"] is not None and loud["true_peak_dbfs"] > peak_limit + 0.5:
                warn.append({"kind": "true_peak", "message": "peak %.1f dBFS is above %.1f" % (loud["true_peak_dbfs"], peak_limit)})
        elif spec.get("audio_required"):
            bad.append({"kind": "no_audio", "message": "this target expects an audio track"})
        poster = row.get("poster")
        if poster and not os.path.isfile(poster):
            warn.append({"kind": "no_poster", "message": "the poster frame is missing"})
        seam = measure_loop_seam(path, info["fps"]) if spec.get("loops") else None
        if seam is not None and seam < LOOP_SEAM_SSIM:
            warn.append({"kind": "loop_seam", "message": "the last frame and the first differ (SSIM %.3f, under %.2f): the "
                         "loop jumps every time it restarts; end on the opening state, or hold the same region"
                         % (seam, LOOP_SEAM_SSIM)})
        errors += len(bad)
        warnings += len(warn)
        result = {"variant": row["variant"], "target": row["target"], "file": path,
                  "size": [info["width"], info["height"]], "fps": info["fps"],
                  "duration_s": info["duration_s"], "bytes": info["bytes"],
                  "verified_on": spec.get("verified_on") or surfaces()["verified_on"],
                  "errors": bad, "warnings": warn}
        if seam is not None:
            result["loop_seam_ssim"] = seam
        results.append(result)
    answer = {"ok": errors == 0, "slug": slug, "checked": len(results), "errors": errors,
              "warnings": warnings, "results": results, "verified_on": surfaces()["verified_on"]}
    if errors:
        answer["kind"] = "check_failed"
        answer["hint"] = "fix the cut or the variant and build again; a store rejects on exactly these numbers"
        return answer, 1
    answer["hint"] = "numbers are right. Looking at the result is a separate duty: poster frame, a sheet of the cut, captions read back"
    return answer, 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(prog="democut.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("tools", help="what this ffmpeg can do here")

    p = sub.add_parser("specs", help="dated delivery targets")
    p.add_argument("--target", action="append", help="repeatable, or comma-separated")
    p.add_argument("--store", choices=["app-store", "play", "product-hunt", "web"])

    p = sub.add_parser("init", help="create the project and cut.json")
    p.add_argument("--slug", required=True)
    p.add_argument("--name")
    p.add_argument("--target", action="append", help="repeatable, or comma-separated")
    p.add_argument("--locale", action="append")

    p = sub.add_parser("source", help="register a recording")
    source_sub = p.add_subparsers(dest="source_command")
    q = source_sub.add_parser("add")
    q.add_argument("--slug", required=True)
    q.add_argument("--id", required=True)
    q.add_argument("--file", required=True)
    q.add_argument("--os", choices=["ios", "android", "web", "desktop"], default=None)
    q.add_argument("--replace", action="store_true")

    p = sub.add_parser("analyze", help="scene changes, frozen stretches, silence, black")
    p.add_argument("--slug", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--from", dest="start", type=float, default=0.0)
    p.add_argument("--to", dest="end", type=float, default=None)
    p.add_argument("--scene-threshold", type=float, default=10.0)
    p.add_argument("--freeze-seconds", type=float, default=1.5)

    p = sub.add_parser("sheet", help="contact sheet with the source time of every tile")
    p.add_argument("--slug", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--from", dest="start", type=float, default=0.0)
    p.add_argument("--to", dest="end", type=float, default=None)
    p.add_argument("--count", type=int, default=12)
    p.add_argument("--cols", type=int, default=4)
    p.add_argument("--width", type=int, default=1600)
    p.add_argument("--grid", action="store_true")
    p.add_argument("--out")

    p = sub.add_parser("grab", help="one full-size frame as PNG")
    p.add_argument("--slug", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--at", type=float, required=True)
    p.add_argument("--grid", action="store_true")
    p.add_argument("--out")

    p = sub.add_parser("time", help="validate the cut and lay out the timeline")
    p.add_argument("--slug", required=True)
    p.add_argument("--variant")

    p = sub.add_parser("build", help="render the variants")
    p.add_argument("--slug", required=True)
    p.add_argument("--variant")
    p.add_argument("--scene", action="append")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("captions", help="SRT / VTT from the timeline and the scenes' say lines")
    p.add_argument("--slug", required=True)
    p.add_argument("--variant")
    p.add_argument("--formats", default="srt,vtt")
    p.add_argument("--max-chars", type=int, default=42)
    p.add_argument("--max-lines", type=int, default=2)
    p.add_argument("--burn", action="store_true")
    p.add_argument("--font-size", type=int, default=28)
    p.add_argument("--margin", type=int, default=60)

    p = sub.add_parser("gif", help="loop export inside a measured byte budget")
    p.add_argument("--slug", required=True)
    p.add_argument("--variant", required=True)
    p.add_argument("--budget-mb", type=float, default=3.0)
    p.add_argument("--seconds", type=float, default=6.0)
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--width", type=int, default=None)
    p.add_argument("--fps", type=int, default=None)
    p.add_argument("--webm", action="store_true")
    p.add_argument("--out")

    p = sub.add_parser("validate", help="re-measure what was delivered")
    p.add_argument("--slug", required=True)
    p.add_argument("--variant")
    return parser


def dispatch(args):
    if args.command == "tools":
        return cmd_tools(args)
    if args.command == "specs":
        return cmd_specs(args)
    if args.command == "init":
        return cmd_init(args)
    if args.command == "source":
        if args.source_command != "add":
            raise usage("the only source command is `source add`")
        return cmd_source_add(args)
    if args.command == "analyze":
        return cmd_analyze(args)
    if args.command == "sheet":
        return cmd_sheet(args)
    if args.command == "grab":
        return cmd_grab(args)
    if args.command == "time":
        return cmd_time(args)
    if args.command == "build":
        return cmd_build(args)
    if args.command == "captions":
        return cmd_captions(args)
    if args.command == "gif":
        return cmd_gif(args)
    if args.command == "validate":
        return cmd_validate(args)
    raise usage("unknown command")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help(sys.stderr)
        return 2
    try:
        answer, code = dispatch(args)
    except Fail as exc:
        payload = {"ok": False, "kind": exc.kind, "message": exc.message}
        if exc.hint:
            payload["hint"] = exc.hint
        payload.update(exc.extra)
        return emit(payload, exc.code)
    except KeyError as exc:
        return emit({"ok": False, "kind": "cut_invalid", "message": "a required field is missing: %s" % exc,
                     "hint": "references/cut-json.md lists every field of a scene and a variant"}, 1)
    return emit(answer, code)


if __name__ == "__main__":
    sys.exit(main())
