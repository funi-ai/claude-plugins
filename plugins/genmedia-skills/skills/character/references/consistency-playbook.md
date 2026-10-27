# Consistency playbook

How to keep a saved character recognisable: building the reference sheet, filling each endpoint's reference fields, the escalation ladder, drift QA, video hand-off and scenes with several characters. Endpoint facts were read from the live schemas on 2026-09-19; re-read the schema before the first paid call (SKILL.md, Discovery guardrail).

## 1. Reference budget per endpoint

Pass `--max` to `resolve` with the number in the last column. "Documented" means the schema states it; everything else is this skill's operating cap.

| Endpoint | Field for references | Documented limit | Cites references as | `--max` |
|---|---|---|---|---|
| `fal-ai/nano-banana-2/edit` | `image_urls` | none stated | plain language ("the woman in the first image") | 6 (up to 8) |
| `fal-ai/nano-banana-pro/edit` | `image_urls` (required) | none stated | plain language | 6 (up to 8) |
| `bytedance/seedream/v5/pro/edit` | `image_urls` (required) | 10; with more, only the **last** 10 are used | plain language | 8 to 10 |
| `openai/gpt-image-2.5/flare/edit` | `image_urls` (required), optional `mask_url` | 16 | plain language | 8 to 16 |
| `alibaba/qwen-image-3/edit` | `image_urls` (required) | 1 to 3; 384 to 2048 px per side; 10 MB each; no alpha PNG | "image 1", "image 2", "image 3" | 3 |
| `fal-ai/qwen-image-edit-2511-multiple-angles` | `image_urls` (required) | the one image to re-render | not applicable (no free prompt; `additional_prompt` is optional) | 1 |
| `fal-ai/phota/edit` | `image_urls` (required) plus `profile_ids` | 10; extra images are ignored | `[[profile_id]]` in the prompt | 4 |
| `bytedance/seedance-2.5/us/reference-to-video` | `image_urls` | 30 images, 30 MB each, 50 files in total | `@Image1`, `@Image2` | 4 to 6 |
| `fal-ai/kling-video/o3/pro/reference-to-video` | `elements[]` = `{frontal_image_url, reference_image_urls}`; `image_urls` for style | 1 to 3 `reference_image_urls` per element; 10 MB, 300 px minimum side, aspect 0.4 to 2.5; 4 elements plus images in total when a video element is used | `@Element1`; style images `@Image1` | 4 per character |
| `alibaba/wan-3.0/reference-to-video` | `reference_image_urls` | 10 | "Image 1" | 4 to 6 |

Why the operating caps are below the documented limits: reference-conditioned models blend what they receive. A second near-identical face adds nothing; a weak or off-style image pulls the result towards it. Spend the budget on different information (front face, angle, body, expression), which is what the round-robin in `resolve` does.

Order matters. `urls[0]` is the primary face. Where an endpoint truncates (Seedream keeps the last 10, Phota the first 10), staying at or under the limit is the only safe choice.

## 2. Building the reference sheet (Workflow B steps 5 and 6)

Inputs: the approved hero (`face`, r1) and its URL. Every job gets the hero URL in `image_urls`. Write the plan to `.genmedia/tmp/<handle>-sheet.json` and run it with `gm.py batch --plan`; plan format and resume rules are in `references/cli-contract.md`.

Batch 1, editor `fal-ai/nano-banana-2/edit` (`resolution` "1K", `num_images` 1, `aspect_ratio` "3:4" for body shots and "1:1" for close-ups):

| Job id | Prompt core (append the anchor and the style notes) | Role |
|---|---|---|
| `fullbody` | Full-body photo of the same character, head to toe in frame, standing relaxed, arms at the sides, facing the camera, plain light-grey studio background, even soft light | `full-body` |
| `face-turn` | Head-and-shoulders portrait of the same character turned about 30 degrees to the left, looking at the camera, neutral expression, same background and light | `face` |
| `expr-smile` | Close-up of the same character with a wide natural smile showing teeth, same hair and skin marks | `expression` |
| `expr-focus` | Close-up of the same character with a serious, focused expression, brows slightly drawn | `expression` |

Plan file for batch 1 (add `face-turn` and `expr-focus` the same way; outputs land in `genmedia-output/mara-sheet/<id>_0.png`, URLs in `jobs[].outputs[].url`):

```json
{"label": "mara-sheet", "jobs": [
  {"id": "fullbody", "endpoint_id": "fal-ai/nano-banana-2/edit", "est_cost_usd": 0.08,
   "input": {"prompt": "Full-body photo of the same character, head to toe in frame, standing relaxed, arms at the sides, facing the camera, plain light-grey studio background, even soft light. <anchor> <style>",
             "image_urls": ["<hero url>"], "aspect_ratio": "3:4", "resolution": "1K", "num_images": 1}},
  {"id": "expr-smile", "endpoint_id": "fal-ai/nano-banana-2/edit", "est_cost_usd": 0.08,
   "input": {"prompt": "Close-up of the same character with a wide natural smile showing teeth, same hair and skin marks. <anchor> <style>",
             "image_urls": ["<hero url>"], "aspect_ratio": "1:1", "resolution": "1K", "num_images": 1}}
]}
```

