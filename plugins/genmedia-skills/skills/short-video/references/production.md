# Production: from the approved beat sheet to clips

Three complete staged productions as `gm.py batch` plans, plus chaining and talking-head chunking. Every endpoint below was active and every field was read from the live OpenAPI schema on **2026-09-19**. It is a dated cache: repeat the Discovery guardrail of SKILL.md before spending. `gm.py`, `pipeline.py`, `frames.py` and `audiokit.py` abbreviate the quoted calls shown in SKILL.md. Plan keys, `"@job"` references, resume and `--retry-failed`: `cli-contract.md`. Cutting, mixing, captions, overlays: `finishing.md`.

## 1. From beats to shots to nodes

1. **Shots.** Walk the beat sheet. A cut, a new place or a new subject starts a shot. Beats that continue one another without a cut are ONE shot (timed ranges in one prompt). A shot longer than the model maximum becomes a chain (section 6).
2. **Ordered duration** per shot = the beat time rounded UP to what the model accepts, never below its minimum. The cut trims the surplus from the head or tail, keeping the hold. Put the ordered seconds, not the beat seconds, in the estimate.

| Model (role) | Start / end field | `duration` | `resolution` | Audio switch | Must set |
|---|---|---|---|---|---|
| `bytedance/seedance-2.5/us/image-to-video` (quality) | `image_url`* / `end_image_url` | string `"4"`-`"30"` (default `"auto"`) | `480p`, `720p`, `1080p` | `generate_audio` (default true, same price) | `duration` |
| `alibaba/wan-3.0/image-to-video` (value, short beats) | `start_image_url`* / `end_image_url` | integer 2-30 (default 5) | `480p`, `720p`, `1080p` (default `1080p`) | `audio` (default true) | `resolution`, `enable_prompt_expansion: false` |
| `minimax/h3-max-turbo/image-to-video` (draft) | `image_url` / `end_image_url` (either may stand alone) | integer 5-15 | `480P`, `768P`, `1080P` (uppercase) | none: a soundtrack is always made | `prompt_expansion_mode` (required; `"disabled"`) |

3. **Nodes.** Ids are unique in the project: `vo`, `kf01`..., `d01`... (drafts), `clip01`..., `music`, `sfx01`, `stt`, `cut`, `final`. A re-roll gets a new id (`clip03-r2`). One label for all stages.
4. **Stage files** under `.genmedia/projects/<slug>/`: `stage-1a-voice-anchor`, `stage-1b-keyframes`, `stage-2-draft`, `stage-3-clips`, later `stage-4-...` for chains and utilities. Templates end in `.tmpl.json`; `pipeline.py fill` writes the `.json` that `gm.py batch` runs.
5. **Keyframe size**: `{"width": 1080, "height": 1920}` for 9:16 (`{"width": 1920, "height": 1080}` for 16:9): inside the keyframe model's lower price tier (area up to 1536x1536). Image-to-video follows the keyframe's shape; the clip comes back near 720x1280 at the 720p tier. Sizes and frame rates differ slightly between models: always normalize before the cut (`finishing.md` S2).

Price hints on 2026-09-19, H3 re-priced 2026-10-01, Seedance 2026-10-21 (US endpoint), per ordered second, confirm with `gm.py price ... --explain`: Seedance 2.5 about $0.26 (480p) / $0.57 (720p) / $1.40 (1080p); Wan 3.0 $0.05 / $0.10 / $0.20; H3 Max Turbo $0.025 (480P) / $0.04 (768P) since the launch discount ended 2026-09-30, with the old half rate still billed on 2026-10-01.

## 2. Production A: faceless narrated b-roll (F5, 30 s, 9:16)

Brief: "a short video about cold brew". Script, 57 words (budget 58): *Cold brew is not iced coffee. Iced coffee is brewed hot, then cooled. Cold brew never meets heat. Coarse grounds sit in cold water for sixteen hours. Time does the work that heat usually does. The result is smoother, less bitter, and stronger than it tastes. Strain it, dilute it one to one, and pour over ice.* Seven sentences, seven shots. `<STYLE>` below stands for the project's style string plus negatives, pasted verbatim (`craft.md` section 2).

