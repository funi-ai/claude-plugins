# Shot modes

Every mode of a product shoot: when to use it, default ratio, endpoint, prompt template, pitfalls. Endpoint IDs were active and every field below was read from the live OpenAPI schema on **2026-09-19**; repeat the Discovery guardrail in SKILL.md before spending. `gm.py` and `pipeline.py` abbreviate the calls shown in SKILL.md. `{LOCK}` is the product lock string (`fidelity-qa.md`), `{LOOK}` the look string (`variation-matrix.md`); both are pasted verbatim into every generative prompt of the shoot.

## Mode chooser

| The user says | Mode | Default ratio |
|---|---|---|
| "white background", "marketplace main image", "catalog", "beyaz fon" | 1 packshot | 1:1 |
| "in a kitchen", "on a desk", "lifestyle", "in use" | 2 lifestyle scene | 4:5 |
| "from above", "flat lay", "with its ingredients / accessories" | 3 flat lay | 1:1 or 4:5 |
| "website header", "banner", "cover", "kampanya görseli" | 4 hero banner | 16:9 (21:9 or 3:1 on request) |
| "someone holding it", "in hand", "worn" (not clothing) | 5 in-hand and on-model | 4:5 |
| "how big is it", "next to", "fits in a bag" | 6 scale and context | 4:5 |
| "texture", "close-up", "stitching", "the cap detail" | 7 detail macro | 1:1 |
| "Christmas", "summer", "Ramazan", "Black Friday", "launch campaign" | 8 seasonal or campaign look | as the base mode |
| "pin", "story", "reel cover", "square post" | 9 social formats | 2:3, 9:16, 1:1 |
| "N variants", "ad set", "A/B creatives", "carousel" | 10 ad pack | 1:1 + 4:5 |
| "put this shirt on a model", "on a mannequin", "manken üstünde" | 11 apparel try-on | 2:3 or 3:4 |

Two modes fit → the one that names the channel wins (a "Christmas story" is mode 9 with a mode 8 look). Nothing fits → mode 2.

## Sizes

One table for Seedream 5.0 Pro edit and GPT Image 2.5 edit: every size stays in Seedream's lower price tier (area up to 1536x1536) and meets GPT Image's rules (both sides multiples of 16, long side up to 3840, aspect up to 3:1). Send it as `"image_size": {"width": W, "height": H}`.

