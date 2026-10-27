# Hero scenes: a real capture inside a generated photograph

Read when a card uses `card-hero-scene`: a phone, tablet, laptop or monitor held, lying or standing in a scene, with the user's real screen on it. The scene is generated; the screen never is. The model paints the device with a flat key-colour screen, `launchkit.py screen-quad` finds that screen, and the compositor warps the untouched capture into it. Probed for phones on 2026-09-20 with four paid plates (hand, hand with the thumb over the screen, phone on a desk in strong perspective), and for laptops, monitors and tablets on 2026-09-24 with fourteen (section 3b): every plate gave a usable screen.

## 1. When to use it, when not

| Use | Do not use |
|---|---|
| `og`, `x-card`, `ph-gallery` slide 1: one emotional picture that says where the product lives (a laptop or monitor for a web or desktop product, a tablet for an iPad app) | App Store and Play screenshot slides that must show the app in use at full size: `card-hero-scene` is a card layout and fails deck validation there (`layout_target_mismatch`); use the device layouts, the drawn frame and the real capture |
| A website hero or social post the user asks for in the same look | `play-feature`: Google's asset guidance (checked 2026-09-20) discourages people handling a device and lists device imagery under content to avoid; `compose` warns `hero_scene_on_play`. Tell the user and offer `card-left-title` or `card-minimal` instead |
| The brief names a setting (outdoors, kitchen, studio desk, commute) | The user wants their exact device model shown: a generated device is a generic device, say so |
| `appstore-search` (Apple asks it to show the real experience) and `appstore-header`, with the device small and in the middle of the plate: everything but the ground sits inside Apple's art safe area (`plates-and-prompts.md` section 4). On `appstore-universal` the box is 27 percent of the width, so a scene there carries no copy | A plate smaller than an App Store creative asset's canvas: upscale it first (`plates-and-prompts.md` section 4), or the warped screen edge fails `jagged_edge` |
| One strong capture exists (rated Great in triage) | The capture is dense small text: a hand-held phone is about 330 px wide on a 1200 px card, nothing small survives |

One scene per set is usually enough. It costs one plate; every re-render after that is free.

## 2. Flow

1. Pick the capture (one screen, high contrast, large elements) and the side that stays empty for the headline.
2. Write the plate prompt from the blueprint in section 3. Choose the key colour (section 4). The user wants the hand and phone of a photo they showed: section 3c.
3. Verify the endpoint (Discovery guardrail), price it, generate one or two plates with `gm.py batch`, `output_format: "png"`. JPEG smears the key edge.
4. Read every plate before anything else: is the screen flat and unobstructed except where you asked for fingers, is the empty side really calm, is there any text or logo in the scene? Reject a plate with lettering anywhere.
5. Register the plate under `plates` in `deck.json` (`file`, `key`), or let the command do it with `--file <downloaded png>`, which copies the file to `plates/<plate id>.png`. Then:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/launchkit.py" screen-quad --slug <slug> --plate <plate id> --write
   ```
6. Read the answer (section 5). Then `compose` the card and Read the PNG at full size and on the contact sheet.

## 3. Plate prompt blueprint

Write prompts in English. Keep the SCREEN block verbatim except for the colour words; it is the part the detection depends on.

```text
SHOT: <photograph | product photograph>, <lens feel>, <depth of field>.
DEVICE: a modern smartphone with thin black bezels, <held upright in a <left|right> hand | lying on <surface>>,
  in the <left|right> third of the frame, screen facing the camera <almost straight on | at a three-quarter angle>,
  tilted about <n> degrees. The screen is tall: about 9 by 19.5.
SCREEN: The phone screen shows a perfectly flat, uniform, solid pure magenta colour (hex FF00FF) from edge to edge:
  no reflections, no glare, no gradient, no text, no icons, no interface.
  A small black <pill-shaped | round> camera cut-out sits at the top centre of the screen.
