# Batch plans: staged worked examples

Five complete pipelines as `gm.py batch` plans. Endpoint IDs were active and every field below was read from the live OpenAPI schema on **2026-09-19**. They are a dated cache: repeat SKILL.md Workflow step 3 before you spend, and let the routing of `image`, `video`, `audio` and `models` override the model picks. `gm.py` and `pipeline.py` abbreviate the calls shown in SKILL.md. Cost lines use prices observed that day; re-price with `gm.py price`.

## Plan format and staging rules

```json
{"label": "<slug>", "max_parallel": 4, "jobs": [
  {"id": "kf01", "endpoint_id": "<endpoint_id>", "est_cost_usd": 0.07,
   "input": {"prompt": "..."}, "download": "genmedia-output/<slug>/stills/kf01_{index}.{ext}"}
]}
```

```text
gm.py batch --plan <plan.json|-> [--timeout 540] [--max-parallel N] [--retry-failed]
pipeline.py fill --template <tmpl.json> --out <plan.json> [--label <slug>] [--placeholder <regex>] [--allow-placeholders]
pipeline.py urls --label <slug>
pipeline.py add --label <slug> --step <id> --path <file> [--url <https-url>] [--tool <name>] [--from <id,id>] [--note <text>]
pipeline.py fetch --label <slug> --step <id> --out <relative-path> [--url <https-url>] [--index N] [--endpoint <endpoint_id>] [--request-id <id>] [--note <text>]
pipeline.py manifest --label <slug>
```

- Those are all the flags. `--max-parallel` overrides the plan value (default 4). Plan keys: `label`, `max_parallel`, `jobs[]` with `id`, `endpoint_id`, `input`, optional `download` and `est_cost_usd`; nothing else is read. Run every command from the project root: the ledger is `.genmedia/runs.jsonl` in the current directory, and a run from another directory sees no earlier requests and pays for them again.
- `label`: the project slug, identical in every stage. `id`: unique across the whole project, not just the stage. `download` is a job-level key next to `input` (inside `input` it is refused) and optional: default `genmedia-output/<label>/<id>_{index}.{ext}`; `false` skips files. `est_cost_usd` is your per-job estimate; the ledger sums it.
- Jobs inside one plan are independent and run in any order. Anything that consumes another job's output goes into a later stage file.
- Save templates as `.genmedia/projects/<slug>/stage-<n>-<name>.tmpl.json` and reference earlier outputs as whole-string values: `"@kf01"` (first output), `"@kf01[1]"` (second), also inside arrays and nested objects. `pipeline.py fill --template <tmpl> --out <plan>` replaces them with CDN URLs from the ledger and writes nothing if any reference is unresolved. A literal string that must start with `@` is written `"@@..."`. Citation tokens inside a prompt (`@Image1`) are untouched: only whole-string values are references.
- `fill` also refuses a text placeholder that survived in a string value of `jobs[].input`: `{LOCK}`, `{{TOKEN}}`, `<describe it>`. It writes nothing and answers `"placeholders"` with the JSON path of every hit, because a placeholder that reaches the model is a wasted paid job. A bracket that belongs in the prompt is escaped `\{ \} \< \>` and the backslash is dropped on write; `--placeholder <regex>` replaces the pattern and `--allow-placeholders` turns the check off.
- An unfilled template cannot be submitted by accident: the helper rejects non-URL values in `*_url` and `*_urls` fields before anything is sent. Fields with other names (compose `tracks`) have no such net; always run `fill`.
- User files: `gm.py upload`, then `pipeline.py add --label <slug> --step <name> --path <file> --url <cdn_url>`; reference as `"@<name>"`.
- Rerunning a plan resumes by `label` + `id`. Failed id, changed input: `--retry-failed`; it resubmits every failed, cancelled or submit-unknown id in the plan file, so fix them all or run a plan file with only the repaired ids. Completed id you want again: new id (`clip02-r2`).
- Canary for 4+ paid jobs on a new endpoint: a plan file with only the first job, then the full plan (the first id is resumed, not repaid).

