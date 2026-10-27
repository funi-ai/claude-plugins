# Troubleshooting: thumbnails

For results that are wrong rather than failed, and for helper problems not covered by the SKILL.md error table. Platform error types: `platform.md` section 4. Helper and ledger mechanics: `cli-contract.md`. Budget for every row: at most 3 attempts per step, one change per attempt, then stop and explain.

## Text

| Symptom | Likely cause | Fix |
|---|---|---|
| A word is misspelt, letters doubled or dropped | Long or unusual word; text described instead of quoted | Quote the exact string, add the `spelled` string from `thumbcheck.py text`, cut the word count. Second failure → plate path, text-only edit (`text-and-readability.md` section 2) |
| Turkish letters flattened (`Ş→S`, `İ→I`, `Ğ→G`, `Ü→U`) | The model treated the diacritic as decoration; a display typeface without those glyphs | Name each special letter in words, ask for "full Turkish glyph support", avoid decorative faces. Then the ladder in `text-and-readability.md` section 1 |
| `I` and `İ` wrong in caps (`SIMDI`, `İLIK`) | The string was uppercased by the model or by a generic routine | Always take `upper` from `thumbcheck.py text --lang tr` and send that string; never send lowercase with "in capitals" |
| Extra words, fake small print, a watermark, a channel logo | No exclusivity sentence; STYLE words like "YouTube" or "magazine cover" invite UI and mastheads | TEXT block ends with "No other words, letters or numbers anywhere"; CONSTRAINTS lists watermark, logo, interface; describe the look, do not name a platform in STYLE |
| Text legible large, mush at 160 px | Cap height too small, thin face, no separation | Fewer words first; then cap height as a fraction of frame height; outline or solid plate; move off the busy area |
| Text sits on the face or in the bottom-right corner | Zone not named | NEGATIVE SPACE and TEXT both name the zone; add "bottom-right corner empty" |
| Text changed in a revision that was about something else | KEEP sentence missing the text | Add "same text wording, position and size" to KEEP; rerun from the same source |
| The user's wording is over budget and they insist | Their call | Render it, show the 160 px preview next to a 3-word alternative, let them choose. Do not shorten silently |

## Picture

| Symptom | Likely cause | Fix |
|---|---|---|
| Output is portrait or square although 16:9 was planned | `image_size` left at `auto` on an edit endpoint: it follows the reference photo | Explicit `{width,height}` on every call. `thumbcheck.py sheet --expect 16:9` catches it (`aspect_ok: false`) |
| `multiple_of` error on the size | 1080 or another side is not a multiple of 16 | 1280x720, 2560x1440, 3840x2160, 720x1280, 1440x2560, 1024x1024, 2048x2048; 1920x1080 comes from `thumbcheck.py fit` |
| The face does not look like the person | Weak reference (small, angled, sunglasses), extreme expression, too many competing references | Better face photo, front-facing and sharp; calmer expression; at most 3 face references; then Identity repair in `revisions.md` |
| Face is over-smoothed or "beautified" | Poster-style words push retouching | Add "natural skin texture, do not beautify or slim the face"; drop "flawless", "glamour", "perfect" |
| Reference photo's background or clothes leak into the thumbnail | The manifest did not limit the reference's role | "image 1 = identity reference (face and hair only; ignore its background, clothing and lighting)" |
| The final differs from the picked draft | The final was generated from the prompt, or image 1 was not the draft | Final = edit with the pick as image 1 and the composition-lock block (`prompt-blueprint.md`) |
| The final is faithful but small flaws were copied too | Composition lock copies everything | Add exactly one corrective sentence after TASK; more than one → new draft |
| Cluttered, no focal point | Too many nouns in the prompt | One subject, one prop. Delete every object that does not explain the hook; darken or blur the background |
| Flat, muddy at small size | Low contrast, no separation light, mid-tone everything | Rim light, darker or flatter background, two colours plus one accent, raise saturation in STYLE |
| Subject vanishes on the dark strip or the light strip of the sheet | Image edges are near-black or near-white | Lighter vignette or thin light outline for dark images; a darker frame edge for bright ones |
| Hands, extra fingers, warped props | Complex hand action | Simplify the action, hide one hand, or crop tighter; keep "hands with five fingers" in CONSTRAINTS |
| Split layouts bleed into each other | Halves described in one sentence | Describe each half in its own sentence, name the divider, give each half its own light and palette |
| Black image, or a withheld result | Safety filter | Do not show it, do not resend unchanged. Usual triggers here: a named public figure, a real brand, gore or shock staging. Rewrite, say what changed. Assume it was billed |

