# Card types

Every card of a listing set: what it is for, which facts it needs, its layout in words, its prompt template and its text budget. Endpoints and fields were verified live on **2026-09-20**; the exact job JSON is in `batch-plans.md`. `cardkit.py` abbreviates `python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py"` as written in SKILL.md.

## 1. The two state files

Both live in `.genmedia/projects/<slug>/` and are written with the Write tool. They are the only source of on-card wording.

`facts.json`: what the user supplied. Every key is optional; a missing key blocks or thins a card, it is never filled in.

```json
{"product_name": "Zeytin Dalı Natürel Sızma Zeytinyağı 500 ml", "brand": "Zeytin Dalı",
 "marketplace": "trendyol", "language": "tr",
 "dimensions": [{"name": "height", "value": 26, "unit": "cm"}, {"name": "width", "value": 7, "unit": "cm"}],
 "weight": {"value": 950, "unit": "g"}, "capacity": {"value": 500, "unit": "ml"},
 "materials": ["koyu yeşil cam şişe", "alüminyum kapak"], "ingredients": [],
 "included": [{"item": "500 ml şişe", "qty": 1, "photo": "bottle-front.jpg"}, {"item": "Yedek kapak", "qty": 1, "photo": "kit-cap.jpg"},
              {"item": "Tarif kitapçığı", "qty": 1, "photo": null}],
 "benefits": ["Soğuk sıkım", "Erken hasat", "Asitlik 0,3", "Işık geçirmeyen cam şişe"],
 "how_to_use": ["Serin yerde sakla", "Çiğ tüket", "Kapağı sıkı kapat"],
 "variants": [], "certifications": [], "warranty": "", "origin": "Ayvalık, Türkiye", "care": [], "other_facts": [],
 "sources": {"benefits": "user message", "dimensions": "spec sheet the user attached"}}
```

`cardkit.py facts --file <facts.json>` answers `cards.possible`, `cards.blocked` (each with the fact it `needs`), `warnings` (kit item without a photo, certification handling, too few or too many benefits) and the list of `numbers` the facts contain. Keep the user's own wording and number formatting (`0,3`, `%100`): the card shows what they wrote.

`cards.json`: the copy deck. One entry per card; `headline` is optional; `label_strings` is the product's own label text from the PRODUCT LOCK, so the read-back can tell label text from stray text; a card may carry `allowed` for other lettering that legitimately appears (a brand name on a kit item).

```json
{"slug": "zeytin-dali-cards", "language": "tr",
 "label_strings": ["ZEYTİN DALI", "Soğuk Sıkım Natürel Sızma Zeytinyağı", "500 ml"],
 "cards": [
  {"id": "c01-main", "type": "main", "strings": []},
  {"id": "c02-benefits", "type": "benefits", "headline": "Neden Zeytin Dalı?",
   "strings": ["Soğuk sıkım", "Erken hasat", "Asitlik 0,3", "Işık geçirmeyen cam şişe"]}
 ]}
```

Who writes what: neutral section titles are yours to write in the card language ("Malzemeler", "Kutuda ne var?", "How to use"). Benefit statements, slogans, numbers, names of materials, steps and anything else that asserts something about the product are the user's words from `facts.json`; you may shorten them by dropping words, never rephrase them into a new claim.

Types: `main`, `benefits`, `inuse`, `dimensions`, `materials`, `howto`, `inbox`, `range`, `trust`, `banner`. That is also the default listing order; banners are delivered separately from the listing slots.

## 2. Text budget (enforced by `cardkit.py text`)

| Type | Strings (headline not counted) | Words per string | Characters per string | Words on the card |
|---|---|---|---|---|
| `main` | 0 | - | - | 0 |
| `benefits` | 5 | 4 | 28 | 26 |
| `inuse` | 2 | 5 | 32 | 14 |
| `dimensions` | 5 | 3 | 18 | 16 |
| `materials` | 4 | 4 | 28 | 24 |
| `howto` | 4 | 5 | 32 | 28 |
| `inbox` | 6 | 3 | 24 | 24 |
| `range` | 12 cells | 3 | 18 | 40 |
| `trust` | 3 | 4 | 28 | 18 |
| `banner` | 1 subline | 8 | 48 | 14 |

Headline on any card: 6 words and 36 characters at most. Over budget → drop words or move a string to another card; never reword a fact into something the user did not say. More text than the budget belongs in the listing's own text fields, where it is searchable.

## 3. Prompt skeleton

One English paragraph per card, blocks always in this order. The block names are for you; they are not sent.

