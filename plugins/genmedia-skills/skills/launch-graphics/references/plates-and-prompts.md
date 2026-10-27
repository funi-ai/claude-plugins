# Plates, decor and prompts: the only things this skill generates

Read when a set needs anything a model has to paint: a background plate, a panorama strip, a sticker or 3D object, thumbnail art, a card illustration. Everything else (frames, status bars, text, the capture itself) is composed locally and costs nothing. Endpoints, fields and prices below were checked with free commands on 2026-09-20; `references/routing-image.md` and the live schema win when they disagree.

## 1. What may be generated, what may not

| Generate | Never generate |
|---|---|
| Background plates and strips (abstract, photographic, illustrated) | The app's interface, or any "improved" version of a capture |
| Decor: stickers, mascots, 3D objects, shapes, with a transparent background | Words, numbers, badges, ratings: all text is HTML text from the deck |
| Scene plates with a key-colour screen (`references/hero-scenes.md`) | Logos of other companies (integration logos come from the user's files) |
| Product Hunt thumbnail art, a card illustration | Store badges, award laurels, review stars, platform UI |

A screen that is not a real capture (a concept the user has not built yet) is only allowed with `mockup: true` on the capture, and the delivery says so.

## 2. Spend nothing first

`background.kind: "solid"` and `"gradient"` are CSS: a two-colour gradient from the theme with two blurred accent blobs carries most store sets and link cards, renders in a second and never fights the headline. Buy a plate when the brief asks for a place, a material, a mood or a character that CSS cannot give. Decide per set, not per slide: one plate or one strip per set keeps it coherent.

## 3. Routing for this skill

| Need | Endpoint | Why | Set on every call |
|---|---|---|---|
| Photographic or painterly plate, scene plate | `bytedance/seedream/v5/pro/text-to-image` | `t2i-general` default in the routing table; rendered a clean key screen in the probe | `image_size` `{width,height}`, `output_format: "png"` |
| Graphic, illustrated, 3D-render look; sticker or object with a transparent background | `openai/gpt-image-2.5/flare/text-to-image` | `t2i-typography` default; design and illustration strength; has `background: "transparent"` | `image_size` (multiples of 16), `quality: "medium"`, `background`, `output_format: "png"` |
| Cut-out of an existing picture (the user's mascot photo, a plate element) | the `bg-remove-image` task in `references/routing-image.md` | non-generative; keeps the pixels | per that row |
| A plate larger than one generation (`appstore-universal`, a Seedream scene plate for `appstore-search`) | `fal-ai/seedvr/upscale/image`, the `upscale-image` default in `references/routing-image.md` | faithful upscale; keeps the screen edge clean (section 4) | `upscale_factor: 2`, `output_format: "png"` |
| Same look across many plates for a brand | the BRAND LOCK block from `brandkit`, pasted into every prompt | one style key | - |

Traps: Seedream's `image_size` needs a total area between 1024x1024 and 2048x2048 and an aspect between 1:16 and 16:1, and it defaults to JPEG. GPT Image 2.5 defaults to `quality: "high"` and bills by tokens: always send `quality`. A user who names a model gets that model after the live check.

## 4. Generation sizes

Generate larger than the render, never smaller than about 60% of it for a soft background; the compositor covers the canvas and never stretches a plate out of proportion.

| Target | Render | Generate | Note |
|---|---|---|---|
| `og` + `x-card` | 1200x630, 1200x600 | 2048x1072 | one plate serves both; keep the subject inside the centred 2:1 band |
| `ph-gallery` | 1270x760 | 1920x1152 | |
| `email-card` | 1208x680 | 1920x1088 | both models take it (limits re-read on 2026-10-13); the card shows at 604 px, so a calm ground reads best |
| `play-feature` | 1024x500 | 2048x1008 | focal point in the centre |
| `play-feature` and a YouTube thumbnail from one plate | 1024x500 and 1280x720 (master 2560x1440) | 2048x1152 | 16:9; the feature graphic takes the centred 2.05:1 band, so subject and horizon stay out of the top and bottom 7 percent (section 10) |
| `ph-thumbnail` | 240x240 | 1024x1024 | judged at 240, 80 and 40 px |
| Store slide, portrait | 1320x2868, 1080x1920 | 1024x2224 | soft or abstract only: it is upscaled about 1.3x |
| Store slide, tablet | 2064x2752, 1440x2560 | 1536x2048 | same |
| Strip across N portrait slides | N x slide width | up to 2048x2048 area, e.g. 3072x1328 for five slides | abstract only; every slide shows a crop, nothing important on a seam |
| Decor | placed at `w` of the canvas | 1024x1024 | transparent PNG |
| `appstore-header` | 3840x1646 | GPT Image 2.5 3840x1648, or Seedream 3120x1336 | 3840x1648 covers it; 3120x1336 is enlarged about 1.23x, fine without an upscale |
| `appstore-search` | 3840x2560 | GPT Image 2.5 3504x2336, or Seedream 2496x1664 | GPT is enlarged about 1.1x; a Seedream plate (1.54x) is fine as a soft ground, a Seedream scene plate gets the upscale step |
| `appstore-universal` | 5244x2950 | GPT Image 2.5 3840x2160, or Seedream 2720x1530, then always the upscale step | neither model reaches 5244 px (below) |
| `appstore-header` and `appstore-universal` from one plate | 3840x1646 and 5244x2950 | the universal plate, upscaled | the header shows its centred 21:9 band, so the subject sits in the middle third of the height |

Model limits behind those sizes (schemas read live on 2026-10-07): GPT Image 2.5 takes sides in multiples of 16, a long edge of at most 3840 px, an aspect up to 3:1 and 655,360 to 8,294,400 pixels; Seedream 5.0 Pro takes a total area from 1024x1024 to 2048x2048 and an aspect from 1:16 to 16:1. So no App Store creative asset is ever generated at its own size, and 5244 px is out of reach of both.

**Upscale step** (`appstore-universal` always; a Seedream scene plate for `appstore-search`). The browser enlarges a plate that is smaller than the canvas, and a scene plate's screen edge then steps: on `appstore-universal` a 2720x1530 scene plate failed `jagged_edge` (0.13 px, measured 2026-10-07), the same plate upscaled first passed. Upscale the generated plate with the `upscale-image` default in `references/routing-image.md`, `fal-ai/seedvr/upscale/image` (faithful, not generative; `upscale_factor` 1 to 10, `output_format` defaults to `jpg`): factor 2 and `"output_format": "png"`, which gives 7680x4320 from GPT Image 2.5 or 5440x3060 from Seedream. Run the guardrail for it like for any endpoint, then a second batch; its `image_url` is the plate's URL from the first batch's `outputs[].url`, or the `cdn_url` of `gm.py upload <plate>`. Register the upscaled file, not the original (`screen-quad --file` for a scene plate). Price: $0.001 per megapixel in its pricing text on 2026-10-07, a few cents at these sizes; `gm.py price fal-ai/seedvr/upscale/image --explain` before the run.

```json
{"id": "ground-up", "endpoint_id": "fal-ai/seedvr/upscale/image", "est_cost_usd": 0.04,
 "download": ".genmedia/projects/<slug>/launch-graphics/plates/ground-up_{index}.{ext}",
 "input": {"image_url": "<the plate's URL>", "upscale_factor": 2, "output_format": "png"}}
```

A scene plate for these targets keeps the device small and in the middle: Apple's art safe area is about 43 x 40 percent of the header, 56 x 40 percent of the search results canvas, and 27 x 33 percent of the universal one, centred across and set above the middle (`surfaces.md` section 1a). A larger device warns `cutoff_zone`. Plates for creative assets stay suitable for a 4+ rating (`store-policy.md` section 2a).

## 5. Prompt blueprints

English prompts. Every plate prompt ends with the exclusion line.

Background plate:

```text
<abstract composition | photograph of <place> | <material> surface>, <palette words taken from the theme colours>,
<light>. The <upper | lower | left | right> <third | half> is calm, low in contrast and <dark | light>, with no
detail, to carry a headline. No devices, no screens, no people's faces<, unless the brief asks>.
No text, letters, numbers, logos or interface elements anywhere in the image.
```

Strip for a panorama set:

```text
One continuous very wide <abstract landscape of soft shapes | gradient mesh | paper-cut hills> in <palette>, flowing
left to right, no focal object, even density, no hard vertical edges, nothing that reads as a border.
No text, letters, numbers, logos or interface elements anywhere in the image.
```

Sticker, mascot or 3D object (transparent background):

```text
A single <object>, <style: glossy 3D render | flat sticker with a white outline | clay>, centred, whole object
visible with margin, soft contact shadow only. Transparent background. No text, letters or logos on it.
```

Product Hunt thumbnail art (when no icon exists; an existing icon always wins):

```text
A simple bold symbol for <what the product does>, one shape, two colours (<hex>, <hex>), thick forms, centred with
margin, readable at 40 pixels. No text, letters or numbers.
```

Rules: name the calm zone and its brightness (the contrast gate measures the real pixels under the text); name the palette in words plus the hex of the accent; never ask for a device unless it is a scene plate; never describe the app's screens.

## 6. Batch plan

Write the plan with the Write tool (not a heredoc), download straight into the project's plate folder, then register each file under `plates` (`{"file": "plates/<name>.png"}`; a scene plate gets its `key` and `quad` from `screen-quad --write`) or `decor` (`{"file": …}`) in `deck.json`. Deck paths are relative to the project folder.

```json
{"label": "<slug>", "max_parallel": 3, "jobs": [
  {"id": "bg-store", "endpoint_id": "bytedance/seedream/v5/pro/text-to-image", "est_cost_usd": 0.07,
   "download": ".genmedia/projects/<slug>/launch-graphics/plates/bg-store_{index}.{ext}",
   "input": {"prompt": "<background plate prompt>", "image_size": {"width": 1024, "height": 2224}, "output_format": "png"}},
  {"id": "coin", "endpoint_id": "openai/gpt-image-2.5/flare/text-to-image", "est_cost_usd": 0.06,
   "download": ".genmedia/projects/<slug>/launch-graphics/plates/coin_{index}.{ext}",
   "input": {"prompt": "<sticker prompt>", "image_size": {"width": 1024, "height": 1024}, "quality": "medium", "background": "transparent", "output_format": "png"}}
]}
```

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/launch-graphics/plates-1.json
```

600000 ms Bash timeout. `status: "pending"` → the same command again; a job with a request ID is resumed, never resubmitted. Mechanics: `references/cli-contract.md`.

## 7. Cost

- `bytedance/seedream/v5/pro/text-to-image`: $0.0675 per image up to a 1536x1536 area, $0.135 up to 2048x2048 (its pricing text on 2026-09-20, marked tentative). 2048x1072, 1920x1152, 1024x2224 and 1024x1024 are in the first tier; 1536x2048, a 3072x1328 strip and the creative-asset sizes (3120x1336, 2496x1664, 2720x1530) are in the second.
- `openai/gpt-image-2.5/flare/text-to-image`: tokens. `gm.py price` answers `1 units`, which is not a price; use `--explain` and the per-size, per-quality table in `references/routing-image.md`.
- Typical set: no plate at all ($0), or one background plus one scene plate plus one or two stickers: well under the default announce threshold. State the estimate in the delivery line. Several sets, second tier sizes, re-rolls or `quality: "high"` → add it up first and apply the gate from `gm.py preflight`.

## 8. Judging a plate before it enters the deck

Read every file. Reject and re-roll (changed prompt, at most three attempts) when: there is any lettering, logo or interface fragment; the calm zone is busy or mid-grey (text will fail `contrast`); the palette fights the theme; a strip has an object where a seam will fall; a sticker is cropped, has a baked background or carries text. A transparent sticker that came back opaque → run the routed background remover on it instead of re-rolling.

## 9. Placing decor

`decor` on a slide: `ref` (key under the deck's `decor`), `x`, `y` (centre, as fractions of the canvas, from -0.5 to 1.5 so a piece may hang over an edge), `w` (width as a fraction of the canvas width), `rotate` (degrees), `z` (`back`, the default: behind the device; `front`: above the device and under the text). Front decor that reaches a text box warns `decor_overlaps_text`. Two to five pieces on a playful set, none on a sober one. Decor never covers a text box or the important part of the capture, and the same piece should return across slides rather than a new object per slide.

## 10. One plate for a feature graphic and a thumbnail

A brand graphic (plate plus the lockup large in the middle) often has a twin: the YouTube thumbnail of the store preview video. One plate serves both, and neither file is built by hand:

1. Generate the plate once at 2048x1152 (16:9, section 4), text-free, with the calm zone in the middle where the lockup will sit. Register it under `plates`.
2. Feature graphic: a `card-lockup` slide on `play-feature` with `lockup: {"width": 0.35}` (`templates.md` section 6). The plate is cover-fitted and centred, so the 1024x500 card is the plate's centred 2.05:1 band.
3. Thumbnail: `/genmedia-skills:youtube-thumbnail`, plate path with a brand lockup, given the same plate file and the same logo file at the same width share. It composites the logo locally over the plate centre-cropped to 16:9 and runs its 160 px gate and delivery sizes; no model redraws the logo there either.

Both centre the plate and measure the lockup against the canvas width, so the two files show the same composition at their own aspect.