Stage 1a, voice and anchor keyframe (independent, one plan, no fill needed):

```json
{"label": "cold-brew-short", "max_parallel": 2, "jobs": [
  {"id": "vo", "endpoint_id": "fal-ai/elevenlabs/tts/eleven-v3", "est_cost_usd": 0.03,
   "input": {"text": "Cold brew is not iced coffee. Iced coffee is brewed hot, then cooled. Cold brew never meets heat. Coarse grounds sit in cold water for sixteen hours. Time does the work that heat usually does. The result is smoother, less bitter, and stronger than it tastes. Strain it, dilute it one to one, and pour over ice.", "voice": "Rachel", "stability": 0.5}},
  {"id": "kf01", "endpoint_id": "bytedance/seedream/v5/pro/text-to-image", "est_cost_usd": 0.07,
   "input": {"prompt": "Macro, slightly high angle of a heavy glass of black cold brew on a walnut counter, a thin stream of cream just touching the surface, the glass fills the lower two thirds, clean dark area in the upper third for a title. Soft window light from the left at 3200 K. Vertical 9:16 composition. <STYLE>", "image_size": {"width": 1080, "height": 1920}, "num_images": 1, "output_format": "png"}}
]}
```

Stage 1b, six keyframes edited from the anchor (template; `image_urls` puts the anchor first so its look wins):

```json
{"label": "cold-brew-short", "max_parallel": 6, "jobs": [
  {"id": "kf02", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Same counter, same light and colour grade as the first image. Close-up of a pour-over cone above a glass full of ice, a stream of hot coffee frozen mid-pour, steam rising. <STYLE>", "image_urls": ["@kf01"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}},
  {"id": "kf03", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Same counter, same light and colour grade as the first image. Eye-level shot of a tall glass jar being filled with clear cold water from a jug at the frame edge, condensation on the glass, no steam. <STYLE>", "image_urls": ["@kf01"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}},
  {"id": "kf04", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Same counter, same light and colour grade as the first image. Macro through the jar wall: coarse coffee grounds sinking slowly through cold water, amber clouds spreading. <STYLE>", "image_urls": ["@kf01"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}},
  {"id": "kf05", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Same kitchen and colour grade as the first image, at night: the sealed jar alone on the counter, blue 6500 K moonlight from the window, liquid half dark. <STYLE>", "image_urls": ["@kf01"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}},
  {"id": "kf06", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Same counter, same light and colour grade as the first image. Close-up of dark coffee straining through a cloth filter into a carafe, a thin steady stream. <STYLE>", "image_urls": ["@kf01"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}},
  {"id": "kf07", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Same counter, same light and colour grade as the first image. Hero shot of a glass full of ice as dark cold brew reaches the rim, centred in the lower two thirds, calm clean area above. <STYLE>", "image_urls": ["@kf01"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}}
]}
```

Measure and caption the voice (`finishing.md` S1, C1). Say it runs 28.2 s with sentence starts at 0.0, 2.0, 5.5, 8.0, 12.5, 16.5, 22.5: beats move to those times (2.0, 3.5, 2.5, 4.5, 4.0, 6.0 and 7.5 s to the end at 30.0); ordered durations become 5, 5, 5, 5, 5, 6, 8 on the draft model (minimum 5) and 2, 4, 3, 5, 4, 6, 8 on the clip models. **Checkpoint A.**

Stage 2, draft pass (all seven shots; two shown, the rest differ only in id, prompt and keyframe):

