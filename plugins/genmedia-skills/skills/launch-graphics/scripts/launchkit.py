#!/usr/bin/env python3
"""launchkit.py - compose store screenshots, link cards and launch graphics from real captures.
Python 3.8+, stdlib only, no network, no paid calls. Prints ONE compact JSON object on stdout.
Exit: 0 ok | 1 failed | 2 usage.

The user's UI never passes through a generative model: a deck (deck.json) names raw captures, copy per
locale, theme, frames and layouts; pages are generated as HTML and rendered by a headless Chromium-family
browser to the exact pixel size of each target. State lives in the project cwd:
.genmedia/projects/<slug>/launch-graphics/ (deck.json, captures/, plates/, build/), imported assets in
.genmedia/launch-graphics/assets/, deliverables in genmedia-output/<slug>/launch-graphics/.

  tools
      Which renderer exists (Chromium-family browser), whether ffmpeg or sips exist, what each command can do.
  specs [--target <id>...] [--store app-store|play|web|product-hunt|chrome-web-store|ads|email]
      Rows of surfaces.json (pixel size, accepted sizes, counts, byte caps, source URL), `verified_on`,
      `unverified`. A null is a number nobody read from the official page: never fill it from memory.
      `attributions`: third-party material that ships in devices.json [{origin, license, bars, changes}]
      (the status bars and home indicators come from Julien Fovelle's Assets Kit UI, CC BY 4.0): credit it where the project
      credits its sources. A page that used such a bar carries the same rows as proof.json `attributions`.
  init --slug <name> [--name "<App Name>"] [--mode app-store|play|both|universal] [--locale en]...
      Folder tree and a deck skeleton. Never overwrites a deck (answers created:false).
  capture add --slug <s> --id <id> --file <path> [--os ios|android|web|desktop] [--locale tr] [--mockup] [--replace]
      Archive a raw capture untouched under captures/, record sha256, pixel size, alpha flag and
      `fullscreen_match` (nearest known device screen within 1% aspect) in the deck. HEIC, TIFF, AVIF, BMP,
      GIF -> kind "convert_first". The agent sets `statusbar_state` after LOOKING at the capture.
  probe <image>... [--colors]
      Size, format, alpha, bytes, aspect and the nearest known device screen. Header parsing only.
      --colors measures the real colours in-page (needs the browser; large captures are sampled small):
      colors {top_strip, bottom_strip, background (most frequent colour), palette (up to 6 by area,
      near-duplicates merged), accent (most saturated colour on at least about 0.5% of the pixels, or
      null), luminance 0..1, scheme light|dark}. Without a browser the header facts still come back,
      `colors` is null and `colors_status` carries kind "tool_missing". `capture add` stores the same
      block as captures.<id>.colors when a browser exists and never fails without one.
  text --slug <s> [--set <id>] [--full]
      The default answer is compact: totals, `checked`, and `findings` (only slides and locales with
      issues). --full adds `sets` with every line: budgets, character counts, upper-casing.
      Per slide and locale: line and character budgets of the layout, locale-correct upper-casing
      (Turkish i/ı), numbers gate, claims gate, store word lists, price talk, the Play tagline note.
      Google Play's avoid list (#1, best, top, free, download/install/play/try now) is an error on sets
      with a play target and a warning elsewhere. A target's `content_rules` are errors on its set: the App Store
      creative assets list no_price, no_discount, no_url, no_copyright, no_apple_badge (Editors' Choice, App of
      the Day...) and no_other_platform (Android, Google Play...). Any error -> exit 1, kind "check_failed".
  assets import --kind bezel|statusbar|bottombar|font --name <id> --file <path> [--os ios|android]
                [--device phone|tablet] [--screen x,y,w,h] [--screen-radius <px>] [--opaque]
  assets list
      User-owned assets that win over the drawn ones; never stored in the skill (the index keeps the
      file's basename, never its path). A bezel is matched by frame id, a font by family name. A bar is
      matched by bar id (ios, ipad, android, android-tablet, ios-home, ipad-home, android-gesture,
      android-tablet-gesture), else by --os inside the same device class: --device phone (default) or
      tablet, so a phone bar never lands on a tablet frame. SVG files pass a safety check (no script,
      no external reference); the index stores `viewbox: [w, h]`, and a status bar less than 5 times as
      wide as it is tall gets a `note`.
      Imported bars: every paint becomes currentColor and the page sets `color` from the strip (dark
      strip -> white). A status bar is scaled by HEIGHT to the bar height of the frame, its width follows
      the artboard, and it is shown as two halves: the left half pinned to the left screen edge, the
      right half to the right edge, so the gap in the middle flexes. An artboard of exactly the screen's
      point width joins seamlessly; wider (an iPad bar exported at landscape width) or narrower ones
      work too. Shapes that cross the middle of a status-bar artboard (island, camera hole, background)
      are dropped: the frame draws its own cut-out. A bottom bar is scaled by height to the bottom strip
      and centred, so a full-width navigation bar and a bare pill both work. Height always wins: an
      artboard whose aspect implies another bar height is not corrected.
      Order of precedence per bar: an imported asset, then a bar that ships as `svg` in devices.json
      (rendered through the same path; a landscape screen takes its `svg_landscape` when it has one; if
      such a bar declares `svg_includes_time: false` its time is live text), then the glyphs drawn for
      this project. Times: iOS 9:41, Android 9:30 (the clocks the shipped exports carry as outlines).
      A bezel PNG without --screen: the transparent screen hole is detected in-page, with its corner
      radius (the capture is clipped to it; --screen-radius overrides); a bezel without alpha, or an
      alpha PNG whose screen is filled -> kind "no_screen_hole" (pass --opaque --screen). The index
      records `orientation` (portrait or landscape, from the image); a bezel is picked by
      `<frame id>-<orientation>` first, then by the frame id, so `ipad` (landscape) and `ipad-portrait`
      can live side by side. There is no rotation: a bezel of the other orientation leaves the drawn frame and a
      `note`. With --screen an alpha-less bezel is stored as
      `opaque: true` (--opaque forces it for a filled screen inside an alpha PNG): the capture is then
      drawn ABOVE the bezel inside the --screen rectangle, clipped by --screen-radius (pixels of the
      bezel image, default 0). A transparent-hole bezel stays on top of the capture. Imported bezels
      get NO added shadow unless the set or slide says `bezel_shadow: true`.
  screen-quad --slug <s> --plate <id> [--file <path>] [--key magenta|green] [--orientation auto|portrait|landscape] [--write]
      Find the flat chroma screen of a generated scene plate: quad (top-left, top-right, bottom-right,
      bottom-left), island, top_guess, orientation, aspect_estimate (perspective undone with the focal
      length the quad implies), aspect_range (across plausible focal lengths), side_ratio, median_key_luma,
      keyed_share, stray_key_share (key colour away from the screen). The top is the side nearest the
      cut-out, else the highest side; --orientation limits it to the short (portrait) or long (landscape)
      sides. --file registers a new plate under plates/; --write stores the result in the deck.
      Errors: "no_key", "no_quad".
  compose --slug <s> [--set <id>] [--target <id>] [--locale <l>] [--slide <id>] [--jobs 4] [--keep-build] [--full]
      The default answer is compact: rendered, failed_count, warnings_count, seconds, pruned, `failed` in
      full, set_warnings, files [{path, target, locale, slide, warnings: [kinds]}], warnings_by_kind
      {kind: [paths]} and `details`: build/compose-last.json, where the full answer (metrics, warning
      texts, proofs, sizes) is written on every run. --full prints that full answer instead.
      Render every selected page to the exact target size: one browser run per page returns the
      metrics and the PNG. Writes <target>/<locale>/NN-<slide>.png (or .jpg, see `export`) and NN-<slide>.proof.json,
      updates manifest.json. Without --slide the run prunes: in every folder it rendered, NN-*.png or .jpg files WITH a
      sibling proof that this run did not produce (renamed, removed or reordered slides, pages that now
      fail a gate) are deleted with their proof and manifest row and listed as `pruned`; with no filter
      at all, rows and files of sets, targets and locales the deck no longer has go too. With --slide
      nothing is pruned. A render whose export format changed removes the slide's earlier .png or .jpg when
      the old proof names it, --slide included, and lists it under `replaced`. A file without a proof is never touched. Hard gates (exit 1, the page is not delivered): copy_too_long, text_overlaps_device,
      contrast below 3.0, wrong_size, alpha, aspect_mismatch above 15%, jagged_edge, capture_changed, jpeg_over_budget.
      A page that draws a capture through a transform (card-hero-scene 3x, tilted card-flow 2x) is
      supersampled; its capture edges are measured after the shrink and a stepped page renders once more
      at a higher factor before jagged_edge fails it. Warnings on the
      file: contrast 3.0-4.5, fit_scale, gutter, device_share, empty_band, chars_per_line,
      play_tagline_share, seam, safe_crop, aspect_mismatch 8-15%, decor_overlaps_text, bytes_over_cap,
      statusbar_kept_dirty, statusbar_identifies_os, statusbar_os_mismatch, hero_scene_on_play,
      lockup_contrast (card-lockup: the lockup's main colour below 3.0 against the ground behind it),
      lockup_size (card-lockup: the asked width did not fit the card's lockup zone),
      ad_safe_zone (text or lockup inside the strips a placement covers with its own interface: the
      target's `safe_insets`), cutoff_zone (text, lockup, icon or capture inside the zones a surface may
      crop: `safe_insets` on a target with `cutoff_zones`, about 15% per edge on `play-feature`, Apple's art
      safe area on appstore-header, appstore-search and appstore-universal; card layouts lay themselves out
      inside that box, so only an explicit `bleed: true` reaches it),
      text_share (text above the target's `text_share_max`),
      small_text (copy below the target's `min_text_px`: 20 px on og, x-card and github-social; sub and badge type never
      shrink below that floor, so over-long copy fails as copy_too_long instead). Every file reports
      `metrics.min_text_px`, the smallest rendered copy size (headline, sub, badge).
      `set_warnings` (screenshot sets only): adjacent_layout_repeat, no_inverted_slide, span_early (a device-span
      pair among the first three slides of a set with a Play target).
  layers --slug <s> --set <id> --slide <id> [--target <id>] [--locale <l>]
      A page as video layers, for a real screen recording under the drawn frame: the page is rendered
      twice (the first capture hidden, its screen black, then white) and ffmpeg turns the pair into
      video-layers/<target>/<locale>/NN-<slide>.fg.png, everything but the capture with a true alpha
      hole, antialiased corners included. NN-<slide>.layers.json carries the canvas, the hole's
      rectangle (even numbers, one pixel under the frame) and a ready ffmpeg filter. The same hard
      gates as compose apply. Not for card-hero-scene, zoom or slides without a capture. The slide's
      capture should be a frame of the recording, so both share one aspect. Needs a browser and ffmpeg.
  sheet --slug <s> --set <id> [--target <id>] [--locale <l>] [--out <png>]
      Contact sheet: every output large plus its true small size (store about 220 px wide, og/x 400,
      ph-gallery 320, ph-thumbnail 240/80/40, Chrome Web Store screenshots and App Store creative assets 640, promo
      tiles at half size) on a light and a dark strip.
  validate --slug <s>  |  validate --dir <path> --target <id>
      Exact size (or a listed accepted size, or a 2x render where the target lists `scales`, or inside the
      target's `allowed` range: Play's sides and 2:1 cap, Apple's exact 3:2 from 1920x1280 to 3840x2560 on
      appstore-search), the target's formats (a size listed under `size_formats` takes only those: 5244x2950 is
      PNG only on appstore-header and appstore-search), no alpha, a
      JPEG with three components whose content matches its name, byte cap (a JPEG on a target without one:
      surfaces.json `jpeg.working_max_bytes`), min/max count, zero-padded order, proof file present and
      matching. Header parsing only.

Deck rules the script enforces:
  - Paths are relative to the project folder or absolute; a parent component is refused (path_escape).
  - Copy lines are ARRAYS, one string per line; every deck locale on every slide (copy_missing), no
    locale the deck does not list (copy_unused). Card layouts need no headline: a slide with no `copy`
    at all is text-free, `text` reports no copy_missing and checks nothing on it, and the page renders
    the same in every locale. Store slides still need a headline per locale.
  - `lockup: false` on a set or a slide keeps the brand lockup (logo, or icon plus app name) off the
    page; a slide's value wins. Default: on, wherever the layout draws one.
  - `compact: true` on a set or a slide (the slide wins) gives a missing lockup's room to the copy: card-left-title
    and card-flow with caption left centre their text block on the card (12 to 88 percent of the height),
    card-centered starts it at 11 percent and hangs its capture from 47.5 percent, a phone at 0.28 of the width.
    It needs the lockup off (on a set: the set's `lockup: false`). Default off: the lockup's room stays empty.
  - `device_top` on a set or a slide: the top edge of the hung capture as a share of the card height (0 to 0.8):
    the phone on card-left-title (default 0.105), the capture on card-centered (default 0.585, compact 0.475).
  - `theme.badge_style`: "pill" (default) or "text": the badge as a bare eyebrow in the readable accent, tracked
    0.1em, with no pill behind it; its contrast is then measured against the pixels under it.
  - card-lockup is the lockup alone, centred and large, over the set's ground: no copy, no capture. Its slide may
    say `lockup: {width, scrim, shadow}`: width = share of the canvas width (0.1 to 0.8, default 0.35, or less where
    the cutoff box is narrower: about 0.235 on appstore-universal), capped by the zone the layout keeps (inside the
    cutoff box on play-feature and the App Store creative assets); scrim = strength of a soft radial shade
    behind it (0 to 0.8), shadow = a light drop shadow. On a plate ground scrim 0.3 and shadow true are the
    defaults, elsewhere 0 and false. The page scales the lockup to the width, picks dark or light for scrim and
    shadow from the lockup's own main colour, and measures that colour against the ground (lockup_contrast).
  - `emphasis` occurs verbatim, case included, inside one headline line of that locale
    (emphasis_not_in_headline); it is set in the accent colour, adjusted to stay readable.
  - `badge` is one short proof or data point (24 characters); the numbers and claims gates apply to it.
  - The numbers gate is exact on the written form: "4.8" and "4,8" are different facts.numbers entries.
  - `invert: true` swaps ground and text colours (bg <-> fg, bg_alt <-> fg_alt); ignored on plate grounds.
  - `theme.muted` is optional (default: fg_alt pulled toward bg); it colours the lockup of a text-only slide.
  - `bezel_shadow: true` on a set or slide adds a drop shadow to an IMPORTED bezel (default: none).
  - `export: {<target>: {format, scale}}` on a set: how that target is delivered; default PNG at 1x.
    format "jpg" renders the PNG, then the browser encodes it (canvas JPEG, no Python codec) at the highest
    quality from 0.92 down to 0.60 that stays under the target's max_bytes, or under
    surfaces.json `jpeg.working_max_bytes` where the platform states none; nothing fits -> jpeg_over_budget.
    scale 2 renders at twice the pixels on targets that list `scales` (og 2400x1260, x-card 2400x1200):
    the layout, gates and type floor stay in 1x pixels, the canvases and the screenshot double. The proof
    records format, scale and jpeg {quality, max_bytes, budget, png_bytes}. A gradient or strip ground that
    ships as JPEG gets seeded grain of up to 2 levels per channel on the background canvas (JPEG_GRAIN);
    captures, text and decor stay clean, and a PNG keeps the browser's own gradient dither.
  - `frame: "auto"` resolves per target; a set may carry its own `mode`; a slide's `capture` may be a map
    {"ios": id, "android": id, "default": id}; `bleed: true|false` overrides a layout's default.
  - Ad targets (`ad-*`, store "ads") take the capture's own OS for `frame: "auto"` and skip the store word
    lists (a call to action is what an ad is for); numbers and claims still need `facts`. A set that also
    lists a store target keeps the store rules.
  - Layouts: device-bottom, device-top, device-center, two-devices (capture2), zoom (zoom{x,y,w,h}),
    device-span + device-span-end, text-only | card-hero-scene (plate with a quad), card-left-title, card-centered, card-minimal,
    card-browser, card-flow (capture2; connector arrow|none; caption top|left), card-lockup | thumb-icon. Backgrounds:
    solid, gradient, plate, strip.
  - card-flow sets its two captures side by side at one height, before on the left, after on the right,
    frameless unless the slide or set names a frame, with a drawn arrow between them (`connector: "none"`
    leaves a plain gap). Copy and lockup are optional; without them the pair takes the whole card.
    `caption: "left"` sets lockup and copy where card-left-title sets them (same text box, start size and copy
    budget, so a series of left-title cards shares one type size) and contains the pair on the right; the
    default "top" stacks them above the pair, centred.
    `tilt` (degrees, at most 8 either way; a number t turns the pair apart as -t and t, a list [left, right]
    names both) turns the captures about their centres and shrinks the pair until the turned boxes fit.
    Such a page renders at twice the pixels and the browser shrinks it back (2x2 mean with Bayer rounding,
    RGB scanlines deflated in Python): headless Chromium clips a rotated rounded element without
    anti-aliasing. The turned edges are measured (jagged_edge). `layers` refuses a tilted slide.
  - device-span puts one device across the seam of two slides of a `strip` set (span_needs_strip otherwise): it
    owns the capture and shows the device's left half at its right edge; the next slide must be device-span-end
    (span_unpaired otherwise), which shows the right half at its left edge with its own copy and takes no capture,
    frame, bleed or bezel_shadow of its own. The `seam` warning skips that device and still checks the text.
  - Status bars of a phone capture in landscape: Android shows a thinner bar (bars.android.landscape, 24 dp, the
    glyphs at their portrait size), so the portrait table applies with that bar; iOS and the neutral bars are
    `landscape.hidden` (by default UIKit hides the bar on every iPhone in landscape): nothing is added or drawn, a flat bar the
    capture brings (a foreign or dirty one) is covered blank, any other is kept with the usual warning.

Without a browser `compose`, `sheet`, `screen-quad` and bezel hole detection answer
{ok:false, kind:"tool_missing", hint}; every other command works with no tool at all.
Env: GM_BROWSER_BIN, GM_FFMPEG_BIN, GM_SIPS_BIN (binary override; the value "none" disables that tool).
"""
import argparse
import base64
import colorsys
import concurrent.futures
import datetime
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
import threading
import time
import unicodedata
import xml.etree.ElementTree as ET
import zlib

VERSION = "lk1"
SCHEMA = 1
HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_TIMEOUT_S = 60
PNG_SIG = b"\x89PNG\r\n\x1a\n"
MAX_SVG_BYTES = 8 * 1024 * 1024
SHEET_READ_LIMIT_PX = 1568  # above this an image viewer may downscale the sheet: small previews stop being true size
TR_ASCII = str.maketrans("ıİşŞğĞüÜöÖçÇ", "iIsSgGuUoOcC")
TR_LANGS = ("tr", "az")
TR_UPPER = {ord("i"): "\u0130", ord("\u0131"): "I"}
TR_LOWER = {ord("\u0130"): "i", ord("I"): "\u0131"}
RTL_LANGS = ("ar", "he", "fa", "ur")
WIDE_SCRIPT_LANGS = ("ja", "zh", "ko")             # smaller base size, no negative tracking
NO_TRACKING_LANGS = WIDE_SCRIPT_LANGS + RTL_LANGS + ("th", "hi")
MODES = ("app-store", "play", "both", "universal")
MODE_STORES = {"app-store": ("app-store",), "play": ("play",), "both": ("app-store", "play"),
               "universal": ("app-store", "play")}
CAPTURE_OS = ("ios", "android", "web", "desktop")
BAR_STATES = ("missing", "empty", "dirty", "clean")
BAR_POLICIES = ("auto", "keep", "none", "mask")
BACKGROUNDS = ("solid", "gradient", "plate", "strip")
CONNECTORS = ("arrow", "none")
CAPTIONS = ("top", "left")         # card-flow: lockup and copy above the pair, or on the left as card-left-title sets them
TILT_MAX = 8.0          # degrees either way; beyond that the pair crowds the arrow and the card's edges
KEYS = ("magenta", "green")
THEME_COLORS = ("bg", "bg_alt", "fg", "fg_alt", "accent", "muted")
THEME_REQUIRED = ("bg", "bg_alt", "fg", "fg_alt", "accent")     # muted is optional: derived from fg_alt when absent
CAPTURE_EXT = {"png": ".png", "jpeg": ".jpg", "webp": ".webp"}
CONVERT_EXT = (".heic", ".heif", ".avif", ".tif", ".tiff", ".bmp", ".gif", ".psd", ".pdf")
FONT_EXT = {".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf"}
ASSET_KINDS = ("bezel", "statusbar", "bottombar", "font")
ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
LOCALE_RE = re.compile(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")
SYSTEM_STACK = '-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
BROWSER_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge",
                 "microsoft-edge", "brave-browser")
BROWSER_PATHS = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium",
                 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                 "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                 "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                 "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe")
MISSING_HINT = ("no Chromium-family browser: install Chrome, Chromium, Edge or Brave, or point GM_BROWSER_BIN at one. "
                "Until then deliver the deck, the copy check and the capture list and say that nothing was rendered")
CLEAN_CAPTURE_TIP = ("retake the capture with a clean bar. iOS simulator: xcrun simctl status_bar booted override "
                     "--time \"9:41\" --dataNetwork wifi --wifiMode active --wifiBars 3 --cellularMode active "
                     "--cellularBars 4 --batteryState discharging --batteryLevel 100 --operatorName ''; crop the bar "
                     "off and set statusbar_state to missing; or, with the user's yes, set statusbar to mask")

# Layout catalogue. `kinds` = target kinds the layout can render on; chars are per authored line and only warn,
# the in-page fit pass is the hard gate. `bleed` = the device may run off the canvas by default.
# `headline` = a headline is REQUIRED: true on store slides, false on cards, which may run text-free (a card
# without `copy`, or with an empty headline, renders no text at all and serves every locale as one file).
# `flow` = two captures side by side at one height, frameless unless a frame is named, joined by a connector.
# `span` = one device across the seam of two neighbouring slides of a strip set: `start` owns the capture and shows
# the left half, the `end` slide right after it shows the right half; each carries its own copy.
LAYOUTS = {
    "device-bottom": {"kinds": ("screenshot",), "captures": 1, "headline": True, "lines": 3, "chars": 18,
                      "sub_lines": 2, "sub_chars": 40, "bleed": True},
    "device-top": {"kinds": ("screenshot",), "captures": 1, "headline": True, "lines": 3, "chars": 18,
                   "sub_lines": 2, "sub_chars": 40, "bleed": True},
    "device-center": {"kinds": ("screenshot",), "captures": 1, "headline": True, "lines": 2, "chars": 20,
                      "sub_lines": 2, "sub_chars": 40, "bleed": False},
    "two-devices": {"kinds": ("screenshot",), "captures": 2, "headline": True, "lines": 3, "chars": 18,
                    "sub_lines": 2, "sub_chars": 40, "bleed": True},
    "zoom": {"kinds": ("screenshot",), "captures": 1, "headline": True, "lines": 3, "chars": 18,
             "sub_lines": 2, "sub_chars": 40, "bleed": False, "zoom": True},
    "device-span": {"kinds": ("screenshot",), "captures": 1, "headline": True, "lines": 3, "chars": 18,
                    "sub_lines": 2, "sub_chars": 40, "bleed": True, "span": "start"},
    "device-span-end": {"kinds": ("screenshot",), "captures": 0, "headline": True, "lines": 3, "chars": 18,
                        "sub_lines": 2, "sub_chars": 40, "bleed": True, "span": "end"},
    "text-only": {"kinds": ("screenshot",), "captures": 0, "headline": True, "lines": 4, "chars": 13,
                  "sub_lines": 3, "sub_chars": 36, "bleed": False},
    "card-hero-scene": {"kinds": ("card",), "captures": 1, "headline": False, "lines": 3, "chars": 14,
                        "sub_lines": 2, "sub_chars": 36, "bleed": False, "plate": True},
    "card-left-title": {"kinds": ("card",), "captures": 1, "headline": False, "lines": 3, "chars": 14,
                        "sub_lines": 3, "sub_chars": 36, "bleed": True},
    "card-centered": {"kinds": ("card",), "captures": (0, 1), "headline": False, "lines": 2, "chars": 24,
                      "sub_lines": 2, "sub_chars": 56, "bleed": True},
    "card-minimal": {"kinds": ("card",), "captures": 0, "headline": False, "lines": 3, "chars": 20,
                     "sub_lines": 2, "sub_chars": 56, "bleed": False},
    "card-browser": {"kinds": ("card",), "captures": 1, "headline": False, "lines": 2, "chars": 34,
                     "sub_lines": 1, "sub_chars": 60, "bleed": False},
    "card-flow": {"kinds": ("card",), "captures": 2, "headline": False, "lines": 2, "chars": 28,
                  "sub_lines": 1, "sub_chars": 60, "bleed": False, "flow": True},
    "card-lockup": {"kinds": ("card",), "captures": 0, "headline": False, "lines": 0, "chars": 0,
                    "sub_lines": 0, "sub_chars": 0, "bleed": False, "lockup": True},
    "thumb-icon": {"kinds": ("square",), "captures": 0, "headline": False, "lines": 0, "chars": 0,
                   "sub_lines": 0, "sub_chars": 0, "bleed": False},
}
FIT_FLOOR = 0.72
FIT_STEP = 0.02
# `compact: true` on a page without a lockup: the room the lockup would take goes to the copy. card-left-title (and
# card-flow with caption left) centres its text block on the card, 12 to 88 percent of the height; card-centered starts
# it at 11 percent and hangs its capture higher, a phone at the left-title phone's scale, so a series mixing both
# layouts shares one phone size (the email cards of 2026-10-13). The phone's width share, then its top share.
COMPACT_CENTERED_PHONE = (0.28, 0.475)
# `device_top`: the top edge of the hung capture as a share of the card height (card-left-title phone, card-centered)
DEVICE_TOP_LAYOUTS = ("card-left-title", "card-centered")
DEVICE_TOP_RANGE = (0.0, 0.8)
# theme.badge_style: "pill" (default) sets the badge on an accent-tinted pill; "text" sets it as a bare, tracked
# eyebrow in the readable accent, measured against the pixels behind it like the headline
BADGE_STYLES = ("pill", "text")
# card-lockup: the lockup as the subject. Width as a share of the canvas width; a plate ground gets a soft scrim and
# a light shadow by default so a white mark holds over a bright horizon (the composition approved on 2026-09-22).
LOCKUP_KEYS = ("width", "scrim", "shadow")
LOCKUP_WIDTH, LOCKUP_WIDTH_RANGE = 0.35, (0.10, 0.80)
LOCKUP_SCRIM_PLATE, LOCKUP_SCRIM_MAX = 0.3, 0.8
# card-hero-scene: the shade under the text holds over the text block, then fades out with an eased curve over this
# share of the canvas width, under the device if it reaches it (see hero_scrim).
HERO_SCRIM_DIM, HERO_SCRIM_FADE = 0.62, 0.40
EXPORT_KEYS = ("format", "scale")
# JPEG export: the quality search starts at Chrome's own default and stops at a floor below which text edges
# on flat grounds ring visibly. Whole percent steps; the first quality that fits the byte budget from the top wins.
JPEG_QUALITY_MAX = 92
JPEG_QUALITY_FLOOR = 60
# Chromium already dithers a canvas gradient, so a PNG shows no banding (measured on 2026-09-23 with Chrome 153:
# single-pixel runs on every target). JPEG smooths that dither away and the rings come back, so a gradient ground
# that ships as JPEG gets seeded grain of up to this many levels of 255, on the background canvas only (#67).
JPEG_GRAIN = 2

# Google Play's avoid list for listing graphics (support.google.com/googleplay/android-developer/answer/9866151,
# read 2026-09-20): ranking, price and call-to-action talk. Hard errors on play-* targets, warnings elsewhere.
PLAY_HARD_WORDS = ("#1", "best", "top", "free", "download now", "install now", "play now", "try now")
# The rest of that list and close kin: a warning on every target.
PROMO_WORDS = ("new", "discount", "sale", "million downloads", "no. 1", "number one", "top rated", "% off", "cheapest",
               "limited time", "app of the year")
# The same talk in other languages: warnings only, the stores publish no word list for them.
PROMO_WORDS_OTHER = ("en iyi", "1 numara", "bir numara", "ücretsiz", "bedava", "indirim", "hemen indir", "şimdi indir",
                     "kostenlos", "gratis", "rabatt", "gratuit", "meilleur", "mejor", "descuento", "grátis", "melhor")
# App Review 2.3.7 keeps prices out of screenshots; Play's list names price talk too.
PRICE_RE = re.compile(r"[$\u20ac\u00a3\u20ba\u00a5\u20b9]\s?\d|\d[\d.,]*\s?(?:[$\u20ac\u00a3\u20ba\u00a5\u20b9]|(?:TL|USD|EUR|GBP|TRY)\b)")
# Words that state a fact about reputation: allowed only when facts.claims carries the same word.
CLAIM_WORDS = (
    "award", "winner", "editor", "featured", "trusted", "certified", "official", "guarantee", "million", "billion",
    "rated", "stars", "reviews", "ödül", "editör", "güvenilen", "güvendiği", "sertifika", "resmi", "garanti",
    "milyon", "milyar", "yıldız", "puan")
# Content rules a surfaces.json row can list under `content_rules`; each is an error in `text` on such a target. Apple's
# creative assets (developer.apple.com/app-store/asset-best-practices, read 2026-10-07) list all six: no prices,
# discounts, URLs or copyright symbols, no Apple-designated recognitions, no logos or mentions of other platforms.
CONTENT_RULES = ("no_price", "no_discount", "no_url", "no_copyright", "no_apple_badge", "no_other_platform")
DISCOUNT_WORDS = ("discount", "% off", "coupon", "promo code", "indirim", "kupon", "rabatt", "descuento", "réduction")
URL_RE = re.compile(r"(?:https?://|www\.)\S+|(?<![\w@.-])[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.(?:com|net|org|io|app|dev|ai|co|"
                    r"me|tv|gg|xyz|so|sh|ly|to|tr|de|uk|fr|es|it|nl|eu|us)\b", re.IGNORECASE)
COPYRIGHT_RE = re.compile("[©℗]")
# matched on the locale-lower-cased line; apostrophes are folded to ' first
APPLE_BADGE_RE = re.compile(r"(?<!\w)(?:editors?'?s?'?\s+choice|(?:app|game)\s+of\s+the\s+day|apple\s+design\s+awards?|"
                            r"app\s+store\s+awards?|günün\s+(?:uygulaması|oyunu)|editör(?:ün|lerin)\s+seçimi)(?!\w)")
OTHER_PLATFORM_WORDS = ("android", "google play", "play store", "galaxy store", "appgallery", "amazon appstore", "microsoft store")


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


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text):
    """ASCII lower-case; Turkish letters are transliterated before anything is stripped."""
    folded = unicodedata.normalize("NFKD", str(text or "").translate(TR_ASCII))
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")[:48].strip("-")


def need_slug(value):
    text = slugify(value)
    if not text:
        raise usage("--slug %r has no letters or digits" % value)
    return text


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


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


def write_json_atomic(path, value):
    write_atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read_json(path, what):
    try:
        with open(path, "rb") as handle:
            value = json.loads(handle.read().decode("utf-8-sig"))
    except OSError as exc:
        raise Fail("not_found", "%s: cannot read %s (%s)" % (what, path, exc.strerror or exc))
    except (ValueError, UnicodeDecodeError) as exc:
        raise Fail("invalid_json", "%s: %s is not valid JSON (%s)" % (what, path, exc))
    if not isinstance(value, dict):
        raise Fail("invalid_json", "%s: %s must hold one JSON object" % (what, path))
    return value


_DATA = {}


def data_file(name):
    if name not in _DATA:
        _DATA[name] = read_json(os.path.join(HERE, name), name)
    return _DATA[name]


def surfaces():
    return data_file("surfaces.json")


def devices():
    return data_file("devices.json")


# ----------------------------------------------------------------------------------------------- image headers

def _jpeg_size(handle):
    handle.seek(2)
    while True:
        marker = handle.read(2)
        if len(marker) < 2 or marker[0] != 0xFF:
            return None, None, None
        if marker[1] == 0xFF:
            handle.seek(-1, 1)
            continue
        if marker[1] in (0xD8, 0x01) or 0xD0 <= marker[1] <= 0xD7:
            continue
        seg = handle.read(2)
        if len(seg) < 2:
            return None, None, None
        length = struct.unpack(">H", seg)[0]
        if 0xC0 <= marker[1] <= 0xCF and marker[1] not in (0xC4, 0xC8, 0xCC):
            frame = handle.read(6)
            height, width = struct.unpack(">HH", frame[1:5])
            return width, height, frame[5] if len(frame) == 6 else None
        handle.seek(length - 2, 1)


def probe_image(path):
    """Format, pixel size, alpha flag, PNG colour type and JPEG component count from the file header. No tool, no decode."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as handle:
            head = handle.read(64)
            fmt, width, height, alpha, color_type, channels = None, None, None, False, None, None
            if head[:8] == PNG_SIG and head[12:16] == b"IHDR":
                fmt = "png"
                width, height = struct.unpack(">II", head[16:24])
                color_type = head[25]
                alpha = color_type in (4, 6)
                if not alpha:                      # a palette or RGB file can still carry a tRNS chunk
                    handle.seek(8)
                    while True:
                        chunk = handle.read(8)
                        if len(chunk) < 8:
                            break
                        length, ctype = struct.unpack(">I4s", chunk)
                        if ctype == b"tRNS":
                            alpha = True
                            break
                        if ctype in (b"IDAT", b"IEND"):
                            break
                        handle.seek(length + 4, 1)
            elif head[:4] == b"RIFF" and head[8:12] == b"WEBP":
                fmt, kind = "webp", head[12:16]
                if kind == b"VP8X":
                    alpha = bool(head[20] & 0x10)
                    width = 1 + int.from_bytes(head[24:27], "little")
                    height = 1 + int.from_bytes(head[27:30], "little")
                elif kind == b"VP8 ":
                    width, height = (v & 0x3FFF for v in struct.unpack("<HH", head[26:30]))
                elif kind == b"VP8L":
                    bits = int.from_bytes(head[21:25], "little")
                    width, height = 1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF)
                    alpha = bool((bits >> 28) & 1)
            elif head[:2] == b"\xff\xd8":
                fmt = "jpeg"
                width, height, channels = _jpeg_size(handle)
    except OSError as exc:
        raise Fail("not_found", "cannot read %s (%s)" % (path, exc.strerror or exc))
    if not fmt or not width or not height:
        ext = os.path.splitext(path)[1].lower()
        if ext in CONVERT_EXT:
            raise Fail("convert_first", "%s is %s: only PNG, JPEG and WebP are composed" % (path, ext[1:].upper()),
                       hint="convert a copy first, the original stays untouched: sips -s format png <in> --out "
                            "<out.png> (macOS) or ffmpeg -i <in> <out.png>")
        raise Fail("unsupported", "%s is not a PNG, JPEG or WebP file this tool can measure" % path,
                   hint="HEIC, TIFF, AVIF or BMP: convert a copy to PNG first (sips or ffmpeg)")
    return {"path": path, "format": fmt, "width": int(width), "height": int(height), "alpha": bool(alpha),
            "color_type": color_type, "channels": channels, "bytes": size, "aspect": round(width / float(height), 4)}


def png_complete(path):
    try:
        with open(path, "rb") as handle:
            if handle.read(8) != PNG_SIG:
                return False
            handle.seek(-12, 2)
            return handle.read(8) == b"\x00\x00\x00\x00IEND"
    except OSError:
        return False


def _png_chunk(tag, body):
    return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xffffffff)


def crop_png_height(path, height):
    """Keep the top `height` rows of a non-interlaced PNG, in place. A filtered row refers only to the rows above
    it, so cutting from the bottom needs no unfiltering. -> True when rows were cut."""
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:8] != PNG_SIG:
        raise Fail("tool_failed", "%s is not a PNG" % os.path.basename(path))
    pos, ihdr, idat, before, after = 8, None, [], [], []
    while pos + 8 <= len(data):
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        tag, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + size]
        pos += 12 + size
        if tag == b"IHDR":
            ihdr = body
        elif tag == b"IDAT":
            idat.append(body)
        elif tag == b"IEND":
            break
        else:
            (after if idat else before).append((tag, body))
    if not ihdr or not idat:
        raise Fail("tool_failed", "%s has no image data" % os.path.basename(path))
    width, rows, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", ihdr[:13])
    if height >= rows:
        return False
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color)
    if interlace or not channels:
        raise Fail("tool_failed", "%s is interlaced or of an unknown colour type; cannot cut it" % os.path.basename(path))
    need = (1 + (width * channels * depth + 7) // 8) * height
    try:
        raw = zlib.decompressobj().decompress(b"".join(idat), need)
    except zlib.error as exc:
        raise Fail("tool_failed", "%s has broken image data: %s" % (os.path.basename(path), exc))
    if len(raw) < need:
        raise Fail("tool_failed", "%s holds fewer rows than its header says" % os.path.basename(path))
    out = [PNG_SIG, _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, depth, color, compression, filtering, 0))]
    out += [_png_chunk(tag, body) for tag, body in before]
    out.append(_png_chunk(b"IDAT", zlib.compress(raw, 6)))
    out += [_png_chunk(tag, body) for tag, body in after]
    out.append(_png_chunk(b"IEND", b""))
    write_atomic(path, b"".join(out))
    return True


def nearest_screen(width, height):
    """Nearest known full-screen size (either orientation). `match` only within 1% of the aspect."""
    best = None
    for os_name, sizes in devices()["screens"].items():
        for sw, sh in sizes:
            for w, h in ((sw, sh), (sh, sw)):
                diff = abs(width / float(height) - w / float(h)) / (w / float(h))
                if best is None or diff < best[0] or (diff == best[0] and (w, h) == (width, height)):
                    best = (diff, os_name, w, h)
                if (w, h) == (width, height):
                    return {"os": os_name, "size": [w, h], "exact": True, "aspect_diff": 0.0, "match": True}
    if best is None:
        return {"os": None, "size": None, "exact": False, "aspect_diff": None, "match": False}
    diff, os_name, w, h = best
    return {"os": os_name, "size": [w, h], "exact": False, "aspect_diff": round(diff, 4), "match": diff <= 0.01}


def data_uri(path, mime=None):
    if mime is None:
        ext = os.path.splitext(path)[1].lower()
        mime = FONT_EXT.get(ext) or {".svg": "image/svg+xml"}.get(ext)
        if mime is None:
            mime = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}[probe_image(path)["format"]]
    with open(path, "rb") as handle:
        return "data:%s;base64,%s" % (mime, base64.b64encode(handle.read()).decode("ascii"))


# ----------------------------------------------------------------------------------------------- colour

def parse_hex(value):
    text = str(value or "").strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", text):
        return None
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def luminance(rgb):
    def channel(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(first, second):
    hi, lo = sorted((luminance(first), luminance(second)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def mix(first, second, share):
    return tuple(a + (b - a) * share for a, b in zip(first, second))


def hue_shift(rgb, degrees):
    h, l, s = colorsys.rgb_to_hls(*(v / 255.0 for v in rgb))
    return tuple(v * 255.0 for v in colorsys.hls_to_rgb((h + degrees / 360.0) % 1.0, l, s))


# ----------------------------------------------------------------------------------------------- project

def project_dir(slug):
    return os.path.join(".genmedia", "projects", slug, "launch-graphics")


def deck_path(slug):
    return os.path.join(project_dir(slug), "deck.json")


def output_dir(slug):
    return os.path.join("genmedia-output", slug, "launch-graphics")


def assets_dir():
    return os.path.join(".genmedia", "launch-graphics", "assets")


def safe_relative(value):
    """A deck path is relative to the project folder or absolute; a relative path never climbs out."""
    text = str(value)
    if os.path.isabs(text):
        return True
    parts = re.split(r"[\\/]+", text)
    return bool(text.strip()) and os.pardir not in parts


def resolve_path(slug, value):
    text = str(value)
    return text if os.path.isabs(text) else os.path.join(project_dir(slug), *re.split(r"[\\/]+", text))


def load_deck(slug):
    path = deck_path(slug)
    if not os.path.isfile(path):
        raise Fail("no_deck", "no deck at %s" % path, hint="run init --slug %s first" % slug)
    deck = read_json(path, "deck")
    return deck


def save_deck(slug, deck):
    write_json_atomic(deck_path(slug), deck)


def deck_hash(slug):
    return sha256_file(deck_path(slug))


# ----------------------------------------------------------------------------------------------- deck validation

class Problems(object):
    def __init__(self):
        self.rows = []

    def add(self, where, message, code="deck_invalid"):
        self.rows.append({"where": where, "code": code, "message": message})

    def __bool__(self):
        return bool(self.rows)

    __nonzero__ = __bool__


def _is_num(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _known(value, mapping):
    """Membership that survives a list or an object where the deck should hold a string."""
    return isinstance(value, str) and value in mapping


def _check_file(problems, slug, where, value, exts=None, must_exist=True):
    if not isinstance(value, str) or not value.strip():
        problems.add(where, "must be a file path (relative to the launch-graphics project folder, or absolute)")
        return None
    if not safe_relative(value):
        problems.add(where, "%r climbs out of the project folder: parent components are not allowed" % value,
                     "path_escape")
        return None
    path = resolve_path(slug, value)
    if exts and os.path.splitext(value)[1].lower() not in exts:
        problems.add(where, "%r must end in one of %s" % (value, ", ".join(exts)))
        return None
    if must_exist and not os.path.isfile(path):
        problems.add(where, "%s does not exist" % path, "file_missing")
        return None
    return path


def target_kind(target_id):
    return surfaces()["targets"][target_id].get("kind", "card")


def set_mode(deck, one_set):
    return one_set.get("mode") or deck.get("mode")


def export_of(one_set, target_id):
    """How a set delivers one target: `export: {<target>: {format, scale}}`, default PNG at 1x."""
    item = (one_set.get("export") or {}).get(target_id) or {}
    return {"format": item.get("format") or "png", "scale": int(item.get("scale") or 1)}


def byte_budget(target, fmt):
    """-> (bytes, source) a file of this format must stay under, or (None, None). A JPEG on a target whose
    platform states no cap takes the skill's working limit (surfaces.json `jpeg.working_max_bytes`)."""
    if target.get("max_bytes"):
        return target["max_bytes"], "max_bytes"
    if fmt in ("jpg", "jpeg"):
        return surfaces()["jpeg"]["working_max_bytes"], "jpeg.working_max_bytes"
    return None, None


