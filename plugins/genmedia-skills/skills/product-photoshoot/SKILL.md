---
name: product-photoshoot
description: >-
  Product photography from the user's REAL product photos: packshot, lifestyle, flat lay, hero banner, in-hand, detail, seasonal, text-free ad-ready variants, try-on. Never re-imagined from text: every shot is reference-conditioned (Seedream 5.0 Pro, GPT Image 2.5, Pixelcut, Bria, FASHN).
  Use when: "product photos for my store", "packshot on white", "lifestyle shots of this bottle", "put this dress on a model", "ürün fotoğrafı çek", "ürünümü beyaz fonda göster", "ürünüm için görsel hazırla", "e-ticaret sitem için ürün çekimi".
  Chain: consumes @handle models from `character`; produces approved stills for `ads`, `marketplace-cards`, `short-video`, `video`.
  NOT for: images without a product photo, one quick edit (use `image`); ads with copy, UGC, ad videos (use `ads`); listing sets, infographics (use `marketplace-cards`); product clips (use `video`); logos, meshes (use `brandkit`, `3d`); model identity (use `character`); batches (use `pipelines`); model choice (use `models`); setup problems (use `setup`).
argument-hint: "[product photo paths] [channel or shot list] [--slug <project>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" *) Bash(command -v genmedia) Bash(genmedia models *) Bash(genmedia schema *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 with a fal key configured by the user, and python3 >= 3.8.
---

# Product photoshoot

A staged photoshoot for a product the user already has photos of: intake, product lock, shot plan, one approved hero, then the rest of the set locked to that hero, checked image by image before delivery. **Prime rule: product fidelity.** The product's shape, label, colours and count come from the user's photos through an edit, multi-reference or compositing endpoint. A text-to-image endpoint never draws the product.

## Step 0 — Preflight

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
```

- `blockers` not empty, CLI missing or older than 0.7.0 → `/genmedia-skills:setup`. Key missing → the user runs `genmedia setup` or exports `FAL_KEY` themselves; wait. Never read, print, request or type a key.
- Keep `config.announce_above_usd` and `config.confirm_above_usd` (defaults 0.50 and 2): they are the cost gate.
- Resume first: Glob `.genmedia/projects/*/plan.md`. A plan for this product exists → read it, run `python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" urls --label <slug>` and continue at the first unfinished step. Never restart a shoot that has ledger entries.

## UX rules

1. Reply in the user's language (Turkish in → Turkish out). Model prompts are English; text that sits on the product stays in its original language and exact spelling, in quotes.
2. No JSON, request IDs or tool narration in chat. Wait silently; one status line per batch at most.
3. **Question budget: 4, asked one at a time as labelled options (AskUserQuestion when available), and only for what you cannot infer** from the photos, the message or the project folder. Give a default with every question and use it when the user skips. Order and defaults:
   - **Product photo** (only if none was attached): ask for the file. There is no default; this is the one question you may not skip.
   - **Channel** → aspect ratios. Default: online store and feed → 1:1 plus 4:5.
   - **Shot set.** Default "starter set": 1 lifestyle hero, 1 packshot on white, 4 coordinated variants.
   - **Look.** Default: derived from the product itself (palette from the pack, neutral soft daylight).
   Option lists: Workflow step 1. Apparel on a person replaces the look question with the model question.
   A named use ("5 Instagram ad images") answers channel and set: ask nothing. Vaguest request ("do something nice with this") → all defaults, shown in the plan card under Assumptions. Consent, plan approval and hero approval are not part of the budget.
4. Two hard stops: the plan when the cost gate says confirm, and **the hero look, always**. Silence or a successful job is not approval. The user picks the hero; you never pick it for them.
5. Cost gate on the whole shoot (hero, remaining shots, finishing): under announce → run; between → one-line estimate and run; at or above confirm → wait for a yes. Never swap a model the user named to get under a threshold; offer the cheaper route in the plan card.
6. Re-roll budget: 2 per shot (3 attempts in total), something changes each time, never resend a policy rejection unchanged. Re-rolls inside the budget need no new approval; say what they cost in the delivery.
7. A real person in any input (model photo for try-on or in-hand, a person wearing the item in the product photo) → ask once whether the user has that person's consent; no yes → crop to the product or generate a model. A generated model is described by age range, styling and mood, never as a celebrity or a named person's lookalike; it is a synthetic person: say so in the delivery and recommend disclosure where the platform requires it. The product's own marks stay exactly as photographed (someone else's brand on it, such as a reseller's stock: ask once that the user may sell and advertise it). No other real logos, no competitor products, no invented claims, badges, ratings, reviews or prices on any image. Uploads and results sit on public URLs: say so once before uploading unreleased products or photos of people.

## Discovery guardrail

`references/routing-image.md` (tasks `product-shot`, `image-multiref`, `image-edit`, `bg-remove-image`, `virtual-try-on`, `upscale-image`) is a dated cache, verified 2026-09-19. Before the plan card is shown, confirm every endpoint in it:

```bash
genmedia models --endpoint_id <id1>,<id2>,<id3> --status all --limit 50 --json
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
```

- Every ID must be `active`; otherwise take the next tier of that task in `references/routing-image.md`, else `genmedia models "<name>" --no-classify --limit 10 --json`, newest active match, and say which model ran.
- Field names, enums and limits come from the schema, never from memory. They do not carry over between families (`image_urls` vs `image_url` vs `model_image`).
- Never invent IDs or fields. Never run `genmedia run` without an endpoint ID. New releases sit under vendor namespaces (`bytedance/`, `openai/`, `bria/`, `pixelcut/`, `google/`), not only `fal-ai/`.

## Routing

First match wins. Templates, ratios and pitfalls per mode: `references/modes.md`. Prices are hints dated 2026-09-19; `gm.py price` decides.

| Shot | Endpoint | Why | Price hint |
|---|---|---|---|
| Packshot: white, brand colour, transparent, or on a supplied backdrop | `pixelcut/product-photo` | non-generative compositor: product pixels are untouched, so nothing can drift | ~USD 0.024/image |
| Only the background changes; the product stays as photographed | `fal-ai/bria/background/replace` | keeps the foreground and replaces what is behind it; licensed-data model | ~USD 0.04/call |
| Scene where the product is re-lit or re-angled: lifestyle, flat lay, hero banner, scale and context, seasonal, social formats | `bytedance/seedream/v5/pro/edit` | arena #1 E-commerce (2026-09-18); up to 10 references at a flat price | ~USD 0.07/image |
| Same, but label or on-pack text is large in frame and must read identically | `openai/gpt-image-2.5/flare/edit` | strongest text fidelity; up to 16 references | ~USD 0.055/image at `quality: "high"` |
| Detail macro | crop the user's own photo, then `fal-ai/seedvr/upscale/image` | real pixels beat invented texture | ~USD 0.001/MP |
| In-hand, the user supplies the person photo | `bria/fibo-edit-1.5/product-holding` | built for 1 to 3 product images in a person's hands | ~USD 0.04/image |
| In-hand or on-body with a generated person | `bytedance/seedream/v5/pro/edit` | person and scene generated around the referenced product | ~USD 0.07/image |
| Apparel on a model (tops, bottoms, one-pieces) | `fal-ai/fashn/tryon/v1.6` | dedicated try-on model; its person image is the user's photo (consent), an `@handle`, or a generated plate (a person only, never the product) from `bytedance/seedream/v5/pro/text-to-image` at 3:4 | ~USD 0.075/call; plate ~USD 0.07 |
| Accessories or several garments on one person | `bria/fibo-edit-1.5/virtual-try-on` | 1 to 3 garment or accessory images per call | ~USD 0.04/image |
| Fixed position or padding of the product in a generated scene | `fal-ai/bria/product-shot` | explicit placement controls | ~USD 0.04/call |
| Approved shot needs a wider or taller canvas | `fal-ai/flux-2-pro/outpaint` | adds canvas, keeps the approved pixels | ~USD 0.03 + USD 0.015/extra MP |
| Approved shot needs print size | `fal-ai/seedvr/upscale/image` (label-heavy: `topaz/upscale/image/precision`, model `Text Refine`) | faithful enlargement; re-check the label afterwards | ~USD 0.001/MP; Topaz ~USD 0.08 per 24 MP |

Tie-breakers:

1. Non-generative beats generative whenever it can do the job: marketplace main image, colour backdrop, cut-out and detail crop never go through a generative model.
2. Text legibility beats scene quality. Label readable at delivery size and central to the shot → GPT Image 2.5. Label small in a wide scene → Seedream, and QA only requires that it is never legibly wrong.
3. The user named a model → use it after the live check; mention the default in one line, never swap silently.
4. `@handle` or "our usual model" → `/genmedia-skills:character` resolves the reference set; pass those URLs as the person references.
5. No product photo at all → ask for one. If the user has none, this is concept art: hand to `/genmedia-skills:image` and say the result will not be their real product.
6. Motion, voice, UGC or a finished ad with copy → deliver the approved stills, then hand to `/genmedia-skills:ads` (static ads with copy, UGC and ad videos), `/genmedia-skills:short-video` (organic TikTok, Reels, Shorts) or `/genmedia-skills:video` (one product clip).
7. A marketplace listing set with text cards (infographic, dimensions, what's in the box, A+ banners) → `/genmedia-skills:marketplace-cards`; it reuses the stills approved here.

Named traps:

- **Re-imagined product.** A prompt like "amber serum bottle with a white label" on a text-to-image endpoint yields a lookalike, not the product. Every generative job carries the product photo in its image field, and the prompt says "image 1 is the real product".
- **Unseen side.** The model invents what the photos do not show (back label, underside, inside). Keep the camera within the angles the references cover, or ask for another photo.
- **`auto_2K`.** Seedream 5.0 Pro defaults to `image_size: "auto_2K"`, which can cross the 1536x1536 area and double the price. Always send `{width,height}` from the size table in `references/modes.md`.
- **Default quality.** GPT Image 2.5 bills by tokens and `quality` defaults to `high`. Set it on purpose: `high` for label shots, `medium` only for look exploration.
- **Pixelcut `sync_mode`.** It defaults to `true` there and returns base64. Always send `"sync_mode": false`.
- **Bria `automatic`.** `fal-ai/bria/product-shot` with `placement_type: "automatic"` returns ten placements per result. Use `manual_placement` or `original` unless the user asked for the spread and saw the price.
- **Try-on field names.** `fal-ai/fashn/tryon/v1.6` takes `model_image` and `garment_image` (no `_url` suffix), so the helper cannot catch an unfilled `@reference` there. Always run `pipeline.py fill`.
- **Headline in the scene.** Offers, prices and slogans are not rendered by the scene model. Leave copy space; text is set later in a design tool or by `/genmedia-skills:ads`.
- **Upscale first.** Upscaling is the last step, on approved shots only.

## Workflow

1. **Intake** inside the question budget; skip every question the request already answers.

   | Question | Labelled options (first = default) |
   |---|---|
   | Channel | A store listing and social feed → 1:1 + 4:5 · B marketplace listing only → 1:1 · C story or reel cover → 9:16 · D website banner → 16:9 |
   | Shot set | A starter set: hero, packshot, 4 variants · B packshots only · C lifestyle campaign: hero + 5 scenes · D ad pack of N coordinated variants |
   | Look | A from the product itself · B bright minimal studio · C warm natural home · D dark premium |
   | Model (apparel, in-hand) | A generate a model · B my own model photo (consent) · C an `@handle` from `character` |

   Channel lists the allowed ratios; it does not multiply the set. Each shot is generated once, at its mode's default ratio in `references/modes.md` (not in the channel's list → the closest ratio that is). The same shot in a second ratio is a finishing step (step 11) on the approved image, only for the shots the user wants twice.
   The user supplied a campaign or mood image → it answers Look: use it as the last reference of the hero job. Pick a slug (`zeytin-dali-shoot`): it is the batch `label`, the ledger filter, `genmedia-output/<slug>/` and `.genmedia/projects/<slug>/`. Any natural-language label works; helpers transliterate Turkish letters.
2. **Look at every product photo with the Read tool** before anything else. HEIC, AVIF, TIFF or CMYK → convert to PNG or sRGB JPEG first (`references/troubleshooting-product.md`). A photo given only as a URL → save a local copy and Read that; never lock a product you have not seen. Choose the primary reference (sharpest, most frontal, label readable) and up to two supporting ones (second angle, label close-up).
3. **Write the PRODUCT LOCK** into `.genmedia/projects/<slug>/plan.md`: type and form, proportions, materials and finish, colours, **label text verbatim line by line**, logo and layout, count and kit contents, what must never change, and which sides are not visible. Format and the one-paragraph English lock string for prompts: `references/fidelity-qa.md`.
4. **Commit the look before prompting**: one pick per axis (angle, surface, light, props, palette accent, copy space) from `references/variation-matrix.md`, checked against its ban list, written to `plan.md` as a fixed `Look:` string. Variants change one or two axes each; palette and light quality never change inside a set.
5. **Shot plan card.** One row per shot: id, mode, ratio and pixel size, endpoint, references, estimated cost. Verify every endpoint (Discovery guardrail), then price them in one call:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price <id1>,<id2>,<id3> --explain
   ```
   Turn the answer into dollars per shot:
   - Seedream 5.0 Pro edit (`unit: "units"`, read `pricing_text`): per output image at or under a 1536x1536 area, plus the surcharge per input image after the first. Hero with 2 product references = base + 1 surcharge; later shots with the hero added = base + 2. Multiply by `num_images`.
   - GPT Image 2.5 edit answers `1 units`, which is not a price. Take the row of the next larger size at your `quality` from the cost table in `references/routing-image.md` (`t2i-typography` notes); add the reference allowance in `references/platform.md` §7 for every reference beyond the first and say "about".
   - `images`, `generations`: `unit_price` x outputs (`num_images`, `num_results`, `num_samples`). `megapixels`: width x height / 1,000,000 x images. Topaz and outpaint: the block rule in `pricing_text`.
   - Sum hero + remaining shots + finishing. Say that re-rolls are extra (worst case: 2 more per shot). Two sources disagree → quote the higher.
   Save the card to `plan.md`, show it (template under Delivery), apply the cost gate. Waiting for a yes is a hard stop: no uploads, no submits.
6. **Upload and register the references** once:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload ./bottle-front.jpg ./bottle-label.jpg
   python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" add --label <slug> --step product --path ./bottle-front.jpg --url <cdn_url>
   ```
   Register each file under its own step name (`product`, `product-label`, `model`); plans then reference `"@product"`.
7. **Hero first.** With the Write tool (no heredocs, no shell quoting), write a one-job plan with id `hero` and `num_images: 2` to `.genmedia/projects/<slug>/stage-1-hero.tmpl.json`, fill it, run it. Give the Bash call a 600000 ms timeout; the helper polls for up to 540 s.
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" fill --template .genmedia/projects/<slug>/stage-1-hero.tmpl.json --out .genmedia/projects/<slug>/stage-1-hero.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/stage-1-hero.json
   ```
   `status: "pending"` → run the same batch command again; it resumes by label and id and never pays twice. Run the fidelity QA (step 10) on both candidates, withhold a failing one, then send the hero checkpoint and **stop**. No generative scene in the plan (packshots only, try-on only) → the first packshot (margin, shadow, backdrop) or the try-on samples are the hero: same stop, then the rest as one batch.
8. **Visual-system lock.** Look rejected → change picks in `references/variation-matrix.md` (not just wording), re-shoot under a new id (`hero-r2`; editing the completed `hero` job only returns `input_changed`, no image), QA, stop again. The user picked candidate n → record `Hero: @hero[n-1]` (outputs are 0-based: candidate 2 is `@hero[1]`) and the final `Look:` string in `plan.md`. Every remaining generative shot now gets: the product references first, the approved hero last in `image_urls`, the lock string and the look string verbatim, and a role line ("image 1 and 2 are the real product; image 3 is the approved campaign shot: match its palette, light and grade, not its composition").
9. **Remaining shots as ONE batch.** Write `.genmedia/projects/<slug>/stage-2-shots.tmpl.json` from the closest worked plan in `references/batch-plans.md`, `fill`, then `batch` exactly as in step 7 (same label, 600000 ms timeout, `max_parallel` = number of jobs up to 12). A shot that needs another shot's output (lifestyle built on the clean packshot) references it as `"@<job_id>"`, and goes into a later stage file if that job has not completed yet.
10. **Fidelity QA, per image, before anything is shown.** Read each output next to the source photo and run the rubric in `references/fidelity-qa.md`: label text identical and legible, geometry and proportions, colour and material, item count, hands and reflections, no invented logos, text or claims, look matches the hero, pixel size as planned (`width` and `height` in the job's `result`). Verdict per shot: pass, re-roll, or repair by another route. A re-roll is a new job id (`s03-r2`) in a small plan with the same label; change what the failure names. After 2 re-rolls: repair move or drop the shot and say so. Then one coherence pass over the whole set.
11. **Finish** approved shots only: extra ratios (a free local crop when the master was composed for it, outpaint to add canvas, or a re-shoot at that ratio with the approved shot as reference: `references/modes.md`, mode 9), upscale, then cut-outs (the upscalers drop alpha).
12. **Manifest and deliver.**
    ```bash
    python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" manifest --label <slug>
    python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --label <slug> --sum
    ```
    `manifest` exits 1 while `problems` is not empty: resolve or explain each one. Append the outcome (approved hero, re-rolls, dropped shots, spend) to `plan.md`.

`plan.md` is the shoot's memory; keep these lines greppable so a later session can resume:

```text
# Shoot: <product>   slug: <slug>   version: v1   status: proposed | approved | hero-approved | delivered
PRODUCT LOCK ... (block from references/fidelity-qa.md)
Lock string: <one paragraph, English>
Look: <one paragraph, English>
Axes: angle=<pick>; framing=<pick>; surface=<pick>; light=<pick>; props=<pick>; copy=<pick>
Hero: pending | @hero[0] | @hero[1]
<the plan card table and Assumptions>
## Log
- <timestamp> v1 proposed, about USD 0.48 | hero approved: candidate 2 | s03 re-roll 1: F8 grip → open palm
```

Marketplace main image (commonly cited basics; **check the marketplace's current rules**): pure white background, the product alone and whole in frame and filling most of it, no added text, badges, watermarks, borders or props, square, large enough for the listing's zoom (the default packshot here is 2000 x 2000). Use the non-generative packshot path so the listing shows the real item. Secondary images may be lifestyle shots.

## Delivery

Plan card (before spending):

```
Shoot plan "<product>" v<n>: <k> shots, about $<total> (estimate; re-rolls extra, at most 2 per shot)
| # | Shot | Mode | Size | Model | Est. |
| hero | <one line> | lifestyle | 1344x1680 (4:5) | Seedream 5.0 Pro edit, 2 candidates | USD 0.15 |
| s01 | <one line> | packshot white | 2000x2000 (1:1) | Pixelcut | USD 0.03 |
Assumptions: <channel, set, look and every default you chose>
Product lock: <type; label text "…"; never change: …>
I make the hero first and stop for your pick. <below the confirm threshold: Starting now. | at or above it: Reply "go" to start, or tell me what to change.>
```

Hero checkpoint:

```
Hero candidates for "<product>":
1. genmedia-output/<slug>/hero_0.png: <what differs>
2. genmedia-output/<slug>/hero_1.png: <what differs>
Fidelity check: label, shape, colour and count match your photo <or: candidate 2 withheld, label misspelt>.
The remaining <n> shots will copy this look. Pick 1 or 2, or tell me what to change. Spent so far: about $<est_cost_usd_completed>.
```

Final:

```
Done: <k> shots for "<product>" in genmedia-output/<slug>/
1. <file>: <mode, ratio, one line>
2. <file>: <mode, ratio, one line>
Manifest: .genmedia/projects/<slug>/manifest.json   Gallery: <gallery_url>
CDN links per file are in the manifest: public to anyone who has them, may expire; the local files are your copies.
<only if a generated person appears: The person in <files> is AI-generated, not a real model; disclose it where the platform requires.>
Models: <display names>. Estimated spend: about $<est_cost_usd_completed>, including <r> re-rolls. Dropped or withheld: <none | shot and reason>.
Next: <one useful step: another ratio, a print-size upscale, or a product video from the approved stills>
```

Translate the templates; keep paths, IDs and numbers as they are.

## Errors

| Signal (verbatim) | Action |
|---|---|
| `"status":"pending"` with `resume` | Run the same `gm.py batch --plan` again (600000 ms timeout). Never resubmit. |
| `input.image_urls: '@product' is not a URL` (exit 2, nothing sent) | The template was run unfilled. Run `pipeline.py fill`, then the filled plan. |
| `pipeline.py fill`: `"unresolved"` lists a reference | That job or registered file does not exist or did not complete. Finish it or `pipeline.py add` the file; never paste a guessed URL. |
| `"kind":"validation"` with `"fields":[]` and a `hint` | The queue hides the reason. Check in order and change the first thing that is off: field names and values against the OpenAPI schema (array vs string, size limits) → input files (format, size, expired URL: re-upload) → prompt (policy). Fix that job, rerun with `--retry-failed`. Max 3 attempts. |
| `fields[].type: "missing"`, field `image_urls` or `image_url` | Wrong image field for this family. Re-read the schema. |
| `"kind":"content_policy"`, or a black image | Do not deliver, do not resend unchanged, never disable the safety checker. Product prompts trip filters on body and mood words: re-describe plainly (`references/troubleshooting-product.md`). Assume it was billed. |
| `image_too_large`, `file_too_large`, `image_load_error` | Resize or re-encode locally, upload again, `pipeline.py add` under the same step name. |
| `"input_changed":true` | A completed id was edited. Restore the plan, or re-roll under a new id. |
| `"kind":"auth"` | Stop every stage. The user fixes the key or balance. |

More: `references/troubleshooting-product.md`. Platform error types: `references/platform.md` section 4.

## This skill does NOT

- Draw the product from a description, or "improve" its design, label or colours. A better-looking wrong product is a failed shot.
- Paint claims, certifications, awards, ratings, reviews, prices or discount badges into an image, even on request. It leaves copy space; wording the user supplies and confirms as true is set later as text. Never competitor or partner logos.
- Guarantee marketplace or ad-platform acceptance. It follows commonly cited basics and tells the user to verify.
- Produce ads with copy, video, voice or captions (use `/genmedia-skills:ads`, `/genmedia-skills:video`, `/genmedia-skills:audio`), text-heavy listing or infographic cards (use `/genmedia-skills:marketplace-cards`), logos (use `/genmedia-skills:brandkit`) or meshes (use `/genmedia-skills:3d`).
- Train a LoRA on the product. Reference conditioning is the default; training is a separate, confirmed decision via `/genmedia-skills:models`.

## Common mistakes

- Planning from the file name instead of looking at the photo; writing the label text from memory instead of reading it.
- Generating all shots at once, then discovering the look is wrong six images later. Hero first, always.
- Paraphrasing the lock or look string per shot. They are pasted verbatim; only the mode slots change.
- Putting the hero first in `image_urls` and calling it "the product". Product references come first; the hero is a look reference only.
- Accepting a label that is "close". One wrong letter is a fail.
- Varying palette and light across an ad pack and calling it a set.
- Reaching for the cliché list (podiums, splashes, petals, neon glow) because it is the model's default.
- Re-rolling with the identical input, or re-rolling a fourth time instead of changing the route.
- Upscaling or fanning out ratios before the user approved the shot.

## Reference index

- `references/modes.md`: read when planning any shot; every mode with when to use it, default ratio, size table, prompt template with PRODUCT LOCK and LOOK slots, input JSON for the non-prompt endpoints, pitfalls.
- `references/fidelity-qa.md`: read when writing the product lock, checking any output, deciding pass, re-roll or repair, and for the repair moves per failure.
- `references/variation-matrix.md`: read when committing the look and when building N coordinated variants or an ad pack; axes, pick lists per category, ban list, set rules.
- `references/batch-plans.md`: read when writing a stage plan; two complete worked shoots (hero plus 5 variants; packshot to lifestyle chain with `@` references) with verified endpoint IDs and field names.
- `references/troubleshooting-product.md`: read when inputs are difficult (HEIC, glass, white on white, tiny text), a stage fails or resumes oddly, try-on misbehaves, a marketplace rejects an image, or costs surprise.
- `references/routing-image.md`: read when picking another tier (budget, premium, control), when an ID is not active, or for dated price and limit notes per task.
- `references/cli-contract.md`: read when a helper call fails, a job is pending, or you need batch plan keys, `wait`, `cancel`, the ledger, the gallery or the raw CLI.
- `references/platform.md`: read when estimating cost, reacting to a platform error type, or explaining URL privacy, billing and safety.
- `scripts/gm.py`: the shared helper (`preflight`, `price`, `upload`, `run`, `wait`, `cancel`, `batch`, `ledger`).
- `scripts/pipeline.py`: project state (`urls`, `fill`, `add`, `fetch`, `manifest`); resolves `@job` references and writes the manifest.
