# Narration, music and the mix

Read at Workflow step 4 (narration before picture) and step 7 (the mix). Routing tables: `references/routing-audio.md`; mechanics of paid calls: `references/cli-contract.md`.

## 1. Narration first, always

The defect this prevents: a script is written, the picture is cut to a guessed length, the voice comes back 40 % longer and the cut no longer fits the store's window. So:

1. Write the script per scene as `say` lines, in the language it will be spoken.
2. Generate the voice **per scene**, one file each (`audio/vo-<scene>.mp3`), not one long take. Per-scene files let `time` prove that every scene is long enough, let you re-do one line for $0.01, and put the words exactly where the picture is.
3. Register them as `voice` in the scenes and run `democut.py time`. It measures the files and fails with `scene_shorter_than_voice` when a scene cannot hold its line.
4. Only then cut the picture to the voice: lengthen the span, lower the `speed`, or cut words.

Rates that hold in practice: English about 2.6-3.0 words per second of finished narration, Turkish about 1.7-1.9 (longer words, fewer of them; two Gemini voices measured in `platform.md` section 10). `time` warns above 3.2 words per second on a `say` line, which is the point where a listener stops following.

## 2. Voice routing

| Need | Endpoint | Note |
|---|---|---|
| English and general | `fal-ai/elevenlabs/tts/eleven-v3` | the default; text ≤ 5000 characters, about $0.10 per 1000 characters |
| Turkish | `fal-ai/gemini-3.1-flash-tts` | its `language_code` enum lists `Turkish (Turkey)`; style direction; about $0.05 per 1000 characters |
| Cheapest multilingual | `xai/tts/v1` | a language enum, lower quality |
| The user's own voice | `/genmedia-skills:audio` voice clone | consent is the user's to give and to state |

Confirm the endpoint and its fields live before the first paid call of the session (`genmedia models --endpoint_id <id> --json`, `genmedia schema <id> --json`); the full dated table is in `references/routing-audio.md`.

Write the narration text into a file with the Write tool and pass it through the helper rather than quoting long text on a command line:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run fal-ai/elevenlabs/tts/eleven-v3 --input .genmedia/projects/<slug>/demo-video/vo-compose.json --download audio/
```

Several lines at once belong in one plan:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/demo-video/voice-plan.json
```

## 3. Writing lines for a demo

- One line per scene, one idea per line. The picture shows the action; the voice says why it matters.
- Never narrate the obvious ("here I click the button"). Say the outcome ("and it is filed before you leave the thread").
- Open on the problem or the result, never on "Hi, welcome to Acme".
- Numbers and claims come from the user. No "trusted by thousands".
- Leave 0.2-0.3 s of `lead` before each line so the cut lands before the voice starts, and 0.2-0.3 s of `tail` so the next cut does not clip the last word.
- The last line ends before the end card: the card is read, not spoken over.

## 4. Music

- One bed for the whole cut, generated to length: `elevenlabs/music/v2.5` takes `music_length_ms` (about $0.60 per started minute), `minimax/music-3` is the value tier. Ask for an instrumental ("force_instrumental") — a demo with lyrics fights the narration.
- Set it in `audio.music` with `gain_db` around −20 under narration, −14 to −16 when there is no voice, plus `fade_in` and `fade_out`.
- `duck_db` turns on sidechain ducking so the bed steps back under the words. Without the `sidechaincompress` filter (`tools` says), keep the bed at a fixed −22.
- No music at all is a legitimate choice for a store preview: the product's own sounds plus narration often read as more serious.

## 5. The recording's own sound

`audio.keep_source` takes the sound recorded with the screen: typing, clicks, the app's own audio. It is off by default because most screen recordings carry room tone, a fan or a notification. Turn it on only after listening; `analyze` reports the recording's integrated loudness, and `audiokit.py extract` pulls the track out if you want to hear it on its own.

Per scene, `"mute": true` drops the source audio for that scene alone (a notification sound in the middle of a flow).

## 6. UI sound effects

`fal-ai/elevenlabs/sound-effects/v2` (about $0.002/s, 0.5-22 s) makes the small sounds a silent recording lacks: a soft click on a send, a rise on a result, a whoosh on an end card. Two or three in a 60 s demo, never one per action. Place them as their own short `voice` files on the scene where they belong, or mix them into the bed before the build.

## 7. Loudness

`build` normalises the finished mix to `audio.lufs` / `audio.true_peak` (EBU R128, defaults −16 LUFS and −1.5 dBTP) and `validate` measures the delivered file back with `ebur128`. A warning there means the mix, not the normaliser, is wrong: a bed far too loud, a voice recorded at a different level per scene, or a scene where everything is silent.

Two rules that matter more than the numbers: nothing may clip, and the narration must stay legible when the bed is at its loudest.

## 8. Other locales

- A second language is a second set of `voice` files and a second variant of the cue file; the picture stays the same unless the UI itself is localised (then it is a second recording).
- `fal-ai/elevenlabs/dubbing` dubs a finished file into a target language in one call (about $0.60 per started minute) and returns a video: use it when the user wants five languages of the same demo and does not need the cut changed. It re-encodes, so run `validate` again afterwards.
- On-screen text in another language is a new overlay PNG, never a translation burned by a model over the old one.
