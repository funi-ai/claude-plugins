# Music, sound effects and foley

Inputs and prompt craft for music, SFX and video-to-audio models. Fields, enums and limits were read from the live
OpenAPI schemas on 2026-09-19; prices are that day's `genmedia pricing` and `llms.txt` numbers and must be confirmed
with `gm.py price`. Tiers and alternates: [routing-audio.md](routing-audio.md). Calling convention:
[cli-contract.md](cli-contract.md). `gm.py` and `audiokit.py` stand for the full helper calls shown in SKILL.md.

Prompts for these models are written in English. Lyrics stay in the language they are sung in.

## 1. Music model cards

`*` = required.

### `elevenlabs/music/v2.5` - default

Two mutually exclusive modes. Nothing is formally required, so a wrong mix is not always a 422: build it right.

| Mode | Fields | Rules |
|---|---|---|
| Prompt | `prompt` (up to 4100 chars), `music_length_ms` (3000-600000; omitted = model decides), `force_instrumental` | `force_instrumental` and `music_length_ms` work only with `prompt`. Always set `music_length_ms`: the price follows the length. |
| Plan | `composition_plan: {chunks: [...]}` with 1-30 chunks, optional `seed` | `seed` works only with a plan. Each chunk: `text`* (optional `[Section name]`, lyric lines, `{inline direction}`; at most 30 lines of 200 chars), `positive_styles`* (list, English; the first chunk sets genre and tone), `duration_ms`* (3000-120000), `negative_styles`, `context_adherence` (`low`, `medium`, `high`), `audio_reference` `{audio_url, start_ms, end_ms, strength}` (window up to 30 s). |

`output_format` is a codec string, default `mp3_48000_192`. Output `.result.audio.url`. Billed per **started**
minute of output (~$0.60 as of 2026-09-19): 30 s costs one minute, 61 s costs two. Pick 58 s, not 62 s, when
either works.

```json
{"prompt": "Warm lo-fi hip hop bed for a product explainer, 82 BPM, dusty Rhodes chords, soft brushed drums, round sub bass, vinyl crackle, no lead melody, leaves room for a voice-over, gentle 4-bar intro and a clean ending",
 "music_length_ms": 58000, "force_instrumental": true}
```

Use a plan when the user needs sections at exact times (intro 8 s, verse 20 s, drop at 0:28) or sung lyrics in a
fixed structure. Chunk durations add up to the track length.

### `minimax/music-3` - songs with the user's lyrics, cheapest per second

`prompt`* (style, mood, vocals, instrumentation, arrangement; a structured caption with genre, BPM, key and a
section plan gives the most control) and `lyrics`* are **both required**. Structure tags `[intro]`, `[verse]`,
`[pre-chorus]`, `[chorus]`, `[post-chorus]`, `[bridge]`, `[instrumental]`, `[solo]`, `[outro]` must each sit on
their own line; text on the same line as a tag is dropped. `duration` 1-300 s is an upper bound (default 60); the
real length comes back as `.result.duration`. Also `seed`, `guidance_scale`, `num_inference_steps`. Output
`.result.audio.url` (44.1 kHz stereo WAV). ~$0.002 per second as of 2026-09-19.

```json
{"prompt": "Upbeat Turkish indie pop, 118 BPM, female lead vocal, bright clean guitars, claps on the chorus, radio mix",
 "lyrics": "[verse]\nSabah vapuru kalkar, martılar peşimde\nCebimde bir simit, güneş yüzümde\n[chorus]\nİstanbul, yine sen\nHer sokakta bir şarkı, söyler dururum ben\n[outro]",
 "duration": 45}
```

Lyrics in a language the model card does not name: generate a 20-30 s draft first (a few cents) and let the user
judge the pronunciation before the full song.

### Others

