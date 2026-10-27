# Tiers and costs

How to price the three tiers for Q1 and the outline card, and how to re-price before the clip stage. Every number here is a **dated hint (2026-09-19)** from `gm.py price ... --explain` and the models' public pricing text; rerun the command, never quote from this file without the date. `gm.py` and `explainer.py` abbreviate the calls shown in SKILL.md.

## 1. The three tiers

| | Animatic | Hybrid (default) | Full |
|---|---|---|---|
| Picture | one approved still per block, slow pan or zoom rendered locally | stills + image-to-video on the blocks marked `animate` (2-3 per minute) | image-to-video on every block |
| Paid stages | style key, keyframes, voice, music | the same + clips for the animated blocks | the same + clips for all blocks |
| Cost driver | stills and music: about a dollar per minute | animated seconds x clip price | total seconds x clip price |
| Checkpoints | CP1, CP2, CP3, CP4, final | + CP5 | + CP5, canary first |
| Upgrade path | any block can be animated later: `plan --stage clips --blocks <n>`; whole video: `approve --stage outline --tier hybrid` | raise or lower the number of animated blocks at CP4 (`visuals` with `animate`) | - |

An animatic is not a lesser product: it is every tier's draft. Its stills are the start frames of the clips, its narration and timing are final. Moving from animatic to hybrid or full later costs only the clips.

