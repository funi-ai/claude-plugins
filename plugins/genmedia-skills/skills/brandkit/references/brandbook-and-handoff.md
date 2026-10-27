# Brandbook and hand-off: book structure, exports, package, manifest

Everything here is local and free. The brandbook is **always a self-contained HTML file**; PDF and PNG exist only when a converter is detected. Nothing depends on Pillow, ImageMagick, rsvg-convert, LibreOffice or a slide template. `brandkit.py`, `pipeline.py` and `gm.py` abbreviate the calls shown in SKILL.md; run them from the project root.

## 1. Probe first

```text
brandkit.py tools
```

| Answer | Means | You can promise |
|---|---|---|
| `png: "browser"`, `pdf: "browser"` | a Chromium-family browser was found (Chrome, Chromium, Edge, Brave; `PATH`, the usual macOS app paths and Windows program folders) | board screenshots, logo PNGs with transparency at exact sizes, brandbook PDF |
| `png: "qlmanage"`, `pdf: null` | macOS Quick Look only | logo PNGs as a **labelled fallback** (size and background not guaranteed); no board screenshots, no PDF |
| `png: null`, `pdf: null` | no converter | SVG files and HTML only. Say so at intake, not at delivery |

`GM_BROWSER_BIN` and `GM_QLMANAGE_BIN` override the binary; the value `none` disables a tool (useful to test the degraded path). Never install anything on the user's machine to get a PDF; never offer a route through the tools named in the first paragraph.

What the script runs, so you can explain or reproduce it:

```text
<browser> --headless --disable-gpu --hide-scrollbars --no-first-run --no-default-browser-check --force-device-scale-factor=1 --user-data-dir=<temp dir> --window-size=<W>,<H> [--default-background-color=00000000] --screenshot=<out.png> <file:// URL>
<browser> --headless … --no-pdf-header-footer --print-to-pdf-no-header --print-to-pdf=<out.pdf> <file:// URL>
qlmanage -t -s <longest side> -o <temp dir> <file.svg>
```

Some headless browsers write the file and never exit: the script waits until the PNG or PDF is complete on disk (at most 60 s), then stops the process and removes the temporary profile. `kind: "tool_failed"` means no complete file appeared: deliver the SVG or HTML and say the export failed; do not loop.

## 2. Before building the book

The book shows what the ledger holds. Get these in place first, or the book will say "not produced" where a plate should be:

1. The five foundation slots approved (`strategy`, `palette`, `logo`, `typography`, `lock`); otherwise `book` answers `kind: "upstream_missing"` with the missing names.
2. The logo production set attached to the approved logo (`logo.md` section 5): `add-asset --slot logo --role primary`, `--role nobg`, `--role mono`, `--role reversed` (and `png-1024`, `icon` when made). The book's logo page places `nobg` (else `primary` with its plate hidden) on white and on the brand background, `mono` and `reversed` on their grounds.
3. Every application the user accepted is **approved**. Open or invalidated applications are left out, silently for the reader but not for you: `status` lists them, and the final message names them.

## 3. `book`

```text
brandkit.py book --brand <slug>
brandkit.py png genmedia-output/<slug>/brandbook/brandbook.html --out genmedia-output/<slug>/brandbook-preview.png --width 1400 --height 6000
brandkit.py book --brand <slug> --pdf
brandkit.py add-asset --brand <slug> --slot brandbook --role pdf --file genmedia-output/<slug>/brandbook/brandbook.pdf
```

Writes `genmedia-output/<slug>/brandbook/brandbook.html` plus `assets/` (copies of the approved raster applications, referenced by relative path) and registers it in slot `brandbook` as **approved, derived**: the book only arranges slots the user already approved, so it inherits that approval (the note quotes the lock approval) and is never a separate review. Logo SVGs are inlined as data URIs; no script, no web font, no network request: the folder can be zipped, mailed or opened offline. Building it twice from unchanged slots creates no new revision (`new_revision: false`).

