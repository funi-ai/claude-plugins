# Batch plans: one worked card set

A complete 7-card set as `gm.py batch` plans. Endpoint IDs were active and every input field below was read from the live OpenAPI schema on **2026-09-20** (`pixelcut/product-photo`, `openai/gpt-image-2.5/flare/edit`, `openai/gpt-image-2.5/sunburst/edit`, `bria/product-dimensions`, `bytedance/seedream/v5/pro/edit`). They are a dated cache: repeat the Discovery guardrail in SKILL.md before spending. `gm.py`, `pipeline.py` and `cardkit.py` abbreviate the calls shown in SKILL.md; run them from the project root (the ledger is `.genmedia/runs.jsonl` in the current directory). Cost lines use prices observed that day; re-price with `gm.py price`.

## Format and rules

```text
gm.py batch --plan <plan.json> [--retry-failed]
pipeline.py fill --template <plan.tmpl.json> --out <plan.json>
pipeline.py add --label <slug> --step <name> --path <file> --url <cdn_url>
pipeline.py urls --label <slug>
```

- Plan keys: `label`, `max_parallel`, `jobs[]` with `id`, `endpoint_id`, `input`, optional `est_cost_usd` and `download`. `download` sits next to `input`, never inside it; default `genmedia-output/<label>/<id>_{index}.{ext}`.
- One `label` for the whole set. Job ids are the card ids of `cards.json` (`c01-main` ... `c07-inbox`), so `cardkit.py readback --card <id>` finds the expected strings. Re-rolls: `c05-materials-r2` (add the same strings under that id, or pass the original id to `readback`).
- References are whole-string values: `"@product"` (a file registered with `pipeline.py add`), `"@c01-main"` (first output of that job), `"@c02-benefits[1]"` (second output, 0-based). `fill` writes nothing while any reference is unresolved.
- The helper refuses non-URL values only in top-level `*_url` and `*_urls` fields. Bria's `image` has no such net: an unfilled template there is submitted and billed. Always `fill`, always run the filled file.
- Jobs inside one plan are independent. A job that consumes another job's output goes into a later stage file: that is why the set has three stages.
- `{LOCK}` and `{SYSTEM}` stand for the verbatim paragraphs from `plan.md` (`set-system.md`). Replace them before saving: a placeholder that reaches the model is a wasted card. `fill` refuses one that survived (`{LOCK}`, `{{TOKEN}}`, `<describe it>`) and names the JSON path of every hit; a bracket that belongs in the prompt is escaped `\{ \} \< \>` and the backslash is dropped on write.
- Every paid call: Bash timeout 600000 ms. `status: "pending"` → run the same command again.

## Pricing a set

Dollars per card, from `gm.py price <ids> --explain`:

- `unit: "images"` (Pixelcut, Bria): `unit_price` x 1.
- GPT Image 2.5 answers `1 units`, which is not a price. Use the cost table in `routing-image.md` (`t2i-typography` notes) at `high`: masters up to 3.7 MP (1600x1600, 1344x2016, 2048x1536, 1552x960, 1952x800) → the 2560x1440 row, about USD 0.055; larger (2000x2000) → the 3840x2160 row, about USD 0.10. Add the reference allowance in `platform.md` §7 for every reference image beyond the first and say "about".
- Seedream (`unit: "units"`, read `pricing_text`): base per output image at or under a 1536x1536 area, plus the surcharge per input image after the first.
- Sum main + anchor x 2 candidates + remaining cards. Dated hint: a 7-card set at 2000x2000 is about USD 1.20, at 1600x1600 about USD 0.90. Re-rolls are extra: worst case 2 more per text card. Two sources disagree → quote the higher.

## The example

Olive oil bottle for a Turkish marketplace, square cards at 2000x2000, card language Turkish. Facts, copy deck, lock string and SET SYSTEM: the examples in `card-types.md` and `set-system.md`. The kit holds the bottle, a spare pourer cap (photographed) and a recipe booklet (no photo).

