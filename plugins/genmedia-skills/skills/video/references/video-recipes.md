# Video recipes

Task -> endpoint -> exact input fields -> input JSON. Fields, enums and limits were read from the live OpenAPI schemas on 2026-09-19; they are a dated cache. Before the first paid call to an endpoint in a session run `genmedia schema <endpoint_id> --format openapi --json` and trust it over this file. Prices are dated hints: confirm with `gm.py price <ids> --explain`. Prompt craft: [prompting-video.md](prompting-video.md). Tiers and alternates: [routing-video.md](routing-video.md).

Every recipe runs the same way: upload local media, write the JSON with the Write tool to `.genmedia/tmp/<label>.json`, estimate, pass the cost gate, then:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run <endpoint_id> --input .genmedia/tmp/<label>.json --label <label> --est-cost <usd>
```

All endpoints below return the clip at `.result.video.url` (the helper downloads it and lists it in `outputs[]`), except where noted. URLs in the examples stand for uploaded `cdn_url` values. Never set the platform flag `sync_mode: true` (base64 output); two endpoints below reuse the name for something else.

## 1. Image-to-video

| Family | Endpoint | Start frame | End frame | Duration | Must set |
|---|---|---|---|---|---|
| Seedance 2.5 (default) | `bytedance/seedance-2.5/us/image-to-video` | `image_url`* | `end_image_url` | string `"4"`-`"30"` | `duration` (default is `auto`), `resolution` |
| Wan 3.0 (value) | `alibaba/wan-3.0/image-to-video` | `start_image_url`* | `end_image_url` | integer 2-30 | `resolution` (default `1080p`), `audio` |
| MiniMax H3 Max Turbo (budget) | `minimax/h3-max-turbo/image-to-video` | `image_url` | `end_image_url` | integer 5-15 | `prompt_expansion_mode`* |
| Kling v3 Pro (control) | `fal-ai/kling-video/v3/pro/image-to-video` | `start_image_url`* | `end_image_url` | string `"3"`-`"15"` | `generate_audio` (true costs +50%) |

`*` = required. Text-to-video on the same families: drop the image fields, add `aspect_ratio` (example B in `prompting-video.md`). Seedance and Kling output follows the start frame's shape; build the keyframe in the target aspect ratio. Seedance images: JPEG/PNG/WebP up to 30 MB.

```json
{"image_url": "https://<cdn>/keyframe.png", "prompt": "<motion-only prompt>", "duration": "5", "resolution": "720p", "generate_audio": true}
```

Budget draft of the same shot (note the required field and the uppercase enum):

```json
{"image_url": "https://<cdn>/keyframe.png", "prompt": "<motion-only prompt>", "duration": 5, "resolution": "768P", "prompt_expansion_mode": "disabled"}
```

## 2. First + last frame

- Default: the Seedance image-to-video endpoint with `image_url` + `end_image_url`. Same fields on Wan (`start_image_url` + `end_image_url`) and Kling v3.
- More than two pinned frames: `blackforestlabs/flux-3/keyframes-to-video` (`keyframes[]` of `{image_url, frame_index}`, at most 10, explicit integer `duration` 5-20).
- **Make the end frame by editing the start frame** (`image` skill, edit route: "same scene, same light, the jar is now open and empty"). Two independently generated stills differ in identity, lens and light, and the model spends the clip morphing between them.
- **End-frame reveal.** When the approved still must be the final composition (cover, logo sting, product hero), pass it as the END frame and derive the start frame from it by removing the hero element. A start frame drifts; an end frame is landed on. Prompt example E in `prompting-video.md`.
- Both frames must share the aspect ratio. Keep the change between them achievable in the ordered seconds: one action, one camera move.

```json
{"image_url": "https://<cdn>/start.png", "end_image_url": "https://<cdn>/end.png", "prompt": "<what happens between the frames; ends exactly on the provided end frame, holding still>", "duration": "5", "resolution": "720p", "generate_audio": false}
```

## 3. Reference / elements-to-video

Use when identity must carry over but the first frame is free. A `character` handle resolves to the image URLs to pass here.

| Family | Endpoint | Reference fields and limits | Cite as |
|---|---|---|---|
| Seedance 2.5 | `bytedance/seedance-2.5/us/reference-to-video` | `image_urls` up to 30 (30 MB each), `video_urls` up to 10 (MP4/MOV, 1.8-30.2 s each and in total, 200 MB, 300-6000 px per side, 24-60 fps), `audio_urls` up to 10 (MP3/WAV, 15 MB, needs an image or video too); 50 files in total | `@Image1`, `@Video1`, `@Audio1` |
| Wan 3.0 | `alibaba/wan-3.0/reference-to-video` | `reference_image_urls` up to 10, `reference_video_urls` up to 5 (15 s total, 16 fps or more), `reference_audio_urls` up to 5 (15 s total) | "Image 1", "Video 1" |
| Kling O3 Pro | `fal-ai/kling-video/o3/pro/reference-to-video` | `elements[]` of `{frontal_image_url, reference_image_urls (1-3)}` or one `{video_url}`; style images in `image_urls`; optional `start_image_url`, `end_image_url`; with a video at most 4 elements + images | `@Element1`, `@Image1` |

Roles: say in the first sentence what each reference is (person, product, location, style). Two or three angles of one person beat one; a product gets its own image; do not mix two people in one image. Input and output seconds are both billed when Seedance gets video references (at 0.6x).

```json
{"task": "reference", "image_urls": ["https://<cdn>/person_front.png", "https://<cdn>/person_side.png", "https://<cdn>/product.png"], "prompt": "@Image1 and @Image2 are the same woman; @Image3 is the bottle she holds. <shot>", "aspect_ratio": "9:16", "duration": "6", "resolution": "720p", "generate_audio": true}
```

Kling elements next to a fixed start frame (`fal-ai/kling-video/v3/pro/image-to-video`):

```json
{"start_image_url": "https://<cdn>/keyframe.png", "elements": [{"frontal_image_url": "https://<cdn>/hero_front.png", "reference_image_urls": ["https://<cdn>/hero_side.png"]}], "prompt": "@Element1 turns from the window and walks toward the camera. <camera, light, hold>", "duration": "5", "generate_audio": false}
```

## 4. Native dialogue, multi-shot

- Dialogue: any Seedance 2.5 generation endpoint with `generate_audio` true; line in double quotes with speaker, delivery and language (example C in `prompting-video.md`). Budget: `bytedance/seedance-2.0/mini/text-to-video` or `bytedance/seedance-2.0/mini/image-to-video` (4-15 s, 480p/720p). Turkish lines: not on Seedance. In a native listen (`platform.md` section 10) every Seedance version mispronounced the line, while Wan 3.0 got it right; example C uses Wan 3.0. Veo 3.1 Lite, flawless in that listen, is no longer listed on fal. The user listens before approving (troubleshooting section 2). Kling v3 speaks English and Chinese only.
- Multi-shot in one call: `fal-ai/kling-video/v3/pro/text-to-video` with `multi_prompt` and no `prompt` (example D). Recurring character across the shots: `fal-ai/kling-video/o3/pro/reference-to-video` with `elements` + `multi_prompt`. Seedance alternative: one 10-30 s prompt with timed beats and written cuts.

## 5. Extend, and chaining past the model maximum

Never order a `duration` above the schema maximum. Three ways to get length, in order of preference:

1. **Native extension.** `bytedance/seedance-2.5/us/reference-to-video` with `task` "extension" and the clip in `video_urls` (1.8-30.2 s). `aspect_ratio` is forced to auto. Billing counts input + output seconds at 0.6x.

   ```json
   {"task": "extension", "video_urls": ["https://<cdn>/clip1.mp4"], "prompt": "Continue @Video1: <what happens next, same camera behaviour, same light>. The last second holds still.", "duration": "6", "resolution": "720p", "generate_audio": true}
   ```

   Flat rate: `fal-ai/ltx-2.3/extend-video` (`video_url`*, optional `prompt`, number `duration` 2-20, default 5; `mode` `end` appends, `start` prepends). Budget: `fal-ai/pixverse/v6/extend` (`video_url`*, `prompt`*, integer `duration` 1-15, `generate_audio_switch` default false).

2. **Last-frame bridging** (works with every image-to-video model). Take the exact final decoded frame of clip N, upload it, use it as the start frame of clip N+1 with a prompt that continues the motion.

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/frames.py" frame genmedia-output/<label>/clip1.mp4 --at last
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload genmedia-output/<label>/clip1_last.png
   ```

   A timestamp guess near the end is not the last frame and leaves a visible jump; `--at last` is exact. Each hop loses a little sharpness and identity: keep chains to 2-3 hops, re-anchor with references where the endpoint allows, and keep camera direction and speed continuous across the seam. Joining the clips is a `pipelines` job.

