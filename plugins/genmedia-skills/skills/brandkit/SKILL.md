---
name: brandkit
description: >-
  Logos and brand identity in approved stages: palette, three logo candidates as real SVG (Recraft V4.1), typography, a frozen BRAND LOCK, applications on the approved logo (GPT Image 2.5 and Seedream edit), HTML brandbook. App icon files (App Store, Play, Android, web, macOS) and a logo sting, rendered locally from the approved SVG.
  Use when: "create a brand identity", "design a logo", "make a brand kit", "app icon and favicon files from my logo", "marka kimliği oluştur", "şirketime logo yap", "kurumsal kimlik ve brandbook hazırla", "logomuzu kartvizite uygula".
  Chain: produces SVG logos, palette hex, icon files and a BRAND LOCK block for `image`, `ads`, `product-photoshoot`, `launch-graphics`.
  NOT for: posters, illustrations (use `image`); product photos (use `product-photoshoot`); ads (use `ads`); listing cards (use `marketplace-cards`); thumbnails (use `youtube-thumbnail`); store screenshots, OG cards (use `launch-graphics`); other productions (use `pipelines`); model choice (use `models`).
argument-hint: "[brand brief or existing logo/site] [deliverables or tier] [--brand <slug>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" *) Bash(command -v genmedia) Bash(genmedia models *) Bash(genmedia schema *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 with a fal key configured by the user, and python3 >= 3.8. A Chromium-family browser is optional (PNG exports, platform icon files, board screenshots, brandbook PDF); macOS qlmanage is a labelled fallback for PNG only; local ffmpeg only for the logo sting.
---

# Brandkit

An identity system built in stages, each one reviewed and approved before the next is paid for: strategy snapshot, palette and typography → three logo candidates (real SVG) → BRAND LOCK → applications → brandbook and hand-off. The value is process and state, not single generations: `scripts/brandkit.py` owns an approval ledger that records every candidate, every approval in the user's words, what each element was built from, and what a change invalidates. Nothing is regenerated silently.

## Step 0 — Preflight

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" tools
```

- Export only (the user brings a finished icon or logo SVG and wants platform icon files or a sting): `brandkit.py tools` is the whole preflight; nothing is generated, so no CLI, key or ledger is needed.
- `blockers` not empty, CLI missing or older than 0.7.0 → `/genmedia-skills:setup`. Key missing → the user runs `genmedia setup` or exports `FAL_KEY` themselves; wait. Never read, print, request or type a key.
- Keep `config.announce_above_usd` and `config.confirm_above_usd` (defaults 0.50 and 2): they are the cost gate.
- `brandkit.py tools` answers `png` (`"browser"`, `"qlmanage"` or `null`), `pdf` (`"browser"` or `null`) and `can` (`icon_export` needs the browser, `sting` the browser plus ffmpeg, `icns` macOS `iconutil`). `null` or `false` is not a blocker: the deliverables become SVG plus HTML, and you say so. Never plan on Pillow, ImageMagick, rsvg-convert or LibreOffice.
- **Resume first, every turn.** Glob `.genmedia/projects/*/brandkit/state.json`. A ledger for this brand exists → `python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" status --brand <slug>` and continue at `next`. The ledger, not the conversation, says what is approved. It is missing but the chat claims approvals → stop and ask. Never hand-edit `state.json`, never paste it into chat or prompts.

## UX rules

1. Reply in the user's language (Turkish in → Turkish out). Model prompts are English; the brand name and every on-image string keep their exact spelling and language, in quotes.
2. No JSON, request IDs, prompts, scores or tool narration in chat. The design reasoning in `references/design-brain.md` stays private; the user sees directions, not rubrics. One status line per batch at most.
3. **Question budget: ONE consolidated intake message** (template under Delivery): brand name in exact spelling, what the company does, audience, three tone words, colours to use or avoid, existing assets, and the tier. Only the name and what the company does block; every other gap gets a stated default (audience "not stated", tone words proposed by you and shown in the strategy snapshot, no colour constraints, no existing assets, no on-image lines so text surfaces carry the logo alone, tier 1). After intake: approvals only, never a second questionnaire; a line the user adds later is welcome, never demanded.
4. **Hard stop after every review**: strategy, palette and typography (one free review), logo, BRAND LOCK, each application batch. The core tier is three reviews after the intake. The brandbook and the package are not reviews: they only arrange what was approved, so they are built right after the last approval and shown in the delivery. Show, then wait. Approval is only what the user says: a finished job, a quiet turn or your own taste is not one. `approve` needs `--note` with the user's own words.
5. Auto-picks only for reversible, free choices. "You pick" → you may approve the strategy snapshot, palette and typography with the note `delegated: "<their words>"`, name the pick and its reason in one line, and continue to the next stage without waiting. Never the logo, the lock or an application: identity-defining or paid-for-downstream choices are human decisions. You may recommend one candidate in a line; choosing is theirs.
6. **Cost: tiers up front, gate per stage batch.** Price the tiers with `gm.py price … --explain` (Workflow step 2) before the first paid call. Each paid batch (logo round, application batch) passes the gate: under announce → run; between → one-line estimate, run; at or above confirm → wait for a yes. A confirmed tier covers the plan shown, not re-rolls beyond it or a bigger plan.
7. Re-rolls: at most 2 per slot, and the prompt must change each time; the script refuses an unchanged prompt and a third re-roll. After a review, another round starts with `brandkit.py new-round --brand <slug> --slot <slot> --change "<what is different>"` before `plan` (job ids then end in `-r2`). A round the user asks for is theirs (`--user-asked "<words>"`), priced and announced like any batch.
8. Never substitute a model silently. The user named one → use it after the live check. A fallback route (raster then vectorize) is said out loud and labelled in the delivery.
9. Stable names: candidates `logo-A`, `logo-B`, `logo-C`, revisions `r1`, `r2`; job ids `logo-A-r1`; applications `app-business-card`. Never rename or reorder between rounds.
10. Safety. Never imitate a named existing brand, designer or artist: translate "like X" into formal qualities (geometric, monoline, high contrast) or decline. Say once, at the first logo review, that a generated mark may resemble existing trademarks and that a trademark search is the user's responsibility. Facts about the company come only from the user: no invented history, claims, certifications, awards, addresses or numbers on any application. Uploads sit on public URLs: say so once before uploading an unreleased logo.

## Discovery guardrail

`references/routing-image.md` (tasks `t2i-vector`, `image-edit`, `image-multiref`, `t2i-typography`, `upscale-image`) is a dated cache, verified 2026-09-19; the Recraft and edit fields in `references/logo.md` and `references/applications.md` were re-read from the live OpenAPI schemas on 2026-09-20. Before the first paid call to an endpoint in a session:

```bash
genmedia models --endpoint_id <id1>,<id2> --status all --limit 50 --json
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
```

- Every ID must be `active`; otherwise take the next tier of that task in `references/routing-image.md`, else `genmedia models "<name>" --no-classify --limit 10 --json`, newest active match, and say which model ran.
- Field names, enums and limits come from the schema, never from memory. They differ per family: the vector endpoints take `colors` as `{r,g,b}` objects and have no `num_images`, `seed` or `style`; the edit endpoints take `image_urls`.
- Never invent IDs or fields. Never `genmedia run` without an endpoint ID. New releases sit under vendor namespaces (`recraft/`, `openai/`, `bytedance/`), not only `fal-ai/`.

## Routing

First match wins. Prices are hints dated 2026-09-20; `gm.py price` decides.

| Stage or need | Route | Why | Price hint |
|---|---|---|---|
| Strategy, palette, typography, BRAND LOCK, boards, brandbook | local: `brandkit.py` | decisions, not pixels; contrast is computed, nothing to generate | USD 0 |
| Logo candidates (three) | `fal-ai/recraft/v4.1/text-to-vector`, one job per candidate | returns real layered SVG; built for logos and icons | ~USD 0.08/image |
| Large-format vector on request | `fal-ai/recraft/v4.1/pro/text-to-vector` | same fields, premium tier | ~USD 0.30/image |
| Companion marks in the approved logo's style (symbol-only icon, pattern tile) | `recraft/v4/style/text-to-vector` with the logo PNG in `image_urls`, `style_match: "precise"` | style-conditioned vectors; a reusable `style_id` comes from `recraft/v4/create-style` | ~USD 0.05/image, +USD 0.005 inline style |
| User has only a raster logo | `fal-ai/recraft/vectorize` | traces PNG/JPG/WEBP to SVG; an approximation until the user approves it | ~USD 0.01/image |
| Vector endpoint down or failing (documented fallback only) | `openai/gpt-image-2.5/flare/text-to-image` flat mark on white → `fal-ai/recraft/vectorize` | raster then trace; labelled "traced" | ~USD 0.06 + USD 0.01 |
| Applications with words besides the logo: business card, social templates, poster, banner, presentation cover | `openai/gpt-image-2.5/flare/edit`, `quality: "high"`, logo PNG as image 1 | typography leader; up to 16 references | ~USD 0.04–0.06/image by size |
| Small or dense text failed once on Flare | `openai/gpt-image-2.5/sunburst/edit` | precision tier, same fields and rates | same table |
| Photoreal mockups with the logo only: signage, packaging, merchandise | `bytedance/seedream/v5/pro/edit`, logo PNG in `image_urls` | arena #1 photoreal and e-commerce; flat price | ~USD 0.07/image |
| App icon, mono and reversed logo, PNG exports | local: `brandkit.py icon`, `svg-variants`, `png` | exact geometry; a model would redraw the mark | USD 0 |
| Platform icon files (App Store, Play, Android adaptive, PWA, favicon, macOS) from the approved icon; logo sting for video | local: `brandkit.py icon-export`, `sting` | one geometry re-rendered per size; dated rules in `scripts/icon-targets.json`; a video model would redraw the logo | USD 0 |
| Print-size raster of an approved application | `fal-ai/seedvr/upscale/image` (text-heavy: `topaz/upscale/image/precision`, model `Text Refine`) | faithful enlargement; re-read the text afterwards | ~USD 0.001/MP; Topaz ~USD 0.08 per 24 MP |

Tie-breakers:

1. Local beats generative whenever geometry or text must be exact: variants, icon, platform files, sting, recolour and exports never go through a model.
2. Words other than the logo on the surface → GPT Image 2.5. Logo alone on a physical object → Seedream 5.0 Pro edit.
3. The user supplies official assets (logo, colours, fonts) → register them with `--origin user`; they are authoritative, skip that stage's generation, and a generated choice never overwrites them.
4. The user named a model → use it after the live check; mention the default in one line.

Traps:

- **One prompt, three times.** The vector endpoint has no `num_images` and no `seed`. Three candidates are three jobs with three different ideas; the script refuses duplicate prompts in a round.
- **Hex in the vector prompt.** Exact colours go in `colors` and `background_color` as `{r,g,b}` integers (`status` prints them per palette colour). They are preferences, not guarantees: `svg-check` reports what came back, `svg-recolor` makes it exact after approval.
- **SVG as a reference.** Edit and style endpoints take PNG, JPG or WEBP. Export the approved logo with `brandkit.py png` first; no converter → ask the user for a PNG export of the approved SVG.
- **Auto size.** GPT Image 2.5 edit defaults `image_size` to `auto`, which follows the input: a square logo yields a square poster. Always send `{width,height}` (multiples of 16). Seedream's default `auto_2K` can double the price: send `{width,height}` inside the 1536x1536 area.
- **Default quality.** `quality` defaults to `high` and bills by tokens. Set it on purpose; `xhigh` or `max` only after the user saw the price.
- **Paraphrased lock.** The BRAND LOCK goes into every application prompt verbatim. Never retype it: prompt files carry the line `{{BRAND_LOCK}}` and `brandkit.py plan` substitutes the approved block; `add-candidate` refuses a prompt without it.
- **Redrawn logo.** A model that "improves" the mark produced a different logo. Compare every application with the approved PNG; drift is a fail, not a style.
- **Raster called vector.** A traced raster is labelled traced; a PNG is never delivered as "the vector logo".

## Workflow

1. **Classify and read state.** `status` first. Request type decides the slots: new identity (all stages); extend (user has some official assets: register them, build the rest); apply only (official logo + colours + type → lock → applications: register what they brought with `--origin user` and approve it with their words from the brief; the pieces you derive, snapshot, palette roles and a missing typeface, go into ONE free review, then the lock review, then the paid batch); change (approve a new revision, then handle the invalidation list); export only (a finished icon or logo SVG in, platform files or a sting out: no stages, no ledger, `icon-export <file> --out-dir genmedia-output/<slug>/app-icon`, then Read the sheet: `references/app-icons.md`). Slot rules and the dependency graph: `references/qa-and-iteration.md`.
2. **Intake and tiers, one message.** Look at every supplied asset first (Read images; `svg-check` SVGs; a site URL is read, never imitated; HEIC, AVIF, TIFF or CMYK files → ask for a PNG or JPEG, no converter is assumed here). Verify and price the routes in one call:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price fal-ai/recraft/v4.1/text-to-vector,openai/gpt-image-2.5/flare/edit,bytedance/seedream/v5/pro/edit --explain
   ```
   Dollars: vector rows answer `unit: "images"` → `unit_price` x jobs (one image per job; a logo round is 3 jobs). GPT Image 2.5 answers `1 units`, which is not a price → take the row of the next larger size at your `quality` from the cost table in `references/routing-image.md` (`t2i-typography` notes; edit rows include one input image) and add the reference allowance in `references/platform.md` §7 per further reference. Seedream (`units`, read `pricing_text`): per output image inside the 1536x1536 area, plus the surcharge per input image after the first. Local stages cost nothing. Tiers (dated hints, recompute): **1 core identity** (3 logo candidates) about USD 0.24; **2 core + 4 applications** (business card, social post, one mockup, app icon) about USD 0.40 to USD 0.55; **3 full kit** (10 generated applications + icon) about USD 0.85 to USD 1.25. Say that each re-roll round adds its batch again (worst case about three times the tier). Send the intake message, apply the gate to the chosen tier, wait where it says confirm.
3. **Strategy, palette and typography (free), Review 1.** `init`, then write `strategy.json`, two or three `palette-<A..C>.json` and two or three `type-<A..C>.json` (family NAMES with rationale and visual traits) with the Write tool (shapes: `references/design-brain.md`, `references/palette.md`, `references/typography.md`) and register them:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" init --brand "<Brand Name>"
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" add-candidate --brand <slug> --slot strategy --id strategy --data .genmedia/projects/<slug>/brandkit/strategy.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" add-candidate --brand <slug> --slot palette --id palette-A --data .genmedia/projects/<slug>/brandkit/palette-A.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" add-candidate --brand <slug> --slot typography --id type-A --data .genmedia/projects/<slug>/brandkit/type-A.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" board --brand <slug> --slot palette --slot typography
   ```
   The script normalises hex, checks roles and computes every contrast pair; fix `problems` before showing anything. Show the snapshot and the board (Delivery), ask for a palette and a pairing in one message, **stop**. On the reply: `approve` strategy, then palette, then typography, each with `--note "<their words>"`. Ship no font files; the only licence statement is "check the licence".
4. **Logo, Review 2 (paid).** Read `references/design-brain.md` and `references/logo.md`. Three genuinely different directions, one prompt file each (`prompts/logo-A-r1.txt`), palette colours as `colors`. Write the spec with the Write tool (`logo-r1.spec.json`: jobs with `prompt_file`, never `input.prompt`; worked spec in `references/logo.md`), let the script build the plan, then run it with a 600000 ms Bash timeout:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" plan --brand <slug> --spec .genmedia/projects/<slug>/brandkit/logo-r1.spec.json --out .genmedia/projects/<slug>/brandkit/logo-r1.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/brandkit/logo-r1.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" svg-check genmedia-output/<slug>/logo-A-r1_0.svg --palette .genmedia/projects/<slug>/brandkit/palette-A.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" png genmedia-output/<slug>/logo-A-r1_0.svg --out genmedia-output/<slug>/look/logo-A-r1.png --size 1024 --background "#ffffff"
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" add-candidate --brand <slug> --slot logo --id logo-A --file genmedia-output/<slug>/logo-A-r1_0.svg --data .genmedia/projects/<slug>/brandkit/logo-A.json --plan-file .genmedia/projects/<slug>/brandkit/logo-r1.json --job logo-A-r1 --expect-text-file .genmedia/projects/<slug>/brandkit/logo-text.txt --read-text-file .genmedia/projects/<slug>/brandkit/logo-A-read.txt
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" board --brand <slug> --slot logo --png
   ```
   `plan` refuses, before anything is paid, what `add-candidate` would refuse afterwards: a wrong round number, duplicate or unchanged prompts, leftover placeholders, a job id the run ledger already knows. `status: "pending"` → the same batch command again, never a resubmit. An output with `path: null` → `pipeline.py fetch`. **Look before you register:** the board only shows registered candidates, so Read each `look/` PNG first and write every word you actually see, letter by letter, to the read file (`text-check` compares without touching the ledger; a `text_mismatch` at `add-candidate` is recorded and cannot be undone by editing the read file). A misspelt name is a failed candidate (retry that letter only, prompt changed, job id `logo-A-r1-t2`). Then register, build the board and Read its PNG for the small sizes. A symbol-only mark registers with `--no-text`. No converter → you cannot see the marks: generate symbol-only candidates, say the visual check was not possible, and let the board speak. Show, give the trademark notice, **stop**. After approval build the production set (`svg-recolor`, `svg-variants`, `png`, then `add-asset` for `primary`, `nobg`, `mono` and `reversed`): `references/logo.md`. `svg-variants` clears the model's background plate for `-nobg.svg`, and the ledger verifies that file like any other variant: never delete shapes by hand.
5. **BRAND LOCK, Review 3.** Write `lock.json` (construction, clear space, misuse, imagery style, layout, do, don't: `references/brand-lock.md`), then `python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" lock --brand <slug> --data .genmedia/projects/<slug>/brandkit/lock.json`. Show the plain-language summary, **stop**, `approve --slot lock --candidate lock`. Tier 1: continue with step 7 in the same turn. From here `brandkit.py lock --brand <slug>` prints the frozen block; it fails while the lock is unapproved or invalidated, and that failure is the signal not to generate.
6. **Applications, one review per batch.** Plan card for the tier (sizes, routes, exact strings: `references/applications.md`), cost gate. Strings are the user's own, character for character; a surface without supplied lines is planned logo-only, and the plan card says in one line which lines they could still add. One prompt file per job: role line for image 1, then the line `{{BRAND_LOCK}}`, then the application block; `plan` replaces that line with the approved block, so the lock is verbatim by construction and never typed by hand. Upload the logo PNG once, register it, build, fill, run:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload genmedia-output/<slug>/logo/logo-primary-1024.png
   python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" add --label <slug> --step logo --path genmedia-output/<slug>/logo/logo-primary-1024.png --url <cdn_url>
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" plan --brand <slug> --spec .genmedia/projects/<slug>/brandkit/apps-1.spec.json --out .genmedia/projects/<slug>/brandkit/apps-1.tmpl.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" fill --template .genmedia/projects/<slug>/brandkit/apps-1.tmpl.json --out .genmedia/projects/<slug>/brandkit/apps-1.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/brandkit/apps-1.json
   ```
   Bash timeout 600000 ms on every `batch`; `status: "pending"` → the same command again, never a resubmit. First call to an endpoint in the session is a one-job canary. QA each output before anyone sees it (`references/qa-and-iteration.md`): Read it next to the logo PNG; read back every word into a read file; `add-candidate --slot app-<name> --id <name> --file … --plan-file …/apps-1.json --job app-<name>-r1 --expect-text-file … --read-text-file …` refuses a missing lock or a text mismatch. `board --slot app-<name>` (repeat `--slot` for one board per batch), show, **stop**, approve each application the user accepts. After the last batch: step 7 in the same turn.
7. **Brandbook and hand-off, no review.** Right after the last approval, in the same turn. `python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" book --brand <slug> --pdf` writes a self-contained HTML book from approved slots only; it inherits their approval (`status: "approved"`, `derived: true`), so there is nothing to ask. With a browser attach the PDF (`add-asset --slot brandbook --role pdf`); without one there is no PDF: deliver the HTML and say that printing it to PDF from any browser gives the same pages. Look at it (`png` of the HTML when a browser exists) before delivering; a missing plate or a wrong page is fixed in its slot, then `book` again (`references/brandbook-and-handoff.md`). Software product, or the user asked for icon or favicon files → first export the approved `app-icon` (`references/app-icons.md`), Read `icon-sheet.png` for the 32 and 16 px sizes and act on `problems` and `warnings`:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" icon-export genmedia-output/<slug>/logo/app-icon.svg --brand <slug> --name "<App Name>"
   ```
   A logo sting (`brandkit.py sting`, same reference) only when asked for or when a video skill will use it. Then:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/brandkit.py" export-list --brand <slug> --copy
   python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" manifest --label <slug>
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --label <slug> --sum
   ```
   `export-list` lists approved files only and names anything stale or missing; resolve or state each. Package layout: `references/brandbook-and-handoff.md`.
8. **Changes.** Register the new candidate, get it approved, and read `invalidated` in the `approve` answer. Tell the user what became stale and what rebuilding costs (Delivery); rebuild only what they confirm, in stage order (the lock is always recomposed and re-approved first; rebuilt jobs are `-r2`). An element that still fits may be kept: `approve` it again with their words. Etiquette: `references/qa-and-iteration.md` section 7.

## Delivery

Intake and tiers (one message):

```
To build "<name as given>" I need two things: the exact spelling of the name, and what the company does.
Optional (my default in brackets): audience [not stated] · three tone words [I propose them] · colours to use or avoid [none] · existing logo, colours, fonts or site [none] · exact lines for cards, posters or posts, such as name, title, contact, headline [logo only].
Tiers (estimates from today's prices; a re-roll round repeats its batch):
1. Core identity: palette, 3 logo candidates as SVG, typography, brand lock, brandbook — about $<t1>
2. Core + 4 applications (business card, social post, one mockup, app icon) — about $<t2>
3. Full kit (adds signage, packaging, merchandise, more social templates, poster, banner, presentation cover) — about $<t3>
I stop for your approval three times: palette and type (free), logo, brand lock; plus once per application batch. The brandbook and the package follow from those approvals. Which tier? [1]
```

Review (every stage; adapt the noun; Review 1 asks for a palette and a pairing in one message):

```
<Stage> for "<Brand>": <n> options — <board path> (open in a browser)
A. <name>: <one line: the idea, not the adjectives>
B. <…>
C. <…>
Checked: <what you verified: contrast pairs, spelling read back, SVG clean; or honestly: could not look, no converter>
<logo review only: A generated mark can resemble existing trademarks; a trademark search before use is your responsibility.>
Spent so far: about $<est_cost_usd_completed>. Pick A, B or C, or tell me what to change. I wait for your answer.
```

Invalidation notice:

```
Approved: <slot> r<n>. This makes stale: <slots>. Still valid: <slots>.
Rebuilding them costs about $<x> (<which batches>). Rebuild all, only <…>, or keep <slot> as it is?
```

Final:

```
Brand kit "<Brand>" — genmedia-output/<slug>/package/
Logo: logo/logo-primary.svg, logo-primary-nobg.svg (transparent), logo-primary-mono.svg, logo-primary-reversed.svg <+ PNG sizes | PNG not made: no converter here>
Palette and type: palette/palette.css, typography/typography.json (font families are names: check each licence before use)
Applications: <k> approved — <list>   Brandbook: brandbook/brandbook.html <+ brandbook.pdf>
<only when exported:> App icon files: app-icon/ (ios, play, android, web, macos; rules as published on <verified_on>) <+ logo sting: logo/<file>.mp4, silent>
BRAND-LOCK.txt is the block to paste into any later prompt. Manifest: package/manifest.json   Gallery: <gallery_url>
Editable: the SVG files and the HTML. Flattened: every application image (mockups are visualisations, not print-ready artwork).
Models: <display names>. Estimated spend: about $<est_cost_usd_completed>, including <r> re-rolls. Not done or withheld: <none | what and why>.
A trademark search for the mark is your responsibility. CDN links are public and may expire; the local files are your copies.
```

Translate the templates; keep paths, hex values, names and on-image strings unchanged.

## Errors

| Signal (verbatim) | Action |
|---|---|
| `"status":"pending"` with `resume` | Run the same `gm.py batch --plan` again (600000 ms timeout). Never resubmit. |
| `brandkit.py`: `kind: "upstream_missing"` | Stage order: the named upstream slot is not approved. Finish that review first. |
| `kind: "lock_not_approved"` or `"lock_missing_in_prompt"` | No generation. Approve the lock, or paste the block from `brandkit.py lock` into the prompt file unchanged. |
| `kind: "text_mismatch"` | The output's words differ from the requested ones (`diff` shows where). Failed output: re-roll with the prompt changed, never deliver. |
| `plan`: `kind: "round_mismatch"`, `"job_id_reused"` or `"placeholder_left"` | Nothing was spent. Fix the job id (`-r<round>`; a retry inside a round adds `-t2`) or the prompt file, then build the plan again. |
| `kind: "reroll_limit"` or `"prompt_unchanged"` | Two re-rolls spent, or nothing changed. Change the route or the idea, or ask the user. |
| `kind: "svg_unsafe"` | Script, external reference or embedded raster in the SVG. Do not show or ship it; re-roll. |
| `kind: "tool_missing"` (`png`, `icon-export`, `sting`, `book --pdf`) | No converter here. Deliver SVG and HTML and say so; never send the logo through a video model instead of `sting`. |
| `icon-export`: `problems` not empty (`clipped_by_mask`, `outside_safe_circle`, `no_alpha`, `bytes_over_cap`), `kind: "icon_empty"` or `"not_approved"` | Nothing was attached. Table and fixes: `references/app-icons.md` section 3. Not approved → register the icon in slot `app-icon` and get it approved first. |
| `"kind":"validation"` with `"fields":[]` and a `hint` | The queue hides the reason. Check in order, change the first thing that is off: fields against the OpenAPI schema (`colors` objects, sizes) → reference URL (expired: re-upload, `pipeline.py add` again) → prompt (a real brand's name, a policy term). Fields or URL fixed → same job id: `plan` (and `fill`) again, then `batch --plan … --retry-failed`. Prompt changed → new id `…-r1-t2`, plain `batch`. Max 3 attempts. |
| `"kind":"content_policy"`, or a black image | Do not deliver or resend unchanged. Usual cause here: a named brand or a trademarked character in the brief. Rewrite in formal qualities. |
| `"kind":"auth"` | Stop every stage. The user fixes the key or balance. |

More: `references/troubleshooting-brandkit.md`. Platform error types: `references/platform.md` section 4.

## This skill does NOT

- Copy, trace or "refresh" another company's logo, or produce a mark "in the style of" a named brand or designer.
- Clear trademarks, check name availability or give legal advice. It says once that the search is the user's job.
- Ship font files or state licence terms. Families are names with a rationale and "check the licence".
- Produce print-ready artwork (dielines, bleed, CMYK, spot colours) or editable PSD, AI or PPTX files. Mockups are visualisations; the editable deliverables are SVG and HTML. Print specs: check with the print shop.
- Invent positioning, history, claims, certifications, contact details or statistics to fill a layout.
- Make ads, product shoots, thumbnails or listing cards (use `/genmedia-skills:ads`, `/genmedia-skills:product-photoshoot`, `/genmedia-skills:youtube-thumbnail`, `/genmedia-skills:marketplace-cards` with the BRAND LOCK pasted in).

## Common mistakes

- Generating logos before the palette is approved, or applications before the lock: the script refuses, and the money would have been wasted anyway.
- Three colourways of one idea presented as three candidates.
- Treating "looks good to me" as approval, or approving with your own summary instead of the user's words.
- Stopping to ask about the brandbook or the package: both follow from approvals already given.
- Recolouring, cleaning or redrawing a candidate during review. The user judges what the model returned; production edits come after approval and only by exact substitution.
- Re-rolling with the same prompt, or a fourth attempt instead of a new idea.
- Regenerating downstream assets right after a palette change without telling the user what became stale and what it costs.
- Paraphrasing the lock, or putting hex codes into the vector prompt instead of `colors`.
- Accepting a name that is "close" (Turkish İ ı ş ğ ü ö ç): one wrong letter is a fail.
- Calling a PNG "the vector", or promising a PDF on a machine without a browser.

## Reference index

- `references/design-brain.md`: read when turning the brief into a direction: strategy snapshot shape, archetype and tone → form, colour and type implications, and how to make three candidates genuinely different.
- `references/palette.md`: read when building or revising palettes: roles, `palette.json` shape, contrast rules, board reading, colour pitfalls.
- `references/logo.md`: read when writing logo prompts, planning the logo batch, checking returned SVG, building the production set (recolour, mono, reversed, PNG, icon) and writing misuse rules.
- `references/typography.md`: read when proposing pairings: `type.json` shape, pairing logic, traits wording for prompts, Turkish coverage, the licence sentence.
- `references/brand-lock.md`: read when writing `lock.json`, checking the emitted block, or pasting it into prompts; format and two examples.
- `references/app-icons.md`: read when exporting platform icon files or a logo sting: what each platform gets and why, dated sources, the checks and their fixes, favicon strategy, hand-off wording.
- `references/applications.md`: read when planning any application: prompt contract with LOCK and logo reference, default sizes, text rules, route and pitfalls per application, worked batch template.
- `references/brandbook-and-handoff.md`: read when building the book, exporting PDF or PNG, assembling the package and manifest.
- `references/qa-and-iteration.md`: read when checking any output, deciding pass, re-roll or repair, and whenever an approval returns an invalidation list; slot rules and the dependency graph.
- `references/troubleshooting-brandkit.md`: read when a stage fails or resumes oddly, a converter misbehaves, text keeps failing, or costs surprise.
- `references/routing-image.md`: read when picking another tier, when an ID is not active, or for the dated GPT Image 2.5 cost table.
- `references/cli-contract.md`: read when a helper call fails, a job is pending, or you need batch plan keys, `wait`, `cancel`, the ledger, the gallery or the raw CLI.
- `references/platform.md`: read when estimating cost, reacting to a platform error type, or explaining URL privacy, billing and safety.
- `scripts/gm.py`: shared helper for every paid call (`preflight`, `price`, `upload`, `run`, `wait`, `cancel`, `batch`, `ledger`).
- `scripts/pipeline.py`: project state (`urls`, `fill`, `add`, `fetch`, `manifest`); resolves `@logo` references and writes the manifest.
- `scripts/brandkit.py`: local, free, no network: approval ledger (`init`, `status`, `add-candidate`, `new-round`, `add-asset`, `approve`, `invalidate`, `lock`), pre-pay plan builder (`plan`), review surfaces (`board`, `book`, `export-list`), checks (`palette-check`, `text-check`, `svg-check`), SVG production (`svg-recolor`, `svg-variants`, `icon`, `png`, `tools`) and platform output (`icon-export`, `sting`); one JSON object per call, exit 0 ok, 1 failed, 2 usage.
- `scripts/icon-targets.json`: dated platform icon sizes, formats and safe zones with source URLs, read by `icon-export`; its `unverified` list names what no official page stated.
