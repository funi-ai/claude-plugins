# Text accuracy

On a card the words are a deliverable, and a shopper forgives a plain layout sooner than `Soguk` for `Soğuk`. Image models render short, large, plainly written strings well and everything else badly. This file is about staying in the first group, proving it, and what to do when a string will not render. `cardkit.py` abbreviates `python3 "${CLAUDE_SKILL_DIR}/scripts/cardkit.py"` as written in SKILL.md.

## 1. Writing strings a model can render

1. **Short.** Two to four words per string, inside the budget of the card type (`card-types.md` section 2). Risk grows with every character, not every word: `paslanmaz çelik gövde` is three words and 21 letters of risk.
2. **Few.** Every extra string makes all the others smaller. Five callouts are the ceiling, three are better.
3. **Final form.** You write the exact casing, punctuation and number format. The model copies; it never uppercases, translates, abbreviates or "improves". `cardkit.py text` returns a locale-correct `upper` when the design needs caps.
4. **Sentence case by default.** All caps is where dotted and dotless I fail most and where diacritics collide with the line above. Caps only for headlines of one or two words.
5. **Plain characters.** Straight quotes and apostrophes, a plain hyphen, `x` instead of a multiplication sign, no emoji or symbols (ticks, stars and arrows are icons drawn by the layout, not typed characters). `cardkit.py text` flags the rest.
6. **No line-break surprises.** A string longer than about 18 characters will be wrapped by the model. Decide the break yourself by making it two strings, or accept any wrap: the read-back joins up to three consecutive lines.
7. **Numbers with their unit, exactly as the user wrote them:** `6,5 cm`, `500 ml`, `%100 pamuk`. One number per string. Never a number that is not in `facts.json` (the numbers gate of `cardkit.py text --facts` fails it).
8. **No claims by typography.** "Best", "No. 1", "garantili", "onaylı", a percentage without a source: `claim_word` warnings mean keep it only when the user stated it and can prove it.
9. **Nothing to fill.** A layout with an empty slot gets filled with invented text. Give every slot a string or remove the slot, and always end with the no-other-text clause.

## 2. Turkish specifics

| Risk | What goes wrong | What to do |
|---|---|---|
| ı and i, I and İ | the dot appears or disappears, or a capital turns small: `SIKIM` becomes `SİKİM`; `İÇİNDEKİLER` came back as `İÇİNDEKiLER` at `quality: "medium"` (2026-09-21) | never let the model change case; caps come from `cardkit.py text` (`upper`); name the letter in the prompt on a re-roll ("the fourth letter is a dotless ı") |
| ş ç ğ ü ö | the mark is dropped (`ş` to `s`, `ğ` to `g`) or drawn as a stray accent | sturdy medium-weight sans, labels at least 3 percent of the card height, spelled form on the re-roll |
| Circumflex (â î û) in words like `kâğıt` | usually dropped | keep it only when the user wrote it; read it back like any other mark |
| Decimal comma, percent sign first | `0,5 L` comes back as `0.5 L`, `%100` as `100%` | quote the string exactly and add "keep the comma" or "the percent sign comes first"; the read-back classifies it as `spacing_or_punct` |
| Suffix apostrophes (`Ayvalık'tan`) | apostrophe dropped or curled | curly and straight count as equal in the read-back; a missing one is a fail |
| Long agglutinated words | letters swapped in the middle of `geçirmeyen`, `kullanılabilir` | prefer the shorter wording the user also accepts; never invent a synonym for a fact without telling them |

Measured on 2026-09-21 (`platform.md` section 10): on a 2000x2000 text card at `quality: "high"`, Flare and Sunburst drew every Turkish letter right down to about 1.5 percent cap height, all-caps lines included; the model would not draw smaller when asked for 1 percent. The one miss was at `medium`. So size is not what breaks Turkish at `high`: the 3 percent floor is for legibility on a phone, and cards with text never run below `high`.

The same method covers German (ä ö ü ß), French, Spanish and Polish accents. Scripts this skill has no evidence for on these models (Arabic and Hebrew right-to-left shaping, Thai, Devanagari, long CJK strings): probe with one cheap card first, tell the user it is a probe, and have a native reader confirm before anything is delivered.

## 3. The TEXT block

```text
Render exactly these strings, each once, spelled exactly as written, in Turkish; keep every diacritic and the exact
capitalisation: headline "Neden Zeytin Dalı?"; row 1 "Soğuk sıkım"; row 2 "Erken hasat"; row 3 "Asitlik 0,3";
row 4 "Işık geçirmeyen cam şişe".
```

- First attempt: quoted strings only. Spelled forms on the first attempt make prompts long and can leak hyphens into the image.
- Re-roll after a letter failure: add the `spelled` value from `cardkit.py text` for the failing string only, and name the letter: `row 1 "Soğuk sıkım" (spelled S-o-ğ-u-k  s-ı-k-ı-m; the third letter is g with a breve, the two vowels of the second word are dotless ı)`.
- The CLOSE clause always follows: no other text anywhere, the product's own label unchanged.

## 4. Read-back procedure (every card, before anyone sees it)

