# Text and readability

Rules for the words on the image, the two ways to get them there, the small-size gate, and delivery sizes. The numbers marked "heuristic" are this skill's design rules, not platform rules. Platform facts are limited to long-standing basics and always carry "check the platform's current rules".

## 1. Hook words

| Rule | Detail |
|---|---|
| Budget | At most 4 words and about 20 characters (heuristic). `thumbcheck.py text "<words>" --lang <code>` counts both and warns. Over budget → cut, do not shrink the type. |
| Job | Add what the title lacks: the stake, the number, the constraint, the twist. Title "How I built a desk" → text "$40" or "NO SCREWS", never "HOW I BUILT A DESK". |
| Material | Concrete nouns, digits, short verbs. Digits beat number words ("7", not "SEVEN"). No hashtags, no emoji, at most one "?" or "!". |
| Casing | ALL CAPS is the default for Latin-script display text. Sentence case is fine for calm or premium channels; then keep the user's own casing. |
| Language | The language the video is published in. Never translate a hook the user wrote. One language per image. |
| Truth | The words are a claim. Numbers, quotes and results must be in the video (SKILL.md UX rule 5). |
| No-text option | Valid and often strongest for faces and objects with a clear story. Offer it as one of the three concepts when the title already carries the hook. |

### Turkish and other non-ASCII text

- Uppercase with the helper, never by hand and never by the model: `i → İ`, `ı → I` (`"iyi" → "İYİ"`, `"ılık" → "ILIK"`). Pass `--lang tr`; the helper warns when Turkish letters appear without it.
- Put the exact string in quotes, add the `spelled` string, and name each special letter in words (prompt 4 in `prompt-blueprint.md`): "Ş (S with a cedilla), İ (capital I with a dot above), Ğ (G with a breve), Ü, Ö (two dots), Ç (C with a cedilla)".
- Ask for "a heavy sans-serif with full Turkish glyph support". Decorative display faces are where diacritics go missing.
- Measured (`platform.md` section 10): GPT Image 2.5 drew Turkish letters right in a 1280x720 headline, and on a 2000 px card at `high` down to about 1.5 percent cap height, caps included. The one miss came at `medium`: a capital İ inside an all-caps word drawn as a small dotted i. Drafts run at `medium` and headlines are caps, so read every İ in the drafts and do not count a miss there against the concept: in that run the same caps line came out right at `high`. A miss in the final: one re-roll with the special letters spelled out; a second failure → plate path with a text-only edit; a third → a wording without the failing letter, or deliver the text-free plate and say the text was not reliable.

## 2. Baked in one pass, or plate plus text edit

Both use the GPT Image 2.5 family for the lettering (`routing-image.md`, task `t2i-typography`). Local text drawing is not an option: many ffmpeg builds lack `drawtext`, and Pillow or ImageMagick are usually absent.

