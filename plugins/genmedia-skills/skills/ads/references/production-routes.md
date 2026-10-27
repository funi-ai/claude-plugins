# Production routes: two worked ads

Two complete `gm.py batch` productions. Endpoint IDs were active and every input field below was read from the live OpenAPI schema on **2026-09-19**. They are a dated cache: repeat the Discovery guardrail in SKILL.md before spending. `gm.py`, `pipeline.py`, `frames.py`, `audiokit.py` and `adkit.py` abbreviate the calls shown in SKILL.md; run them from the project root (the ledger is `.genmedia/runs.jsonl` in the current directory). Prices are that day's hints: re-price with `gm.py price`.

## 1. Rules for every plan

- Plan keys: `label`, `max_parallel`, `jobs[]` with `id`, `endpoint_id`, `input`, optional `est_cost_usd` and `download`. `download` sits next to `input`; default `genmedia-output/<label>/<id>_{index}.{ext}`; `false` skips files.
- One `label` per ad. Ids are unique across the ad: `kf-presenter`, `vo-a`, `head-a`, `broll1`, `endcard`; re-rolls get a new id (`head-a-r2`).
- Whole-string references: `"@product"` (registered with `pipeline.py add`), `"@kf-presenter"` (first output), `"@kf-presenter[1]"` (second). `pipeline.py fill` writes nothing while one is unresolved. The helper refuses non-URL values only in top-level `*_url` and `*_urls` fields; nested fields (compose `tracks`, `images[].url`) have no net. Always fill, always run the filled file.
- Jobs in one plan are independent. A consumer of another job's output goes into a later stage file. Save templates with the Write tool as `.genmedia/projects/<slug>/stage-<n>.tmpl.json`.
- `{LOCK}` stands for the lock string from `plan.md`. Replace it before saving; `fill` refuses a placeholder that survived (`{LOCK}`, `{{TOKEN}}`, `<describe it>`) and names the JSON path of every hit. A bracket that belongs in the prompt is escaped `\{ \} \< \>` and the backslash is dropped on write.
- Seedream addresses references as `Figure 1`, `Figure 2`; GPT Image 2.5 as `image 1`, `image 2`. Order = order in `image_urls`. Product first.
- Every paid call: Bash timeout 600000 ms. `status: "pending"` → run the same command again.

## 2. Route choice in detail

| Question | A: native audio, one generation | B: TTS, talking head, b-roll |
|---|---|---|
| Spoken language | English, or another language after a probe. Boreal's model page names English as its validated language; Seedance publishes no language list. Turkish, one clip each, native listen on 2026-09-21 (`platform.md` section 10): Veo 3.1 Lite flawless (no longer listed on fal), Wan 3.0 right, every Seedance version mispronounced (ş as s, "merhala"; 2.0 Mini with a foreign accent) | Any language with a schema-verified TTS: `language_code` enum of `fal-ai/gemini-3.1-flash-tts` lists "Turkish (Turkey)", `language` enum of `xai/tts/v1` lists `tr` |
| Exact wording | No. The model may paraphrase, drop or mispronounce a word, brand names most of all | Yes. TTS speaks the text; listen once |
| Same voice across variants | No | Yes: same endpoint, `voice` and style text |
| Length | One take, 4 to 30 s (Seedance), 1 to 20 s (Boreal) | Any; every talking-head job under its audio limit |
| Cost shape | One big number per take; a re-roll repays all of it | Small parts; a re-roll repays one part |
| Typical 15 s cost | ~$8.50 Seedance 720p, ~$4 at 480p, ~$0.15 Boreal 720p | ~$2.50 with draft b-roll, ~$7 with Seedance b-roll |