```json
{"label": "cold-brew-short", "max_parallel": 7, "jobs": [
  {"id": "d01", "endpoint_id": "minimax/h3-max-turbo/image-to-video", "est_cost_usd": 0.13,
   "input": {"prompt": "Locked-off macro. 0-2 s: the cream stream hits the coffee and blooms into slow swirling clouds. No cuts, no text. <STYLE>", "image_url": "@kf01", "duration": 5, "resolution": "480P", "prompt_expansion_mode": "disabled"}},
  {"id": "d07", "endpoint_id": "minimax/h3-max-turbo/image-to-video", "est_cost_usd": 0.2,
   "input": {"prompt": "Slow push-in, 8% closer over 6 s. Cold brew fills the glass over the ice, the ice shifts and settles. The last 1.5 s hold completely still. No cuts, no text. <STYLE>", "image_url": "@kf07", "duration": 8, "resolution": "480P", "prompt_expansion_mode": "disabled"}}
]}
```

QA sheets, mute the drafts, rough cut against the voice (`finishing.md` S2-S6). **Checkpoint B.** Stage 3, quality clips plus music; 2-3 s beats go to the value model (tie-breaker 4), audio off because a voice goes on top:

```json
{"label": "cold-brew-short", "max_parallel": 8, "jobs": [
  {"id": "clip01", "endpoint_id": "alibaba/wan-3.0/image-to-video", "est_cost_usd": 0.2,
   "input": {"prompt": "Locked-off macro. The cream stream hits the coffee and blooms into slow swirling clouds. No cuts, no text. <STYLE>", "start_image_url": "@kf01", "duration": 2, "resolution": "720p", "audio": false, "enable_prompt_expansion": false}},
  {"id": "clip02", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 2.3,
   "input": {"prompt": "Locked-off close-up. Hot coffee streams onto the ice, steam rises and drifts right, one ice cube cracks and drops. No cuts, no text. <STYLE>", "image_url": "@kf02", "duration": "4", "resolution": "720p", "generate_audio": false}},
  {"id": "clip03", "endpoint_id": "alibaba/wan-3.0/image-to-video", "est_cost_usd": 0.3,
   "input": {"prompt": "Locked-off. Clear cold water rises in the jar, small bubbles cling to the glass. No steam, no cuts, no text. <STYLE>", "start_image_url": "@kf03", "duration": 3, "resolution": "720p", "audio": false, "enable_prompt_expansion": false}},
  {"id": "clip04", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 2.9,
   "input": {"prompt": "Imperceptible push-in, 5% closer over 5 s. Coarse grounds sink through the water, amber clouds unfold and drift. No cuts, no text. <STYLE>", "image_url": "@kf04", "duration": "5", "resolution": "720p", "generate_audio": false}},
  {"id": "clip05", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 2.3,
   "input": {"prompt": "Locked-off. Time passes: the blue moonlight slides across the counter and warms into 3200 K morning light while the liquid in the jar darkens. No cuts, no text. <STYLE>", "image_url": "@kf05", "duration": "4", "resolution": "720p", "generate_audio": false}},
  {"id": "clip06", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 3.4,
   "input": {"prompt": "Slow lateral drift to the right, 10% of frame width over 6 s. Dark coffee runs through the cloth in a steady stream, the carafe fills. No cuts, no text. <STYLE>", "image_url": "@kf06", "duration": "6", "resolution": "720p", "generate_audio": false}},
  {"id": "clip07", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 4.5,
   "input": {"prompt": "Slow push-in, 8% closer over 6 s. Cold brew fills the glass over the ice, the ice shifts and settles. The last 1.5 s hold completely still. No cuts, no text. <STYLE>", "image_url": "@kf07", "duration": "8", "resolution": "720p", "generate_audio": false}},
  {"id": "music", "endpoint_id": "elevenlabs/music/v2.5", "est_cost_usd": 0.6,
   "input": {"prompt": "90 BPM, felt piano and soft brushed percussion, warm, unhurried, no vocals, no strong melody, leaves room for a narrator", "music_length_ms": 30000, "force_instrumental": true}}
]}
```