```text
ROLE    image 1 is the real product on a white background; image 2 shows its label close up; image 3 is the approved
        card of this set: match its palette, type, icons, grid and callout style, not its words or its layout.
LOCK    {LOCK}       the lock string from plan.md, verbatim
CARD    <the layout paragraph of the card type, slots filled>
SYSTEM  {SYSTEM}     the SET SYSTEM paragraph from plan.md, verbatim
TEXT    Render exactly these strings, each once, spelled exactly as written, in <language>; keep every diacritic
        and the exact capitalisation: headline "<...>"; callout 1 "<...>"; callout 2 "<...>".
CLOSE   No other text anywhere: no extra labels, badges, seals, ratings, prices, watermarks or placeholder words.
        The only other lettering is the product's own label, unchanged. Exactly one <product>. Even studio light,
        true colours, square-on view.
```

- The anchor has no image 3; its ROLE line names only the product images.
- Image order: product references first, kit items next, the anchor last. "image N" must match the position in `image_urls`.
- Strings go in straight double quotes, in the listing's language, in their final casing. Nothing else in the prompt is in that language.
- Every text job sends `image_size` as an object, `quality: "high"`, `background: "opaque"`, `output_format: "png"`, `num_images: 1` (the anchor: 2).

## 4. The cards

### `main`: main image
- Purpose: the search-result image. Product alone, whole, on pure white. Needs only the photo.
- Route: `pixelcut/product-photo`, never a generative model. No prompt, no text. Default 2000x2000 JPEG, margin 8 percent so the product fills most of the frame, soft drop shadow (leave `shadow` out for none).
- Its output, `@c01-main`, is image 1 of every later card: a clean cut-out keeps a cluttered phone background out of the set.
- Pitfalls: clipped straps or handles, floor left between parts, a props-and-packaging photo (most marketplaces want the product only), transparent or glass items losing their edges (see `troubleshooting-cards.md`).

### `benefits`: benefit infographic (the anchor)
- Purpose: the three to five reasons to buy, readable in two seconds on a phone. Needs `benefits` (3 to 5).
- Layout: product large on the right half, turned as photographed. Headline top left. Benefits as a vertical icon list on the left, one line icon and one short label each. A leader line to the product only for a benefit that is a visible part (cap, handle, port); an abstract benefit ("cold pressed") gets an icon row, not a line pointing at nothing.
- CARD: `Layout: a square product infographic. The <product> stands on the right half, filling about 70 percent of the card height, on the set background. Top left: the headline. Below it, a left-aligned vertical list of <n> rows, each a small line icon and one short label; <row k: a thin leader line runs from its label to the <visible part>>. Generous spacing, nothing overlaps the product.`
- Pitfalls: filler pills and seals the model adds on its own; icons that depict something false (a leaf for a product that is not plant-based); a sixth benefit squeezed in.

### `inuse`: in use, or scale in context
- Purpose: show the size and the moment of use. Needs the photo; a caption only from a stated benefit or use.
- Layout: one believable scene, the product the largest sharp object, a hand or an everyday object for scale, an optional caption strip along the bottom in the set colours.
- Route: with a caption → GPT Image 2.5 Sunburst edit. No text at all → `bytedance/seedream/v5/pro/edit` at 1536x1536 (its base-price area), prompt roles written as "Figure 1", without the TEXT block. An approved still from `product-photoshoot` → pass it as the scene reference.
- CARD: `Layout: a square lifestyle card. Scene: <one sentence: place, surface, daylight>. The <product> is <in a relaxed adult hand | standing next to <everyday object>>, label facing the camera, true to scale: it is <height from facts> tall. A solid strip in the set's primary colour along the bottom 14 percent carries the caption.`
- Pitfalls: scale is a fact. No height in `facts.json` → no hand, no size comparison, neutral context only. Fingers over the label. A generated person: generic description, disclosed in the delivery.

### `dimensions`: size card
- Purpose: end returns caused by wrong size expectations. Needs `dimensions` with units.
- Route A, `bria/product-dimensions`: square card, up to three measures (`height`, `width_bottom`, `width_top`), optional `weight` and `capacity` badges, `title` up to 80 characters, `background` as the set's hex. The numbers are typed fields, not prompt text. It formats labels itself as `<value> <unit>` with a decimal point (`26.5 cm`, measured 2026-09-21), so check it with `cardkit.py readback ... --numbers-only` and read units and title by eye; the title is typeset and keeps Turkish letters. A non-integer value on a comma-decimal card (Turkish, German: `6,5 cm`) → route B, because a decimal point there is wrong text. Its badges print English words (`Net Weight 0.5 kg`, `Capacity 500 ml`): on a non-English card leave `weight` and `capacity` off or take route B. Depth and length are not offered.
- Route B, GPT Image 2.5 Sunburst edit: depth or length, a size table, a non-square card, decimal commas, or the exact set look.
- CARD (route B): `Layout: a square dimensions card. The <product> stands centred on the set background, square-on. Thin dimension lines with short end ticks sit outside its silhouette: one vertical line on the left spanning its full height, one horizontal line below spanning its full width<, one ...>. Each line carries exactly one label. Do not add other units, conversions or measurements.`
- Pitfalls: a line that spans the wrong extent (body without cap); the same number twice; inches added unasked; a digit swapped. Every digit is read back; `digit` failures are never delivered.

