# Troubleshooting cards

Symptom → cause → what to change. Text failures have their own procedure in `text-accuracy.md`; marketplace rejections are in `marketplaces.md` section 5; platform error types are in `platform.md` section 4. `cardkit.py`, `gm.py` and `pipeline.py` abbreviate the calls written in SKILL.md.

## 1. Difficult inputs

| Situation | Do |
|---|---|
| HEIC, HEIF, AVIF, TIFF, a CMYK JPEG, or a 40 MB photo | `cardkit.py convert <file> --out .genmedia/tmp/<name>.jpg` (sRGB JPEG, longest side 3000 px, aspect kept; needs `sips` or ffmpeg). Read the converted file, upload that copy. `kind: "tool_missing"` → ask the user to export a JPEG ("most compatible" on a phone). |
| The photo is only a URL | Save a local copy first and Read it. Never lock a product you have not looked at. A listing page is not a photo: ask for the image files. |
| Cluttered or dark phone photo | That is what stage 1 is for: the Pixelcut cut-out becomes image 1 of every card. When the cut-out itself is poor (section 4), ask for one photo on a plain surface near a window. |
| Several variants or several units in one photo | Ask which one the listing sells; crop to it (any tool the user has) or ask for a single-item photo. "Exactly one" in the lock string does not reliably remove the others. |
| The spec sheet is a PDF, a screenshot or a photo of the box | Read it, copy the values into `facts.json`, note the source under `sources`, and list the extracted values in the intake message so the user can correct them. A number you could not read clearly is left out, not guessed. |
| The user pastes a competitor's listing "for the specs" | Those are another product's facts. Use them for layout inspiration at most; every value still comes from the user about their own product. |
| The user gives facts in one language and wants cards in another | Translating a benefit is rewriting a claim. Propose the translation in the intake message and use it only after they confirm the wording. |
| Photos of people (model holding the product) | Consent question once. No yes → crop to the product or describe a generated person generically. |

## 2. The product drifts (fidelity)

| Symptom | Cause | Change |
|---|---|---|
| A nicer, different product: new cap, smoother shape, extra button | the prompt described the product richly, so the model drew the description | shorten the lock string to identity plus "exactly as in image 1"; make the product larger; product image first in `image_urls` |
| Label text on the pack is wrong or re-typeset | the label is too small in the master, or no close-up was given | label close-up as image 2; product at 70 percent of the card height; `label_suspect` in the read-back fails the card |
| The product took on the set palette (cream bottle turns olive) | SET SYSTEM colours read as product colours | add "the palette applies to background, type and icons only; the product keeps its photographed colours" |
| Two products, or a reflection that reads as a second one | layout left a large empty zone | "exactly one <product>"; fill the zone with the text column; remove mirrors and glossy floors from the layout |
| Wrong scale in the in-use card | no size in the prompt | give the height from `facts.json` and one scale anchor (a hand, a mug); no height in the facts → no scale scene |
| A view the photos never showed (back, inside, underside, cutaway) | the card type invited it | stay at the photographed angle; ask for another photo; materials cards say "no cutaway, no exploded view" |
| Kit card shows extra items | models complete kits with cables, manuals, pouches | "Exactly <n> items ... Nothing else is in the kit."; one reference photo per drawn item; items without photos are text rows |
| Hands: six fingers, fingers over the label | hard content | grip on the lower third, "label facing the camera and not covered"; or an open palm; or no hand |

Two re-rolls did not fix it → drop the card or choose the simpler layout of the same type (icon list instead of leader lines; product alone instead of a scene) and say so in the delivery. A better-looking wrong product is never delivered.

## 3. The set drifts (coherence)