- Canary: eight paid jobs, so run a one-job plan with `clip02` first, QA it, then the full plan (the id resumes, it is not paid twice).
- Cost math (2026-09-19, H3 at the 2026-10-01 rate, Seedance at the 2026-10-21 US rate): voice 310 characters x $0.10/1000 = $0.03; keyframes 7 x about $0.07 = $0.49; drafts 39 s x $0.025 = $0.98; Seedance 27 s x $0.5676 = $15.33; Wan 5 s x $0.10 = $0.50; music $0.60; word timings under $0.01. About $17.95 plus the finish (`finishing.md` section 5). Value tier (all seven shots on Wan at 720p, 32 s): clips $3.20, total about $5.30. Draft-only (H3 at 768P as the final picture, 39 s x $0.04): about $2.70.
- Turkish narration: swap `vo` for `fal-ai/gemini-3.1-flash-tts` with `"prompt"` (not `text`), `"language_code": "Turkish (Turkey)"`, `"voice": "Kore"`, `"style_instructions": "Warm, lively narrator, natural conversational pace, short pauses between sentences"`, `"output_format": "mp3"`. Budget 1.7 words per second (`platform.md` section 10); that rate assumes a natural pace, and "unhurried" read at 1.2 to 1.4.
- Narration longer than the TTS limit (5000 characters on Eleven v3) does not occur in short-form; for per-sentence re-rolls use `audiokit.py chunk` (section 7) and `audiokit.py concat`.

## 3. Production B: before / after through first + last frame (F7, 8 s, 9:16)

The user's photo of the empty room is uploaded and registered as `@before` (SKILL.md Workflow step 5). Look at it first: if it is not vertical, the first keyframe recomposes it. Stage 1a, the "before" keyframe in the target shape:

```json
{"label": "room-makeover", "max_parallel": 1, "jobs": [
  {"id": "kf-before", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "The same room as the first image, same camera position, same walls, windows and floor, framed as a vertical 9:16 wide shot. Empty and unfurnished, flat overcast daylight at 6000 K, drained colour. <STYLE>", "image_urls": ["@before"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}}
]}
```

Stage 1b, the "after" as an EDIT of the before keyframe, so geometry and camera cannot drift:

```json
{"label": "room-makeover", "max_parallel": 1, "jobs": [
  {"id": "kf-after", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Exactly the same room, camera position, lens, walls, windows and floor as the first image. Now furnished: a low oak sofa on the left, a wool rug, a floor lamp switched on, two plants by the window, warm evening light at 3000 K, saturated but natural colour. Nothing else changes. <STYLE>", "image_urls": ["@kf-before"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}}
]}
```

Read both keyframes side by side: same vanishing lines, same window positions, equal detail. **Checkpoint A** (the after is a creative decision: the user approves it). Stage 2, draft, then quality, same prompt:

```json
{"label": "room-makeover", "max_parallel": 1, "jobs": [
  {"id": "d01", "endpoint_id": "minimax/h3-max-turbo/image-to-video", "est_cost_usd": 0.2,
   "input": {"prompt": "Locked-off wide shot. 0-3 s: the empty room, dust drifts in flat light. At 3.0 s warm light sweeps from left to right across the room and the furniture settles into place behind the sweep, finished by 4.0 s. 4-7 s: the furnished room, the lamp glows, leaves move slightly. The video ends exactly on the last frame and holds it for 1 s. Geometry, camera and lens stay fixed. No flicker, no text. <STYLE>", "image_url": "@kf-before", "end_image_url": "@kf-after", "duration": 8, "resolution": "480P", "prompt_expansion_mode": "disabled"}}
]}
```

```json
{"label": "room-makeover", "max_parallel": 1, "jobs": [
  {"id": "clip01", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 4.5,
   "input": {"prompt": "<the same prompt as d01>", "image_url": "@kf-before", "end_image_url": "@kf-after", "duration": "8", "resolution": "720p", "generate_audio": false}}
]}
```

