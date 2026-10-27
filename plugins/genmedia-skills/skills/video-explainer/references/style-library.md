# Style library

Ten explainer looks. Each has a **STYLE string** (saved verbatim with `explainer.py style --style-file`, pasted by the helper into every keyframe and clip prompt) and a **key-image prompt** (the one picture that every keyframe references). The style is chosen with the user at CP1; the key image is approved at CP2. Scene and motion rules: `blocks-and-script.md`.

## How the style key works

1. **STYLE string** = technique, line, fill, palette, light, texture, in 1-3 English sentences, ending with a realism statement. No subject matter, no brand, studio, film, game or artist names: describe the physical look instead. Fill the `<accent>` slots with the user's colours if they gave any (as plain colour words plus hex), else keep the defaults.
2. **Key image** = a neutral plate in that style with three or four simple objects and the full palette. It anchors technique and colour, not content. The helper's keyframe prompt tells the model to take only the style from it. Generate it at the video's aspect ratio (the helper sets the size).
3. **Every keyframe** = `<reference instruction> Scene: <scene>. <STYLE string> <negative>`, with the key image (and the mascot sheet, if any) as references. You never write this by hand; `explainer.py plan --stage keyframes` does.
4. Changing the STYLE string after CP1 reopens the outline approval; changing the key image reopens CP2. Both are deliberate: a new look is a new video.

Write the key-image prompt to `.genmedia/projects/<slug>/stylekey.txt`; the helper appends the STYLE string if your file does not contain it. A key image that comes back with lettering, a face in close-up or a busy scene is re-rolled (`--reroll`): whatever is in it leaks into every block.

**Choosing** (first match wins; show the user two options when two fit):

| Content | Style |
|---|---|
| Step-by-step reasoning, school subjects, "how X works" for a general audience | 1 whiteboard |
| Software, business, product concepts, startup and SaaS topics | 2 flat vector |
| Systems with parts and flows: logistics, cloud architecture, factories, cities | 3 isometric |
| Stories, history, culture, children, warm brand voice | 4 paper cut-out |
| Friendly product or character-led topics, consumer apps, playful brands | 5 clay 3D |
| Engineering, mechanics, architecture, "under the hood" | 6 blueprint |
| Nature, health, wellbeing, reflective essays | 7 watercolour |
| Real-world subjects where credibility matters: science news, geography, industry | 8 cinematic documentary |
| Numbers are the story: economics, reports, comparisons | 9 data-viz |
| Technology, security, space, night-time or "future" topics | 10 neon line |

Photoreal people in a documentary style raise consent and uncanny-motion risks; prefer places, objects and hands. All illustrated styles animate more forgivingly than photoreal ones: a reason hybrid and full tiers default to them.

## 1. Whiteboard

- **STYLE:** `Hand-drawn whiteboard marker illustration on a clean white background, confident black marker outlines of uneven thickness, flat fills in only two accent colors, <teal #1F9E9E> and <orange #F28C28>, small hatching for shadow, generous empty space, slightly wobbly hand-made lines. A drawn illustration with no photographic realism.`
- **Key image:** `A style reference plate: a light bulb, a paper airplane, a potted plant and a curved arrow, arranged loosely with wide gaps on a white board. No hands, no markers, no frame.`
- **Motion:** lines drawing themselves, objects sliding in, arrows growing. Avoid a drawing hand: it morphs.
- **Watch for:** grey paper texture creeping in; ask for "pure white background" in the scene if it does.

## 2. Flat vector

- **STYLE:** `Modern flat vector illustration, geometric simplified shapes, no outlines, smooth solid fills with at most one soft shadow shape per object, limited palette of <deep blue #1E3A8A>, <sky blue #60A5FA>, <warm yellow #FBBF24> and off-white, soft rounded corners, clean negative space, subtle paper grain. A drawn illustration with no photographic realism.`
- **Key image:** `A style reference plate: a laptop, a coffee cup, a location pin and a simple human figure with no facial features, evenly spaced on an off-white background.`
- **Motion:** elements scale in, slide, rotate; charts grow. The most stable style for image-to-video.
- **Watch for:** faces. Keep figures featureless ("no facial features") for consistency across blocks.

