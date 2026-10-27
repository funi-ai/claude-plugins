# Palette: roles, contrast, board

The palette stage costs nothing: no model is called. You propose two or three options, the script normalises them and computes every contrast pair, the board shows them. `brandkit.py` abbreviates the call shown in SKILL.md.

## 1. `palette-<A..C>.json`

```json
{
  "name": "Forest roast",
  "rationale": "Deep green carries craft and calm; amber is the single warm signal.",
  "colors": [
    {"hex": "#1F3D2B", "name": "Pine",  "role": "primary",    "use": "logo, large fields, buttons"},
    {"hex": "#E8A33D", "name": "Amber", "role": "accent",     "use": "one highlight per layout"},
    {"hex": "#F6F1E7", "name": "Oat",   "role": "background", "use": "page and packaging ground"},
    {"hex": "#14201A", "name": "Night", "role": "text",       "use": "body text, reversed grounds"}
  ]
}
```

Rules the script enforces (`palette-check --input <file>` runs the same checks without touching the ledger):

- 3 to 8 colours; `hex` as `#rgb` or `#rrggbb` (stored lowercase); `role` one of `primary`, `secondary`, `accent`, `background`, `surface`, `text`, `neutral`, `support`.
- Exactly one `primary`; at least one `background` and one `text`.
- Every `text` colour on every `background` and `surface` must reach 4.5:1. Below that the palette is refused (`kind: "palette_problems"`): fix it before anyone sees it.
- No duplicate hex; two options with identical colour sets are refused (`duplicate_palette`).
- Notes (not blocking): an accent, primary or secondary under 3:1 on the background ("shapes only, never text or thin lines"); two colours closer than a visible step.

What comes back: per colour `rgb` (the `{r,g,b}` object the vector endpoint wants), `label` (black or white, whichever reads better on the swatch), all `pairs` with ratio and grade, and `text_pairs` (the best pairs at 4.5:1 or more, which later go into the BRAND LOCK).

Contrast is the WCAG 2 relative-luminance ratio: 4.5:1 for body text (AA), 3:1 for large type and UI shapes, 7:1 for AAA. It is computed, never eyeballed. Vision is for harmony; the script is for numbers.

## 2. Building options

1. Start from the snapshot: tone row in `design-brain.md` section 3, the user's `colours_use` and `colours_avoid`, and where the brand lives first (a sign wants contrast at distance; an app wants a calm background and one signal colour).
2. Give each colour a job. A colour without a `use` is a colour to delete. Typical sizes: 4 to 5 colours; more only for a product range or a data-heavy product.
3. Think in proportion, roughly 60 / 30 / 10: ground, primary, accent. The accent is rare on purpose.
4. Make the options differ in **strategy**, not in hue rotation: for example A = expected for the category but refined, B = the tone words taken literally, C = a deliberate break from the category (still inside the user's constraints).
5. Name colours with plain nouns (Pine, Oat). Names appear in the book, in `palette.css` and in the lock.
6. The user gave official colours → one option only, registered with `--origin user`, approved with their words. It never becomes stale when the strategy changes, and you do not "improve" it. If their text colour fails on their background, the script still registers the official palette and reports the pair under `notes` (`official palette: …`): say so with the number and offer a darker text tone as a separate, clearly generated addition. The script needs 3 to 8 colours with one `primary`, one `background` and one `text`: when the official set is smaller (two brand colours), add the missing neutral roles yourself (an off-white, a near-black from the same hue family) and name them as your additions in the review.

Extracting colours from an existing logo: `svg-check <file.svg>` lists the hex values actually used (measured). From a raster logo you can only observe: propose values, label them observed, and let the user confirm.

## 3. Pitfalls

- **Pure black on pure white** everywhere: harsh on screens and anonymous. A near-black and an off-white from the palette's own hue family hold the system together.
- **Accent as text.** Most warm accents fail on light backgrounds. The note says "shapes only": obey it in every later application.
- **Two primaries.** Two equally loud colours make every layout a negotiation. One primary, one accent.
- **Trend gradients.** A gradient is a fifth and sixth colour plus a direction. Use one only when the snapshot asks for it, define it as two named stops, and expect the mono logo variant to flatten it.
- **Colour meaning claims.** Do not tell the user what a colour "means" in their culture or market as fact. Say what it does in this system: contrast, warmth, distance from competitors they named.
- **Colour-blind pairs.** Red and green of similar lightness collapse for many viewers; when both exist, separate them in lightness (the pairs table shows it) and never encode meaning by hue alone.
- **Screen values only.** The palette is sRGB hex. CMYK, Pantone and RAL conversions depend on stock and process; they are set with the print shop. Never invent a Pantone number.

## 4. Review 1

Register the snapshot, the palette options and the type pairings (`typography.md`), build one board, look at it when a browser exists (`board --slot palette --slot typography --png`, then Read the PNG), and send one review message that asks for a palette and a pairing. One line per option about the idea ("A: the refined expected; green for craft, amber as the only warm note"), one line on what you checked ("every text pair passes 4.5:1; amber is for shapes only"). Then stop.

```text
brandkit.py add-candidate --brand <slug> --slot palette --id palette-B --data .genmedia/projects/<slug>/brandkit/palette-B.json
brandkit.py board --brand <slug> --slot palette --slot typography --png
brandkit.py approve --brand <slug> --slot strategy --candidate strategy --note "<their words>"
brandkit.py approve --brand <slug> --slot palette --candidate palette-B --note "<their words>"
```

Approve the strategy first: the palette's approval is refused while the snapshot is open. "You pick" → you may approve the palette with `--note 'delegated: "<their words>"'`; say which one and why in one line.

After approval `status` prints the approved colours with their `rgb` objects. Those feed the logo plan's `colors` (primary first, at most three) and `background_color` (the background role).

## 5. Changing the palette later

A new option is a new candidate (`palette-B` in revision r2). Registering it changes nothing. Approving it returns `invalidated`: normally the generated logo, the lock, every application and the book; typography stays. Follow the invalidation etiquette in `qa-and-iteration.md`: tell, price, ask, then rebuild in stage order. A logo whose shapes still work is usually **kept** (approve it again in the user's words), then recoloured exactly with `svg-recolor`: that costs nothing and the geometry check proves it is the same mark.