Batch 2 goes into the same plan file later (same `label`, new job ids; finished ids are answered from the ledger, not resubmitted), for example `{"id": "turn-90", "endpoint_id": "fal-ai/qwen-image-edit-2511-multiple-angles", "est_cost_usd": 0.04, "input": {"image_urls": ["<fullbody url>"], "horizontal_angle": 90, "vertical_angle": 0, "zoom": 5}}`.

Batch 2, after `fullbody` passed QA, camera orbit with `fal-ai/qwen-image-edit-2511-multiple-angles` (input: `image_urls` = the full-body URL, `vertical_angle` 0, `zoom` 5; no prompt needed):

| Job id | `horizontal_angle` | Role |
|---|---|---|
| `turn-45` | 45 | `turnaround` |
| `turn-90` | 90 (right side) | `turnaround` |
| `turn-180` | 180 (back) | `turnaround` |

- The orbit endpoint invents what the source does not show. Check the back view against the anchor (hair length, emblem placement); discard it rather than keep a wrong back.
- Orbit output is billed per megapixel and keeps the input size unless `image_size` is set.
- If an orbit view softens the face, regenerate that view with the editor instead ("the same character seen in full profile from the right side") and keep the orbit result only for body geometry.
- Optional, for the user to look at: one strip with four views on `fal-ai/nano-banana-2/edit`, `aspect_ratio` "4:1" ("character turnaround sheet: front, three-quarter, side and back view of the same character, identical outfit and proportions, plain background"). A strip is a weak reference (each view is small); store it as `turnaround` only when the endpoint budget is 3 or fewer.
- Keep 4 to 8. Discard without asking: anything that fails drift QA, near-duplicates, views no planned shot needs.

