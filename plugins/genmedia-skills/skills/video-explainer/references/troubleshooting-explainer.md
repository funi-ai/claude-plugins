# Troubleshooting: explainer videos

Results that are wrong rather than failed, helper refusals, resume oddities, drifted lengths and surprising costs. Failed jobs and platform error types: SKILL.md Errors and `platform.md` section 4. Bounded repair everywhere: at most 3 attempts per block and stage, something changes each time, then stop and tell the user.

## 0. Inputs

| Situation | Do |
|---|---|
| The source is a PDF, slide deck export or long document | Read it with the Read tool (PDFs by page range). Outline from its headings; every claim in the script traces to a page. Do not upload the document anywhere: only generated prompts leave the machine. |
| The user supplies images (diagrams, product shots, a mascot) | Read each one first. HEIC, AVIF, TIFF or CMYK → convert before upload: `sips -s format png in.heic --out out.png` (macOS), or `ffmpeg -hide_banner -loglevel error -i in.avif out.png`, or `magick in.tiff -colorspace sRGB out.png`. Use as a block's still with `attach --kind keyframe`, or as style donors (`style-library.md`, Variants). |
| The user supplies their own narration recordings | One file per block: `attach --kind audio`, then `set-audio --block <n> --duration <s>` (measure with `audiokit.py probe`). One long recording: out of scope for block timing; cut it per block first with `audiokit.py extract --start --duration`. |
| The material is private | Say once that uploads and results sit on public, unguessable URLs that may expire; the script text itself is sent to the TTS model. |
| The topic needs facts you do not have | Research, list sources in the outline card, leave out what you cannot confirm. Never fill a gap with a plausible number. |

## 1. The helper refuses

| Message (`kind`) | Meaning | Do |
|---|---|---|
| `gate`: `outline not approved` | CP1 is open for the listed blocks, or the STYLE string changed after CP1 | show the (changed) outline, get the yes, `approve --stage outline [--blocks n]` |
| `gate`: `keyframes are gated` ... `audio not measured (audio-before-video barrier)` | a block has no measured narration | finish the narration batch, `set-audio`; never plan visuals against estimated lengths |
| `gate`: ... `narration not approved (CP3)` / `keyframe not approved (CP4)` | the user has not approved that block's take or still (a redo voids the old approval) | checkpoint message for those blocks only, then `approve --stage ... --blocks n` |
| `gate`: `style key not approved or has no URL (CP2)` | no key image recorded, or it changed | `style --key-job <id>` (or `--key-path` + `--key-url`), CP2, `approve --stage style` |
| `gate`: `narration is gated` ... `voice not approved (CP2)` | nobody picked the voice yet | audition, the user listens, `approve --stage voice --voice <name>`; a voice the user named: approve it with `--note` |
| `gate`: `narration is gated` ... `not the voice approved at CP2` | `voice.json` lacks the picked voice or holds another one | put the approved name into `voice.json` (a family that names the field differently: `--voice-field`); a new pick is a new `approve --stage voice` after the user said so |
| `gate`: `the tier is animatic` | clips were planned on an animatic project | name the blocks (`--blocks`) after the user agreed to pay for them; a tier the user changed for the whole video is recorded with `approve --stage outline --tier <tier>` |
| `not_ready` with `problems` | an input of the stage is missing: job not completed, file gone, no URL | finish the batch; re-download is not possible from the helper, so for a lost file re-upload your local copy or re-roll; `attach --url` for supplied files |
| `not_ready`: `cannot approve ...` `flagged long` | a block is over the speech budget | `edit` it shorter; the outline cannot be approved with `long` blocks |
| `exists` on `init` | the project already has a ledger | `edit`, `visuals`, `style`; `--force` only before anything was generated or when the user wants a new video |
| `no_project` | wrong slug or wrong directory | run every command from the project root (the folder that holds `.genmedia/`); slugs are case-sensitive on Linux |
| `bad_input` on `set-audio` | the piped probe or batch output was a failure object | read its `upstream`; usual cause: no files matched the glob, or ffprobe is missing (use `plan --stage probe`) |
| `ffmpeg_failed` | ffmpeg's last error line is in `message` | unreadable input (re-download, re-encode), disk full, or an odd `--size`; rerun `render --blocks <n> --force` |
| `usage`: `unknown TTS endpoint` / `unknown clip endpoint` | the endpoint has no built-in preset | read its schema, pass `--text-field`, or `--image-field` and `--duration-type` (and `--min-s`, `--max-s`, plus required fields in `--base-input`) |

