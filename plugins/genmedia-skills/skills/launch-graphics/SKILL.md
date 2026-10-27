---
name: launch-graphics
description: >-
  Launch and listing stills for software: App Store and Google Play screenshots, App Store header and search assets (iOS 27), Play feature graphic, OG and X link cards, Product Hunt images, ad sizes. REAL captures composed in HTML (frames, status bars, exact sizes, locales), never redrawn; Seedream 5.0 Pro and GPT Image 2.5 paint only plates and scenes.
  Use when: "App Store screenshots for my app", "App Store header and search results image", "Google Play screenshots and feature graphic", "OG image and Twitter card for my site", "localize my store screenshots", "App Store ekran görüntüleri hazırla", "sitem için OG görseli yap", "Product Hunt lansman görselleri".
  Chain: takes a BRAND LOCK and icons from `brandkit`; gives PNG sets, a manifest, ad stills and video layers to `ads`.
  NOT for: physical-product listings (use `marketplace-cards`); ad copy, video ads (use `ads`); YouTube thumbnails (use `youtube-thumbnail`); demo and preview videos (use `demo-video`); logos, icons (use `brandkit`); posters (use `image`).
argument-hint: "[capture paths] [app-store|play|both|universal|creative-assets|og|product-hunt|ads] [locales] [--slug <project>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" *) Bash(command -v genmedia) Bash(genmedia models *) Bash(genmedia schema *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires python3 >= 3.8 and a Chromium-family browser (Chrome, Chromium, Edge, Brave) for rendering. The genmedia CLI >= 0.7.0 with a fal key configured by the user is needed only when a plate, scene or sticker is generated.
---

# Launch Graphics

Store screenshots, link cards and Product Hunt images for software, built from the user's real captures. One `deck.json` holds captures, copy per locale, theme and layouts; `launchkit.py` turns it into HTML and a headless browser renders every page at the exact pixel size. The interface is never regenerated: a model that repaints a screen misspells it, and both stores want the app as it is. Models paint only what is not the product: background plates, a scene with a key-colour screen, decor. A whole set with CSS backgrounds costs USD 0 and re-renders in seconds.

## Step 0 — Preflight

Once per session:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" tools
```

- `can.compose: false` → no Chromium-family browser. Say so and follow the fallback ladder in `references/composition.md` (copy, deck and validation still work; rendering does not). Never plan on Pillow, ImageMagick or `drawtext`.
- Only when something will be generated (Workflow step 5):
  ```bash
  command -v genmedia
  python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
  ```
  `blockers` not empty, CLI missing or older than 0.7.0 → `/genmedia-skills:setup`. Key missing → the user runs `genmedia setup` or exports `FAL_KEY` themselves; wait. Never read, print, request or type a key. Keep `config.announce_above_usd` and `config.confirm_above_usd` (defaults 0.50 and 2).
- Resume first: `.genmedia/projects/<slug>/launch-graphics/deck.json` exists for this product → continue from it; never start a second deck for the same slug.

## UX rules

1. Reply in the user's language. Copy on the images is in the language it ships in, written by you per locale; model prompts are English. Paths, ids and field names stay as they are.
2. No JSON, prompts, request IDs or tool narration in chat. One status line per long step at most.
3. **Question budget: 3, one at a time, labelled options, only when the answer is missing:**
   - Q1 targets and mode, when the request does not say: A App Store · B Google Play · C both, each with its own device · D one universal design for both · E link cards (OG + X) · F Product Hunt · G App Store header and search results assets (iOS 27). Several may be chosen. Ad placements (`ad-*` targets) arrive as a hand-off from `/genmedia-skills:ads` with copy already approved there; an ad request that starts here goes to `ads` first.
   - Q2 captures, when no file was given: ask for the paths and hand over the capture list (`references/copy-and-narrative.md`).
   - Q3 status bars, when any capture's bar is `dirty` (another clock, carrier, weak signal, battery not full, notification icons): one question for all of them, naming what you saw: A mask with the standard bar (9:41 / 9:30, full icons) · B keep as it is. A → `statusbar: "mask"`, B → `statusbar: "keep"`; no answer → `auto`, said in the delivery.
   Everything else is a default you state in the delivery: 5 store slides; locales = the app's own language plus English; theme from the user's repo or captures (look before asking: theme tokens, logo, icon); CSS gradient backgrounds; platform-true frames; iPhone 6.9-inch and Play phone sizes.
4. **Free draft first.** Render the whole set with CSS backgrounds, show the contact sheet, then improve. Plates and scenes are an upgrade you offer or the brief demands, never a precondition. Revisions re-render only what changed.
5. **Facts come from the user.** Ratings, user counts, awards, prices, rankings, press and partner logos appear only when the user supplied them (`facts` in the deck). Never invent proof. A screen that is not a real capture carries `mockup: true` and the delivery says so.
6. **Store rules are told once, as facts, not enforced as taste** (`references/store-policy.md`): drawn frames are not Apple's own product bezels (the user may import those); Google lists device imagery under content to avoid, so on Play sets the framed default is announced with the frameless option; a universal set carries nothing that identifies one platform.
7. Cost: a composed set is free. Before any generation, estimate the plan and apply the gate from preflight: under `announce_above_usd` → run and state it; up to `confirm_above_usd` → one line, then run; above → explicit yes. Never quote a price from memory.
8. Bounded: at most 3 repair attempts per step, something changes each time; a content-policy rejection is never resent unchanged; a job with a request ID is resumed, never resubmitted. Silence is never approval of a paid plan.

## Discovery guardrail

Sizes and device data are dated caches: `scripts/surfaces.json` and `scripts/devices.json` carry `verified_on`; a `null` is a number nobody read from the official page, never fill it from memory. `launchkit.py specs` prints the rows with their source URLs; when a store rejects a size, the official page wins and the row is corrected.

Before the first paid call to an endpoint in a session:

```bash
genmedia models --endpoint_id <endpoint_id> --json
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
```

`status` must be `active`; fields and limits come from the schema. Not active → next tier of the same task in `references/routing-image.md`. Never `genmedia run` with a prompt instead of an endpoint ID. New releases sit under vendor namespaces, not only `fal-ai/`.

## Routing

| Need | How | Why |
|---|---|---|
| Frames, status bars, text, layout, every size and locale | `launchkit.py compose` | exact pixels, real fonts, no misspelt UI, USD 0 |
| Background that CSS cannot give (place, material, mood) | `bytedance/seedream/v5/pro/text-to-image` | photoreal default; one plate per set |
| Illustrated or 3D look, sticker with a transparent ground | `openai/gpt-image-2.5/flare/text-to-image`, `quality: "medium"`, `background: "transparent"` | design strength; transparent output |
| Phone, tablet, laptop or monitor in a scene with the real screen in it | scene plate with a flat magenta screen, then `launchkit.py screen-quad` | the capture is warped in untouched (`references/hero-scenes.md`) |
| Cut-out of an existing picture | `bg-remove-image` task in `references/routing-image.md` | non-generative |
| Plate for a canvas no model reaches (`appstore-universal`, 5244 px) | the plate, then `fal-ai/seedvr/upscale/image`, factor 2, PNG | GPT Image 2.5 stops at a 3840 px edge, Seedream at 2048x2048 area (`references/plates-and-prompts.md` section 4) |

Tie-breakers and traps:

1. Text is never generated. A headline inside a plate is a rejected plate.
2. `frame: "auto"` follows the TARGET, not the capture: App Store targets get `iphone`, `ipad` or, on `appstore-mac`, `macos-window`, Play targets `android-phone` or `android-tablet`, universal sets `neutral-phone`, cards follow the capture's `os` (`web` and `desktop` → `browser`); `card-flow` is frameless unless a frame is named.
3. One file never serves both stores (Apple's phone ratio is above Play's 2:1 cap): `both` and `universal` render one deck at each store's size.
4. `card-hero-scene` on a Play target warns `hero_scene_on_play`: Google discourages people handling a device. Offer `card-left-title`. On `play-feature` a card is laid out inside Play's cutoff zones (about 15 percent per edge): only the background reaches the edges, and `bleed: true` there warns `cutoff_zone`. Plan it text-free unless the graphic must say something the listing does not: a slide without `copy` plus `lockup: false` is one file for every locale (Google wants the text localised per market, Play already shows the icon and the name next to it, and a tagline may cover 20 percent at most). Say that once in the plan card; the user decides (`references/surfaces.md` section 1). A product whose value is a transformation (an input and what it made of it) → `card-flow`: `capture` before, `capture2` after, an arrow between them; in a series of `card-left-title` cards add `caption: "left"` so lockup, copy and type size line up (`references/templates.md` section 2). A brand graphic whose whole design is a plate and the logo → `card-lockup`, the lockup dead centre at a share of the width (`lockup: {"width": 0.35}`); its YouTube twin comes from the same plate (`references/plates-and-prompts.md` section 10).
5. `og` and `x-card` are two renders of one slide (1200x630 and 1200x600); keep content inside the centred 2:1 band (`safe_crop`). PNG at 1x is the default; a set's `export` switches a target to JPEG under its byte cap, and on these two cards to 2x (`references/og-cards.md` section 6). Offer JPEG on `bytes_over_cap` or a console that refuses the weight.
6. Ad targets (`specs --store ads`): the frame follows the capture's OS, the store word lists do not run (an ad may call to action), numbers and claims still need `facts`. 9:16 placements cover their top and bottom with interface: act on `ad_safe_zone`; Google App campaigns want little text: act on `text_share`. No drawn buttons, no store badges (`references/surfaces.md` section 2b).
7. App Store creative assets (`appstore-header` 3840x1646, `appstore-search` 3840x2560, `appstore-universal` 5244x2950 PNG only; shown on iOS 27 and iPadOS 27 or later) are card targets laid out inside Apple's art safe area (17, 23 and 9 percent of the canvas): the header carries one idea for a first-time visitor (`card-lockup`, or one short line), the search asset makes the app's purpose plain with the real interface (`card-left-title`), the universal asset serves both. A search results asset replaces the screenshots in search on iOS 27. `text` fails prices, discounts, URLs, ©, Apple recognitions (Editors' Choice, App of the Day) and other platforms on them; keep everything 4+. After delivery, point the user to App Store Connect's Preview (`references/surfaces.md` section 1a). Not the `universal` mode.
8. Email cards (`email-card`, 1208x680 for a 604x340 slot): the email's header carries the brand, so `lockup: false` with `compact: true`, which gives the lockup's room to the copy; `theme.badge_style: "text"` for a quiet eyebrow; `export` as `jpg` (1 MB cap). The email repeats the card's title as live text and alt text (`references/surfaces.md` section 2c).
9. The user named a model → use it after the live check.
10. A capture is only ever tilted or warped by `launchkit.py` (`card-flow` `tilt`, `card-hero-scene`), never in a page you write: headless Chromium draws transformed edges without anti-aliasing, and only `compose` supersamples them and checks the result (`jagged_edge`).

## Workflow

1. **Intake.** Targets, mode, locales, captures, brand. Read every capture with the Read tool before planning. HEIC, TIFF or AVIF → the user or `sips`/`ffmpeg` converts to PNG first (`convert_first`). Look in the user's repo for theme colours, logo and icon before asking anything; no brand colours anywhere → take them from the captures (`capture add` stores measured `colors`: background, palette, accent, light or dark scheme; `probe --colors` does the same for any image). Never sample pixels with improvised tools.
2. **Project and captures.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" init --slug <slug> --name "<App Name>" --mode both --locale en --locale tr
   python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" capture add --slug <slug> --id home --file ./shots/home.png --os ios
   ```
   Raw files are archived untouched with their hash. Rate each capture Great, Usable or Retake and coach retakes (`references/copy-and-narrative.md`). LOOK at the top of each capture and set `statusbar_state` in the deck: `clean`, `dirty`, `empty` or `missing` (`references/devices-and-statusbar.md`); a `dirty` bar → Q3. iOS bars render 9:41, Android 9:30, icons full; island and camera hole come from the frame.
3. **Copy first.** Pick the arc for each set, then write every headline as line arrays per locale: one idea, an emphasis word, proof only where the user gave a fact. Transcreate, do not translate (`references/localization.md`).
4. **Deck.** Edit `.genmedia/projects/<slug>/launch-graphics/deck.json` with the Write or Edit tool: `theme`, `facts`, `sets[]` (targets, background, slides with `layout`, `capture`, `copy`). Layouts, required fields and ready fragments: `references/templates.md`; every field: `references/composition.md`. Then:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" text --slug <slug>
   ```
   Fix every error (copy budget, number or claim not in `facts`, store avoid-words, emphasis not in the headline) by rewriting the copy, never by shrinking type.
5. **Plates, only when needed** (`references/plates-and-prompts.md`, `references/hero-scenes.md`). Guardrail, then price, then one batch:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price bytedance/seedream/v5/pro/text-to-image,openai/gpt-image-2.5/flare/text-to-image --explain
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/launch-graphics/plates-1.json
   ```
   600000 ms Bash timeout; `status: "pending"` → the same command again. Read every plate; reject any with lettering. A scene plate:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" screen-quad --slug <slug> --plate forest --file .genmedia/projects/<slug>/launch-graphics/plates/forest_0.png --write
   ```
   A plate for `appstore-universal`, or a Seedream scene plate for `appstore-search`, is upscaled before it is registered (`references/plates-and-prompts.md` section 4). Without a camera cut-out the top is the highest side, so laptops, monitors and landscape tablets come out landscape; `--orientation portrait|landscape` overrides it when the answer's `orientation` is wrong for the capture.
6. **Compose.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" compose --slug <slug>
   ```
   300000 ms Bash timeout (about two pages per second). The answer is compact: counts, `failed[]` in full, `warnings_by_kind` with paths; per-file metrics and warning texts are in the `details` file (Read it when a warning needs numbers; `--full` prints everything). `failed[]` lists pages stopped by a hard gate (`copy_too_long`, `text_overlaps_device`, `contrast`, `aspect_mismatch`, `jagged_edge`, `capture_changed`, `jpeg_over_budget`): fix the deck, re-run only those with `--set`, `--slide`, `--locale`, `--target`. Act on `contrast`, `fit_scale`, `chars_per_line`, `small_text`, `play_tagline_share`, `seam`, `safe_crop`, `cutoff_zone`; explain the ones you keep. A run without `--slide` prunes pages the deck no longer has (`pruned[]`); never delete output files by hand.
7. **Look before you show.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" sheet --slug <slug> --set store --target appstore-iphone-69 --locale tr
   ```
   Read the sheet: judge the true-size row first (is slide 1 understood at 220 px; is a card readable at 400 px; the thumbnail at 40 px). Then Read full-size files: every headline letter by letter in every locale (ı İ ş ğ ü ö ç), status bar, frame for the store, nothing clipped, no key-colour rim on a scene, straight smooth screen edges on a hero scene or a tilted card (`compose` already gates `jagged_edge`; a step you still see is a failed page). Wrong → fix the deck and re-render; never deliver a page you did not look at.
8. **Video layers, only for a video hand-off** (`references/composition.md` section 7b): a real recording under the drawn frame, for `/genmedia-skills:ads` or `/genmedia-skills:demo-video`. The slide's capture is a frame of that recording; then
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" layers --slug <slug> --set ads-video --slide flow --target ad-video-9x16
   ```
   returns the alpha layer, the hole's rectangle and a ready ffmpeg filter for the video skill. Needs local ffmpeg (`can.layers`).
9. **Validate and deliver.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" validate --slug <slug>
   ```
   Exact sizes, no alpha, counts, byte caps, proofs. Then the delivery message. Revisions: edit the deck, re-render the affected pages, validate again.

## Delivery

```
<App> launch graphics: genmedia-output/<slug>/launch-graphics/
App Store 6.9": appstore-iphone-69/<locale>/01-hero.png … 05-<id>.png (1320x2868, <n> locales)
Google Play: play-phone/<locale>/… (1080x1920) · feature graphic play-feature/<locale>/01-feature.png
Link cards: og/<locale>/01-<id>.png (1200x630), x-card/<locale>/01-<id>.png (1200x600) · Product Hunt: ph-gallery/…, ph-thumbnail/…
App Store creative assets (iOS 27 and iPadOS 27): appstore-header/<locale>/01-<id>.png (3840x1646) · appstore-search/… (3840x2560) · appstore-universal/… (5244x2950, PNG)
Email cards: email-card/<locale>/01-<id>.jpg (1208x680, shown at 604x340)
Overview: sheet-<set>-<target>.png · manifest.json
Real captures, unchanged; frames and status bars are drawn; text is set in <font>. <only when a page drew a shipped bar:> Status bars and home indicators: Assets Kit UI Mobile, Tablet & Desktop by Julien Fovelle, CC BY 4.0. <only if true:> The <phone, tablet, laptop or monitor> in the hero card is a generated generic device. <only if true:> <slide> shows a mockup, not a shipped screen.
Chosen for you: <mode, slide count, locales, theme source, backgrounds, frames — every default the user did not set>
Store notes: <one line each that applies: drawn frames are not Apple's product bezels (import yours to swap) · Google discourages device imagery on Play, frameless is one switch away · the feature graphic carries no text, so one file serves every locale · creative assets show only on iOS 27 and iPadOS 27 and later, a search results asset replaces the screenshots in search there; check them in App Store Connect's Preview before submitting · warnings kept and why>
Generated: <none, USD 0 | n plates on <model>, est. USD <x>> · Files are local; nothing was uploaded.
Next: tell me a slide and what to change (copy, order, layout, colour); re-rendering is free.
```

Translate it; keep paths, sizes and on-image text unchanged. Link cards: add the meta-tag note from `references/og-cards.md`.

## Errors

| Signal | Do |
|---|---|
| `kind: "tool_missing"` | No Chromium-family browser (or `GM_BROWSER_BIN` wrong). Fallback ladder in `references/composition.md`; say rendering was not done. |
| `deck_invalid`, `deck_schema`, `layout_target_mismatch`, `mode_target_mismatch`, `universal_frame`, `span_needs_strip`, `span_unpaired` | The message names set, slide and field. Fix that field from `references/templates.md`; do not guess a second time without reading it. |
| `copy_missing`, `copy_unused`, `emphasis_not_in_headline` | A locale lacks a slide's copy, the deck lists a locale no copy uses, or the emphasis word is not verbatim in a headline line. Fix the copy. A card slide may instead carry no `copy` at all and render text-free; half a localisation is still `copy_missing`. |
| `check_failed` from `text` | Budget, numbers gate, claims gate or a store avoid-word. Rewrite; add to `facts` only what the user really stated. |
| `copy_too_long` from `compose` | The fit pass hit its floor. Shorter words or one more line; never a smaller floor. |
| `text_overlaps_device`, `contrast` | Move to a layout with room, change the plate's calm side, `dim` the plate or invert the slide. |
| `no_key`, `no_quad`, `aspect_mismatch`, `plate_without_quad` | Scene plate problem → `references/hero-scenes.md` section 5; re-roll with a changed prompt, at most 3. `aspect_mismatch` naming `--orientation` → run `screen-quad` again with it. |
| `jagged_edge` | Stepped edges on a warped or tilted capture. Never deliver that page. `compose` already rendered it supersampled and retried at a higher factor, so the plate's own screen edge is stepped (JPEG, upscaled or edited plate): regenerate it as PNG (`references/hero-scenes.md` section 6). On an App Store creative asset a plate smaller than the canvas steps too: upscale it first (`references/plates-and-prompts.md` section 4). |
| `layers_unsupported` | A hero scene, a zoom, a device across a seam or a slide without a capture cannot take a recording: use an upright framed layout, or keep that beat a still. |
| `capture_changed`, `file_missing`, `path_escape`, `convert_first` | The archived capture differs or a path is wrong: `capture add --replace`, fix the path, convert the file. |
| `gm.py` `status: "pending"` / `kind: "content_policy"` / `kind: "auth"` | Same command again, never resubmit / rewrite and say what changed / stop, the user fixes key or balance. |

Looks wrong rather than failed: `references/troubleshooting-launch-graphics.md`. Platform error types: `references/platform.md`.

## This skill does NOT

- Redraw, restyle, translate or "enhance" the app's interface with a model, or invent screens, ratings, reviews, awards or user counts.
- Ship or download Apple's device artwork or interface kit files (Apple's licence forbids redistributing them). Frames are this project's drawings; the status bars and home indicators come from Julien Fovelle's Assets Kit UI on Figma Community (CC BY 4.0, credited in `scripts/devices.json` and in each proof file); the user may import their own bezels, bars and fonts.
- Upload to App Store Connect, Play Console, Product Hunt or a website, or handle any credential.
- Make app icons or logos (`/genmedia-skills:brandkit`), demo, preview or launch videos (`/genmedia-skills:demo-video`), ad concepts, ad copy or video ads (`/genmedia-skills:ads`; this skill only composes the stills and layers that skill asks for), physical-product listing images (`/genmedia-skills:marketplace-cards`), YouTube thumbnails (`/genmedia-skills:youtube-thumbnail`), one-off posters (`/genmedia-skills:image`).

## Common mistakes

- Designing before the copy exists, then shrinking type to fit. Copy first; the fit floor is a hard stop on purpose.
- Feature lists as headlines. One idea per slide; slide 1 says why the app matters to someone who sees nothing else.
- The same layout five times, or no inverted slide in a set of five (`set_warnings`).
- Judging at full size only. Stores show about 220 px, feeds about 400 px.
- An Android frame or status bar on an App Store page, or any platform mark in a universal set.
- A hero scene for a dense screen: at card size nothing small survives.
- Buying plates before a free draft exists, or a new plate per slide instead of one per set.
- Translating headlines word for word; Turkish and German need their own line breaks.
- Filling a `null` in `surfaces.json` from memory, or trusting another tool's size table.

## Reference index

- `references/surfaces.md` — read when choosing targets or answering a size, count or format question: the dated table behind `surfaces.json`, the App Store creative assets and their art safe areas, ad placement sizes and safe zones, OG versus X, why one file cannot serve both stores.
- `references/store-policy.md` — read before writing copy or choosing frames: App Review 2.3.3 and 2.3.10, the creative-asset content rules, Apple's bezel guidance, Google's avoid lists, the claims gate, the mockup flag.
- `references/copy-and-narrative.md` — read at steps 2 and 3: capture triage and the capture list, headline angles, budgets, arcs for store sets and Product Hunt galleries, rhythm and seam rules.
- `references/localization.md` — read when a set has more than one locale: transcreation, Turkish, German, CJK and RTL specifics, store locale codes, the per-locale QA list.
- `references/og-cards.md` — read for link cards: which pages deserve a card, card layouts, type scale, safe band, series and batches, the meta tags for the delivery.
- `references/templates.md` — read at step 4: every layout with its fields and budgets, frames and `auto` resolution, backgrounds, validated deck fragments.
- `references/composition.md` — read when editing the deck or reading `compose` output: every deck field, folder trees, proofs and manifest, gates with thresholds, the no-browser fallback.
- `references/devices-and-statusbar.md` — read when setting `statusbar_state`, refreshing `devices.json`, giving clean-capture tips or importing bezels, bars and fonts.
- `references/hero-scenes.md` — read for `card-hero-scene`: plate prompt blueprint, key colour, reading `screen-quad`, repairs.
- `references/plates-and-prompts.md` — read before generating anything: what may be generated, routing, sizes, prompt blueprints, batch plan, cost.
- `references/troubleshooting-launch-graphics.md` — read when a result looks wrong, or an error kind is not in the table above.
- `references/routing-image.md` — read when a default endpoint is not active or another tier is needed; dated GPT Image 2.5 cost table.
- `references/cli-contract.md` — read when a `gm.py` call fails or is pending: `batch`, `wait`, ledger, raw-CLI fallback.
- `references/platform.md` — read when estimating cost or reacting to a platform error type.
- `scripts/gm.py` — shared helper for every paid call (`preflight`, `price`, `run`, `batch`, `wait`, `ledger`).
- `scripts/launchkit.py` — local, free, no network: `tools`, `specs`, `init`, `capture add`, `probe` (`--colors`), `text`, `assets`, `screen-quad`, `compose`, `layers`, `sheet`, `validate`; one compact JSON object per call (`--full` on `compose` and `text`), exit 0 ok, 1 failed, 2 usage.
- `scripts/surfaces.json` — dated target sizes, counts, caps and source URLs read by `launchkit.py specs` and `validate`.
- `scripts/devices.json` — dated frame geometry, status and bottom bars, known device screen sizes.
