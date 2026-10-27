# Product lock and fidelity QA

The lock says what the product is; the QA proves each output still is that product. Both are done by looking: open the files with the Read tool. `gm.py` and `pipeline.py` abbreviate the calls shown in SKILL.md.

## 1. Writing the PRODUCT LOCK

Read every product photo first. Write only what you can see; mark the rest unknown. Ask the user only for what a photo cannot tell and the shoot needs (real height for scale shots, the exact wording of text that is too small to read).

Save this block at the top of `.genmedia/projects/<slug>/plan.md`:

```text
PRODUCT LOCK (from bottle-front.jpg, bottle-label.jpg; seen 2026-09-19)
Type: 500 ml dark green glass bottle, square shoulders, short neck, pourer cap
Proportions: height about 3.4 x width; label covers the middle 45% of the body height
Materials: glossy dark green glass; matte cream paper label; matte black cap
Colours: bottle deep bottle-green; label warm cream; text dark olive; thin gold rule under the name
Label text, verbatim, top to bottom: "ZEYTİN DALI" / "Soğuk Sıkım Natürel Sızma Zeytinyağı" / "500 ml"
Logo and layout: single olive-branch line drawing above the name, centred; all text centred
Count and kit: exactly 1 bottle; no box
Real size: 26 cm tall (from the user)
Never change: wording and spelling of the label (Turkish letters İ, ğ, ı included), the branch drawing, cap colour, bottle shape, glass colour
Not visible in the photos: back label, base. Never show them.
Reference coverage: front, and front three-quarter from the right, at eye level. Camera stays within that arc; top-down only with the bottle lying label-up.
```

Then compress it into the **lock string**, one English paragraph of 60 to 90 words, pasted verbatim into every generative prompt:

```text
The product is the 500 ml dark green glass olive oil bottle from Figure 1: square shoulders, short neck, matte black pourer cap, matte cream paper label on the middle of the body. Keep its shape, proportions, glass colour, cap and label exactly as in Figure 1. The label shows an olive-branch line drawing and reads "ZEYTİN DALI", "Soğuk Sıkım Natürel Sızma Zeytinyağı", "500 ml", centred, dark olive on cream. Do not add, remove, translate or restyle any text or drawing on it. Exactly one bottle, 26 cm tall.
```

Rules:

- Quote label text exactly as printed, in its language, with its capitalisation and diacritics. Never translate or "correct" it.
- Colours in plain words. Hex codes only when the user gave brand hexes.
- More than one product in the photo → the lock names which one, and the prompt says "ignore the other items in Figure 1". Better: crop the photo to the product before upload.
- Variants of one product (three scents, five colours) → one lock per variant, one shared look, one hero: shoot it with one variant and pass it to the others as the look reference only. Never let one reference stand in for another variant.
- The lock is the user's to correct: show its one-line summary in the plan card.

## 2. The rubric

Run it on every output before the user sees it. Read the output, then Read the primary source photo again; do not compare from memory.

| # | Check | Pass when | Severity |
|---|---|---|---|
| F1 | Label text | Every legible word equals the lock, letter by letter, diacritics included. No extra, missing or reordered line | blocker |
| F2 | Logo and graphics | Same drawing, same position and proportions on the label; not mirrored | blocker |
| F3 | Geometry | Silhouette, proportions (height to width), cap, handle, ports, seams and part count match. Not stretched to fit the frame | blocker |
| F4 | Colour and material | Hue, darkness and finish (matte, gloss, metallic, transparent) match under the scene's light; no tint from coloured light | blocker |
| F5 | Count and kit | Exactly the planned number of products; no mini copies, no second label in reflections or background | blocker |
| F6 | Inventions | No new text, claims, badges, seals, barcodes, brand names on props, watermarks or borders anywhere in the frame | blocker |
| F7 | Physics | Contact shadow present and in the light's direction; reflection shows this product; nothing floats; liquid level and transparency plausible | re-roll |
| F8 | Hands and people | Five fingers, natural joints, plausible grip; hand does not cover the label; product scale in the hand matches the lock | re-roll |
| F9 | Look lock | Palette, light direction and quality, grade and surface family match the approved hero and the look string | re-roll |
| F10 | Technical | Pixel size as planned; not black; product fully in frame; copy space where the plan put it; no model-made frame or caption | re-roll |

The legibility rule for F1: text on the product must be **either correct or too small to read**. Legible and wrong is always a blocker. Small and soft is acceptable only in wide shots (lifestyle, banner, scale); hero, packshot, detail and ad-pack shots need the brand name readable at delivery size.

How to look:

- Judge at full size, not from the thumbnail impression. When the label is under roughly a tenth of the frame height, crop it out locally (`magick`, `ffmpeg -vf crop`, `sips -c`) and Read the crop next to the label close-up.
- Read the label aloud to yourself line by line and compare with the lock's quoted strings. Turkish dotted and dotless letters (İ, I, ı, i), ğ, ş, ç, ö, ü and numerals with units ("500 ml") are the usual casualties.
- Count products, caps, buttons, straps. Counting finds what a glance misses.
- Non-generative outputs (Pixelcut, local crops, faithful upscales) skip F1 to F6 on the product itself but still get F5, F10 and an edge check: no halo, no clipped parts, no leftover background inside handles.