Never get around a gate by writing a plan by hand: the gates are the user's approvals and the audio barrier, not bureaucracy.

## 2. Narration

| Symptom (reported by the user: you cannot hear) | Likely cause | Fix |
|---|---|---|
| A term, name or abbreviation is mispronounced | the model guesses from spelling | respell it phonetically in that block (`edit`), keep the correct spelling for the SRT (fix the cue with the Edit tool). Recurring jargon: `fal-ai/minimax/speech-2.8-hd` has a `pronunciation_dict` (check its schema); switching voice model mid-video is a last resort and needs the user's yes |
| Numbers, dates or symbols are read wrongly | digits left in the script | write them as words in the narration language |
| Wrong language, or a foreign accent | language field missing, or free-string language on a model that does not support it | set the enum value (`language_code: "Turkish (Turkey)"` on Gemini TTS, `language: "tr"` on xAI); if the language is in no enum, audition other models and let the user judge |
| The narrator sounds different from block to block | voice settings changed between plans, high randomness | one `voice.json` for all blocks; lower Gemini `temperature` or raise ElevenLabs `stability`; re-roll only the blocks that stand out |
| Too fast or too slow overall | model default pace | Gemini: say it in `style_instructions` ("slow, measured pace"); numeric speed control exists on MiniMax Speech (`voice_setting`), not on ElevenLabs v3 or Gemini. Re-measure after any change. Never time-stretch takes |
| One block is rushed | too many words for its picture | shorten the text; do not ask the voice to hurry |
| Stage directions are spoken aloud ("pause", "excited") | tags or brackets in the text | remove them; delivery lives in the settings |
| Long silence at the end of a take (block flagged `over` although the sentence is short) | the model padded the file | trim: `audiokit.py extract <take> --out <trimmed> --duration <speech seconds>`, `attach --kind audio`, `set-audio` |
| Loudness jumps between blocks | per-take level differences | `audiokit.py loudnorm` on the outliers (`assembly-explainer.md` section 2); the final mix is normalised as a whole anyway |
| Clicks at block borders | a take starts or ends mid-waveform | re-roll the take, or add a 10 ms fade in and out with local ffmpeg (`afade`), then `attach --kind audio` the result and `set-audio` its duration |

## 3. Pictures

| Symptom | Likely cause | Fix |
|---|---|---|
| Keyframes look like different illustrators | scenes contain style words; key image too weak or too busy | remove style words from scenes; re-roll the key image as a clean plate (`style-library.md`); after a new key: CP2 again, then re-plan keyframes (new ids are chosen automatically) |
| Content of the key image shows up in blocks (the same cup everywhere) | the plate has a dominant object | a plate with 3-4 small, unrelated objects; the helper already tells the model to take style only |
| Letters, numerals or pseudo-text in a keyframe | the scene implies signage, charts or UI | describe shapes instead ("three unlabeled bars"); add "no numerals anywhere" to the scene; re-roll. Needed text → typography still, not animated |
| The mascot changes shape or colour | no reference sheet, or different wording per scene | sheet via `/genmedia-skills:character` + `style --ref-url`; identical character description in every scene |
| A chart's proportions contradict the narration | the model invents ratios | state the ratio in the scene; verify at CP4; for exact charts let the user supply the graphic and `attach` it |
| Clip loses the style halfway, morphs or adds objects | motion line too ambitious, or prompt expansion rewrote it | one slow action; keep `enable_prompt_expansion: false` (Wan) and `prompt_expansion_mode: "disabled"` (H3); re-roll with a simpler motion; after 2 re-rolls make the block a still |
| Clip contains a cut or a camera move you did not ask for | the model's habit | the helper already asks for one continuous shot; add "camera stays fixed" to the motion line |
| A character in a clip mouths words | the model animates speech | "mouth closed, not speaking" in the motion line; faceless scenes avoid it entirely |
| Black bars around a clip in the final | the clip's aspect differs from the project's (the keyframe was the wrong shape) | keyframes must be generated at the project aspect (the presets do it; custom endpoints need `--size-field` or a size in `--base-input`); re-roll that keyframe and clip |
| The still's pan shows a blurry or cropped edge | source image smaller than the output | generate keyframes at the preset size; for supplied small images use `--size 1280x720` or upscale them first via `/genmedia-skills:image` |
| Photoreal people look uncanny in motion | documentary style with faces | prefer hands, objects, places; or keep those blocks as stills |

Re-roll etiquette: change the scene or motion text (the helper then picks a new id by itself) or pass `--reroll` for the same text; approve only the new take; old files stay on disk and in the manifest as superseded, which is fine.