```text
gm.py upload ./bottle-front.jpg ./bottle-label.jpg ./kit-cap.jpg
pipeline.py add --label zeytin-dali-cards --step product --path ./bottle-front.jpg --url <cdn_url of the first file>
pipeline.py add --label zeytin-dali-cards --step product-label --path ./bottle-label.jpg --url <cdn_url of the second file>
pipeline.py add --label zeytin-dali-cards --step kit-cap --path ./kit-cap.jpg --url <cdn_url of the third file>
```

### Stage 1, `stage-1-main.tmpl.json`: the main image

```json
{"label": "zeytin-dali-cards", "max_parallel": 1, "jobs": [
  {"id": "c01-main", "endpoint_id": "pixelcut/product-photo", "est_cost_usd": 0.03,
   "input": {"image_url": "@product", "sync_mode": false, "image_size": {"width": 2000, "height": 2000},
     "background": {"mode": "Color", "color": {"r": 255, "g": 255, "b": 255}},
     "shadow": {"type": "Drop"}, "margin": {"all": "8%"}, "output_format": "jpeg"}}
]}
```

`fill`, `batch`, then Read `genmedia-output/zeytin-dali-cards/c01-main_0.jpg`: clean edges, nothing clipped, pure white, no leftovers of the old background. Leave `shadow` out for no shadow at all. A portrait listing (2:3) → `{"width": 1200, "height": 1800}` here; Pixelcut takes any size.

### Stage 2, `stage-2-anchor.tmpl.json`: the anchor, two candidates

```json
{"label": "zeytin-dali-cards", "max_parallel": 1, "jobs": [
  {"id": "c02-benefits", "endpoint_id": "openai/gpt-image-2.5/flare/edit", "est_cost_usd": 0.30,
   "input": {
     "prompt": "image 1 is the real product on a white background; image 2 shows its label close up. The product is the 500 ml dark green glass olive oil bottle from image 1: square shoulders, short neck, matte black pourer cap, matte cream paper label on the middle of the body. Keep its shape, proportions, glass colour, cap and label exactly as in image 1. The label shows an olive-branch line drawing and reads \"ZEYTİN DALI\", \"Soğuk Sıkım Natürel Sızma Zeytinyağı\", \"500 ml\", centred, dark olive on cream. Do not add, remove, translate or restyle anything on the label. Exactly one bottle, 26 cm tall. Layout: a square product infographic. The bottle stands on the right half, filling about 70 percent of the card height, on the set background. Top left: the headline. Below it, a left-aligned vertical list of 4 rows, each a small line icon and one short label: an olive press, an olive branch with young fruit, a water drop, a bottle with a small sun crossed out. Generous spacing, nothing overlaps the bottle. SET SYSTEM: square card with a 7 percent outer margin. Palette: background warm cream #F6F1E7, primary deep olive #2F4A2F, accent amber #D9A441 used sparingly, text near-black #1E1E1E. Type: one sturdy geometric sans-serif family, bold headlines and medium labels, sentence case, headline cap height about 5 percent of the card height, labels at least 3 percent, generous letter spacing, never script, condensed or outlined. Icons: single-weight line icons in deep olive with rounded ends, no fill, all the same size. Grid: headline top left, one left-aligned text column on the left 40 percent, product on the right half. Callouts: thin deep-olive leader lines ending in a small dot on the product, bold label at the outer end, no boxes. Flat, clean, no gradients, no badges, no shadows under text. Render exactly these strings, each once, spelled exactly as written, in Turkish; keep every diacritic and the exact capitalisation: headline \"Neden Zeytin Dalı?\"; row 1 \"Soğuk sıkım\"; row 2 \"Erken hasat\"; row 3 \"Asitlik 0,3\" (keep the comma); row 4 \"Işık geçirmeyen cam şişe\". No other text anywhere: no extra labels, badges, seals, ratings, prices, watermarks or placeholder words. The only other lettering is the product's own label, unchanged. Even studio light, true colours, square-on view.",
     "image_urls": ["@c01-main", "@product-label"],
     "image_size": {"width": 2000, "height": 2000}, "quality": "high", "background": "opaque",
     "num_images": 2, "output_format": "png"}}
]}
```