HAND: <the fingers grip the sides and do not cover the screen | the thumb overlaps the lower <left|right> corner of the screen a little>.
BACKGROUND: <setting>, strongly blurred, darker and calm on the <opposite> two thirds to leave empty space.
LIGHT: <natural light, time of day>, realistic skin and materials.
EXCLUSIONS: No text, letters, numbers or logos anywhere in the image.
```

Rules that matter:

- Name the screen aspect. Generated phones came out between 0.40 and 0.46 (width / height) across the probe and the first end-to-end run, against 0.46 for a current iPhone capture and 0.50 for a 1080x2160 Android capture. When a plate comes back too narrow, re-roll with the sentence strengthened ("the screen is wide for a phone: its width is almost half of its height"), or put a capture on the card whose aspect matches the plate: the capture with the smallest mismatch wins over the one you planned.
- Ask for the cut-out. It is how `screen-quad` tells the top of the phone from the bottom. Without it the answer carries `top_guess: true` and assumes the higher short side is the top.
- A thumb over the screen is fine and looks natural: it is not key-coloured, so it stays on top of the capture.
- Put the phone opposite the headline. `compose` fails the card with `text_overlaps_device` when a text box touches the screen or device box, and no prompt wording fixes a plate whose phone sits in the middle.
- Generate wider than you deliver: 2048x1072 for `og` and `x-card` (one plate serves both), 1920x1152 for `ph-gallery`. All sides are multiples of 16.
- Larger screens: section 3b.

Worked prompt (the one that produced the probe's best plate):

```text
Photograph with shallow depth of field. A man's right hand holds a modern smartphone with thin black bezels upright in
the right third of the frame, the screen faces the camera almost straight on, tilted about six degrees clockwise.
The phone screen shows a perfectly flat, uniform, solid pure magenta colour (hex FF00FF) from edge to edge: no
reflections, no glare, no gradient, no text, no icons, no interface. A small black pill-shaped camera cut-out sits at
the top centre of the screen. The thumb overlaps the lower right corner of the screen a little; the other fingers grip
the side. Background: a sunlit green forest path in strong bokeh blur, darker on the left two thirds to leave calm
empty space. Natural light, realistic skin, 35mm look. No text or logos anywhere in the image.
```

## 3b. Laptops, monitors and tablets

Same blueprint; swap the DEVICE block and keep SCREEN. No cut-out is needed: `screen-quad` takes the highest side as the top (section 5), which is right for a laptop lid, a monitor on a stand and a tablet in a stand or in hands.

```text
DEVICE (laptop): a modern <silver | dark grey> laptop with a thin black bezel around its display stands open on <surface>
  in the right <third | half> of the frame, <the display faces the camera almost straight on | turned about 40 degrees
  away from the camera, the display seen at a three-quarter angle>, the lid opened to about 110 degrees; the whole
  laptop is visible. The display is wide: about 16 by 10. The keys are plain, without printed characters.
DEVICE (monitor): a large modern desktop monitor with a very thin black bezel on a slim stand, on <desk> in the right
  half of the frame, facing the camera almost straight on, seen from sitting eye height. The display is wide: 16 by 9.
  Nothing covers the screen; no keyboard in the frame.
DEVICE (tablet, landscape): a modern tablet with thin, even black bezels stands in landscape orientation on a simple
  folding stand on a matte <surface>, the screen at a gentle three-quarter angle, leaning back about 15 degrees. The
  screen is about 4 by 3, wider than it is tall. The surface is matte: no reflection of the screen or its colour.
DEVICE (tablet, in hands): two hands hold a modern tablet with thin, even black bezels upright in portrait orientation,
  the screen almost straight on, tilted about five degrees; the fingers grip the side bezels and do not cover the screen.
SCREEN: The <laptop display | monitor | tablet screen> shows a perfectly flat, uniform, solid pure magenta colour
  (hex FF00FF) from edge to edge: no reflections, no glare, no gradient, no text, no icons, no interface, no windows.
  All four edges of the display are fully visible.