def text_free(slide):
    """True when a slide renders no copy in any locale: no `copy` at all, or every locale empty."""
    entries = (slide.get("copy") or {}).values()
    return not any(entry.get("headline") or entry.get("sub") or entry.get("badge")
                   for entry in entries if isinstance(entry, dict))


def lockup_wanted(one_set, slide):
    """`lockup: false` on the slide, else on the set, keeps the brand lockup off the page (default: on).
    A card-lockup slide's object form counts as on."""
    for source in (slide, one_set):
        value = source.get("lockup")
        if value is not None:
            return value if isinstance(value, bool) else True
    return True


def compact_layout(slide):
    """The layouts whose text block moves into a missing lockup's room under `compact: true`."""
    layout = slide.get("layout")
    return layout in ("card-left-title", "card-centered") or (layout == "card-flow" and slide.get("caption") == "left")


def compact_wanted(one_set, slide):
    """`compact` on the slide, else on the set (default off). It acts only where the page draws no lockup."""
    value = slide.get("compact")
    return bool(one_set.get("compact") if value is None else value)


def device_top_of(one_set, slide):
    """`device_top` on the slide, else on the set, else None: the layout's own top."""
    value = slide.get("device_top")
    return one_set.get("device_top") if value is None else value


def _check_device_top(problems, where, value):
    low, high = DEVICE_TOP_RANGE
    if value is not None and not (_is_num(value) and low <= value <= high):
        problems.add(where + ".device_top", "must be a share of the card height between %g and %g: where the top edge of "
                     "the hung capture sits" % (low, high))


def lockup_style(slide, background):
    """Width share, scrim and shadow of a card-lockup slide. A plate ground gets a soft scrim and a shadow by default."""
    value = slide.get("lockup")
    given = value if isinstance(value, dict) else {}
    on_plate = background.get("kind") == "plate" or (background.get("kind") == "strip" and bool(background.get("plate")))
    return {"width": float(given.get("width", LOCKUP_WIDTH)),
            "scrim": float(given.get("scrim", LOCKUP_SCRIM_PLATE if on_plate else 0.0)),
            "shadow": bool(given.get("shadow", on_plate))}


def copy_spec(slide):
    """The layout entry whose copy budget binds this slide. A card-flow with `caption: "left"` sets its copy in
    card-left-title's text box at card-left-title's size, so it takes that budget too."""
    spec = LAYOUTS[slide["layout"]]
    if spec.get("flow") and slide.get("caption") == "left":
        return dict(spec, **{key: LAYOUTS["card-left-title"][key] for key in ("lines", "chars", "sub_lines", "sub_chars")})
    return spec


def validate_copy(problems, where, copy, locales, spec, needs_copy):
    if not needs_copy and (copy is None or copy == {}):      # a layout that takes no headline may run text-free
        return
    if not isinstance(copy, dict) or not copy:
        problems.add(where + ".copy", "must map every deck locale to {headline, sub, emphasis, badge}", "copy_missing")
        return
    for locale in locales:
        if locale not in copy:
            problems.add("%s.copy.%s" % (where, locale), "locale %r has no copy on this slide" % locale, "copy_missing")
    for locale, entry in copy.items():
        spot = "%s.copy.%s" % (where, locale)
        if locale not in locales:
            problems.add(spot, "locale %r is not in deck.locales: no target renders it" % locale, "copy_unused")
            continue
        if not isinstance(entry, dict):
            problems.add(spot, "must be an object with headline, sub, emphasis, badge")
            continue
        for key in entry:
            if key not in ("headline", "sub", "emphasis", "badge"):
                problems.add("%s.%s" % (spot, key), "unknown copy field (known: headline, sub, emphasis, badge)")
        for key, required in (("headline", spec["headline"]), ("sub", False)):
            lines = entry.get(key)
            if lines is None or lines == []:
                if required:
                    problems.add("%s.%s" % (spot, key), "is required: an ARRAY of lines, the author decides the breaks")
                continue
            if not isinstance(lines, list) or any(not isinstance(s, str) or not s.strip() for s in lines):
                problems.add("%s.%s" % (spot, key), "must be an array of non-empty strings, one per line")
        emphasis = entry.get("emphasis")
        if emphasis is not None:
            joined = " ".join(s for s in (entry.get("headline") or []) if isinstance(s, str))
            if not isinstance(emphasis, str) or not emphasis.strip():
                problems.add(spot + ".emphasis", "must be a string or null")
            elif not any(emphasis in s for s in (entry.get("headline") or []) if isinstance(s, str)):
                problems.add(spot + ".emphasis", "%r does not occur verbatim inside one headline line of this locale "
                             "(%r); it is matched exactly, including case" % (emphasis, joined), "emphasis_not_in_headline")
        badge = entry.get("badge")
        if badge is not None and (not isinstance(badge, str) or not badge.strip()):
            problems.add(spot + ".badge", "must be a string or null")


def validate_deck(deck, slug, files=True):
    """Every problem with its exact place. `files=False` skips the existence checks (unit tests, init)."""
    problems = Problems()
    targets = surfaces()["targets"]
    frames = devices()["frames"]
    if deck.get("schema") != SCHEMA:
        problems.add("schema", "is %r, this script reads schema %d" % (deck.get("schema"), SCHEMA), "deck_schema")
        return problems
    if deck.get("slug") != slug:
        problems.add("slug", "is %r but the deck lives in the project folder %r" % (deck.get("slug"), slug))
    if deck.get("mode") not in MODES:
        problems.add("mode", "must be one of %s, got %r" % (", ".join(MODES), deck.get("mode")))
    app = deck.get("app")
    if not isinstance(app, dict) or not isinstance(app.get("name"), str) or not app["name"].strip():
        problems.add("app.name", "must be the app's display name")
        app = {}
    for key in ("icon", "logo"):
        if app.get(key) is not None:
            _check_file(problems, slug, "app." + key, app[key], (".png", ".jpg", ".jpeg", ".webp", ".svg"), files)
    theme = deck.get("theme")
    if not isinstance(theme, dict):
        problems.add("theme", "must be an object with %s and font" % ", ".join(THEME_COLORS))
        theme = {}
    for key in THEME_COLORS:
        if key not in THEME_REQUIRED and theme.get(key) is None:
            continue
        if parse_hex(theme.get(key)) is None:
            problems.add("theme." + key, "must be a hex colour like #0f172a, got %r" % (theme.get(key),))
    font = theme.get("font") or {}
    if not isinstance(font, dict) or not isinstance(font.get("family", "system"), str):
        problems.add("theme.font", "must be {family, files, weight_headline, weight_body}")
        font = {}
    for index, item in enumerate(font.get("files") or []):
        _check_file(problems, slug, "theme.font.files[%d]" % index, item, tuple(FONT_EXT), files)
    for key in ("weight_headline", "weight_body"):
        value = font.get(key)
        if value is not None and not (isinstance(value, int) and 100 <= value <= 900):
            problems.add("theme.font." + key, "must be a weight between 100 and 900, got %r" % (value,))
    if theme.get("badge_style") is not None and theme["badge_style"] not in BADGE_STYLES:
        problems.add("theme.badge_style", "must be %s or absent (default pill), got %r"
                     % (" or ".join(BADGE_STYLES), theme["badge_style"]))
    locales = deck.get("locales")
    if not isinstance(locales, list) or not locales or any(not isinstance(l, str) or not LOCALE_RE.fullmatch(l) for l in locales):
        problems.add("locales", "must be a non-empty list of locale codes such as en, tr, pt-BR")
        locales = []
    if len(set(locales)) != len(locales):
        problems.add("locales", "lists a locale twice")
    if locales and deck.get("default_locale") not in locales:
        problems.add("default_locale", "%r is not in locales" % (deck.get("default_locale"),))
    for locale in deck.get("rtl_locales") or []:
        if locale not in locales:
            problems.add("rtl_locales", "%r is not in locales" % (locale,))
    facts = deck.get("facts") or {}
    if not isinstance(facts, dict) or not isinstance(facts.get("numbers", []), list) or not isinstance(facts.get("claims", []), list):
        problems.add("facts", "must be {numbers: [...], claims: [...]}")

    captures = deck.get("captures")
    if not isinstance(captures, dict):
        problems.add("captures", "must be an object keyed by capture id")
        captures = {}
    for cid, cap in captures.items():
        where = "captures.%s" % cid
        if not ID_RE.fullmatch(cid):
            problems.add(where, "capture ids are lower-case letters, digits and hyphens")
        if not isinstance(cap, dict):
            problems.add(where, "must be an object")
            continue
        _check_file(problems, slug, where + ".file", cap.get("file"), (".png", ".jpg", ".jpeg", ".webp"), files)
        if cap.get("os") not in CAPTURE_OS:
            problems.add(where + ".os", "must be one of %s, got %r" % (", ".join(CAPTURE_OS), cap.get("os")))
        if cap.get("statusbar_state", "missing") not in BAR_STATES:
            problems.add(where + ".statusbar_state", "must be one of %s (set it after looking at the capture)"
                         % ", ".join(BAR_STATES))
        if cap.get("statusbar", "auto") not in BAR_POLICIES:
            problems.add(where + ".statusbar", "must be one of %s" % ", ".join(BAR_POLICIES))
        if not isinstance(cap.get("mockup", False), bool):
            problems.add(where + ".mockup", "must be true or false")
        by_locale = cap.get("by_locale") or {}
        if not isinstance(by_locale, dict):
            problems.add(where + ".by_locale", "must map a locale to a file")
            by_locale = {}
        for locale, item in by_locale.items():
            if locale not in locales:
                problems.add("%s.by_locale.%s" % (where, locale), "locale %r is not in deck.locales" % locale)
            _check_file(problems, slug, "%s.by_locale.%s" % (where, locale), item, (".png", ".jpg", ".jpeg", ".webp"), files)

    plates = deck.get("plates") or {}
    if not isinstance(plates, dict):
        problems.add("plates", "must be an object keyed by plate id")
        plates = {}
    for pid, plate in plates.items():
        where = "plates.%s" % pid
        if not isinstance(plate, dict):
            problems.add(where, "must be an object")
            continue
        _check_file(problems, slug, where + ".file", plate.get("file"), (".png", ".jpg", ".jpeg", ".webp"), files)
        if plate.get("key") not in KEYS + (None,):
            problems.add(where + ".key", "must be magenta, green or null")
        quad = plate.get("quad")
        if quad is not None and not (isinstance(quad, list) and len(quad) == 4 and all(
                isinstance(p, list) and len(p) == 2 and all(_is_num(v) for v in p) for p in quad)):
            problems.add(where + ".quad", "must be null or four [x, y] points: top-left, top-right, bottom-right, bottom-left")
    decor = deck.get("decor") or {}
    if not isinstance(decor, dict):
        problems.add("decor", "must be an object keyed by decor id")
        decor = {}
    for did, item in decor.items():
        if not isinstance(item, dict):
            problems.add("decor.%s" % did, "must be an object with file")
            continue
        _check_file(problems, slug, "decor.%s.file" % did, item.get("file"), (".png", ".webp", ".jpg", ".jpeg"), files)

    sets = deck.get("sets")
    if not isinstance(sets, list) or not sets:
        problems.add("sets", "is empty: add at least one set with targets and slides")
        return problems
    seen_sets = set()
    for s_index, one in enumerate(sets):
        if not isinstance(one, dict):
            problems.add("sets[%d]" % s_index, "must be an object")
            continue
        sid = one.get("id")
        where = "sets[%d] %r" % (s_index, sid)
        if not isinstance(sid, str) or not ID_RE.fullmatch(sid):
            problems.add(where + ".id", "set ids are lower-case letters, digits and hyphens")
        elif sid in seen_sets:
            problems.add(where + ".id", "duplicate set id")
        seen_sets.add(sid)
        mode = one.get("mode") or deck.get("mode")
        if one.get("mode") is not None and one["mode"] not in MODES:
            problems.add(where + ".mode", "must be one of %s" % ", ".join(MODES))
            mode = deck.get("mode")
        wanted = one.get("targets")
        if not isinstance(wanted, list) or not wanted:
            problems.add(where + ".targets", "must be a non-empty list of target ids (see specs)")
            wanted = []
        kinds = set()
        wanted = [tid for tid in wanted if isinstance(tid, str)] if all(isinstance(t, str) for t in wanted) else []
        if not wanted and one.get("targets"):
            problems.add(where + ".targets", "every target must be a string id")
        for tid in wanted:
            if tid not in targets:
                problems.add(where + ".targets", "unknown target %r (known: %s)" % (tid, ", ".join(sorted(targets))))
                continue
            kinds.add(targets[tid].get("kind"))
            store = targets[tid]["store"]
            if targets[tid].get("kind") == "screenshot" and store in ("app-store", "play") and mode in MODE_STORES and store not in MODE_STORES[mode]:
                problems.add(where + ".targets", "target %r belongs to %s but the mode is %r" % (tid, store, mode),
                             "mode_target_mismatch")
        if len(set(wanted)) != len(wanted):
            problems.add(where + ".targets", "lists a target twice")
        orientation = one.get("orientation", "portrait")
        if orientation not in ("portrait", "landscape"):
            problems.add(where + ".orientation", "must be portrait or landscape")
        elif orientation == "landscape":
            for tid in wanted:
                if tid in targets and not targets[tid].get("orientation_swappable"):
                    problems.add(where + ".orientation", "target %r has a fixed orientation" % tid)
        if one.get("frame", "auto") != "auto" and not _known(one.get("frame"), frames):
            problems.add(where + ".frame", "must be auto, none or one of %s" % ", ".join(sorted(frames)))
        background = one.get("background") or {"kind": "solid"}
        if not isinstance(background, dict) or background.get("kind") not in BACKGROUNDS:
            problems.add(where + ".background.kind", "must be one of %s" % ", ".join(BACKGROUNDS))
            background = {"kind": "solid"}
        if background.get("kind") == "plate" and not background.get("plate"):
            problems.add(where + ".background.plate", "kind plate needs a plate id")
        if background.get("plate") is not None and not _known(background.get("plate"), plates):
            problems.add(where + ".background.plate", "plate %r is not in deck.plates" % (background.get("plate"),))
        for key in ("from", "to", "color"):
            value = background.get(key)
            if value is not None and not (isinstance(value, str) and (value in THEME_COLORS or parse_hex(value))):
                problems.add("%s.background.%s" % (where, key), "must be a theme key (%s) or a hex colour"
                             % ", ".join(THEME_COLORS))
        if one.get("bezel_shadow") is not None and not isinstance(one["bezel_shadow"], bool):
            problems.add(where + ".bezel_shadow", "must be true or false")
        if one.get("lockup") is not None and not isinstance(one["lockup"], bool):
            problems.add(where + ".lockup", "must be true or false: false keeps the brand lockup off every slide of this set")
        if one.get("compact") is not None and not isinstance(one["compact"], bool):
            problems.add(where + ".compact", "must be true or false")
        elif one.get("compact") and one.get("lockup") is not False:
            problems.add(where + ".compact", "compact gives the lockup's room to the copy, so it needs lockup: false on the "
                         "set as well")
        _check_device_top(problems, where, one.get("device_top"))
        export = one.get("export")
        if export is not None and not isinstance(export, dict):
            problems.add(where + ".export", "must be an object {target id: {format: png|jpg, scale: 1|2}}")
            export = {}
        for tid, item in sorted((export or {}).items()):
            spot = "%s.export.%s" % (where, tid)
            if tid not in wanted or tid not in targets:
                problems.add(spot, "names a target this set does not render (targets: %s)" % ", ".join(wanted))
                continue
            if not isinstance(item, dict) or not item or set(item) - set(EXPORT_KEYS):
                problems.add(spot, "must be {format: png|jpg, scale: 1|2}; both keys are optional")
                continue
            if item.get("format", "png") not in targets[tid]["formats"]:
                problems.add(spot + ".format", "%s takes %s, got %r (write jpg, not jpeg)"
                             % (tid, " or ".join(targets[tid]["formats"]), item.get("format")))
            scales = targets[tid].get("scales") or [1]
            if isinstance(item.get("scale", 1), bool) or item.get("scale", 1) not in scales:
                problems.add(spot + ".scale", "%s renders at %s, got %r" % (tid, " or ".join("%dx" % v for v in scales), item.get("scale")))
        if background.get("angle") is not None and not _is_num(background["angle"]):
            problems.add(where + ".background.angle", "must be a number of degrees (180 = top to bottom)")
        dim = background.get("dim")
        if dim is not None and not (_is_num(dim) and 0 <= float(dim) <= 0.9):
            problems.add(where + ".background.dim", "must be between 0 and 0.9")
        slides = one.get("slides")
        if not isinstance(slides, list) or not slides:
            problems.add(where + ".slides", "is empty: add at least one slide")
            continue
        seen_slides = set()
        for index, slide in enumerate(slides):
            if not isinstance(slide, dict):
                problems.add("%s.slides[%d]" % (where, index), "must be an object")
                continue
            spot = "%s.slides[%d] %r" % (where, index, slide.get("id"))
            if not isinstance(slide.get("id"), str) or not ID_RE.fullmatch(slide["id"]):
                problems.add(spot + ".id", "slide ids are lower-case letters, digits and hyphens")
            elif slide["id"] in seen_slides:
                problems.add(spot + ".id", "duplicate slide id in this set")
            seen_slides.add(slide.get("id"))
            layout = slide.get("layout")
            spec = LAYOUTS.get(layout) if isinstance(layout, str) else None
            if spec is None:
                problems.add(spot + ".layout", "unknown layout %r (known: %s)" % (layout, ", ".join(LAYOUTS)))
                continue
            for kind in sorted(k for k in kinds if k and k not in spec["kinds"]):
                problems.add(spot + ".layout", "layout %s renders on %s targets, but this set has a %s target: "
                             "give that target its own set" % (layout, "/".join(spec["kinds"]), kind), "layout_target_mismatch")
            need = spec["captures"]
            low, high = (need, need) if isinstance(need, int) else need
            refs = [("capture", slide.get("capture")), ("capture2", slide.get("capture2"))]
            if low >= 1 and not slide.get("capture"):
                problems.add(spot + ".capture", "layout %s needs a capture: every device slot names a real screen" % layout)
            if low >= 2 and not slide.get("capture2"):
                problems.add(spot + ".capture2", "layout %s needs a second capture" % layout)
            if high == 0 and (slide.get("capture") or slide.get("capture2")):
                problems.add(spot + ".capture", "layout %s shows no capture: remove it or pick another layout" % layout
                             if spec.get("span") != "end" else "layout device-span-end shows the device of the device-span "
                             "slide before it: remove capture here")
            for key, ref in refs:
                names = list(ref.values()) if isinstance(ref, dict) else [ref] if ref is not None else []
                if isinstance(ref, dict) and (not ref or any(k not in ("ios", "android", "default") for k in ref)):
                    problems.add("%s.%s" % (spot, key), "a per-OS capture map uses the keys ios, android, default")
                for name in names:
                    if not _known(name, captures):
                        problems.add("%s.%s" % (spot, key), "capture %r is not in deck.captures" % (name,))
            if slide.get("frame") is not None and slide["frame"] != "auto" and not _known(slide["frame"], frames):
                problems.add(spot + ".frame", "must be null, auto, none or one of %s" % ", ".join(sorted(frames)))
            if mode == "universal" and any(targets[t].get("kind") == "screenshot" for t in wanted if t in targets):
                value = slide.get("frame") if slide.get("frame") not in (None, "auto") else one.get("frame")
                if _known(value, frames) and frames[value]["os"] in ("ios", "android"):
                    problems.add(spot + ".frame", "frame %r identifies a platform: a universal set uses "
                                 "neutral-phone or none" % value, "universal_frame")
            if not isinstance(slide.get("invert", False), bool):
                problems.add(spot + ".invert", "must be true or false")
            if slide.get("bleed") is not None and not isinstance(slide["bleed"], bool):
                problems.add(spot + ".bleed", "must be true, false or absent")
            if slide.get("bezel_shadow") is not None and not isinstance(slide["bezel_shadow"], bool):
                problems.add(spot + ".bezel_shadow", "must be true, false or absent")
            value = slide.get("lockup")
            if isinstance(value, dict) and spec.get("lockup"):
                for key in sorted(set(value) - set(LOCKUP_KEYS)):
                    problems.add("%s.lockup.%s" % (spot, key), "unknown key: the lockup takes %s" % ", ".join(LOCKUP_KEYS))
                low, high = LOCKUP_WIDTH_RANGE
                if "width" in value and not (_is_num(value["width"]) and low <= value["width"] <= high):
                    problems.add(spot + ".lockup.width", "must be a share of the canvas width between %g and %g (default %g)"
                                 % (low, high, LOCKUP_WIDTH))
                if "scrim" in value and not (_is_num(value["scrim"]) and 0 <= value["scrim"] <= LOCKUP_SCRIM_MAX):
                    problems.add(spot + ".lockup.scrim", "must be between 0 and %g (0 = no scrim)" % LOCKUP_SCRIM_MAX)
                if "shadow" in value and not isinstance(value["shadow"], bool):
                    problems.add(spot + ".lockup.shadow", "must be true or false")
            elif isinstance(value, dict):
                problems.add(spot + ".lockup", "only layout card-lockup takes {width, scrim, shadow}: use true or false here, "
                             "or pick card-lockup for a large centred lockup")
            elif value is not None and not isinstance(value, bool):
                problems.add(spot + ".lockup", "must be true, false or absent; it wins over the set's lockup")
            elif spec.get("lockup") and not lockup_wanted(one, slide):
                problems.add(spot + ".lockup", "layout card-lockup draws nothing but the lockup, and lockup: false (here or on "
                             "the set) turns it off: set lockup to true or {width, scrim, shadow} on this slide")
            if slide.get("compact") is not None and not isinstance(slide["compact"], bool):
                problems.add(spot + ".compact", "must be true, false or absent; it wins over the set's compact")
            elif slide.get("compact") and not compact_layout(slide):
                problems.add(spot + ".compact", "only card-left-title, card-centered and card-flow with caption left give a "
                             "missing lockup's room to the copy: remove compact here")
            elif slide.get("compact") and lockup_wanted(one, slide):
                problems.add(spot + ".compact", "compact gives the lockup's room to the copy, so it needs lockup: false (on "
                             "this slide or the set)")
            _check_device_top(problems, spot, slide.get("device_top"))
            if slide.get("device_top") is not None and layout not in DEVICE_TOP_LAYOUTS:
                problems.add(spot + ".device_top", "only %s hang a capture from a top edge: remove device_top here"
                             % " and ".join(DEVICE_TOP_LAYOUTS))
            if spec.get("flow"):
                if slide.get("connector") is not None and slide["connector"] not in CONNECTORS:
                    problems.add(spot + ".connector", "must be %s or absent (default arrow)" % " or ".join(CONNECTORS))
                if slide.get("bleed") is True:
                    problems.add(spot + ".bleed", "layout %s keeps both captures inside the card: remove bleed" % layout)
                tilt = slide.get("tilt")
                if tilt is not None and not (
                        (_is_num(tilt) and abs(tilt) <= TILT_MAX)
                        or (isinstance(tilt, list) and len(tilt) == 2 and all(_is_num(t) and abs(t) <= TILT_MAX for t in tilt))):
                    problems.add(spot + ".tilt", "must be degrees between -%g and %g, or a list of two such numbers "
                                 "(left capture, right capture)" % (TILT_MAX, TILT_MAX))
                if slide.get("caption") is not None and slide["caption"] not in CAPTIONS:
                    problems.add(spot + ".caption", "must be %s or absent (default top: lockup and copy above the pair; "
                                 "left: where card-left-title sets them)" % " or ".join(CAPTIONS))
            elif slide.get("connector") is not None:
                problems.add(spot + ".connector", "only layout card-flow draws a connector: remove it or pick card-flow")
            if not spec.get("flow") and slide.get("tilt") is not None:
                problems.add(spot + ".tilt", "only layout card-flow tilts its captures: remove it or pick card-flow")
            if not spec.get("flow") and slide.get("caption") is not None:
                problems.add(spot + ".caption", "only layout card-flow moves its caption: remove it (card-left-title and "
                             "card-hero-scene set their text on the side already) or pick card-flow")
            if spec.get("zoom"):
                zoom = slide.get("zoom")
                if not (isinstance(zoom, dict) and all(_is_num(zoom.get(k)) for k in "xywh")
                        and 0 <= zoom["x"] < 1 and 0 <= zoom["y"] < 1 and 0 < zoom["w"] <= 1 and 0 < zoom["h"] <= 1
                        and zoom["x"] + zoom["w"] <= 1.0001 and zoom["y"] + zoom["h"] <= 1.0001):
                    problems.add(spot + ".zoom", "layout zoom needs {x, y, w, h} as fractions of the capture, inside 0..1")
            if spec.get("plate"):
                pid = slide.get("plate") or background.get("plate")
                if not _known(pid, plates):
                    problems.add(spot + ".plate", "layout %s needs a plate id from deck.plates" % layout)
                elif not isinstance(plates[pid], dict) or not plates[pid].get("quad"):
                    problems.add(spot + ".plate", "plate %r has no quad: run screen-quad --plate %s --write" % (pid, pid),
                                 "plate_without_quad")
            elif slide.get("plate") is not None and not _known(slide["plate"], plates):
                problems.add(spot + ".plate", "plate %r is not in deck.plates" % (slide["plate"],))
            if spec.get("lockup") and slide.get("copy") not in (None, {}):
                problems.add(spot + ".copy", "layout card-lockup carries no copy, the lockup is the whole design: remove "
                             "copy, or pick card-centered for a line under the brand")
            else:
                validate_copy(problems, spot, slide.get("copy"), locales, spec, spec["headline"])
            items = slide.get("decor") or []
            if not isinstance(items, list):
                problems.add(spot + ".decor", "must be a list")
                items = []
            for d_index, item in enumerate(items):
                dspot = "%s.decor[%d]" % (spot, d_index)
                if not isinstance(item, dict) or not _known(item.get("ref"), decor):
                    problems.add(dspot + ".ref", "must name an entry of deck.decor")
                    continue
                for key, low_v, high_v in (("x", -0.5, 1.5), ("y", -0.5, 1.5), ("w", 0.02, 2.0)):
                    if not _is_num(item.get(key)) or not low_v <= item[key] <= high_v:
                        problems.add("%s.%s" % (dspot, key), "must be a number between %s and %s (x, y = centre, "
                                     "w = width, as fractions of the canvas)" % (low_v, high_v))
                if item.get("rotate") is not None and not _is_num(item["rotate"]):
                    problems.add(dspot + ".rotate", "must be a number of degrees")
                if item.get("z", "back") not in ("back", "front"):
                    problems.add(dspot + ".z", "must be back or front")
        validate_spans(problems, where, slides, background)
    return problems


def validate_spans(problems, where, slides, background):
    """A device across a seam is a pair: device-span, then device-span-end right after it, on a strip ground."""
    roles = []
    for one in slides:
        layout = one.get("layout") if isinstance(one, dict) else None
        roles.append(LAYOUTS.get(layout, {}).get("span") if isinstance(layout, str) else None)
    for index, role in enumerate(roles):
        if not role:
            continue
        slide = slides[index]
        spot = "%s.slides[%d] %r" % (where, index, slide.get("id"))
        if background.get("kind") != "strip":
            problems.add(spot + ".layout", "layout %s puts one device across the seam of two slides, which needs a "
                         "background that crosses it: set the set's background kind to strip" % slide["layout"], "span_needs_strip")
        if role == "start" and (index + 1 >= len(roles) or roles[index + 1] != "end"):
            problems.add(spot + ".layout", "device-span shows the left half of its device: the next slide must be "
                         "device-span-end, which shows the right half", "span_unpaired")
        if role == "end":
            if index == 0 or roles[index - 1] != "start":
                problems.add(spot + ".layout", "device-span-end shows the right half of the device of the device-span "
                             "slide right before it, and there is none", "span_unpaired")
            for key in ("frame", "bleed", "bezel_shadow"):
                if slide.get(key) is not None:
                    problems.add("%s.%s" % (spot, key), "the device of a span pair is set on its device-span slide: "
                                 "remove %s here" % key)


def require_deck(slug, files=True):
    deck = load_deck(slug)
    problems = validate_deck(deck, slug, files=files)
    if problems:
        first = problems.rows[0]
        raise Fail(first["code"], "deck.json: %s %s" % (first["where"], first["message"]),
                   hint="fix deck.json (%d problem%s) and run the command again"
                        % (len(problems.rows), "" if len(problems.rows) == 1 else "s"),
                   extra={"problems": problems.rows[:40], "deck": deck_path(slug)})
    return deck


def find_set(deck, set_id):
    for one in deck["sets"]:
        if one["id"] == set_id:
            return one
    raise Fail("not_found", "set %r is not in the deck (sets: %s)" % (set_id, ", ".join(s["id"] for s in deck["sets"])))


# ----------------------------------------------------------------------------------------------- frames and bars

def resolve_frame(target_id, mode, capture_os, set_frame="auto", slide_frame=None):
    """Frame id for one page. An explicit slide frame wins over the set frame; `auto` resolves per TARGET."""
    frames = devices()["frames"]
    for value in (slide_frame, set_frame):
        if value and value != "auto":
            if value not in frames:
                raise Fail("deck_invalid", "unknown frame %r" % value)
            return value
    target = surfaces()["targets"][target_id]
    if target.get("kind") == "screenshot" and target.get("auto_frame"):
        if mode == "universal" and target.get("device") in ("phone", "tablet"):
            return "neutral-phone"
        return target["auto_frame"]          # a Mac screenshot keeps its window in every mode
    if capture_os in ("web", "desktop"):
        return "browser"
    if mode == "universal":
        return "neutral-phone"
    if target.get("auto_frame"):
        return target["auto_frame"]          # a store card keeps the store's own device
    return {"ios": "iphone", "android": "android-phone"}.get(capture_os, "neutral-phone")


def statusbar_decision(mode, state, policy="auto", flat=None, frame_kind="phone", frame_os=None, capture_os=None,
                       hidden=False):
    """The status-bar decision table as a pure function.

    action: none | keep | extend | extend_blank | overlay | repaint | repaint_blank | test_flat | mask
    `test_flat` means the page measures the strip and the caller asks again with flat=True/False.
    `mask` (policy "mask", the user agreed to cover a bar the capture has): the bar area is covered with its most
    common colour whether it is flat or not, then the frame's bar is drawn (blank in universal): the page reports
    `repaint` or `repaint_blank`. A capture with no bar (`missing`) is treated as under "auto".
    `hidden`: the page's platform shows no status bar here (a phone in landscape whose bar has `landscape.hidden`:
    iOS, neutral). Nothing is added and nothing is drawn; a bar the capture brings is covered blank when flat.
    """
    def result(action, glyphs=False, warning=None):
        return {"action": action, "glyphs": glyphs, "warning": warning}
    if policy == "none" or frame_kind in ("window",):
        return result("none")
    if policy == "keep":
        return result("keep")
    if state not in BAR_STATES:
        raise Fail("deck_invalid", "statusbar_state must be one of %s" % ", ".join(BAR_STATES))
    neutral = mode == "universal" or frame_os == "neutral"
    if policy == "mask" and state != "missing":
        return result("mask", glyphs=not (neutral or hidden))
    if hidden:
        if state == "missing":
            return result("none")
        if state == "empty":
            return result("keep")
        foreign = (capture_os in ("ios", "android") and frame_os in ("ios", "android") and capture_os != frame_os)
        if state == "clean" and not (foreign or neutral):
            return result("keep")
        if flat is None:
            return result("test_flat")
        if flat:
            return result("repaint_blank")
        return result("keep", warning="statusbar_identifies_os" if neutral else
                      "statusbar_os_mismatch" if state == "clean" else "statusbar_kept_dirty")
    if neutral:
        if state == "missing":
            return result("extend_blank")
        if flat is None:
            return result("test_flat")
        if flat:
            return result("repaint_blank")
        return result("keep", warning=None if state == "empty" else "statusbar_identifies_os")
    if state == "missing":
        return result("extend", glyphs=True)
    if state == "empty":
        return result("overlay", glyphs=True)
    foreign = (capture_os in ("ios", "android") and frame_os in ("ios", "android") and capture_os != frame_os)
    if state == "clean" and not foreign:
        return result("keep")
    if flat is None:
        return result("test_flat", glyphs=True)
    if flat:
        return result("repaint", glyphs=True)
    return result("keep", warning="statusbar_os_mismatch" if state == "clean" else "statusbar_kept_dirty")


def tablet_shaped(width, height):
    return min(width, height) / float(max(width, height)) > 0.62


def own_bar_height(capture_os, width, height, top_bar):
    """Height of the status bar INSIDE the capture (its own OS and device class): what a repaint has to cover."""
    data = devices()
    tablet = tablet_shaped(width, height)
    donor = {"ios": "ipad" if tablet else "iphone", "android": "android-tablet" if tablet else "android-phone"}.get(capture_os)
    bar_id = data["frames"][donor]["statusbar"] if donor else None
    if bar_id:
        bar = data["bars"][bar_id]
        if width > height and not tablet:       # a phone in landscape: its own landscape bar, or none (iOS)
            turned = landscape_bar(bar)
            return 0.0 if turned.get("hidden") else turned["height"]
        return bar["height"]
    return (top_bar or {}).get("height") or 0.0


def landscape_bar(bar):
    """A phone status bar as a landscape screen shows it. `landscape.hidden` (iOS, neutral): the platform shows none,
    so the page draws none. `landscape.height`: a thinner strip; the artwork keeps its portrait scale (`art_height`)
    and is moved so its glyphs sit at `landscape.center_y` (`art_shift`); the drawn glyphs move the same way."""
    turn = bar.get("landscape")
    if not turn or turn.get("hidden"):
        return {"os": bar.get("os"), "kind": bar.get("kind"), "height": 0.0, "hidden": True}
    layout = bar.get("layout")
    shift = turn["center_y"] - (layout["center_y"] if layout else bar["height"] / 2.0)
    return dict(bar, height=turn["height"], art_height=bar["height"], art_shift=shift,
                layout=dict(layout, center_y=turn["center_y"]) if layout else layout)


def frameless_bar_os(target_id, capture_os):
    """Whose bars a frameless capture borrows. On a store surface it is the STORE's platform, not the capture's:
    an iOS capture with `frame: "none"` must not carry its own 9:41 bar onto a Play page, and an Android capture
    must not carry Android glyphs onto an App Store target (App Review 2.3.10, store-policy.md section 4). The
    decision table then treats the borrowed bar like a frame's: flat foreign bar repainted, anything else kept
    with `statusbar_os_mismatch`. Off-store surfaces (web cards, Product Hunt, ads) keep the capture's own."""
    if capture_os not in ("ios", "android"):
        return capture_os                    # a web or desktop capture has no phone bar to trade
    target = surfaces()["targets"][target_id]
    if target.get("device") == "desktop":
        return capture_os                    # a Mac listing has no phone bar of its own to lend
    return {"app-store": "ios", "play": "android"}.get(target.get("store"), capture_os)


def frame_bars(frame_id, bar_os, mode, tablet=False):
    """(frame, status bar, bottom bar). A frameless capture borrows the bars of `bar_os` and its device class."""
    data = devices()
    frame = data["frames"][frame_id]
    top, bottom = frame.get("statusbar"), frame.get("bottombar")
    if frame["kind"] == "none" and bar_os in ("ios", "android"):
        donor = data["frames"]["neutral-phone" if mode == "universal" else
                               {("ios", False): "iphone", ("ios", True): "ipad", ("android", False): "android-phone",
                                ("android", True): "android-tablet"}[(bar_os, bool(tablet))]]
        top, bottom = donor["statusbar"], donor["bottombar"]
    return frame, data["bars"].get(top) if top else None, data["bars"].get(bottom) if bottom else None


# ----------------------------------------------------------------------------------------------- homography

