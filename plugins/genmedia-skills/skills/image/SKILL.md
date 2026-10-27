---
name: image
description: >-
  One-off still images and edits with fal's genmedia CLI: photoreal stills (Seedream 5.0 Pro), posters and on-image text (GPT Image 2.5), SVG icons (Recraft), multi-reference edits, inpaint, erase, outpaint, background removal, upscale, vectorize, layerize.
  Use when: "make an image of", "poster with this headline", "SVG icon set", "edit this photo", "remove the background", "upscale to 4K", "bana bir görsel üret", "bu fotoğrafı düzenle", "arka planı sil".
  Chain: produces files and CDN URLs for `video`, `3d`, `pipelines`; consumes @handle sets from `character`.
  NOT for: product shoots (use `product-photoshoot`); listing cards (use `marketplace-cards`); product ads (use `ads`); thumbnails, covers (use `youtube-thumbnail`); logos, brand kits (use `brandkit`); store screenshots, OG cards (use `launch-graphics`); meshes (use `3d`); video (use `video`); sound (use `audio`); recurring characters (use `character`); model choice (use `models`); campaigns (use `pipelines`); setup problems (use `setup`).
argument-hint: "[what to make or change] [image paths] [--model <endpoint-id>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(command -v genmedia) Bash(genmedia version *) Bash(genmedia models *) Bash(genmedia schema *) Bash(genmedia pricing *) Bash(genmedia docs *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 with a fal key configured by the user, and python3 >= 3.8.
---

# Image

Still images on fal through the `genmedia` CLI: generate, edit, repair, cut out, enlarge, vectorize, split into layers, dress a person. One request in, finished files on disk out. Every paid call goes through the bundled helper `scripts/gm.py`; every endpoint is confirmed live before money is spent.

## Step 0 — Preflight

