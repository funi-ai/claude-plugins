# Applications: prompt contract, sizes, text rules, pitfalls

Every application is conditioned on the **approved logo as an image reference** and on the **BRAND LOCK**. Endpoint fields below were read from the live OpenAPI schemas on **2026-09-20** (all IDs active that day); they are a dated cache: repeat the Discovery guardrail in SKILL.md before spending. `gm.py`, `pipeline.py` and `brandkit.py` abbreviate the calls shown in SKILL.md; run them from the project root.

## 1. The two edit endpoints

| | `openai/gpt-image-2.5/flare/edit` (and `/sunburst/edit`, same fields) | `bytedance/seedream/v5/pro/edit` |
|---|---|---|
| Use for | surfaces that carry words besides the logo | photoreal objects that carry the logo only |
| Required | `prompt`, `image_urls` (max 16) | `prompt`, `image_urls` (up to 10; only the last 10 are used) |
| `image_size` | preset, `auto` (**default, follows the input image**) or `{width,height}`. Concrete sizes as documented on the family's text-to-image endpoint: both sides multiples of 16, longest edge 3840, aspect at most 3:1, 655,360 to 8,294,400 pixels. The edit schema does not restate these limits: stay inside them. | preset, `auto_1K`, `auto_2K` (**default**) or `{width,height}`: total pixels between 1024x1024 and 2048x2048, aspect 1:16 to 16:1. At or under a 1536x1536 area is the lower price step. |
| Other fields | `quality` `auto` / `low` / `medium` / `high` (default) / `xhigh` / `max`; `num_images` 1-10; `background` `auto` / `transparent` / `opaque`; `output_format` `png` (default) / `jpeg` / `webp`; `mask_url` optional | `num_images` 1-6; `output_format` `jpeg` (default) / `png`; `enable_safety_checker` |
| Output | `.result.images[].url` | `.result.images[].url` |
| Reference naming in prompts | `image 1`, `image 2` | `Figure 1`, `Figure 2` |
| Dollars | token-priced: the row of the next larger size at your `quality` in the GPT Image 2.5 table of `routing-image.md` (edit rows include one input image) + the reference allowance in `platform.md` §7 per further reference | `pricing_text`: base per output image + surcharge per input image after the first; double above the 1536x1536 area |

Neither endpoint takes SVG. Image 1 is always a PNG export of the approved logo (`logo.md` section 5). Never send `sync_mode`.

## 2. Prompt contract

One prompt file per job, `prompts/app-<name>-r1.txt`, three parts in this order:

```text
image 1 is the approved logo of "<Brand Name>". Use it exactly as supplied.
{{BRAND_LOCK}}
APPLICATION: <what it is>, <format in words: landscape 3:2, portrait 4:5>.
Logo placement: <surface>, <position>, <width as a share of the surface, e.g. one third of the card width>, <orientation: upright, parallel to the top edge>; variant: <full colour | reversed single colour | one colour>; keep the clear space free.
Text, exact, nothing else: "<string 1>" (<type role and place: headline type, top left>); "<string 2>" (<body type, under the name>).
Layout: <alignment, margins, what stays empty>.
Scene: <mockups only: the object, its material, the surface it rests on, light and camera following the lock's imagery style>.
Physical: <how the mark is applied: ink on uncoated paper, cut vinyl on glass, embroidery, one-colour screen print; true scale cues>.
Avoid: any other text, placeholder or dummy text, invented contact details, QR codes, barcodes, extra logos, watermarks, <format-specific items>.
```

- The line `{{BRAND_LOCK}}` stays exactly like that. `brandkit.py plan` replaces it with the approved block; you never type the block (`brand-lock.md` section 4).
- Seedream jobs say `Figure 1` in the role line. A surface without words says `Text: none besides the logo.`
- "Put the logo on the bag" is not a placement. Surface, position, scale, orientation and variant are all stated, every time.
- One application per job, one idea per application. A job that shows card, letterhead and envelope at once has three places to fail and no way to retry one.
- Model prompts are English; every on-image string keeps its language and letters, in straight quotes. For strings with İ ı ş ğ ü ö ç add `Spelling, letter by letter: …` after the string.

## 3. Text rules (DESIGN rule: wrong text = failed output)

