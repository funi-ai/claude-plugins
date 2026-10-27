# Troubleshooting brandkit

Signal → cause → move. `brandkit.py` always prints one JSON object; on failure it carries `ok: false`, `kind`, `message` and usually a `hint`. Exit 2 (`kind: "usage"`) means the call was wrong, exit 1 means the script refused on purpose. Platform error types and billing rules: `platform.md`; helper mechanics (`pending`, `wait`, `--retry-failed`, the ledger): `cli-contract.md`. Every repair is bounded: 3 attempts, something changes each time, then stop and say so.

## 1. Ledger and resume

| Signal | Cause | Move |
|---|---|---|
| `kind: "no_state"` | no ledger for this slug in this directory | right project root? `status` without `--brand` lists the ledgers here. New brand → `init`. The chat claims earlier approvals → ask the user; do not recreate approvals from memory |
| `--brand is required (ledgers here: A, B)` | several brands in one project | pass `--brand <slug>`; the slug is the folded name (`"Tilki Kahve"` → `Tilki-Kahve`, Turkish letters transliterated like `gm.py` labels) |
| `init` answers `existing: true` | the ledger already exists | nothing was overwritten; continue at `next` |
| `kind: "state_conflict"` | two commands wrote at once | run the command again; one writer at a time, never parallel `add-candidate` calls |
| `kind: "state_corrupt"` or `"state_schema"` | the file was edited by hand or by another version | do not repair it by hand; show the user the path and ask whether to restore it from their backup or start a new ledger and re-register the approved files with `--origin user` and their renewed approval |
| `status.next` says a review is open, but the user already answered in an earlier session | the approval was never recorded | ask them to confirm once more, then `approve --note "<their words>"`; never back-fill silently |
| `kind: "unknown_candidate"` | the id is not in this slot (or not in `--revision N`) | the answer lists the open round's ids; to approve a candidate of an older round pass `--revision` |
| `kind: "upstream_missing"` | stage order | finish and approve the named slot first; strategy is approved before palette, even when both were shown in one review |

## 2. `plan` refusals (nothing was spent)

| `kind` | Cause | Move |
|---|---|---|
| `round_mismatch` | the job id says `-r1`, the slot is in round r2 (or the reverse) | rename the jobs; `gm.py` resumes a known id and would hand back the old output |
| `job_id_reused` | the run ledger has this id with another prompt | a retry inside a round is `…-r1-t2`, then `-t3`; a new round is `…-r2` |
| warning `already in the run ledger` | same id, same prompt | intended only when resuming a `pending` batch |
| `placeholder_left` | `<Brand Name>`, `{{…}}` or `{LOOK}` survived in a prompt file | fill or delete it; angle brackets have no place in a prompt |
| `duplicate_prompt` / `prompt_unchanged` | two jobs share a prompt, or the slot already tried this exact prompt | change what the failure named: wording, text size, idea, route |
| `lock_missing_in_prompt` | an `app-*` prompt file lacks the line `{{BRAND_LOCK}}` (or has it twice) | one role line, the token on its own line, the application block |
| `lock_not_approved` | lock draft, open or invalidated | `brand-lock.md` sections 3 and 5; no application is planned before that |
| usage: `give the prompt as prompt_file` | `input.prompt` was written into the spec | move it to a text file; the script builds the plan |

## 3. `add-candidate` and `add-asset` refusals