## 1. Keyframes to image-to-video clips to a cut

Stage 1a, the style anchor (`stage-1a-anchor.tmpl.json` needs no fill; run it directly):

```json
{"label": "harbor-film", "max_parallel": 1, "jobs": [
  {"id": "kf01", "endpoint_id": "bytedance/seedream/v5/pro/text-to-image", "est_cost_usd": 0.07,
   "input": {"prompt": "Wide shot of a fishing harbor at dawn, soft fog, 35mm film look, muted teal and amber palette", "image_size": {"width": 1920, "height": 1080}, "num_images": 1, "output_format": "png"}}
]}
```

Stage 1b, remaining keyframes edited from the anchor so palette, grade and characters hold:

```json
{"label": "harbor-film", "max_parallel": 3, "jobs": [
  {"id": "kf02", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Same harbor, same film look and palette as the reference: close-up of weathered hands coiling a rope", "image_urls": ["@kf01"], "image_size": {"width": 1920, "height": 1080}, "output_format": "png"}},
  {"id": "kf03", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Same harbor, same film look and palette as the reference: a small boat leaving the pier, seen from behind", "image_urls": ["@kf01"], "image_size": {"width": 1920, "height": 1080}, "output_format": "png"}},
  {"id": "kf04", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Same harbor, same film look and palette as the reference: gulls over open water, sun breaking through", "image_urls": ["@kf01"], "image_size": {"width": 1920, "height": 1080}, "output_format": "png"}}
]}
```

QA gate, then **checkpoint: approve stills**. Stage 2, clips:

```json
{"label": "harbor-film", "max_parallel": 4, "jobs": [
  {"id": "clip01", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 2.9,
   "input": {"prompt": "Slow push-in across the harbor, fog drifting, water gently moving, no cuts", "image_url": "@kf01", "duration": "5", "resolution": "720p", "generate_audio": true}},
  {"id": "clip02", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 2.9,
   "input": {"prompt": "Hands coil the rope in one steady motion, shallow depth of field, static camera", "image_url": "@kf02", "duration": "5", "resolution": "720p", "generate_audio": true}},
  {"id": "clip03", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 2.9,
   "input": {"prompt": "The boat pulls away from the pier, camera holds, wake spreading", "image_url": "@kf03", "duration": "5", "resolution": "720p", "generate_audio": true}},
  {"id": "clip04", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 2.9,
   "input": {"prompt": "Gulls wheel over the water as sunlight breaks through, slow tilt up", "image_url": "@kf04", "duration": "5", "resolution": "720p", "generate_audio": true}}
]}
```

QA gate, **checkpoint: approve clips**. Stage 3, the cut. Local ffmpeg: `assembly.md` recipes A2 and A3. Without ffmpeg:

```json
{"label": "harbor-film", "max_parallel": 1, "jobs": [
  {"id": "cut", "endpoint_id": "fal-ai/ffmpeg-api/merge-videos", "est_cost_usd": 0.01,
   "input": {"video_urls": ["@clip01", "@clip02", "@clip03", "@clip04"], "target_fps": 24, "resolution": {"width": 1280, "height": 720}},
   "download": "genmedia-output/harbor-film/harbor-film_cut.{ext}"}
]}
```

- Cost math: stills 4 x $0.0675; clips 4 x 5 s x ~$0.5676/s at 720p = ~$11.35 (token-priced: read `pricing_text` from `--explain`); cut: cents. Seedream sizes: total pixels between 1024x1024 and 2048x2048, so 1280x720 is too small; 1920x1080 stays in the lower price tier (area up to 1536x1536).
- Swap for drafts: `minimax/h3-max-turbo/image-to-video` with `"image_url"`, `"duration": 5` (integer 5-15), `"resolution": "768P"` (uppercase) and the required `"prompt_expansion_mode": "disabled"`.
- Continuous-shot variant: clips become sequential. After `clip01` completes, take its exact last frame (local recipe A6, or `fal-ai/ffmpeg-api/extract-frame` with `"frame_type": "last"`, output `images[0]`), and feed it as `image_url` of `clip02`. One job per stage; slower, seam-free.

