# Assembly: from measured blocks to one file

The block ledger, the audio measurement, the timing model, local assembly and what to do without ffmpeg, music, loudness and captions. `gm.py`, `explainer.py`, `pipeline.py`, `audiokit.py` and `frames.py` abbreviate the quoted calls shown in SKILL.md. Utility fields and output paths were read from the live OpenAPI schemas on 2026-09-19 (`routing-utility.md` has the dated table); local commands were run with ffmpeg 9.0.1 on macOS the same day.

## 1. Ledger, ids, folders

`.genmedia/projects/<slug>/blocks.json` is owned by `explainer.py`. Never edit it by hand; every change has a command.

| Per block | Meaning |
|---|---|
| `index`, `narration`, `words`, `chars`, `est_s`, `flags` | script and sizing (`long`, `short`, `over`, `dead_air`) |
| `scene`, `motion`, `move`, `animate` | the visual: picture, what moves, pan or zoom of a still, clip wanted |
| `audio`, `keyframe`, `clip` | each `{job, request_id, status, path, url}`; audio also `duration_s`; clip also `ordered_s`; `stale: true` after the scene or motion changed |
| `visual_s` | picture length in whole seconds, set by `set-audio` |
| `approved` | digests of what the user approved (`script`, `audio`, `keyframe`, `clip`); any change to the approved thing voids it for that block |
| `render` | local segment path and the signature of its inputs |

Project level: `style` (`name`, `text`, `negative`, `key_job`, `key_url`, `key_path`, `refs`), `tier`, `fit`, `lead_s`, `tail_s`, `block_s`, `rate`, `approvals` log, `final`.

Job ids (the batch `label` is the slug): `stylekey`, `aud-<voice>`, `n07` narration, `p-n07` probe, `kf07` keyframe, `clip07` clip, plus what you add by hand (`music`, `align`). A redo is `n07-r2`, `kf07-r3`. `plan` chooses the id: the same endpoint and input as the recorded request → same id, which `gm.py batch` resumes for free; anything changed, or `--reroll` → the next `-rN`. Status, request id, path and URL flow back from `.genmedia/runs.jsonl` whenever a command runs; nothing needs to be pasted.

Files: `genmedia-output/<slug>/style/`, `audition/`, `narration/`, `keyframes/`, `clips/`, `blocks/` (rendered segments and `list.txt`), `<slug>_cut.mp4` (voice only), `<slug>_final.mp4`, `<slug>.srt`. Plans: `.genmedia/projects/<slug>/plan-<stage>[-b<blocks>].json`.

A user's own file (recorded narration, a supplied diagram, a stock clip): `explainer.py attach --slug <slug> --block <n> --kind audio|keyframe|clip --path <file> [--url <cdn_url>]`. A URL is needed only when fal must read it (keyframe → clip, a finished video → burned captions): `gm.py upload <file>` first. Attached audio still needs `set-audio --block <n> --duration <s>`.

## 2. Measure the narration (the barrier)

Local (ffprobe present):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/audiokit.py" probe genmedia-output/<slug>/narration/*.mp3 | python3 "${CLAUDE_SKILL_DIR}/scripts/explainer.py" set-audio --slug <slug> --probe -
```

Files are matched to blocks by their recorded path, else by the `n07` / `n07-r2` file-name prefix; takes of superseded ids are ignored. Without ffprobe, probe on fal and pipe the batch output straight in, because the run ledger does not keep results:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/explainer.py" plan --slug <slug> --stage probe
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/plan-probe.json | python3 "${CLAUDE_SKILL_DIR}/scripts/explainer.py" set-audio --slug <slug> --batch-result -
```

The probe jobs call `fal-ai/ffmpeg-api/metadata` with `media_url`, read `result.media.duration`, and carry the job-level key `"download": false` (the result echoes the input URL). Last resort: `set-audio --block <n> --duration <seconds>` with a number the user read off a player.

`set-audio` answers with a table (`est_s`, `audio_s`, `visual_s`, `flags`, `over_by_s`), the `measured_rate` and the new `total_s`. Decide per flag:

| Flag | Meaning | Do |
|---|---|---|
| `over`, by up to about 1 s | the block grew to 11 s | keep it; say so in CP3 |
| `over`, by more | the sentence is too long for one picture | `edit` the text shorter, re-plan that block, measure again (max 3 takes) |
| `dead_air` | audio fills under half the block | with `--fit audio` the block is already short; consider merging its text into a neighbour |
| estimate far from measured on every block | the heuristic rate is off for this voice | note `measured_rate`, use it as `--wps` for rewrites |

Uneven loudness between takes is evened before assembly, per file, only when the user hears a difference: `audiokit.py loudnorm <in> --out <out> --lufs -16`, then `attach --kind audio` the result and `set-audio` its duration. The final mix is normalised as a whole in any case.