## 3. Isometric

- **STYLE:** `Isometric vector illustration at a fixed 30 degree angle, clean geometric volumes with three flat tones per surface (top light, left mid, right dark), thin darker edge lines, palette of <indigo #4F46E5>, <mint #34D399>, <coral #FB7185> on a very light grey floor plane, tiny rounded details, no perspective distortion. A drawn illustration with no photographic realism.`
- **Key image:** `A style reference plate: a small warehouse building, a delivery van, a server rack and a tree on one isometric floor tile grid, seen from the same fixed isometric angle.`
- **Motion:** vehicles travel along paths, packages move on belts, lights blink. State "camera stays fixed, isometric angle unchanged".
- **Watch for:** the angle flipping between blocks; repeat "same fixed isometric angle, seen from the upper left" in every scene.

## 4. Paper cut-out

- **STYLE:** `Layered paper cut-out collage, shapes cut from matte colored craft paper with slightly rough edges, visible paper fibre texture, soft drop shadows between layers that show real depth, palette of <terracotta #C8553D>, <mustard #E0A526>, <sage #8AA17D> and cream, lit softly from the upper left. Handmade stop-motion craft look with no photographic realism and no real people.`
- **Key image:** `A style reference plate: a paper sun, a paper mountain range in three layers, a paper house and a paper bird, layered with visible shadows on a cream paper background.`
- **Motion:** layers slide sideways at different speeds (parallax), pieces hinge or flutter. Slight stop-motion stutter is on-style.
- **Watch for:** the model drifting to glossy vector; the words "matte", "fibre texture" and "drop shadows between layers" hold it.

## 5. Clay 3D

- **STYLE:** `Soft clay 3D render, rounded chunky forms with visible fingerprint-like surface texture, matte plasticine materials, pastel palette of <peach #FFB4A2>, <lavender #B8A9E8>, <mint #A8E6CF> with one saturated accent <blue #3B82F6>, soft studio lighting from the upper left with gentle contact shadows, shallow depth of field, plain pastel backdrop. Stylized miniature, not photorealistic, no real people.`
- **Key image:** `A style reference plate: a clay rocket, a clay cloud, a clay smartphone and a small round clay character with dot eyes, standing on a plain pastel floor with a seamless backdrop.`
- **Motion:** squash and stretch, bouncing, objects rolling in; slow orbit of the camera works here (true 3D look).
- **Watch for:** mascot drift. If a clay character recurs, build a sheet with `/genmedia-skills:character` and pass it via `style --ref-url`.

## 6. Blueprint

- **STYLE:** `Technical blueprint drawing, fine white and pale cyan line work on a deep blueprint blue background <#0B3C8C>, precise orthographic and cutaway views, thin construction lines and dashed hidden edges, faint grid, small arrowheads and dimension ticks without any numerals or lettering, one highlight color <amber #FFB000> for the part being explained. A technical drawing with no photographic realism.`
- **Key image:** `A style reference plate: a cutaway of a simple gear pump, a bolt and a small electric motor drawn as blueprint line work on a gridded blueprint sheet, with dimension ticks but no numerals or letters.`
- **Motion:** lines trace in, the amber highlight travels through the mechanism, parts explode apart slowly.
- **Watch for:** fake dimension text. The negative covers it; if gibberish numerals still appear, add "no numerals anywhere" to the scene.

## 7. Watercolour

- **STYLE:** `Loose watercolour illustration on cold-press paper, soft wet-on-wet washes with blooming edges, visible paper grain and pigment granulation, delicate pencil under-drawing, airy composition with unpainted white paper around the subject, palette of <sea green #5FA8A0>, <dusty rose #D8A7A0>, <ochre #D9A441> and soft grey. A hand-painted picture with no photographic realism.`
- **Key image:** `A style reference plate: a painted leaf, a small bird, a teacup and a rolling hill, each as a loose watercolour vignette with white paper between them.`
- **Motion:** washes spreading, leaves drifting, light shifting. Ask for very slow motion; fast movement breaks the painted texture.
- **Watch for:** edges filling the whole frame. "Unpainted white paper around the subject" keeps the vignette.

## 8. Cinematic documentary

