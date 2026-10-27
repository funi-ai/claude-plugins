# Troubleshooting launch graphics

Symptom → cause → what to change. Every `kind` and issue `code` that `launchkit.py` (`lk1`) can emit is listed once. Gate thresholds are in `composition.md` sections 6 and 7; generation and platform errors of `gm.py` are in `cli-contract.md` and `platform.md`. `launchkit.py` abbreviates the call shown in SKILL.md.

How to read a failure: exit 2 is a usage error (`kind: "usage"`, the message names the flag); exit 1 carries `kind`, `message`, usually a `hint`. Deck failures add `problems[]` (up to 40 rows with `where`, `code`, `message`): fix all of them in one edit, not one per run. `compose` puts per-page failures in `failed[]` with `gates[]` and the path of the failed `render`; its default answer names warnings by code only (`warnings_by_kind`), and the messages and numbers are in the `details` file (`build/compose-last.json`) or come with `--full`. `text` lists only copies with issues (`findings[]`); `--full` shows every line.

## 1. Wrong rather than failed

| What happened | Cause | Do |
|---|---|---|
| `init` answers `created: false` | a deck already exists and was left untouched | Read it and continue from it; never start a second slug to get around it |
| `capture add` said `statusbar_state: "clean"` and the slide shows a carrier name or 14 percent battery | the state is a guess from the pixel size | Read the capture, set the state (`devices-and-statusbar.md` section 4), compose the slide again |
| `text` is `ok` and `compose` still shrinks or fails the headline | character budgets are estimates; the fit pass measures the real glyphs | shorten the longest line; wide letters and capitals cost more than the count says |
| `compose` is `ok` with warnings and the set was delivered unseen | warnings do not stop a run, and the compact answer shows only their codes | Read `warnings_by_kind`, open the `details` file for the numbers, Read slide 1 of every target and locale, then the `sheet`; name remaining warnings in the delivery |
| the theme was picked by eye and the device melts into the ground, or the accent is off-brand | colours were guessed | take them from `captures.<id>.colors` or `probe --colors` (`composition.md` section 2); brand colours from the user win |
| `validate` reports `deck_changed` on files that look fine | the deck was edited after they were rendered | one full `compose`, then `validate` again |
| `validate` reports `order`, or an old file is still in the folder, after a slide was renamed, removed or moved | the last runs all used `--slide`, which never prunes | one `compose` without `--slide` (no filter at all when a set, target or locale left the deck): stale `NN-*.png` files with a proof go, with their manifest rows, and are listed in `pruned` |
| a file the user expected is gone after `compose` | it was a launchkit render (it had a proof) that the run no longer produced, so it was pruned; `pruned[]` names it | it can be rendered again from the deck; files without a proof are never deleted. Keep hand-made files out of the output folders or without a `.proof.json` sibling |
| a slide fails a gate under `--slide` and its old PNG is still there | `--slide` never prunes; the manifest row is already gone | do not deliver it; fix the slide, or run once without `--slide` |
| a single slide composed into an empty output folder fails `validate` with `order` or `too_few` | `validate` judges the folder as a set | expected until the whole set exists |
| the small previews on the sheet look soft | the sheet is taller than 1568 px and the viewer scaled it (`note` in the answer) | `sheet` once per `--target` |
| a `both` deck delivers the Play slides with iOS screens | one capture id was used for both stores | capture map on the slide: `{"ios": "home", "android": "home-android"}` |
| the same PNG is "fixed" in an image editor | breaks `proof_mismatch` and the archive rule | change the deck and compose; a JPEG or 2x file is an `export` entry in the deck, never an edit of the delivered file |

## 2. Deck errors

