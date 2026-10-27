# Video troubleshooting

Symptom -> likely cause -> the ONE thing to change next. Error types and billing rules live in [platform.md](platform.md) section 4-5; helper error kinds in [cli-contract.md](cli-contract.md). Field facts below were read from live schemas on 2026-09-19.

## 0. Before any re-render

- A re-render is a new job at full price. Add it to the running total and pass the cost gate again when the total crosses a threshold the user has not approved.
- At most 3 attempts per shot. Each attempt changes exactly one thing, so you learn what worked. Order of changes: prompt wording -> motion intensity -> duration -> seed (where the schema has one) -> start frame -> model tier.
- **Fix the still, not the video.** Wrong composition, wrong product shape, wrong face in frame one: repair the keyframe with `image` (cents), then animate again. Do not try to prompt a video model out of a bad start frame.
- Same flaw twice with different wording: the model cannot do it. Simplify the shot, split it, or move to another family; say so instead of trying a third phrasing.
- Tell the user what you saw on the frames and what you will change, in one line, before spending again.

## 1. Picture

| Symptom | Likely cause | Change |
|---|---|---|
| Face or product drifts away from the start frame by the end | too much motion, long duration, camera move too large | motion intensity "subtle"; shorten to 4-5 s; smaller camera amount; add "her face and hair stay exactly as in the first frame". Persistent: reference-to-video or Kling `elements` with 2-3 angles |
| Different person in every clip of a series | each clip generated from text | one approved keyframe per shot made from the same `character` references; or reference-to-video with the same `image_urls` every time |
| Almost nothing moves | prompt re-describes the still instead of motion; "subtle" taken literally; prompt rewriter softened it | lead with the action verb; name a visible start and end state; on Wan set `enable_prompt_expansion` false, on MiniMax `prompt_expansion_mode` "disabled" |
| Chaos, morphing limbs, melting background | too many actions or moving elements; "dynamic" on a busy set | one action; "background static"; simpler set in the keyframe; shorter clip |
| Camera move ignored or wrong | several moves asked; move buried at the end of the prompt | one move, second sentence of the prompt, with an amount; Kling: raise `cfg_scale` slightly |
| Jump or redraw in the first frames | prompt contradicts the start frame (different light, outfit, angle) | delete every scene description from an image-to-video prompt; keep motion only |
| End frame not reached, or a snap in the last frames | too much change between the two frames for the seconds ordered | longer duration, or an end frame closer to the start (edit the start frame instead of generating a new still); end the prompt with "ends exactly on the provided end frame, holding still" |
| Unwanted cuts inside the clip | Seedance cuts when the prompt reads like several scenes | "one continuous shot, no cuts"; remove scene changes from the prompt |
| Wanted cuts did not happen | single-shot wording | Seedance: timed beats with "Cut to ..."; Kling: `multi_prompt` |
| Garbled text, wrong logo | models do not render exact text | remove the text from the prompt, leave negative space, composite in post (`pipelines`) |
| Output cropped or letterboxed | Seedance and Kling image-to-video follow the start frame | regenerate or outpaint the keyframe in the target ratio (`image`); or reframe the finished clip (`video-recipes.md` section 7) |
| `aspect_ratio` had no effect | the endpoint ignores it (image-to-video) or the field name differs | check the schema; change the keyframe instead |
| Slow-motion look | model default for low-motion prompts | "real-time speed", state the action's duration ("pours for two seconds") |
| Flicker, boiling texture | fine repeating patterns, heavy grain in the keyframe | cleaner keyframe; less camera motion; Seedance `bitrate_mode` "high" helps compression artefacts only |
| Black or near-black clip, or a solid frame | safety block or decode failure | treat as a policy hit: do not deliver, do not resend unchanged; check the input image and prompt |
| Soft or low-detail result at 720p | expected at draft resolution | approve the motion first, then upscale (`video-recipes.md` section 10) rather than re-rendering at 1080p |

## 2. Sound and speech (native audio)

Frames cannot verify audio. Wrong words can be caught cheaply: `/genmedia-skills:audio` extracts the clip's track and transcribes it with Scribe v2 (under a cent; Scribe needs the audio file, not the mp4; without local ffmpeg it uses Wizper, which takes the mp4). Mispronunciation cannot: a transcript wrote Seedance 2.0's "merhala" as "Merhaba" (`platform.md` section 10). Pronunciation and voice quality need the user's ears: ask them to listen and say what you could not check.

