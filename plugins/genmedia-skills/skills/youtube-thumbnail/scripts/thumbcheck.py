#!/usr/bin/env python3
"""thumbcheck.py - judge a thumbnail at the size people see it. Python 3.8+, stdlib only, no network.

Prints ONE compact JSON object on stdout. Exit: 0 ok | 1 failed | 2 usage.

  tools
      Which local image tool exists (ffmpeg, macOS sips) and which commands can run here.
  probe <image>... [--expect 16:9] [--max-kb N]
      Pixel size, aspect, named ratio, file size. PNG/JPEG/GIF/WebP/BMP headers are parsed in pure
      Python (works with no tool at all). A failed --expect/--max-kb check -> exit 1, kind "check_failed".
  preview <image> [--width 160] [--out <file.png>]
      The small-size gate: a ~160 px wide PNG to LOOK at before anyone else does.
  sheet <image>... --out <sheet.png> [--expect 16:9] [--cell 480] [--small 160] [--cols N]
      Comparison sheet for 1-9 variants: each numbered cell shows the variant large and, below it, the
      true-size small preview twice (on a dark and on a light strip, like a feed in dark and light mode).
  fit <image> (--size WxH | --max-side N) [--out <file.jpg|.png>] [--max-kb N] [--quality 92]
      Exact delivery size (scale to cover, centre crop) or a bounded copy for upload (also converts
      HEIC/TIFF/AVIF where the local tool can decode them). JPEG quality steps down until --max-kb fits.
  frame <video> --at <seconds|m:ss|h:mm:ss> [--out <file.png>]
      One PNG frame of the user's own video (needs ffmpeg).
  text "<hook words>" [--lang tr]
      Locale-correct ALL CAPS (Turkish i/ı), word and character budget, letter-by-letter spelling
      for the prompt and for the character-by-character check.
  lockup <plate> --logo <file.svg|png|webp> --out <file.png> [--size WxH] [--width 0.35] [--scrim 0.3] [--no-shadow]
      The user's own logo file, centred and large over a text-free plate: the plate is scaled to cover --size
      (default: its own size) and centre-cropped, a soft radial scrim goes behind the logo, the logo is drawn at
      --width of the canvas width (capped by a zone of 88 x 80 percent) with a light drop shadow. Scrim and
      shadow turn dark or light from the logo's own main colour. The logo is never redrawn by a model. Answers
      lockup {rect, width_share, asked, capped, ink, contrast} and warnings lockup_contrast (below 3.0 against
      the ground behind it), lockup_size (the width did not fit), logo_opaque (no transparency). The PNG is RGBA,
      fully opaque; `fit` makes the delivery JPEGs. Needs a Chromium-family browser.

preview, sheet and fit need local ffmpeg or macOS sips; frame needs ffmpeg; lockup needs a Chromium-family
browser. Without them the command answers {ok:false, kind:"tool_missing", hint} (exit 1) and the skill falls
back to looking at the full-size file. Never draws text with a local tool: no drawtext, Pillow or ImageMagick is
assumed; `lockup` only places the user's own logo file.
Env: GM_FFMPEG_BIN, GM_FFPROBE_BIN, GM_SIPS_BIN, GM_BROWSER_BIN (binary override; the value "none" disables that tool).
"""
import argparse
import base64
import json
import math
import os
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
import zlib

TIMEOUT_S = 120
KB = 1000  # conservative: platforms that say "2 MB" never mean less than 2,000,000 bytes
READ_LIMIT_PX = 1568  # above this an image viewer may downscale the sheet, so small previews stop being true size
NAMED_RATIOS = (("16:9", 16 / 9), ("9:16", 9 / 16), ("1:1", 1.0), ("4:5", 4 / 5), ("5:4", 5 / 4),
                ("4:3", 4 / 3), ("3:4", 3 / 4), ("3:2", 3 / 2), ("2:3", 2 / 3), ("21:9", 21 / 9))
RATIO_TOLERANCE = 0.01
SIPS_FIRST_EXT = (".heic", ".heif", ".avif")
FFMPEG_JPEG_Q = (2, 3, 4, 5, 6, 8, 10, 13, 16, 20)
SIPS_JPEG_Q = (92, 88, 84, 80, 75, 70, 65, 60, 50, 40)
MISSING_HINT = ("no local ffmpeg or sips: Read the full-size file and judge it as if it were 160 px wide, say "
                "that the mechanical preview was unavailable, and deliver the master without resizing")
FONT = {  # 5x7 numerals for the cell badges
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
}
TR_UPPER = {ord("i"): "İ", ord("ı"): "I"}
TR_LANGS = ("tr", "az")
MAX_WORDS = 4
MAX_CHARS = 20
BROWSER_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge",
                 "microsoft-edge", "brave-browser")
BROWSER_PATHS = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium",
                 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                 "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                 "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                 "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe")
BROWSER_HINT = ("no Chromium-family browser: install Chrome, Chromium, Edge or Brave, or point GM_BROWSER_BIN at one. "
                "Until then deliver the text-free plate and the logo file and say the lockup was not composed")
PAGE_TIMEOUT_S = 90
# Brand lockup over a plate: the same composition as launch-graphics' card-lockup (width as a share of the canvas
# width, a zone of 88 x 80 percent, an elliptical scrim around the logo, a light shadow).
LOCKUP_WIDTH, LOCKUP_WIDTH_RANGE = 0.35, (0.10, 0.80)
LOCKUP_SCRIM, LOCKUP_SCRIM_MAX = 0.3, 0.8
LOCKUP_MAX_SIDE = 4096
MAX_SVG_BYTES = 8 * 1024 * 1024


class Fail(Exception):
    def __init__(self, kind, message, hint=None, code=1, extra=None):
        Exception.__init__(self, message)
        self.kind, self.message, self.hint, self.code, self.extra = kind, message, hint, code, extra or {}


