# Video prompting

How to write the `prompt` for a video job. Craft rules are model-independent; the per-family section holds syntax and limits read from the live schemas on 2026-09-19 (re-check with `genmedia schema <endpoint_id> --format openapi --json`). Prompts are English; spoken lines stay in the language they must be heard in. Exact input fields per task: [video-recipes.md](video-recipes.md).

## 1. Shot grammar

One shot = one prompt. Fill the slots in this order; drop a slot only when the start frame already fixes it.

| # | Slot | Write | Example fragment |
|---|---|---|---|
| 1 | Subject + action | who or what, doing one thing, with a visible beginning and end | "a barista tilts the steel jug and pours a rosetta into a white cup" |
| 2 | Camera | ONE move, with a speed or amount; or "locked-off" | "slow push-in, about 10% closer over the shot" |
| 3 | Framing + lens | shot size, angle, focal feel, depth of field | "medium close-up at counter height, 50 mm look, shallow depth of field" |
| 4 | Light | source, direction, temperature | "window light from camera left, warm 3200K practical behind, soft shadows" |
| 5 | Motion intensity | how much moves besides the subject | "subtle: steam drifts, background patrons barely move" |
| 6 | Sound (audio on) | bed, one or two timed events, music or none, voice | "cafe murmur, milk hiss as the pour starts, no music" |
| 7 | End hold | what the last second looks like | "the last second holds still on the finished cup" |
| 8 | Absent | what must not appear, phrased as a property | "clean frame without text, logos or extra hands" |

Rules that change results:

1. **Image-to-video: motion only.** The frame already holds subject, set, light and lens. Re-describing it invites the model to redraw it. Write what moves, how the camera moves, what is heard, how it ends. Name the subject only to anchor the action ("the woman", "the bottle").
2. **One camera move per shot, always with a rate.** "Slow", "rapid", or a number ("orbit 30 degrees", "push in 10%"). Two moves in five seconds produce neither. Complexity comes from cutting shots together, not from stacking moves.
3. **Numbers beat adjectives.** Kelvin instead of "warm", seconds instead of "slowly", degrees instead of "orbit". Delete "cinematic", "stunning", "premium", "beautiful": replace each with the physical property that would create the impression (light ratio, lens, surface, pace).
4. **Causes, not feelings.** Posture, pace, light and sound are inputs; mood is the output. At most one short mood clause at the end.
5. **Say what stays still.** "The background stays static", "the product does not rotate", "her face keeps the same expression until the last second". Unspecified regions get invented motion.
6. **Hold the ending.** Reserve the last 0.5-2 s for a settled frame: it is the cover frame, the loop point and the cut point. If the move needs 3 s, order 5.
7. **Motivate transitions.** A hand crossing the lens, a door opening, the camera passing behind the subject. Unmotivated changes read as glitches.
8. **Keep exact text, logos, ratings, counters and captions out of the generation.** Models garble them. Leave negative space for them and add them in post (`pipelines`). Exception: short signage that is part of the scene, in quotes, and expect to check it on the frames.
9. **Length.** Roughly 40-120 words for a 5 s shot, up to about 250 for a timed 10-30 s shot. Long tails get ignored. Hard caps exist (section 5).
10. **No invented proof and no real people or brands as style handles.** Describe the look (grain, palette, lens), not a studio, director or trademark.

## 2. Camera vocabulary

| Intent | Move | Working amount |
|---|---|---|
| Intimacy, authority | slow push-in | 5-10% closer over 5 s; "felt, not seen" |
| | locked-off | nothing moves but the subject; safest for products and talking heads |
| Reveal | pull-back | detail to context in about 2 s, then hold |
| | orbit | 15-30 degrees per 5 s for products; 90-180 only for energetic hero shots |
| | crane or rise | ground detail to scale in about 2 s |
| | lateral slide | foreground object wipes the frame; replaces a cut |
| Energy | whip pan | about 0.5 s with blur, slight overshoot, settle |
| | snap zoom | about 0.3 s, no easing |
| | handheld follow | camera trails the subject by a beat, brief focus hunt |
| Life in a still | breathe | tiny drift plus 2-3% zoom |
| | rack focus | foreground to background once, on the narrative pivot |

Premium and product looks: one slow move or none; no handheld, whip pans, fast zooms or dutch angles. Vertical drift up reads as scale or hope, down as going deeper.

## 3. Light: direction + temperature

Every light gets a direction and a temperature (Kelvin, or warm/cool plus the source).