3. **One long Seedance job** (up to 30 s) with timed beats, when the content fits one prompt.

No local ffmpeg: `fal-ai/ffmpeg-api/extract-frame` returns the frame at `.result.images[0].url` (already a URL, no upload needed):

```json
{"video_url": "https://<cdn>/clip1.mp4", "frame_type": "last"}
```

`frame_type` is `first`, `middle` or `last`; about $0.0002 per second of input as of 2026-09-19. Probe without ffmpeg: `fal-ai/ffmpeg-api/metadata` with `media_url`* returns duration, fps, resolution and the audio track under `.result.media`.

## 6. Edit / restyle by instruction

| Need | Endpoint | Fields | Limits |
|---|---|---|---|
| Default edit | `google/gemini-omni-flash/v1.1/edit` | `video_url`*, `prompt`*, `resolution` `360p`-`4k` (default `720p`) | one plain instruction |
| Cheapest | `blackforestlabs/flux-3/edit-video` | `video_url`*, `prompt`* (4096 chars) | MP4 under 50 MB and under 15 s; keeps motion, timing, framing |
| Edit with character/object elements | `fal-ai/kling-video/o3/pro/video-to-video/edit` | `video_url`*, `prompt`* citing `@Video1`, `elements[]`, `image_urls`, `keep_audio` default true | MP4/MOV, 3-15 s, 720-3840 px, 200 MB; at most 4 elements + images |
| Highest fidelity | `bytedance/seedance-2.5/us/reference-to-video`, `task` "editing" | `video_urls`, `prompt` citing `@Video1`, optional `image_urls` | `duration` and `aspect_ratio` forced to auto: estimate with the source length |