## 2. Turning `gm.py price --explain` into dollars

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price bytedance/seedream/v5/pro/text-to-image,bytedance/seedream/v5/pro/edit,fal-ai/gemini-3.1-flash-tts,alibaba/wan-3.0/image-to-video,elevenlabs/music/v2.5 --explain
python3 "${CLAUDE_SKILL_DIR}/scripts/explainer.py" status --slug <slug>
```

`status` gives the quantities (`blocks`, `stills`, `narration_chars`, `total_s`, `animated_s`, `music_minutes`; `measured: false` means seconds are still the plan, 10 s per block). Multiply by the price rows according to `unit`:

| `unit` in the price row | Seen on | Dollars |
|---|---|---|
| `units` with `pricing_text` | Seedream 5.0 Pro t2i and edit | the per-image figure in the text for an area up to 1536x1536 (1920x1080, 1080x1920 and 1536x1536 qualify) x `stills`; edit adds the per-reference figure for each reference after the first (mascot sheets) |
| `1000 characters` | TTS | `narration_chars` / 1000 x `unit_price`; audition = voices x sample characters (the plan prints it) |
| `seconds`, `needs_llms_txt: false` | Wan 3.0, H3 Max Turbo | clip models print only their **cheapest resolution**: take the figure for your resolution from `routing-video.md` or the row's `pricing_text` (`--explain`), x `animated_s` (hybrid) or `total_s` (full). Utilities: seconds of output x `unit_price` |
| `1000 tokens` with `pricing_text` | Seedance 2.5 | the per-second figure for your resolution in the text x seconds |
| `minutes` | ElevenLabs Music, auto-subtitle | **started** minutes x `unit_price` (`music_minutes`) |
| `compute seconds` | metadata probe, merge-videos, images-to-video, loudnorm | fractions of a cent per call; budget $0.01 each |
| `units`, text says "per hour ... rounded upwards" | forced alignment | one flat figure per call, whatever the length: align the whole voice track once, never per block |

Rules: two sources disagree → quote the higher. Pass the same figures to `plan` (`--price-per-image`, `--price-per-1k`, `--price-per-second`) so the run ledger carries them and `gm.py ledger --label <slug> --sum` matches your card. Say "about", round up, state that re-rolls are extra, and add a 20 percent reserve to the clip line in your own head before you call a tier affordable.

## 3. Worked estimate: 60 s, 6 blocks, Turkish narration of about 800 characters

Prices observed 2026-09-19, H3 re-priced 2026-10-01: Seedream 5.0 Pro $0.0675 per image (area up to 1536x1536; first reference free, $0.0045 per further reference); Gemini 3.1 Flash TTS $0.05 per 1000 characters (ElevenLabs v3 $0.10, xAI TTS $0.015); ElevenLabs Music $0.60 per started minute; Wan 3.0 image-to-video $0.05 / $0.10 / $0.20 per second at 480p / 720p / 1080p; Seedance 2.5 about $0.2646 / $0.5676 / $1.396 per second (US endpoint, re-priced 2026-10-21); H3 Max Turbo $0.025 / $0.04 / $0.08 per second at 480P / 768P / 1080P since the launch discount ended 2026-09-30, with the old half rate still billed on 2026-10-01; compose $0.0002 per output second; auto-subtitle $0.03 per minute; `veed/subtitles` $0.10 per minute with a one-minute minimum.

| Line | Quantity | Animatic | Hybrid (2 animated blocks) | Full |
|---|---|---|---|---|
| Style key | 1 image | $0.07 | $0.07 | $0.07 |
| Keyframes | 6 images, 1 reference | $0.41 | $0.41 | $0.41 |
| Voice audition | 3 voices x ~120 chars | $0.02 | $0.02 | $0.02 |
| Narration | 800 chars, Gemini TTS | $0.04 | $0.04 | $0.04 |
| Music bed | 1 started minute | $0.60 | $0.60 | $0.60 |
| Clips, Wan 3.0 720p | 0 s / 20 s / 60 s | - | $2.00 | $6.00 |
| Assembly | local ffmpeg (free; there is no fal route) | $0 | $0 | $0 |
| Captions | sidecar SRT | $0 | $0 | $0 |
| **Total, about** | | **$1.15** | **$3.15** | **$7.15** |

Same plan with other choices:

| Change | Effect on the total |
|---|---|
| No music | -$0.60 (animatic about $0.55) |
| ElevenLabs v3 voice (English default) | +$0.04 |
| Third animated block in hybrid | +$1.00 |
| Clips on Seedance 2.5 at 720p | hybrid about $12.50, full about $35.20 |
| Clips on Seedance 2.5 at 480p | hybrid about $6.45, full about $17.05 |
| Clips on H3 Max Turbo 768P (draft look, adds its own soundtrack that the render drops) | hybrid about $1.95, full about $3.55 at the post-discount $0.04/s |
| Clips on Wan 3.0 at 1080p | clip line doubles: full about $13.15 |
| Burned-in captions | +$0.03 (auto-subtitle) or +$0.10 (`veed/subtitles` with our SRT) |
| Mascot sheet of 3 references on every keyframe | +6 x 3 x $0.0045 = +$0.08 |
| One keyframe re-roll / one 10 s Wan clip re-roll | +$0.07 / +$1.00 |

A one-minute full tier costs dollars, not cents, and on the premium clip model tens of dollars. That is why the tier is the user's choice (Q1) and the clip stage has its own checkpoint.

## 4. Longer videos (same assumptions, Gemini voice, music on, Wan 3.0 720p, hybrid = one block in three animated)

| Length | Blocks | Animatic | Hybrid | Full | Full on Seedance 2.5 720p |
|---|---|---|---|---|---|
| 1 min | 6 | about $1.15 | about $3.15 | about $7.15 | about $35.20 |
| 2 min | 12 | about $2.20 | about $6.20 | about $14.20 | about $70 |
| 3 min | 18 | about $3.25 | about $9.25 | about $21.25 | about $105 |
| 5 min | 30 | about $5.35 | about $15.35 | about $35.35 | about $176 |

Per extra minute: stills $0.41, voice $0.04, music $0.60, plus $6.00 for fully animated Wan 720p seconds. Wall-clock matters too: 30 clips at an account concurrency of 2 can take an hour; tell the user before starting, and remember the batch is resumable.

## 5. Where the estimate moves after CP3

- **Measured seconds replace planned seconds.** With `--fit audio` blocks shrink and grow by a second or two. Rerun `status`: `animated_s` and `total_s` are now real. The clip line is `sum of ordered seconds x price`; `plan --stage clips --price-per-second <p>` prints exactly that as `est_total_usd`, including clamping to the model's range (a 3 s block on a model whose minimum is 5 s is billed 5 s).
- **Music minutes jump at 60 s boundaries.** 59 s → one minute, 61 s → two. If the total lands just over a boundary, offer the choice: trim a block's tail by rewriting one sentence, or pay the extra $0.60, or drop the bed for the last seconds (the render fades the bed out at the end anyway; a bed shorter than the video is looped by the local render).
- **State the clip total in the CP4 message**, even when the user already chose the tier: the approval of keyframes is also the approval to spend the largest line.
- A materially higher total than CP1 showed (more than 20 percent) is a new estimate and needs a new yes.

## 6. Cost gate and cheap-first order

Thresholds come from `gm.py preflight` → `config` (defaults: announce at $0.50, confirm at $2).

| Stage | Typical 60 s cost | Gate |
|---|---|---|
| Style key + audition | under $0.10 | runs after CP1 without another question |
| Narration | under $0.10 | runs after CP2 |
| Keyframes | about $0.41 | runs after CP3; announce if the remaining plan is between the thresholds |
| Clips | $2 and up | explicit yes at CP4 with the re-priced number; canary before 4 or more clips on a new endpoint |
| Music, captions | under $1 | announce |

CP1 already carries the whole-plan confirmation for the chosen tier; later gates only fire when the number moved or a stage alone crosses the confirm threshold. Never reach a lower number by silently changing a model the user named, the resolution they asked for, or the number of animated blocks they approved: offer it, in one line.

## 7. Saving money without hurting the result

1. Draft the whole video as an animatic; animate only after the user has watched it. Most script and pacing changes happen here, at cents.
2. Animate fewer, better blocks. A still with a slow move under a good sentence beats a clip with meaningless motion.
3. 720p clips, scaled to 1920x1080 by the local render (lanczos). Native 1080p doubles the Wan price and more than doubles Seedance's. For a quality finish of a premium film, one upscale of the final (`/genmedia-skills:video`) beats rendering every clip at 1080p.
4. Redo single blocks (`--blocks <n>`); identical re-plans resume for free. Never re-run a whole stage to fix one block.
5. One forced-alignment call for the whole voice track, if word-exact captions are needed at all; the block-timed SRT is free and usually enough.
