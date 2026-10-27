# Prompting for still images

How to turn a request into a prompt that lands on the first or second try. Field names mentioned here were read from the live schemas on 2026-09-19; behaviour notes are craft guidance, not guarantees. Endpoint choice: [routing-image.md](routing-image.md). Prompts for edits and utilities: [editing-recipes.md](editing-recipes.md).

## Ground rules

1. Write prompts in English. Text that must appear in the picture stays in the user's language, in quotes, spelled exactly.
2. Describe what a camera or a designer would see. "Award-winning, stunning, masterpiece, 8k, ultra-detailed, hyperrealistic" carry no visual information and push models toward a glossy synthetic look. Delete them.
3. A style word needs a visual target: not "cinematic" but "anamorphic wide shot, teal shadows, warm practical lamps, light haze".
4. Say what should be there, not what should not. Only a few endpoints have a `negative_prompt` field (check the schema); everywhere else "no people" can summon people. Write "an empty street" instead.
5. One subject, one idea, one light. Two ideas are two jobs.
6. Never assume a control exists. `seed`, `num_images`, `negative_prompt`, `quality`, `resolution` are all missing on some families. The schema decides.
7. Per-family rules below override the universal structure.

## Universal structure

Nine slots, in this order. Models weight the beginning: subject first, constraints last. Fill what matters for the job, skip the rest; 40 to 120 words suits most photo prompts.

| # | Slot | Write | Weak → strong |
|---|---|---|---|
| 1 | Subject | who or what, with 2 to 3 defining traits | "a woman" → "a woman in her sixties, silver bob, denim work apron" |
| 2 | Action | a verb in mid-motion | "standing" → "wiping clay from her hands with a rag" |
| 3 | Setting | place, time, one anchoring detail | "in a studio" → "in a small pottery studio, late afternoon, shelves of unglazed bowls behind her" |
| 4 | Composition and lens | shot size, angle, focal length feel, depth of field, where the subject sits | "close up" → "waist-up, eye level, 50mm look, subject on the right third, background softly out of focus" |
| 5 | Lighting | source, direction, quality, colour | "good lighting" → "window light from the left, soft, warm; deep shadow on the far cheek" |
| 6 | Palette | 2 to 4 named colours and their roles | "colourful" → "clay browns and off-white, one accent of cobalt blue on the apron" |
| 7 | Texture and material | surfaces the eye can feel | "detailed" → "dusty wood bench, wet clay sheen, linen weave" |
| 8 | Style or medium | photo genre and era, or illustration medium | "realistic" → "documentary photograph, 35mm colour negative film, visible grain" |
| 9 | Constraints | framing for use, empty areas, exact text, exclusions phrased positively | "no text" → "plain wall fills the top third, free of objects" |

Assembled: `A woman in her sixties with a silver bob and a denim work apron wipes clay from her hands with a rag in a small pottery studio, late afternoon, shelves of unglazed bowls behind her. Waist-up, eye level, 50mm look, she sits on the right third, background softly out of focus. Soft warm window light from the left, deep shadow on the far cheek. Clay browns and off-white with one cobalt-blue accent on the apron. Dusty wood bench, wet clay sheen, linen weave. Documentary photograph on 35mm colour negative film, visible grain. The top third is plain wall.`

## Per-family notes

### Seedream 5.0 Pro (`bytedance/seedream/v5/pro/…`)
- Full sentences in photographic language; the universal structure maps one to one. Strong on film looks, portraits, product and lifestyle scenes.
- No `seed` and no `negative_prompt` in the schema. Variation comes from `num_images` (1 to 6) or from rewording one slot.
- Short on-image text works when quoted (fal lists native text rendering in 14 languages); for layouts, several text blocks or small type, route to GPT Image 2.5 instead.
- Always send `image_size` as `{width,height}`: the `auto_2K` default can land in the higher price tier.

