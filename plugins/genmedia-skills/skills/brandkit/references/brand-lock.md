# BRAND LOCK: format, writing rules, examples

The lock is the frozen descriptor of the identity: one text block, composed by `brandkit.py` from the approved strategy, palette, logo and typography plus the rules you write in `lock.json`. After the user approves it, it goes **verbatim** into every later generation prompt, in this skill and in any sibling skill that works for the brand. It is the reason the tenth application still looks like the first. `brandkit.py` abbreviates the call shown in SKILL.md.

Why verbatim and not "in your own words": every paraphrase is a small redesign. A colour that becomes "deep green", a rule that loses its "never", a font described differently on the poster than on the card: that is how a set drifts. The block is long on purpose and identical everywhere; only the application block after it changes.

## 1. What you write: `lock.json`

```json
{
  "logo_construction": "A solid triangular fox ear that doubles as a roof, with one amber dot below its apex; the wordmark sits to the right, baseline aligned with the base of the ear.",
  "clear_space": "The height of the amber dot on every side; nothing enters that zone.",
  "min_size": "Never under 24 px or 10 mm wide; below 48 px use the symbol without the wordmark.",
  "misuse": ["recolouring outside the palette", "stretching, tilting or rearranging symbol and wordmark",
             "shadows, glows, outlines or gradients", "placing it on busy photos without a plain plate"],
  "imagery_style": "Natural window light, matte surfaces (oak, unglazed ceramic, kraft paper), calm compositions with one subject, true colours, no filters.",
  "layout": "Left-aligned, generous margins, one accent element per layout.",
  "do": ["let Pine dominate and use Amber once per layout", "set text only in the listed text colour pairs"],
  "dont": ["coffee beans, steam swirls or cups seen from the side", "gradients, glossy 3D or neon colours",
           "invented claims, dates, awards or contact details"]
}
```

| Field | Required | Write it like this |
|---|---|---|
| `logo_construction` | yes | What the mark is made of, in shapes and relations a stranger could check against the image. No adjectives of praise. |
| `clear_space` | yes | In units of the mark itself ("the height of the dot"), never in pixels. |
| `min_size` | no | What you verified on the logo board's 96, 48 and 24 px previews, plus the rule for smaller uses. |
| `misuse` | yes, 3 or more | Specific to this mark: what breaks it (see `logo.md` section 7). |
| `imagery_style` | yes | Light, surfaces, composition, colour treatment: what a photographer would need. No camera brands, no artist or brand names. |
| `layout` | no | Alignment, margins, density, the one recurring device if there is one. |
| `do` | yes, 1 or more | Positive rules that use palette names and roles. |
| `dont` | yes, 2 or more | The snapshot's `avoid` list, the category clichés, effects. Always include a line against invented facts. |

The script adds the rest from approved data, so do **not** repeat it in your fields: the brand name in exact spelling, the logo preservation sentence with the mark type, every palette colour as `role #HEX "Name"`, up to four text colour pairs that pass 4.5:1 with their ratios, the type lines (`Headline type: <family> <weight>, <traits>`), and the tone words. Values you restate by hand can disagree with the ledger after a change; values the script writes cannot.

Writing rules:

- English, imperative, concrete. The readers are an image model and, in the brandbook, a human. Both need checkable statements.
- Only facts the user gave. The lock carries no founding year, slogan, address, claim or audience statistic unless the user supplied it and wants it on every asset (rare).
- The brand name and any fixed string keep their original language and letters (İ ı ş ğ ü ö ç); everything else is English.
- Separate list entries with list items, not semicolons: the script joins them with semicolons and strips trailing full stops.
- Keep it under about 2500 characters. The block above is about 2000. GPT Image 2.5 accepts prompts up to 32000 characters and the Recraft vector endpoints up to 10000, so length is not the limit; attention is.

## 2. What the script emits

```text
brandkit.py lock --brand <slug> --data .genmedia/projects/<slug>/brandkit/lock.json
```

needs approved strategy, palette, logo and typography (`kind: "upstream_missing"` otherwise), writes `lock-r<n>.txt` next to the ledger, registers the candidate `lock`, and answers the text:

```text
=== BRAND LOCK: Tilki Kahve (lock r1; strategy r1, palette r1, logo r1, typography r1) - FROZEN, APPLY AS WRITTEN ===
Brand name, exact spelling: "Tilki Kahve". Never translate, abbreviate, re-case or re-letter it.
Logo: the supplied logo image is the approved mark (pictorial symbol + wordmark). Reproduce it exactly: same shapes, proportions and colours. Never redraw, restyle, outline, tilt, stretch, add effects to it or add words to it.
Logo construction: A solid triangular fox ear that doubles as a roof, with one amber dot below its apex; the wordmark sits to the right, baseline aligned with the base of the ear.
Clear space: The height of the amber dot on every side; nothing enters that zone.
Minimum size: Never under 24 px or 10 mm wide; below 48 px use the symbol without the wordmark.
Logo misuse, never: recolouring outside the palette; stretching, tilting or rearranging symbol and wordmark; shadows, glows, outlines or gradients; placing it on busy photos without a plain plate.
Palette, exact values: primary #1F3D2B "Pine"; accent #E8A33D "Amber"; background #F6F1E7 "Oat"; text #14201A "Night". Brand elements use only these colours.
Text colour pairs that pass contrast: #F6F1E7 on #14201A (14.9:1); #1F3D2B on #F6F1E7 (10.6:1); #E8A33D on #14201A (7.8:1); #1F3D2B on #E8A33D (5.5:1).
Headline type: Fraunces 600, soft high-contrast old-style serif, rounded terminals, slightly condensed
Body type: Inter 400, neutral humanist grotesque, open apertures, even rhythm
Imagery style: Natural window light, matte surfaces (oak, unglazed ceramic, kraft paper), calm compositions with one subject, true colours, no filters.
Layout: Left-aligned, generous margins, one accent element per layout.
Tone: warm, curious, precise.
Do: let Pine dominate and use Amber once per layout; set text only in the listed text colour pairs.
Don't: coffee beans, steam swirls or cups seen from the side; gradients, glossy 3D or neon colours; invented claims, dates, awards or contact details.
=== END BRAND LOCK ===
```

