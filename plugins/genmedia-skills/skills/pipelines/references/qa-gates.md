# QA gates

A gate sits after every stage: look at what came back before the next stage spends money on top of it. A flawed keyframe costs cents to redo; the same flaw discovered after image-to-video, music and upscale costs the whole chain. `gm.py` and `pipeline.py` abbreviate the calls shown in SKILL.md; recipe numbers (A1, A6, ...) refer to `assembly.md`.

## The gate, in order

1. **Mechanical** (from the batch output, no tools): `counts` has no `failed`, `pending` or `not_submitted`; every job has `outputs` with a `path`; image jobs: no `true` in `result.has_nsfw_concepts` (fal returns a black image for a blocked one and still bills it; treat as a policy hit, never deliver it).
2. **Look.** One batched pass per stage, not one tool call per file per thought:
   - Images: Read each file.
   - Clips with ffmpeg: one contact sheet per clip, then Read the sheets:

     ```bash
     ffmpeg -hide_banner -loglevel error -i genmedia-output/<slug>/clip01_0.mp4 -vf "fps=1,scale=480:-2,tile=6x1" -frames:v 1 -update 1 genmedia-output/<slug>/qa/clip01_sheet.jpg
     ```

     One tile per second; use `tile=6x2` for clips up to 12 s. Add the exact last frame (A6) when the clip feeds another clip or must land on an end frame.
   - Clips without ffmpeg: a one-stage batch of `fal-ai/ffmpeg-api/extract-frame` jobs (`frame_type` `first`, `middle`, `last`; output `images[0]`; about $0.0002 per second of input on 2026-09-19), or `fal-ai/workflow-utilities/extract-nth-frame` (`frame_interval`, `max_frames`) for a denser sample. Read the downloaded frames.
   - Probe every clip and audio file (A1): duration, size, audio stream present or absent as planned.
3. **Verdict** per asset: `pass`, `re-roll` (completed but weak), or `fail` (error). Write it to the plan log.
4. **Repair** inside the budget below, one node at a time.
5. **Checkpoint**, if the plan declares one here: send the checkpoint message and stop. Otherwise continue.

Frames catch composition, identity and artifacts. They do not show motion quality. When motion is the risk (walk cycles, hands, liquids, camera moves) and the clip is about to be built on, ask a model one concrete question: `fal-ai/video-understanding` (`video_url`, `prompt`, optional `detailed_analysis`; about $0.01 per 5 s on 2026-09-19; output `result.output`), for example "Does the person's face or clothing change during the clip? Does any object appear or vanish? Answer per second." Treat the answer as a hint, not a verdict. Alternatives are in `routing-utility.md` (`understand-video`).

## What to check

| Asset | Pass when |
|---|---|
| Keyframe / still | Shows what the prompt asked; framing leaves room for the planned motion; palette, grade, character and wardrobe match the anchor; no mangled hands, faces or stray text; not black; pixel size equals the plan. |
| Product still | Shape, proportions, label text and colors equal the packshot (compare side by side); no invented claims, badges or logos. |
| Clip | First frame equals the keyframe; the move is the prompted one; identity and objects are stable to the last frame; no unplanned cut; duration and resolution equal the plan; with an end frame: last frame (A6) equals it. |
| Voice | Duration is plausible for the text (roughly 2 to 3 words per second) and fits the picture plan; file is not tiny or silent (`silencedetect`, below). You cannot hear: for names, numbers and any non-English script run one check with `fal-ai/audio-understanding` (`audio_url`, `prompt`: "Transcribe this exactly"; about $0.01 per 5 s on 2026-09-19) and compare with the script. Say at the checkpoint that you verified text, not tone. |
| Music | Length equals the request; not silent. Mood is the user's call at the checkpoint or delivery; music is mixed last so swapping it stays cheap. |
| Talking head | Probe: duration equals the audio chunk. Frames: mouth open and closed across tiles (not frozen), face stable, no second face. |
| Final | A1: duration equals the plan within 0.2 s, one video and one audio stream, planned size; first frame not black (it becomes the thumbnail); captions legible on an extracted frame; loudness measured when audio was mixed (A5). |

Cheap detectors (local, free), each prints nothing when clean:

