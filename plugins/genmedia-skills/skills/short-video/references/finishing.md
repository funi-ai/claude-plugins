# Finishing: measure, caption, cut, mix, composite, deliver

Everything after the clips exist. Deterministic work never goes through a generative model. Two routes, chosen once from `gm.py preflight`: **local ffmpeg** (`ffmpeg.found` true: free, exact, the only route with real mixing, cutaways and timed overlays) or **fal utilities** (URLs in, URL out, cents per call, hard cuts only). Local recipes were run on 2026-09-19 with ffmpeg 9.0.1 on macOS using core filters only (`scale`, `crop`, `fps`, `trim`, `overlay`, `fade`, `xfade`, `amix`, `sidechaincompress`, `adelay`, `concat` demuxer). They do not need `drawtext`, `subtitles` or libass, which many builds lack. Utility fields were read from the live schemas the same day.

Rules for local commands: file names below are shortened; the batch saved outputs as `genmedia-output/<slug>/<id>_<index>.<ext>` (`pipeline.py urls --label <slug>` lists them). ffmpeg writes only under `genmedia-output/<slug>/` (the batch already created it; never `mkdir`), text files it reads (concat lists) are written with the Write tool under `.genmedia/tmp/`, one command per Bash call (no `for` loops, no `printf >` redirects: they prompt); add `-hide_banner -loglevel error`, never `-y` outside that folder, and register every product: `pipeline.py add --label <slug> --step <id> --path <file> --tool ffmpeg --from <ids>`. `gm.py`, `pipeline.py`, `frames.py`, `audiokit.py` abbreviate the quoted calls of SKILL.md.

## 1. Measure the voice, write the captions (after stage 1)

**C1. Word timings → sidecar captions → beat times.** Take the voice URL from `pipeline.py urls --label <slug>`, write `.genmedia/projects/<slug>/stt.json`:

```json
{"audio_url": "<CDN URL of vo>", "diarize": false, "tag_audio_events": false}
```

```text
gm.py run fal-ai/elevenlabs/speech-to-text/scribe-v2 --input .genmedia/projects/<slug>/stt.json --label <slug> --no-download --est-cost 0.01 | audiokit.py captions --input - --out-base genmedia-output/<slug>/<slug> --formats srt,txt --max-chars 32 --max-lines 2
```

- It writes `<slug>.srt`, `<slug>.txt` and `<slug>.result.json` (the raw words). Bash timeout 600000 ms; `status: "pending"` passes through: run the printed `gm.py wait ... --no-download` into the same `captions` call.
- **Beat times**: in `<slug>.result.json`, the `start` of each sentence's first word is that beat's boundary. Update the beat sheet and the ordered durations before any clip is paid for.
- **Spelling**: you hold the script, the transcript is a guess. Compare `<slug>.txt` with the script and correct names and Turkish characters in the `.srt` with the Edit tool; timings stay. When the text must be exact everywhere, run `fal-ai/elevenlabs/forced-alignment` (`audio_url`, `text`) through the same pipe instead; it bills per started hour (about $0.22 on 2026-09-19), so align once.
- Burn-in version of the cues (short lines for 9:16): `audiokit.py captions --input genmedia-output/<slug>/<slug>.result.json --out-base genmedia-output/<slug>/<slug>_burn --formats srt --max-chars 24 --max-lines 1 --max-duration 2.5`.
- A voice that starts later than 0.0 s in the cut (lead-in): pass `--offset <seconds>`. F10: transcribe the extracted span, not the whole episode.

**Voice too long for the beat sheet** (over budget by more than 0.5 s): shorten the script and regenerate the voice (cents). Never speed the voice up past 5%, never let the picture run past the target to fit it.

## 2. Local cut (S-recipes)

**S1. Probe** every input: `frames.py probe <clip>` (duration, size, fps, audio) and `audiokit.py probe <audio>...`.

**S2. Trim to the beat and normalize, picture only.** One working size for every part; sound is built separately (S4):

```bash
ffmpeg -hide_banner -loglevel error -ss 0.5 -i clip02_0.mp4 -frames:v 84 -an -vf "scale=720:1280:force_original_aspect_ratio=increase:flags=lanczos,crop=720:1280,setsar=1,fps=24" -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p n02.mp4
```