1. **Strings come from the user, exactly.** Name, title, phone, e-mail, address, slogan, date, price: only what they gave, in their spelling. No field → the surface does not have it. Never placeholder data ("John Doe", "+90 555…", "www.brand.com"), never lorem ipsum, never an invented slogan.
2. Few and short: at most about 5 short strings on a business card, 3 on a poster or social post, 1 or 2 on a banner. Long copy belongs in the user's design tool with the real fonts.
3. Before the batch, write the expected strings to `app-<name>-expect.txt`, **one string per line, regardless of how the layout wraps it**. A lettered logo is text too: add the wordmark's line once for every time the logo appears (card front and back = twice).
4. After the batch, Read the image at full size and write what you actually see to `app-<name>-read.txt`, same convention, including anything you did not ask for. `add-candidate` compares after Unicode normalisation and whitespace collapsing; order is ignored; `ı` for `i`, a dropped letter or an extra invented line is `kind: "text_mismatch"` with the first differing character. That output is never shown. `brandkit.py text-check --expected-file … --read-file …` runs the same comparison without touching the ledger.
5. Retry ladder for a text failure (each step changes the prompt, job id `…-r1-t2`, then `-t3`): spell the failing string letter by letter and enlarge it → fewer strings on the surface → `openai/gpt-image-2.5/sunburst/edit` (say which model ran) → deliver the surface without that string and say so. Never a fourth attempt.
6. Mockups (Seedream route) carry the logo only. If the user wants words on a physical object (product name on a box), route that job to GPT Image 2.5 instead.

## 4. Logo variant by surface

| Surface | Variant as image 1 | Why |
|---|---|---|
| white or light, smooth, full-colour print or screen | `logo-primary` (no plate) | the approved colours carry |
| dark ground, photo with a dark area, dark app plate | `logo-reversed` | the primary colour disappears on dark |
| kraft, corrugated, newsprint; one-colour print | `logo-mono` | ink on absorbent stock is one colour in practice |
| emboss, deboss, foil, engraving, embroidery, cut vinyl | `logo-mono` | these processes have no colour of their own; say the process in `Physical:` |

Export each variant you need once (`brandkit.py png … --size 1024`, transparent background), upload, and register each under its own step so templates can name it:

```text
gm.py upload genmedia-output/<slug>/logo/logo-primary-1024.png genmedia-output/<slug>/logo/logo-reversed-1024.png
pipeline.py add --label <slug> --step logo --path genmedia-output/<slug>/logo/logo-primary-1024.png --url <first cdn_url>
pipeline.py add --label <slug> --step logo-reversed --path genmedia-output/<slug>/logo/logo-reversed-1024.png --url <second cdn_url>
```

Uploads are public URLs: say so once before uploading an unreleased logo. A PNG made by `qlmanage` may have a white background: use it on light surfaces only and say "opaque reference" in the role line. CDN links expire: a `validation` failure weeks later usually means re-upload and `pipeline.py add` again.

## 5. Catalogue

Sizes are defaults that satisfy both endpoints' limits; change them on request inside the limits of section 1. Cost hints dated 2026-09-20, `quality: "high"`; recompute with `gm.py price`.

| Application | Slot | Route | Default `image_size` | Text | Hint |
|---|---|---|---|---|---|
| Business card, front and back on a plain surface | `app-business-card` | GPT Image 2.5 Flare edit | 1536x1024 | user's name, title, contact lines | ~$0.05 |
| Social post | `app-social-post` | GPT Image 2.5 Flare edit | 1024x1024, or 1024x1280 for 4:5 | headline, optional one line | ~$0.05 |
| Social story or reel cover | `app-social-story` | GPT Image 2.5 Flare edit | 1152x2048 | headline | ~$0.06 |
| Poster | `app-poster` | GPT Image 2.5 Flare edit | 1024x1536 | headline, date or place if given | ~$0.05 |
| Banner | `app-banner` | GPT Image 2.5 Flare edit | 2304x768 (3:1, the widest allowed) | one line | ~$0.05 |
| Presentation cover | `app-presentation-cover` | GPT Image 2.5 Flare edit | 1920x1088 (1080 is not a multiple of 16) | title, optional subtitle | ~$0.06 |
| Signage: shopfront, door or wall sign | `app-signage` | Seedream 5.0 Pro edit | 1536x1024 | logo only | ~$0.07 |
| Packaging: box, bag, label, cup | `app-packaging` | Seedream 5.0 Pro edit | 1280x1600 | logo only | ~$0.07 |
| Merchandise: tote, T-shirt, mug, cap | `app-merch-<item>` | Seedream 5.0 Pro edit | 1280x1600 | logo only | ~$0.07 |
| App icon and favicon | `app-icon` | local: `brandkit.py icon`, then `icon-export` | 1024 SVG; after approval every platform file (`app-icons.md`) | none | $0 |