Verdicts:

- **pass**: deliver.
- **re-roll**: same route, changed input. Budget 2 per shot.
- **repair**: another route from section 3, when the failure is one the current model repeats.
- **drop**: after the budget is spent. Tell the user which shot is missing and why; never deliver a blocker "for reference".

Write each verdict into the `## Log` of `plan.md` as one line: `s03 re-roll 1: F1 "ZEYTIN" without dotted İ → label close-up added, product larger`.

## 3. Repair moves

Every new attempt is a new job id (`s03-r2`, `s03-r3`) in a small plan with the same label, and changes the thing the failure names. Never resend the same input: the result is a differently wrong image at the same price.

| Failure | First re-roll | Second re-roll or repair |
|---|---|---|
| F1 text garbled or misspelt | Add the label close-up as Figure 2; put the quoted text earlier in the prompt; make the product larger in frame; straighten the angle | Move the shot to `openai/gpt-image-2.5/flare/edit` with `"quality": "high"`; still wrong → composite fallback |
| F1 text right but soft | Larger product in frame, or a larger size from the size table | `topaz/upscale/image/precision` with `"model": "Text Refine"`, then re-check F1 on the result |
| F2 logo redrawn or mirrored | Name the drawing in the lock string ("olive branch with seven leaves, stem to the left"); label close-up as Figure 2 | GPT Image 2.5 route; then composite fallback |
| F3 shape drift, stretched, wrong cap | State proportions as numbers; choose a ratio that lets the product stand upright; remove wide-angle wording | Camera back to the reference angle; `fal-ai/bria/product-shot` with `placement_type: "original"`, or composite fallback |
| F4 colour or finish shift | Neutral white key light in the look string; name the colour twice ("deep bottle-green glass, not black, not teal"); `output_format: "png"` | Drop coloured props that bounce onto the product; background-only route `fal-ai/bria/background/replace` |
| F5 duplicates | "Exactly one"; remove props of the same object family; remove mirrors and glossy tables | Simplify the scene to one surface and one backdrop |
| F6 invented text or badges | "No text or labels on any other object"; remove books, packaging, signage, screens, shopping bags from the scene | Keep the scene, erase nothing by hand: re-shoot with fewer props. A "bestseller" seal is a false claim, not a flourish |
| F7 floating, wrong shadow or reflection | Name the contact ("stands on the oak table, soft shadow falling to the right") | Matte surface instead of glossy; lower the camera angle toward the reference's |
| F8 hands | Simplest grip ("resting on an open palm"); hand enters from one frame edge; label unobstructed | `bria/fibo-edit-1.5/product-holding` with a real person photo (consent), or crop the hand out |
| F9 look drift | Hero as the last reference; restate the look string verbatim; drop extra references down to product + hero | Re-derive the shot from the hero itself: hero as Figure 1 with "same set, new framing" |
| F10 wrong size or black frame | Explicit `image_size`; black = safety block, treat as policy hit | Plain wording (`troubleshooting-product.md`), never a disabled checker |

Scale of the failure decides too: the same blocker on both hero candidates means the route is wrong, not the dice. Go straight to the repair column.

### Composite fallback (guaranteed product pixels)

When two generative attempts cannot hold the label, stop generating the product:

1. Make an empty plate: the failed shot's scene without the product. Job on `bytedance/seedream/v5/pro/edit` with the failed output as Figure 1: "Remove the bottle completely. Keep the table, the background, the light and the shadows' direction. Leave the spot where it stood empty and clean."
2. Composite the real product onto it with `pixelcut/product-photo`: `"background": {"mode": "Image", "image_url": "@plate", "image_fit": "Cover"}`, `"shadow": {"type": "Generative"}`, a `margin` that puts the product at the planned size (it is fitted inside the margins: per-side `left`, `right`, `top`, `bottom` values move it off-centre; check placement on the first result), `"sync_mode": false`.
3. QA for F7 and F9. This works when the source photo's camera angle and light direction fit the plate (eye-level, frontal scenes). It fails for top-down or strongly angled scenes: choose a frontal variant of the shot instead.

## 4. Coherence pass (once per set)

After every shot passed on its own, look at the set as a set, once:

- Read all finals in one pass. Same palette family, same light direction and softness, same grade, same surface family as the hero? Copy space on the same side across an ad pack?
- An outlier gets **one** coherence re-roll (it counts against its budget of 2): restate the look string first in the prompt and name the offending colour or light explicitly.
- Still off → drop it from the set or offer it as a standalone image. A set of five that match beats six that do not.

## 5. Mechanical gate before delivery

`pipeline.py manifest --label <slug>` checks that every latest output exists and is not empty and that no id is pending or failed. It exits 1 while `problems` is not empty. A weak shot that was re-rolled under a new id (`s03-r2`) is no problem: the old id stays `completed`. A job that *failed* keeps its id: repair it with `--retry-failed`, or, if you dropped the shot, leave it, log the decision in `plan.md` and name it in the delivery; that is the only kind of problem you may deliver with. Then check by hand: the number of delivered files equals the plan minus logged drops; every delivered file has a line in the delivery message; rejected attempts stay in the output folder but are not listed as deliverables.
