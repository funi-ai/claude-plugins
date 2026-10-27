---
name: short-video
description: >-
  Short-form video for TikTok, Reels and Shorts (9:16, 16:9, 1:1) built from an approved beat sheet. Formats: viral hook, app launch, personal brand, course promo, faceless narrated b-roll, luxury product, before/after, testimonial, AI avatar, podcast clip. Seedream keyframes, Seedance 2.5 clips after a MiniMax H3 draft, SRT.
  Use when: "make a TikTok about", "15 second Reel for my app launch", "faceless Short with voice-over", "before and after video", "Reels videosu hazırla", "ürünüm için TikTok videosu yap", "seslendirmeli kısa video", "öncesi sonrası videosu".
  Chain: consumes stills from `image`, `product-photoshoot`, `launch-graphics`, @handle from `character`; produces a cut, SRT and manifest.
  NOT for: one clip, lipsync or upscale (use `video`); UGC, paid or app install ads (use `ads`); store stills (use `launch-graphics`); screen-recording demos (use `demo-video`); explainers (use `video-explainer`); voice or music (use `audio`); joining files (use `pipelines`); thumbnails (use `youtube-thumbnail`).
argument-hint: "[topic or goal] [platform] [--format <name>] [--seconds 15|30|45] [--slug <project>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/frames.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/audiokit.py" *) Bash(command -v genmedia) Bash(genmedia models *) Bash(genmedia schema *) Bash(ffprobe *) Bash(ffmpeg *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 with a fal key configured by the user, and python3 >= 3.8. Local ffmpeg is optional (free assembly, contact sheets, exact last frames).
---

# Short video

A 6 to 60 second vertical video, produced like a small film: brief, format and hook, **beat sheet**, approval, generation plan, keyframes, clips, sound, cut, captions. The beat sheet is the contract: nothing is generated before the user approved it, and every later step is traced back to one of its rows. Mechanics (batch, wait, ledger) live in `references/cli-contract.md`; this skill owns the craft and the order of work.

## Step 0 — Preflight

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
```

- `blockers` not empty, CLI missing or older than 0.7.0 → `/genmedia-skills:setup`. Key missing → the user runs `genmedia setup` or exports `FAL_KEY` themselves; wait. Never read, print, request or type a key.
- Keep `ffmpeg.found` and `ffmpeg.drawtext` (assembly route, burn-in route) and `config.announce_above_usd` / `config.confirm_above_usd` (cost gate; defaults 0.50 and 2).
- Resume first: Glob `.genmedia/projects/*/plan.md`. A plan for this video exists → read it, run `python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" urls --label <slug>`, continue at the first unfinished step. Never restart a project that has ledger entries.

## UX rules

1. Reply in the user's language (Turkish in → Turkish out). Model prompts are English; narration, dialogue and on-screen text stay in the language and exact spelling the user will publish. IDs, field names and paths stay as they are.
2. No JSON, request IDs or tool narration in chat. Wait silently; one status line per batch at most.
3. **Question budget: 2 before the beat sheet, one at a time, as labelled options (AskUserQuestion when available). After that: approvals only.**
   - Q1 **goal or topic**, only when the request has none ("make me a Reel"). There is no default for it.
   - Q2 **platform**, only when it cannot be inferred: the request names two placements with different shapes (website hero and Reels), or a placement you cannot map to a shape. No placement named → 9:16, which serves TikTok, Reels and Shorts at once: do not ask.
   - A must-have asset that is missing (F8 quote, F10 recording, F2 screenshots, F3 or F9 photos of a real person) costs no question: write the beat sheet with a labelled placeholder (`<customer quote, verbatim>`), list it under "Needed from you", and generate nothing for those beats until it arrives. Never fill a placeholder with invented words, faces or numbers.
   - Everything else is decided by you and listed under Assumptions in the beat sheet, where the user edits it: format (Routing), length (format default, else 15 s), hook family, narration language (the user's), voice (routing default), music on, captions as sidecar SRT, delivery 1080x1920, clip tier (quality after a draft pass).
4. **Hard stops.** (a) The beat sheet, always, whatever it costs. (b) The generation plan when the cost gate says confirm. (c) Keyframes and voice before any clip is paid for. (d) The draft cut before quality clips, when a draft pass ran. (e) A real person's photo, footage or voice: the user's explicit yes that they have that person's consent, before it is uploaded or used; ask with the beat sheet. Silence, a finished job or a yes to an older version is never approval. One approval covers one version.
5. Cost gate on the whole plan, all stages together: under announce → run; between → one-line estimate and run; at or above confirm → wait for a yes. Never swap a model the user named to get under a threshold; offer the cheaper tier in the plan and let them choose.
6. Re-roll budget: 2 per node (3 attempts), something changes each time; a policy rejection is never resent unchanged. A job with a request ID is resumed, never resubmitted.
7. Guardrails (full list under "This skill does NOT"): real people need the user's word that they have consent; testimonials, ratings and numbers come from the user or do not appear; no strobing or flashing hooks; uploads and results sit on public URLs, say so once before uploading private footage.

## Discovery guardrail

The tables below and `references/routing-video.md`, `references/routing-audio.md`, `references/routing-utility.md` are dated caches (verified 2026-09-19). Every distinct endpoint of the generation plan is confirmed **before the plan is shown**:

```bash
genmedia models --endpoint_id <id1>,<id2>,<id3> --status all --limit 50 --json
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
```

- The call returns at most `--limit` rows (default 20, verified 2026-09-23): keep `--limit` at or above the number of IDs, and a response with `has_more: true` means rows are missing, not that those IDs are gone.
- Every ID must be `active`; otherwise take the next tier of that task in the routing reference, else `genmedia models "<name>" --no-classify --limit 10 --json`, newest active match, and say which model ran.
- Field names, enums, duration ranges and limits come from the schema, never from memory. They do not carry over between families (`image_url` vs `start_image_url`; `duration` `"5"` vs `5`; `720p` vs `768P`).
- Never invent IDs or fields. Never run `genmedia run` without an endpoint ID. New releases sit under vendor namespaces (`bytedance/`, `minimax/`, `alibaba/`, `google/`, `elevenlabs/`), not only `fal-ai/`.

## Routing

**Format** (first match wins; arcs, beat timings for 15, 30 and 45 s, asset lists and pitfalls: `references/formats.md`)

| Format | Pick when the user wants | Default | Production shape |
|---|---|---|---|
| F1 viral hook | attention for one product, place or idea; "hook", "scroll-stopper" | 8 s | one continuous shot, native sound |
| F2 app or SaaS launch | software, a feature, a launch | 15 s | the user's real screenshots composited, never regenerated; UI sound, end card. A screen RECORDING is the main picture → `/genmedia-skills:demo-video` |
| F3 personal brand | a founder or creator introduced | 12 s | the person's photos or `@handle`, consent |
| F4 course or webinar promo | a course, cohort, event with a date | 15 s | hook, proof, promise, CTA card; proof from the user |
| F5 faceless narrated b-roll | a topic told by a voice over footage; "faceless", "seslendirmeli" | 30 s | voice first, one b-roll shot per sentence, captions |
| F6 luxury or aesthetic product | an object shown with restraint | 8 s | product photo → one slow move, end hold |
| F7 before / after | a change of state: room, desk, brand, routine | 8 s | two keyframes (after edited from before) → first + last frame clip |
| F8 testimonial or story | a customer's words | 15 s | the user's real quote, name and permission; b-roll or abstract picture |
| F9 AI avatar or talking head | a presenter speaking to camera | 15 s | portrait + voice → talking-head model, chunked by its audio limit |
| F10 podcast or audiogram clip | an existing recording made visual | 30 s | their audio stays; transcript drives beats; captions carry it |

The vaguest request with a topic ("a short video about cold brew") → F5, 30 s, 9:16, narration in the user's language. Two formats fit → the one whose assets the user already has.

**Role defaults** (verified active 2026-09-19; prices are dated hints, `gm.py price` decides)

| Role | Endpoint | Why | Price hint |
|---|---|---|---|
| keyframe (style anchor) | `bytedance/seedream/v5/pro/text-to-image` | quality default for stills; 1080x1920 stays in the lower price tier | ~USD 0.07/image |
| keyframe locked to the anchor, a product or a person | `bytedance/seedream/v5/pro/edit` | up to 10 references keep grade, product and face | ~USD 0.07 + USD 0.0045 per extra reference |
| clip, quality; also first + last frame | `bytedance/seedance-2.5/us/image-to-video` | arena #1; `end_image_url`; 4-30 s; audio included | ~USD 0.57/s at 720p, ~USD 0.26/s at 480p |
| clip, value; beats of 2-3 s | `alibaba/wan-3.0/image-to-video` | arena #2 at a fifth of the price; 2-30 s | ~USD 0.10/s at 720p |
| clip, draft pass | `minimax/h3-max-turbo/image-to-video` | cheapest motion check; 5-15 s; a 5 s 480P clip ran in under 10 s | ~USD 0.025/s at 480P (launch discount ended 2026-09-30) |
| talking head | `fal-ai/bytedance/omnihuman/v1.5` | portrait + audio; audio under 60 s at 720p | ~USD 0.16/s |
| voice, English and general | `fal-ai/elevenlabs/tts/eleven-v3` | default TTS | ~USD 0.10 per 1000 characters |
| voice, Turkish | `fal-ai/gemini-3.1-flash-tts` | `language_code` enum lists `Turkish (Turkey)`; `style_instructions` | ~USD 0.05 per 1000 characters |
| music bed | `elevenlabs/music/v2.5` | exact length through `music_length_ms` | ~USD 0.60 per started minute |
| sound effect | `fal-ai/elevenlabs/sound-effects/v2` | 0.5-22 s, loopable | ~USD 0.002/s |
| word timings for captions | `fal-ai/elevenlabs/speech-to-text/scribe-v2` | word timestamps feed `audiokit.py captions` | ~USD 0.008/min |
| burned-in captions | `fal-ai/workflow-utilities/auto-subtitle`; exact SRT (any language): `veed/subtitles` | word-highlight style; veed takes `srt_content` and lists `tr-TR` | ~USD 0.03/min; ~USD 0.10/min, 1 min minimum |
| text overlay or end card with exact words | `openai/gpt-image-2.5/flare/text-to-image` | `background: "transparent"` PNG, composited locally; never a video prompt | token-priced, ~USD 0.05-0.10 each |
| final to 1080x1920 | `fal-ai/seedvr/upscale/video` (quality tier), else a free local lanczos scale | one upscale of the cut beats rendering every clip at 1080p | ~USD 0.06 per second of 1080x1920 at 30 fps |
| cut, mux, frames, probe | local ffmpeg, else `references/routing-utility.md` | free and exact; fal utilities cost cents | - |

**Tie-breakers**

1. Voice before picture: the measured narration sets beat times, clip count and music length. Never generate clips against an unmeasured script.
2. Keyframe first, always: every shot starts from an approved still in the target shape. Image-to-video follows the still's aspect ratio; text-to-video is only for a throwaway draft.
3. One uncut shot = one generation. Consecutive beats in the same set with no cut are timed ranges inside ONE prompt; a cut starts a new job.
4. A beat shorter than the model minimum is generated at the minimum and trimmed in the cut. You pay for ordered seconds: 2-3 s beats go to Wan 3.0 (minimum 2 s) unless the user chose Seedance (minimum 4 s).
5. A shot longer than the model maximum, or two shots that must join without a seam: chain them. Exact last frame of clip N (`frames.py frame --at last`) → start frame of clip N+1, identical style string, camera direction and speed continued.
6. 720p clips, then ONE finish to 1080x1920: the paid upscale on the quality tier, the free local scale on value and draft tiers (`references/finishing.md` section 5). Native 1080p costs about 2.5 times more per second on Seedance; use it only on request.
7. The user named a model → use it after the live check; mention the default in one line, never swap silently.
8. `@handle` or "our presenter again" → `/genmedia-skills:character` resolves the reference set; pass those URLs as references of the keyframe edit.
9. Wrong skill: a video whose main picture is the user's screen recording → `/genmedia-skills:demo-video`; a paid or UGC ad for a product → `/genmedia-skills:ads`; a narrated explainer longer than a minute → `/genmedia-skills:video-explainer`; one clip with no beat sheet → `/genmedia-skills:video`; the cover of the finished video → `/genmedia-skills:youtube-thumbnail`; only joining files that exist → `/genmedia-skills:pipelines`.

**Traps**

- **Typography in a video prompt.** Video models garble words. Hook text, captions, prices, counters, star ratings, logos, lower thirds and UI text are COMPOSITED after generation; the prompt only reserves clean negative space for them. Split table: `references/craft.md` section 6; how to composite: `references/finishing.md` section 3.
- **Style drift.** Ten shots, ten grades. Write ONE style string (lens, grade, palette, grain, light family) and paste it verbatim, last, into every keyframe and clip prompt. Never paraphrase it.
- **`duration: "auto"`** (Seedance default) makes cost unknowable. Always set it. Seedance takes a string `"4"`-`"30"`, H3 an integer 5-15, Wan an integer 2-30.
- **H3 required field.** `prompt_expansion_mode` must be sent; `"disabled"` keeps your timing. Its resolution enum is uppercase (`480P`). It always adds a soundtrack: mute drafts in the cut.
- **Wan defaults.** `resolution` defaults to `1080p` (double the 720p price) and `enable_prompt_expansion` to true (rewrites your beats). Set both.
- **Mux length.** `fal-ai/ffmpeg-api/merge-audio-video` is as long as the shorter input (a long voice loses its end, a short one cuts the picture) and replaces the clip's own audio (measured 2026-09-19 and 2026-09-21). Match lengths first.
- **Native speech in another language.** In a native listen of one Turkish line, Veo 3.1 Lite was flawless and Wan 3.0 right, while every Seedance version mispronounced it (`references/platform.md` section 10). Veo is no longer listed on fal, so Turkish dialogue: Wan 3.0 and a user listen before approving, or TTS plus a talking-head model. A transcript alone misses mispronunciation.
- **Platform numbers.** Safe zones, length limits and cover rules live only in `references/platforms.md`, under its "unverified" banner. Do not quote platform numbers from memory anywhere else.

## Workflow

1. **Brief.** Spend the question budget only if needed. Read every user file with the Read tool before planning (HEIC, AVIF, TIFF, CMYK → convert to PNG or sRGB JPEG first, commands in `references/troubleshooting-short-video.md` section 0; videos → `frames.py sheet`; a file given only as a URL → save a local copy and Read that). Pick an ASCII kebab-case slug (`cold-brew-short`, `parfum-tanitimi`; helpers would transliterate a Turkish label anyway, but every path below uses the slug literally): it is the batch `label`, the ledger filter, `genmedia-output/<slug>/` and `.genmedia/projects/<slug>/`.
2. **Format, hook, style.** Choose the format (Routing) and ONE hook family from `references/hooks.md`. Write the style string and the negatives list (`references/craft.md`). Write the script if there is a voice: at most 2.3 words per second of voiced time (Turkish: 1.7, measured on Gemini voices in `references/platform.md` section 10), first word at 0.0 s, no greeting. Composited text (hook text, end card, CTA) is not spoken: a line moved into the voice-over later is a script change, counted against the same budget before the voice is ordered. The pace word in `style_instructions` moves the rate more than the voice does (1.2 to 2.1 words/s in `references/platform.md` section 10): ask for a natural, lively pace with short pauses between sentences; never "unhurried", "slow" or "calm pace" in short-form.
3. **Beat sheet.** Fill the template under Delivery from the matching structure in `references/formats.md`. Rules, all checkable:
   - Hook lands inside the first 1-2 s and works with the sound off. One hook mechanism.
   - One idea per beat. One camera move per beat, with a speed or amount (`slow push-in, 8% closer over 4 s`), or `locked-off`. Light has a direction and a temperature. Every beat names its sound.
   - Beats are 1-2 s in the hook, 2-5 s after it; ranges are contiguous and sum to the target length (within 0.5 s).
   - The last beat ends on a 0.5-2 s hold: settled frame, no new motion. It is the cover frame and the loop point.
   - The Text column is composited text only (hook text 3-5 words; reading time = words / 3 s). Essential picture and all text stay inside the safe zone of `references/platforms.md`.
   - Under the table: Generated vs composited, Assets needed from the user, Assumptions, rough cost per clip tier (ordered clip seconds x the per-second hint of the Role table, plus about USD 1 for stills, voice and music; marked rough, the priced plan follows in step 4).
   Save it to `.genmedia/projects/<slug>/plan.md`, show it, **stop**. Changes → new version, show again.
4. **Generation plan.** Map beats to shots (tie-breakers 3-5) and list every node: id (`kf01`, `vo`, `d01`, `clip01`, `music`, `cut`), role, endpoint, the parameters that drive price (size, `duration`, `resolution`, audio switch, characters), depends-on, estimate. Closest worked plan: `references/production.md`. Run the Discovery guardrail, then price everything in one call:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price <id1>,<id2>,<id3> --explain
   ```
   Dollars per node:
   - Keyframes (`unit: "units"`, read `pricing_text`): price per image at or under a 1536x1536 area (1080x1920 qualifies) x images; an edit adds the per-reference surcharge after the first input image. Text overlays are token-priced and `pricing_text` gives token rates only, no per-image figure: budget the upper end of the dated hint (USD 0.10 per overlay at the default `quality: "high"`; about USD 0.05 at 1024x1024, about USD 0.10 at 3840x2160 on 2026-09-19) and say it is a hint.
   - Clips: **ordered** seconds x the per-second figure for your `resolution`. Seedance is token-priced: use the per-second number for that resolution in `pricing_text`. H3 and Wan answer `seconds` with their cheapest tier only (`needs_llms_txt: false` does not mean flat): take the tier from the Price cell in `references/routing-video.md` or the row's `pricing_text` (`--explain`), and quote the higher figure.
   - Voice: characters / 1000 x `unit_price`. Music: started minutes x `unit_price`. Sound effects and talking head: seconds x `unit_price`. Scribe and auto-subtitle: minutes x `unit_price`. Upscale: width x height x frames / 1,000,000 x `unit_price`.
   - Sum every stage, draft pass included; say "about" and that re-rolls are extra. Offer the value tier in one line when quality clips dominate the total.
   Append the plan to `plan.md`, show it (template under Delivery), apply the cost gate.
5. **Upload and register user files** once; plans then reference them as `"@product"`:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload ./product.jpg
   python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" add --label <slug> --step product --path ./product.jpg --url <cdn_url>
   ```
6. **Stage 1: voice and keyframes** (cheap, parallel). Anchor keyframe first as a one-job plan; the other keyframes are edits of the anchor so grade and subject hold. Write each stage with the Write tool to `.genmedia/projects/<slug>/stage-<n>-<name>.tmpl.json`, then:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" fill --template .genmedia/projects/<slug>/stage-1b-keyframes.tmpl.json --out .genmedia/projects/<slug>/stage-1b-keyframes.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/stage-1b-keyframes.json
   ```
   Give every `batch`, `run` and `wait` call a Bash timeout of 600000 ms (the helper polls up to 540 s; the default 120 s kills it). `status: "pending"` → run the same batch command again; it resumes by label and id and never pays twice.
7. **Measure the voice, lock the times.** `python3 "${CLAUDE_SKILL_DIR}/scripts/audiokit.py" probe genmedia-output/<slug>/vo_0.mp3`, then word timings and the sidecar captions in one step (`references/finishing.md` C1). **The length on the beat sheet is a hard limit** (a platform length such as 15, 30 or 60 s above all): the measured voice to its last word plus the end hold must fit inside it. Over → cut words and regenerate the voice now (cents), before any clip is ordered; never speed the voice up, never lengthen clips or the hold past the sheet's length. Then move each beat boundary to the start of its first spoken word, round shot durations up to what the model accepts, update `plan.md`. Read every keyframe with the Read tool: subject, shape, negative space for text, no garbled lettering, one grade. **Checkpoint A: keyframes and voice. Stop.**
8. **Draft pass** (default when the quality clip stage alone reaches the confirm threshold; skip when the user declines or chose the draft model as the final tier): every shot on the draft endpoint at 480P from the approved keyframes, QA (step 10), rough cut against the voice (step 12, drafts muted). It proves motion, framing and pacing, not the look. **Checkpoint B: the draft cut. Stop.** Fix prompts and beat times now; they cost cents here and dollars later.
9. **Quality clips** as ONE batch (`max_parallel` = number of jobs, up to 12; say the expected wall-clock in one line). Four or more jobs on an endpoint not yet run in this project → run a one-job canary plan with the first id, QA it, then the full plan (the id is resumed, not repaid). Chained shots run in later stage files, one hop per stage.
10. **QA every clip before it enters the cut:**
    ```bash
    python3 "${CLAUDE_SKILL_DIR}/scripts/frames.py" sheet genmedia-output/<slug>/clip01_0.mp4 --count 6
    ```
    Read the sheet: the planned action and the one camera move happened; subject still matches the keyframe in the last tile; no morphing, extra limbs, invented text or logos; negative space is still clean; the end holds; `frames.py probe` shows the ordered duration and shape. Verdict: pass, re-roll (new id `clip03-r2`, change what the flaw names), or fail after 2 re-rolls (simplify the beat, tell the user). Frames cannot judge sound: say so. No ffmpeg → `fal-ai/ffmpeg-api/extract-frame` with `frame_type` first, middle, last.
11. **Music and effects**, after the picture length is known: `music_length_ms` = cut length; instrumental under a voice. Effects only on beats the sheet names.
12. **Assemble** (`references/finishing.md`). `ffmpeg.found` → local: trim each clip to its beat, normalize to one size and rate, concat, final size on the picture cut (tie-breaker 6), mix voice over ducked music, loudness, mux, probe. No ffmpeg → `fal-ai/ffmpeg-api/merge-videos`, then `fal-ai/ffmpeg-api/compose` when voice and music both sit under the picture, else `fal-ai/ffmpeg-api/merge-audio-video` with lengths matched first. Register local products with `pipeline.py add`; bare-string results go through `pipeline.py fetch`.
13. **Composite and caption.** Sidecar `.srt` always when there is speech (free). Burn-in only through `fal-ai/workflow-utilities/auto-subtitle` or `veed/subtitles`, or locally when `ffmpeg.drawtext` is true; burn last, after any upscale. Hook text, labels, CTA and end card: the user's files first, else transparent overlay PNGs from the typography model, placed with the timed-overlay recipe (`references/finishing.md` section 3). Read every rendered word against `plan.md`, Turkish characters included; what cannot be composited here is listed under "Left for your editor".
14. **Final gate, manifest, deliver.** Probe the final (length not over the sheet and at most 0.5 s under it, shape, audio stream), build one sheet of the final and read it against the beat sheet: hook inside 2 s, text inside the safe zone, end hold present. Then:
    ```bash
    python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" manifest --label <slug>
    python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --label <slug> --sum
    ```
    `manifest` exits 1 while `problems` is not empty: resolve or explain each. Append the outcome to `plan.md`.

## Delivery

Beat sheet (hard stop; this exact table is saved in `plan.md`):

```
Beat sheet v<n>: "<title>" · <format> · <seconds> s · <9:16 1080x1920> · hook: <family>
| # | Time | Shot (one idea) | Camera (one move + speed) | Light | Sound | Text (composited) |
| 1 | 0.0-1.5 | <hook, readable with sound off> | <snap push-in, 0.3 s> | <hard key left, 3200K> | <silence, then sub hit at 1.2 s> | "<3-5 words>" |
| 2 | 1.5-5.0 | ... | ... | ... | VO: "<line>" | - |
| n | <..-end> | <payoff, last 1.0 s hold> | locked-off | ... | music resolves | "<CTA verb>" + logo |
Style string: <one paragraph, English, pasted verbatim into every prompt>
Generated: <picture, motion, ambience> · Composited: <hook text, captions, CTA card, logo, numbers>
Needed from you: <files, quotes, numbers, permissions> · Assumptions: <every default you chose>
Rough cost: quality about $<x> · value about $<y> · draft-only about $<z>. Nothing is generated until you approve.
Approve, or tell me which beats to change.
```

Generation plan (after approval): `Plan v<n>: <k> nodes, about $<total> (estimate; re-rolls extra).` then one row per node (id, beats, model, key parameters, estimate), the checkpoints, and `Reply "go" to start.` when the gate says confirm.

Checkpoint: `Checkpoint <A|B>: <what>` + numbered local paths with one line each + `Spent so far about $<est_cost_usd_completed>. Next: <step>, about $<y>. Approve all, or name the numbers to redo and what to change.`

Final:

```
Done: "<title>" (<seconds> s, <width>x<height>)
Final: genmedia-output/<slug>/<slug>_final.mp4 · Captions: genmedia-output/<slug>/<slug>.srt · Cover frame: <path>
Parts: genmedia-output/<slug>/ · Beat sheet and log: .genmedia/projects/<slug>/plan.md · Manifest: .genmedia/projects/<slug>/manifest.json
Link: <CDN URL if any> (public to anyone who has it, may expire; the local file is your copy)
Models: <display names>. Estimated spend about $<est_cost_usd_completed>, including <r> re-rolls. Gallery: <gallery_url>
Composited by me: <list>. Left for your editor: <list or none>. Sound and lip sync were not machine-checked: watch it once with audio.
<if a synthetic person or voice appears: it is AI-generated; label it where the platform asks for it.>
```

Translate the templates; keep paths, IDs and numbers as they are.

## Errors

| Signal (verbatim) | Action |
|---|---|
| `"status":"pending"` with `resume` | Run the same `gm.py batch --plan` (or `gm.py wait`) again with the 600000 ms timeout. Never resubmit. Six reruns with no state change → report, offer to continue later. |
| `input.<key>: '@kf01' is not a URL` (exit 2, nothing sent) | The template was run unfilled. `pipeline.py fill`, then the filled plan. |
| `pipeline.py fill`: `"unresolved"` lists a reference | That job did not complete or the file was never registered. Finish it or `pipeline.py add` it; never paste a guessed URL. |
| `"kind":"validation"` with named `fields` (HTTP 422, nothing ran) | Fix exactly the named field from the OpenAPI schema (name, type, enum case, range), then rerun the same plan with `--retry-failed`. A field you cannot find in the schema is deleted, not guessed. |
| `"kind":"validation"` with `"fields":[]` and a `hint` | `COMPLETED` was terminal, not success; the queue hides the reason. Check in order, change the first thing that is off: fields against the OpenAPI schema (start-frame field name, `duration` type and range, resolution case, required `prompt_expansion_mode`) → input files (expired URL, over 30 MB, odd format: re-upload) → prompt (policy). Rerun with `--retry-failed`. Max 3 attempts. |
| `"kind":"content_policy"` | Rewrite that beat's prompt or keyframe. Never resend unchanged, never reword to slip past a filter. Assume it was billed. |
| `audio_duration_too_long`, or a talking-head job that fails with empty `fields` | Probe the audio. Split the narration into chunks under the model limit (`references/production.md` section 7), one clip per chunk. |
| `"kind":"ffmpeg_missing"` from `frames.py` or `audiokit.py` | Use the fal utility named in the `hint`. |
| `"input_changed":true` | A completed id was edited. Restore the plan, or re-roll under a new id. |
| `"kind":"auth"` | Stop every stage. The user fixes the key or balance. |

Wrong-looking results (drift, seams, garbled text, captions off, voice too long): `references/troubleshooting-short-video.md`. Platform error types: `references/platform.md` section 4.

## This skill does NOT

- Invent proof. No fabricated testimonials, customers, faces of "users", ratings, review counts, revenue, follower or result numbers. F8 needs the real quote, the name or an agreed anonymisation, and the user's word that they may publish it; a rating always names its source.
- Use a real person's face or voice without the user confirming consent (F3, F8, F9, F10 hosts and guests). No lookalikes of public figures.
- Make misleading before/after: no health, body, medical, income or investment results; both states are honest depictions of the same subject, and a dramatization is labelled as one.
- Build hooks on strobing, rapid flashing or high-contrast flicker (photosensitivity), or on fake platform UI, fake notifications or fake news frames.
- Use real brand, studio, film-stock, artist or celebrity names as style handles. Describe the physical look instead.
- Show logos, packaging, trademarks or characters the user does not own, a competitor's product or mark, or comparative claims against a named competitor. A generated logo or mark in a clip fails QA.
- Pass a synthetic presenter, a narrator or a cloned voice off as a real customer, employee or expert. Voice cloning of a real person goes through `audio` with their consent.
- Ask a video model for typography, or promise platform acceptance, reach or "virality". Platform facts are heuristics to verify (`references/platforms.md`).
- Publish, schedule or upload to any platform.

## Common mistakes

- Generating before the beat sheet was approved, or treating "looks good" about keyframes as approval of the clip budget.
- Two camera moves in one beat; "cinematic" instead of a lens, a move and a Kelvin value; a beat with no sound entry.
- Paraphrasing the style string per shot, or writing keyframes independently instead of editing them from the anchor.
- Writing the script after the clips. Voice first; its measured length moves the beats.
- Asking for the hook text, the price or the logo inside the video prompt instead of reserving space and compositing it.
- No end hold: the move runs to the last frame, so the cover frame is a blur and the loop jumps.
- Paying Seedance minimums for 2 s beats, or rendering every clip at 1080p instead of upscaling the cut once.
- Skipping the draft pass on an USD 8+ clip stage, then re-rolling quality clips to fix pacing.
- Burning captions before the upscale, or trusting speech-to-text spelling of names without reading the transcript.
- Chaining from a timestamp screenshot instead of the exact last frame; changing the style string across a seam.
- Quoting safe-zone or length numbers from memory instead of `references/platforms.md`.

## Reference index

- `references/formats.md`: read when choosing the format and writing the beat sheet; ten formats with when to use, arc, beat structures for 15, 30 and 45 s with timings, asset manifest, generated vs composited split, pitfalls.
- `references/hooks.md`: read when picking the hook family and writing beat 1; families with mechanism, timing, examples, spoken and text hook rules, banned hooks.
- `references/craft.md`: read when writing the style string, any keyframe or clip prompt, or the sound plan; camera, light and sound vocabulary with numbers, the generated vs composited table, prompt templates, the prompt lint checklist to run before every paid stage.
- `references/platforms.md`: read when choosing shape, size, length, text placement, cover frame or loop; the ONLY place with platform numbers, all flagged as unverified heuristics, plus the one safe-zone rule.
- `references/production.md`: read when writing the generation plan and stage files; beat-to-shot mapping, per-model field table, three complete worked `gm.py batch` productions (faceless narrated b-roll; before/after through first + last frame; luxury product image-to-video), exact-last-frame chaining, talking-head chunking.
- `references/finishing.md`: read when measuring the voice, writing captions, cutting, mixing, compositing text or choosing the final size; tested local ffmpeg recipes next to the fal utility route, overlay and end-card method, burned-caption routes, the final gate.
- `references/troubleshooting-short-video.md`: read when a result is wrong rather than failed, a stage resumes oddly, lengths do not match, or costs surprise.
- `references/routing-video.md`: read when picking another clip tier or family, when an ID is not active, or for dated price and limit notes.
- `references/routing-audio.md`: read when choosing a voice, music, effect, transcription or dubbing model, and for language support checks.
- `references/routing-utility.md`: read when assembling without local ffmpeg or when you need a utility endpoint's verified fields.
- `references/cli-contract.md`: read when a helper call fails, a job is pending, or you need batch plan keys, `wait`, `cancel`, the ledger or the raw CLI.
- `references/platform.md`: read when estimating cost, reacting to a platform error type, or explaining URL privacy, billing and safety.
- `scripts/gm.py`: the shared helper (`preflight`, `price`, `upload`, `run`, `wait`, `cancel`, `batch`, `ledger`).
- `scripts/pipeline.py`: project state (`urls`, `fill`, `add`, `fetch`, `manifest`); resolves `"@job"` references.
- `scripts/frames.py`: `probe`, `sheet` (contact sheet for QA), `frame --at last` (exact last frame for chaining).
- `scripts/audiokit.py`: `probe`, `captions` (word timings to SRT), `chunk` and `concat` (long or per-chunk narration), `loudnorm`.
