# Speech, dialogue and voices

Per-model inputs for text-to-speech, dialogue, cloning and voice design. Every field, enum and limit below was read
from the live OpenAPI schema on 2026-09-19; prices are that day's `genmedia pricing` numbers. It is a cache:
re-read `genmedia schema <endpoint_id> --format openapi --json` before the first paid call. Tiers, alternates and
stale IDs: [routing-audio.md](routing-audio.md). Calling convention and JSON shapes: [cli-contract.md](cli-contract.md).

`gm.py` and `audiokit.py` below stand for the full helper calls shown in SKILL.md. Inputs are JSON files written
with the Write tool to `.genmedia/tmp/<label>.json`, never shell-quoted text.

## 1. Model cards

`*` = required. "Text field" is where the spoken words go.

### `fal-ai/gemini-3.1-flash-tts` - default for Turkish and any non-English speech, dialogue, directed reads

| Field | Value |
|---|---|
| Text field | `prompt`* (not `text`), 1-50000 characters. Delivery notes may sit inline ("Say cheerfully: ...") and tags such as `[sigh]`, `[laughing]`, `[whispering]`, `[short pause]` are read as direction, not spoken. |
| `language_code` | Enum of display names, 87 entries: `"Turkish (Turkey)"`, `"English (US)"`, `"English (UK)"`, `"German (Germany)"`, `"French (France)"`, `"Spanish (Spain)"`, `"Arabic (Egypt)"`, `"Azerbaijani (Azerbaijan)"`, ... Omitted = auto-detect from the text. Always set it for non-English. |
| `voice` | Enum, 30 presets, default `Kore`. Schema notes: `Kore` strong, firm female; `Puck` upbeat, lively male; `Charon` calm, professional male; `Zephyr` bright, clear female; `Aoede` warm, melodic female. Others: `Achernar`, `Achird`, `Algenib`, `Algieba`, `Alnilam`, `Autonoe`, `Callirrhoe`, `Despina`, `Enceladus`, `Erinome`, `Fenrir`, `Gacrux`, `Iapetus`, `Laomedeia`, `Leda`, `Orus`, `Pulcherrima`, `Rasalgethi`, `Sadachbia`, `Sadaltager`, `Schedar`, `Sulafat`, `Umbriel`, `Vindemiatrix`, `Zubenelgenubi`. Ignored when `speakers` is set. |
| `style_instructions` | Up to 4000 characters of plain-language direction, kept apart from the text: pace, warmth, accent, energy. Write it in English. |
| `speakers` | 2-10 items `{speaker_id, voice}`; each `speaker_id` is an alias that must match a line prefix in `prompt` (`Ayse: ...`). Keep aliases short and ASCII; they only label whose line it is. |
| `temperature` | 0-2, default 1. Lower (0.6-0.8) keeps chunks of one narration consistent. |
| `output_format` | `mp3` (default), `wav` (24 kHz 16-bit mono), `ogg_opus`. |
| Output, price | `.result.audio.url`; ~$0.05 per 1000 characters as of 2026-09-19 - confirm with `gm.py price`. |

```json
{"prompt": "İstanbul'da sabah erken başlar. Vapur iskeleden ayrılırken martılar simit peşindedir.",
 "language_code": "Turkish (Turkey)", "voice": "Aoede",
 "style_instructions": "Warm documentary narrator, unhurried, slight smile, clear consonants.",
 "temperature": 0.7, "output_format": "mp3"}
```

### `fal-ai/elevenlabs/tts/eleven-v3` - default for English and general reads