`fill`, `batch`, tiles and read-back on `c02-benefits_0.png` and `c02-benefits_1.png`, fidelity check, anchor checkpoint, **stop**. The user picks candidate 2 → `Anchor: @c02-benefits[1]` goes into `plan.md`.

### Stage 3, `stage-3-cards.tmpl.json`: the remaining five cards as ONE batch

```json
{"label": "zeytin-dali-cards", "max_parallel": 5, "jobs": [
  {"id": "c03-inuse", "endpoint_id": "openai/gpt-image-2.5/sunburst/edit", "est_cost_usd": 0.20,
   "input": {"prompt": "image 1 is the real product on a white background; image 2 shows its label close up; image 3 is the approved card of this set: match its palette, type, icons, grid and callout style, not its words or its layout. {LOCK} Layout: a square lifestyle card. Scene: a pale oak kitchen table in soft morning daylight, a plate of sliced tomatoes beside the bottle. A relaxed adult hand holds the bottle by its lower third and tilts it to pour a thin stream of oil onto the plate, label facing the camera and not covered, true to scale: the bottle is 26 cm tall. A solid strip in the set's primary colour along the bottom 14 percent carries the caption in the set's light background colour. {SYSTEM} Render exactly this string, once, spelled exactly as written, in Turkish; keep every diacritic and the exact capitalisation: caption \"Çiğ tüket\". No other text anywhere: no extra labels, badges, seals, ratings, prices, watermarks or placeholder words. The only other lettering is the product's own label, unchanged. Exactly one bottle. Natural hand, five fingers.",
     "image_urls": ["@c01-main", "@product-label", "@c02-benefits[1]"],
     "image_size": {"width": 2000, "height": 2000}, "quality": "high", "background": "opaque", "num_images": 1, "output_format": "png"}},
  {"id": "c04-dimensions", "endpoint_id": "bria/product-dimensions", "est_cost_usd": 0.04,
   "input": {"image": "@c01-main",
     "dimensions": [{"name": "height", "value": 26, "unit": "cm", "position": "left"},
                    {"name": "width_bottom", "value": 7, "unit": "cm", "position": "bottom"}],
     "style": "default", "title": "Ölçüler", "title_position": "top_left", "background": "#F6F1E7",
     "output_size": 2000, "output_format": "png"}},
  {"id": "c05-materials", "endpoint_id": "openai/gpt-image-2.5/sunburst/edit", "est_cost_usd": 0.20,
   "input": {"prompt": "image 1 is the real product on a white background; image 2 shows its label close up; image 3 is the approved card of this set: match its palette, type, icons, grid and callout style, not its words or its layout. {LOCK} Layout: a square materials card. The bottle fills the centre, seen from the same angle as image 1, on the set background. Top left: the headline. 2 callouts with thin leader lines point to: the dark green glass of the body, the matte black pourer cap. No cutaway, no exploded view, nothing the reference photos do not show. {SYSTEM} Render exactly these strings, each once, spelled exactly as written, in Turkish; keep every diacritic and the exact capitalisation: headline \"Malzemeler\"; callout 1 \"Koyu yeşil cam şişe\"; callout 2 \"Alüminyum kapak\". No other text anywhere: no extra labels, badges, seals, ratings, prices, watermarks or placeholder words. The only other lettering is the product's own label, unchanged. Exactly one bottle. Even studio light, true colours.",
     "image_urls": ["@c01-main", "@product-label", "@c02-benefits[1]"],
     "image_size": {"width": 2000, "height": 2000}, "quality": "high", "background": "opaque", "num_images": 1, "output_format": "png"}},
  {"id": "c06-howto", "endpoint_id": "openai/gpt-image-2.5/sunburst/edit", "est_cost_usd": 0.15,
   "input": {"prompt": "image 1 is the real product on a white background; image 2 is the approved card of this set: match its palette, type, icons, grid and callout style, not its words or its layout. {LOCK} Layout: a square how-to card with 3 equal panels in a row under the headline, numbered 1 to 3 with large numerals in the set's primary colour. Panel 1 shows a single line icon of a cupboard with a snowflake above its label. Panel 2 shows a single line icon of a salad bowl above its label. Panel 3 shows the bottle from image 1, small, with its cap closed, above its label. Same icon style in every panel. {SYSTEM} Render exactly these strings, each once, spelled exactly as written, in Turkish; keep every diacritic and the exact capitalisation: headline \"Nasıl kullanılır?\"; panel 1 \"Serin yerde sakla\"; panel 2 \"Çiğ tüket\"; panel 3 \"Kapağı sıkı kapat\". Apart from the numerals 1, 2 and 3 there is no other text anywhere: no extra labels, badges, seals, ratings, prices, watermarks or placeholder words. The only other lettering is the product's own label, unchanged.",
     "image_urls": ["@c01-main", "@c02-benefits[1]"],
     "image_size": {"width": 2000, "height": 2000}, "quality": "high", "background": "opaque", "num_images": 1, "output_format": "png"}},
  {"id": "c07-inbox", "endpoint_id": "openai/gpt-image-2.5/sunburst/edit", "est_cost_usd": 0.25,
   "input": {"prompt": "image 1 is the real product on a white background; image 2 shows its label close up; image 3 is the real spare pourer cap from the kit; image 4 is the approved card of this set: match its palette, type, icons, grid and callout style, not its words or its layout. {LOCK} Layout: a square kit card, top-down, even light, on the set background. Top left: the headline. Exactly 2 photographed items, separated by a clear gap: the bottle from image 1 lying on its back with the label up, and the spare pourer cap from image 3 at its real relative size. Under each item its label. Below them, one text row with a plain line icon of a booklet. Nothing else is in the kit. {SYSTEM} Render exactly these strings, each once, spelled exactly as written, in Turkish; keep every diacritic and the exact capitalisation: headline \"Kutuda ne var?\"; label 1 \"1 x 500 ml şişe\"; label 2 \"1 x Yedek kapak\"; row \"1 x Tarif kitapçığı\". No other text anywhere: no extra labels, badges, seals, ratings, prices, watermarks or placeholder words. The only other lettering is the product's own label, unchanged.",
     "image_urls": ["@c01-main", "@product-label", "@kit-cap", "@c02-benefits[1]"],
     "image_size": {"width": 2000, "height": 2000}, "quality": "high", "background": "opaque", "num_images": 1, "output_format": "png"}}
]}
```