Store each keeper with its URL so nothing is uploaded again:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" add-ref mara ./genmedia-output/mara-sheet/fullbody_0.png --role full-body --cdn-url "<url from the batch result>"
```

## 3. Escalation ladder

Climb one rung per failed QA, cheapest first. Stop as soon as a result passes. At most 3 paid attempts per shot; then report what still drifts and offer the next rung.

| Rung | Change | Typical symptom it fixes | Cost |
|---|---|---|---|
| 1. Tighten the anchor | Name the traits that drifted with concrete words and their side; add a "Keep identical" line listing them; move any shot variable out of the anchor; remove adjectives that invite beautifying ("stunning", "perfect skin") | Eye or hair colour off, marks missing, age shifts, face gets prettier and more generic | free |
| 2. Add or re-role references | Add the missing angle or expression; put the cleanest frontal close-up first; `drop-ref` low-resolution, off-style or contradictory images; for an outfit shot pass `--roles face,outfit,full-body` | Wrong face from the side, profile shots drift, outfit bleeds into every shot, body proportions change | one sheet shot |
| 3. Stronger multi-reference model | Same references and prompt on `bytedance/seedream/v5/pro/edit`, then `openai/gpt-image-2.5/flare/edit` (more references, optional mask) or `fal-ai/nano-banana-pro/edit` (2K to 4K). Never swap away from a model the user named without saying so | Identity holds in close-ups but breaks in wide or busy scenes; small faces | price difference of the model |
| 4. Lock frames (video) | Generate and QA a still of the exact first frame, pass it as the start frame; for shots that turn or end on the face, also an end frame; shorten the clip; reduce motion near the face | Face morphs over time, identity lost after a turn, wardrobe changes mid-clip | one still per clip |
| 5. Train | Phota profile or LoRA (`references/training.md`). Always confirm cost. Worth it for long-running characters and large image volumes, not for a single campaign image | Likeness never exceeds "similar person"; hundreds of images needed | several dollars plus dataset work |

Extra moves that are not rungs:
- Small face in a wide shot: generate at 2K, or generate a tighter shot and outpaint.
- One wrong detail in an otherwise good image (mole on the wrong side, missing earring): edit that image with the same editor and the face reference, one instruction, rather than rerolling.
- Fix the `seed` where the endpoint returns one to test a prompt change in isolation.

## 4. Drift QA checklist

Open the result and the primary `face` reference (and the `full-body` reference for body shots) with the Read tool. Compare in this order; stop at the first clear miss.

| Area | Check |
|---|---|
| Face | Face shape and jaw, eye colour and shape, brow thickness, nose length and width, lip shape. Would a stranger say "same person"? |
| Hair | Colour, length, texture, parting side, hairline. Facial hair as in the anchor. |
| Marks | Every mole, scar, freckle pattern, tattoo or emblem in the anchor is present, on the correct side, not mirrored. |
| Build and age | Proportions, height impression, apparent age within the anchor's range. |
| Signature items and outfit | Present when the anchor says always; outfit as the shot line says; no stray logos or text. |
| Artefacts | Hands and fingers, extra limbs, asymmetrical eyes, waxy skin, duplicated character in the background. |
| Safety | Black frame, or `has_nsfw_concepts` true: not a result (`references/platform.md` section 3). |
| Video keyframes | Check the first frame, the middle and the last frame (extract them, or view the clip's frames); identity must hold at all three. |

Verdicts: pass (deliver), soft miss on a variable (outfit colour, background): fix the shot line and rerun once; hard miss on identity: climb the ladder. Tell the user the truth in the summary line ("hair parting differs slightly from the sheet") instead of overselling.

## 5. Hand-off to `image` and `video`

The contract is always the same three values from `resolve`: `description` (anchor), `style`, `urls` (plus `legend` for numbered citations).

Stills (any multi-reference editor): `image_urls` = `urls`, prompt as in SKILL.md Workflow C step 3. For `alibaba/qwen-image-3/edit` write "the woman from image 1" and keep to 3 URLs.

Video, in order of preference:

1. **First-frame lock.** Make the still of the opening frame with the sheet (QA it), then give `video` that file or URL as the start frame for its image-to-video default. The motion prompt describes movement only; do not re-describe the face. Start-frame field names differ per family (`image_url`, `start_image_url`); the `video` skill owns that mapping.
2. **Reference-to-video** when the shot cannot start on a prepared still (character enters the frame, several cuts):
   - `bytedance/seedance-2.5/us/reference-to-video`: `image_urls` = `urls`; write "@Image1 is Mara's face, @Image2 her full body" and then the action, using the `legend` indexes. Set `duration` explicitly; `auto` makes the cost unknowable.
   - `fal-ai/kling-video/o3/pro/reference-to-video`: one element per character: `frontal_image_url` = the `face` URL, `reference_image_urls` = 1 to 3 of the other URLs (`full-body`, `turnaround`; the schema asks for at least one, so a face-only sheet needs one more view first); cite `@Element1`. Optional `start_image_url` and `end_image_url` combine rung 4 with elements.
   - `alibaba/wan-3.0/reference-to-video` (budget): `reference_image_urls` = `urls`; cite "Image 1".
3. Both: lock the first frame and pass elements or references for what appears later in the clip.

Video prices are per second or per token and reach dollars per clip quickly; the cost gate and the keyframe-approval checkpoint belong to `video`. Hand over the anchor, the URLs and the QA-passed still, not a finished command.

## 6. Several characters in one scene

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" resolve mara bolt --max 6
```

- `--max` is shared evenly; each character gets face first. `characters[].indexes` tells you which positions in `urls` belong to whom.
- Bind every character to its images in the prompt, by index or order: "The woman from images 1 to 3 is Mara: <anchor>. The robot from images 4 to 6 is Bolt: <anchor>." Then one shot line that places them: who is left and right, who is nearer, who looks at whom.
- Give each character a distinguishing position or action; identical poses invite feature swapping.
- Two characters work with every routed editor. Three or more: use `openai/gpt-image-2.5/flare/edit` (16 references) or `bytedance/seedream/v5/pro/edit` (10), 3 references each, and expect a retry.
- Fallback when faces blend: generate the scene with character A only, leaving space for B, QA it, then run a second edit that adds B with B's references plus the scene image. One identity per pass.
- Kling O3: one element per character (`@Element1`, `@Element2`). Seedance: keep each character's images contiguous and cite them by number.
- Run drift QA per character. A scene passes only when every character passes.

## 7. Symptoms to cause

| Symptom | Likely cause | First fix |
|---|---|---|
| Result looks like a generic attractive version of the character | Beautifying adjectives; too few face references; prompt longer on scene than on identity | Rung 1, then add the angled `face` reference |
| Same pose and expression in every shot | Only neutral references; pose words in the anchor | Add `expression` references; clean the anchor |
| Default outfit appears although the shot names another | `full-body` reference dominates | `--roles face,expression,outfit`, leave `full-body` out for that shot |
| Mirrored marks or parting | Model flipped a side view; ambiguous anchor | State the side from the character's point of view; add the matching profile reference |
| Style drifts (photo becomes illustration) | Style missing from the prompt; mixed-style references | Always append `style`; drop off-style references |
| `file_download_error` | Expired or unreachable `cdn_url` | `resolve --refresh`, resubmit once |
| Character duplicated in the scene | The reference strip shows several views and the model copied them | Do not pass a multi-view strip to scene shots; use single-view references |
