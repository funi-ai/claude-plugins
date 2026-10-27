# Troubleshooting

Read when a command fails with a kind that is not in the SKILL.md table, or when the file is fine by the numbers and wrong to the eye.

## 1. Error kinds from `democut.py`

| Kind | What happened | Do |
|---|---|---|
| `ffmpeg_missing` | no local ffmpeg/ffprobe, or `GM_FFMPEG_BIN` points at something else | say the cut cannot be made locally; the fal `ffmpeg-api` utilities in `references/routing-utility.md` do trim, concat, mux and loudnorm for cents, or the user installs ffmpeg |
| `source_changed` | the registered recording is gone or its bytes changed | `source add --replace`, then re-check every in/out point: the timings no longer mean what they meant |
| `not_a_video` | the file has no video stream ffprobe can read | a still belongs in a scene's `still`; a `.mov` screenshot is not a recording |
| `bad_span` | `out` ≤ `in`, or past the end of the recording | read the sheet again and fix the numbers |
| `bad_speed` | outside 0.25-4.0 | keep 0.75-2.5 for anything a person watches |
| `bad_zoom` | unknown kind, or a region missing | `none`, `hold`, `push`, `pull`; a region is `[x, y, w, h]` in fractions |
| `scene_shorter_than_voice` | the narration does not fit | lengthen the span, lower `speed`, or cut words — never speed the voice up |
| `duration_out_of_range` | an official target's window is missed | App Store previews are 15-30 s, creative-asset videos 5-30 s; drop or shorten scenes, or build the master instead |
| `wrong_size` | the variant's `width` x `height` is not one the row takes | drop the override, or pick a listed size; the search results video takes any exact 3:2 from 1920x1280 to 3840x2560 with even sides |
| `fps_not_allowed`, `fps_too_high` | the variant's `fps` breaks the row's rule | App Store previews at most 30; creative-asset videos exactly 30 or 60 |
| `transition_too_long` | a dissolve longer than half of a neighbour | shorten it or make it a cut |
| `frame_aspect_mismatch` | recording and device hole are over 30 % apart | a phone recording needs a phone frame; ask `launch-graphics` for the matching layers |
| `frame_invalid` | the file is not a launch-graphics layers file | pass the `*.layers.json`, not the PNG |
| `overlay_invisible` | an overlay PNG is transparent everywhere | it was exported without a composited alpha; re-render it |
| `gif_target` | a GIF row was used as a video variant | build a video variant, then `gif --budget-mb 3` |
| `budget_unreachable` | even 320 px @ 8 fps is over the budget | shorten the loop, remove the zoom, or deliver WebM/MP4 |
| `not_built` | no manifest or no file for that variant | `build` first |
| `check_failed` | `time` or `validate` found errors | every error names the scene or the number; fix and run again |
| `path_escape` | a path with a parent-directory component | keep files inside the project |
| `tool_failed` | ffmpeg itself refused | the message carries its last lines; see section 2 |

Warnings a placement adds (the cut renders; act on them or say why you keep them):

| Kind | What happened | Do |
|---|---|---|
| `quick_cut` | a scene shorter than the row's `min_scene_seconds` | merge it into a neighbour or hold it longer |
| `fast_motion` | `speed` above the row's `max_scene_speed` | cut the wait out instead of playing it fast |
| `narration_muted` | narration on a placement that autoplays muted | put the words on screen; keep sound as texture |
| `audio_never_heard` | audio on the search results video, which cannot be unmuted | set the variant's `audio` to `false` |
| `loop_seam` | the last frame and the first differ (SSIM under 0.95) | end on the opening state, or hold the same region at both ends |

## 2. ffmpeg failures worth recognising

- **`do not match the corresponding second input link timebase`** — a filter graph mixing `concat` and `xfade`. `democut.py` normalises every branch (`fps`, `settb=AVTB`, `setsar=1`, `format`) for exactly this reason; if you build your own graph by hand, do the same.
- **`Nothing was written into output file`** — the graph failed to configure; the real error is two lines above.
- **`Invalid argument` on a zoompan** — a region smaller than the floor, or a scene of zero frames. Check the timeline.
- **`Conversion failed! Decoding error`** — the recording is truncated. Re-export it from the recorder.
- **`No such filter: 'drawtext'` / `'subtitles'`** — the build has no libfreetype/libass. That is expected on many machines: captions ship as sidecar files, and text arrives as PNG overlays.

## 3. It renders, but it looks wrong

| Symptom | Cause | Fix |
|---|---|---|
| Soft, mushy UI text | zoomed past what the recording holds, or the recording is smaller than the target | record at 2x; keep the region above ~0.45 of the width; `time` warns as `zoom_deep` |
| The picture jitters during a push | the zoom is doing a long, slow move over fine UI lines | shorten the move, use a `hold`, or give the zoom a bigger region |
| Bars on the sides or top | `fit: "pad"` with a different aspect | choose `fit: "crop"` plus a region, or accept the bars and say so |
| Bars **inside** the picture | the recording already had letterboxing | `source add` reports `letterbox`; crop it with a `hold` region |
| A flash at a dissolve | a bright end card or a white screen | dissolve into the product's own ground, or make it a cut |
| The last frame is black | a still scene faded out at the end | drop the trailing fade; a demo ends on something readable |
| The overlay is not there | a PNG whose alpha is empty, or timings outside the scene | `time` catches an empty alpha; check `start`/`end` are in **scene** time |
| Captions drift late | cues come from the timeline, not from the words | take word timings from the narration (`references/captions-and-locales.md` section 2) |
| Music swamps the voice | no ducking available, or the bed is too loud | lower `music.gain_db` to −22, set `duck_db`, re-`build` |
| The audio ends before the picture | a scene was lengthened after the narration was made | `time` shows the per-scene numbers; re-measure |
| The file is enormous | a store bitrate (10-12 Mbps) on a long master | that is correct for Apple; for the web build a `web-16x9` variant |

## 4. Slow builds

- The first build renders every scene; the second reuses the cache (`reused` in the answer). Only changed scenes re-render.
- A `push` zoom is the expensive step: it decodes, upscales 2x and re-scales every frame. A 90 s demo with six pushes takes minutes, not seconds.
- Give the `build` call a 600000 ms Bash timeout, and never run two builds of the same slug at once.
- `--scene <id>` re-renders one scene when you are iterating on it.

## 5. When the cut is right and the platform still says no

Read the official page again on the day (`references/surfaces.md` names each one), correct the row in `scripts/video-surfaces.json` with a new `verified_on`, re-run `validate`, and say which number changed. The page wins over this project's table, always.