| Endpoint | Input | Output | Notes |
|---|---|---|---|
| `cassetteai/music-generator` | `prompt`*, `duration`* (10-180 s, integer) | `.result.audio_file.url` | Cheapest instrumental bed, billed per output minute. The output key is `audio_file`, not `audio`. |
| `sonilo/v1.1/text-to-music` | `prompt`*, `duration` (1-600 s, default 90), `num_samples` (1-3) | `.result.audio.url` (first), `.result.audios[]` (all, AAC/m4a) | Billed per second and per sample; a sample under 10 s bills as 10 s. fal describes the output as licensed and commercial-use-safe: still check the model page. |
| `google/lyria-3.5` | `prompt`* (up to 5000 chars), `image_url` (mood reference) | `.result.audio.url` (MP3), `.result.lyrics` | Successor of `fal-ai/lyria3/pro` (verified 2026-09-22, same fields). No duration field: put the length in the prompt ("a 2-minute track" or section timestamps such as `[0:00-0:30] Intro`). `negative_prompt` is not supported: say what you want, not what to avoid. Flat price per track. |
| `fal-ai/stable-audio-25/text-to-audio` | `prompt`*, `seconds_total` (1-190, **default 190**), `seed`, `guidance_scale`, `num_inference_steps` (4-8) | `.result.audio.url` | Flat price per track whatever the length; set `seconds_total` anyway so the cut fits. Never set `sync_mode`. |
| `sonilo/v1.1/video-to-music` | `video_url`*, `prompt`, `prompt_influence` (0-1), `start_offset`, `duration` (up to 600 s), `num_samples` (1-3) | `.result.audio.url`, `.result.audios[]` | Scores to picture. Without `prompt` it captions the video itself. Returns audio only; putting it on the video is `pipelines`. |

## 2. Music prompt craft

Write one dense sentence or a short list in this order; leave out what you do not care about rather than padding.

1. **Use** - what it sits under: voice-over bed, ad sting, game loop, intro ident, full song.
2. **Genre and era** - "90s boom bap", "modern cinematic hybrid", "Anatolian psych rock", not "cool music".
3. **Tempo and feel** - BPM number plus groove: "96 BPM, laid-back swing", "140 BPM four-on-the-floor".
4. **Instrumentation** - three to five named sources: "felt piano, bowed cello, soft sub, shaker". Name regional
   instruments plainly (bağlama, ney, darbuka) when the brief calls for them.
5. **Structure** - "4-bar intro, build at 0:20, full drop at 0:30, clean ending on the downbeat".
6. **Mood arc** - where it starts and where it lands: "curious to confident".
7. **Mix notes** - "no lead melody", "sparse midrange, leaves room for narration", "wide stereo pads", "no vocals".
8. **Ending** - "clean ending" for a cut, "seamless loop" for a bed that repeats.

Rules:
- Under a voice: no lead melody, no vocals, sparse 1-4 kHz. Say so in the prompt and set `force_instrumental` where
  the model has it. "Instrumental" in the prompt alone is a wish, not a switch.
- Length: cut length plus about 2 s of tail, then trim or fade in the edit. Mind billing steps (started minutes,
  per-second, per-track).
- Never name living artists, bands or songs as a style target. Describe the traits instead (tempo, instruments,
  production era). Requests to imitate a specific artist's voice are refused.
- One idea per track. "Epic orchestral trap with jazz flute and polka" produces mush; offer two variations instead.
- Variations: change one axis (tempo, lead instrument, mood), keep the rest of the prompt identical, and label them.

Examples:

```text
Corporate explainer bed: modern minimal electronica, 100 BPM, muted pluck arpeggio, warm pad, light rimshot groove, optimistic and steady, no lead melody, no vocals, clean ending.
15-second ad sting: bright funk-pop, 116 BPM, slap bass, tight horn stab on the last beat, handclaps, energetic start to finish, hard stop at the end.
Documentary underscore: slow cinematic ambient, 60 BPM, bowed strings, ney flute phrases far in the background, deep drone, contemplative, no percussion, long fade out.
```

## 3. Sound effects

| Endpoint | Input | Output | Notes |
|---|---|---|---|
| `fal-ai/elevenlabs/sound-effects/v2` | `text`* (up to 450 chars), `duration_seconds` (0.5-22; omitted = automatic), `loop`, `prompt_influence` (0-1, default 0.3), `output_format` | `.result.audio.url` | Default. Per-second price: set the duration. Higher `prompt_influence` = more literal, less varied. |
| `sonilo/v1.1/text-to-sound-effects` | `prompt`*, `duration` (0.5-180 s, default 8), `audio_format` (`aac` default, `mp3`, `wav`, `flac`) | `.result.audio.url`, `.result.audios[]` | Longer than 22 s. Ask for `wav` or `mp3` when the file goes into an editor. |
| `mirelo-ai/sfx2.0/text-to-audio` | `prompt`* (1-2000 chars), `negative_prompt`, `duration` (0.1-600 s, **default 30**), `num_samples` (1-4, **default 2**), `upload_audio_format`, `seed` | `.result.audio[]` (list) | Several takes per call. Billed per second and per sample, so the defaults bill 60 s: set `duration` and send `num_samples:1` unless variations are wanted. No loop or ambience mode (SFX 1.6 had one): loops on ElevenLabs. |