- `fps=` is the rate most clips already have (`frames.py probe`; generated clips are usually 24). Converting 24 to 30 only duplicates frames and raises the upscale price by a quarter. One rate for every part, the end card included.
- `-ss` = where the beat's action starts inside the clip; `-frames:v` = the beat's length in frames (seconds x fps, rounded; 3.5 s at 24 fps is 84). The last part takes `DUR` x fps minus the frames of all the others, so the cut is exactly `DUR`. Never `-t` per part: each part rounds up to a whole frame, and four parts made 15.04 s of a 15 s sheet on 2026-09-21. Keep the hold: trim surplus from the head of the last shot, not its tail.
- Free finish (section 5): use `1080:1920` in both places instead of `720:1280`. 16:9: `1280:720` or `1920:1080`.
- Chained link: drop the duplicated first frame by starting the filter with `trim=start_frame=1,setpts=PTS-STARTPTS,`.
- Keep a clip's native sound (F1, F6): replace `-an` with `-c:a aac -ar 48000 -ac 2`; then every part needs an audio stream (silent parts: add `-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000` as second input with `-map 0:v:0 -map 1:a:0 -shortest`).
- A user's screen recording or footage is normalized the same way.

**S3. Concatenate** (hard cuts; identical parameters after S2, so no re-encode):

Write `.genmedia/tmp/<slug>-list.txt` with the Write tool (pre-approved; `genmedia-output/` is not), one line per part in play order: `file '<project>/genmedia-output/<slug>/n01.mp4'`, `file '<project>/genmedia-output/<slug>/n02.mp4'`, ..., where `<project>` is the absolute project directory Then:

```bash
ffmpeg -hide_banner -loglevel error -f concat -safe 0 -i .genmedia/tmp/<slug>-list.txt -c copy genmedia-output/<slug>/<slug>_cut.mp4
```

A relative path in the list would resolve against `.genmedia/tmp/`, not the project. Probe the cut: its duration is `DUR` for everything below and equals the beat sheet's length, never more.

**S4. Sound bed: voice over ducked music, optional effect, cut to `DUR`:**

```bash
ffmpeg -hide_banner -loglevel error -i vo_0.mp3 -i music_0.mp3 -i sfx01_0.mp3 -filter_complex "[0:a]aresample=48000,apad,atrim=duration=30,asplit=2[vo][key];[1:a]aresample=48000,atrim=duration=30,volume=0.35,afade=t=out:st=28.5:d=1.5[bed];[bed][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];[2:a]aresample=48000,adelay=3000:all=1,volume=0.8,apad,atrim=duration=30[fx];[vo][duck][fx]amix=inputs=3:duration=first:normalize=0[mix]" -map "[mix]" -c:a aac -b:a 192k genmedia-output/<slug>/bed.m4a
```

- Replace every `30` with `DUR` and `28.5` with `DUR - 1.5`. `adelay=3000` places the effect at 3.0 s (milliseconds); one `[n:a]...adelay` branch per effect and raise `inputs`. No effect: drop input 2, the `[fx]` branch, and use `inputs=2`. A voice lead-in: `adelay=<ms>:all=1` before `apad` in the voice branch (and the same `--offset` for captions).
- `normalize=0` keeps `amix` from halving the voice; padding the voice first keeps the compressor from ending early. No voice (F1, F6, F7): `volume=0.8` and no `sidechaincompress`.
- Music delayed to the transition (F7): `adelay` in the music branch before `atrim`.

**S5. Loudness**: `audiokit.py loudnorm genmedia-output/<slug>/bed.m4a --out genmedia-output/<slug>/bed_norm.m4a` (defaults -16 LUFS, true peak -1.0).

**S6. Mux**:

```bash
ffmpeg -hide_banner -loglevel error -i <slug>_cut.mp4 -i bed_norm.m4a -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart genmedia-output/<slug>/<slug>_mix.mp4
```

**S7. Cutaway over a join** (F9: b-roll covers the jump between two talking-head chunks while their audio continues). Base = the concatenated head clips WITH audio; the b-roll part is already normalized:

```bash
ffmpeg -hide_banner -loglevel error -i heads.mp4 -i n_broll.mp4 -filter_complex "[1:v]trim=duration=2.5,setpts=PTS-STARTPTS+9.0/TB[b];[0:v][b]overlay=0:0:enable='between(t,9.0,11.5)':eof_action=pass[v]" -map "[v]" -map 0:a -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -c:a copy -movflags +faststart heads_cutaway.mp4
```

`9.0` = start of the cutaway (about 1 s before the join), `2.5` = its length, `11.5` = start + length.

**S8. Wipe instead of a generated transition** (F7 fallback when the first + last frame clip morphs badly: one clip per state, then):

```bash
ffmpeg -hide_banner -loglevel error -i n_before.mp4 -i n_after.mp4 -filter_complex "[0:v][1:v]xfade=transition=wipeleft:duration=0.6:offset=2.9[v]" -map "[v]" -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p wipe.mp4
```

`offset` = first part's duration minus the transition; the result is shorter by the transition's duration. Other values: `wiperight`, `slideup`, `fade`. Use at most one transition style per video.

## 3. Composite: text, logo, labels, end card

Exact words never come from a video model. Sources for the pixels, in this order:

