# Batch plans: two worked shoots

Complete `gm.py batch` plans for a product shoot. Endpoint IDs were active and every input field below was read from the live OpenAPI schema on **2026-09-19**. They are a dated cache: repeat the Discovery guardrail in SKILL.md before spending. `gm.py` and `pipeline.py` abbreviate the calls shown in SKILL.md; run them from the project root (the ledger is `.genmedia/runs.jsonl` in the current directory). Cost lines use prices observed that day; re-price with `gm.py price`.

## Format and rules

```text
gm.py batch --plan <plan.json> [--retry-failed]
pipeline.py fill --template <plan.tmpl.json> --out <plan.json>
pipeline.py add --label <slug> --step <name> --path <file> --url <cdn_url>
pipeline.py urls --label <slug>
```

- Plan keys: `label`, `max_parallel`, `jobs[]` with `id`, `endpoint_id`, `input`, optional `est_cost_usd` and `download`. `download` sits next to `input`, never inside it; default `genmedia-output/<label>/<id>_{index}.{ext}`.
- One `label` for the whole shoot. Job ids are unique across the shoot: `hero`, `s01` ... `s05`, re-rolls `s03-r2`.
- References are whole-string values: `"@product"` (a file registered with `pipeline.py add`), `"@hero"` (first output of job `hero`), `"@hero[1]"` (second output). They work inside arrays and nested objects. `fill` writes nothing while any reference is unresolved.
- The helper refuses non-URL values only in top-level `*_url` and `*_urls` fields. `model_image`, `garment_image` and nested fields such as `background.image_url` have no such net: an unfilled template there is submitted and bills. Always `fill`, always run the filled file.
- Jobs inside one plan are independent. A job that consumes another job's output goes into a later stage file.
- `{LOCK}` and `{LOOK}` in the stage-2 examples stand for the verbatim strings from `plan.md`. Replace them before saving: a placeholder that reaches the model is a wasted job. `fill` refuses one that survived (`{LOCK}`, `{{TOKEN}}`, `<describe it>`) and names the JSON path of every hit; a bracket that belongs in the prompt is escaped `\{ \} \< \>` and the backslash is dropped on write.
- Every paid call: Bash timeout 600000 ms. `status: "pending"` → run the same command again.

## Plan A: hero plus 5 variants (starter set)

Olive oil bottle, label text matters, channel: store listing and Instagram. Lock and look strings: the examples in `fidelity-qa.md` and `variation-matrix.md`.

Upload and register once:

```text
gm.py upload ./bottle-front.jpg ./bottle-label.jpg
pipeline.py add --label zeytin-dali-shoot --step product --path ./bottle-front.jpg --url <cdn_url of the first file>
pipeline.py add --label zeytin-dali-shoot --step product-label --path ./bottle-label.jpg --url <cdn_url of the second file>
```

Stage 1, `stage-1-hero.tmpl.json`: one job, two candidates of one look.

```json
{"label": "zeytin-dali-shoot", "max_parallel": 1, "jobs": [
  {"id": "hero", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.15,
   "input": {
     "prompt": "Figure 1 is the real product; Figure 2 shows its label close up. The product is the 500 ml dark green glass olive oil bottle from Figure 1: square shoulders, short neck, matte black pourer cap, matte cream paper label on the middle of the body. Keep its shape, proportions, glass colour, cap and label exactly as in Figure 1. The label shows an olive-branch line drawing and reads \"ZEYTİN DALI\", \"Soğuk Sıkım Natürel Sızma Zeytinyağı\", \"500 ml\", centred, dark olive on cream. Do not add, remove, translate or restyle any text or drawing on it. Exactly one bottle, 26 cm tall. Scene: the bottle stands on a pale oak kitchen table in a lived-in home kitchen, mid-morning. Beside it, smaller than the bottle: a torn piece of sourdough bread on a linen napkin and a small unglazed ceramic bowl. Background softly out of focus. Look: palette of deep green and cream taken from the label, warm pale oak and unglazed ceramic surfaces, one accent of lemon yellow. Soft window light from camera left, neutral white, gentle shadows falling right. 50 mm feel at eye level, background softly out of focus. Natural contrast, true colours. Unhurried, domestic. No text, logos or watermarks except the product's own label. Camera: front three-quarter from the right at eye level. Composition: bottle on the right third filling about 40 percent of the frame height, calm area on the left for copy. Physical: true scale, soft contact shadow on the oak, reflections on the glass consistent with the window. Exactly one bottle.",
     "image_urls": ["@product", "@product-label"],
     "image_size": {"width": 1344, "height": 1680}, "num_images": 2, "output_format": "png"}}
]}
```