### GPT Image 2.5 Flare / Sunburst (`openai/gpt-image-2.5/…`)
- Think design brief, not caption. It follows long, sectioned instructions (the schema allows 32,000 characters) and honours layout. Use labelled lines:

  ```
  Format: A3 portrait gig poster for print.
  Layout: headline across the top third; illustration in the centre; details in a strip along the bottom; wide margins.
  Text (exact, nothing else): headline "NEON NIGHTS"; details "12 Ekim · Zorlu PSM · 21.00".
  Type: heavy condensed sans for the headline, light sans for details, white on dark.
  Visual: a saxophone player in silhouette against magenta and cyan stage haze, screen-print texture.
  Palette: near-black, magenta, cyan, white.
  Rules: spell every word exactly as quoted, Turkish characters intact; no other words, logos or signatures.
  ```
- Set `quality` on every call: `medium` while exploring, `high` for finals. `background: "transparent"` with `output_format: "png"` for cut-out assets.
- No `seed`. Iterate by editing the result (`…/edit`) rather than rerolling: "keep everything, change only …".
- Edits: three labelled sentences. `Change:` what becomes different. `Keep:` what must stay identical (name it: face, pose, framing, label, colours). `Blend:` how the change sits in the scene (light direction, shadow, perspective, scale, grain).