def emit(obj, code=0):
    text = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    sys.stdout.buffer.write(text.encode("utf-8", "backslashreplace") + b"\n")  # UTF-8 whatever the locale says
    sys.stdout.buffer.flush()
    return code


def usage(message):
    return Fail("usage", message, code=2)


# ---------------------------------------------------------------------------- local tools

def find_tool(env_name, default):
    """Return an absolute path or None. The override value "none" disables the tool."""
    override = os.environ.get(env_name)
    if override:
        if override.strip().lower() == "none":
            return None
        if os.path.isfile(override) and os.access(override, os.X_OK):
            return override
        raise Fail("tool_missing", "%s points to %r, which is not an executable file" % (env_name, override))
    return shutil.which(default)


def tools():
    return {"ffmpeg": find_tool("GM_FFMPEG_BIN", "ffmpeg"), "sips": find_tool("GM_SIPS_BIN", "sips"),
            "ffprobe": find_tool("GM_FFPROBE_BIN", "ffprobe")}


def find_browser():
    """A Chromium-family browser: GM_BROWSER_BIN first ("none" disables it), then the usual names and app paths."""
    if os.environ.get("GM_BROWSER_BIN"):
        return find_tool("GM_BROWSER_BIN", "")
    for name in BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    for path in BROWSER_PATHS:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def tool_order(path, need="image"):
    """Tools able to do the job, best first. ffmpeg scales better; sips decodes HEIC on macOS."""
    have = tools()
    order = [name for name in ("ffmpeg", "sips") if have[name]]
    if need == "video":
        order = [name for name in order if name == "ffmpeg"]
    elif path.lower().endswith(SIPS_FIRST_EXT):
        order.sort(key=lambda name: name != "sips")
    if not order:
        what = "ffmpeg" if need == "video" else "ffmpeg or sips"
        raise Fail("tool_missing", "%s not found on this machine" % what,
                   "install ffmpeg, or ask the user for a screenshot of the frame" if need == "video" else MISSING_HINT)
    return [(name, have[name]) for name in order]


def run(argv):
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return 124, "", "%s did not finish within %d s" % (os.path.basename(argv[0]), TIMEOUT_S)
    except OSError as exc:
        return 127, "", "cannot start %s: %s" % (argv[0], exc)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


def tail(text, lines=3):
    return " | ".join([ln.strip() for ln in text.strip().splitlines() if ln.strip()][-lines:])


def check_input(path):
    if path.startswith(("http://", "https://")):
        raise usage("give a local file; gm.py downloads results for you (outputs[].path)")
    if not os.path.isfile(path):
        raise Fail("not_found", "no such file: %s" % path)
    return os.path.abspath(path)


def ensure_parent(path):
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(parent):
        os.makedirs(parent)
    return os.path.abspath(path)