- Why these routes: every card with baked text runs on Sunburst at `high`; the anchor ran on Flare because looks get rejected and Flare is the fast tier. `c04` is Bria because the measures are a height and a width in whole numbers: typed fields beat prompted digits (a `6,5 cm` on this Turkish card would go to route B of `card-types.md`: Bria prints `6.5 cm` and its number format cannot be set). Its weight and capacity badges are left off on this Turkish card (both print English words, `Net Weight 0.5 kg` and `Capacity 500 ml`, measured 2026-09-21): the capacity is already on the label and can go on the benefits card.
- `c04` is checked with `cardkit.py readback --plan ... --card c04-dimensions --seen-file ... --numbers-only` (expected strings in `cards.json`: `"26 cm"`, `"7 cm"`), then units, title and the measured extents by eye. It is the first call to that endpoint, so it is its own canary. Its `title` is typeset and rendered Turkish letters right on 2026-09-21; a title that still loses a letter → run it again as `c04-dimensions-r2` without `title`, or take route B of `card-types.md`.
- Cost math (2026-09-20; A = the reference allowance in `platform.md` §7): main $0.024. Anchor: 2 x ($0.10 for a 4 MP `high` image + A for the second reference) = $0.30. `c03`, `c05`: $0.10 + 2A = $0.20 each. `c06`: $0.15. `c07`: $0.10 + 3A = $0.25. `c04` $0.04. Total about $1.16 → say "about $1.20". At the default thresholds ($0.50 announce, $2 confirm): one line, then run. Worst case with every re-roll spent: about $3.10, so say that re-rolls are extra. At 1600x1600 the GPT Image cards drop to the 2560x1440 row (about $0.055): the set is about $0.90.
- The anchor job doubled as the canary for the GPT Image family; Pixelcut and Bria are one-job first calls. No extra canary is needed.