| `kind` | Cause | Move |
|---|---|---|
| usage: `candidate ids in slot logo are logo-A …` | unstable or free-form ids | `palette-A`, `logo-A`, `type-A` (A to F); applications: the slot name without `app-` |
| usage: `need the text read back` | a generated logo or application without `--expect-text-file` + `--read-text-file` or `--no-text` | read the output, write what you see; `--no-text` only when the image truly shows no letters |
| `text_mismatch` | the words differ (`diff` shows the first differing character with its code point) | failed output, never shown; retry ladder in `applications.md` section 3 or `logo.md` section 4 |
| `prompt_unchanged` right after a `text_mismatch` on the same file | the failed read-back is recorded; a read file corrected afterwards does not rehabilitate that output | dry-run with `text-check` before `add-candidate`; now retry the job with a changed prompt (`-t2`) |
| `kind: "internal"` | unexpected input or a damaged file the script could not interpret | read `message`; do not retry blindly, do not hand-edit the ledger; treat a ledger problem like `state_corrupt` |
| `reroll_limit` | three failed attempts for this candidate in this round, or two rounds already re-rolled | stop; change the route or the idea, or let the user ask for a round (`--user-asked`) |
| `duplicate_candidate` | the id exists in the open round | another attempt at the same letter belongs to a retry job before registering, or to a new round |
| `duplicate_direction`, `duplicate_palette`, `duplicate_pairing` | two options that are the same idea, colours or families | make them differ in substance (`design-brain.md` section 4) |
| `palette_problems` | contrast or role rules failed | fix the values; never show a palette with failing body-text contrast |
| `svg_unsafe` | script, event handler, animation, external link or `url()`, embedded raster, entity declaration or a non-UTF-8 file | do not show, ship or hand-clean it; re-roll. An embedded raster means the model returned a picture wrapped in SVG: simplify the prompt (flat, few shapes) |
| `svg_invalid` | truncated download or an HTML error page saved as `.svg` | `pipeline.py fetch` the URL again; still broken → re-roll |
| `svg_too_large` | over 8 MB | an illustration, not a logo: fewer shapes, no texture |
| `not_approved` (`add-asset`) | assets derive from an approved revision | approve first |
| `geometry_changed` (`add-asset`) | the file is not a recolour of the approved candidate | variants come from `svg-recolor` / `svg-variants` only (clearing or deleting the full-canvas plate is allowed); a redrawn or hand-edited mark is a new candidate for a new review |

## 4. Vector endpoint behaviour

| Symptom | Move |
|---|---|
| `validation` naming `colors` or `background_color` | they are `{r,g,b}` integer objects, not hex strings; copy them from `status.palette[].rgb` |
| Returned colours are near the palette, not on it | expected: `colors` are preferences. Judge the candidate as returned; after approval `svg-recolor` with the map from `svg-check --palette` (`nearest_palette`) |
| The name is misspelt again and again | spell it letter by letter, ask for a larger, simpler wordmark, drop the tagline. After three failures: offer symbol-only candidates now and the lockup set later by the user in the approved display face, and say why |
| Live `<text>` elements (`text_elements` > 0) | the wordmark would render in whatever font the viewer has: re-roll with "letters as clean outlines" |
| Thousands of paths, megabytes | the prompt asked for an illustration: remove texture, shading, scenery, "detailed"; one idea, few shapes |
| A plate fills the canvas | normal; boards hide it on coloured grounds, `svg-variants` clears it, `svg-recolor --transparent-background` removes it from the primary file |
| Hex codes or words from the prompt drawn into the mark | hex in prose is read as text: colours go through `colors`; keep the prompt free of quoted strings other than the name |
| The user wants "the same but slightly different" | there is no `seed` and no image-to-image on this route: a new job is a new drawing. Small formal edits to an approved SVG happen in the user's vector tool; then it comes back as `--origin user` |
| Endpoint not active or failing three times | documented fallback only: flat raster from `openai/gpt-image-2.5/flare/text-to-image`, then `fal-ai/recraft/vectorize`; say that this route ran and label the result traced |

## 5. Edit endpoints (applications)

| Symptom | Cause → move |
|---|---|
| Square output for a poster or banner | `image_size` left at `auto` follows the square logo → always `{width,height}` |
| A cost two or four times the estimate | GPT Image 2.5 `quality` `xhigh`/`max`, several references, or Seedream above the 1536x1536 area (`auto_2K` default) → explicit size and `quality`; re-price |
| `validation` with empty `fields` on a queued job | in order: fields against the OpenAPI schema (size limits, `image_urls` is an array) → the reference URL (expired CDN link: upload again, `pipeline.py add` again, `plan` and `fill` again) → the prompt |
| `content_policy`, or a black image | usually a real brand or a trademarked character named in the brief, or a real person. Rewrite in formal qualities; never resend unchanged |
| The logo is "improved" | see `qa-and-iteration.md` section 6: two-reference repair, flatter composition, the right variant as image 1 |
| Seedream wrote words nobody asked for | add them to `Avoid:`; remove label-like empty areas; if the surface needs words, it is a GPT Image 2.5 job |
| Turkish letters wrong on the second attempt too | Sunburst tier, larger type, fewer strings; after the third failure deliver the surface without that string and say so |
| The reference is an SVG or a data URI | edit endpoints take PNG, JPG or WEBP URLs: `brandkit.py png`, `gm.py upload` |