| `kind` or `code` | Cause | Action |
|---|---|---|
| `no_deck` | no `deck.json` for the slug | `init --slug <s>`; check the working directory is the user's project root |
| `invalid_json` | the deck, the asset index or the manifest is not one JSON object | re-Read the file, repair the syntax (trailing comma, smart quotes) with Edit |
| `deck_schema` | `schema` is not 1 | never edit `schema`; a deck from a newer skill version needs that version |
| `deck_invalid` | a field has the wrong type or value: `where` names it (mode, theme colour, locale code, capture `os`, `statusbar_state`, background kind, `zoom` box, decor numbers, an id with capitals or spaces, an unknown layout, a capture a layout does not take) | fix every row of `problems[]`; ids are lower-case letters, digits and hyphens |
| `path_escape` | a deck path contains `..` | paths are relative to the project folder or absolute |
| `file_missing` | a capture, plate, decor, icon, logo or font file is not there | add the capture with `capture add`; put brand files inside the project folder |
| `mode_target_mismatch` | a store target outside the mode's stores (`play-phone` in an `app-store` deck) | change `mode`, or give the set its own `mode` |
| `layout_target_mismatch` | a store layout in a card set, or the reverse, or mixed target kinds in one set | one set per kind: screenshots, cards, the square |
| `universal_frame` | an iOS or Android frame named in a universal store set | `neutral-phone`, `none` or `auto` |
| `plate_without_quad` | `card-hero-scene` names a plate that has no `quad` | `screen-quad --slug <s> --plate <id> --write` |
| `not_found` | the set named by `--set`, a plate id, a folder or a file does not exist | the message lists what exists |
| `nothing_selected` | `--set`, `--target`, `--locale`, `--slide` match no page | the hint lists sets and locales; the target must be in that set |
| `not_rendered` | `sheet` or `validate` before any `compose`, or a set and locale without files | compose first |

## 3. Copy errors

`copy_missing`, `copy_unused` and `emphasis_not_in_headline` are deck errors and stop `text`, `compose` and `sheet`; the rest are `issues[]` of `launchkit.py text` (errors make it exit 1 with `kind: "check_failed"`).

| Code | Level | Cause → action |
|---|---|---|
| `copy_missing` | error | a deck locale has no entry on a slide, or `copy` is absent → write that locale's lines (`localization.md`), never copy the English ones in |
| `copy_unused` | error | a slide carries a locale that `locales` does not list → add the locale to the deck or delete the stray entry |
| `emphasis_not_in_headline` | error | `emphasis` is not a verbatim part of one headline line, case included, or it spans a line break → pick a phrase inside one line |
| `too_many_lines` | error | more lines than the layout takes → merge lines, drop `sub` lines, or a layout with more lines (`templates.md` section 2) |
| `badge_too_long` | error | over 24 characters → one data point, not a sentence |
| `number_not_in_facts` | error | a digit string that is not in `facts.numbers` exactly as written (`4,8` is not `4.8`) → remove it, or the user confirms it and it goes into facts in that spelling |
| `claim_not_in_facts` | error | a reputation word (award, editor, featured, trusted, rated, stars, million, their Turkish forms…) without a `facts.claims` entry containing it → remove it, or the user supplies the claim in their words |
| `banned_store_word` | error with a `play-*` target in the set, else warning | `#1`, `best`, `top`, `free`, `download now`, `install now`, `play now`, `try now` → rephrase; "top" as a position ("on top") is caught too |
| `promo_word` | warning | new, sale, discount, "% off", limited time and kin, also in Turkish, German, French, Spanish, Portuguese → rephrase on store targets |
| `price_in_copy` | warning; error on an App Store creative asset | a currency amount on a store target → remove (`store-policy.md` section 6) |
| `discount_in_copy`, `url_in_copy`, `copyright_symbol`, `apple_badge`, `other_platform` | error, only in a set with an App Store creative asset (`content_rules`) | discount talk, a web address, ©, Editors' Choice, App of the Day and kin, Android, Google Play and other stores → remove; Apple asks these assets to carry none of them, a true award included (`store-policy.md` section 2a) |
| `chars_per_line` | warning | a line over the character budget → shorten before composing |
| `symbol` | warning | emoji or symbols render in the machine's emoji font → remove |

The word lists know English and some Turkish, German and Romance words. Apply the same rules by reading in every other language.

## 4. Capture and asset errors

