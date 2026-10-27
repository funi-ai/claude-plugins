# Logo: prompts for the vector model, SVG checks, production set

Endpoint fields below were read from the live OpenAPI schemas on **2026-09-20** (all IDs active that day). They are a dated cache: repeat the Discovery guardrail in SKILL.md before spending. `gm.py`, `pipeline.py` and `brandkit.py` abbreviate the calls shown in SKILL.md; run them from the project root.

## 1. What the vector endpoint takes

`fal-ai/recraft/v4.1/text-to-vector` (and `fal-ai/recraft/v4.1/pro/text-to-vector`, same fields, about four times the price):

| Field | Verified | Use here |
|---|---|---|
| `prompt` | string, 1 to 10000 chars, required | one idea per job, built as in section 2 |
| `image_size` | `square_hd` (default), `square`, `portrait_4_3`, `portrait_16_9`, `landscape_4_3`, `landscape_16_9`, or `{width,height}` | `square_hd` for symbols, stacked lockups and emblems; `landscape_4_3` for horizontal lockups |
| `colors` | array of `{r,g,b}` integers 0 to 255; "preferable colors" | approved palette: primary first, then at most two more |
| `background_color` | one `{r,g,b}` object | the palette's background role, so the plate is predictable and removable |
| `enable_safety_checker` | boolean, default true | leave it |

