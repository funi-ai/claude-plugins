# `cut.json`: every field

Read whenever you edit the cut or an error names a field. The file lives at `.genmedia/projects/<slug>/demo-video/cut.json`, is written by `democut.py init` and edited with the Write or Edit tool. Paths are relative to the project cwd (or absolute); a parent-directory component is refused (`path_escape`).

## 1. Top level

```json
{
  "schema": 1,
  "script": "0.1.0",
  "slug": "acme",
  "name": "Acme",
  "created": "2026-09-20T10:00:00Z",
  "updated": "2026-09-20T10:31:00Z",
  "locales": ["en", "tr"],
  "sources": { },
  "audio": { },
  "scenes": [ ],
  "variants": [ ]
}
```

`schema`, `script`, `created` and `updated` are the script's; leave them alone. `locales` is a note to yourself: cue files and overlays are per locale, the cut is not.

## 2. `sources` — written by `source add`, never by hand

```json
"sources": {
  "app": {"file": "recordings/inbox.mov", "sha256": "…", "bytes": 84123456,
          "width": 1290, "height": 2796, "fps": 60, "duration_s": 42.3,
          "has_audio": true, "video_codec": "h264", "audio_codec": "aac",
          "os": "ios", "letterbox": null, "added": "2026-09-20T10:02:00Z"}
}
```

The recording is referenced where it lies (recordings are large; nothing is copied). Move it, re-export it or trim it in another tool and every command stops with `source_changed`: run `source add --replace` and check the in/out points, because the timings no longer mean what they meant.

`letterbox` is filled when `cropdetect` finds bars already baked into the recording. Crop them with a `hold` zoom on the content rectangle, or the delivered file gets bars inside bars.

## 3. `audio`

```json
"audio": {
  "keep_source": false,
  "source_gain_db": -8.0,
  "music": {"file": "audio/bed.mp3", "gain_db": -20.0, "fade_in": 1.0, "fade_out": 1.5},
  "duck_db": -12.0,
  "lufs": -16.0,
  "true_peak": -1.5,
  "sample_rate": 48000
}
```

- `keep_source` takes the recording's own sound (typing, notification sounds, a voice recorded during the capture). Off by default: most screen recordings carry room noise and a fan.
- `music` is one file for the whole cut, trimmed to the timeline, faded at both ends. Generate it with `gm.py` (`references/narration-and-audio.md`) or take the user's file.
- `duck_db` turns on sidechain ducking of the bed under the narration. `null` keeps a flat bed. Without the `sidechaincompress` filter (`tools`), it is ignored.
- `lufs` / `true_peak` are the delivery targets, measured back by `validate`. −16 LUFS suits web and store players; −14 is louder and clips more; do not go above −1.0 dBTP.

## 4. `scenes` — the ordered list

```json
{
  "id": "compose",
  "source": "app",
  "in": 12.40,
  "out": 16.10,
  "speed": 1.0,
  "mute": false,
  "zoom": {"kind": "push", "region": [0.28, 0.16, 0.44, 0.30], "ease": "in-out"},
  "frame": {"layers": ".genmedia/projects/acme/launch-graphics/…/01-hero.layers.json"},
  "voice": {"file": "audio/vo-compose.mp3", "lead": 0.25, "tail": 0.25, "gain_db": 0},
  "say": "Start a reply without leaving the list.",
  "overlays": [{"file": "cards/lower-third-en.png", "start": 0.4, "end": 3.0,
                "x": "center", "y": "bottom", "margin": 96, "fade": 0.25, "scale": 1.0}],
  "hold_last": 0.0,
  "transition": {"kind": "cut", "seconds": 0}
}
```