| Symptom | Change |
|---|---|
| Card 5 has another typeface or icon style | the anchor must be the **last** entry of `image_urls` and named in the ROLE line; the SET SYSTEM paragraph must be byte-identical to `plan.md` (search the template for a paraphrase) |
| Colours wander from card to card | hex values plus colour names in the paragraph; "flat colours, no gradients"; do not describe scene lighting on graphic cards |
| Every card copies the anchor's layout | the ROLE line lacks "not its words or its layout"; give the card's own layout paragraph more detail |
| The anchor's words reappear on other cards | same clause; on a re-roll name the words: `do not write "Erken hasat"`; the read-back reports them as `extra` |
| Block names appear as text ("Headline", "Row 1", "TEXT") | the model drew the scaffolding | rewrite the TEXT block as sentences: `The headline reads "...". The first row reads "...".` |
| Too many references, muddy result | each extra image dilutes the others | product, label close-up, kit items that are drawn, anchor; nothing else |

## 4. Endpoint quirks

**`pixelcut/product-photo`**
- Returns base64 unless `"sync_mode": false` is sent. Always send it.
- Glass, clear plastic, fine mesh, white on white: edges vanish or the product looks pasted. Try `"shadow": {"type": "Generative"}` for grounding under a new id; still poor → ask for a photo on a mid-grey or coloured surface, which separates better than white on white.
- Nested `background.image_url` is not checked by the helper for unfilled `@` references. The main image uses `mode: "Color"`, so this matters only for custom backdrops.
- The output is the listing's first image: look at the corners and between handles or straps at full zoom for leftovers of the old background.

**`bria/product-dimensions`**
- `image` (not `image_url`): the helper cannot catch an unfilled `"@c01-main"` there. Always run the filled plan.
- `style` is required (`default`, `childlike`, `elegant`). `dimensions[].name` is one of `height`, `width_bottom`, `width_top`; depth and length are not offered. `unit`: `mm`, `cm`, `m`, `in`, `ft` and the quote-mark forms. `output_size` 256 to 2200, square only. `background`: a hex value or `white`, `cream`, `charcoal`.
- Measured on 2026-09-21 (`platform.md` section 10): the badges carry English words, `Capacity 500 ml` and `Net Weight 0.5 kg` (the `weight` label is an enum, `Weight` or `Net Weight`). On a non-English card leave both off or take route B of `card-types.md`.
- It draws the labels itself from numeric fields as `<value> <unit>` with a decimal point: `26.5 cm`, `26 cm`, `7 cm`. A decimal comma or custom wording cannot be requested (a non-integer value on a Turkish or German card → route B). `title` is typeset, not generated: Turkish letters came back right in mixed case and in caps. Output is a 2200x2200 opaque PNG at the default `output_size`. Check with `readback --numbers-only`, then look at which extent each line measures: `height` spans the whole product, cap included, and `width_top` sits over the cap; on irregular shapes (L-shaped, soft goods, handles) the automatic lines can measure the wrong span → route B.
- Its look is its own; only the background follows the set. Tell the user when that card looks different from the rest and offer route B.
- Never send `"sync": true` (base64 output).

**GPT Image 2.5 edit (Flare and Sunburst)**
- `image_size: "auto"` follows the input photo; always send the object. Sides are multiples of 16 (`marketplaces.md` section 3).
- `quality` defaults to `high`; `xhigh` and `max` multiply the price (about 2 and 4 times the `high` row). Use them only when the user agreed to the price, and they do not fix spelling.
- `background: "opaque"` on every card: `cardkit.py fit` does not flatten alpha, and a transparent card does not survive a JPEG copy cleanly.
- No `seed`: nothing can be "regenerated slightly". Every new job is a new roll of every letter.
- `mask_url` exists, but it does not protect the rest of the card: an opaque black-and-white mask broke the output and an RGBA mask still let the whole frame change (2026-09-21, `platform.md` section 10). Repairs are full edits, read back in full.

**Seedream 5.0 Pro edit (text-free scenes only)**
- Default `image_size` is `auto_2K`, which can cross the 1536x1536 area and double the price. Send the object.
- Roles are written "Figure 1", "Figure 2". It renders text when asked, but this skill does not rely on it for card text: no read-back guarantee has been established for it here.

## 5. Policy blocks and sensitive categories