- Sound is built in the finish so the onset sits on the transition frame: a thin room tone for 0-3 s, a whoosh at 3.0 s (`fal-ai/elevenlabs/sound-effects/v2`: `"text"`, `"duration_seconds": 1.0`), music from 3.0 s (`music_length_ms` 5000, placed with a 3 s delay).
- QA: in the sheet the transition must land between 40% and 60% of the clip, and the last tile must equal `kf-after`. A transition that morphs the walls → lower the difference between the keyframes, or cut the two states hard in the edit instead.
- Labels "before" and "after", and any claim, are composited (`finishing.md` section 3). A generated after is called a visualization in the delivery message.
- The user has a REAL after photo: register it as `@after` and make `kf-after` a recomposing edit of it alone (the stage 1a prompt, without inventing or removing anything), never an edit of the before. Read both keyframes: camera position and geometry match → the first + last frame clip above; they do not match → one 4 s locked-off clip per state and the wipe (`finishing.md` S8). Do not "improve" the real after.
- Cost math: keyframes $0.14; draft 8 s x $0.025 = $0.20; clip 8 s x $0.5676 = $4.54; effect and music about $0.61. About $5.50: the confirm gate applies. Value route: `alibaba/wan-3.0/image-to-video` with `start_image_url` + `end_image_url`, `"duration": 8`, `"resolution": "720p"`: $0.80.

## 4. Production C: luxury product, image-to-video (F6, 8 s, 9:16)