1. **The user's files**: logo PNG, designed cards, brand fonts rendered by their designer.
2. **A transparent text overlay from a typography-capable image model.** `openai/gpt-image-2.5/flare/text-to-image` (active, schema read 2026-09-19): `"background": "transparent"`, `"output_format": "png"`, `"image_size": {"width": 1088, "height": 1920}` (both sides must be multiples of 16; crop to 1080 wide in the overlay), `"quality"` default `high`; token-priced, about $0.05-0.10 per overlay: read `pricing_text`. Prompt: the exact words in quotes, the weight, the colour, the position inside the safe box of `platforms.md` ("centred horizontally, between 18% and 30% of the height"), "transparent background, nothing else". Read the PNG: every letter, every Turkish character (ğ, ş, ı, İ, ö, ü, ç). A typo is a re-roll with the word spelled out letter by letter, never a delivery.
3. **An opaque end card** from the same model (logo description only if the user owns the brand; better: their logo file placed by them), or the end-card background of `craft.md` plus an overlay from 2.
4. None of these possible → list the texts under "Left for your editor" in the delivery message with their times and positions. Do not fake text with a video prompt.

**T1. Timed overlay with fades** (hook text, labels, CTA line, logo):

```bash
ffmpeg -hide_banner -loglevel error -i <slug>_mix.mp4 -loop 1 -framerate 24 -t 30 -i hook_text.png -filter_complex "[1:v]format=rgba,crop=1080:1920,scale=720:1280,fade=t=in:st=0:d=0.2:alpha=1,fade=t=out:st=1.4:d=0.3:alpha=1[t];[0:v][t]overlay=0:0:shortest=1[v]" -map "[v]" -map 0:a -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -c:a copy -t 30 -movflags +faststart genmedia-output/<slug>/<slug>_text.mp4
```

- Both `30` = `DUR`, and the loop input's `-framerate` equals the cut's rate; without them the output grows past the cut. Fade times are absolute: for a CTA from 27.0 s use `fade=t=in:st=27.0:d=0.2:alpha=1` and no fade-out. Hard on/off without fades: drop `-loop 1 -framerate 24 -t 30` and the fades, use `overlay=0:0:enable='between(t,0,1.5)'`.
- A small PNG (logo): `scale=<width>:-1` and `overlay=(W-w)/2:H*0.18`. Several overlays: chain them, `[v1][t2]overlay=...[v2]`.
- Working size 720x1280: keep `scale=720:1280`; on a 1080x1920 master drop it.

**T2. End card as a part** (before S3): `ffmpeg -hide_banner -loglevel error -loop 1 -framerate 24 -t 2 -i card.png -vf "scale=720:1280:force_original_aspect_ratio=increase:flags=lanczos,crop=720:1280,setsar=1" -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p card.mp4`, then list it last in `list.txt`. Music resolves under it; the CTA holds at least words / 3 s, minimum 1.5 s.

## 4. Captions in the picture

Sidecar `<slug>.srt` is always delivered when there is speech. Burn-in is an extra, last step, after any upscale (every later re-encode softens text):

| Route | Use when | Input and notes |
|---|---|---|
| `veed/subtitles` | you hold the exact cues (`<slug>_burn.srt`), in any language, or names matter | `video_url`*, `preset`* (basic 1x: `simple`, `plain`, ...; dynamic 2x: `glass`, `fusion`, `glide`, ...), `srt_content` (paste the SRT text: no transcription), `language` (enum, lists `tr-TR`), `customization.position` `top`/`center`/`bottom`. About $0.10 per input minute, 1 minute minimum, x2 above 1080p: for a 1080x1920 master quote $0.20. Output `video`. |
| `fal-ai/workflow-utilities/auto-subtitle` | word-highlight style, no exact text needed | `video_url`*, `language` (two-letter code, default `en`; `"tr"` transcribed and burned a Turkish line exactly on 2026-09-21), `words_per_subtitle` 1-12 (2-3 for 9:16), `font_size` 20-150, `position`, `y_offset` -200..200, `highlight_color`, `font_name`. About $0.03/min. It transcribes by itself: read `result.transcription`, misheard names are burned in. |
| Soft track | the platform or player reads embedded tracks | `ffmpeg -hide_banner -loglevel error -i final.mp4 -i <slug>.srt -map 0 -map 1 -c copy -c:s mov_text -metadata:s:s:0 language=eng final_cc.mp4` (free; most social apps ignore it) |
| Local burn | only when `ffmpeg.drawtext` is true AND `ffmpeg -filters` lists `subtitles` | `-vf "subtitles=<slug>_burn.srt:force_style='Alignment=2,MarginV=80,FontSize=14,Bold=1,Outline=2'"` (libass units on a 288-line canvas for SRT input: `MarginV=80` is about 28% up from the bottom); not run on the test machine, so check one frame against the safe box |

