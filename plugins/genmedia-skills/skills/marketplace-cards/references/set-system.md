# The two locks: PRODUCT LOCK and SET SYSTEM

A card set is coherent because two paragraphs never change: the **lock string** (what the product is) and the **SET SYSTEM** (how every card looks). Both are written once into `.genmedia/projects/<slug>/plan.md` and pasted verbatim into every prompt. Only the layout and the TEXT block differ per card (`card-types.md`).

## 1. PRODUCT LOCK

Written from the photos, after you Read them. Nothing in it comes from memory of "products like this".

```text
PRODUCT LOCK
Type and form:   500 ml olive oil bottle, square shoulders, short neck
Proportions:     about four times as tall as wide; cap is one eighth of the height
Materials:       dark green glass, matte black aluminium pourer cap, matte cream paper label
Colours:         glass #1F3B2A (approx.), label #F2EAD8, print dark olive
Label, verbatim: line 1 "ZEYTİN DALI" | line 2 "Soğuk Sıkım Natürel Sızma Zeytinyağı" | line 3 "500 ml"
Marks:           olive-branch line drawing above line 1, centred
Count and kit:   one bottle; nothing else in the photo belongs to the product
Never change:    bottle shape, glass colour, cap, label layout and every letter on it
Unseen sides:    back label, base
References:      @product = bottle-front.jpg (primary), @product-label = bottle-label.jpg
```

- Read the label letter by letter and copy it exactly, diacritics and casing included. These lines become `label_strings` in `cards.json`.
- Hex values are estimates by eye; mark them "approx.". They steer the model, they do not measure the product.
- A side the photos do not show is listed as unseen. A card that needs it waits for another photo.
- Someone else's brand on the product (a reseller's stock): ask once that the user may sell and advertise it. The mark stays exactly as photographed.

**Lock string** (one English paragraph, pasted into every generative prompt):

```text
The product is the 500 ml dark green glass olive oil bottle from image 1: square shoulders, short neck, matte black
pourer cap, matte cream paper label on the middle of the body. Keep its shape, proportions, glass colour, cap and
label exactly as in image 1. The label shows an olive-branch line drawing and reads "ZEYTİN DALI", "Soğuk Sıkım
Natürel Sızma Zeytinyağı", "500 ml", centred, dark olive on cream. Do not add, remove, translate or restyle anything
on the label. Exactly one bottle, 26 cm tall.
```

Say "image 1" for GPT Image jobs and "Figure 1" for Seedream jobs; that is the only allowed edit. Give the height only when `facts.json` has it.

## 2. SET SYSTEM: five decisions, made once

Decide each axis, write the result as one paragraph, never paraphrase it afterwards.

| Axis | Default and reason | Alternatives (when) |
|---|---|---|
| Palette | Four colours: background = a light neutral tinted with the product's lightest colour; primary = the product's or brand's darkest colour (headlines, icons, lines); one accent from the product; text = near-black. From the product, so the set looks like it belongs to it. | The user gave brand colours → use them as primary and accent. Dark premium product → dark background, light text. |
| Type | One sans-serif family described in words: bold for headlines, medium for labels, sentence case. Sturdy letterforms keep diacritics (the breve of ğ, the dot of İ) visible at phone size. | A serif headline for heritage or gourmet goods, still a sans for labels. Never script, condensed, thin or outlined type. |
| Icons | Single-weight line icons in the primary colour, rounded ends, no fill, all the same size. One style reads as one brand. | Solid one-colour glyphs for tools and rugged goods. Never emoji, 3D, gradients or mixed styles. |
| Grid | 7 percent outer margin; headline top left; product zone and text zone fixed (product right, text left); one text column. The eye learns the layout on card 2 and reads the rest faster. | Product left when its label faces right. Portrait masters: product bottom, text top. |
| Callouts | Thin leader line in the primary colour ending in a small dot on the product; label in bold next to the line's outer end; no boxes. | Rounded pill behind the label when the background is busy (in-use cards). |

Size rules that go into the paragraph: headline cap height about 5 percent of the card height, labels at least 3 percent (60 px on a 2000 px card, about 12 px on a phone). Smaller type is hard to read on a phone; at `quality: "high"` the letters themselves held down to about 1.5 percent (2026-09-21).

Check every text and background pair before the anchor is rendered:

```text
cardkit.py contrast "#1E1E1E" "#F6F1E7"     -> ok:true, ratio 14.81
cardkit.py contrast "#D9A441" "#F6F1E7"     -> ok:false, ratio 2.0: an accent, never a text colour
```

`ok` means at least 4.5:1. The accent is for icons and highlights; text on the accent needs its own check.