def homography(src, dst):
    """3x3 matrix mapping four source points to four destination points (h33 = 1), Gaussian elimination."""
    if len(src) != 4 or len(dst) != 4:
        raise Fail("no_quad", "a homography needs four point pairs")
    degenerate = Fail("no_quad", "the four points are degenerate (three on one line, or repeated)",
                      hint="run screen-quad again, or fix plates.<id>.quad by hand: top-left, top-right, "
                           "bottom-right, bottom-left")
    for points in (src, dst):
        extent = max(max(abs(p[0]) for p in points), max(abs(p[1]) for p in points), 1.0)
        for skip in range(4):
            a, b, c = [points[i] for i in range(4) if i != skip]
            if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) <= 1e-7 * extent * extent:
                raise degenerate
    rows = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([float(x), float(y), 1.0, 0.0, 0.0, 0.0, -u * x, -u * y, float(u)])
        rows.append([0.0, 0.0, 0.0, float(x), float(y), 1.0, -v * x, -v * y, float(v)])
    scale = max(max(abs(v) for v in row) for row in rows) or 1.0
    for col in range(8):
        pivot = max(range(col, 8), key=lambda r: abs(rows[r][col]))
        if abs(rows[pivot][col]) < 1e-9 * scale:
            raise degenerate
        rows[col], rows[pivot] = rows[pivot], rows[col]
        lead = rows[col][col]
        rows[col] = [value / lead for value in rows[col]]
        for r in range(8):
            if r != col and rows[r][col]:
                factor = rows[r][col]
                rows[r] = [a - factor * b for a, b in zip(rows[r], rows[col])]
    h = [rows[i][8] for i in range(8)] + [1.0]
    return [h[0:3], h[3:6], h[6:9]]


def apply_homography(h, point):
    x, y = point
    w = h[2][0] * x + h[2][1] * y + h[2][2]
    return ((h[0][0] * x + h[0][1] * y + h[0][2]) / w, (h[1][0] * x + h[1][1] * y + h[1][2]) / w)


def matrix3d(h):
    values = (h[0][0], h[1][0], 0, h[2][0], h[0][1], h[1][1], 0, h[2][1], 0, 0, 1, 0, h[0][2], h[1][2], 0, 1)
    return "matrix3d(%s)" % ",".join("%.10f" % v for v in values)


def grow_quad(quad, pixels):
    """Push every corner away from the centre so the warped screen tucks under the antialiased key edge."""
    cx = sum(p[0] for p in quad) / 4.0
    cy = sum(p[1] for p in quad) / 4.0
    grown = []
    for x, y in quad:
        dx, dy = x - cx, y - cy
        norm = math.hypot(dx, dy) or 1.0
        grown.append((x + dx / norm * pixels, y + dy / norm * pixels))
    return grown


def quad_bbox(quad):
    xs, ys = [p[0] for p in quad], [p[1] for p in quad]
    return [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]


def quad_aspect(quad):
    dist = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1])  # noqa: E731
    width = (dist(quad[0], quad[1]) + dist(quad[3], quad[2])) / 2.0
    height = (dist(quad[0], quad[3]) + dist(quad[1], quad[2])) / 2.0
    if height <= 0 or width <= 0:
        raise Fail("no_quad", "the quad has no area")
    return width / height


def aspect_gap(capture, estimate, span=None):
    """Relative distance of a capture's aspect from the plate screen's: 0 inside the plate's aspect_range."""
    low, high = span if span else (estimate, estimate)
    if capture < low:
        return (low - capture) / low
    return (capture - high) / high if capture > high else 0.0


ASSUMED_FOCAL = 1.4      # focal length in plate widths when the quad cannot give one (about a 50 mm look)
FOCAL_RANGE = (0.5, 4.0)  # plausible focal lengths in plate widths (about 18 to 145 mm on full frame)
MIN_PERSPECTIVE = 0.02   # below this depth change along either side direction the focal length is noise
FOCAL_SLACK = (1.3, 2.0)  # the focal length is trusted within this factor when measured, when assumed
STRAY_KEY_WARN = 0.002   # key-coloured share of a plate outside the screen island worth a look


def rectified_ratio(corners, width, height, focal=None):
    """World length of side c0-c1 over side c0-c3 of a rectangle seen as `corners` (cyclic), whether the focal length
    came from the quad itself, and that focal length. The principal point is the image centre and pixels are square;
    the focal length is the one that makes the two side directions perpendicular (Zhang and He's whiteboard method).
    It is only conditioned when both side directions recede: a quad whose opposite sides are nearly parallel in one
    direction, or whose answer is outside FOCAL_RANGE, gets ASSUMED_FOCAL (the ratio then barely depends on it).
    `focal` (pixels) skips the estimate."""
    h = homography([(0, 0), (1, 0), (1, 1), (0, 1)], corners)
    cx, cy, span = width / 2.0, height / 2.0, float(max(width, height))
    cols = [(h[0][j] - cx * h[2][j], h[1][j] - cy * h[2][j], h[2][j]) for j in (0, 1)]
    (a1, b1, z1), (a2, b2, z2) = cols
    measured = False
    if focal is None:
        focal = ASSUMED_FOCAL * span
        recede = min(abs(z) * focal / (math.hypot(a, b) or 1e-12) for a, b, z in cols)
        if recede >= MIN_PERSPECTIVE:
            f2 = -(a1 * a2 + b1 * b2) / (z1 * z2)
            if f2 > 0 and FOCAL_RANGE[0] * span <= math.sqrt(f2) <= FOCAL_RANGE[1] * span:
                focal, measured = math.sqrt(f2), True
    length = lambda a, b, z: math.sqrt((a / focal) ** 2 + (b / focal) ** 2 + z * z)  # noqa: E731
    return length(a1, b1, z1) / length(a2, b2, z2), measured, focal


def orient_screen(corners, island, orientation, width, height):
    """Order a detected screen as top-left, top-right, bottom-right, bottom-left. The top is the side nearest the
    camera cut-out when there is one, else the highest side in the image; `portrait` limits the choice to the two
    short sides of the real screen, `landscape` to the two long ones, `auto` takes any side."""
    corners = [(float(x), float(y)) for x, y in corners]
    ratio, measured, focal = rectified_ratio(corners, width, height)      # side 0 (c0-c1) over side 1 (c1-c2)
    long_even = ratio >= 1.0
    sides = range(4)
    if orientation == "portrait":
        sides = [k for k in sides if (k % 2 == 0) != long_even]
    elif orientation == "landscape":
        sides = [k for k in sides if (k % 2 == 0) == long_even]

    def mid(k):
        a, b = corners[k], corners[(k + 1) % 4]
        return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
    if island:
        top = min(sides, key=lambda k: math.hypot(mid(k)[0] - island["cx"], mid(k)[1] - island["cy"]))
    else:
        top = min(sides, key=lambda k: mid(k)[1])
    quad = [corners[(top + i) % 4] for i in range(4)]
    if (quad[1][0] - quad[0][0]) * (quad[3][1] - quad[0][1]) - (quad[1][1] - quad[0][1]) * (quad[3][0] - quad[0][0]) < 0:
        quad = [quad[1], quad[0], quad[3], quad[2]]
    aspect = ratio if top % 2 == 0 else 1.0 / ratio
    # a generated photograph is no exact pinhole camera: the answer spans the focal lengths the scene could have
    slack = FOCAL_SLACK[0 if measured else 1]
    span = [rectified_ratio(corners, width, height, focal * f)[0] for f in (1.0 / slack, slack)] + [ratio]
    span = [v if top % 2 == 0 else 1.0 / v for v in span]
    dist = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1])  # noqa: E731
    return {"quad": [[round(x, 2), round(y, 2)] for x, y in quad], "top_guess": not island,
            "orientation": "landscape" if aspect > 1.0 else "portrait", "aspect_estimate": round(aspect, 4),
            "aspect_range": [round(min(span), 4), round(max(span), 4)],
            "focal_measured": measured,
            "side_ratio": {"width": round(dist(quad[0], quad[1]) / dist(quad[3], quad[2]), 3),
                           "height": round(dist(quad[0], quad[3]) / dist(quad[1], quad[2]), 3)}}


# ----------------------------------------------------------------------------------------------- copy gates

def lang_of(locale):
    return str(locale or "en").lower().split("-")[0]


def upper_for(text, locale):
    return text.translate(TR_UPPER).upper() if lang_of(locale) in TR_LANGS else text.upper()


def lower_for(text, locale):
    return text.translate(TR_LOWER).lower() if lang_of(locale) in TR_LANGS else text.lower()


def fact_numbers(facts):
    """Numbers the copy may carry. The gate is EXACT on the written form: "4.8" and "4,8" are different entries."""
    allowed = set()
    for item in (facts or {}).get("numbers") or []:
        text = str(item).strip()
        allowed.add(text)
        allowed.update(NUMBER_RE.findall(text))
    return allowed


def word_hit(word, low, stem=False):
    """Case-insensitive match on word boundaries (the caller lower-cases with the locale's rules).
    `stem` matches the start of a word only, so suffixed forms count: award -> awards, editör -> editörün."""
    head = r"(?<!\w)" if word[0].isalnum() else ""
    tail = r"(?!\w)" if word[-1].isalnum() and not stem else ""
    return re.search(head + re.escape(word) + tail, low, re.UNICODE) is not None


def check_line(text, locale, facts, stores, rules=()):
    """Issues of one authored string: numbers gate, claims gate, store word lists, price talk, content rules.

    `stores` = the stores of the set's targets. Google's avoid list is a hard error on play targets only.
    `rules` = the `content_rules` of the set's targets (CONTENT_RULES): each one found is an error."""
    issues = []
    clean = " ".join(unicodedata.normalize("NFC", text).split())
    low = lower_for(clean, locale)
    allowed = fact_numbers(facts)

    def issue(code, level, message):
        issues.append({"code": code, "level": level, "text": text, "message": message})
    for token in NUMBER_RE.findall(clean):
        if token not in allowed:
            issue("number_not_in_facts", "error", "number %r is not in facts.numbers exactly as written: remove it or "
                  "have the user confirm it" % token)
    claims = [lower_for(str(c), locale) for c in (facts or {}).get("claims") or []]
    for word in CLAIM_WORDS:
        if word_hit(word, low, stem=True) and not any(word in claim for claim in claims):
            issue("claim_not_in_facts", "error", "claim word %r needs a matching facts.claims entry in the user's words" % word)
            break
    on_play = "play" in stores
    ad_only = set(stores) == {"ads"}    # an ad may call to action; a set that also feeds a store listing keeps the word lists
    for word in () if ad_only else PLAY_HARD_WORDS:
        if word_hit(word, low):
            issue("banned_store_word", "error" if on_play else "warning",
                  "%r is on Google Play's avoid list for listing graphics (ranking, price or call-to-action talk): "
                  "rephrase%s" % (word, "" if on_play else "; a Play target would refuse this copy"))
            break
    for word in () if ad_only else PROMO_WORDS + PROMO_WORDS_OTHER:
        if word_hit(word, low):
            issue("promo_word", "warning", "%r reads as promotion, ranking or price talk: both stores discourage it in "
                  "listing graphics" % word)
            break
    if PRICE_RE.search(clean) and "no_price" in rules:
        issue("price_in_copy", "error", "a currency amount: Apple's creative assets carry no specific prices")
    elif PRICE_RE.search(clean) and set(stores) & {"app-store", "play"}:
        issue("price_in_copy", "warning", "a currency amount in store copy: App Review 2.3.7 keeps prices out of "
              "screenshots, and prices differ per storefront")
    folded = low.replace("’", "'").replace("ʼ", "'")
    found = [word for word in DISCOUNT_WORDS if word_hit(word, low)] if "no_discount" in rules else []
    if found:
        issue("discount_in_copy", "error", "%r is discount talk: Apple's creative assets carry no discounts" % found[0])
    url = URL_RE.search(clean) if "no_url" in rules else None
    if url:
        issue("url_in_copy", "error", "%r reads as a web address: Apple's creative assets carry no URLs" % url.group(0))
    if "no_copyright" in rules and COPYRIGHT_RE.search(clean):
        issue("copyright_symbol", "error", "a copyright symbol: Apple's creative assets carry none")
    badge = APPLE_BADGE_RE.search(folded) if "no_apple_badge" in rules else None
    if badge:
        issue("apple_badge", "error", "%r is an Apple-designated recognition: Apple asks creative assets to leave these "
              "out, even when the app received it" % badge.group(0))
    found = [word for word in OTHER_PLATFORM_WORDS if word_hit(word, low)] if "no_other_platform" in rules else []
    if found:
        issue("other_platform", "error", "%r names another platform or marketplace: Apple's creative assets carry no "
              "logos or mentions of them (App Review 2.3.10)" % found[0])
    if any(unicodedata.category(ch) in ("So", "Cs", "Co") or ord(ch) > 0xFFFF for ch in clean):
        issue("symbol", "warning", "emoji and symbols render in the system emoji font and differ per machine")
    return issues


# ----------------------------------------------------------------------------------------------- in-page scripts

# Everything below runs synchronously inside ONE load handler: no promises, no timers. A headless browser
# dumps the DOM and takes the screenshot right after `load`, so later work would be lost. Geometry is in CSS
# pixels; a canvas holds S.D device pixels per CSS pixel (a 2x export), so pixel reads scale by D.
PAGE_JS = r"""
(function(){'use strict';
function $(id){return document.getElementById(id)}
function chan(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)}
function lum(c){return 0.2126*chan(c[0])+0.7152*chan(c[1])+0.0722*chan(c[2])}
function ratio(a,b){var hi=Math.max(a,b),lo=Math.min(a,b);return(hi+0.05)/(lo+0.05)}
function rgba(c,a){return'rgba('+Math.round(c[0])+','+Math.round(c[1])+','+Math.round(c[2])+','+a+')'}
function hex(c){return'#'+c.map(function(v){return('0'+Math.round(v).toString(16)).slice(-2)}).join('')}
function rect(el){var r=el.getBoundingClientRect();return[r.left,r.top,r.width,r.height].map(function(v){return Math.round(v*10)/10})}
function grain(g,w,h,a){var im=g.getImageData(0,0,w,h),d=im.data,s=0x2545f491;   // seeded: the same page renders the same file
 function u(){s^=s<<13;s^=s>>>17;s^=s<<5;return(s>>>0)/4294967296}
 for(var i=0;i<d.length;i++){if((i&3)!==3)d[i]+=Math.round((u()+u()-1)*a)}g.putImageData(im,0,0)}   // per channel: JPEG rings in chroma too
function paintBackground(S,out){var c=$('lk-bg'),g=c.getContext('2d',{willReadFrequently:true}),b=S.bg,D=S.D||1;
 g.setTransform(D,0,0,D,0,0);g.fillStyle=b.color;g.fillRect(0,0,S.W,S.H);
 if(b.kind==='gradient'){var l=b.line,gr=g.createLinearGradient(l[0],l[1],l[2],l[3]);gr.addColorStop(0,b.from);gr.addColorStop(1,b.to);
  g.fillStyle=gr;g.fillRect(0,0,S.W,S.H);
  (b.blobs||[]).forEach(function(o){var rg=g.createRadialGradient(o.x,o.y,0,o.x,o.y,o.r);rg.addColorStop(0,rgba(o.color,o.alpha));
   rg.addColorStop(0.5,rgba(o.color,o.alpha*0.42));rg.addColorStop(1,rgba(o.color,0));g.fillStyle=rg;g.fillRect(0,0,S.W,S.H)});
  if(b.grain)grain(g,Math.round(S.W*D),Math.round(S.H*D),b.grain)}
 if(b.kind==='plate'){g.imageSmoothingEnabled=true;g.imageSmoothingQuality='high';g.drawImage($(b.plate),b.draw[0],b.draw[1],b.draw[2],b.draw[3]);
  if(b.dim>0){g.fillStyle=rgba(b.dimColor,b.dim);g.fillRect(0,0,S.W,S.H)}}
 if(b.scrim&&b.scrim.rx>0){var s=b.scrim;g.save();g.translate(s.x,s.y);g.scale(1,s.ry/s.rx);   // an ellipse around a card-lockup's lockup
  var sg=g.createRadialGradient(0,0,0,0,0,s.rx);sg.addColorStop(0,rgba(s.color,s.alpha));sg.addColorStop(0.55,rgba(s.color,s.alpha*0.55));
  sg.addColorStop(1,rgba(s.color,0));g.fillStyle=sg;g.fillRect(-s.rx,-s.rx,2*s.rx,2*s.rx);g.restore()}
 out.decor=[];
 (S.backDecor||[]).forEach(function(d){var im=$(d.img),w=d.w,h=w*im.naturalHeight/im.naturalWidth;g.save();g.translate(d.cx,d.cy);
  g.rotate(d.rotate*Math.PI/180);g.shadowColor='rgba(0,0,0,0.30)';g.shadowBlur=w*0.09;g.shadowOffsetY=w*0.045;g.imageSmoothingQuality='high';
  g.drawImage(im,-w/2,-h/2,w,h);g.restore();var e=Math.hypot(w,h)/2;out.decor.push({ref:d.ref,z:'back',rect:[d.cx-w/2,d.cy-h/2,w,h],reach:e})});
 return g}
function keyPlate(S){var hs=S.hero,c=$('lk-plate'),g=c.getContext('2d',{willReadFrequently:true}),D=S.D||1,WD=Math.round(S.W*D);g.setTransform(D,0,0,D,0,0);g.imageSmoothingQuality='high';
 g.drawImage($(hs.plate),hs.draw[0],hs.draw[1],hs.draw[2],hs.draw[3]);var im=g.getImageData(0,0,WD,Math.round(S.H*D)),d=im.data,LO=40,HI=130,green=hs.key==='green',MED=hs.med||235,keyed=0,bx=hs.box;
 for(var i=0;i<d.length;i+=4){var r=d[i],gg=d[i+1],b=d[i+2],k=green?gg-Math.max(r,b):Math.min(r,b)-gg;
  if(k<=10)continue;var q=i>>2,qx=q%WD,px=qx/D,py=(q-qx)/WD/D,near=px>=bx[0]&&py>=bx[1]&&px<=bx[0]+bx[2]&&py<=bx[1]+bx[3];
  if(k<=LO||(!green&&Math.abs(r-b)>=110)){   // key light bounced onto a finger or the bezel next to the screen
   if(k<=LO&&near){var cut=(k-10)*0.7;if(green){d[i+1]=gg-cut}else{d[i]=r-cut;d[i+2]=b-cut}}
   continue}
  if(!near){if(green){d[i+1]=gg-k}else{d[i]=r-k;d[i+2]=b-k}continue}   // key colour away from the screen is scene light (a reflection on the table): neutral, opaque
  var a=Math.min(1,(k-LO)/(HI-LO));
  if(a>=1){keyed++;var l=(green?gg:(r+b)/2)/MED;if(l<1){d[i]=d[i+1]=d[i+2]=0;d[i+3]=Math.round(255*Math.min(0.4,(1-l)*1.2))}
   else{d[i]=d[i+1]=d[i+2]=255;d[i+3]=Math.round(255*Math.min(0.3,(l-1)*1.2))}}
  else{var spill=Math.max(0,k);if(green){d[i+1]=gg-spill}else{d[i]=r-spill;d[i+2]=b-spill}d[i+3]=Math.round(255*(1-a))}}
 g.putImageData(im,0,0);
 if(hs.scrim){var s=hs.scrim,gr=g.createLinearGradient(s.x0,0,s.x1,0);gr.addColorStop(0,rgba(s.color,s.alpha));gr.addColorStop(s.hold,rgba(s.color,s.alpha*0.85));
  for(var k=1;k<=8;k++){var u=k/8;gr.addColorStop(s.hold+(1-s.hold)*u,rgba(s.color,s.alpha*0.85*(1-u*u*(3-2*u))))}   // eased out: no corner, no seam
  g.globalCompositeOperation='source-atop';g.fillStyle=gr;g.fillRect(0,0,S.W,S.H);g.globalCompositeOperation='source-over'}
 return{ctx:g,keyed:keyed}}
function grab(img,y0,h){var nw=img.naturalWidth,sw=Math.min(360,nw),sh=Math.max(2,Math.round(h*sw/nw)),c=document.createElement('canvas');c.width=sw;c.height=sh;
 var g=c.getContext('2d',{willReadFrequently:true});g.drawImage(img,0,y0,nw,h,0,0,sw,sh);return{d:g.getImageData(0,0,sw,sh).data,w:sw,h:sh}}
function modeColor(s){var bins={},best=null,bn=0,n=s.w*s.h;for(var p=0;p<n;p++){var i=p*4,k=(s.d[i]>>4)<<8|(s.d[i+1]>>4)<<4|(s.d[i+2]>>4),o=bins[k];
  if(!o){o=bins[k]=[0,0,0,0]}o[0]++;o[1]+=s.d[i];o[2]+=s.d[i+1];o[3]+=s.d[i+2];if(o[0]>bn){bn=o[0];best=o}}
 return[best[1]/best[0],best[2]/best[0],best[3]/best[0]]}
function share(s,col,x0,y0,x1,y1){var hit=0,n=0;for(var y=y0;y<y1;y++)for(var x=x0;x<x1;x++){var i=(y*s.w+x)*4;n++;
  if(Math.abs(s.d[i]-col[0])<=14&&Math.abs(s.d[i+1]-col[1])<=14&&Math.abs(s.d[i+2]-col[2])<=14)hit++}return n?hit/n:0}
function ink(col){return lum(col)<0.36?'#ffffff':'#000000'}
function statusBars(S,out){out.devices=[];S.devices.forEach(function(dv){var el=$(dv.id),info={id:dv.id,capture:dv.capture,rect:rect(el),plan:dv.plan,applied:dv.plan};
  var cap=$(dv.cap);if(cap){var nw=cap.naturalWidth,nh=cap.naturalHeight;info.natural=[nw,nh];
   if(dv.kind==='window'){var t=modeColor(grab(cap,0,Math.max(2,Math.round(nh*0.01))));if(lum(t)<0.2)el.classList.add('lk-dark');info.chrome=lum(t)<0.2?'dark':'light'}
   else if(dv.plan==='extend'||dv.plan==='extend_blank'){var edge=Math.max(2,Math.round(nh*0.006)),top=modeColor(grab(cap,0,edge)),bot=modeColor(grab(cap,nh-edge,edge));
    var a=$(dv.id+'-top'),b=$(dv.id+'-bot'),gl=$(dv.id+'-gl'),pl=$(dv.id+'-pill');if(a)a.style.background=hex(top);if(b)b.style.background=hex(bot);
    if(gl)gl.style.color=ink(top);if(pl)pl.style.background=ink(bot);var ib=$(dv.id+'-ibot');if(ib)ib.style.color=ink(bot);
    info.strip=hex(top);info.bottom=hex(bot)}
   else if(dv.plan==='overlay'||dv.plan==='test_flat'||dv.plan==='mask'){var bar=Math.max(2,Math.round(dv.barFrac*Math.min(nw,nh))),s=grab(cap,0,bar),col=modeColor(s);info.strip=hex(col);
    var gl2=$(dv.id+'-gl');if(gl2)gl2.style.color=ink(col);
    if(dv.plan==='test_flat'||dv.plan==='mask'){var e=Math.max(1,Math.round(s.h*0.15)),side=Math.max(1,Math.round(s.w*0.012));
     var all=share(s,col,0,0,s.w,s.h),low=share(s,col,0,s.h-e,s.w,s.h),lft=share(s,col,0,0,side,s.h),rgt=share(s,col,s.w-side,0,s.w,s.h);
     info.flat=all>=0.78&&low>=0.92&&lft>=0.9&&rgt>=0.9;info.flat_share=Math.round(all*1000)/1000;var cv=$(dv.id+'-cover');
     if(info.flat||dv.plan==='mask'){if(cv){cv.style.background=hex(col);cv.style.display='block'}if(gl2)gl2.style.display=dv.glyphs?'block':'none';info.applied=dv.glyphs?'repaint':'repaint_blank'}
     else{if(gl2)gl2.style.display='none';info.applied='keep'}}}}
  out.devices.push(info)})}
function lockupInk(el,S){var im=el.querySelector('img:not(.lk-icon)');if(!im)return S.colors.headline;   // icon plus name: the name is set in fg
 try{var r=im.getBoundingClientRect(),w=Math.max(1,Math.min(200,Math.round(r.width))),h=Math.max(1,Math.round(w*r.height/Math.max(1,r.width))),c=document.createElement('canvas');
  c.width=w;c.height=h;var g=c.getContext('2d',{willReadFrequently:true});g.drawImage(im,0,0,w,h);var d=g.getImageData(0,0,w,h).data,bins={},best=null,bn=0;
  for(var i=0;i<d.length;i+=4){if(d[i+3]<200)continue;var k=(d[i]>>4)<<8|(d[i+1]>>4)<<4|(d[i+2]>>4),o=bins[k];if(!o){o=bins[k]=[0,0,0,0]}
   o[0]++;o[1]+=d[i];o[2]+=d[i+1];o[3]+=d[i+2];if(o[0]>bn){bn=o[0];best=o}}
  return best?[best[1]/best[0],best[2]/best[0],best[3]/best[0]]:null}catch(e){return null}}
function lockupFit(S){var L=S.lockup,el=$('lk-lockup-i');if(!L||!el)return null;var r=el.getBoundingClientRect();if(!(r.width>0&&r.height>0))return null;
 var want=r.height*L.width/r.width,h=Math.min(want,L.maxH,r.height*L.maxW/r.width),k=h/r.height;el.style.height=h+'px';   // images follow the height,
 Array.prototype.forEach.call(el.querySelectorAll('span'),function(s){s.style.fontSize=parseFloat(s.style.fontSize)*k+'px';s.style.marginLeft=parseFloat(s.style.marginLeft)*k+'px'});   // the name is scaled
 var ink=lockupInk(el,S),light=lum(ink||S.colors.headline)>0.4;
 if(L.shadow)el.style.filter='drop-shadow(0 '+(h*0.03).toFixed(2)+'px '+(h*0.12).toFixed(2)+'px '+(light?'rgba(0,0,0,0.38)':'rgba(255,255,255,0.5)')+')';
 var q=rect(el);return{rect:q,ink:ink,light:light,width_share:Math.round(q[2]/S.W*1000)/1000,asked:L.share,capped:h<want-0.5}}
function fitText(S,out){var t=S.text,root=document.documentElement,blocks=t.blocks.map(function(b){return{box:$(b),inner:$(b+'-i')}}),scale=1,ok=false;
 function fits(){for(var i=0;i<blocks.length;i++){var b=blocks[i],bw=b.box.clientWidth,bh=b.box.clientHeight,sp=b.inner.querySelectorAll('.l>span');
   for(var j=0;j<sp.length;j++)if(sp[j].getBoundingClientRect().width>bw+0.5)return false;if(b.inner.getBoundingClientRect().height>bh+0.5)return false}return true}
 if(!blocks.length){out.fit_ok=true;out.fit_scale=1;return}
 for(;;){root.style.setProperty('--fs',(t.base*scale)+'px');if(fits()){ok=true;break}if(scale-t.step<t.floor-1e-9)break;scale=Math.round((scale-t.step)*1000)/1000}
 out.fit_ok=ok;out.fit_scale=scale;out.headline_px=Math.round(t.base*scale*10)/10}
function contrastAt(g,S,r,col){var D=S.D||1,x0=Math.max(0,Math.floor(r[0]*D)),y0=Math.max(0,Math.floor(r[1]*D)),x1=Math.min(Math.round(S.W*D),Math.ceil((r[0]+r[2])*D)),y1=Math.min(Math.round(S.H*D),Math.ceil((r[1]+r[3])*D));
 if(x1<=x0||y1<=y0)return null;var d=g.getImageData(x0,y0,x1-x0,y1-y0).data,w=x1-x0,h=y1-y0,step=Math.max(1,Math.floor(Math.sqrt(w*h/3500))),tl=lum(col),vals=[];
 for(var y=0;y<h;y+=step)for(var x=0;x<w;x+=step){var i=(y*w+x)*4;if(d[i+3]<250)continue;vals.push(ratio(tl,lum([d[i],d[i+1],d[i+2]])))}
 if(!vals.length)return null;vals.sort(function(a,b){return a-b});return Math.round(vals[Math.floor(vals.length*0.05)]*100)/100}
window.addEventListener('load',function(){var out={ok:true,script:'lk1'},S=window.LK_SPEC;try{
 out.canvas=[S.W,S.H];var lk=lockupFit(S);
 if(lk&&S.bg.scrim){var sc=S.bg.scrim,q=lk.rect;sc.x=q[0]+q[2]/2;sc.y=q[1]+q[3]/2;sc.rx=0.9*q[2];sc.ry=Math.max(1.6*q[3],0.45*q[2]);sc.color=lk.light?[0,0,0]:[255,255,255]}
 var g=paintBackground(S,out),sample=g;
 if(lk)out.lockup={rect:lk.rect,width_share:lk.width_share,asked:lk.asked,capped:lk.capped,ink:lk.ink?hex(lk.ink):null,contrast:lk.ink?contrastAt(g,S,lk.rect,lk.ink):null};
 if(S.hero){var kp=keyPlate(S);sample=kp.ctx;out.keyed=kp.keyed}
 statusBars(S,out);fitText(S,out);
 out.text=[];var nodes=document.querySelectorAll('[data-role]');for(var i=0;i<nodes.length;i++){var el=nodes[i],role=el.getAttribute('data-role'),r=rect(el),col=S.colors[role];
  out.text.push({role:role,block:el.getAttribute('data-block'),rect:r,font_px:Math.round(parseFloat(getComputedStyle(el).fontSize)*10)/10,
   contrast:col?contrastAt(sample,S,r,col):null})}
 out.boxes=[];(S.measure||[]).forEach(function(m){var el=$(m.id);if(el)out.boxes.push({id:m.id,role:m.role,rect:rect(el)})});
}catch(e){out={ok:false,kind:'js_error',message:String(e&&e.stack||e)}}
$('lk-metrics').textContent=JSON.stringify(out)});})();
"""

QUAD_JS = r"""
window.addEventListener('load',function(){var out=document.getElementById('lk-metrics');try{
var img=document.getElementById('scene'),W=img.naturalWidth,H=img.naturalHeight,green=window.LK_KEY==='green';
var c=document.createElement('canvas');c.width=W;c.height=H;var g=c.getContext('2d',{willReadFrequently:true});g.drawImage(img,0,0);
var d=g.getImageData(0,0,W,H).data,N=W*H,m=new Uint8Array(N),p,i;
for(i=0,p=0;p<N;p++,i+=4){var k=green?d[i+1]-Math.max(d[i],d[i+2]):Math.min(d[i],d[i+2])-d[i+1];if(k>110&&(green||Math.abs(d[i]-d[i+2])<90))m[p]=1}
var lab=new Int32Array(N),best=0,bestN=0,cur=0,stack=new Int32Array(N);
for(var s=0;s<N;s++){if(!m[s]||lab[s])continue;cur++;var top=0,n=0;stack[top++]=s;lab[s]=cur;
 while(top){p=stack[--top];n++;var x=p%W;
  if(x>0&&m[p-1]&&!lab[p-1]){lab[p-1]=cur;stack[top++]=p-1}
  if(x<W-1&&m[p+1]&&!lab[p+1]){lab[p+1]=cur;stack[top++]=p+1}
  if(p>=W&&m[p-W]&&!lab[p-W]){lab[p-W]=cur;stack[top++]=p-W}
  if(p<N-W&&m[p+W]&&!lab[p+W]){lab[p+W]=cur;stack[top++]=p+W}}
 if(n>bestN){bestN=n;best=cur}}
if(bestN<Math.max(400,N*0.004)){out.textContent=JSON.stringify({ok:false,kind:'no_key',keyed:bestN,w:W,h:H});return}
var pts=[],x0=W,y0=H,x1=0,y1=0;
for(p=0;p<N;p++){if(lab[p]!==best)continue;var px=p%W,py=(p-px)/W;if(px<x0)x0=px;if(px>x1)x1=px;if(py<y0)y0=py;if(py>y1)y1=py;
 if(px===0||px===W-1||py===0||py===H-1||lab[p-1]!==best||lab[p+1]!==best||lab[p-W]!==best||lab[p+W]!==best)pts.push([px,py])}
pts.sort(function(a,b){return a[0]-b[0]||a[1]-b[1]});function cr(o,a,b){return(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])}
var lo=[],up=[],q;for(i=0;i<pts.length;i++){q=pts[i];while(lo.length>1&&cr(lo[lo.length-2],lo[lo.length-1],q)<=0)lo.pop();lo.push(q)}
for(i=pts.length-1;i>=0;i--){q=pts[i];while(up.length>1&&cr(up[up.length-2],up[up.length-1],q)<=0)up.pop();up.push(q)}
var hull=lo.slice(0,-1).concat(up.slice(0,-1)),edges=[];
for(i=0;i<hull.length;i++){var a=hull[i],b=hull[(i+1)%hull.length],len=Math.hypot(b[0]-a[0],b[1]-a[1]);if(len>0)edges.push({a:a,b:b,len:len,ang:Math.atan2(b[1]-a[1],b[0]-a[0])})}
function dang(u,v){var t=Math.abs(u-v)%(2*Math.PI);return t>Math.PI?2*Math.PI-t:t}
var groups=[];edges.forEach(function(e){var gl=groups[groups.length-1];if(gl&&dang(gl.ang,e.ang)<0.07){gl.ang=Math.atan2(Math.sin(gl.ang)*gl.len+Math.sin(e.ang)*e.len,Math.cos(gl.ang)*gl.len+Math.cos(e.ang)*e.len);gl.len+=e.len;gl.b=e.b}
 else groups.push({a:e.a,b:e.b,len:e.len,ang:e.ang})});
if(groups.length>1&&dang(groups[0].ang,groups[groups.length-1].ang)<0.07){var last=groups.pop();groups[0].a=last.a;groups[0].len+=last.len}
var sorted=groups.slice().sort(function(u,v){return v.len-u.len}),L1=sorted[0],L2=null,S1=null,S2=null;
sorted.forEach(function(s){if(!L2&&s!==L1&&dang(s.ang,L1.ang)>2.6)L2=s});
var shorts=sorted.filter(function(s){return s!==L1&&s!==L2&&Math.min(dang(s.ang,L1.ang),Math.PI-dang(s.ang,L1.ang))>1.0});S1=shorts[0];
shorts.forEach(function(s){if(!S2&&S1&&s!==S1&&dang(s.ang,S1.ang)>2.6)S2=s});
if(!L2||!S1||!S2){out.textContent=JSON.stringify({ok:false,kind:'no_quad',groups:groups.length,keyed:bestN,w:W,h:H});return}
function fit(s){var dx=s.b[0]-s.a[0],dy=s.b[1]-s.a[1],L=Math.hypot(dx,dy),ux=dx/L,uy=dy/L,sel=[];
 for(var j=0;j<pts.length;j++){var t=(pts[j][0]-s.a[0])*ux+(pts[j][1]-s.a[1])*uy;if(t<L*0.12||t>L*0.88)continue;if(Math.abs((pts[j][0]-s.a[0])*uy-(pts[j][1]-s.a[1])*ux)<=2.5)sel.push(pts[j])}
 if(sel.length<8)return{px:s.a[0],py:s.a[1],ux:ux,uy:uy,n:sel.length};var mx=0,my=0;sel.forEach(function(v){mx+=v[0];my+=v[1]});mx/=sel.length;my/=sel.length;
 var sxx=0,sxy=0,syy=0;sel.forEach(function(v){var e=v[0]-mx,f=v[1]-my;sxx+=e*e;sxy+=e*f;syy+=f*f});var th=0.5*Math.atan2(2*sxy,sxx-syy);
 return{px:mx,py:my,ux:Math.cos(th),uy:Math.sin(th),n:sel.length}}
var sides=[L1,S1,L2,S2].map(function(s){return{s:s,f:fit(s)}});
function meet(A,B){var det=A.ux*(-B.uy)-(-B.ux)*A.uy,t=((B.px-A.px)*(-B.uy)-(-B.ux)*(B.py-A.py))/det;return[A.px+A.ux*t,A.py+A.uy*t]}
sides.sort(function(u,v){return hull.indexOf(u.s.a)-hull.indexOf(v.s.a)});
var corners=[0,1,2,3].map(function(j){return meet(sides[j].f,sides[(j+1)%4].f)});
var bw=x1-x0+3,bh=y1-y0+3,ox=x0-1,oy=y0-1,vis=new Uint8Array(bw*bh),qq=new Int32Array(bw*bh),qt=0;
function free(x,y){var X=x+ox,Y=y+oy;return X<0||Y<0||X>=W||Y>=H||lab[Y*W+X]!==best}
function push(x,y){var t=y*bw+x;if(!vis[t]&&free(x,y)){vis[t]=1;qq[qt++]=t}}
for(var bx=0;bx<bw;bx++){push(bx,0);push(bx,bh-1)}for(var by=0;by<bh;by++){push(0,by);push(bw-1,by)}
var NB=[[-1,0],[1,0],[0,-1],[0,1]];
while(qt){p=qq[--qt];var cx=p%bw,cy=(p-cx)/bw;NB.forEach(function(o){var nx=cx+o[0],ny=cy+o[1];if(nx>=0&&ny>=0&&nx<bw&&ny<bh)push(nx,ny)})}
var holes=[],hv=new Uint8Array(bw*bh);
for(s=0;s<bw*bh;s++){var hx=s%bw,hy=(s-hx)/bw;if(vis[s]||hv[s]||!free(hx,hy))continue;var hn=0,sx=0,sy=0;qt=0;qq[qt++]=s;hv[s]=1;
 while(qt){p=qq[--qt];var ax=p%bw,ay=(p-ax)/bw;hn++;sx+=ax;sy+=ay;for(var t2=0;t2<4;t2++){var nx2=ax+NB[t2][0],ny2=ay+NB[t2][1];if(nx2<0||ny2<0||nx2>=bw||ny2>=bh)continue;
   var np=ny2*bw+nx2;if(!vis[np]&&!hv[np]&&free(nx2,ny2)){hv[np]=1;qq[qt++]=np}}}
 holes.push({n:hn,cx:Math.round((sx/hn+ox)*10)/10,cy:Math.round((sy/hn+oy)*10)/10})}
holes=holes.filter(function(h){return h.n>=20&&h.n<bestN*0.03}).sort(function(u,v){return v.n-u.n});
var hist=new Uint32Array(256);for(p=0;p<N;p++)if(lab[p]===best)hist[green?d[p*4+1]:(d[p*4]+d[p*4+2])>>1]++;var acc=0,med=0;for(;med<256;med++){acc+=hist[med];if(acc>=bestN/2)break}
function r2(v){return Math.round(v*100)/100}
var gw=0.05*Math.max(x1-x0,y1-y0),stray=0;   // what the compositor would treat as key outside the screen box
for(i=0,p=0;p<N;p++,i+=4){var sx2=p%W,sy2=(p-sx2)/W;if(sx2>=x0-gw&&sx2<=x1+gw&&sy2>=y0-gw&&sy2<=y1+gw)continue;
 var k2=green?d[i+1]-Math.max(d[i],d[i+2]):Math.min(d[i],d[i+2])-d[i+1];if(k2>40&&(green||Math.abs(d[i]-d[i+2])<110))stray++}
out.textContent=JSON.stringify({ok:true,w:W,h:H,keyed:bestN,keyed_share:Math.round(bestN/N*10000)/10000,stray_key_share:Math.round(stray/N*10000)/10000,corners:corners.map(function(v){return[r2(v[0]),r2(v[1])]}),
 fit_points:sides.map(function(s){return s.f.n}),island:holes[0]||null,median_key_luma:med});
}catch(e){out.textContent=JSON.stringify({ok:false,kind:'js_error',message:String(e&&e.stack||e)})}});
"""