| Field | Value |
|---|---|
| Text field | `text`*, 1-5000 characters. |
| `voice` | Free string, default `Rachel`. Schema examples: `Aria`, `Roger`, `Sarah`, `Laura`, `Charlie`, `George`, `Callum`, `River`, `Liam`, `Charlotte`, `Alice`, `Matilda`, `Will`, `Jessica`, `Eric`, `Chris`, `Brian`, `Daniel`, `Lily`, `Bill`. A name outside this list is unverifiable: audition it. |
| `language_code` | Free ISO 639-1 string (`"tr"`, `"de"`). No enum, so support cannot be proven from the schema. |
| `stability` | 0-1, default 0.5. Lower = more expressive and less repeatable; 0.5-0.7 for long narration. |
| `timestamps` | `true` adds a `timestamps` array. Its item shape is not documented; for captions use forced alignment ([speech-tools.md](speech-tools.md)). |
| `apply_text_normalization` | `auto` (default), `on`, `off`: spells out numbers and symbols. |
| Not on v3 | `speed`, `style`, `similarity_boost`, `previous_text`, `next_text` exist only on `fal-ai/elevenlabs/tts/turbo-v2.5` and `fal-ai/elevenlabs/tts/multilingual-v2` (`speed` 0.7-1.2); v3's schema does not list them, so do not send them. |
| Output, price | `.result.audio.url`; ~$0.10 per 1000 characters (turbo v2.5 ~$0.05) as of 2026-09-19. |

### `xai/tts/v1` - budget tier, longest single call

| Field | Value |
|---|---|
| Text field | `text`*, up to 15000 characters. Inline tags `[laugh]`, `[pause]`, `[sigh]`; wrapping tags `<whisper>..</whisper>`, `<slow>..</slow>`. |
| `language` | Enum: `auto` (default), `en`, `tr`, `de`, `fr`, `it`, `ja`, `ko`, `ru`, `hi`, `id`, `vi`, `bn`, `zh`, `es-ES`, `es-MX`, `pt-BR`, `pt-PT`, `ar-EG`, `ar-SA`, `ar-AE`. |
| `voice` | Enum, 28 presets, default `eve`: `ara`, `leo`, `rex`, `sal`, `luna`, `iris`, `atlas`, `aurora`, `orion`, `celeste`, `cosmo`, `helix`, ... The schema gives no gender or tone notes: audition. |
| `output_format` | Object `{codec: mp3|wav|pcm|mulaw|alaw, sample_rate: 8000..48000, bit_rate}`; default mp3, 24 kHz, 128 kbps. |
| Output, price | `.result.audio.url`; ~$0.015 per 1000 characters as of 2026-09-19. |

### `fal-ai/minimax/speech-2.8-hd` (and `fal-ai/minimax/speech-2.8-turbo`) - numeric control, cloned voices

| Field | Value |
|---|---|
| Text field | `prompt`*, 1-10000 characters. Pauses: `<#0.5#>` (0.01-99.99 s). Interjections: `(laughs)`, `(sighs)`, `(coughs)`, `(clears throat)`, `(gasps)`, `(sniffs)`, `(groans)`, `(yawns)`. |
| `output_format` | **`"url"`**. The schema default is `hex`; on 2026-09-21 the default still came back as a file URL (`platform.md` section 10), but send `url` so a change cannot leave a hex string. |
| `language_boost` | Enum of English names: `Turkish`, `English`, `German`, `French`, `Spanish`, `Arabic`, `Russian`, ... or `auto`. |
| `voice_setting` | Object: `voice_id` (free string, default `Wise_Woman`; schema examples `Friendly_Person`, `Inspirational_girl`, `Deep_Voice_Man`, `Calm_Woman`, `Casual_Guy`, `Lively_Girl`, `Patient_Man`, `Young_Knight`, `Determined_Man`, `Lovely_Girl`, `Decent_Boy`, `Imposing_Manner`, `Elegant_Man`, `Abbess`, `Sweet_Girl_2`, `Exuberant_Girl`), `speed` 0.5-2, `pitch` -12..12, `vol` 0.01-10, `emotion` (`happy`, `sad`, `angry`, `fearful`, `disgusted`, `surprised`, `neutral`), `english_normalization`. |
| `pronunciation_dict` | `{"tone_list": ["text/(pronunciation)", ...]}` replaces how a word is read. |
| `audio_setting` | `{format: mp3|pcm|flac, sample_rate, bitrate, channel}`; default mp3, 32 kHz, mono. |
| `voice_modify`, `normalization_setting` | Timbre, pitch and intensity offsets; built-in loudness target (default on, -18). |
| Output, price | `.result.audio.url` plus `.result.duration_ms`; ~$0.10 (HD) / ~$0.06 (Turbo) per 1000 characters as of 2026-09-19. |