## Re-roll, repair, text-free fallback

A card that failed the read-back: a new id in a small plan, same label, changed prompt (`text-accuracy.md` section 5). The old file stays on disk; delivery points at the new id.

```json
{"label": "zeytin-dali-cards", "max_parallel": 1, "jobs": [
  {"id": "c05-materials-r2", "endpoint_id": "openai/gpt-image-2.5/sunburst/edit", "est_cost_usd": 0.20,
   "input": {"prompt": "<c05 prompt, with: callout 1 \"Koyu yeşil cam şişe\" (spelled K-o-y-u  y-e-ş-i-l  c-a-m  ş-i-ş-e; the letters after e are s with a cedilla) and labels one step larger, at least 3.5 percent of the card height>",
     "image_urls": ["@c01-main", "@product-label", "@c02-benefits[1]"],
     "image_size": {"width": 2000, "height": 2000}, "quality": "high", "background": "opaque", "num_images": 1, "output_format": "png"}}
]}
```

Narrow repair (layout good, one string wrong): the failed card is image 1.

```json
{"label": "zeytin-dali-cards", "max_parallel": 1, "jobs": [
  {"id": "c06-howto-r2", "endpoint_id": "openai/gpt-image-2.5/sunburst/edit", "est_cost_usd": 0.15,
   "input": {"prompt": "image 1 is a finished product card; image 2 is the real product for reference. Change only one thing: the label under panel 3 that currently reads \"Kapagi siki kapat\" must read \"Kapağı sıkı kapat\" (spelled K-a-p-a-ğ-ı  s-ı-k-ı  k-a-p-a-t; g with a breve, then dotless ı, and both vowels of the second word are dotless ı). Same font, size, colour and position. Keep every other word, the layout, the product and the colours exactly as they are. No other text anywhere.",
     "image_urls": ["@c06-howto", "@c01-main"],
     "image_size": {"width": 2000, "height": 2000}, "quality": "high", "background": "opaque", "num_images": 1, "output_format": "png"}}
]}
```

Read back **all** strings of the repaired card, not only the repaired one. Failed job (error, no image): fix its input in the template, `fill`, rerun the stage file with `--retry-failed`; the flag resubmits every failed id in that file.

Text-free fallback after three failed attempts (`text-accuracy.md` section 7); add `{"id": "c06-howto-plate", "type": "howto", "strings": []}` to `cards.json` so the read-back expects no text:

```json
{"label": "zeytin-dali-cards", "max_parallel": 1, "jobs": [
  {"id": "c06-howto-plate", "endpoint_id": "openai/gpt-image-2.5/sunburst/edit", "est_cost_usd": 0.15,
   "input": {"prompt": "image 1 is the real product on a white background; image 2 is the approved card of this set: match its palette, icons, grid and callout style. {LOCK} Layout: a square how-to card with 3 equal panels in a row, each with a single line icon: a cupboard with a snowflake, a salad bowl, the bottle from image 1 with its cap closed. {SYSTEM} This card carries no text at all. Where the headline and the 3 panel labels would sit, draw empty flat panels in the background colour, one top left and one under each icon, each large enough for a line of text, with clean edges. No letters, numbers, placeholder words or scribbles anywhere except the product's own label, unchanged.",
     "image_urls": ["@c01-main", "@c02-benefits[1]"],
     "image_size": {"width": 2000, "height": 2000}, "quality": "high", "background": "opaque", "num_images": 1, "output_format": "png"}}
]}
```