Prompt craft: **source + action + material + space + perspective**, one event per call.

```text
Heavy wooden door slams shut in a stone hallway, short reverb tail, close perspective.
Single soft UI confirmation chime, glassy, two ascending notes, dry, no reverb.
Steady rain on a tin roof with distant thunder, no voices, no music, seamless loop.
Fast cinematic whoosh passing left to right, airy, ends abruptly.
```

- Layered scenes (rain + traffic + footsteps): generate each layer separately and mix in the edit; one prompt with
  three sources gives the model the choice of which to drop.
- State what must be absent when it matters: "no music", "no voices".
- Loops: `loop:true` (ElevenLabs), duration 8-15 s, and say "seamless loop".
- UI sounds and stings: 0.5-2 s, "dry, no reverb", generate 2-3 takes and let the user choose.

## 4. Foley for an existing video

First question to answer yourself: does the clip already have sound? `audiokit.py probe <file>` shows `has_audio`.
Native-audio video models already deliver a track; add foley only to silent clips or when the user wants it replaced.

| Endpoint | Input | Output | Limits and notes |
|---|---|---|---|
| `mirelo-ai/sfx2.0/video-to-video` | `video_url`*, `text_prompt`, `negative_prompt`, `preserve_speech` (default true), `duration` (1-600 s, default 10), `num_samples` (1-4, **default 2**), `seed` | `.result.video[]` (list of videos with the new track) | Default. Set `duration` to the clip length. Speech already in the clip is kept unless `preserve_speech` is false. `num_samples:1` for one result. |
| `fal-ai/mmaudio-v2` | `video_url`*, `prompt`*, `negative_prompt`, `duration` (1-30 s, default 8), `num_steps`, `cfg_strength`, `seed` | `.result.video.url` | A tenth of the price; `prompt` is required; clips up to 30 s. |
| `sonilo/v1.1/video-to-sound-effects` | `video_url`*, `prompt`, `segments: [{start, end, prompt}]`, `audio_format` | `.result.audio.url`, `.result.audios[]` | Audio only, matched to the video length. Per-segment prompts for clips where the action changes. |
| `mirelo-ai/sfx2.0/video-to-audio` | `video_url`*, `text_prompt`, `negative_prompt`, `preserve_speech`, `return_speech`, `duration` (1-600 s, default 10), `num_samples` (1-4, default 2), `upload_audio_format` | `.result.audio[]`; the kept speech at `.result.speech.audio.url` with `return_speech` | Audio-only variant of the default. |
| `fal-ai/kling-video/video-to-audio` | `video_url`* (.mp4/.mov, up to 100 MB, 3-20 s), `sound_effect_prompt`, `background_music_prompt` (each up to 200 chars), `asmr_mode` | `.result.video.url` and `.result.audio.url` | SFX plus a music bed in one flat-priced call. Both prompts default to a car-race demo text: always set both, or the clip gets screeching tyres. |

Prompt what is **seen**, in order: "footsteps on gravel, a car door closes, engine starts and pulls away". Add the
space ("outdoors, light wind") and what to avoid ("no music, no speech"). Upload the local clip first
(`gm.py upload`), pass the `cdn_url`. After the run, check that the returned duration matches the clip
(`audiokit.py probe`). Several samples: present them numbered; the pick is the user's.

## 5. Cost and licensing

- Estimate = unit price x seconds (or minutes, or tracks) x `num_samples`. Assume samples multiply the price
  unless the model's pricing text says otherwise. Units differ per model: per second (MiniMax Music, Sonilo,
  ElevenLabs SFX, Mirelo, MMAudio), per started minute (ElevenLabs Music, CassetteAI), per track (Lyria 3.5, Stable
  Audio 2.5), per video (Kling video-to-audio). Rules and thresholds: [platform.md](platform.md) §7-8.
- Licensing: say nothing about rights from memory. Each model carries its own licence: check the badge on
  `https://fal.ai/models/<endpoint_id>` (the catalog calls the field `license_type`; the CLI output does not show
  it) before client or commercial work, and tell the user that is where the answer lives.