### `materials`: materials, ingredients, what is inside
- Purpose: what it is made of. Needs `materials` or `ingredients`.
- Layout: the product or a close view that the photos really show, two to four callouts with leader lines to the named part, headline on top.
- CARD: `Layout: a square materials card. The <product> fills the centre, seen from the same angle as image 1. <n> callouts with thin leader lines point to: <part 1>, <part 2>. No cutaway, no exploded view, nothing the reference photos do not show.`
- Pitfalls: invented cross-sections and inner layers; a full ingredient list (it does not fit: four strings here, the list goes in the listing text); purity claims the user did not make.

### `howto`: how to use
- Purpose: remove doubt about use or setup. Needs `how_to_use` (2 to 4 steps).
- Layout: a row or a 2x2 grid of equal panels, a large step numeral in each (drawn by the layout, not part of the strings), one line icon or one simple product view, the step label under it.
- CARD: `Layout: a square how-to card with <n> equal panels in <a row | a 2x2 grid>, numbered 1 to <n> with large numerals in the set's primary colour. Panel k shows <a single line icon of <action> | the <product> <state>> above its label. Same icon style in every panel.`
- Pitfalls: hands and people in every panel (each one can fail); steps out of order; a step the user never gave. The read-back ignores bare step numerals on this type only.

### `inbox`: what is in the box
- Purpose: set expectations of the kit. Needs `included`.
- Layout: a tidy top-down arrangement on the set background, every item separate, a short label under each ("1 x <item>").
- Rule: an item is drawn photoreal only from the user's photo of it (add each as a reference; GPT Image takes up to 16). An item without a photo becomes a text row with a plain line icon, never an invented object.
- CARD: `Layout: a square kit card, top-down, even light. Exactly <n> items, separated by clear gaps: <item 1 from image 1>, <item 2 from image 3>. Under each item its label. <Below them, a text list with a plain line icon per row for: <items without photos>.> Nothing else is in the kit.`
- Pitfalls: bonus items (cables, manuals, pouches) the model adds; wrong count; packaging the user did not mention.

### `range`: own-range comparison
- Purpose: help choose between the user's own variants. Needs `variants` (2 or more), ideally a photo of each.
- Layout: variants side by side in equal columns, a small table under them: up to 4 rows, 12 cells in total, each cell at most 3 words.
- Rule: the user's own products only. No competitor, no "others" column, no ticks against crosses, no unnamed rival. Marks of other brands never appear.
- CARD: `Layout: a square comparison card with <n> equal columns. Column k: the variant from image k on top, its name under it, then <r> short rows. Thin rules between rows, no ticks, no crosses, no winner highlight.`
- Pitfalls: the most text-dense card, so the likeliest to fail the read-back: keep cells to numbers and single words, or plan the text-free route from the start. One variant photographed, the others described → only the photographed one is shown; the rest are table text.

### `trust`: trust card
- Purpose: warranty, origin, certification, return terms the user can prove. Needs at least one of `warranty`, `certifications`, `origin`, `other_facts`.
- Layout: product small on one side, two or three statements, each with a plain line icon.
- Rule: a certification is its name in plain words. No seals, laurels, ribbons, stars, flags dressed as badges, "official" emblems or review counts, and no mark of a certifying body unless the user supplies the artwork and confirms the licence (then it is a reference image, checked like a label).
- CARD: `Layout: a square trust card. The <product> sits on the right third. On the left, <n> rows, each a plain line icon and one statement. Calm, factual, no badges or seals of any kind.`
- Pitfalls: `claim_word` warnings from `cardkit.py text` are all relevant here; drop anything the user cannot back up.

### `banner`: enhanced-content banner
- Purpose: wide module for brand or enhanced-content areas ("A+" on Amazon, store pages elsewhere). Needs `product_name` and a benefit or the brand.
- Layout: product on one third, a calm two-thirds for a headline of at most 6 words and an optional subline. Large type: these modules are scaled down on phones.
- Sizes: the master of the module's ratio from `marketplaces.md` (1552x960 for a 970x600 module, 1952x800 for 1464x600), then `cardkit.py fit`.
- CARD: `Layout: a wide banner. The <product> stands on the <left | right> third, filling 80 percent of the height. The other two thirds are calm set background with the headline in large type and one subline under it, both inside the central 80 percent of the width.`
- Pitfalls: long sublines; text near the edges (modules are cropped differently on mobile); a module that has its own text fields: keep baked text to the headline and put the copy in the fields.