```json
{"prompt": "Hoş geldiniz. <#0.4#> Bugün üç başlığımız var.", "output_format": "url", "language_boost": "Turkish",
 "voice_setting": {"voice_id": "Calm_Woman", "speed": 1.05, "emotion": "neutral"}}
```

### Others

- `fal-ai/chatterbox/text-to-speech/multilingual`: `text`* **up to 300 characters per request**; `voice` is a
  language name (`"turkish"`, `"english"`, ...) or the URL of a voice sample, in which case set
  `custom_audio_language` (enum includes `turkish`); `exaggeration` 0.25-2, `cfg_scale` 0-1 (0 reduces accent
  carry-over). Cheapest way to speak Turkish in a user's own voice; chunk aggressively.
- `fal-ai/inworld-tts`: `text`* up to 2000 characters, 113 named voices in an enum, English-centric; cheapest.
- `fal-ai/qwen-3-tts/text-to-speech/1.7b`: `text`*, `language` enum without Turkish; pairs with its clone endpoint.

## 2. Dialogue

Gemini, any listed language, one call:

```json
{"prompt": "Ayse: Vapur kaçta kalkıyor?\nMehmet: On dakikası var, koşarsak yetişiriz!\nAyse: O zaman simidi yolda alırız.",
 "language_code": "Turkish (Turkey)",
 "speakers": [{"speaker_id": "Ayse", "voice": "Aoede"}, {"speaker_id": "Mehmet", "voice": "Puck"}],
 "style_instructions": "Casual, slightly rushed, friendly."}
```

`fal-ai/elevenlabs/text-to-dialogue/eleven-v3`: `inputs`* is a list of `{text, voice}` in speaking order; optional
`stability` (rounded to 0, 0.5 or 1), `language_code` (free string), `seed`, `use_speaker_boost`. Output
`.result.audio.url`. Long dialogues: chunk with `audiokit.py chunk --unit line`. Lines stay whole; a single line
above `--max-chars` is split and every piece repeats its speaker prefix (`Ayse: `, `[S1] `).

## 3. Turkish (and any non-English language)

1. Choose a model whose enum lists the language: Gemini (`"Turkish (Turkey)"`), xAI (`"tr"`), MiniMax
   (`"Turkish"`), Chatterbox multilingual (`"turkish"`). The same check works for every language: read the enum.
2. ElevenLabs takes `language_code:"tr"` but the schema cannot confirm it. Use it only when the user asks for an
   ElevenLabs voice, and audition one sentence first.
3. Keep the script in Turkish with correct diacritics (ç, ğ, ı, İ, ö, ş, ü). Never ASCII-fold; "kış" and "kis" are
   different sounds. The helper passes UTF-8 through untouched.
4. Make the text speakable before sending it (this is editing for the ear, not rewriting; show the user what changed
   when it is more than numerals):
   - Numbers, dates, currency and units as words: "12,50 TL" → "on iki lira elli kuruş", "2026" → "iki bin yirmi altı".
   - Abbreviations expanded: "Dr." → "Doktor", "vb." → "ve benzeri", "km" → "kilometre".
   - Foreign brand names and acronyms respelled the way they should sound when the first audition misreads them
     ("iPhone" → "ayfon", "fal.ai" → "fal nokta ey ay"). Suffix apostrophes stay ("Google'ın").
   - One sentence per thought; long clause chains get commas where a speaker would breathe.