Output: `.result.images[0].url`, content type `image/svg+xml`. There is **no** `num_images`, `seed`, `style` or negative-prompt field: a candidate is one job, and "again" is a new job with a changed prompt. Output size varies a lot (fal's own example is about 1.7 MB); the script accepts up to 8 MB.

`colors` are preferences. Expect near-misses such as `#1e3c2a` for `#1f3d2b`: that is why `svg-check --palette` exists and why exact recolouring happens after approval, never during review.

## 2. Prompt construction

One prompt per candidate, English, written to `prompts/logo-A-r1.txt` (the prompt is hashed: an unchanged re-roll is refused, at `plan` time and again at `add-candidate`). Fixed clause order:

```text
<mark type> logo for "<Brand Name>", <what the company is, 3 to 6 words>.
Idea: <the single idea in one plain sentence>.
Form: <shape logic: geometry, stroke, negative space, number of shapes>.
Composition: <symbol left of wordmark | symbol above wordmark | wordmark only | enclosed emblem>, centred, generous margin.
Lettering: the text reads exactly "<Brand Name>" <casing note>, <type traits>, letters as clean outlines. No other text.
Colour: flat fills using the supplied colours only, primary for the main shapes, plain flat background.
Style: flat vector, few simple shapes, clean closed paths, minimal anchor points, no gradients, no shadows, no outlines around the whole mark, no 3D, no texture, no mockup, no photo.
Avoid: <the snapshot's avoid list>.
```

Rules:

- **Exact name in straight quotes**, once, in the casing you want. Never ask the model to uppercase Turkish: write `"TİLKİ KAHVE"` or `"Tilki Kahve"` yourself. For names with İ ı ş ğ ü ö ç add: `Spelling, letter by letter: T-i-l-k-i K-a-h-v-e`.
- `<type traits>` in the Lettering clause: the approved display face's `traits` from Review 1 (`typography.md` section 2), unless the idea is custom lettering.
- Symbol-only candidates end the Lettering clause with `No text, no letters, no numbers.` and register with `--no-text`.
- **No hex codes in the prompt.** Colour goes through `colors`. In prose use roles ("primary", "accent").
- No camera or render words (lens, lighting, depth of field, realistic, cinematic, glossy): they pull a vector model toward illustration.
- No brand, designer or artist names. "Like X" becomes formal qualities.
- At most three colours in a mark unless the user asked for more; never pad to three.
- One idea per prompt. Two metaphors in one mark read as neither.

`logo-text.txt` holds what every lettered candidate must show (normally one line: the name). `logo-A.json` holds `mark_type` and `idea` (`design-brain.md` section 4).

## 3. The logo round as one batch

Prompts stay in plain text files; the plan is built by the script, so nobody escapes quotes or newlines by hand. `.genmedia/projects/<slug>/brandkit/logo-r1.spec.json`, written with the Write tool (`prompt_file` is relative to the project root; `input` carries everything except the prompt):

```json
{"label": "<slug>", "max_parallel": 3, "jobs": [
  {"id": "logo-A-r1", "endpoint_id": "fal-ai/recraft/v4.1/text-to-vector", "est_cost_usd": 0.08,
   "prompt_file": ".genmedia/projects/<slug>/brandkit/prompts/logo-A-r1.txt",
   "input": {"image_size": "square_hd",
             "colors": [{"r": 31, "g": 61, "b": 43}, {"r": 232, "g": 163, "b": 61}],
             "background_color": {"r": 246, "g": 241, "b": 231}}},
  {"id": "logo-B-r1", "endpoint_id": "fal-ai/recraft/v4.1/text-to-vector", "est_cost_usd": 0.08,
   "prompt_file": ".genmedia/projects/<slug>/brandkit/prompts/logo-B-r1.txt",
   "input": {"image_size": "landscape_4_3",
             "colors": [{"r": 31, "g": 61, "b": 43}, {"r": 232, "g": 163, "b": 61}],
             "background_color": {"r": 246, "g": 241, "b": 231}}},
  {"id": "logo-C-r1", "endpoint_id": "fal-ai/recraft/v4.1/text-to-vector", "est_cost_usd": 0.08,
   "prompt_file": ".genmedia/projects/<slug>/brandkit/prompts/logo-C-r1.txt",
   "input": {"image_size": "square_hd",
             "colors": [{"r": 31, "g": 61, "b": 43}],
             "background_color": {"r": 246, "g": 241, "b": 231}}}
]}
```

```text
brandkit.py plan --brand <slug> --spec .genmedia/projects/<slug>/brandkit/logo-r1.spec.json --out .genmedia/projects/<slug>/brandkit/logo-r1.json
gm.py batch --plan .genmedia/projects/<slug>/brandkit/logo-r1.json
```

- `plan` answers `est_cost_usd`, `warnings` (hex codes in a vector prompt) and refuses before any spend: `round_mismatch` (the id says r1 while the slot is in r2), `duplicate_prompt`, `prompt_unchanged` (this slot already tried that exact prompt), `placeholder_left` (`<Brand Name>`, `{{…}}`), `job_id_reused` (the run ledger knows this id with another prompt: `gm.py` would resume the old job and submit nothing), `upstream_missing` (palette not approved). It also saves each final prompt under `prompts/resolved/<job id>.txt`.
- Job ids: `logo-<letter>-r<round>`. A retry of one letter inside a round (after a `text_mismatch`) is `logo-A-r1-t2`, then `-t3`; a new round is `logo-A-r2`.
- Cost: `unit: "images"` → 3 x `unit_price` (about $0.24 on 2026-09-20). Under the default announce threshold: run, and state it in the review line.
- The three jobs are the first calls to this endpoint: they are their own canary. Bash timeout 600000 ms. `status: "pending"` → the same `gm.py batch --plan` again.
- Files land as `genmedia-output/<slug>/logo-A-r1_0.svg`. An output with `path: null` (the CLI did not download it) → `pipeline.py fetch --label <slug> --step logo-A-r1 --url <outputs[].url> --out genmedia-output/<slug>/logo-A-r1_0.svg`.
- A job that failed alone is fixed and rerun with `--retry-failed`; the others stay valid.
- Register with `--plan-file …/logo-r1.json --job logo-A-r1`: the ledger then hashes exactly the prompt that was paid for.

## 4. Check, look, register

Per file:

```text
brandkit.py svg-check genmedia-output/<slug>/logo-A-r1_0.svg --palette .genmedia/projects/<slug>/brandkit/palette-A.json
```

| Field | Read it as |
|---|---|
| `unsafe` not empty (`kind: "svg_unsafe"`) | script, event handler, external link or embedded raster: not a clean vector. Never show it; re-roll. |
| `paths` over ~400, `bytes` in the megabytes | an illustration, not a logo: simplify the prompt (fewer shapes, no texture). |
| `text_elements` > 0 | live `<text>`: renders in whatever font the viewer has. Ask for outlined letters in the re-roll. |
| `colors`, `nearest_palette`, `off_palette` | what came back and the closest approved hex per colour: the map for `svg-recolor` later. |
| `full_canvas_background`, `background_color` | the plate behind the mark; boards hide it on coloured grounds, variants clear it. |
| `geometry_sha256` | fingerprint of shapes only; recolouring keeps it, redrawing changes it. |

**Look before you register.** The board shows registered candidates only, and a lettered candidate cannot be registered without its read-back, so look at each returned file first:

```text
brandkit.py png genmedia-output/<slug>/logo-A-r1_0.svg --out genmedia-output/<slug>/look/logo-A-r1.png --size 1024 --background "#ffffff"
brandkit.py text-check --expected-file .genmedia/projects/<slug>/brandkit/logo-text.txt --read-file .genmedia/projects/<slug>/brandkit/logo-A-read.txt
```

Read the PNG. For every lettered candidate write what you actually see, one string per line, into `logo-A-read.txt`; `text-check` is the dry run. Then register with `--expect-text-file` and `--read-text-file`, build `board --slot logo --png` and Read it for the small sizes. A mismatch at `add-candidate` is recorded as a failed attempt; correcting the read file afterwards does not rehabilitate that output (`prompt_unchanged`), so read carefully the first time. The script compares after Unicode normalisation: `ı` for `i`, a missing letter, or extra invented text (`EST. 1987`) are all `text_mismatch`: the output is a failed attempt, it never becomes a candidate, and the same letter may be retried twice with a changed prompt (spelled letter by letter, shorter, wordmark larger). Also judge what the script cannot: is the idea readable, does it survive at 24 px, does it resemble a famous mark (drop it if so).

No converter (`tools.png` is `null`): you cannot see the marks. Generate symbol-only candidates (nothing to misspell), register them with `--no-text`, and say in the review that you checked structure and colours but could not look; the user's eyes are the check. With `qlmanage` only, export each candidate with `brandkit.py png` and Read those files instead of the board.

A new round (the user rejects all, or asks for changes):

```text
brandkit.py new-round --brand <slug> --slot logo --change "B kept; A rounder ears; C replaced by an emblem idea"
brandkit.py new-round --brand <slug> --slot logo --change "badge variant" --user-asked "bir de rozet şeklinde görelim"
```

Two rounds without `--user-asked` are the budget. Job ids become `logo-A-r2`. A candidate carried over unchanged is registered again with its old file (the script recognises the identical file and does not call it an unchanged re-roll).

## 5. Production set, after approval

Nothing here calls a model. `svg-check` gave you the map from returned colours to approved hex.

```text
brandkit.py svg-recolor genmedia-output/<slug>/logo-B-r1_0.svg --out genmedia-output/<slug>/logo/logo-primary.svg --map "#1e3c2a=#1f3d2b" --map "#e9a43c=#e8a33d" --map "#f5f0e6=#f6f1e7"
brandkit.py svg-variants genmedia-output/<slug>/logo/logo-primary.svg --out-dir genmedia-output/<slug>/logo --ink "#14201a" --paper "#f6f1e7"
brandkit.py png genmedia-output/<slug>/logo/logo-primary-nobg.svg --out genmedia-output/<slug>/logo/logo-primary-1024.png --size 1024
brandkit.py add-asset --brand <slug> --slot logo --role primary --file genmedia-output/<slug>/logo/logo-primary.svg
brandkit.py add-asset --brand <slug> --slot logo --role nobg --file genmedia-output/<slug>/logo/logo-primary-nobg.svg
brandkit.py add-asset --brand <slug> --slot logo --role mono --file genmedia-output/<slug>/logo/logo-primary-mono.svg
brandkit.py add-asset --brand <slug> --slot logo --role reversed --file genmedia-output/<slug>/logo/logo-primary-reversed.svg
```

- `svg-recolor` substitutes exact colours only (attributes, `style` attributes, `<style>` text), reports `not_found` and `left_unmapped`, and refuses to write if geometry changed. `--transparent-background` also clears the plate.
- `svg-variants` writes `-mono.svg` (every paint → ink), `-reversed.svg` (every paint → paper, for dark grounds) and, when a plate exists, `-nobg.svg`. Gradients flatten. **Shapes that touch merge** when all colours collapse (an amber dot on a green triangle disappears): look at the mono result; when detail is lost, make the mono by hand-picked substitution instead, for example `svg-recolor --map "<inner colour>=<paper>" --map "<outer colour>=<ink>"`, and register that file as role `mono`.
- `add-asset` roles: `primary`, `mono`, `reversed`, `nobg`, `png-1024` (any `png-<n>`), `icon`. For the four SVG roles the script compares the geometry fingerprint with the approved candidate and refuses a redrawn file (`geometry_changed`); the one allowed difference is the full-canvas background plate, cleared or deleted. `nobg` is the transparent logo of the verified set: the book places it on white and on the brand background.
- PNG needs a converter. `qlmanage` output is a labelled fallback (size and background not guaranteed): fine as a model reference, named as such in a hand-off. No converter → ask the user to export one PNG of `logo-primary-nobg.svg` (any browser or design tool) before the applications stage; the SVG set is still delivered.

App icon, local and exact (platform files for the stores, Android, the web and macOS come from the approved icon afterwards: `app-icons.md`):

```text
brandkit.py icon genmedia-output/<slug>/logo/logo-primary.svg --out genmedia-output/<slug>/logo/app-icon.svg --background "#1f3d2b" --padding 0.2 --radius 0.22
brandkit.py png genmedia-output/<slug>/logo/app-icon.svg --out genmedia-output/<slug>/logo/app-icon-1024.png --size 1024
```

The icon nests the untouched mark on a palette-coloured plate. Use the reversed or mono variant as input when the plate is dark. The command warns when the mark is much wider than tall: a horizontal lockup is unreadable in a square. Then either the symbol alone exists as its own SVG, or you generate a **companion mark**: `recraft/v4/style/text-to-vector` with `prompt` (the symbol idea, "no text"), `image_urls` = the approved logo PNG (1 to 10 PNG, JPG or WEBP), `style_match: "precise"`, the same `colors`. It is a new drawing: it goes through its own review (`app-icon` slot, job id `app-icon-r1`) and is never called "the logo". Like every `app-*` job its prompt carries the `{{BRAND_LOCK}}` line; end the application block with `Symbol only. No text, no letters, no numbers.` and read the result back: words from the lock drawn into the mark are a failed output. Prefer the local `icon` command whenever the approved mark fits a square. A reusable `style_id` for many companions comes from `recraft/v4/create-style` (`image_urls` 1 to 10, `base_style: "vector_illustration"`, `match: "precise"`; about half a cent) and replaces `image_urls` in later calls.

## 6. Existing and raster logos

- Official SVG from the user → `svg-check`, register with `--origin user`, approve in their words, skip generation. Never recolour or "clean" it without being asked.
- Only a PNG or JPG → `fal-ai/recraft/vectorize` (`image_url`; PNG, JPG or WEBP under 5 MB, under 16 MP, sides between 256 and 4096 px; about one cent; output `.result.image.url`). A trace is an approximation: show it next to the original, label it traced, and let the user approve it before anything is built on it.
- Documented fallback when the vector endpoint is not active or failed three times: a flat mark on plain white from `openai/gpt-image-2.5/flare/text-to-image` (`quality: "high"`, `image_size` 1024x1024, same prompt minus the vector-only words), then `fal-ai/recraft/vectorize`. Say that this route ran; the delivery calls the result traced.

## 7. Writing the misuse rules

They go into `lock.json` (`misuse`, at least three) and are specific to this mark, not boilerplate. Derive them from its construction: what breaks it? Typical set: no recolouring outside the palette; no stretching, tilting or rearranging symbol and wordmark; no effects (shadow, glow, outline, gradient); no placement on busy photos without the plate; no re-typing the wordmark in another face; nothing inside the clear space. Clear space and minimum size are stated in units of the mark itself ("the height of the fox ear on every side", "never under 24 px or 10 mm wide"), and the minimum is what you verified on the board's small sizes, not a guess.