```

What the probe gave (2048x1072 PNG, `quality: "medium"` on GPT; aspect is `screen-quad`'s perspective-corrected `aspect_estimate`). Key area and corners were found on all fourteen, with the right orientation and no flag:

| Scene (asked) | `bytedance/seedream/v5/pro/text-to-image` | `openai/gpt-image-2.5/flare/text-to-image` |
|---|---|---|
| Laptop straight on (16:10 = 1.60) | 1.62 | 1.67 |
| Laptop at three quarters, cafe table (1.60) | 1.58 | 1.39, and 1.30 on a re-roll that named "1.6 times": a 16:10 capture fails `aspect_mismatch` |
| Monitor on a stand (16:9 = 1.78) | 1.65 | 1.76 |
| Tablet on a stand, landscape (4:3 = 1.33) | 1.31 | 1.34, with a magenta reflection on a glossy counter (`stray_key_share` 4.4%); "matte counter" re-roll: 1.37, none |
| Tablet in two hands, portrait (3:4 = 0.75) | 0.68, re-roll 0.63 | 0.64, re-roll 0.68 (wording "three quarters of its height") |

Choices that follow:

- Angled laptop: Seedream. GPT Image painted the screen too narrow twice.
- A portrait tablet in hands comes out 0.63 to 0.68 whatever the prompt says. That fits 11-inch class iPads (about 0.69) and most Android tablets (0.625), not 13-inch iPads (0.75): pick the capture by the plate, or plan a landscape tablet on a stand, which followed 4:3.
- Say "matte" for any surface under a screen. A glossy counter mirrors the magenta; `compose` turns it neutral grey, which still reads as a stain.
- Laptop keys came out without letters; GPT's carry faint unreadable marks at full plate size, invisible on a card.

## 3c. Keeping the hand and phone of a reference photo

When the user points at a photo and wants its hand and phone (grip, size, angle, perspective) in a scene of their own, edit that photo; do not describe it to a text-to-image model.

- Route to `openai/gpt-image-2.5/flare/edit` with the reference as the **only** input image. Describe the new scene in words; ask the model to keep the hand and the phone exactly as they are and to change only three things: replace the background with the described scene, remove any text or logo in the photo, and paint the screen with the SCREEN block of section 3 (key colour, cut-out kept). The reference's geometry survives and everything around it changes.
- Do not add the scene as a second input image. With two inputs the model takes the scene as its base and redraws the hand: a smaller, tilted phone, a thumb over the screen. Seen with GPT Image 2.5 Flare edit and Seedream 5.0 Pro edit alike.
- The scene is then a new one, close to the description rather than a copy of a scene plate the user liked. Say so when the user expected their earlier scene.
- The plate still goes through `screen-quad` and every gate. Two outputs from one call are a good first batch.

Found on 2026-09-25 building an `og` hero card from a hand-held-phone reference: the two-input edits (three Seedream plates, two GPT plates) redrew the hand every time; the single-input GPT edit matched the grip and the perspective on both of its outputs, and both screens landed inside the capture's `aspect_range`.

## 4. Key colour

- `magenta` is the default: almost nothing in a real scene is pure magenta, and it survives foliage, skin, wood and sky.
- `green` only when the scene itself is pink, purple or neon (night city, flowers, a magenta brand wall). Never green in nature scenes.
- The capture's own colours do not matter: the key is removed from the plate, not from the capture.

## 5. Reading the `screen-quad` answer

| Field | Meaning | Act when |
|---|---|---|
| `quad` | four corners in plate pixels: top-left, top-right, bottom-right, bottom-left of the screen as the device holds it | stored by `--write` together with `key`, `median_key_luma`, `aspect_estimate`, `aspect_range`, `orientation`, `island`, `top_guess`; without `--write` nothing reaches the deck and `compose` fails with `plate_without_quad` |
| `orientation` | `portrait` or `landscape`: which way the screen stands. The top is the side nearest the cut-out; without one, the highest side in the image | wrong for the capture (a phone lying on its side, a tablet turned): `screen-quad --orientation portrait` or `landscape` limits the top to the short or the long sides. A capture of the other orientation fails `aspect_mismatch`, and the message names the flag |
| `aspect_estimate` | width / height of the real screen: the perspective is undone with the focal length the quad implies (an assumed 50 mm look when a pair of sides is nearly parallel; a warning says so) | compared with the capture through `aspect_range` |
| `aspect_range` | the aspects the screen can have across plausible focal lengths: a point straight on, wide in strong perspective, because a generated photograph is no exact camera | a capture inside it is not stretched. Outside by more than 8%: `compose` warns `aspect_mismatch`; above 15% it fails. Re-roll with the aspect line strengthened (section 3b lists what each model tends to paint), or pick a capture whose aspect fits |
| `side_ratio` | `width` (top edge over bottom edge) and `height` (left over right); far from 1 means strong perspective | below about 0.9 or above 1.1: small UI text will not survive, choose a bolder capture |
| `top_guess` | no cut-out was found | true: check on the composite that the capture is not upside down; re-roll with the cut-out sentence if it is |
| `keyed_share` | share of the plate that is key-coloured | very small: the device is too small to carry a screen, re-roll closer (under 0.4 percent the answer is `no_key`) |
| `stray_key_share` | key colour away from the screen: a reflection on a table, a glow on a wall | from 0.2 percent a warning. `compose` keeps it opaque and neutral grey instead of cutting a hole; Read the card, and if the grey stain shows, re-roll with "matte surface, no reflection of the screen" |
| `warnings` | "no island or punch-hole was found", "a side was fitted from few points", "assumed lens", stray key | Read the corners and the orientation on the composed card at full size |
| `kind: "no_key"` | no key colour found | the key is the other colour (`--key green`), or the model ignored the SCREEN block: re-roll once, then try the other routed model |
| `kind: "no_quad"` | the key area is not a four-sided shape | a hand covers a whole edge or the phone leaves the frame; re-roll with "the whole phone is visible" |

## 6. What the compositor does (so you can judge the result)

The capture sits under the plate and is warped with a `matrix3d` homography to the stored corners, grown by 2 px. The plate's key pixels become transparent with a soft edge, the key colour is removed from the half-transparent rim, and the brightness variation of the painted screen is carried over as a faint shade, so glare and finger shadows of the scene fall on the real capture. Only key colour near the screen is cut out; key colour elsewhere (a reflection) stays opaque and turns neutral grey. Rounded screen corners, the cut-out and fingers come from the plate. The capture gets the same status-bar work as in a frameless slide (`devices-and-statusbar.md` section 3). Lockup and text go to the side away from the device, over a scrim laid on the plate (black under light text, white under dark; `background.dim` sets its strength, default 0.62). The scrim holds its strength to just past the text block, then eases out over 40 percent of the card width, under the device and the hand when it reaches them: the keyed screen is a hole in the plate, so the capture is never shaded, while the hand and bezel on the text side come out a little darker, which reads as scene light. Headline and logo are HTML on top.

Edges. Headless Chromium draws a `matrix3d`-warped element without anti-aliasing, so at 1x every edge of the capture, and every line inside it, steps like a staircase. A hero page therefore renders at 3x and is shrunk back (2x where 3x would pass 50 megapixels), and `compose` measures the capture's four edges on the result: the median distance of the sub-pixel edge from a smooth curve. Above 0.11 px it renders once more at a higher factor, then fails the page with `jagged_edge` (measured 2026-09-25 with UI and photographic captures: 0.121 to 0.179 px at 1x, at most 0.091 at 3x). The capture's own content does not count: only the pixels at the edge are read. A `jagged_edge` that survives supersampling comes from the plate: its own screen edge is stepped (JPEG, upscaled or edited); regenerate it as PNG. The App Store creative assets are all above that limit, so they render at 2x; a plate the browser must enlarge there steps the edge as well (measured 2026-10-07: 0.13 px for a 2720x1530 plate on `appstore-universal`, a clean pass for the same plate upscaled first). Never deliver such a page and never rebuild the scene in a hand-written page: only `compose` supersamples and checks.

Look for: a coloured rim around the screen (report it, then re-roll the plate as PNG if it was JPEG), a capture that looks squeezed (aspect), UI text too small to read (perspective or size), a headline over a busy area (contrast warning).

## 7. Cost and repairs

- One plate on `bytedance/seedream/v5/pro/text-to-image` at 2048x1072 was $0.0675 on 2026-09-20 and again on 2026-09-24 (area up to 1536x1536; larger areas up to 2048x2048 cost twice that). The fourteen larger-screen plates of section 3b were estimated at $0.73 together. `openai/gpt-image-2.5/flare/text-to-image` is token-priced: set `quality: "medium"` and estimate with `gm.py price --explain` and the table in `references/routing-image.md`. Never quote these from memory: price before you spend.
- At most three plate attempts per scene, each with a changed prompt. Two plates in the first batch (one per routed model, or two hand positions) is a reasonable default and stays under the announce threshold.
- A scene that keeps failing is not worth a fourth plate: fall back to `card-left-title` with the drawn frame and say why.

## 8. Honesty

The device in the scene is a generic generated phone, tablet, laptop or monitor, not the user's device and not an Apple, Google or other maker's product image. The screen content is the user's real capture, unchanged. Say both in the delivery line when a hero scene is part of the set.
