# Look and variation matrix

How to commit a look before prompting, how to vary a set without breaking it, and what not to reach for. The product never varies; only the world around it does. `{LOCK}` and the rubric live in `fidelity-qa.md`; templates in `modes.md`.

## 1. The look string

One fixed English paragraph of 35 to 60 words, written once, saved as the `Look:` line in `.genmedia/projects/<slug>/plan.md`, pasted verbatim into every generative prompt of the shoot. It carries what makes six images one campaign:

| Slot | Decide | Example |
|---|---|---|
| Palette | 2 colours taken from the pack + 1 neutral + at most 1 accent; brand hexes only if the user gave them | "deep green and cream from the label, warm oak, one accent of lemon yellow" |
| Light | direction, quality, colour temperature. Neutral white on the product | "soft window light from camera left, gentle falloff, neutral white" |
| Surface family | one material family for the whole set | "pale oak and unglazed ceramic" |
| Lens and depth | one feel | "50 mm feel at eye level, background softly out of focus" |
| Grade | contrast and saturation in plain words | "natural contrast, true colours, no filter look" |
| Mood | two words, concrete | "unhurried, domestic" |
| Invariants | always the same sentence | "No text, logos or watermarks except the product's own label." |

```text
Look: palette of deep green and cream taken from the label, warm pale oak and unglazed ceramic surfaces, one accent of lemon yellow. Soft window light from camera left, neutral white, gentle shadows falling right. 50 mm feel at eye level, background softly out of focus. Natural contrast, true colours. Unhurried, domestic. No text, logos or watermarks except the product's own label.
```

Default look when the user gave none: derive the palette from the pack, neutral soft daylight, one natural surface that fits the category (section 3), eye level. Say so under Assumptions. After the hero is approved, the string is frozen: a change of look is a new plan version and a new hero.

## 2. Axes

Commit one pick per axis for the hero **before** writing its prompt, and write the picks into `plan.md` (`Axes: angle=front-3/4-right; framing=product-40%; surface=pale-oak; ...`). Variants then move along the *free* axes only.

| Axis | Options | Locked or free inside a set |
|---|---|---|
| Palette | from the look string | **locked** |
| Light quality and direction | soft window / overcast / hard sun with crisp shadow / studio softbox; left or right | **locked** (time of day may shift only in a seasonal sub-set) |
| Grade | natural / bright and airy / deep and contrasty | **locked** |
| Surface family | wood, stone, linen, ceramic, paper, brushed metal, concrete, water-safe tile | locked family, free member (oak table → oak shelf) |
| Angle | front, three-quarter left or right, slightly above, top-down, low hero angle | free, **but only inside the reference coverage** written in the lock |
| Framing | product fills 70% (bold crop) / 40% (standard) / 15% (environmental) | free |
| Composition anchor | centred / left third / right third / lower third / diagonal | free; use at least 3 different anchors in a set of 6 |
| Props | none / one use-prop / ingredient or material cue / scale anchor / human hand | free; never more than 3 prop kinds in one frame |
| Background depth | seamless / shallow blur / readable room | free |
| Copy space | none / top / left / right | free per shot, identical across an ad pack |
| Human presence | none / hand / cropped figure | free; faces only on request |

## 3. Pick lists by category

Starting points that fit how the product is really used. One surface + one light + at most two props.

| Category | Surfaces | Light | Props that belong |
|---|---|---|---|
| Skincare, cosmetics | bathroom tile, pale stone, folded cotton towel, mirror shelf | soft window, bright overcast | the product's own texture swatch, a washcloth, a ceramic dish |
| Food, oil, sauces, coffee, tea | oak table, worn cutting board, linen, enamel tray | window side light, breakfast sun | the real ingredients, bread, a spoon, a cup in use |
| Drinks | bar top, picnic cloth, fridge door shelf, kitchen counter | hard sun with crisp shadow, cool daylight | a filled glass of the same drink, ice, the opener |
| Supplements, wellness | kitchen counter, desk, gym bag edge | clean daylight | a water glass, a weekly routine cue (keys, notebook) |
| Fashion accessories, bags, shoes | concrete step, cafe chair, hallway bench, car seat | street daylight, doorway light | a coat sleeve, a phone, a train ticket |
| Jewellery, watches | linen, stone tray, skin (wrist, collarbone) | small soft source, controlled reflections | a shirt cuff, a ring dish |
| Electronics, gadgets | desk, sofa arm, backpack pocket, workbench | monitor-side daylight, evening lamp | the cable it ships with, a laptop edge, headphones |
| Home, decor, candles | shelf, side table, window sill, bedside | late afternoon window, lamp glow in the background only | a book spine-away, a plant the room would have, matches |
| Toys, kids | play mat, wooden floor, low shelf | bright even daylight | a child's hand (no face), blocks, a storage basket |
| Tools, outdoor | workbench, tailgate, garden table, trail rock | open shade, overcast | gloves, the material it works on |