## 4. Length and timing

| Symptom | Cause | Fix |
|---|---|---|
| Total is several seconds under or over the target | `--fit audio`: blocks follow the measured voice | inside the `--length-s` range: normal, say the real length at CP3. Over the maximum: `set-audio` and `status` answer `length.status: "over"` with `length.cut` (blocks and words to cut); shorten those, re-plan only them, measure again. Every block rounds up to a whole second. For an exact running time: `--fit grid` at init, and rewrite `over` blocks |
| `not_ready` or `gate` naming `over the requested <n> s` | the estimate (with 10 percent headroom) or the measured total is past the length the user asked for | shorten the blocks named in the message; the outline, CP3 and keyframes stay closed until it fits |
| A block feels like dead air | short sentence in a long block (grid fit), or long tail | merge the text into a neighbour, or use audio fit; tails are 0.6 s by default |
| The voice starts too abruptly after each cut | lead-in too short for this voice | it is set at `init` (`--lead-s`); changing it means a new project before narration, so decide at the first audition |
| SRT cues drift inside a block | proportional timing | acceptable for reading; for word-exact cues run the forced-alignment recipe (`assembly-explainer.md` section 7) |
| The final is longer than `total_s` by a fraction | container rounding | under 0.1 s is fine; more means a segment was rendered with other settings: `render --force`, then `--final` |
| A clip freezes on its last frame for a moment | the narration redo made the block longer than the clip, or the model's maximum clamped it | acceptable up to about a second; otherwise re-roll the clip at the new `visual_s` |

## 5. Resume and state

- **`status` is the source of truth.** It merges the run ledger into the block ledger and names the next step. After any interruption: `status`, then continue; never start over.
- **`pending` batches**: run the same `gm.py batch --plan <path>` again (Bash timeout 600000 ms). It resumes by label and id. Six reruns without a state change → tell the user, offer to continue later.
- **Wrong directory**: the run ledger is `.genmedia/runs.jsonl` relative to the current directory. Running from another folder sees no earlier requests and would pay for them again. Always run from the project root.
- **Expired CDN URLs** (resuming days later; a clip or caption job fails with empty `fields` although the input looks right): upload again only what the next stage reads (`gm.py upload`), record it (`style --key-url`, `attach --kind keyframe --block <n> --path <file> --url <new>`), restore the voided approval of the unchanged file (`approve --stage style|keyframes [--blocks <n>] --note "same file, new URL"`), then plan. After a new style-key URL, plan keyframes only with `--blocks <n>`: every keyframe input changed, so an unnamed plan would generate and bill all of them again.
- **`input_changed: true`** from the batch: a plan file was edited by hand after its job completed. Regenerate the plan with `explainer.py plan`; use `--reroll` for a new take.
- **A partial redo plan was overwritten** before it ran: harmless; `plan` again produces the same ids.
- **The user deleted `genmedia-output/`**: narration and stills must be regenerated only if their URLs also expired; otherwise download them again by hand from the URLs in `blocks.json` (`pipeline.py fetch` with a new step name), then `attach`.
- **Two people or two sessions on one project**: the ledgers are plain files without locking. One writer at a time.

## 6. Costs that surprise

| Surprise | Why | Prevent |
|---|---|---|
| Music billed two minutes for a "one minute" video | 61-120 s is two started minutes | generate the bed at `total_ms` after CP3; if it lands just over a boundary, offer a shorter bed (the local render loops and fades it) |
| Clips cost double the estimate | Wan defaults to 1080p when `resolution` is missing; `gm.py price` shows only the 480p figure | keep the preset (`720p`), price with the figure for your resolution |
| A keyframe cost $0.135 | Seedream's `auto_2K` default crossed the 1536x1536 area | keep the helper's explicit `image_size`; on other endpoints pass `--size-field` or a size in `--base-input` |
| A 3 s block billed 5 s | clamped to the model minimum | expected on H3 (5 s) and Seedance (4 s); Wan takes 2 s |
| Forced alignment cost $0.22 x blocks | it bills per call, rounded up to an hour | align the voice-only cut once |
| The ledger total exceeds the card | re-rolls, canaries on changed inputs, auditions | pass prices to every `plan`, report `gm.py ledger --label <slug> --sum` at each checkpoint |
| A failed job was billed | a runtime failure (policy, unreadable input) can bill; schema-level 422s normally do not | fix the named cause before `--retry-failed`; see `platform.md` section 5 |