`fill`, `batch`, fidelity QA on `hero_0.png` and `hero_1.png`, hero checkpoint, **stop**. The user picks candidate 2 → `Hero: @hero[1]` goes into `plan.md`.

Stage 2, `stage-2-shots.tmpl.json`: the five remaining shots as ONE batch.

```json
{"label": "zeytin-dali-shoot", "max_parallel": 5, "jobs": [
  {"id": "s01", "endpoint_id": "openai/gpt-image-2.5/flare/edit", "est_cost_usd": 0.16,
   "input": {"prompt": "image 1 is the real product; image 2 shows its label close up; image 3 is the approved campaign shot: match its palette, light and grade, not its composition. {LOCK} Scene: the bottle alone on a seamless warm cream backdrop. {LOOK} Camera: straight front at label height. Composition: bottle centred, filling 70 percent of the frame height, every line of the label sharp and readable. Physical: soft contact shadow, no reflections of other objects. Exactly one bottle.",
     "image_urls": ["@product", "@product-label", "@hero[1]"],
     "image_size": {"width": 1536, "height": 1536}, "quality": "high", "num_images": 1, "output_format": "png"}},
  {"id": "s02", "endpoint_id": "pixelcut/product-photo", "est_cost_usd": 0.03,
   "input": {"image_url": "@product", "sync_mode": false, "image_size": {"width": 2000, "height": 2000},
     "background": {"mode": "Color", "color": {"r": 255, "g": 255, "b": 255}},
     "shadow": {"type": "Drop"}, "margin": {"all": "8%"}, "output_format": "jpeg"}},
  {"id": "s03", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.08,
   "input": {"prompt": "Figure 1 is the real product; Figure 2 shows its label close up; Figure 3 is the approved campaign shot: match its palette, light and grade, not its composition. {LOCK} Scene: a relaxed adult hand enters from the right edge and tilts the bottle to pour a thin stream of oil into the small unglazed bowl on the oak table; label facing the camera, fingers on the lower third of the bottle and not covering the label; hand anatomically natural, five fingers. {LOOK} Camera: front three-quarter from the right at eye level. Composition: bottle in the lower-right, calm area on the left. Physical: bottle 26 cm tall, clearly larger than the hand's width; contact shadows consistent. Exactly one bottle.",
     "image_urls": ["@product", "@product-label", "@hero[1]"],
     "image_size": {"width": 1344, "height": 1680}, "num_images": 1, "output_format": "png"}},
  {"id": "s04", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.08,
   "input": {"prompt": "Figure 1 is the real product; Figure 2 shows its label close up; Figure 3 is the approved campaign shot: match its palette, light and grade, not its composition. {LOCK} Scene: top-down flat lay, camera exactly overhead. The bottle lies on its back, label up, diagonally on the pale oak table. Around it with clear gaps: a handful of green olives, half a lemon, a sprig of fresh thyme. Short soft shadows all falling to the right. {LOOK} Composition: clean area along the top edge. Exactly one bottle.",
     "image_urls": ["@product", "@product-label", "@hero[1]"],
     "image_size": {"width": 1536, "height": 1536}, "num_images": 1, "output_format": "png"}},
  {"id": "s05", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.08,
   "input": {"prompt": "Figure 1 is the real product; Figure 2 shows its label close up; Figure 3 is the approved campaign shot: match its palette, light and grade, not its composition. {LOCK} Scene: same kitchen and table as Figure 3, recomposed for a vertical frame: the bottle stands in the lower-middle in front of a plain pale plaster wall. {LOOK} Camera: straight front at eye level. Composition: bottle fills about a third of the frame height; the top two fifths are plain wall, kept empty for a headline; nothing important in the bottom tenth. Exactly one bottle.",
     "image_urls": ["@product", "@product-label", "@hero[1]"],
     "image_size": {"width": 1152, "height": 2048}, "num_images": 1, "output_format": "png"}}
]}
```

