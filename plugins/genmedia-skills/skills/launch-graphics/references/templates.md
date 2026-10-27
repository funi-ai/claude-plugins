# Templates: layouts, frames, backgrounds

Every layout `launchkit.py` can render, the slide fields it validates, the copy budget per layout, how frames resolve and what the four background kinds paint. The numbers are the ones in the script (version `lk1`) and in `scripts/devices.json`; when this page and the script disagree, the script wins and `launchkit.py text` reports the binding budget. The deck around the slides is in `composition.md`; status bars are in `devices-and-statusbar.md`. `launchkit.py` abbreviates the call shown in SKILL.md.

## 1. Slide fields

| Field | Type | Rule |
|---|---|---|
| `id` | string | lower-case letters, digits, hyphens, 40 characters at most, unique in the set; becomes the file name `NN-<id>.png` |
| `layout` | string | one of section 2. A layout renders on one target kind (screenshot, card or square); a set that mixes kinds fails with `layout_target_mismatch` |
| `capture`, `capture2` | capture id, or `{"ios": id, "android": id, "default": id}` | required or refused per layout (section 2). The map picks `ios` on the iPhone and iPad `appstore-*` targets, `android` on `play-*` targets, otherwise `default` (`appstore-mac` included) |
| `copy` | `{<locale>: {headline, sub, emphasis, badge}}` | every deck locale, no other locale, no other key; `headline` and `sub` are arrays of lines; `emphasis` occurs verbatim in one headline line. On a card layout the whole field may be left out: the slide is then text-free (below). A `copy` that names some locales and not others is still `copy_missing` |
| `lockup` | bool or absent; on `card-lockup` also `{width, scrim, shadow}` | wins over the set's `lockup`. `false` keeps the brand lockup (logo, or icon plus app name) off this page; the default is on wherever the layout draws one. The object sizes the lockup of `card-lockup` (section 2) and is refused on any other layout |
| `compact` | bool or absent | wins over the set's `compact`; `card-left-title`, `card-centered` and `card-flow` with `caption: "left"` only, and only on a page without a lockup (on the set it needs the set's `lockup: false`). `true` gives the lockup's empty room to the copy (section 2). The default keeps that room empty, so the text of a series that mixes pages with and without a lockup stays in one place |
| `device_top` | number from 0 to 0.8, or absent | wins over the set's `device_top`; `card-left-title` and `card-centered` only: the top edge of the hung capture as a share of the card height (section 2). Use it to choose where a bleeding phone is cut off, for example in the gap above a button instead of through it |
| `invert` | bool | swaps ground and text colours of this slide (`bg` and `fg`, `bg_alt` and `fg_alt`). Ignored when the set's background names a plate; hex values in `background.from` and `to` do not swap, theme keys do |
| `bleed` | bool or absent | overrides the layout's default (section 2); `card-flow` refuses `true` |
| `frame` | `null`, `"auto"`, `"none"` or a frame id | wins over the set's `frame` (section 3) |
| `bezel_shadow` | bool or absent | wins over the set's `bezel_shadow`. `true` puts a drop shadow under an IMPORTED bezel; the default is none. Drawn frames always carry their shadow and ignore the flag |
| `connector` | `"arrow"` (default) or `"none"` | `card-flow` only: the arrow drawn between the two captures, or a plain gap |
| `caption` | `"top"` (default) or `"left"` | `card-flow` only: `top` stacks lockup and copy above the pair, centred; `left` sets them where `card-left-title` does, with its start size and copy budget, and holds the pair on the right (section 2) |
| `tilt` | degrees, or `[left, right]` | `card-flow` only, at most 8 either way: `2.5` turns the pair apart (-2.5 left, 2.5 right), a list sets each capture. The pair shrinks until the turned captures fit the card; the page renders at twice the pixels and is shrunk back so the turned edges stay smooth |
| `zoom` | `{x, y, w, h}` | layout `zoom` only: the crop as fractions of the capture, inside 0..1 |
| `plate` | plate id | `card-hero-scene` only (or take `background.plate`); the plate needs a `quad` or the deck fails with `plate_without_quad` |
| `decor` | list of `{ref, x, y, w, rotate, z}` | `ref` is a key of the deck's `decor`; `x`, `y` = centre and `w` = width as fractions of the canvas (`x`, `y` from -0.5 to 1.5, `w` from 0.02 to 2); `z: "back"` (default) is painted into the background behind the device, `"front"` sits above the device and below the text. Front decor over text warns `decor_overlaps_text` |

## 2. Layouts and their budgets

Lines over the budget are an error in `launchkit.py text` (`too_many_lines`), characters over the budget a warning (`chars_per_line`); the hard gate is the fit pass in `compose` (`copy_too_long` at 72 percent of the start size). `badge` takes 24 characters on every layout. Characters are counted per authored line.

