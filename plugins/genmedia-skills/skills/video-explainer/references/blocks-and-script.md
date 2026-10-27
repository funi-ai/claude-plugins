# Blocks and script

How to turn a topic, document or draft into blocks that `explainer.py init` accepts without flags, and how to describe one picture per block. `explainer.py` abbreviates `python3 "${CLAUDE_SKILL_DIR}/scripts/explainer.py"`. Costs and tiers: `tiers-and-costs.md`. Styles: `style-library.md`.

## 1. The block

A block is the unit of planning, payment and repair: **one narration chunk + one visual**, 10 s by default.

| Length asked | Blocks at 10 s | Spoken words, English | Spoken words, Turkish |
|---|---|---|---|
| 30 s | 3 | 60-68 | 41-46 |
| 1 min | 6 | 120-135 | 82-92 |
| 2 min | 12 | 240-270 | 163-184 |
| 3 min | 18 | 360-405 | 245-275 |
| 5 min | 30 | 600-675 | 408-459 |

- Inside a block: 0.4 s lead-in, the sentence(s), 0.6 s tail (`--lead-s`, `--tail-s`). The speech budget of a 10 s block is therefore 9.0 s.
- `--block-s` may be 4 to 30. Shorter blocks (6-8 s) feel faster and cost more pictures; longer blocks (12-15 s) suit calm, dense lessons. Change it only for a reason the user gave; 10 s matches what image-to-video models render well in one take.
- The plan is a target, not a grid: after the voice is measured, each block's picture length `visual_s` becomes lead + measured audio + tail, rounded up to a whole second (`--fit audio`, default). A total of 57 s or 63 s for a "one minute" video is normal. Use `--fit grid` only when the user needs an exact running time: every block is then exactly `block_s` and an overrun must be rewritten.

## 2. Words per second (labelled heuristics)

`init` sizes blocks with these rates. They are planning heuristics for a clear, unhurried explainer voice, **not measurements**; TTS voices differ by 10-20 percent. `set-audio` prints `measured_rate` after the first narration batch: use that number (`--wps`) for every later rewrite in the project.

| Language | Rate | 9.0 s of speech holds about | Note |
|---|---|---|---|
| English (`en`) | 2.5 words/s | 22 words | |
| Turkish (`tr`) | 1.7 words/s | 15 words | agglutinative: fewer, longer words; count suffix-heavy words as "long". Measured 2026-09-20 on `fal-ai/gemini-3.1-flash-tts`: Charon, calm read, 1.9 words/s over a 3:45 narration and 1.4 to 1.85 on single 10 s blocks; Aoede, warm read, 1.78 on a 15 s short. On 2026-09-21 Charon with the `voice.json` of section 6 read 1.57 and the 10 percent headroom absorbed it. The earlier 2.0 cost four re-voicings |
| German (`de`) | 2.1 words/s | 19 words | compounds |
| Dutch (`nl`) | 2.4 | 21 | |
| Spanish (`es`), French (`fr`) | 2.6 | 23 | |
| Italian (`it`), Portuguese (`pt`) | 2.5 | 22 | |
| Russian (`ru`), Polish (`pl`), Arabic (`ar`) | 2.0 | 18 | |
| Hindi (`hi`) 2.3, Indonesian (`id`) 2.2 | | 20 | |
| Chinese (`zh`) | 4.0 characters/s | 36 characters | counted in characters, not words |
| Japanese (`ja`) | 6.0 characters/s | 54 characters | |
| Korean (`ko`) | 4.5 characters/s | 40 characters | |
| anything else | 2.3 words/s | 20 words | say that the rate is a default guess |

Numbers, years, units and abbreviations are spoken longer than they look: "2024" is three or four spoken words, "%15" two or three. Spell them out in the script the way they should be said (section 3); then the count is honest.

Flags from `init` and `edit`: `long` = estimated speech over the budget by more than 5 percent (must be fixed before CP1, `approve --stage outline` refuses it); `short` = under half the budget (merge with a neighbour, or accept a short block: with `--fit audio` it simply becomes a shorter block). After measuring: `over` = the block grew past `block_s`; `dead_air` = the audio fills less than half the block.

**Requested length.** `init --length-s` records what the user asked for: `30-40`, or `15` for a hard maximum. Every block rounds up to a whole second, so the total is the sum of those. Before the voice exists, estimated blocks count 10 percent longer (5 percent with a measured `--wps`): `length.status: "over"` stops the outline approval and `length.cut` names the fewest blocks to shorten and by how many words. After measuring, the real total must fit the maximum before CP3 and before keyframes are planned. A total under the minimum is reported, not blocked: add a sentence or say the real length at CP3.