Pages (each a print page, A4 landscape, via the file's own print CSS):

| # | Page | Source |
|---|---|---|
| cover | primary logo, brand name, the revision stamp of all five foundation slots | ledger |
| 1 | Strategy snapshot: every string and list of the approved `strategy.json`, with the note that facts were supplied by the owner | strategy |
| 2 | Logo: primary on white and on the brand background, one-colour, reversed on dark; construction, clear space, minimum size, the never-list | logo assets + lock data |
| 3 | Colour: swatches, a table of name, role, hex, RGB and use, contrast pairs at 3:1 and above; a note that print conversions are set with the print shop | palette |
| 4 | Typography: display and body (and mono) samples with Turkish letters, family names, weights, fallbacks; "named, not bundled; check the licence" | typography |
| 5 | Imagery, tone and layout; do and don't | lock data + tone words |
| 6 | Applications: every approved `app-*` file with its name; "visualisations generated with AI, not print-ready artwork" | applications |
| last | The BRAND LOCK block in full, the trademark sentence and the AI-generation note | lock |

Before delivering, not a review: look at the preview PNG when a browser exists (page by page: missing plates, a font that fell back, an application that is cropped), then put the path and one line per page into the delivery; nothing waits for a reply. The type samples render in the real face only where it is installed: say so instead of apologising for a fallback. Changes to content are changes to a slot (new lock wording, another application approved): make them there, run `book` again, deliver the new revision.

PDF: `book --pdf` writes `brandbook.pdf` next to the HTML. Without a browser it answers `pdf: null` with `pdf_reason`; the delivery then says: "Open brandbook.html in any browser and print to PDF (A4 landscape, background graphics on): the pages are the same." Attach the PDF with `add-asset` so the package lists it. A slot change after that makes the PDF a stale asset: `export-list` names it until it is rebuilt.

## 4. Exports the user may ask for

| Need | Command | Notes |
|---|---|---|
| Logo PNG, transparent, exact width | `brandkit.py png <logo>.svg --out <file>.png --size 2048` | height follows the viewBox; `--background "#hex"` for an opaque plate; with `qlmanage` the result is labelled `fallback: true` |
| Several sizes of the logo (social avatar, email signature) | one `png` call per size, then `add-asset --role png-<n>` | the PNG header is read back: `size` in the answer is what was actually written |
| App icon files for App Store, Play, Android, web (favicon, PWA) and macOS | `brandkit.py icon-export <approved app-icon.svg> --brand <slug>` | one call writes every platform file from the approved icon and checks sizes, alpha and safe circles: `app-icons.md` |
| Logo sting for video intros and end cards | `brandkit.py sting <logo>.svg --out <file>.mp4 --background "#hex" --size 1080x1920` | the real SVG animated by the browser, joined by ffmpeg; silent: `app-icons.md` section 5 |
| Board as an image for chat | `board … --png` | needs a browser; otherwise send the HTML path |
| Recoloured or single-colour logo for a special surface | `svg-recolor`, `svg-variants --ink … --paper …` | exact substitution only; geometry is verified |
| PDF/EPS logo, CMYK or Pantone values, font files, Apple's layered Icon Composer file | not produced here | say so; the SVG opens in any design tool, which exports those formats; colour conversions belong to the print shop; fonts are the user's download and licence check |

## 5. Package

```text
brandkit.py export-list --brand <slug>
brandkit.py export-list --brand <slug> --copy
pipeline.py manifest --label <slug>
gm.py ledger --label <slug> --sum
```

`export-list` without `--copy` is the dry run: `files` (approved candidates and their current assets, each with `kind: "editable"` or `"flattened"`), `pending` (slots without an approval), `problems` (invalidated slots, stale assets, missing files). It exits 1 while `problems` is not empty. Resolve each one, or decide with the user to leave it out and say so in the final message. `--copy` writes the package even then; the problems travel inside `manifest.json`, which is honest, but do not call the kit complete.

```text
genmedia-output/<slug>/package/
  manifest.json
  BRAND-LOCK.txt                      the approved block, for any later prompt
  logo/source/logo-B-r1_0.svg         the approved candidate exactly as returned
  logo/logo-primary.svg               recoloured to exact palette hex
  logo/logo-primary-mono.svg  logo-primary-reversed.svg  logo-primary-nobg.svg
  logo/logo-primary-1024.png  app-icon.svg  app-icon-1024.png
  palette/palette.css                 :root { --brand-primary-pine: #1f3d2b; … }
  palette/palette.json                colours, roles, rgb, contrast pairs
  typography/typography.json          family names, weights, traits, the licence sentence
  applications/<name>/<file>.png      approved applications, flattened
  app-icon/                           icon-export folder when made: ios/ play/ android/ web/ macos/ icon-sheet.png icon-export.json
  brandbook/brandbook.html  assets/  brandbook.pdf
```

`manifest.json`: `brand`, `generated_at`, `state_version`, `revisions` (approved revision per slot), `files[]` (`slot`, `revision`, `role`, `to`, `kind`, `sha256`), `generated_files`, `pending`, `problems`, and three standing notes (applications are AI visualisations, font families are names, the trademark search is the owner's). The checksum lets a later session tell whether a file in the package is still the approved one.

Two manifests, two jobs: the **package manifest** says what is approved and delivered; `pipeline.py manifest` writes `.genmedia/projects/<slug>/manifest.json` from the run ledger (every paid job, its outputs and estimated cost, plus registered local files) and runs its own mechanical gate. `gm.py ledger --sum` gives the estimated spend for the final message (quote `est_cost_usd_completed`; `est_cost_usd` also counts failed requests); count re-rolls from the job ids (`-r2`, `-t2`).

## 6. Final message checklist

Use the Final template in SKILL.md, in the user's language, and make sure it says:

- where the package is, and which files are **editable** (SVG, HTML, CSS, JSON, TXT) and which are **flattened** (every application image);
- what was **not** made and why: no PNG or PDF (no converter), an application withheld after three failed attempts, a slot left stale by the user's choice;
- models by display name, estimated spend including re-rolls, the gallery link from the last batch;
- fonts: names only, check each licence; colours: screen values, print conversions with the print shop; mockups: visualisations, not print-ready artwork;
- the trademark sentence, once;
- CDN links are public and expire; the local files are the durable copies;
- the next step inside the plugin: paste `BRAND-LOCK.txt` into prompts for `/genmedia-skills:ads`, `/genmedia-skills:product-photoshoot`, `/genmedia-skills:youtube-thumbnail` or `/genmedia-skills:marketplace-cards`, with `logo-primary-1024.png` as the reference.

Suggest adding `.genmedia/` to `.gitignore` only when the project is a git repository and the user agrees; `genmedia-output/` is theirs to commit or not.