Category starting points (pick one, then adjust to the product's real colours):

| Category | Palette direction | Type feel | Icons |
|---|---|---|---|
| Food and drink | warm off-white, one deep natural colour from the pack | friendly geometric sans | rounded line icons |
| Beauty and care | soft tinted neutral, low-contrast accent | light-looking but medium weight sans | fine line icons, generous space |
| Electronics and accessories | cool light grey or near-black, one saturated accent | technical grotesque sans | precise line icons, square ends |
| Home and kitchen | warm grey or linen, muted accent | humanist sans | rounded line icons |
| Apparel and bags | paper white or kraft tone, accent from the fabric | editorial sans, optional serif headline | minimal, few icons |
| Kids and toys | light pastel background, two product colours at most | rounded sans | chunky rounded icons |
| Tools and outdoor | concrete grey or dark, safety-colour accent | heavy grotesque sans | solid glyphs |

Ban list (each one makes a set look like a template or breaks a marketplace norm): rainbow gradients, glossy 3D badges, starbursts, laurel seals, ribbons, fake interface chrome, drop-shadowed or outlined text, more than one accent, all-caps paragraphs, script fonts, neon glow, confetti, stock people pointing at the product, mascots the user does not own.

**The paragraph** (template, then the worked example used in `batch-plans.md`):

```text
SET SYSTEM: <canvas and margin>. Palette: background <hex name>, primary <hex name>, accent <hex name> used
sparingly, text <hex name>. Type: <family description>, <casing>, headline cap height about 5 percent of the card
height, labels at least 3 percent, generous letter spacing, never script, condensed or outlined. Icons: <style>.
Grid: <zones>. Callouts: <style>. Flat, clean, no gradients, no badges, no shadows under text.
```

```text
SET SYSTEM: square card with a 7 percent outer margin. Palette: background warm cream #F6F1E7, primary deep olive
#2F4A2F, accent amber #D9A441 used sparingly, text near-black #1E1E1E. Type: one sturdy geometric sans-serif family,
bold headlines and medium labels, sentence case, headline cap height about 5 percent of the card height, labels at
least 3 percent, generous letter spacing, never script, condensed or outlined. Icons: single-weight line icons in
deep olive with rounded ends, no fill, all the same size. Grid: headline top left, one left-aligned text column on
the left 40 percent, product on the right half. Callouts: thin deep-olive leader lines ending in a small dot on the
product, bold label at the outer end, no boxes. Flat, clean, no gradients, no badges, no shadows under text.
```

The user's own logo: only from a file they supply, passed as a reference image and checked like a label. Never redraw a logo from a description, and never add one the user did not ask for.

## 3. The anchor

The first infographic (`c02-benefits`) is where the system is seen for the first time. Two candidates of the same system, on Flare, then a hard stop.

- The user approves → record `Anchor: @c02-benefits[n-1]` and keep the paragraph unchanged. The approved file is the style reference of every later card, always **last** in `image_urls`, with the role line "match its palette, type, icons, grid and callout style, not its words or its layout".
- An approved anchor that also passed the read-back is delivered as card 2 as it is. Its look was approved but a string failed → it still serves as the style reference, and card 2 is rendered again in the stage-3 batch on Sunburst.
- The user rejects the look → change picks, not adjectives, and render a new id (`c02-benefits-v2`):

| Complaint | Change |
|---|---|
| "too busy", "crowded" | one callout fewer, margin 9 percent, icons smaller, drop the accent from the text column |
| "cheap", "like a template" | off-white instead of pure white or saturated background, accent only on one element, lighter line weight, more empty space |
| "not my brand" | ask for the brand colours or a brand file (the user spoke first; this is not a new question round), rebuild the palette from them |
| "hard to read" | darker text, labels 3.5 percent, fewer words per label, no text over the product or a photo |
| "too plain" | a tinted panel behind the text column, the accent on the headline underline, one larger hero icon |

Three rejected looks → stop and ask for one reference listing image the user likes (their own, or a style they describe). Never imitate another brand's trade dress.

## 4. QA rubric per card

Text comes first (`text-accuracy.md`). Then, Read the card next to `c01-main` and the source photo:

| # | Check | Fail means |
|---|---|---|
| F1 | Shape and proportions match the lock | re-roll; say "same silhouette as image 1" and name the part that drifted |
| F2 | Label layout and every legible label letter match `label_strings` | re-roll with the label close-up as image 2 and the product larger; a label too small to read is fine, a legibly wrong one is not |
| F3 | Colours and materials match (glass stays glass, matte stays matte) | re-roll naming the material; check the SET SYSTEM did not tint the product |
| F4 | Count and kit: exactly the items planned | re-roll with "exactly <n>" and "nothing else is in the kit" |
| F5 | Nothing invented: no new buttons, ports, caps, inner parts, accessories, no unseen side | re-roll from an angle the photos cover |
| F6 | Facts: every number, unit and claim on the card is in `facts.json`; leader lines point at the right part | re-roll; a wrong number is never delivered |
| F7 | People: hands natural, no real or famous likeness; disclosed when generated | re-roll or remove the person |
| S1 | Palette, type, icon and callout style match the anchor | re-roll with the anchor as the last reference and the paragraph verbatim |
| S2 | Margins and headline position match the grid | re-roll; restate the grid sentence |
| S3 | Pixel size as planned (`cardkit.py probe <file> --expect WxH`) | fix `image_size` in the plan; re-roll |

Verdict per card: **pass**, **re-roll** (new id, something changes, 2 at most), or **text-free route** (`text-accuracy.md` section 7). After all cards pass, look at the whole set side by side once: a card that passes alone but looks like it came from another set is re-rolled within its budget or reported as the weak one.
