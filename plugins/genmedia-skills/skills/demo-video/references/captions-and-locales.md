# Captions, cue files and other languages

Read when a video needs captions, a second language, or when someone asks for burned-in subtitles.

## 1. The default is a sidecar file

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" captions --slug <slug> --variant <id> --formats srt,vtt
```

Cues come from the timeline and the scenes' `say` lines: each line is split to 42 characters and 2 lines, spread across its scene, and clamped so two cues never overlap across a dissolve. Sidecar files win because the platform draws them (YouTube, a web player, a documentation site), the viewer can turn them off, and they stay editable after the video is rendered.

Deliver `.srt` for YouTube and most players, `.vtt` for `<track>` in HTML, `.txt` when someone wants the script.

## 2. Word-accurate captions

Cue times from the timeline are accurate to the scene, not to the word. When the narration must be highlighted word by word (a social cut, a caption-heavy style), take the timings from the audio instead:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run fal-ai/elevenlabs/speech-to-text/scribe-v2 --input .genmedia/projects/<slug>/demo-video/stt.json
python3 "${CLAUDE_SKILL_DIR}/scripts/audiokit.py" captions --input .genmedia/runs/<job>.json --out-base genmedia-output/<slug>/demo-video/<variant>/<slug>-words
```

Scribe v2 costs about $0.008 per minute. Feed it the narration track as an audio file (mp3, m4a or wav), not the finished mix with music and never an mp4 with a picture: that ends `COMPLETED` with a 422 result (2026-09-21). Add each scene's start offset when the words came from per-scene files.

## 3. Burned-in captions

Burn-in is a last resort: it cannot be turned off, it re-encodes the picture, and a typo means rendering again.

- Local burn-in needs libass in the ffmpeg build. `democut.py tools` reports it as `can.burn_captions`; `captions --burn` refuses honestly when it is missing rather than pretending.
- Without libass there are two honest routes: the paid `fal-ai/workflow-utilities/auto-subtitle` (about $0.03/min, word-highlight style) or `veed/subtitles` (takes `srt_content`, lists `tr-TR`, about $0.10/min with a one-minute minimum) — both in `references/routing-utility.md`; or PNG overlays composed where the text is already exact (`/genmedia-skills:launch-graphics`) and placed as scene `overlays`.
- Never burn captions into an App Store preview you also want to reuse elsewhere; ship the clean master plus the cue file.

## 4. Another language

Three levels, cheapest first:

1. **Cue file only.** New `say` lines translated per locale, `captions` run again with the translated cut. The picture and the voice do not change. Cost: $0.
2. **New narration.** A second set of `voice` files in the target language, a second variant, the same scenes. `time` re-measures: a Turkish line is usually longer than its English original, so a scene that just fit will fail — lengthen it or cut words rather than speeding up the voice.
3. **Dubbing.** `fal-ai/elevenlabs/dubbing` takes the finished file and a `target_lang` and returns a dubbed video (about $0.60 per started minute). Fast, keeps the picture, and the timing is theirs, not yours. Run `validate` on the result: it comes back re-encoded.

The localised UI is a different matter. If the product's interface is translated, the demo in that language needs **its own recording**; translating the interface in post would mean repainting the product, which this skill never does.

## 5. Writing captions people can read

- 42 characters per line, at most 2 lines, at least 0.8 s on screen, 1 s per 12-14 characters as a sanity check.
- Break lines at clauses, not at the width limit: "Every message, / already sorted" reads; "Every message, already / sorted" does not.
- Keep the product's own spelling: capitalisation, diacritics (ı İ ş ğ ü ö ç), product names. Read the file back letter by letter before delivering.
- Do not caption what is already written on the screen; caption the voice.

## 6. What goes in the delivery

Name the cue files next to the video, say which language each one is, and say plainly whether captions are burned in or not. If the user asked for burn-in and the build could not do it, say that in one line and name the route that would (paid, or PNG overlays), instead of quietly delivering a sidecar.