## 3. Writing for the ear

1. **One idea per block.** If the block needs "and also", it is two blocks.
2. **Arc.** Block 1 is the hook: a question, a surprising fact the source supports, or the viewer's problem. Never "in this video we will". Middle blocks build in the order a person would need them. The last block pays off the hook and ends on a full stop, not on a list. A call to action, if the user wants one, is one sentence in the last block.
3. **Sentences a voice can carry.** 8 to 16 words each, at most two per block in Turkish, two or three in English. Subject and verb early. No brackets, no slashes, no "e.g.", no footnotes, no emoji, no markdown. One breath per sentence.
4. **Say it the way it is spoken.** Write numbers, years, currencies, percentages, units and symbols as words in the narration language ("yüzde on beş", "two point five million"). Expand abbreviations on first use, or always when the letters are not pronounced as a word. Foreign names: keep the spelling; if the audition mispronounces one, respell it phonetically in the narration and keep the correct spelling for the SRT (`troubleshooting-explainer.md`).
5. **Concrete before abstract.** An example the viewer can picture, then the rule. The picture of the block is that example.
6. **No stage directions in the text.** No "[pause]", "(excited)", timecodes or speaker labels: most TTS models read them aloud or change voice. Delivery belongs in the voice settings, identical for every block (section 6). Exception: tags the chosen model documents, used sparingly and auditioned first.
7. **Transitions are spoken, not visual.** "That is why", "Sonra" carry the viewer across the cut; the pictures change hard at block borders.
8. **Turkish specifics.** Verb-final sentences grow long fast: split at "ve", "ama", "çünkü". Avoid chains of "-ması için -dığında" nominalisations in one sentence. Question hooks work well ("Hiç düşündünüz mü, ..."). Keep dotted and dotless i exact (İ, ı): they change the word and the pronunciation.
9. **Sources.** From a document: every claim traces to a page; do not add facts the document lacks without saying so. From a topic: research first, list the sources in the outline card, leave out what you could not confirm. Health, law and money topics get a plain "this is general information" sentence only if the user wants it; never advice.

Read every block once at speaking pace before `init`. If you run out of breath, so will the voice.

## 4. From text to `init`

