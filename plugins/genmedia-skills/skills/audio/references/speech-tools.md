# Speech tools: transcription, captions, dubbing, cleanup, loudness

Fields, enums and limits were read from the live OpenAPI schemas on 2026-09-19; prices are that day's numbers and
must be confirmed with `gm.py price`. Tiers and alternates: [routing-audio.md](routing-audio.md). Calling
convention: [cli-contract.md](cli-contract.md). `gm.py` and `audiokit.py` stand for the full helper calls shown in
SKILL.md; `audiokit.py` is local and free.

Every source file is uploaded first (`gm.py upload <file>` → `cdn_url`). Uploads are public links: say so before
sending private recordings ([platform.md](platform.md) §1).

## 1. Speech-to-text

| Endpoint | Input | Output | Use when |
|---|---|---|---|
| `fal-ai/elevenlabs/speech-to-text/scribe-v2` | `audio_url`*, `language_code` (optional; schema examples are three-letter codes `eng`, `spa`, `fra`, `deu`, `jpn`; Turkish in that scheme is `tur`; omitted = auto-detect), `diarize` (default `true`), `tag_audio_events` (default `true`), `keyterms` (up to 100 strings of 50 chars; adds 30% to the price) | `.result.text`, `.result.language_code`, `.result.language_probability`, `.result.words[]` = `{text, start, end, type, speaker_id}` with `type` `word`, `spacing` or `audio_event` | Default. Word times and speakers in one pass. ~$0.008 per input minute as of 2026-09-19. |
| `fal-ai/wizper` | `audio_url`* (mp3, mp4, mpeg, mpga, m4a, wav, webm), `task` (`transcribe`, `translate`), `language` (enum of two-letter codes incl. `tr`; **default `en`**; auto-detect needs `null`, which `gm.py` skips, so always set it), `max_segment_len` (10-29 s), `merge_chunks` | `.result.text`, `.result.chunks[]` = `{timestamp: [start, end], text}`, `.result.languages` | Translation of speech straight to English text; video containers accepted. Segment times only, no words, no speakers. Compute-billed: cost depends on runtime. |
| `nvidia/nemotron-asr-multilingual/asr` | `audio_url`*, `language` (enum incl. `tr-TR`, default `auto`), `acceleration` | `.result.output` (text only) | Plain text, no timestamps. |

Rules:
- Names, brands, jargon: pass them as `keyterms` on Scribe (state the 30% surcharge in the estimate).
- The source is a video: Wizper accepts mp4 directly. Scribe does not: an mp4 with a video stream ended `COMPLETED`
  with a 422 result, while mp3 and m4a of the same speech were transcribed word for word (2026-09-21). Extract the track first:
  `audiokit.py extract clip.mp4 --out .genmedia/tmp/clip.mp3`, then upload the mp3.
- Music or noise under the speech and a poor transcript: clean first (§4), transcribe the cleaned file.
- Wizper with the default `language` transcribes Turkish as if it were English. Set `"language": "tr"`. Language
  unknown: use Scribe v2, which detects it.
- Long recordings: price is per input minute, so estimate from `audiokit.py probe` before sending.

Transcribe and keep the big result out of the chat in one step (both halves are pre-approved helper calls):

```bash
gm.py run fal-ai/elevenlabs/speech-to-text/scribe-v2 --input .genmedia/tmp/<label>-stt.json --label <label> --no-download --est-cost <usd> | audiokit.py captions --input - --out-base genmedia-output/<label>/<label> --speakers
```

`captions` writes `<out-base>.srt`, `.vtt`, `.txt` and `.result.json` (the raw model result, so captions can be
re-cut later without paying again) and prints only a summary: cue count, duration, language, speakers, two preview
cues. When `gm.py` reports a failure or `pending`, that JSON is passed through unchanged: read `kind`, or run the
`resume` command and pipe `gm.py wait ... --no-download` into the same `captions` call.

## 2. Captions (SRT / VTT)

Two routes:

| Situation | Route |
|---|---|
| You have the script (your own TTS narration, a supplied transcript) | `fal-ai/elevenlabs/forced-alignment`: `audio_url`*, `text`* (the exact words spoken, up to 675000 chars; audio up to 10 hours, 3 GB) → `.result.words[]` = `{text, start, end, loss}`, `.result.characters[]`, `.result.loss`. Billed per started **hour** (~$0.22 as of 2026-09-19), so one short clip costs the same as 59 minutes: align the joined narration once, not each chunk. |
| No script | Scribe v2 (§1). Correct names in the `.txt`, and if the user wants the fixed text in the captions, run forced alignment with the corrected text. |

```bash
gm.py run fal-ai/elevenlabs/forced-alignment --input .genmedia/tmp/<label>-align.json --label <label> --no-download --est-cost <usd> | audiokit.py captions --input - --out-base genmedia-output/<label>/<label> --formats srt,vtt
```

`audiokit.py captions` options:

| Option | Default | Meaning |
|---|---|---|
| `--max-chars` | 42 | Characters per line. 32-37 for vertical video, 42 for 16:9. |
| `--max-lines` | 2 | Lines per cue; 1 for short-form "one line at a time" captions. |
| `--max-duration` | 6 | Seconds per cue. 2.5-3 for punchy short-form. |
| `--max-gap` | 0.8 | A silence longer than this starts a new cue. |
| `--offset` | 0 | Shift every cue, e.g. the narration starts 1.5 s into the video. A negative value drops the words it moves before 0:00 (`dropped_words` in the output). |
| `--speakers`, `--speaker-names speaker_0=Ayşe,speaker_1=Mehmet` | off | Prefix a cue with the speaker when it changes (Scribe diarization). Ask for names only if the user wants them shown. |
| `--keep-events` | off | Keep Scribe audio events such as `(laughter)`. |
| `--formats` | `srt,vtt,txt` | Any subset. |

Cues break at sentence ends, speaker changes, long silences and the size limits; cues never overlap; a very short
cue is held for at least 0.7 s when the next cue allows. Wizper results work too, but only segment times exist:
word times are spread evenly and the summary says `approximate_timing:true`. Tell the user when that is the case.

`alignment_loss` in the summary is the model's average misfit. A value far above what a clean read of the same
length gave, or captions that drift late in the file, mean the text does not match the audio (ad-libs, a skipped
paragraph): transcribe with Scribe instead.

Translated captions: translate the `.txt` yourself cue by cue, keep the timing, keep each line within
`--max-chars`. Burning captions into the picture is `pipelines` (it owns the subtitle endpoints and the mux).

## 3. Dubbing

| Route | Endpoint and input | Output | Notes |
|---|---|---|---|
| One call | `fal-ai/elevenlabs/dubbing`: `video_url` or `audio_url` (video wins when both are set), `target_lang`* (ISO 639-1, `"tr"`, `"en"`), `source_lang` (auto when omitted), `num_speakers` (1-50), `highest_resolution` (default `true`) | `.result.video.url`, `.result.target_lang` | Default. Billed per started input minute (~$0.60 as of 2026-09-19). The schema documents only a `video` output: give it a video. For an audio-only source use the manual chain. |
| Lips re-synced | `fal-ai/heygen/v2/translate/precision`: `video_url`* (up to 8 minutes), `output_language`* (enum of names: `"Turkish"`, `"English"`, `"German"`, ...), `speaker_num`, `translate_audio_only`, `enable_caption`, `enable_dynamic_duration`, `srt_url` + `srt_role` | `.result.video.url`, `.result.caption_file.url` when captions are on | Billed per output second. The pricing API and the model's pricing text disagreed on 2026-09-19 (0.05 vs 0.10 per second): estimate with the higher one. A 60 s clip is already above the confirm threshold. |
| Manual chain | 1. `audiokit.py extract` the track. 2. Optional cleanup (§4) to separate speech from the music bed. 3. Scribe v2 with `diarize`. 4. Translate the transcript yourself, sentence by sentence, aiming at the same spoken length (Turkish runs longer than English: tighten). 5. TTS per speaker ([tts-and-voices.md](tts-and-voices.md)); a cloned voice only with consent. 6. `audiokit.py probe`: compare with the source duration; adjust speed or wording, at most 3 rounds. 7. Hand over to `video` for lipsync or `pipelines` for the mux. | audio file(s) + translated SRT | Use when the user needs a specific voice, script approval before synthesis, or the music bed kept intact. |