HOLE_JS = r"""
window.addEventListener('load',function(){var out=document.getElementById('lk-metrics');try{
var img=document.getElementById('scene'),W=img.naturalWidth,H=img.naturalHeight,c=document.createElement('canvas');c.width=W;c.height=H;
var g=c.getContext('2d',{willReadFrequently:true});g.drawImage(img,0,0);var d=g.getImageData(0,0,W,H).data,N=W*H,clear=new Uint8Array(N),any=0,p;
for(p=0;p<N;p++)if(d[p*4+3]<24){clear[p]=1;any++}
if(!any){out.textContent=JSON.stringify({ok:false,kind:'no_screen_hole',reason:'opaque',w:W,h:H});return}
var seen=new Uint8Array(N),stack=new Int32Array(N),top=0;
function seed(q){if(clear[q]&&!seen[q]){seen[q]=1;stack[top++]=q}}
function flood(cb){while(top){var q=stack[--top],x=q%W;if(cb)cb(q,x);if(x>0)seed(q-1);if(x<W-1)seed(q+1);if(q>=W)seed(q-W);if(q<N-W)seed(q+W)}}
for(var x=0;x<W;x++){seed(x);seed(N-W+x)}for(var y=0;y<H;y++){seed(y*W);seed(y*W+W-1)}flood(null);
var lab=new Int32Array(N),best=null,id=0;for(p=0;p<N;p++){if(!clear[p]||seen[p])continue;var o={id:++id,n:0,x0:W,y0:H,x1:0,y1:0};seed(p);
 flood(function(q,qx){var qy=(q-qx)/W;lab[q]=o.id;o.n++;if(qx<o.x0)o.x0=qx;if(qx>o.x1)o.x1=qx;if(qy<o.y0)o.y0=qy;if(qy>o.y1)o.y1=qy});if(!best||o.n>best.n)best=o}
if(!best||best.n<N*0.15){out.textContent=JSON.stringify({ok:false,kind:'no_screen_hole',reason:'no enclosed transparent area',w:W,h:H});return}
var bw=best.x1-best.x0+1,bh=best.y1-best.y0+1,radius=W;
// corner radius: walk the diagonal in from each corner of the hole's box; a round corner of radius r is first met at r(1-1/sqrt2)
[[best.x0,best.y0,1,1],[best.x1,best.y0,-1,1],[best.x0,best.y1,1,-1],[best.x1,best.y1,-1,-1]].forEach(function(c){
 for(var k=0;k<Math.min(bw,bh)/2;k++){if(lab[(c[1]+c[3]*k)*W+c[0]+c[2]*k]===best.id)break}radius=Math.min(radius,k/(1-Math.SQRT1_2))});
out.textContent=JSON.stringify({ok:true,w:W,h:H,screen:[best.x0,best.y0,bw,bh],fill:Math.round(best.n/(bw*bh)*1000)/1000,radius:Math.round(radius*10)/10});
}catch(e){out.textContent=JSON.stringify({ok:false,kind:'js_error',message:String(e&&e.stack||e)})}});
"""

COLORS_JS = r"""
window.addEventListener('load',function(){var out=document.getElementById('lk-metrics');try{
var img=document.getElementById('scene'),nw=img.naturalWidth,nh=img.naturalHeight;
function chan(v){v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)}
function lum(c){return 0.2126*chan(c[0])+0.7152*chan(c[1])+0.0722*chan(c[2])}
function hex(c){return'#'+c.map(function(v){return('0'+Math.max(0,Math.min(255,Math.round(v))).toString(16)).slice(-2)}).join('')}
function grab(x,y,w,h,tw,th){var c=document.createElement('canvas');c.width=tw;c.height=th;var g=c.getContext('2d',{willReadFrequently:true});
 g.imageSmoothingQuality='high';g.drawImage(img,x,y,w,h,0,0,tw,th);return g.getImageData(0,0,tw,th).data}
function bins(d){var map={},list=[],n=0;for(var i=0;i<d.length;i+=4){if(d[i+3]<128)continue;n++;var k=(d[i]>>4)<<8|(d[i+1]>>4)<<4|(d[i+2]>>4),o=map[k];
  if(!o){o=map[k]={n:0,r:0,g:0,b:0};list.push(o)}o.n++;o.r+=d[i];o.g+=d[i+1];o.b+=d[i+2]}
 list.forEach(function(o){o.c=[o.r/o.n,o.g/o.n,o.b/o.n]});list.sort(function(a,b){return b.n-a.n});return{list:list,n:n}}
function strip(y0,h){var tw=Math.min(240,nw),b=bins(grab(0,y0,nw,h,tw,Math.max(2,Math.round(h*tw/nw))));return b.list.length?hex(b.list[0].c):null}
var scale=Math.min(1,256/Math.max(nw,nh)),tw=Math.max(1,Math.round(nw*scale)),th=Math.max(1,Math.round(nh*scale));   // large captures are sampled small
var d=grab(0,0,nw,nh,tw,th),all=bins(d);
if(!all.n){out.textContent=JSON.stringify({ok:false,kind:'no_pixels',message:'the image is fully transparent'});return}
var groups=[];all.list.forEach(function(o){for(var i=0;i<groups.length;i++){var g=groups[i].c;
  if(Math.abs(g[0]-o.c[0])+Math.abs(g[1]-o.c[1])+Math.abs(g[2]-o.c[2])<54){groups[i].n+=o.n;return}}groups.push({c:o.c,n:o.n})});   // near-duplicates merge into the larger one
groups.sort(function(a,b){return b.n-a.n});
var accent=null,best=0;groups.forEach(function(g){var mx=Math.max(g.c[0],g.c[1],g.c[2]),mn=Math.min(g.c[0],g.c[1],g.c[2]),sat=mx?(mx-mn)/mx:0,val=mx/255;
 if(g.n/all.n>=0.005&&sat>=0.35&&val>=0.3&&sat*Math.sqrt(val)>best){best=sat*Math.sqrt(val);accent=hex(g.c)}});
var total=0,count=0;for(var i=0;i<d.length;i+=4){if(d[i+3]<128)continue;total+=lum([d[i],d[i+1],d[i+2]]);count++}
var edge=Math.max(2,Math.round(nh*0.006)),bg=groups[0].c;
out.textContent=JSON.stringify({ok:true,w:nw,h:nh,colors:{top_strip:strip(0,edge),bottom_strip:strip(nh-edge,edge),background:hex(bg),
 palette:groups.slice(0,6).map(function(g){return hex(g.c)}),accent:accent,luminance:Math.round(total/count*1000)/1000,scheme:lum(bg)>=0.4?'light':'dark'}});
}catch(e){out.textContent=JSON.stringify({ok:false,kind:'js_error',message:String(e&&e.stack||e)})}});
"""

# The PNG render in, the JPEG out: toDataURL is the synchronous twin of canvas.toBlob, and the load handler must
# finish before the DOM is dumped. Qualities are whole percent; only an encode that was measured under the
# budget is ever returned.
JPEG_JS = r"""
window.addEventListener('load',function(){var out=document.getElementById('lk-metrics');try{
var img=document.getElementById('scene'),J=window.LK_JPEG,c=document.createElement('canvas');c.width=img.naturalWidth;c.height=img.naturalHeight;
var g=c.getContext('2d',{alpha:false});g.fillStyle='#ffffff';g.fillRect(0,0,c.width,c.height);g.drawImage(img,0,0);var tried=[];
function enc(q){var u=c.toDataURL('image/jpeg',q/100),at=u.indexOf(',')+1,n=u.length-at,pad=u.slice(-2)==='=='?2:u.slice(-1)==='='?1:0,b=n*3/4-pad;
 if(u.slice(0,at)!=='data:image/jpeg;base64,')throw new Error('this browser gave '+u.slice(0,at)+' for image/jpeg');tried.push([q,b]);return{q:q,bytes:b,data:u.slice(at)}}
var best=enc(J.hi);
if(best.bytes>J.max){var low=enc(J.lo);
 if(low.bytes>J.max){out.textContent=JSON.stringify({ok:false,kind:'jpeg_over_budget',quality:J.lo,bytes:low.bytes,tried:tried});return}
 var a=J.lo,b=J.hi;best=low;while(b-a>1){var m=(a+b)>>1,r=enc(m);if(r.bytes<=J.max){a=m;best=r}else b=m}}
out.textContent=JSON.stringify({ok:true,quality:best.q,bytes:best.bytes,w:c.width,h:c.height,tried:tried,data:best.data});
}catch(e){out.textContent=JSON.stringify({ok:false,kind:'js_error',message:String(e&&e.stack||e)})}});
"""

# Supersampling factors. A hero scene warps the capture with matrix3d, which software-rendered headless Chromium
# samples without smoothing: every edge inside and around the screen steps. Measured 2026-09-24 on a hand-held
# tablet plate (RMS distance of the screen edge from a straight line): 0.156 px at 1x, 0.093 at 2x, 0.071 at 3x,
# 0.058 at 4x. A tilted card-flow capture only has a rotated rounded clip; 2x was enough there.
SUPERSAMPLE_WARP, SUPERSAMPLE_TILT = 3, 2
SUPERSAMPLE_MAX_PIXELS = 50000000    # a larger render falls back to 2x (browser canvas and shrink memory)
# The jagged_edge gate, median over a page's transformed edges (see edge_gate). Re-measured 2026-09-25 with the
# local-level edge estimate of SHRINK_JS on flat, UI, photographic JPEG and synthetic textured captures: hero scenes
# on 14 larger-screen plates and 8 phone plates, 1x 0.121 to 0.179 (an axis-parallel quad does not step: under 0.05),
# 2x at most 0.116, 3x and 4x at most 0.091; card-flow tilts of 2 to 8 degrees on play-feature, og and ph-gallery,
# caption top and left, 1x 0.072 to 0.088 where Chromium steps (6 of 68 pages it drew nearly smooth at 1x), 2x to 4x
# at most 0.053 (photographs 0.043). Each threshold sits midway between the worst supersampled and the best stepped page.
JAGGED_MEDIAN = {"warp": 0.11, "tilt": 0.06}

# A supersampled render shrunk by LK_SHRINK: each output pixel is the mean of an F x F block, rounded against a
# 4x4 Bayer threshold so the mean survives (plain rounding would undo the browser's gradient dither and band).
# A canvas only encodes RGBA PNG, which stores refuse, so the page returns PNG-filtered RGB scanlines (per row the
# filter with the smallest sum of absolute values) and Python deflates them into an RGB PNG.
# LK_EDGES are measured on the shrunk pixels. Per scan line across an edge: the pixel that holds the edge, within
# 1 px of the drawn line; the outside level from 2 to 4 px out and the inside level from the 3 px after that pixel,
# each flat within 4% of the contrast (at least 48 levels); the sub-pixel position is the outside share of the 3 px
# up to the edge. Only those few pixels count, so photo texture, UI lines and marks inside the capture no longer move
# the estimate (the 11 px profile before had 5 px of capture in it: a textured capture read 0.15 to 0.26 px at any
# factor). A line whose sides are uneven is skipped; an edge with under a quarter of its lines left is not judged.
SHRINK_JS = r"""
window.addEventListener('load',function(){var out=document.getElementById('lk-metrics');try{
var img=document.getElementById('scene'),F=window.LK_SHRINK,w=img.naturalWidth,h=img.naturalHeight,W=Math.round(w/F),H=Math.round(h/F);
if(W*F!==w||H*F!==h)throw new Error(w+'x'+h+' is not a multiple of '+F);
var a=document.createElement('canvas');a.width=w;a.height=h;var g=a.getContext('2d',{willReadFrequently:true});g.drawImage(img,0,0);
var s=g.getImageData(0,0,w,h).data,N=F*F,B=[0,8,2,10,12,4,14,6,3,11,1,9,15,7,13,5];
var R=W*3,rgb=new Uint8Array(R*H),raw=new Uint8Array((R+1)*H),cand=[0,1,2,3,4].map(function(){return new Uint8Array(R)});
for(var y=0;y<H;y++)for(var x=0;x<W;x++){var t=(B[(y&3)*4+(x&3)]+0.5)/16,i=y*R+x*3;
 for(var ch=0;ch<3;ch++){var sum=0;for(var v=0;v<F;v++)for(var u=0;u<F;u++)sum+=s[((y*F+v)*w+x*F+u)*4+ch];rgb[i+ch]=Math.floor(sum/N+t)}}
var edges=(window.LK_EDGES||[]).map(function(e){   // straightness of each transformed edge: RMS of the sub-pixel edge position from a line
 var dx=e[2]-e[0],dy=e[3]-e[1],steep=Math.abs(dy)>=Math.abs(dx),L=steep?Math.abs(dy):Math.abs(dx),pts=[],a0,a1;if(L<8)return{n:0,rms:null};
 // segments run clockwise on screen, so the capture lies along (-dy, dx): v runs from 8 px outside to 8 px inside
 var dir=(steep?-dy:dx)>0?1:-1,m3=function(p,q,r){return Math.max(Math.min(p,q),Math.min(Math.max(p,q),r))},up=function(p,q){return p-q};
 a0=Math.ceil((steep?Math.min(e[1],e[3]):Math.min(e[0],e[2]))+0.15*L);a1=Math.floor((steep?Math.max(e[1],e[3]):Math.max(e[0],e[2]))-0.15*L);
 for(var a=a0;a<=a1;a++){var c=steep?e[0]+(a-e[1])*dx/dy:e[1]+(a-e[0])*dy/dx,m=Math.floor(c),v=[],ok=true;
  for(var k=0;k<17;k++){var q=m+dir*(k-8),px=steep?q:a,py=steep?a:q;if(px<0||py<0||px>=W||py>=H){ok=false;break}var i=py*R+px*3;v.push(0.299*rgb[i]+0.587*rgb[i+1]+0.114*rgb[i+2])}
  if(!ok)continue;var far0=m3(v[0],v[1],v[2]),far1=m3(v[14],v[15],v[16]);if(Math.abs(far1-far0)<48)continue;
  var sg=far1>far0?1:-1,t=-1;for(k=7;k<=9;k++)if(sg*(v[k]-(far0+far1)/2)>=0){t=k;break}   // the pixel holding the edge, within 1 px of the line
  if(t<0)continue;
  // local levels: outside from 2..4 px out, inside from the 3 px after the edge pixel (fully covered for a slope under 1).
  // Photo texture, UI lines or a dark band at the edge make either side uneven or the ramp non-monotonic: skip the line.
  var bo=m3(v[t-4],v[t-3],v[t-2]),ins=[v[t+1],v[t+2],v[t+3]].sort(up),bi=ins[1],C=sg*(bi-bo),tol=0.04*C;
  if(C<48||Math.abs(v[t-4]-bo)>tol||Math.abs(v[t-3]-bo)>tol||ins[2]-bi>tol||bi-ins[0]>tol)continue;
  if(sg*(v[t-1]-v[t-2])<-tol||sg*(v[t]-v[t-1])<-tol||sg*(v[t+1]-v[t])<-tol||sg*(v[t]-(bo+bi)/2)<0||sg*(v[t-1]-(bo+bi)/2)>=0)continue;
  var cov=0;for(k=t-2;k<=t;k++)cov+=Math.min(1,Math.max(0,(bi-v[k])/(bi-bo)));   // outside share of the 3 px up to the edge
  pts.push([a,dir>0?m-8+t-2+cov:m+9-(t-2+cov)])}
 // an edge whose content leaves under a quarter of its lines clean is not judged
 var n=pts.length;if(n<Math.max(20,0.25*(a1-a0+1)))return{n:n,rms:null};   // a quadratic takes the slow bend of a generated screen edge; steps stay in the residual
 var ma=0;pts.forEach(function(q){ma+=q[0]});ma/=n;var sc=Math.max(1,(a1-a0)/2),M=[[0,0,0],[0,0,0],[0,0,0]],V=[0,0,0];
 pts.forEach(function(q){var t=(q[0]-ma)/sc,b=[1,t,t*t];for(var r=0;r<3;r++){V[r]+=b[r]*q[1];for(var c2=0;c2<3;c2++)M[r][c2]+=b[r]*b[c2]}});
 for(var r=0;r<3;r++){var piv=M[r][r]||1e-12;for(var c2=r+1;c2<3;c2++){var f2=M[c2][r]/piv;for(var c3=r;c3<3;c3++)M[c2][c3]-=f2*M[r][c3];V[c2]-=f2*V[r]}}
 var co=[0,0,0];for(r=2;r>=0;r--){var acc=V[r];for(c2=r+1;c2<3;c2++)acc-=M[r][c2]*co[c2];co[r]=acc/(M[r][r]||1e-12)}
 var ss=0;pts.forEach(function(q){var t=(q[0]-ma)/sc,res=q[1]-(co[0]+co[1]*t+co[2]*t*t);ss+=res*res});
 return{n:n,rms:Math.round(Math.sqrt(ss/n)*1000)/1000}});
for(var y=0;y<H;y++){var best=0,low=Infinity,o=y*R;
 for(var f=0;f<5;f++){var cf=cand[f],cost=0;for(var j=0;j<R;j++){var a=j>=3?rgb[o+j-3]:0,b=y?rgb[o-R+j]:0,cc=j>=3&&y?rgb[o-R+j-3]:0,p,e;
   if(f===0)p=0;else if(f===1)p=a;else if(f===2)p=b;else if(f===3)p=(a+b)>>1;else{var q=a+b-cc,pa=Math.abs(q-a),pb=Math.abs(q-b),pc=Math.abs(q-cc);p=pa<=pb&&pa<=pc?a:pb<=pc?b:cc}
   e=(rgb[o+j]-p)&255;cf[j]=e;cost+=e<128?e:256-e}
  if(cost<low){low=cost;best=f}}
 raw[y*(R+1)]=best;raw.set(cand[best],y*(R+1)+1)}
var bin='';for(var j=0;j<raw.length;j+=32768)bin+=String.fromCharCode.apply(null,raw.subarray(j,j+32768));
out.textContent=JSON.stringify({ok:true,w:W,h:H,rows:btoa(bin),edges:edges});
}catch(e){out.textContent=JSON.stringify({ok:false,kind:'js_error',message:String(e&&e.stack||e)})}});
"""

PAGE_CSS = """*{box-sizing:border-box}html,body{margin:0;padding:0}
body{position:relative;overflow:hidden;-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
canvas,img{display:block}#lk-bg,#lk-plate{position:absolute;left:0;top:0}.lk-src,#lk-metrics{display:none}
.lk-tb{position:absolute;display:flex;flex-direction:column;z-index:8}.lk-tbi{display:flex;flex-direction:column}
.lk-h{font-weight:var(--wh);font-size:var(--fs);line-height:1.06;letter-spacing:var(--track);color:var(--fg)}
.lk-h .l,.lk-sub .l{white-space:nowrap}.lk-h .em{color:var(--accent)}
.lk-sub{font-weight:var(--wb);font-size:max(calc(var(--fs)*var(--sub)),var(--min-px));line-height:1.32;color:var(--fg-alt);margin-top:calc(var(--fs)*0.34)}
.lk-tbi>.lk-sub:first-child{margin-top:0}
.lk-badge{display:inline-block;font-weight:700;font-size:max(calc(var(--fs)*var(--badge)),var(--min-px));line-height:1;letter-spacing:var(--badge-track);padding:var(--badge-pad,0.62em 1.15em);
border-radius:99em;background:var(--badge-bg);color:var(--badge-fg);margin-bottom:calc(var(--fs)*0.4);white-space:nowrap}
.lk-rule{width:calc(var(--fs)*1.15);height:calc(var(--fs)*0.1);border-radius:99px;background:var(--accent);margin-bottom:calc(var(--fs)*0.46)}
.lk-shadowed .lk-h,.lk-shadowed .lk-sub{text-shadow:0 2px 28px var(--halo)}
.lk-lockup{position:absolute;display:flex;align-items:center;z-index:8;color:var(--fg);font-weight:700;letter-spacing:-0.01em;white-space:nowrap}
.lk-lockup img{height:100%;width:auto}.lk-lockup img.lk-icon{border-radius:22.5%;aspect-ratio:1/1;object-fit:cover}
.lk-dev{position:absolute}.lk-body,.lk-bezel,.lk-screen,.lk-cut,.lk-btn,.lk-pill,.lk-time,.lk-cluster,.lk-cap{position:absolute}
.lk-screen{overflow:hidden;background:#000}.lk-cut{background:#000}.lk-cap{left:0}.lk-strip,.lk-cover{position:absolute;left:0;width:100%}.lk-cover{top:0;display:none}
.lk-glyphs{position:absolute;left:0;top:0;width:100%;height:0;color:#000}.lk-time{white-space:nowrap;line-height:1}
.lk-cluster{display:flex;align-items:center}.lk-cluster svg{display:block;fill:currentColor}.lk-ibar{position:absolute;overflow:hidden}
.lk-ibar svg{display:block;position:absolute;top:0}
.lk-pill{border-radius:99px;left:50%;transform:translateX(-50%)}
.lk-win{overflow:hidden;background:var(--bar)}.lk-tbar{position:absolute;left:0;top:0;width:100%;background:var(--bar);display:flex;align-items:center}
.lk-dots{display:flex}.lk-dots i{display:block;border-radius:50%}.lk-dots i.d{display:none}.lk-win.lk-dark .lk-dots i.l{display:none}.lk-win.lk-dark .lk-dots i.d{display:block}
.lk-addr{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);border-radius:99px;background:var(--pill);color:var(--txt);display:flex;
align-items:center;justify-content:center;white-space:nowrap;overflow:hidden}
.lk-title{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);color:var(--txt);font-weight:600;white-space:nowrap}
.lk-edge{position:absolute;left:0;top:0;right:0;bottom:0;border:1px solid var(--edge);pointer-events:none}
.lk-win.lk-dark,.lk-win.lk-dark .lk-tbar{background:var(--bar-d)}.lk-win.lk-dark .lk-addr{background:var(--pill-d);color:var(--txt-d)}
.lk-win.lk-dark .lk-title{color:var(--txt-d)}.lk-win.lk-dark .lk-edge{border-color:var(--edge-d)}
.lk-card{overflow:hidden;background:#000}.lk-decor{position:absolute;z-index:6}.lk-mono{position:absolute;display:flex;align-items:center;justify-content:center;
font-weight:800;color:var(--fg)}
"""


# ----------------------------------------------------------------------------------------------- geometry

def strips_for(action, top_bar, bottom_bar):
    """Fractions of the screen's short side added above and below the capture."""
    if action in ("extend", "extend_blank"):
        return ((top_bar or {}).get("height") or 0.0, (bottom_bar or {}).get("height") or 0.0)
    return (0.0, 0.0)


def body_geometry(frame, body_w, cap_w, cap_h, strips, bezel_asset=None):
    """The screen takes the capture's aspect (plus added strips); the body follows with a constant bezel."""
    if bezel_asset:
        scale = body_w / float(bezel_asset["size"][0])
        sx, sy, sw, sh = (v * scale for v in bezel_asset["screen"])
        sw_i = int(round(sw))
        cap_px = int(round(sw_i * cap_h / float(cap_w)))
        short = min(sw_i, cap_px)
        top, bottom = int(round(strips[0] * short)), int(round(strips[1] * short))
        return {"bw": body_w, "bh": bezel_asset["size"][1] * scale, "sx": sx, "sy": sy, "sw": sw_i, "sh": int(round(sh)),
                "short": short, "top": top, "bottom": bottom, "cap_h": int(round(sh)) - top - bottom, "bar": 0, "bez": 0.0}
    if frame["kind"] == "window":
        bar = int(round(max(frame["titlebar"]["min_px"], frame["titlebar"]["height"] * body_w)))
        sw = int(round(body_w))
        cap_px = int(round(sw * cap_h / float(cap_w)))
        return {"bw": float(sw), "bh": float(bar + cap_px), "sx": 0.0, "sy": float(bar), "sw": sw, "sh": cap_px,
                "short": min(sw, cap_px), "top": 0, "bottom": 0, "cap_h": cap_px, "bar": bar, "bez": 0.0}
    bez = round(frame.get("bezel", 0) * body_w, 1)
    sw = int(round(body_w - 2 * bez))
    cap_px = int(round(sw * cap_h / float(cap_w)))
    short = min(sw, cap_px)
    top, bottom = int(round(strips[0] * short)), int(round(strips[1] * short))
    sh = cap_px + top + bottom
    return {"bw": sw + 2 * bez, "bh": sh + 2 * bez, "sx": bez, "sy": bez, "sw": sw, "sh": sh, "short": short,
            "top": top, "bottom": bottom, "cap_h": cap_px, "bar": 0, "bez": bez}


def fit_body_width(shot, zone_w, zone_h):
    width = float(zone_w)
    for _ in range(3):
        geo = body_geometry(shot["frame"], width, shot["cw"], shot["ch"], shot["strips"], shot.get("bezel_asset"))
        if geo["bh"] <= zone_h:
            break
        width = width * zone_h / geo["bh"]
    return width


def flow_tilts(slide):
    """card-flow tilt as [left, right] degrees: a number t tilts the pair apart (-t, t); a list names both."""
    tilt = slide.get("tilt") if LAYOUTS.get(slide.get("layout"), {}).get("flow") else None
    if isinstance(tilt, list):
        return [float(tilt[0]), float(tilt[1])]
    return [-float(tilt), float(tilt)] if tilt else [0.0, 0.0]


def supersample(slide, pixels=0):
    """A page with a transformed capture renders at a multiple of its pixels and is shrunk back in the browser:
    headless Chromium draws a rotated rounded clip and a matrix3d-warped screen without anti-aliasing, which reads
    as jagged steps along every edge. `pixels` is the output size (width x height at the export scale)."""
    if slide.get("layout") == "card-hero-scene":
        return SUPERSAMPLE_WARP if pixels * SUPERSAMPLE_WARP ** 2 <= SUPERSAMPLE_MAX_PIXELS else 2
    return SUPERSAMPLE_TILT if any(flow_tilts(slide)) else 1


def flow_width(shot, height):
    """Body width at which this capture's body (frame, strips and title bar included) is `height` tall."""
    width = height * shot["cw"] / float(shot["ch"])
    for _ in range(3):
        geo = body_geometry(shot["frame"], width, shot["cw"], shot["ch"], shot["strips"], shot.get("bezel_asset"))
        width = width * height / geo["bh"]
    return width


def safe_box(target, W, H):
    """(x0, y0, x1, y1) of the target's safe area on this canvas, from `safe_insets` as shares of the sides."""
    insets = target.get("safe_insets") or {}
    return (insets.get("left", 0) * W, insets.get("top", 0) * H,
            W - insets.get("right", 0) * W, H - insets.get("bottom", 0) * H)


def shift_plan(plan, dx, dy):
    """Move every box of a plan laid out on an inner canvas onto the full canvas."""
    for block in plan["blocks"]:
        block["box"][0] = round(block["box"][0] + dx, 1)
        block["box"][1] = round(block["box"][1] + dy, 1)
    for dev in plan["devices"]:
        dev["x"] = round(dev["x"] + dx, 1)
        dev["y"] = round(dev["y"] + dy, 1)
    if plan["zoom"]:
        zx, zy, zw, zh = plan["zoom"]
        plan["zoom"] = (zx + dx, zy + dy, zw, zh)
    if plan["lockup"]:
        plan["lockup"]["x"] += dx
        plan["lockup"]["y"] += dy
    if plan["icon"]:
        ix, iy, side = plan["icon"]
        plan["icon"] = (ix + dx, iy + dy, side)
    if plan["connector"]:
        plan["connector"]["x"] += dx
        plan["connector"]["y"] += dy
    return plan


def plan_page(layout, W, H, slide, shots, quad_box=None, has_sub=True, copy=None, min_px=0.0, gutter=0.0, safe_top=0.0,
              safe=None, lockup=True, compact=False, device_top=None):
    """Boxes of one page in canvas pixels: text blocks, device bodies, zoom card, lockup, icon, connector.
    safe_top: share of the height a placement covers with its own interface; portrait text starts below it.
    safe: (x0, y0, x1, y1) of a box the surface never crops; a card layout is laid out inside it and does not
    bleed unless the slide asks for it, so only background reaches the cutoff zones.
    lockup: False when the page draws no lockup; card-flow then gives its room to the captures. On card-lockup it is
    {width_px, aspect}: the asked width in canvas pixels and the lockup's width over its height, as far as known.
    compact: without a lockup, the lockup's room goes to the copy (COMPACT_CENTERED_PHONE); with one it does nothing.
    device_top: the hung capture's top edge as a share of the height (DEVICE_TOP_LAYOUTS), None = the layout's own."""
    if safe and "card" in LAYOUTS[layout]["kinds"]:
        x0, y0, x1, y1 = safe
        inner = dict(slide)
        if inner.get("bleed") is None:
            inner["bleed"] = False
        quad = [quad_box[0] - x0, quad_box[1] - y0, quad_box[2], quad_box[3]] if quad_box else None
        plan = plan_page(layout, x1 - x0, y1 - y0, inner, shots, quad_box=quad, has_sub=has_sub, copy=copy,
                         min_px=min_px, gutter=max(0.0, gutter - min(x0, y0)), lockup=lockup, compact=compact,
                         device_top=device_top)
        return shift_plan(plan, x0, y0)
    close = bool(compact) and not lockup          # the lockup's empty room goes to the copy
    spec = LAYOUTS[layout]
    portrait = H >= W * 1.1
    unit = min(W, H * 1.9)
    plan = {"blocks": [], "devices": [], "zoom": None, "lockup": None, "icon": None, "connector": None, "head": 0.0, "sub": 0.40,
            "badge": 0.27, "rule": False, "shadowed": False, "text_side": None}
    flag = slide.get("bleed")

    def block(box, align, valign, parts=("badge", "headline", "sub")):
        plan["blocks"].append({"id": "tb%d" % len(plan["blocks"]), "box": [round(v, 1) for v in box], "align": align,
                               "valign": valign, "parts": list(parts)})

    def place(index, width, x, y, z=3):
        shot = shots[index]
        geo = body_geometry(shot["frame"], width, shot["cw"], shot["ch"], shot["strips"], shot.get("bezel_asset"))
        geo.update({"shot": index, "x": round(x, 1), "y": round(y, 1), "z": z})
        plan["devices"].append(geo)
        return geo

    def contain(index, zone, z=3):
        zx, zy, zw, zh = zone
        shot = shots[index]
        width = fit_body_width(shot, zw, zh)
        geo = body_geometry(shot["frame"], width, shot["cw"], shot["ch"], shot["strips"], shot.get("bezel_asset"))
        return place(index, width, zx + (zw - geo["bw"]) / 2.0, zy + (zh - geo["bh"]) / 2.0, z)

    def drop(index, width, centre_x, top, floor, bleed, z=3, from_bottom=False):
        """A device hung from `top` (or standing on `floor`); centred in the zone when it fits as a whole."""
        shot = shots[index]
        if not bleed:
            return contain(index, (centre_x - width / 2.0, top, width, floor - top), z)
        geo = body_geometry(shot["frame"], width, shot["cw"], shot["ch"], shot["strips"], shot.get("bezel_asset"))
        if geo["bh"] <= floor - top:
            y = top + (floor - top - geo["bh"]) / 2.0
        else:
            y = floor - geo["bh"] if from_bottom else top
        return place(index, width, centre_x - geo["bw"] / 2.0, y, z)

    def wide(index):
        return shots[index]["cw"] > shots[index]["ch"]

    def body_share(index):
        kind = shots[index]["frame"]["kind"]
        return 0.80 if kind == "phone" and not wide(index) else 0.86

    if layout in ("device-bottom", "device-top", "two-devices", "zoom", "device-center"):
        bleed = spec["bleed"] if flag is None else flag
        if portrait:
            plan["head"] = (0.084 if layout == "device-center" else 0.092) * W
            if layout == "device-top":
                block((0.07 * W, 0.725 * H, 0.86 * W, 0.215 * H), "center", "center")
                drop(0, body_share(0) * W, W / 2.0, 0.035 * H, 0.705 * H, bleed, from_bottom=True)
            elif layout == "device-center" and safe_top:      # the sub line joins the headline: the bottom strip is not for text
                down = max(0.0, safe_top + 0.01 - 0.05) * H
                block((0.07 * W, 0.05 * H + down, 0.86 * W, 0.19 * H), "center", "center")
                contain(0, (0.10 * W, 0.255 * H + down, 0.80 * W, 0.695 * H - down))
            elif layout == "device-center":
                block((0.07 * W, 0.05 * H, 0.86 * W, 0.15 * H), "center", "center", ("badge", "headline"))
                if has_sub:
                    block((0.10 * W, 0.885 * H, 0.80 * W, 0.075 * H), "center", "center", ("sub",))
                contain(0, (0.10 * W, 0.215 * H, 0.80 * W, (0.655 if has_sub else 0.735) * H))
            else:
                down = max(0.0, safe_top + 0.01 - 0.06) * H if safe_top else 0.0
                block((0.07 * W, 0.06 * H + down, 0.86 * W, 0.215 * H), "center", "center")
                if layout == "device-bottom":
                    drop(0, body_share(0) * W, W / 2.0, 0.295 * H + down, 0.965 * H, bleed)
                elif layout == "two-devices":
                    drop(1, 0.62 * W, 0.66 * W, 0.30 * H + down, 0.965 * H, bleed, z=3)
                    drop(0, 0.68 * W, 0.37 * W, 0.345 * H + down, 0.965 * H, bleed, z=4)
                else:                      # the whole screen stays behind as context, the crop comes forward
                    drop(0, 0.74 * W, W / 2.0, 0.30 * H + down, 0.965 * H, True, z=3)
                    plan["devices"][-1]["context"] = True
                    plan["zoom"] = (0.04 * W, 0.36 * H + down, 0.92 * W, 0.50 * H)
        else:
            plan["head"] = 0.083 * H
            stacked = layout == "device-center" or (shots and wide(0) and layout != "two-devices")
            if stacked:
                plan["head"] = 0.07 * H
                block((0.08 * W, 0.045 * H, 0.84 * W, 0.225 * H), "center", "center")
                if layout == "zoom":
                    plan["zoom"] = (0.12 * W, 0.30 * H, 0.76 * W, 0.65 * H)
                else:
                    contain(0, (0.12 * W, 0.30 * H, 0.76 * W, 0.65 * H))
            else:
                right = layout != "device-top"          # the device stands right, the text left
                text_x, centre = (0.06 * W, 0.73 * W) if right else (0.54 * W, 0.27 * W)
                block((text_x, 0.14 * H, 0.40 * W, 0.72 * H), "left", "center")
                if layout == "zoom":
                    plan["zoom"] = (centre - 0.22 * W, 0.10 * H, 0.44 * W, 0.80 * H)
                elif layout == "two-devices":
                    drop(1, 0.20 * W, centre + 0.10 * W, 0.16 * H, 0.95 * H, bleed, z=3)
                    drop(0, 0.22 * W, centre - 0.10 * W, 0.22 * H, 0.95 * H, bleed, z=4)
                else:
                    drop(0, 0.26 * W, centre, 0.17 * H, 0.94 * H, bleed)
    elif spec.get("span"):
        # One device centred on the seam: device-span draws it about its right edge, device-span-end about its left
        # edge, with the same geometry, so the two crops meet. Each slide keeps its own copy on its own side.
        seam = float(W) if spec["span"] == "start" else 0.0
        bleed = spec["bleed"] if flag is None else flag
        if portrait:
            plan["head"] = 0.092 * W
            down = max(0.0, safe_top + 0.01 - 0.06) * H if safe_top else 0.0
            block((0.07 * W, 0.06 * H + down, 0.86 * W, 0.215 * H), "center", "center")
            if wide(0):             # a landscape capture across two portrait slides: contained, up to 0.86 of each
                contain(0, (seam - 0.86 * W, 0.295 * H + down, 1.72 * W, 0.67 * H - down))
            else:
                drop(0, body_share(0) * W, seam, 0.295 * H + down, 0.965 * H, bleed)
        elif wide(0):
            plan["head"] = 0.07 * H
            block((0.08 * W, 0.045 * H, 0.84 * W, 0.225 * H), "center", "center")
            contain(0, (seam - 0.76 * W, 0.30 * H, 1.52 * W, 0.65 * H))
        else:
            plan["head"] = 0.083 * H
            text_x = 0.06 * W if spec["span"] == "start" else 0.54 * W       # the text keeps to the side away from the seam
            block((text_x, 0.14 * H, 0.40 * W, 0.72 * H), "left", "center")
            drop(0, 0.26 * W, seam, 0.17 * H, 0.94 * H, bleed)
    elif layout == "text-only":
        plan["head"] = 0.126 * W if portrait else 0.14 * H
        plan["sub"] = 0.34
        block((0.07 * W, 0.16 * H, 0.86 * W, 0.62 * H), "center", "center")
        plan["lockup"] = {"x": 0.0, "w": float(W), "y": 0.865 * H, "h": 0.06 * min(W, H) * (1.0 if portrait else 1.4), "align": "center",
                          "muted": True}
    elif layout == "card-left-title":
        plan["head"] = 0.060 * unit
        plan["sub"] = 0.37
        plan["lockup"] = {"x": 0.06 * W, "w": 0.88 * W, "y": 0.095 * H, "h": 0.088 * H, "align": "left"}
        block((0.06 * W, (0.12 if close else 0.25) * H, 0.44 * W, (0.76 if close else 0.63) * H), "left", "center")
        if shots[0]["frame"]["kind"] == "window" or wide(0):
            if flag is True:
                geo = body_geometry(shots[0]["frame"], 0.62 * W, shots[0]["cw"], shots[0]["ch"], shots[0]["strips"])
                place(0, 0.62 * W, 0.535 * W, (H - geo["bh"]) / 2.0)
            else:
                contain(0, (0.525 * W, 0.13 * H, 0.425 * W, 0.74 * H))
        else:
            drop(0, 0.27 * W, 0.745 * W, (0.105 if device_top is None else device_top) * H, 0.92 * H, flag is not False)
    elif layout == "card-centered":
        plan["head"] = 0.062 * unit
        plan["sub"] = 0.36
        plan["lockup"] = {"x": 0.0, "w": float(W), "y": 0.085 * H, "h": 0.085 * H, "align": "center"}
        if shots:
            block((0.10 * W, (0.11 if close else 0.215) * H, 0.80 * W, 0.325 * H), "center", "center")
            is_window = shots[0]["frame"]["kind"] == "window" or wide(0)
            phone, top = COMPACT_CENTERED_PHONE if close else (0.22, 0.585)
            width = (0.64 if is_window else phone) * W
            drop(0, width, W / 2.0, (top if device_top is None else device_top) * H, 0.95 * H, flag is not False)
        else:
            block((0.10 * W, 0.24 * H, 0.80 * W, 0.62 * H), "center", "center")
    elif layout == "card-minimal":
        plan["head"] = 0.074 * unit
        plan["sub"] = 0.34
        plan["rule"] = True
        plan["lockup"] = {"x": 0.06 * W, "w": 0.88 * W, "y": 0.095 * H, "h": 0.088 * H, "align": "left"}
        block((0.06 * W, 0.27 * H, 0.80 * W, 0.62 * H), "left", "bottom")
    elif layout == "card-browser":
        plan["head"] = 0.043 * unit
        plan["sub"] = 0.5
        # the caption grows with its content (badge, second line, sub at the target's type floor); the window follows
        head, entry = plan["head"], copy or {}
        need = 1.06 * head * max(1, len(entry.get("headline") or [])) + 0.02 * H
        if entry.get("sub"):
            need += 0.34 * head + 1.32 * max(plan["sub"] * head, min_px) * len(entry["sub"])
        if entry.get("badge"):
            need += 2.24 * max(plan["badge"] * head, min_px) + 0.4 * head
        caption = min(0.42 * H, max(0.18 * H, need))
        start = max(0.055 * H, gutter + 2.0)
        block((0.08 * W, start, 0.84 * W, caption), "center", "center")
        top = start + caption + 0.035 * H
        if flag is True:
            drop(0, 0.80 * W, W / 2.0, top, 0.94 * H, True)
        else:
            contain(0, (0.10 * W, top, 0.80 * W, 0.935 * H - top))
    elif layout == "card-flow":
        # before -> after: two captures at one height, centred as a row; lockup and copy above it when present, or on
        # the left exactly where card-left-title puts them (caption: left), so a series of cards shares one type size
        entry = copy or {}
        worded = bool(entry.get("headline") or entry.get("sub") or entry.get("badge"))
        if slide.get("caption") == "left" and (worded or lockup):
            plan["head"] = 0.060 * unit
            plan["sub"] = 0.37
            if lockup:
                plan["lockup"] = {"x": 0.06 * W, "w": 0.44 * W, "y": 0.095 * H, "h": 0.088 * H, "align": "left"}
            if worded:
                block((0.06 * W, (0.12 if close else 0.25) * H, 0.44 * W, (0.76 if close else 0.63) * H), "left", "center")
            zx, zy, zw, zh = 0.52 * W, 0.10 * H, 0.42 * W, 0.80 * H
        else:                   # caption top; also a left caption with nothing to hold: the pair takes the card
            plan["head"] = 0.056 * unit
            plan["sub"] = 0.42
            top = 0.07 * H
            if lockup:
                plan["lockup"] = {"x": 0.0, "w": float(W), "y": top, "h": 0.08 * H, "align": "center"}
                top += 0.11 * H
            if worded:
                head = plan["head"]
                need = 1.06 * head * len(entry.get("headline") or []) + 0.02 * H
                if entry.get("sub"):
                    need += 0.34 * head + 1.32 * max(plan["sub"] * head, min_px) * len(entry["sub"])
                if entry.get("badge"):
                    need += 2.24 * max(plan["badge"] * head, min_px) + 0.4 * head
                caption = min(0.34 * H, max(0.12 * H, need))
                block((0.08 * W, top, 0.84 * W, caption), "center", "center")
                top += caption + 0.035 * H
            zx, zy, zw, zh = 0.06 * W, top, 0.88 * W, 0.93 * H - top
        arrow = slide.get("connector", "arrow") != "none"
        link = 0.30 if arrow else 0.12                  # the space between the two, as a share of their height
        ratios = [flow_width(shots[i], 1000.0) / 1000.0 for i in (0, 1)]
        tilts = flow_tilts(slide)
        turn = [(math.cos(math.radians(t)), abs(math.sin(math.radians(t)))) for t in tilts]
        # a tilted capture takes the room of its rotated box: per unit of height r*cos+sin wide, r*sin+cos tall
        height = min(zh / max(r * sn + cs for r, (cs, sn) in zip(ratios, turn)),
                     zw / (sum(r * cs + sn for r, (cs, sn) in zip(ratios, turn)) + link))
        widths = [flow_width(shots[i], height) for i in (0, 1)]
        slots = [w * cs + height * sn for w, (cs, sn) in zip(widths, turn)]
        x = zx + (zw - sum(slots) - link * height) / 2.0
        for index in (0, 1):
            geo = place(index, widths[index], x + (slots[index] - widths[index]) / 2.0, zy)
            geo["y"] = round(zy + (zh - geo["bh"]) / 2.0, 1)
            geo["tilt"] = tilts[index]
            x += slots[index] + (link * height if index == 0 else 0.0)
        if arrow:
            side = 0.16 * height
            plan["connector"] = {"x": round(x - slots[1] - link * height / 2.0 - side / 2.0, 1),
                                 "y": round(zy + (zh - side) / 2.0, 1), "w": round(side, 1), "h": round(side, 1)}
    elif layout == "card-hero-scene":
        if quad_box is None:
            raise Fail("deck_invalid", "layout card-hero-scene needs a plate with a screen quad")
        plan["head"] = 0.060 * unit
        plan["sub"] = 0.37
        plan["shadowed"] = True
        qx, _qy, qw, _qh = quad_box
        left = qx + qw / 2.0 >= W / 2.0
        plan["text_side"] = "left" if left else "right"
        x0 = 0.06 * W if left else qx + qw + 0.05 * W
        x1 = qx - 0.05 * W if left else 0.94 * W
        plan["lockup"] = {"x": x0, "w": max(1.0, x1 - x0), "y": 0.095 * H, "h": 0.088 * H, "align": "left"}
        block((x0, 0.25 * H, max(1.0, x1 - x0), 0.63 * H), "left", "center")
    elif layout == "card-lockup":
        # the lockup alone, centred in a zone with the usual card margins; the page scales it to the asked width
        fill = lockup if isinstance(lockup, dict) else {}
        zx, zy, zw, zh = 0.06 * W, 0.10 * H, 0.88 * W, 0.80 * H
        width = min(fill.get("width_px") or LOCKUP_WIDTH * W, zw)
        plan["lockup"] = {"x": zx, "w": zw, "y": zy, "h": zh, "align": "center",
                          "inner": round(min(zh, width / (fill.get("aspect") or 3.0)), 1)}
    elif layout == "thumb-icon":
        side = 0.62 * min(W, H)
        plan["icon"] = ((W - side) / 2.0, (H - side) / 2.0, side)
    return plan


