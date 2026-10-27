# Assembly: local ffmpeg and fal utilities side by side

Deterministic work (probe, trim, scale, concat, mix, mux, captions) never goes through a generative model. Two routes; pick once per project from `gm.py preflight`:

| | Local ffmpeg (`ffmpeg.found` true) | fal utilities |
|---|---|---|
| Cost, speed | Free, seconds | Cents, queue time per call |
| Inputs | Local files (the ones the batch already downloaded) | URLs (pass CDN URLs with `"@job"` references) |
| Limits | None that matter here | `merge-videos` width and height 512-2048; `merge-audios` 2-5 files |
| Mixing two audio tracks | Yes (A4) | Only as two audio tracks in compose, each lowered while they overlap; no volume control |
| Exactness | Frame- and sample-exact | Per endpoint; verify the output |

Recipes were run on 2026-09-19 with ffmpeg 9.0.1 on macOS. They use only core filters (`scale`, `pad`, `crop`, `fps`, `setsar`, `concat` demuxer, `amix`, `sidechaincompress`, `apad`, `atrim`, `afade`, `loudnorm`, `xfade`, `acrossfade`, `reverse`, `tile`). They do **not** use `drawtext`, `subtitles` or `ass`: many builds, including Homebrew's, ship without them, and `ffmpeg.drawtext` in the preflight output tells you. Utility fields and output paths were read from the live schemas the same day; the full dated table is in `routing-utility.md`.

Rules for every local command: file names in the recipes are shortened, the batch saved its outputs as `genmedia-output/<slug>/<id>_<index>.<ext>` (`pipeline.py urls --label <slug>` lists them); ffmpeg writes only under `genmedia-output/<slug>/` (the batch already created it; never `mkdir`), text files it reads (concat lists) are written with the Write tool under `.genmedia/tmp/`, one ffmpeg or ffprobe command per Bash call (no `for` loops, no `printf >` redirects: they prompt); never pass `-y` for a path outside it; add `-hide_banner -loglevel error`; afterwards register the product with `pipeline.py add --label <slug> --step <id> --path <file> --tool ffmpeg --from <ids>`.

## A1. Probe

```bash
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,r_frame_rate -of json genmedia-output/<slug>/clip01_0.mp4
ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 genmedia-output/<slug>/clip01_0.mp4
ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 genmedia-output/<slug>/clip01_0.mp4
```

The second prints nothing when the clip is silent (decides A2 variant); the third is the frame count for per-megapixel upscale pricing.

fal: `fal-ai/ffmpeg-api/metadata`, input `media_url`, output `result.media.{duration, fps, frame_count, resolution.width, resolution.height, audio}`. Set the job-level key `"download": false` (next to `input`): the result echoes the input as `media.url`, and the downloader would fetch it again. Read the numbers from the batch output at once; the ledger does not keep `result`.

## A2. Normalize every clip to one size, rate and codec

Concat without re-encoding (A3) needs identical parameters. Letterbox to fit:

```bash
ffmpeg -hide_banner -loglevel error -i clip01.mp4 -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -ar 48000 -ac 2 norm_clip01.mp4
```

- Silent clip: add `-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000` as a second input plus `-map 0:v:0 -map 1:a:0 -shortest`, so every part has an audio stream.
- Fill instead of letterbox (16:9 to 9:16): `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30`.
- Delivery transcode: same command with the target size and `-movflags +faststart`.

fal: `fal-ai/workflow-utilities/scale-video`: `video_url`, `width` and/or `height` (even numbers), `mode` `stretch` (default) | `pad` | `crop`, `pad_color`, `codec` `libx264` | `libx265`, `crf` (default 18). Output `result.video`. The default `stretch` distorts; always pass `mode`.

## A3. Concatenate

Write `.genmedia/tmp/<slug>-list.txt` with the Write tool, one line per part in play order:

```text
file '<project>/genmedia-output/<slug>/norm_clip01.mp4'
file '<project>/genmedia-output/<slug>/norm_clip02.mp4'
file '<project>/genmedia-output/<slug>/norm_clip03.mp4'
```

