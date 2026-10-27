# Training an identity (ladder rung 5)

Training is the closest thing fal offers to a trained identity: a Phota profile or a LoRA. It costs dollars, needs a dataset, and the result is tied to one inference family. Reach for it only when rungs 1 to 4 of the ladder are exhausted or the user asks for it. **Every training job needs an explicit yes after a cost estimate, whatever the amount.**

Schemas and prices below were read live on 2026-09-19. Full dated rows: `references/routing-image.md`, tasks `character-identity` and `train-lora`. Re-check the trainer's schema and price before you ask for confirmation.

## 1. Which path

| Path | Train | Use | Dataset | Price hint (2026-09-19, confirm with `gm.py price <ids> --explain`) | Pick when |
|---|---|---|---|---|---|
| Phota profile | `fal-ai/phota/create-profile` | `fal-ai/phota/edit`, `fal-ai/phota` | ZIP of 30 to 50 images of the subject | $2.90 per training run; inference $0.09 per 1K image, $0.18 per 4K | Photoreal person, the user has 30 or more good photos, results should still accept reference images and several base models |
| FLUX.2 LoRA (default LoRA) | `fal-ai/flux-2-trainer-v2` | `fal-ai/flux-2/lora` | ZIP, 10 or more images, captions or `default_caption` | $0.0064 per step; default 1000 steps is about $6.40; inference about $0.021 per megapixel | Mascot, illustrated or stylised character, product; or a person with only 10 to 25 photos |
| Z-Image Turbo LoRA (budget) | `fal-ai/z-image-turbo-trainer-v2` | `fal-ai/z-image/turbo/lora` | ZIP of image and caption pairs, or `default_caption` | $0.00085 per step, 500-step billing floor; default 2000 steps is about $1.70; inference about $0.0085 per megapixel | Cheapest trained identity, high-volume drafts |
| FLUX.1 portrait LoRA (control) | `fal-ai/flux-lora-portrait-trainer` | `fal-ai/flux-lora` | ZIP, 10 or more images | **Price mismatch**: fal's text says $0.0024 per step, the pricing API returns $0.024 per step; default 2500 steps is $6 or $60. Read the model page and quote the higher figure | Only when the user asks for it, or needs `subject_crop` and `trigger_phrase` |

fal describes Phota as personalised photo editing that preserves identity; this skill uses it for photoreal people. For non-photoreal characters a LoRA learns shape and rendering style together, which is what you want there. Never downgrade a path the user named to save money; offer the cheaper one and let them choose.

What training does not give you: a LoRA works only on its own inference endpoint family, takes no reference images there, and does not carry over to video. Video identity stays on rung 4 (frame lock with a trained still) and reference-to-video.

## 2. Dataset

Quality rules are those of `references/reference-photos.md`, scaled up: one subject per image, varied angle, expression, distance, light and background; consistent hair and age; no filters, no occlusion, no near-duplicates. A drifted image in the dataset teaches the drift.

| Source | How |
|---|---|
| The user's photos | Ask for a folder. Real person: the consent question must already be answered (`real_person` in the sheet). |
| An invented character | Generate the missing images from the sheet with Workflow C (different framings, light, expressions, outfits, plain and busy backgrounds), run drift QA on each, keep only passes. This is a paid fan-out: include it in the estimate (for example 20 editor images at about $0.08 each). |

Build the ZIP locally. `pack` takes the active references plus every image in the given folders, removes byte-identical duplicates, names files `001.jpg`, `002.png`, and can write one caption file per image:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" pack mara --from ./photos/mara --caption "photo of MARA01 woman"
```

Output: `{zip, images, captions, bytes, fits:{lora_10_plus, phota_30_to_50}, warnings}`. It uploads nothing and starts nothing.

Captions and trigger token:
- Choose a token that is not a word: the handle in capitals plus digits (`MARA01`). Caption pattern: `photo of MARA01 woman`, `illustration of BOLT01 robot mascot`. Use the same token in every later prompt and store it with `set-trained --trigger`.
- `fal-ai/flux-2-trainer-v2` and `fal-ai/z-image-turbo-trainer-v2`: captions come from `NNN.txt` files in the ZIP or from the `default_caption` input. Their schemas state that missing captions without `default_caption` cause an error, so always provide one of the two.
- `fal-ai/flux-lora-portrait-trainer`: pass `trigger_phrase`; with caption files, `[trigger]` inside a caption is replaced by it.
- `fal-ai/phota/create-profile`: images only, no captions (`pack` without `--caption`).

## 3. Estimate, confirm, run

1. Price in one call; `--explain` adds the trainer's pricing text as `pricing_text`, which decides when `needs_llms_txt` is true or the routing row is tagged mismatch:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price fal-ai/flux-2-trainer-v2,fal-ai/flux-2/lora --explain
```

2. Estimate = dataset generation (if any) + steps x price per step (or the flat run price) + 3 validation images. Quote the higher figure when sources disagree.
3. Ask once (this is the training confirmation, outside the creation budget):

```text
Training @mara as a <Phota profile | FLUX.2 LoRA>:
- dataset: <N> images (<source>)
- cost: about $<X> (training $<a> + dataset $<b> + test images $<c>); repairs are extra
- the ZIP of the photos is uploaded to fal and gets a public link until it expires
- result works on <inference endpoint display name> only; it does not apply to video
[Train now]  [Cheaper option: <name>, about $<Y>]  [Not now]
```