### Nano Banana Pro / 2 (`fal-ai/nano-banana-pro`, `fal-ai/nano-banana-2`)
- Conversational instructions work: say what the image is for and who will see it, then describe it. It reasons about the request, so give context rather than keyword lists.
- `enable_web_search: true` when the picture depends on real-world facts (a current product, a landmark's actual look, data for an infographic); it adds a small fee. `thinking_level` exists on Nano Banana 2 only.
- `system_prompt` holds a house style across calls (palette, illustration manner) so the per-image prompt stays short.
- Size is `aspect_ratio` plus `resolution`; `seed` exists. In edits, refer to inputs by position ("the second image").

### FLUX.2 (`fal-ai/flux-2-pro`, `fal-ai/flux-2-max`)
- Descriptive prose, subject first, camera and light spelled out. No negative prompt.
- Pro and Max have no `num_images`: variations are separate jobs with different `seed` values in one batch.
- `image_size` takes presets or `{width,height}`; per-megapixel pricing makes size the cost lever.

### Recraft vector (`fal-ai/recraft/v4.1/text-to-vector`)
- Write a mark brief, not a scene. Name the mark type (wordmark, monogram, pictorial mark, emblem, icon set), the geometry (circle grid, rounded terminals, single stroke weight), fill versus outline, and the number of colours.
- Put brand colours in the `colors` field as `[{"r":…,"g":…,"b":…}]` and the backdrop in `background_color`; colour words in the prompt are a weaker signal.
- Photographic vocabulary (lens, depth of field, lighting) does not apply. Ask for flat shapes, generous negative space, and legibility at 32 px.
- No `num_images` and no `seed`: run 3 to 4 concept prompts as separate jobs, each a different idea (not a paraphrase). Keep a wordmark short and quoted; check the spelling in the result.
- Brand-consistent sets: create a style once with `recraft/v4/create-style`, then pass `style_id` to `recraft/v4/style/text-to-vector`.

### Ideogram V4 (`ideogram/v4`, `ideogram/v4/fast`)
- Typography-first family. Put the quoted text early, then the typographic treatment (weight, width, case, arrangement), then the imagery behind it.
- `expansion_model` rewrites the prompt (default `Medium`, extra fee). Send `"None"` when the copy must be exact or the prompt is already complete.
- `rendering_speed`: `TURBO` for drafts, `QUALITY` for finals. `seed` exists: fix it while adjusting wording.

## Realism checklist (the anti-AI look)

A photo reads as synthetic when everything is clean, centred, evenly lit and posed. Add real-world evidence by name:

| Area | Ask for |
|---|---|
| Skin | visible pores, fine lines, uneven tone, a few freckles or a blemish; never "flawless" |
| Hair | flyaway strands, an imperfect parting, hair crossing the face |
| Eyes | a catchlight that matches the named light source; gaze off-camera unless it is a portrait to camera |
| Hands | give them a task (holding, gripping, resting on something) or keep them out of frame |
| Light | one motivated key light with a direction; let shadows be dark; mix temperatures (warm lamp against cool window) |
| Optics | a focal-length feel, a clear focal plane with something soft in front of or behind it, slight motion blur on moving parts, grain or sensor noise |
| Framing | subject off-centre, a partly cropped object at the edge, something in the foreground |
| Moment | a mid-action verb instead of a pose; asymmetric posture, weight on one leg |
| Place | lived-in detail: scuffed floor, cables, crumbs, creased fabric, fingerprints on glass; a real background, not a gradient void |
| Era | one capture device and stay with it: "recent flagship phone photo", "35mm colour negative, 1990s", "instant film"; do not mix |

Still looks rendered after one try → add a named imperfection from the table. Do not add adjectives. Product shots are the exception: keep the product clean and put the imperfection in the surface and surroundings.

## Text in the image

1. Route first: legible words mean GPT Image 2.5 (or Ideogram V4 on a budget), not a photo model.
2. Quote every string exactly and add "exact text, nothing else". Keep each block under about eight words and the image under three blocks.
3. Give hierarchy and position: which block is largest, where each sits, alignment, and what is behind it (a calm area or a solid panel for contrast).
4. Describe type by category and feature (bold condensed sans, high-contrast serif, rounded monoline script), not by commercial font names.
5. Non-English copy: keep it verbatim and name the risky characters ("Turkish characters İ, ı, ş, ğ, ç, ö, ü must be correct"). Spell a fragile word letter by letter in parentheses.
6. Never trust generated prices, dates, URLs, phone numbers or legal lines. Either verify them character by character in the result or leave negative space and let the user typeset them.
7. Body copy (more than about 25 words) is not rendered in the model. Reserve the area instead.
8. QA: open the result and read every word against the brief. One wrong block → edit endpoint: `Change: the headline must read exactly "…". Keep: everything else.` Two failures → deliver the image with clean negative space and say the text should be set in a design tool.

## Negative space for overlays

When the user will add copy, a logo or UI on top:

- Name the area and its size: "the left 40 percent", "the top third", "a band along the bottom".
- Say what fills it: plain wall, clear sky, out-of-focus backdrop, a smooth gradient of the scene's own colour. Low detail and even tone keep later text legible.
- Put the subject on the opposite third, looking or moving toward the empty area.
- State it positively: "the top third is empty sky, free of objects and text".
- Keep the subject about 10 percent away from every edge so platform crops survive. Thumbnails: face on one side, room for three or four large words on the other.
- In the delivery line, tell the user where the space is.

## Worked rewrites

**1. Portrait, photoreal** → `bytedance/seedream/v5/pro/text-to-image`, `{"width":1296,"height":1728}`
- Before: `beautiful realistic portrait of a fisherman, 8k, ultra detailed`
- After: `A weathered fisherman in his fifties, grey stubble, orange waterproof jacket, coils a wet rope on the deck of a small boat at dawn. Chest-up, slightly below eye level, 85mm look, he is left of centre, harbour lights blurred behind. Cold blue ambient light with a warm deck lamp from the right catching the side of his face. Visible pores, cracked knuckles, salt stains on the jacket. Documentary photograph, 35mm colour negative film, grain.`
- Why: traits, a mid-action verb, a motivated two-temperature light and named imperfections replace the praise words.

**2. Product hero with room for copy** → same endpoint, `{"width":2048,"height":1152}`
- Before: `coffee bag product photo, nice background`
- After: `A matte kraft-paper coffee bag with a black label stands on a rough concrete counter, a few roasted beans scattered at its base. The bag sits on the right third, straight-on at label height, 70mm look, shallow depth of field. Soft daylight from a large window on the left, gentle contact shadow to the right. Warm browns and grey concrete, no other props. The left 45 percent is empty, softly blurred plaster wall in even tone. Commercial still-life photograph.`
- Why: placement, light matched to a matte material, and a described empty area the designer can use. With a real product photo, run it as recipe 7 in editing-recipes.md instead.

**3. Poster with Turkish copy** → `openai/gpt-image-2.5/flare/text-to-image`, `quality: "high"`, `{"width":1024,"height":1536}`
- Before: `yaz festivali afişi yap, tarih 5 temmuz`
- After: the labelled brief pattern above with `Text (exact, nothing else): headline "YAZ FESTİVALİ"; sub-line "5 Temmuz · Kadıköy Sahil"`, `Rules: Turkish characters İ and ö must be correct; no other words.`
- Why: the copy is quoted in Turkish while the brief is English; hierarchy and positions are explicit; the risky glyphs are named. Afterwards read the poster and compare every character.

**4. Logo** → `fal-ai/recraft/v4.1/text-to-vector`, `colors: [{"r":18,"g":52,"b":86},{"r":244,"g":162,"b":97}]`
- Before: `modern logo for a bakery called Fırın 1923, photorealistic, 3D`
- After: `Pictorial mark plus wordmark for an artisan bakery. Mark: a stylised wheat ear forming a rising sun, built from five rounded leaf shapes, single stroke weight, flat fill. Wordmark "Fırın 1923" in a warm humanist serif, set to the right of the mark. Two colours only on a plain off-white background. Balanced, generous spacing, readable at 32 px.`
- Why: a logo is geometry and restraint; photo terms were removed, colours moved into the `colors` field, and the deliverable is SVG. Run three different concepts as separate jobs.

**5. Instruction edit** → `openai/gpt-image-2.5/flare/edit`
- Before: `make it night`
- After: `Change: turn the scene to night, deep blue sky with a few stars, street lamps on with warm pools of light, windows lit. Keep: the buildings, the parked cars, the two people, the framing and every sign exactly as they are. Blend: shadows fall away from each lamp, reflections of the lamps on the wet road, overall exposure low but faces still readable.`
- Why: one change, an explicit keep list, and physics so the edit does not look pasted.

**6. Multi-reference** → `bytedance/seedream/v5/pro/edit`
- Before: `put her in this jacket in paris`
- After: `Image 1 is the woman. Image 2 is the jacket. Image 3 is the street. Dress the woman from image 1 in the jacket from image 2, zipped halfway, and place her walking toward camera on the street from image 3. Keep her face, hair and build exactly as in image 1. Keep the jacket's cut, colour and chest logo exactly as in image 2. Match the overcast light and wet pavement of image 3. Full body, 35mm look, mid-stride.`
- Why: a manifest fixes roles by position, identity is referenced instead of described, and light is taken from the scene image.

**7. Film still** → `bytedance/seedream/v5/pro/text-to-image`, `{"width":2048,"height":1152}`
- Before: `cinematic shot of a detective in the rain`
- After: `A tired detective in a soaked grey trench coat lights a cigarette under a flickering pharmacy sign on an empty backstreet at night. Wide shot from across the road, low angle, anamorphic look with horizontal flare from the sign, he stands small on the left third. Green neon from the sign against sodium-orange street light, rain streaks backlit, steam from a grate. Wet asphalt reflections, heavy film grain. Still frame from a 1970s crime film.`
- Why: "cinematic" became a lens, a colour contrast, a blocking decision and an era.

**8. Infographic or UI mock** → `openai/gpt-image-2.5/flare/text-to-image` (`fal-ai/nano-banana-pro` with `enable_web_search` when the facts must be looked up)
- Before: `infographic about coffee brewing methods`
- After: a labelled brief: `Format: 1536x1024 landscape infographic. Layout: title bar on top, four equal columns below, thin dividers. Text (exact, nothing else): title "FOUR WAYS TO BREW"; column heads "Espresso", "Pour-over", "French press", "Cold brew"; under each, one line: "25 s · fine", "3 min · medium", "4 min · coarse", "12 h · coarse". Visual: one flat line icon of the device per column. Palette: cream background, dark brown text, one orange accent. Rules: no other words or numbers.`
- Why: every string is supplied by you, so nothing is invented; the grid is explicit; numbers can be verified on the result.

## Iterating

- Change one slot per round and say which. Keep the seed where one exists.
- Describe the defect in observable terms ("light is flat and frontal") and fix that slot, rather than adding emphasis words or capitals.
- The same failure twice means the approach is wrong: change the route (edit instead of reroll, another family, text set in post), not the adjectives.
- Carry the approved prompt forward verbatim into variants and later edits; consistency lives in repeated wording.