## 2. Narrated short: voice-over, stills, clips, music, mix

Voice first: its measured length sets clip durations and music length. Stage 1 (voice and stills are independent of each other):

```json
{"label": "kahve-short", "max_parallel": 4, "jobs": [
  {"id": "vo", "endpoint_id": "fal-ai/gemini-3.1-flash-tts", "est_cost_usd": 0.02,
   "input": {"prompt": "Her sabah aynı koku. Taze çekilmiş kahve, sıcak su ve biraz sabır. Gerisi kendiliğinden gelir.", "language_code": "Turkish (Turkey)", "voice": "Kore", "style_instructions": "Warm, unhurried, intimate documentary narrator", "output_format": "mp3"}},
  {"id": "kf01", "endpoint_id": "bytedance/seedream/v5/pro/text-to-image", "est_cost_usd": 0.07,
   "input": {"prompt": "Macro of coffee beans pouring into a hand grinder, morning window light, warm tones", "image_size": {"width": 1080, "height": 1920}}},
  {"id": "kf02", "endpoint_id": "bytedance/seedream/v5/pro/text-to-image", "est_cost_usd": 0.07,
   "input": {"prompt": "Hot water poured in a slow spiral over a paper filter, steam rising, same warm morning light", "image_size": {"width": 1080, "height": 1920}}},
  {"id": "kf03", "endpoint_id": "bytedance/seedream/v5/pro/text-to-image", "est_cost_usd": 0.07,
   "input": {"prompt": "A filled ceramic cup on a wooden table by the window, steam, soft focus background", "image_size": {"width": 1080, "height": 1920}}}
]}
```

Measure the voice (`ffprobe` recipe A1, or a `fal-ai/ffmpeg-api/metadata` job with input `{"media_url": "@vo"}` and the job-level key `"download": false`, reading `result.media.duration` from the batch output). Say it is 11.4 s: three clips of 4 + 4 + 5 = 13 s leave a tail. **Checkpoint: approve voice and stills.** Stage 2:

```json
{"label": "kahve-short", "max_parallel": 4, "jobs": [
  {"id": "clip01", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 2.3,
   "input": {"prompt": "Beans tumble into the grinder, slight handheld drift, no people speaking", "image_url": "@kf01", "duration": "4", "resolution": "720p", "generate_audio": false}},
  {"id": "clip02", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 2.3,
   "input": {"prompt": "Water spirals over the grounds, the bloom rises, steam curls, static camera", "image_url": "@kf02", "duration": "4", "resolution": "720p", "generate_audio": false}},
  {"id": "clip03", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 2.9,
   "input": {"prompt": "Steam rises from the cup, light shifts slowly across the table, slow push-in", "image_url": "@kf03", "duration": "5", "resolution": "720p", "generate_audio": false}},
  {"id": "music", "endpoint_id": "elevenlabs/music/v2.5", "est_cost_usd": 0.6,
   "input": {"prompt": "Gentle acoustic guitar and soft piano, slow, warm, minimal, leaves room for a voice", "music_length_ms": 13000, "force_instrumental": true}}
]}
```

Assembly with ffmpeg: `assembly.md` recipes A2, A3, A4, A5. Without ffmpeg, first bring the music down (the compose schema has no volume field), then lay the timeline:

```json
{"label": "kahve-short", "max_parallel": 1, "jobs": [
  {"id": "music-low", "endpoint_id": "fal-ai/ffmpeg-api/loudnorm", "est_cost_usd": 0.01,
   "input": {"audio_url": "@music", "integrated_loudness": -30}}
]}
```