| Look | Recipe |
|---|---|
| Window natural | large soft source from one side, room fill, 5500K, soft shadows |
| Interview warm | soft key 45 degrees at 3200-4000K, cooler fill 1.5 stops under, background 1 stop under |
| Single-source drama | one small hard source, 40-60% of the frame in shadow |
| High-key product | even soft light, white-to-grey gradient, minimal shadow |
| Golden hour | low sun behind or beside the subject, 3000K rim, long shadows |
| Neon duo | two opposed saturated colours, no ambient fill, rim separation |
| Screen-as-key | dark room, display glow is the only source, light haze |
| Candle | 1800-2200K, flicker, moving soft shadows |

5000K and above reads analytical or "before"; 3200K and below reads intimate or "after"; a deliberate mix reads as transition. Synthetic people: always a catchlight, never flat frontal light, shadows consistent with the set.

## 4. Motion intensity and sound

Motion intensity, one of three, stated in words:

- **Subtle**: hair, fabric, steam, dust, breathing, a 2-5% camera drift. Default for products, portraits, first tries on an approved keyframe (least identity drift).
- **Moderate**: one clear body action or object move plus a gentle camera move.
- **Dynamic**: running, vehicles, crowds, fast camera. Highest risk of morphing; shorten the shot and simplify the background.

Sound plan, only when the audio switch is on:

- Four layers: **bed** (ambience or deliberate silence), **impacts** (one or two events tied to visible moments), **music** (describe tempo and instruments, or write "no music" when music comes later in post), **voice**.
- Dialogue: speaker, delivery, then the line in double quotes: `The woman looks into the lens and says calmly: "Bugün her şey değişiyor."` One or two short lines per 5 s (about 2-3 words per second). Keep the line in its spoken language; say the language once ("in Turkish") when the rest of the prompt is English.
- Several speakers: one line per speaker, `Host: "..."`, `Guest: "..."`, in speaking order.
- The clip will get voice-over or music later: turn audio off where it costs extra (Kling v3), or keep it on where it is free (Seedance) and ask for "ambience only, no music, no speech".

## 5. Per-family syntax and limits (schemas read 2026-09-19)

**Seedance 2.5** (`bytedance/seedance-2.5/us/text-to-video`, `bytedance/seedance-2.5/us/image-to-video`, `bytedance/seedance-2.5/us/reference-to-video`)
- Fields: `prompt`, `duration` string `"4"`-`"30"` or `"auto"` (default auto: always set it), `resolution` `480p`/`720p`/`1080p`, `aspect_ratio` (text and reference only; image-to-video follows the image), `generate_audio` default true at no extra cost, `bitrate_mode`. `seed` exists only on reference-to-video. No `negative_prompt`: phrase absences as properties inside the prompt.
- Reference tokens are positional and 1-based per array: `@Image1` = `image_urls[0]`, `@Video1`, `@Audio1`. Give every reference a role in the first sentence ("@Image1 is the woman, @Image2 is the bottle she holds, @Image3 is the kitchen"). An unreferenced file is wasted budget.
- `task`: `reference` (guide with the media), `editing` (modify `@Video1`; `aspect_ratio` and `duration` are forced to auto), `extension` (continue `@Video1`; `aspect_ratio` forced to auto). Audio references need at least one image or video reference.
- Understands timed beats and cuts written in prose ("Cut to ..."), which is how to get several shots in one 10-30 s job.

**Kling v3 Pro / Standard, Kling O3** (`fal-ai/kling-video/v3/pro/text-to-video`, `fal-ai/kling-video/v3/pro/image-to-video`, `fal-ai/kling-video/o3/pro/reference-to-video`)
- `prompt` max 2500 characters, OR `multi_prompt`, never both. `negative_prompt` exists (default "blur, distort, and low quality"). `cfg_scale` 0-1, default 0.5 (how closely the model follows the prompt): leave it alone on the first try, raise it slightly only as a repair when the prompt is ignored.
- `multi_prompt`: array of `{"prompt", "duration"}` with per-shot `duration` as a string `"1"`-`"15"`; `shot_type` `customize` (your shots) or `intelligent` (model decides the cuts from one prompt). Set the top-level `duration` to the sum of the shots and keep it within `"3"`-`"15"`. Write each shot as a full shot-grammar line; repeat the character description or cite the same element in every shot.
- Elements: `elements[]` entries are `{frontal_image_url, reference_image_urls (1-3)}` or `{video_url}` (one video element per request); cite as `@Element1`, `@Element2` in array order. Cite an element only if it exists in the array. On O3 reference-to-video, style images go in `image_urls` and are cited `@Image1`.
- Native speech is Chinese or English only; other languages are auto-translated to English. For English speech fal's schema note says lowercase text, uppercase only for acronyms and proper nouns.
- Image-to-video has no `aspect_ratio`: the start frame decides.