| Field | Meaning | Rules |
|---|---|---|
| `id` | names the idea | unique, kebab-case, used in file names and error messages |
| `source` | a key of `sources` | omit only for a `still` scene |
| `in` / `out` | seconds in the SOURCE | `out > in`, inside the recording; the scene's output length is `(out - in) / speed` |
| `speed` | 0.25 to 4.0 | audio follows through chained `atempo`; above 2.5 reads as comedy |
| `mute` | drop this scene's source audio | only matters with `keep_source` |
| `zoom.kind` | `none`, `hold`, `push`, `pull` | `references/editing.md` section 4 |
| `zoom.region` | `[x, y, w, h]` as fractions of the source frame | each ≥ 0.12; reshaped to the destination aspect, reported as `region_adjusted` |
| `zoom.from` | reserved | not used in v1: a push starts on the whole frame |
| `zoom.ease` | `in-out` (default) or `linear` | only for `push` and `pull` |
| `frame.layers` | a `*.layers.json` from `launch-graphics layers` | the recording plays inside the drawn device; the alpha PNG sits beside it |
| `voice` | one narration file for this scene | `lead` is silence before the words, `tail` after; the scene must be at least `lead + duration + tail` |
| `say` | the words spoken (or that would be) | drives the cue files and the words-per-second warning |
| `overlays` | timed PNGs, in scene time | `x`: `left`/`center`/`right`/pixels, `y`: `top`/`center`/`bottom`/pixels, `margin` in pixels, `fade` on alpha, `scale` multiplies the PNG's own size |
| `hold_last` | seconds of frozen last frame | for a settled ending or a loop point |
| `transition` | `{"kind": "cut"}` or `{"kind": "dissolve", "seconds": 0.4}` | the transition to the NEXT scene; a dissolve overlaps and shortens the timeline |

A **still scene** (intro plate, end card) replaces `source`/`in`/`out`:

```json
{"id": "end", "still": {"file": "cards/end-en.png", "seconds": 2.5, "fade": 0.4},
 "transition": {"kind": "cut"}}
```

## 5. `variants` — what gets delivered

```json
{
  "id": "appstore-iphone",
  "target": "appstore-iphone-69",
  "width": null, "height": null, "fps": null,
  "fit": "pad",
  "scenes": ["*"],
  "audio": true,
  "background": "#0E1116",
  "formats": ["mp4"],
  "poster_at": 0.0
}
```

- `target` is a row of `scripts/video-surfaces.json` (`specs`); `width`, `height` and `fps` default to that row and are overridden only on an unofficial target, or within what an official row accepts (a listed size, the search results video's 3:2 range, 30 or 60 fps on a creative-asset video). `time` refuses anything else.
- `fit` decides what happens when the picture and the canvas disagree: `pad` (contain: bars in `background`) or `crop` (cover: the edges are lost). A desktop recording in a 9:16 variant is `crop` plus a zoom region, or `pad` and say so.
- `scenes` is `["*"]` or an explicit list: that is how one cut yields a 90 s demo, a 20 s store preview and a 5 s loop without a second project.
- `audio: false` renders silent (loops and App Store creative-asset videos autoplay muted, and start with it).
- `poster_at` is the second the poster PNG is taken from; keep it on a frame that stands alone.

## 6. Worked fragments

A 9:16 cut of a desktop recording, same scenes, tighter framing:

```json
{"id": "vertical", "target": "social-9x16", "fit": "crop", "scenes": ["hook", "compose", "result"],
 "audio": true, "background": "#0E1116", "formats": ["mp4"], "poster_at": 0.6}
```

A silent feature loop built from one scene:

```json
{"id": "loop-filing", "target": "loop-16x9", "fit": "crop", "scenes": ["filed"],
 "audio": false, "background": "#0E1116", "formats": ["mp4"], "poster_at": 0.0}
```

A scene that plays inside a drawn iPhone over a plate, narrated:

```json
{"id": "hero", "source": "phone", "in": 3.0, "out": 9.5, "speed": 1.0,
 "zoom": {"kind": "none"},
 "frame": {"layers": ".genmedia/projects/acme/launch-graphics/video-layers/ad-video-9x16/en/01-hero.layers.json"},
 "voice": {"file": "audio/vo-hero.mp3", "lead": 0.3, "tail": 0.3},
 "say": "Every message, already sorted.", "transition": {"kind": "dissolve", "seconds": 0.4}}
```

## 7. Order of operations inside `build`

Per scene: trim → speed → frame rate → zoom (`crop`+`scale` for a hold, pre-upscale + `zoompan` for a move) → fit into the device hole or the canvas → the alpha frame on top → hold the last frame. Then the scenes are joined (`concat`, or `xfade` where a dissolve is asked for). Then the overlays are composited on the joined picture in timeline time, and the audio is assembled from the same scene list (source audio, narration delayed to each scene's start, music, ducking, EBU R128 normalisation). Then the encoder settings of the target.

Each scene is cached under `build/<variant>/sc-<id>-<hash>.mp4`, keyed by that scene's fields, the recording's hash, the frame layer and the variant geometry. Change one scene and only that scene re-renders; `--force` ignores the cache.