| `kind` | Cause | Action |
|---|---|---|
| `convert_first` | HEIC, HEIF, AVIF, TIFF, BMP, GIF, PSD or PDF | convert a copy, keep the original: `sips -s format png <in> --out <out.png>` (macOS) or `ffmpeg -i <in> <out.png>`; `tools` says which exists. Neither → ask the user for a PNG export |
| `unsupported` | not an image this tool can measure (a renamed file, a truncated download) | ask for the original file |
| `usage`: "--os is required" | a portrait capture that matches no known full-screen size | pass `--os ios` or `--os android` after looking at it |
| `exists` | another file already archived under that id | a new `--id`, or `--replace` when the new file supersedes the old one |
| `not_found` on `--locale` | the capture has no default file yet | add it without `--locale` first |
| `colors: null` after `capture add`, or `colors_status.kind: "tool_missing"` / `failed[]` on `probe --colors` | no browser, or the image could not be read in the page; the capture is archived either way | ask for the brand colours, or Read the capture and call the values estimates; with a browser back, `probe --colors <file>` |
| `capture_changed` | the archived file no longer matches its `sha256` | captures are never edited in place; `capture add … --replace` with the intended file |
| `no_screen_hole` | a bezel without alpha and without `--screen`, or an alpha file without an enclosed transparent area of at least 15 percent | pass `--screen x,y,w,h` (and `--screen-radius`): a file without alpha is then stored as an opaque bezel with the capture drawn above it; a filled screen inside an alpha PNG needs `--opaque` as well (`devices-and-statusbar.md` section 6) |
| `usage`: "--device is for…", "--opaque needs --screen", "--screen-radius is…" | a bezel flag on a bar or the reverse | `--device` belongs to bars; `--screen`, `--screen-radius`, `--opaque` to bezels |
| `svg_unsafe`, `svg_invalid`, `svg_too_large` | a bar, icon or logo SVG with scripts, images, `use`, external references or entities; broken XML, no `viewBox` and no numeric size; over 8 MB | export again as plain outlined shapes (`devices-and-statusbar.md` section 6); `reasons[]` names what was found |

## 5. Plate and quad errors

| `kind` or field | Cause | Action |
|---|---|---|
| `no_key` | no connected key-coloured area of at least 0.4 percent of the plate | the model ignored the screen sentence, or the key is the other colour: try `--key green` once, else a new plate with the SCREEN block verbatim (`hero-scenes.md` section 3) |
| `no_quad` | the key area has no four clear sides (a hand covers an edge, the phone leaves the frame), or a hand-written quad is degenerate | a new plate with the whole phone visible; a hand-edited `quad` is top-left, top-right, bottom-right, bottom-left |
| `top_guess: true` | no island or punch-hole found inside the screen; the highest side was taken as the top | Read the composed card: a phone upside down → a new plate with the cut-out sentence; a capture turned by 90 degrees → `screen-quad --orientation portrait` or `landscape` |
| warning "a side was fitted from few points" | a short or occluded screen edge | Read the corners on the render at full size |
| `aspect_mismatch` | the plate's screen is wider or narrower than the capture (warning from 8 percent, failure above 15) | a new plate that names the capture's aspect; or the capture of a device with a closer aspect |
| plate generation failed or was blocked | `gm.py` error | `platform.md`; never resend a content-policy rejection unchanged |

## 6. Render errors

| `kind` | Cause | Action |
|---|---|---|
| `tool_missing` | no Chromium-family browser, or `GM_BROWSER_BIN=none` | `composition.md` section 9; say that nothing was rendered |
| `tool_failed`: "gave no complete screenshot and DOM within 60 s" | the browser hung or the machine is loaded | run again; then `--jobs 1`; then name the binary with `GM_BROWSER_BIN`. The page's earlier file and manifest row are kept and never pruned: a browser failure says nothing about the page |
| `tool_failed`: "cannot start" | `GM_BROWSER_BIN` points at something that is not a browser binary | fix or unset it |
| `tool_failed`: "the page script did not report" or "the page script failed" | the browser stopped before the page script ran, or an image failed to decode | run again with `--keep-build`; Read the message; a capture that no viewer opens is a bad file → `capture add --replace` |
| `copy_too_long`, `text_overlaps_device`, `contrast`, `aspect_mismatch`, `wrong_size`, `alpha`, `jpeg_over_budget` | hard gates | `composition.md` section 6; Read `build/failed/<page>.png` first |
| `copy_too_long` on `og` or `x-card` for copy that fits on `ph-gallery` | `sub` and `badge` cannot shrink below 20 px there, so the block runs out of height sooner | fewer `sub` lines, a shorter badge, or a layout with a taller text box |
| `internal` | an input the script did not expect | report the command and the message; check the file the command named |