Instruction pattern: the change, then what must survive ("Replace the red car with a blue bicycle. Keep the street, the light, the camera move and the timing unchanged."). One change per pass. Probe the source first (`scripts/frames.py probe`) and trim or re-encode locally when it breaks a limit.

```json
{"video_url": "https://<cdn>/source.mp4", "prompt": "Turn the daytime scene into night with wet streets and neon reflections. Keep the people, the framing and the camera move unchanged.", "resolution": "720p"}
```

## 7. Reframe to another aspect ratio

`fal-ai/ltx-2.3/reframe`: `video_url`* (up to 60 s), `aspect_ratio` `1:1`/`4:5`/`5:4`/`9:16`/`16:9`, `resolution` `720p`/`1080p` (default `1080p` at twice the price; billed on input seconds). No prompt.

```json
{"video_url": "https://<cdn>/landscape.mp4", "aspect_ratio": "9:16", "resolution": "720p"}
```

Budget or when the fill needs direction: `luma/agent/ray/v3.2/reframe` (`video_url`*, `aspect_ratio`*, `prompt`* describing the new canvas area; source 10 s or less; `resolution` default `540p`). A plain crop or pad is not a generation job: do it with ffmpeg or hand it to `pipelines`.

## 8. Motion transfer

`fal-ai/kling-video/v3/pro/motion-control`: `image_url`* (character, clear body, unobstructed), `video_url`* (driving performance, head and upper body visible), `character_orientation`* `video` (complex motion, source up to 30 s) or `image` (follows camera moves, up to 10 s), `keep_original_sound` default true, optional `prompt`, one face `elements[]` entry only with orientation `video`.

```json
{"image_url": "https://<cdn>/character.png", "video_url": "https://<cdn>/dance.mp4", "character_orientation": "video", "keep_original_sound": false}
```

Budget, non-human or several characters: `fal-ai/bytedance/dreamactor/v2` (`image_url`* JPEG/PNG up to 4.7 MB, 480x480 to 1920x1080; `video_url`* up to 30 s, MP4/MOV/WebM; `trim_first_second` default true removes the 1 s lead-in). A real person in the driving video or the image: consent first.

## 9. Lipsync vs talking head

| You have | Task | Default | Budget | Control |
|---|---|---|---|---|
| A video of the speaker + new audio | lipsync | `fal-ai/sync-lipsync/v3` | `fal-ai/latentsync` | `fal-ai/heygen/v3/lipsync/precision` (`start_time`, `end_time`, captions) |
| One image + audio | talking head | `fal-ai/bytedance/omnihuman/v1.5` | `fal-ai/flashtalk` | `fal-ai/kling-video/ai-avatar/v2/pro`, `fal-ai/heygen/avatar4/image-to-video` |
| Only a script | neither yet | get speech from `audio`, then one of the rows above; or generate the footage with native dialogue (section 4) | | |