Candidate ids are the slot name without `app-` (`business-card`; two options in one review: `business-card-A`, `business-card-B`); job ids `app-business-card-r1`, `app-business-card-B-r1`.

Per application, what goes wrong and what to write:

- **Business card.** State the format in words and leave millimetres to the printer: 85 x 55 mm is common in Europe and Turkey, 3.5 x 2 in in the US; check with the print shop. Ask for "front and back side by side, flat, top-down, soft even light" rather than a stack of cards at an angle: angled stacks hide misspellings. Front: logo alone. Back: the user's lines, left-aligned in the body type. It is a visualisation: the print file is set in a design tool from the SVG logo and the real fonts, and the delivery says so.
- **Social templates.** "Template" here means a flattened image in the brand's layout, not an editable file. Platform sizes and safe areas change: the ratios above (1:1, 4:5, 9:16) are widely used basics; check the current rules of the platform. Keep text inside the central 80 percent. For a series, fix the layout sentence and change only the strings: that is what makes it a template. No fake UI (like counts, handles, buttons).
- **Poster and banner.** One focal element, the logo small and in a corner with its clear space, one headline. A banner wider than 3:1 is outside the model's limits: generate 3:1 with everything important in the middle band and say that the final crop happens in the user's tool. A poster that only needs flat colour, logo and a headline is often better as the brandbook-style HTML the user can edit; offer it when they ask for "editable".
- **Presentation cover.** Title slide only. Large calm area for the title, logo in a corner. A full deck is outside this skill.
- **Signage.** Name the sign type (fascia above the door, projecting blade sign, vinyl on glass, brushed metal letters on a wall), the mounting and the time of day. Street scenes invent neighbours: add "no other shop names, no street signs with text, no people facing the camera". Never invent an address or opening hours on the door.
- **Packaging.** Name the pack type, material and finish, and the print method. Never invent what regulation puts on a pack: ingredients, weights, nutrition tables, barcodes, recycling or certification marks, warnings. The mockup shows the brand face only; `Avoid:` lists those items explicitly. Dielines, bleed and legal panels are print-shop work.
- **Merchandise.** One item per job, plain background from the palette or the lock's imagery style. State the technique (one-colour screen print, embroidery about 8 cm wide on the chest): it decides the variant (section 4) and keeps the model from printing a full-colour gradient on a cap.
- **App icon and favicon.** Never generated: `brandkit.py icon` nests the untouched mark on a palette plate (`logo.md` section 5). Offer two options when the palette allows (primary mark on the background colour; reversed mark on the primary colour), register them with `--origin local` in slot `app-icon`, show the board, stop. After approval run `brandkit.py icon-export` on the approved file: it writes the App Store and Play masters, Android adaptive layers, favicon and PWA files and the macOS icon set from dated platform rules, checks them and attaches the export to the slot (`app-icons.md`). Single extra sizes: `png`, then `add-asset --slot app-icon --role png-<n>`. A horizontal lockup is unreadable in a square: use a symbol-only mark or the companion mark from `logo.md`.

## 6. Worked batch: tier 2 (business card, social post, tote)

`.genmedia/projects/<slug>/brandkit/apps-1.spec.json`:

```json
{"label": "<slug>", "max_parallel": 3, "jobs": [
  {"id": "app-business-card-r1", "endpoint_id": "openai/gpt-image-2.5/flare/edit", "est_cost_usd": 0.05,
   "prompt_file": ".genmedia/projects/<slug>/brandkit/prompts/app-business-card-r1.txt",
   "input": {"image_urls": ["@logo"], "image_size": {"width": 1536, "height": 1024}, "quality": "high",
             "num_images": 1, "output_format": "png"}},
  {"id": "app-social-post-r1", "endpoint_id": "openai/gpt-image-2.5/flare/edit", "est_cost_usd": 0.05,
   "prompt_file": ".genmedia/projects/<slug>/brandkit/prompts/app-social-post-r1.txt",
   "input": {"image_urls": ["@logo"], "image_size": {"width": 1024, "height": 1280}, "quality": "high",
             "num_images": 1, "output_format": "png"}},
  {"id": "app-merch-tote-r1", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "prompt_file": ".genmedia/projects/<slug>/brandkit/prompts/app-merch-tote-r1.txt",
   "input": {"image_urls": ["@logo-mono"], "image_size": {"width": 1280, "height": 1600},
             "num_images": 1, "output_format": "png"}}
]}
```

