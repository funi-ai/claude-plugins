---
name: audio
description: >-
  One-off speech, music, sound effects and speech tools via fal's genmedia CLI: text-to-speech with a schema-verified Turkish path (Gemini 3.1 Flash TTS, ElevenLabs v3), dialogue, voice cloning, music, foley for silent video, transcription (Scribe v2), SRT/VTT, dubbing, cleanup, loudness. Voiced or narrated videos go to a scenario skill; audio alone stays here.
  Use when: "bunu seslendir", "Türkçe seslendirme yap", "fon müziği yap", "bu videonun altyazısını çıkar", "read this script aloud", "clone my voice", "add sound to this silent clip", "transcribe this recording", "dub this video into English".
  Chain: produces audio files, CDN urls, durations and SRT/VTT for `video` (lipsync, talking head) and `pipelines` (muxing).
  NOT for: narrated explainers (use `video-explainer`); voiced ads (use `ads`); voiced shorts (use `short-video`); muxing audio or captions onto video (use `pipelines`); talking head, lipsync, native-audio clips (use `video`); model choice or prices (use `models`); setup problems (use `setup`).
argument-hint: "[what to make or process] [--voice <name>] [--lang <code>] [--model <endpoint-id>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/audiokit.py" *) Bash(command -v genmedia) Bash(genmedia version *) Bash(genmedia models *) Bash(genmedia schema *) Bash(genmedia pricing *) Bash(genmedia docs *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 and python3 >= 3.8. ffmpeg and ffprobe are optional (local concat and duration checks).
---

# Audio

Make and process sound with fal models: speech (any language the model's schema lists, Turkish first-class),
dialogue, cloned voices, music, sound effects, foley for silent clips, transcripts, captions, dubbing, cleanup and
loudness. One job or one narration at a time; anything that puts audio onto picture belongs to `pipelines`, and a
voiced video as a whole belongs to its scenario skill (`video-explainer`, `ads`, `short-video`).

## Step 0 — Preflight

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
```

- `blockers` non-empty: stop. Missing key: tell the user to run `genmedia setup` or export `FAL_KEY` themselves,
  then wait. Never read, print, request or type a key. Anything else broken: `/genmedia-skills:setup`.
- `ffmpeg.found:false` only disables local concat and probing: join chunks with `fal-ai/ffmpeg-api/merge-audios`
  and take durations from result fields instead. Details: `references/cli-contract.md`.

## UX rules

1. Reply in the user's language. Spoken text and lyrics stay in the language the audience will hear; never
   translate or "improve" a script unless asked. Style, music and SFX prompts are written in English.
2. No JSON, request IDs or tool narration in chat. Wait silently; at most one status line per batch.
3. Act on defaults. **Question budget: 1**, only for voice or language when neither the script's language, the
   brief ("warm female narrator") nor earlier turns settle it. Ask it as labelled options.
   Language = the language of the script, not of the chat. No voice named: a short text (up to ~1500 characters)
   gets the default voice that fits the brief, plus one line offering another voice; a longer one gets the
   audition (step 5), which replaces the question. The cloning consent gate and cost confirmations are gates, not
   questions; they do not count.
4. Never infer approval from silence. A voice for a long narration is expensive to redo: audition first (step 5).
5. Cost policy (`references/platform.md` §7-8): estimate from `gm.py price`, never from memory. Under USD 0.50 run;
   USD 0.50 to USD 2 say the estimate in one line and run; USD 2 or more confirm first. The `config` values preflight
   prints (`announce_above_usd`, `confirm_above_usd`) override these defaults. Units differ: speech is priced per
   1000 characters, music and SFX per second, minute or track, STT and dubbing per input minute (rounded up).
   Never downgrade or swap a model the user named.
6. Bounded repair: 3 attempts per step, something changes each time, a content-policy rejection is never resent
   unchanged, a job with a request ID is resumed (`gm.py wait`), never resubmitted.
7. **Voice consent.** Clone or convert only the user's own voice or one they confirm they have the rights to.
   Ask once, plainly, before uploading the sample. Public figures, or "make it sound like <celebrity>": refuse.

## Discovery guardrail

Routing below is a dated cache (2026-09-19). Before the first paid call to an endpoint in a session:

```bash
genmedia models --endpoint_id <endpoint_id> --json
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
```

`status` must be `active`. The helper resolves the nested shapes the short CLI view hides (voices, `speakers`,
`voice_setting`, language enums); `--field <name>` adds one field's description. Never invent IDs, fields, voices or
language values. A model you do not know: `genmedia models "<name>" --no-classify --limit 10 --json`, newest active match, say which you picked.
Never use smart routing (`genmedia run` with a prompt instead of an endpoint ID).

## Routing

Full dated tables with prices and limits: `references/routing-audio.md`. Parameter detail per model:
`references/tts-and-voices.md`, `references/music-and-sfx.md`, `references/speech-tools.md`.

| Intent | Default endpoint | Why | Reach for instead when |
|---|---|---|---|
| Speech, English or general | `fal-ai/elevenlabs/tts/eleven-v3` | fal's top-listed TTS (no arena board for audio); `timestamps` option | long or cheap: `xai/tts/v1` (15000 chars per call) |
| Speech, Turkish or any non-English | `fal-ai/gemini-3.1-flash-tts` | `language_code` enum lists the language, so support is verifiable; `style_instructions` direct the read | budget or very long: `xai/tts/v1` (`language:"tr"`); speed, pitch, emotion numbers: `fal-ai/minimax/speech-2.8-hd` |
| Dialogue, several voices | `fal-ai/gemini-3.1-flash-tts` with `speakers` (2-10) | one call, language enum still applies | English with ElevenLabs voices: `fal-ai/elevenlabs/text-to-dialogue/eleven-v3` |
| Reusable cloned voice | `fal-ai/minimax/voice-clone` then a MiniMax speech endpoint | returns a `custom_voice_id`; Turkish works through `language_boost` | one-off line: `fal-ai/zonos2` (no Turkish normalization); Turkish, short lines: `fal-ai/chatterbox/text-to-speech/multilingual` |
| New voice from a description | `fal-ai/minimax/voice-design` | returns `custom_voice_id` plus a preview | - |
| Re-voice a recording | `fal-ai/elevenlabs/voice-changer` | keeps timing and performance | - |
| Music, instrumental or sung | `elevenlabs/music/v2.5` | newest; `force_instrumental`; exact length in ms | song with your lyrics, cheap: `minimax/music-3`; bed under USD 0.10: `cassetteai/music-generator`; score to picture: `sonilo/v1.1/video-to-music` |
| Sound effect | `fal-ai/elevenlabs/sound-effects/v2` | up to 22 s, `loop` | longer than 22 s: `sonilo/v1.1/text-to-sound-effects`; several takes per call: `mirelo-ai/sfx2.0/text-to-audio` |
| Foley for a silent video | `mirelo-ai/sfx2.0/video-to-video` | returns the video with a synced track, up to 600 s; keeps speech already in the clip | cheap, up to 30 s: `fal-ai/mmaudio-v2`; audio only or per-segment prompts: `sonilo/v1.1/video-to-sound-effects` |
| Transcript, speakers, word times | `fal-ai/elevenlabs/speech-to-text/scribe-v2` | word timestamps plus diarization | translate speech to English text: `fal-ai/wizper` (`task:"translate"`) |
| Captions for a script you already have | `fal-ai/elevenlabs/forced-alignment` | exact word times for known text | no script: Scribe v2 |
| Dub a video | `fal-ai/elevenlabs/dubbing` | one call, `target_lang` ISO code | lips re-synced: `fal-ai/heygen/v2/translate/precision`; full control: manual chain in `references/speech-tools.md` |
| Clean speech | `fal-ai/elevenlabs/audio-isolation` | strips music and noise, takes audio or video | noise only, cheaper: `fal-ai/deepfilternet3`; stems: `fal-ai/demucs` |
| Loudness, join, probe | `fal-ai/ffmpeg-api/loudnorm`, `fal-ai/ffmpeg-api/merge-audios`, `fal-ai/ffmpeg-api/metadata` | EBU R128, ordered concat (2-5 files), duration | local ffmpeg through `scripts/audiokit.py` is free |

Tie-breakers, in order:
1. The user named a model: use it after the alive check. Mention a better fit once; never swap silently.
2. Non-English speech: only a model whose schema **enum** lists the language. A free-string language field
   (ElevenLabs `language_code`) proves nothing: audition one short line before a long read.
3. Script longer than the model's text limit: chunk (step 4) rather than switching to a worse voice.
4. Word timings needed: generate the speech, then run forced alignment with the same text. It has a fixed output
   shape; the TTS `timestamps` array does not.
5. Several fit: pick the cheaper per unit, then the one with fewer required fields.

Named traps:
- **text-vs-prompt.** The spoken text goes in `text` on ElevenLabs, xAI, Chatterbox, Inworld, Zonos2 and
  ElevenLabs SFX; in `prompt` on Gemini TTS and MiniMax speech; in `text_prompt` on the Mirelo video endpoints (`prompt` on its text-to-audio); in `inputs[].text` on
  text-to-dialogue. Read `required` in the schema; never guess.
- **language field zoo.** Gemini `language_code:"Turkish (Turkey)"`; ElevenLabs `language_code:"tr"` (free
  string); xAI `language:"tr"`; MiniMax `language_boost:"Turkish"`; Chatterbox multilingual
  `custom_audio_language:"turkish"`; dubbing `target_lang:"tr"`; HeyGen `output_language:"Turkish"`; Wizper
  `language:"tr"`; Nemotron `language:"tr-TR"`. Values do not transfer between models.
- **hex default.** MiniMax speech `output_format` defaults to `hex` in the schema. The default still returned a file
  URL on 2026-09-21; send `"output_format":"url"` anyway so a change on fal's side cannot leave a hex string.
- **Wizper speaks English.** Its `language` defaults to `en`; Turkish audio with the default comes back wrong.
  Always set it (`"tr"`). Auto-detect needs `null`, which `gm.py` drops: unknown language goes to Scribe v2.
- **lyrics required.** `minimax/music-3` rejects a request without `lyrics`. Instrumental: use
  `elevenlabs/music/v2.5` with `force_instrumental:true`, or an instrumental-only model.
- **started minutes.** ElevenLabs Music bills each started minute of output, dubbing each started input minute,
  forced alignment each started hour. 61 s of music costs two minutes.
- **samples multiply.** Mirelo endpoints default to `num_samples:2`, and Mirelo text-to-audio to 30 s; Sonilo bills per second and per sample. Send
  `num_samples:1` unless the user wants variations.
- **output key differs.** Mostly `.result.audio.url`; `audio_file` on `cassetteai/music-generator` and
  `fal-ai/deepfilternet3`; a list on Mirelo (`audio[]`, `video[]`); `audios[]` on Sonilo; `video` on foley,
  dubbing and HeyGen; one key per stem on Demucs; plain strings for `custom_voice_id`, `text`, `output`. `gm.py`
  downloads every URL it finds: match files by `outputs[].json_path`, not by position.
- **foley on a clip that already has sound.** Seedance, Kling v3 and Wan 3.0 clips usually carry native audio.
  Ask `video` for a silent render, or keep the native track; do not stack.

## Workflow

1. **Classify** the request with the Routing table. Collect: the exact text or the source file, language, voice
   hints, target duration, where the result is going (video bed, podcast, captions).
2. **Verify** the endpoint (Discovery guardrail). Build the input only from fields the schema lists.
3. **Estimate** and apply the cost gate. Characters include spaces and tags; minutes and hours round up.

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price fal-ai/gemini-3.1-flash-tts,fal-ai/elevenlabs/forced-alignment
   ```

4. **Long scripts.** Over the model's text limit, or over ~3000 characters on any model (a bad sentence should
   cost one chunk, not the whole read): save the script to `.genmedia/tmp/<label>.txt`, put every other input
   field in `<label>-base.json`, then chunk with `--max-chars` = 3000 or the schema's `maxLength` of the text
   field, whichever is smaller (Chatterbox multilingual 300, Inworld 2000):

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/audiokit.py" chunk --input .genmedia/tmp/<label>.txt --max-chars <n> --endpoint <endpoint_id> --text-field <text|prompt> --base-input .genmedia/tmp/<label>-base.json --label <label> --price-per-1k <usd>
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/tmp/<label>-plan.json
   ```

   It splits at sentence boundaries only, keeps every chunk under the limit and writes a resumable batch plan.
   Same voice, same settings, same seed (when the model has one) in every chunk.
5. **Audition** before any narration above ~1500 characters whose voice the user has not picked, and before a
   cloned voice is used at length: one representative sentence (under 200 characters, in the script's language) on 2-3 voices as one
   `gm.py batch`. Present numbered local files with one-word descriptions; the user picks; then run the full text.
6. **Local inputs** (voice sample, recording, video): upload first, pass the `cdn_url`. Say once that uploads are
   public links (`references/platform.md` §1).

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload ./sample.wav
   ```

7. **Run.** Write the input with the Write tool to `.genmedia/tmp/<label>.json` (no shell quoting, Turkish
   characters survive), then

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run <endpoint_id> --input .genmedia/tmp/<label>.json --label <label> --est-cost <usd>
   ```

   `status:"pending"`: run the printed `gm.py wait ...` later; never resubmit. Text results (transcripts,
   alignments): add `--no-download` and pipe into `audiokit.py captions` (`references/speech-tools.md`).
8. **Assemble and verify.** Join chunks in order, then measure:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/audiokit.py" concat --label <label> --plan .genmedia/tmp/<label>-plan.json --out genmedia-output/<label>/<label>.mp3 --gap-ms 250
   python3 "${CLAUDE_SKILL_DIR}/scripts/audiokit.py" probe genmedia-output/<label>/<label>.mp3
   ```

   `concat --label` takes the chunk files from the ledger in plan order and refuses an incomplete set; explicit
   files instead of `--label` also work. Check that the file exists, is not a few bytes long, and that its duration fits the target (narration for a
   fixed slot: within the slot; music bed: at least the cut length). Too long by under 10%: regenerate with a
   faster `speed` where the model has one, otherwise shorten the text with the user. Listen-proof what you can:
   for speech in a language you cannot audition, transcribe one chunk with Scribe v2 and compare with the script.
9. **Finish** when asked or when the audio goes under picture: loudness to -16 LUFS for speech-only delivery or
   -18 for a bed under video (`audiokit.py loudnorm`, free; without ffmpeg `fal-ai/ffmpeg-api/loudnorm`), captions
   (`references/speech-tools.md`). Muxing onto the video is `pipelines`.

## Delivery

One file:

```
<one line: what it is, in the user's language>
File: genmedia-output/<label>/<file>          (durable copy)
Link: <cdn url>                               (public, may expire)
<Model display name> · <voice or style> · <language> · <m:ss> · est. $<cost>
```

Audition:

```
Same sentence, three voices. Pick a number, or describe what to change.
1. <Voice> - <one-word character>   genmedia-output/<label>/v1_0.mp3
2. <Voice> - <one-word character>   genmedia-output/<label>/v2_0.mp3
3. <Voice> - <one-word character>   genmedia-output/<label>/v3_0.mp3
```

Transcript or captions: file paths of `.srt`/`.vtt`/`.txt`, detected language, number of speakers, duration, and
the first two cues as a preview. Never paste a whole transcript unless asked. Multi-file sets: add the
`gallery_url`. Cloned or designed voice: give the handle you stored (not the raw ID) and the 7-day rule.

## Errors

| Signal (`gm.py` `kind`, field `type` or message) | Action |
|---|---|
| `validation` with empty `fields` (the usual case: queued jobs lose field detail) | Compare the input with `gm.py schema <endpoint_id>`, in this order: text field name, language and voice strings, text length, required extras (`lyrics`, `duration`, `preview_text`), source URL reachable. Fix one thing, resend once. |
| `validation` with `missing` on `text` or `prompt` | text-vs-prompt trap: re-read the schema, move the text to the required field. |
| `validation` with `one_of`, `enum` or `literal_error` on a language or voice field | Value copied from another model. Take the exact enum string from `gm.py schema <endpoint_id>`. |
| `validation` with `sequence_too_long`, `string_too_long` or a `max_length` in the message | Text over the model limit: chunk (step 4). Never truncate silently. |
| Completed, but no audio file and a long `audio` string in `result` | MiniMax `hex` output (the default returned a file on 2026-09-21, so fal changed something): resend with `"output_format":"url"` (a new paid job; say so). |
| `audio_duration_too_short`, or a clone that sounds wrong | Sample under 10 s or noisy: ask for 10-60 s of clean solo speech, optionally run `fal-ai/elevenlabs/audio-isolation` first. |
| `file_download_error`, `unsupported_audio_format` | Upload the local file again (`gm.py upload`); convert to wav or mp3 locally first. |
| `content_policy` | Do not resend unchanged. Say which text was flagged, offer a rewrite; voice impersonation requests stay refused. |
| `auth`, `cli_missing` | Stop. User fixes key or install (`/genmedia-skills:setup`). |
| `rate_limit`, `server`, `pending` | Wait, then `gm.py wait` or rerun the same batch command. Never resubmit a job that has a request ID. |

More, including wrong-language output, mispronunciation, clipped endings and drifting captions:
`references/troubleshooting-audio.md`.

## Reference index

- `references/routing-audio.md` - read when choosing or pricing an endpoint, when a default is not active, or when the user names an old model ID (stale-ID table).
- `references/tts-and-voices.md` - read when building any speech, dialogue, clone or voice-design input: per-model fields, voices, language values, Turkish guidance, chunking, pronunciation, audition flow.
- `references/music-and-sfx.md` - read when writing a music, SFX or foley prompt, choosing a duration, or when the user asks about commercial use of generated music.
- `references/speech-tools.md` - read when transcribing, aligning, making SRT/VTT, dubbing, cleaning audio, separating stems, normalizing loudness or joining files.
- `references/troubleshooting-audio.md` - read when output is wrong although the job succeeded, or an error is not in the table above.
- `references/cli-contract.md` - read when a `gm.py` or raw `genmedia` call behaves unexpectedly, for JSON shapes, the batch plan format, resume rules and the raw-CLI fallback.
- `references/platform.md` - read when estimating cost, reacting to a fal error type, or before uploading private material (public URLs, billing, concurrency, safety).
- `scripts/gm.py` - the shared helper (preflight, price, upload, run, wait, batch, ledger).
- `scripts/audiokit.py` - local, free audio utilities: `chunk` (script to batch plan), `captions` (timestamps to SRT/VTT), `concat`, `probe`, `extract`, `loudnorm`.
