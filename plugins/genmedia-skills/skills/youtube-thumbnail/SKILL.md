---
name: youtube-thumbnail
description: >-
  Thumbnails and covers that survive at small size: YouTube thumbnails (16:9), Shorts, Reels and TikTok covers (9:16), podcast and course covers (1:1), from a title plus an optional face photo, @handle character, brand colours or a frame of the user's own video. Text baked in by GPT Image 2.5; faces locked through reference edits.
  Use when: "make a thumbnail for my video", "YouTube thumbnail with my face", "Shorts cover", "podcast cover art", "thumbnail from this frame", "change only the text on the thumbnail", "videoma thumbnail yap", "kapak görseli hazırla", "küçük resimdeki yazıyı değiştir".
  Chain: consumes an @handle from `character` and stills or frames from `image` and `video`; produces sized PNG and JPEG.
  NOT for: posters, photo edits (use `image`); logos (use `brandkit`); link cards, OG images (use `launch-graphics`); ad creatives (use `ads`); the video (use `video`, `short-video`); new characters (use `character`); batches (use `pipelines`); model choice (use `models`); setup problems (use `setup`).
argument-hint: "[video title or topic] [face photo | @handle | video frame] [--format 16:9|9:16|1:1]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/thumbcheck.py" *) Bash(command -v genmedia) Bash(genmedia models *) Bash(genmedia schema *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 with a fal key configured by the user, and python3 >= 3.8. Local ffmpeg or macOS sips is optional (small-size previews, comparison sheets, exact delivery sizes); a Chromium-family browser is optional (placing the user's own logo on a plate).
---

# YouTube Thumbnail

Thumbnails and covers judged at the size people actually see them: about 160 px wide in a feed. One title in, three different concepts out, the user picks, one final, narrow revisions, files at the exact delivery size. The craft (concept frameworks, prompt blueprint, text rules, the small-size gate) lives here; mechanics live in `references/cli-contract.md` and `references/platform.md`.

## Step 0 — Preflight

Once per session:

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
python3 "${CLAUDE_SKILL_DIR}/scripts/thumbcheck.py" tools
```

- `blockers` not empty, CLI missing or older than 0.7.0 → `/genmedia-skills:setup`. Key missing → the user runs `genmedia setup` or exports `FAL_KEY` themselves; wait. Never read, print, request or type a key.
- Keep `config.announce_above_usd` and `config.confirm_above_usd` (defaults 0.50 and 2): they are the cost-gate thresholds.
- `thumbcheck.py tools` says which of `preview`, `sheet`, `fit`, `frame` can run here (needs local ffmpeg or macOS `sips`), and whether `lockup` can (needs a Chromium-family browser). Neither present → the degraded gate in Workflow step 6. Never plan on `drawtext`, Pillow or ImageMagick: text is rendered by the model.
- Resume first: a `.genmedia/projects/<slug>/thumbnail.md` that matches this request → read it, continue at its first open step. Never restart a project that has ledger entries.

## UX rules

1. Reply in the user's language (Turkish in → Turkish out). Write model prompts in English; the on-image text stays in the language and exact spelling it will be published in. Endpoint IDs, field names and paths stay as they are.
2. No JSON, request IDs, prompts or tool narration in chat. Wait silently; at most one status line per batch.
3. **Question budget: 2, one at a time, as labelled options, only when the answer is missing:**
   - Q1 the hook words: no title and no topic → ask for the title. Title known → do not ask; write the 2 to 4 hook words yourself (three different ones across the concepts).
   - Q2 face or no face: ask only if nothing decides it. A photo, an `@handle` or "me / my face / ben" → face. "Faceless", a product, a screen recording, a landscape → no face.
   The user asks for just one thumbnail or names the concept → one draft instead of three; the pick becomes a yes or no. Everything else is a default you state in the delivery line: format 16:9; text language = the title's language; palette = the brand colours given, else chosen per concept; photoreal poster look; 3 concepts; final master 2560x1440 delivered as 1920x1080 and 1280x720. Not counted: the consent confirmation, the pick, a cost confirmation.
4. **The pick is a hard stop.** Show the comparison sheet and wait. Silence, a successful job or your own preference is never a pick. Recommending one is allowed; choosing is not.
5. **Truthfulness.** A thumbnail may dramatise, never misrepresent. Everything shown or written must be in the video or honestly follow from it: no invented numbers, results, reactions, products or guests; no fake UI of a real platform; no logos or characters the user does not own. Cannot tell what the video delivers → ask before promising it (this replaces Q1 or Q2, it does not add a question).
6. **Faces.** A real person's photo (the user included) → one confirmation that they have that person's consent, and one line that uploads sit on public URLs. Never a celebrity or public figure the user is not; "looks like <famous person>" is refused, offer an invented face or a faceless concept. An invented face is a stand-in: never present it as a real named person, customer, expert or guest, and say in the delivery that the face is AI-generated.
7. Cost: estimate the whole request before the first paid call (Workflow step 4) and apply the gate with the thresholds from preflight: under `announce_above_usd` → run; up to `confirm_above_usd` → one line with the estimate, then run; at or above it → show the estimate and wait for an explicit yes (`references/platform.md` section 8). An approval covers the plan shown; a larger plan needs a new one. Never quote a price from memory; never swap a model the user named to save money.
8. Bounded: at most 3 draft rounds and 3 revision rounds; each attempt changes something; a content-policy rejection is never resent unchanged; a job with a request ID is resumed, never resubmitted.

## Discovery guardrail

Routing below is a dated cache (`references/routing-image.md`, verified 2026-09-19). Before the first paid call to an endpoint in a session:

```bash
genmedia models --endpoint_id <endpoint_id> --json
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
```

- `status` must be `active`. Not active or 404 → next tier of the same task in `references/routing-image.md`, else `genmedia models "<name>" --no-classify --limit 10 --json`, newest active match, and say which model ran.
- Field names, enums and limits come from the schema, never from memory. The user names a model → search before doubting; new releases sit under vendor namespaces (`openai/`, `bytedance/`, `google/`, `alibaba/`), not `fal-ai/`.
- Never `genmedia run` without an endpoint ID (smart routing resolves stale defaults).

## Routing

| Step | Endpoint | Why |
|---|---|---|
| Drafts, nothing to reference | `openai/gpt-image-2.5/flare/text-to-image`, `quality: "medium"` | typography leader; only the target family can preview the text, a cheap draft model cannot |
| Drafts with a face photo, `@handle` refs, a product shot or a video frame | `openai/gpt-image-2.5/flare/edit`, `quality: "medium"` | references go in `image_urls` (max 16); same family as the final |
| Final | `openai/gpt-image-2.5/sunburst/edit`, `quality: "high"` | precision tier; the picked draft is image 1, so the final is that composition, not a new roll |
| Revision (text, expression, background, colour) | `openai/gpt-image-2.5/sunburst/edit`, `quality: "high"` | the current final is image 1; one scope per round |
| Text-free plate, photoreal (alternative path) | `bytedance/seedream/v5/pro/text-to-image` | arena #1 photoreal; text is added afterwards with a GPT Image 2.5 edit |
| Identity plate when the face drifts | `fal-ai/nano-banana-2/edit` | routing default for identity-consistent images; text added afterwards |
| Enlarge a real frame or photo | `fal-ai/seedvr/upscale/image`; faces or text first: `topaz/upscale/image/precision` | faithful; Topaz has `Faces` and `Text Refine` models |
| Frame of the user's video | `thumbcheck.py frame` (local ffmpeg) | exact timestamp; no ffmpeg → ask the user for a screenshot |
| The user's own logo on a text-free plate | `thumbcheck.py lockup` (local browser) | the mark is placed from the user's file; a model would redraw it |

Tie-breakers:

1. Text on the image → GPT Image 2.5, even for a photoreal concept. No text at all (user said so) → drafts may run on `bytedance/seedream/v5/pro/text-to-image` or its `/edit`; the rest of the flow is unchanged. Seedream rejects 1280x720 (its minimum area is 1024x1024) and has no `quality` field: send `image_size` 1920x1080 (9:16 → 1080x1920, 1:1 → 1536x1536) and price it per image from its routing row (about USD 0.07 each on 2026-09-19: three drafts are about USD 0.20, recompute the total).
2. Default text strategy is **baked in one pass**. Use the **plate path** (text-free plate, then one "add only this text" edit) when: the same plate needs several languages or A/B wordings; a diacritic failed twice; the plate is a real frame or photo. Details: `references/text-and-readability.md`.
3. `@handle` → read `.genmedia/characters/<handle>/character.json` (anchor `description`; `refs[]` with `role: "face"` and `active: true`), reuse a ref's `cdn_url` when it has one, else upload its file; use the anchor verbatim. `real_person: true` → UX rule 6 applies; a recorded `consent_confirmed_at` is the confirmation. Unknown handle → say so, offer `/genmedia-skills:character`; never substitute.
4. The user named a model → use it after the live check; offer the default in one line.
5. The design is a plate plus the user's own logo (a brand channel, an app's store preview video) → plate path, then `thumbcheck.py lockup` places the logo file centred at a share of the width (`references/text-and-readability.md` section 2b). The plate already exists (a `launch-graphics` plate, the user's photo) → no paid call: lockup, gate, step 10. No logo file → ask for it; never let the model draw the mark.

Traps:

- **Auto-size trap.** The edit endpoints default `image_size` to `auto`, which follows the input image: a portrait face photo yields a portrait thumbnail. Always send `{width,height}`.
- **Default-quality trap.** `quality` defaults to `high` and the family bills by tokens. Set it on every call: `medium` drafts, `high` finals; `xhigh` or `max` only after the user agreed to the price.
- **Multiples-of-16 trap.** 1920x1080 is not a legal GPT Image size. Render 1280x720, 2560x1440 or 3840x2160 and let `thumbcheck.py fit` produce 1920x1080.
- **Attached-image trap.** A text-to-image endpoint has no image field; it ignores the photo and bills anyway. Any reference → the `/edit` endpoint.
- **New-roll trap.** Re-running the prompt at high quality gives a different picture (no `seed` in this family). The final is an edit of the pick.
- **Casing trap.** Never let the model uppercase Turkish: write the final string yourself (`thumbcheck.py text`), in quotes, and check it letter by letter.

## Workflow

1. **Intake.** Title or topic, format (default 16:9), face or not, brand colours, references. HEIC, AVIF, TIFF or very large photos first: `thumbcheck.py fit <file> --max-side 2048 --out .genmedia/tmp/<name>.jpg`; Read and upload that copy. Open every local image with the Read tool before planning (who and what is really in it decides the concepts). A frame from the user's video: `python3 "${CLAUDE_SKILL_DIR}/scripts/thumbcheck.py" frame <video> --at <seconds or m:ss>`, then Read it. Spend the question budget only as UX rule 3 allows.
2. **State card.** Pick a short ASCII `<slug>` (`eksi-maya`): it is the batch `label`, the ledger filter, the output folder and the project folder. A natural-language label also works; the helper folds `"Ekşi maya"` to `Eksi-maya`, and that folded form is then the folder name. Write `.genmedia/projects/<slug>/thumbnail.md` with the Write tool and update it after every step:
   ```text
   # <title> — thumbnail
   promise: <one line: what the video really delivers>
   format: 16:9 | text language: <code> | face: <none | photo path | @handle> (consent: <yes, date | n/a>) | palette: <colours>
   [ ] concepts  [ ] drafts-1  [ ] gate  [ ] pick: -  [ ] final  [ ] revisions 0/3  [ ] delivered
   log:
   - <date> drafts-1: 1 <framework> "<TEXT>", 2 <framework> "<TEXT>", 3 <framework> "<TEXT>"
   ```
3. **Three different concepts.** Read `references/frameworks.md`. Brainstorm at least five privately, keep the three strongest that use **different frameworks** (not three colourways of one idea), each with its own 2 to 4 hook words. Run every hook through the text check and use its `upper` string verbatim:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/thumbcheck.py" text "şimdi izle" --lang tr
   ```
   Hook words and pictures may use only numbers, results, quotes, products and guests the user stated (title, brief, their files); the title alone does not give you one → use a question, a constraint-free hook or a text-free concept, or ask (UX rule 5). Reject any concept that fails the truthfulness rule. Face chosen → at least two of the three concepts show it. The title already carries the hook → one concept may be text-free.
4. **Verify and price.** Discovery guardrail for each endpoint, then:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price openai/gpt-image-2.5/flare/edit,openai/gpt-image-2.5/sunburst/edit
   ```
   GPT Image 2.5 answers `1 units`, which is not a price. Dollars for this skill: jobs x the per-size, per-quality row (a size that is not listed → the next larger row) of the GPT Image 2.5 table in `references/routing-image.md` (`t2i-typography` notes; the edit rows already include one input image) + the reference allowance in `references/platform.md` §7 for every further reference image. Dated hints (2026-09-19): draft 1280x720 `medium` about USD 0.01; final or revision 2560x1440 `high` about USD 0.055; 3840x2160 `high` about USD 0.10. Typical whole job (3 drafts + final + 3 revisions): about USD 0.25 without references, about USD 0.45 with one face reference → under the default announce threshold, run and state the estimate in the delivery line. A second draft round, more references, `xhigh`, `max`, 4K, or several videos in one request (one slug and state card per video; the estimate is the sum) → recompute and apply the gate first.
5. **Drafts in one batch.** Upload references once and keep `urls` (argument order); uploads are public URLs, say so once for private material:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload ./me.jpg
   ```
   Build each prompt from `references/prompt-blueprint.md`. Write the plan with the Write tool to `.genmedia/projects/<slug>/drafts-1.json`:
   ```json
   {"label": "<slug>", "max_parallel": 3, "jobs": [
     {"id": "draft-a", "endpoint_id": "openai/gpt-image-2.5/flare/edit", "est_cost_usd": 0.02,
      "input": {"prompt": "<concept A>", "image_urls": ["<face url>"], "image_size": {"width": 1280, "height": 720}, "quality": "medium", "num_images": 1, "output_format": "png"}},
     {"id": "draft-b", "endpoint_id": "openai/gpt-image-2.5/flare/edit", "est_cost_usd": 0.02, "input": {"prompt": "<concept B>", "image_urls": ["<face url>"], "image_size": {"width": 1280, "height": 720}, "quality": "medium", "num_images": 1, "output_format": "png"}},
     {"id": "draft-c", "endpoint_id": "openai/gpt-image-2.5/flare/edit", "est_cost_usd": 0.02, "input": {"prompt": "<concept C>", "image_urls": ["<face url>"], "image_size": {"width": 1280, "height": 720}, "quality": "medium", "num_images": 1, "output_format": "png"}}
   ]}
   ```
   A concept that uses no reference → `openai/gpt-image-2.5/flare/text-to-image` for that job, without `image_urls` (est. 0.01); never attach a reference the concept does not show. 9:16 → 720x1280 drafts, 1440x2560 final. 1:1 → 1024x1024 drafts, 2048x2048 final.
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/drafts-1.json
   ```
   Give the Bash call a 600000 ms timeout (the helper polls up to 540 s). `status: "pending"` → run the same command again; it resumes by id and never pays twice. Take the file paths from `jobs[].outputs[].path` (normally `genmedia-output/<slug>/draft-a_0.png`); a job with `error` follows the Errors table, the others stay valid.
6. **Small-size gate, before the user sees anything.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/thumbcheck.py" sheet genmedia-output/<slug>/draft-a_0.png genmedia-output/<slug>/draft-b_0.png genmedia-output/<slug>/draft-c_0.png --expect 16:9 --out genmedia-output/<slug>/sheet-1.png
   ```
   Read the sheet: each numbered variant sits above its true-size 160 px preview. Judge the small one first, per variant: (1) subject identifiable, (2) every word legible and spelt exactly as `upper`, (3) one focal point, (4) text clear of the face and of the bottom-right corner, (5) face matches the reference photo (Read both), (6) truthful. Rubric and fixes: `references/text-and-readability.md`. A variant that fails → re-roll it once as a new id (`draft-a2`) with the prompt changed where it failed, then rebuild the sheet. Still failing → show it labelled as weak or drop it; never claim a check you could not make. No ffmpeg and no `sips` → Read each full-size file, judge as if it were a postage stamp, and say the mechanical preview was unavailable.
7. **Show and stop.** Send the pick message (Delivery) with the sheet path. Wait for the user's choice. "None" → one new round with new frameworks (`drafts-2.json`, new ids), maximum 3 rounds.
8. **Final.** Picked draft URL (`outputs[].url`, or upload the file again) is image 1, identity references follow. Prompt: the composition-lock block of `references/prompt-blueprint.md`. Write `.genmedia/tmp/<slug>-final.json`:
   ```json
   {"prompt": "<composition lock + original blocks>", "image_urls": ["<picked draft url>", "<face url>"], "image_size": {"width": 2560, "height": 1440}, "quality": "high", "num_images": 1, "output_format": "png"}
   ```
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run openai/gpt-image-2.5/sunburst/edit --input .genmedia/tmp/<slug>-final.json --label "<slug>" --est-cost 0.11 --download "genmedia-output/<slug>/final_{index}.{ext}"
   ```
   `--est-cost`: 0.06 with the draft alone, 0.11 with one identity reference. 600000 ms Bash timeout. `pending` → `gm.py wait <endpoint_id> <request_id>`, never a second `run`. Then gate again: `thumbcheck.py preview genmedia-output/<slug>/final_0.png`, Read the preview, Read the full image, compare text letter by letter and the face against the reference. Gate fails → run the final again with exactly one corrective sentence after TASK (max 3 attempts; these are repairs, not the user's revision rounds) and take the new file name from `outputs[].path` (existing files are never overwritten); never deliver a final whose text is wrong. The user asked for 4K up front → render 3840x2160 here instead of upscaling later.
9. **Narrow revisions, max 3 rounds, only when the user asks** (otherwise go to step 10; after an accepted revision run step 10 again on the new file). One scope per round: only the text, only the expression, only the background, only a colour. The current final is image 1; prompt patterns and exact fields: `references/revisions.md`. Each accepted result becomes the next source (`rev1_0.png`, `rev2_0.png`). A request that changes the concept is not a revision: go back to step 3 and say so.
10. **Deliver at pixel size.**
    ```bash
    python3 "${CLAUDE_SKILL_DIR}/scripts/thumbcheck.py" fit genmedia-output/<slug>/final_0.png --size 1280x720 --max-kb 2000 --out genmedia-output/<slug>/thumbnail-1280x720.jpg
    python3 "${CLAUDE_SKILL_DIR}/scripts/thumbcheck.py" probe genmedia-output/<slug>/thumbnail-1280x720.jpg --expect 16:9 --max-kb 2000
    ```
    The source is the latest accepted file (`final_0.png`, later `rev<n>_0.png`). Default set: the PNG master, 1920x1080 JPEG, 1280x720 JPEG. Sizes per format and the platform notes: `references/text-and-readability.md`. No local tool → deliver the master, state its dimensions from `probe` (works without tools) and say the resize was not done. Update the state card, then send the final message.

## Delivery

Pick message (after the gate, never before):

```
3 thumbnail drafts for "<title>": genmedia-output/<slug>/sheet-1.png
1. <framework in plain words> — "<TEXT>" — <one line: why it should earn the click>
2. <…>
3. <…>
Checked at 160 px: <what passed; anything weak, honestly>. Drafts are medium quality; the final is rendered from your pick at full quality.
Gallery: <gallery_url> · est. $<est_cost_usd_completed> so far
Which one? (number, or "none" with what is missing)
```

Final message:

```
Thumbnail ready: genmedia-output/<slug>/thumbnail-1280x720.jpg (<kb> KB), thumbnail-1920x1080.jpg (<kb> KB)
Master: genmedia-output/<slug>/<latest accepted file> (2560x1440 PNG)
Link: <cdn url> (public to anyone with the link; may expire — the local files are your copy)
GPT Image 2.5 Sunburst · text "<TEXT>" · est. $<est_cost_usd_completed> so far
Chosen for you: <format, text language, palette, look — every default the user did not set>
<only with an invented face:> The face is AI-generated and shows no real person.
File size: long-standing YouTube guidance is 16:9, at least 1280x720, under 2 MB — check YouTube's current limits.
Want a narrow change? Only the text, only the expression, only the background or only a colour (<n> of 3 rounds left).
```

Translate both; keep paths, numbers and the on-image text unchanged. A withheld or black result: say which and why, offer a compliant rewrite, never show it.

## Errors

| Signal | Do |
|---|---|
| `kind: "validation"`, field `image_urls`, type `missing` | A reference was sent to a text-to-image endpoint or as `image_url`. Use the `/edit` endpoint with the `image_urls` array. |
| A validation error on `image_size` (types such as `multiple_of`, `less_than_equal`, `greater_than_equal`, `value_error`) | A side is not a multiple of 16, or the size is outside 655,360 to 8,294,400 pixels. Use 1280x720, 2560x1440, 3840x2160 (or the 9:16 and 1:1 pairs above). |
| `kind: "validation"` with empty `fields` and a `hint` (the queue said `COMPLETED`, the job failed) | Check in order, change the first thing that is off: fields against the OpenAPI schema; reference files (format, size, expired URL → `thumbcheck.py fit`, upload again); then the prompt (a real person's name, a brand, a policy term). Max 3 attempts. May have been billed. |
| `kind: "content_policy"`, or a black image | Do not deliver, do not resend unchanged. Usual causes here: a named public figure, a real logo, shock imagery. Rewrite and say what changed. |
| `file_download_error`, `image_load_error` | Expired or blocked URL, or a HEIC/odd file. `thumbcheck.py fit` to JPEG, upload again. |
| `status: "pending"` | Same `batch` command again, or `gm.py wait`. Never resubmit. |
| `kind: "not_found"` | Stale ID → Discovery guardrail; say which model ran. |
| `kind: "auth"` | Stop. The user fixes the key or balance. |
| `thumbcheck.py`: `kind: "tool_missing"` | No ffmpeg and no `sips`. Use the degraded gate (step 6) and deliver the master; `probe` and `text` still work. |

Wrong rather than failed (misspelt text, lost likeness, clutter, muddy at 160 px, text under the duration badge): `references/troubleshooting-thumbnail.md`. Platform error types: `references/platform.md` section 4.

## This skill does NOT

- Draw text locally. No `drawtext`, Pillow or ImageMagick is assumed; an overlay in an editor is the user's own option, offered with the text-free plate. `thumbcheck.py lockup` only places the user's own logo file.
- Promise click-through rates, "viral" results or A/B outcomes. It ships readable, truthful candidates; the platform's own test tools decide.
- Clone another channel's thumbnail, use a celebrity's likeness, or put real platform UI, logos or fake counters on the image.
- Make channel banners, end screens or the video (use `/genmedia-skills:image`, `/genmedia-skills:video` or `/genmedia-skills:short-video`), logos or channel branding (use `/genmedia-skills:brandkit`), ad creatives (use `/genmedia-skills:ads`), or create the recurring character itself (use `/genmedia-skills:character`).
- Upload to YouTube or any platform.

## Common mistakes

- Three variants of one idea (same layout, new colour). The pick is only worth a hard stop when the concepts differ.
- Judging at full size. A thumbnail that needs zooming has already failed; look at the 160 px preview first.
- More than 4 words, thin fonts, text over the face, text in the bottom-right corner (the duration badge sits there).
- Repeating the title as the text. The text adds the hook the title lacks.
- Rendering the final from the prompt instead of from the pick, then presenting a different picture.
- "Make it pop" handled as a full regeneration. Ask which single scope, then edit.
- Sending a revision with two scopes ("new text and new background"): run them as two rounds, text last.
- Leaving `quality` and `image_size` to their defaults on an edit endpoint.

## Reference index

- `references/frameworks.md` — read when choosing concepts (step 3): the framework library with when-to-use, composition sketch, truthfulness risk, and how to pick three that differ.
- `references/prompt-blueprint.md` — read when writing any draft, final or plate prompt: the block blueprint, identity-lock and composition-lock blocks, six worked prompts including a Turkish-text one.
- `references/text-and-readability.md` — read when writing hook words, choosing baked versus plate path, placing the user's logo on a plate (section 2b), running the small-size gate, or choosing delivery sizes and safe zones per format.
- `references/revisions.md` — read when the user asks for any change after the pick: allowed scopes, prompt patterns, verified edit-endpoint fields, wording A/B batches, upscale after approval.
- `references/troubleshooting-thumbnail.md` — read when a result is wrong rather than failed, or a helper reports a problem not in the table above.
- `references/routing-image.md` — read when a tier other than the default is needed (budget typography, identity, upscale), an ID is not active, or for the dated GPT Image 2.5 cost table.
- `references/cli-contract.md` — read when a helper call fails, a job is pending, or you need `batch`, `wait`, the ledger, the gallery or the raw-CLI fallback.
- `references/platform.md` — read when estimating cost, reacting to a platform error type, or explaining URL privacy, expiry and consent.
- `scripts/gm.py` — shared helper for every paid call (`preflight`, `price`, `upload`, `run`, `wait`, `batch`, `ledger`).
- `scripts/thumbcheck.py` — local, free, no network: `tools`, `probe`, `preview`, `sheet`, `fit`, `frame`, `text`, `lockup` (the user's logo over a plate, needs a browser); one JSON object per call, exit 0 ok, 1 failed, 2 usage.
