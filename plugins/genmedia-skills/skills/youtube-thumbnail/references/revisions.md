# Revisions

Everything that happens after the pick: narrow edits, wording tests, language variants, identity repair, enlarging. `gm.py` and `thumbcheck.py` abbreviate the calls shown in SKILL.md. Fields below were read from the live OpenAPI schemas on 2026-09-19; re-check with `genmedia schema <endpoint_id> --format openapi --json` before the first paid call.

## Etiquette

1. **One scope per round.** Only the text, only the expression, only the background, only a colour, only one element removed. Two requests in one message → two rounds, picture changes first, text last (text is the most fragile part).
2. **The current final is the source.** It goes in as image 1. Each accepted result becomes the next source; never go back to a draft or to the original prompt.
3. **Say what stays.** Every revision prompt has a `KEEP:` sentence. The model re-renders the whole image; what you do not protect may move.
4. **Maximum 3 rounds**, each different. After the third, stop and offer: accept the best so far, or a new draft round (SKILL.md Workflow step 3).
5. **A new idea is not a revision.** Different framework, different subject, different layout → new drafts. Say so instead of forcing it through an edit.
6. **Gate every result** (`text-and-readability.md` section 5) and compare it with its source: build a two-cell sheet, source first.
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/thumbcheck.py" sheet genmedia-output/<slug>/final_0.png genmedia-output/<slug>/rev1_0.png --expect 16:9 --out genmedia-output/<slug>/sheet-rev1.png
   ```
   Anything outside the scope changed (face, text, object, crop) → that attempt failed; tighten `KEEP:` and retry within the 3-attempt limit.
7. Log each round in `.genmedia/projects/<slug>/thumbnail.md`: scope, source file, result file, accepted or not.
8. **A thumbnail this skill did not make** ("change only the text on this one"): it must be the user's own; Read it, `thumbcheck.py probe` it, write a state card, upload it as image 1. `image_size` = the legal size of the same aspect at or above the source (a 1920x1080 source → 2560x1440, because 1080 is not a multiple of 16), then `thumbcheck.py fit` back to the delivery size. New words are still a claim: the truthfulness rule applies. Someone else's thumbnail is never edited.

## Edit endpoint fields (verified)

`openai/gpt-image-2.5/sunburst/edit` (finals and revisions) and `openai/gpt-image-2.5/flare/edit` (drafts, wording tests) share one input schema:

| Field | Type, limits | Use here |
|---|---|---|
| `prompt` | string, 1 to 32,000 chars, required | revision pattern below |
| `image_urls` | array of URLs, required, at most 16 | `[<current final>]`; add the face reference as image 2 only for an expression change |
| `image_size` | preset, `auto` (default, follows the input) or `{width,height}`: multiples of 16, long edge ≤ 3840, aspect ≤ 3:1, 655,360 to 8,294,400 px | always explicit and equal to the source size when that size is legal, e.g. `{"width": 2560, "height": 1440}` |
| `quality` | `auto`, `low`, `medium`, `high` (default), `xhigh`, `max` | `high` for anything that may ship; `medium` for wording tests |
| `num_images` | 1 to 10, default 1 | 1; variations multiply the cost |
| `output_format` | `png` (default), `jpeg`, `webp` | `png`; JPEG copies come from `thumbcheck.py fit` |
| `output_compression` | 0 to 100, only with `jpeg` or `webp` | not used |
| `background` | `auto` (default), `transparent`, `opaque` | not used |
| `mask_url` | optional URL; the schema says only that it "indicates what part of the image to edit" | not used by default. Measured 2026-09-21 (`platform.md` section 10): an opaque black-and-white mask broke the output; an RGBA mask with the edit area transparent guided the edit but the whole frame was redrawn. Instruction-only edits need no mask. A user-supplied mask: send it as RGBA with the edit area transparent, then compare face and text outside it with the source |
| `sync_mode` | boolean | never |

There is no `seed`, no `negative_prompt` and no strength or fidelity field: control comes from the prompt and from keeping the scope narrow. Output: `.result.images[].url`.

## Prompt pattern

```text
REFERENCES: image 1 = the current thumbnail.
CHANGE ONLY: <one thing, stated precisely>.
KEEP: everything else exactly as in image 1: same people and faces, same pose, same objects, same background,
  same colours and light, same framing, same text wording, position and size<, except the changed item>.
```

Run it (600000 ms Bash timeout; `pending` → `gm.py wait`, never a second run):

```json
{"prompt": "<pattern above>", "image_urls": ["<current final url>"], "image_size": {"width": 2560, "height": 1440}, "quality": "high", "num_images": 1, "output_format": "png"}
```

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run openai/gpt-image-2.5/sunburst/edit --input .genmedia/tmp/<slug>-rev1.json --label "<slug>" --est-cost 0.06 --download "genmedia-output/<slug>/rev1_{index}.{ext}"
```

The source URL is `outputs[].url` of the previous step while the session is fresh; otherwise `gm.py upload` the local file again. Cost: the 2560x1440 `high` row of the GPT Image 2.5 table in `routing-image.md` (about $0.055 on 2026-09-19, one input image included); each further input image adds the reference allowance in `platform.md` §7 (an estimate, not a price).

## Scopes