Non-English on route A is a probe, not a plan: one short clip with the hardest line (brand name included). Turkish: `alibaba/wan-3.0/image-to-video` (`start_image_url`, `"resolution": "480p"`, `"duration": 5`; ~$0.25); not Seedance, whose Turkish failed a native listen. Veo 3.1 Lite passed it too but is no longer listed on fal. A transcript is a cheap first filter for wrong words: `audiokit.py extract <clip> --out .genmedia/tmp/probe.mp3`, `gm.py upload` it, run `fal-ai/elevenlabs/speech-to-text/scribe-v2` on the mp3 (under a cent; Scribe rejects an mp4 with a video stream; without local ffmpeg `fal-ai/wizper` takes the mp4 with `"language": "tr"`). It does not hear mispronunciation (it wrote Seedance 2.0's "merhala" as "Merhaba"), so the user's listen decides. Any word off → another take or route B. Kling v3 is never the probe: it speaks Chinese or English and translates the rest to English.

Hybrid that is often right: route B for the speech, plus one or two Seedance b-roll clips with `generate_audio: true` for ambience under the voice (local mix only).

## 3. Turning prices into dollars

`gm.py price <ids> --explain` → per row `unit_price`, `unit`, and `pricing_text` when the unit needs reading.

| Job | Formula | Example (2026-09-19) |
|---|---|---|
| Seedream still | per image; +$0.0045 per input image after the first; doubles above 1536x1536 area | 2 candidates, 2 references: 2 x ($0.0675 + $0.0045) = $0.15 |
| GPT Image 2.5 card | `1 units` is not a price: size and quality row in `routing-image.md` (`t2i-typography` notes), plus the reference allowance in `platform.md` §7 per input image after the first | 1152x2048 at `high`, picture + logo: about $0.08 + the allowance = $0.13 |
| Seedance clip | tokens = height x width x seconds x 24 / 1024; x $0.02568 per 1000 tokens (720p and below, US endpoint, 2026-10-21) | 720x1280, 8 s: 172,800 tokens = $4.44 |
| Boreal, MiniMax clip | per second at the chosen resolution x seconds | MiniMax 768P 5 s: $0.20 (launch discount ended 2026-09-30) |
| Talking head | per second x measured voice seconds (`on_camera_s` from `adkit.py check` until measured) | OmniHuman 8.5 s: $1.36 |
| Voice | characters / 1000 x price (`chars_total` from `adkit.py check`) | 184 chars on Gemini TTS: $0.01 |
| Music | per started minute | $0.60 |
| Captions | per minute of video, one minute minimum on `veed/subtitles` | $0.03 auto-subtitle, $0.10 veed basic preset |
| fal utilities | cents per call | $0.01 each |

Add every stage and every planned variant, round up, say "about", say re-rolls are extra. Put each job's share into `est_cost_usd` so `gm.py ledger --label <slug> --sum` matches the card.

## 4. Plan A: one speaking take (English, 8 s, 9:16)

Insulated bottle. Facts sheet: "keeps drinks cold for 24 hours" (user's spec sheet). Script passed `adkit.py check` (18 words, budget 18; the hook's "six pm" is flagged as a number and carries the same source as "24 hours"), written in the second person: a generated presenter has no experience of her own to report. Presenter: generated, disclosed.

```text
gm.py upload ./norda-front.jpg
pipeline.py add --label norda-ugc --step product --path ./norda-front.jpg --url <cdn_url>
```

Stage 1a, `stage-1a.tmpl.json` (no references; run directly). The plate shows a person only, never the product:

```json
{"label": "norda-ugc", "max_parallel": 1, "jobs": [
  {"id": "presenter", "endpoint_id": "bytedance/seedream/v5/pro/text-to-image", "est_cost_usd": 0.07,
   "input": {"prompt": "Phone selfie video still of a woman in her late twenties in a parked car, daylight through the windscreen, natural skin texture, no makeup look, grey hoodie, relaxed half smile, looking into the lens, one hand free and visible at chest height. Unpolished phone-camera look, slight wide-angle distortion. No text, no logos.", "image_size": {"width": 1080, "height": 1920}, "num_images": 1, "output_format": "png"}}
]}
```

An `@handle` or the user's own photo (consent confirmed) replaces this stage: register its reference URL as `presenter`. Stage 1b, `stage-1b.tmpl.json`, the keyframe:

```json
{"label": "norda-ugc", "max_parallel": 1, "jobs": [
  {"id": "kf-presenter", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.15,
   "input": {"prompt": "Figure 1 is the real product; Figure 2 is the presenter. {LOCK} The woman from Figure 2, same face, hair, hoodie and car interior, holds the bottle from Figure 1 upright in her right hand at chest height, label facing the lens and unobstructed, fingers around the lower third. True scale: the bottle is 26 cm tall. She looks into the lens, mouth closed, about to speak. Phone selfie framing, head and shoulders in the upper two thirds, calm area above her head. Exactly one bottle. No added text, badges or logos.", "image_urls": ["@product", "@presenter"], "image_size": {"width": 1080, "height": 1920}, "num_images": 2, "output_format": "png"}}
]}
```

QA both candidates against `norda-front.jpg` (label, shape, colour, count, five fingers). **Checkpoint 1: the user picks one** (`@kf-presenter[1]` = candidate 2). Stage 2, `stage-2.tmpl.json`, the take:

```json
{"label": "norda-ugc", "max_parallel": 1, "jobs": [
  {"id": "take", "endpoint_id": "bytedance/seedance-2.5/us/image-to-video", "est_cost_usd": 4.5,
   "input": {"prompt": "Handheld phone selfie, slight natural sway, one continuous take, no cuts. The woman speaks to the lens in casual American English, natural pace: \"Your iced coffee, still iced at six pm. Norda keeps it cold for 24 hours. Link's below.\" She lifts the bottle a little on the word Norda and keeps the label toward the camera. Quiet car interior ambience, no music, no on-screen text, no subtitles.", "image_url": "@kf-presenter[1]", "duration": "8", "resolution": "720p", "generate_audio": true}}
]}
```

Draft or budget take, same stage and keyframe, `creatify/boreal` (~$0.08):

```json
{"id": "take-draft", "endpoint_id": "creatify/boreal", "est_cost_usd": 0.08,
 "input": {"prompt": "[VISUAL] Handheld phone selfie in a parked car, one continuous take. The woman talks to the lens and lifts the steel bottle slightly, label toward the camera. [SPEECH] Your iced coffee, still iced at six pm. Norda keeps it cold for 24 hours. Link's below. [SOUNDS] Quiet car interior, no music.", "image_url": "@kf-presenter[1]", "duration": 8, "resolution": "720p", "aspect_ratio": "auto", "manifest_disclosure": false}}
```

- Seedance: `duration` is a string enum `"4"`..`"30"`; image-to-video takes its ratio from the keyframe. Boreal: `duration` is a number 1-20; leave `[TEXT]` out (copy comes from the end card and captions); `"manifest_disclosure": true` burns a visible "AI-generated" label when the user wants the disclosure inside the video.
- QA: `frames.py sheet` and `probe` (`has_audio` true, 8 s). **Checkpoint 2:** you cannot hear; the user checks every word, above all "Norda" and "24".
- Finish: end card (`static-formats.md`, format `end-card`), section 6 steps 4 and 5 with one part plus the card, captions (section 7). Card total: about $4.90 quality, about $0.45 draft.

## 5. Plan B: voice, talking head, b-roll, mux (Turkish, 15 s, 9:16)

Olive oil from a `product-photoshoot` project: its lock string and approved hero are reused. Script (`adkit.py check`: 29 words, 184 characters, `on_camera_s` 8.5): block a on camera = hook + problem, block b voice-over = product + proof, block c on camera = CTA. One TTS job per block, identical voice settings.

Stage 1, voice and keyframes together (`@product`, `@presenter` registered as in plan A):

```json
{"label": "zd-ad", "max_parallel": 4, "jobs": [
  {"id": "vo-a", "endpoint_id": "fal-ai/gemini-3.1-flash-tts", "est_cost_usd": 0.01,
   "input": {"prompt": "Salatanın tadı neden hep aynı, biliyor musun? Çünkü yağın bir tadı yok.", "language_code": "Turkish (Turkey)", "voice": "Aoede", "style_instructions": "Friendly home cook talking to a friend, lively, natural pace, slight smile", "output_format": "mp3"}},
  {"id": "vo-b", "endpoint_id": "fal-ai/gemini-3.1-flash-tts", "est_cost_usd": 0.01,
   "input": {"prompt": "Zeytin Dalı: erken hasat, soğuk sıkım natürel sızma. Ayvalık zeytininden, tek kaynaktan.", "language_code": "Turkish (Turkey)", "voice": "Aoede", "style_instructions": "Friendly home cook talking to a friend, lively, natural pace, slight smile", "output_format": "mp3"}},
  {"id": "vo-c", "endpoint_id": "fal-ai/gemini-3.1-flash-tts", "est_cost_usd": 0.01,
   "input": {"prompt": "Bir kaşık dene, farkı anla.", "language_code": "Turkish (Turkey)", "voice": "Aoede", "style_instructions": "Friendly home cook talking to a friend, lively, natural pace, slight smile", "output_format": "mp3"}},
  {"id": "kf-presenter", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.15,
   "input": {"prompt": "Figure 1 is the real product; Figure 2 is the presenter. {LOCK} The woman from Figure 2, same face and clothes, stands at a home kitchen counter and holds the bottle from Figure 1 upright beside her shoulder, label facing the lens and unobstructed. She looks into the lens, mouth closed, about to speak. Chest-up framing, eye level, soft window light from the left, calm area above her head. Exactly one bottle. No added text.", "image_urls": ["@product", "@presenter"], "image_size": {"width": 1080, "height": 1920}, "num_images": 2, "output_format": "png"}},
  {"id": "kf-pour", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Figure 1 is the real product. {LOCK} Close shot on the same kitchen counter: the bottle stands on the right third, label sharp, next to a wooden bowl of green salad; a thin stream of golden oil has just been poured over the leaves. Soft window light from the left. Exactly one bottle. No added text.", "image_urls": ["@product"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}},
  {"id": "kf-hero", "endpoint_id": "bytedance/seedream/v5/pro/edit", "est_cost_usd": 0.07,
   "input": {"prompt": "Figure 1 is the real product. {LOCK} The bottle alone on pale oak, olive branches softly out of focus behind it, warm morning light, bottle centred in the lower two thirds, calm empty area in the upper third. Exactly one bottle. No added text.", "image_urls": ["@product"], "image_size": {"width": 1080, "height": 1920}, "output_format": "png"}}
]}
```

Measure the voice, then fix every length from it:

```text
audiokit.py probe genmedia-output/zd-ad/vo-a_0.mp3 genmedia-output/zd-ad/vo-b_0.mp3 genmedia-output/zd-ad/vo-c_0.mp3
```

Say 5.2 s, 5.4 s and 2.4 s: 13.0 s of speech + 1.8 s end card + pauses at the joins = 15 s. Over target → cut words and re-roll that block under a new id; never speed the voice up. **Checkpoint 1: keyframes and the three voice files.**

Stage 2, clips. Heads only for blocks a and c; b-roll silent and at least as long as `vo-b`:

```json
{"label": "zd-ad", "max_parallel": 4, "jobs": [
  {"id": "head-a", "endpoint_id": "fal-ai/bytedance/omnihuman/v1.5", "est_cost_usd": 0.85,
   "input": {"image_url": "@kf-presenter", "audio_url": "@vo-a", "resolution": "720p", "prompt": "She talks to the camera like to a friend, small natural head movements, keeps the bottle still beside her shoulder"}},
  {"id": "head-c", "endpoint_id": "fal-ai/bytedance/omnihuman/v1.5", "est_cost_usd": 0.4,
   "input": {"image_url": "@kf-presenter", "audio_url": "@vo-c", "resolution": "720p", "prompt": "She smiles, nods once and tips the bottle slightly toward the camera"}},
  {"id": "broll1", "endpoint_id": "minimax/h3-max-turbo/image-to-video", "est_cost_usd": 0.1,
   "input": {"prompt": "Golden oil keeps pouring in a thin steady stream over the salad leaves, slow push-in, the bottle stays still and unchanged, no people, no text", "image_url": "@kf-pour", "duration": 5, "resolution": "768P", "prompt_expansion_mode": "disabled"}},
  {"id": "broll2", "endpoint_id": "minimax/h3-max-turbo/image-to-video", "est_cost_usd": 0.1,
   "input": {"prompt": "Slow orbit of about 15 degrees around the bottle, morning light sweeps across the label, olive branches sway slightly, the bottle stays still and unchanged, no text", "image_url": "@kf-hero", "duration": 5, "resolution": "768P", "prompt_expansion_mode": "disabled"}}
]}
```

- Quality b-roll: `bytedance/seedance-2.5/us/image-to-video` with `"image_url"`, `"duration": "4"`, `"resolution": "720p"`, `"generate_audio": false` (~$2.25 per 4 s clip). Draft heads: `veed/fabric-1.0` with `image_url`, `audio_url` and the required `"resolution": "480p"` (~$0.08/s). OmniHuman limits: audio under 60 s at 720p, under 30 s at 1080p; `resolution` defaults to 1080p.
- Cheapest head to probe: `creatify/boreal` with `image_url`, `audio_url` and `duration`, ~$0.01/s at 720p. It keeps the supplied audio, and on a Turkish voice the mouth followed it (closed in pauses, rounded on "Bugün" and "ekşi"; 2026-09-21, like OmniHuman). `duration` is rounded to a legal frame count (9.2 gave 9.04 s), and a voice longer than that loses its end: ask for the next whole second above the voice length. A native listener rated Boreal passable and OmniHuman better, neither flawless: Boreal for drafts, OmniHuman for the final. One block, the user watches and listens, then decide.
- MiniMax generates its own soundtrack; the assembly drops it (`-an`). Its `prompt_expansion_mode` is required: `disabled` keeps the product wording you wrote.
- QA: a `frames.py sheet` per clip; `frames.py probe` on the heads: duration equals the voice, `has_audio` true (false → mux that voice back on with step 3's command). **Checkpoint 2: clips; the user listens to the heads.**

Stage 3, music and end card in one plan (end card job: `static-formats.md`, format `end-card`):

```json
{"id": "music", "endpoint_id": "elevenlabs/music/v2.5", "est_cost_usd": 0.6,
 "input": {"prompt": "Light acoustic guitar and soft hand percussion, warm, Mediterranean kitchen mood, steady, leaves room for a voice, clean ending", "music_length_ms": 15000, "force_instrumental": true}}
```

Card total: stills $0.36 (presenter plate included) + voice $0.03 + heads $1.25 + b-roll $0.20 + music $0.60 + end card $0.08 + captions $0.10 = about $2.65 (about $6.95 with Seedance b-roll).

## 6. Assembly, local ffmpeg (`ffmpeg.found` true)

Commands were run on 2026-09-19 with ffmpeg 9.0.1 on synthetic clips of these sizes. ffmpeg writes only under `genmedia-output/<slug>/`; media file names below are shortened and live there. The two concat lists are written with the Write tool under `.genmedia/tmp/` (a `printf >` redirect or a list under `genmedia-output/` prompts); each line holds an absolute path, `file '<project>/genmedia-output/<slug>/<part>.mp4'` (`<project>` = the absolute project directory; a relative path would resolve against `.genmedia/tmp/`). `VF` is shorthand, not a filter: paste `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30` in its place in every command (16:9: swap the numbers; letterbox instead of crop: `force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2`).

```bash
# 1. heads: one size, rate and codec; they keep their own audio
ffmpeg -hide_banner -loglevel error -i head-a_0.mp4 -vf "VF" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -ac 2 n_head-a.mp4
# 2. b-roll: trim each to its share of vo-b (2 x 2.8 s >= 5.4 s), drop its sound, join
ffmpeg -hide_banner -loglevel error -t 2.8 -i broll1_0.mp4 -an -vf "VF" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p n_broll1.mp4
#    Write .genmedia/tmp/zd-ad-broll.txt: one line per b-roll part, file '<project>/genmedia-output/zd-ad/n_broll1.mp4', then n_broll2
ffmpeg -hide_banner -loglevel error -f concat -safe 0 -i .genmedia/tmp/zd-ad-broll.txt -c copy broll.mp4
# 3. voice onto the b-roll; apad + -shortest end the file with the picture, so the voice is never cut
ffmpeg -hide_banner -loglevel error -i broll.mp4 -i vo-b_0.mp3 -map 0:v:0 -map 1:a:0 -c:v copy -af apad -c:a aac -b:a 192k -ar 48000 -ac 2 -shortest n_broll-vo.mp4
# 4. end card still to a 1.8 s clip with a silent track
ffmpeg -hide_banner -loglevel error -loop 1 -framerate 30 -i endcard_0.png -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 -t 1.8 -vf "VF" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 -ac 2 -shortest n_endcard.mp4
# 5. join in script order
#    Write .genmedia/tmp/zd-ad-cut.txt: n_head-a, n_broll-vo, n_head-c, n_endcard, each as file '<project>/genmedia-output/zd-ad/<part>.mp4'
ffmpeg -hide_banner -loglevel error -f concat -safe 0 -i .genmedia/tmp/zd-ad-cut.txt -c copy zd-ad_cut.mp4
# 6. music under everything; DUR from frames.py probe on the cut (15.0 here), fade starts at DUR - 1
ffmpeg -hide_banner -loglevel error -i zd-ad_cut.mp4 -i music_0.mp3 -filter_complex "[1:a]aresample=48000,atrim=duration=15.0,volume=0.18,afade=t=out:st=14.0:d=1[bed];[0:a][bed]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v:0 -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart zd-ad_final.mp4
```

Every part must have an audio stream and identical parameters or `-c copy` breaks the join: repeat step 1 for each head and step 2 for each b-roll clip. `normalize=0` keeps the voice at full level. Register the result: `pipeline.py add --label zd-ad --step final --path genmedia-output/zd-ad/zd-ad_final.mp4 --tool ffmpeg --from head-a,broll1,broll2,head-c,endcard,vo-b,music`.

## 7. Assembly without ffmpeg, and captions

Compose concatenates more than it places (measured 2026-09-21, `platform.md` section 10): one picture track per request (an image track counts as one), clips back to back from 0 at the first clip's size and frame rate, gaps and keyframe durations ignored; an audio track honours only its first keyframe's timestamp; a clip's own audio is dropped as soon as an audio track exists. So every part is cut to its planned length and brought to one size and frame rate first, and the voice becomes one file. Lengths come from a `fal-ai/ffmpeg-api/metadata` job per file (input `{"media_url": "@vo-a"}`, job-level `"download": false`, read `result.media.duration` from the batch output). Three small fal stages (four when a part needs scaling), cents in total, then a check:

1. **Cut to length** (one plan): `fal-ai/workflow-utilities/trim-video` per part (job ids `t-head-a`, `t-broll1`, `t-broll2`, `t-head-c`) with `"start_time": 0` and `"duration"` in seconds: each head to its voice length (OmniHuman runs a few frames past its audio), the b-roll clips to shares that add up to `vo-b` (2.8 + 2.6 s for a 5.4 s line); trim is frame-exact and keeps any audio. A part that is not 9:16 (the MiniMax b-roll is 768x1344) goes through `fal-ai/workflow-utilities/scale-video` in a stage of its own before this one, with `"width": 1080`, `"height": 1920` and `"mode": "crop"` (the default `stretch` distorts); its trim then reads the scaled clip. The end card, job `card-clip`: `fal-ai/ffmpeg-api/images-to-video` with `"images": [{"url": "@endcard", "frames": 60}]` and `"fps": 30`, 2.0 s so the cut stays at 15.0 s (it held the last image a frame or more too long: probe it, trim if it matters). In the same plan: job `voice`, `fal-ai/ffmpeg-api/merge-audios` with `"audio_urls": ["@vo-a", "@vo-b", "@vo-c"]` (joins end to end, no gaps: 13.0 s here), and `@music-low`, a `fal-ai/ffmpeg-api/loudnorm` job on `@music` with `"integrated_loudness": -30` (there is no volume field anywhere on this route).
2. **One picture**: job `cut`, `fal-ai/ffmpeg-api/merge-videos` with `"video_urls": ["@t-head-a", "@t-broll1", "@t-broll2", "@t-head-c", "@card-clip"]`, `"target_fps": 30` and `"resolution": {"width": 1080, "height": 1920}`. It converts frame rates, scales, keeps each part's length and pads silent parts. Its result also lists the input clips as URLs, so the download template fetches them again: the cut is the `_0` file.
3. **Sound on the picture**, the timeline job:

```json
{"label": "zd-ad", "max_parallel": 1, "jobs": [
  {"id": "timeline", "endpoint_id": "fal-ai/ffmpeg-api/compose", "est_cost_usd": 0.01, "download": false,
   "input": {"tracks": [
     {"id": "picture", "type": "video", "keyframes": [{"timestamp": 0, "duration": 15000, "url": "@cut"}]},
     {"id": "voice", "type": "audio", "keyframes": [{"timestamp": 0, "duration": 13000, "url": "@voice"}]},
     {"id": "bed", "type": "audio", "keyframes": [{"timestamp": 0, "duration": 15000, "url": "@music-low"}]}]}}
]}
```

Then **save and check** locally: the result is a bare string at `result.video_url`: `pipeline.py fetch --label zd-ad --step final --url <video_url> --out genmedia-output/zd-ad/zd-ad_final.mp4 --endpoint fal-ai/ffmpeg-api/compose`. Probe it: duration equal to the cut (a bed longer than the cut makes the file longer, because compose trims nothing), `has_audio` true. Voice and bed are each lowered while they overlap, so the mix comes out quieter than the parts; the user listens.

A voice that should start later than 0 takes that offset as its keyframe `timestamp`; only the first keyframe's timestamp counts, later keyframes in the track follow without a gap. The two-call shortcut without music: `fal-ai/ffmpeg-api/merge-audio-video` (`video_url`, `audio_url`) on the cut; it replaces the cut's own audio and is as long as the shorter input, so give picture and voice the same length.

Captions, always last, after the cut is approved (a local cut goes through `gm.py upload` first; the captioned result becomes the final and is registered like it):

| Need | Endpoint and fields | Notes |
|---|---|---|
| Exact text you hold (any language, Turkish included) | `veed/subtitles`: `video_url`, `preset` (required; `simple`, `plain`, `karl`, `hustle` are basic, `glass`, `fusion`, `glide` are dynamic at double price), `srt_content` or `srt_file_url`, `language` (`tr-TR` is in the enum), `customization.position` `top` / `center` / `bottom` | Write the SRT from the approved script and the measured block starts: no transcription, no misspelled brand name |
| Fast word-highlight captions | `fal-ai/workflow-utilities/auto-subtitle`: `video_url`, `language` (two-letter code, default `en`; `tr` works), `words_per_subtitle` 1-12, `font_size` 20-150, `position`, `y_offset`, `highlight_color`, `font_name` | It transcribes: read `result.transcription` against the script; a wrong brand name is burned in. A Turkish line came back exact on 2026-09-21 |
| The user's editor or the ad platform adds them | sidecar `.srt` written with the Write tool | Free; stays editable |

Keep captions out of the bottom fifth and the right edge on 9:16: platform buttons sit there (check the platform's current safe zones).