## 3. Timing model

```
block i:  |lead_s| narration audio_s |  tail  |        visual_s = ceil(lead_s + audio_s + tail_s), at least 3 s
start_i = sum of visual_s of the blocks before it;  voice starts at start_i + lead_s (default 0.4 s)
```

- `--fit audio` (default): the picture follows the voice. `--fit grid`: every block is exactly `block_s`; a voice that does not fit is a gate (`over`), not a stretch. The voice is never sped up and the picture is never time-stretched.
- Clips are ordered at `visual_s`, clamped to the model's range (Wan 2-30, Seedance 4-30, H3 5-15). Longer than needed → the render trims; shorter → the last frame is held. A redo of the narration that changes `visual_s` does not force a new clip for a second of difference.
- `explainer.py timeline --slug <slug>` prints the table, `total_s`, `total_ms`, `drift_s` against the target and `music_minutes`.

## 4. Route A: local ffmpeg (`ffmpeg.found` true)

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/explainer.py" render --slug <slug>
python3 "${CLAUDE_SKILL_DIR}/scripts/explainer.py" render --slug <slug> --final --music genmedia-output/<slug>/music_0.mp3
```

What `render` does, with core filters only (never `drawtext`, `subtitles` or `ass`):

| Step | Filter chain |
|---|---|
| Still block | the keyframe is scaled to twice the output size, then `zoompan` moves over it for `visual_s x fps` frames: `in` and `out` zoom 8 percent, `left` and `right` pan at 1.08 zoom. The 2x pre-scale removes zoompan's jitter. |
| Clip block | `scale` + `pad` to the output size (letterbox, never stretch), `fps`, `tpad=stop_mode=clone` to hold the last frame, `trim` to `visual_s`. The clip's own audio is dropped. |
| Block audio | `aresample=48000`, stereo, `adelay=<lead ms>`, `apad`, `atrim` to `visual_s`: the voice sits at its offset and every segment is exactly `visual_s` long. |
| Segments | H.264 CRF 18, yuv420p, AAC 192k 48 kHz stereo, identical parameters → `blocks/b07.mp4` |
| `--final` | concat demuxer with `-c copy` → `<slug>_cut.mp4`; then one audio pass: music looped or cut to the total, `volume` (default 0.25), 1 s fade-in, 2 s fade-out, `sidechaincompress` keyed by the voice (ducking; `--no-duck` disables), `amix` with `normalize=0`, `loudnorm` to `--lufs` (default -16, TP -1.5, LRA 11); video stream copied → `<slug>_final.mp4` |

- Flags: `--blocks 3,7` (segments only), `--size 1280x720` (default from the aspect: 1920x1080, 1080x1920, 1080x1080, 1440x1080), `--fps 30`, `--music-volume 0.25`, `--lufs -16` (`-14` is louder, streaming-style), `--force`.
- Segments are cached by a signature of their inputs and settings; a second `render` redoes only what changed. `--final` refuses when any segment was made with other inputs, size or fps.
- Redo of block 7 after a new take or keyframe: `render --slug <slug> --blocks 7`, then `render --slug <slug> --final --music <file>`. Seconds, not minutes.
- 720p clips are scaled up to 1080p with lanczos. That is acceptable for illustrated styles; for a premium documentary look render at `--size 1280x720` and upscale the final once through `/genmedia-skills:video`.
- The bed must be instrumental and unobtrusive; if the user still finds it loud, rerun `--final` with `--music-volume 0.15`. Without `--music` the voice alone is normalised.
- Transitions are hard cuts on purpose: narration carries the join, and crossfades would shorten the timeline that the SRT depends on.

## 5. Music bed (one job, after the total is known)

Write `.genmedia/projects/<slug>/plan-music.json` with the Write tool, `music_length_ms` = `total_ms` from `timeline`:

```json
{"label": "<slug>", "max_parallel": 1, "jobs": [
  {"id": "music", "endpoint_id": "elevenlabs/music/v2.5", "est_cost_usd": 0.6,
   "input": {"prompt": "Light, curious instrumental bed for an educational explainer: soft marimba and piano, gentle pulse, no drums fill, no vocals, stays in the background, leaves room for a narrator", "music_length_ms": 58000, "force_instrumental": true},
   "download": "genmedia-output/<slug>/music_{index}.{ext}"}
]}
```

`music_length_ms` accepts 3000-600000; the price is per **started** minute. Budget beds and licensing notes: `routing-audio.md` (task `music`). Mood words come from the style and the topic, in English; never name artists or songs.

## 6. Without local ffmpeg

There is no fal route for an explainer. `fal-ai/ffmpeg-api/compose` concatenates instead of placing (measured 2026-09-21, `platform.md` section 10): one picture track per request, so stills and clips cannot share a call; an image track holds every still for the first keyframe's duration; an audio track honours only its first keyframe's timestamp and plays the rest back to back, without the lead and tail pauses, so the narration runs ahead of the pictures block by block; overlapping audio tracks are lowered. `explainer.py timeline --compose` therefore stops with `kind: "unsupported"` instead of writing a plan.

What to do when preflight reports `ffmpeg.found` false:

1. Say it on the outline card, before any paid stage: assembly runs on the user's machine and needs ffmpeg, a free install (`brew install ffmpeg` on macOS, the package manager elsewhere). After the install, rerun `gm.py preflight` and continue with route A.
2. A user who cannot install it gets the approved parts unassembled: narration files, stills, clips, the SRT (`timeline --srt`) and the `timeline` table (per block: start, length, narration offset) as the edit list for their editor. Say plainly that the video itself was not assembled.
3. Narration can still be measured without ffprobe: `plan --stage probe` (the fal metadata utility), then `set-audio --batch-result -`.

## 7. Captions

Always, free:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/explainer.py" timeline --slug <slug> --srt genmedia-output/<slug>/<slug>.srt
```