**Wan 3.0** (`alibaba/wan-3.0/text-to-video`, `alibaba/wan-3.0/image-to-video`, `alibaba/wan-3.0/reference-to-video`)
- `duration` integer 2-30 (null lets the model decide: do not), `resolution` default `1080p` (set `720p`), `aspect_ratio` includes `adaptive`, audio switch is `audio`, `seed` supported.
- `enable_prompt_expansion` defaults to true and rewrites your prompt; the rewritten text comes back as `actual_prompt`. With a full shot-grammar prompt set it false so timing and camera survive; keep it on for short prompts.
- References are cited positionally in plain words: "the subject in Image 1 walks past Video 1".

**MiniMax H3 Max Turbo** (`minimax/h3-max-turbo/text-to-video`, `minimax/h3-max-turbo/image-to-video`)
- `prompt_expansion_mode` is required: `disabled` for a full shot-grammar prompt, `balanced` for short ones, `quality` spends up to about 30 s on a richer rewrite. `duration` integer 5-15. `resolution` uppercase `480P`/`768P`/`1080P`. The rewritten prompt is returned as `expanded_prompt`: read it when a draft misses the brief.
- A soundtrack is generated; `target_audio_url` pins your own clip instead.

**Edit models.** `google/gemini-omni-flash/v1.1/edit` wants one plain instruction ("replace the red car with a blue bicycle; keep everything else"). `fal-ai/kling-video/o3/pro/video-to-video/edit` cites the source as `@Video1` and elements as `@Element1`. Both: state what must be preserved, change one thing per pass.

## 6. Timed beats (shots longer than about 6 s)

Write time, not just scenes. Each beat: what changes on screen, one camera behaviour, the sound event. Beats sum to the ordered `duration`; the last beat is the hold.

```text
0-2 s: <hook action>. <camera>. <sound event>.
2-6 s: <development>. <same or no camera move>. <sound>.
6-9 s: <payoff>. <camera settles>. <sound>.
9-10 s: hold on <final composition>, no new motion.
```

More than about four beats, or beats that need different sets or lenses: split into several jobs and cut them together (`pipelines`), or use Kling `multi_prompt`.

## 7. Prompt lint (run before every paid call)

1. Subject and ONE action in the first sentence; image-to-video prompts do not re-describe the frame.
2. Exactly one camera move, with a rate or amount, or "locked-off".
3. Every light has a direction and a temperature (or the start frame fixes the light and the prompt says nothing).
4. Motion intensity stated; what must stay still is named.
5. Audio on: a sound plan with at least one timed event, dialogue in quotes with speaker and language, or "no music / no speech" chosen on purpose.
6. The last 0.5-2 s is a hold.
7. Timed beats sum to `duration`; `duration`, `resolution`, aspect ratio and the audio switch are set as parameters, not only in prose.
8. No empty quality adjectives; no real person, brand, studio or artist names as style handles.
9. Exact text, logos, ratings and captions are left for post; the frame leaves room for them.
10. References cited with the family's real syntax (`@Image1` / `@Element1` / "Image 1") and every uploaded reference has a role.
11. Absences phrased as properties, or placed in `negative_prompt` where the schema has one.
12. Under the family's prompt cap; nothing in the prompt that the chosen endpoint cannot take (no end frame in a text-to-video prompt, no `multi_prompt` next to `prompt`).

## 8. Worked examples

Inputs as they go into `.genmedia/tmp/<label>.json`. URLs are placeholders for uploaded `cdn_url` values.

**A. Product hero from an approved keyframe** (`bytedance/seedance-2.5/us/image-to-video`)

```json
{"image_url": "https://<cdn>/keyframe.png", "duration": "5", "resolution": "720p", "generate_audio": true,
 "prompt": "The perfume bottle stays perfectly still on the wet slate. Slow orbit of about 20 degrees to the right, ending centred. A thin ribbon of mist drifts left to right behind the bottle; one water bead slides down the glass at two seconds. Light does not change. Subtle motion only, background static. Sound: low room tone, a single soft water drip at two seconds, no music. The last second holds still. Clean frame without text or hands."}
```