Both fal routes need the video as a URL: `gm.py upload` the mix (it becomes a public link: say so once), `pipeline.py add ... --url`, then a one-job stage with `"video_url": "@mix"`. Placement: `platforms.md` section 2; extract one frame of the result and look at it before delivering.

## 5. Final size

| Finish | When | How |
|---|---|---|
| Upscale (paid) | default when the plan is already above the confirm threshold and the user wants the quality tier | upload and register the local picture cut (`gm.py upload`, `pipeline.py add --step cut ... --url`), then one job: `fal-ai/seedvr/upscale/video` with `"video_url": "@cut"`, `"upscale_mode": "factor"`, `"upscale_factor": 1.5` (720x1280 → 1080x1920), `"output_quality": "high"`. $0.001 per megapixel of output: 1080 x 1920 x frames / 1,000,000; about $0.05 per second at 24 fps, $0.06 at 30 fps; a 30 s cut at 30 fps is about $1.90. Then S4-S6 audio, then text, then captions. |
| Free scale | value and draft tiers, plans under the confirm threshold, or the user declines | S2 straight to `1080:1920` with `flags=lanczos`. No new detail, no cost. |
| Native 1080p clips | only on request | `resolution` `1080p` on the clip model: about 2.5 times the 720p price on Seedance, double on Wan |

Order: trim and normalize → concat → (upscale) → sound bed → mux → text overlays → burned captions → probe → manifest.

## 6. Without local ffmpeg

One-job stages, URLs through `"@job"` references:

1. Trim each shot: `fal-ai/workflow-utilities/trim-video` with `video_url`, `start_time`, `end_time`. Its defaults are `start_time` 1 and `duration` 2: always pass both ends.
2. Concatenate: `fal-ai/ffmpeg-api/merge-videos` with `video_urls` (play order), `"target_fps": 24`, `"resolution": {"width": 720, "height": 1280}` (each side 512-2048).
3. Sound: one track → `fal-ai/ffmpeg-api/merge-audio-video` (`video_url`, `audio_url`, `start_offset`); it replaces the clip's audio and is as long as the shorter input (a long voice loses its end, a short one cuts the picture), so match lengths first. Voice plus music → lower the music with `fal-ai/ffmpeg-api/loudnorm` (`audio_url`, `"integrated_loudness": -30`), then `fal-ai/ffmpeg-api/compose` with one video track holding the merged cut from step 2 as its only keyframe and two audio tracks, each one continuous file (`tracks[] = {id, type, keyframes[] = {timestamp, duration, url}}`, milliseconds). The tracks are mixed at equal weight, each lowered while both play. Compose returns `result.video_url` as a bare string: set the job-level `"download": false` and save it with `pipeline.py fetch --label <slug> --step final --url <video_url> --out genmedia-output/<slug>/<slug>_final.mp4 --endpoint fal-ai/ffmpeg-api/compose`. Compose trims nothing and plays clips at the first clip's frame rate (measured 2026-09-21, `platform.md` section 10): that is why steps 1 and 2 come first.
4. Exact frames for QA and chaining: `fal-ai/ffmpeg-api/extract-frame` (`frame_type` `first`, `middle`, `last`; output `images[0]`). Probe: `fal-ai/ffmpeg-api/metadata` (`media_url`, job-level `"download": false`).
5. Still to clip (end card), made before step 2 so it joins the merge: `fal-ai/ffmpeg-api/images-to-video` with `images: [{"url": "@card", "frames": 48}]`, `"fps": 24` (2 s; it held the last image a frame or more too long on 2026-09-21: probe it, trim if the length matters).
6. Not available on this route: ducking, crossfades, wipes, cutaways, timed PNG overlays. Hook text and CTA then travel as caption cues: put them into the SRT for `veed/subtitles` (hook text as the first cue, CTA as the last), or list them under "Left for your editor".

## 7. Final gate (before the manifest)

1. `frames.py probe` the final: duration not over the beat sheet's length (not even by a frame) and at most 0.5 s under it, target size, `has_audio` true, constant frame rate.
2. `frames.py sheet <final> --count 9 --cols 3`, Read it next to the beat sheet: hook visible in the first tile, every beat present in order, one grade throughout, end hold in the last tile.
3. `frames.py frame <final> --at 0.8` and one frame inside a caption: text spelled exactly as in `plan.md`, inside the safe box, not overlapping captions.
4. Cover: `frames.py frame <final> --at last --out genmedia-output/<slug>/<slug>_cover.png`.
5. Say what no frame can prove: sound balance, lip sync, music taste. Ask the user to watch once with audio.
6. `pipeline.py add` the final and the cover, then `pipeline.py manifest --label <slug>` (SKILL.md step 14).