| Scope | CHANGE ONLY line | Notes |
|---|---|---|
| Text wording | `replace the text with exactly "<NEW TEXT>" (letters: <spelled>), same typeface, colours, outline, position and overall size` | Run the new words through `thumbcheck.py text` first. Longer text → say "reduce the letter size only as much as needed to keep the same margins", then check the 160 px preview again |
| Text spelling fix | `correct the text so that it reads exactly "<TEXT>" (letters: <spelled>); the letter <X> must be <description>` | For diacritics name the letter in words (`text-and-readability.md` section 1) |
| Text style | `make the text <fill colour> with a <outline or plate>`, or `move the text to the <zone>` | Moving text exposes the area behind it; say what should appear there ("continue the background gradient") |
| Expression | `change the presenter's expression to <emotion, intensity, physical cue>; identity, head position, hair and lighting stay` | Add the face reference as image 2 and the identity-lock sentence from `prompt-blueprint.md`. Extreme expressions cost likeness |
| Background | `replace the background with <description>; the subject's outline, edge light and cast shadow stay` | Keep the rim-light colour compatible with the new background, or change both in the same sentence (it is one scope: "background and its light") |
| Colour or grade | `change <element> to <colour hex and name>`, or `raise overall contrast and saturation slightly` | Brand colours as hex plus a plain name |
| Remove an element | `remove <element> and fill the area with <what is behind it>` | One element per round |
| Add a callout | `add one <colour> hand-drawn circle around <target> and one short arrow pointing at it from <direction>` | One callout per image |
| Resize or move the subject | not a narrow edit | It recomposes the image: new draft, or a final re-render with one added sentence (`prompt-blueprint.md`, Composition lock) |

"Make it pop", "more clickable", "better": ask which one scope they mean, offering the four common ones: bigger or bolder text, stronger expression, simpler background, more contrast. That question is part of the revision, not of the intake budget.

## Wording tests (A/B text)

The user wants to see several wordings: one batch on the fast tier, then promote the winner.

```json
{"label": "<slug>", "max_parallel": 3, "jobs": [
  {"id": "text-a", "endpoint_id": "openai/gpt-image-2.5/flare/edit", "est_cost_usd": 0.02,
   "input": {"prompt": "<pattern, text = \"NO OVEN\">", "image_urls": ["<current final url>"], "image_size": {"width": 1280, "height": 720}, "quality": "medium", "num_images": 1, "output_format": "png"}},
  {"id": "text-b", "endpoint_id": "openai/gpt-image-2.5/flare/edit", "est_cost_usd": 0.02,
   "input": {"prompt": "<pattern, text = \"10 MINUTES\">", "image_urls": ["<current final url>"], "image_size": {"width": 1280, "height": 720}, "quality": "medium", "num_images": 1, "output_format": "png"}}
]}
```

Sheet, gate, the user picks, then one `sunburst/edit` revision at full size with the winning words. The batch counts as one revision round. Platforms that offer their own thumbnail A/B test want separate final files: promote each wording the user wants to test, and never predict which will win.

## Language variants

One plate, one text-add edit per language (`prompt-blueprint.md`, Plate path). If the final was baked, make the plate first with one revision: `CHANGE ONLY: remove the text and continue the background behind it`. Then add each language's text to that plate, never to another language's version. Every language passes `thumbcheck.py text --lang <code>` and the letter-by-letter check on its own.

## Identity repair (the face drifts)

Use after one failed re-roll with a calmer expression. Two calls instead of one:

1. **Identity plate** on `fal-ai/nano-banana-2/edit` (the `character-identity` default in `routing-image.md`). Verified fields: `prompt` (3 to 50,000 chars, required), `image_urls` (array), `aspect_ratio` (`auto` default, `16:9`, `9:16`, `1:1`, `4:5` and others), `resolution` (`0.5K`, `1K` default, `2K`, `4K`), `num_images` 1 to 4, `output_format` `png` default, `seed`. Output `.result.images[].url`. About $0.08 per image at 1K, 1.5 times that at 2K (2026-09-19; confirm with `gm.py price fal-ai/nano-banana-2/edit`). This family takes `aspect_ratio` plus `resolution`, not `image_size`.
   ```json
   {"prompt": "<blueprint blocks with the identity lock, TEXT: none, NEGATIVE SPACE sentence kept>", "image_urls": ["<face url 1>", "<face url 2>"], "aspect_ratio": "16:9", "resolution": "2K", "num_images": 1, "output_format": "png"}
   ```
2. Gate the plate for likeness, then add the text with the Plate path edit. Compare the face before and after the text-add; if the text-add moved the face, rerun it once with the KEEP sentence listing the face first.

Still no likeness → more or better references (front-facing, sharp, even light), or hand off to `/genmedia-skills:character` to build a proper reference set. Do not keep rolling.

## Enlarge

- **The user wants 4K after approving a 2560x1440 final:** do not re-render (it would be a new picture). Upscale the approved file with `fal-ai/seedvr/upscale/image`. Verified fields: `image_url` (required, a single URL), `upscale_mode` `factor` (default) or `target`, `upscale_factor` 1 to 10 (default 2), `target_resolution` `720p`, `1080p` (default), `1440p`, `2160p`, `output_format` `jpg` (default), `png`, `webp`, `noise_scale`, `seed`. Output `.result.image.url` (singular). $0.001 per megapixel on 2026-09-19: a 3840x2160 result is about one cent.
  ```json
  {"image_url": "<final url>", "upscale_mode": "factor", "upscale_factor": 1.5, "output_format": "png"}
  ```
  Then `thumbcheck.py probe` for the real dimensions and Read the result at full size: an upscaler can soften or warp lettering, so compare the text with the source before delivering. Damaged → `topaz/upscale/image/precision` with `"model": "Text Refine"` (fields: `image_url`, `model`, `upscale_factor` 1 to 4, `output_format` `jpeg` or `png`, `face_enhancement`; about $0.08 per started 24 MP of output on 2026-09-19).
- **A real frame or photo is smaller than the render size** (a 1280x720 frame for a 2560x1440 final): enlarge it before using it as the plate, `upscale_factor` 2. Faces in the frame: `topaz/upscale/image/precision` with `"model": "Faces"`.
- Never upscale drafts to judge them, and never upscale before an edit: edits come first, enlarging last.