| Symptom | Likely cause | Change |
|---|---|---|
| No audio track (`has_audio` false in `scripts/frames.py probe`) | audio switch off or named differently: `generate_audio` (Seedance, Kling), `audio` (Wan), `generate_audio_switch` (PixVerse); Kling O3 defaults to false | set the field the schema lists |
| Music although none was wanted | no sound plan in the prompt | write "no music" and name the ambience you want instead |
| Speech in English although the line was Turkish | Kling v3 speaks only Chinese and English and auto-translates | Wan 3.0 for the shot, or TTS from `audio` plus lipsync |
| Turkish sounds foreign or a sound is wrong (ş as s, "merhala") | the Seedance family did this to every Turkish line in a native listen | Wan 3.0 for the shot, or TTS plus lipsync |
| Line cut off or rushed | too many words for the seconds | about 2-3 words per second; shorten the line or lengthen the clip; "finishes speaking by second N" |
| Wrong person speaks | several faces, speaker not identified | name the speaker by a visible trait ("the woman in the red coat says ..."); one speaker per shot is safest |
| Mouth moves without the line, or mumbling | line not in quotes; stage directions mixed into the line | speaker + delivery, then the exact line in double quotes, nothing else inside the quotes |
| Clip will get voice-over later but has speech-like noise | audio left on without a plan | Kling: `generate_audio` false (also cheaper); Seedance: "ambience only, no speech, no music", or strip the track locally |

## 3. Lipsync and talking head

| Symptom | Likely cause | Change |
|---|---|---|
| `face_detection_error`, or mouth untouched | face small, turned away, covered, or cut by the frame | a source with a clear, mostly frontal face for the whole clip; talking head: a sharper portrait |
| Sync drifts or mouth smears on loud music | audio is a full mix | sync to the clean voice track only; add music afterwards in `pipelines` |
| Video ends before the audio, or loops oddly | lengths differ | `fal-ai/sync-lipsync/v3`: choose `sync_mode` (`cut_off`, `loop`, `bounce`, `silence`, `remap`); `fal-ai/latentsync`: `loop_mode`; or trim the audio to the clip |
| OmniHuman rejects the audio as too long (422) | 1080p allows under 30 s, 720p under 60 s | set `resolution` "720p"; longer scripts: split the audio at sentence breaks and make several clips |
| Wrong face talks in a group image | no speaker selection | OmniHuman `mask_url`: white over the speaker |
| Identity of a real person | consent not confirmed | stop and ask; see `platform.md` section 9 |

## 4. Jobs, inputs, limits

| Symptom | Cause | Do |
|---|---|---|
| `status:"pending"` after the helper's timeout | video renders often outlast one tool call (several minutes; longer at 1080p or in a queue) | `gm.py wait <endpoint_id> <request_id>`; repeat as needed. One status line to the user. Never resubmit |
| Tool call was killed, no output | the helper wrote the ledger line before polling | `gm.py ledger --tail 5`, then `gm.py wait` with that request |
| `submission state unknown` | submit ended without a request ID | check https://fal.ai/dashboard/requests before submitting again |
| Long `IN_QUEUE` | account concurrency (new accounts: 2 at once) | wait; cancelling and resubmitting loses the place and can bill twice |
| `validation` with `fields:[]` and a `hint` | runtime failure of a queued job; detail lost by the CLI | check each media input against the limits in `video-recipes.md` (seconds, MB, pixels, fps, format); probe with `scripts/frames.py probe`; re-encode; then rerun once |
| Seedance rejects a reference video | outside 1.8-30.2 s, under 24 fps or above 60, a side under 300 px, over 200 MB, not MP4/MOV | normalise locally (below), upload again |
| `file_download_error` | expired or private URL; an old `cdn_url` | upload the local file again |
| `content_policy_violation` on an image or video input | the media, not the prompt, was flagged | never resend unchanged; tell the user which input; a different model only when the content is clearly benign |
| `Schema fetch failed (429)` | catalog API rate limit (not a job failure) | wait 10-60 s and retry the free call; do not skip the schema check |
| Optional media field silently ignored | wrong field name for this family | compare with the schema's property list before every first call; see the field-name trap in SKILL.md |

Local normalisation with ffmpeg (free; each writes a new file, originals stay):

```bash
ffmpeg -i in.mov -t 15 -r 24 -vf "scale=-2:720" -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -movflags +faststart out.mp4   # format, fps, height, max length
ffmpeg -ss 1 -to 9 -i in.mp4 -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac cut.mp4                                         # keep seconds 1-9
ffmpeg -i in.mp4 -c:v copy -an silent.mp4                                                                                   # drop the audio track
ffmpeg -i in.mp4 -vn -ac 1 -ar 44100 voice.wav                                                                              # audio only, for lipsync
```

No local ffmpeg: `fal-ai/workflow-utilities/trim-video` and `fal-ai/workflow-utilities/scale-video` in [routing-utility.md](routing-utility.md) (always pass explicit start and end times).

## 5. When to stop

After three attempts on one shot, or when the running total would cross the confirmation threshold again, stop and offer choices instead of another try:

1. Keep the best take so far (name its flaw).
2. Simplify the shot (less motion, shorter, locked-off camera).
3. Change the ladder: fix the keyframe, or pin an end frame.
4. Change the model tier (say the price difference).
5. Split into two shots and cut them together with `pipelines`.