4. After a yes, upload the ZIP and write the trainer input with the Write tool:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload .genmedia/characters/mara/dataset.zip
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run fal-ai/flux-2-trainer-v2 --input .genmedia/tmp/mara-train.json --label mara-train --est-cost 6.40 --download ".genmedia/characters/mara/lora_{index}.{ext}"
```

Trainer inputs (all other fields: leave at their defaults unless the user asks):

| Trainer | Input JSON |
|---|---|
| `fal-ai/phota/create-profile` | `{"image_data_url": "<zip cdn_url>"}`; pass `--no-download` instead of `--download ...` (the two exclude each other; the result is only a `profile_id`) |
| `fal-ai/flux-2-trainer-v2` | `{"image_data_url": "<zip cdn_url>", "default_caption": "photo of MARA01 woman", "steps": 1000}` |
| `fal-ai/z-image-turbo-trainer-v2` | `{"image_data_url": "<zip cdn_url>", "default_caption": "photo of MARA01 woman", "steps": 2000}` |
| `fal-ai/flux-lora-portrait-trainer` | `{"images_data_url": "<zip cdn_url>", "trigger_phrase": "MARA01", "steps": 2500}` (note the plural field name) |

5. Training outlasts one tool call. `gm.py run` returns `status:"pending"` with a `resume` line when its polling budget ends: run that `gm.py wait ...` again later. **Never submit the trainer a second time**; a duplicate is the most expensive mistake in this skill. Wait silently; one status line at most. Do not promise a duration.
6. Read the result: Phota `result.profile_id`; LoRA trainers `result.diffusers_lora_file.url` (and `config_file`). A download template fetches both; on `fal-ai/z-image-turbo-trainer-v2` (2026-09-21) they landed as `lora_0.safetensors` (the weights) and `lora_1.json` (the config). The FLUX.2 trainer returns the same two keys; pick the weights by `outputs[].json_path` (`diffusers_lora_file`), not by index. The `.safetensors` under `.genmedia/characters/<handle>/` is the durable copy; the URL may expire. If it does, upload the local file again and store the new URL.
7. Record it:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" set-trained mara --type lora --endpoint fal-ai/flux-2/lora --lora-url "<diffusers_lora_file url>" --trigger MARA01 --trainer fal-ai/flux-2-trainer-v2
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" set-trained mara --type profile --endpoint fal-ai/phota/edit --profile-id "<profile_id>" --trainer fal-ai/phota/create-profile
```

8. Validate with 2 or 3 cheap test images (front close-up, full body, one scene), run drift QA against the sheet, then deliver: "@mara is trained (<type>); est. cost ~$X; test images: <paths>". A trained identity that fails QA is reported as such, with the likely dataset cause; do not retrain without a new confirmation.

## 4. Using a trained identity

`resolve` returns `trained` when it exists. Use it when the user wants maximum fidelity or volume; otherwise the reference path stays the default (it needs no special endpoint).

Phota profile, editing or restaging (`fal-ai/phota/edit`; `image_urls` is required, 10 at most):

```json
{"prompt": "[[<profile_id>]] as a barista behind a wooden counter, morning window light, 35mm photo",
 "profile_ids": ["<profile_id>"],
 "image_urls": ["<face ref or the scene image to edit>"],
 "base_model": "nb2", "resolution": "1K", "aspect_ratio": "3:4", "num_images": 1}
```

- The prompt field's schema says to refer to a profile as `[[profile_id]]`; the `profile_ids` field's description also mentions `@Profile1` tags. Follow the prompt field, and re-read both descriptions if results ignore the profile.
- `base_model`: `nb2` (default; the only one with `4K`), `qwen-image-2`, `flux-2`, `seedream-5-pro`. `aspect_ratio`: `auto`, `1:1`, `16:9`, `4:3`, `3:4`, `9:16`. `num_images` 1 to 4.
- Text only: `fal-ai/phota` has no `profile_ids` and no `image_urls`; the `[[profile_id]]` in the prompt is the whole link.

LoRA (`fal-ai/flux-2/lora`, `fal-ai/z-image/turbo/lora`: at most 3 LoRAs; `fal-ai/flux-lora`):

```json
{"prompt": "photo of MARA01 woman, <anchor>, reading on a tram, overcast light, 35mm photo",
 "loras": [{"path": "<lora url>", "scale": 1}],
 "image_size": "portrait_4_3", "num_images": 1}
```

- `scale` 0 to 4, default 1. Likeness too weak: raise towards 1.2. Every image looks like the dataset (same pose, same light): lower towards 0.8 and vary the prompt.
- These endpoints are text-to-image: no reference images. To place a LoRA-made character into an existing picture, generate the character first, then use an editor with both images.
- Keep the anchor in the prompt anyway; token plus anchor is more stable than the token alone.
- Drift QA still applies to every result.

## 5. Errors specific to training

| Signal | Action |
|---|---|
| `archive_file_count_below_minimum`, `archive_file_count_exceeds_maximum` (`ctx` has the counts) | Add or remove images, `pack` again, upload again. Tell the user the requirement and the gap. |
| `invalid_archive` | The ZIP is not what the trainer expects: rebuild with `pack` (flat, images at the root). |
| 422 naming a caption problem | Pass `default_caption`, or `pack --caption`. |
| `status:"pending"` from `gm.py run` | Normal. `gm.py wait <endpoint_id> <request_id>`; the ledger (`gm.py ledger --tail 5`) has the ID if the call was killed. |
| Training "completed" but fetching the result fails | `COMPLETED` is not success (`references/cli-contract.md`). Report the failure; a rerun is a new paid job and needs a new yes. |
| `file_download_error` at inference | The LoRA URL expired: upload the local `.safetensors`, `set-trained` with the new URL. |
| Results look like the dataset's background or outfit | Dataset too uniform. Add variety, retrain only with a new confirmation; meanwhile lower `scale`. |