1. **Tiles.** `cardkit.py tiles genmedia-output/<slug>/<file>.png` cuts overlapping zoom tiles (PNG needs no tool; the JSON lists the tile paths). A 2000 px card shown whole is scaled down by an image viewer; the tiles show small type at full size.
2. **Transcribe first.** Read every tile. With the Write tool, write `.genmedia/projects/<slug>/seen-<card id>.txt`: every piece of text visible anywhere on the card, one string per line, exactly as drawn, letter by letter for every word that carries a special letter or a digit. Include text on the product's label and any small print. Do this **before** you look at `cards.json` again: a reader who knows the expected string sees it even when the image says something else. If a letter is ambiguous at tile size, write what is most literally there and treat the string as failed.
   ```text
   # c02-benefits_0.png
   Neden Zeytin Dalı?
   Soğuk sıkım
   Erken hasat
   Asitlik 0,3
   Işık geçirmeyen
   cam şişe
   ZEYTİN DALI
   ```
   Lines starting with `# ` are comments. A string wrapped over two or three lines may be written as it appears; the comparison joins neighbours.
3. **Compare.** `cardkit.py readback --plan .genmedia/projects/<slug>/cards.json --card <id> --seen-file <seen file>`. It normalises Unicode composition, whitespace and quote style, nothing else. Exit 0 and `verdict: "pass"` only when every expected string was found exactly and nothing unexpected is on the card.
4. **Read the result.** Per expected string a `status`: `match`, or a failure class with the first differing character and its Unicode name. `extra` lists stray text; `label_suspect` means the product's own label came out differently from `label_strings` (a fidelity failure); `ignored` lists label text and, on how-to cards, bare step numerals.
5. **A renderer that formats its own labels** (`bria/product-dimensions`): add `--numbers-only`. It passes when the numbers on the card are exactly the numbers requested; then check units, title and the measured extents by eye against `facts.json`.
6. **Record** the verdict in the `## Log` of `plan.md` (card id, attempt, failure class, what changed).

Never edit `cards.json` to match what the image says, never transcribe from the prompt, and never skip the read-back for a card that "obviously looks right".

## 5. Failure class → repair

Budget: 2 re-rolls per card, a new job id each time (`c05-materials-r2`, `-r3`), same batch label, and the prompt changes as the class says.

| Class | Typical sight | Change for the next attempt |
|---|---|---|
| `diacritic` | `Soguk`, `Isik`, `IÇINDEKILER` | spelled form for that string, name the letter and its mark, one string fewer on the card; labels one step larger (3.5 percent) only for legibility, since size was not the cause at `high` (2026-09-21) |
| `case` | `SOĞUK SIKIM` for `Soğuk sıkım` | add "exact capitalisation, do not change case" next to the string; check the SET SYSTEM paragraph does not ask for caps |
| `digit` | `0,8` for `0,3` | the number alone in its own string, larger, "the digits are 0 comma 3"; on dimension cards consider the Bria route |
| `spacing_or_punct` | `0.3`, `500ml`, a hyphen added at a wrap | quote it on its own TEXT line, forbid line breaks inside it, say which separator it uses |
| `misspelt` | swapped or doubled letters in a long word | shorten or split the string, fewer strings, larger type |
| `missing` | the string is not on the card | check it is in the TEXT block; the layout has too many slots or too little room |
| `extra` | a pill, a seal, a slogan, lorem-ipsum-like filler | name it: `do not write "<seen>"`; repeat the no-other-text clause; remove empty slots from the layout |
| `label_suspect` | the pack's own text changed | label close-up as image 2, product larger, "do not restyle the label" |

Attempt ladder: attempt 2 applies the table. Attempt 3 applies the table again **and** simplifies the card (drop the weakest string, with the user's wording untouched), or uses the narrow repair below when only one string is wrong and the layout is good. After attempt 3: section 7.

## 6. Narrow text repair (an edit of the failed card)

When the layout is right and one string is wrong, edit instead of re-rolling the composition. `openai/gpt-image-2.5/sunburst/edit`, the failed card as image 1, the product reference as image 2, same `image_size`, `quality: "high"`:

```text
image 1 is a finished product card; image 2 is the real product for reference. Change only one thing: the label that
currently reads "Soguk sıkım" must read "Soğuk sıkım" (spelled S-o-ğ-u-k  s-ı-k-ı-m; the third letter is g with a
breve). Same font, size, colour and position. Keep every other word, the layout, the product and the colours exactly
as they are. No other text anywhere.
```

The family has no `seed` and regenerates the whole image, so every string of the result is read back again, not just the repaired one. A repair counts as one of the two re-rolls.

## 7. The text-free route

After three failed attempts, or from the start for a dense table the budget cannot hold, deliver the card without text and say so plainly. Same endpoint, same references, same SET SYSTEM; the TEXT block is replaced:

```text
This card carries no text at all. Where the headline and the <n> labels would sit, draw empty flat panels in the
background colour, one for the headline top left and one next to each icon, each large enough for a line of text,
with clean edges. Icons, leader lines and the product as described. No letters, numbers, placeholder words or
scribbles anywhere except the product's own label, unchanged.
```

Read it back as usual against an empty expectation: add an entry for the plate job to `cards.json` (`{"id": "c06-howto-plate", "type": "howto", "strings": []}`), transcribe the tiles (an empty seen file with only a `# ` comment line is valid), run `readback`. Any lettering outside the label is `extra` and fails. Then write `genmedia-output/<slug>/listing/copy.md` with the Write tool:

```text
# Copy for 06-howto.png (set the text in a design tool: Canva, Figma, Photoshop, Affinity)
Font direction: sturdy geometric sans, bold headline, medium labels, colour #1E1E1E on #F6F1E7
Headline (top left panel): Nasıl kullanılır?
Panel 1: Serin yerde sakla
Panel 2: Çiğ tüket
Panel 3: Kapağı sıkı kapat
```

Tell the user in the delivery, in one sentence: which card is text-free, which string failed and how many times, and that the wording is in `copy.md` for them or their designer to set. Do not overlay the text yourself with a local tool: no font, shaping or rendering stack is assumed on this machine, and a silently different typeface breaks the set.