```bash
ffmpeg -hide_banner -loglevel error -f concat -safe 0 -i .genmedia/tmp/<slug>-list.txt -c copy genmedia-output/<slug>/<slug>_cut.mp4
```

`<project>` is the absolute path of the project directory (the one the Write tool already needs). A relative path in the list would resolve against `.genmedia/tmp/`, not the project; `-safe 0` allows absolute paths. `-c copy` is only safe after A2.

fal: `fal-ai/ffmpeg-api/merge-videos`: `video_urls` (2 or more, play order), optional `target_fps` (1-60; default is the lowest input fps), `resolution` (preset or `{width,height}`, each 512-2048; default is the minimum width and height across inputs), `resolution_aspect_ratio_video_index`. Output `result.video`. Mixed aspect ratios: set `resolution` explicitly, or scale first. For a deliverable above 2048 px: upscale per clip and use the local concat. Measured 2026-09-21: a 30 fps clip with sound plus a 24 fps silent clip, with `target_fps` 30 and `resolution` 1280x720, came back 10.0 s at 30 fps with one continuous audio track (the silent part padded); `result.metadata.input_videos[].url` lists the inputs, so a download template fetches them again: the merged file is `_0`.

## A4. Voice plus music with ducking, cut to the picture length

`DUR` is the cut's duration from A1. The voice is padded with silence to `DUR`, the music trimmed and faded, and the voice drives a compressor on the music:

```bash
ffmpeg -hide_banner -loglevel error -i vo.mp3 -i music.mp3 -filter_complex "[0:a]aresample=48000,apad,atrim=duration=13,asplit=2[vo][key];[1:a]aresample=48000,atrim=duration=13,volume=0.35,afade=t=out:st=11.5:d=1.5[bed];[bed][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck];[vo][duck]amix=inputs=2:duration=first:normalize=0[mix]" -map "[mix]" -c:a aac -b:a 192k genmedia-output/<slug>/bed.m4a
```

- Replace both `13` with `DUR` and `11.5` with `DUR - 1.5`. Delay the voice with `adelay=600:all=1` before `apad` for a 0.6 s lead-in.
- `normalize=0` keeps `amix` from halving the voice. Without ducking: drop the `sidechaincompress` step and use `volume=0.2`.
- `sidechaincompress` ends with its shorter input; padding the voice first is what keeps the bed full length.

fal: no listed endpoint mixes two tracks (`fal-ai/ffmpeg-api/merge-audios` joins 2-5 files end to end with no gap, 2 s + 10 s gave 12.0 s on 2026-09-21; output `result.audio`). Use two audio tracks in compose (below) after lowering the music with loudnorm, or mix locally.

## A5. Loudness

```bash
ffmpeg -hide_banner -loglevel error -i bed.m4a -af "loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 192k genmedia-output/<slug>/bed_norm.m4a
```

`-16` LUFS suits social and web; `-14` is the louder streaming target, `-23` broadcast. To read the measured values: `-af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=summary -f null -`.

fal: `fal-ai/ffmpeg-api/loudnorm`: `audio_url`, `integrated_loudness` (default -18, range -70 to -5), `true_peak` (default -0.1), `loudness_range` (default 7). Output `result.audio`. A low target (for example -30) is the only fal-side way to turn a music bed down.

## A6. Exact first and last frame

```bash
ffmpeg -hide_banner -loglevel error -i clip01.mp4 -frames:v 1 -update 1 genmedia-output/<slug>/clip01_first.png
ffmpeg -hide_banner -loglevel error -i clip01.mp4 -vf reverse -frames:v 1 -update 1 genmedia-output/<slug>/clip01_last.png
```

`reverse` buffers the whole clip in memory: fine for generated clips of a few seconds, not for long footage (there use `-sseof -0.2`, which is approximate). A last frame that feeds the next image-to-video job must be uploaded (`gm.py upload`) and registered (`pipeline.py add ... --url`).