Once per session:

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
```

- `blockers` empty → continue. CLI missing or older than 0.7.0 → send the user to `/genmedia-skills:setup`.
- Key missing or invalid → ask the user to run `genmedia setup` or export `FAL_KEY` themselves, then wait. Never read, print, request or type a key.
- Calling convention, JSON shapes and the raw-CLI fallback: `references/cli-contract.md`.

## UX rules

1. Reply in the user's language (Turkish in → Turkish out). Write model prompts in English; keep on-image text in the language and exact spelling the user gave. Endpoint IDs and field names stay as they are.
2. No JSON, request IDs or tool narration in chat. Wait silently; at most one status line per batch. IDs live in the ledger (`.genmedia/runs.jsonl`).
3. **Question budget: 0 for plain generation.** Pick the model, size, count and style yourself and say what you chose in the delivery line. **1 question, as labelled options, only when blocked:**
   - several attached images and their roles cannot be inferred (which is the base, which are references);
   - the image must carry text and the user gave no wording;
   - the request fits two deliverables that cost very differently (SVG logo vs raster mock-up);
   - there is nothing to depict: no subject, and no project context to take one from.
   Consent and cost confirmations below are not part of the budget.
4. Never read approval into silence or into a job that succeeded. Reversible picks (seed, draft model, crop) are yours; irreversible or brand-defining picks (final logo, hero image) belong to the user.
5. Cost: estimate before spending. Under USD 0.50 run; USD 0.50 to USD 2 say the estimate in one line and run; USD 2 or more, show it and wait for a yes. The user may override both thresholds in `.genmedia/config.json`; use the values preflight prints under `config`. Never quote a price from memory; never swap a model the user named to save money. Details: `references/platform.md` sections 7 and 8.
6. At most 3 attempts per step and something must change each time. A content-policy rejection is never resent unchanged. A job that has a request ID is resumed, never resubmitted.
7. A real person's face or body as input (edit, try-on, identity reference): ask once whether the user has that person's consent. No real logos or characters the user does not own. Uploads and results sit on public URLs: say so before uploading something private.

## Discovery guardrail

The routing below is a dated cache (`references/routing-image.md`, verified 2026-09-19), not truth. Before the first paid call to an endpoint in a session:

```bash
genmedia models --endpoint_id <endpoint_id> --json
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
```

- `status` must be `active`. Not active or 404 → next tier in `references/routing-image.md`, else search: `genmedia models "<name>" --no-classify --limit 10 --json`, take the newest active match and tell the user which one you used.
- Take field names, enums and limits from the schema, never from memory. Parameter names do not carry over between model families.
- The user names a model you do not know → search before doubting; it may be newer than this file. New releases sit under vendor namespaces (`bytedance/`, `openai/`, `google/`, `alibaba/`, `xai/`, `meta/`), not `fal-ai/`.
- Never run `genmedia run` without an endpoint ID (smart routing resolves stale, broken defaults). Old IDs from blogs and other skills: translate them with the "Stale IDs" table in `references/routing-image.md`.

## Routing

First match wins; a "Same, …" row refines the row above it. Tiers, prices and limits per task: `references/routing-image.md`. Every price word in this file is a hint dated 2026-09-19; `gm.py price` and the routing reference decide.

**No input image (generate)**

| Intent | Endpoint | Why |
|---|---|---|
| Any legible words in the picture: poster, headline, UI mock, label, infographic, meme | `openai/gpt-image-2.5/flare/text-to-image` | strongest text and layout fidelity; transparent backgrounds |
| Same, intricate or dense layout, time is no issue | `openai/gpt-image-2.5/sunburst/text-to-image` | precision tier, slower |
| Same, predictable per-megapixel cost | `ideogram/v4/fast` | typography family without token pricing |
| Deliverable is SVG: logo, icon, vector illustration | `fal-ai/recraft/v4.1/text-to-vector` | returns real editable SVG |
| Banner strips 4:1, 8:1, 1:4, 1:8 | `fal-ai/nano-banana-2` | these ratios are values of its `aspect_ratio` enum |
| "Quick", "rough", ideation, many cheap variations | `fal-ai/z-image/turbo` | half a cent per megapixel |
| Volume drafts at a flat cent | `meta/muse-image/text-to-image` | about USD 0.01 per image, fixed ~2.5 MP |
| Photoreal, portrait, film still, lifestyle, e-commerce still, anything else | `bytedance/seedream/v5/pro/text-to-image` | arena #1 on Overall, Film and E-commerce (2026-09-18) |
| Same, 4K output or facts that need web grounding | `fal-ai/nano-banana-pro` | `resolution` up to 4K, `enable_web_search` |

**Input image present (edit)**

| Intent | Endpoint | Why |
|---|---|---|
| Change one thing, keep the rest; add or fix text on the image | `openai/gpt-image-2.5/flare/edit` | precise instruction following; its optional `mask_url` is a hint, not a boundary |
| Combine several images into one (product + scene + style, person + outfit + place) | `bytedance/seedream/v5/pro/edit` | up to 10 references at a flat price |
| More than 10 references, or references plus a mask | `openai/gpt-image-2.5/flare/edit` | up to 16 `image_urls` plus `mask_url` (RGBA, transparent = edit; a hint, the frame is redrawn) |
| Product on a new background or in a new scene | `bytedance/seedream/v5/pro/edit` | arena #1 E-commerce; restages while keeping the item |
| Packshot: solid, transparent or supplied background with shadow, product pixels untouched | `pixelcut/product-photo` | non-generative compositor |
| Swap only the background from a prompt or reference | `fal-ai/bria/background/replace` | foreground is preserved, licensed-data model |
| Fill a masked region from a prompt | `fal-ai/flux-pro/v1/fill` | dedicated mask-fill model |
| Remove an object, mask supplied | `fal-ai/bria/eraser` | clean removal, keeps alpha |
| Remove an object, no mask | `openai/gpt-image-2.5/flare/edit` | instruction edit; no mask needed |
| Extend the canvas, change aspect ratio by adding content | `fal-ai/flux-2-pro/outpaint` | per-side pixel control |
| Cut out the subject (transparent PNG) | `fal-ai/birefnet/v2` | under a cent; matting and portrait variants |
| Enlarge faithfully (print, 4K) | `fal-ai/seedvr/upscale/image` | USD 0.001 per megapixel, invents nothing |
| Enlarge a portrait or text-heavy image at top fidelity | `topaz/upscale/image/precision` | Faces and Text Refine models |
| Raster to SVG | `fal-ai/recraft/vectorize` | one cent |
| Split into editable layers | `bytedance/seedream/v5/pro/layerize` | base plus transparent layers |
| Garment onto a person | `fal-ai/fashn/tryon/v1.6` | dedicated try-on model |
| "What is in this image", "write a prompt from this" | none: open the file with the Read tool | free; you are the vision model |

Tie-breakers:

1. An attached image decides first: it is an edit, whatever the wording.
2. Legible text beats photoreal: a photoreal ad with a headline goes to GPT Image 2.5.
3. A vector deliverable beats style: if the user will open it in Illustrator or Figma, it is Recraft vector.
4. Mask supplied → dedicated mask endpoint. No mask → instruction edit; do not ask the user to draw one.
5. The user named a model → use it after the live check, even when this table disagrees. Offer the alternative in one line, never swap silently.
6. `@handle`, "same person as before", "our mascot again" → hand off to `/genmedia-skills:character` to resolve the reference set, then return here and run a multi-reference edit with those URLs.
7. Ten or more deliverables, or image plus video plus audio in one request → `/genmedia-skills:pipelines` plans it; this skill supplies routing and prompts.
8. Scenario requests leave this skill: a shoot of the user's real product → `/genmedia-skills:product-photoshoot`; marketplace listing cards → `/genmedia-skills:marketplace-cards`; an ad with copy → `/genmedia-skills:ads`; a thumbnail or cover → `/genmedia-skills:youtube-thumbnail`; a logo or brand identity → `/genmedia-skills:brandkit`. A plain one-off image or edit stays here.

Named traps:

- **Attached-image trap.** A text-to-image endpoint has no image field; it ignores the picture and bills anyway. Image in → `/edit` endpoint, URLs in the `image_urls` array (array even for one image). Exceptions take a single `image_url`: the utility endpoints and `fal-ai/flux-pro/kontext`.
- **Raster-logo trap.** Never deliver a PNG from a photo model as "the logo". Logo, icon, badge → `fal-ai/recraft/v4.1/text-to-vector`. `fal-ai/recraft/vectorize` is for a raster the user already owns.
- **Default-quality trap.** GPT Image 2.5 bills by tokens and `quality` defaults to `high`. Always set it: `medium` for exploration (about a quarter of the cost), `high` for finals, `xhigh` or `max` only after the user agreed to the price.
- **auto_2K trap.** Seedream 5.0 Pro defaults to `image_size: "auto_2K"`, which can cross the 1536x1536 area and double the price. Always send an explicit `{width,height}`.
- **Size-knob trap.** Some families take `image_size`, others `aspect_ratio` plus `resolution`. The wrong knob is ignored without an error and the job bills in full. See the table under Workflow.
- **3D-look trap.** "A 3D render of a sneaker" is an image. Only a mesh file (GLB, USDZ, OBJ, STL) is a 3D job: `/genmedia-skills:3d`.
- **Upscale-first trap.** Upscaling comes after every edit (only a cut-out may follow it). Editing an upscaled image pays per megapixel for pixels that get regenerated, and hits input limits.
- **Face-swap trap.** No face-swap endpoint is listed on fal. Identity goes through `/genmedia-skills:character` and a multi-reference edit, with consent.

## Workflow

1. **Classify and route.** Generate, edit or utility; pick the endpoint above. Resolve `@handle` through `character` first.
2. **Look at what you were given.** Open every local input image with the Read tool: it fixes roles (base vs reference), tells you the aspect ratio to keep, and feeds the prompt. Never describe an image you have not seen.
3. **Confirm the endpoint** (Discovery guardrail) and price it:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price <endpoint_id>
   ```
   Most image endpoints answer `needs_llms_txt: true`. Convert by `unit`: `megapixels` → width x height / 1,000,000 x images; `images`, `generations`, `requests` → x outputs; `units` and `compute seconds` → not multipliable, take the dated Price cell of that endpoint in `references/routing-image.md` (size tiers, per-reference surcharges), or `pricing_text` from `gm.py price <id> --explain` when the endpoint has no row. GPT Image 2.5 answers `1 units`, which is not a price: use the per-size, per-quality table in the `t2i-typography` notes there. Two sources disagree → quote the higher. Apply the cost gate to the whole plan (all variations, all steps) and say "about".