```json
{"label": "kahve-short", "max_parallel": 1, "jobs": [
  {"id": "timeline", "endpoint_id": "fal-ai/ffmpeg-api/compose", "est_cost_usd": 0.01, "download": false,
   "input": {"tracks": [
     {"id": "picture", "type": "video", "keyframes": [
       {"timestamp": 0, "duration": 4000, "url": "@clip01"},
       {"timestamp": 4000, "duration": 4000, "url": "@clip02"},
       {"timestamp": 8000, "duration": 5000, "url": "@clip03"}]},
     {"id": "voice", "type": "audio", "keyframes": [{"timestamp": 600, "duration": 11400, "url": "@vo"}]},
     {"id": "bed", "type": "audio", "keyframes": [{"timestamp": 0, "duration": 13000, "url": "@music-low"}]}]}}
]}
```

Compose returns `result.video_url` as a bare string: no file is written, but the URL is in the ledger, so save it with `pipeline.py fetch --label kahve-short --step timeline --out genmedia-output/kahve-short/kahve-short_final.mp4`. Timestamps and durations are milliseconds. Clips were generated with `generate_audio` false so nothing competes with the voice. This timeline is safe for compose because the clips come from one model at one size and frame rate, the voice is one file and the bed is exactly the cut's length: compose plays clips back to back and trims nothing (`assembly.md`, Timeline compose).

- Cost math: voice ~95 chars x $0.05/1000; stills 3 x $0.0675; clips 13 s x ~$0.5676 = ~$7.40; music $0.60 per started minute; utilities: cents.
- English voice: `fal-ai/elevenlabs/tts/eleven-v3` with `"text"` (not `prompt`), `"voice"`, `"stability"`.

## 3. Product still to ad clip

Upload and register the packshot (`@product`). Stage 1, hero variants, cheap and parallel:

```json
{"label": "serum-ad", "max_parallel": 3, "jobs": [
  {"id": "hero-a", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Place the exact product from the reference on wet black stone, soft rim light, water droplets; keep shape, label text and colors unchanged", "image_urls": ["@product"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}},
  {"id": "hero-b", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Place the exact product from the reference on pale sand with a palm shadow, morning sun; keep shape, label text and colors unchanged", "image_urls": ["@product"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}},
  {"id": "hero-c", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Place the exact product from the reference on a marble bathroom shelf, soft daylight, eucalyptus sprig; keep shape, label text and colors unchanged", "image_urls": ["@product"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}}
]}
```

QA gate (label legible, proportions right), then **checkpoint: the user picks the hero** (a creative pick; never choose for them). Stage 2, the end frame, edited from the chosen hero, never generated independently:

```json
{"label": "serum-ad", "max_parallel": 1, "jobs": [
  {"id": "endframe", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.08,
   "input": {"prompt": "Same scene and framing as the first image; the product now centered and slightly closer, droplets settled, clean space in the upper third; keep the product identical to the second image", "image_urls": ["@hero-a", "@product"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}}
]}
```

Stage 3, the move between the two frames (the prompt describes only the transition):

```json
{"label": "serum-ad", "max_parallel": 1, "jobs": [
  {"id": "reveal", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 2.9,
   "input": {"prompt": "Slow orbit of about 20 degrees toward the product, droplets run down the stone, light sweeps across the label, ends held still", "image_url": "@hero-a", "end_image_url": "@endframe", "duration": "5", "resolution": "720p", "generate_audio": false}}
]}
```

- Ad copy, prices and logos are never left to a video model. Add them in an editor, or build an end card with the typography routing of `image` and append it (recipe A8 turns a still into a clip).
- Format variants without re-generating: `fal-ai/workflow-utilities/scale-video` with `"video_url"`, `"width"`, `"height"`, `"mode": "pad"` or `"crop"`, or local recipe A2.
- Cost math: 3 heroes x $0.0675 + $0.0045 per extra reference; end frame ~$0.08; reveal 5 s x ~$0.5676.

## 4. Script to talking head