## 7. Validation errors (`validate`, `kind: "check_failed"`)

| Code | Cause → action |
|---|---|
| `wrong_size` | not the target's size, an accepted alternate or inside Play's allowed range or Apple's 3:2 search results range → compose again; never resize by hand |
| `alpha`, `format`, `format_mismatch`, `jpeg_channels` | a file with alpha, not PNG or JPEG, content that does not match its extension, or a JPEG without three colour components → it did not come from `compose`; compose again. `format` also names a size that takes one format only: 5244x2950 on an App Store creative asset is PNG only, so `export` it as PNG |
| `too_large` | over the byte cap (`og`, `x-card` 5 MB, `ph-gallery` and `ph-thumbnail` 3 000 000 bytes, `github-social` and `email-card` 1 000 000 bytes; a JPEG on a target without one, the 5 MB working limit) → `export` the target as `jpg` and compose, or a calmer background, smaller plate area |
| `proof_missing`, `proof_invalid`, `proof_mismatch` | no proof, a broken one, or the file changed after rendering → compose that slide again |
| `file_missing` | listed in the manifest, gone from disk → compose again |
| `name`, `order` | not `NN-<slide id>.png`, or numbers with gaps or repeats → a partial run, or stale files after `--slide` runs: one `compose` without `--slide` prunes them (section 1) |
| `too_few`, `too_many` | outside the platform's count (`play-phone` 2 to 8, `play-tablet`, `play-tablet-7`, `play-tablet-10` 4 to 8, `appstore-iphone-*`, `appstore-ipad-13`, `appstore-mac` 1 to 10, the App Store creative assets and `email-card` at least 1, `cws-screenshot` 1 to 5, `ph-gallery` at least 2, `play-feature`, `ph-thumbnail`, `github-social` and the `cws-promo-*` tiles exactly 1) → add or drop slides |
| `size_note`, `deck_changed`, `mockup` | warnings: an alternate size; the deck changed since the render; a screen flagged as mockup → say the last one in the delivery |

## 8. Visual defects