fal: `fal-ai/ffmpeg-api/extract-frame`: `video_url`, `frame_type` `first` (default) | `middle` | `last`. Output `result.images[0]` (a list, not `image`), so `"@lastframe"` resolves directly and no upload is needed.

## A7. Put the audio on the picture

```bash
ffmpeg -hide_banner -loglevel error -i <slug>_cut.mp4 -i bed_norm.m4a -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart genmedia-output/<slug>/<slug>_final.mp4
```

- `-shortest` ends the file with the shorter stream; build the bed to the cut's length (A4) so the picture is never cut short.
- Keep clip ambience under the bed: replace the maps with `-filter_complex "[0:a]volume=0.25[amb];[1:a][amb]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v:0 -map "[a]"`.

fal: `fal-ai/ffmpeg-api/merge-audio-video`: `video_url`, `audio_url`, `start_offset` (seconds, default 0). Output `result.video`. One audio track only: it replaces any audio the clip already had. The output is as long as the **shorter** input, like `-shortest` (measured 2026-09-19 and 2026-09-21, `platform.md` section 10): a 6.4 s voice on a 5.2 s clip lost its end, and a 2 s sound on a 4 s clip cut the picture to 2 s. Make the lengths match first (music via `music_length_ms`, a shorter script, a longer or extended clip, or `trim-video`) and check the output duration (A1) before delivering.

## A8. Still to clip (end card, title)

```bash
ffmpeg -hide_banner -loglevel error -loop 1 -framerate 30 -i card.png -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 -t 2 -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -ar 48000 -ac 2 -shortest genmedia-output/<slug>/card.mp4
```

Same size, rate and codecs as A2, so it concatenates with `-c copy`.

fal: `fal-ai/ffmpeg-api/images-to-video`: `images` = list of `{url, frames}` (max 200), `fps` (default 24); a 2 s hold at 24 fps is `"frames": 48`. Output `result.video`. Holds were not exact on 2026-09-21: one extra frame for a single image; for two images the first came back one frame short (53 of 54) and the last 11 to 30 frames long: probe the clip and cut it with `trim-video` when the length matters.

## A9. Trim

```bash
ffmpeg -hide_banner -loglevel error -ss 1.0 -t 3.5 -i clip02.mp4 -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac genmedia-output/<slug>/clip02_trim.mp4
```

Re-encode; `-c copy` cuts only on keyframes.

fal: `fal-ai/workflow-utilities/trim-video`: `video_url`, `start_time`, and `end_time` or `duration`. Output `result.video` plus `original_duration`, `trimmed_duration`. **Defaults are `start_time` 1 and `duration` 2**: always pass `start_time` and one end. It is frame-exact and keeps the audio (6 s clip, `duration` 2.8 → 2.80 s, 2026-09-21).

## A10. Crossfade between two normalized clips

```bash
ffmpeg -hide_banner -loglevel error -i norm_clip01.mp4 -i norm_clip02.mp4 -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac genmedia-output/<slug>/xf_01_02.mp4
```

`offset` = first clip's duration minus the fade. Each fade shortens the total by its duration; recompute `DUR` before A4. No fal equivalent is listed; hard cuts only on that route.

## Timeline compose (fal only)

`fal-ai/ffmpeg-api/compose` puts one picture track and one or more audio tracks into one file:

```json
{"tracks": [
  {"id": "picture", "type": "video", "keyframes": [{"timestamp": 0, "duration": 5000, "url": "@clip01"}, {"timestamp": 5000, "duration": 5000, "url": "@clip02"}]},
  {"id": "voice", "type": "audio", "keyframes": [{"timestamp": 600, "duration": 8400, "url": "@vo"}]}
]}
```