| Situation | Path |
|---|---|
| Default: one language, one wording | **Baked**: text is part of the draft and final prompts. Layout and lettering are designed together, which looks best. |
| Same image in several languages or A/B wordings | **Plate**: one text-free plate, then one text-add edit per wording. The picture stays constant, only the words change. |
| A special letter failed twice | **Plate**: a text-only edit is a narrower task than a full scene with text. |
| The plate is a real frame or photo (framework 8, a product shot, the user's portrait as-is) | **Plate**: the picture must not be redrawn; text and callout are added by edit. |
| The user wants to set type themselves | **Plate only**: deliver the text-free image with clean negative space and say where the text zone is. |
| The user's own logo is the subject (a brand channel, the store preview video of an app) | **Plate plus lockup**: the logo file is placed locally by `thumbcheck.py lockup` (section 2b), never drawn by the model. Words, if any, still come from a text-add edit before the lockup. |

Plate prompts and the text-add pattern: `prompt-blueprint.md`, Plate path. An edit re-renders the image: after every text-add, compare the face and key objects with the plate before showing it.

## 2b. Brand lockup on a plate

A model that redraws a brand mark changes it; the user's own file is placed instead, locally, by a headless Chromium-family browser:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/thumbcheck.py" lockup genmedia-output/<slug>/plate_0.png --logo ./brand/lockup.svg --size 2560x1440 --out genmedia-output/<slug>/lockup_0.png
```

- The plate is scaled to cover `--size` and centre-cropped; the logo sits dead centre at `--width` of the canvas width (default 0.35), inside a zone of 88 x 80 percent, over a soft elliptical scrim (`--scrim`, default 0.3; 0 for a calm plate) with a light drop shadow (`--no-shadow` turns it off). Scrim and shadow turn dark or light from the logo's own main colour. Centred, it stays clear of the duration badge.
- Logo files: SVG, or PNG or WebP with transparency. Ask for the file; never trace, redraw or generate it. A logo the user does not own is out (SKILL.md UX rule 5).
- Warnings: `lockup_contrast` (the logo's main colour below 3.0:1 against the ground behind it: raise `--scrim`, the logo version made for dark or light grounds, a calmer plate), `lockup_size` (a tall mark reached 80 percent of the height before the asked width), `logo_opaque` (the file has a background box: ask for the transparent version). Act on each before the gate.
- Then the small-size gate (section 5) on the result, and `fit` for the delivery sizes (section 6). Master 2560x1440, as for any final.
- No paid call is needed when the plate already exists. The same plate as a `launch-graphics` Play feature graphic: generate it once at 16:9 (2048x1152, the calm zone in the middle); `launch-graphics` shows its centred 2.05:1 band with its `card-lockup` layout and this command shows the whole 16:9, both with the logo at the same share of the width, so the two files read as one design.

## 3. Type direction (what to ask the model for)

- Heavy, wide or condensed sans-serif. Thin, script and serif faces break up at 160 px.
- Separation from the picture by at least one of: thick dark outline, solid colour plate behind the letters, hard drop shadow. On busy backgrounds use the plate.
- Two lines at most; the most important word largest or in the accent colour; tight line spacing.
- Cap height (heuristic): one line about 1/6 of frame height in 16:9, two lines about 1/8 each; 9:16 about 1/14 per line; 1:1 about 1/5.
- Contrast pairs that survive compression: white or yellow (#FFD400) on near-black, black on yellow, white on saturated red or blue. Avoid red on blue, green on red, grey on anything.
- Text never touches the frame edge: keep about 5 percent margin (heuristic). Platforms round the corners of thumbnails.

## 4. Placement and safe zones

| Format | Keep clear | Put text |
|---|---|---|
| 16:9 video thumbnail | Bottom-right corner (the duration badge covers it). Bottom edge in general: progress bars and hover previews sit there. Faces. | Upper or middle band, on the side the face looks towards. |
| 9:16 cover | Top strip and bottom third (captions, buttons, account name overlay them in feeds). Outside the central 4:5 area (profile grids crop to the centre). | Central band, centred horizontally. |
| 1:1 cover | Corners (apps round or badge them). | Centre or upper two thirds; show name in a fixed corner across a series. |

Overlay positions are long-standing interface habits, not published specifications, and they differ between apps and over time: check the platform's current rules and the user's own channel page when placement is tight.

## 5. The small-size gate

Run it on every draft set and on every final or revision, before the user sees anything. Order matters: look small first, large second.

1. Build the sheet (`thumbcheck.py sheet ... --expect <ratio> --out ...`) or a single preview (`thumbcheck.py preview <file>`), then Read it. Each variant is shown large and, below, at true 160 px on a dark and on a light strip.
2. **Transcribe, then compare.** Looking only at the small preview, write down (privately) what the text says and what the subject is. Then compare with the intended `upper` string and subject. You know what it should say, so reading it large first proves nothing.
3. Score each variant:

| Check | Pass at 160 px | Typical fix (one per re-roll) |
|---|---|---|
| Subject | Nameable in one second | Raise the subject's share of the frame; simplify or darken the background |
| Text legible | Your transcription matches `upper` | Fewer words; larger cap height; outline or plate; move off busy areas |
| Text exact | At full size every character matches `spelled`, diacritics included, no stray words | Spell the letters out in the prompt; name special letters; plate path |
| One focal point | The eye lands on one thing | Remove the second prop; blur or darken the background |
| Separation | Subject and text stand out on both strips; edges do not melt into the dark or the light strip | Rim light; thin light outline around the whole subject; brighter or darker background edge |
| Placement | Text clear of faces, the bottom-right corner and the margins | Name the zone in NEGATIVE SPACE and TEXT |
| Likeness | Face matches the reference photo opened next to it | Lower expression intensity; add a second face reference; identity plate (`revisions.md`) |
| Truthful | Nothing shown or written that the video does not contain | Remove it; never negotiate this one |
| Format | `variants[].checks.aspect_ok` true; no `warnings` about mixed ratios | Explicit `image_size`; see the auto-size trap |

4. A failing draft is re-rolled once under a new id with the one prompt change from the table, then the sheet is rebuilt. Do not show a draft that fails Text exact or Truthful. Other weaknesses may be shown if named honestly in the pick message.
5. The sheet is wider than about 1568 px (the helper warns) → viewers may downscale it and the small previews stop being true size: also run `preview` on each variant.
6. No local tool → Read the full-size files, apply the same table as if the image were a postage stamp, and say in the pick message that the mechanical preview was unavailable. Never write "checked at 160 px" when it was not.

## 6. Render and delivery sizes

GPT Image 2.5 sizes must be multiples of 16 per side, at most 3840 on the long edge, between 655,360 and 8,294,400 pixels (live schema, 2026-09-19).

| Format | Draft | Final master | Deliver (with `thumbcheck.py fit`) |
|---|---|---|---|
| 16:9 | 1280x720 | 2560x1440 (4K asked up front: 3840x2160) | 1920x1080 JPEG and 1280x720 JPEG, plus the PNG master |
| 9:16 | 720x1280 | 1440x2560 | 1080x1920 JPEG, plus the PNG master |
| 1:1 | 1024x1024 | 2048x2048 (large podcast art: 2880x2880) | 1400x1400 or 3000x3000 JPEG as the directory asks, plus the PNG master |

Platform notes (long-standing basics; check the platform's current rules before relying on them):

- **YouTube video thumbnails:** 16:9, at least 1280x720 recommended, JPG or PNG, a 2 MB upload limit for many years. Check YouTube's current limits: they have been raised for some accounts and formats.
- **Shorts, Reels, TikTok covers:** 9:16 at 1080x1920 is the common working size. Whether a custom cover can be uploaded, or only a frame picked, depends on the platform, the app version and the account: check before promising it.
- **Podcast directories:** square JPEG or PNG; Apple's long-standing spec is 1400 to 3000 px per side. Check the directory's current rules.
- **Course platforms:** each has its own size. Ask the user for the spec; otherwise deliver 16:9 and 1:1.

File size: a photographic PNG at 1920x1080 often exceeds 2 MB; JPEG at high quality is a fraction of that with no visible loss at thumbnail sizes. `fit --max-kb 2000` steps the JPEG quality down until the file fits and reports `size_kb` and `jpeg_quality` (approximate); `kind: "too_large"` means even the lowest step did not fit: deliver a smaller `--size`. `probe --expect <ratio> --max-kb <n>` is the final mechanical check and works without any local tool. After a centre crop (`cropped: true`) Read the result: no text or face may be cut.
