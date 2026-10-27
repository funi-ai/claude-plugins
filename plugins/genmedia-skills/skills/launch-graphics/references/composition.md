# Composition: the deck, the commands, the gates

`deck.json` is the single source of a project: captures, copy per locale, theme, frames and layouts. `launchkit.py` turns it into HTML pages and a headless Chromium-family browser renders each page to the exact pixel size of its target. Nothing here costs money and a re-render is free. This page follows the script (version `lk1`); when they disagree the script wins. Layouts and slide fields: `templates.md`. Status bars and imported assets: `devices-and-statusbar.md`. Errors: `troubleshooting-launch-graphics.md`. `launchkit.py` abbreviates the call shown in SKILL.md; every command prints one JSON object, exit 0 ok, 1 failed, 2 usage.

## 1. Folders

```text
.genmedia/projects/<slug>/launch-graphics/
  deck.json                       source of truth (schema 1)
  captures/<id>.png               raw captures, archived untouched; captures/<locale>/<id>.png per locale
  plates/                         generated plates and decor (gm.py downloads here)
  build/                          compose-last.json (the full answer of the last compose run); pages and metrics with
                                  --keep-build; build/failed/<page>.png for every page a hard gate stopped
.genmedia/launch-graphics/assets/  user-imported bezels, bars, fonts + index.json (shared by all projects of this folder;
                                  the index keeps each source file's name, never its path)
genmedia-output/<slug>/launch-graphics/
  <target>/<locale>/NN-<slide id>.png  + NN-<slide id>.proof.json (.jpg for a JPEG export)
  <target>--<set id>/<locale>/...  a later set that names a target an earlier set already owns
  manifest.json · sheet-<set>[-<target>][-<locale>].png
```

`NN` is the slide's position in its set, so a slide rendered alone keeps its number. The first set that lists a target owns the plain `<target>` folder; every later set with the same target writes to `<target>--<set id>`. The locale suffix of a sheet appears only for a locale other than `default_locale`.

**Paths in the deck** are relative to the project folder (`captures/home.png`, `brand/icon.png`) or absolute. A `..` component fails with `path_escape`; a missing file with `file_missing`. Accepted: captures and plates `.png .jpg .jpeg .webp`; decor the same; `app.icon` and `app.logo` also `.svg` (screened for scripts and external references at compose time); fonts `.woff2 .woff .ttf .otf`.

## 2. `deck.json` reference

```json
{"schema": 1, "slug": "pocket", "mode": "both",
 "app": {"name": "Pocket Ledger", "icon": "brand/icon.png", "logo": null, "url": "pocketledger.example"},
 "theme": {"bg": "#0f172a", "bg_alt": "#1e293b", "fg": "#ffffff", "fg_alt": "#cbd5e1", "accent": "#3b82f6", "muted": "#64748b",
           "font": {"family": "system", "files": [], "weight_headline": 800, "weight_body": 500}},
 "locales": ["en", "tr"], "default_locale": "en", "rtl_locales": [],
 "facts": {"numbers": ["4.8"], "claims": ["Rated 4.8 by early users"]},
 "captures": {"home": {"file": "captures/home.png", "sha256": "…", "os": "ios", "width": 1206, "height": 2622, "alpha": false,
              "fullscreen_match": {"os": "ios", "size": [1206, 2622], "exact": true, "aspect_diff": 0.0, "match": true},
              "statusbar_state": "clean", "statusbar": "auto", "mockup": false,
              "colors": {"top_strip": "#f6f7fb", "bottom_strip": "#ffffff", "background": "#f7f8fb",
                         "palette": ["#f7f8fb", "#6642ff", "#d4d6db", "#3853ff", "#84868b", "#bbbbc3"],
                         "accent": "#3853ff", "luminance": 0.811, "scheme": "light"},
              "by_locale": {"tr": "captures/tr/home.png"}, "sha256_by_locale": {"tr": "…"}}},
 "plates": {"forest": {"file": "plates/forest.png", "key": "magenta", "quad": [[1107.9, 201.98], [1430.6, 144.53], [1574.35, 875.04], [1242.43, 937.44]],
            "median_key_luma": 247, "aspect_estimate": 0.446, "aspect_range": [0.44, 0.452], "orientation": "portrait"}},
 "decor": {"coin": {"file": "plates/coin.png"}},
 "sets": [{"id": "store", "mode": null, "targets": ["appstore-iphone-69", "play-phone"], "orientation": "portrait", "frame": "auto",
           "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160}, "slides": []}]}
```