The product photo is registered as `@product`. Stage 1, two scene candidates (cheap; the pick is the user's):

```json
{"label": "amber-parfum", "max_parallel": 2, "jobs": [
  {"id": "kf-a", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "The exact bottle from the first image, unchanged in shape, label and colour, standing small on a rough plaster plinth in a large empty room; the bottle is a fifth of the frame height, lower centre; hard shadow geometry on the wall; one small hard source from the upper left at 3000 K, 50% of the frame in shadow; calm empty area in the upper third. <STYLE>", "image_urls": ["@product"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}},
  {"id": "kf-b", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "The exact bottle from the first image, unchanged in shape, label and colour, emerging from near-black on polished dark stone; only the glass edge and the metal cap catch a narrow warm light at 2700 K; faint reflection below; the bottle is a fifth of the frame height; calm dark area above. <STYLE>", "image_urls": ["@product"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}}
]}
```

Compare the label and proportions with the photo at full size. **Checkpoint A: the user picks.** Stage 2 (after a draft on the H3 model with the same prompt, `"duration": 8`):

```json
{"label": "amber-parfum", "max_parallel": 1, "jobs": [
  {"id": "clip01", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 4.5,
   "input": {"prompt": "0-1.5 s: complete stillness. 1.5-6 s: imperceptible push-in, 6% closer, while the light creeps across the shoulder of the bottle and a highlight travels along the glass edge. 6-8 s: everything holds still. Sound: near silence, a faint room tone, one soft glass resonance at 1.5 s. No hands, no camera shake, no text, no new objects. <STYLE>", "image_url": "@kf-a", "duration": "8", "resolution": "720p", "generate_audio": true}}
]}
```

- Native audio stays on: no voice goes on top, and foley is the sound design. Add isolated piano notes only if the user wants music.
- **Land on the approved frame** (logo stings, reveals): make the approved still the END frame. Start frame = an edit of it ("same scene, the bottle still in full shadow"), then `image_url` start + `end_image_url` approved still, and a prompt that describes the entrance and ends with "the video ends exactly on the last frame and holds it". On the draft model `end_image_url` may stand alone.
- Cost math: keyframes $0.14; draft $0.10; clip $4.54; about $4.80 before the finish.

## 5. Checklist before every paid stage

Prompt lint (`craft.md` section 8) · every `"@ref"` resolves (`pipeline.py fill` exits 0) · `duration` type and range match the model row above · `est_cost_usd` on every job, stage total equals the approved plan · Bash timeout 600000 ms · the stage's checkpoint, if any, was approved for THIS version.

## 6. Chaining: shots longer than the model maximum, seamless joins

One hop per stage, because each clip needs the previous clip's frame:

1. Run `clip05a`. QA it.
2. Exact last frame: `frames.py frame genmedia-output/<slug>/clip05a_0.mp4 --at last --out genmedia-output/<slug>/clip05a_last.png` (the final decoded frame, not a timestamp guess).
3. `gm.py upload` the PNG, then `pipeline.py add --label <slug> --step clip05a-last --path genmedia-output/<slug>/clip05a_last.png --url <cdn_url>`.
4. `clip05b`: start field = `"@clip05a-last"`, the chained-continuation template (`craft.md` section 7), style string byte-identical, same camera direction and speed, same model, same `resolution`.
5. In the cut, drop the first frame of `clip05b` (it duplicates the last frame of `clip05a`): trim its head by one frame duration (`finishing.md` S2).

No ffmpeg: a one-job stage on `fal-ai/ffmpeg-api/extract-frame` with `"video_url": "@clip05a"`, `"frame_type": "last"`; its output is `images[0]`, so `"@clip05a-last"` resolves without an upload. Each hop loses a little sharpness and colour: cap a chain at three links, and prefer one longer generation (Seedance and Wan reach 30 s) when the shot allows it.

## 7. Talking head (F9): voice chunks, then one avatar job per chunk

`fal-ai/bytedance/omnihuman/v1.5` takes `image_url` + `audio_url`; audio must be under 60 s at `"resolution": "720p"` and under 30 s at the default `1080p`; billed per second of audio (about $0.16). Short chunks keep a re-roll cheap and give cutaways a place to sit.

```text
audiokit.py chunk --input .genmedia/projects/<slug>/script.txt --max-chars 180 --endpoint fal-ai/elevenlabs/tts/eleven-v3 --text-field text --base-input .genmedia/projects/<slug>/voice-base.json --label <slug> --plan-out .genmedia/projects/<slug>/stage-1a-voice.json --price-per-1k 0.10
```

`voice-base.json` holds the shared settings (`{"voice": "Rachel", "stability": 0.5}`); the plan gets jobs `c001`, `c002`, ... split at sentence ends (about 180 characters is 8-13 s of English speech). Run it, `audiokit.py probe` every chunk, approve voice and portrait (Checkpoint A; `portrait` is the id of the portrait keyframe job, or the step name of the user's registered photo, used only after their consent yes), then:

```json
{"label": "<slug>", "max_parallel": 3, "jobs": [
  {"id": "head01", "endpoint_id": "fal-ai/bytedance/omnihuman/v1.5", "est_cost_usd": 1.8,
   "input": {"image_url": "@portrait", "audio_url": "@c001", "resolution": "720p", "prompt": "Speaks calmly to the camera, small natural head movement, steady eye contact"}},
  {"id": "head02", "endpoint_id": "fal-ai/bytedance/omnihuman/v1.5", "est_cost_usd": 1.6,
   "input": {"image_url": "@portrait", "audio_url": "@c002", "resolution": "720p", "prompt": "Speaks calmly to the camera, small natural head movement, steady eye contact"}}
]}
```

- Draft pass: the same plan on `fal-ai/flashtalk` (`image_url` + `audio_url`, about $0.02/s).
- The avatar clips carry the voice: concatenate them in order, cover every join with a 2-3 s b-roll cutaway (picture only, the head's audio continues underneath: `finishing.md` S7), then music, then captions.
- Turkish or any language the TTS schema lists works here, because the avatar follows the audio (OmniHuman on a Turkish voice, 2026-09-21: the mouth closed in pauses and rounded on "Bugün" and "ekşi"; a native listener rated it good, not flawless; `platform.md` section 10). `error: audio_duration_too_long` → smaller `--max-chars`.
- F10 uses the same idea in reverse: the user's audio span is the track, visuals are ordinary clips with audio off, captions are mandatory.
