# Input prep for image-to-3D (verified 2026-09-20)

An image-to-3D model has no idea which pixels are "the product": the background, the hand, the shadow and the second item all end up **welded into the same mesh**. Fixing the picture costs cents and seconds; a wrong mesh costs the full call and minutes. Run this file before every image-based call. Endpoint fields: [models-3d.md](models-3d.md).

## 1. The input checklist

Open every input with the Read tool first. Judge each line; one "no" means fix before paying.

| # | Check | Why it matters | Fix |
|---|---|---|---|
| 1 | Exactly one object (one figure) in the picture | several items come back as one lump; a turnaround sheet comes back as a single sculpture of all its panels | crop one item per image (section 3); a set of separate items is one mesh call per item |
| 2 | Whole object inside the frame, with a margin | a cropped edge becomes a flat cut surface | ask for a wider photo, or hand off to `/genmedia-skills:image` to extend the canvas; never let the mesh model guess a missing half silently |
| 3 | Object fills more than about half of the frame | Hunyuan's own schema tip; a tiny object gets tiny detail | crop tighter, keep a margin |
| 4 | Plain, contrasting background | clutter, tabletops and walls get reconstructed as geometry | background removal (section 4) |
| 5 | Nothing touches or covers it: no hand, stand, packaging, cable, second product | occluders are baked into the shape | re-shoot, or hand off to `/genmedia-skills:image` for removal; check that the edit did not change the product |
| 6 | Neutral, even light; no hard cast shadow, no blown highlights | shadows become dark texture and floor plates; highlights are baked in as white paint | re-shoot in shade or a light tent; Rodin `texture_delight` and Hi3D `shading` reduce baked light afterwards |
| 7 | Little perspective distortion: shot from a distance with a longer lens, roughly at the object's mid height, three-quarter front or straight front | a wide-angle close-up stretches the near side into the geometry | re-shoot from further away and crop |
| 8 | Sharp, at least about 1024 px on the long side | blur becomes mushy geometry and texture | better photo, or upscale through `/genmedia-skills:image` for real photos only |
| 9 | No text overlays, watermarks, borders, stickers added in an app | they become part of the texture | use the original file |
| 10 | Format and size inside the endpoint's limits (section 2) | avoids a paid-side 422 | convert locally |

Characters that will be rigged, in addition: full body, feet visible, **A-pose or T-pose** (arms away from the torso, legs apart, fingers visible), no cape, bag, weapon or long hair crossing the silhouette, facing the camera. Arms held against the body come back welded to the torso, and the auto-rig then has no separate limb to bind. Meshy `pose_mode` and Rodin `TAPose` normalise a pose, but they cannot separate limbs that the picture fuses.

Known weak spots of every current image-to-3D model (say so **before** paying, offer to proceed anyway): clear glass and liquids, mirror chrome, thin wires and spokes, hair and fur, foliage, lace and meshes, fine printed text on labels (it comes back as a blurry texture, never as readable text), and interiors (a mug is usually hollow only as far as the picture shows).

## 2. Limits per endpoint (from the live schemas)

| Endpoint family | Stated input limits |
|---|---|
| Hunyuan3D v3.1 Pro and Rapid | 128 to 5000 px per side, at most 8 MB, JPG, PNG or WEBP; extra views JPG or PNG recommended |
| Meshy 7.1 | jpg, jpeg, png; AVIF and HEIF are converted by the endpoint; multi-image takes 1 to 4, extras are ignored |
| Hi3D v3.0 | PNG, JPEG or WebP, at most 20 MB per image |
| Rodin v2.5 | 1 to 5 images in `image_urls`; no size limit stated |
| Tripo H3.1, Trellis 2 | no limit stated in the schema |

No limit stated → send a PNG or JPEG of about 1024 to 2048 px and under 8 MB; a typed 422 (`image_too_large`, `file_too_large`, `unsupported_image_format`) names the real limit if there is one.

Local conversion, whichever tool exists (both are optional; ask the user to export a PNG or JPEG if neither does):

```bash
sips -s format png IMG_1234.heic --out .genmedia/tmp/mug-front.png
ffmpeg -v error -y -i IMG_1234.heic -vf "scale='min(2048,iw)':-2" .genmedia/tmp/mug-front.png
```

Read the converted file before uploading it. Uploads are public URLs: say so once for unreleased products and for photos of people.

