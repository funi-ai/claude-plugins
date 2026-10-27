# Troubleshooting images

For results that are wrong rather than failed, and for failures that the short table in SKILL.md does not cover. Rule for every row: at most 3 attempts per step, change exactly one thing per attempt, say what you changed. Platform error types in full: [platform.md](platform.md) section 4. Helper and CLI failures: [cli-contract.md](cli-contract.md). Field names below were read from live schemas on 2026-09-19.

## Generation looks wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| On-image text misspelt, extra words, mangled diacritics | photo model used for a text job; copy not quoted; too many or too long blocks | Route to `openai/gpt-image-2.5/flare/text-to-image`. Quote each string, add "exact text, nothing else", name risky characters. One wrong block → fix it with the edit endpoint instead of rerolling. Two failures → deliver clean negative space and say the text should be typeset in a design tool. See "Text in the image" in [prompting-image.md](prompting-image.md) |
| Output has the wrong shape or size, no error was raised | wrong size knob for the family (`image_size` sent to an `aspect_ratio` model or the reverse) | Re-read the schema, use the knob it lists, rerun. This was billed; tell the user |
| Seedream job cost twice the estimate | `image_size` left at `auto_2K`, which crossed the 1536x1536 area | Always send `{width,height}` inside the lower tier (1536x1536, 2048x1152, 1152x2048, 1728x1296, 1296x1728) |
| GPT Image job cost far more than expected | `quality` left at the `high` default or set to `max`; large custom size | Set `quality` explicitly; draft at `medium`. Estimate from the per-size table in [routing-image.md](routing-image.md), not from the `1 units` the pricing API returns |
| Plastic skin, glossy render look | praise adjectives, even frontal light, centred pose | Delete "8k, ultra-detailed, perfect". Add two named imperfections and one motivated light from the realism checklist |
| Extra fingers, fused limbs | hands idle and prominent | Give hands a task or crop them out; use `num_images` 2 to 4 and pick; repair one bad hand with an instruction edit |
| Subject centred although off-centre was asked | composition slot missing or late in the prompt | Move "subject on the left third, facing right" to directly after the subject |
| Subject cropped at the edge | ratio too tight for the pose | Name shot size ("full body, feet visible, space above the head") or outpaint afterwards |
| Brand colours drift | colours only named loosely | Vector: `colors` field with RGB values. Raster: name 2 to 4 colours with roles; fix with an edit ("Change: the jacket to deep teal") |
| All variations look the same | over-specified prompt with `num_images` | Vary one slot per job (angle, light or palette) in a batch instead of raising `num_images` |
| Turkish (or other non-English) prompt gives weaker results | models are tuned on English prompts | Translate the brief to English; keep only on-image text in the original language |

## Edit looks wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| The whole picture changed, not just the target | no keep list; model re-imagined the scene | Rewrite as `Change / Keep / Blend`. Still drifting → `openai/gpt-image-2.5/flare/edit`; still → mask the region (recipes 3 and 4 in [editing-recipes.md](editing-recipes.md)) |
| Face or identity drifts | the prompt describes the face and fights the reference; identity image buried among references | Remove the description, refer to "the person from image 1", put the identity image first, drop weak references. Recurring person → `character` skill |
| Product label, logo or shape altered | generative restage touched product pixels | Use a path that does not repaint the product: `pixelcut/product-photo` or `fal-ai/bria/background/replace`. Label must be regenerated legibly → GPT Image 2.5 edit |
| Objects from the style reference appear in the result | role not limited | Manifest line: "image N is a style reference: use only its palette, light and texture" |
| Output ratio differs from the input | endpoint default size, not the input's | GPT Image edit: leave `image_size` at `auto`. Seedream edit: send `{width,height}` in the input's ratio. Nano Banana edit: `aspect_ratio: "auto"` |
| Result is smaller or softer than the input | editor renders at its own resolution | Accept and upscale last; or use an editor with `resolution: "2K"`/`"4K"` |
| Only some references were used | over the limit: Seedream uses the last 10 silently; GPT Image rejects more than 16; Muse more than 10 | Trim to the strongest references; tell the user which were dropped |

## Masks, erasing, outpainting

| Symptom | Likely cause | Fix |
|---|---|---|
| Everything except the target was repainted | mask polarity inverted | Invert the mask (white over the region to change), rerun once |
| GPT Image mask edit: part of the frame came back black, or everything shifted | an opaque black-and-white mask, or the expectation that its mask protects the rest (it does not) | Masked region with the rest untouched → `fal-ai/flux-pro/v1/fill`. Staying on GPT Image → an RGBA mask with the edit area transparent, and accept small changes elsewhere |
| 422 about dimensions on `mask_url` | mask and image differ in pixel size | Resize the mask to the image's exact width and height, upload again |
| Ghost outline or seam where the object was | mask hugs the object too tightly; its shadow or reflection was left outside | Grow the mask by 10 to 20 px (`magick mask.png -morphology Dilate Disk:12 out.png` where ImageMagick exists) and include shadow and reflection; for SAM masks use `mask_type: "automatic"` on `fal-ai/bria/eraser` |
| SAM 3 returned an overlay, not a mask | `apply_mask` left at its default `true` | Send `"apply_mask": false`; look at the mask before using it |
| SAM 3 segmented the wrong thing | default placeholder prompt, or an ambiguous noun | Set `prompt` to a specific noun phrase ("red car on the left"); or add `box_prompts` from a rough box you read off the image |
| Outpaint repeats the subject or tiles a pattern | too much new canvas in one pass | Expand at most about half the original side per pass, `mode: "high"`, run two passes |
| `fal-ai/image-apps-v2/outpaint` shrank the picture | `zoom_out_percentage` defaults to 20 | Send `"zoom_out_percentage": 0` |