The SRT is built from known timings: each block's text is split at sentence ends, then at the clause mark nearest the middle, into cues of at most 2 lines x 42 characters (`--max-chars`, `--max-lines`); inside a block, cue times are proportional to text length. Block starts are exact; cue borders inside a block are estimates within a second. It uses the narration exactly as written, so spelling (Turkish characters, names) is right by construction. If a narration line was respelled phonetically for the voice, fix that cue in the `.srt` with the Edit tool.

Word-exact timing (karaoke-style burn-in, fast speech): align once, on the voice-only cut, not per block (the aligner bills a flat figure per call, about $0.22 on 2026-09-19):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/audiokit.py" extract genmedia-output/<slug>/<slug>_cut.mp4 --out genmedia-output/<slug>/voice.m4a --mono
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload genmedia-output/<slug>/voice.m4a
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run fal-ai/elevenlabs/forced-alignment --input .genmedia/projects/<slug>/align.json --label <slug> --no-download --est-cost 0.22 | python3 "${CLAUDE_SKILL_DIR}/scripts/audiokit.py" captions --input - --out-base genmedia-output/<slug>/<slug> --formats srt,vtt
```

`align.json` = `{"audio_url": "<cdn_url>", "text": "<all narration blocks joined with spaces>"}`; output `result.words[]` with `start` and `end` in seconds of the whole cut, so no offset is needed.

Burned-in captions: only on request, only through fal, as the very last step (after any upscale), and the clean file is always delivered too.

| Route | Input | Notes |
|---|---|---|
| `veed/subtitles` (preferred for an explainer: exact text, Turkish) | `video_url`, `preset` (required; `simple`, `plain` and similar are the base price, the dynamic presets `glass`, `whisper`, `glide`, `glide2`, `fusion`, `terminal`, `handwritten`, `backdrop`, `backdrop2` double it), `srt_content` (paste our SRT: transcription is skipped) or `srt_file_url`; `language` enum includes `tr-TR` | output `result.video`; about $0.10 per input minute, one minute minimum |
| `fal-ai/workflow-utilities/auto-subtitle` | `video_url`, `language` (two-letter code, default `en`; `tr` transcribed a Turkish line exactly on 2026-09-21), `words_per_subtitle` 1-12 (6-8 for 16:9), `font_size` 20-150, `position`, `y_offset`, `font_name`, `highlight_color` | it transcribes by itself: read `result.transcription` and compare it with the script before delivering; about $0.03 per minute |

Upload the final (`gm.py upload`), run the one-job plan, and keep both files. A soft subtitle track needs no special filter: `ffmpeg -hide_banner -loglevel error -i <slug>_final.mp4 -i <slug>.srt -map 0 -map 1 -c copy -c:s mov_text -metadata:s:s:0 language=tur <slug>_final_cc.mp4` (player-rendered; many platforms ignore embedded tracks, so the sidecar SRT remains the deliverable).

## 8. Final gate

1. `frames.py probe genmedia-output/<slug>/<slug>_final.mp4`: `duration_s` within 1 s of `total_s`, expected size, `has_audio` true.
2. `frames.py sheet <final> --count 12 --cols 4` and Read it against the outline: block order, one style from first to last tile, no lettering, clips did not freeze early, letterboxing only where expected.
3. The SRT's last cue ends before `total_s`; open the file and read the first and last cue.
4. `pipeline.py add --label <slug> --step final --path <final> --tool ffmpeg`, `pipeline.py manifest --label <slug>` (exit 1 lists problems: unfinished or failed ids left over from re-rolls are explained, not hidden), `gm.py ledger --label <slug> --sum`.
5. You cannot hear the mix. Say so in the delivery and ask the user to watch once with sound: voice level against the bed, clicks at block borders, a mispronounced term.