5. Style direction stays in English (`style_instructions`); only the spoken text is Turkish.
6. Proof what you cannot hear: transcribe the audition (or the first chunk) with Scribe v2 and compare with the
   script. A mismatch in a name or number means respell and regenerate that chunk only.

## 4. Pronunciation and pacing

| Need | Do |
|---|---|
| A word is misread | Respell phonetically in the text; on MiniMax add a `pronunciation_dict.tone_list` entry. |
| Pause | MiniMax `<#0.6#>`; xAI `[pause]`; Gemini `[short pause]`; ElevenLabs: end the sentence, start a new paragraph. |
| Faster or slower | MiniMax `voice_setting.speed`; ElevenLabs turbo/multilingual `speed` (0.7-1.2); Gemini: say it in `style_instructions` (the pace word alone moved a Turkish read between 1.2 and 2.1 words/s: `platform.md` section 10); xAI `<slow>..</slow>`. |
| Emotion | MiniMax `emotion`; Gemini `style_instructions` or an inline note; ElevenLabs lower `stability`. |
| Numbers read oddly | Spell them out; on ElevenLabs try `apply_text_normalization:"on"`; on MiniMax English `english_normalization:true`. |
| Planning length | Rule of thumb only: narration runs near 150 words per minute in English and 120-130 in Turkish. Always measure the result (`audiokit.py probe`, or `duration_ms` on MiniMax). |

## 5. Long scripts

Per-call text limits: Gemini 50000, xAI 15000, MiniMax 10000, ElevenLabs v3 5000, Inworld 2000, Chatterbox
multilingual 300. Chunk at ~3000 characters even below the limit: a repair then costs one chunk.

```bash
audiokit.py chunk --input .genmedia/tmp/<label>.txt --max-chars 3000 --endpoint fal-ai/gemini-3.1-flash-tts --text-field prompt --base-input .genmedia/tmp/<label>-base.json --label <label> --price-per-1k <usd from gm.py price>
gm.py batch --plan .genmedia/tmp/<label>-plan.json
audiokit.py concat --label <label> --plan .genmedia/tmp/<label>-plan.json --out genmedia-output/<label>/<label>.mp3 --gap-ms 250
```

- `--base-input` holds every field except the text (voice, language, style, `output_format`). The tool adds the
  text field per chunk, numbers jobs `c001`, `c002`, ... and refuses to lose a character.
- Keep voice, settings and (where the model has one) `seed` identical across chunks; lower Gemini `temperature`.
- `--continuity` adds `previous_text`/`next_text`. Use it only with `fal-ai/elevenlabs/tts/turbo-v2.5` and
  `fal-ai/elevenlabs/tts/multilingual-v2`, the endpoints whose schema lists those fields.
- A chunk failed: fix its text in the plan, rerun the same `gm.py batch` command with `--retry-failed`. `concat
  --label` refuses to build a narration with a missing chunk.
- No local ffmpeg: `fal-ai/ffmpeg-api/merge-audios` takes `audio_urls` (2-5 CDN URLs, in order) and returns
  `.result.audio.url`; merge in rounds for more than five chunks.

## 6. Audition

Run before a narration above ~1500 characters whose voice the user has not chosen, and before any paid clone is
used at length. Shorter text, no voice named: skip it, use the default voice that fits the brief, offer a change. One sentence from the real script (the one with the hardest name or number), under 200
characters, same settings as the final read. Plan for `gm.py batch`:

```json
{"label": "<label>-audition", "jobs": [
 {"id": "v1", "endpoint_id": "fal-ai/gemini-3.1-flash-tts", "input": {"prompt": "<sentence>", "language_code": "Turkish (Turkey)", "voice": "Aoede"}},
 {"id": "v2", "endpoint_id": "fal-ai/gemini-3.1-flash-tts", "input": {"prompt": "<sentence>", "language_code": "Turkish (Turkey)", "voice": "Charon"}},
 {"id": "v3", "endpoint_id": "xai/tts/v1", "input": {"text": "<sentence>", "language": "tr", "voice": "eve"}}]}
```