| Field | Type, default | Written by | Notes |
|---|---|---|---|
| `schema`, `slug` | 1, the folder's slug | `init` | never edit; another schema fails with `deck_schema` |
| `mode` | `app-store`, `play`, `both`, `universal`; `init` default `both` | `init`, then you | a store target outside the mode's stores fails with `mode_target_mismatch`; a set may override it with its own `mode` |
| `app.name` | string, required | `init` (`--name`, else the slug text) | lockup text and `macos-window` title |
| `app.icon`, `app.logo`, `app.url` | path, path, string; all null | you | the logo replaces icon plus name in the lockup; `url` fills the browser frame's address pill. No icon file yet → `/genmedia-skills:brandkit` exports one from the approved mark (`app-icon/web/icon-512.png`, or the `app-icon.svg` itself) |
| `theme.bg`, `bg_alt`, `fg`, `fg_alt`, `accent` | five hex colours, all required | `init` (a dark placeholder), then you, from the user's brand and the captures' measured colours (below) | `bg`/`bg_alt` ground, `fg` headline, `fg_alt` sub, `accent` emphasis, badge tint, rule and blobs |
| `theme.badge_style` | `"pill"` (default) or `"text"` | you | `pill` sets the badge on a pill tinted 22 percent toward `accent`, text in `fg`. `text` sets it as a bare eyebrow: no pill, the readable accent (as for `emphasis`), wider tracking; its contrast is then measured against the pixels under it like the headline's. The badge is set as written: write an eyebrow in capitals in the copy |
| `theme.muted` | hex, optional; default `fg_alt` mixed 35 percent toward `bg` | `init` writes one; you may delete it | colours the lockup of a `text-only` slide, nothing else |
| `theme.font` | `family: "system"`, `files: []`, weights 800 and 500 (100 to 900) | you | a named family embeds `files` as data URIs: one file is used for every weight, several are matched by weight words in the file name (`bold`, `semibold`, `extrabold`…). No `files` → a font imported under the same name. Nothing is fetched from the network |
| `locales`, `default_locale`, `rtl_locales` | list, member, subset | `init` (`--locale`, default `en`), then you | `ar`, `he`, `fa`, `ur` render right-to-left even when not listed |
| `facts.numbers`, `facts.claims` | lists of strings | you, from the user's words only | the numbers gate is exact on the written form: `4.8` and `4,8` are two entries |
| `captures.<id>` | object | `capture add` | you edit only `statusbar_state` (`missing`, `empty`, `dirty`, `clean`), `statusbar` (`auto`, `keep`, `none`, `mask` — `mask` only after the user agreed to cover a non-standard bar, `devices-and-statusbar.md` section 4) and `mockup`. `colors` is measured by `capture add` when a browser exists, otherwise null; it is information for you and no page reads it. A file that no longer matches its `sha256` fails with `capture_changed` |
| `plates.<id>` | `file`, `key` (`magenta`, `green`, null), `quad` | you register a background plate as `{"file": …}`; `screen-quad --write` writes `key`, `quad`, `median_key_luma`, `aspect_estimate`, `aspect_range`, `orientation`, `island`, `top_guess`, size and `sha256` | the quad is top-left, top-right, bottom-right, bottom-left in plate pixels |
| `decor.<id>` | `{"file": …}` | you | referenced by a slide's `decor[].ref` |
| `sets[].id` | lower-case id, unique | you (`init` writes one set `store`) | names the sheet and the `--set` filter |
| `sets[].targets` | list of target ids from `launchkit.py specs` | `init` by mode, then you | all of one kind: store screenshots, or cards, or the square |
| `sets[].orientation` | `portrait` (default), `landscape` | you | landscape only when every target is `orientation_swappable` (the store screenshot targets) |
| `sets[].frame`, `sets[].background`, `sets[].slides` | `auto`; `{"kind": "solid"}`; required | you | `templates.md` |
| `sets[].bezel_shadow` | bool, default false; a slide's own `bezel_shadow` wins | you | a drop shadow under an IMPORTED bezel; drawn frames always carry their shadow (`devices-and-statusbar.md` section 6) |
| `sets[].export` | `{"<target id>": {"format": "png" or "jpg", "scale": 1 or 2}}`, both keys optional; default PNG at 1x | you, only when asked or when a file is too heavy | how one target of the set is delivered. `jpg`: the PNG render is encoded by the browser at the highest quality from 0.92 down to 0.60 that stays under the target's `max_bytes`, or under `surfaces.json` `jpeg.working_max_bytes` (5 000 000) where the platform states none. `scale: 2` only where the target lists `scales` (`og` 2400x1260, `x-card` 2400x1200): same layout and gates, twice the pixels. A `gradient` or `strip` ground that ships as `jpg` gets fine grain (up to 2 levels per channel) on the background only, so JPEG does not bring back the banding the browser dithers away in a PNG. Switching format replaces the old file |
| `sets[].lockup` | bool, default true; a slide's own `lockup` wins | you | `false` keeps the brand lockup off every page of the set. For `play-feature`, where Play shows the icon and the app name next to the graphic itself, and wherever the plate already carries the brand (`templates.md` section 2). A `card-lockup` slide needs its lockup and may size it with `{width, scrim, shadow}` (`templates.md` sections 1 and 2) |
| `sets[].compact` | bool, default false; a slide's own `compact` wins | you | with `lockup: false` on the set: `card-left-title`, `card-centered` and `card-flow` with `caption: "left"` give the lockup's empty room to the copy (`templates.md` section 2). For cards whose surface shows the brand already, such as an email under its own header |
| `sets[].device_top` | number from 0 to 0.8; a slide's own `device_top` wins | you | the top edge of the hung capture on `card-left-title` and `card-centered`, as a share of the card height (`templates.md` section 2) |