def hero_scrim(W, box, side_left, alpha, light_text):
    """The shade a hero scene lays on its plate under the lockup and text: full strength from the card's edge to the
    text block's far side, then eased out to nothing over HERO_SCRIM_FADE of the width. The fade may pass under the
    device and the hand; the keyed screen is a hole in the plate, so the capture is never shaded. It used to end at
    the device's near edge: with a large phone close to the text that was a 60 px ramp, and a vertical seam in the
    open sky above the phone (2026-09-25). x0 -> x1 runs from the text side; `hold` is where the fade starts."""
    text_edge = (box[0] + box[2]) if side_left else (W - box[0])          # from the text side to the block's far side
    reach = min(float(W), text_edge + HERO_SCRIM_FADE * W)
    hold = min(0.9, max(0.3, (text_edge + 0.02 * W) / reach))
    return {"x0": 0 if side_left else W, "x1": round(reach if side_left else W - reach, 1), "hold": round(hold, 3),
            "color": [0, 0, 0] if light_text else [255, 255, 255], "alpha": alpha}


def hero_mapping(plate_w, plate_h, quad, W, H, margins=None):
    """Cover-fit the plate on the canvas, shifted so the screen quad stays in view. -> (draw rect, quad on canvas).
    margins: (left, top, right, bottom) in pixels the quad is held inside; default 4% of the width, 3% of the height."""
    left, top, right, bottom = margins or (0.04 * W, 0.03 * H, 0.04 * W, 0.03 * H)
    scale = max(W / float(plate_w), H / float(plate_h))
    dw, dh = plate_w * scale, plate_h * scale
    dx, dy = (W - dw) / 2.0, (H - dh) / 2.0
    box = quad_bbox([(x * scale + dx, y * scale + dy) for x, y in quad])
    for axis, size, near, far in ((0, W, left, right), (1, H, top, bottom)):
        low, high = box[axis], box[axis] + box[axis + 2]
        shift = 0.0
        if low < near:
            shift = near - low
        elif high > size - far:
            shift = (size - far) - high
        if axis == 0:
            dx = min(0.0, max(W - dw, dx + shift))
        else:
            dy = min(0.0, max(H - dh, dy + shift))
    return [dx, dy, dw, dh], [(x * scale + dx, y * scale + dy) for x, y in quad]


def cover_rect(image_w, image_h, W, H, index=0, count=1):
    """Cover-fit an image on a strip of `count` canvases and return the draw rect for canvas `index`."""
    total = W * count
    scale = max(total / float(image_w), H / float(image_h))
    dw, dh = image_w * scale, image_h * scale
    return [(total - dw) / 2.0 - index * W, (H - dh) / 2.0, dw, dh]


def gradient_line(angle, x0, y0, width, height):
    """CSS-style angle (180 = top to bottom, 90 = left to right) as canvas gradient end points."""
    theta = math.radians(angle)
    dx, dy = math.sin(theta), -math.cos(theta)
    half = (abs(width * dx) + abs(height * dy)) / 2.0
    cx, cy = x0 + width / 2.0, y0 + height / 2.0
    return [cx - dx * half, cy - dy * half, cx + dx * half, cy + dy * half]


BLOB_SPOTS = (((0.90, 0.08), (0.06, 0.94)), ((0.08, 0.12), (0.96, 0.78)), ((0.88, 0.46), (0.04, 0.26)),
              ((0.16, 0.96), (0.92, 0.04)))


def background_spec(background, pal, W, H, index, count, plate_info, grain=0):
    """What the page script paints into the background canvas. `grain` (levels of 255) goes on a gradient only."""
    kind = background.get("kind", "solid")

    def colour(key, default):
        value = background.get(key) or default
        return to_hex(pal[value]) if value in pal else to_hex(parse_hex(value))
    base = colour("color", "bg")
    spec = {"kind": "solid", "color": base}
    dark = luminance(parse_hex(base)) < 0.3
    accent, accent2 = pal["accent"], hue_shift(pal["accent"], 38)
    strength = (0.42, 0.30) if dark else (0.20, 0.15)
    if kind == "plate" or (kind == "strip" and background.get("plate")):
        draw = cover_rect(plate_info["width"], plate_info["height"], W, H, index if kind == "strip" else 0,
                          count if kind == "strip" else 1)
        dim = background.get("dim") or 0.0
        spec = {"kind": "plate", "color": base, "plate": "plate-src", "draw": draw, "dim": dim,
                "dimColor": list(pal["bg"])}
    elif kind == "gradient":
        first, second = BLOB_SPOTS[index % len(BLOB_SPOTS)]
        side = min(W, H)
        spec = {"kind": "gradient", "color": base, "from": colour("from", "bg"), "to": colour("to", "bg_alt"),
                "line": gradient_line(background.get("angle", 160), 0, 0, W, H), "grain": grain,
                "blobs": [{"x": first[0] * W, "y": first[1] * H, "r": 0.85 * side, "color": list(accent), "alpha": strength[0]},
                          {"x": second[0] * W, "y": second[1] * H, "r": 0.70 * side, "color": list(accent2), "alpha": strength[1]}]}
    elif kind == "strip":
        side = min(W, H)
        blobs = []
        for seam in range(count + 1):
            blobs.append({"x": (seam - index) * W, "y": (0.14 if seam % 2 == 0 else 0.86) * H, "r": 0.95 * side,
                          "color": list(accent if seam % 2 == 0 else accent2), "alpha": strength[seam % 2]})
        spec = {"kind": "gradient", "color": base, "from": colour("from", "bg"), "to": colour("to", "bg_alt"),
                "line": gradient_line(background.get("angle", 110), -index * W, 0, W * count, H), "blobs": blobs, "grain": grain}
    return spec


def readable_accent(accent, grounds, ink, floor=4.6):
    """The accent as text: pulled toward the text colour until it holds `floor`:1 on every ground colour."""
    colour = accent
    for step in range(15):
        colour = mix(accent, ink, step * 0.06)
        if all(contrast_ratio(colour, ground) >= floor for ground in grounds):
            break
    return colour


def palette(theme, invert):
    """Theme colours of one slide. `invert` swaps ground and text: bg <-> fg, bg_alt <-> fg_alt."""
    pal = {key: parse_hex(theme[key]) for key in THEME_REQUIRED}
    pal["muted"] = parse_hex(theme.get("muted")) or mix(pal["fg_alt"], pal["bg"], 0.35)     # meta text: the lockup of a text slide
    if invert:
        pal["bg"], pal["fg"] = pal["fg"], pal["bg"]
        pal["bg_alt"], pal["fg_alt"] = pal["fg_alt"], pal["bg_alt"]
    tinted = mix(pal["bg_alt"], pal["accent"], 0.25 if luminance(pal["bg"]) < 0.3 else 0.12)   # under an accent blob
    pal["accent_text"] = readable_accent(pal["accent"], (pal["bg"], pal["bg_alt"], tinted), pal["fg"])
    return pal


# ----------------------------------------------------------------------------------------------- page markup

def esc(text):
    return html.escape(str(text), quote=True)


def px(value):
    return ("%.2f" % value).rstrip("0").rstrip(".") + "px"


def shadow_css(width, strength):
    layers = ((0.006, 0.014, 0.22), (0.03, 0.06, 0.24), (0.085, 0.17, 0.30))
    return ",".join("0 %s %s rgba(0,0,0,%.2f)" % (px(width * dy), px(width * blur), alpha * strength)
                    for dy, blur, alpha in layers)