Show the translated script before synthesis when the dub is for publication: wording is a human decision, and a
re-dub costs the full price again. Estimate = source minutes (`audiokit.py probe`, rounded up) x unit price. At or
above the confirm threshold, offer a trial on the first minute in the same message (the cut is a local ffmpeg
trim or a `pipelines` step) so voices and translation are judged before the full spend.

## 4. Cleanup and separation

| Endpoint | Input | Output | Use when |
|---|---|---|---|
| `fal-ai/elevenlabs/audio-isolation` | `audio_url` or `video_url` (one of them) | `.result.audio.url` | Speech over music or heavy noise; also the no-ffmpeg way to get the speech track of a video. Billed per minute. |
| `fal-ai/deepfilternet3` | `audio_url`*, `audio_format` (`mp3` default, `wav`, `flac`, `aac`, `m4a`, `ogg`, `opus`), `bitrate` | `.result.audio_file.url` (also `duration`, `sample_rate`, `channels`) | Steady noise (hiss, fan, hum) under otherwise clean speech; cheaper, per second. The output key is `audio_file`. Never set `sync_mode`. |
| `fal-ai/demucs` | `audio_url`*, `stems` (subset of `vocals`, `drums`, `bass`, `other`, `guitar`, `piano`), `model` (default `htdemucs_6s`; guitar and piano exist only on 6-stem models), `output_format` (`mp3` default, `wav`), `shifts`, `overlap` | one key per stem: `.result.vocals.url`, `.result.drums.url`, ... | Karaoke or instrumental version, removing a music bed, remix stems. Request only the stems you need; match files by `outputs[].json_path`. |

Order of operations for a bad recording: isolate or denoise → transcribe or clone → normalize loudness last.
Separation is for material the user owns or may edit; do not strip vocals from commercial tracks for reuse.

## 5. Loudness, joining, probing

Local and free when ffmpeg is installed:

```bash
audiokit.py loudnorm genmedia-output/<label>/<label>.mp3 --out genmedia-output/<label>/<label>-norm.mp3 --lufs -16 --true-peak -1.0
audiokit.py concat genmedia-output/<label>/c001_0.mp3 genmedia-output/<label>/c002_0.mp3 --out genmedia-output/<label>/<label>.mp3 --gap-ms 250
audiokit.py probe genmedia-output/<label>/<label>.mp3
audiokit.py extract interview.mp4 --out .genmedia/tmp/interview.mp3 --start 12 --duration 600
```

On fal (no local ffmpeg, or the file is already a CDN URL):

| Endpoint | Input | Output |
|---|---|---|
| `fal-ai/ffmpeg-api/loudnorm` | `audio_url`*, `integrated_loudness` (-70..-5, default -18), `true_peak` (-9..0, default -0.1), `loudness_range` (1-20, default 7), `print_summary`, `dual_mono`, `linear` (needs the `measured_*` values) | `.result.audio.url`, `.result.summary` when requested |
| `fal-ai/ffmpeg-api/merge-audios` | `audio_urls`* (2-5 URLs, played in order, not mixed), `output_format` | `.result.audio.url` |
| `fal-ai/ffmpeg-api/metadata` | `media_url`* | `.result.media.duration`, plus codec, sample rate, channels |

All three are compute-billed at a tiny rate; an estimate of one cent per call is a safe upper bound for short files.

Targets (conventions, not model facts): -16 LUFS for speech delivered on its own (podcast, voice note), -14 LUFS
for music published to streaming, -18 to -20 LUFS for a narration that will be mixed with music under picture, true
peak at -1 dBTP for anything that will be re-encoded. Normalize the final joined file, never the chunks one by one.

No listed fal endpoint mixes two tracks on top of each other. Voice over a music bed, ducking and the mux onto
video belong to `pipelines`; hand over the normalized voice file, the bed, both durations and the SRT.
