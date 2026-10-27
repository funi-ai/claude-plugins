# Typography: pairings as names, traits for prompts

This stage costs nothing and ships nothing: no font files, no downloads, no licence statements. You propose two or three pairings as family **names** with a rationale; the board shows them with whatever the viewer's machine has; the approved pairing enters the BRAND LOCK as names plus visual **traits**, because image models follow a description of letterforms far better than a font name.

## 1. `type-<A..C>.json`

```json
{
  "name": "Editorial warm",
  "rationale": "A soft serif gives the headlines a human voice; a neutral grotesque keeps menus and labels quiet.",
  "display": {"family": "Fraunces", "weight": "600", "fallback": "serif",
              "traits": "soft high-contrast old-style serif, rounded terminals, slightly condensed",
              "use": "headlines, packaging front, signage"},
  "body":    {"family": "Inter", "weight": "400", "fallback": "sans-serif",
              "traits": "neutral humanist grotesque, open apertures, even rhythm",
              "use": "body text, UI, small print"},
  "mono":    {"family": "IBM Plex Mono", "weight": "400", "fallback": "monospace",
              "traits": "engineered monospace with soft corners", "use": "codes, prices in tables"}
}
```

Enforced by the script: `display.family` and `body.family` (names), `fallback` one of `serif`, `sans-serif`, `monospace`, `cursive`, `system-ui`, and non-empty `traits` for both. `mono` is optional. Two options with the same pair of families are refused (`duplicate_pairing`), also when display and body are swapped.

`traits` is the load-bearing field: classification (old-style, transitional, didone, slab, grotesque, neo-grotesque, geometric, humanist, rounded, mono), contrast (low, high), width, terminals, x-height, one distinctive letter if there is one. Write what you would tell a sign painter who has never seen the font.

## 2. Pairing logic

- **Contrast with kinship.** Pair across classifications (serif display + sans body, or the reverse) and keep one shared quality: similar x-height, similar stroke endings, or the same era. Two similar sans families together look like a mistake.
- **One voice, one workhorse.** The display face carries the personality (it may be the system's single loud element, see `design-brain.md`); the body face must be boring in the good sense and have the weights the brand needs (regular, medium, bold, italics if it writes long text).
- **Lead the logo.** Typography is picked in Review 1, before any logo is generated. The approved display face's `traits` go into the Lettering clause of every lettered logo prompt (`logo.md` section 2), so the wordmark and the headlines speak with one voice. A candidate built on custom lettering says so in its idea; the display face then recedes instead of competing. An official logo the user brought already made the typographic statement: the display face echoes its construction or recedes.
- **Match the tone row** in `design-brain.md` section 3, then check the places from the brief: a sign wants sturdy shapes at distance, an app wants screen-proven text faces, packaging wants a condensed cut for long ingredient lines.
- **Single-family systems are valid.** One family with a wide weight range (display bold + text regular) is often the most coherent answer for a small company. Offer it as one of the options.
- Options differ in voice, not in lookalike swaps: for example A = warm editorial (serif + sans), B = geometric calm (one sans family), C = characterful display + plain text.

## 3. Families you may name

Widely used families that are commonly offered as open-source downloads. The table is a list of names to start from, not a licence statement: you state no licence terms, and the user checks the licence and the character set of the version they download.

| Voice | Display candidates | Text candidates |
|---|---|---|
| warm, editorial | Fraunces, Playfair Display, DM Serif Display, Lora, Cormorant Garamond | Source Serif 4, Literata, Merriweather |
| neutral, modern | Inter, Manrope, Work Sans, DM Sans, Public Sans | Inter, Source Sans 3, IBM Plex Sans, Noto Sans |
| geometric, friendly | Poppins, Outfit, Sora, Nunito, Quicksand | Nunito Sans, Figtree |
| technical | Space Grotesk, IBM Plex Sans, JetBrains Mono, Space Mono | IBM Plex Sans, Roboto Mono for data |
| bold, poster | Archivo, Anton, Bebas Neue, Oswald, Bricolage Grotesque | Archivo, Barlow |
| slab, sturdy | Roboto Slab, Zilla Slab, Bitter | Bitter, Source Serif 4 |

The user names a commercial or custom font they own → use it by name with `--origin user`, write its traits, and say nothing about its licence except that it is theirs to check.

**Turkish and other extended alphabets.** A brand that writes Turkish needs İ ı Ş ş Ğ ğ Ü ü Ö ö Ç ç in every weight it uses; display faces are the usual gap (uppercase-only or Latin-basic poster fonts). The board prints `Iİıi Şş Ğğ Üü Öö Çç` in the display face for exactly this reason: a letter that falls back to another font is visible at once. Tell the user to check the character set of the downloaded version; do not assert coverage yourself.

## 4. Board and review

```text
brandkit.py add-candidate --brand <slug> --slot typography --id type-A --data .genmedia/projects/<slug>/brandkit/type-A.json
brandkit.py board --brand <slug> --slot typography --png
brandkit.py board --brand <slug> --slot typography --webfonts
```

- The default board is self-contained and loads nothing. Each family row says whether the font **rendered in the real face** on the viewer's machine or fell back; a fallback specimen proves nothing about the pairing, and the row says so.
- `--webfonts` adds one stylesheet link to Google Fonts for the named families, so the specimens render for users who do not have them installed. Use it only when the user is fine with the board loading a third-party stylesheet; the board is then no longer self-contained, and a family that is not served there still falls back (its row will say so). Never hand this version off as the archival board.
- Your own look (`--png`) runs in a headless browser with your machine's fonts: if the rows say fallback, you did not see the pairing either. Say that in the review line instead of praising letterforms you did not see.
- Review: part of Review 1 with the strategy snapshot and the palettes, one board (`board --slot palette --slot typography`), one message asking for both picks, one stop. One line per option (voice, where each face works). "You pick" → you may approve with `--note 'delegated: "<their words>"'`.

## 5. Typography in the lock and in prompts

`lock --data` writes lines such as `Headline type: Fraunces 600, soft high-contrast old-style serif, rounded terminals`. In application prompts that block is pasted unchanged; the application block then assigns roles per string ("headline in the headline type, details in the body type"). Image models approximate a named face; judge the result against the **traits**, and never promise the user that the mockup shows the exact font. Final, exact typesetting happens in the user's design tool with the real font files.

The sentence that goes wherever fonts are mentioned in a delivery, the book and the package: **font families are named, not bundled; check the licence of each family before use.**
