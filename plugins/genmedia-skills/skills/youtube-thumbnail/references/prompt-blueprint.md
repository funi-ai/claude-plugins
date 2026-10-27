# Prompt blueprint

How to write every draft, final and plate prompt. Prompts are English; the on-image text is quoted in its own language and spelling. Endpoints and fields were read from the live schemas on 2026-09-19 (`openai/gpt-image-2.5/flare/text-to-image`, `openai/gpt-image-2.5/flare/edit`, `openai/gpt-image-2.5/sunburst/edit`): `prompt` up to 32,000 characters, no `negative_prompt`, no `seed`, so every exclusion is written as a positive instruction in the CONSTRAINTS block. Concepts come from `frameworks.md`, text rules from `text-and-readability.md`.

## Rules

1. Labelled blocks, fixed order, one short paragraph each. A block that does not apply is left out, never filled with filler.
2. The exact text goes in double quotes, already in its final casing (`thumbcheck.py text` gives `upper` and `spelled`). Never ask the model to translate, uppercase or "make up a catchy line".
3. Say where the text is not: the model composes better when the empty zone is described ("the right 40 percent is a plain dark area for the text").
4. Name one focal point and its share of the frame. Thumbnails fail from timid scale more than from anything else.
5. With references, the first block is a manifest that gives each image a role by position. `image_urls` order must match it.
6. Three drafts differ in blocks SUBJECT to PALETTE and TEXT. FORMAT and CONSTRAINTS stay identical so the comparison is fair.
7. Real brands, channel names and people are never named in a prompt. Describe what is seen.

## Blocks

```text
FORMAT: <YouTube video thumbnail | vertical cover | square cover>, <16:9 | 9:16 | 1:1>, one unified frame,
  built to be recognised at the size of a postage stamp.
REFERENCES: image 1 = <role>. image 2 = <role>.            (only with image_urls)
SUBJECT: <who or what is the single focal point>, <share of frame, position: e.g. left half, 50 percent of height>.
EXPRESSION: <one emotion, its intensity, where the eyes look>.        (people only)
ACTION: <one frozen moment; what the hands do; what is held or pointed at>.
COMPOSITION: <framework layout in words>; focal point on the <left|right> third; <element> overlaps <element> for depth;
  NEGATIVE SPACE: <zone> stays plain for the text; bottom-right corner empty.
BACKGROUND: <simple, low detail; how it separates from the subject: darker, blurred, flat colour>.
LIGHTING: <key light direction and quality>, <rim or hair light for separation>, <contrast level>.
PALETTE: <2 dominant colours + 1 accent; hex plus plain names for brand colours>.
STYLE: <photoreal poster | bold flat graphic | 3D render | ...>, <saturation, sharpness, finish>.
TEXT: the only text in the image reads exactly "<TEXT>" <(letters: <spelled>)>, <lines>, <typeface feel>, <fill colour>,
  <outline or plate behind it>, <position>, <size as share of frame height>. No other words, letters or numbers anywhere.
CONSTRAINTS: no watermark, no logo, no interface elements, no border, no extra people, no small print;
  hands with five fingers; keep faces clear of text and graphics.
```

Block notes:

