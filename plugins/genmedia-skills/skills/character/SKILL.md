---
name: character
description: >-
  Create, store, reuse and evolve a recurring character (person, mascot, product-as-character) so later images and videos keep the same identity. Identity is a local character sheet plus reference-conditioned generation (Nano Banana 2 Edit and Seedream 5.0 Pro Edit for stills, Seedance 2.5 and Kling O3 reference-to-video for clips), with optional LoRA training.
  Use when: "create a character", "make a character sheet", "keep the same face in every image", "use @mara in this scene", "same mascot across all shots", "my character keeps changing", "train a LoRA of me", "list my characters", "karakter oluştur", "aynı karakteri kullan", "yüzü hep aynı kalsın".
  Chain: produces an @handle (anchor text plus reference URLs) for `image`, `video` and the scenario skills.
  NOT for: a one-off image (use `image`); animating or voicing a finished character (use `video`, `audio`); presenter ads (use `ads`); face thumbnails (use `youtube-thumbnail`); multi-shot productions (use `pipelines`); model choice (use `models`).
argument-hint: "[create|use|list|train] [@handle] [what to make]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" *) Bash(command -v genmedia) Bash(genmedia models *) Bash(genmedia schema *) Bash(genmedia pricing *) Bash(genmedia assets characters list *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 and python3 >= 3.8.
---

# Character: one identity across images and videos

Make a character once, reuse it everywhere. Be honest with the user about what this is: the `genmedia` CLI has no trained-identity switch and does not expand `@handle` in prompts. Identity here is (a) a local character sheet, the source of truth, (b) reference images plus an anchor text passed to a multi-reference model on every call, (c) optionally a trained profile or LoRA, (d) optionally a mirror in fal Assets. This skill resolves `@handle` itself.

## Step 0 — Preflight

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
```

- Key missing: tell the user to run `genmedia setup` or export `FAL_KEY` themselves, then wait. Never read, print, ask for or type a key. Other blockers: `/genmedia-skills:setup`.
- Reuse of an existing character in a session that already passed preflight: skip this step.
- `assets.enabled` is not `true`: work local only and say nothing about fal Assets.

## UX rules

1. Reply in the user's language. Anchors, style notes and model prompts are English unless on-image or spoken text needs another language. Handles, flags and IDs stay as they are.
2. No JSON, request IDs, URL lists or tool narration in chat. Wait silently; at most one status line per batch.
3. **Question budget: 2 while creating** (Q1 consent when the character is a real person, Q2 approve the hero image), **0 while reusing**. One question at a time, as labelled options (AskUserQuestion when available). Not counted: a cost confirmation under rule 6, and one routing question when a creation request names no subject at all ("make me a character"): `[From my photos] [Invented person] [Mascot or product]`. Everything else is a default you pick: handle (ASCII slug of the name, `Işıl` becomes `isil`), look, roles, which references to keep, model, sizes.
4. The hero image is a human decision: every later reference derives from it. Never treat silence or a successful job as approval. Reference picks after that are reversible (`drop-ref`), so make them yourself.
5. Real people: before any upload or generation, get the user's confirmation that they have the person's consent, and tell them uploads land on public, expiring URLs (`references/platform.md` sections 1 and 9). Record it with `--real-person --consent`. Public figures in deceptive, sexual or defamatory contexts: refuse.
6. Cost: estimate the whole plan (hero candidates plus the sheet, or every shot of a series) with `gm.py price` before its first paid call. Under USD 0.50 run; USD 0.50 to USD 2 announce in one line and run; USD 2 or more, and every training job, show the estimate and wait for a yes. `gm.py preflight` returns the user's own thresholds under `config` (`announce_above_usd`, `confirm_above_usd` from `.genmedia/config.json`); they replace 0.50 and 2. `needs_llms_txt: true` in the price output: rerun with `--explain` and estimate from `pricing_text` before multiplying. Never quote a price from memory, never swap a model the user named.
7. Bounded repair: at most 3 attempts per step, something must change each time, never resend a content-policy rejection unchanged, a job with a request ID is resumed, never resubmitted.

## Discovery guardrail

Routing below is a dated cache (2026-09-19). Before the first paid call to an endpoint in a session: `genmedia models --endpoint_id <id> --json` (must be `active`) and `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <id>`, which resolves the nested shapes and limits the short CLI view drops (`--field <name>` prints one field in full, with its description). Never invent endpoint IDs or parameters. Never run `genmedia run` without an endpoint ID (smart routing resolves stale defaults). A model the user names that you do not know: `genmedia models "<name>" --no-classify --limit 10 --json` (new releases sit under vendor namespaces such as `bytedance/`, `openai/`, `alibaba/`, not `fal-ai/`), take the newest active match, say which one.

## Routing

Intent to flow:

| The user wants | Do |
|---|---|
| A character from their own photos | Workflow A |
| A character from a description | Workflow B |
| `@handle` (or a saved name) in an image or video | Workflow C, zero questions |
| "It does not look like them any more" | Escalation ladder below, then `references/consistency-playbook.md` |
| Two or more saved characters in one scene | Workflow C with several handles; rules in `references/consistency-playbook.md` |
| Highest fidelity, "train it", hundreds of images | `references/training.md` (always confirm cost) |
| List, inspect, change anchor, retire a reference | `character.py list`, `show`, `update`, `drop-ref` |

Endpoint per job (full dated table: `references/routing-image.md`, task `character-identity`):

| Job | Endpoint | Why | Reference input |
|---|---|---|---|
| Hero portrait from text | `bytedance/seedream/v5/pro/text-to-image` | quality-first still default; pass an explicit `image_size` | none |
| Any shot conditioned on the sheet (default) | `fal-ai/nano-banana-2/edit` | top-tier editor, keeps likeness, ratios up to 8:1 for strips | `image_urls` (no documented maximum; send 8 or fewer) |
| Exact camera orbit of one approved image | `fal-ai/qwen-image-edit-2511-multiple-angles` | numeric `horizontal_angle` 0-360, `vertical_angle` -30 to 90, `zoom` 0-10 | `image_urls`, one image |
| Stronger multi-reference | `bytedance/seedream/v5/pro/edit` | documented limit, flat price | `image_urls`, 10 (only the last 10 are used) |
| Most references, or a mask | `openai/gpt-image-2.5/flare/edit` | 16 references plus `mask_url` | `image_urls`, 16 |
| 2K-4K finals | `fal-ai/nano-banana-pro/edit` | premium fidelity | `image_urls` |
| Budget | `alibaba/qwen-image-3/edit` | cheap, identity-preserving | `image_urls` 1-3, cite as "image 1" |
| Trained profile | `fal-ai/phota/edit`, `fal-ai/phota` | identity lives in a `profile_id` | see `references/training.md` |
| Video with references | `bytedance/seedance-2.5/us/reference-to-video` | largest budget, cite `@Image1` | `image_urls`, 30 |
| Video with a structured subject | `fal-ai/kling-video/o3/pro/reference-to-video` | `elements[]`: `frontal_image_url` plus 1-3 `reference_image_urls`, cite `@Element1` | per element |

Tie-breakers:
- Face matters more than wardrobe: spend the reference budget on `face` first, then `full-body`, then the rest. `resolve` already orders them that way.
- More references is not more identity. Past about 6 to 8 images the model averages them; prefer fewer, cleaner references before a bigger model.
- Orbit endpoint versus editor: use the orbit endpoint for side and back views of a full-body image (geometry), the editor for expressions, outfits and any close-up where the face must stay sharp.
- Video: a still that already passed drift QA, used as the first frame, beats any amount of text. Reference-to-video is for shots that cannot start from a still.

Named traps:
- **Literal handle.** A prompt containing `@mara` sent to the CLI is just text. Always resolve, then replace the handle with the anchor.
- **Anchor creep.** Pose, outfit of the day, location, lighting and mood are shot variables. Put them in the anchor and every shot inherits them.
- **Dead links.** A `cdn_url` from an old session can be gone. `file_download_error` means `resolve --refresh`, not a new model.
- **Silent truncation.** Seedream uses only the last 10 images and Phota ignores images after 10; an over-long list loses the face references first or last without an error. Always pass `--max`.
- **Assets is not identity.** A fal Assets character is a reference bundle for fal's web apps, not a fidelity mechanism, and it is disabled on many accounts.
- **No face swap.** No listed image face-swap endpoint exists; do not route to unlisted ones.

Escalation ladder when identity drifts (stop at the first rung that passes QA; details in `references/consistency-playbook.md`):
1. Tighten the anchor: name the 3 to 5 traits that drifted, move variables out.
2. Add or re-role references: a missing angle, a cleaner face close-up; drop the weak one.
3. Switch to a stronger multi-reference model (table above), same references.
4. Video only: lock the first frame (and the last, if needed) with an approved still.
5. Train a profile or LoRA. Expensive, always confirm.

## Workflow

Write every model input as a JSON file under `.genmedia/tmp/` with the Write tool, then pass it with `--input`. No heredocs, no shell-quoted prompts.

### A. Bootstrap from the user's photos

1. Q1 (real person only): consent plus the public-URL notice, one question. Stop on anything but a clear yes.
2. Check the photos against `references/reference-photos.md` (4 to 8 to keep, angles, light, what to reject). Too few or too uniform: say exactly what is missing; offer to generate the missing views in step 5.
3. Write the anchor from what the photos show (`references/character-sheet.md`), then:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" init mara --name "Mara" --description "<anchor>" --style "<style notes>" --real-person --consent
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" add-ref mara ./photos/front.jpg ./photos/smile.jpg --role face
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" add-ref mara ./photos/standing.jpg --role full-body
```

4. Add the best photo first within each role: order is priority. Files are copied into the sheet; nothing is uploaded yet.
5. Optional: fill missing views with Workflow B steps 5 and 6. The reference URLs come from `character.py resolve mara --roles face,full-body --max 3` (this uploads those photos) and take the place of the hero URL. Q2 is then the approval of the first generated view; with photos only, there is no Q2.
6. Deliver with the creation template.

### B. Bootstrap from a description

1. Draft the anchor and style notes from the request; do not interview the user. `init` as above (no `--real-person` for invented characters).
2. Price the whole creation (2 hero candidates plus the sheet of step 5) and apply the cost gate once. Typical total as of 2026-09-19: about USD 0.50 to USD 0.70 (hero candidates ~USD 0.07 each at this size, editor shots ~USD 0.08, orbit views ~USD 0.04), a dated hint, not a quote. Then the hero: 2 candidates on `bytedance/seedream/v5/pro/text-to-image`. The explicit `image_size` matters: the default `auto_2K` bills the higher tier.

```json
{"prompt": "Head-and-shoulders portrait, facing the camera, neutral expression, plain light-grey background, soft even light. <anchor> <style>",
 "image_size": {"width": 1152, "height": 1536}, "num_images": 2}
```

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price bytedance/seedream/v5/pro/text-to-image,fal-ai/nano-banana-2/edit,fal-ai/qwen-image-edit-2511-multiple-angles
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run bytedance/seedream/v5/pro/text-to-image --input .genmedia/tmp/mara-hero.json --label mara --est-cost 0.14
```

3. Q2: write both local paths (`outputs[].path`) in the question itself, numbered; an image you opened with Read is not visible to the user, so never say "shown above". Ask which one is the character (or what to change). Do not continue without an answer; a change request is a new hero attempt (max 3). Then store the pick with its `outputs[].url`, so nothing is uploaded twice:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" add-ref mara "<outputs[].path of the pick>" --role face --cdn-url "<outputs[].url of the pick>"
```

4. Rewrite the anchor to match the approved image (what it shows beats what you planned): `character.py update mara --description "<anchor>"`.
5. Reference sheet as batches (`python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/tmp/mara-sheet.json`; plan JSON, prompts and fields: `references/consistency-playbook.md` section 2), every job with the hero URL in `image_urls`:
   - batch 1 on `fal-ai/nano-banana-2/edit`: full-body front in a neutral pose on a plain background, a slightly turned face, 2 expression close-ups (for example open smile, focused);
   - batch 2 on `fal-ai/qwen-image-edit-2511-multiple-angles`, after the full-body image passed QA, with its URL: `horizontal_angle` 45, 90 and 180;
   - optional 4:1 strip of four views for the user to look at: role `turnaround`.
6. Run drift QA (below) on every result. Keep the best 4 to 8, `add-ref` each with its role and `--cdn-url`. Discard the rest without asking.
7. Deliver with the creation template.

### C. Use a character (image or video), zero questions

1. Find the handles in the request (`@mara`, or a saved name: `character.py list`). Unknown handle: say so, list what exists, stop. Never substitute another character.
2. Pick the endpoint, take its reference cap (`references/consistency-playbook.md` section 1, checked against the schema), then resolve with it. A series of shots is one plan: estimate all of it and apply rule 6 before the first call.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" resolve mara --max 6
```

   Output: `description` (the anchor), `style`, `urls[]` (face first), `legend[]` (index, handle, role), `trained`, `warnings[]`. It uploads a reference only when it has no `cdn_url`; `--refresh` re-uploads all. Uploads create public URLs on the user's fal account: an external side effect, never do it for a character you are not about to use. `--roles face,outfit` narrows; `--no-upload` forbids uploading.
3. Build the prompt: anchor first, then what must not change, then the shot variables, then style. Never leave `@handle` in the text.

```text
The same character as in the reference images: <description>.
Keep identical: face, hair, skin marks, build, <signature item>.
Shot: <action>, <place>, <framing and lens>, <light>, <outfit if it differs>.
Style: <style>.
```

4. Run or hand off. Stills: run here (input below; several shots go into one `gm.py batch` plan, format in `references/cli-contract.md`) or give `image` the same values. A presenter ad, a face thumbnail or another scenario job: give the same values to that skill (`ads`, `youtube-thumbnail`, `short-video`, `video-explainer`, `product-photoshoot`). Video: give `video` the same `urls` plus the anchor; first choice is a QA-passed still as the first frame, otherwise reference-to-video (Seedance cites `@Image1`, Kling takes `face` as `frontal_image_url` and 1 to 3 others as `reference_image_urls`). `trained` present and the user wants maximum fidelity: `references/training.md`, section "Using a trained identity".

```json
{"prompt": "<the four lines of step 3>", "image_urls": ["<urls[0]>", "<urls[1]>"],
 "aspect_ratio": "3:4", "resolution": "1K", "num_images": 1}
```

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run fal-ai/nano-banana-2/edit --input .genmedia/tmp/mara-shot.json --label mara-shots --est-cost 0.08
```

5. Drift QA before delivering, then the reuse template. A result worth keeping as a new reference: `add-ref` it (role `outfit` or `expression`).

### Drift QA (every generated image or keyframe, before the user sees it)

Open the result and the `face` reference with Read and compare: face shape, eyes and brows, nose and mouth; hair colour, length and parting; skin marks (moles, scars, freckles, tattoos) present and on the correct side; build and apparent age; signature items and outfit as the anchor states; hands and extra limbs; black frame or `has_nsfw_concepts`. One clear miss means do not deliver: climb the ladder one rung and retry (max 3). Report honestly when the third attempt still drifts.

## Delivery

Fill in and translate to the user's language; paths, handles and model names stay verbatim.

Creation:

```text
<Name> is saved as @<handle>.
Sheet: .genmedia/characters/<handle>/  (<N> references: <roles>)
Hero: <local path>
Anchor: "<first sentence of the anchor>"
Made with <model display names>, est. cost ~$<X>. Links to the references are public and may expire; the files in the sheet are the durable copies.
Gallery: <gallery_url of the last run>
Use it: "@<handle> <doing something, somewhere>" in any image or video request.
```

Reuse:

```text
<local path(s)>
<cdn url>  (public link, may expire)
@<handle> with <N> references on <model display name>, <size or duration>, est. ~$<X>. Checked against the sheet: face, hair, marks, outfit.
```

## Errors

| Signal | Action |
|---|---|
| `character.py`: `kind:"not_found"` | Handle does not exist here. Show `list`; create it only if the user asks. |
| `character.py`: `kind:"consent"` | `--real-person` without `--consent`. Ask Q1, then rerun with both flags. |
| `character.py`: `kind:"upload"` | Some references did not upload. Use the returned `urls` if the face is among them; otherwise fix the file and rerun `resolve`. |
| `gm.py`: `kind:"validation"` with `fields:[]` and a `request_id` | The job reached `COMPLETED` and failed (`COMPLETED` is not success; it may be billed); queued jobs hide fal's error type. A retry is a new paid job and counts against the 3 attempts. Compare the input with the schema first. If it matches, change one thing per attempt, in this order: `resolve <handle> --refresh` (expired reference URL), a lower `--max` or a downscaled reference, a different face reference, then the content-policy row. |
| `file_download_error`; `sequence_too_long`; `image_too_large`, `file_too_large`, `unsupported_image_format` | In that order: URL expired or unreachable, `resolve <handle> --refresh` and rerun once; too many references, re-resolve with `--max <limit>`; bad file, convert or downscale it locally, `drop-ref` the old one, `add-ref` the new one. |
| `face_detection_error` | The face reference is unusable: ask for, or generate, a clear frontal close-up. |
| `content_policy_violation`, black image, `has_nsfw_concepts` | Never resend unchanged; rewrite the shot, not the person. See `references/platform.md` section 4. |
| `status:"pending"` (exit 0, or exit 1 with `kind:"rate_limit"`, `"server"`, `"auth"`) | Still running, or the result could not be fetched yet: fal did not say the job failed. Run the returned `resume` command (`gm.py wait <endpoint_id> <request_id>`) or the same `batch` command again, once, later. Never resubmit. |
| 403 `authorization_error` on `genmedia assets ...` | fal Assets is off for this account: stay local, do not mention it. |

## Reference index

- `references/character-sheet.md` — read when writing or editing an anchor, choosing roles, or when you need the `character.json` schema and the full `scripts/character.py` command reference.
- `references/reference-photos.md` — read when the user supplies photos, or before generating sheet views: counts, angles, light, rejection list, consent wording.
- `references/consistency-playbook.md` — read when a result drifts, when filling a specific endpoint's reference fields, for video hand-off details and for scenes with several characters.
- `references/training.md` — read when the ladder reaches rung 5 or the user asks to train: Phota profile versus LoRA, dataset ZIP (`character.py pack`), cost gate, storing and using the result.
- `references/assets-mirror.md` — read only when preflight reports fal Assets enabled and the user wants the character visible in fal's web apps.
- `references/routing-image.md` — read when the default endpoint is unavailable or the user asks for cheaper or better: dated tiers, prices, limits (tasks `character-identity`, `image-multiref`, `train-lora`).
- `references/cli-contract.md` — read when a helper or CLI call fails or you need the raw CLI fallback (`scripts/gm.py` usage, JSON shapes, batch plans, resume rules).
- `references/platform.md` — read when handling a fal error type, estimating cost, or deciding what is safe to upload or generate.