| Layout | Targets | Captures | Headline lines x characters | `sub` lines x characters | Bleeds by default |
|---|---|---|---|---|---|
| `device-bottom` | store | 1 | 3 x 18 | 2 x 40 | yes |
| `device-top` | store | 1 | 3 x 18 | 2 x 40 | yes |
| `device-center` | store | 1 | 2 x 20 | 2 x 40 | never |
| `two-devices` | store | 2 | 3 x 18 | 2 x 40 | yes |
| `zoom` | store | 1 | 3 x 18 | 2 x 40 | the context device always |
| `device-span` | store, `strip` set | 1 | 3 x 18 | 2 x 40 | yes (off the bottom); always off its right edge |
| `device-span-end` | store, `strip` set | 0: the device of the slide before it | 3 x 18 | 2 x 40 | as its `device-span` |
| `text-only` | store | 0 | 4 x 13 | 3 x 36 | - |
| `card-hero-scene` | card | 1 and a plate with a quad | 3 x 14 | 2 x 36 | - |
| `card-left-title` | card | 1 | 3 x 14 | 3 x 36 | phone yes, window no |
| `card-centered` | card | 0 or 1 | 2 x 24 | 2 x 56 | yes |
| `card-minimal` | card | 0 | 3 x 20 | 2 x 56 | - |
| `card-browser` | card | 1 | 2 x 34 | 1 x 60 | no |
| `card-flow` | card | 2 | 2 x 28 | 1 x 60 | never |
| `card-flow`, `caption: "left"` | card | 2 | 3 x 14 | 3 x 36 | never |
| `card-lockup` | card | 0 | no copy | - | never |
| `thumb-icon` | square | 0 | no copy | - | - |

Store = `appstore-iphone-*`, `appstore-ipad-13`, `appstore-mac`, `play-phone`, `play-tablet`, `play-tablet-7`, `play-tablet-10`. Card = `og`, `x-card`, `github-social`, `ph-gallery`, `email-card`, `play-feature`, `cws-screenshot`, `cws-promo-small`, `cws-promo-marquee`, and the App Store creative assets `appstore-header`, `appstore-search`, `appstore-universal`. Square = `ph-thumbnail`.

**Text-free cards.** A store slide needs a headline in every locale. The card layouts do not: a slide with no `copy` (or with `"headline": []` in every locale) renders no text at all. `text` checks nothing on it and reports it as `text_free`; `compose` measures no copy, so the fit pass, `contrast`, `chars_per_line`, `small_text`, `play_tagline_share` and `text_share` have nothing to fire on; the page comes out the same in every locale, so one file serves them all. Use it where the surface itself carries the words (section 5 item 8) — not to dodge a `copy_too_long` that shorter copy would fix.

### Store slides (portrait; landscape is at the end of this section)