The header names the revisions the block was built from. That stamp is how you, the book and a later session can tell a current lock from a stale one.

A second shape, for an apply-only job where the user brought an official symbol-only logo, their own colours and a commercial typeface (all registered with `--origin user`): the block is the same; the differences are in the data. The logo line reads `approved mark (user-supplied symbol, no wordmark)` because that is what you wrote as `mark_type` in the logo data file; the type line carries the family the user named and the traits you wrote for it; `logo_construction` describes what you measured and saw (`svg-check`, your own look), not what you would have designed; `misuse` comes from the user's existing guidelines when they have any, otherwise from the mark, and the review says which.

## 3. Review 3

Show the user a plain-language summary in their language, not the block: what the logo is and how much room it needs, the colours with their jobs, the two typefaces, the imagery style in one sentence, the three or four most important never-rules. Offer the file path for the full text. Then stop.

```text
brandkit.py approve --brand <slug> --slot lock --candidate lock --note "<their words>"
brandkit.py lock --brand <slug>
brandkit.py lock --brand <slug> --out genmedia-output/<slug>/BRAND-LOCK.txt
```

- Changes before approval: edit `lock.json`, run `lock --data` again (a new lock revision; the old candidate is superseded), show the summary again.
- `lock` without `--data` prints the approved block. It answers `kind: "lock_not_approved"` while the lock is a draft, an open candidate or invalidated (`invalidated_by` names the cause). That refusal is the stop sign: no application is planned, priced or generated until it is resolved.
- The lock is never auto-approved, even under "you pick": it decides what every paid application looks like.

## 4. Putting it into prompts

Never type or paste the block yourself. A prompt file for any `app-*` job has three parts:

```text
image 1 is the approved logo of "Tilki Kahve". Use it exactly as supplied.
{{BRAND_LOCK}}
APPLICATION: <the application block, see applications.md>
```

`brandkit.py plan` replaces the line `{{BRAND_LOCK}}` with the approved block, refuses a prompt without the token (`lock_missing_in_prompt`) or while the lock is not approved (`lock_not_approved`), and writes the final prompt into the batch plan and into `prompts/resolved/<job id>.txt`. `add-candidate` later checks the paid prompt again: a candidate whose prompt does not contain the current block is refused. Two independent checks, because a lock that is "almost" there is the most expensive failure in the kit: every asset has to be redone.

What may follow the block, and what may not:

| Allowed in the application block | Not allowed |
|---|---|
| Which logo variant is image 1 on this surface ("image 1 is the reversed, single-colour version for dark grounds") | A colour that is not in the palette "just for this poster" |
| Placement, scale and orientation of the logo on this format | "Make the logo bolder / rounder / more modern" |
| Exact strings, each with its type role ("headline in the headline type") | New tone words, a different imagery style |
| Format-specific physics: emboss, embroidery, print on kraft | Anything the `misuse` or `dont` lines forbid |

A per-application override may narrow the lock (one colour only, no accent on this surface), never contradict it. If an application truly needs what the lock forbids, that is a lock change: new `lock.json`, new review, and the invalidation list that comes back from `approve`.

## 5. When the lock goes stale

Approving a new palette, logo, typography or strategy revision invalidates the lock (it was built from the old revision) and, through it, every application and the book. `status` shows `lock: invalidated` with `invalidated_by`. Then:

1. Tell the user what became stale and what rebuilding costs (`qa-and-iteration.md`, invalidation etiquette). The lock itself is free.
2. Revise `lock.json` where the change touches it: a new logo needs new construction, clear-space and misuse lines; a new palette usually needs only `do` and `dont` wording that names colours; new typography needs nothing here (the script rewrites the type lines).
3. `lock --data`, summary, stop, approve. The header now carries the new revision numbers.
4. Only then rebuild the applications the user confirmed, each with a fresh plan (`plan` injects the new block; old prompts cannot be reused by accident, because the old block no longer matches).

## 6. Using the lock outside this skill

The hand-off package contains `BRAND-LOCK.txt`. For an ad, a product shoot, a thumbnail or a listing card made later with a sibling skill: paste the file's content unchanged at the top of that skill's prompt, upload `logo-primary-1024.png` as a reference when the logo must appear, and keep the sibling's own rules for everything else. When the identity changes, the package is exported again and the old file is retired: a lock file without the current revision stamp is history, not a rule.