## 3. One object per image: cropping sheets and sets

A character sheet, a turnaround or a collage is never sent as one image. Cut it up first. Multi-view endpoints need the **same pose in every panel**: when that holds, each panel becomes its own file and goes into its own view slot; when the panels show different poses or expressions, keep only the clearest panel (front or three-quarter) and use a single-image endpoint.

```bash
ffmpeg -v error -y -i sheet.png -vf "crop=820:1400:40:60" .genmedia/tmp/hero-front.png
```

`crop=width:height:x:y` in pixels from the top-left corner. Read each crop: the whole figure, nothing of its neighbour.

## 4. Background removal (one mechanical call, kept in this skill)

Endpoint `fal-ai/birefnet/v2` (task `bg-remove-image` in [routing-image.md](routing-image.md); active and schema-checked 2026-09-20). Input, written to `.genmedia/tmp/<slug>-cutout.json`:

```json
{"image_url": "<uploaded photo url>", "model": "General Use (Heavy)", "operating_resolution": "2048x2048", "output_format": "png"}
```

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run fal-ai/birefnet/v2 --input .genmedia/tmp/<slug>-cutout.json --label "<slug>" --est-cost 0.01 --download "genmedia-output/<slug>/cutout_{index}.{ext}"
```

- Upload the photo first (`gm.py upload`), run the call, then pass the cut-out's `outputs[0].url` straight on as the mesh input (no second upload). Output: `image` (a PNG with transparency). Compute-billed at a fraction of a cent per image (pricing API: $0.0008 per compute second on 2026-09-19).
- **Read the cut-out.** Thin parts (handles, straps, antennas, glass edges) are what matting loses. A damaged cut-out is worse than a busy background: try `"model": "Matting"` once, else keep the original and crop tighter.
- Transparency: Rodin documents `use_original_alpha` for it. Hunyuan 3.1 Pro and Tripo H3.1 took a BiRefNet cut-out cleanly on 2026-09-21: no backing plate, no halo (`platform.md` section 10). Default: send the transparent PNG; if the mesh comes back with a backing plate or a dark halo, flatten the cut-out onto white and rerun (that is one of the three repair attempts):

```bash
ffmpeg -v error -y -i cutout_0.png -filter_complex "[0:v]split[a][b];[a]drawbox=c=white:t=fill,format=rgb24[bg];[bg][b]overlay=format=auto" -frames:v 1 cutout-white.png
```

Anything beyond a clean cut-out (remove a hand, rebuild a cropped corner, relight, change the angle of a real product) is image craft: `/genmedia-skills:image`, or `/genmedia-skills:product-photoshoot` when product fidelity matters. Take back a file path and its URL.

## 5. No picture yet: the reference-picture brief

For a description-only request, the default is a picture first, because a picture can be checked and fixed for cents. Hand this brief to `/genmedia-skills:image` (fill the slots; English; one image, square, at least 1024 px):

```text
Reference image for 3D reconstruction. ONE <object, with its defining parts, materials and colours>,
the whole object in frame with a clear margin, centred, <three-quarter front view | straight front view>,
shot from a distance with a long lens (minimal perspective), camera at the object's mid height.
Plain seamless light-grey background, soft even studio light from both sides, no hard shadows,
no reflections of a room, no floor texture. No text, no logo, no props, no hands, no second object.
Matte, clearly readable surfaces; every part fully visible, nothing cropped.
```

Character variant (for rigging): replace the view line with `full body, straight front view, neutral A-pose: arms held about 30 degrees away from the torso, legs slightly apart, fingers visible, feet on the ground, neutral face`, and add `no cape, no bag, no weapon, hair tied back, nothing crossing the silhouette`.

Style note: a stylised look (clay, toy, low-poly, anime) is set **in this picture**; the mesh model copies what it sees. Low-poly as actual geometry is a Meshy `model_type` or a polygon budget, not a picture style.

Self-check the returned picture against section 1 (Read it). Show it to the user and wait for a yes when the mesh call will cost `announce_above_usd` or more, when it is a character or a hero asset, or when the description left real design choices open. Otherwise state its path in the delivery and continue. An `@handle` character: `/genmedia-skills:character` owns the identity and its sheet; ask it for one front A-pose view, not the sheet.

## 6. Orbit views for multi-view endpoints

When: the back and sides matter (360 degree product viewer, characters, anything viewed from behind) or a single-view mesh came back with a melted back. Real photos of the other sides are better than generated ones; use them when the user has them (section 7).

Generated views: `fal-ai/qwen-image-edit-2511-multiple-angles` (active and schema-checked 2026-09-20; listed under `character-identity` in [routing-image.md](routing-image.md)). Fields: `image_urls`* (the one front picture), `horizontal_angle` 0 to 360 (the schema: 0 front, 90 right side, 180 back, 270 left side), `vertical_angle` -30 to 90 (0 = eye level), `zoom` 0 to 10 (5 = medium), `image_size` (defaults to the input's size), `output_format`, `num_images` 1 to 4, `seed`, optional `additional_prompt`. Price: $0.035 per megapixel, about $0.04 per 1024x1024 view.

Plan, written with the Write tool to `.genmedia/tmp/<slug>-views.json`:

```json
{"label": "<slug>", "max_parallel": 3, "jobs": [
  {"id": "view-right", "endpoint_id": "fal-ai/qwen-image-edit-2511-multiple-angles", "est_cost_usd": 0.04,
   "input": {"image_urls": ["<front url>"], "horizontal_angle": 90, "vertical_angle": 0, "zoom": 5, "num_images": 1, "output_format": "png"}},
  {"id": "view-back", "endpoint_id": "fal-ai/qwen-image-edit-2511-multiple-angles", "est_cost_usd": 0.04,
   "input": {"image_urls": ["<front url>"], "horizontal_angle": 180, "vertical_angle": 0, "zoom": 5, "num_images": 1, "output_format": "png"}},
  {"id": "view-left", "endpoint_id": "fal-ai/qwen-image-edit-2511-multiple-angles", "est_cost_usd": 0.04,
   "input": {"image_urls": ["<front url>"], "horizontal_angle": 270, "vertical_angle": 0, "zoom": 5, "num_images": 1, "output_format": "png"}}
]}
```

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/tmp/<slug>-views.json
```