## Requests to refuse or redirect

| Request | Response |
|---|---|
| "Use <celebrity>'s face", "someone who looks like <creator>" | No: likeness of a real person without their consent. Offer an invented face, the user's own face, or a faceless framework |
| "Copy this channel's thumbnail" | Open the example with the Read tool and take layout ideas only (framing, contrast, text position). Never upload someone else's thumbnail as a reference, never reproduce their face, logo or wording |
| A number, result, guest or product that is not in the video | No: truthfulness rule. Offer the strongest true alternative (the real number, a question, a curiosity gap) |
| Fake platform UI, fake comments, fake "breaking news" from a real outlet, verified ticks, play buttons | No. A generic, unbranded callout (circle, arrow, badge) is fine |
| Real logos of other companies (review and versus videos) | Only as they appear in the user's own photos of the product the video really tests, used as references. Never generated or redrawn from memory, never altered, damaged or mocked to disparage, never placed so that the brand seems to endorse the channel |
| Banner, logo, end screen, the video itself | Out of scope: `/genmedia-skills:image` or `/genmedia-skills:video` |

## Helpers, files, state

| Symptom | Cause | Fix |
|---|---|---|
| `thumbcheck.py`: `kind: "tool_missing"` | Neither ffmpeg nor macOS `sips` on this machine | Degraded gate: Read the full-size files, say the mechanical preview was unavailable; deliver the PNG master and its `probe` numbers; tell the user the resize is one step in any image editor. `probe` and `text` still work |
| `kind: "convert_failed"` | The tool cannot decode the file (HEIC on ffmpeg, AVIF on older macOS, a corrupt download) | The helper already tried the second tool. Ask for a JPEG or PNG export, or re-download the result (`gm.py wait <endpoint_id> <request_id>`) |
| `kind: "unsupported_format"` from `probe` | Format the header parser does not know and no tool to ask | `thumbcheck.py fit <file> --max-side 2048 --out <file>.jpg`, then probe the copy |
| `kind: "too_large"` from `fit` | Even the lowest JPEG step exceeds `--max-kb` | Deliver the next smaller `--size`, or raise the limit if the platform allows (check the platform's current rules) |
| `kind: "check_failed"` from `probe` | Wrong aspect or file too big | Aspect: the render size was wrong, or a crop is needed (`fit --size`). Size: `fit --max-kb` |
| `lockup`: `kind: "tool_missing"` | No Chromium-family browser here | Install Chrome, Chromium, Edge or Brave (or point `GM_BROWSER_BIN` at one); until then deliver the text-free plate and the logo file and say the lockup was not composed. Never ask the model to draw the logo instead |
| `lockup`: `kind: "svg_invalid"` | The file is not a plain SVG (entities, no `<svg>` root, no size) | Ask for a plain SVG export, or a transparent PNG |
| `lockup` warns `lockup_contrast`, `lockup_size` or `logo_opaque` | Logo colour close to the ground, a tall mark, a logo with a background box | `references/text-and-readability.md` section 2b |
| `fit` warns `upscaled` | The source is smaller than the target | Deliver a smaller size, or Enlarge in `revisions.md` first |
| `fit` warns `cropped` | Aspect of source and target differ | Read the result; if text or face is cut, re-render at the right aspect instead of cropping |
| Sheet warning "larger than 1568 px" | Many variants or `--cell` raised | Also run `preview` per variant, or lower `--cell` |
| `frame`: `extract_failed` | Timestamp past the end, or an unreadable video | Earlier timestamp; ask the user for a screenshot |
| `file_download_error` on a revision | The source URL from an earlier session expired | `gm.py upload` the local file, use the new URL |
| A draft job is `failed` with empty `fields` | Queued jobs hide the reason | SKILL.md error table order: schema → reference files → prompt. For reference photos: `fit --max-side 2048` to a JPEG and upload again |
| Session resumed, unsure what was picked | State lives on disk | Read `.genmedia/projects/<slug>/thumbnail.md`, then `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --label "<slug>" --tail 20`; continue at the first open step, never regenerate what exists |
| Costs drifting up over rounds | Re-rolls and extra references | `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --label "<slug>" --sum`; state the running estimate in the next message; apply the cost gate before another round |
