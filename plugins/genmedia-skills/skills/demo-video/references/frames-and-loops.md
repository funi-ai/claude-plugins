# Device frames, plates, end cards and loops

Read when a recording should play inside a drawn device, when a demo needs an intro or end card, or when the deliverable is a loop or a GIF.

## 1. The recording inside a drawn device

The frame geometry is **not** re-derived here. `/genmedia-skills:launch-graphics` composes the page (device frame, status bar, headline, background plate), and its `layers` command renders everything except the capture with a true alpha hole where the screen sits. Ask that skill for the `layers` of a framed slide; it writes `…/video-layers/<target>/<locale>/NN-<slide>.fg.png` and `NN-<slide>.layers.json` (canvas, the hole's rectangle, the capture's size). Point a scene at the JSON:

```json
"frame": {"layers": ".genmedia/projects/<slug>/launch-graphics/video-layers/ad-video-9x16/en/01-hero.layers.json"}
```

`democut.py` then scales the recording into the hole, puts the alpha layer on top, and fits the whole canvas to the variant. What it checks:

- The recording's aspect against the hole's: more than 30 % apart is an error (`frame_aspect_mismatch`) — a phone recording belongs in a phone frame. Between 8 % and 30 % it warns and pads the difference with the variant's `background`.
- The layers file and its PNG must both exist, and the PNG must be the one the JSON names.

Practical notes:

- The slide's capture in `launch-graphics` should be a **frame of this recording**, so both share one aspect and the still and the video match.
- A hero scene (a generated hand holding a phone) or a zoom layout cannot take a recording: the `layers` command refuses them (`layers_unsupported`). Use an upright framed layout.
- Framing costs pixels: the recording is scaled down into the hole, so a 1290-wide recording inside a 1200-wide hole on a 886-wide canvas is fine, while a 720-wide recording is not.
- A frame is worth it for store previews, ad placements and social cuts. A product demo on your own website usually reads better full-bleed, with no device around it.

## 2. Plates, intro and end cards

Anything that is **not the product** may be generated:

| Part | How |
|---|---|
| End card (logo, one line, a URL) | `/genmedia-skills:launch-graphics` renders exact text at the exact size; `/genmedia-skills:brandkit` has the lockup and the logo sting |
| Background plate behind a framed device | a generated still (`references/routing-image.md`), one per video, no lettering |
| Lower thirds, headline overlays | PNGs with alpha, composed where the text is exact, placed as scene `overlays` |
| A logo sting at the head | `brandkit.py sting` renders it from the approved SVG |

A still scene holds a card for a couple of seconds:

```json
{"id": "end", "still": {"file": "cards/end-en.png", "seconds": 2.5, "fade": 0.4}, "transition": {"kind": "cut"}}
```

Rules: no text is ever generated into a picture by a model; an end card is read at 2-3 s (about 3 words per second, plus a beat); the card's background should be the product's own dark or light ground so the dissolve into it is not a flash.

## 3. Loops

A loop is a variant with one or two scenes, `audio: false`, and an ending that matches its beginning.

- Pick a scene where one action completes: open → result, drag → snap, type → suggestion.
- 3-8 s. Longer and it is a video that repeats; shorter and nobody sees the action.
- Set `hold_last` to 0.3-0.6 s so the result is readable before the loop restarts.
- Start and end on the same screen state when you can. A loop that jumps reads as broken. On a looping target (`loops` in `specs`: the loop rows and both App Store creative-asset videos) `validate` measures it: `loop_seam` warns when the last frame and the first are under 0.95 SSIM.
- Silent by default: every autoplaying loop on the web is muted.

## 4. GIF, and the byte budget

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" gif --slug <slug> --variant loop-16x9 --budget-mb 3 --seconds 6 --webm
```

The budget is **measured, never estimated**: the ladder (1080@20 → 960@18 → 900@15 → … → 320@8) is rendered with `palettegen`/`paletteuse` and weighed, and the first step under the budget wins. The answer lists every step it tried, so you can tell the user what the size cost.

- Product Hunt's cap is 3 MB for every image, GIF included, and a GIF animates only on hover: the command also writes the first frame as a PNG. **Read that PNG.** It is the thumbnail.
- A GIF has 256 colours: a dark UI with a gradient will band. If the banding is ugly, deliver WebM (`--webm`, VP9) or MP4 and say why.
- What makes a GIF small: fewer frames per second (12 reads fine for UI), a smaller width, less motion, no zoom, a flat background. What makes it huge: a push zoom, a video-like background, a fade.
- `ph-thumbnail-gif` is a GIF target, not a video variant: build a video variant (`loop-1x1`) and export the GIF from it. `build` refuses a GIF target on purpose.

## 5. Poster and first frames

- `build` writes `<slug>-poster.png` from `poster_at` in the variant.
- Apple's default poster frame for an app preview is 5 s in; set `poster_at` so the frame at 5 s is worth showing, or expect Apple's default to pick something else.
- A creative-asset video has no stated default: the user picks its poster frame in App Store Connect, it applies wherever the asset is used, and it cannot be edited after approval. Recommend one with `poster_at` and name its time in the delivery.
- The poster and the GIF's first frame are judged small: look at them, do not assume them.