4. **Upload local inputs** and keep the `urls` array (argument order). Remote URLs that fal can fetch go in unchanged. HEIC, AVIF, TIFF or CMYK files: convert to PNG or sRGB JPEG first (`references/troubleshooting-image.md`, Input problems); a queued job that fails on the format does not say why.
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload ./product.png ./scene.jpg
   ```
5. **Write the prompt** with `references/prompting-image.md` (structure, per-family rules, text rendering). Edits: `Change:` what differs, `Keep:` what must stay identical, `Blend:` how it sits in the scene; label each reference by position ("image 1 is the base photo, image 2 is the jacket"). Field names and JSON per job: `references/editing-recipes.md`.
6. **Write the input JSON** with the Write tool to `.genmedia/tmp/<label>.json`. No shell quoting, no heredocs. Only fields that exist in the schema. Never `sync_mode: true`; `pixelcut/product-photo` defaults it to true, so send `"sync_mode": false` there.
   ```json
   {"prompt": "…", "image_size": {"width": 2048, "height": 1152}, "num_images": 1, "output_format": "png"}
   ```
7. **Run.** `<label>` is a short slug for this piece of work; it names the output folder and groups the ledger.
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run <endpoint_id> --input .genmedia/tmp/<label>.json --label <label> --est-cost <usd>
   ```
   Give the Bash call a 600000 ms timeout: the helper polls for up to 540 s. `status: "pending"` (or the call was killed: the helper's `ledger --tail 5` command has the request ID) → resume, never submit again:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" wait <endpoint_id> <request_id>
   ```
   Four or more independent jobs → write one plan (shape in `references/cli-contract.md`, Batch) and run it; after `pending`, run the same command again:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/tmp/<label>-plan.json
   ```
8. **Check before you show.** `ok` is true and every `outputs[].path` exists. If `result.has_nsfw_concepts` has a `true`, that file is a black placeholder: do not deliver it. Seedream 5.0 Pro, GPT Image 2.5 and Nano Banana return no such array, so open the first output with the Read tool: black frame, wrong or misspelt text, cropped subject and extra limbs are caught here, not by the user.
9. **Deliver** with the template below. For edits chained on a result, reuse `outputs[].url` while it is fresh, otherwise upload the local file again.

### Draft → final ladder

Use it when the user is exploring ("a few ideas", "not sure about the style") or the final is expensive (4K, `quality: "max"`, more than 4 finals). Skip it for a single clear request: run the default model once.

1. Drafts: 3 to 4 distinct directions on `fal-ai/z-image/turbo` (photo, illustration) or on the target GPT Image endpoint at `quality: "medium"` (text layouts; a draft model cannot preview typography).
2. The user picks a direction. This is their decision; do not pick for them.
3. Final: the routed default at full settings, prompt carried over and tightened. A draft from another model is a direction, not a seed: say that the final will differ in detail.
4. Upscale last, only if the target size exceeds what the model renders natively.

### Variations

- Same idea, different rolls → `num_images` (check the schema maximum: 4 on most, 6 on Seedream, 10 on GPT Image and Muse; Recraft vector and FLUX.2 Pro / Max have none, so send separate jobs). Cost scales linearly.
- Different ideas → separate jobs with different prompts in one `batch`; one variable changes per job (angle, light, palette), everything else is copied verbatim.
- Reproducible iteration → fix `seed` where the schema has one (Nano Banana, FLUX, Z-Image; not Seedream 5.0 Pro or GPT Image 2.5). Record the seed the result returns.

### Size and aspect per family (verify in the schema)

| Family | Knob | Rules |
|---|---|---|
| Seedream 5.0 Pro (t2i, edit) | `image_size`: `{width,height}`, preset, `auto_1K`, `auto_2K` | total pixels 1024x1024 to 2048x2048, aspect 1:16 to 16:1. Lower price tier up to 1536x1536 area: 1536x1536, 2048x1152, 1152x2048, 1728x1296, 1296x1728 |
| GPT Image 2.5 (t2i, edit) | `image_size`: `{width,height}`, preset, `auto` | both sides multiples of 16, longest side 3840, aspect up to 3:1, 655,360 to 8,294,400 pixels. 1080 is not a multiple of 16: use 1920x1088, or 2560x1440 and downscale. Edit default `auto` follows the input |
| Nano Banana Pro / 2 | `aspect_ratio` enum + `resolution` (`1K`, `2K`, `4K`; 2 adds `0.5K`) | no pixel sizes; 2K and 4K multiply the price |
| Muse Image | `aspect_ratio` free `"w:h"` string | output fixed near 2.5 MP |
| Recraft vector, Ideogram V4, Z-Image, FLUX | `image_size` preset or `{width,height}` | `square` is 512 px, `square_hd` 1024 px |

Platform defaults by use: 1:1 feed and marketplace, 4:5 portrait feed, 9:16 story and reel cover, 16:9 thumbnail and slide, 3:2 or 4:3 editorial. Use unknown → 1:1 (1536x1536 on Seedream 5.0 Pro). An edit keeps the input's ratio unless the user asks otherwise.

### Transparent backgrounds

- New asset (sticker, icon PNG, cut-out object): GPT Image 2.5 Flare with `"background": "transparent"` and `"output_format": "png"`. Flat-price alternative: `fal-ai/ideogram/v3/generate-transparent`.
- Existing image: `fal-ai/birefnet/v2`. Hair, fur, glass → `"model": "Matting"`; people → `"Portrait"`.
- JPEG has no alpha: every step after a cut-out keeps `png` (or `webp`). SeedVR and Topaz precision drop alpha even with `png` output (measured 2026-09-21), so when the asset must also be larger, upscale first and cut out last.

### 4K and print

Order: generate at the largest native size that stays in the price tier you chose → get approval → upscale once. Native 4K exists on Nano Banana Pro / 2 (`resolution: "4K"`, price doubles) and GPT Image 2.5 (3840x2160). For anything else, `fal-ai/seedvr/upscale/image` with `upscale_mode: "target"` is cheaper than rendering large. Recipes: `references/editing-recipes.md`.

## Delivery

Single image:

```
Saved: genmedia-output/<label>/<file>
Link: <cdn url> (public to anyone with the link; may expire — the local file is your copy)
<Model display name> · <width>x<height> · est. $<cost>
<one line: what you chose on the user's behalf, and the one most useful next step>
```

Set of images:

```
Saved <n> files in genmedia-output/<label>/
1. <file> — <what differs>
2. <file> — <what differs>
Gallery: <gallery_url>
<Model display name> · <size> · est. $<total>
Which one should I take further?
```

Draft round: list the directions with one line each, say they are drafts from a cheaper model, ask which to finalize. Blocked or black result: say which output was withheld and why, offer a compliant rewrite; never show the black file. Translate the template into the user's language; keep paths, URLs and model names as they are.

## Errors

Helper errors come back as `{ok:false, kind, http_status, message, fields[]}`.

| Signal | Do |
|---|---|
| `kind: "validation"`, `fields[].type: "missing"`, field `image_urls` | You sent `image_url` to an edit endpoint (or the reverse). Re-read the schema, fix the field name and shape, rerun. |
| `fields[].type` `one_of`, `literal_error`, `enum` on `image_size`, `aspect_ratio`, `resolution`, `quality` | Wrong knob or value for this family. Use the nearest allowed value from the schema and tell the user what was substituted. |
| `multiple_of`, `greater_than_equal`, `less_than_equal` on width or height | Round to the bound in the message (GPT Image: multiples of 16; Seedream: total pixel window). |
| `image_too_large`, `file_too_large`, `image_too_small` | Resize locally (`sips`, `ffmpeg` or `magick`, whichever exists), upload again. Too small → upscale first. |
| `file_download_error`, `image_load_error` | The URL expired or is blocked, or the file is corrupt. Upload the local file again; re-encode to PNG if it still fails. |
| `kind: "content_policy"`, or `has_nsfw_concepts` true, or a black image | Do not deliver, do not resend unchanged, do not switch the safety checker off. Tell the user which part was flagged and offer a rewrite. Assume it was billed. |
| `kind: "validation"` with empty `fields` and a `hint` (the queue said `COMPLETED`, the job had failed; the reason is not recoverable) | Check in this order and change the first thing that is off: field names and values against the OpenAPI schema; input files (format, over the model's size limit, expired URL → convert or resize, upload again); then the prompt (policy). Nothing off → tell the user, point to https://fal.ai/dashboard/requests, do not retry blind. May have been billed. |
| `kind: "not_found"` | The ID is stale. Discovery guardrail: next tier or search; say which model ran. |
| `kind: "auth"` | Stop. The user fixes the key or balance (`genmedia setup`, fal dashboard). |
| `kind: "rate_limit"` or `"server"` | Wait briefly, then `wait` on the same request or rerun once. Second failure → next tier, after asking if the user named this model. |

More cases (garbled text, wrong face, halos, seams, colour shift, SVG problems): `references/troubleshooting-image.md`. Full platform table: `references/platform.md` section 4.

## Reference index

- `references/routing-image.md` — read when picking a tier other than the default (budget, premium, control), when an ID is not active, when the user names an old model ID, or for price and limit notes per task.
- `references/prompting-image.md` — read when writing any prompt that matters: universal structure, per-family rules (Seedream 5.0 Pro, GPT Image 2.5, Nano Banana, FLUX.2, Recraft vector, Ideogram V4), realism checklist, on-image text rules, negative space for overlays, worked rewrites.
- `references/editing-recipes.md` — read when the job has an input image or is a utility: edit, multi-reference roles, inpaint, erase, outpaint, background remove and replace, product swaps, try-on, upscale, vectorize, layerize, image understanding; exact endpoints, field names and input JSON.
- `references/troubleshooting-image.md` — read when a result is wrong rather than failed: bad text, lost identity, halos, seams, colour shift, plastic skin, soft upscale, SVG issues; and for error types not in the table above.
- `references/cli-contract.md` — read when a helper call fails, a job is pending, you need `batch`, `wait`, `cancel`, the ledger, the gallery, or the raw CLI because python3 is missing.
- `references/platform.md` — read when estimating cost, handling a platform error type, explaining URL privacy and expiry, or judging a safety question.
- `scripts/gm.py` — the helper every paid call goes through; `--help` on any subcommand is free.