## Variants

Text-free in-use scene on Seedream (no caption; size at the base-price area; roles as "Figure"):

```json
{"label": "zeytin-dali-cards", "max_parallel": 1, "jobs": [
  {"id": "c03-inuse", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.08,
   "input": {"prompt": "Figure 1 is the real product on a white background; Figure 2 shows its label close up; Figure 3 is an approved card of this set: match its colour palette only. <lock string with Figure 1> Scene: a pale oak kitchen table in soft morning daylight; a relaxed adult hand tilts the bottle to pour a thin stream of oil onto a plate of sliced tomatoes, label facing the camera and not covered; the bottle is 26 cm tall. No text, logos or watermarks except the product's own label. Exactly one bottle. Natural hand, five fingers.",
     "image_urls": ["@c01-main", "@product-label", "@c02-benefits[1]"],
     "image_size": {"width": 1536, "height": 1536}, "num_images": 1, "output_format": "png"}}
]}
```

Enhanced-content banner for a 970x600 module: the 97:60 master, then `cardkit.py fit ... --size 970x600`. In a real set this job sits in the stage-3 file with the other cards (one batch, one cost gate); its file goes to `genmedia-output/<slug>/banners/` with a second `cardkit.py order --out-dir` call, not into the listing order.

```json
{"label": "zeytin-dali-cards", "max_parallel": 1, "jobs": [
  {"id": "b01-banner", "endpoint_id": "openai/gpt-image-2.5/sunburst/edit", "est_cost_usd": 0.12,
   "input": {"prompt": "image 1 is the real product on a white background; image 2 shows its label close up; image 3 is the approved card of this set: match its palette, type and icon style, not its words or its layout. {LOCK} Layout: a wide banner. The bottle stands on the right third, filling 80 percent of the height, on the set background. The other two thirds are calm background with the headline in large type and one subline under it, both inside the central 80 percent of the width. {SYSTEM} Render exactly these strings, each once, spelled exactly as written, in Turkish; keep every diacritic and the exact capitalisation: headline \"Ayvalık'tan sofranıza\"; subline \"Soğuk sıkım, erken hasat\". No other text anywhere: no extra labels, badges, seals, ratings, prices, watermarks or placeholder words. The only other lettering is the product's own label, unchanged. Exactly one bottle.",
     "image_urls": ["@c01-main", "@product-label", "@c02-benefits[1]"],
     "image_size": {"width": 1552, "height": 960}, "quality": "high", "background": "opaque", "num_images": 1, "output_format": "png"}}
]}
```

The SET SYSTEM paragraph opens with "square card"; for a banner replace those two words with "wide banner" and nothing else. Every headline here must come from the user: "Ayvalık'tan sofranıza" is on this banner because the user wrote it, not because it sounds right.

## Finish

```text
cardkit.py probe genmedia-output/zeytin-dali-cards/c03-inuse_0.png --expect 2000x2000
cardkit.py order --out-dir genmedia-output/zeytin-dali-cards/listing --item main=genmedia-output/zeytin-dali-cards/c01-main_0.jpg --item benefits=genmedia-output/zeytin-dali-cards/c02-benefits_1.png --item inuse=genmedia-output/zeytin-dali-cards/c03-inuse_0.png --item dimensions=genmedia-output/zeytin-dali-cards/c04-dimensions_0.png --item materials=genmedia-output/zeytin-dali-cards/c05-materials-r2_0.png --item howto=genmedia-output/zeytin-dali-cards/c06-howto_0.png --item inbox=genmedia-output/zeytin-dali-cards/c07-inbox_0.png
pipeline.py manifest --label zeytin-dali-cards
gm.py ledger --label zeytin-dali-cards --sum
```

`order` writes `01-main.jpg` to `07-inbox.png` plus `listing.json` and never overwrites a different file without `--replace`. `manifest` lists superseded attempts as well; explain them in the delivery (re-rolled, replaced by `-r2`) instead of hiding them. Then the final template in SKILL.md.
