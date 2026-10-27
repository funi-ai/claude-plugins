---
name: demo-video
description: >-
  Product demos, store previews, App Store header/search videos and loops cut from the user's REAL screen recording: trimmed, sped, zoomed, framed, captioned, voiced with local ffmpeg. Models add only what is not the product: narration (Eleven v3, Gemini TTS for Turkish), music and UI sound.
  Use when: "make a demo video of my app", "App Store preview video", "App Store header video", "Google Play promo video", "turn this screen recording into a demo", "GIF loop for my changelog", "Product Hunt launch video", "ekran kaydımdan tanıtım videosu yap", "changelog için GIF döngüsü".
  Chain: takes recordings, device frames (`layers`) and end cards from `launch-graphics`; produces MP4, WebM, GIF, SRT/VTT and posters.
  NOT for: generated b-roll shorts (use `short-video`); explainers with generated pictures (use `video-explainer`); paid ads (use `ads`); store screenshots, link cards (use `launch-graphics`); one generated clip (use `video`); voice or music alone (use `audio`); joining finished files (use `pipelines`).
argument-hint: "[recording paths] [demo|app-store|app-store-header|app-store-search|play|product-hunt|loop] [--seconds 60] [--slug <project>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/frames.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/audiokit.py" *) Bash(command -v genmedia) Bash(genmedia models *) Bash(genmedia schema *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires python3 >= 3.8 and a local ffmpeg/ffprobe (the cut, the frames, the mix and every check are local and free). The genmedia CLI >= 0.7.0 with a fal key configured by the user is needed only for narration, music, sound, dubbing or a generated plate.
---

# Demo video

A product demo, a store preview or a feature loop built from the user's real screen recording. The interface is never regenerated: the recording is cut, sped, zoomed, framed, captioned and voiced. Apple states the same rule for previews (2.3.4: video screen captures of the app itself, narration and overlays allowed). One `cut.json` holds the recordings, the ordered scenes and the variants; `democut.py` turns it into files with local ffmpeg, and re-cutting is free.

## Step 0 — Preflight

Once per session:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" tools
```

- `kind: "ffmpeg_missing"` → no local cut is possible. Say so and offer the paid utility route in `references/routing-utility.md`, or ask the user to install ffmpeg. Never improvise with other tools.
- Keep `can.burn_captions` (libass), `can.duck` (sidechaincompress), `can.webm`. Missing ones change what you promise, never what you claim.
- Only when something will be generated (narration, music, sound, dubbing, a plate):
  ```bash
  command -v genmedia
  python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
  ```
  `blockers` not empty, CLI missing or older than 0.7.0 → `/genmedia-skills:setup`. Key missing → the user runs `genmedia setup` or exports `FAL_KEY` themselves; wait. Never read, print, request or type a key. Keep `config.announce_above_usd` and `config.confirm_above_usd` (defaults 0.50 and 2).
- Resume first: `.genmedia/projects/<slug>/demo-video/cut.json` exists → continue from it, never start a second cut for the same product.

## UX rules

1. Reply in the user's language. Narration, `say` lines and on-screen text stay in the language they ship in; model prompts are English. Paths, ids and field names stay as they are.
2. No JSON, filter graphs, request IDs or tool narration in chat. One status line per long step at most.
3. **Question budget: 2, one at a time, labelled options, only when the answer is missing:**
   - Q1 the recording, when no file was given: ask for paths and hand over the short capture list from `references/recording-tips.md`. There is no default for footage.
   - Q2 where it goes, when the request does not say: A website demo (16:9) · B App Store preview · C App Store header or search results video · D Google Play promo · E Product Hunt launch video · F a silent loop or GIF. Several may be chosen; one cut serves them all.
   Everything else is a default you state in the delivery: 60 s for a demo, 20 s for a store preview, 12 s for an App Store header or search video, 6 s for a loop; narration on for a demo, off for a loop or a header or search video; music off unless asked; captions as a sidecar file; cuts, not dissolves; no device frame unless a store or social target wants one.
4. **The cut card is a hard stop.** Show the scene list (times, what happens, what is said, lengths) and wait for a yes before anything is generated or rendered. Silence is not approval, and a yes to an older version is not a yes to this one.
5. **Narration before picture.** Generate the voice per scene, let `time` measure it, and cut the picture to it. Never time a scene by guessing how long a sentence takes (`references/narration-and-audio.md`).
6. **Look before you deliver.** Read the poster frame and a contact sheet of the finished file, and read the first frame of any GIF. A demo that validates and shows the wrong screen is still wrong.
7. **Facts and privacy come from the user.** Ratings, counts, awards, customer names and logos appear only when the user supplied them. If a frame shows real data, the fix is a new recording, not a blur; say that plainly.
8. Cost: the cut, the frames, the loops and every check are USD 0. Before any generation, estimate and apply the gate from preflight: under `announce_above_usd` → run and state it; up to `confirm_above_usd` → one line, then run; above → explicit yes. Never quote a price from memory.
9. Bounded: at most 3 repair attempts per step, something changes each time; a content-policy rejection is never resent unchanged; a job with a request ID is resumed, never resubmitted.

## Discovery guardrail

`scripts/video-surfaces.json` is a dated cache (`verified_on`, read by `democut.py specs`): a `null` is a number nobody read from the official page, never fill it from memory, and when a store rejects a file the official page wins and the row is corrected.

Before the first paid call to an endpoint in a session:

```bash
genmedia models --endpoint_id <endpoint_id> --json
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
```

`status` must be `active`; fields, enums and limits come from the schema. Not active → the next tier of that task in `references/routing-audio.md`. Never `genmedia run` with a prompt instead of an endpoint ID. New releases sit under vendor namespaces, not only `fal-ai/`.

## Routing

| Need | How | Why |
|---|---|---|
| Trim, speed, zoom, frame, join, overlay, mix, loudness, GIF, checks | `democut.py` (local ffmpeg) | exact, free, repeatable; the product's pixels never pass through a model |
| Look at a recording or a result without watching it | `democut.py analyze`, `sheet`, `grab`; `frames.py sheet` | detectors and contact sheets instead of guesses |
| Narration | `fal-ai/elevenlabs/tts/eleven-v3`; Turkish: `fal-ai/gemini-3.1-flash-tts` | default TTS; the Turkish path is schema-verified |
| Music bed, UI sounds | `elevenlabs/music/v2.5` (exact length), `fal-ai/elevenlabs/sound-effects/v2` | length control; cheap per second |
| Word-accurate caption timings | `fal-ai/elevenlabs/speech-to-text/scribe-v2` → `audiokit.py captions` | word timestamps |
| Another language for a finished file | `fal-ai/elevenlabs/dubbing` | one call per language |
| Device frame, end card, exact on-image text | `/genmedia-skills:launch-graphics` (`layers`, composed PNGs) | text is composed where it is exact, never generated |
| Background plate behind a framed device | `bytedance/seedream/v5/pro/text-to-image` | one plate per video, no lettering |
| No local ffmpeg | `fal-ai/ffmpeg-api/*` in `references/routing-utility.md` | cents per call, a fallback and not the default |

Tie-breakers and traps:

1. **The interface is never generated, restyled, reframed or "enhanced".** `video-reframe`, `video-edit` and upscalers repaint UI text: they are for generated footage, not for a recording.
2. Zoom in fractions of the source frame, read off `grab --grid` or `sheet --grid`; `hold` for detail, `push` once to lead the eye, `pull` once to reveal context (`references/editing.md`).
3. A store preview is not the demo with a shorter end: it is its own variant with its own scene subset.
4. Play and Product Hunt take a **YouTube URL**, not a file: deliver the file and say who uploads it.
5. An App Store header or search results video (iOS 27 creative asset) is its own silent, looping variant: `appstore-header-video` (3840x1646) or `appstore-search-video` (3:2), 30 or 60 fps, 5-30 s, one idea, scenes of 2 s or more, ending where it began. Apple lists no universal video; the stills are `launch-graphics` work (`references/surfaces.md` section 1a).
6. A phone recording needs a phone frame; `time` refuses a 30 % aspect mismatch.
7. Burn-in only when `can.burn_captions`; otherwise a sidecar file, or the paid subtitle route, said out loud.
8. The user named a model → use it after the live check.

## Workflow

1. **Intake.** Goal, targets, recordings, brand. Read every file the user named. Then, per recording:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" init --slug <slug> --name "<Product>" --target web-16x9
   python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" source add --slug <slug> --id app --file ./recordings/demo.mov --os desktop
   ```
   The answer carries size, fps, duration, audio, any baked-in letterboxing and the targets the aspect fits. A recording smaller than the target, or one that shows real data, gets a retake ask now, not after the edit (`references/recording-tips.md`).
2. **Look at it.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" analyze --slug <slug> --source app
   python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" sheet --slug <slug> --source app --count 12 --cols 4 --grid
   ```
   Read the sheet. `dead_spans` and `keep_spans` are candidates, never an edit: a still screen is sometimes the point. `grab --at <s> --grid` for any frame you will zoom into.
3. **Cut card.** Scenes in order: id, source in/out, speed, zoom, what the viewer sees, what the voice says, length; then the variants, what is generated, what is needed from the user, and the assumptions. Show it, **stop**, wait for a yes (`references/editing.md`).
4. **Narration, measured** (only if the demo is voiced). Price and run one batch per `references/narration-and-audio.md`, one file per scene, then let the numbers decide the picture:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price fal-ai/elevenlabs/tts/eleven-v3,elevenlabs/music/v2.5 --explain
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/demo-video/voice-plan.json
   ```
5. **Write the cut.** Edit `.genmedia/projects/<slug>/demo-video/cut.json` with the Write or Edit tool: `scenes`, `audio`, `variants`. Every field: `references/cut-json.md`. Device frames come from `launch-graphics layers` (`references/frames-and-loops.md`).
6. **Gate.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" time --slug <slug>
   ```
   Fix every error before rendering: `scene_shorter_than_voice` (lengthen the span, slow it, or cut words — never speed the voice), `duration_out_of_range` on a store target, `wrong_size`, `fps_not_allowed`, `transition_too_long`, `frame_aspect_mismatch`, `overlay_invisible`. Act on the warnings (`quick_cut`, `fast_motion`, `narration_muted` on a creative-asset video) or explain the ones you keep.
7. **Build.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" build --slug <slug>
   ```
   600000 ms Bash timeout. Scenes are cached by content: a revision re-renders only what changed (`--scene <id>`, `--force`). Then captions and loops:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" captions --slug <slug> --variant <id> --formats srt,vtt
   python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" gif --slug <slug> --variant loop-16x9 --budget-mb 3 --seconds 6
   ```
8. **Look at the result.** Read the poster frame, then a contact sheet of the finished file, then the GIF's first frame:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/frames.py" sheet genmedia-output/<slug>/demo-video/<variant>/<slug>.mp4 --count 9 --cols 3
   ```
   Check the first 3 seconds, the zoomed frames (legible?), the last frame (settled?), every frame for private data, and read the cue file letter by letter.
9. **Validate and deliver.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/democut.py" validate --slug <slug>
   ```
   Exact size, fps, duration inside the platform window, codec and profile, byte cap, audio configuration, measured loudness and true peak, and on a looping target the seam (`loop_seam`). Then the delivery message. Revisions: edit the cut, re-build, validate again.

## Delivery

```
<Product> demo: genmedia-output/<slug>/demo-video/
Master 16:9: web-16x9/<slug>.mp4 (1920x1080, <n> s) · poster web-16x9/<slug>-poster.png
App Store preview: appstore-iphone/<slug>.mp4 (886x1920, <n> s, H.264 High, AAC 256k) <only if built>
App Store header / search video: appstore-header-video/<slug>.mov (3840x1646, <n> s, <fps> fps, silent loop) · poster frame to pick in App Store Connect: <t> s <only if built>
Play promo / Product Hunt: the same master — both platforms take a YouTube URL, so upload it and paste the link <only if built>
Loops: loop-16x9/<slug>-loop.mp4 · <slug>-loop.gif (<n> MB, <w>px@<fps>) · first frame <slug>-loop-first.png <only if built>
Captions: <variant>/<slug>.srt, .vtt (<language>) <only if built> · manifest.json
Your recording, unchanged: cut, <sped up where it waited>, zoomed on <what>, <framed in a drawn device>. Nothing in the interface was regenerated.
Chosen for you: <length, scene count, narration on/off, music, captions, frames, fit — every default the user did not set>
Store notes: <one line each that applies: App Store previews are 15-30 s, up to 3 per device, screen captures only (2.3.4) · header and search videos loop muted (search: never unmuted), show on iOS 27 and iPadOS 27 or later, and their poster frame is fixed once approved · only the first 30 s of a Play promo autoplays · Product Hunt images, GIF included, stay under 3 MB and the GIF animates on hover>
Generated: <none, USD 0 | narration <n> lines on <model>, music, est. USD <x>> · Files are local; nothing was uploaded.
Next: name a scene and what to change (in/out, speed, zoom, words); re-cutting is free.
```

Translate it; keep paths, sizes and on-screen text unchanged.

## Errors

| Signal | Do |
|---|---|
| `kind: "ffmpeg_missing"` | No local ffmpeg. Say the cut cannot be made here; offer the fal `ffmpeg-api` route (`references/routing-utility.md`) or ask the user to install it. |
| `source_changed` | The recording moved or changed. `source add --replace`, then re-check every in/out: the old timings no longer mean anything. |
| `check_failed` from `time` | Every entry names a scene and a number. Fix the cut; nothing renders while an error stands. |
| `scene_shorter_than_voice` | Lengthen the span, lower `speed`, or cut words. Never speed the narration up to fit. |
| `duration_out_of_range` | An official window was missed (App Store previews 15-30 s, header and search videos 5-30 s). Drop or shorten scenes for that variant only. |
| `wrong_size`, `fps_not_allowed`, `fps_too_high` | The variant's size or fps breaks its row. Drop the override or pick a value the row takes (`specs`). |
| `loop_seam` from `validate` | The loop jumps at its restart. End on the opening state or hold the same region, build, validate again. |
| `frame_aspect_mismatch`, `frame_invalid`, `layers_unsupported` | Wrong device frame or the wrong file. Ask `launch-graphics` for matching `layers` from an upright framed slide. |
| `overlay_invisible`, `not_found` on an overlay | The PNG has no visible alpha, or the path is wrong. Re-render it where the text is exact. |
| `budget_unreachable`, `gif_target` | Shorten the loop or drop the zoom; build a video variant first and export the GIF from it. |
| `check_failed` from `validate` | A store rejects on exactly these numbers. Fix the variant, build again, validate again. |
| `tool_failed` | ffmpeg refused; the message carries its last lines → `references/troubleshooting-demo-video.md`. |
| `gm.py` `status: "pending"` / `kind: "content_policy"` / `kind: "auth"` | Same command again, never resubmit / rewrite and say what changed / stop, the user fixes key or balance. |

Looks wrong rather than failed: `references/troubleshooting-demo-video.md`. Platform error types: `references/platform.md`.

## This skill does NOT

- Regenerate, restyle, reframe, translate or "enhance" the product's interface, or invent screens, data, ratings, reviews or user counts.
- Deliver a frame with someone's real data in it, or blur one instead of asking for a clean recording.
- Upload anything: App Store Connect, Play Console, YouTube, Product Hunt and websites stay the user's job, and no credential is ever handled.
- Make store screenshots, App Store header or search stills, link cards or Product Hunt gallery stills (`/genmedia-skills:launch-graphics`), generated b-roll shorts (`/genmedia-skills:short-video`), narrated explainers with generated pictures (`/genmedia-skills:video-explainer`), paid ad placements (`/genmedia-skills:ads`), single generated clips (`/genmedia-skills:video`), voice or music on their own (`/genmedia-skills:audio`), or joining files that already exist (`/genmedia-skills:pipelines`).

## Common mistakes

- Cutting before looking: trusting `dead_spans` without reading a sheet, and removing the one still frame that was the point.
- Writing the script, cutting the picture, then generating the voice. The measured voice comes first.
- A demo that opens on a splash screen, a login or an empty state. The first 3 seconds show the product doing its job.
- Zooming deeper than the recording allows, then delivering soft UI text instead of asking for a 2x recording.
- A dissolve between every scene. Cuts are the default; a dissolve means "elsewhere, later".
- Delivering a 45 s file to an App Store window of 15-30 s and hoping. `time` is not optional.
- A header or search video that needs its narration, cuts every second, or jumps at the loop point: it autoplays muted, on repeat.
- One long variant re-cut by hand for each platform instead of scene subsets in `variants`.
- A GIF whose first frame is a fade-in: on Product Hunt that frame is the thumbnail.
- Narration that describes the clicks instead of the outcome.
- Quoting a platform number from memory instead of `specs`, or leaving a corrected number only in the chat.

## Reference index

- `references/editing.md` — read at steps 2 and 3: demo shapes and lengths, what the detectors do and do not know, building the edit list, zoom grammar, transitions, first and last frame.
- `references/cut-json.md` — read when editing the cut or when an error names a field: every field of sources, audio, scenes and variants, worked fragments, what `build` does in which order.
- `references/surfaces.md` — read when choosing targets or answering a size, length or format question: the dated rows behind `video-surfaces.json` and what each platform actually accepts.
- `references/store-policy.md` — read before planning a store preview or a header or search video: App Review 2.3.3, 2.3.4, 2.3.7, 2.3.10, Apple's creative-asset content rules, Play's YouTube rules, Product Hunt, privacy and claims.
- `references/narration-and-audio.md` — read at steps 4 and 7: narration first, voice routing, writing lines, music, ducking, loudness, other languages.
- `references/captions-and-locales.md` — read for captions, word-accurate timings, burn-in routes and localisation.
- `references/frames-and-loops.md` — read when a recording plays inside a drawn device, or when the deliverable is a loop, a GIF or an end card.
- `references/recording-tips.md` — read when there is no usable recording: what cannot be fixed later, capture settings, clean phone recordings, performing the flow.
- `references/troubleshooting-demo-video.md` — read when a result looks wrong, an ffmpeg message is unclear, or an error kind is not in the table above.
- `references/routing-audio.md` — read before generating narration, music, sound or a dub; dated prices and limits.
- `references/routing-image.md` — read before generating a plate or a card image.
- `references/routing-utility.md` — read when there is no local ffmpeg, or for the paid subtitle and mux routes.
- `references/cli-contract.md` — read when a `gm.py` call fails or is pending: `batch`, `wait`, ledger, raw-CLI fallback.
- `references/platform.md` — read when estimating cost or reacting to a platform error type.
- `scripts/democut.py` — local, free, no network: `tools`, `specs`, `init`, `source add`, `analyze`, `sheet`, `grab`, `time`, `build`, `captions`, `gif`, `validate`; one compact JSON object per call, exit 0 ok, 1 failed, 2 usage.
- `scripts/video-surfaces.json` — dated target sizes and size ranges, duration windows, frame-rate rules, loop and sound flags, codec profiles, byte caps and source URLs read by `democut.py`.
- `scripts/gm.py` — shared helper for every paid call (`preflight`, `price`, `run`, `batch`, `wait`, `ledger`).
- `scripts/frames.py` — contact sheets, probes and exact frames of any video file.
- `scripts/audiokit.py` — local audio utilities: `probe`, `extract`, `loudnorm`, `concat`, `chunk`, and `captions` from word timings.