- **STYLE:** `Cinematic documentary photography, natural available light with soft contrast, 35mm lens look with shallow depth of field, muted natural color grade leaning <teal> in shadows and <warm amber> in highlights, fine film grain, steady tripod framing, real-world textures and honest detail. Photorealistic, no illustration, no people looking into the camera.`
- **Key image:** `A style reference frame: a wooden desk by a window in morning light with a notebook, a glass of water and a small plant, shot as a quiet documentary still life.`
- **Motion:** slow push-in, drifting dust or steam, a hand entering the frame. The premium clip model earns its price here; illustrated styles forgive the value model more.
- **Watch for:** identifiable real people, brands on objects, and invented signage. Places, objects, hands and silhouettes are safe subjects. Facts shown photoreally look like evidence: never stage an event that did not happen as if it were footage.

## 9. Data-viz

- **STYLE:** `Clean editorial data visualisation graphic, flat geometric charts and diagram shapes on a dark charcoal background <#111827>, thin precise lines, rounded bar ends, palette of <electric blue #3B82F6>, <emerald #10B981>, <amber #F59E0B> with light grey guides, generous margins, subtle soft glow under highlighted elements, completely free of numerals, letters and labels. A vector graphic with no photographic realism.`
- **Key image:** `A style reference plate: a bar chart with five bars, a donut chart, a rising line chart and a row of simple pictogram people, all unlabeled, arranged in a tidy grid.`
- **Motion:** bars growing, the line drawing itself, segments filling, pictograms counting up by appearing. Growth direction must match the fact (up is more).
- **Watch for:** proportions are claims. A bar twice as tall says "double": describe the ratio in the scene ("the right bar is about twice the height of the left one") and check it at CP4. Exact values belong in the narration and captions; charts that must carry readable numbers are typography stills (SKILL.md, Role defaults), not animated.

## 10. Neon line

- **STYLE:** `Minimal neon line art on a near-black background <#0A0A12>, single-weight glowing outlines in <cyan #22D3EE> and <magenta #E879F9> with a soft outer glow, no fills, simple iconic shapes, faint dotted grid floor receding into darkness, high contrast. A line graphic with no photographic realism.`
- **Key image:** `A style reference plate: a glowing outline of a padlock, a satellite, a microchip and a paper plane, spaced evenly above a faint dotted grid.`
- **Motion:** outlines drawing on, pulses travelling along lines, slow grid drift.
- **Watch for:** strobing. Ask for "steady glow, no flicker, no flashing" in motion lines; flashing content is a photosensitivity risk.

## Variants

- **User's brand colours.** Replace the `<accent>` slots; keep the count of colours. More than four colours stops reading as a style.
- **Style donor images** (the user's own illustrations or a brand guide page). Read them first with the Read tool, write a STYLE string that describes what you see, upload them, and generate the key image on `bytedance/seedream/v5/pro/edit` with the donors as `image_urls` and this opening sentence before the plate description: `The input images are style donors: borrow their rendering technique, palette and line quality, and nothing of their characters, lettering or layout.` Run it as `plan --stage stylekey --endpoint bytedance/seedream/v5/pro/edit --base-input <file with image_urls>`. Only with images the user owns or may use.
- **Mascot or host.** Default is faceless. If the user wants a recurring character: `/genmedia-skills:character` produces the sheet and handle; add its URLs with `style --ref-url <url>` (repeat the flag, at most 9 so the key image stays among the 10 references Seedream reads), describe the character with identical words in every scene, keep the mouth closed in motion lines, and budget +$0.0045 per extra reference per keyframe (dated 2026-09-19).
- **Custom style.** Write it with the same anatomy: technique → line → fill → palette (2-4 named colours with hex) → light → texture → realism statement. Test it with the key image before CP2; a STYLE string that needs a paragraph of exceptions is two styles.

## Negative line

The helper appends `No text, no letters, no numbers, no captions, no logos, no watermark.` to every keyframe prompt and a no-text, no-speech, one-shot line to every clip prompt. Replace the keyframe negative only for a reason (`style --negative-file`), for example adding "no people" for a faceless brand. Never remove the lettering ban: garbled text is the most common reason a keyframe fails CP4.
