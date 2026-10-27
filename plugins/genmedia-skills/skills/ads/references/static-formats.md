# Static ad formats and end cards

Six static formats plus the video end card. Exact copy is baked by the typography image model on top of a picture whose product came from the user's photo. Fields below were read from the live OpenAPI schemas on **2026-09-19**; repeat the Discovery guardrail in SKILL.md before spending. `gm.py`, `pipeline.py` and `adkit.py` abbreviate the calls shown in SKILL.md.

## 1. Two passes, and why

| Pass | Job | Endpoint | Why |
|---|---|---|---|
| 1. Picture | the locked product in its scene, with a calm area where copy will sit, **no text** | `bytedance/seedream/v5/pro/edit` (product photo first in `image_urls`) | Same fidelity rules as `product-photoshoot`; approved once, reused for every format, ratio and copy variant. An approved `product-photoshoot` still IS pass 1: register it and skip the job |
| 2. Copy | headline, lines, CTA, logo placed on the approved picture | `openai/gpt-image-2.5/flare/edit` (picture first, logo file second) | Strongest text fidelity in the dated routing; a typo re-rolls only this pass, and the scene cannot drift while copy is fixed |

- One pass is fine for flat graphic layouts (solid or gradient backdrop): GPT Image 2.5 edit with the product photo and logo as references. Then the product fidelity check runs on that output.
- Always deliver the text-free picture next to the finished ad: a designer can set the type in their own tool, and ad platforms often add their own headline fields.
- A logo is a file from the user, passed as a reference ("image 2 is the logo: reproduce it unchanged"). No file → set the brand name in plain type and say so. Never generate a logo from a name here.
- Copy passes through `adkit.py check` as `copy.json` first (`scripts-and-claims.md`, section 4): every number, offer and superlative needs its source before it is rendered.

## 2. Verified fields

`openai/gpt-image-2.5/flare/edit`: `prompt` (up to 32000 characters), `image_urls` (required, up to 16), `image_size` (`auto` default, a preset, or `{width,height}`), `quality` `auto` / `low` / `medium` / `high` (default) / `xhigh` / `max`, `num_images` 1-10, `output_format` `png` (default) / `jpeg` / `webp`, `background` `auto` / `transparent` / `opaque`, `mask_url` (optional). Output `result.images[]`. The text-to-image endpoint of the same model documents concrete sizes as multiples of 16, longest edge up to 3840, aspect up to 3:1; the edit schema does not restate it, so stay on multiples of 16. `mask_url` is a hint, not a boundary (measured 2026-09-21, `platform.md` section 10): an opaque black-and-white mask broke the output, and an RGBA mask with the edit area transparent still let the whole frame change. Do not use it to protect approved areas; a fix goes through a full edit whose result is read back again.

`bytedance/seedream/v5/pro/edit`: `prompt`, `image_urls` (required, up to 10; only the last 10 are used), `image_size` (preset, `auto_1K`, `auto_2K` default, or `{width,height}` with total pixels between 1024x1024 and 2048x2048), `num_images` 1-6, `output_format` `jpeg` (default) / `png`. Output `result.images[]`.