- **SUBJECT scale.** Faces 40 to 60 percent of frame height, objects 50 to 70 percent. State it as a number.
- **EXPRESSION.** One emotion word plus a physical cue ("eyebrows raised, mouth slightly open, looking at the jar"). Eyes point at the cause or at the text, not at nothing.
- **NEGATIVE SPACE.** Name the zone and its treatment ("the right 45 percent is a smooth dark teal gradient"). For a text-free plate the same sentence stays, the TEXT block goes.
- **LIGHTING.** Separation is the job: a bright rim on a dark field, or a dark subject edge on a bright field. Flat light reads as mud at 160 px.
- **PALETTE.** Two colours plus one accent. High-contrast pairs: yellow on near-black, white on saturated blue, black on yellow, white on red. Avoid red text on blue and green on red (they vibrate).
- **TEXT size.** Cap height about one sixth of the frame height for a single line, about one eighth per line for two lines. Two lines maximum.
- **No text at all** (user's choice): replace the TEXT block with "TEXT: none. No words, letters or numbers anywhere in the image."

## Identity lock (a recurring face)

Add to REFERENCES and SUBJECT whenever a person is rendered from the user's photo or an `@handle`. One to three face references; more adds cost, rarely likeness.

```text
REFERENCES: image 1 = identity reference for the presenter (face and hair only; ignore its background, clothing and lighting).
SUBJECT: the presenter is the person photographed in image 1, and a friend of theirs must recognise them at a glance.
  Their age, the proportions of the face, the eyes, the skin with its moles, lines and freckles, and the hair stay theirs.
  No retouched, younger, slimmer or generic-presenter version of them. Only pose, expression, clothing and lighting are
  new, and those come from this prompt, not from image 1.
```

- `@handle`: append the character's anchor `description` to the first SUBJECT sentence ("... the person photographed in image 1: <anchor>") and keep its wording verbatim.
- Consent first (SKILL.md UX rule 6). A public figure the user is not, or "someone who looks like <name>": do not write the prompt.
- Judge likeness in the small-size gate by opening the reference and the draft together. Likeness drifts most under extreme expressions: if a draft fails, lower the intensity one step before changing anything else.

## Composition lock (the final, from the picked draft)

The final is an edit of the pick, so the user gets the picture they chose. Image 1 is the picked draft; identity references follow.

```text
REFERENCES: image 1 = the approved draft: keep its layout, framing, subject pose, colours, text wording, text position and
  text size. image 2 = identity reference for the presenter.
TASK: render the approved draft again as a finished, full-quality image. Same composition, sharper detail: clean edges on
  the lettering, natural skin texture, crisp eyes, clean background gradients. Do not add, remove or move any element.
<then the original blocks SUBJECT to CONSTRAINTS of that draft, unchanged>
```

If the gate on the draft found a small flaw (text a little small, corner too busy), add exactly one sentence for it after TASK. Anything larger is a new draft, not a final.

## Plate path (text added in a second call)

Plate prompt: the normal blocks with `TEXT: none ...` and an explicit NEGATIVE SPACE sentence. Photoreal plates may run on `bytedance/seedream/v5/pro/text-to-image` with an explicit `image_size` such as `{"width": 1920, "height": 1080}` (inside its lower price tier; its minimum area is 1024x1024, so 1280x720 is rejected; it has no `quality` field). Text-add prompt, on `openai/gpt-image-2.5/flare/edit` for a draft or `openai/gpt-image-2.5/sunburst/edit` for a final, plate as image 1:

```text
REFERENCES: image 1 = the finished picture.
TASK: add one text element and change nothing else. Keep every other pixel of image 1 as it is: same people, faces,
  objects, colours, light and framing.
TEXT: <TEXT block as above, position = the plain zone that image 1 already has>.
```

## Worked prompts

Each is the `prompt` value; size, quality and endpoint per SKILL.md Workflow steps 5 and 8.

**1. Reaction face + curiosity gap, 16:9, face photo.** Video: "I tested a $3 phone charger for 30 days". `image_urls: [<face>]`.

```text
FORMAT: YouTube video thumbnail, 16:9, one unified frame, built to be recognised at the size of a postage stamp.
REFERENCES: image 1 = identity reference for the presenter (face and hair only; ignore its background, clothing and lighting).
SUBJECT: the presenter is the person photographed in image 1, and a friend of theirs must recognise them at a glance: age, face proportions, eyes, skin and hair stay theirs, no retouched or generic version. Head and shoulders on the left, 55 percent of frame height.
EXPRESSION: wary disbelief, one eyebrow raised, lips pressed, eyes on the charger.
ACTION: holds a small white phone charger between two fingers at arm's length, as if it might bite; a thin wisp of smoke rises from it.
COMPOSITION: face on the left third, charger on the right third at eye level, both overlapping a dark field. NEGATIVE SPACE: the top right quarter stays plain for the text; bottom-right corner empty.
BACKGROUND: near-black workshop, heavily blurred, no readable detail.
LIGHTING: soft key from the left, strong orange rim light from behind right on hair and shoulder, high contrast.
PALETTE: near-black and warm skin tones, accent safety orange (#FF6A00).
STYLE: photoreal poster, saturated, crisp, slightly larger-than-life.
TEXT: the only text in the image reads exactly "DAY 30" (letters: D-A-Y / 3-0), one line, heavy condensed sans-serif, white fill, thick black outline, top right, cap height one sixth of the frame height. No other words, letters or numbers anywhere.
CONSTRAINTS: no watermark, no logo, no interface elements, no border, no extra people, no brand marks on the charger; hands with five fingers; face clear of text.
```

**2. Before / after, 16:9, faceless.** Video: "Small balcony makeover on a budget".

```text
FORMAT: YouTube video thumbnail, 16:9, one unified frame split by a clean vertical line, built to be recognised at the size of a postage stamp.
SUBJECT: the same narrow city balcony twice, same camera angle; the right version fills slightly more than half the frame.
COMPOSITION: left 45 percent "before": bare concrete, a broken plastic chair, grey light. Right 55 percent "after": wooden deck tiles, two cushions, string lights, green plants, golden hour. A thin white divider. NEGATIVE SPACE: the upper left area of the dull side stays plain for the text; bottom-right corner empty.
BACKGROUND: soft blurred rooftops, identical on both sides.
LIGHTING: left flat and overcast, right warm low sun with glowing string lights; strong contrast between the halves.
PALETTE: cold grey against warm amber and leaf green, accent yellow (#FFD400).
STYLE: photoreal, bright, clean, believable for a small budget.
TEXT: the only text in the image reads exactly "$180" (characters: $-1-8-0), one line, heavy rounded sans-serif, yellow fill (#FFD400), thick black outline, upper left, cap height one fifth of the frame height. No other words, letters or numbers anywhere.
CONSTRAINTS: no watermark, no logo, no interface elements, no border, no people; nothing in the "after" half that the budget could not buy.
```

**3. Big number, 16:9, graphic, brand colours.** Video: "7 spreadsheet mistakes that cost you hours".

```text
FORMAT: YouTube video thumbnail, 16:9, one unified frame, built to be recognised at the size of a postage stamp.
SUBJECT: a giant numeral 7 as a solid 3D object, 70 percent of frame height, left of centre, cracked where a small red error triangle is wedged into it.
COMPOSITION: numeral on the left half, tilted 5 degrees; behind it a huge, out-of-focus grid of pale cells. NEGATIVE SPACE: right 40 percent is a smooth deep green gradient for the text; bottom-right corner empty.
BACKGROUND: deep green (#0B3D2E) to black gradient, faint grid lines only.
LIGHTING: hard top-left key, crisp drop shadow, glossy highlight on the numeral's edge.
PALETTE: deep green (#0B3D2E) and white, accent alarm red (#FF3B30).
STYLE: bold 3D graphic, clean, high saturation, no photographic clutter.
TEXT: the only text in the image, apart from the giant 7, reads exactly "MISTAKES" (letters: M-I-S-T-A-K-E-S), one line, heavy condensed sans-serif, white fill, right side, vertically centred, cap height one seventh of the frame height. No other words, letters or numbers anywhere.
CONSTRAINTS: no watermark, no logo, no real software interface, no border, no small print, no readable cell contents.
```

**4. Tutorial result with Turkish text, 16:9.** Video: "Evde ekşi maya nasıl yapılır?". `thumbcheck.py text "7 günde ekşi maya" --lang tr` → `7 GÜNDE EKŞİ MAYA`.

```text
FORMAT: YouTube video thumbnail, 16:9, one unified frame, built to be recognised at the size of a postage stamp.
SUBJECT: a glass jar of lively sourdough starter, bubbly and domed above a rubber band mark, 65 percent of frame height, right of centre.
ACTION: a wooden spoon lifts a stretchy ribbon of starter from the jar.
COMPOSITION: jar on the right third, spoon rising towards the upper right; a small out-of-focus bag of flour behind. NEGATIVE SPACE: the left 45 percent is a plain dark wooden surface fading to shadow for the text; bottom-right corner empty.
BACKGROUND: dark rustic kitchen, heavily blurred.
LIGHTING: warm window light from the right, bright rim on the glass, deep shadows on the left.
PALETTE: dark walnut brown and cream, accent warm yellow (#FFC93C).
STYLE: photoreal food photography, appetising, crisp bubbles, rich contrast.
TEXT: the only text in the image is Turkish and reads exactly "7 GÜNDE" on the first line and "EKŞİ MAYA" on the second line (letters: 7 / G-Ü-N-D-E / E-K-Ş-İ / M-A-Y-A). Spell it with the Turkish letters Ü (U with two dots), Ş (S with a cedilla) and İ (capital I with a dot above); do not replace them with U, S or I. Heavy sans-serif with full Turkish glyph support, cream fill, first line in yellow (#FFC93C), thick dark outline, left side, each line one eighth of the frame height. No other words, letters or numbers anywhere.
CONSTRAINTS: no watermark, no logo, no interface elements, no border, no hands other than the one holding the spoon, no label on the jar.
```

**5. Screenshot + callout, 16:9, plate path on a real frame.** The plate is the user's own frame (`thumbcheck.py frame`), enlarged if needed (`revisions.md`, Enlarge). `image_urls: [<frame>]`, endpoint `openai/gpt-image-2.5/flare/edit`.

```text
REFERENCES: image 1 = a real frame from the user's video. It is the picture; do not redraw or restyle it.
TASK: crop in so that the settings panel on the right fills about 70 percent of the frame, keep all on-screen content exactly as it is, then add one callout and one text element. Change nothing else.
COMPOSITION: a thick yellow (#FFD400) hand-drawn circle around the "Auto-save" toggle, a short yellow arrow pointing at it from the lower left. Slightly darken everything outside the circle. Bottom-right corner empty.
TEXT: the only added text reads exactly "TURN THIS OFF" (letters: T-U-R-N / T-H-I-S / O-F-F), one line, heavy condensed sans-serif, white fill, thick black outline, lower left, cap height one seventh of the frame height. Add no other words.
CONSTRAINTS: no watermark, no invented interface elements, no logos added, do not alter any existing on-screen text.
```

**6. Vertical cover with an `@handle` character, 9:16.** Short: "3 stretches for desk workers". Anchor text comes from `character.json`; `image_urls: [<face ref 1>, <face ref 2>]`; drafts 720x1280.

```text
FORMAT: vertical cover for a short video, 9:16, one unified frame, recognisable as a tiny tile in a profile grid.
REFERENCES: image 1 and image 2 = identity references for the presenter (face and hair only).
SUBJECT: the presenter is the same person as in images 1 and 2: <anchor description verbatim>. Upper body, centred, head in the upper-middle of the frame, 35 percent of frame height.
EXPRESSION: relieved smile, eyes closed for a moment.
ACTION: seated on an office chair, both arms stretched overhead, fingers interlaced.
COMPOSITION: everything important inside the central 4:5 area; NEGATIVE SPACE: a plain band across the vertical centre-lower area, behind the torso, for the text; top strip and bottom third free of text and faces.
BACKGROUND: bright minimal home office, soft blur, one plant.
LIGHTING: large soft window light from the left, gentle rim on the arms.
PALETTE: warm white and sage green, accent coral (#FF6F61).
STYLE: photoreal, fresh, friendly, clean.
TEXT: the only text in the image reads exactly "3 DESK STRETCHES" on two lines, "3 DESK" then "STRETCHES" (letters: 3 / D-E-S-K / S-T-R-E-T-C-H-E-S), heavy rounded sans-serif, white fill, coral (#FF6F61) plate behind the letters, centred horizontally, just below the vertical centre, each line one fourteenth of the frame height. No other words, letters or numbers anywhere.
CONSTRAINTS: no watermark, no logo, no interface elements, no border, no extra people; hands with five fingers.
```

Square covers (podcast, course): use frameworks 9 or 12, FORMAT "square cover, 1:1", at most three words, cap height one fifth of the frame, show name or episode number small in a fixed corner.