- `type` is `video`, `audio` or `image`; `timestamp` and `duration` are **milliseconds**; every track needs a unique `id`. The example is right only because both clips are already exactly 5.0 s at one size and frame rate: the video timestamps and durations place nothing (next bullet).
- Output is `result.video_url` and `result.thumbnail_url`, **bare strings**. `--download` saves no file, but the helper records both URLs as outputs with `path: null` (video first), so run `pipeline.py fetch --label <slug> --step timeline --out genmedia-output/<slug>/<slug>_final.mp4`; the URL, endpoint and request id come from the ledger, `--index 1` takes the thumbnail. Set `"download": false` to keep the empty download call out of the way.
- It is a concatenator, not a timeline editor (measured 2026-09-21, `platform.md` section 10): one picture track only (a video track plus an image track is a 400), clips back to back in keyframe order, gaps and keyframe durations ignored, output at the first clip's size and frame rate, a clip with another frame rate played too slow or too fast. So: trim every clip to its planned length first (A9 or `trim-video`) and bring all of them to one size and frame rate (`scale-video`, or `merge-videos` with `resolution` and `target_fps`); a still becomes a clip first (A8, `images-to-video`).
- Audio: put each continuous sound on its own track (the finished voice-over, the bed); a track starts at its first keyframe's timestamp and later keyframes in the same track follow without gaps, so a voice made of separate lines needs one joined file (`merge-audios` joins without gaps: any pause has to be inside the files). Overlapping tracks are mixed at equal weight, each lowered, and a clip's own audio is dropped as soon as any audio track exists.
- The schema has no volume, fade or transition fields. Set levels beforehand (A5 or the loudnorm endpoint).
- Probe the result (A1) and compare duration, size and audio with the plan before delivering.

## Captions

| Need | Route | Notes |
|---|---|---|
| Fast burned-in word captions from the audio | `fal-ai/workflow-utilities/auto-subtitle` (~$0.03/min on 2026-09-19) | `video_url`, `language` (default `en`; two-letter code: `tr` transcribed and burned a Turkish line exactly on 2026-09-21), `words_per_subtitle` 1-12, `font_name` (Google Font), `font_size` 20-150, `position`, `highlight_color`, `enable_animation`. Output `result.video` plus `transcription`, `words`. Speech-to-text mistakes on names are burned in: read `transcription` during QA. |
| Exact text you already hold (any language) | `veed/subtitles` (~$0.10 per input minute, 1 min minimum; x2 for dynamic presets and above 1080p) | `video_url` + `preset` required (`simple`, `plain`, ... are basic; `glass`, `fusion`, ... are dynamic and double the price); `srt_content` or `srt_file_url` skips transcription and is burned verbatim (the `plain` preset still reveals a cue word by word); `language` enum includes `tr-TR`; `translation_language` adds cost. Output `result.video`. |
| Flat fee, simple style | `fal-ai/auto-caption` (~$0.10 per video) | mp4 under 400 MB. Output `result.video_url`, a bare string: no file is saved, the URL is in the ledger; save it with `pipeline.py fetch --label <slug> --step <job id> --out <path>`. |
| Free, always | Sidecar `.srt` written with the Write tool from the script and the measured timings | The right artefact for YouTube and most players. |
| Soft subtitle track in the mp4 (needs no libass) | `ffmpeg -hide_banner -loglevel error -i final.mp4 -i captions.srt -map 0 -map 1 -c copy -c:s mov_text -metadata:s:s:0 language=tur final_cc.mp4` | Player-rendered, can be switched off; not visible on platforms that ignore embedded tracks. |

Burn captions as the very last step, after the cut is approved and after any upscale: every later re-encode softens text. Local burn-in with `subtitles=` or `drawtext=` is allowed only when `ffmpeg.drawtext` is true, and even then the fal route gives the styled result users expect.

## Order of operations

1. Probe everything (A1). 2. Trim (A9). 3. Normalize (A2). 4. Concat or crossfade (A3, A10). 5. Measure `DUR`. 6. Mix (A4), loudness (A5). 7. Mux (A7). 8. Upscale if planned (merge first when the target fits 2048 px). 9. Captions. 10. Probe the final (A1): duration, size, audio stream present. 11. `pipeline.py add` the final, then `pipeline.py manifest`.