Sizes that satisfy both models (multiples of 16, inside Seedream's lower price tier):

| Ratio | Size | Typical placement (check the platform's current specs) |
|---|---|---|
| 1:1 | 1536 x 1536 | feed, marketplace, carousel |
| 4:5 | 1280 x 1600 | feed portrait (default static) |
| 9:16 | 1152 x 2048 | stories, vertical video end card |
| 16:9 | 2048 x 1152 | web banner, 16:9 end card |
| 1.91:1 | 1536 x 800 | link-preview style landscape |

Price hints: Seedream about $0.07 per picture plus $0.0045 per extra reference; GPT Image 2.5 about $0.06 to $0.10 per card at `high` at these sizes, about a quarter at `medium` (cost table in `routing-image.md`, `t2i-typography` notes), plus the reference allowance in `platform.md` §7 for the logo. Confirm with `gm.py price <ids> --explain`.

## 3. Copy-pass prompt skeleton

```text
image 1 is the finished photograph; image 2 is the brand logo. Keep image 1 exactly as it is: do not redraw, move, relight or restyle the product, the scene or any text printed on the product. Add only the following typography, in the calm area <where>:
HEADLINE, <position>, <weight and size relative to the frame width>, <colour>: "<exact headline>"
SUBLINE, below the headline, regular weight, about 40 percent of the headline size: "<exact subline>"
CTA, <position>, as a rounded button, <fill colour>, <text colour>: "<exact CTA>"
LOGO: place image 2 unchanged, <corner>, about <n> percent of the frame width.
Typeface: clean geometric sans-serif, the same family for all text. Spell every word exactly as quoted, including the letters ı, İ, ğ, ş, ç, ö, ü. No other text, numbers, badges, stars, seals or watermarks anywhere.
```

Rules: every string in straight double quotes, in its own language, exactly as approved; one line per text element; say where nothing may go ("keep the product and its label uncovered"); colours in plain words or the user's brand hex; ask for one typeface family. Text-to-text ratio: a static ad carries 5 to 12 words in total; more goes into the platform's caption field.

Stage plan (pass 2), two candidates of the first format:

```json
{"label": "zd-static", "max_parallel": 2, "jobs": [
  {"id": "ad-headline", "endpoint_id": "openai/gpt-image-2.5/flare/edit", "est_cost_usd": 0.21,
   "input": {"prompt": "image 1 is the finished photograph; image 2 is the brand logo. Keep image 1 exactly as it is: do not redraw, move, relight or restyle the bottle, the scene or the label text. Add only the following typography in the calm upper third: HEADLINE, centred, bold, about 70 percent of the frame width, dark olive green: \"Salatanın tadı değişsin.\" SUBLINE, below it, regular weight, about 40 percent of the headline size, same colour: \"Erken hasat, soğuk sıkım.\" CTA, bottom centre, rounded button, dark olive fill, cream text: \"Hemen dene\" LOGO: place image 2 unchanged, top left, about 14 percent of the frame width. Typeface: clean geometric sans-serif, one family. Spell every word exactly as quoted, including the letters ı, ğ, ş. No other text, numbers, badges, stars or watermarks.", "image_urls": ["@picture", "@logo"], "image_size": {"width": 1280, "height": 1600}, "quality": "high", "num_images": 2, "output_format": "png"}}
]}
```

## 4. The six formats

Zones are fractions of the frame; "calm area" is what pass 1 must leave empty (say it in the pass-1 prompt: "calm, evenly lit empty area in the upper third, no objects, no texture changes").

| Format | Zones | Copy limits | Needs from the facts sheet |
|---|---|---|---|
| `headline` (default) | product 55 to 65 percent of the height, lower or right; headline in the calm third; CTA button bottom; logo in a corner | headline up to 6 words, subline up to 8, CTA up to 3 | nothing beyond true wording |
| `bullets` | product on one side (40 percent of the width); headline plus 3 bullets stacked on the other, each with a simple tick or dot | headline up to 5 words; 3 bullets of up to 4 words each | each bullet is a fact (F-id) stated as a feature, not an outcome |
| `before-after` | two equal panels, left BEFORE, right AFTER, thin divider, small labels, product and CTA in a bottom strip | labels 1 word each; headline up to 6 words; time span line ("14 gün sonra") | the user's two real photos of the same subject and the time span. Never generated, never for body, skin or weight results without the user's substantiation. The photos are evidence: join them locally (recipe below), let pass 2 add only labels and headline, then compare both panels with the originals |
| `offer` | product centre or right; big offer figure in a contrasting block; terms line small at the bottom; CTA | offer up to 4 words ("İlk siparişe %15 indirim" is the long end); terms line verbatim from the user | the offer, its terms and its end date from the user. No strike-through prices, countdowns or "last chance" unless real and supplied |
| `comparison` | two columns: "ours" with the product, "ordinary" with a generic unbranded object; 3 rows of short attributes with tick or dash | column titles up to 2 words; 3 rows of up to 3 words | every row a sourced fact; the other column is a generic category, never a named or recognisable competitor, pack shape or colour scheme |
| `review-quote` | quote in large type with quotation marks over or beside the product; attribution line below; optional star row ONLY with platform and date | quote up to 15 words, verbatim; attribution exactly as the user approved | the real quote, attribution and permission. Star ratings only with the user's number, platform and date on the card |

Joining two evidence photos without a model (core ffmpeg filters; 1536 x 1024 result, swap the numbers for other sizes):

```bash
ffmpeg -hide_banner -loglevel error -i before.png -i after.png -filter_complex "[0:v]scale=768:1024:force_original_aspect_ratio=increase,crop=768:1024[a];[1:v]scale=768:1024:force_original_aspect_ratio=increase,crop=768:1024[b];[a][b]hstack=inputs=2" -frames:v 1 -update 1 genmedia-output/<slug>/before-after.png
```

Upload and register the result as `@picture`. If pass 2 alters either panel, deliver the joined picture plus the copy for the user's editor instead. No local ffmpeg → the user joins the photos.

Per-format pass-1 hints: `bullets` and `comparison` work best on a plain or softly graded backdrop (one-pass is fine); `headline` and `review-quote` carry lifestyle scenes; `offer` wants strong contrast between the figure block and the scene.

## 5. End card for video

- Size = the video's ratio from the table (9:16 → 1152 x 2048; the assembly scales it to the cut's size). Content: product hero from an approved keyframe, brand name or logo, one line, the CTA, optional disclosure line ("Presenter is AI-generated."). 1.5 to 2 s on screen, so at most about 6 words plus the logo.
- Job: the copy-pass skeleton with `"image_urls": ["@kf-hero", "@logo"]`, id `endcard`. The assembly turns it into a clip (`production-routes.md`, section 6 step 4).
- Keep the important elements inside the middle 70 percent of a 9:16 frame: platform UI covers the top strip, the bottom fifth and the right edge (check the platform's current safe zones).

## 6. Text QA (every output, before the user sees it)

Read the image with the Read tool at full size, then compare character by character against `copy.json`:

| Check | Pass when | Fail → |
|---|---|---|
| Spelling | every word, diacritic, digit, currency sign and punctuation mark equals the approved string | re-roll with the failing string repeated once more at the end of the prompt: `The headline reads exactly: "..."`. Third failure → shorten the string or deliver the text-free picture plus the copy for the user's editor |
| Nothing extra | no invented words, numbers, badges, stars, seals, fake UI, watermarks | re-roll; add the invented item to the "No ..." sentence |
| Product | label, shape, colour and count still match the photo; the copy pass changed nothing | re-roll pass 2 with a stronger "keep image 1 exactly" line; repeated → one-pass is not the fix: go back to the approved picture and reduce what pass 2 is asked to do |
| Logo | matches the file, not redrawn or recoloured | re-roll; else leave the logo to the user's editor |
| Layout | copy inside the calm area, product and its label uncovered, contrast readable at phone size (view the image small) | adjust zone words, colours; re-roll |
| Claims | every rendered claim is the sourced one; nothing strengthened | fix the copy, never ship |

## 7. Sets, ratios and variants

- Order: `headline` in the default ratio, two candidates → the user picks → the same picture and type treatment for the remaining formats and ratios, all in ONE batch with the pick passed as a style reference ("image 3 is the approved ad: match its typeface, colours and button style, not its layout").
- Another ratio needs a pass-1 picture in that ratio (edit from the approved picture plus the product photo: "same scene, reframed to 9:16, calm area at the top"), then pass 2. Do not stretch or crop finished type.
- Copy variants (headline A/B/C) re-run pass 2 only: about $0.08 each. Size a matrix with `adkit.py matrix`, treating headlines as hooks and pictures as visuals.
- A designer wants layers: `bria/ad-delayer` (input `image_url`, `text_mode` `svg` or `font`; about $0.30 per request as of 2026-09-19) splits a flat ad; read its live schema for the output shape before promising a file type.
- Deliver per ad: the PNG, the text-free picture, and the copy as plain text with its sources.
