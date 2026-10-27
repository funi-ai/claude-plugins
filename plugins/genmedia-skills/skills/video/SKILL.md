---
name: video
description: >-
  One-off clips and clip edits via fal's genmedia CLI: text/image-to-video, first+last frame, reference-to-video, native dialogue, extend, restyle, reframe, motion transfer, lipsync, talking head, upscale. Defaults: Seedance 2.5, Wan 3.0 (value), MiniMax H3 (budget). Scenario videos go to a scenario skill; single clips stay here.
  Use when: "make a video of", "animate this image", "video between these two frames", "make her say this", "lipsync this video", "extend this clip", "make it vertical 9:16", "bu görseli videoya çevir", "video oluştur", "bu videoyu uzat".
  Chain: takes keyframes from `image`, @handle refs from `character`, speech from `audio`; hands .mp4 files and urls to `pipelines`.
  NOT for: TikTok, Reels, Shorts (use `short-video`); ads (use `ads`); narrated explainers (use `video-explainer`); screen-recording demos (use `demo-video`); multi-clip films, muxing (use `pipelines`); stills (use `image`); TTS, music, dubbing (use `audio`); identity setup (use `character`); model choice (use `models`).
argument-hint: "[what to make or change] [image/video/audio paths or urls] [--model <endpoint-id>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/frames.py" *) Bash(command -v genmedia) Bash(genmedia version *) Bash(genmedia models *) Bash(genmedia schema *) Bash(genmedia pricing *) Bash(genmedia docs *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 and python3 >= 3.8. Local ffmpeg is optional (frame review and chaining fall back to a fal utility endpoint).
---

# Video

One clip per request: generate it (text, start frame, first+last frame, references, native dialogue, multi-shot) or change one (extend, edit, reframe, motion transfer, lipsync, talking head, upscale, background removal).
Video is the expensive modality: approve a cheap still first, estimate before every job, never submit the same job twice.
Films made of several clips, voice-over, music and captions belong to `pipelines`; short-form social videos, ads and narrated explainers belong to `short-video`, `ads` and `video-explainer`; this skill makes the clips.

## Step 0 — Preflight

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
```

- `blockers` non-empty, CLI missing or older than 0.7.0: send the user to `/genmedia-skills:setup` and stop.
- Key missing or invalid: the user runs `genmedia setup` or exports `FAL_KEY` themselves; wait. Never read, print, request or type a key.
- Note `ffmpeg.found` (decides how step 9 extracts frames) and the `config` thresholds. Calling convention and fallbacks: `references/cli-contract.md`.

## UX rules

1. Reply in the user's language (often Turkish). Write model prompts in English; spoken lines and on-screen words stay in the language they must be heard or read in. IDs and field names stay as-is.
2. No JSON, request IDs or tool narration in chat. Wait silently; one status line at most ("still rendering, I will pick it up again").
3. Act on defaults: 5 s, 720p, 16:9 unless the platform implies vertical (Reels, TikTok, Shorts, Stories -> 9:16) or a start frame fixes the shape. **Question budget: 1**, only for aspect ratio or duration when neither the request nor the media settles it, as labelled options (AskUserQuestion when available). The cost confirmation is separate and does not count.
4. **Cost gate before every video job** (`references/platform.md` section 8): under USD 0.50 run; USD 0.50 to USD 2 say the estimate in one line and run; USD 2 or more wait for an explicit yes. These are the defaults; the `config` values preflight reports (`announce_above_usd`, `confirm_above_usd`) override them. A single 5 s 720p clip on the quality default is already above USD 2 (as of 2026-09-19), so expect to confirm. Never quote a price from memory. Never silently swap or downgrade a model the user named; offer the cheaper option in the same line and let them choose.
5. One checkpoint, not two: show the keyframe and the video estimate together ("Approve this frame? Animating it: 5 s, 720p, <model>, about $X. Cheaper: <option> about $Y."). Silence or a successful render is never approval.
6. Bounded repair: at most 3 attempts per step, something must change each time, never resend a content-policy rejection unchanged. A job that has a request ID is resumed, never resubmitted.
7. Real people: a recognisable person's face or voice (lipsync, talking head, motion transfer, identity references) needs the user's confirmation that they have consent. No invented testimonials or endorsements, no real logos the user does not own.

## Discovery guardrail

`references/routing-video.md` is a dated cache. Before the first paid call to an endpoint in a session:

```bash
genmedia models --endpoint_id <endpoint_id> --json
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
```

- Status must be `active`. Take field names, enums and limits from the schema, not from memory: they do not transfer between families or between the tasks of one family.
- Never invent endpoint IDs or parameters. Unknown model name from the user: `genmedia models "<name>" --no-classify --limit 10 --json`, pick the newest active match, say which one you picked. New releases sit under vendor namespaces (`bytedance/`, `alibaba/`, `minimax/`, `google/`), not only `fal-ai/`.
- Never use smart routing (`genmedia run` with a prompt where the endpoint ID belongs): it resolves stale video defaults.

## Routing

The media the user brings decides the task; the task decides the endpoint. Every task is a separate endpoint with its own field names.

| Intent | Default endpoint | Media fields | Why |
|---|---|---|---|
| Text only | `bytedance/seedance-2.5/us/text-to-video` | none | arena #1 on every generation board; 4-30 s; audio included |
| Animate a start frame | `bytedance/seedance-2.5/us/image-to-video` | `image_url` | same model; output shape follows the image |
| First + last frame | same endpoint | `image_url` + `end_image_url` | pins both ends |
| Keep a person, product or style, no fixed first frame | `bytedance/seedance-2.5/us/reference-to-video` | `image_urls`, `video_urls`, `audio_urls`; cite `@Image1` | largest reference budget |
| Spoken dialogue in new footage | Seedance 2.5 (text or image endpoint), `generate_audio` true | as above | arena #1 for native lip-synced speech; non-English lines: tie-breaker 6 |
| Several shots in one call | `fal-ai/kling-video/v3/pro/text-to-video` | `multi_prompt` instead of `prompt` | only family with a per-shot schema |
| Start frame + end frame + character elements together | `fal-ai/kling-video/v3/pro/image-to-video` | `start_image_url`, `end_image_url`, `elements[]` cited `@Element1` | richest control surface |
| Continue a clip | `bytedance/seedance-2.5/us/reference-to-video`, `task` "extension" | `video_urls`, cite `@Video1` | flat-rate alternative: `fal-ai/ltx-2.3/extend-video` (`video_url`) |
| Change a clip by instruction, restyle | `google/gemini-omni-flash/v1.1/edit` | `video_url` | arena top-three tie, cheapest; elements-driven edit: `fal-ai/kling-video/o3/pro/video-to-video/edit` |
| Other aspect ratio with generative fill | `fal-ai/ltx-2.3/reframe` | `video_url` | dedicated, no prompt needed |
| Drive a character image with a motion video | `fal-ai/kling-video/v3/pro/motion-control` | `image_url`, `video_url`, `character_orientation` | budget and non-human: `fal-ai/bytedance/dreamactor/v2` |
| Existing video + new audio | `fal-ai/sync-lipsync/v3` | `video_url`, `audio_url` | budget: `fal-ai/latentsync` |
| One image + audio | `fal-ai/bytedance/omnihuman/v1.5` | `image_url`, `audio_url` | budget: `fal-ai/flashtalk` |
| Upscale | `fal-ai/seedvr/upscale/video` | `video_url` | faithful; budget: `fal-ai/flashvsr/upscale/video` |
| Remove background | `bria/video/background-removal/v3` | `video_url` | set `background_color` "Transparent" for alpha |

Tiers for the generation tasks, same prompt and workflow:

- **Quality (default): Seedance 2.5.** Token-priced, about USD 0.57/s at 720p and USD 1.40/s at 1080p as of 2026-10-21 (the US-hosted endpoints, the only Seedance 2.5 fal still lists); confirm with `gm.py price <id> --explain`. Default 720p.
- **Value: Wan 3.0** (`alibaba/wan-3.0/text-to-video`, `alibaba/wan-3.0/image-to-video`, `alibaba/wan-3.0/reference-to-video`). Arena #2 overall at about USD 0.10/s 720p. Its `resolution` defaults to 1080p (twice the 720p price): set it. Start frame is `start_image_url`, audio switch is `audio`.
- **Budget, drafts: MiniMax H3 Max Turbo** (`minimax/h3-max-turbo/text-to-video`, `minimax/h3-max-turbo/image-to-video`). Cents per second. `prompt_expansion_mode` is required; `resolution` values are uppercase (`768P`); 5-15 s.
- **Control: Kling v3 Pro** (end frame, elements, `multi_prompt`, motion-control), **Gemini Omni Flash** (edit).

Tie-breakers:

1. The user named a model: use it. Translate stale IDs with the table in `references/routing-video.md`; say so, never swap silently.
2. Exact composition or a product that must look right in frame one: image-to-video from an approved keyframe, not reference-to-video. References carry identity; they do not pin the first frame.
3. The same person or product across several clips: reference-to-video or Kling elements; a `character` handle supplies the image URLs.
4. Exploring an idea: offer 480p on the same model or the budget tier, then render the keeper at 720p. Offer, do not impose.
5. 1080p or 4K only on request. Usually cheaper: render 720p, approve, then upscale.
6. Spoken language other than English or Chinese: Turkish → Wan 3.0 (text or image endpoint); in a native listen (`references/platform.md` section 10) it was right and every Seedance version mispronounced the line. Veo 3.1 Lite, flawless in that listen, is no longer listed on fal. Other languages: one probe clip the user listens to. Exact words: TTS from `audio` plus lipsync. Kling v3 voices auto-translate everything else to English.
7. Post-hoc lipsync is for footage that already exists. For new footage, native dialogue scores higher and is one job instead of three.
8. Scenario requests leave this skill: a TikTok, Reel, Short or promo built from a beat sheet → `/genmedia-skills:short-video`; an ad for a product → `/genmedia-skills:ads`; a narrated explainer → `/genmedia-skills:video-explainer`. A single clip or a clip edit stays here.

Traps:

- **Field-name trap.** Start frame: `image_url` (Seedance, MiniMax, Omni Flash) vs `start_image_url` (Kling v3, Wan 3.0). End frame: `end_image_url`. References: `image_urls` (Seedance, Kling O3) vs `reference_image_urls` (Wan, MiniMax). A wrong required name fails with 422; a wrong optional name is ignored and you pay for a clip without your media.
- **Wrong-task trap.** An image sent to a text-to-video endpoint is ignored. An image means the `image-to-video` endpoint.
- **Auto-duration trap.** Seedance `duration` defaults to `auto` and Wan accepts `null`: cost becomes unknowable. Always set `duration`.
- **Duration-type trap.** String enums on Seedance and Kling (`"5"`; a JSON number is coerced), integers on Wan and MiniMax. Longer than the model maximum is never requested: chain it (`references/video-recipes.md`).
- **Audio-default trap.** `generate_audio` defaults to true on Seedance (same price), Kling v3 (+50%); false on Kling O3. Set it explicitly on every call; turn it off on Kling when the clip will get voice-over or music later.
- **Aspect trap.** Seedance and Kling v3 image-to-video have no usable `aspect_ratio`: the start frame decides. Make the keyframe in the target ratio. A user image in another shape: outpaint it with `image` first, or reframe the finished clip; say which.
- **Lipsync vs talking head.** Video + audio is lipsync. One image + audio is talking head. Neither generates speech: get the audio from `audio` first.

Full dated tables, prices, limits and alternates: `references/routing-video.md`. Probes and frame utilities: `references/routing-utility.md`.

## Workflow

1. **Classify.** Media in hand + verb -> one row of the routing table. Infer aspect ratio and duration; spend the one question only if you cannot.
2. **Keyframe first.** For anything beyond a throwaway clip (a specific subject, product or person, brand work, anything to be published, any job at or above the announce threshold) get a still approved before paying for motion: have `image` generate the keyframe in the target aspect ratio, show it, get a yes. For first+last frame, make the end frame by editing the start frame (`image`, edit route) so identity, light and lens stay locked. Skip the ladder when the user supplied the start image, asked for pure text-to-video, or wants a budget-tier draft. `@handle` in the request: `character` resolves it to reference URLs (face first) plus an anchor text; best is a still of that character as the start frame, otherwise reference-to-video with those URLs. Never leave `@handle` in the prompt text.
3. **Verify** the endpoint and read its schema (Discovery guardrail). Map each file to its real field name.
4. **Upload** local media; use the returned `urls`. Uploaded files are public links: say so before uploading anything sensitive.

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload ./keyframe.png
   ```

5. **Write the prompt** with the shot grammar in `references/prompting-video.md`: subject + action, one camera move with a speed, framing, light with direction and temperature, motion intensity, sound plan when audio is on, end hold. For image-to-video describe motion only; the frame already holds the scene. Run the lint list there before spending.
6. **Estimate.** Seconds x the per-second tier your arguments select (resolution, audio; input seconds too when a video is an input). The pricing API returns ONE number per endpoint, usually the cheapest tier, and `needs_llms_txt:false` does not mean flat: for every video model price with `--explain`, read `pricing_text` and quote the higher figure. Arithmetic examples: `references/video-recipes.md` section 11. Apply the cost gate (UX rule 4).

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price bytedance/seedance-2.5/us/image-to-video,alibaba/wan-3.0/image-to-video
   ```

7. **Run.** Write the input object with the Write tool to `.genmedia/tmp/<label>.json` (exact fields per task: `references/video-recipes.md`), then run with a Bash timeout of 600000 ms. The helper submits async, records the request in the ledger first, polls with a bound and downloads into `genmedia-output/<label>/`; the file is `outputs[0].path`.

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run bytedance/seedance-2.5/us/image-to-video --input .genmedia/tmp/<label>.json --label <label> --est-cost <usd>
   ```

8. **Pending is normal.** `status:"pending"` means the job is still rendering and still billable. Resume it with the `resume` command the helper printed (same 600000 ms Bash timeout); never run step 7 again for the same clip. If the tool call died, the ledger still has the request.

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" wait <endpoint_id> <request_id>
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --tail 5
   ```

9. **Look before you deliver.** Build a contact sheet and read it with the Read tool:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/frames.py" sheet genmedia-output/<label>/<file>.mp4
   ```

   Check: subject still matches the keyframe or references at the end; the requested action and camera move happened; no morphing, extra limbs, melted text or black frames; duration and shape as ordered; the last frames settle. No local ffmpeg (`kind:"ffmpeg_missing"`): pull `first`, `middle`, `last` with `fal-ai/ffmpeg-api/extract-frame` (`references/video-recipes.md`), a fraction of a cent. Frames cannot judge sound: say that audio and lip sync were not checked.
10. **Repair or deliver.** A flaw the user would see: name it, change one thing (prompt wording, motion intensity, duration, seed, then model) and treat the re-render as a new cost. Otherwise deliver.
11. **Longer, or several clips.** Beyond the model maximum: extend, or bridge with the exact last frame (`scripts/frames.py frame --at last`), both in `references/video-recipes.md`. Three or more clips, voice-over, music, captions: hand over to `pipelines`, or to the scenario skill that owns the format (`short-video`, `ads`, `video-explainer`).

## Delivery

Translate the labels; keep paths, URLs and numbers literal.

```text
<local path to .mp4>
<CDN url>  (public to anyone with the link; may expire - the local file is the durable copy)
<Model display name> · <seconds> s · <resolution> · <aspect ratio> · audio <on|off> · est. $<cost>
Checked on frames: <what holds; any flaw you saw>. Not checked: <audio / lip sync>.
Next: <one concrete option: extend, upscale to 1080p, add voice-over via audio + pipelines>
```

Keyframe checkpoint (before the video job):

```text
<local path to keyframe>
Approve this frame? Animating it: <seconds> s, <resolution>, <model>, about $<estimate>.
Cheaper: <tier or 480p draft>, about $<estimate>.
```

More than one clip in the session: add the `gallery_url` the helper returned.

## Errors

| Signal (helper `kind`, fal `type` or verbatim text) | Action |
|---|---|
| `validation` + `fields[].type:"missing"` on `image_url`, `start_image_url`, `first_frame_url`, `video_url` (only when the field detail survives the queue) | Field-name trap. Re-read the schema, rename, rerun. Normally not billed. |
| `literal_error`, `enum`, `one_of` on `duration`, `resolution`, `aspect_ratio` | Take the nearest allowed value from the schema; tell the user the substitution. |
| `validation`, `http_status:422`, `fields:[]` plus a `hint` | The usual shape of a failed queued job (the helper exits 1 although fal said COMPLETED); the CLI lost the detail. First compare every field name, enum and type with the OpenAPI schema, then check media limits (size, seconds, pixels, fps, format). Do not resend unchanged. |
| `content_policy` / `content_policy_violation` | Never resend unchanged, never reword to slip past. Name the flagged part (prompt, image, audio), offer a compliant rewrite. |
| `file_download_error` | The media URL is dead or private: upload the local file again, use the new URL. |
| `video_duration_too_long`, `file_too_large`, `image_too_small`, `unsupported_video_format` | Fix locally to the bound in the message (trim, re-encode, resize), upload, rerun. Ask first if trimming loses wanted content. |
| `status:"pending"`, `still_running`, `Request is still in progress` | Still rendering. `gm.py wait`. Never resubmit. |
| `no_media_generated`, `generation_timeout`, `request_timeout`, `server` | One retry after a short wait; then lower duration or resolution, or move one tier (ask first if the user named the model). 5xx is not billed. |
| `not_found` | Routing cache is stale: search with `genmedia models "<name>" --no-classify --limit 10 --json`, say what you used instead. |
| `auth`, `No fal.ai API key found`, locked balance | Stop. The user fixes the key or tops up; send them to `/genmedia-skills:setup`. |

More symptoms (identity drift, frozen motion, garbled speech, lipsync misses): `references/troubleshooting-video.md`.

## Reference index

| File | Read when |
|---|---|
| `references/prompting-video.md` | read when writing or repairing any video prompt: shot grammar, timed beats, per-family syntax (Seedance tokens and tasks, Kling `multi_prompt`/elements, Wan, MiniMax), lint checklist, worked examples |
| `references/video-recipes.md` | read when building the input JSON for a task: exact fields and examples for image-to-video, first-last, references, extend and chaining, edit, reframe, motion transfer, lipsync vs talking head, upscale, background removal, frame extraction fallback |
| `references/troubleshooting-video.md` | read when a render is wrong or a job fails in a way the Errors table does not settle |
| `references/routing-video.md` | read when choosing a tier or alternate, checking limits and dated prices, or translating a stale model ID |
| `references/routing-utility.md` | read when you need a fal-side probe, frame extraction, trim or scale endpoint because local ffmpeg is missing |
| `references/cli-contract.md` | read when a helper call behaves unexpectedly, python3 is missing (raw CLI fallback), or you need the JSON shapes and ledger rules |
| `references/platform.md` | read when estimating cost (units, tiers, worked examples), reacting to an error type, or explaining URL privacy and expiry |
| `scripts/gm.py` | run for every fal call: `preflight`, `price`, `upload`, `run`, `wait`, `cancel`, `ledger` |
| `scripts/frames.py` | run for local review and chaining: `probe`, `sheet` (contact sheet), `frame --at first\|middle\|last\|<seconds>` (exact last frame) |