def svg_viewbox(root, path):
    """(width, height) of an SVG's artboard: the viewBox, else numeric width and height."""
    numbers = re.findall(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?", root.get("viewBox") or "")
    try:
        if len(numbers) == 4:
            width, height = float(numbers[2]), float(numbers[3])
        else:
            width = float(re.sub(r"[a-z%]+$", "", root.get("width") or ""))
            height = float(re.sub(r"[a-z%]+$", "", root.get("height") or ""))
    except ValueError:
        raise Fail("svg_invalid", "%s has no viewBox and no numeric width/height" % path)
    if width <= 0 or height <= 0:
        raise Fail("svg_invalid", "%s has an empty artboard" % path)
    return width, height


PATH_ARGS = {"M": 2, "L": 2, "T": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "A": 7, "Z": 0}


def path_bbox(data):
    """Rough bounding box of SVG path data (control points count as points): [x0, y0, x1, y1] or None."""
    tokens = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", data or "")
    xs, ys, x, y, start, index, command = [], [], 0.0, 0.0, (0.0, 0.0), 0, None
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
            if command in "Zz":
                x, y = start
                continue
        if command is None:
            return None
        need = PATH_ARGS[command.upper()]
        chunk = tokens[index:index + need]
        if len(chunk) < need or any(t.isalpha() for t in chunk):
            return None
        values = [float(t) for t in chunk]
        index += need
        relative, kind = command.islower(), command.upper()
        if kind == "H":
            x = x + values[0] if relative else values[0]
        elif kind == "V":
            y = y + values[0] if relative else values[0]
        else:
            pairs = [values[5:7]] if kind == "A" else [values[i:i + 2] for i in range(0, need, 2)]
            for px_, py_ in pairs:
                xs.append(x + px_ if relative else px_)
                ys.append(y + py_ if relative else py_)
            x, y = xs[-1], ys[-1]
        xs.append(x)
        ys.append(y)
        if kind == "M":
            start = (x, y)
            command = "l" if relative else "L"
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None


def shape_bbox(element):
    """Bounding box of one drawn SVG element in artboard units, own translate/matrix transform applied."""
    name = local_name(element.tag)

    def num(key, default=0.0):
        try:
            return float(re.sub(r"[a-z%]+$", "", element.get(key) or "") or default)
        except ValueError:
            return default
    if name == "path":
        box = path_bbox(element.get("d"))
    elif name == "rect":
        box = [num("x"), num("y"), num("x") + num("width"), num("y") + num("height")]
    elif name in ("circle", "ellipse"):
        rx, ry = (num("r"), num("r")) if name == "circle" else (num("rx"), num("ry"))
        box = [num("cx") - rx, num("cy") - ry, num("cx") + rx, num("cy") + ry]
    else:
        return None
    if box is None:
        return None
    found = re.match(r"\s*(translate|matrix)\(([^)]*)\)\s*$", element.get("transform") or "")
    if found:
        v = [float(n) for n in re.findall(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", found.group(2))]
        m = [1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0.0] if found.group(1) == "translate" and v else v
        if len(m) == 6:
            corners = [(m[0] * cx + m[2] * cy + m[4], m[1] * cx + m[3] * cy + m[5]) for cx in (box[0], box[2]) for cy in (box[1], box[3])]
            box = [min(c[0] for c in corners), min(c[1] for c in corners), max(c[0] for c in corners), max(c[1] for c in corners)]
    return box


def drop_centre_shapes(root, width):
    """A status-bar export often carries the island, the camera hole or a background. Whatever crosses the middle of
    the artboard goes: the frame draws its own cut-out, and the two halves of the bar must not split a shape."""
    dropped = 0
    for parent in list(root.iter()):
        if local_name(parent.tag) in ("clipPath", "mask", "defs"):
            continue
        for child in list(parent):
            box = shape_bbox(child)
            if box and box[0] < width / 2.0 < box[2] and not (box[2] - box[0]) < 0.004 * width:
                parent.remove(child)
                dropped += 1
    return dropped


def inline_svg(source, prefix, style="", drop_centre=False):
    """A checked SVG as inline markup: no declaration, no size attributes, namespace dropped, every paint
    turned into currentColor (the page sets `color`), and every id prefixed so that two copies of one file
    on a page keep their own clip paths, masks and gradients. -> (markup, artboard width, artboard height)."""
    # `source` is a file path (an imported asset) or {"markup": text, "label": name} (a bar shipped in devices.json)
    path = source["label"] if isinstance(source, dict) else source
    root = check_svg(source["markup"], path) if isinstance(source, dict) else load_svg(source)
    width, height = svg_viewbox(root, path)
    if drop_centre:
        drop_centre_shapes(root, width)
    if not root.get("viewBox"):
        root.set("viewBox", "0 0 %g %g" % (width, height))
    for key in ("width", "height"):
        if key in root.attrib:
            del root.attrib[key]
    ids = {element.get("id") for element in root.iter() if element.get("id")}
    inside_defs = set()
    for element in root.iter():
        if local_name(element.tag) in ("clipPath", "mask", "defs"):
            inside_defs.update(element.iter())

    def relink(value):
        value = re.sub(r"url\(\s*['\"]?#([^)'\"\s]+)['\"]?\s*\)", lambda m: "url(#%s%s)" % (prefix, m.group(1)) if m.group(1) in ids else m.group(0), value)
        return value
    painted = False
    for element in root.iter():
        if element.get("id"):
            element.set("id", prefix + element.get("id"))
        for key in list(element.attrib):
            value = element.attrib[key]
            name = local_name(key)
            if name == "href" and value.startswith("#") and value[1:] in ids:
                element.attrib[key] = "#" + prefix + value[1:]
            elif "url(" in value:
                element.attrib[key] = relink(value)
            if name in ("fill", "stroke") and element not in inside_defs:
                low = value.strip().lower()
                if low not in ("none", "transparent", "inherit") and not low.startswith("url("):
                    element.attrib[key] = "currentColor"
                    painted = painted or name == "fill"
            elif name == "style" and element not in inside_defs:
                element.attrib[key] = re.sub(r"(^|;)\s*(fill|stroke)\s*:\s*(?!none|transparent|inherit|url)[^;]+",
                                             lambda m: "%s%s:currentColor" % (m.group(1), m.group(2)), relink(value))
        if local_name(element.tag) == "style" and element.text:
            element.text = relink(element.text)
    if root.get("fill") is None:
        root.set("fill", "currentColor")       # shapes without a fill draw black by default: make them follow `color`
    if style:
        root.set("style", style)
    text = ET.tostring(root, encoding="unicode")
    text = re.sub(r"\sxmlns(:\w+)?=\"[^\"]*\"", "", text)
    return re.sub(r"<(/?)(?:\w+):", r"<\1", text), width, height


def bar_anchor(align, x, top, sw):
    if align == "center":
        return "left:%s;top:%s;transform:translate(-50%%,-50%%)" % (px(x * sw), px(top))
    if align == "right":
        return "right:%s;top:%s;transform:translateY(-50%%)" % (px((1 - x) * sw), px(top))
    return "left:%s;top:%s;transform:translateY(-50%%)" % (px(x * sw), px(top))


def time_text(bar, lay, sw, short):
    return ('<div class="lk-time" style="%s;font-size:%s;font-weight:%d;letter-spacing:%sem;font-family:%s">%s</div>'
            % (bar_anchor(lay["time_align"], lay["time_x"], lay["center_y"] * short, sw), px(lay["time_size"] * short),
               lay["time_weight"], lay.get("time_tracking", 0), esc(lay["font"]), esc(bar["time"])))


def glyph_layer(dev_id, bar, sw, short, hidden, imported=None):
    style = "display:none" if hidden else ""
    if imported:
        # Scaled by HEIGHT to the bar height of the frame; the width follows the artboard. Two copies, each clipped to
        # its own half: the left cluster stays pinned left, the right cluster pinned right, the gap between them flexes.
        # A landscape phone bar is thinner than its artwork: the artwork keeps its portrait scale and moves up.
        bar_h = bar["height"] * short
        art_h = bar.get("art_height", bar["height"]) * short
        _markup, vbw, vbh = inline_svg(imported, "x")
        width = art_h * vbw / vbh
        half = min(sw / 2.0, width / 2.0)
        size = "width:%s;height:%s" % (px(width), px(art_h))
        if bar.get("art_shift"):
            size += ";top:%s" % px(bar["art_shift"] * short)
        left = inline_svg(imported, "%s-l-" % dev_id, "left:0;" + size, drop_centre=True)[0]
        right = inline_svg(imported, "%s-r-" % dev_id, "right:0;" + size, drop_centre=True)[0]
        clock = ""
        lay = bar.get("layout")
        if isinstance(imported, dict) and imported.get("live_time") and lay and bar.get("time"):
            clock = time_text(bar, lay, sw, short)         # the shipped bar carries no outlined clock: the time is live text
        return ('<div class="lk-glyphs" id="%s-gl" style="%s"><div class="lk-ibar lk-ihalf" style="left:0;top:0;width:%s;height:%s">%s</div>'
                '<div class="lk-ibar lk-ihalf" style="right:0;top:0;width:%s;height:%s">%s</div>%s</div>') % (
            dev_id, style, px(half), px(bar_h), left, px(half), px(bar_h), right, clock)
    lay = bar.get("layout")
    if not lay or not bar.get("glyphs"):
        return ""
    top = lay["center_y"] * short
    height = lay["glyph_h"] * short
    icons = []
    for name in lay["order"]:
        box = bar["glyph_boxes"][name]
        ring = ""
        if name == "battery" and lay.get("ring") and lay["ring"] in bar["glyphs"]:
            ring = '<path opacity="%s" d="%s"/>' % (lay.get("ring_opacity", 1), bar["glyphs"][lay["ring"]])
        unit = height / float(lay.get("glyph_ref") or 12)          # `glyph_h` is the height of a glyph `glyph_ref` units tall
        before = 0.0 if not icons else (lay.get("gap_before") or {}).get(name, lay["gap"]) * short
        icons.append('<svg viewBox="0 0 %s %s" style="height:%s;width:%s;margin-left:%s">%s<path d="%s"/></svg>' % (
            box[0], box[1], px(unit * box[1]), px(unit * box[0]), px(before), ring, bar["glyphs"][name]))
    time_html = time_text(bar, lay, sw, short)
    cluster = '<div class="lk-cluster" style="%s">%s</div>' % (bar_anchor(lay["cluster_align"], lay["cluster_x"], top, sw), "".join(icons))
    return '<div class="lk-glyphs" id="%s-gl" style="%s">%s%s</div>' % (dev_id, style, time_html, cluster)


def screen_inner(dev):
    """Capture plus the status-bar work, in screen coordinates. Shared by drawn frames and hero scenes."""
    did, sw, short, top, bottom, cap_h = dev["id"], dev["sw"], dev["short"], dev["top"], dev["bottom"], dev["cap_h"]
    action, parts = dev["action"], []
    if top:
        parts.append('<div class="lk-strip" id="%s-top" style="top:0;height:%dpx"></div>' % (did, top))
    parts.append('<img class="lk-cap" id="%s" alt="" style="top:%dpx;width:%dpx;height:%dpx" src="%s">'
                 % (dev["cap_id"], top, sw, cap_h, dev["uri"]))
    if bottom:
        pill = ""
        spec = (dev.get("bottom_bar") or {}).get("pill")
        if dev.get("bottom_svg"):       # an imported bar: transparent wrapper, shapes take `color` (never a background);
            _markup, vbw, vbh = inline_svg(dev["bottom_svg"], "x")      # scaled by HEIGHT to the strip and centred
            width = bottom * vbw / vbh
            pill = '<div class="lk-ibar" id="%s-ibot" style="left:50%%;top:0;width:%s;height:%dpx;transform:translateX(-50%%)">%s</div>' % (
                did, px(width), bottom, inline_svg(dev["bottom_svg"], "%s-b-" % did, "left:0;width:%s;height:%dpx" % (px(width), bottom))[0])
        elif spec and dev["glyphs"]:
            pill = '<div class="lk-pill" id="%s-pill" style="width:%s;height:%s;bottom:%s"></div>' % (
                did, px(spec["w"] * short), px(spec["h"] * short), px(spec["bottom"] * short))
        parts.append('<div class="lk-strip" id="%s-bot" style="top:%dpx;height:%dpx;overflow:hidden">%s</div>' % (did, top + cap_h, bottom, pill))
    bar = dev.get("top_bar")
    if bar and action in ("test_flat", "mask"):
        parts.append('<div class="lk-cover" id="%s-cover" style="height:%s"></div>' % (did, px(max(bar["height"], dev.get("own_bar") or 0) * short)))
    if bar and dev["glyphs"] and action in ("extend", "overlay", "test_flat", "mask"):
        parts.append(glyph_layer(did, bar, sw, short, action in ("test_flat", "mask"), dev.get("top_svg")))
    return "".join(parts)


def cutout_html(dev):
    cut = dev["frame"].get("cutout") or {}
    if cut.get("type") not in ("island", "punch"):
        return ""
    short, sw, sh = dev["short"], dev["sw"], dev["sh"]
    w, h, off = cut["w"] * short, cut["h"] * short, cut["top"] * short
    if dev["cw"] > dev["ch"]:      # landscape: the cut-out sits on the left short side
        return '<div class="lk-cut" style="left:%s;top:%s;width:%s;height:%s;border-radius:%s"></div>' % (
            px(off), px((sh - w) / 2.0), px(h), px(w), px(h / 2.0))
    return '<div class="lk-cut" style="left:%s;top:%s;width:%s;height:%s;border-radius:%s"></div>' % (
        px((sw - w) / 2.0), px(off), px(w), px(h), px(h / 2.0))


def tilt_css(dev):
    """A card-flow capture turned about its centre; the page is supersampled so its edges stay smooth."""
    return ";transform:rotate(%sdeg)" % px(dev["tilt"])[:-2] if dev.get("tilt") else ""


def window_html(dev, app, strength):
    frame, bw, bh, bar = dev["frame"], dev["bw"], dev["bh"], dev["bar"]
    tb, col = frame["titlebar"], frame["colors"]
    dot = max(6.0, tb["dot"] * bw)
    dots = "".join('<i class="l" style="width:%s;height:%s;background:%s"></i>' % (px(dot), px(dot), c) for c in tb["dots"])
    dots += "".join('<i class="d" style="width:%s;height:%s;background:%s"></i>' % (px(dot), px(dot), c) for c in tb["dots_dark"])
    middle = ""
    if tb.get("pill"):
        label = re.sub(r"^[a-z]+://", "", str(app.get("url") or "")).split("/")[0]
        middle = '<div class="lk-addr" style="width:%s;height:%s;font-size:%s">%s</div>' % (
            px(tb["pill"]["w"] * bw), px(tb["pill"]["h"] * bar), px(bar * 0.36), esc(label))
    elif tb.get("title"):
        middle = '<div class="lk-title" style="font-size:%s">%s</div>' % (px(bar * 0.42), esc(app.get("name") or ""))
    radius = frame["body_radius"] * bw
    variables = ("--bar:%s;--bar-d:%s;--pill:%s;--pill-d:%s;--txt:%s;--txt-d:%s;--edge:%s;--edge-d:%s" % (
        col["bar"], col["bar_dark"], col["pill"], col["pill_dark"], col["text"], col["text_dark"], col["border"], col["border_dark"]))
    return ('<div class="lk-dev lk-win" id="%s" style="left:%s;top:%s;width:%s;height:%s;z-index:%d;border-radius:%s;box-shadow:%s;%s%s">'
            '<div class="lk-tbar" style="height:%dpx;padding-left:%s"><div class="lk-dots" style="gap:%s">%s</div>%s</div>'
            '<div class="lk-screen" style="left:0;top:%dpx;width:%dpx;height:%dpx">%s</div>'
            '<div class="lk-edge" style="border-radius:%s"></div></div>') % (
        dev["id"], px(dev["x"]), px(dev["y"]), px(bw), px(bh), dev["z"], px(radius), shadow_css(bw, strength * 0.8), variables,
        tilt_css(dev), bar, px(tb["pad"] * bw), px(tb["dot_gap"] * bw), dots, middle, bar, dev["sw"], dev["sh"], screen_inner(dev), px(radius))


def device_html(dev, app, strength):
    frame, bw, bh = dev["frame"], dev["bw"], dev["bh"]
    if frame["kind"] == "window":
        return window_html(dev, app, strength)
    dimmed = ";filter:brightness(0.42) saturate(0.85)" if dev.get("context") and strength >= 1.0 else (
        ";opacity:0.4" if dev.get("context") else "")
    open_tag = '<div class="lk-dev" id="%s" style="left:%s;top:%s;width:%s;height:%s;z-index:%d%s%s">' % (
        dev["id"], px(dev["x"]), px(dev["y"]), px(bw), px(bh), dev["z"], dimmed, tilt_css(dev))
    if dev.get("bezel_asset"):
        asset = dev["bezel_asset"]
        scale = bw / float(asset["size"][0])
        shadow = ";filter:drop-shadow(0 %s %s rgba(0,0,0,%.2f))" % (px(bw * 0.05), px(bw * 0.09), 0.38 * strength) if dev.get("bezel_shadow") else ""
        image = '<img class="lk-bezel-img" alt="" style="position:absolute;left:0;top:0;width:%s;height:%s%s" src="%s">' % (
            px(bw), px(bh), shadow, asset["uri"])
        screen = '<div class="lk-screen" style="left:%s;top:%s;width:%dpx;height:%dpx;border-radius:%s">%s</div>' % (
            px(dev["sx"]), px(dev["sy"]), dev["sw"], dev["sh"], px((asset.get("screen_radius") or 0) * scale), screen_inner(dev))
        # a transparent screen hole: the bezel lies over the capture. An opaque bezel: the capture lies over the bezel.
        return open_tag + (image + screen if asset.get("opaque") else screen + image) + "</div>"
    col = frame.get("colors") or {}
    if frame["kind"] == "none":
        key = "window_radius" if dev["os"] in ("web", "desktop") else "screen_radius"
        radius = frame.get(key, 0.03) * dev["short"]
        # tilted, the ground under the capture is transparent: black would bleed through its anti-aliased edge
        tilted = bool(dev.get("tilt"))
        return (open_tag + '<div class="lk-body" style="left:0;top:0;right:0;bottom:0;border-radius:%s;background:%s;box-shadow:%s,0 0 0 %s rgba(127,127,127,0.26)"></div>'
                '<div class="lk-screen" style="left:0;top:0;width:%dpx;height:%dpx;border-radius:%s%s">%s</div></div>'
                % (px(radius), "transparent" if tilted else "#000", shadow_css(bw, strength), px(max(1.0, bw * 0.0016)), dev["sw"], dev["sh"],
                   px(radius), ";background:transparent" if tilted else "", screen_inner(dev)))
    rim = frame.get("rim", 0) * bw
    body_r = frame["body_radius"] * bw
    buttons = ""
    for button in frame.get("buttons") or []:
        depth = 0.011 * bw
        side = "left:%s" % px(-depth * 0.45) if button["side"] == "left" else "right:%s" % px(-depth * 0.45)
        buttons += '<div class="lk-btn" style="%s;top:%s;width:%s;height:%s;border-radius:%s;background:%s"></div>' % (
            side, px(button["top"] * bh), px(depth), px(button["h"] * bh), px(depth * 0.4), col.get("button", "#333"))
    body = ('<div class="lk-body" style="left:0;top:0;right:0;bottom:0;border-radius:%s;background:linear-gradient(140deg,%s 0%%,%s 18%%,%s 50%%,%s 82%%,%s 100%%);'
            'box-shadow:%s,inset 0 0 0 %s rgba(255,255,255,0.10)"></div>' % (
                px(body_r), col["rim_light"], col["body"], col["rim_dark"], col["body"], col["rim_light"],
                shadow_css(bw, strength), px(max(1.0, bw * 0.0016))))
    bezel = '<div class="lk-bezel" style="left:%s;top:%s;right:%s;bottom:%s;border-radius:%s;background:%s"></div>' % (
        px(rim), px(rim), px(rim), px(rim), px(max(0.0, body_r - rim)), col["bezel"])
    screen = '<div class="lk-screen" style="left:%s;top:%s;width:%dpx;height:%dpx;border-radius:%s;background:%s">%s%s</div>' % (
        px(dev["sx"]), px(dev["sy"]), dev["sw"], dev["sh"], px(frame["screen_radius"] * dev["short"]),
        col.get("screen_off", "#000"), screen_inner(dev), cutout_html(dev))
    return open_tag + buttons + body + bezel + screen + "</div>"


def zoom_html(dev, zone, zoom, strength):
    """A frameless enlarged crop of the capture as a rounded card."""
    zx, zy, zw, zh = zone
    crop_w, crop_h = zoom["w"] * dev["cw"], zoom["h"] * dev["ch"]
    scale = min(zw / crop_w, zh / crop_h)
    width, height = int(round(crop_w * scale)), int(round(crop_h * scale))
    x, y = zx + (zw - width) / 2.0, zy + (zh - height) / 2.0
    radius = 0.06 * min(width, height)
    return ('<div class="lk-dev lk-card" id="lk-zoom" style="left:%s;top:%s;width:%dpx;height:%dpx;z-index:5;border-radius:%s;box-shadow:%s,0 0 0 %s rgba(127,127,127,0.22)">'
            '<img class="lk-cap" alt="" style="left:%s;top:%s;width:%s;height:%s" src="%s"></div>') % (
        px(x), px(y), width, height, px(radius), shadow_css(width, max(strength, 0.8) * 1.25), px(max(1.0, width * 0.002)),
        px(-zoom["x"] * dev["cw"] * scale), px(-zoom["y"] * dev["ch"] * scale), px(dev["cw"] * scale),
        px(dev["ch"] * scale), dev["uri"])


def emphasise(line, emphasis, state):
    if emphasis and not state["done"] and emphasis in line:
        state["done"] = True
        before, after = line.split(emphasis, 1)
        return '%s<span class="em" data-role="em">%s</span>%s' % (esc(before), esc(emphasis), esc(after))
    return esc(line)


def text_html(plan, copy, rtl):
    out = []
    state = {"done": False}
    flex = {"left": "flex-start", "center": "center", "right": "flex-end", "top": "flex-start", "bottom": "flex-end"}
    for block in plan["blocks"]:
        align = block["align"]
        if rtl and align in ("left", "right"):
            align = "right" if align == "left" else "left"
        inner = []
        if "badge" in block["parts"] and copy.get("badge"):
            inner.append('<div class="lk-badge"><span data-role="badge" data-block="%s">%s</span></div>' % (block["id"], esc(copy["badge"])))
        if "headline" in block["parts"] and copy.get("headline"):
            if plan.get("rule"):
                inner.append('<div class="lk-rule"></div>')
            lines = "".join('<div class="l"><span data-role="headline" data-block="%s">%s</span></div>'
                            % (block["id"], emphasise(line, copy.get("emphasis"), state)) for line in copy["headline"])
            inner.append('<div class="lk-h">%s</div>' % lines)
        if "sub" in block["parts"] and copy.get("sub"):
            lines = "".join('<div class="l"><span data-role="sub" data-block="%s">%s</span></div>' % (block["id"], esc(line))
                            for line in copy["sub"])
            inner.append('<div class="lk-sub">%s</div>' % lines)
        if not inner:
            continue
        x, y, w, h = block["box"]
        cross = flex[align]
        if rtl and align in ("left", "right"):       # under dir=rtl the cross axis starts at the right edge
            cross = "flex-start" if align == "right" else "flex-end"
        out.append('<div class="lk-tb%s" id="%s"%s style="left:%s;top:%s;width:%s;height:%s;justify-content:%s;align-items:%s;text-align:%s">'
                   '<div class="lk-tbi" id="%s-i" style="align-items:%s">%s</div></div>' % (
                       " lk-shadowed" if plan.get("shadowed") else "", block["id"], ' dir="rtl"' if rtl else "", px(x), px(y), px(w), px(h),
                       flex[block["valign"]], cross, align, block["id"], cross, "".join(inner)))
    return "".join(out), [b["id"] for b in plan["blocks"] if any(('id="%s"' % b["id"]) in chunk for chunk in out)]


def lockup_html(plan, app, uris, W):
    spot = plan.get("lockup")
    if not spot:
        return ""
    height = spot.get("inner") or spot["h"]     # card-lockup: the lockup is smaller than its zone and centred in it
    if uris.get("logo"):
        inner = '<img alt="" src="%s">' % uris["logo"]
    else:
        icon = '<img class="lk-icon" alt="" src="%s">' % uris["icon"] if uris.get("icon") else ""
        inner = '%s<span style="font-size:%s;margin-left:%s">%s</span>' % (
            icon, px(height * 0.56), px(height * 0.30 if icon else 0), esc(app.get("name") or ""))
    if spot["align"] == "center":
        place = "left:%s;width:%s;justify-content:center" % (px(spot.get("x") or 0.0), px(spot.get("w") or W))
    else:
        place = "left:%s" % px(spot["x"])
    tone = ";color:var(--muted)" if spot.get("muted") else ""
    return '<div class="lk-lockup" id="lk-lockup" style="%s;top:%s;height:%s%s"><div id="lk-lockup-i" style="display:flex;align-items:center;height:%s">%s</div></div>' % (
        place, px(spot["y"]), px(spot["h"]), tone, px(height) if spot.get("inner") else "100%", inner)


def lockup_aspect(app, slug):
    """Width over height of the lockup: the logo's own artboard, else an estimate for icon plus name that the page
    corrects when it scales the lockup."""
    if app.get("logo"):
        path = resolve_path(slug, app["logo"])
        if path.lower().endswith(".svg"):
            width, height = svg_viewbox(load_svg(path), path)
        else:
            info = probe_image(path)
            width, height = info["width"], info["height"]
        return width / float(height) if width > 0 and height > 0 else 3.0
    return (1.3 if app.get("icon") else 0.0) + 0.56 * 0.58 * max(1, len(app.get("name") or ""))


def font_css(deck, slug):
    font = (deck.get("theme") or {}).get("font") or {}
    family = font.get("family") or "system"
    if family == "system":
        return "", SYSTEM_STACK
    files = [resolve_path(slug, item) for item in font.get("files") or []]
    if not files:
        imported = asset_index().get("font", {}).get(slugify(family))
        if imported:
            files = [imported["file"]]
    rules = []
    weights = (("thin", 100), ("extralight", 200), ("light", 300), ("regular", 400), ("medium", 500), ("semibold", 600),
               ("extrabold", 800), ("bold", 700), ("black", 900), ("heavy", 900))
    for path in files:
        name = os.path.basename(path).lower().replace("-", "").replace("_", "")
        weight = "100 900" if len(files) == 1 else str(next((w for key, w in weights if key in name), 400))
        rules.append('@font-face{font-family:"%s";src:url(%s);font-weight:%s;font-style:normal}' % (
            family.replace('"', ""), data_uri(path), weight))
    return "".join(rules), '"%s", %s' % (family.replace('"', ""), SYSTEM_STACK)


# ----------------------------------------------------------------------------------------------- imported assets

FORBIDDEN_SVG = ("script", "foreignObject", "iframe", "object", "embed", "audio", "video", "handler", "set", "animate",
                 "animateTransform", "animateMotion", "image", "use")


def local_name(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def load_svg(path):
    """Parse an SVG file and refuse anything that can run code or reach outside the file."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as handle:
            raw = handle.read(MAX_SVG_BYTES + 1)
    except OSError as exc:
        raise Fail("not_found", "cannot read %s (%s)" % (path, exc.strerror or exc))
    if size > MAX_SVG_BYTES:
        raise Fail("svg_too_large", "%s is %d bytes (limit %d)" % (path, size, MAX_SVG_BYTES))
    return check_svg(raw, path)


def check_svg(raw, path):
    """The safety check itself, for a file's bytes or for markup that ships in devices.json."""
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff") or b"\x00" in raw[:4096]:
        raise Fail("svg_unsafe", "%s is not UTF-8 text: its content cannot be screened" % path)
    if re.search(br"<!ENTITY|<!DOCTYPE[^>]*\[", raw, re.I):
        raise Fail("svg_unsafe", "%s declares XML entities" % path, extra={"reasons": ["entity declaration"]})
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise Fail("svg_invalid", "%s is not well-formed XML: %s" % (path, exc))
    if local_name(root.tag) != "svg":
        raise Fail("svg_invalid", "%s: the root element is <%s>, not <svg>" % (path, local_name(root.tag)))
    reasons = []
    for element in root.iter():
        name = local_name(element.tag)
        if name in FORBIDDEN_SVG:
            reasons.append("<%s> element" % name)
        for key, value in element.attrib.items():
            attr = local_name(key)
            if attr.lower().startswith("on"):
                reasons.append("event handler %s" % attr)
            if attr == "href" and not value.strip().startswith("#"):
                reasons.append("external or embedded reference in <%s>" % name)
            if re.search(r"url\(\s*['\"]?(?!#)", value) or re.match(r"\s*(javascript|vbscript|data)\s*:", value, re.I):
                reasons.append("external url() or script URL in attribute %s" % attr)
        if name == "style" and re.search(r"@import|url\(\s*['\"]?(?!#)", element.text or ""):
            reasons.append("@import or external url() in <style>")
    if reasons:
        raise Fail("svg_unsafe", "%s is not safe to inline" % path, extra={"reasons": sorted(set(reasons))},
                   hint="export again as plain outlined shapes: no scripts, images, links or external styles")
    return root


def asset_index():
    path = os.path.join(assets_dir(), "index.json")
    if not os.path.isfile(path):
        return {}
    data = read_json(path, "asset index")
    assets = data.get("assets")
    return assets if isinstance(assets, dict) else {}


def find_asset(kind, names, os_name=None, device=None):
    """An imported asset by name (frame id or bar id). Bars also match by OS, but only inside the same device
    class: a phone bar never lands on a tablet frame."""
    table = asset_index().get(kind) or {}
    for name in names:
        if name and name in table and os.path.isfile(table[name].get("file", "")):
            return table[name]
    if os_name:
        for entry in table.values():
            if (entry.get("os") == os_name and (entry.get("device") or "phone") == (device or "phone")
                    and os.path.isfile(entry.get("file", ""))):
                return entry
    return None


# ----------------------------------------------------------------------------------------------- browser

def find_browser():
    override = os.environ.get("GM_BROWSER_BIN")
    if override:
        if override.strip().lower() == "none":
            return None
        return override if os.path.isfile(override) and os.access(override, os.X_OK) else shutil.which(override)
    for name in BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    for path in BROWSER_PATHS:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def find_tool(name):
    override = os.environ.get("GM_%s_BIN" % name.upper())       # GM_FFMPEG_BIN, GM_SIPS_BIN; "none" disables the tool
    if override:
        if override.strip().lower() == "none":
            return None
        return override if os.path.isfile(override) and os.access(override, os.X_OK) else None
    return shutil.which(name)


def need_browser(what):
    binary = find_browser()
    if not binary:
        raise Fail("tool_missing", "%s needs a Chromium-family browser, and none was found" % what, hint=MISSING_HINT)
    return binary


def file_url(path):
    return pathlib.Path(os.path.abspath(path)).as_uri()


def _tail_has(path, needle, span=256):
    try:
        with open(path, "rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - span))
            return needle in handle.read()
    except OSError:
        return False


VIEWPORT_PAGE = ('<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0">'
                 '<pre id="lk-metrics">pending</pre><script>/* LK_VIEWPORT */addEventListener("load",function(){'
                 'document.getElementById("lk-metrics").textContent=JSON.stringify({ok:true,viewport:[innerWidth,innerHeight]})'
                 '})</script></body></html>')
_WINDOW_INSET = {}
_WINDOW_INSET_LOCK = threading.Lock()


def window_inset(binary):
    """How many CSS pixels the page viewport falls short of --window-size in height. The new headless mode
    (what `--headless` means in current Chrome and Edge) counts the browser's tab strip and toolbar into the
    window: the viewport is 84 to 87 px shorter while the screenshot stays window-sized, and some builds
    (Chromium 141 on Linux) leave that bottom band unpainted. chrome-headless-shell gives 0. Measured once per binary and process; a failed probe gives 0."""
    with _WINDOW_INSET_LOCK:
        if binary in _WINDOW_INSET:
            return _WINDOW_INSET[binary]
        work = tempfile.mkdtemp(prefix="launchkit-viewport-")
        inset = 0
        try:
            page = os.path.join(work, "viewport.html")
            with open(page, "w", encoding="utf-8") as handle:
                handle.write(VIEWPORT_PAGE)
            seen = parse_metrics(run_browser(binary, page, 800, 600)).get("viewport")
            if isinstance(seen, list) and len(seen) == 2 and isinstance(seen[1], (int, float)):
                inset = int(600 - seen[1])
                inset = inset if 0 < inset <= 300 else 0
        except Fail:
            inset = 0
        finally:
            shutil.rmtree(work, ignore_errors=True)
        _WINDOW_INSET[binary] = inset
        return inset


def run_browser(binary, page, width, height, shot=None, dom=True, scale=1):
    """ONE headless run gives the dumped DOM (metrics) and the screenshot. Chrome often does not exit by itself
    after either: poll for complete outputs, then stop it. Every run gets its own throw-away profile.
    `scale` is the device scale factor: the window stays width x height CSS pixels, the screenshot is scale times that.
    With a screenshot the window grows by the browser's own inset (`window_inset`) so the viewport is the full
    height, and the extra rows are cut off the bottom of the PNG afterwards."""
    profile = tempfile.mkdtemp(prefix="launchkit-browser-")
    sink_path = os.path.join(profile, "dom.html")
    if shot and os.path.exists(shot):
        os.remove(shot)
    inset = window_inset(binary) if shot else 0
    argv = [binary, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
            "--force-device-scale-factor=%d" % scale, "--force-color-profile=srgb", "--user-data-dir=" + profile,
            "--window-size=%d,%d" % (width, height + inset), "--virtual-time-budget=6000"]
    if dom:
        argv.append("--dump-dom")
    if shot:
        argv.append("--screenshot=" + os.path.abspath(shot))
    argv.append(file_url(page))

    def done():
        return (not dom or _tail_has(sink_path, b"</html>")) and (not shot or png_complete(shot))
    started = time.time()
    text = ""
    try:
        with open(sink_path, "wb") as sink:
            try:
                process = subprocess.Popen(argv, stdout=sink, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
            except OSError as exc:
                raise Fail("tool_failed", "cannot start %s: %s" % (binary, exc.strerror or exc), hint=MISSING_HINT)
            try:
                while time.time() - started < PAGE_TIMEOUT_S:
                    if done():
                        break
                    if process.poll() is not None:
                        break
                    time.sleep(0.05)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(5)
        finished = done()
        if dom and finished:
            with open(sink_path, "rb") as handle:
                text = handle.read().decode("utf-8", "replace")
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if not finished:
        raise Fail("tool_failed", "%s gave no complete %s for %s within %d s" % (
            os.path.basename(binary), "screenshot and DOM" if shot and dom else "screenshot" if shot else "DOM",
            os.path.basename(page), PAGE_TIMEOUT_S), hint="run the command again; if it repeats, render with --jobs 1")
    if inset:
        crop_png_height(shot, height * scale)
    return text


def parse_metrics(dom_text):
    found = re.search(r'<pre id="lk-metrics"[^>]*>(.*?)</pre>', dom_text, re.S)
    body = html.unescape(found.group(1)) if found else ""
    try:
        data = json.loads(body)
    except ValueError:
        raise Fail("tool_failed", "the page script did not report (got %r)" % body[:80],
                   hint="the browser stopped before the load handler ran: run the command again")
    if not isinstance(data, dict):
        raise Fail("tool_failed", "the page script reported %r" % (data,))
    return data


def analysis_page(script, image_path, prelude=""):
    return ('<!doctype html><html><head><meta charset="utf-8"></head><body><pre id="lk-metrics">pending</pre>'
            '<img id="scene" alt="" style="display:none" src="%s"><script>%s%s</script></body></html>'
            % (data_uri(image_path), prelude, script))


def run_analysis(script, image_path, prelude=""):
    binary = need_browser("pixel analysis")
    work = tempfile.mkdtemp(prefix="launchkit-page-")
    try:
        page = os.path.join(work, "analyse.html")
        with open(page, "w", encoding="utf-8") as handle:
            handle.write(analysis_page(script, image_path, prelude))
        return parse_metrics(run_browser(binary, page, 800, 600))
    finally:
        shutil.rmtree(work, ignore_errors=True)


def encode_jpeg(png_path, jpg_path, budget):
    """The PNG render as JPEG, encoded by the browser (stdlib Python has no encoder): the highest quality from
    JPEG_QUALITY_MAX down to JPEG_QUALITY_FLOOR whose file stays at or under `budget` bytes.
    -> {quality, bytes, tried} with the file written, or {over: bytes at the floor} with nothing written."""
    prelude = "window.LK_JPEG=%s;" % json.dumps({"max": budget, "hi": JPEG_QUALITY_MAX, "lo": JPEG_QUALITY_FLOOR})
    data = run_analysis(JPEG_JS, png_path, prelude)
    if not data.get("ok"):
        if data.get("kind") == "jpeg_over_budget":
            return {"over": data.get("bytes"), "tried": data.get("tried")}
        raise Fail("tool_failed", "the JPEG encode failed: %s" % str(data.get("message") or data.get("kind"))[:300])
    try:
        blob = base64.b64decode(data.get("data") or "", validate=True)
    except (ValueError, TypeError):
        raise Fail("tool_failed", "the browser returned no readable JPEG", hint="run the command again")
    if blob[:2] != b"\xff\xd8" or len(blob) > budget:
        raise Fail("tool_failed", "the browser returned %d bytes that are not a JPEG under the %d-byte budget" % (len(blob), budget))
    write_atomic(jpg_path, blob)
    return {"quality": data["quality"] / 100.0, "bytes": len(blob), "tried": data.get("tried")}


def shrink_png(path, factor, edges=()):
    """Shrink a supersampled render in place by an integer factor, in the browser (stdlib Python has no codec).
    `edges` (segments in output pixels) are measured on the shrunk pixels: [{n, rms}] per segment, see edge_gate."""
    data = run_analysis(SHRINK_JS, path, "window.LK_SHRINK=%d;window.LK_EDGES=%s;" % (factor, json.dumps([list(e) for e in edges])))
    if not data.get("ok"):
        raise Fail("tool_failed", "shrinking the supersampled render failed: %s" % str(data.get("message") or data.get("kind"))[:300])
    try:
        rows = base64.b64decode(data.get("rows") or "", validate=True)
        width, height = int(data["w"]), int(data["h"])
    except (ValueError, TypeError, KeyError):
        raise Fail("tool_failed", "the browser returned no readable scanlines", hint="run the command again")
    if len(rows) != height * (1 + width * 3) or any(rows[y * (1 + width * 3)] > 4 for y in range(height)):
        raise Fail("tool_failed", "the browser returned %d bytes, not %dx%d filtered RGB scanlines" % (len(rows), width, height))
    write_atomic(path, PNG_SIG + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                 + _png_chunk(b"IDAT", zlib.compress(rows, 6)) + _png_chunk(b"IEND", b""))
    return data.get("edges") or []


def _clockwise_sides(corners):
    """The four sides of a quad as [x0, y0, x1, y1], clockwise on screen (y down): the capture lies to the right of
    each side, which is how SHRINK_JS tells outside from inside."""
    corners = list(corners)
    if sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(corners, corners[1:] + corners[:1])) < 0:
        corners.reverse()
    return [[corners[i][0], corners[i][1], corners[(i + 1) % 4][0], corners[(i + 1) % 4][1]] for i in range(4)]


def transformed_edges(shots, quad_canvas=None):
    """{kind, segments} where a capture's edge is drawn through a transform, segments [x0, y0, x1, y1] in CSS
    pixels, clockwise: "warp" for the four sides of a hero scene's screen quad, "tilt" for the four sides of every
    tilted capture box; None for a page without one. A page with edges must be supersampled (render_job enforces it)."""
    if quad_canvas:
        return {"kind": "warp", "segments": [[round(v, 2) for v in side] for side in _clockwise_sides(quad_canvas)]}
    edges = []
    for shot in shots:
        if not shot.get("tilt") or "x" not in shot:
            continue
        turn = math.radians(shot["tilt"])
        cx, cy = shot["x"] + shot["bw"] / 2.0, shot["y"] + shot["bh"] / 2.0
        corners = [(cx + dx * math.cos(turn) - dy * math.sin(turn), cy + dx * math.sin(turn) + dy * math.cos(turn))
                   for dx, dy in ((-shot["bw"] / 2.0, -shot["bh"] / 2.0), (shot["bw"] / 2.0, -shot["bh"] / 2.0),
                                  (shot["bw"] / 2.0, shot["bh"] / 2.0), (-shot["bw"] / 2.0, shot["bh"] / 2.0))]
        edges += _clockwise_sides(corners)
    return {"kind": "tilt", "segments": [[round(v, 2) for v in edge] for edge in edges]} if edges else None


def edge_gate(kind, measured):
    """-> (jagged, median RMS or None). Each measured edge is the RMS distance (output pixels) of its sub-pixel
    position from a quadratic along it; stair steps from an un-anti-aliased transform raise it, a soft shadow, the
    slow bend of a generated screen and the capture's own content do not. The median over the page's edges ignores
    one edge crossed by an arrow; an edge whose content left too few clean lines has no rms and is not counted."""
    values = sorted(e["rms"] for e in measured if e.get("rms") is not None)
    if len(values) < 2:
        return False, None
    middle = len(values) // 2
    median = values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2.0
    return median > JAGGED_MEDIAN[kind], round(median, 3)


# ----------------------------------------------------------------------------------------------- page assembly

_SHA_CACHE = {}


def cached_sha(path):
    key = (os.path.abspath(path), os.path.getmtime(path), os.path.getsize(path))
    if key not in _SHA_CACHE:
        _SHA_CACHE[key] = sha256_file(path)
    return _SHA_CACHE[key]


def pick_capture(ref, target):
    """The capture id of one slot on one target: a per-OS map picks the store's phone OS, a desktop target `default`."""
    if isinstance(ref, dict):
        want = None if target.get("device") == "desktop" else {"app-store": "ios", "play": "android"}.get(target.get("store"))
        return ref.get(want) or ref.get("default") or next(iter(ref.values()))
    return ref


def shipped_bar(bar_id, bar, landscape=False):
    """A bar that ships as SVG markup in devices.json renders exactly like an imported one. A landscape screen
    takes `svg_landscape` when the bar has one (the iPad bars: a wider artboard, a longer home indicator)."""
    if not bar or not bar.get("svg"):
        return None
    key = "svg_landscape" if landscape and bar.get("svg_landscape") else "svg"
    return {"markup": bar[key], "label": "devices.json bars.%s.%s" % (bar_id, key), "live_time": not bar.get("svg_includes_time", True)}


def bar_attribution(bar_id, bar):
    return {"bar": bar_id, "origin": bar.get("origin"), "license": bar.get("license"), "changes": bar.get("changes")}


def attributions():
    """Third-party material that ships in devices.json, one row per origin: licences such as CC BY ask for credit."""
    rows = {}
    for bar_id, bar in devices()["bars"].items():
        if bar.get("svg"):
            key = (bar.get("origin"), bar.get("license"))
            row = rows.setdefault(key, {"origin": key[0], "license": key[1], "bars": [], "changes": []})
            row["bars"].append(bar_id)
            if bar.get("changes") not in row["changes"]:
                row["changes"].append(bar.get("changes"))
    return list(rows.values())


def make_shot(deck, slug, capture_id, locale, target_id, mode, one_set, slide, index, bare=False):
    """Everything one capture needs on one page: file, frame, bars, the status-bar plan."""
    cap = deck["captures"][capture_id]
    localized = locale in (cap.get("by_locale") or {})
    path = resolve_path(slug, cap["by_locale"][locale] if localized else cap["file"])
    info = probe_image(path)
    recorded = (cap.get("sha256_by_locale") or {}).get(locale) if localized else cap.get("sha256")
    actual = cached_sha(path)
    if recorded and recorded != actual:
        raise Fail("capture_changed", "capture %r (%s) no longer matches the sha256 in the deck" % (capture_id, path),
                   hint="raw captures are archived untouched: run capture add again with --replace if the new file is intended")
    frame_id = "none" if bare else resolve_frame(target_id, mode, cap.get("os"), one_set.get("frame", "auto"), slide.get("frame"))
    if LAYOUTS[slide["layout"]].get("flow") and all(v in (None, "auto") for v in (slide.get("frame"), one_set.get("frame"))):
        frame_id = "none"                    # a before/after pair reads as two screens, not two devices
    frame, top_bar, bottom_bar = frame_bars(frame_id, frameless_bar_os(target_id, cap.get("os")), mode,
                                            tablet_shaped(info["width"], info["height"]))
    bars = devices()["bars"]
    top_id = next((key for key, value in bars.items() if value is top_bar), "")
    bottom_id = next((key for key, value in bars.items() if value is bottom_bar), "")
    policy = cap.get("statusbar", "auto")
    own_bar = own_bar_height(cap.get("os"), info["width"], info["height"], top_bar)
    # A phone in landscape (framed, or frameless with a phone-shaped capture): Android shows a thinner bar, iOS none.
    turned = info["width"] > info["height"] and top_bar is not None and (
        frame["kind"] == "phone" or (frame["kind"] == "none" and not tablet_shaped(info["width"], info["height"])))
    if turned:
        top_bar = landscape_bar(top_bar)
        if top_bar.get("hidden") and not own_bar and policy != "keep":
            policy = "none"                  # no bar on the page and none in the capture (an iPhone in landscape)
    hidden = bool(top_bar and top_bar.get("hidden"))
    if top_bar is None or target_kind(target_id) == "square" or (policy == "auto" and cap.get("os") in ("web", "desktop")):
        policy = "none"                      # a web or desktop capture has no status bar unless the deck says keep
    decision = statusbar_decision(mode, cap.get("statusbar_state", "missing"), policy, None, frame["kind"],
                                  (top_bar or {}).get("os") or frame.get("os"), cap.get("os"), hidden)
    shot = {"id": "dev%d" % index, "cap_id": "cap%d" % index, "capture": capture_id, "path": path, "sha256": actual,
            "cw": info["width"], "ch": info["height"], "os": cap.get("os"), "frame_id": frame_id, "frame": frame,
            "top_bar": top_bar, "bottom_bar": bottom_bar, "action": decision["action"], "glyphs": decision["glyphs"],
            "state": cap.get("statusbar_state", "missing"), "policy": policy, "mockup": bool(cap.get("mockup")),
            "strips": strips_for(decision["action"], top_bar, bottom_bar), "uri": data_uri(path),
            "own_bar": own_bar, "hidden_bar": hidden}
    if frame["kind"] in ("phone", "tablet") and cap.get("os") in ("ios", "android") and (
            tablet_shaped(info["width"], info["height"]) != (frame["kind"] == "tablet")):
        shot["shape_note"] = "capture %r has the shape of a %s but sits in a %s frame: supply a capture from that device class" % (
            capture_id, "tablet" if frame["kind"] == "phone" else "phone", frame["kind"])
    if decision["glyphs"] and top_bar:
        klass = "tablet" if frame["kind"] == "tablet" else "phone"
        top_svg = find_asset("statusbar", (top_id,), top_bar.get("os"), klass)
        bottom_svg = find_asset("bottombar", (bottom_id,), top_bar.get("os"), klass) if bottom_bar else None
        landscape = info["width"] > info["height"]
        shot["top_svg"] = top_svg["file"] if top_svg else shipped_bar(top_id, top_bar, landscape)
        shot["bottom_svg"] = bottom_svg["file"] if bottom_svg else shipped_bar(bottom_id, bottom_bar, landscape)
        shot["attributions"] = [bar_attribution(bar_id, bar) for bar_id, bar, source in (
            (top_id, top_bar, shot["top_svg"]), (bottom_id, bottom_bar, shot["bottom_svg"])) if isinstance(source, dict)]
    orientation = "landscape" if info["width"] > info["height"] else "portrait"
    bezel = None if bare else (find_asset("bezel", (frame_id + "-" + orientation,)) or find_asset("bezel", (frame_id,)))
    turned = bezel and bezel.get("size") and ("landscape" if bezel["size"][0] > bezel["size"][1] else "portrait") != orientation
    if turned and frame["kind"] in ("phone", "tablet"):
        shot["bezel_skipped"] = ("imported bezel %r is %s, the capture %r is %s: the drawn frame is used (a bezel is never "
                                 "rotated; import the %s export as %s-%s)" % (
                                     frame_id, "portrait" if orientation == "landscape" else "landscape", capture_id,
                                     orientation, orientation, frame_id, orientation))
    elif bezel and bezel.get("screen") and frame["kind"] in ("phone", "tablet"):
        hole = bezel["screen"][2] / float(bezel["screen"][3])
        short = float(min(info["width"], info["height"]))
        screen_h = info["height"] + (shot["strips"][0] + shot["strips"][1]) * short
        if abs(hole - info["width"] / screen_h) / hole <= 0.02:
            shot["bezel_asset"] = {"size": bezel["size"], "screen": bezel["screen"], "uri": data_uri(bezel["file"]),
                                   "source": bezel.get("source"),
                                   "file": bezel["file"], "opaque": bool(bezel.get("opaque")),
                                   "screen_radius": bezel.get("screen_radius") or 0}
            flag = slide.get("bezel_shadow") if slide.get("bezel_shadow") is not None else one_set.get("bezel_shadow")
            shot["bezel_shadow"] = bool(flag)
        else:
            shot["bezel_skipped"] = "imported bezel %r has a %.3f screen, the capture is %.3f: the drawn frame is used" % (
                frame_id, hole, info["width"] / screen_h)
    return shot


def build_page(deck, slug, one_set, slide, slide_index, target_id, locale, layer=None, scale=1, factor=None):
    """-> (html text, context for the gates). Pure assembly: no browser, no writes.
    layer "#000000" or "#ffffff": the first capture is hidden and its screen filled with that colour (see `layers`).
    scale 2: the layout stays in CSS pixels at the target size; the canvases get twice the backing pixels, so a
    browser run at device scale factor 2 paints the background and plate as sharp as the text. `factor` is the
    supersampling part of `scale` (see supersample)."""
    target = surfaces()["targets"][target_id]
    mode = set_mode(deck, one_set)
    W, H = target["width"], target["height"]
    if one_set.get("orientation") == "landscape" and target.get("orientation_swappable") and H > W:
        W, H = H, W
    layout = slide["layout"]
    spec = LAYOUTS[layout]
    background = dict(one_set.get("background") or {"kind": "solid"})
    invert = bool(slide.get("invert")) and background.get("kind") != "plate" and not background.get("plate")
    pal = palette(deck["theme"], invert)
    copy = dict((slide.get("copy") or {}).get(locale) or {})
    lang = lang_of(locale)
    rtl = locale in (deck.get("rtl_locales") or []) or lang in RTL_LANGS
    app = deck.get("app") or {}
    hero = layout == "card-hero-scene"
    owner = slide
    if spec.get("span") == "end":             # the right half of the device the device-span slide before it owns
        owner = one_set["slides"][slide_index - 1]
        slide = dict(slide, bleed=owner.get("bleed"))
    refs = [r for r in (owner.get("capture"), owner.get("capture2")) if r]
    shots = [make_shot(deck, slug, pick_capture(ref, target), locale, target_id, mode, one_set, owner, i, bare=hero)
             for i, ref in enumerate(refs)]
    sources, measure, notes = [], [], []
    plate_id = slide.get("plate") or background.get("plate")
    plate, plate_info, quad_canvas, quad_box, mismatch, hero_spec, aspect_flip = None, None, None, None, None, None, None
    if plate_id:
        plate = deck["plates"][plate_id]
        plate_path = resolve_path(slug, plate["file"])
        plate_info = probe_image(plate_path)
        sources.append('<img class="lk-src" id="plate-src" alt="" src="%s">' % data_uri(plate_path))
    insets = target.get("safe_insets") or {}
    # A cutoff surface crops its edges: everything but the background is laid out inside `safe`. An overlay
    # placement only covers the strips with its own interface, so there portrait text starts below the top one.
    cutoff = safe_box(target, W, H) if insets and target.get("cutoff_zones") else None
    if hero:
        if plate is None or plate_info is None:
            raise Fail("deck_invalid", "layout card-hero-scene needs a plate id from deck.plates")
        margins = None
        if cutoff:
            margins = (max(0.04 * W, cutoff[0]), max(0.03 * H, cutoff[1]), max(0.04 * W, W - cutoff[2]),
                       max(0.03 * H, H - cutoff[3]))
        draw, quad_canvas = hero_mapping(plate_info["width"], plate_info["height"], plate["quad"], W, H, margins)
        quad_box = quad_bbox(quad_canvas)
    style = lockup_style(slide, background) if spec.get("lockup") else None
    if style and cutoff and "width" not in (slide["lockup"] if isinstance(slide.get("lockup"), dict) else {}):
        # an unasked width fits the cutoff box: card-lockup's zone is 88 percent of its width (plan_page)
        style["width"] = min(style["width"], round(0.88 * (cutoff[2] - cutoff[0]) / W, 4))
    wanted = dict(style, width_px=style["width"] * W, aspect=lockup_aspect(app, slug)) if style else lockup_wanted(one_set, slide)
    plan = plan_page(layout, W, H, slide, shots, quad_box=quad_box, has_sub=bool(copy.get("sub")), copy=copy,
                     min_px=float(target.get("min_text_px") or 0), gutter=float(target.get("gutter_px") or 0),
                     safe_top=0.0 if cutoff else float(insets.get("top") or 0), safe=cutoff, lockup=wanted,  # pyright: ignore[reportArgumentType] (card-lockup passes its size)
                     compact=compact_wanted(one_set, slide), device_top=device_top_of(one_set, slide))
    if not lockup_wanted(one_set, slide):       # Play draws icon and app name next to the graphic itself
        plan["lockup"] = None
    strength = 1.0 if luminance(pal["bg"]) < 0.3 else 0.55
    body = []
    devices_spec = []
    if hero and plate is not None and quad_canvas is not None and quad_box is not None:
        shot = shots[0]
        top = math.hypot(quad_canvas[1][0] - quad_canvas[0][0], quad_canvas[1][1] - quad_canvas[0][1])
        geo = body_geometry({"kind": "none", "bezel": 0}, max(320.0, round(top * 2.0)), shot["cw"], shot["ch"], shot["strips"])
        shot.update(geo)
        estimate = plate.get("aspect_estimate") or quad_aspect(plate["quad"])
        mismatch = aspect_gap(shot["sw"] / float(shot["sh"]), estimate, plate.get("aspect_range"))
        if (shot["sw"] > shot["sh"]) != (estimate > 1.0):
            aspect_flip = ("landscape", "portrait") if estimate > 1.0 else ("portrait", "landscape")
        matrix = homography([(0, 0), (shot["sw"], 0), (shot["sw"], shot["sh"]), (0, shot["sh"])], grow_quad(quad_canvas, 2.0))
        body.append('<div class="lk-dev" id="%s" style="left:0;top:0;width:%dpx;height:%dpx;z-index:1;transform-origin:0 0;transform:%s">'
                    '<div class="lk-screen" style="left:0;top:0;width:%dpx;height:%dpx">%s</div></div><canvas id="lk-plate" width="%d" height="%d" '
                    'style="z-index:2;width:%dpx;height:%dpx"></canvas>'
                    % (shot["id"], shot["sw"], shot["sh"], matrix3d(matrix), shot["sw"], shot["sh"], screen_inner(shot), W * scale, H * scale, W, H))
        dim = background.get("dim")
        hero_spec = {"plate": "plate-src", "draw": draw, "key": plate.get("key") or "magenta", "med": plate.get("median_key_luma") or 235,
                     "box": _grow(quad_box, 0.05 * max(quad_box[2], quad_box[3])),
                     "scrim": hero_scrim(W, plan["blocks"][0]["box"], plan["text_side"] == "left",
                                         dim if dim is not None else HERO_SCRIM_DIM, luminance(pal["fg"]) > 0.5)}
        background = {"kind": "solid", "color": "bg"}
    else:
        for geo in plan["devices"]:
            shot = shots[geo["shot"]]
            shot.update(geo)
            body.append(device_html(shot, app, strength))
        if plan["zoom"]:
            if not plan["devices"]:            # no context device on this canvas (a landscape zoom): only the crop card
                shots[0].update({"action": "none", "frame_id": "none", "unplaced": True})
            body.append(zoom_html(shots[0], plan["zoom"], slide["zoom"], strength))
            measure.append({"id": "lk-zoom", "role": "zoom"})
    for shot in shots:
        bar_frac = shot.get("own_bar") or (shot["top_bar"] or {}).get("height") or 0.0
        if not shot.get("unplaced"):          # the page measures a device it drew, never one it left out
            devices_spec.append({"id": shot["id"], "cap": shot["cap_id"], "capture": shot["capture"], "plan": shot["action"],
                                 "glyphs": shot["glyphs"], "barFrac": bar_frac, "kind": shot["frame"]["kind"]})
        for key in ("bezel_skipped", "shape_note"):
            if shot.get(key):
                notes.append(shot[key])
    slides = one_set["slides"]
    jpeg = not layer and export_of(one_set, target_id)["format"] == "jpg"
    if factor is None:
        factor = supersample(slide, W * H * scale * scale)
    grain = JPEG_GRAIN * factor if jpeg else 0        # an F x F average divides the grain of a supersampled page by F
    bg_spec = background_spec(background, pal, W, H, slide_index, len(slides), plate_info, grain)
    fit_lockup = None
    if style and plan["lockup"]:          # the page scales the lockup to the width, then centres the scrim on it
        spot = plan["lockup"]
        fit_lockup = {"width": round(style["width"] * W, 1), "share": style["width"],
                      "maxW": round(spot["w"], 1), "maxH": round(spot["h"], 1), "shadow": style["shadow"]}
        if style["scrim"] > 0:
            bg_spec["scrim"] = {"alpha": style["scrim"]}  # pyright: ignore[reportArgumentType] (the page script reads it)
    back_decor = []
    for d_index, item in enumerate(slide.get("decor") or []):
        path = resolve_path(slug, deck["decor"][item["ref"]]["file"])
        width = item["w"] * W
        if item.get("z", "back") == "front":
            info = probe_image(path)
            height = width * info["height"] / float(info["width"])
            body.append('<img class="lk-decor" id="decF%d" alt="" style="left:%s;top:%s;width:%s;transform:rotate(%sdeg);'
                        'filter:drop-shadow(0 %s %s rgba(0,0,0,0.30))" src="%s">' % (
                            d_index, px(item["x"] * W - width / 2.0), px(item["y"] * H - height / 2.0), px(width),
                            item.get("rotate") or 0, px(width * 0.045), px(width * 0.09), data_uri(path)))
            measure.append({"id": "decF%d" % d_index, "role": "decor_front"})
        else:
            sources.append('<img class="lk-src" id="decB%d" alt="" src="%s">' % (d_index, data_uri(path)))
            back_decor.append({"img": "decB%d" % d_index, "ref": item["ref"], "cx": item["x"] * W, "cy": item["y"] * H,
                               "w": width, "rotate": item.get("rotate") or 0})
    uris = {}
    for key in ("icon", "logo"):
        if app.get(key):
            path = resolve_path(slug, app[key])
            if path.lower().endswith(".svg"):
                load_svg(path)
            uris[key] = data_uri(path)
    if plan["connector"]:
        spot = plan["connector"]
        body.append('<div id="lk-flow" style="position:absolute;left:%s;top:%s;width:%s;height:%s;z-index:7;color:var(--fg)">'
                    '<svg viewBox="0 0 48 48" width="100%%" height="100%%" fill="none" stroke="currentColor" stroke-width="4.5" '
                    'stroke-linecap="round" stroke-linejoin="round"><path d="M6 24H41M28 11l13 13-13 13"/></svg></div>'
                    % (px(spot["x"]), px(spot["y"]), px(spot["w"]), px(spot["h"])))
        measure.append({"id": "lk-flow", "role": "connector"})
    if plan["lockup"]:
        body.append(lockup_html(plan, app, uris, W))
        measure.append({"id": "lk-lockup-i", "role": "lockup"})
    if plan["icon"]:
        x, y, side = plan["icon"]
        if uris.get("icon"):
            body.append('<img id="lk-icon" alt="" style="position:absolute;left:%s;top:%s;width:%s;height:%s;border-radius:22.5%%;'
                        'object-fit:cover;box-shadow:%s" src="%s">' % (px(x), px(y), px(side), px(side), shadow_css(side, strength * 0.9), uris["icon"]))
        else:
            letter = upper_for((app.get("name") or "?").strip()[:1], locale)
            body.append('<div class="lk-mono" id="lk-icon" style="left:%s;top:%s;width:%s;height:%s;font-size:%s">%s</div>'
                        % (px(x), px(y), px(side), px(side), px(side * 0.86), esc(letter)))
        measure.append({"id": "lk-icon", "role": "icon"})
    text_markup, block_ids = text_html(plan, copy, rtl)
    body.append(text_markup)
    face_css, stack = font_css(deck, slug)
    font = (deck["theme"].get("font") or {})
    head = plan["head"] * (0.9 if lang in WIDE_SCRIPT_LANGS else 1.0)
    plain_badge = deck["theme"].get("badge_style") == "text"     # a bare eyebrow: no pill, the readable accent, wide tracking
    badge_bg = mix(pal["bg"], pal["accent"], 0.22)
    badge_fg = pal["accent_text"] if plain_badge else pal["fg"]
    halo = "rgba(0,0,0,0.45)" if luminance(pal["fg"]) > 0.5 else "rgba(255,255,255,0.5)"
    variables = ("--fs:%s;--fg:%s;--fg-alt:%s;--accent:%s;--muted:%s;--wh:%d;--wb:%d;--sub:%s;--badge:%s;--track:%s;"
                 "--badge-bg:%s;--badge-fg:%s;--halo:%s;--badge-track:%s;--min-px:%s" % (
                     px(head), to_hex(pal["fg"]), to_hex(pal["fg_alt"]), to_hex(pal["accent_text"]), to_hex(pal["muted"]),
                     font.get("weight_headline") or 800, font.get("weight_body") or 500, plan["sub"], plan["badge"],
                     "0" if lang in NO_TRACKING_LANGS else "-0.028em", "transparent" if plain_badge else to_hex(badge_bg),
                     to_hex(badge_fg), halo, "0" if lang in NO_TRACKING_LANGS else ("0.1em" if plain_badge else "0.04em"),
                     px(float(target.get("min_text_px") or 0))))
    colors = {"headline": list(pal["fg"]), "sub": list(pal["fg_alt"]), "em": list(pal["accent_text"])}  # pyright: ignore[reportArgumentType] (theme hex is validated)
    if plain_badge:                 # nothing of its own behind it: measured against the ground like the headline
        variables += ";--badge-pad:0"
        colors["badge"] = list(badge_fg)  # pyright: ignore[reportArgumentType] (theme hex is validated)
    spec_js = {"W": W, "H": H, "D": scale, "bg": bg_spec, "backDecor": back_decor, "hero": hero_spec, "devices": devices_spec,
               "text": {"blocks": block_ids, "base": head, "floor": FIT_FLOOR, "step": FIT_STEP}, "colors": colors,
               "measure": measure}
    if fit_lockup:
        spec_js["lockup"] = fit_lockup
    hole = ""
    if layer and shots:
        hole = "#%s{visibility:hidden}#%s .lk-screen{background:%s !important}" % (shots[0]["cap_id"], shots[0]["id"], layer)
    page = ('<!doctype html><html lang="%s"><head><meta charset="utf-8"><title>%s</title><style>%s%s:root{%s}'
            'html,body{width:%dpx;height:%dpx}body{background:%s;font-family:%s}' + hole + '</style></head><body>'
            '<pre id="lk-metrics">pending</pre>%s<canvas id="lk-bg" width="%d" height="%d" style="width:%dpx;height:%dpx"></canvas>%s'
            '<script>window.LK_SPEC=%s;</script><script>%s</script></body></html>') % (
        esc(locale), esc("%s %s %s" % (one_set["id"], target_id, slide["id"])), face_css, PAGE_CSS, variables, W, H,
        bg_spec["color"], stack, "".join(sources), W * scale, H * scale, W, H, "".join(body),
        json.dumps(spec_js, ensure_ascii=False).replace("</", "<\\/"), PAGE_JS)
    over = []
    budget = copy_spec(slide)
    for key, limit, lines in (("headline", budget["chars"], copy.get("headline") or []), ("sub", budget["sub_chars"], copy.get("sub") or [])):
        over += [{"role": key, "line": line, "chars": len(line), "budget": limit} for line in lines if limit and len(line) > limit]
    context = {"W": W, "H": H, "target_id": target_id, "target": target, "layout": layout, "mode": mode, "locale": locale,
               "set": one_set["id"], "slide": slide["id"], "slide_index": slide_index, "slide_count": len(slides),
               "strip": (one_set.get("background") or {}).get("kind") == "strip", "quad_box": quad_box,
               "aspect_mismatch": mismatch, "aspect_flip": aspect_flip, "shots": shots, "plate_id": plate_id,
               "edges": transformed_edges(shots, quad_canvas if hero else None),
               "plate_file": resolve_path(slug, plate["file"]) if plate else None, "over_budget": over, "notes": notes,
               "badge_contrast": round(contrast_ratio(badge_fg, badge_bg), 2) if copy.get("badge") and not plain_badge else None,
               "frame": shots[0]["frame_id"] if shots else None, "invert": invert,
               "accent_text": to_hex(pal["accent_text"]) if to_hex(pal["accent_text"]) != to_hex(pal["accent"]) else None,
               "mockup": any(s["mockup"] for s in shots),
               "attributions": [row for index, row in enumerate(a for s in shots for a in s.get("attributions") or [])
                                if row not in [a for s in shots for a in s.get("attributions") or []][:index]]}
    return page, context


# ----------------------------------------------------------------------------------------------- gates

def _grow(rect, margin):
    return [rect[0] - margin, rect[1] - margin, rect[2] + 2 * margin, rect[3] + 2 * margin]


def _overlap(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def largest_empty_band(rects, height):
    """Tallest full-width band that no content rectangle touches, as a share of the canvas height."""
    spans = sorted((max(0.0, r[1]), min(float(height), r[1] + r[3])) for r in rects if r[3] > 0 and r[1] < height and r[1] + r[3] > 0)
    gap, cursor = 0.0, 0.0
    for top, bottom in spans:
        gap = max(gap, top - cursor)
        cursor = max(cursor, bottom)
    return max(gap, height - cursor) / float(height)


def evaluate_gates(metrics, ctx):
    """Hard gates and warnings of one rendered page, from the rectangles and contrasts the page measured."""
    hard, warns = [], []
    W, H = ctx["W"], ctx["H"]
    short = float(min(W, H))
    target = ctx["target"]
    screenshot = target.get("kind") == "screenshot"

    def add(rows, code, message, **extra):
        rows.append(dict({"code": code, "message": message}, **extra))
    texts = [t for t in metrics.get("text") or [] if t["role"] in ("headline", "sub", "badge")]
    text_rects = [t["rect"] for t in texts]
    device_rects = [d["rect"] for d in metrics.get("devices") or []]
    device_rects += [b["rect"] for b in metrics.get("boxes") or [] if b["role"] in ("zoom", "connector")]
    if ctx.get("quad_box"):
        device_rects = [ctx["quad_box"]]
    scale = metrics.get("fit_scale", 1.0)
    if not metrics.get("fit_ok", True):
        add(hard, "copy_too_long", "the copy does not fit its box at %d%% of the layout size: rewrite the copy (fewer or "
            "shorter lines); do not shrink further" % int(round(FIT_FLOOR * 100)), fit_scale=scale)
    elif scale < 0.9:
        add(warns, "fit_scale", "the headline was shrunk to %d%% to fit: shorter lines read better at thumbnail size"
            % int(round(scale * 100)), fit_scale=scale)
    # a card on a target with cutoff zones is laid out in the safe box as if that were its canvas, so the margin is a
    # share of that box too: of the whole canvas it was 51 px on appstore-search, where card-flow keeps 36 between
    # caption and pair, and every top caption failed (2026-10-12)
    area = short
    if target.get("cutoff_zones") and target.get("safe_insets"):
        x0, y0, x1, y1 = safe_box(target, W, H)
        area = min(x1 - x0, y1 - y0)
    margin = 0.02 * area
    if any(_overlap(t, _grow(d, margin)) for t in text_rects for d in device_rects):
        add(hard, "text_overlaps_device", "a text box touches the device or the screen quad (2% margin): shorten the "
            "copy or pick a layout with more room")
    contrasts = [(t["contrast"], t["role"]) for t in metrics.get("text") or [] if t.get("contrast") is not None]
    if ctx.get("badge_contrast") is not None:
        contrasts.append((ctx["badge_contrast"], "badge"))
    if contrasts:
        lowest, role = min(contrasts)
        if lowest < 3.0:
            add(hard, "contrast", "%s text has %.2f:1 against the pixels behind it (needs 3.0, better 4.5): change the "
                "theme colours, dim the plate or move the text" % (role, lowest), ratio=lowest, role=role)
        elif lowest < 4.5:
            add(warns, "contrast", "%s text has %.2f:1 against the pixels behind it (4.5 is comfortable)" % (role, lowest),
                ratio=lowest, role=role)
    gutter = float(target.get("gutter_px") or 0.04 * short)
    if any(r[0] < gutter - 0.5 or r[1] < gutter - 0.5 or r[0] + r[2] > W - gutter + 0.5 or r[1] + r[3] > H - gutter + 0.5
           for r in text_rects):
        add(warns, "gutter", "text sits closer than %d px to an edge" % round(gutter))
    share = None
    if screenshot and device_rects and ctx["layout"] != "zoom":
        share = max((min(H, r[1] + r[3]) - max(0.0, r[1])) / float(H) for r in device_rects)
        if not 0.50 <= share <= 0.85:
            add(warns, "device_share", "the device covers %.2f of the canvas height (0.50 to 0.85 reads best)" % share, share=round(share, 3))
    band = None
    if screenshot and ctx["layout"] != "text-only":      # a text slide is airy on purpose
        content = text_rects + device_rects + [b["rect"] for b in metrics.get("boxes") or []] + [d["rect"] for d in metrics.get("decor") or []]
        band = largest_empty_band(content, H)
        if band > 0.25:
            add(warns, "empty_band", "an empty band covers %.2f of the height" % band, share=round(band, 3))
    for row in ctx.get("over_budget") or []:
        add(warns, "chars_per_line", "%s line %r has %d characters, the layout budget is %d" % (row["role"], row["line"], row["chars"], row["budget"]))
    tagline = None
    if target.get("store") == "play" and text_rects:
        blocks = {}
        for t in texts:
            r, box = t["rect"], blocks.get(t.get("block"))
            blocks[t.get("block")] = [r[0], r[1], r[0] + r[2], r[1] + r[3]] if box is None else [
                min(box[0], r[0]), min(box[1], r[1]), max(box[2], r[0] + r[2]), max(box[3], r[1] + r[3])]
        tagline = sum((b[2] - b[0]) * (b[3] - b[1]) for b in blocks.values()) / float(W * H)
        if tagline > 0.20:
            add(warns, "play_tagline_share", "text covers %.2f of the image; Google asks for taglines within 0.20" % tagline, share=round(tagline, 3))
    limit = target.get("text_share_max")
    if limit and text_rects:
        covered = sum(r[2] * r[3] for r in text_rects) / float(W * H)
        if covered > limit:
            add(warns, "text_share", "text covers %.2f of the image; %s asks for overlaid text and logos within %.2f"
                % (covered, target["label"], limit), share=round(covered, 3))
    insets = target.get("safe_insets")
    if insets:
        keep = safe_box(target, W, H)
        boxes = text_rects + [b["rect"] for b in metrics.get("boxes") or [] if b["role"] in ("lockup", "icon")]
        cutoff = bool(target.get("cutoff_zones"))
        if cutoff:               # a cropped edge takes the capture with it, an interface strip only covers it
            boxes = boxes + device_rects
        if any(r[0] < keep[0] - 0.5 or r[1] < keep[1] - 0.5 or r[0] + r[2] > keep[2] + 0.5 or r[1] + r[3] > keep[3] + 0.5 for r in boxes):
            if cutoff:
                add(warns, "cutoff_zone", "text, the lockup or a capture reaches into the cutoff zones %s may crop "
                    "(left %d%%, right %d%%, top %d%%, bottom %d%%): the logo, the app name, the copy and the main UI "
                    "belong inside x %d to %d, y %d to %d; only background runs to the edges"
                    % (target["label"], round(insets.get("left", 0) * 100), round(insets.get("right", 0) * 100),
                       round(insets.get("top", 0) * 100), round(insets.get("bottom", 0) * 100),
                       round(keep[0]), round(keep[2]), round(keep[1]), round(keep[3])))
            else:
                add(warns, "ad_safe_zone", "text or the lockup sits inside the strips this placement covers with its own interface "
                    "(top %d%%, bottom %d%%, sides %d%%): move it, or accept it for feeds that show the image bare"
                    % (round(insets.get("top", 0) * 100), round(insets.get("bottom", 0) * 100), round(insets.get("left", 0) * 100)))
    if ctx.get("strip") and ctx.get("slide_count", 1) > 1:
        seam = 0.03 * W
        first, last = ctx["slide_index"] == 0, ctx["slide_index"] == ctx["slide_count"] - 1
        # a span pair's device crosses its seam on purpose; anything else near a seam is an accident
        crossing = [] if LAYOUTS.get(ctx["layout"], {}).get("span") else device_rects
        if any((not first and r[0] < seam) or (not last and r[0] + r[2] > W - seam) for r in text_rects + crossing):
            add(warns, "seam", "a text box or a device sits within 3% of a seam of the panorama strip")
    if target.get("safe_aspect") and W / float(H) < target["safe_aspect"]:
        band_h = W / float(target["safe_aspect"])
        low, high = (H - band_h) / 2.0, (H + band_h) / 2.0
        boxes = text_rects + [b["rect"] for b in metrics.get("boxes") or [] if b["role"] in ("lockup", "icon")]
        if any(r[1] < low - 0.5 or r[1] + r[3] > high + 0.5 for r in boxes):
            add(warns, "safe_crop", "content falls outside the centred %g:1 band that a wider card keeps" % target["safe_aspect"])
    if ctx.get("jagged"):
        add(hard, "jagged_edge", "the %s capture edges step (median %.3f px off a smooth line at %dx supersampling): headless "
            "Chromium drew the transform without anti-aliasing, or the plate's own screen edge is stepped; do not deliver "
            "this file"
            % ("warped" if (ctx.get("edges") or {}).get("kind") == "warp" else "tilted", ctx["edge_rms"], ctx["supersample"]),
            edge_rms=ctx["edge_rms"])
    mismatch = ctx.get("aspect_mismatch")
    if mismatch is not None:
        if mismatch > 0.15:
            flip = ctx.get("aspect_flip")
            add(hard, "aspect_mismatch", "the capture and the plate's screen differ by %d%% in aspect: %s"
                % (round(mismatch * 100), "the plate's screen is %s and the capture is not: run screen-quad again with "
                   "--orientation %s, or use a %s capture" % (flip[0], flip[1], flip[0]) if flip else
                   "generate the plate again and name the capture's aspect in its prompt"), mismatch=round(mismatch, 4))
        elif mismatch > 0.08:
            add(warns, "aspect_mismatch", "the capture is stretched by %d%% to fill the plate's screen" % round(mismatch * 100),
                mismatch=round(mismatch, 4))
    lockup = metrics.get("lockup")
    if lockup:
        if lockup.get("contrast") is not None and lockup["contrast"] < 3.0:
            add(warns, "lockup_contrast", "the lockup's main colour %s has %.2f:1 against the ground behind it (3.0 reads at a "
                "glance): raise the scrim, pick a calmer plate area, or use the logo version made for this ground"
                % (lockup.get("ink"), lockup["contrast"]), ratio=lockup["contrast"])
        if lockup.get("capped"):
            add(warns, "lockup_size", "the lockup reached %.2f of the width, not the %.2f asked: the card keeps it inside its zone "
                "(%s). A tall mark reaches its height first" % (lockup.get("width_share") or 0, lockup.get("asked") or 0,
                                                                 "the cutoff box" if target.get("cutoff_zones") else "card margins"),
                share=lockup.get("width_share"))
    fronts = [b["rect"] for b in metrics.get("boxes") or [] if b["role"] == "decor_front"]
    if any(_overlap(t, f) for t in text_rects for f in fronts):
        add(warns, "decor_overlaps_text", "a front decor element covers text")
    by_id = {s["id"]: s for s in ctx.get("shots") or []}
    bars = []
    for dev in metrics.get("devices") or []:
        shot = by_id.get(dev.get("id"))
        if not shot:
            continue
        final = {"action": shot["action"], "warning": None}
        if shot["action"] == "mask":
            final = {"action": "repaint" if shot["glyphs"] else "repaint_blank", "warning": None}
        elif shot["action"] == "test_flat":
            final = statusbar_decision(ctx["mode"], shot["state"], shot["policy"], bool(dev.get("flat")), shot["frame"]["kind"],
                                       (shot["top_bar"] or {}).get("os") or shot["frame"].get("os"), shot["os"],
                                       bool(shot.get("hidden_bar")))
        bars.append({"capture": shot["capture"], "state": shot["state"], "action": final["action"], "strip": dev.get("strip")})
        if final["warning"]:
            add(warns, final["warning"], {"statusbar_kept_dirty": "the status bar of capture %r is not a flat strip, so it "
                                          "was kept as it is: %s" % (shot["capture"], CLEAN_CAPTURE_TIP),
                                          "statusbar_identifies_os": "capture %r keeps a status bar that identifies its "
                                          "platform on a universal page: %s" % (shot["capture"], CLEAN_CAPTURE_TIP),
                                          "statusbar_os_mismatch": "capture %r shows the status bar of another platform "
                                          "than this page: supply a capture per OS" % shot["capture"]}[final["warning"]])
    if ctx["layout"] == "card-hero-scene" and target.get("store") == "play":
        add(warns, "hero_scene_on_play", "Google's guidance discourages people handling a device and device imagery in "
            "Play assets: prefer a framed or frameless capture here")
    sizes = [t["font_px"] for t in texts if t.get("font_px")]
    smallest = min(sizes) if sizes else None
    floor = target.get("min_text_px")
    if floor and smallest is not None and smallest < floor - 0.05:
        add(warns, "small_text", "the smallest copy is set at %.1f px; below %d px it cannot be read where %s is shown"
            % (smallest, floor, target["label"]), px=smallest)
    for note in ctx.get("notes") or []:
        add(warns, "note", note)
    summary = {"fit_scale": scale, "headline_px": metrics.get("headline_px"),
               "contrast_min": min(contrasts)[0] if contrasts else None, "contrast_role": min(contrasts)[1] if contrasts else None,
               "accent_text": ctx.get("accent_text"), "min_text_px": smallest, "device_share": round(share, 3) if share is not None else None,
               "empty_band": round(band, 3) if band is not None else None,
               "tagline_share": round(tagline, 3) if tagline is not None else None,
               "aspect_mismatch": round(mismatch, 4) if mismatch is not None else None, "statusbars": bars,
               "edge_rms": ctx.get("edge_rms"), "supersample": ctx.get("supersample")}
    if lockup:
        summary["lockup"] = {key: lockup.get(key) for key in ("rect", "width_share", "asked", "contrast", "ink")}
    return hard, warns, summary


# ----------------------------------------------------------------------------------------------- commands

def cmd_tools(_args):
    browser = find_browser()
    ffmpeg, sips = find_tool("ffmpeg"), find_tool("sips")
    can_render = bool(browser)
    return {"ok": True, "browser": {"found": can_render, "path": browser},
            "ffmpeg": {"found": bool(ffmpeg), "path": ffmpeg}, "sips": {"found": bool(sips), "path": sips},
            "can": {"specs": True, "init": True, "capture": True, "probe": True, "text": True, "validate": True,
                    "assets_import": True, "bezel_hole_detection": can_render, "screen_quad": can_render,
                    "compose": can_render, "sheet": can_render, "layers": bool(can_render and ffmpeg), "convert_heic_tiff": bool(ffmpeg or sips)},
            "hint": None if can_render else MISSING_HINT}, 0


def cmd_specs(args):
    data = surfaces()
    rows = []
    for tid, row in data["targets"].items():
        if args.target and tid not in args.target:
            continue
        if args.store and row["store"] != args.store:
            continue
        rows.append(dict({"id": tid}, **row))
    unknown = [t for t in args.target or [] if t not in data["targets"]]
    if unknown:
        raise usage("unknown target %s (known: %s)" % (", ".join(unknown), ", ".join(sorted(data["targets"]))))
    return {"ok": True, "verified_on": data["verified_on"], "targets": rows, "unverified": data.get("unverified", []),
            "attributions": attributions(),
            "hint": "a null is a number that was not read from the official page on verified_on: never fill it from memory"}, 0


DEFAULT_THEME = {"bg": "#0f172a", "bg_alt": "#1e293b", "fg": "#ffffff", "fg_alt": "#cbd5e1", "accent": "#3b82f6",
                 "muted": "#64748b", "font": {"family": "system", "files": [], "weight_headline": 800, "weight_body": 500}}
MODE_TARGETS = {"app-store": ["appstore-iphone-69"], "play": ["play-phone"], "both": ["appstore-iphone-69", "play-phone"],
                "universal": ["appstore-iphone-69", "play-phone"]}


def cmd_init(args):
    slug = need_slug(args.slug)
    locales = args.locale or ["en"]
    for locale in locales:
        if not LOCALE_RE.fullmatch(locale):
            raise usage("--locale %r is not a locale code such as en, tr or pt-BR" % locale)
    if len(set(locales)) != len(locales):
        raise usage("--locale lists a locale twice")
    root = project_dir(slug)
    path = deck_path(slug)
    for folder in ("captures", "plates", "build"):
        os.makedirs(os.path.join(root, folder), exist_ok=True)
    os.makedirs(output_dir(slug), exist_ok=True)
    created = not os.path.exists(path)
    if created:
        deck = {"schema": SCHEMA, "slug": slug, "mode": args.mode,
                "app": {"name": args.name or args.slug.strip(), "icon": None, "logo": None, "url": None},
                "theme": DEFAULT_THEME, "locales": locales, "default_locale": locales[0],
                "rtl_locales": [l for l in locales if lang_of(l) in RTL_LANGS], "facts": {"numbers": [], "claims": []},
                "captures": {}, "plates": {}, "decor": {},
                "sets": [{"id": "store", "targets": MODE_TARGETS[args.mode], "orientation": "portrait", "frame": "auto",
                          "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160}, "slides": []}]}
        save_deck(slug, deck)
    else:
        deck = load_deck(slug)
    return {"ok": True, "created": created, "slug": slug, "deck": path, "project": root, "output": output_dir(slug),
            "mode": deck.get("mode"), "locales": deck.get("locales"),
            "note": None if created else "a deck already exists and was left untouched",
            "next": "capture add for every real screen, then write slides and copy into deck.json, then text"}, 0


def cmd_capture_add(args):
    slug = need_slug(args.slug)
    deck = load_deck(slug)
    if not ID_RE.fullmatch(args.id):
        raise usage("--id uses lower-case letters, digits and hyphens")
    if args.locale and args.locale not in (deck.get("locales") or []):
        raise usage("--locale %r is not in the deck's locales %s" % (args.locale, deck.get("locales")))
    info = probe_image(args.file)
    near = nearest_screen(info["width"], info["height"])
    captures = deck.setdefault("captures", {})
    existing = captures.get(args.id)
    os_name = args.os or (existing or {}).get("os") or (near["os"] if near["match"] else None)
    if os_name is None:
        if info["width"] > info["height"]:
            os_name = "web"
        else:
            raise usage("--os is required: %dx%d matches no known full-screen size (ios, android, web or desktop)"
                        % (info["width"], info["height"]))
    digest = sha256_file(args.file)
    folder = os.path.join("captures", args.locale) if args.locale else "captures"
    relative = "%s/%s%s" % (folder.replace(os.sep, "/"), args.id, CAPTURE_EXT[info["format"]])
    target = resolve_path(slug, relative)
    if os.path.exists(target) and sha256_file(target) != digest and not args.replace:
        raise Fail("exists", "%s already holds a different file" % target,
                   hint="captures are archived untouched: use a new --id, or pass --replace if this file supersedes it")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if not os.path.exists(target) or sha256_file(target) != digest:
        shutil.copyfile(args.file, target)
    if args.locale:
        if existing is None:
            raise Fail("not_found", "capture %r has no default file yet: add it without --locale first" % args.id)
        existing.setdefault("by_locale", {})[args.locale] = relative
        existing.setdefault("sha256_by_locale", {})[args.locale] = digest
        entry = existing
    else:
        fullscreen = near["match"] and os_name in ("ios", "android")
        entry = dict(existing or {})
        entry.update({"file": relative, "sha256": digest, "os": os_name, "width": info["width"], "height": info["height"],
                      "alpha": info["alpha"], "fullscreen_match": near if near["match"] else None,
                      "statusbar_state": (existing or {}).get("statusbar_state") or ("clean" if fullscreen else "missing"),
                      "statusbar": (existing or {}).get("statusbar") or "auto",
                      "mockup": bool(args.mockup or (existing or {}).get("mockup", False))})
        entry.setdefault("by_locale", {})
        entry["colors"] = None
        if find_browser():
            try:
                entry["colors"] = image_colors(target)
            except Fail:
                entry["colors"] = None          # colours are a convenience: the capture is archived either way
        captures[args.id] = entry
    save_deck(slug, deck)
    warnings = []
    if info["alpha"]:
        warnings.append("the capture has an alpha channel: transparent pixels show the screen-off colour of the frame")
    if os_name in ("ios", "android") and not near["match"]:
        warnings.append("no known full-screen size matches: treated as content without a status bar (statusbar_state missing)")
    return {"ok": True, "id": args.id, "locale": args.locale, "file": target, "sha256": digest, "width": info["width"],
            "height": info["height"], "alpha": info["alpha"], "os": os_name, "fullscreen_match": near if near["match"] else None,
            "nearest_screen": near, "statusbar_state": entry.get("statusbar_state"), "mockup": entry.get("mockup"),
            "colors": None if args.locale else entry.get("colors"), "warnings": warnings,
            "hint": "LOOK at the capture, then set captures.%s.statusbar_state in deck.json: missing (no bar), empty (bar "
                    "area without glyphs), dirty (another clock than 9:41 or 9:30, carrier, weak signal, battery not full, "
                    "notification icons) or clean. A dirty bar: ask the user whether to mask it with the standard bar "
                    "(statusbar: mask) or keep it (statusbar: keep)" % args.id}, 0


def image_colors(path):
    """Colours of an image, measured in-page: strips, background, palette, accent, luminance, scheme."""
    found = run_analysis(COLORS_JS, path, "window.LK_COLORS=1;")
    if not found.get("ok") or not isinstance(found.get("colors"), dict):
        raise Fail("tool_failed", "no colours could be read from %s (%s)" % (path, found.get("message") or found.get("kind")))
    return found["colors"]


def cmd_probe(args):
    images = []
    for path in args.images:
        info = probe_image(path)
        info["nearest_screen"] = nearest_screen(info["width"], info["height"])
        info["fullscreen"] = info["nearest_screen"]["match"]
        images.append(info)
    result = {"ok": True, "images": images}
    if args.colors:
        if not find_browser():      # the header facts stand on their own; only the colour part needs the browser
            for info in images:
                info["colors"] = None
            result["colors_status"] = {"ok": False, "kind": "tool_missing", "message": "--colors needs a Chromium-family "
                                       "browser, and none was found",
                                       "hint": "the header facts above are complete; for colours ask the user for the brand "
                                               "colours or Read the capture, or point GM_BROWSER_BIN at a Chromium-family browser"}
        else:
            failures = []
            for info in images:
                try:
                    info["colors"] = image_colors(info["path"])
                except Fail as exc:
                    info["colors"] = None
                    failures.append({"path": info["path"], "kind": exc.kind, "message": exc.message})
            result["colors_status"] = {"ok": not failures, "failed": failures} if failures else {"ok": True}
            result["hint"] = ("colours are measured, not chosen: build theme.bg/fg from `background` and `scheme`, take "
                              "`accent` only when the user has no brand colour, then let compose measure the contrast")
    return result, 0


def cmd_text(args):
    slug = need_slug(args.slug)
    deck = require_deck(slug, files=False)
    sets = [find_set(deck, args.set)] if args.set else deck["sets"]
    targets = surfaces()["targets"]
    facts = deck.get("facts") or {}
    errors = warnings = 0
    out_sets, notes = [], []
    for one in sets:
        stores = sorted({targets[t]["store"] for t in one["targets"]})
        rules = sorted({rule for t in one["targets"] for rule in targets[t].get("content_rules") or []})
        slides = []
        for slide in one["slides"]:
            spec = copy_spec(slide)
            name = slide["layout"] + (" (caption left)" if spec is not LAYOUTS[slide["layout"]] else "")
            budget = {"headline_lines": spec["lines"], "headline_chars": spec["chars"], "sub_lines": spec["sub_lines"],
                      "sub_chars": spec["sub_chars"], "badge_chars": 24}
            locales = {}
            for locale, entry in (slide.get("copy") or {}).items():
                issues, rows = [], {}
                for key, max_lines, max_chars in (("headline", spec["lines"], spec["chars"]), ("sub", spec["sub_lines"], spec["sub_chars"])):
                    lines = entry.get(key) or []
                    if len(lines) > max_lines:
                        issues.append({"code": "too_many_lines", "level": "error", "text": " / ".join(lines),
                                       "message": "%s has %d lines, layout %s takes %d" % (key, len(lines), name, max_lines)})
                    rows[key] = []
                    for line in lines:
                        clean = " ".join(line.split())
                        rows[key].append({"text": line, "chars": len(clean), "upper": upper_for(clean, locale)})
                        if len(clean) > max_chars:
                            issues.append({"code": "chars_per_line", "level": "warning", "text": line,
                                           "message": "%d characters, budget %d: compose shrinks the type down to %d%% and then "
                                                      "fails" % (len(clean), max_chars, int(FIT_FLOOR * 100))})
                        issues.extend(check_line(line, locale, facts, stores, rules))
                if entry.get("badge"):
                    badge = " ".join(entry["badge"].split())
                    rows["badge"] = {"text": entry["badge"], "chars": len(badge), "upper": upper_for(badge, locale)}
                    if len(badge) > budget["badge_chars"]:
                        issues.append({"code": "badge_too_long", "level": "error", "text": entry["badge"],
                                       "message": "a badge is one short proof or data point: %d characters, budget %d"
                                                  % (len(badge), budget["badge_chars"])})
                    issues.extend(check_line(entry["badge"], locale, facts, stores, rules))
                if entry.get("emphasis"):
                    rows["emphasis"] = entry["emphasis"]
                errors += sum(1 for i in issues if i["level"] == "error")
                warnings += sum(1 for i in issues if i["level"] != "error")
                locales[locale] = dict(rows, issues=issues, ok=not any(i["level"] == "error" for i in issues))
            row = {"id": slide["id"], "layout": slide["layout"], "budget": budget, "locales": locales, "text_free": text_free(slide)}
            if slide.get("caption"):
                row["caption"] = slide["caption"]
            slides.append(row)
        bare = [slide["id"] for slide in slides if slide["text_free"]]
        if bare:
            notes.append("set %s renders no copy on %s: nothing to check there, and the page comes out the same in "
                         "every locale, so one file serves them all" % (one["id"], ", ".join(bare)))
        if "play" in stores:
            notes.append("set %s has a Play target: Google asks for taglines within 20%% of the image; compose measures it "
                         "as play_tagline_share" % one["id"])
        if any(targets[t]["store"] == "app-store" and targets[t].get("kind") == "card" for t in one["targets"]):
            notes.append("set %s has an App Store creative asset: text is optional and short, one language per file; it "
                         "must suit a 4+ rating whatever the app's own; key elements stay inside Apple's art safe area "
                         "(compose warns cutoff_zone)" % one["id"])
        out_sets.append({"id": one["id"], "stores": stores, "slides": slides})
    result = {"ok": errors == 0, "errors": errors, "warnings": warnings, "notes": notes,
              "facts": {"numbers": sorted(fact_numbers(facts)), "claims": facts.get("claims") or []}}
    if args.full:
        result["sets"] = out_sets
    else:       # only what needs a decision: slides and locales with findings, plus totals
        result["checked"] = {"sets": len(out_sets), "slides": sum(len(one["slides"]) for one in out_sets),
                             "copies": sum(len(slide["locales"]) for one in out_sets for slide in one["slides"]),
                             "text_free": sum(1 for one in out_sets for slide in one["slides"] if slide["text_free"])}
        result["findings"] = [dict({"set": one["id"], "slide": slide["id"], "layout": slide["layout"], "locale": locale,
                                    "issues": entry["issues"]}, **({"caption": slide["caption"]} if slide.get("caption") else {}))
                              for one in out_sets for slide in one["slides"] for locale, entry in slide["locales"].items() if entry["issues"]]
        result["hint"] = "budgets, character counts and the locale-correct upper-casing of every line: pass --full"
    if errors:
        result.update({"kind": "check_failed", "message": "%d copy problem%s: fix the copy in deck.json, then run text again"
                       % (errors, "" if errors == 1 else "s"),
                       "hint": "a number or claim that is not in facts comes out of the copy, or the user confirms it and it "
                               "goes into facts; never invent a fact"})
    return result, int(bool(errors))


def parse_screen(value):
    parts = [p for p in re.split(r"[,x ]+", value.strip()) if p]
    if len(parts) != 4 or any(not re.fullmatch(r"\d+", p) for p in parts):
        raise usage("--screen is x,y,w,h in pixels of the bezel image")
    x, y, w, h = (int(p) for p in parts)
    if w <= 0 or h <= 0:
        raise usage("--screen needs a positive width and height")
    return [x, y, w, h]


def cmd_assets(args):
    index_path = os.path.join(assets_dir(), "index.json")
    assets = asset_index()
    if args.action == "list":
        rows = [dict({"kind": kind, "name": name}, **entry) for kind, table in sorted(assets.items()) for name, entry in sorted(table.items())]
        return {"ok": True, "assets": rows, "index": index_path,
                "hint": "imported assets win over the drawn ones: a bezel by frame id, a bar by bar id or --os, a font by family name"}, 0
    if not args.kind or not args.name or not args.file:
        raise usage("assets import needs --kind, --name and --file")
    name = slugify(args.name)
    if not name:
        raise usage("--name %r has no letters or digits" % args.name)
    if not os.path.isfile(args.file):
        raise Fail("not_found", "cannot read %s" % args.file)
    ext = os.path.splitext(args.file)[1].lower()
    bar_note = None
    entry = {"os": args.os, "sha256": sha256_file(args.file), "imported_at": now(), "source": os.path.basename(args.file)}
    if args.screen_radius is not None and (args.kind != "bezel" or args.screen_radius < 0):
        raise usage("--screen-radius is a pixel radius of zero or more, for --kind bezel")
    if args.device and args.kind not in ("statusbar", "bottombar"):
        raise usage("--device is for --kind statusbar or bottombar")
    if args.opaque and args.kind != "bezel":
        raise usage("--opaque is for --kind bezel")
    if args.kind == "font":
        if ext not in FONT_EXT:
            raise usage("a font is a %s file" % ", ".join(FONT_EXT))
    elif args.kind in ("statusbar", "bottombar"):
        if ext != ".svg":
            raise usage("a %s is an SVG export: one bar, full screen width, single-colour fills" % args.kind)
        root = load_svg(args.file)
        entry["viewbox"] = [round(v, 3) for v in svg_viewbox(root, args.file)]
        entry["device"] = args.device or "phone"
        if args.kind == "statusbar" and entry["viewbox"][0] < 5 * entry["viewbox"][1]:
            bar_note = ("the artboard is %gx%g, less than 5 times as wide as it is tall: probably not a status bar (export the "
                        "whole bar: time left, icons right)" % tuple(entry["viewbox"]))
    else:
        info = probe_image(args.file)
        if info["format"] not in ("png", "webp"):
            raise usage("a bezel is a PNG or WebP with a transparent screen area")
        entry["size"] = [info["width"], info["height"]]
        entry["orientation"] = "landscape" if info["width"] > info["height"] else "portrait"
        entry["opaque"] = bool(args.opaque or not info["alpha"])     # no transparent hole: the capture is drawn above the bezel
        entry["screen_radius"] = args.screen_radius or 0
        if args.opaque and not args.screen:
            raise usage("--opaque needs --screen x,y,w,h: a filled screen cannot be detected")
        if args.screen:
            screen = parse_screen(args.screen)
            if screen[0] + screen[2] > info["width"] or screen[1] + screen[3] > info["height"]:
                raise usage("--screen reaches outside the %dx%d image" % (info["width"], info["height"]))
            entry.update({"screen": screen, "screen_from": "argument"})
        else:
            if not info["alpha"]:
                raise Fail("no_screen_hole", "%s has no alpha channel, so no transparent screen area can be found" % args.file,
                           hint="pass --screen x,y,w,h (pixels of the screen rectangle inside the bezel image)")
            found = run_analysis(HOLE_JS, args.file)
            if not found.get("ok"):
                raise Fail(found.get("kind") or "no_screen_hole", "no enclosed transparent screen area in %s (%s)"
                           % (args.file, found.get("reason") or found.get("message") or "unknown"),
                           hint="the screen is filled: pass --opaque --screen x,y,w,h --screen-radius <px> (pixels of the "
                                "screen rectangle inside the bezel image); without --opaque the filled screen would hide "
                                "the capture")
            entry.update({"screen": found["screen"], "screen_from": "detected", "hole_fill": found.get("fill")})
            if args.screen_radius is None and found.get("radius"):      # the capture is clipped to the hole's corners
                entry["screen_radius"] = found["radius"]
    folder = os.path.join(assets_dir(), args.kind)
    os.makedirs(folder, exist_ok=True)
    target = os.path.join(folder, name + ext)
    shutil.copyfile(args.file, target)
    entry["file"] = target
    assets.setdefault(args.kind, {})[name] = entry
    write_json_atomic(index_path, {"schema": SCHEMA, "assets": assets})
    result = {"ok": True, "kind": args.kind, "name": name, "asset": entry, "index": index_path,
              "hint": "user-owned files stay in this project: never copy them into the skill or a repository"}
    if bar_note:
        result["note"] = bar_note
    if entry.get("viewbox"):
        result["viewbox"] = entry["viewbox"]
    if entry.get("orientation") == "landscape" and not name.endswith("-landscape"):
        result["note"] = ("landscape bezel: it fits landscape captures only; portrait captures keep the drawn frame "
                          "(a bezel is never rotated). For both, import the portrait export as %s-portrait" % name)
    if entry.get("opaque"):
        result["note"] = ("opaque bezel: the capture is drawn above it inside --screen (corner radius %g px); the image's own "
                          "corners and background show as they are, so prefer a PNG that is transparent outside the device"
                          % entry["screen_radius"])
    return result, 0


def cmd_screen_quad(args):
    slug = need_slug(args.slug)
    deck = load_deck(slug)
    pid = slugify(args.plate)
    if not pid:
        raise usage("--plate %r has no letters or digits" % args.plate)
    plates = deck.setdefault("plates", {})
    plate = plates.get(pid)
    registered = False
    if args.file:
        info = probe_image(args.file)
        relative = "plates/%s%s" % (pid, CAPTURE_EXT[info["format"]])
        target = resolve_path(slug, relative)
        if os.path.abspath(args.file) != os.path.abspath(target):
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(args.file, target)
        plate = dict(plate or {})
        plate["file"] = relative
        registered = True
    if plate is None or not isinstance(plate, dict) or not plate.get("file"):
        raise Fail("not_found", "plate %r is not in deck.plates" % pid, hint="pass --file <path> to register it")
    if not safe_relative(plate["file"]):
        raise Fail("path_escape", "plates.%s.file climbs out of the project folder" % pid)
    path = resolve_path(slug, plate["file"])
    info = probe_image(path)
    key = args.key or plate.get("key") or "magenta"
    found = run_analysis(QUAD_JS, path, "window.LK_KEY=%s;" % json.dumps(key))
    if not found.get("ok"):
        kind = found.get("kind") or "no_quad"
        messages = {"no_key": "no %s key area was found in %s" % (key, path),
                    "no_quad": "the %s area in %s has no four clear sides" % (key, path)}
        raise Fail(kind if kind in messages else "tool_failed", messages.get(kind) or str(found.get("message")),
                   hint="generate the plate again: a flat pure %s screen (magenta #FF00FF, green #00FF00), fully lit, no "
                        "reflections, all four screen edges visible; or pass --key %s"
                        % (key, "green" if key == "magenta" else "magenta"), extra={"plate": pid, "analysis": found})
    shape = orient_screen(found["corners"], found.get("island"), args.orientation, info["width"], info["height"])
    result = {"ok": True, "plate": pid, "file": path, "width": info["width"], "height": info["height"], "key": key,
              "quad": shape["quad"], "island": found.get("island"), "top_guess": shape["top_guess"],
              "orientation": shape["orientation"], "aspect_estimate": shape["aspect_estimate"],
              "aspect_range": shape["aspect_range"],
              "side_ratio": shape["side_ratio"], "median_key_luma": found["median_key_luma"],
              "keyed_share": found["keyed_share"], "stray_key_share": found.get("stray_key_share", 0.0),
              "fit_points": found.get("fit_points"), "written": False, "warnings": []}
    if result["stray_key_share"] >= STRAY_KEY_WARN:
        result["warnings"].append("%.1f%% of the plate is key colour outside the screen (a reflection or a glow): the card "
                                  "turns it neutral grey; look at it on the render and re-roll with a matte surface if it "
                                  "shows" % (result["stray_key_share"] * 100))
    if shape["top_guess"]:
        result["warnings"].append("no island or punch-hole was found: the highest %sside was taken as the top; check the render"
                                  % ("" if args.orientation == "auto" else "%s " % ("short" if args.orientation == "portrait" else "long")))
    if not shape["focal_measured"] and max(abs(v - 1.0) for v in shape["side_ratio"].values()) > 0.1:
        result["warnings"].append("the perspective was corrected with an assumed lens: aspect_estimate may be off by a few percent")
    if min(found.get("fit_points") or [0]) < 8:
        result["warnings"].append("a side was fitted from few points: check the corners on the render")
    if args.write:
        plate.update({"key": key, "quad": shape["quad"], "median_key_luma": found["median_key_luma"],
                      "aspect_estimate": shape["aspect_estimate"], "aspect_range": shape["aspect_range"],
                      "orientation": shape["orientation"],
                      "island": found.get("island"), "top_guess": shape["top_guess"], "width": info["width"],
                      "height": info["height"], "sha256": sha256_file(path)})
        plates[pid] = plate
        save_deck(slug, deck)
        result["written"] = True
    elif registered:
        result["warnings"].append("the file was copied to plates/ but the deck was not changed: pass --write")
    return result, 0


def target_folders(deck):
    """(set id, target id) -> folder name. The first set that names a target owns <target>; later sets get <target>--<set>."""
    owner, table = {}, {}
    for one in deck["sets"]:
        for tid in one["targets"]:
            if tid not in owner:
                owner[tid] = one["id"]
            table[(one["id"], tid)] = tid if owner[tid] == one["id"] else "%s--%s" % (tid, one["id"])
    return table


def set_level_warnings(deck, sets):
    rows = []
    targets = surfaces()["targets"]
    for one in sets:
        if not any(targets[t].get("kind") == "screenshot" for t in one["targets"]):
            continue                      # a card series legitimately repeats one layout
        layouts = [s["layout"] for s in one["slides"]]
        for index in range(1, len(layouts)):
            if layouts[index] == layouts[index - 1]:
                rows.append({"set": one["id"], "code": "adjacent_layout_repeat",
                             "message": "slides %s and %s both use %s: vary the layout from slide to slide"
                                        % (one["slides"][index - 1]["id"], one["slides"][index]["id"], layouts[index])})
        early = [s["id"] for s in one["slides"][:3] if LAYOUTS[s["layout"]].get("span")]
        if early and any(targets[t].get("store") == "play" for t in one["targets"]):
            rows.append({"set": one["id"], "code": "span_early",
                         "message": "slides %s split one device across a seam among the first three images; Google asks to "
                                    "keep the interface prominent there: start the pair at slide 4 or later" % " and ".join(early)})
        if len(layouts) >= 5 and not any(s.get("invert") for s in one["slides"]):
            rows.append({"set": one["id"], "code": "no_inverted_slide",
                         "message": "a set of %d slides has no inverted slide: one or two break the rhythm" % len(layouts)})
    return rows


def render_job(binary, deck, slug, job, build_dir, keep):
    one, slide, index, target_id, locale = job["set"], job["slide"], job["index"], job["target"], job["locale"]
    fmt, scale = job["export"]["format"], job["export"]["scale"]
    name = "%02d-%s" % (index + 1, slide["id"])
    base = {"set": one["id"], "target": target_id, "locale": locale, "slide": slide["id"]}
    started = time.time()
    stem = "%s-%s-%s-%s" % (one["id"], job["folder"], locale, name)
    page_path = os.path.join(build_dir, stem + ".html")
    shot_path = os.path.join(build_dir, stem + ".png")
    jpg_path = os.path.join(build_dir, stem + ".jpg")
    try:
        target = surfaces()["targets"][target_id]
        factor = supersample(slide, target["width"] * target["height"] * scale * scale)
        page, ctx = build_page(deck, slug, one, slide, index, target_id, locale, scale=scale * factor, factor=factor)
        with open(page_path, "w", encoding="utf-8") as handle:
            handle.write(page)
        edges = ctx.get("edges")
        if edges and factor < 2:
            raise Fail("tool_failed", "slide %s draws a capture through a transform but was not supersampled: every such "
                       "layout must be listed in supersample()" % slide["id"])
        while True:
            metrics = parse_metrics(run_browser(binary, page_path, ctx["W"], ctx["H"], shot=shot_path, scale=scale * factor))
            if not metrics.get("ok"):
                raise Fail("tool_failed", "the page script failed: %s" % str(metrics.get("message"))[:300])
            measured = shrink_png(shot_path, factor, [[v * scale for v in e] for e in edges["segments"]] if edges else ()) if factor > 1 else []
            jagged, median = edge_gate(edges["kind"], measured) if edges else (False, None)
            wider = factor + 1
            if not jagged or wider > 4 or ctx["W"] * ctx["H"] * (scale * wider) ** 2 > SUPERSAMPLE_MAX_PIXELS:
                break
            factor = wider               # still stepped: one more pass at a higher factor before the gate speaks
            page, ctx = build_page(deck, slug, one, slide, index, target_id, locale, scale=scale * factor, factor=factor)
            with open(page_path, "w", encoding="utf-8") as handle:
                handle.write(page)
        ctx["edge_rms"], ctx["jagged"], ctx["supersample"] = median, jagged, factor
        hard, warns, summary = evaluate_gates(metrics, ctx)
        info = probe_image(shot_path)
        want = (ctx["W"] * scale, ctx["H"] * scale)
        if (info["width"], info["height"]) != want:
            hard.append({"code": "wrong_size", "message": "rendered %dx%d, the target is %dx%d%s" % (
                info["width"], info["height"], want[0], want[1], " (%dx)" % scale if scale != 1 else "")})
        if info["alpha"]:
            hard.append({"code": "alpha", "message": "the PNG carries an alpha channel; stores refuse it"})
        cap, cap_source = byte_budget(ctx["target"], fmt)
        if fmt == "png" and cap and info["bytes"] > cap:
            warns.append({"code": "bytes_over_cap", "message": "%d bytes, the cap of %s is %d: export it as JPEG (set export "
                          "{\"%s\": {\"format\": \"jpg\"}}) or simplify the background" % (info["bytes"], target_id, cap, target_id)})
        jpeg = None
        if fmt == "jpg" and not hard:
            encoded = encode_jpeg(shot_path, jpg_path, cap)
            if "over" in encoded:
                hard.append({"code": "jpeg_over_budget", "message": "even JPEG quality %d gives %d bytes, over the %d-byte budget "
                             "of %s (%s): calm the background or the plate area, or export PNG if the cap allows it"
                             % (JPEG_QUALITY_FLOOR, encoded["over"] or 0, cap, target_id, cap_source)})
            else:
                jpeg = {"quality": encoded["quality"], "max_bytes": cap, "budget": cap_source, "png_bytes": info["bytes"]}
                info = probe_image(jpg_path)
        if keep:
            write_json_atomic(os.path.join(build_dir, stem + ".metrics.json"), metrics)
        if hard:
            failed_dir = os.path.join(build_dir, "failed")
            os.makedirs(failed_dir, exist_ok=True)
            kept = os.path.join(failed_dir, stem + ".png")
            os.replace(shot_path, kept)
            return dict(base, ok=False, kind=hard[0]["code"], message=hard[0]["message"], gates=hard, warnings=warns,
                        render=kept, metrics=summary)
        out_dir = os.path.join(output_dir(slug), job["folder"], locale)
        os.makedirs(out_dir, exist_ok=True)
        ext = "." + fmt
        final = os.path.join(out_dir, name + ext)
        os.replace(jpg_path if jpeg else shot_path, final)
        replaced = replace_other_format(out_dir, name, ext)
        digest = sha256_file(final)
        proof = {"schema": SCHEMA, "script": VERSION, "file": name + ext, "sha256": digest, "width": info["width"],
                 "height": info["height"], "bytes": info["bytes"], "format": fmt, "scale": scale,
                 "set": one["id"], "target": target_id, "locale": locale,
                 "slide": slide["id"], "layout": ctx["layout"], "frame": ctx["frame"], "mode": ctx["mode"],
                 "deck_sha256": job["deck_sha256"],
                 "captures": [{"id": s["capture"], "file": s["path"], "sha256": s["sha256"], "mockup": s["mockup"],
                               "bezel": s["bezel_asset"]["source"] if s.get("bezel_asset") else None} for s in ctx["shots"]],
                 "mockup": ctx["mockup"],
                 "plate": {"id": ctx["plate_id"], "file": ctx["plate_file"], "sha256": sha256_file(ctx["plate_file"])} if ctx["plate_file"] else None,
                 "gates": {"hard": [], "warnings": warns}, "metrics": summary, "rendered_at": now()}
        if jpeg:
            proof["jpeg"] = jpeg
        if ctx.get("attributions"):
            proof["attributions"] = ctx["attributions"]       # credit that travels with the file (CC BY material in the frame)
        write_json_atomic(os.path.join(out_dir, name + ".proof.json"), proof)
        return dict(base, ok=True, path=final, proof=os.path.join(out_dir, name + ".proof.json"), width=info["width"],
                    height=info["height"], bytes=info["bytes"], format=fmt, scale=scale, jpeg=jpeg, sha256=digest,
                    layout=ctx["layout"], frame=ctx["frame"],
                    mockup=ctx["mockup"], warnings=warns, metrics=summary, seconds=round(time.time() - started, 2),
                    **({"replaced": replaced} if replaced else {}))
    except Fail as exc:
        return dict(base, ok=False, kind=exc.kind, message=exc.message, hint=exc.hint, gates=[], warnings=[])
    finally:
        if not keep:
            for leftover in (page_path, shot_path, jpg_path):
                if os.path.exists(leftover):
                    os.remove(leftover)


def replace_other_format(out_dir, name, ext):
    """A slide whose export switched between PNG and JPEG: the earlier file goes, but only when the proof that
    this render is about to overwrite names it. Left behind, it would have no proof and never be pruned.
    -> the removed path or None."""
    owner = None
    try:
        owner = read_json(os.path.join(out_dir, name + ".proof.json"), "proof").get("file")
    except (Fail, AttributeError):
        pass
    stale = os.path.join(out_dir, name + (".jpg" if ext == ".png" else ".png"))
    if owner == os.path.basename(stale) and os.path.isfile(stale):
        os.remove(stale)
        return stale
    return None


OUTPUT_NAME_RE = re.compile(r"\d{2}-[a-z0-9][a-z0-9-]*\.(?:png|jpg)")


def remove_output(path):
    """Delete one launchkit-made file: NN-<slide>.png or .jpg WITH its sibling proof. Anything else is not ours.
    A proof that names the other format's file belongs to that file: it stays."""
    proof = os.path.splitext(path)[0] + ".proof.json"
    if not OUTPUT_NAME_RE.fullmatch(os.path.basename(path)) or not os.path.isfile(path) or not os.path.isfile(proof):
        return False
    os.remove(path)
    try:
        owner = read_json(proof, "proof").get("file")
    except (Fail, AttributeError):
        owner = None
    sibling = os.path.join(os.path.dirname(proof), owner) if isinstance(owner, str) and owner != os.path.basename(path) else None
    if not (sibling and os.path.isfile(sibling)):
        os.remove(proof)
    return True


def prune_outputs(slug, deck, jobs, results, kept, full):
    """After a run without --slide: in every folder it rendered, drop files the run did not produce (renamed,
    removed or reordered slides, pages that now fail a gate). `full` (no filter at all) also drops manifest rows
    of sets, targets and locales the deck no longer has. -> (manifest rows to keep, pruned paths)."""
    produced = {os.path.abspath(r["path"]) for r in results if r.get("ok") or r.get("path")}
    spared = set()                  # a browser failure says nothing about the page: its earlier file stays,
    for job, row in zip(jobs, results):     # in either format, since the export may have switched since
        if row.get("kind") in ("tool_failed", "tool_missing"):
            stem = os.path.splitext(os.path.join(output_dir(slug), job["folder"], job["locale"], job["name"]))[0]
            spared.update(os.path.abspath(stem + ext) for ext in (".png", ".jpg"))
    pruned = []
    for folder, locale in sorted({(job["folder"], job["locale"]) for job in jobs}):
        out_dir = os.path.join(output_dir(slug), folder, locale)
        if not os.path.isdir(out_dir):
            continue
        for name in sorted(os.listdir(out_dir)):
            path = os.path.join(out_dir, name)
            if os.path.abspath(path) in produced or os.path.abspath(path) in spared:
                continue
            if remove_output(path):
                pruned.append(path)
    if full:
        alive = {(one["id"], tid, locale) for one in deck["sets"] for tid in one["targets"] for locale in deck["locales"]}
        for row in kept:
            if (row.get("set"), row.get("target"), row.get("locale")) not in alive and row.get("path"):
                remove_output(row["path"])
                pruned.append(row["path"])
        folders = target_folders(deck)
        living = {(folders[(set_id, tid)], locale) for set_id, tid, locale in alive}
        root = output_dir(slug)
        for folder in sorted(os.listdir(root)) if os.path.isdir(root) else []:
            for locale in sorted(os.listdir(os.path.join(root, folder))) if os.path.isdir(os.path.join(root, folder)) else []:
                out_dir = os.path.join(root, folder, locale)
                if (folder, locale) in living or not os.path.isdir(out_dir):
                    continue
                for name in sorted(os.listdir(out_dir)):       # a folder of a set, target or locale the deck dropped
                    if remove_output(os.path.join(out_dir, name)):
                        pruned.append(os.path.join(out_dir, name))
    gone = {os.path.abspath(path) for path in pruned}
    rows = [row for row in kept if os.path.abspath(row.get("path") or "") not in gone]
    return rows, sorted(set(pruned))


def cmd_compose(args):
    slug = need_slug(args.slug)
    deck = require_deck(slug)
    binary = need_browser("compose")
    if not 1 <= args.jobs <= 16:
        raise usage("--jobs must be between 1 and 16")
    sets = [find_set(deck, args.set)] if args.set else deck["sets"]
    folders = target_folders(deck)
    digest = deck_hash(slug)
    jobs = []
    for one in sets:
        for target_id in one["targets"]:
            if args.target and target_id != args.target:
                continue
            for locale in deck["locales"]:
                if args.locale and locale != args.locale:
                    continue
                for index, slide in enumerate(one["slides"]):
                    if args.slide and slide["id"] != args.slide:
                        continue
                    export = export_of(one, target_id)
                    jobs.append({"set": one, "slide": slide, "index": index, "target": target_id, "locale": locale,
                                 "folder": folders[(one["id"], target_id)], "deck_sha256": digest, "export": export,
                                 "name": "%02d-%s.%s" % (index + 1, slide["id"], export["format"])})
    if not jobs:
        raise Fail("nothing_selected", "no page matches --set/--target/--locale/--slide",
                   hint="sets: %s; locales: %s" % (", ".join(s["id"] for s in deck["sets"]), ", ".join(deck["locales"])))
    build_dir = os.path.join(project_dir(slug), "build")
    os.makedirs(build_dir, exist_ok=True)
    started = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(lambda job: render_job(binary, deck, slug, job, build_dir, args.keep_build), jobs))
    seconds = time.time() - started
    files = [r for r in results if r["ok"]]
    failed = [r for r in results if not r["ok"]]
    for row in files + failed:
        row.pop("ok", None)
    manifest_path = os.path.join(output_dir(slug), "manifest.json")
    previous = []
    if os.path.isfile(manifest_path):
        try:
            previous = read_json(manifest_path, "manifest").get("files") or []
        except Fail:
            previous = []
    # a browser failure says nothing about the page: its earlier row (and file) stay
    touched = {(r["set"], r["target"], r["locale"], r["slide"]) for r in results if r.get("kind") not in ("tool_failed", "tool_missing")}
    kept = [row for row in previous if isinstance(row, dict)
            and (row.get("set"), row.get("target"), row.get("locale"), row.get("slide")) not in touched]
    pruned = []
    if not args.slide:
        kept, pruned = prune_outputs(slug, deck, jobs, results, kept, full=not (args.set or args.target or args.locale))
    entries = kept + [{k: r[k] for k in ("path", "proof", "set", "target", "locale", "slide", "layout", "frame", "width", "height",
                                          "bytes", "format", "scale", "sha256", "mockup")} for r in files]
    for entry, row in zip(entries[len(kept):], files):
        entry["warnings"] = [w["code"] for w in row["warnings"]]
    entries.sort(key=lambda row: (row.get("target") or "", row.get("set") or "", row.get("locale") or "", row.get("path") or ""))
    write_json_atomic(manifest_path, {"schema": SCHEMA, "script": VERSION, "slug": slug, "deck_sha256": digest,
                                      "updated_at": now(), "files": entries})
    by_kind = {}
    for row in files:
        for warning in row["warnings"]:
            by_kind.setdefault(warning["code"], []).append(row["path"])
    details = os.path.join(build_dir, "compose-last.json")
    result = {"ok": not failed, "rendered": len(files), "failed_count": len(failed),
              "warnings_count": sum(len(row["warnings"]) for row in files), "seconds": round(seconds, 2),
              "pages_per_second": round(len(results) / seconds, 2) if seconds > 0 else None, "pruned": pruned,
              "failed": failed, "set_warnings": set_level_warnings(deck, sets), "files": files,
              "warnings_by_kind": by_kind, "mockups": sorted({r["path"] for r in files if r.get("mockup")}),
              "manifest": manifest_path, "details": details}
    replaced = sorted(r["replaced"] for r in files if r.get("replaced"))
    if replaced:
        result["replaced"] = replaced      # earlier PNG or JPEG of a slide whose export format changed, even under --slide
    if failed:
        result.update({"kind": failed[0]["kind"], "message": "%d of %d pages failed; the first: %s %s %s: %s" % (
            len(failed), len(results), failed[0]["target"], failed[0]["locale"], failed[0]["slide"], failed[0]["message"]),
            "hint": "a failed page is not delivered: fix the deck (copy, layout, colours, capture) and compose that slide again"})
    else:
        result["hint"] = "Read several outputs before delivering; then sheet for the small-size check and validate"
    write_json_atomic(details, result)            # the full answer, metrics and warning texts included, every time
    if not args.full:
        result = dict(result)
        result["files"] = [{"path": row["path"], "target": row["target"], "locale": row["locale"], "slide": row["slide"],
                            "warnings": [w["code"] for w in row["warnings"]]} for row in files]
        result["hint"] += "; metrics and warning texts per file are in `details` (or pass --full)"
    return result, int(bool(failed))


def cmd_layers(args):
    """One page as video layers: everything but the first capture, with a true alpha hole where that capture sits."""
    slug = need_slug(args.slug)
    deck = require_deck(slug)
    binary = need_browser("layers")
    ffmpeg = find_tool("ffmpeg")
    if not ffmpeg:
        raise Fail("tool_missing", "layers needs a local ffmpeg to build the alpha layer, and none was found",
                   hint="say that the recording could not be framed on this machine; the composed still of the slide is unaffected")
    one = find_set(deck, args.set)
    target_id = args.target or one["targets"][0]
    if target_id not in one["targets"]:
        raise usage("set %r has no target %r (it lists %s)" % (one["id"], target_id, ", ".join(one["targets"])))
    locale = args.locale or deck["locales"][0]
    if locale not in deck["locales"]:
        raise usage("the deck has no locale %r" % locale)
    found = [(i, sl) for i, sl in enumerate(one["slides"]) if sl["id"] == args.slide]
    if not found:
        raise usage("set %r has no slide %r" % (one["id"], args.slide))
    index, slide = found[0]
    if any(flow_tilts(slide)):
        raise Fail("layers_unsupported", "a tilted capture has no rectangular hole for a recording to play in",
                   hint="make a copy of the slide without `tilt` for the video layers; the still keeps its tilt")
    if slide["layout"] in ("card-hero-scene", "zoom", "device-span") or not slide.get("capture"):
        raise Fail("layers_unsupported", "layout %r cannot be cut into video layers" % slide["layout"],
                   hint="a recording needs an upright framed capture: use device-bottom, device-top, device-center, two-devices, "
                        "card-left-title, card-centered, card-browser or card-flow; a hero scene or a zoom stays a still with a local pan, "
                        "and so does a device across a seam")
    name = "%02d-%s" % (index + 1, slide["id"])
    build_dir = os.path.join(project_dir(slug), "build")
    out_dir = os.path.join(output_dir(slug), "video-layers", target_id, locale)
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    shots_png, ctx, metrics = {}, None, None
    try:
        for tone, colour in (("black", "#000000"), ("white", "#ffffff")):
            page, ctx = build_page(deck, slug, one, slide, index, target_id, locale, layer=colour)
            page_path = os.path.join(build_dir, "layers-%s-%s.html" % (name, tone))
            shots_png[tone] = os.path.join(build_dir, "layers-%s-%s.png" % (name, tone))
            with open(page_path, "w", encoding="utf-8") as handle:
                handle.write(page)
            found_metrics = parse_metrics(run_browser(binary, page_path, ctx["W"], ctx["H"], shot=shots_png[tone]))
            os.remove(page_path)
            if not found_metrics.get("ok"):
                raise Fail("tool_failed", "the page script failed: %s" % str(found_metrics.get("message"))[:300])
            metrics = metrics or found_metrics
        if ctx is None:
            raise Fail("tool_failed", "no layer page was built")
        hard, warns, _summary = evaluate_gates(metrics, ctx)
        if hard:
            raise Fail(hard[0]["code"], hard[0]["message"], hint="fix the deck as for compose, then run layers again", extra={"gates": hard})
        fg = os.path.join(out_dir, name + ".fg.png")
        done = subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", shots_png["black"], "-i", shots_png["white"],
                               "-filter_complex", "[1:v][0:v]blend=all_mode=difference,format=gray,negate[al];"
                                                  "[0:v][al]alphamerge,format=rgba,unpremultiply=inplace=1",
                               "-frames:v", "1", "-update", "1", fg], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120, check=False)
        if done.returncode != 0 or not png_complete(fg):
            raise Fail("tool_failed", "ffmpeg could not build the alpha layer: %s" % done.stderr.decode("utf-8", "replace").strip()[-300:])
    finally:
        for leftover in shots_png.values():
            if os.path.exists(leftover):
                os.remove(leftover)
    info = probe_image(fg)
    if (info["width"], info["height"]) != (ctx["W"], ctx["H"]) or not info["alpha"]:
        raise Fail("tool_failed", "the layer came back as %dx%d, alpha %s" % (info["width"], info["height"], info["alpha"]))
    shot = ctx["shots"][0]
    x0, y0 = int(math.floor(shot["x"] + shot["sx"])) - 1, int(math.floor(shot["y"] + shot["sy"] + shot["top"])) - 1
    wide, tall = int(math.ceil(shot["sw"])) + 2, int(math.ceil(shot["cap_h"])) + 2      # one pixel under the frame on every side,
    wide, tall = wide + wide % 2, tall + tall % 2                                        # even numbers for the video scaler
    W, H = ctx["W"], ctx["H"]
    recipe = ("color=black:s=%dx%d:r=30[c];[0:v]scale=%d:%d,fps=30[r];[c][r]overlay=%d:%d:shortest=1[u];"
              "[u][1:v]overlay=0:0:format=auto,format=yuv420p" % (W, H, wide, tall, x0, y0))
    record = {"schema": SCHEMA, "script": VERSION, "set": one["id"], "slide": slide["id"], "target": target_id, "locale": locale,
              "canvas": [W, H], "fg": name + ".fg.png", "fg_sha256": sha256_file(fg),
              "screen": {"x": x0, "y": y0, "w": wide, "h": tall, "capture": shot["capture"], "capture_size": [shot["cw"], shot["ch"]],
                         "aspect": round(shot["cw"] / float(shot["ch"]), 4)},
              "ffmpeg_filter": recipe, "inputs": ["0: the screen recording (trim with -ss and -t)", "1: the fg layer, looped (-loop 1 -framerate 30)"],
              "deck_sha256": deck_hash(slug), "mockup": ctx["mockup"], "warnings": warns, "rendered_at": now()}
    if ctx.get("attributions"):
        record["attributions"] = ctx["attributions"]
    record_path = os.path.join(out_dir, name + ".layers.json")
    write_json_atomic(record_path, record)
    return {"ok": True, "fg": fg, "layers": record_path, "canvas": [W, H], "screen": record["screen"], "ffmpeg_filter": recipe,
            "warnings": [w["code"] for w in warns],
            "next": "ffmpeg -ss <start> -t <seconds> -i <recording> -loop 1 -framerate 30 -i <fg> -filter_complex \"<ffmpeg_filter>\" "
                    "-t <seconds> -an -c:v libx264 -crf 18 -pix_fmt yuv420p <out.mp4>"}, 0


def sheet_sizes(target):
    if target.get("kind") == "square":
        return [240, 80, 40]
    return [int(target.get("sheet_width") or 320)]


def cmd_sheet(args):
    slug = need_slug(args.slug)
    deck = require_deck(slug, files=False)
    one = find_set(deck, args.set)
    binary = need_browser("sheet")
    locale = args.locale or deck["default_locale"]
    if locale not in deck["locales"]:
        raise usage("--locale %r is not in the deck" % locale)
    if args.target and args.target not in one["targets"]:
        raise usage("--target %r is not in set %s" % (args.target, one["id"]))
    manifest_path = os.path.join(output_dir(slug), "manifest.json")
    if not os.path.isfile(manifest_path):
        raise Fail("not_rendered", "no manifest at %s" % manifest_path, hint="run compose first")
    rows = [r for r in read_json(manifest_path, "manifest").get("files") or []
            if r.get("set") == one["id"] and r.get("locale") == locale and (not args.target or r.get("target") == args.target)]
    rows = [r for r in rows if os.path.isfile(r.get("path", ""))]
    if not rows:
        raise Fail("not_rendered", "set %s has no rendered files for locale %s" % (one["id"], locale), hint="run compose first")
    targets = surfaces()["targets"]
    width, pad, gap = SHEET_READ_LIMIT_PX, 28, 16
    inner = width - 2 * pad
    parts, y = [], pad
    order = [t for t in one["targets"] if any(r["target"] == t for r in rows)]
    for tid in order:
        target = targets[tid]
        items = sorted((r for r in rows if r["target"] == tid), key=lambda r: r["path"])
        uris = [data_uri(r["path"]) for r in items]
        parts.append('<div class="t" style="top:%dpx">%s &middot; %dx%d &middot; %s &middot; %d file%s</div>' % (
            y, esc(target["label"]), items[0]["width"], items[0]["height"], esc(locale), len(items), "" if len(items) == 1 else "s"))
        y += 34
        portrait = items[0]["height"] > items[0]["width"]
        large_h = 520 if portrait else None
        if portrait:                       # one row when the count allows it
            room = (inner - gap * (len(items) - 1)) / float(len(items))
            large_h = int(max(320, min(520, room * items[0]["height"] / float(items[0]["width"]))))
        large_w = min(640, inner)          # used only when large_h is not set
        if target.get("kind") == "square":
            large_w, large_h = 240, None
        x, row_h = pad, 0
        for number, (item, uri) in enumerate(zip(items, uris), 1):
            w = int(round(large_h * item["width"] / float(item["height"]))) if large_h else large_w
            h = large_h if large_h else int(round(large_w * item["height"] / float(item["width"])))
            if x + w > pad + inner and x > pad:
                x, y = pad, y + row_h + gap + 18
                row_h = 0
            parts.append('<div class="n" style="left:%dpx;top:%dpx">%02d</div><img alt="" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx" src="%s">'
                         % (x, y, number, x, y + 18, w, h, uri))
            x += w + gap
            row_h = max(row_h, h + 18)
        y += row_h + gap
        sizes = sheet_sizes(target)
        if not portrait and target.get("kind") == "screenshot":
            sizes = [int(round(sizes[0] * 1.6))]
        shown = list(zip(items, uris))[:3] if target.get("kind") == "screenshot" else list(zip(items, uris))
        half = (inner - gap) // 2
        tallest = 0
        for column, (tone, colour) in enumerate((("light", "#ffffff"), ("dark", "#0e1014"))):
            left = pad + column * (half + gap)
            cells, cx, line_y, line_h, strip_h = [], left + 14, 0, 0, 0
            for size in sizes:
                for item, uri in shown:
                    h = int(round(size * item["height"] / float(item["width"])))
                    if cx + size > left + half - 14 and cx > left + 14:
                        cx, line_y, line_h = left + 14, line_y + line_h + 12, 0
                    cells.append((cx, line_y, size, h, uri))
                    cx += size + 12
                    line_h = max(line_h, h)
                    strip_h = max(strip_h, line_y + h)
            tallest = max(tallest, strip_h)
            parts.append('<div class="s" style="left:%dpx;width:%dpx;top:%dpx;height:%dpx;background:%s"></div>' % (left, half, y, strip_h + 40, colour))
            parts.append('<div class="c %s" style="left:%dpx;top:%dpx">true size &middot; %s%s</div>' % (
                tone, left + 14, y + 6, " / ".join("%d px" % v for v in sizes),
                " &middot; first %d" % len(shown) if len(shown) < len(items) else ""))
            for cx2, ly, size, h, uri in cells:
                parts.append('<img alt="" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx" src="%s">' % (cx2, y + 26 + ly, size, h, uri))
        y += tallest + 40 + gap + 6
        y += 10
    height = int(y + pad - gap)
    page = ('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;width:%dpx;height:%dpx;background:#eceef2;'
            'font-family:%s;overflow:hidden}body{position:relative}img,div{position:absolute}img{display:block}'
            '.t{left:%dpx;font-size:17px;font-weight:700;color:#1b1f27;white-space:nowrap}.n{font-size:12px;font-weight:600;color:#697080}'
            '.s{border-radius:10px}.c{font-size:11px;font-weight:600;z-index:2}.c.light{color:#697080}'
            '.c.dark{color:#9aa3b5}</style></head><body>%s</body></html>') % (width, height, SYSTEM_STACK, pad, "".join(parts))
    suffix = "-%s" % args.target if args.target else ""
    out = args.out or os.path.join(output_dir(slug), "sheet-%s%s%s.png" % (one["id"], suffix, "" if locale == deck["default_locale"] else "-" + locale))
    work = tempfile.mkdtemp(prefix="launchkit-sheet-")
    try:
        page_path = os.path.join(work, "sheet.html")
        with open(page_path, "w", encoding="utf-8") as handle:
            handle.write(page)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        shot = os.path.join(work, "sheet.png")
        run_browser(binary, page_path, width, height, shot=shot, dom=False)
        os.replace(shot, out)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    info = probe_image(out)
    result = {"ok": True, "sheet": out, "width": info["width"], "height": info["height"], "set": one["id"], "locale": locale,
              "targets": order, "files": len(rows),
              "hint": "Read the sheet: judge the first slides at the small size on the light and the dark strip; a "
                      "headline that cannot be read there is too long or too small"}
    if info["height"] > SHEET_READ_LIMIT_PX:
        result["note"] = ("the sheet is taller than %d px, so a viewer may scale it down and the small previews stop being "
                          "true size: run sheet once per --target" % SHEET_READ_LIMIT_PX)
    return result, 0


def size_ok(target, width, height):
    """(ok, note) for a delivered file: the render size (or a multiple the target lists under `scales`), a listed
    accepted size, or inside the store's allowed range (sides, and a long-side cap or an exact `ratio` [w, h])."""
    for factor in target.get("scales") or []:
        if factor != 1 and (width, height) == (target["width"] * factor, target["height"] * factor):
            return True, None
    sizes = [tuple(s) for s in target.get("accepted_sizes") or []] or [(target["width"], target["height"])]
    if (target["width"], target["height"]) not in sizes:
        sizes.insert(0, (target["width"], target["height"]))
    if target.get("orientation_swappable"):
        sizes += [(h, w) for w, h in sizes]
    if (width, height) in sizes:
        return True, None if (width, height) in sizes[:1] + [(sizes[0][1], sizes[0][0])] else "an accepted alternate size"
    allowed = target.get("allowed")
    if allowed:
        low, high = min(width, height), max(width, height)
        ratio = allowed.get("ratio")
        shaped = width * ratio[1] == height * ratio[0] if ratio else high <= allowed["max_ratio"] * low + 0.5
        if low >= allowed["min_side"] and high <= allowed["max_side"] and shaped:
            return True, "inside the store's allowed range, not the project's render size"
    return False, None


def check_file(path, target, want_size=None):
    issues = []
    info = probe_image(path)
    if want_size:
        if [info["width"], info["height"]] != list(want_size):
            issues.append({"code": "wrong_size", "level": "error", "message": "%dx%d, the proof says %dx%d"
                           % (info["width"], info["height"], want_size[0], want_size[1])})
    ok, note = size_ok(target, info["width"], info["height"])
    if not ok:
        issues.append({"code": "wrong_size", "level": "error", "message": "%dx%d is not a size %s takes (%dx%d)"
                       % (info["width"], info["height"], target["label"], target["width"], target["height"])})
    elif note:
        issues.append({"code": "size_note", "level": "warning", "message": note})
    if info["alpha"]:
        issues.append({"code": "alpha", "level": "error", "message": "the file carries an alpha channel (PNG colour type %s)"
                       % info.get("color_type")})
    fmt = {"jpeg": "jpg"}.get(info["format"], info["format"])
    only = (target.get("size_formats") or {}).get("%dx%d" % (info["width"], info["height"]))
    if fmt not in target.get("formats", ["png", "jpg"]):
        issues.append({"code": "format", "level": "error", "message": "%s is not accepted (%s)" % (fmt, ", ".join(target["formats"]))})
    elif only and fmt not in only:
        issues.append({"code": "format", "level": "error", "message": "%s takes %dx%d as %s only, not %s"
                       % (target["label"], info["width"], info["height"], " or ".join(only), fmt)})
    named = {".png": "png", ".jpg": "jpg", ".jpeg": "jpg"}.get(os.path.splitext(path)[1].lower())
    if named and named != fmt:
        issues.append({"code": "format_mismatch", "level": "error", "message": "named %s but the file is %s" % (named, fmt)})
    if fmt == "jpg" and info.get("channels") != 3:
        issues.append({"code": "jpeg_channels", "level": "error", "message": "a JPEG with %s component%s; stores and cards want "
                       "three-component colour" % (info.get("channels"), "" if info.get("channels") == 1 else "s")})
    cap, source = byte_budget(target, fmt)
    if cap and info["bytes"] > cap:
        issues.append({"code": "too_large", "level": "error", "message": "%d bytes, the cap is %d (%s)" % (info["bytes"], cap, source)})
    proof_path = os.path.splitext(path)[0] + ".proof.json"
    proof = None
    if not os.path.isfile(proof_path):
        issues.append({"code": "proof_missing", "level": "error", "message": "no %s next to the file: it was not rendered by compose"
                       % os.path.basename(proof_path)})
    else:
        try:
            proof = read_json(proof_path, "proof")
        except Fail as exc:
            issues.append({"code": "proof_invalid", "level": "error", "message": exc.message})
        if proof is not None and proof.get("sha256") != sha256_file(path):
            issues.append({"code": "proof_mismatch", "level": "error", "message": "the file changed after it was rendered "
                           "(sha256 differs from the proof): compose it again"})
    return info, proof, issues


def check_group(names, target):
    """Count and order rules for the files of one folder."""
    issues = []
    numbers = []
    for name in names:
        found = re.match(r"(\d{2})-[a-z0-9][a-z0-9-]*\.(?:png|jpe?g)$", name)
        if not found:
            issues.append({"code": "name", "level": "error", "message": "%s is not NN-<slide id>.png or .jpg with a zero-padded number" % name})
        else:
            numbers.append(int(found.group(1)))
    if numbers and sorted(numbers) != list(range(1, len(numbers) + 1)):
        issues.append({"code": "order", "level": "error", "message": "numbers %s are not 01..%02d without gaps or repeats"
                       % (sorted(numbers), len(numbers))})
    low, high = target.get("min_count"), target.get("max_count")
    if low and len(names) < low:
        issues.append({"code": "too_few", "level": "error", "message": "%d file%s, %s needs at least %d"
                       % (len(names), "" if len(names) == 1 else "s", target["label"], low)})
    if high and len(names) > high:
        issues.append({"code": "too_many", "level": "error", "message": "%d files, %s takes at most %d" % (len(names), target["label"], high)})
    return issues


def cmd_validate(args):
    targets = surfaces()["targets"]
    groups = []
    if args.dir:
        if not args.target:
            raise usage("validate --dir needs --target <id>")
        if args.target not in targets:
            raise usage("unknown target %r (known: %s)" % (args.target, ", ".join(sorted(targets))))
        if not os.path.isdir(args.dir):
            raise Fail("not_found", "%s is not a folder" % args.dir)
        names = sorted(n for n in os.listdir(args.dir) if n.lower().endswith((".png", ".jpg", ".jpeg")) and not n.startswith("."))
        if not names:
            raise Fail("not_found", "no PNG or JPEG files in %s" % args.dir)
        groups.append({"target": args.target, "locale": None, "set": None, "dir": args.dir, "names": names, "sizes": {}})
        digest = None
    else:
        if not args.slug:
            raise usage("validate needs --slug <s>, or --dir <path> --target <id>")
        slug = need_slug(args.slug)
        manifest_path = os.path.join(output_dir(slug), "manifest.json")
        if not os.path.isfile(manifest_path):
            raise Fail("not_rendered", "no manifest at %s" % manifest_path, hint="run compose first")
        manifest = read_json(manifest_path, "manifest")
        digest = deck_hash(slug) if os.path.isfile(deck_path(slug)) else None
        table = {}
        for row in manifest.get("files") or []:
            if not isinstance(row, dict) or row.get("target") not in targets or not row.get("path"):
                continue
            key = (row["target"], row.get("locale"), row.get("set"), os.path.dirname(row["path"]))
            group = table.setdefault(key, {"target": row["target"], "locale": row.get("locale"), "set": row.get("set"),
                                           "dir": os.path.dirname(row["path"]), "names": [], "sizes": {}})
            group["names"].append(os.path.basename(row["path"]))
            group["sizes"][os.path.basename(row["path"])] = (row.get("width"), row.get("height"))
        groups = [table[key] for key in sorted(table, key=lambda k: tuple(str(v) for v in k))]
        if not groups:
            raise Fail("not_rendered", "the manifest lists no files", hint="run compose first")
    errors = warnings = checked = 0
    out = []
    for group in groups:
        target = targets[group["target"]]
        files = []
        for name in sorted(group["names"]):
            path = os.path.join(group["dir"], name)
            if not os.path.isfile(path):
                issues = [{"code": "file_missing", "level": "error", "message": "%s is listed in the manifest but is gone" % path}]
            else:
                _info, proof, issues = check_file(path, target, group["sizes"].get(name) if all(group["sizes"].get(name) or ()) else None)
                if proof and digest and proof.get("deck_sha256") != digest:
                    issues.append({"code": "deck_changed", "level": "warning", "message": "deck.json changed after this "
                                   "file was rendered: compose again before delivering"})
                if proof and proof.get("mockup"):
                    issues.append({"code": "mockup", "level": "warning", "message": "shows a screen flagged as mockup: say so on delivery"})
            checked += 1
            files.append({"file": name, "ok": not any(i["level"] == "error" for i in issues), "issues": issues})
        issues = check_group(sorted(group["names"]), target)
        every = issues + [i for f in files for i in f["issues"]]
        errors += sum(1 for i in every if i["level"] == "error")
        warnings += sum(1 for i in every if i["level"] != "error")
        out.append({"target": group["target"], "locale": group["locale"], "set": group["set"], "dir": group["dir"],
                    "count": len(group["names"]), "min_count": target.get("min_count"), "max_count": target.get("max_count"),
                    "ok": not any(i["level"] == "error" for i in every), "issues": issues, "files": files})
    result = {"ok": errors == 0, "checked": checked, "groups": out, "errors": errors, "warnings": warnings,
              "verified_on": surfaces()["verified_on"]}
    if errors:
        result.update({"kind": "check_failed", "message": "%d problem%s in %d file%s" % (
            errors, "" if errors == 1 else "s", checked, "" if checked == 1 else "s"),
            "hint": "compose the named slides again; never resize or re-save a delivered file by hand"})
    return result, int(bool(errors))


# ----------------------------------------------------------------------------------------------- main

class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise usage(message)


def build_parser():
    parser = Parser(prog="launchkit.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>", parser_class=Parser)
    sub.add_parser("tools", help="which renderer and converters exist").set_defaults(func=cmd_tools)
    p = sub.add_parser("specs", help="rows of surfaces.json")
    p.add_argument("--target", action="append")
    p.add_argument("--store", choices=("app-store", "play", "web", "product-hunt", "chrome-web-store", "ads", "email"))
    p.set_defaults(func=cmd_specs)
    p = sub.add_parser("init", help="folder tree and deck skeleton")
    p.add_argument("--slug", required=True)
    p.add_argument("--name")
    p.add_argument("--mode", choices=MODES, default="both")
    p.add_argument("--locale", action="append")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("capture", help="archive a raw capture")
    p.add_argument("action", choices=("add",))
    p.add_argument("--slug", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--os", choices=CAPTURE_OS)
    p.add_argument("--locale")
    p.add_argument("--mockup", action="store_true")
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=cmd_capture_add)
    p = sub.add_parser("probe", help="size, alpha and nearest device screen from the header")
    p.add_argument("images", nargs="+")
    p.add_argument("--colors", action="store_true")
    p.set_defaults(func=cmd_probe)
    p = sub.add_parser("text", help="copy budgets and gates")
    p.add_argument("--slug", required=True)
    p.add_argument("--set")
    p.add_argument("--full", action="store_true")
    p.set_defaults(func=cmd_text)
    p = sub.add_parser("assets", help="import or list user-owned bezels, bars and fonts")
    p.add_argument("action", choices=("import", "list"))
    p.add_argument("--kind", choices=ASSET_KINDS)
    p.add_argument("--name")
    p.add_argument("--file")
    p.add_argument("--os", choices=("ios", "android"))
    p.add_argument("--device", choices=("phone", "tablet"))
    p.add_argument("--screen")
    p.add_argument("--screen-radius", type=float)
    p.add_argument("--opaque", action="store_true")
    p.set_defaults(func=cmd_assets)
    p = sub.add_parser("screen-quad", help="find the chroma screen of a scene plate")
    p.add_argument("--slug", required=True)
    p.add_argument("--plate", required=True)
    p.add_argument("--file")
    p.add_argument("--key", choices=KEYS)
    p.add_argument("--orientation", choices=("auto", "portrait", "landscape"), default="auto")
    p.add_argument("--write", action="store_true")
    p.set_defaults(func=cmd_screen_quad)
    p = sub.add_parser("compose", help="render pages to exact-size PNG files")
    p.add_argument("--slug", required=True)
    p.add_argument("--set")
    p.add_argument("--target")
    p.add_argument("--locale")
    p.add_argument("--slide")
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--keep-build", action="store_true")
    p.add_argument("--full", action="store_true")
    p.set_defaults(func=cmd_compose)
    p = sub.add_parser("layers", help="one page as video layers: alpha hole where the capture sits")
    p.add_argument("--slug", required=True)
    p.add_argument("--set", required=True)
    p.add_argument("--slide", required=True)
    p.add_argument("--target")
    p.add_argument("--locale")
    p.set_defaults(func=cmd_layers)
    p = sub.add_parser("sheet", help="contact sheet with true small sizes")
    p.add_argument("--slug", required=True)
    p.add_argument("--set", required=True)
    p.add_argument("--target")
    p.add_argument("--locale")
    p.add_argument("--out")
    p.set_defaults(func=cmd_sheet)
    p = sub.add_parser("validate", help="size, alpha, bytes, counts, order, proofs")
    p.add_argument("--slug")
    p.add_argument("--dir")
    p.add_argument("--target")
    p.set_defaults(func=cmd_validate)
    return parser


def main(argv=None):
    try:
        parser = build_parser()
        args = parser.parse_args(argv)
        if not getattr(args, "func", None):
            raise usage("a command is required: tools, specs, init, capture, probe, text, assets, screen-quad, compose, "
                        "sheet, validate")
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