## Cut-outs and transparency

| Symptom | Fix |
|---|---|
| Halo or colour fringe around hair, fur, glass | `fal-ai/birefnet/v2` with `"model": "Matting"` (people: `"Portrait"`), `operating_resolution: "2048x2048"`, `refine_foreground` true |
| Holes in a glossy or transparent product | `"General Use (Heavy)"`; if still wrong, `fal-ai/bria/background/remove` |
| Transparency vanished after a later step | a step wrote JPEG (SeedVR and Topaz default to it), or the endpoint drops alpha: SeedVR and Topaz precision do, even with `png` (2026-09-21). Keep `output_format: "png"` (or `webp`) after a cut-out, and put every upscale before the cut-out |
| `pixelcut/product-photo` returned no file, or a huge base64 string | its `sync_mode` defaults to true. Send `"sync_mode": false` |

## Upscale, try-on, vector, layers

| Symptom | Fix |
|---|---|
| Upscale is soft | stay at 2x to 4x per pass; switch to `topaz/upscale/image/precision` (`High Fidelity V3`, or `Low Resolution V2` for compressed sources) |
| Faces changed after upscaling | Topaz `face_enhancement` defaults to true: send false, or use the faithful `fal-ai/seedvr/upscale/image`. Never a generative upscaler on a face that must stay the same |
| Small text warped by the upscaler | `topaz/upscale/image/precision` with `"model": "Text Refine"`; better: render larger natively in GPT Image 2.5 (up to 3840 px) |
| Try-on lost the print or picked the wrong garment area | set `category` and `garment_photo_type` explicitly, `mode: "quality"`, `num_samples` 4; cut out the garment first. Still wrong → `fal-ai/flux-pro/v1/vto` with a styling prompt |
| Try-on output too small | FASHN renders 864x1296: upscale last |
| SVG has thousands of paths, file is huge | the source was a photo or had gradients. Simplify to flat colour first, or generate the mark with `fal-ai/recraft/v4.1/text-to-vector` |
| Letters in the SVG are shapes, not editable text | expected: vector models output paths. Say so; the user sets live type in their design tool |
| You cannot preview an SVG | It is text: check that it contains `<path`. For a look, convert with `rsvg-convert`, `magick` or `qlmanage -t` if present; otherwise ask the user to open it |
| Layerize split too much or too little | name the elements in `prompt` ("separate the bottle, the label text and the background"), or use `fal-ai/qwen-image-layered` with `num_layers` |

## Blocked and black images

- `result.has_nsfw_concepts` contains `true` → that index is a black placeholder. Withhold it, keep the others.
- Families without that array (Seedream 5.0 Pro, GPT Image 2.5, Nano Banana, Recraft, most utilities): open the first output before delivering. A solid black or blank frame is a block, not a result.
- Queued jobs that fail on policy come back as `kind: "validation"` with empty `fields` and a `hint`; the type is not recoverable from the CLI. If the input matches the schema, treat it as a policy or input-fetch problem.
- Reaction: tell the user which part was probably flagged, offer a compliant rewrite, and wait. Do not reword to slip past a filter, do not raise `safety_tolerance`, do not disable `enable_safety_checker`. A block on clearly harmless content may be tried once on another family, and the user is told.
- Assume blocked outputs were billed.

## Input problems

| Symptom | Fix |
|---|---|
| Helper exits 2: `input.image_url … is not a URL` | a local path was passed. Upload first, pass the returned URL |
| Job fails with `file_download_error` on FASHN | `model_image` and `garment_image` have no `_url` suffix, so the helper cannot pre-check them; they still need uploaded URLs |
| `file_download_error` on a chained edit | the earlier CDN URL expired or came from another session. Upload the local file again |
| `image_too_large`, `file_too_large` | downscale locally, then upload: `sips -Z 2048 in.jpg --out out.jpg` (macOS), `ffmpeg -i in.jpg -vf scale=2048:-2 out.jpg`, or `magick in.jpg -resize 2048x2048 out.jpg` |
| `unsupported_image_format`, `image_load_error` (HEIC, AVIF, TIFF, CMYK JPEG) | convert to PNG or sRGB JPEG first (`sips -s format png in.heic --out out.png`, or ffmpeg / magick) |
| Phone photo arrives rotated | bake the EXIF orientation before upload (`magick in.jpg -auto-orient out.jpg`) |
| `image_too_small` | upscale first (recipe 9), then edit |

## Pricing and helper oddities

| Symptom | Fix |
|---|---|
| Price call fails with 400 "Invalid request parameters" | too many IDs in one call (a 55-ID call failed, 10 worked, 2026-09-19). Price in groups of up to 10 |
| Price shows `1 units`, `0.01 units` or another non-image unit | not a per-image price. `needs_llms_txt` is true: rerun `gm.py price <id> --explain` and read `pricing_text`; GPT Image 2.5 also has a dated table in [routing-image.md](routing-image.md) |
| `status: "pending"` | the job is still running. Run the printed `resume` command; never submit again |
| `outputs[].path` is null with an `error` | the download failed, the job did not. Fetch `outputs[].url` with `curl -L -o <path> <url>` |
| `kind: "not_found"` on an ID from this skill | the cache is stale. Next tier in [routing-image.md](routing-image.md), or search the catalog; tell the user which model ran |

## When to stop

After three changed attempts on the same step, stop spending. Report in the user's language: what was tried, what each attempt changed, what the remaining defect is, and the best next option (another family, a mask, text set in post, or a better source image). Show the best attempt so far and let the user decide.
