# Reference photos: what to collect, what to reject

References carry more identity than any prompt. A few clean, varied images beat many similar ones. This file covers photos the user supplies (Workflow A) and the views you generate (Workflow B); the same standard applies to both.

## Consent first (real people)

Ask once, before reading more than the file names, before any upload and before any generation. One labelled question, in the user's language:

```text
These photos show a real person. Two things before I continue:
1. Do you have this person's consent to create and reuse AI images of them? (If it is you, just say so.)
2. To use the photos, I upload them to fal; uploaded files get a public link that anyone holding it can open until it expires.
[Yes, I have consent - continue]  [No / not sure - stop]
```

- Anything but a clear yes: stop. Offer an invented character instead.
- Record the yes with `init ... --real-person --consent`. The helper refuses `--real-person` without `--consent`.
- Refuse regardless of consent claims: public figures in deceptive, sexual or defamatory contexts; sexualised content of anyone who is or looks under 18.
- A user who says "this is me" counts as consent for themselves, not for other people in the frame. Crop others out or reject the photo.
- Invented characters, mascots and products skip this question.

## How many

| Purpose | Count | Why |
|---|---|---|
| Sheet for reference-conditioned generation (default) | **4 to 8 kept**, from up to about 12 candidates | Most routed editors take 3 to 16 images and blur identity when fed many similar ones. `resolve --max` picks from the sheet per call. |
| Minimum that still works | 1 sharp frontal `face` | Everything else can be generated from it (Workflow B steps 5 and 6), at lower fidelity than real photos. |
| LoRA training | 10 or more, 15 to 25 is a good range | Trainer schemas ask for "at least 10 images". See `references/training.md`. |
| Phota profile | 30 to 50 | The endpoint's own requirement. |

## The set to aim for

| # | View | Role | Notes |
|---|---|---|---|
| 1 | Front, head and shoulders, neutral expression, eyes to camera | `face` | The primary. Add it first. |
| 2 | Slight turn (15 to 30 degrees), relaxed or light smile | `face` | Gives the model depth cues for the nose and jaw. |
| 3 | Head to toe, standing, arms relaxed | `full-body` | Build, proportions, default outfit. |
| 4 | Three-quarter view (about 45 degrees) | `turnaround` | |
| 5 | Full profile | `turnaround` | Needed for side shots; skip if no shot will need it. |
| 6 | Open smile or laugh, close-up | `expression` | Teeth and smile lines are identity too. |
| 7 | A second strong expression or a different light | `expression` | Optional. |
| 8 | Alternative outfit or the signature garment alone | `outfit` | Optional; pass it only for shots that use it. |

## Quality bar for each photo

Accept:
- One person in frame, face unobstructed, eyes visible, in focus.
- Face at least about 400 px tall; short side of the image 1024 px or more when possible. Larger is fine; several routed models reject files above 10 MB, so downscale giant originals before `add-ref`.
- Even, soft light (window light, overcast, shade). Natural colour.
- Plain or uncluttered background. It does not need removal.
- Recent and mutually consistent: same hair length and colour, same facial hair, same glasses status across the set.
- PNG, JPG or WebP. Convert HEIC and others locally first. PNG with transparency: flatten onto a neutral background (one routed editor rejects alpha PNGs).

Reject (say which file and why, in one line each):
- Sunglasses, masks, hands or hair covering the face, heavy shadows across the eyes.
- Beauty filters, face-tuning, heavy makeup or costume that the character will not always wear, strong colour grading.
- Group photos, or a second face anywhere in frame.
- Extreme wide-angle selfies taken at arm's length (they distort the nose and jaw), extreme up or down angles.
- Motion blur, heavy noise, screenshots of screens, tiny crops, watermarks or text overlays.
- Near-duplicates (burst shots): keep one. The helper rejects byte-identical files by itself; you catch the look-alikes.
- Photos years apart mixed together, unless the user picks which age the character is.
- Anything the user would not want on a public URL.

Variety that helps: angle, expression, distance, light direction. Variety that hurts: different hairstyles, different ages, different facial hair, hats in some and not others.

## Non-human subjects

| Subject | `face` | `full-body` | `turnaround` | Extra care |
|---|---|---|---|---|
| Mascot or illustrated character | Front view of the head or the whole front | Whole figure, neutral pose | Side and back; a model sheet strip if one exists | Keep line style and palette identical across references; put them in `style`. |
| Product as character | Hero front view, label readable | The whole product on a plain background | Back and side, top if it matters | The brand must belong to the user. Label text survives best when it is large in at least one reference. |
| Pet or animal | Front of the face, eyes visible | Whole body, standing | Side view | Markings and their side go into the anchor. |

## When the user's photos fall short

Do not start an interview. State what is missing in one sentence and pick the path:

| Situation | Path |
|---|---|
| Only 1 to 3 usable photos | Keep them as `face` (and `full-body` if present). Generate the missing views with Workflow B step 5, passing the photos in `image_urls`. The first generated view needs the user's approval (Q2). |
| Many photos, all the same angle and expression | Keep the best 2. Generate the rest as above. |
| No frontal face at all | Ask for one frontal photo (this is inside Q-budget only if Q1 or Q2 was not needed; otherwise state it as a blocker and wait). `face_detection_error` on later jobs is the usual symptom of skipping this. |
| Photos contradict each other (long and short hair) | Choose the most recent look, write the anchor for it, tell the user which look you chose. |

## Storing

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" add-ref mara ./photos/front.jpg ./photos/slight-turn.jpg --role face
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" add-ref mara ./photos/standing.jpg --role full-body
python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" show mara
```

- Best first inside each role; order is priority in `resolve`.
- `add-ref` copies the files into the sheet and uploads nothing. The first `resolve` uploads only the references it picks.
- `show` lists missing files, references without a URL and whether a `face` exists. Fix warnings before the first generation.