Write the script with the Write tool to `.genmedia/projects/<slug>/script.txt`: **one paragraph per block, blank line between blocks**. Optional labels (`Block 3:`, `Blok 3:`, `Sahne 3)`) are stripped.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/explainer.py" init --slug <slug> --script .genmedia/projects/<slug>/script.txt --lang tr --minutes 2 --tier hybrid --title "<title>"
```

- `--split auto` (default): two or more paragraphs → your blocks are kept as written. A single paragraph (a draft the user pasted) → sentences are packed into blocks up to the word budget; read the result, it splits on punctuation only and knows nothing about ideas.
- `--minutes` (or `--blocks`) is the target; a different block count is reported, not forced. Fix the script, not the target, unless the user agrees to a new length.
- `init` refuses to overwrite a project. One sentence changed → `edit --slug <slug> --block <n> --narration-file <file>`: it resets that block's audio and approvals only. Inserting or deleting a block → `init --force` before any narration was generated; afterwards prefer rewriting neighbours, because a re-init makes every block new (narration jobs whose text and settings did not change are still resumed for free by their ids, but block numbers shift).
- A user's finished script is theirs: split it, flag what is `long`, propose cuts, and change wording only with their agreement.

## 5. One picture per block: scene and motion lines

`visuals.json` is a list the helper merges into the ledger; partial lists are fine.

```json
[
  {"index": 1, "scene": "A glass of water on a kitchen table, a faint dinosaur silhouette reflected on the glass", "motion": "The water ripples gently and the silhouette slowly fades in", "animate": true},
  {"index": 2, "scene": "A low sun above a calm sea, thin wavy lines of vapor rising from the surface", "move": "in"},
  {"index": 3, "scene": "One grey cloud above green hills, rain falling on the left side, snow on the right", "move": "out"}
]
```

**Scene rules** (English, 12-35 words, present tense):

1. Describe what is in the frame, not what it means: subjects, their arrangement, one background. "The water cycle" is not a scene; "a cloud raining onto a mountain lake" is.
2. One focal subject, at most three elements. Explainer frames are read in under two seconds while someone is talking.
3. No style words. Technique, palette, line quality and lighting live in the STYLE string, which the helper appends verbatim to every prompt. A scene that says "watercolor" or "3D" fights it.
4. No words in the picture: no labels, titles, numbers, signs, UI text, speech bubbles. The helper adds a negative for lettering; your scene must not ask for any. A block that truly needs a labelled diagram: put the exact words in double quotes in its scene (in the narration language, at most a handful of short labels), plan only that block on the typography model with `plan --stage keyframes --blocks <n> --endpoint openai/gpt-image-2.5/flare/edit --allow-text` (SKILL.md, Role defaults), compare every rendered word with the scene, and do not animate it.
5. Composition words help: "centered", "seen from the side", "wide view", "close-up of". Leave the lower fifth calm if the user plans burned-in captions.
6. Continuity is stated, not assumed: a recurring object or mascot is described with the same words every time ("the small orange robot with one antenna"); with a mascot sheet, pass its URLs once via `style --ref-url` and name the character identically in each scene.
7. Real people, brands and logos: not without the user's confirmation that they own them or have consent. Prefer generic stand-ins ("a scientist", "a delivery van").

**Motion rules** (only for blocks with `"animate": true`; English, one sentence):

- One continuous, slow action that illustrates the sentence: something fills, grows, flows, rotates, appears, moves from A to B. No cuts, no camera acrobatics, no new objects arriving from nowhere.
- Name what moves and what stays: "the arrows travel clockwise around the circle; the background stays still".
- Nobody speaks or mouths words in the clip: the narration is the only voice.
- No motion line → the helper uses a gentle parallax default. Good for mood, weak for explanation: if you cannot name a meaningful motion, the block should be a still.

**Which blocks to animate (hybrid):** the hook, the one block where a process is the point, and the payoff. Two or three per minute. Definitions, lists, quotes and transitions stay stills; their pan or zoom (`move`: `in`, `out`, `left`, `right`; alternated by default) is enough life.

## 6. Voice settings that stay equal in every block (`voice.json`)

One JSON object, written once, passed as `--base-input` to the audition and to every narration plan. The helper adds the text field per block. Fields verified in the live schemas on 2026-09-19; re-check with `genmedia schema <endpoint_id> --format openapi --json`.

| Endpoint | Text field (set by the helper) | Put into `voice.json` |
|---|---|---|
| `fal-ai/gemini-3.1-flash-tts` | `prompt` | `language_code` (enum, e.g. `"Turkish (Turkey)"`, `"English (US)"`, `"German (Germany)"`), `voice` (30 names; default `Kore`), `style_instructions` (one sentence: "Warm, clear, unhurried explainer narrator; even pace; no theatrical emphasis"), `output_format` `"mp3"`, optionally `temperature` (lower = steadier across blocks) |
| `fal-ai/elevenlabs/tts/eleven-v3` | `text` (<= 5000 chars) | `voice` (free string: take names from the `examples` of the live schema, on 2026-09-19 `Aria`, `Roger`, `Sarah`, `George`, `Charlotte`, `Brian` and others; default `Rachel`), `stability` 0-1 (0.6-0.8 keeps blocks alike), `language_code` (ISO 639-1 free string: it cannot prove a language is supported, so audition first), `apply_text_normalization` |
| `xai/tts/v1` | `text` (<= 15000 chars) | `language` (enum, includes `tr`, `en`, `de`, `fr`, `es-ES`...), `voice` (28 names; default `eve`) |
| other TTS | pass `--text-field <name>` from its schema | whatever its schema requires; `fal-ai/minimax/speech-2.8-hd` takes `output_format: "url"` (send it; the `hex` default still returned a file on 2026-09-21) and `language_boost: "Turkish"` |

```json
{"language_code": "Turkish (Turkey)", "voice": "Charon", "style_instructions": "Warm, clear, unhurried explainer narrator; even pace; no theatrical emphasis", "output_format": "mp3"}
```

- **Audition before the long narration.** `plan --stage audition --voices <3 names>` speaks the first sentences of block 1 (or `--text-file`) in each voice for well under a cent each. You cannot hear: the user picks, and `approve --stage voice --voice <name>` records the pick; narration is not planned before it, nor with another `voice` in `voice.json`. Offer contrast (one lower, one brighter, one neutral voice); voice names carry no gender or age guarantee, so describe them only with the words of the model's schema description.
- **Language routing.** English or no strong reason otherwise → ElevenLabs v3. Turkish, or any language that appears in Gemini's `language_code` enum → Gemini 3.1 Flash TTS (schema-verified support, cheaper, style instruction). Tight budget or very long scripts → xAI TTS when its `language` enum lists the language. A language in no enum → audition on ElevenLabs v3 with `language_code` set and let the user judge; say that support is not verified.
- Never change `voice`, `style_instructions`, `stability` or `temperature` between blocks of one video. A redo of one block uses the same `voice.json`.
- A real person's voice (clone) is out of scope here: `/genmedia-skills:audio`, with consent.