| Ratio | W x H | Typical use (platform specs change: check the platform's current rules) |
|---|---|---|
| 1:1 | 1536 x 1536 | store listing, feed post, carousel |
| 4:5 | 1344 x 1680 | portrait feed post, ad |
| 3:4 | 1296 x 1728 | lookbook, try-on plate |
| 2:3 | 1248 x 1872 | pin |
| 9:16 | 1152 x 2048 | story, reel or short cover |
| 16:9 | 2048 x 1152 | site hero, slide, video thumbnail |
| 3:2 | 1872 x 1248 | editorial, blog |
| 1.91:1 | 2048 x 1072 | link preview, landscape ad |
| 21:9 | 2240 x 960 | wide site banner |
| 3:1 | 2640 x 880 | strip banner (GPT Image's widest) |

Other families use other knobs: `fal-ai/nano-banana-pro/edit` takes `aspect_ratio` + `resolution`; Bria product-holding and try-on take an `aspect_ratio` enum; Pixelcut takes `image_size`; Bria product-shot takes `shot_size`. The wrong knob is ignored without an error and the job bills in full.

## Prompt skeleton (all generative modes)

```text
Figure 1 is the real product[; Figure 2 shows its label close up][; Figure 3 is the approved campaign shot: match its palette, light and grade, not its composition].
{LOCK}
Scene: <mode slots>
Look: {LOOK}
Camera: <angle inside what the references show>, <lens feel>, <depth of field>.
Composition: <where the product sits, how much of the frame it fills>, <copy space: none | clean area top / left / right>.
Physical: true scale, contact shadow on the surface, reflections consistent with the material and the light.
No added text, logos, stickers or watermarks anywhere except the product's own label. Exactly <n> product[s].
```

- Seedream's own schema example addresses references as `Figure 1`, `Figure 2`; on GPT Image 2.5 and Nano Banana write `image 1`, `image 2`. Order = order in `image_urls`. Product references first, hero last. Swapping "Figure" for "image" is the only edit ever made to the pasted lock string.
- State the product first, the scene second. A prompt that opens with the scene gets a scene with a lookalike in it.
- Quote on-pack text exactly, in its own language: `the label reads "ZEYTİN DALI"`. Everything else is English.
- Name light by direction, quality and colour temperature ("soft window light from camera left, neutral white"); coloured light on the product causes colour-fidelity failures.
- Never write "beautiful", "stunning", "8k", "award-winning". Name the surface, the light and the lens instead.

## 1. Packshot

When: marketplace main image, catalog grid, any place the real item must be shown untouched. Default 1:1, white.

Endpoint `pixelcut/product-photo` → `.result.image.url`. No prompt. The product is cut out and composited; nothing is generated on it.

```json
{"image_url": "<url:product>", "sync_mode": false,
 "image_size": {"width": 2000, "height": 2000},
 "background": {"mode": "Color", "color": {"r": 255, "g": 255, "b": 255}},
 "shadow": {"type": "Drop"}, "margin": {"all": "8%"}, "output_format": "jpeg"}
```

- `background.mode`: `Color` (default white), `Transparent` (always PNG; never with `output_format: "jpeg"`), `Image` with `image_url` and `image_fit` `Cover` / `Contain` / `Stretch`.
- `shadow.type`: `Drop` (deterministic; `shadow.drop` has `horizontal`, `vertical`, `blur`, `opacity`, `color`) or `Generative` (`shadow.generative.opacity`, optional `light_source`). Omit `shadow` for none. A strict marketplace main image: no shadow or a faint `Drop`.
- `margin.all` as `"8%"` (0 to 49%) or px; per-side overrides `top`, `right`, `bottom`, `left`. A smaller margin = the product fills more of the frame.
- `sync_mode` defaults to **true** on this endpoint: always send `false`.
- Pitfalls: the canvas can be larger than the source supports; a 900 px phone crop on a 2000 px canvas is soft: check, and ask for a better photo rather than upscaling a label. The cut-out inherits the source's light and angle: a crooked or yellow-lit source gives a crooked, yellow packshot. Source unusable → mode 2 template with `Scene: seamless pure white studio sweep, soft even light, faint contact shadow` on the generative route, plus strict QA, and tell the user it is a generated rendition.
- Brand-colour backdrop: same call with `color` from the brand palette. Backdrop from an approved empty scene: `background.mode: "Image"` (this is also the composite fallback in `fidelity-qa.md`).

Background swap that keeps the photo's own perspective and light: `fal-ai/bria/background/replace` → `.result.images[].url`.

```json
{"image_url": "<url:product>", "prompt": "on a pale oak table, softly blurred bright kitchen behind, morning light from the left", "refine_prompt": true, "num_images": 2}
```

Give `prompt` or `ref_image_url`, never both. Also `negative_prompt`, `seed`, `fast` (default true). The foreground keeps its original light, so describe a background whose light direction matches the photo.

## 2. Lifestyle scene

When: the product in the place it is used. Default 4:5. Endpoint `bytedance/seedream/v5/pro/edit` (label large in frame → `openai/gpt-image-2.5/flare/edit` with `"quality": "high"`).

```text
Scene: the product stands on <surface> in <specific place>, <time of day>. <one or two props that belong to the use, smaller than the product>. Background <depth: softly out of focus | readable>.
```

```json
{"prompt": "<skeleton>", "image_urls": ["<url:product>", "<url:product-label>"], "image_size": {"width": 1344, "height": 1680}, "num_images": 1, "output_format": "png"}
```

Pitfalls: props that look like the product (other bottles, jars, boxes) get duplicated labels: choose props from another object family. People in the background invite faces and hands: leave them out unless asked. One surface, one light source.

## 3. Flat lay

When: kits, ingredients, accessories, "what is in the box". Default 1:1. Same endpoint and JSON as mode 2.

```text
Scene: top-down flat lay, camera exactly overhead. The product lies <orientation> on <surface>. Around it, with clear gaps: <3 to 5 named items that are truly part of the product's story>. Even soft light from the top left, short soft shadows all falling the same way.
```

Pitfalls: only a top or front view of the product works; a flat lay needs the face the references show, lying down. Do not list items that are not in the box under "what's in the box": that is a false claim. Count the items in the result.

## 4. Hero banner

When: site header, campaign cover, store banner. Default 16:9; copy space is mandatory.

```text
Scene: <environment that carries the campaign idea>, wide composition. The product sits on the <left | right> third, large enough that its label reads. The opposite half is calm and uncluttered for a headline: <plain wall | sky | soft gradient of the surface>.
```

Pitfalls: never ask the scene model to write the headline; copy is set later. Extreme ratios shrink the product: keep it at no less than a third of the frame height. For 3:1 and wider, shoot 16:9 first, get approval, then extend with `fal-ai/flux-2-pro/outpaint` (`image_url`, `expand_left`, `expand_right`, `expand_top`, `expand_bottom` 0 to 2048 px, `mode` `high` / `fast`, `output_format`): the approved pixels stay, only canvas is added.

## 5. In-hand and on-model (not clothing)

When: scale by touch, jewellery, watches, bags, glasses, cosmetics in use. Default 4:5.

- Generated person: mode 2 JSON on `bytedance/seedream/v5/pro/edit`.
  ```text
  Scene: a <age range, skin tone, styling in plain words> person's hand holds the product <grip: resting on an open palm | between thumb and fingers at the base>, label facing the camera and unobstructed, <setting>. Hand anatomically natural, five fingers, relaxed.
  ```
- The user's own person photo (consent first): `bria/fibo-edit-1.5/product-holding` → `.result.image.url`.
  ```json
  {"person_image_url": "<url:model>", "product_image_urls": ["<url:product>"], "instruction": "She holds the bottle in her right hand at chest height, label facing the camera.", "aspect_ratio": "4:5"}
  ```
  `product_image_urls` 1 to 3; `aspect_ratio` enum `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9` (unset keeps the person photo's ratio); `seed`.
- Worn accessory on the user's person photo: `bria/fibo-edit-1.5/virtual-try-on` (`person_image_url`, `garment_image_urls` 1 to 3, `instruction`, `aspect_ratio`) → `.result.image.url`.

Pitfalls: fingers covering the label; a hand that makes a 30 ml bottle look like 300 ml (give the real height in the lock). Simplest grip wins. Faces are optional: crop at the shoulders when the face adds nothing.

## 6. Scale and context

When: size is a purchase question (bags, furniture, devices, travel sizes). Default 4:5. Mode 2 endpoint.

```text
Scene: the product next to <one universally known scale anchor: a hand, a coffee mug, a laptop, a door frame>, both on the same surface and at the same distance from the camera. The product is <real dimension, e.g. 12 cm tall>; the anchor is visibly <larger | smaller>.
```

Pitfalls: no invented dimension lines or numbers (a measured diagram is a typography job for `/genmedia-skills:image`, with the user's real numbers). Without a real dimension from the user, ask or skip this mode: a wrong scale is a misleading image.

## 7. Detail macro

When: texture, stitching, closure, material, print quality. Default 1:1.

1. Crop the user's sharpest photo around the detail with whatever exists: `magick in.png -crop WxH+X+Y out.png`, `ffmpeg -i in.png -vf crop=W:H:X:Y out.png`, or on macOS `sips -c H W in.png --out out.png` (centre crop).
2. Upload, then `fal-ai/seedvr/upscale/image` → `.result.image.url`:
   ```json
   {"image_url": "<url:crop>", "upscale_mode": "factor", "upscale_factor": 2, "output_format": "png"}
   ```
   Text in the crop → `topaz/upscale/image/precision` with `"model": "Text Refine"`, `"upscale_factor": 2`.
3. Generative macro only for the product's *contents or material* (a cream swirl, fabric weave, coffee crema), never for a label or logo: mode 2 JSON with `Scene: extreme close-up of <material>, raking light, shallow depth of field`, and say it is an illustration of the texture.

Pitfall: a source too small to crop (under about 1000 px on the detail) → ask for a closer photo instead of inventing detail.

## 8. Seasonal or campaign look

A look, not a layout: run any mode with a seasonal `{LOOK}`. Change palette accent, props and light; never the product.

```text
Scene: <base mode scene>, dressed for <occasion> with <2 restrained cues from variation-matrix.md, e.g. pine sprig and warm low window light>. The cues stay at the edges; the product remains the largest, sharpest object.
```

Pitfalls: seasonal text ("Sale", "Yılbaşı indirimi") is copy, not scenery: leave space. Religious and national symbols only on explicit request. Do not tint the product with coloured light.

## 9. Social formats

One approved idea in several ratios. Order: approve the master (4:5 or 1:1) → derive. When the plan asks for 4:5 and 1:1 of the same shot, compose the 4:5 master with the product and the copy space inside its central square: the 1:1 is then a free local crop.

| Target | Route |
|---|---|
| Wider or taller, same image | `fal-ai/flux-2-pro/outpaint`: compute the pixels to add per side; approved pixels untouched |
| Different framing (9:16 story from a 4:5 post) | re-shoot: same prompt, new `image_size`, approved master as the last reference, plus "Same scene, same props, same light as the last figure; recomposed for a vertical frame, product in the lower-middle, clean area in the top fifth" |
| Square crop of a larger frame | crop locally; free |

Keep platform UI zones clear on 9:16 (top and bottom bands hold interface elements; exact safe zones vary: check the platform's current specs). Pins: product in the upper two thirds, calm lower third.

## 10. Ad pack

N coordinated variants for testing or a carousel. Default 1:1 plus 4:5 of the winners. Build it with `variation-matrix.md` (roles, axes, one variable per variant) and run it as the single stage-2 batch in `batch-plans.md` plan A. Every variant carries `{LOCK}`, `{LOOK}` and the hero reference; each leaves copy space on the same side so one text layout fits all.

## 11. Apparel try-on

When: a garment photo (flat lay, ghost mannequin or on another model) must be shown on a person. Default 2:3 or 3:4. Consent first if the person is real; a generated model plate (a person only; the garment never comes from text) is one job on `bytedance/seedream/v5/pro/text-to-image` (`prompt`, `image_size` 1296 x 1728, `num_images`, `output_format`): front-facing, arms clear of the torso, plain fitted basics, plain backdrop, described by age range and styling, never as a named person. A recurring model comes from `/genmedia-skills:character`.

`fal-ai/fashn/tryon/v1.6` → `.result.images[].url`:

```json
{"model_image": "<url:model>", "garment_image": "<url:garment>", "category": "auto", "garment_photo_type": "auto", "mode": "quality", "num_samples": 2, "output_format": "png"}
```

- The two image fields have **no `_url` suffix** but take URLs. `category`: `tops`, `bottoms`, `one-pieces`, `auto`. `garment_photo_type`: `auto`, `model`, `flat-lay`. `mode`: `performance`, `balanced` (default), `quality`. `num_samples` 1 to 4. `moderation_level` stays at its default.
- Best inputs: person front-facing, arms clear of the torso, full garment area visible; garment on a plain background, unfolded.
- Output size is fixed by the model: read the result's width and height, and upscale with `fal-ai/seedvr/upscale/image` if the channel needs more.
- Alternatives (`routing-image.md`, task `virtual-try-on`): `bria/fibo-edit-1.5/virtual-try-on` for 1 to 3 garments or accessories in one call; `google/virtual-try-on` (`person_image_url`, `product_image_url`) as a second opinion on a failed fit.
- Scene around the dressed model: take the try-on result as Figure 1 of a mode 2 job ("keep the person and the garment exactly; change only the environment"), then QA the garment again: print, colour, buttons, length.

## Control and premium options

- Exact placement in a generated scene: `fal-ai/bria/product-shot` → `.result.images[].url`: `image_url` (at most 12 MB), `scene_description` **or** `ref_image_url` (English only, not both), `placement_type` `original` / `automatic` / `manual_placement` (default) / `manual_padding`, `manual_placement_selection` (default `bottom_center`), `shot_size` `[w, h]` near one megapixel, `padding_values` `[left, right, top, bottom]`, `num_results` 1 to 4. `automatic` returns ten placements per result: price it first.
- Native 4K or a Nano Banana look: `fal-ai/nano-banana-pro/edit` (`image_urls`, `aspect_ratio` enum, `resolution` `1K` / `2K` / `4K`, `num_images` 1 to 4); 4K doubles the price.
- Budget drafts of a look (never finals): `meta/muse-image/edit`, `image_urls` 1 to 10, about a cent.