Register the portrait (`@portrait`; a real person needs consent, list it under Assumptions). Split the script so every chunk stays under the avatar model's audio limit (`fal-ai/bytedance/omnihuman/v1.5`: under 60 s at 720p, under 30 s at 1080p). Stage 1, voice chunks with identical settings:

```json
{"label": "welcome-avatar", "max_parallel": 2, "jobs": [
  {"id": "vo01", "endpoint_id": "fal-ai/elevenlabs/tts/eleven-v3", "est_cost_usd": 0.05,
   "input": {"text": "Hi, I'm Maya. Welcome to the team. In the next two minutes I'll show you where everything lives and who to ask when you get stuck.", "voice": "Rachel", "stability": 0.5}},
  {"id": "vo02", "endpoint_id": "fal-ai/elevenlabs/tts/eleven-v3", "est_cost_usd": 0.05,
   "input": {"text": "First, your laptop is already set up. Open the handbook from the dock, and start with the page called First Week.", "voice": "Rachel", "stability": 0.5}}
]}
```

Probe each chunk (must be under the limit), **checkpoint: approve the voice** (cents) before the avatar step (dollars). Stage 2:

```json
{"label": "welcome-avatar", "max_parallel": 2, "jobs": [
  {"id": "head01", "endpoint_id": "fal-ai/bytedance/omnihuman/v1.5", "est_cost_usd": 1.5,
   "input": {"image_url": "@portrait", "audio_url": "@vo01", "resolution": "720p"}},
  {"id": "head02", "endpoint_id": "fal-ai/bytedance/omnihuman/v1.5", "est_cost_usd": 1.3,
   "input": {"image_url": "@portrait", "audio_url": "@vo02", "resolution": "720p"}}
]}
```

Concatenate in order (recipe A3, or `fal-ai/ffmpeg-api/merge-videos`), then captions if wanted (`assembly.md`, Captions).

- Cost math: voice chars x $0.10/1000; avatar ~$0.16 per second of audio, so probe before you estimate.
- Turkish script: use the `vo` job of example 2. Drafts: `fal-ai/flashtalk` takes the same `image_url` + `audio_url`.
- Existing footage instead of a portrait is lipsync, not talking head: route through `video`.

## 5. Upscale and finishing chain

Inputs are finished, approved clips: earlier jobs (`"@clip01"`) or uploaded files registered with `pipeline.py add`. Probe first (recipe A1, or `fal-ai/ffmpeg-api/metadata` with the job-level `"download": false`): width, height, fps and duration drive the price. One stage:

```json
{"label": "harbor-film", "max_parallel": 4, "jobs": [
  {"id": "up01", "endpoint_id": "fal-ai/seedvr/upscale/video", "est_cost_usd": 0.25,
   "input": {"video_url": "@clip01", "upscale_mode": "target", "target_resolution": "1080p", "output_quality": "high"}},
  {"id": "up02", "endpoint_id": "fal-ai/seedvr/upscale/video", "est_cost_usd": 0.25,
   "input": {"video_url": "@clip02", "upscale_mode": "target", "target_resolution": "1080p", "output_quality": "high"}}
]}
```

- Cost math: $0.001 per megapixel of output video data = width x height x frames / 1,000,000. 1920x1080 x 120 frames is about $0.25; 2160p is four times that.
- Order: a deliverable up to 2048 px per side: merge first, upscale the one merged file (one job). Larger (2160p): upscale per clip as above, then concatenate locally with recipe A3, because `fal-ai/ffmpeg-api/merge-videos` limits width and height to 512-2048.
- Stills: `fal-ai/seedvr/upscale/image` with `"image_url"`, `"upscale_mode": "factor"`, `"upscale_factor": 2` (output under `image`, not `images`).
- Finish: loudness (recipe A5 or `fal-ai/ffmpeg-api/loudnorm`), delivery sizes (recipe A2 or `fal-ai/workflow-utilities/scale-video`). Upscale only approved finals; never upscale drafts to judge them.