```bash
ffmpeg -hide_banner -i genmedia-output/<slug>/clip01_0.mp4 -vf blackdetect=d=0.5:pix_th=0.10 -an -f null - 2>&1 | grep -o "black_start:[0-9.]* black_end:[0-9.]*"
ffmpeg -hide_banner -i genmedia-output/<slug>/clip01_0.mp4 -vf freezedetect=n=0.003:d=2 -an -f null - 2>&1 | grep -o "freeze_start: [0-9.]*"
ffmpeg -hide_banner -i genmedia-output/<slug>/vo_0.mp3 -af silencedetect=n=-50dB:d=1 -f null - 2>&1 | grep -o "silence_start: [0-9.]*"
```

A still keyframe animated with almost no motion trips `freezedetect`; that is a finding (the clip is a slideshow), not a false alarm.

## Re-roll and repair budgets

| Scope | Budget | Then |
|---|---|---|
| One node | 3 attempts in total, each different from the last | Stop, explain, ask how to proceed. |
| One stage | Re-roll up to a third of its jobs without asking | More than that failing QA means the approach is wrong (prompt pattern, model, reference). Revise the plan; do not grind. |
| Whole project | Re-roll and repair spend within 20 percent of the approved total | Beyond that it is a new plan version and needs approval. |
| Same flaw twice on one node | Change the model tier or restructure the prompt, not just the wording | |

What must change between attempts:

| Finding | Change |
|---|---|
| Off-style or off-palette still | Name the anchor's palette and grade explicitly; pass the anchor in `image_urls`; keep the seed out of it. |
| Identity or product drift in a clip | Shorter `duration`; simpler motion; add an end frame; or move to a reference-capable endpoint through `video` routing. |
| Wrong or excess motion | Rewrite the motion sentence to one move and one subject; say what stays still. |
| Unwanted speech or sounds under narration | `generate_audio` false. |
| Garbled on-image text | Remove text from the generation; add it in an editor or through `image` typography routing. |
| `content_policy` or a black image | Rewrite the flagged part plainly; never resend unchanged; never disable a safety checker. |
| `validation` from a queued job | Compare the input with the schema; typical causes are listed in `troubleshooting-pipelines.md`. |
| 5xx, timeout | Wait briefly, `--retry-failed` once; a second failure means another model (ask first if the user named this one). |

Mechanics:

- **Failed id**: edit that job's input in the stage template, `pipeline.py fill` again, then `gm.py batch --plan <plan> --retry-failed`. Only ids whose last request failed, was cancelled or has an unknown submit state are resubmitted. Everything else is resumed from the ledger for free.
- **Completed but weak id**: completed jobs are never rerun. Add a new job with a new id (`clip03-r2`, then `clip03-r3`) to the stage template and run it; point later stages at `"@clip03-r2"`. Both takes stay in the manifest; the plan log says which one was used.
- Never rerun a whole stage, never change the `label` to force fresh jobs, never delete ledger lines.
- Partial success is normal: continue QA and later stages with what landed when the missing node is not an input to them; report the rest.

## Checkpoint etiquette

- Show a numbered list: local path plus one line on what each asset shows and any doubt you have. Offer the gallery link for a side-by-side view.
- Accept partial answers ("1, 2 and 4 are fine, redo 3 with less fog"): redo only what was named, then show only the redone items.
- The approval is consumed by the step it gates. A later change to an approved asset reopens that checkpoint.
- Creative picks that are hard to reverse (hero variant, voice, character look) are always the user's. Reversible picks (which of two re-rolls, trim points, music level) are yours.
- You may recommend: say which you would pick and why in one line. Do not decide.

## Pre-delivery gate (mechanical, all must hold)

1. `pipeline.py manifest --label <slug>` exits 0, or every listed problem is explained in the delivery message (for example a superseded take that was cancelled).
2. The final file exists under `genmedia-output/<slug>/`, is registered (`pipeline.py add` or a ledger job), and its probe (A1) matches the plan's duration, size and audio expectation.
3. Every checkpoint declared in the approved plan version has an approval line in the plan log.
4. `plan.md` has no unfilled placeholders (`<...>`) and its status is updated (`delivered`).
5. No black first frame, no job left `pending`, no file delivered that failed its QA verdict.
6. Estimated spend (`gm.py ledger --label <slug> --sum`) is stated, and is within 20 percent of the approved total or covered by a newer approved version.
7. Safety: real-person assumption confirmed in the approved plan; no fabricated claims or third-party logos in the deliverable; synthetic presenter disclosed when it is an ad.