def wrote(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0


def clear(path):
    """Remove an older output so a tool that writes nothing cannot look like a success."""
    if os.path.isfile(path):
        os.remove(path)


# ---------------------------------------------------------------------------- image headers (pure Python)

def _jpeg_size(data):
    pos = 2
    while pos + 9 < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7 or marker == 0xFF:
            pos += 2 if marker != 0xFF else 1
            continue
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        pos += 2 + length
    return None


def _webp_size(data):
    kind = data[12:16]
    if kind == b"VP8X" and len(data) >= 30:
        return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
    if kind == b"VP8L" and len(data) >= 25:
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if kind == b"VP8 " and len(data) >= 30:
        width, height = struct.unpack("<HH", data[26:30])
        return width & 0x3FFF, height & 0x3FFF
    return None


def header_info(path):
    """(format, width, height, has_alpha|None) from the file header, or None when the format is not parsed here."""
    with open(path, "rb") as fh:
        data = fh.read(256 * 1024)
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        width, height, _depth, color = struct.unpack(">IIBB", data[16:26])
        return "png", width, height, color in (4, 6) or b"tRNS" in data[:4096]
    if data[:2] == b"\xff\xd8":
        size = _jpeg_size(data)
        if size is None:
            with open(path, "rb") as fh:
                size = _jpeg_size(fh.read())
        return ("jpeg", size[0], size[1], False) if size else None
    if data[:6] in (b"GIF87a", b"GIF89a"):
        width, height = struct.unpack("<HH", data[6:10])
        return "gif", width, height, None
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        size = _webp_size(data)
        return ("webp", size[0], size[1], None) if size else None
    if data[:2] == b"BM" and len(data) >= 26:
        width, height = struct.unpack("<ii", data[18:26])
        return "bmp", width, abs(height), None
    return None


def tool_info(path):
    """Pixel size through sips or ffprobe for formats the header parser does not know (HEIC, AVIF, TIFF)."""
    have = tools()
    if have["sips"]:
        code, out, _ = run([have["sips"], "-g", "pixelWidth", "-g", "pixelHeight", path])
        values = dict(line.strip().split(": ", 1) for line in out.splitlines() if ": " in line)
        if code == 0 and values.get("pixelWidth", "").isdigit() and values.get("pixelHeight", "").isdigit():
            return int(values["pixelWidth"]), int(values["pixelHeight"])
    if have["ffprobe"]:
        code, out, _ = run([have["ffprobe"], "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0:s=x", path])
        parts = out.strip().split("x")
        if code == 0 and len(parts) == 2 and all(p.isdigit() for p in parts):
            return int(parts[0]), int(parts[1])
    return None


def ratio_name(width, height):
    aspect = width / float(height)
    for name, value in NAMED_RATIOS:
        if abs(aspect - value) / value <= RATIO_TOLERANCE:
            return name
    divisor = math.gcd(width, height)
    return "%d:%d" % (width // divisor, height // divisor)


def parse_ratio(text):
    try:
        left, right = text.lower().replace("x", ":").split(":")
        value = float(left) / float(right)
        if value <= 0:
            raise ValueError
        return value
    except (ValueError, ZeroDivisionError):
        raise usage("--expect takes a ratio such as 16:9, 9:16 or 1:1, got %r" % text)


def describe(path, expect=None, max_kb=None):
    info = header_info(path)
    fmt = info[0] if info else os.path.splitext(path)[1].lstrip(".").lower() or "unknown"
    size = (info[1], info[2]) if info else tool_info(path)
    if not size or size[0] <= 0 or size[1] <= 0:
        raise Fail("unsupported_format", "cannot read the pixel size of %s" % path,
                   "convert it first: thumbcheck.py fit <file> --max-side 2048 --out <file>.jpg (needs ffmpeg or sips)")
    width, height = size
    nbytes = os.path.getsize(path)
    item = {"path": path, "format": fmt, "width": width, "height": height,
            "aspect": round(width / float(height), 4), "ratio": ratio_name(width, height),
            "size_bytes": nbytes, "size_kb": int(math.ceil(nbytes / float(KB)))}
    if info and info[3] is not None:
        item["has_alpha"] = bool(info[3])
    checks = {}
    if expect is not None:
        checks["aspect_ok"] = abs(item["aspect"] - expect) / expect <= RATIO_TOLERANCE
    if max_kb is not None:
        checks["size_ok"] = nbytes <= max_kb * KB
    if checks:
        item["checks"] = checks
    return item


# ---------------------------------------------------------------------------- pixels: BMP in, PNG out

def read_bmp(path):
    """(width, height, [RGB bytearray rows, top-down]) from an uncompressed 24/32-bit BMP (ffmpeg and sips output)."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:2] != b"BM" or len(data) < 54:
        raise Fail("convert_failed", "the local tool did not write a BMP")
    offset = struct.unpack("<I", data[10:14])[0]
    width, height = struct.unpack("<ii", data[18:26])
    bpp = struct.unpack("<H", data[28:30])[0]
    compression = struct.unpack("<I", data[30:34])[0]
    if bpp not in (24, 32) or compression not in (0, 3) or width <= 0 or height == 0:
        raise Fail("convert_failed", "unsupported BMP layout (%d bpp, compression %d)" % (bpp, compression))
    if compression == 3 and struct.unpack("<III", data[54:66]) != (0xFF0000, 0xFF00, 0xFF):
        raise Fail("convert_failed", "unsupported BMP channel masks")
    # the 4th byte is real alpha only when a BITFIELDS header declares it; in plain 32-bit BMPs it is padding
    has_alpha = bpp == 32 and compression == 3 and struct.unpack("<I", data[66:70])[0] == 0xFF000000
    top_down, height = height < 0, abs(height)
    step = bpp // 8
    stride = (width * step + 3) & ~3
    rows = []
    for y in range(height):
        start = offset + y * stride
        raw = data[start:start + width * step]
        if len(raw) < width * step:
            raise Fail("convert_failed", "truncated BMP")
        rgb = bytearray(width * 3)
        rgb[0::3], rgb[1::3], rgb[2::3] = raw[2::step], raw[1::step], raw[0::step]
        if has_alpha and min(raw[3::4]) < 255:  # flatten transparency onto white
            alpha = raw[3::4]
            for x in range(width):
                a = alpha[x]
                if a < 255:
                    for c in range(3):
                        rgb[x * 3 + c] = (rgb[x * 3 + c] * a + 255 * (255 - a)) // 255
        rows.append(rgb)
    if not top_down:
        rows.reverse()
    return width, height, rows


def write_png(path, width, height, rows):
    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(row) for row in rows)
    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                 + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def load_scaled(path, width, workdir):
    """Decode + scale with the local tool, return (tool, w, h, rows). Tries the second tool when the first fails."""
    errors = []
    for index, (name, binary) in enumerate(tool_order(path)):
        bmp = os.path.join(workdir, "scaled_%d_%d.bmp" % (width, index))
        if name == "ffmpeg":
            argv = [binary, "-v", "error", "-y", "-i", path, "-vf", "scale=%d:-2:flags=lanczos" % width,
                    "-frames:v", "1", "-update", "1", "-pix_fmt", "bgr24", bmp]
        else:
            argv = [binary, "-s", "format", "bmp", "--resampleWidth", str(width), path, "--out", bmp]
        code, _, err = run(argv)
        if code == 0 and wrote(bmp):
            w, h, rows = read_bmp(bmp)
            os.remove(bmp)
            return name, w, h, rows
        errors.append("%s: %s" % (name, tail(err) or "no output"))
    raise Fail("convert_failed", "could not decode %s (%s)" % (path, "; ".join(errors)))


def new_canvas(width, height, color):
    line = bytes(color) * width
    return [bytearray(line) for _ in range(height)]


def fill(canvas, x, y, width, height, color):
    width = max(0, min(width, len(canvas[0]) // 3 - x))  # slice assignment must never change a row's length
    line = bytes(color) * width
    for row in canvas[max(0, y):y + height]:
        row[x * 3:(x + width) * 3] = line


def blit(canvas, x, y, width, rows):
    width = max(0, min(width, len(canvas[0]) // 3 - x))
    for offset, row in enumerate(rows):
        if 0 <= y + offset < len(canvas):
            canvas[y + offset][x * 3:(x + width) * 3] = row[:width * 3]


def badge(canvas, x, y, digit, scale=4):
    pad = 2 * scale
    fill(canvas, x, y, 5 * scale + 2 * pad, 7 * scale + 2 * pad, (255, 212, 0))
    for gy, line in enumerate(FONT[digit].split()):
        for gx, bit in enumerate(line):
            if bit == "1":
                fill(canvas, x + pad + gx * scale, y + pad + gy * scale, scale, scale, (0, 0, 0))


# ---------------------------------------------------------------------------- commands

def cmd_tools(_args):
    have = tools()
    image_ok = bool(have["ffmpeg"] or have["sips"])
    browser = find_browser()
    result = {"ok": True, "ffmpeg": {"found": bool(have["ffmpeg"]), "path": have["ffmpeg"]},
              "sips": {"found": bool(have["sips"]), "path": have["sips"]},
              "browser": {"found": bool(browser), "path": browser},
              "can": {"probe": True, "text": True, "preview": image_ok, "sheet": image_ok, "fit": image_ok,
                      "frame": bool(have["ffmpeg"]), "lockup": bool(browser)}}
    if not image_ok:
        result["message"] = MISSING_HINT
    return emit(result)


def cmd_probe(args):
    expect = parse_ratio(args.expect) if args.expect else None
    images = [describe(check_input(path), expect, args.max_kb) for path in args.images]
    failed = [i["path"] for i in images if not all(i.get("checks", {}).values())]
    if failed:
        return emit({"ok": False, "kind": "check_failed", "message": "%d of %d files fail --expect/--max-kb"
                     % (len(failed), len(images)), "failed": failed, "images": images}, 1)
    return emit({"ok": True, "images": images})


def cmd_preview(args):
    source = check_input(args.image)
    if not 60 <= args.width <= 480:
        raise usage("--width must be between 60 and 480")
    out = ensure_parent(args.out or "%s-%dw.png" % (os.path.splitext(source)[0], args.width))
    workdir = tempfile.mkdtemp(prefix="thumbcheck_")
    try:
        tool, width, height, rows = load_scaled(source, args.width, workdir)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    write_png(out, width, height, rows)
    return emit({"ok": True, "preview": out, "width": width, "height": height, "tool": tool,
                 "source": describe(source), "next": "Read the preview: subject readable, every word legible, one focal point"})


def cmd_sheet(args):
    if not 1 <= len(args.images) <= 9:
        raise usage("give 1 to 9 images")
    if not 240 <= args.cell <= 640 or not 60 <= args.small <= 240 or args.small * 2 + 24 > args.cell:
        raise usage("--cell 240-640, --small 60-240, and two small previews must fit under one cell")
    expect = parse_ratio(args.expect) if args.expect else None
    sources = [check_input(path) for path in args.images]
    out = ensure_parent(args.out)
    if not out.lower().endswith(".png"):
        raise usage("--out must end in .png")
    cols = args.cols or min(len(sources), 3)
    if not 1 <= cols <= len(sources):
        raise usage("--cols must be between 1 and the number of images")
    margin, gap, strip_pad, head = 16, 16, 12, 50  # head: badge band above the image, never on top of it
    workdir = tempfile.mkdtemp(prefix="thumbcheck_")
    try:
        cells, variants, tool = [], [], None
        for number, source in enumerate(sources, 1):
            tool, bw, bh, big = load_scaled(source, args.cell, workdir)
            _, sw, sh, small = load_scaled(source, args.small, workdir)
            cells.append((bw, bh, big, sw, sh, small))
            item = describe(source, expect)
            item["n"] = number
            variants.append(item)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    rows_of_cells = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    heights = [head + max(c[1] for c in row) + 8 + max(c[4] for c in row) + 2 * strip_pad for row in rows_of_cells]
    sheet_w = margin * 2 + cols * args.cell + (cols - 1) * gap
    sheet_h = margin * 2 + sum(heights) + (len(heights) - 1) * gap
    canvas = new_canvas(sheet_w, sheet_h, (32, 32, 32))
    y, number = margin, 0
    for row, row_h in zip(rows_of_cells, heights):
        big_h = max(c[1] for c in row)
        for col, (bw, bh, big, sw, sh, small) in enumerate(row):
            number += 1
            x = margin + col * (args.cell + gap)
            badge(canvas, x, y, str(number))
            blit(canvas, x, y + head, bw, big)
            strip_y, strip_h, half = y + head + big_h + 8, row_h - head - big_h - 8, args.cell // 2
            fill(canvas, x, strip_y, half, strip_h, (15, 15, 15))
            fill(canvas, x + half, strip_y, args.cell - half, strip_h, (255, 255, 255))
            blit(canvas, x + (half - sw) // 2, strip_y + strip_pad, sw, small)
            blit(canvas, x + half + (args.cell - half - sw) // 2, strip_y + strip_pad, sw, small)
        y += row_h + gap
    write_png(out, sheet_w, sheet_h, canvas)
    warnings = []
    if len({v["ratio"] for v in variants}) > 1:
        warnings.append("variants have different aspect ratios: %s" % ", ".join(sorted({v["ratio"] for v in variants})))
    bad = [str(v["n"]) for v in variants if not v.get("checks", {}).get("aspect_ok", True)]
    if bad:
        warnings.append("aspect differs from --expect %s: variant %s" % (args.expect, ", ".join(bad)))
    if max(sheet_w, sheet_h) > READ_LIMIT_PX:
        warnings.append("sheet is larger than %d px; a viewer may downscale it, so also run `preview` on each "
                        "variant for a true-size look" % READ_LIMIT_PX)
    return emit({"ok": True, "sheet": out, "tool": tool, "count": len(variants), "cols": cols, "rows": len(heights),
                 "cell_width": args.cell, "small_width": args.small, "sheet_width": sheet_w, "sheet_height": sheet_h,
                 "layout": "numbered left-to-right, top-to-bottom; under each: the small preview on dark and on light",
                 "variants": variants, "warnings": warnings})


def parse_size(text):
    try:
        width, height = [int(v) for v in text.lower().split("x")]
        if not (16 <= width <= 8192 and 16 <= height <= 8192):
            raise ValueError
        return width, height
    except ValueError:
        raise usage("--size takes WIDTHxHEIGHT between 16 and 8192, for example 1280x720; got %r" % text)


def encode(tool, binary, source, out, fmt, scale_to, crop_to, quality_index):
    sw, sh = scale_to
    if tool == "ffmpeg":
        chain = "scale=%d:%d:flags=lanczos" % (sw, sh)
        if crop_to:
            chain += ",crop=%d:%d" % crop_to
        argv = [binary, "-v", "error", "-y", "-i", source, "-vf", chain, "-frames:v", "1", "-update", "1"]
        if fmt == "jpeg":
            argv += ["-pix_fmt", "yuvj444p", "-q:v", str(FFMPEG_JPEG_Q[quality_index])]
        else:
            argv += ["-pix_fmt", "rgb24"]
        argv.append(out)
    else:
        argv = [binary, "-s", "format", fmt]
        if fmt == "jpeg":
            argv += ["-s", "formatOptions", str(SIPS_JPEG_Q[quality_index])]
        argv += ["-z", str(sh), str(sw)]
        if crop_to:
            argv += ["-c", str(crop_to[1]), str(crop_to[0])]
        argv += [source, "--out", out]
    return run(argv)


def cmd_fit(args):
    source = check_input(args.image)
    if bool(args.size) == bool(args.max_side):
        raise usage("give exactly one of --size WxH or --max-side N")
    info = describe(source)
    width, height = info["width"], info["height"]
    if args.size:
        target = parse_size(args.size)
        factor = max(target[0] / float(width), target[1] / float(height))
        scale_to = (max(target[0], int(math.ceil(width * factor))), max(target[1], int(math.ceil(height * factor))))
        crop_to = target if scale_to != target else None
        suffix = "-%dx%d" % target
    else:
        if not 256 <= args.max_side <= 8192:
            raise usage("--max-side must be between 256 and 8192")
        factor = min(1.0, args.max_side / float(max(width, height)))
        scale_to = (max(1, int(round(width * factor))), max(1, int(round(height * factor))))
        target, crop_to, suffix = scale_to, None, "-%dpx" % max(scale_to)
    out = ensure_parent(args.out or os.path.splitext(source)[0] + suffix + ".jpg")
    ext = os.path.splitext(out)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        raise usage("--out must end in .jpg, .jpeg or .png")
    if os.path.abspath(out) == source:
        raise usage("--out must differ from the input file")
    fmt = "png" if ext == ".png" else "jpeg"
    ladder = FFMPEG_JPEG_Q if fmt == "jpeg" else (None,)
    start = 0
    if fmt == "jpeg" and args.quality is not None:
        if not 40 <= args.quality <= 100:
            raise usage("--quality must be between 40 and 100")
        start = min(range(len(SIPS_JPEG_Q)), key=lambda i: abs(SIPS_JPEG_Q[i] - args.quality))
    errors, done = [], None
    for tool, binary in tool_order(source):
        for index in range(start, len(ladder)):
            clear(out)
            code, _, err = encode(tool, binary, source, out, fmt, scale_to, crop_to, index)
            if code != 0 or not wrote(out):
                errors.append("%s: %s" % (tool, tail(err) or "no output"))
                done = None  # an earlier, larger step was already cleared: fall through to the next tool
                break
            done = (tool, index)
            if args.max_kb is None or os.path.getsize(out) <= args.max_kb * KB:
                break
        if done:
            break
    if not done:
        raise Fail("convert_failed", "could not write %s (%s)" % (out, "; ".join(errors)))
    written = describe(out, max_kb=args.max_kb)
    result = {"ok": True, "out": written.pop("path")}
    result.update(written)
    result.update({"tool": done[0], "source": {"width": width, "height": height},
                   "cropped": bool(crop_to), "upscaled": factor > 1.0, "warnings": []})
    if fmt == "jpeg":
        result["jpeg_quality"] = SIPS_JPEG_Q[done[1]]
    if (result["width"], result["height"]) != tuple(target):
        raise Fail("convert_failed", "wrote %dx%d instead of %dx%d" % (result["width"], result["height"], target[0], target[1]))
    if factor > 1.0:
        result["warnings"].append("the source is smaller than the target, so this copy is soft: enlarge on fal first "
                                  "(references/revisions.md, Enlarge) or deliver a smaller size")
    if crop_to:
        result["warnings"].append("aspect differed: centre-cropped %dx%d to %dx%d; Read the result and check that "
                                  "no text or face was cut" % (scale_to[0], scale_to[1], target[0], target[1]))
    if args.max_kb is not None and not result["checks"]["size_ok"]:
        result.update({"ok": False, "kind": "too_large", "message": "still %d KB at the lowest quality step (limit %d KB)"
                       % (result["size_kb"], args.max_kb), "hint": "write a .jpg instead of .png, or deliver a smaller --size"})
        return emit(result, 1)
    return emit(result)


def parse_time(text):
    try:
        parts = [float(p) for p in text.split(":")]
        if not 1 <= len(parts) <= 3 or any(p < 0 for p in parts):
            raise ValueError
        seconds = 0.0
        for part in parts:
            seconds = seconds * 60 + part
        return seconds
    except ValueError:
        raise usage("--at takes seconds, m:ss or h:mm:ss, got %r" % text)


def cmd_frame(args):
    video = check_input(args.video)
    seconds = parse_time(args.at)
    label = ("%.2f" % seconds).rstrip("0").rstrip(".").replace(".", "_")
    out = ensure_parent(args.out or "%s_%ss.png" % (os.path.splitext(video)[0], label))
    if not out.lower().endswith(".png"):
        raise usage("--out must end in .png")
    _, ffmpeg = tool_order(video, need="video")[0]
    clear(out)
    code, _, err = run([ffmpeg, "-v", "error", "-y", "-ss", "%.3f" % seconds, "-i", video, "-an",
                        "-frames:v", "1", "-update", "1", out])
    if code != 0 or not wrote(out):
        raise Fail("extract_failed", "no frame at %s s: %s" % (label.replace("_", "."), tail(err) or "nothing was written"),
                   "is the timestamp past the end of the video? try an earlier one")
    written = describe(out)
    result = {"ok": True, "frame": written.pop("path"), "at_s": round(seconds, 3)}
    result.update(written)
    result["next"] = "Read the frame; when it is smaller than the render size, enlarge it before using it as the plate"
    return emit(result)


def cmd_text(args):
    text = " ".join(args.text.split())
    if not text:
        raise usage("give the hook words")
    lang = args.lang.lower().split("-")[0].split("_")[0]
    upper = (text.translate(TR_UPPER) if lang in TR_LANGS else text).upper()
    words = upper.split(" ")
    special = sorted({ch for ch in upper if ch.isalpha() and ord(ch) > 127})
    warnings = []
    if len(words) > MAX_WORDS:
        warnings.append("%d words: cut to %d or fewer, the title carries the rest" % (len(words), MAX_WORDS))
    if len(upper) > MAX_CHARS:
        warnings.append("%d characters: over about %d the letters get too small at 160 px; shorten or plan two lines"
                        % (len(upper), MAX_CHARS))
    if lang not in TR_LANGS and any(ch in text for ch in "ıİğĞşŞ"):
        warnings.append("Turkish letters found but --lang is %r: rerun with --lang tr so i/ı are cased correctly" % args.lang)
    return emit({"ok": True, "text": text, "lang": lang, "upper": upper, "words": len(words), "chars": len(upper),
                 "spelled": " / ".join("-".join(word) for word in words), "special_letters": special,
                 "checks": {"words_ok": len(words) <= MAX_WORDS, "chars_ok": len(upper) <= MAX_CHARS},
                 "warnings": warnings})


# ---------------------------------------------------------------------------- brand lockup (browser)

# Runs synchronously inside the load handler: a headless browser dumps the DOM right after `load`. The picture is
# drawn on a canvas and handed back as a PNG data URL, so the window size (and the new headless mode's own bars)
# never touches the output.
LOCKUP_JS = r"""
window.addEventListener('load',function(){var out=document.getElementById('tc-out');try{
function $(id){return document.getElementById(id)}
function chan(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)}
function lum(c){return 0.2126*chan(c[0])+0.7152*chan(c[1])+0.0722*chan(c[2])}
function rgba(c,a){return'rgba('+c[0]+','+c[1]+','+c[2]+','+a+')'}
function hex(c){return'#'+c.map(function(v){return('0'+Math.round(v).toString(16)).slice(-2)}).join('')}
var T=window.TC,W=T.W,H=T.H,p=$('plate'),l=$('logo'),c=document.createElement('canvas');c.width=W;c.height=H;
var g=c.getContext('2d',{willReadFrequently:true});g.imageSmoothingEnabled=true;g.imageSmoothingQuality='high';
var pw=p.naturalWidth,ph=p.naturalHeight,k=Math.max(W/pw,H/ph);g.drawImage(p,(W-pw*k)/2,(H-ph*k)/2,pw*k,ph*k);
var want=T.width*W,w=Math.min(want,0.88*W,0.80*H*T.aspect),h=w/T.aspect,x=(W-w)/2,y=(H-h)/2;
var sw=Math.max(1,Math.min(200,Math.round(w))),sh=Math.max(1,Math.round(sw/T.aspect)),m=document.createElement('canvas');m.width=sw;m.height=sh;
var mg=m.getContext('2d',{willReadFrequently:true});mg.drawImage(l,0,0,sw,sh);var d=mg.getImageData(0,0,sw,sh).data,bins={},best=null,bn=0,clear=0;
for(var i=0;i<d.length;i+=4){if(d[i+3]<200){clear++;continue}var key=(d[i]>>4)<<8|(d[i+1]>>4)<<4|(d[i+2]>>4),o=bins[key];if(!o){o=bins[key]=[0,0,0,0]}
 o[0]++;o[1]+=d[i];o[2]+=d[i+1];o[3]+=d[i+2];if(o[0]>bn){bn=o[0];best=o}}
var ink=best?[best[1]/best[0],best[2]/best[0],best[3]/best[0]]:null,light=ink?lum(ink)>0.4:true,shade=light?[0,0,0]:[255,255,255];
if(T.scrim>0){var rx=0.9*w,ry=Math.max(1.6*h,0.45*w);g.save();g.translate(W/2,H/2);g.scale(1,ry/rx);var rg=g.createRadialGradient(0,0,0,0,0,rx);
 rg.addColorStop(0,rgba(shade,T.scrim));rg.addColorStop(0.55,rgba(shade,T.scrim*0.55));rg.addColorStop(1,rgba(shade,0));g.fillStyle=rg;g.fillRect(-rx,-rx,2*rx,2*rx);g.restore()}
var contrast=null;if(ink){var x0=Math.max(0,Math.floor(x)),y0=Math.max(0,Math.floor(y)),bw=Math.min(W,Math.ceil(x+w))-x0,bh=Math.min(H,Math.ceil(y+h))-y0;
 var b=g.getImageData(x0,y0,bw,bh).data,step=Math.max(1,Math.floor(Math.sqrt(bw*bh/3500))),tl=lum(ink),vals=[];
 for(var yy=0;yy<bh;yy+=step)for(var xx=0;xx<bw;xx+=step){var j=(yy*bw+xx)*4,bl=lum([b[j],b[j+1],b[j+2]]);vals.push((Math.max(tl,bl)+0.05)/(Math.min(tl,bl)+0.05))}
 vals.sort(function(u,v){return u-v});contrast=Math.round(vals[Math.floor(vals.length*0.05)]*100)/100}
g.save();if(T.shadow){g.shadowColor=light?'rgba(0,0,0,0.38)':'rgba(255,255,255,0.5)';g.shadowBlur=h*0.24;g.shadowOffsetY=h*0.03}
g.drawImage(l,x,y,w,h);g.restore();
var r=function(v){return Math.round(v*10)/10},url=c.toDataURL('image/png');
out.textContent=JSON.stringify({ok:true,rect:[r(x),r(y),r(w),r(h)],width_share:Math.round(w/W*1000)/1000,asked:T.width,capped:w<want-0.5,
 ink:ink?hex(ink):null,contrast:contrast,clear_share:Math.round(clear/(sw*sh)*1000)/1000,png:url.slice(url.indexOf(',')+1)});
}catch(e){out.textContent=JSON.stringify({ok:false,kind:'js_error',message:String(e&&e.stack||e)})}});
"""


def data_uri(path, fmt):
    mime = {"svg": "image/svg+xml", "png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}[fmt]
    with open(path, "rb") as fh:
        return "data:%s;base64,%s" % (mime, base64.b64encode(fh.read()).decode("ascii"))


def svg_aspect(path):
    """Width over height of an SVG's artboard (viewBox, else numeric width and height). The file is only shown
    through <img>, where scripts never run and nothing outside the file is fetched; entities are refused."""
    if os.path.getsize(path) > MAX_SVG_BYTES:
        raise Fail("svg_too_large", "%s is larger than %d bytes" % (path, MAX_SVG_BYTES))
    with open(path, "rb") as fh:
        raw = fh.read()
    if b"<!ENTITY" in raw.upper():
        raise Fail("svg_invalid", "%s declares XML entities" % path, "export the logo again as plain outlined shapes")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise Fail("svg_invalid", "%s is not well-formed XML: %s" % (path, exc))
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise Fail("svg_invalid", "%s: the root element is not <svg>" % path)
    try:
        box = [float(v) for v in (root.get("viewBox") or "").replace(",", " ").split()]
        width, height = (box[2], box[3]) if len(box) == 4 else (
            float((root.get("width") or "").rstrip("px")), float((root.get("height") or "").rstrip("px")))
    except ValueError:
        raise Fail("svg_invalid", "%s has no viewBox and no numeric width and height" % path)
    if width <= 0 or height <= 0:
        raise Fail("svg_invalid", "%s has an empty artboard" % path)
    return width / height


def run_page(binary, page):
    """ONE headless run; the page writes its answer into <pre id="tc-out">. Chrome often does not exit by itself
    after --dump-dom: poll for the complete DOM, then stop it. Every run gets a throw-away profile."""
    profile = tempfile.mkdtemp(prefix="thumbcheck-browser-")
    sink_path = os.path.join(profile, "dom.html")
    argv = [binary, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
            "--force-color-profile=srgb", "--user-data-dir=" + profile, "--window-size=800,600",
            "--virtual-time-budget=6000", "--dump-dom", pathlib.Path(page).resolve().as_uri()]

    def done():
        try:
            with open(sink_path, "rb") as fh:
                fh.seek(0, 2)
                fh.seek(max(0, fh.tell() - 256))
                return b"</html>" in fh.read()
        except OSError:
            return False
    try:
        with open(sink_path, "wb") as sink:
            try:
                process = subprocess.Popen(argv, stdout=sink, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
            except OSError as exc:
                raise Fail("tool_failed", "cannot start %s: %s" % (binary, exc), BROWSER_HINT)
            started = time.time()
            try:
                while time.time() - started < PAGE_TIMEOUT_S and not done() and process.poll() is None:
                    time.sleep(0.05)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(5)
        if not done():
            raise Fail("tool_failed", "%s gave no complete page within %d s" % (os.path.basename(binary), PAGE_TIMEOUT_S),
                       "run the command again")
        with open(sink_path, "rb") as fh:
            text = fh.read().decode("utf-8", "replace")
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    start, end = text.find('<pre id="tc-out">'), text.find("</pre>")
    body = text[start + len('<pre id="tc-out">'):end] if 0 <= start < end else ""
    try:
        data = json.loads(body.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
    except ValueError:
        raise Fail("tool_failed", "the page did not report (got %r)" % body[:80], "run the command again")
    if not isinstance(data, dict):
        raise Fail("tool_failed", "the page reported %r" % (data,))
    return data


def cmd_lockup(args):
    plate = check_input(args.plate)
    logo = check_input(args.logo)
    low, high = LOCKUP_WIDTH_RANGE
    if not low <= args.width <= high:
        raise usage("--width is a share of the canvas width between %g and %g" % (low, high))
    if not 0 <= args.scrim <= LOCKUP_SCRIM_MAX:
        raise usage("--scrim must be between 0 and %g (0 = none)" % LOCKUP_SCRIM_MAX)
    out = ensure_parent(args.out)
    if not out.lower().endswith(".png"):
        raise usage("--out must end in .png; `fit` makes the JPEG delivery sizes from it")
    if out in (plate, logo):
        raise usage("--out must differ from the input files")
    plate_info = header_info(plate)
    if not plate_info or plate_info[0] not in ("png", "jpeg", "webp"):
        raise Fail("unsupported_format", "the plate must be PNG, JPEG or WebP: %s" % plate,
                   "convert it first: thumbcheck.py fit <file> --max-side 2048 --out <file>.png")
    width, height = parse_size(args.size) if args.size else (plate_info[1], plate_info[2])
    if max(width, height) > LOCKUP_MAX_SIDE:
        raise usage("the canvas is at most %d px on its longer side" % LOCKUP_MAX_SIDE)
    warnings = []
    if logo.lower().endswith(".svg"):
        fmt, aspect = "svg", svg_aspect(logo)
    else:
        info = header_info(logo)
        if not info or info[0] not in ("png", "jpeg", "webp"):
            raise Fail("unsupported_format", "the logo must be SVG, PNG, JPEG or WebP: %s" % logo)
        fmt, aspect = info[0], info[1] / float(info[2])
    binary = find_browser()
    if not binary:
        raise Fail("tool_missing", "lockup needs a Chromium-family browser, and none was found", BROWSER_HINT)
    spec = {"W": width, "H": height, "width": args.width, "scrim": args.scrim, "shadow": not args.no_shadow, "aspect": aspect}
    workdir = tempfile.mkdtemp(prefix="thumbcheck_")
    try:
        page = os.path.join(workdir, "lockup.html")
        with open(page, "w", encoding="utf-8") as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8"></head><body><pre id="tc-out">pending</pre>'
                     '<img id="plate" alt="" style="display:none" src="%s"><img id="logo" alt="" style="display:none" src="%s">'
                     '<script>window.TC=%s;%s</script></body></html>'
                     % (data_uri(plate, plate_info[0]), data_uri(logo, fmt), json.dumps(spec), LOCKUP_JS))
        data = run_page(binary, page)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    if not data.get("ok"):
        raise Fail("tool_failed", "the lockup page failed: %s" % str(data.get("message") or data.get("kind"))[:300])
    try:
        blob = base64.b64decode(data.pop("png"), validate=True)
    except (KeyError, ValueError, TypeError):
        raise Fail("tool_failed", "the browser returned no readable PNG", "run the command again")
    if not blob.startswith(b"\x89PNG\r\n\x1a\n") or struct.unpack(">II", blob[16:24]) != (width, height):
        raise Fail("tool_failed", "the browser returned something other than a %dx%d PNG" % (width, height))
    clear(out)
    with open(out, "wb") as fh:
        fh.write(blob)
    data.pop("ok", None)
    clear_share = data.pop("clear_share", None)
    if data.get("contrast") is not None and data["contrast"] < 3.0:
        warnings.append({"code": "lockup_contrast", "message": "the logo's main colour %s has %.2f:1 against the ground "
                         "behind it: raise --scrim, use the logo version made for this ground, or a calmer plate"
                         % (data.get("ink"), data["contrast"])})
    if data.get("capped"):
        warnings.append({"code": "lockup_size", "message": "the logo reached %.2f of the width, not %.2f: a tall mark "
                         "reaches 80 percent of the height first" % (data["width_share"], args.width)})
    if fmt == "jpeg" or (clear_share is not None and clear_share < 0.02):
        warnings.append({"code": "logo_opaque", "message": "the logo fills its whole box (no transparent area), so the box "
                         "hides the plate: use a version without a background, e.g. the SVG or transparent PNG from brandkit"})
    source = {"width": plate_info[1], "height": plate_info[2]}
    cropped = abs(plate_info[1] / float(plate_info[2]) - width / float(height)) > 0.002
    return emit({"ok": True, "out": out, "width": width, "height": height, "lockup": data, "scrim": args.scrim,
                 "shadow": not args.no_shadow, "source": source, "cropped": cropped,
                 "upscaled": width > plate_info[1] or height > plate_info[2], "warnings": warnings,
                 "next": "Read the file, then the 160 px gate (preview), then fit for the delivery sizes"})


def build_parser():
    parser = argparse.ArgumentParser(prog="thumbcheck.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    p = sub.add_parser("tools", help="which local tools exist and which commands can run")
    p.set_defaults(func=cmd_tools)
    p = sub.add_parser("probe", help="pixel size, aspect, ratio, file size; optional checks")
    p.add_argument("images", nargs="+", metavar="image")
    p.add_argument("--expect", help="required aspect ratio, e.g. 16:9")
    p.add_argument("--max-kb", type=int, help="required maximum file size in KB (1 KB = 1000 bytes)")
    p.set_defaults(func=cmd_probe)
    p = sub.add_parser("preview", help="small PNG for the small-size gate")
    p.add_argument("image")
    p.add_argument("--width", type=int, default=160, help="preview width in px, 60-480 (160)")
    p.add_argument("--out", help="output .png (default: <image>-<width>w.png)")
    p.set_defaults(func=cmd_preview)
    p = sub.add_parser("sheet", help="numbered comparison sheet with true-size small previews")
    p.add_argument("images", nargs="+", metavar="image")
    p.add_argument("--out", required=True, help="output .png")
    p.add_argument("--expect", help="aspect ratio every variant should have, e.g. 16:9")
    p.add_argument("--cell", type=int, default=480, help="width of the large view per variant, 240-640 (480)")
    p.add_argument("--small", type=int, default=160, help="width of the small preview, 60-240 (160)")
    p.add_argument("--cols", type=int, default=0, help="columns (default: min(count, 3))")
    p.set_defaults(func=cmd_sheet)
    p = sub.add_parser("fit", help="exact delivery size, or a bounded copy for upload")
    p.add_argument("image")
    p.add_argument("--size", help="WIDTHxHEIGHT: scale to cover, centre crop")
    p.add_argument("--max-side", type=int, help="downscale so the longer side is at most N px; never upscales")
    p.add_argument("--out", help="output .jpg or .png (default: <image>-<size>.jpg)")
    p.add_argument("--max-kb", type=int, help="step JPEG quality down until the file fits (1 KB = 1000 bytes)")
    p.add_argument("--quality", type=int, help="starting JPEG quality, 40-100 (92)")
    p.set_defaults(func=cmd_fit)
    p = sub.add_parser("frame", help="one PNG frame of a local video (needs ffmpeg)")
    p.add_argument("video")
    p.add_argument("--at", required=True, help="seconds, m:ss or h:mm:ss")
    p.add_argument("--out", help="output .png (default: <video>_<seconds>s.png)")
    p.set_defaults(func=cmd_frame)
    p = sub.add_parser("lockup", help="the user's logo centred over a plate (needs a Chromium-family browser)")
    p.add_argument("plate")
    p.add_argument("--logo", required=True, help="the user's own logo: .svg, or a transparent .png or .webp")
    p.add_argument("--out", required=True, help="output .png")
    p.add_argument("--size", help="WIDTHxHEIGHT: cover and centre-crop the plate (default: the plate's own size)")
    p.add_argument("--width", type=float, default=LOCKUP_WIDTH, help="logo width as a share of the canvas width, 0.10-0.80 (0.35)")
    p.add_argument("--scrim", type=float, default=LOCKUP_SCRIM, help="radial shade behind the logo, 0-0.8 (0.3; 0 = none)")
    p.add_argument("--no-shadow", action="store_true", help="no drop shadow under the logo")
    p.set_defaults(func=cmd_lockup)

    p = sub.add_parser("text", help="locale-correct caps, word budget, spelling string")
    p.add_argument("text")
    p.add_argument("--lang", default="en", help="language of the text, e.g. tr, en, de (en)")
    p.set_defaults(func=cmd_text)
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
        payload.update(exc.extra)
        return emit(payload, exc.code)


if __name__ == "__main__":
    sys.exit(main())