- All take `video_url`* or `image_url`* plus `audio_url`* (HeyGen Avatar 4 alone can instead speak a `prompt` with one of its built-in `voice` names). Output length follows the audio: estimate with the audio seconds.
- `fal-ai/sync-lipsync/v3` has a field named `sync_mode` that is NOT the platform's base64 flag: it chooses what happens when audio and video lengths differ (`cut_off` default, `loop`, `bounce`, `silence`, `remap`). Setting it is fine.
- `fal-ai/latentsync`: `loop_mode` `pingpong` or `loop` when the audio is longer than the video.
- `fal-ai/bytedance/omnihuman/v1.5`: `resolution` defaults to `1080p` (audio under 30 s); `720p` allows under 60 s and fal's schema calls it faster and higher quality: set `720p`. `mask_url` (white = the speaker) when several people are in the image.
- Source for lipsync: face visible and mostly frontal for the whole clip, steady framing. Clean speech without music gives the best sync; mix music afterwards.

```json
{"image_url": "https://<cdn>/presenter.png", "audio_url": "https://<cdn>/voiceover.mp3", "resolution": "720p"}
```

## 10. Upscale, background removal

Upscale is the LAST step, after the clip is approved: it multiplies pixels, not quality of motion, and re-rendering an upscaled clip wastes it.

- `fal-ai/seedvr/upscale/video`: `video_url`*, `upscale_mode` `target` + `target_resolution` `720p`/`1080p`/`1440p`/`2160p`, or `factor` + `upscale_factor` 1-10 (default 2). Priced per megapixel of output video data (width x height x frames): read `pricing_text` (`--explain`), about $0.25 for 121 frames at 1080p as of 2026-09-19. The schema has no audio switch: probe the result and re-mux the original track if `has_audio` is false.
- Budget: `fal-ai/flashvsr/upscale/video` (`upscale_factor` 1-4; set `preserve_audio` true, it defaults to false). Premium: `topaz/upscale/video/precision` (`upscale_factor` 1-4, `target_fps` 16-60 for interpolation, `model` default `Proteus`).

```json
{"video_url": "https://<cdn>/approved_720p.mp4", "upscale_mode": "target", "target_resolution": "1080p"}
```

Background removal: `bria/video/background-removal/v3` with `video_url`*. `background_color` defaults to `Black`: set `Transparent` for alpha, and keep an alpha-capable `output_container_and_codec` (`webm_vp9` default, `mov_proresks` for editors; MP4 H.264 has no alpha). `preserve_audio` default true. Budget: `veed/video-background-removal/fast` (its output is an array: `.result.video[0].url`).

```json
{"video_url": "https://<cdn>/presenter.mp4", "background_color": "Transparent", "output_container_and_codec": "webm_vp9"}
```

## 11. Cost arithmetic (dated hints, 2026-09-19; Seedance 2026-10-21)

The pricing API returns one number per endpoint; for per-second video models it is usually the lowest tier. Always price with `gm.py price <ids> --explain` and read `pricing_text`.

| Job | Arithmetic | About |
|---|---|---|
| Seedance 2.5, 5 s, 720p | 5 x $0.57 | $2.85 -> confirm |
| Seedance 2.5, 5 s, 480p draft | 5 x $0.26 | $1.30 -> announce |
| Seedance 2.5, 10 s, 1080p | 10 x $1.40 | $14.00 -> confirm |
| Wan 3.0, 5 s, 720p | 5 x $0.10 | $0.50 -> announce |
| MiniMax H3 Max Turbo, 5 s, 768P | 5 x $0.04 (launch discount ended 2026-09-30) | $0.20 -> run |
| Kling v3 Pro, 5 s, audio on / off | 5 x $0.168 / 5 x $0.14 (the API base beats the $0.112 tier: quote the higher) | $0.84 / $0.70 -> announce |
| Seedance extension of a 5 s clip by 6 s, 720p | (5 + 6) x $0.57 x 0.6 | $3.75 -> confirm |
| Omni Flash edit, 8 s, 720p | 8 x $0.10 | $0.80 -> announce |
| Sync Lipsync 3, 20 s | 20 x $0.133 | $2.70 -> confirm |

Re-renders are new jobs at full price. The gate applies to the whole plan the user approved, including the keyframe.
