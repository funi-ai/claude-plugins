---
name: marketplace-cards
description: >-
  Listing-image SETS for one product (Amazon, Trendyol, Hepsiburada, Etsy, Shopify) from the user's REAL photos and facts: main packshot, benefit infographic, dimensions, materials, how-to, in-use, what's-in-the-box, trust card, A+ banners. Text baked in by GPT Image 2.5 edit and read back letter by letter; packshot by Pixelcut, dimensions by Bria.
  Use when: "listing images for my product", "Amazon infographic with callouts", "A+ content banners", "what's in the box image", "pazaryeri görselleri hazırla", "Trendyol için ürün görselleri", "ürün özellik infografiği yap", "Hepsiburada görsel seti".
  Chain: consumes approved stills from `product-photoshoot`; produces ordered listing files and a manifest.
  NOT for: text-free lifestyle or campaign shoots (use `product-photoshoot`); ad creatives (use `ads`); posters (use `image`); logos (use `brandkit`); app store screenshots (use `launch-graphics`); product videos (use `video`); campaigns (use `pipelines`); model choice (use `models`); setup problems (use `setup`).
argument-hint: "[product photo paths] [marketplace] [facts or spec sheet] [--slug <project>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py" *) Bash(command -v genmedia) Bash(genmedia models *) Bash(genmedia schema *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 with a fal key configured by the user, and python3 >= 3.8. Local ffmpeg or macOS sips is optional (exact delivery sizes, JPEG copies, HEIC conversion, zoom tiles of JPEG files).
---

# Marketplace cards

One product, one coordinated image set for its listing: facts sheet, product lock, set plan, main image, one approved anchor infographic, then every other card locked to that anchor and checked word by word. Two non-negotiables. **Product fidelity:** every card is conditioned on the user's real photos through an edit or compositing endpoint; text-to-image never draws the product. **Text is a deliverable:** every string is sent verbatim in quotes and read back from the output character by character; a card with a wrong letter is a failed card.

## Step 0 — Preflight

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py" tools
```

- `blockers` not empty, CLI missing or older than 0.7.0 → `/genmedia-skills:setup`. Key missing → the user runs `genmedia setup` or exports `FAL_KEY` themselves; wait. Never read, print, request or type a key.
- Keep `config.announce_above_usd` and `config.confirm_above_usd` (defaults 0.50 and 2): they are the cost gate.
- `cardkit.py tools` says whether `fit` (exact sizes, JPEG copies) and `convert` (HEIC and other phone formats) can run here. `facts`, `text`, `contrast`, `readback`, `probe`, `order` and `tiles` on PNG need no tool. Never plan on Pillow, ImageMagick or `drawtext`: text is rendered by the model or set by the user in a design tool.
- Resume first: Glob `.genmedia/projects/*/plan.md`. A plan for this product exists → read it, run `python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" urls --label <slug>`, continue at the first unfinished step. Never restart a set that has ledger entries.

## UX rules

1. Reply in the user's language (Turkish in → Turkish out). Model prompts are English; on-card strings stay in the listing's language, verbatim, in quotes. IDs, fields and paths stay as they are.
2. No JSON, request IDs, prompts or tool narration in chat. Wait silently; one status line per batch at most.
3. **Question budget: ONE consolidated intake message** (template under Delivery), sent after you looked at the photos. It lists only what is missing, grouped by the card it unlocks, each line with its default or "left off". Defaults: marketplace → generic (square 2000x2000, white main image); card language → the language the user writes in (Trendyol, Hepsiburada → Turkish); set → every card the facts allow, in listing order, 8 at most; look → derived from the product. No product photo → that is the only blocker: the same single message asks for the photos (2 to 3: front, label close-up, each kit item) and lists the facts, without its first line. Whatever the user leaves unanswered is left off the cards, never guessed and never asked again. Not counted: consent, cost confirmation, the anchor approval.
4. **Facts come from the user only:** their messages, a spec sheet or listing they point to, and text legible on the product in their photos. Never from model knowledge, the category or "typical values". Everything lives in `facts.json`; a string that is not backed by it does not go on a card.
5. Two hard stops: the plan when the cost gate says confirm, and **the anchor card, always**. Silence or a successful job is not approval.
6. Cost gate on the whole set: under announce → run; between → one-line estimate and run; at or above confirm → wait for a yes. Never swap a model the user named to get under a threshold; offer fewer cards or 1600 px instead.
7. Re-roll budget: 2 per card (3 attempts), and the prompt changes each time (spelled-out string, larger type, fewer callouts, shorter string). After that: the text-free route, said honestly. Wrong or garbled text is never delivered. Re-rolls inside the budget need no approval; report their cost.
8. No ratings, reviews, "best seller", "#1", prices, discounts, award or press badges, medical or regulatory claims, even on request. A certification is written as plain words the user supplied; its mark is never drawn unless the user supplies the artwork and confirms the licence. Comparison charts show the user's own variants only, never a named competitor, its marks or a thinly veiled "Brand X". The product's own marks stay as photographed; a generated person is described by age range and styling, never as a real or famous person, and is disclosed in the delivery; a real person's photo needs the user's confirmation of consent. Uploads sit on public URLs: say so once before uploading unreleased products.

## Discovery guardrail

`references/routing-image.md` (tasks `image-edit`, `product-shot`, `image-multiref`; GPT Image 2.5 cost table under `t2i-typography`) is a dated cache, verified 2026-09-19. `bria/product-dimensions` is not in that cache; it was verified active with the fields in `references/batch-plans.md` on 2026-09-20. Before the plan card is shown, confirm every endpoint in it:

```bash
genmedia models --endpoint_id <id1>,<id2>,<id3> --status all --limit 50 --json
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
```

- Every ID must be `active`; otherwise take the next tier of that task in `references/routing-image.md`, else `genmedia models "<name>" --no-classify --limit 10 --json`, newest active match, and say which model ran.
- Field names, enums and limits come from the schema, never from memory. They differ per family: `image_urls` (GPT Image, Seedream), `image_url` (Pixelcut), `image` (Bria dimensions).
- Never invent IDs or fields. Never `genmedia run` without an endpoint ID. New releases sit under vendor namespaces (`openai/`, `bytedance/`, `bria/`, `pixelcut/`), not only `fal-ai/`.

## Routing

First match wins. Layout, template and text budget per card: `references/card-types.md`. Prices are hints dated 2026-09-20; `gm.py price` decides.

| Card | Endpoint | Why | Price hint |
|---|---|---|---|
| Main image: product alone on pure white | `pixelcut/product-photo` | non-generative compositor: the listing shows the real item, nothing can drift | ~USD 0.024/image |
| Anchor: the first infographic, where the look is explored | `openai/gpt-image-2.5/flare/edit`, `quality: "high"`, 2 candidates | typography leader, fast tier; product photos go in `image_urls` (max 16) | ~USD 0.10 each at 2000x2000 |
| Every other card with text, banners, re-rolls, text repairs | `openai/gpt-image-2.5/sunburst/edit`, `quality: "high"` | precision tier for small type; same token rates | same |
| Dimensions: height, top and bottom width, weight, capacity, square card, values it can print as the user wrote them | `bria/product-dimensions` | measurements go in as typed fields, not prompt text; its weight and capacity badges print English words | ~USD 0.04/image |
| Dimensions with depth or length, a size table, a non-square card, a decimal value on a comma-decimal card (Turkish `6,5 cm`: Bria's number format cannot be set), or the exact set look | `openai/gpt-image-2.5/sunburst/edit` | numbers in quotes, every digit read back | as above |
| In-use or scale scene with no text at all | `bytedance/seedream/v5/pro/edit` at its base-price master (1536x1536 for a square set; sizes per ratio in `references/marketplaces.md`) | arena #1 E-commerce (2026-09-18); flat price | ~USD 0.07/image; above a 1536x1536 area the price doubles |
| Text-free card with reserved panels (alternative route) | `openai/gpt-image-2.5/sunburst/edit` | holds a described grid and leaves panels empty | as above |
| Exact pixel size, JPEG copy, listing-order names | `cardkit.py fit`, `cardkit.py order` | local and free | USD 0 |

Tie-breakers:

1. Any baked text → GPT Image 2.5 edit, even on a photoreal in-use card. Text cards always run at `quality: "high"`: letters are the deliverable, and `medium` saves cents but costs re-rolls.
2. Non-generative beats generative: the main image never goes through a generative model.
3. The user named a model → use it after the live check and mention the default in one line. A model without an image-reference input cannot make product cards: say so, do not route around the fidelity rule.
4. Approved stills of this product from `/genmedia-skills:product-photoshoot` (`.genmedia/projects/*/manifest.json`) → use them as the scene reference of the in-use card and banners instead of inventing a new scene.
5. No product photo → ask. The user has none → this is concept art: hand to `/genmedia-skills:image` and say the result will not be their product.
6. Budget pressure → fewer cards or 1600x1600, never another model for the text.

Named traps (each explained in `references/troubleshooting-cards.md` section 8): no `seed`, so a card that passed is never rendered again and a text repair is an edit of it; send `{width,height}` and `quality` on every job; GPT Image sides are multiples of 16 (render the master, `cardkit.py fit` scales it); no filler claims, stray words fail the read-back; never ask the model to uppercase Turkish (`cardkit.py text` gives `upper`); Bria's `image` and Pixelcut's `background.image_url` are not checked for unfilled `"@ref"`, so always `pipeline.py fill`; Pixelcut needs `"sync_mode": false`; stay within the photographed sides.

## Workflow

1. **Look first.** Read every product photo with the Read tool. HEIC, AVIF, TIFF, CMYK or huge files → `python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py" convert <file> --out .genmedia/tmp/<name>.jpg` first, then Read and upload that copy. Pick the primary reference (sharp, frontal, label readable) and up to two supporting ones. Pick a slug (`zeytin-dali-cards`): it is the batch `label`, the ledger filter, `genmedia-output/<slug>/` and `.genmedia/projects/<slug>/`. A natural-language label also works; the helpers transliterate Turkish letters.
2. **Facts sheet.** Write what the user already gave to `.genmedia/projects/<slug>/facts.json` with the Write tool (schema: `references/card-types.md`), then:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py" facts --file .genmedia/projects/<slug>/facts.json
   ```
   `cards.possible` is the set you can build now; `cards.blocked` names the fact each missing card needs. Send the one intake message, merge the answer into `facts.json`, run `facts` again. Still blocked → that card is left off. Never ask twice. Photos and "go" with no facts at all → the set is `main`, a caption-free `inuse` and whatever the pack's own legible text backs (a capacity, a material); the plan card lists every card left off and the fact it needs.
3. **PRODUCT LOCK** into `.genmedia/projects/<slug>/plan.md`: type and form, proportions, materials, colours, **label text verbatim line by line**, count, what must never change, which sides are unseen. Format and the one-paragraph English lock string: `references/set-system.md`.
4. **Copy deck.** Write every on-card string to `.genmedia/projects/<slug>/cards.json` (one entry per card: `id`, `type`, `headline`, `strings`; top-level `language` and `label_strings` from the lock). Strings come from `facts.json` only, inside the text budget of the card type. Then:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py" text --plan .genmedia/projects/<slug>/cards.json --facts .genmedia/projects/<slug>/facts.json
   ```
   Fix every `issues` entry: over budget → drop words, never change a fact; `number_not_in_facts` → the number goes or the user confirms it; `claim_word` → keep only if the user stated it. Writing rules: `references/text-accuracy.md`.
5. **SET SYSTEM, chosen once:** palette (from the product), type style, icon style, grid, callout style, written as one fixed English paragraph in `plan.md` (`references/set-system.md`). Check every text colour on its background:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py" contrast "#1E1E1E" "#F6F1E7"
   ```
   `ok: false` (below 4.5:1) → darken or lighten until it passes. The accent is for icons and highlights, not for text.
6. **Set plan card.** One row per card: listing position, card, size, endpoint, references, estimated cost. Verify every endpoint (Discovery guardrail), then price them in one call:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price pixelcut/product-photo,openai/gpt-image-2.5/flare/edit,openai/gpt-image-2.5/sunburst/edit,bria/product-dimensions --explain
   ```
   Dollars per card and dated set totals: `references/batch-plans.md` section "Pricing a set" (GPT Image 2.5 answers `1 units`, which is not a price). Two sources disagree → quote the higher; re-rolls are extra.
   Save the card to `plan.md`, show it (Delivery), apply the cost gate. Waiting for a yes is a hard stop: no uploads, no submits.
7. **Upload and register** the references once:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload ./bottle-front.jpg ./bottle-label.jpg
   python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" add --label <slug> --step product --path ./bottle-front.jpg --url <cdn_url>
   ```
   One step name per file (`product`, `product-label`, `kit-cable`); plans reference them as `"@product"`.
8. **Main image.** Write `.genmedia/projects/<slug>/stage-1-main.tmpl.json` (job `c01-main`, plan in `references/batch-plans.md`) with the Write tool, fill it, run it with a 600000 ms Bash timeout (the helper polls up to 540 s):
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" fill --template .genmedia/projects/<slug>/stage-1-main.tmpl.json --out .genmedia/projects/<slug>/stage-1-main.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/stage-1-main.json
   ```
   `status: "pending"` → run the same batch command again; it resumes by label and id and never pays twice. Read the result: edges clean, nothing clipped, pure white, product fills most of the frame. It is the listing's first image and, as `"@c01-main"`, the clean product reference of every card.
9. **Anchor card** (`c02-benefits`, stage 2; no `benefits` card in the set → the first card with text in listing order is the anchor; no text card at all → no SET SYSTEM and no anchor stop: main image, scene, QA, deliver): Flare edit, `num_images: 2`, prompt = role line + lock string + layout + SET SYSTEM + TEXT block + no-other-text clause (`references/card-types.md`). Same `fill` and `batch` calls. Run step 11 on both candidates (one seen file each: `seen-c02-benefits_0.txt`, `seen-c02-benefits_1.txt`), withhold a failing one, send the anchor checkpoint and **stop**. Both fail the read-back → re-roll as `c02-benefits-r2` on Sunburst with `num_images: 1` and the changed prompt (the anchor is then `@c02-benefits-r2`); still failing after the budget → show one for the look only, name the wrong word, and render card 2 again on Sunburst in stage 3 with that candidate as the style reference. Look rejected → change picks in `references/set-system.md`, not just wording, and render a new id (`c02-benefits-v2`).
10. **Lock, then the remaining cards as ONE batch.** The user picked candidate n → record `Anchor: @c02-benefits[n-1]` (outputs are 0-based) and the final SET SYSTEM paragraph in `plan.md`. Write `stage-3-cards.tmpl.json` from the worked plan in `references/batch-plans.md`: every card gets the product references first, the anchor last in `image_urls`, the lock and SET SYSTEM paragraphs verbatim, its own TEXT block and the role line ("image 1 and 2 are the real product; image 3 is the approved card of this set: match its palette, type, icons, grid and callout style, not its words or its layout"). `fill`, then `batch` as in step 8 (`max_parallel` = number of jobs, 12 at most). A placeholder that reaches the model is a wasted card, so `fill` refuses one that survived and names the JSON path of every hit.
11. **QA per card, before anything is shown.** Order matters:
    ```bash
    python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py" tiles genmedia-output/<slug>/c05-materials_0.png
    python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py" readback --plan .genmedia/projects/<slug>/cards.json --card c05-materials --seen-file .genmedia/projects/<slug>/seen-c05-materials.txt
    python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py" probe genmedia-output/<slug>/c05-materials_0.png --expect 2000x2000
    ```
    (a) Read the tiles and write down every piece of text you see, one string per line, **before** looking at the expected strings again (Write tool → `seen-<id>.txt`); (b) `readback` compares them character by character and exits 1 on any difference, missing string or stray text; (c) fidelity against the lock (shape, label, colour, count, no invented parts); (d) every number and claim is in `facts.json`; (e) palette, type and icon style match the anchor; (f) pixel size as planned (`probe`). Verdict: pass, re-roll (new id `c05-materials-r2`, same label, changed prompt per `references/text-accuracy.md`), or the text-free route after 2 re-rolls. Procedure and repair moves: `references/text-accuracy.md`.
12. **Finish and deliver.** Exact sizes and JPEG copies where the marketplace wants them (`references/marketplaces.md`), then listing-order names, manifest and spend:
    ```bash
    python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py" fit genmedia-output/<slug>/c03-inuse_0.png --size 1200x1800 --out genmedia-output/<slug>/fit/c03-inuse.jpg
    python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py" order --out-dir genmedia-output/<slug>/listing --item main=genmedia-output/<slug>/c01-main_0.jpg --item benefits=genmedia-output/<slug>/c02-benefits_1.png
    python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" manifest --label <slug>
    python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --label <slug> --sum
    ```
    `fit` never crops (a crop can cut text): a ratio mismatch is an error, render the right ratio instead. No local tool → deliver the masters and state their sizes. `manifest` exits 1 while `problems` is not empty: resolve or explain each one. Append the outcome to `plan.md`.

`plan.md` is the set's memory; keep these lines greppable:

```text
# Cards: <product>   slug: <slug>   marketplace: <name>   language: <code>   status: proposed | approved | anchor-approved | delivered
PRODUCT LOCK ... (block from references/set-system.md)
Lock string: <one paragraph, English>
SET SYSTEM: <one paragraph, English>
Anchor: pending | @c02-benefits[0] | @c02-benefits[1]
<the plan card table and Assumptions>
## Log
- <timestamp> v1 proposed, about USD 1.00 | anchor approved: candidate 2 | c05 re-roll 1: "Soğuk sıkım" lost the breve → spelled out, type larger
```

## Delivery

Intake message (the one question round; drop every line you already know):

```
I looked at your photos: <one line: what the product is, what the label says>.
To build the full set I still need (skip any line and that card or detail is left off; I never fill in specs myself):
- Dimensions and weight (dimensions card): e.g. height x width x depth, unit
- 3 to 5 benefit statements in your words (benefit infographic)
- Materials or ingredients (materials card)
- What is in the box, item by item (what's-in-the-box card; a photo of each item if you have one)
- How to use it, 3 to 4 short steps (how-to card)
- Warranty, certifications, origin: only what you can prove (trust card)
- Your other variants, if you want a range chart
<Trendyol, Hepsiburada or another moderated marketplace only:> - Does your category accept images with text on them? No answer: I plan the full set and flag that text cards may be refused there
Marketplace: <default or named> · card language: <code> · reply "go" to start with what I have.
```

Plan card (before spending):

```
Card set "<product>" for <marketplace>, v<n>: <k> cards, about $<total> (estimate; re-rolls extra, at most 2 per card)
| # | Card | Size | Model | Text on card | Est. |
| 1 | Main image, pure white | 2000x2000 | Pixelcut | none | USD 0.03 |
| 2 | Benefit infographic (anchor, 2 candidates) | 2000x2000 | GPT Image 2.5 Flare edit | "<headline>" + <n> callouts | USD 0.26 |
Left off: <card: the fact it needs>
Assumptions: <marketplace, language, sizes and every default you chose>
Product lock: <type; label text "…"; never change: …>
I make the main image and the first infographic, then stop for your approval of the look. <below the confirm threshold: Starting now. | at or above it: Reply "go" to start, or tell me what to change.>
```

Anchor checkpoint:

```
Main image: genmedia-output/<slug>/c01-main_0.jpg
First card of the set, 2 candidates:
1. genmedia-output/<slug>/c02-benefits_0.png
2. genmedia-output/<slug>/c02-benefits_1.png
Text check: every word matches what you gave me, letter by letter <or: candidate 2 withheld, "Soğuk" came out as "Soguk">.
The remaining <n> cards copy this palette, type, icon and callout style. Pick 1 or 2, or tell me what to change. Spent so far: about $<est_cost_usd_completed>.
```

Final:

```
Done: <k> listing images for "<product>" in genmedia-output/<slug>/listing/
01-main.jpg · 02-benefits.png · 03-inuse.png · ... (upload in this order)
Text check: all <n> strings read back identical to your wording. <or: card 6 is delivered text-free with copy.md, because "<string>" failed 3 times: set the text in a design tool.>
Manifest: .genmedia/projects/<slug>/manifest.json   Gallery: <gallery_url>
CDN links per file are in the manifest: public to anyone who has them, may expire; the local files are your copies.
<only if a generated person appears: The person in <files> is AI-generated; disclose it where the platform requires.>
Models: <display names>. Estimated spend: about $<est_cost_usd_completed>, including <r> re-rolls. Left off: <card and the fact it needed | none>.
Marketplace basics I followed are commonly cited, not guaranteed: check <marketplace>'s current image rules before uploading.
```

Translate the templates; keep paths, IDs, numbers and on-card strings as they are.

## Errors

| Signal (verbatim) | Action |
|---|---|
| `"status":"pending"` with `resume` | Run the same `gm.py batch --plan` again (600000 ms timeout). Never resubmit. |
| `input.image_urls: '@c01-main' is not a URL`, `input.image_url: '@product' is not a URL` (exit 2, nothing sent) | The template was run unfilled. `pipeline.py fill`, then the filled plan. Bria's `image` field gives no such warning: it would be submitted and billed. |
| `pipeline.py fill`: `"unresolved"` lists a reference | That job or registered file does not exist or did not complete. Finish it or `pipeline.py add` the file; never paste a guessed URL. |
| `"kind":"validation"` with `"fields":[]` and a `hint` | The queue hides the reason. Check in order, change the first thing that is off: fields and values against the OpenAPI schema (sizes divisible by 16, `dimensions[].name` enum, array vs string) → input files (format, size, expired URL: re-upload) → prompt (a real brand or person, a policy term). Rerun with `--retry-failed`. Max 3 attempts. |
| A validation error on `image_size` (`multiple_of`, `less_than_equal`, `greater_than_equal`) | Illegal GPT Image size. Use the masters in `references/marketplaces.md`. |
| `"kind":"content_policy"`, or a black image | Do not deliver, do not resend unchanged, never disable the safety checker. Re-describe plainly (`references/troubleshooting-cards.md`). Assume it was billed. |
| `cardkit.py readback`: `"kind":"check_failed"` | The card failed. Follow each entry's `repair` line, re-roll under a new id inside the budget, read back again. Never deliver it, never "fix" the expected strings to match. |
| `cardkit.py`: `"kind":"tool_missing"` | No ffmpeg and no `sips`. Deliver the master files, state their pixel sizes, say the resize was not done. |
| `"input_changed":true` | A completed id was edited. Restore the plan, or re-roll under a new id. |
| `"kind":"auth"` | Stop every stage. The user fixes the key or balance. |

More: `references/troubleshooting-cards.md`. Platform error types: `references/platform.md` section 4.

## This skill does NOT

- Invent or "round" a spec, dimension, ingredient, certification, award or benefit, or accept one from a web search. Unknown means left off.
- Draw the product from a description, or improve its design, label or colours.
- Draw text locally or promise pixel-exact typography. When the model cannot render a string in 3 attempts, it delivers a text-free card with reserved panels plus `copy.md`, and says the text must be set in a design tool.
- Compare against competitors, show ratings, reviews, prices, discounts or seals, or guarantee that a marketplace accepts the images.
- Shoot text-free lifestyle campaigns (use `/genmedia-skills:product-photoshoot`) or ad creatives (use `/genmedia-skills:ads`), design logos (use `/genmedia-skills:brandkit`), make product videos (use `/genmedia-skills:video`), or upload to any marketplace.

## Common mistakes

- Transcribing the card while looking at the expected strings: you will read what you expect. Write down what is there first, compare second.
- Accepting "close": `Soguk` for `Soğuk`, `IÇINDEKILER` for `İÇİNDEKİLER`, `0.5 L` for `0,5 L`. One character is a fail.
- Six callouts and a paragraph on one card. Text budget first; a second card beats a crowded one.
- Paraphrasing the lock or the SET SYSTEM per card. They are pasted verbatim; only layout and TEXT change.
- Generating the whole set before the anchor is approved, then discovering the look is wrong seven cards later.
- Rendering a passed card again "for consistency": every letter is re-rolled.
- Putting the anchor first in `image_urls` and calling it the product. Product references first, the anchor last, as a style reference only.
- Filling gaps with plausible specs, or lifting them from a similar product's listing.
- Cropping a card to reach a marketplace size instead of rendering the right ratio.

## Reference index

- `references/card-types.md`: read when planning the set and writing any card prompt; `facts.json` and `cards.json` schema, the prompt skeleton, and per card type: purpose, facts it needs, layout in words, template with PRODUCT LOCK, SET SYSTEM and TEXT slots, text budget, pitfalls.
- `references/set-system.md`: read when writing the PRODUCT LOCK, choosing the SET SYSTEM (palette, type, icons, grid, callouts), checking fidelity and set coherence, or when the user rejects the anchor look.
- `references/text-accuracy.md`: read when writing on-card strings, for Turkish specifics, the read-back procedure, the repair moves per failure class, and the text-free route with `copy.md`.
- `references/batch-plans.md`: read when writing any stage plan; one complete worked set (main, anchor, remaining cards as one batch, re-roll, text-free fallback) with verified endpoint IDs, exact input fields and the cost math.
- `references/marketplaces.md`: read when choosing sizes, ratios and card order for Amazon, Trendyol, Hepsiburada, Etsy or a Shopify store; labelled basics only, with the legal master size per ratio.
- `references/troubleshooting-cards.md`: read when inputs are difficult, a card drifts from the product or the set, text keeps failing, Bria or Pixelcut misbehave, a marketplace rejects an image, or costs surprise.
- `references/routing-image.md`: read when another tier is needed, an ID is not active, or for the dated GPT Image 2.5 cost table.
- `references/cli-contract.md`: read when a helper call fails, a job is pending, or you need batch plan keys, `wait`, `cancel`, the ledger, the gallery or the raw CLI.
- `references/platform.md`: read when estimating cost, reacting to a platform error type, or explaining URL privacy, billing and safety.
- `scripts/gm.py`: the shared helper (`preflight`, `price`, `upload`, `run`, `wait`, `cancel`, `batch`, `ledger`).
- `scripts/pipeline.py`: project state (`urls`, `fill`, `add`, `fetch`, `manifest`); resolves `@job` references and writes the manifest.
- `scripts/cardkit.py`: local, free, no network: `tools`, `facts`, `text`, `contrast`, `tiles`, `readback`, `probe`, `fit`, `convert`, `order`; one JSON object per call, exit 0 ok, 1 failed, 2 usage.