- Why these routes: `s01` is the label shot, so it goes to GPT Image 2.5 (`quality` set on purpose; its prompt says `image 1`, so write the lock string's "Figure 1" as "image 1" in that one job). `s02` is the listing image: non-generative. `s03` to `s05` are scenes: Seedream.
- Cost math (2026-09-19): hero 2 x ($0.0675 + 1 x $0.0045) = $0.144. `s01`: next larger row of the GPT Image cost table at `high` ($0.055) + 2 x the reference allowance of `platform.md` §7 = about $0.16. `s02` $0.024. `s03`-`s05`: 3 x ($0.0675 + 2 x $0.0045) = $0.23. Total about $0.56; worst case with every re-roll spent, about $1.70. At the default thresholds ($0.50 announce, $2 confirm) round up and announce it in one line; the hero stop happens whatever the cost.
- The hero doubled as the canary for the Seedream endpoint. `s01` and `s02` are the first calls to their endpoints, one job each: no extra canary needed.

## Plan B: packshot to lifestyle chain

Tan leather backpack, phone photo on a cluttered floor. The clean packshot becomes the reference for everything after it, so the model never sees the clutter.

Stage 1, `stage-1-pack.tmpl.json`: listing packshot and a transparent cut-out (after `upload` + `add --step product`).

```json
{"label": "kuzey-backpack", "max_parallel": 2, "jobs": [
  {"id": "pack-white", "endpoint_id": "pixelcut/product-photo", "est_cost_usd": 0.03,
   "input": {"image_url": "@product", "sync_mode": false, "image_size": {"width": 2000, "height": 2000},
     "background": {"mode": "Color", "color": {"r": 255, "g": 255, "b": 255}},
     "shadow": {"type": "Drop"}, "margin": {"all": "10%"}, "output_format": "png"}},
  {"id": "pack-cutout", "endpoint_id": "pixelcut/product-photo", "est_cost_usd": 0.03,
   "input": {"image_url": "@product", "sync_mode": false, "image_size": {"width": 2000, "height": 2000},
     "background": {"mode": "Transparent"}, "margin": {"all": "6%"}, "output_format": "png"}}
]}
```

QA both (edges, straps not clipped, no floor left between the handles). Stage 2, `stage-2-hero.tmpl.json`: the lifestyle hero is built on the packshot.

```json
{"label": "kuzey-backpack", "max_parallel": 1, "jobs": [
  {"id": "life-hero", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.14,
   "input": {"prompt": "Figure 1 is the real product on a white background. The product is the tan full-grain leather backpack from Figure 1: single top flap with two brass buckles, one front pocket, rolled top handle, contrast cream stitching, and the small embossed word \"KUZEY\" centred on the flap. Keep its shape, proportions, leather colour and grain, buckles, stitching and embossing exactly as in Figure 1. Do not add pockets, zips, tags or text. Exactly one backpack, 42 cm tall. Scene: the backpack rests upright on a worn wooden bench in a bright hallway by the front door, mid-morning; a wool coat hangs out of focus behind it. Look: palette of tan leather, cream and warm grey plaster, one accent of dark navy. Soft daylight from a door on camera right, neutral white, gentle shadows falling left. 50 mm feel slightly above eye level, background softly out of focus. Natural contrast, true colours. Everyday, ready to leave. No text, logos or watermarks except the product's own embossing. Composition: backpack on the left third filling half the frame height, calm wall on the right. Physical: true scale on the bench, soft contact shadow.",
     "image_urls": ["@pack-white"],
     "image_size": {"width": 1344, "height": 1680}, "num_images": 2, "output_format": "png"}}
]}
```

Hero checkpoint, **stop**. The user picks candidate 1 → `@life-hero[0]`. Stage 3, `stage-3-shots.tmpl.json`: a second scene, a background-only budget variant, and the site banner extended from the approved hero.

```json
{"label": "kuzey-backpack", "max_parallel": 3, "jobs": [
  {"id": "life-02", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.08,
   "input": {"prompt": "Figure 1 is the real product on a white background; Figure 2 is the approved campaign shot: match its palette, light and grade, not its composition. {LOCK} Scene: the backpack stands on the passenger seat of a parked car, door open, street softly out of focus behind. {LOOK} Camera: front three-quarter from the left, slightly above. Composition: backpack centred low, filling 40 percent of the frame. Exactly one backpack.",
     "image_urls": ["@pack-white", "@life-hero[0]"],
     "image_size": {"width": 1344, "height": 1680}, "num_images": 1, "output_format": "png"}},
  {"id": "bg-01", "endpoint_id": "fal-ai/bria/background/replace", "est_cost_usd": 0.04,
   "input": {"image_url": "@pack-white", "prompt": "on a worn wooden bench in a bright hallway, warm grey plaster wall, soft daylight from the right", "refine_prompt": true, "num_images": 1}},
  {"id": "banner", "endpoint_id": "fal-ai/flux-2-pro/outpaint", "est_cost_usd": 0.15,
   "input": {"image_url": "@life-hero[0]", "expand_left": 0, "expand_right": 1648, "expand_top": 0, "expand_bottom": 0, "mode": "high", "output_format": "png"}}
]}
```

- `banner`: 1344 + 1648 = 2992 px wide at 1680 px high, close to 16:9; the approved pixels stay and the calm right side grows into copy space. Outpaint bills the first output megapixel plus every extra megapixel of input and output, each rounded up (here 6 MP out, 3 MP in: $0.03 + 5 x $0.015 + 3 x $0.015 = about $0.15): confirm the rule in `pricing_text`.
- `bg-01` keeps the product as photographed, including its light: judge whether the light direction fits the new background and check the edges; if it does not fit, drop it rather than re-roll it.
- Cost math: packshots 2 x $0.024; hero 2 x $0.0675; `life-02` $0.0675 + $0.0045; `bg-01` $0.04; `banner` about $0.15. Total about $0.45.

Composite fallback (after two failed generative attempts on a shot, `fidelity-qa.md` section 3): a plate job, QA that the plate is empty, then, in a later stage file, the real product on it.

```json
{"label": "kuzey-backpack", "max_parallel": 1, "jobs": [
  {"id": "life-02-plate", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Remove the backpack from Figure 1 completely. Keep the car seat, the open door, the street, the light and the direction of the shadows exactly. Leave the spot where it stood empty and clean. No new objects, no text.",
     "image_urls": ["@life-02"], "image_size": {"width": 1344, "height": 1680}, "num_images": 1, "output_format": "png"}}
]}
```

```json
{"label": "kuzey-backpack", "max_parallel": 1, "jobs": [
  {"id": "life-02-comp", "endpoint_id": "pixelcut/product-photo", "est_cost_usd": 0.03,
   "input": {"image_url": "@product", "sync_mode": false, "image_size": {"width": 1344, "height": 1680},
     "background": {"mode": "Image", "image_url": "@life-02-plate", "image_fit": "Cover"},
     "shadow": {"type": "Generative"}, "margin": {"all": "22%"}, "output_format": "png"}}
]}
```

## Re-rolls, repairs, try-on

Weak but completed shot: a new id in a small plan, same label, changed input. The old file stays on disk; later stages and the delivery point at the new id.

```json
{"label": "zeytin-dali-shoot", "max_parallel": 1, "jobs": [
  {"id": "s03-r2", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.08,
   "input": {"prompt": "<s03 prompt with the grip changed to: the bottle rests upright on an open palm, label facing the camera>",
     "image_urls": ["@product", "@product-label", "@hero[1]"],
     "image_size": {"width": 1344, "height": 1680}, "num_images": 1, "output_format": "png"}}
]}
```

Failed job (error, no image): fix its input in the template, `fill`, then rerun the stage file with `--retry-failed`. The flag resubmits every failed id in that file, so fix them all or run a file that holds only the repaired ids.

Try-on stage (garment and model registered as `garment` and `model`; consent confirmed when the person is real):

```json
{"label": "keten-gomlek", "max_parallel": 1, "jobs": [
  {"id": "tryon", "endpoint_id": "fal-ai/fashn/tryon/v1.6", "est_cost_usd": 0.15,
   "input": {"model_image": "@model", "garment_image": "@garment", "category": "tops", "garment_photo_type": "flat-lay", "mode": "quality", "num_samples": 2, "output_format": "png"}}
]}
```

Estimate `num_samples` x the per-generation price until `gm.py price` or the model page says otherwise. The approved try-on result then becomes Figure 1 of a scene job (`modes.md`, mode 11), with the garment re-checked afterwards.

Finish with `pipeline.py manifest --label <slug>` and the delivery template in SKILL.md.