**Theme from measured colours.** Do not guess a palette from looking at a capture. `capture add` stores `colors` per capture, and `probe <image>… --colors` measures any other file (the user's site screenshot, a logo on its ground): `background` (most frequent colour), `top_strip` and `bottom_strip` (the edges a status strip would continue), `palette` (up to six by area, near-duplicates merged), `accent` (the most saturated colour on at least about 0.5 percent of the pixels, or null), `luminance` 0 to 1 and `scheme` (`light` or `dark`). Use them like this: the user's brand colours win when they gave any; otherwise `accent` is the candidate for `theme.accent`. Build `bg`, `bg_alt` and `fg` from `background` and `scheme`, so the slide belongs to the app: a shade or tint of the app's ground or of the brand colour, `fg` light on a dark ground and dark on a light one. Keep a visible step between `bg` and the capture's `background`: a frameless or light-bezelled screen on a ground of exactly its own colour melts into the slide. Then let `compose` measure: `contrast` and `metrics.accent_text` tell whether the choice holds. Say in the plan card which colours came from the capture. Without a browser `colors` is null (`colors_status.kind: "tool_missing"` on `probe`): ask for the brand colours, or Read the capture and say the values are estimates.

Edit the deck with the Write or Edit tool, never with a shell one-liner. Commands that write the deck (`capture add`, `screen-quad --write`) rewrite the whole file with two-space indentation: Read it again before the next Edit.

## 3. Command sequence

| Step | Command | The answer carries |
|---|---|---|
| 1 | `tools` | `browser`, `ffmpeg`, `sips` (`found`, `path`), `can` (what works here), `hint` |
| 2 | `specs [--store <s>] [--target <id>]…` | `verified_on`, `targets` rows, `unverified`, `attributions` (`origin`, `license`, `bars`, `changes`: third-party artwork that ships in `devices.json`, today the Android bars under CC BY 4.0) |
| 3 | `init --slug <s> --name "<App>" --mode <m> --locale en --locale tr` | `created` (false = an existing deck was left untouched), `deck`, `project`, `output`, `next` |
| 4 | `capture add --slug <s> --id <id> --file <path> [--os …] [--locale tr] [--mockup] [--replace]` | archived `file`, `sha256`, size, `alpha`, `os`, `fullscreen_match`, `nearest_screen`, the `statusbar_state` it assumed, `colors` (null without a browser, and for a `--locale` file), `warnings`, `hint` |
| 4b | optional: `probe <image>… [--colors]` | per image `format`, size, `alpha`, `bytes`, `aspect`, `nearest_screen`, `fullscreen`; with `--colors` also `colors` and one `colors_status` |
| 5 | you: Read each capture, set `statusbar_state`, write theme, facts, sets, slides and copy | - |
| 6 | `text --slug <s> [--set <id>] [--full]` | compact by default: `errors`, `warnings`, `notes`, `facts`, `checked` (`sets`, `slides`, `copies`, `text_free`) and `findings[]` (`set`, `slide`, `layout`, `locale`, `issues[]`), only for copies with an issue. `--full` adds `sets` with every line: the slide's `budget`, `chars` and the locale-correct `upper`. A text-free card slide has nothing to check: it is counted in `checked.text_free`, named in `notes`, carries `text_free: true` in `--full`, and never reports `copy_missing` |
| 7 | optional plates: `gm.py`, then `screen-quad --slug <s> --plate <id> --file <png> --write` | `hero-scenes.md` section 5 |
| 8 | `compose --slug <s> [--full]` | compact by default: `rendered`, `failed_count`, `warnings_count`, `seconds`, `pages_per_second`, `pruned[]`, `failed[]` in full (`kind`, `message`, `gates[]`, `warnings[]`, `render`, `metrics`), `set_warnings[]`, `files[]` (`path`, `target`, `locale`, `slide`, `warnings`: codes only), `warnings_by_kind` (`{code: [paths]}`), `mockups[]`, `manifest`, `details` |
| 9 | you: Read outputs at full size, slide 1 of every target and locale first | - |
| 10 | `sheet --slug <s> --set <id> [--target <id>] [--locale <l>]` | `sheet` path, size, `targets`; a `note` when the sheet is taller than 1568 px (run it per `--target`) |
| 11 | `validate --slug <s>` | `groups[]` per target, locale and set with `count`, `issues[]`, `files[]`; totals; exit 1 with `kind: "check_failed"` on any error |

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" compose --slug pocket --set store --target play-phone --locale tr --slide hero
```

**The details file.** Every `compose` run, failed ones included, writes its full answer to `build/compose-last.json` (the `details` path): per file also `proof`, `layout`, `frame`, size, `bytes`, `sha256`, `mockup`, `seconds`, the warnings with their messages and numbers, and `metrics`. `--full` prints that instead of the compact answer. Work from the compact answer; Read the details file when `warnings_by_kind` names something you need the numbers for (which ratio, which line, which `fit_scale`). It is overwritten by the next run.

`capture add` details: without `--os` the OS comes from an exact or 1 percent aspect match against the known full-screen sizes in `devices.json`; a landscape file without a match is taken as `web`; a portrait one needs `--os`. A full-screen match starts as `statusbar_state: "clean"`, anything else as `missing`: both are guesses until you have looked. `--locale` needs the default file first. A different file under an existing id fails with `exists` unless `--replace` is given.

## 4. Rendering again

- `--set`, `--target`, `--locale`, `--slide` combine; no match → `nothing_selected`. Slide ids may repeat across sets, so pair `--slide` with `--set`.
- The manifest is merged: rows of pages a run did not touch stay.
- **Pruning.** A run without `--slide` cleans every `<target>/<locale>` folder it rendered into: an `NN-*.png` or `NN-*.jpg` that has a proof next to it and that this run did not produce (a renamed, removed or reordered slide, a page that now fails a gate) is deleted with its proof and its manifest row. A run with no filter at all also removes the rows and files of sets, targets and locales the deck no longer has. The answer lists every deleted path in `pruned`: mention it when something the user may have wanted is on the list. A file without a proof is never touched, so the user's own files in those folders are safe. A page that failed with `tool_failed` or `tool_missing` keeps its earlier file and row: a browser failure says nothing about the page.
- `--slide` never prunes. A slide that fails a gate in such a run loses its manifest row while its older PNG stays on disk until the next run without `--slide`: do not deliver it.
- A format switch (`export` from PNG to JPEG or back) removes the slide's earlier file in any run, `--slide` included, but only when the proof being overwritten names it; the answer lists it under `replaced`. A file of the other format that the proof does not name is the user's and stays.
- After renaming, removing or reordering slides, run `compose` once without `--slide`; `validate` is clean afterwards.
- Every proof records the deck's hash. After any deck edit `validate` marks older files `deck_changed` (warning): finish with one full `compose` so every file carries the final hash.
- `--jobs` 1 to 16, default 4 parallel browser runs. Measured here on 2026-09-20: about 1.5 s per page, 52 pages in 29 s with 4 jobs. A page gets 60 s; `tool_failed` → run again, then with `--jobs 1`.
- `--keep-build` keeps each page's HTML and `.metrics.json` in `build/`. A hard-gate failure always leaves its render in `build/failed/`: Read it, it shows the defect.

## 5. The fit pass

The headline starts at the layout's size (`templates.md`; 9.2 percent of the width on a portrait device slide, 6 percent of the width unit on `card-left-title`), and shrinks in 2 percent steps until every authored line sits on one row inside the text box and the block fits the box height. `sub` and `badge` scale with it (`sub` 0.34 to 0.5 of the headline by layout, `badge` 0.27). At 72 percent it stops: `copy_too_long`, and the answer is a rewrite. `ja`, `zh`, `ko` start at 90 percent of the Latin size.

**Type floor.** A target may carry `min_text_px` in `surfaces.json`: 20 px on `og`, `x-card` and `github-social`, none elsewhere. There `sub` and `badge` never render below the floor, however far the headline shrinks; copy that needed smaller type therefore runs out of room and fails as `copy_too_long` instead of turning unreadable. Any copy that still ends below the floor warns `small_text`. The results are `metrics.fit_scale`, `metrics.headline_px` and `metrics.min_text_px` (the smallest rendered size among headline, `sub` and `badge`).

## 6. Hard gates (the page is not delivered; `compose` exits 1)

| Code | Fires when | Change |
|---|---|---|
| `copy_too_long` | the copy does not fit at 72 percent | shorter or fewer lines, drop `sub`, or a layout with a wider box; never edit the floor |
| `text_overlaps_device` | a text rectangle touches a device, the zoom card or the hero quad, grown by 2 percent of the short side (of the cutoff box on a target with `cutoff_zones`, which card layouts treat as their canvas) | shorten the copy; on a hero card use a plate whose phone sits further to the side |
| `contrast` below 3.0 | the 5th-percentile WCAG ratio of headline, `sub`, emphasis or a `text` badge against the real pixels under it; a pill badge against its pill | theme colours, `background.dim` on a plate, `invert`, or another plate |
| `aspect_mismatch` above 15 percent | capture aspect against the plate's `aspect_range` (or `aspect_estimate` on an older deck) | a new plate that names the aspect, or another capture; when the message names `--orientation`, run `screen-quad` again with it |
| `jagged_edge` | the median edge of a warped (hero scene) or tilted (`card-flow`) capture is more than 0.11 or 0.06 px off a smooth line after supersampling and one retry at a higher factor; measured at the edge pixels only, so photographs and busy screens inside the capture do not trigger it | the plate's own screen edge is stepped: a new PNG plate (`hero-scenes.md` section 6); never a hand-written page |
| `capture_changed` | the archived file differs from its `sha256` | `capture add … --replace` if the new file is meant |
| `wrong_size`, `alpha` | the PNG is not the target size (times `scale`), or carries alpha | run again; if it repeats, report it with `tools` output |
| `jpeg_over_budget` | a `jpg` export is over its byte budget even at quality 0.60 | a calmer background or a smaller plate area; PNG if the target states no cap |

## 7. Warnings (the page is delivered; say which ones remain)

| Code | Threshold | Change |
|---|---|---|
| `fit_scale` | headline shrunk below 0.9 | shorter lines |
| `chars_per_line` | a line over the layout budget | the same |
| `contrast` | 3.0 to 4.5 | as above; 4.5 is the comfortable floor |
| `gutter` | text closer to an edge than 60 px (`og`, `x-card`), 64 (`github-social`), 56 (`ph-gallery`, `email-card`), 50 (`play-feature`), else 4 percent of the short side | shorter lines |
| `device_share` | visible device height outside 0.50 to 0.85 of the canvas; store targets, not `zoom` | `bleed`, another layout, a capture of the right device class |
| `empty_band` | an empty full-width band over 0.25 of the height; store targets, not `text-only` | the same; typical for a phone slide on a tablet target |
| `play_tagline_share` | text blocks cover more than 0.20 of a `play-*` image | drop `sub`, shorten |
| `seam` | text or device within 3 percent of an inner seam of a `strip` set; the device of a `device-span` pair is exempt at its own seam, its text is not | another layout for that slide, or a `device-span` pair when the device should cross |
| `safe_crop` | `og`: text, lockup or icon outside the centred 1200x600 band | fewer lines |
| `aspect_mismatch` | 8 to 15 percent | judge the render; a new plate if the capture looks squeezed |
| `decor_overlaps_text` | front decor over a text rectangle | move the decor or set `z: "back"` |
| `small_text` | the smallest copy is below the target's `min_text_px` (20 px on `og`, `x-card`, `github-social`) | shorter copy, or a layout with larger type |
| `bytes_over_cap` | a PNG over the target's byte cap (`og`, `x-card` 5 000 000; `ph-gallery`, `ph-thumbnail` 3 000 000; `github-social`, `email-card` 1 000 000); `validate` fails it as `too_large` | `export` that target as `jpg` (section 2), or a calmer background |
| `statusbar_kept_dirty`, `statusbar_identifies_os`, `statusbar_os_mismatch` | `devices-and-statusbar.md` section 3 | a clean capture, or a capture per OS |
| `hero_scene_on_play` | `card-hero-scene` on a Play target | `card-left-title` or `card-minimal` there |
| `ad_safe_zone` | text, lockup or icon inside the strips a placement covers with its own interface (`safe_insets`: top 14, bottom 35, sides 6 percent on the 9:16 ad targets) | `device-bottom` or `device-center`; shorter copy; keep it only for feeds that show the image bare, and say so |
| `cutoff_zone` | text, lockup, icon or capture inside the zones a surface may crop (`safe_insets` on a target with `cutoff_zones`: about 15 percent per edge on `play-feature`, safe box x 154 to 876, y 73 to 422; Apple's art safe area on `appstore-header`, `appstore-search`, `appstore-universal`, `surfaces.md` section 1a) | card layouts already lay themselves out inside that box, so this means an explicit `bleed: true`, a plate whose screen sits at an edge, or a hand-set rectangle: drop the bleed, or move the element and leave the edges to the background |
| `text_share` | text rectangles cover more than the target's `text_share_max` (0.20 on `ad-feed-4x5`, `ad-square`, `ad-landscape`: Google App campaigns) | drop `sub`, shorten, or add a text-free variant for Google |
| `lockup_contrast` | `card-lockup`: the lockup's main colour (the logo's most common opaque colour, or `fg` for the name) below 3.0:1 against the ground behind it, scrim included | raise `scrim`, a calmer plate or plate crop, or the logo version made for that ground |
| `lockup_size` | `card-lockup`: the asked `width` did not fit the zone (88 x 80 percent of the card, of the cutoff box on `play-feature` and the App Store creative assets; a `width` the slide does not set already fits the box) | a smaller `width`; a tall or square mark reaches the height first |
| `note` | an imported bezel did not fit the capture, or a capture has the wrong device shape for its frame | read the message |

`set_warnings` (store sets only): `adjacent_layout_repeat`, `no_inverted_slide` (five or more slides, none inverted), `span_early` (a `device-span` pair among the first three slides of a set with a Play target).

`validate` issues: errors `wrong_size`, `alpha`, `format` (also a size the target takes in one format only: 5244x2950 is PNG only on the App Store creative assets), `format_mismatch` (a `.jpg` that holds a PNG or the reverse), `jpeg_channels` (a JPEG without three colour components), `too_large` (a JPEG on a target without a cap is held to `jpeg.working_max_bytes`), `proof_missing`, `proof_invalid`, `proof_mismatch`, `file_missing`, `name`, `order`, `too_few`, `too_many`; warnings `size_note`, `deck_changed`, `mockup`. `validate --dir <path> --target <id>` checks any folder the same way, without the manifest.

## 7b. Video layers (`layers`)

For a video ad or demo where a real screen recording plays inside the drawn frame (`/genmedia-skills:ads`, software route):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" layers --slug <slug> --set ads-video --slide flow --target ad-video-9x16 --locale tr
```

- The page is rendered twice with the slide's first capture hidden, its screen black and then white; ffmpeg turns the pair into `video-layers/<target>/<locale>/NN-<slide>.fg.png`: everything but the capture (ground, frame, drawn status bar, cut-out, copy) with a true alpha hole, antialiased corners included. Nothing is keyed by colour.
- `NN-<slide>.layers.json` carries `canvas`, `screen` (`x`, `y`, `w`, `h` of the hole: even numbers, one pixel under the frame on every side, plus the capture's size and aspect) and `ffmpeg_filter`, a ready filter graph: input 0 the recording, input 1 the looped layer. The assembly itself belongs to the video skill.
- The capture of that slide should be a frame of the recording, so page and recording share one geometry. The hard gates of `compose` apply; `compose` still renders the same slide as a still.
- Refused (`layers_unsupported`): `card-hero-scene`, `zoom`, `device-span` and `device-span-end` (the hole would run off the canvas), slides without a capture, a `card-flow` slide with `tilt` (a turned capture leaves no rectangular hole; copy the slide without `tilt` for the video). On `two-devices` and `card-flow` only the first capture becomes the hole. Needs a browser and a local ffmpeg (`tools` → `can.layers`); a run never prunes or lists these files in `manifest.json`.

## 8. `proof.json` and `manifest.json`

Proof, next to every PNG or JPEG: `schema`, `script` (`lk1`), `file`, `sha256`, `width`, `height`, `bytes`, `format`, `scale`, `jpeg` (`quality`, `max_bytes`, `budget`: `max_bytes` or `jpeg.working_max_bytes`, `png_bytes`) on a JPEG, `set`, `target`, `locale`, `slide`, `layout`, `frame`, `mode`, `deck_sha256`, `captures[]` (`id`, `file`, `sha256`, `mockup`, `bezel`: the source file name of the imported bezel it sits in, or null), `mockup`, `plate` (`id`, `file`, `sha256`) or null, `gates.warnings[]`, `metrics` (`fit_scale`, `headline_px`, `contrast_min`, `contrast_role`, `accent_text`, `min_text_px`, `device_share`, `empty_band`, `tagline_share`, `aspect_mismatch`, `statusbars[]` with `capture`, `state`, `action`, `strip`), `rendered_at`, and, on a page whose plan drew a shipped third-party bar, `attributions[]` (`bar`, `origin`, `license`, `changes`). That credit travels with the file: keep the proofs with the PNGs when you hand them on, and name the source once in the delivery note (`devices-and-statusbar.md` section 7). A file edited or re-saved after rendering fails `proof_mismatch`: never resize or convert a delivered file in place: a JPEG or a 2x file is an `export` in the deck, then `compose`.

Manifest: `schema`, `script`, `slug`, `deck_sha256`, `updated_at`, `files[]` with `path`, `proof`, `set`, `target`, `locale`, `slide`, `layout`, `frame`, `width`, `height`, `bytes`, `format`, `scale`, `sha256`, `mockup`, `warnings` (codes). `mockup: true` anywhere goes into the delivery note.

## 9. Without a browser

`compose`, `sheet`, `screen-quad` and the hole detection of a bezel import need a Chromium-family browser (Chrome, Chromium, Edge, Brave; searched on PATH and in the usual install folders). Without one they answer `kind: "tool_missing"`. `GM_BROWSER_BIN` names a binary to use; the value `none` switches the browser off. Current Chrome and Edge count their own tab strip and toolbar into the headless window, so the viewport is 84 to 87 px shorter than asked; `launchkit.py` measures that once per binary, opens the window taller and cuts the PNG back to the target size. `chrome-headless-shell` has no such inset.

1. **Still works:** `tools`, `specs`, `init`, `capture add` (it archives the capture and leaves `colors` null), `probe` (with `--colors` the header facts still come back, `colors` is null and `colors_status` says `tool_missing`), `text`, `assets list`, `assets import` (fonts, bars, and bezels with `--screen`), `validate`.
2. **Deliver:** the finished `deck.json`, the clean `text` result, the capture triage and capture list, the plan. There is no second renderer: no page is written, nothing is drawn with ffmpeg, and the real interface is never handed to an image model to fake a render.
3. **Say it plainly:** "Nothing was rendered: this machine has no Chrome, Chromium, Edge or Brave. The deck is complete and checked; install one of them, or point `GM_BROWSER_BIN` at one, and the set renders from this deck as it is." Do not call a deck a finished set.
