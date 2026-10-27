#!/usr/bin/env python3
# GENERATED from shared/scripts/frames.py — edit the source, then run scripts/sync_shared.py
"""frames.py - look at a video without watching it. Python 3.8+, stdlib only, local ffmpeg/ffprobe.

Prints ONE compact JSON object on stdout. Exit: 0 ok | 1 failed | 2 usage.

  probe <video>
      -> {ok, path, duration_s, width, height, fps, frame_count, has_audio, video_codec, size_bytes}
  sheet <video> [--count 6] [--cols 3] [--width 480] [--out <file.jpg>]
      Contact sheet for self-review: N frames spread from the first to the exact last frame, tiled
      left-to-right, top-to-bottom. -> {ok, sheet, count, cols, times_s:[...], duration_s, ...}
  frame <video> [--at first|middle|last|<seconds>] [--out <file.png>]
      One lossless PNG. `--at last` (default) is the exact final decoded frame, not a timestamp guess:
      use it as the start image of the next clip when chaining.

No ffmpeg/ffprobe -> {ok:false, kind:"ffmpeg_missing", hint} (exit 1); the hint names the fal utility
endpoint that does the same job. Never touches the network, never reads credentials.
Env: GM_FFMPEG_BIN, GM_FFPROBE_BIN (binary overrides, used by the tests).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

TIMEOUT_S = 180
FALLBACK_HINT = ("no local ffmpeg/ffprobe: run fal-ai/ffmpeg-api/extract-frame with video_url and "
                 "frame_type first|middle|last (see references/video-recipes.md), or install ffmpeg")


class Fail(Exception):
    def __init__(self, kind, message, hint=None, code=1):
        Exception.__init__(self, message)
        self.kind, self.message, self.hint, self.code = kind, message, hint, code


def emit(obj, code=0):
    sys.stdout.write(json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n")
    return code


def find_bin(env_name, default):
    override = os.environ.get(env_name)
    if override:
        if os.path.isfile(override) and os.access(override, os.X_OK):
            return override
        raise Fail("ffmpeg_missing", "%s points to %r, which is not an executable file" % (env_name, override),
                   FALLBACK_HINT)
    found = shutil.which(default)
    if not found:
        raise Fail("ffmpeg_missing", "%s not found on PATH" % default, FALLBACK_HINT)
    return found


def run(argv):
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        raise Fail("timeout", "%s did not finish within %d s" % (os.path.basename(argv[0]), TIMEOUT_S))
    except OSError as exc:
        raise Fail("ffmpeg_missing", "cannot start %s: %s" % (argv[0], exc), FALLBACK_HINT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


def tail(text, lines=4):
    return " | ".join([ln.strip() for ln in text.strip().splitlines() if ln.strip()][-lines:])


def check_input(path):
    if path.startswith(("http://", "https://")):
        raise Fail("usage", "give a local file; download the URL first (gm.py downloads results for you)", code=2)
    if not os.path.isfile(path):
        raise Fail("not_found", "no such file: %s" % path)
    return path


def parse_rate(text):
    try:
        if "/" in text:
            num, den = text.split("/", 1)
            return round(float(num) / float(den), 3) if float(den) else None
        return round(float(text), 3)
    except (TypeError, ValueError):
        return None


def probe(path):
    ffprobe = find_bin("GM_FFPROBE_BIN", "ffprobe")
    code, out, err = run([ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path])
    if code != 0:
        raise Fail("probe_failed", "ffprobe could not read the file: %s" % tail(err))
    try:
        data = json.loads(out)
    except ValueError:
        raise Fail("probe_failed", "ffprobe did not return JSON")
    streams = data.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise Fail("no_video_stream", "the file has no video stream")
    fmt = data.get("format") or {}

    def number(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    duration = number(video.get("duration")) or number(fmt.get("duration"))
    if not duration or duration <= 0:
        raise Fail("probe_failed", "could not determine the duration")
    frames = video.get("nb_frames")
    return {
        "path": path,
        "duration_s": round(duration, 3),
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": parse_rate(video.get("avg_frame_rate") or "") or parse_rate(video.get("r_frame_rate") or ""),
        "frame_count": int(frames) if str(frames).isdigit() else None,
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
        "video_codec": video.get("codec_name"),
        "size_bytes": int(fmt["size"]) if str(fmt.get("size", "")).isdigit() else os.path.getsize(path),
    }


def ensure_parent(path):
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(parent):
        os.makedirs(parent)


def grab(ffmpeg, video, at, out, duration):
    """Write one frame. at: 'last' or seconds (float)."""
    ensure_parent(out)
    quality = ["-q:v", "2"] if out.lower().endswith((".jpg", ".jpeg")) else []
    if at == "last":
        # Decode the final second and keep overwriting one file: what remains is the exact last frame.
        window = "-%.3f" % min(1.0, max(duration, 0.05))
        argv = [ffmpeg, "-v", "error", "-y", "-sseof", window, "-i", video, "-an", "-update", "1"] + quality + [out]
    else:
        argv = [ffmpeg, "-v", "error", "-y", "-ss", "%.3f" % max(0.0, at), "-i", video, "-an",
                "-frames:v", "1", "-update", "1"] + quality + [out]
    code, _, err = run(argv)
    if code != 0 or not os.path.isfile(out) or os.path.getsize(out) == 0:
        raise Fail("extract_failed", "ffmpeg could not write %s: %s" % (out, tail(err) or "no output"))
    return out


def default_out(video, suffix):
    stem = os.path.splitext(os.path.abspath(video))[0]
    return stem + suffix


def cmd_probe(args):
    info = probe(check_input(args.video))
    info["ok"] = True
    return emit(info)


def cmd_frame(args):
    video = check_input(args.video)
    info = probe(video)
    ffmpeg = find_bin("GM_FFMPEG_BIN", "ffmpeg")
    at = args.at
    if at == "first":
        where, label = 0.0, "first"
    elif at == "middle":
        where, label = info["duration_s"] / 2.0, "middle"
    elif at == "last":
        where, label = "last", "last"
    else:
        try:
            where = float(at)
        except ValueError:
            raise Fail("usage", "--at takes first, middle, last or seconds, got %r" % at, code=2)
        if where < 0 or where >= info["duration_s"]:
            raise Fail("usage", "--at %s is outside the clip (0 to %.3f s); use --at last for the final frame"
                       % (at, info["duration_s"]), code=2)
        label = ("%.2f" % where).replace(".", "_") + "s"
    out = args.out or default_out(video, "_%s.png" % label)
    grab(ffmpeg, video, where, out, info["duration_s"])
    return emit({"ok": True, "frame": out, "at": at, "exact_last": at == "last",
                 "duration_s": info["duration_s"], "width": info["width"], "height": info["height"]})


def cmd_sheet(args):
    video = check_input(args.video)
    if not 2 <= args.count <= 16:
        raise Fail("usage", "--count must be between 2 and 16", code=2)
    if not 120 <= args.width <= 1024:
        raise Fail("usage", "--width must be between 120 and 1024", code=2)
    info = probe(video)
    ffmpeg = find_bin("GM_FFMPEG_BIN", "ffmpeg")
    duration = info["duration_s"]
    count = args.count
    cols = args.cols if args.cols else min(count, 3)
    if not 1 <= cols <= count:
        raise Fail("usage", "--cols must be between 1 and --count", code=2)
    rows = (count + cols - 1) // cols
    times = [round(duration * i / (count - 1), 3) for i in range(count - 1)]
    out = args.out or default_out(video, "_sheet.jpg")
    ensure_parent(out)
    workdir = tempfile.mkdtemp(prefix="frames_")
    try:
        for index, moment in enumerate(times):
            grab(ffmpeg, video, moment, os.path.join(workdir, "f_%02d.png" % index), duration)
        grab(ffmpeg, video, "last", os.path.join(workdir, "f_%02d.png" % (count - 1)), duration)
        tile = "scale=%d:-2,tile=%dx%d:padding=6:margin=6:color=white" % (args.width, cols, rows)
        argv = [ffmpeg, "-v", "error", "-y", "-framerate", "1", "-start_number", "0",
                "-i", os.path.join(workdir, "f_%02d.png"), "-vf", tile, "-frames:v", "1", "-update", "1",
                "-q:v", "3", out]
        code, _, err = run(argv)
        if code != 0 or not os.path.isfile(out) or os.path.getsize(out) == 0:
            raise Fail("sheet_failed", "ffmpeg could not build the contact sheet: %s" % (tail(err) or "no output"))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    result = {"ok": True, "sheet": out, "count": count, "cols": cols, "rows": rows,
              "times_s": times + [duration], "order": "left-to-right, top-to-bottom; last tile = exact last frame"}
    result.update({k: info[k] for k in ("duration_s", "width", "height", "fps", "has_audio")})
    return emit(result)


def build_parser():
    parser = argparse.ArgumentParser(prog="frames.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    p = sub.add_parser("probe", help="duration, size, fps, audio track")
    p.add_argument("video")
    p.set_defaults(func=cmd_probe)
    p = sub.add_parser("sheet", help="contact sheet of N frames for self-review")
    p.add_argument("video")
    p.add_argument("--count", type=int, default=6, help="frames on the sheet, 2-16 (6)")
    p.add_argument("--cols", type=int, default=0, help="columns (default: min(count, 3))")
    p.add_argument("--width", type=int, default=480, help="pixel width of each tile, 120-1024 (480)")
    p.add_argument("--out", help="output .jpg (default: <video>_sheet.jpg)")
    p.set_defaults(func=cmd_sheet)
    p = sub.add_parser("frame", help="one PNG frame; --at last is the exact final frame")
    p.add_argument("video")
    p.add_argument("--at", default="last", help="first | middle | last | <seconds> (last)")
    p.add_argument("--out", help="output image (default: <video>_<at>.png)")
    p.set_defaults(func=cmd_frame)
    return parser


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    if not getattr(args, "func", None):
        parser.print_help(sys.stderr)
        return 2
    try:
        return args.func(args)
    except Fail as exc:
        payload = {"ok": False, "kind": exc.kind, "message": exc.message}
        if exc.hint:
            payload["hint"] = exc.hint
        return emit(payload, exc.code)


if __name__ == "__main__":
    sys.exit(main())