Seasonal cues, two at most, at the frame's edges: winter (pine sprig, wool, low warm window light), spring (blossom branch, open window), summer (hard sun, lemon, woven straw), autumn (dry leaves, brown paper, low sun), gifting (plain kraft wrap, twine, a blank tag). Occasion-specific religious or national symbols only when the user asks.

## 4. Ban list: overused AI looks

These are the models' defaults, which is why every generated product image looks the same. Do not use them unless the user asks for one by name or the brand already owns that look. Reach for the right column instead.

| Banned by default | Instead |
|---|---|
| Product on a pastel podium or cylinder with floating spheres and arches | a real surface from section 3 |
| Levitating product, exploding splash, ingredients frozen in mid-air | the ingredient lying next to it, one drip at most |
| Neon purple, teal or magenta rim glow; "cyber" gradients | neutral key light; colour comes from props and surface |
| Marble slab + eucalyptus sprig + gold accents | the category's own surface; one plant only if the room would have it |
| Rose petals, scattered flowers, silk folds | a towel, a linen napkin, nothing |
| Mirror-black wet surface with perfect reflection | matte stone or wood; reflections are where labels duplicate |
| Water droplets on things that are never cold or wet | condensation only on chilled drinks |
| Fairy-light bokeh, lens flares, light rays, smoke or mist without a source | a window, a lamp, a doorway: a nameable light source |
| Golden hour on everything | the light of the place and time the product is used |
| Lab glassware, molecules, DNA helix for "science" | omit; efficacy claims are copy and need proof |
| Random succulents, monstera leaves, pampas grass | a prop from the use case |
| Perfect manicured hand in a pinch grip presenting to camera | relaxed hand, open palm or natural carry |
| Extra mini products, boxes and bags with invented branding | unbranded props from a different object family |

Also banned across a session: giving the next product the same look as the previous one by habit. Unless it is the same brand, a new shoot differs from the last one in at least two of palette, light, surface family.

## 5. Building N coordinated variants

1. **Fix the system**: `{LOCK}`, `{LOOK}`, approved hero as the last reference, same copy-space side.
2. **Give every variant a role**, so the set covers different questions a buyer has:

   | Role | Shows | Typical axes moved |
   |---|---|---|
   | hook | the product big and unmistakable | framing 70%, low or front angle, no props |
   | context | where and when it is used | readable room, framing 15 to 40% |
   | detail | material, closure, texture | mode 7 crop, or framing 70% on the label |
   | scale | size in the hand or next to an anchor | human hand or anchor prop |
   | ingredients or kit | what it is made of, what comes with it | flat lay, ingredient props |
   | occasion | season, gift, routine moment | two seasonal cues, time of day |
   | offer-ready | calm frame with generous copy space | seamless or plain wall, left or right third |

   N = 3 → hook, context, detail. N = 5 → add scale and offer-ready. N = 6 or more → add ingredients or kit, then occasion; after that, second executions of context with a new surface member.
3. **Move one or two free axes per variant**, never a locked one. Write the matrix into `plan.md` before prompting:

   ```text
   id   role     angle        framing  anchor       props            depth       copy
   hero context  3/4 right    40%      right third  bread, bowl      soft blur   left
   s01  hook     front        70%      centred      none             seamless    none
   s02  detail   front        70%      centred      none (crop)      -           none
   s03  scale    3/4 right    40%      lower third  hand pouring     soft blur   left
   s04  kit      top-down*    40%      diagonal     olives, lemon    flat        top
   s05  offer    front        40%      right third  none             plain wall  left
   * bottle lying label-up: inside the reference coverage
   ```
4. **Testing sets** (the user will A/B the ads): change exactly one axis between the variants being compared and keep the model the same, or the result says nothing about why one won.
5. **Diversity check before the batch**: at least 3 composition anchors and 2 framings in a set of 6; no two variants with the same role and the same anchor; nothing from the ban list.
6. **`num_images` is not variation.** It re-rolls the same idea (useful for the hero: two candidates of one look). Different ideas are different jobs with different prompts in one batch.
7. After the batch: per-image rubric, then the coherence pass in `fidelity-qa.md`.