Two or three candidates, contrasting (gender, energy, or model), never six. It costs a few cents at most; do not
ask permission for it, do present it (template in SKILL.md). The pick is the user's. Reuse the picked input as the
`--base-input` of the full run so nothing drifts.

## 7. Cloning, design, conversion

**Consent first.** Before uploading a sample ask once: is this your own voice, or do you have the speaker's
permission to clone it? No clear yes: stop. Never clone public figures. Tell the user the upload is a public link.

Sample: 10-60 s of one speaker, clean, no music, natural pace. Prepare it locally when needed:
`audiokit.py extract <recording> --out .genmedia/tmp/sample.wav --start 5 --duration 40 --mono`. Noisy: run
`fal-ai/elevenlabs/audio-isolation` first.

| Endpoint | Input | Output | Notes |
|---|---|---|---|
| `fal-ai/minimax/voice-clone` | `audio_url`* (at least 10 s), `noise_reduction`, `need_volume_normalization`, `text` (preview, up to 1000 chars), `model` (preview model enum) | `.result.custom_voice_id`, optional preview `.result.audio.url` | ~$1.50 per clone plus preview characters as of 2026-09-19 (announce it). The voice is deleted unless a TTS call uses it within 7 days. Pass the ID as `voice_setting.voice_id` on a MiniMax speech endpoint with `language_boost`; `fal-ai/minimax/speech-2.8-hd` accepted a clone's ID on 2026-09-21 and spoke in the cloned voice, by ear a little less close to the sample than the clone's own preview (`platform.md` section 10). Nothing machine-checks the likeness: the user listens to one short line before a long read. Rejected there: `fal-ai/minimax/speech-02-hd`, the family the clone preview uses (text field `text`, up to 5000 chars; same `voice_setting`, `language_boost`, `output_format:"url"`). Set the preview `text` to a sentence in the target language; omitted, the schema default (an English demo line) is used for the preview and billed per character. |
| `fal-ai/minimax/voice-design` | `prompt`* (voice description, up to 2000 chars), `preview_text`* (1-500 chars) | `.result.custom_voice_id`, `.result.audio.url` | ~$3 per designed voice as of 2026-09-19: that is over the confirm threshold, get a yes first. |
| `fal-ai/zonos2` | `reference_audio_url`*, `text`, `language` (normalization codes `en_us`, `en_gb`, `fr_fr`, `de`, `es`, `it`, `pt_br`, `ja`, `cmn`, `ko`), `accurate_mode`, `seed` | `.result.audio.url` (WAV) | Clone and speak in one call, billed per minute. `text` has a demo default: always set it. No Turkish normalization. |
| `fal-ai/chatterbox/text-to-speech/multilingual` | `voice` = sample URL, `custom_audio_language` | `.result.audio.url` | Turkish in the user's voice, 300 characters per call. |
| `fal-ai/qwen-3-tts/clone-voice/1.7b` | `audio_url`* (up to 300 s), `reference_text` | `.result.speaker_embedding.url` | Feed to `fal-ai/qwen-3-tts/text-to-speech/1.7b` as `speaker_voice_embedding_file_url`. |
| `fal-ai/elevenlabs/voice-changer` | `audio_url`*, `voice`, `remove_background_noise` | `.result.audio.url` | Keeps the performance, swaps the timbre; billed per minute. |

Remember a cloned or designed voice in `.genmedia/voices.json` (this skill owns the file):

```json
{"fatih-tr": {"endpoint_id": "fal-ai/minimax/voice-clone", "custom_voice_id": "<id>", "created": "2026-09-19",
  "last_used": "2026-09-19", "use_with": "fal-ai/minimax/speech-2.8-hd", "consent": "own voice, confirmed in chat"}}
```

Refer to it by handle in chat, update `last_used` on every TTS call, and warn when it is older than 6 days unused.