600000 ms Bash timeout; `pending` → the same command again. Take each view's URL from `jobs[].outputs[0].url` and its file from `jobs[].outputs[0].path`.

**Read every view next to the front picture.** Keep a view only if: same object, same proportions and colours, same parts (nothing added, nothing missing), plain background, whole object in frame. Drop a bad view instead of re-rolling it more than once: a multi-view call with a wrong view is worse than a single-view call. Tell the user once: these sides are a model's guess, not their product.

View-to-field mapping:

| View (`horizontal_angle`) | Hunyuan v3.1 Pro | Tripo H3.1 multiview `image_urls` index | Hi3D v3.0 multi-view | Meshy 7.1 multi-image, Rodin v2.5 |
|---|---|---|---|---|
| front (0) | `input_image_url` | 0 | `front_image_url` | first item of `image_urls` |
| left side (270) | `left_image_url` | 1 | `left_image_url` | any order |
| back (180) | `back_image_url` | 2 | `back_image_url` | any order |
| right side (90) | `right_image_url` | 3 | `right_image_url` | any order |
| 45 degree fronts (315, 45), top (`vertical_angle` 90) | `left_front_image_url`, `right_front_image_url`, `top_image_url` | not accepted | not accepted | optional extra items, within the 4 or 5 image maximum |

Tripo's list is positional (front, left, back, right; front required) and the schema offers no way to skip a slot: with only a front and a back view, use Hunyuan's named fields instead of putting the back view into the "left" position. "Left" and "right" are taken from each schema's own wording; no schema defines whether they mean the object's side or the viewer's. If side details come out mirrored on the mesh, swap the two side views: that is one repair attempt.

## 7. Several real photos from the user

- Same object, same state (lid on in all, or off in all), same light, same distance, camera at the same height, one view per file.
- Run the checklist on every photo; remove the background of each the same way.
- Name the views yourself after Reading them (front, back, left, right); never trust file names.
- More than the endpoint takes → keep front, back, then the side that shows the most unique detail.
- Do not mix a real front with generated sides of a different look unless the user agrees; state which views were real.

## 8. What to record

Keep the prepared files under `genmedia-output/<slug>/` (front, cut-out, views): they are the evidence for a repair and the inputs for a later retexture. Mention in the delivery which inputs were the user's, which were edited and which were generated.