- A black image, `has_nsfw_concepts: true` or `kind: "content_policy"`: never deliver, never resend unchanged, never disable the checker; assume it was billed.
- Usual causes on cards: body words in beauty and health copy ("skin", "intimate", "slimming"), before-and-after framing, weapons-adjacent tools (knives, axes), alcohol and tobacco, medicine-like packaging, children in in-use scenes. Re-describe plainly: product and surface first, no body close-ups, adults only, no effect on the body shown.
- Health, supplement, cosmetic-efficacy and child-safety statements are regulated almost everywhere. They go on a card only as the user's exact, provable wording, and the delivery says that the claim is theirs. "Clinically proven", cure or treatment language, and age-suitability marks are not drawn.
- A block on clearly benign content may be retried once on the other GPT Image tier or, for text-free scenes, on Seedream, and the user is told.

## 6. Resume and state

| Symptom | Do |
|---|---|
| New session, set half done | Read `plan.md`, run `pipeline.py urls --label <slug>`; continue at the first card without a passed read-back in the `## Log`. Never re-render a card that passed. |
| `"input_changed": true` on a completed id | The template was edited after the job ran. Restore it, or give the changed job a new id. |
| The anchor URL no longer loads (`file_download_error`) | CDN links expire. Upload the local anchor file again, `pipeline.py add --label <slug> --step anchor --path <file> --url <cdn_url>`, and reference `"@anchor"` in later templates. Same for `c01-main`. |
| The user rejects the main image at the anchor checkpoint (clipped part, leftover background) | Rerun it under a new id (`c01-main-v2`, section 4) and reference `"@c01-main-v2"` from then on. The anchor was built from the old cut-out: keep it only when the defect is not visible in it, otherwise render the anchor again under a new id and ask for approval again. |
| `manifest` lists problems for superseded attempts | Expected: failed or replaced ids stay in the ledger. Explain each in the delivery; do not delete ledger lines. |
| `readback` says `plan_invalid: card ... is not in the plan` | The re-roll id is not in `cards.json`. Pass the original card id to `--card`, or add the re-roll id with the same strings. |
| The user changes a fact after cards were made | Update `facts.json` and `cards.json`, rerun `cardkit.py text`, re-render only the cards that show that fact (new ids), read back, redo `order` with `--replace`. |

## 7. Cost surprises

- A re-roll template copied from the anchor still has `num_images: 2`: two images, double the price.
- A master above 3.7 MP moves to the top row of the cost table; 2000x2000 is already there. 1600x1600 is the budget master.
- Every reference image adds input tokens. Four references on seven cards can add a third to the set.
- `gm.py ledger --label <slug> --sum` is an estimate built from your own `est_cost_usd` values. The actual charge is on fal's billing dashboard.
- Worst case for the plan card: every text card re-rolled twice. Say "re-rolls extra, at most 2 per card" before starting, and report how many were used.

## 8. Named traps

The short list in SKILL.md Routing, spelled out.

- **New-roll trap.** This family has no `seed`: rendering a card again re-rolls every letter. A card that passed is never rendered again; a text repair is an edit of that card, followed by a full read-back.
- **Auto-size and default-quality trap.** The edit endpoints default `image_size` to `auto` (follows the input photo) and `quality` to `high` on a token-billed model. Send `{width,height}` and `quality` on every job.
- **Multiples-of-16 trap.** GPT Image sizes need both sides divisible by 16, 655,360 to 8,294,400 pixels, aspect at most 3:1. 1200x1800 and 970x600 are not legal: render the same-ratio master (1344x2016, 1552x960) and let `cardkit.py fit` scale it.
- **Invented-spec trap.** Infographic layouts attract filler pills ("BPA free", "100% natural", star rows, certification seals). Every prompt ends with the no-other-text clause, and any stray word found by the read-back fails the card.
- **Casing trap.** Never ask the model to uppercase Turkish. Write the final casing yourself (`cardkit.py text` returns a locale-correct `upper`).
- **Unguarded-field trap.** The helper refuses an unfilled `"@ref"` only in `*_url` and `*_urls` fields. Bria's `image` and Pixelcut's nested `background.image_url` have no such net: always `pipeline.py fill`, always run the filled file.
- **Pixelcut `sync_mode`.** It defaults to `true` there and returns base64. Always send `"sync_mode": false`.
- **Unseen side.** Cards invite new angles (back, inside, underside). Stay within what the photos show or ask for another photo.