| Symptom | Cause | Fix |
|---|---|---|
| A magenta or green rim around the hero screen | the plate was JPEG, the screen has glare or a gradient, or the key bleeds into a reflective bezel | a new plate as PNG with "perfectly flat, uniform" screen wording; never paint over the render |
| The capture looks squeezed or stretched in the scene | `aspect_mismatch` between 8 and 15 percent was accepted | a new plate naming the aspect ("about 9 by 19.5"), or another capture |
| Small interface text in the scene is mush | the phone is small or strongly tilted (`side_ratio` far from 1) | a bolder capture, a closer phone, or `card-left-title` |
| Headline over the phone on a hero card | the phone sits near the middle, so the text box between gutter and phone is narrow: `text_overlaps_device` or `copy_too_long` | a plate with the phone in the outer third on the side away from the text; shorter lines; never move the text by hand |
| Text over a busy plate | `contrast` warns or fails | `background.dim` up to 0.9, a plate with a calm zone under the text box, or a gradient. `invert` does nothing on plate grounds |
| The hand or the bezel on a hero card is darker on the text side | the scrim eases out over 40 percent of the width past the text block and runs under the device; the screen itself is never shaded | expected. A lower `background.dim` lightens it; `contrast` says how low it can go |
| A vertical seam in the sky next to the phone on a hero card | a page composed before 2026-09-25: the scrim ended at the device's near edge, a short ramp when the phone stood close to the text | compose it again |
| Jagged or light-rimmed edges on turned cards | the cards were turned in a page written by hand: headless Chromium clips a rotated element with `overflow: hidden` and `border-radius` without anti-aliasing, and the card's own ground shows through the edge | `card-flow` with `tilt`, which renders at twice the pixels, shrinks back and leaves the card's ground transparent; never hand-write a page for a composition `launchkit.py` can draw |
| Stair-stepped edges or lines on a hero scene's screen | a `matrix3d`-warped capture drawn at 1x: headless Chromium does not anti-alias it | `compose` renders hero pages at 3x (2x on canvases over 5.5 MP, the App Store creative assets among them) and gates `jagged_edge`; a failed page is never delivered. If it still fails, the plate's own screen edge is stepped: a new PNG plate (`hero-scenes.md` section 6). On `appstore-universal` and `appstore-search` a plate the browser has to enlarge steps too: upscale it to the canvas first (`plates-and-prompts.md` section 4) |
| A grey stain under a tablet or laptop | the plate mirrored its magenta screen on a glossy surface; `compose` neutralises key colour away from the screen | `screen-quad` warned `stray_key_share`: re-roll with "matte surface, no reflection of the screen" |
| Banding on a dark gradient | not in the PNG: Chromium dithers canvas gradients (single-pixel steps on every target, checked 2026-09-23). A JPEG export gets grain against it; banding seen elsewhere comes from a viewer, a store or a tool that re-encodes the file | compare against the delivered PNG at 100 percent before changing anything; for a JPEG, keep the default quality; widen `from` and `to` or use `solid` if a platform's own re-encoding bands it |
| The added status strip has a visible edge or the wrong colour | `extend` samples the capture's top edge; the app header is a gradient, a photo or a different colour a few pixels down | a full-screen capture with a clean bar (state `clean`), which needs no strip |
| Glyphs have the wrong colour, or sit over the app's own clock | the bar area's most common colour misleads, or the state says `empty` while the bar has content | set `dirty` (flat bars are repainted) or supply a clean capture |
| The masked bar is a flat band over a photo or gradient | `statusbar: "mask"` covers the bar area with its main colour, flat or not | expected after the user's yes; `statusbar: "keep"` or a clean capture instead |
| The repaint covered part of the app's header | the capture comes from a device with a shorter bar than the drawn one | `statusbar: "keep"` on that capture, or retake on a current device |
| Two home indicators | the capture was cropped only at the top and `extend` added a bottom strip | crop both ends, or use the full-screen capture |
| An imported status bar looks too large or too small | height wins: the artboard is scaled to the frame's bar height, whatever its width | export at the bar's real height (62 pt iPhone, 32 pt iPad, 52 dp Android phone, 36 dp Android tablet); the import answer shows `viewbox`, and a `note` when the file is hardly a bar |
| Part of an imported status bar is missing | a shape that crosses the middle of the artboard is dropped on purpose (island, camera hole, background); a bar flattened into one compound path goes entirely | export time and icon cluster as separate shapes; an island in the export needs no action, the frame draws its own |
| The gap between clock and icons differs from the design file | the two halves are pinned to the screen edges and the middle flexes | expected; an artboard of exactly the screen's point width joins seamlessly |
| Images were handed on without credit | the shipped status bars and home indicators are CC BY 4.0 artwork; `proof.json` lists them under `attributions` | keep the proofs with the files and put the one-line credit in the delivery note (`devices-and-statusbar.md` section 7) |
| An imported bar is not used, or a phone bar does not show on the tablet frame | bars match by bar id, else by `--os` inside one device class | name the file by its bar id (`ios`, `ipad`, `android-gesture`…), or import the tablet version with `--device tablet` |
| With an opaque imported bezel the screen has square corners, or the bezel's island is gone | the capture is drawn above the bezel inside `--screen`, clipped only by `--screen-radius` | import again with the measured `--screen-radius`; for a visible island use a bezel with a transparent screen hole |
| Square screen corners show outside an imported transparent-hole bezel | the bezel was imported before the corner radius was measured (`screen_radius: 0`) | import it again without `--screen-radius`; detection measures the corner |
| An imported bezel is not used and the `note` says it is never rotated | the bezel and the capture have different orientations (Apple's iPad exports are landscape) | import the export of the capture's orientation as `<frame id>-portrait` or `<frame id>-landscape`; both can live side by side |
| An imported bezel is not used and the `note` compares two screen aspects | the capture comes from another model than the bezel (iPad Pro 13", 11" and mini differ by more than 2 percent) | the bezel of the capture's own device, or the drawn frame |
| `no_screen_hole` for a PNG that has alpha | its screen is painted (a placeholder pattern, a wallpaper), so there is no hole to find | `--opaque --screen x,y,w,h --screen-radius <px>`; without `--opaque` the painted screen would cover the capture |
| A flat rectangle around an imported bezel | the PNG has an opaque background outside the device | a PNG that is transparent outside the device (the import `note` says so) |
| An imported bezel looks pasted on, without depth | imported bezels get no shadow by default, which is what Apple's guidelines ask for | leave it for Apple bezels; otherwise `bezel_shadow: true` on the set or slide |
| Small type on a link card | `sub` and `badge` are held at 20 px on `og` and `x-card`; on `ph-gallery` and `play-feature` there is no floor and a badge can fall to about 15 px | `small_text` warns when copy ends under a target's floor; elsewhere Read the 320 or 400 px view of the `sheet` and drop what cannot be read |
| Device too small, empty band | a phone capture on a tablet target, a tablet-shaped capture in a phone frame (`note`), `bleed: false` on a tall phone | a capture of that device class; default bleed; `device-center` for whole devices |
| Device cut off where the point of the screen is | `device-top` bleeds the top away, `device-bottom` the bottom | swap the two layouts, or `bleed: false` |
| One locale overflows (`copy_too_long`, `fit_scale` under 0.9) | longer words, same line breaks | rewrite that locale: shorter native wording, another break, one more line, drop `sub` (`localization.md` section 3) |
| Arabic or Hebrew text is left-aligned | the locale is not `ar`, `he`, `fa`, `ur` and not in `rtl_locales` | list it in `rtl_locales`. Text mirrors inside its block; the block, the device and the lockup do not move, by design |
| Empty boxes or a serif fallback in CJK, Arabic or Thai text | the font has no glyphs for the script | a font file in `theme.font.files`, or `family: "system"` on a machine that has the script |
| The wrong device for the store (iPhone on Play, punch-hole on the App Store) | `frame` is set on the set or slide | `frame: "auto"`; per-store frames only come from `auto` |
| An Android frame on `play-feature` though the user wanted none | `auto` gives `play-feature` the Play device | `frame: "none"`, or `card-minimal` |
| The feature graphic sits smaller than on other cards | its card is laid out inside Play's cutoff zones (about 15 percent per edge), so type and device follow the safe box, not the canvas | by design: shorter copy reads larger there. Only the background may reach the edges |
| `cutoff_zone` on `play-feature` | `bleed: true` on that slide, a plate whose screen quad sits at an edge, or a lockup moved by hand | drop the bleed, a plate with the screen nearer the middle; a background that runs off the edge is fine, the logo, the name, the slogan and the main UI are not |
| `cutoff_zone` on an App Store creative asset | the same causes; on a hero scene, a device larger than Apple's art safe area (17, 23 and 9 percent of the header, search and universal canvases) | a plate with the device small and in the middle (`plates-and-prompts.md` section 4), or `card-left-title` with the capture; the box is Apple's own, from its template |
| Everything on a creative asset sits small in the middle | the card is laid out inside Apple's art safe area | by design: that box is what Apple keeps clear of every crop. The ground fills the rest; judge in App Store Connect's Preview, not at full size |
| Empty address pill, or the wrong title in a window | `app.url` is null; `macos-window` shows `app.name` | fill `app.url`; the pill shows the host only |
| The capture is soft inside a sharp frame | a downscaled or forwarded capture | the original file at native size (`fullscreen_match` exact) |

## 9. Repair budget

At most three attempts per step (a plate, a slide's copy, a layout choice), and something must change each time: the words, the layout, the colours, the capture or the plate prompt. Running the same deck again only makes sense after `tool_failed`. After the third attempt stop, say what was tried, and offer the simpler alternative: a gradient instead of the plate, `card-left-title` instead of the scene, a shorter headline the user approves.
