# Audio troubleshooting

Symptom → cause → action, for jobs that failed and for jobs that "succeeded" with the wrong sound. Platform error
types and billing rules: [platform.md](platform.md) §4-5. Helper error kinds and resume rules:
[cli-contract.md](cli-contract.md). Budget for every row: at most 3 attempts per step, something changes each time,
a job that has a request ID is resumed with `gm.py wait`, never resubmitted.

## 1. Request rejected (HTTP 422, `kind:"validation"`)

Schema-level rejections come back before any work is done and normally cost nothing.

| Signal | Cause | Action |
|---|---|---|
| `missing` on `text` | The model takes `prompt` (Gemini TTS, MiniMax speech, music models) or `text_prompt` (Mirelo video endpoints; its text-to-audio takes `prompt`) | Read `required` in `genmedia schema <endpoint_id> --json`; move the text. |
| `missing` on `prompt` | The model takes `text` (ElevenLabs TTS and SFX, xAI, Chatterbox, Inworld) or `inputs` (text-to-dialogue) | Same. |
| `missing` on `lyrics` | `minimax/music-3` needs lyrics | Write lyrics with the user, or switch to `elevenlabs/music/v2.5` with `force_instrumental:true` for an instrumental. |
| `missing` on `duration` | `cassetteai/music-generator` requires it (10-180, integer) | Add it. |
| `missing` on `preview_text` | `fal-ai/minimax/voice-design` needs both `prompt` and `preview_text` | Add a 1-2 sentence preview in the target language. |
| `enum`, `literal_error`, `one_of` on `language_code`, `language`, `language_boost`, `output_language`, `voice` | Value borrowed from another model (`"tr"` sent to Gemini, `"Turkish"` sent to xAI) | Copy the exact string from `genmedia schema <endpoint_id> --format openapi --json`. |
| `string_too_long`, `too_long`, or a message naming a maximum length | Text above the model limit (ElevenLabs v3 5000, MiniMax 10000, xAI 15000, Chatterbox multilingual 300, ElevenLabs SFX 450, Inworld 2000) | `audiokit.py chunk` with a smaller `--max-chars`. Never truncate silently. |
| `too_short` / `too_long` on `speakers` or `audio_urls` | Gemini `speakers` needs 2-10 entries; `fal-ai/ffmpeg-api/merge-audios` takes 2-5 URLs | One speaker: drop `speakers`, use `voice`. More than five files: merge in rounds or use `audiokit.py concat`. |
| `greater_than_equal`, `less_than_equal` on a duration field | Outside the model window (ElevenLabs SFX 0.5-22 s, MMAudio 1-30 s, Mirelo up to 600 s, ElevenLabs Music 3000-600000 ms) | Clamp, tell the user the adjusted value, or route to the model with the wider window. |
| 422 with empty `fields` after a queued job | The CLI truncates field details of queued failures | Compare the input with the OpenAPI schema; if it matches, treat as a runtime error: unreachable or oversized source file, unsupported format, content policy. Check https://fal.ai/dashboard/requests. |

## 2. Source file problems

| Signal | Action |
|---|---|
| `file_download_error` | The URL is not fetchable by fal (local path, expired CDN link, auth wall). Upload the local file again with `gm.py upload` and use the new `cdn_url`. |
| `unsupported_audio_format`, `unsupported_video_format` | Convert locally: `audiokit.py extract <file> --out <file>.mp3` (or `.wav`), upload, retry once. |
| `audio_duration_too_short` on a clone | MiniMax voice-clone wants at least 10 s. Ask for 10-60 s of clean solo speech; do not pad with silence. |
| `audio_duration_too_long`, `video_duration_too_long`, `file_too_large` | Trim with `audiokit.py extract --start --duration` (ask first if wanted content would be lost), or pick the model with the wider limit (HeyGen 8 minutes, Kling video-to-audio 3-20 s and 100 MB, Qwen clone 300 s). |

## 3. The job succeeded but the result is wrong