## 6. Converters, boards, book

| Signal | Move |
|---|---|
| `kind: "tool_missing"` | no browser (and for SVG no `qlmanage`): deliver SVG and HTML, say so. For the applications stage ask the user for one PNG export of `logo-primary-nobg.svg` (any browser or design tool can make it) |
| `kind: "tool_failed"` | the browser started but wrote no complete file within 60 s (sandbox, first-run dialog, a locked profile). Try once more; then treat it as missing. Do not try other tools. `icon-export` and `sting` start several browsers at once: repeat with `--jobs 1` before giving up |
| `icon-export` answers `problems`, or the sheet shows a tiny or cut mark | the input is a lockup, not a symbol, or carries an opaque shape that is not a plate. Codes and fixes: `app-icons.md` section 3. Never fix an icon by generating per-size versions |
| `png` via `qlmanage`: `fallback: true`, `transparent: "unknown"` | a Quick Look thumbnail: fine as a model reference on light surfaces, labelled as fallback in a hand-off; never the "official PNG" |
| Board PNG cut off at the bottom | the height is an estimate: `brandkit.py png <board>.html --out <file>.png --width 1400 --height 5000` |
| Board says a font is "NOT available in this browser" | the specimen shows a fallback face: say that you (or they) did not see the real pairing; `board --webfonts` loads the families from Google Fonts when the user accepts a third-party request; a family not served there still falls back |
| The font rows say "not checked (scripts off)" | the viewer blocks scripts in local files; the samples still render, the check does not |
| PDF pages without coloured plates when the user prints by hand | their print dialog has "background graphics" off; `book --pdf` does not have that problem |
| Book shows "not produced" on the logo page | the roles `primary`, `mono`, `reversed` were never attached: `add-asset`, then `book` again |
| `export-list` exits 1 | read `problems`: invalidated slot, stale asset, missing file. Rebuild, re-approve, or leave out with the user's agreement |

## 7. Cost surprises

- A logo round is three jobs; two re-roll rounds make it nine. Say "each further round costs about the same again" at intake and at every new round.
- The Pro vector tier costs about four times the default; the style endpoint adds a small fee when the style is created inline. Neither is ever chosen silently.
- Retries inside a round are paid jobs too: count `-t2` and `-t3` ids in `gm.py ledger --label <slug> --sum` for the final message.
- Failed jobs: platform errors (5xx) are not billed; a validation failure may be. Resubmitting is always a new billable job, which is why a `pending` batch is resumed with the same command and never rebuilt.
- A change after the applications stage is the expensive one. The invalidation notice must carry the rebuild price before anything is regenerated.

## 8. Requests to decline or reshape

| Request | Answer |
|---|---|
| "Make it like <famous brand>", "Nike tarzı", a designer's or artist's name | never imitated; translate into formal qualities (one solid silhouette, no text, a single cut) and say that you did |
| "Is this logo free to use? Is the name available?" | not something this skill can determine; a generated mark can resemble existing trademarks, and the search is the user's responsibility. Said once at the logo review, again only if asked |
| "Which licence does this font have? Bundle the font files" | families are names; the user checks the licence of the version they download; nothing is bundled |
| "Add our ISO certificate, 'since 1987', a phone number" that the user has not supplied | facts come from the user: ask for the exact string or leave it out |
| A real person's face, signature or another company's logo on an application | likeness needs the user's confirmation of consent; third-party logos only when the user owns them or has the right to use them |
| Print-ready files, dielines, CMYK or Pantone values | outside this skill: mockups are visualisations; the SVG and the palette go to the print shop, which sets the conversions |