**B. Ten-second text-to-video with timed beats** (`bytedance/seedance-2.5/us/text-to-video`)

```json
{"aspect_ratio": "9:16", "duration": "10", "resolution": "720p", "generate_audio": true,
 "prompt": "0-2 s: extreme close-up of a cold espresso cup on a cluttered desk at dawn, 6000K window light from the left, locked-off camera, silence except a laptop fan. 2-6 s: a hand slides a fresh cup into frame and steam rises; the light warms to 3200K as a desk lamp clicks on; slow push-in of about 10%; the lamp click is audible at two seconds. 6-9 s: the person, seen from the shoulders down, lifts the cup and the clutter behind falls out of focus; soft lo-fi piano enters. 9-10 s: hold on the cup at chest height with empty space above it for a title. No text, no logos, no face."}
```

**C. Native dialogue in Turkish** (`alibaba/wan-3.0/image-to-video`; its Turkish passed a native listen, Seedance's did not: `platform.md` section 10)

```json
{"start_image_url": "https://<cdn>/presenter.png", "duration": 6, "resolution": "720p", "audio": true, "enable_prompt_expansion": false,
 "prompt": "The woman looks into the lens, smiles briefly, and says in Turkish, in a calm friendly voice: \"Merhaba, bugün size yeni koleksiyonu göstereceğim.\" She gestures once with her right hand toward the rack beside her, then rests it. Locked-off camera, medium close-up. Subtle motion: natural blinking, slight head movement, background static. Sound: quiet boutique room tone, her voice clear and close, no music. She finishes speaking by second five and holds a smile for the last second."}
```

**D. Three shots in one call** (`fal-ai/kling-video/v3/pro/text-to-video`; no top-level `prompt`)

```json
{"aspect_ratio": "16:9", "duration": "12", "shot_type": "customize", "generate_audio": false,
 "negative_prompt": "blur, distortion, text, watermark, extra fingers",
 "multi_prompt": [
  {"duration": "4", "prompt": "Wide shot of a lone cyclist in a yellow rain jacket on an empty coastal road at dawn, overcast 6500K light, slow crane rise from the asphalt to reveal the sea, waves moving gently."},
  {"duration": "4", "prompt": "Medium tracking shot from the side of the same cyclist in the yellow rain jacket, camera moves at the rider's speed, shallow depth of field, spray lifting from the front wheel."},
  {"duration": "4", "prompt": "Close-up of the same cyclist's face in the yellow hood, locked-off camera, the rider stops, exhales and looks out to sea; the last second holds still."}]}
```

**E. End-frame reveal: finish exactly on an approved cover** (`bytedance/seedance-2.5/us/image-to-video`). The start frame is the cover edited to an empty set (made with `image`); the approved cover is the end frame.

```json
{"image_url": "https://<cdn>/cover_empty_set.png", "end_image_url": "https://<cdn>/cover_approved.png",
 "duration": "5", "resolution": "720p", "generate_audio": false,
 "prompt": "0-1.5 s: the empty studio set is alive: soft haze drifts, the light sweeps slowly from left to right. 1.5-3.5 s: the sneaker drops in from above, lands on the plinth with a small bounce and settles. 3.5-5 s: the camera eases to the final composition and the video ends exactly on the provided end frame, holding still. No flicker, no extra objects, no text."}
```

**F. References with roles** (`bytedance/seedance-2.5/us/reference-to-video`, `task` "reference")

```json
{"task": "reference", "image_urls": ["https://<cdn>/mira_front.png", "https://<cdn>/mira_side.png", "https://<cdn>/thermos.png", "https://<cdn>/cabin.png"],
 "aspect_ratio": "16:9", "duration": "8", "resolution": "720p", "generate_audio": true,
 "prompt": "@Image1 and @Image2 are the same woman, Mira; @Image3 is the green steel thermos she carries; @Image4 is the cabin interior where the scene takes place. Mira walks in from the snowy doorway, sets the thermos on the wooden table, unscrews the cap and pours; steam rises. Slow push-in from a medium shot to a medium close-up. Warm 2800K firelight from the right, cool blue daylight from the door behind her. Moderate motion, furniture static. Sound: wind fades as the door closes at two seconds, liquid pouring at five seconds, crackling fire, no music, no speech. The last second holds on her hands around the cup."}
```