| Symptom | Likely cause | Action |
|---|---|---|
| No audio file; `result.audio` is a very long string | MiniMax `output_format` `hex` (the default returned a file on 2026-09-21; a string means fal changed it) | Resend with `"output_format":"url"`. It is a new paid job: say so. |
| `outputs[]` has several files and the wrong one was delivered | Multi-sample or multi-stem model (Mirelo `num_samples` default 2, Sonilo `audios[]`, Demucs stems, Kling video-to-audio returns video and audio) | Match by `outputs[].json_path` (`audio[1]`, `vocals`, `video`), not by position. Send `num_samples:1` next time. |
| Wrong language, or a heavy foreign accent | Language field omitted, wrong field for this model, or a free-string field the model ignored | Set the enum-backed field (Gemini `language_code`, xAI `language`, MiniMax `language_boost`). ElevenLabs with `language_code:"tr"` still wrong: switch to a model whose enum lists the language and tell the user why. |
| Turkish letters read wrong (ı/i, ğ dropped) | ASCII-folded script, or text passed through shell quoting | Restore diacritics; write the input JSON with the Write tool and pass it with `--input`; never inline the text in a shell command. |
| A name, brand, acronym or number is misread | The model guessed the pronunciation | Respell the word phonetically, spell numbers out, or add a MiniMax `pronunciation_dict` entry. Regenerate only the affected chunk (`gm.py batch --retry-failed` does not apply to completed jobs: give the fixed chunk a new job id such as `c004b`, then pass the files to `audiokit.py concat` explicitly). |
| Stage directions are spoken aloud ("pause", "laughs") | Tag syntax of another model | Use this model's tags (MiniMax `<#0.5#>` and `(laughs)`, xAI `[pause]`, Gemini `[short pause]`) or remove them. ElevenLabs v3 gets plain punctuation. |
| The voice changes between chunks | Different settings per chunk, high randomness | Same `voice`, same settings, same `seed` where available, Gemini `temperature` 0.6-0.8, ElevenLabs `stability` 0.6+. Regenerate the outlier chunk only. |
| The end of a chunk is clipped or swallowed | Text ended without terminal punctuation, or a tag at the very end | End every chunk with `.`, `!` or `?` (the chunker splits at sentence ends); move trailing tags inside the sentence. |
| Narration too long or short for its slot | Speaking rate differs from the estimate | Under 10% off: adjust `speed` (MiniMax 0.5-2, ElevenLabs turbo/multilingual 0.7-1.2) or the Gemini style note ("slightly faster pace"). More: edit the text with the user. Do not time-stretch speech by more than a few percent. |
| Audible click or uneven pause at chunk joins | Hard cuts between files | `audiokit.py concat --gap-ms 200` to 300; chunk at paragraph ends; keep one output format across chunks. |
| A cloned voice sounds unlike the speaker | Noisy, short, musical or multi-speaker sample | New sample: 20-60 s, one speaker, no music, natural pace; try `noise_reduction:true` and `need_volume_normalization:true`; each clone is a new charge, so fix the sample first. |
| A cloned voice ID stopped working | MiniMax deletes a clone that no TTS call used within 7 days | Clone again (paid) and update `.genmedia/voices.json`; use it once right after cloning. |
| Music has vocals although an instrumental was asked | Only the prompt said "instrumental" | ElevenLabs Music: `force_instrumental:true` (prompt mode). Other models: say "instrumental, no vocals, no choir" and re-roll once, then switch model. |
| Music ignores the requested length | Model treats duration as an upper bound (`minimax/music-3`), has no duration field (`google/lyria-3.5`: state the length in the prompt), or defaults high (Stable Audio 2.5: 190 s) | Read `.result.duration` or probe the file; trim or fade in the edit; for exact lengths use `elevenlabs/music/v2.5` with `music_length_ms`. |
| The bed fights the narration | Busy midrange, lead melody | Regenerate with "no lead melody, sparse midrange, leaves room for voice-over"; level and ducking are set in `pipelines`. |
| SFX is a collage of several sounds | Several events in one prompt | One event per call; layer in the edit. Raise ElevenLabs `prompt_influence` for a more literal result. |
| Foley is out of sync or generic | No prompt, clip longer than the model window, or fast cuts | Describe the visible actions in order; keep within the limit (MMAudio 30 s, Mirelo 600 s); split at cuts, or use Sonilo `segments`. |
| Foley result has two soundtracks | The source clip already had audio | Ask `video` for a silent render or strip the track locally, then rerun; or keep the native audio. |
| Transcript is English-looking nonsense for Turkish audio | Wizper `language` default `en` | Set `"language":"tr"`, or use Scribe v2. |
| Transcript misses names and terms | Out-of-vocabulary words | Scribe `keyterms` (adds 30%), then correct the rest by hand in the `.txt`. |
| Speakers are merged or split wrongly | Overlapping talk, similar voices | Report it; offer manual speaker names only where the user cares. Diarization labels are not identities: never name a real person from a voice. |
| Captions drift later and later | The aligned text is not what was said (ad-libs, skipped lines), or an `--offset` was forgotten | Re-transcribe with Scribe and cut captions from that; apply `--offset` for narration that starts late in the video. |
| Caption timing is coarse | Source was Wizper (`approximate_timing:true`) | Re-run on Scribe v2 or forced alignment for word-accurate cues. |
| Dub comes back without the original music | One-call dubbing re-voices the whole track | Use the manual chain: Demucs or audio-isolation to keep the bed, TTS the speech, remix in `pipelines`. |

## 4. Helper and platform

| Signal | Action |
|---|---|
| `status:"pending"` with a `resume` command | The job is still running and billable. Run the `gm.py wait ...` command later. Never submit again. |
| `kind:"content_policy"` | Never resend unchanged. Tell the user which text or file was flagged and offer a compliant rewrite. Impersonation and deceptive-voice requests are not rewritten, they are declined. |
| `kind:"auth"`, locked balance | Stop all generation. The user fixes the key or tops up; never ask for or handle the key. |
| `kind:"rate_limit"`, `kind:"server"` | Wait briefly, then `gm.py wait` or rerun the same batch command once. A second 5xx: offer the next tier in [routing-audio.md](routing-audio.md); if the user named the model, ask first. |
| `kind:"not_found"` on an endpoint | The cached ID is stale: `genmedia models "<name>" --no-classify --limit 10 --json`, newest active match, tell the user which one. Check the stale-ID table in [routing-audio.md](routing-audio.md). |
| `audiokit.py` says `ffmpeg_missing` / `ffprobe_missing` | Use the fal utilities named in the message (`fal-ai/ffmpeg-api/merge-audios`, `fal-ai/ffmpeg-api/loudnorm`, `fal-ai/ffmpeg-api/metadata`) or the duration fields of the result. WAV files probe without ffprobe. |
| `audiokit.py concat --label` says `incomplete` | A chunk failed or is still pending: rerun the same `gm.py batch` command (add `--retry-failed` after fixing the input), then concat again. |
| `audiokit.py captions` says `no_timestamps` | The result has no `words[]` or `chunks[]` (Nemotron returns text only; a TTS result is not a transcript). Run Scribe v2 or forced alignment. |
| A delivered link stopped working | CDN links are public and may expire. The local file is the durable copy; re-upload it when a URL is needed again. |