- **`device-bottom`**: text block on top (6 to 27.5 percent of the height), the device below it at 80 percent of the canvas width (86 for a tablet or a frameless capture), hung from 29.5 percent. With bleed it runs off the bottom edge; `bleed: false` scales it down until the whole body fits. The workhorse and the usual slide 1.
- **`device-top`**: the mirror image: the device stands on a line at 70.5 percent and bleeds off the top, the text sits under it. Alternate it with `device-bottom`. With bleed the top of the capture is cut off, so use it for screens whose content sits low.
- **`device-center`**: headline and `badge` on top, the whole device in the middle, `sub` in its own block under the device. Smaller type (8.4 percent of the width against 9.2). The layout for a calm closer and the only device layout that always shows the frame whole.
- **`two-devices`**: `capture` in front on the left, `capture2` behind it on the right, text on top. Two screens that belong together; both need the same appearance mode.
- **`zoom`**: the crop named by `zoom` comes forward as a rounded card (up to 92 percent of the width), the whole screen stays behind it as a dimmed device. For a detail a full screen hides: a number, a chart, one row. Crop wide and short: the card zone is about 0.92 x 0.50 of the canvas.
- **`device-span`** and **`device-span-end`**: one device across the seam between two slides of a `strip` set, on purpose. `device-span` owns `capture` and draws the device centred on its right edge; the very next slide must be `device-span-end`, which draws the same device, same size and height, centred on its left edge, so the two crops meet at the seam. Each slide has its own `copy` in the text block on top (landscape canvas: on the side away from the seam). The device sits like `device-bottom`'s, hung from 29.5 percent and off the bottom with bleed; `bleed: false` shows it whole. A landscape capture is contained whole instead, up to 0.86 of each slide's width (0.76 on a landscape canvas, text on top): the classic game panorama; on portrait slides it covers less height, so `device_share` may warn and is expected there. `device-span-end` takes no `capture`, `frame`, `bleed` or `bezel_shadow` of its own; they come from its `device-span`. Each crop shows half a device, so pick a capture whose two halves both read alone: no line of text or key control across the middle. Errors: `span_needs_strip` (the set's background is not `strip`), `span_unpaired` (a `device-span` not followed by `device-span-end`, or the reverse). A pair among the first three slides of a set with a Play target warns `span_early`: Google asks for the interface to stay prominent in the first three screenshots (`store-policy.md` section 2). `layers` refuses both.
- **`text-only`**: a large centred statement (start size 12.6 percent of the width) and the brand lockup at the bottom. One per set at most, never slide 1 (`store-policy.md` section 2).

### Cards

- **`card-left-title`**: lockup top left, text block on the left 44 percent, the capture on the right. A phone capture hangs at 27 percent of the width from 10.5 percent of the height (`device_top` moves it) and bleeds off the bottom (`bleed: false` shows it whole); a window or landscape capture is contained on the right, and `bleed: true` enlarges it to 62 percent of the width so it runs off the right edge. The text block runs from 25 to 88 percent of the height, below the lockup's place; without a lockup, `compact: true` centres it on the card (12 to 88 percent).
- **`card-centered`**: lockup, text and capture on one centred axis; the text block starts at 21.5 percent of the height and the capture (window 64 percent wide, phone 22) hangs from 58.5 percent, rising from the bottom edge. Without a lockup, `compact: true` moves the text block up to 11 percent and hangs the capture from 47.5 percent, a phone at 28 percent of the width: the left-title phone's scale, so a series that mixes both layouts shares one phone size. `device_top` sets the capture's top in either case. Without a capture the text block takes the middle of the card.
- **`card-minimal`**: lockup top left, a short accent rule, then headline and `sub` bottom-aligned on the left. Largest card type (7.4 percent of the width unit). The series layout (`og-cards.md` section 7).
- **`card-browser`**: a caption on top, a large window below. The caption box grows with what it holds (18 percent of the height for a short caption, up to 42 for two lines with `sub` and `badge`, which count at no less than the target's type floor), and the window is contained whole in what is left, at most 80 percent of the width: more words mean a smaller window. `bleed: true` sets the window to the full 80 percent and lets it run off the bottom.
- **`card-flow`**: before → after. `capture` on the left, `capture2` on the right, both at one height, a drawn arrow between them (`connector: "none"` leaves a plain gap of 12 percent of their height), the pair centred on the card. Frameless unless the slide or the set names a frame (`frame: "auto"` means `none` here). Lockup and caption sit above the pair when present; the caption box grows with its content like `card-browser`'s. Without copy and with `lockup: false` the pair takes the whole card (inside the cutoff box on `play-feature`). Each capture keeps its own aspect, so a taller capture is simply narrower; the arrow gives the direction, so the pair is not mirrored for right-to-left locales and a text-free page stays one file for every locale. Never bleeds. `tilt` turns the captures a few degrees for a looser, hand-placed look; 2 to 3 degrees reads as intent, more starts to cost size. A tilted pair is drawn by `launchkit.py`, never by a page written by hand: headless Chromium clips a turned rounded card without anti-aliasing, and only the supersampled compose path keeps its edges clean. `caption: "left"` puts the card into the `card-left-title` composition: lockup top left (6 percent of the width in, 9.5 percent of the height down, 8.8 percent high), the text block from 6 to 50 percent of the width and 25 to 88 percent of the height, left-aligned and vertically centred, at `card-left-title`'s start size (6 percent of the width unit) and budget (3 x 14, `sub` 3 x 36), so a series of left-title cards shares one type size. The pair, arrow and `tilt` included, is contained in the zone from 52 to 94 percent of the width and 10 to 90 percent of the height, centred in it; two phone captures come out larger there than under a caption on top. `lockup: false` leaves the text where it is (`compact: true` then centres it on the card, as on `card-left-title`); a text-free slide keeps the lockup alone on the left, as `card-left-title` does, so a text-free pair reads better with the default `top`; with neither copy nor lockup there is nothing to set on the left and the pair takes the whole card. Two landscape captures side by side get small in the right-hand zone: keep them under a caption on top.
- **`card-hero-scene`**: the plate covers the card, the capture is warped into the plate's screen quad, lockup and text go to the side away from the phone, over a scrim that eases out past the text, under the phone if it reaches it. `background.dim` sets the scrim strength (default 0.62). No frame is drawn: the phone in the plate is the frame. Details: `hero-scenes.md`.
- **`card-lockup`**: the brand lockup alone, large and dead centre, over the set's ground: the plate is the picture, the lockup is the subject. No `copy`, no capture. `lockup: {"width": 0.35, "scrim": 0.3, "shadow": true}` on the slide: `width` is the lockup's share of the canvas width (0.1 to 0.8, default 0.35), `scrim` the strength of a soft elliptical shade behind it (0 to 0.8), `shadow` a light drop shadow. On a `plate` or plate `strip` ground the defaults are scrim 0.3 and shadow on; on a solid or gradient ground neither, and `lockup: true` takes the defaults. The lockup stays inside a zone of 88 x 80 percent of the card (of the cutoff box on `play-feature` and on the App Store creative assets, where a `width` the slide does not set shrinks to fit the box: about 0.235 on `appstore-universal`), so a tall mark reaches the height first and warns `lockup_size`. The page scales the lockup to the width itself (logo or icon plus name), turns scrim and shadow dark or light from the lockup's own main colour, and measures that colour against the ground behind it (`lockup_contrast` below 3.0). One file for every locale. `lockup: false`, here or on the set, leaves nothing to draw and is refused. On `play-feature` Google asks the graphic not to repeat the icon's branding and Play shows the icon and name next to it: say that once in the plan card, the user decides.
- **`thumb-icon`**: `app.icon` at 62 percent of the square with rounded corners, or the first letter of `app.name` when there is no icon. No `copy`.

The lockup is `app.logo` when set, otherwise `app.icon` plus `app.name` as text. It appears on `text-only`, `card-left-title`, `card-centered`, `card-minimal`, `card-flow` (top centre; top left with `caption: "left"`) and `card-hero-scene`, at a fixed small height at the top; `card-lockup` makes it the subject. On `text-only` the name is set in `theme.muted` (optional; by default `fg_alt` mixed 35 percent toward `bg`), elsewhere in `fg`. `lockup: false` on the set, or on one slide, leaves it off: the surface may already show the icon and the name next to the image (`play-feature`), or the brand may be in the plate itself.

On `og` and `x-card` `sub` and `badge` never render below 20 px (`min_text_px` in `surfaces.json`); copy that would need smaller type fails as `copy_too_long` (`composition.md` section 5).

### Landscape store sets (`orientation: "landscape"`)

`appstore-mac` is landscape by itself (2880x1800) and needs no `orientation`; its desktop captures always take the stacked form below. Text takes the left 40 percent and the device stands on the right (`device-top`: mirrored). `device-center`, and any layout except `two-devices` whose capture is itself landscape, stacks instead: headline on top, the capture contained below. `zoom` shows only the crop card, without the context device. `device-span` keeps the text on the side away from its seam (stacked on top for a landscape capture). A landscape capture in a phone frame gets the cut-out on the left short side and the landscape status-bar rows (`devices-and-statusbar.md` section 3): a thin Android bar, no bar on an iPhone.

## 3. Frames

Frames are drawn from `scripts/devices.json`, never from a bitmap: the screen takes the capture's aspect (plus any added status strips), the body follows with a constant bezel, so a capture is never cropped or stretched by its frame.

| Frame id | What is drawn |
|---|---|
| `iphone` | phone with a pill-shaped island, iOS status bar and home indicator |
| `ipad` | tablet, uniform bezel, no cut-out, iPad bar |
| `android-phone` | phone with a centred punch-hole, Android bar and gesture pill |
| `android-tablet` | tablet, uniform bezel, no cut-out, Android tablet bar and gesture pill |
| `neutral-phone` | phone without cut-out, strips without glyphs: shows no platform |
| `browser` | window with three grey dots and an address pill |
| `macos-window` | window with three coloured dots and the centred `app.name` |
| `none` | the capture as a rounded card with a shadow and a hairline |

How `"auto"` resolves (a slide's `frame` wins over the set's; both default to `auto`):

1. **Store targets** take the target's frame whatever the capture's `os` is: `appstore-iphone-*` → `iphone`, `appstore-ipad-13` → `ipad`, `appstore-mac` → `macos-window`, `play-phone` → `android-phone`, `play-tablet`, `play-tablet-7`, `play-tablet-10` → `android-tablet`. In `mode: "universal"` every phone and tablet store target → `neutral-phone` (`appstore-mac` keeps its window), and an explicit iOS or Android frame fails with `universal_frame`.
2. **Cards and the square**: `card-flow` → `none`; otherwise capture `os` `web` or `desktop` → `browser`; otherwise `universal` → `neutral-phone`; otherwise the target's own device (`play-feature` → `android-phone`, `appstore-header`, `appstore-search`, `appstore-universal` → `iphone`); otherwise `ios` → `iphone`, `android` → `android-phone`.
3. `macos-window` is chosen by `auto` only on `appstore-mac`; elsewhere name it on the slide for a desktop app capture.
4. A set may carry its own `mode`, so one deck can hold a `both` set and a `universal` set.

Desktop captures: the window is a neutral drawing, never a real browser's chrome. The address pill shows the host of `app.url` (scheme and path are dropped; empty when `app.url` is null). The title bar turns dark when the top edge of the capture is dark. A capture that already contains browser chrome is a Retake: capture the page only.

`frame: "none"` on a phone or tablet capture still gets the status-bar work: the bars of the target's store on `appstore-*` and `play-*`, of the capture's own OS on the other targets, neutral in `universal`, always in its own device class. A capture whose OS is not the store's is then treated like one in a foreign frame (`devices-and-statusbar.md` section 3). A tablet-shaped capture in a phone frame, or the reverse, renders with a `note` warning: supply a capture from that device class. An imported bezel (`devices-and-statusbar.md` section 6) replaces the drawn body of the frame with the same id; it gets no added shadow unless `bezel_shadow: true` is set on the set or the slide.

## 4. Backgrounds (`sets[].background`)

| `kind` | Fields | What is painted |
|---|---|---|
| `solid` | `color` (theme key or hex, default `bg`) | one colour |
| `gradient` | `from` (default `bg`), `to` (default `bg_alt`), `angle` (default 160; 180 = top to bottom, 90 = left to right) | the gradient plus two soft accent blobs whose corners rotate from slide to slide |
| `plate` | `plate` (id), `dim` 0 to 0.9 | the plate cover-fitted and centred, never stretched; `dim` lays the theme `bg` over it at that opacity |
| `strip` | `plate` and `dim`, or `from`, `to`, `angle` (default 110) | one picture across all slides of the set: slide n shows the n-th crop. Without a plate it is one long gradient with accent blobs on the seams |

Seam rule for `strip`: only the background crosses a seam, and the device of a `device-span` pair (section 2) at its own seam. A text box, or any other device, within 3 percent of the canvas width from an inner seam warns `seam`; on a span pair the text is still checked. The order is part of the design: adding, removing or moving a slide changes every crop. The crop differs per target width, so Read each target.

`emphasis` takes the accent colour, pulled toward the text colour until it holds 4.6:1 on the ground; `metrics.accent_text` reports the colour used when it was adjusted.

## 5. Pick a layout

1. Slide 1 of a store set → `device-bottom`, shortest headline, strongest capture.
2. The next slide → `device-top`; then never the same layout twice in a row (`adjacent_layout_repeat`).
3. A detail that is small on the full screen → `zoom`. Two screens that tell one story → `two-devices`. One screen that should run across two slides of a `strip` set (a landscape game or video capture, a long timeline) → a `device-span` pair, from slide 4 on in a set with a Play target and never on slide 1.
4. A closer, or the slide that should look whole and upright → `device-center`.
5. A statement without a screen → `text-only`, once, not first.
6. Sets of five or more → one or two slides with `invert: true` (`no_inverted_slide`).
7. Link card for a page with a screen → `card-left-title`; desktop product → `card-browser`; a product whose value is a transformation (an input and what the product made of it) → `card-flow`, with `caption: "left"` when the other cards of the series are `card-left-title`; short symmetrical title → `card-centered`; no screen worth showing, or a series → `card-minimal`; launch or home page with a plate budget → `card-hero-scene`; a brand graphic whose whole design is a plate and the logo → `card-lockup`.
8. `play-feature` → a card layout; say once that Google lists device imagery under content to avoid and offer `card-minimal`. Offer the text-free version in the same breath (no `copy`, `lockup: false`): Google asks for the graphic and its text to be localised per market, so copy on it means one render per store language while a text-free graphic is one file for every locale; Play already shows the icon and the app name next to it and adds its own overlays in the promotional formats, and a tagline may cover 20 percent of the image at most (`play_tagline_share`). Copy on the feature graphic is worth it when the graphic has to say something the listing does not — the user decides, in the plan card.
9. `ph-thumbnail` → `thumb-icon`, in a set of its own.
10. Ad targets (`surfaces.md` section 2b): portrait ones (`ad-feed-4x5`, `ad-vertical-9x16`, `ad-video-9x16`) share a set and take `device-bottom` or `device-center`; on the 9:16 ones the text starts below the top 14 percent by itself, and `device-top` puts its copy into the covered bottom strip (`ad_safe_zone`). `ad-square` → `device-center` with a one-line headline, in a set of its own when the portrait copy runs to two lines. `ad-landscape`, `ad-video-16x9` → the card layouts. The `sub` line may be the call to action; no drawn buttons, no store badges.
11. `appstore-mac` → a set of its own. Slide 1 `device-bottom`, then `zoom` for a detail, `device-center` as the closer; with a desktop capture all of them stack on the landscape canvas (headline on top, window below), so vary them by crop and `invert` rather than by layout alone. `text-only` once at most, as on the phones.
12. `play-tablet-7`, `play-tablet-10` → the `play-tablet` choices (shortest copy of the deck); one set per slot, each with its own `orientation`.
13. `cws-screenshot` → `card-browser` for an extension seen on a page, `card-left-title` for a popup or a side panel; one short line each, since the store shows the file at 640x400. `cws-promo-small` and `cws-promo-marquee` share one text-free set: `card-centered` with the lockup and a capture rising from the bottom is the free draft; a brand plate under `card-minimal` is the upgrade.
14. `github-social` → the `og` choices; add it to the `og` set when the repository page and the site share one card.
15. App Store creative assets (`surfaces.md` section 1a) → a set of their own; every element is laid out inside Apple's art safe area, so the ground does most of the work. `appstore-header` carries one idea for a first-time visitor: `card-lockup` over a plate, or `card-centered` with one short line; no feature list. `appstore-search` makes the app's purpose plain and shows the real interface: `card-left-title` with the strongest capture and one line, `card-flow` when the value is a before → after (`caption: "left"` gives the pair more room inside the safe area: 26 percent of the canvas height against 18 with the caption on top, measured 2026-10-12), or `card-hero-scene` with the device small and in the middle of the plate. `appstore-universal` serves both placements and has the smallest box (about 27 percent of the width, above the middle): `card-lockup`, or a single capture with no copy. Offer text-free first; copy means one file per language. The header and the universal asset can share a set when they share a design (as below); the search asset gets its own.
16. `email-card` (`surfaces.md` section 2c) → a set of its own with `lockup: false` (the email's header carries the brand) and `compact: true`: `card-centered` for a phone screen under a two-line title, `card-left-title` for a three-line title, a window, or a phone cut off at a chosen place (`device_top`). `theme.badge_style: "text"` gives a quiet eyebrow instead of the pill. Export as `jpg`. The email says the same thing in live text and alt text.

## 6. Deck fragments

Entries of `sets`; all three validated, composed and passed `validate` with `lk1` on 2026-09-20 (captures `home`, `home-android`, `budgets` are phone captures, `dashboard` is a `web` capture; locale `en`). `sub`, `emphasis` and `badge` are optional.

Default store set, five slides:

```json
{"id": "store", "targets": ["appstore-iphone-69", "play-phone"], "orientation": "portrait", "frame": "auto",
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160}, "slides": [
  {"id": "hero", "layout": "device-bottom", "capture": {"ios": "home", "android": "home-android"},
   "copy": {"en": {"headline": ["Know what's left", "before payday"], "sub": ["Every account on one screen"], "emphasis": "payday"}}},
  {"id": "budgets", "layout": "device-top", "capture": "budgets", "invert": true,
   "copy": {"en": {"headline": ["A budget that", "warns you early"], "emphasis": "early"}}},
  {"id": "balance", "layout": "zoom", "capture": "home", "zoom": {"x": 0, "y": 0.17, "w": 1, "h": 0.3},
   "copy": {"en": {"headline": ["Your balance,", "always current"], "emphasis": "current"}}},
  {"id": "together", "layout": "two-devices", "capture": "home", "capture2": "budgets",
   "copy": {"en": {"headline": ["Spending and", "budgets together"], "emphasis": "together"}}},
  {"id": "forecast", "layout": "device-center", "capture": "budgets",
   "copy": {"en": {"headline": ["See month-end", "before it comes"], "sub": ["Forecasts from your own spending"], "emphasis": "before"}}}]}
```

Panorama store set with one device across the seam of slides 4 and 5 (the pair starts at slide 4 because the set has a Play target). Composed with `lk1` on 2026-09-23 against a real headless Chromium on both targets: no warning, the two halves meet at the seam, `validate` passed:

```json
{"id": "pano", "targets": ["appstore-iphone-69", "play-phone"], "frame": "auto",
 "background": {"kind": "strip", "from": "bg", "to": "bg_alt", "angle": 110}, "slides": [
  {"id": "hero", "layout": "device-bottom", "capture": {"ios": "home", "android": "home-android"},
   "copy": {"en": {"headline": ["Know what's left", "before payday"], "emphasis": "payday"}}},
  {"id": "budgets", "layout": "device-top", "capture": "budgets", "invert": true,
   "copy": {"en": {"headline": ["A budget that", "warns you early"], "emphasis": "early"}}},
  {"id": "balance", "layout": "zoom", "capture": "home", "zoom": {"x": 0, "y": 0.17, "w": 1, "h": 0.3},
   "copy": {"en": {"headline": ["Your balance,", "always current"], "emphasis": "current"}}},
  {"id": "month", "layout": "device-span", "capture": {"ios": "home", "android": "home-android"},
   "copy": {"en": {"headline": ["The whole month", "in one view"], "emphasis": "one view"}}},
  {"id": "month-end", "layout": "device-span-end",
   "copy": {"en": {"headline": ["And what", "comes next"], "emphasis": "next"}}}]}
```

Product Hunt gallery, four images, and the thumbnail in its own set:

```json
{"id": "ph", "targets": ["ph-gallery"], "frame": "auto",
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160}, "slides": [
  {"id": "promise", "layout": "card-browser", "capture": "dashboard",
   "copy": {"en": {"headline": ["One dashboard for every account"]}}},
  {"id": "phone", "layout": "card-left-title", "capture": "home",
   "copy": {"en": {"headline": ["Every account,", "one screen"], "sub": ["Know what's left before payday"], "emphasis": "one screen"}}},
  {"id": "sync", "layout": "card-centered", "capture": "dashboard", "invert": true,
   "copy": {"en": {"headline": ["Budgeting that", "keeps up with you"], "sub": ["Web, iPhone and Android in sync"], "emphasis": "keeps up"}}},
  {"id": "closer", "layout": "card-minimal",
   "copy": {"en": {"headline": ["Your money,", "finally in order"], "sub": ["Launching today"], "emphasis": "in order"}}}]}
```

```json
{"id": "ph-thumb", "targets": ["ph-thumbnail"], "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160},
 "slides": [{"id": "icon", "layout": "thumb-icon"}]}
```

Text-free Play feature graphic: the plate is the whole design, no copy, no lockup. Composed and passed `validate` with `lk1` on 2026-09-22; both locales came out as the same file, byte for byte (the deck's `plates.dusk` is a registered background plate):

```json
{"id": "feature", "targets": ["play-feature"], "frame": "auto", "lockup": false,
 "background": {"kind": "plate", "plate": "dusk"},
 "slides": [{"id": "feature", "layout": "card-minimal"}]}
```

Before → after feature graphic: a frame of the phone recording on the left, the finished listing on the right, frameless, text-free, one file for every locale. Composed with `lk1` on 2026-09-22 against a real headless Chromium: no warning, both locales byte for byte the same PNG, proofs written, `validate` passed:

```json
{"id": "feature", "targets": ["play-feature"], "frame": "auto", "lockup": false,
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160},
 "slides": [{"id": "flow", "layout": "card-flow", "capture": "walkthrough", "capture2": "listing"}]}
```

Brand graphic: a registered photographic plate and the user's own lockup (`app.logo`, an SVG) dead centre at 35 percent of the width, soft scrim and shadow by default on a plate. Composed with `lk1` on 2026-09-24 against a real headless Chromium on `play-feature` and `og`: the lockup came out at 0.35 of the width on both, proofs written, `validate` passed. The same plate serves a 16:9 YouTube thumbnail with the same lockup (`plates-and-prompts.md` section 10):

```json
{"id": "brand", "targets": ["play-feature"], "background": {"kind": "plate", "plate": "dusk"},
 "slides": [{"id": "brand", "layout": "card-lockup", "lockup": {"width": 0.35}}]}
```

A text-free card keeps its layout's proportions: the text zone simply stays empty. That suits a plate, or a capture told to fill the card (`card-left-title` with `bleed: true`); `card-centered` without copy leaves its upper half empty, so give it a plate or a wide capture rather than a small phone.

Open Graph and X pair: one set, one slide, two files (`og/en/01-home.png`, `x-card/en/01-home.png`):

```json
{"id": "social", "targets": ["og", "x-card"], "frame": "auto",
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160}, "slides": [
  {"id": "home", "layout": "card-left-title", "capture": "home",
   "copy": {"en": {"headline": ["Every account,", "one screen"], "sub": ["Know what's left before payday"], "emphasis": "one screen"}}}]}
```

A left-title card series with a before → after card in it: `caption: "left"` sets its lockup and copy where the `card-left-title` card has them, at the same size, the frameless pair on the right (`walkthrough` is a frame of a phone recording, with `statusbar: "none"`; `listing` and `home` are phone captures). Composed with `lk1` on 2026-09-25 against a real headless Chromium on `og` and `ph-gallery`: no warning, both headlines at one size on each target (71.8 px on `og`, 76.2 px on `ph-gallery`), `validate` passed:

```json
{"id": "social", "targets": ["og", "ph-gallery"], "frame": "auto",
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160}, "slides": [
  {"id": "phone", "layout": "card-left-title", "capture": "home",
   "copy": {"en": {"headline": ["Every listing,", "one screen"], "emphasis": "one screen"}}},
  {"id": "how", "layout": "card-flow", "caption": "left", "capture": "walkthrough", "capture2": "listing",
   "copy": {"en": {"headline": ["From a", "walkthrough", "to a listing"], "emphasis": "a listing"}}}]}
```

Mac App Store set, three slides on the landscape canvas (`desk` is a `desktop` capture of the app window). Composed with `lk1` on 2026-09-23 against a real headless Chromium: no warning, `validate` passed:

```json
{"id": "mac", "targets": ["appstore-mac"], "frame": "auto",
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160}, "slides": [
  {"id": "hero", "layout": "device-bottom", "capture": "desk",
   "copy": {"en": {"headline": ["Every account,", "one window"], "emphasis": "one window"}}},
  {"id": "detail", "layout": "zoom", "capture": "desk", "zoom": {"x": 0.25, "y": 0.12, "w": 0.72, "h": 0.36}, "invert": true,
   "copy": {"en": {"headline": ["Budgets, at once"], "emphasis": "at once"}}},
  {"id": "closer", "layout": "device-center", "capture": "desk",
   "copy": {"en": {"headline": ["See month-end early"], "sub": ["Forecasts from your own spending"], "emphasis": "early"}}}]}
```

App Store creative assets: the brand lockup as the header and the universal asset, and a search results asset with the real interface. Composed with `lk1` on 2026-10-07 against a real headless Chromium in `en` and `tr`: no warning, lockup, copy and phone inside Apple's art safe area on every page (the lockup's default width came out at 0.35 on the header and 0.235 on the universal asset), `validate` passed:

```json
{"id": "creative", "targets": ["appstore-header", "appstore-universal"], "frame": "auto",
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160},
 "slides": [{"id": "brand", "layout": "card-lockup"}]}
```

```json
{"id": "search", "targets": ["appstore-search"], "frame": "auto",
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160}, "slides": [
  {"id": "plan", "layout": "card-left-title", "capture": "home",
   "copy": {"en": {"headline": ["Plan every", "lira"], "sub": ["Budgets in two taps"]}}}]}
```

Email cards: no lockup, the room it leaves goes to the copy, a bare eyebrow (`"badge_style": "text"` in the theme), JPEG under the 1 MB cap. The third card hangs its phone lower so the cut falls where the capture allows. Composed with `lk1` on 2026-10-13 against a real headless Chromium: no warning, the eyebrow measured on the page at 4.9 to 5.5:1, 80 to 107 KB at quality 0.92, `validate` passed:

```json
{"id": "email", "targets": ["email-card"], "frame": "auto", "lockup": false, "compact": true,
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160}, "export": {"email-card": {"format": "jpg"}},
 "slides": [
  {"id": "accounts", "layout": "card-centered", "capture": "home",
   "copy": {"en": {"headline": ["Every account,", "one screen"], "badge": "BUDGETS"}}},
  {"id": "web", "layout": "card-left-title", "capture": "dashboard", "bleed": true,
   "copy": {"en": {"headline": ["Your budget", "in the browser"], "badge": "ON THE WEB"}}},
  {"id": "forecast", "layout": "card-left-title", "capture": "home", "device_top": 0.165,
   "copy": {"en": {"headline": ["Know what's", "left before", "payday"], "badge": "FORECAST"}}}]}
```

Chrome Web Store listing: two screenshots, then both promo tiles text-free in a set of their own, and the GitHub preview next to the Open Graph card. Composed with `lk1` on 2026-09-23 against a real headless Chromium: no warning, `validate` passed:

```json
{"id": "cws", "targets": ["cws-screenshot"], "frame": "auto",
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160}, "slides": [
  {"id": "shot", "layout": "card-browser", "capture": "dashboard", "copy": {"en": {"headline": ["Every account in one tab"]}}},
  {"id": "side", "layout": "card-left-title", "capture": "dashboard",
   "copy": {"en": {"headline": ["Budgets that", "warn early"], "emphasis": "early"}}}]}
```

```json
{"id": "promo", "targets": ["cws-promo-small", "cws-promo-marquee"], "frame": "auto",
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160},
 "slides": [{"id": "tile", "layout": "card-centered", "capture": "dashboard"}]}
```

```json
{"id": "social", "targets": ["og", "github-social"], "frame": "auto",
 "background": {"kind": "gradient", "from": "bg", "to": "bg_alt", "angle": 160}, "slides": [
  {"id": "repo", "layout": "card-left-title", "capture": "dashboard",
   "copy": {"en": {"headline": ["Every account,", "one screen"], "sub": ["Open-source budgeting"], "emphasis": "one screen"}}}]}
```