`prompts/app-business-card-r1.txt` (the user gave a name, a title and an e-mail address; nothing else exists on the card):

```text
image 1 is the approved logo of "Tilki Kahve". Use it exactly as supplied.
{{BRAND_LOCK}}
APPLICATION: business card, front and back shown side by side, flat, seen from directly above, landscape 3:2.
Logo placement: front side, centred, one third of the card width, upright; variant: full colour on the background colour; keep the clear space free. Back side: no logo.
Text, exact, nothing else: "Elif Demir" (headline type, back side, top left); "Kurucu" (body type, under the name); "elif@tilkikahve.example" (body type, bottom left). Spelling, letter by letter: K-u-r-u-c-u.
Layout: left-aligned, generous margins, the right half of the back side stays empty.
Scene: two uncoated cards on a pale oak table, soft window light from the left, short soft shadows.
Physical: matte uncoated paper, ink slightly absorbed, true business-card scale.
Avoid: any other text, phone numbers, addresses, QR codes, icons, extra logos, rounded card stacks, watermarks.
```

```text
brandkit.py plan --brand <slug> --spec .genmedia/projects/<slug>/brandkit/apps-1.spec.json --out .genmedia/projects/<slug>/brandkit/apps-1.tmpl.json
pipeline.py fill --template .genmedia/projects/<slug>/brandkit/apps-1.tmpl.json --out .genmedia/projects/<slug>/brandkit/apps-1.json
gm.py batch --plan .genmedia/projects/<slug>/brandkit/apps-1.json
```

- Cost (2026-09-20): two GPT jobs at the 1024x1536 row, `high` ($0.041 each, one reference included) + one Seedream job ($0.0675) = about $0.15. With the icon (free) that is tier 2's application batch. Add the logo round ($0.24) for the tier total; say that each retry adds its job again.
- `plan` answers `unresolved_references: ["@logo", "@logo-mono"]`: that is the cue to run `fill` (`logo-mono` is registered with `pipeline.py add --step logo-mono` like the variants in section 4; a tote is one-colour screen print). `fill` writes nothing while a reference is unknown; `gm.py` refuses a non-URL in `image_urls`.
- First call to each endpoint in the session is a canary: run the business card alone first (a one-job spec), then the rest. Bash timeout 600000 ms; `status: "pending"` → the same batch command again.

Register, per output, after your own look and the read-back:

```text
brandkit.py add-candidate --brand <slug> --slot app-business-card --id business-card --file genmedia-output/<slug>/app-business-card-r1_0.png --plan-file .genmedia/projects/<slug>/brandkit/apps-1.json --job app-business-card-r1 --expect-text-file .genmedia/projects/<slug>/brandkit/app-business-card-expect.txt --read-text-file .genmedia/projects/<slug>/brandkit/app-business-card-read.txt --endpoint openai/gpt-image-2.5/flare/edit --cost 0.05
brandkit.py board --brand <slug> --slot app-business-card --slot app-social-post --slot app-merch-tote --png
```

A mockup whose logo has no legible letters registers with `--no-text` only when the approved mark itself has none; a lettered logo on a tote is read back like any other text.

## 7. Repairing one output, and print sizes

- **Logo redrawn or distorted, scene fine.** Do not re-roll the scene. GPT Image 2.5 edit with two references: `image 1 is the mockup to correct; image 2 is the approved logo`, then the lock token, then `APPLICATION: replace the mark on <surface> with image 2 exactly, same position, scale and perspective; change nothing else.` Job id `app-<name>-r1-t2`. This costs one more job and usually saves the round.
- **One string wrong, layout fine.** Same move with the failing string spelled out. A `mask_url` does not keep the rest of the surface as it was: GPT Image redraws the whole frame even with an RGBA mask, and an opaque black-and-white mask breaks the output (measured 2026-09-21, `platform.md` section 10). Read every string of the new result again.
- **Print-size raster of an approved application.** `fal-ai/seedvr/upscale/image` (`image_url`, `upscale_mode: "factor"`, `upscale_factor` 1 to 10, `output_format: "png"`; about a tenth of a cent per megapixel). Text-heavy surfaces: `topaz/upscale/image/precision` with `model: "Text Refine"`, `upscale_factor` 1 to 4, `face_enhancement: false`, `output_format: "png"` (about $0.08 per started 24 MP). Run with `gm.py run`, Read the result, read the text back again (upscalers can "fix" letters), then attach it: `add-asset --slot app-poster --role print-2x --file …`. Still a visualisation, not print-ready artwork.
