---
name: pipelines
description: >-
  Engine for multi-step productions no scenario skill owns, via fal's genmedia CLI: plan card, cost gate, staged batch fan-out, QA gates, assembly (local ffmpeg or fal ffmpeg-api: concat, mux, captions), manifest.
  Use when: "turn this storyboard into a film", "stitch these clips together", "add voice-over and music to my video", "burn in these subtitles", "talking avatar from this script", "make 10 variations", "resume my batch", "bu klipleri birleştir", "bu videoya müzik ve seslendirme ekle", "altyazıyı videoya göm".
  Chain: consumes files, CDN URLs and handles from `image`, `video`, `audio`, `character`; produces plan, manifest, files.
  NOT for: ads, shorts, explainers (use `ads`, `short-video`, `video-explainer`); product shoots, listing cards, thumbnails, brand kits, meshes (use `product-photoshoot`, `marketplace-cards`, `youtube-thumbnail`, `brandkit`, `3d`); one image, clip or sound (use `image`, `video`, `audio`); identity sheets (use `character`); model choice (use `models`); setup problems (use `setup`).
argument-hint: "[what to produce] [--slug <project>] [--resume]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" *) Bash(command -v genmedia) Bash(genmedia models *) Bash(genmedia schema *) Bash(ffprobe *) Bash(ffmpeg *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 and python3 >= 3.8. Local ffmpeg is optional.
---

# Pipelines

The method for any production that needs more than one generation or an assembly step: storyboard to clips to film, narrated video, product still to ad clip, talking avatar, batch variations, upscale and finishing chains, captions. This skill owns the mechanics (plan, gate, stage, wait, check, assemble, record). Creative craft and model choice belong to `image`, `video`, `audio`, `character` and `models`. Productions with their own scenario skill (`ads`, `short-video`, `video-explainer`, `product-photoshoot`, `marketplace-cards`, `youtube-thumbnail`, `brandkit`, `3d`) belong to that skill, which carries this engine.

## Step 0 — Preflight

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
```

- `blockers` not empty: stop and point to `/genmedia-skills:setup`. Key missing: the user runs `genmedia setup` or exports `FAL_KEY` themselves; wait. Never read, print, request or type a key.
- Keep `ffmpeg.found` and `ffmpeg.drawtext` from the output: they decide the assembly path.
- Keep `config.announce_above_usd` and `config.confirm_above_usd`: they are the cost-gate thresholds (defaults 0.50 and 2).
- Resume first: look for `.genmedia/projects/*/plan.md` (Glob). If one matches this request, read it and run `python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" urls --label <slug>`. Continue at the first unfinished step. Never restart a project that has ledger entries.

Details: `references/cli-contract.md`.

## UX rules

- Reply in the user's language (often Turkish). Write model prompts in English unless spoken or on-image text is in another language. Flags, IDs and file names stay as they are.
- No JSON, request IDs or tool narration in chat. Wait silently; at most one status line per batch ("6 of 8 clips done, still rendering").
- **Question budget: the plan approval plus the checkpoints declared in the plan. Nothing else.** Missing details (aspect ratio, voice, clip count, music mood) are decided by you and shown in the plan card under Assumptions; the user edits the plan instead of answering a questionnaire. Only exception: an input nobody but the user can supply (their file, their saved-workflow ID); ask for it once, before the plan.
- A plan that uses a real person's likeness or voice lists the consent under Assumptions and always waits for the approval, whatever it costs.
- Approvals are hard stops. Silence, a stage that succeeded, or a yes given to an earlier version never count as approval. One approval covers one plan version and is consumed once.
- A materially different plan (a new paid step, or total up more than 20 percent) is a new version and needs a new approval.
- Cost gate on the whole plan, all stages and all fan-out jobs together (`references/platform.md` section 8): under USD 0.50 run, USD 0.50 to USD 2 announce and run, USD 2 or more confirm (or the thresholds from preflight `config`). A multi-stage plan always gets its plan card; the gate decides whether you wait for a yes.
- Never downgrade or swap a model the user named to get under a threshold. Offer the cheaper route in the plan card and let them choose.
- Deliver local paths first, then CDN URLs (public, may expire), then one summary line and the gallery link.

## Discovery guardrail

- Every distinct endpoint in the plan is verified before the plan card is shown, not just before the first call: a plan that fails at stage 3 has already spent stages 1 and 2.
- The role table below and `references/routing-utility.md` are dated caches. Generation-model choice follows the routing of `image`, `video`, `audio` and `models`; the short list here is the default when the user has no preference.
- Utility endpoints are carried in `references/routing-utility.md` because catalog search does not surface all of them. Never add `fal-ai/` style IDs from memory, blogs or other skill packs.
- Never invent endpoint IDs, fields, enums or limits. User names an unknown model: `genmedia models "<name>" --no-classify --limit 10 --json`, pick the newest active match, say which.
- Never use smart routing (`genmedia run` with a prompt instead of an endpoint ID).

## Routing

**Which method**

1. One generation, no assembly: not this skill. Hand to `image`, `video` or `audio`. An ad, a short-form social video, a narrated explainer, a product shoot, listing cards, a thumbnail, a brand kit or a mesh: hand to `ads`, `short-video`, `video-explainer`, `product-photoshoot`, `marketplace-cards`, `youtube-thumbnail`, `brandkit` or `3d`.
2. N independent generations (variations, format sets, batch upscales): one stage, one batch plan.
3. Dependent steps (keyframes, then clips, then a cut): staged batches with a QA gate between stages. A stage is the set of nodes whose inputs all exist.
4. Only assembling files that already exist: skip to Workflow step 10. Under the cost gate this usually needs no confirmation.
5. The user names a saved fal Workflow (`workflows/<owner>/<name>`) or asks to export one: these skills do not use fal Workflows. Say so in one line and offer the staged pipeline for the same chain.

**Role defaults (verified active 2026-09-19; prices are dated hints, confirm with `gm.py price`)**

| Role | Endpoint | Why | Price hint |
|---|---|---|---|
| keyframe | `bytedance/seedream/v5/pro/text-to-image` | quality default for stills | ~USD 0.07/image up to 1536x1536 |
| consistent keyframe, product scene | `bytedance/seedream/v5/pro/edit` | up to 10 references keep style and product | ~USD 0.07/image |
| image-to-video | `bytedance/seedance-2.5/us/image-to-video` | quality default; optional `end_image_url` | token-priced, ~USD 0.57/s at 720p |
| image-to-video, budget or drafts | `minimax/h3-max-turbo/image-to-video` | cheapest current tier | ~USD 0.04/s at 768P (launch discount ended 2026-09-30) |
| voice-over | `fal-ai/elevenlabs/tts/eleven-v3` | default TTS | ~USD 0.10 per 1000 chars |
| voice-over, Turkish | `fal-ai/gemini-3.1-flash-tts` | `language_code` enum lists Turkish | ~USD 0.05 per 1000 chars |
| music bed | `elevenlabs/music/v2.5` | exact length via `music_length_ms` | ~USD 0.60 per started minute |
| talking head | `fal-ai/bytedance/omnihuman/v1.5` | image + audio; under 60 s at 720p | ~USD 0.16/s |
| upscale video / image | `fal-ai/seedvr/upscale/video`, `fal-ai/seedvr/upscale/image` | faithful, cheap | ~USD 0.001 per megapixel |
| concat, mux, timeline, frames, probe, trim, scale, loudness, captions | `references/routing-utility.md` | verified fields and output paths | cents or less |

**Assembly decision**

- `ffmpeg.found` is true: assemble locally. Free, fast, exact, no resolution cap, and the only route with real mixing (ducking, crossfades). Recipes: `references/assembly.md`.
- No ffmpeg: fal utilities, URLs in and URL out. `fal-ai/ffmpeg-api/merge-videos` for a cut, `fal-ai/ffmpeg-api/merge-audio-video` for one audio track, `fal-ai/ffmpeg-api/compose` when voice and music must both sit under the picture. Compose plays clips back to back at the first clip's size and frame rate and ignores gaps and durations: trim and normalize the clips and join the voice into one file first (`references/assembly.md`).
- Burned-in captions: never count on the local `drawtext` or `subtitles` filters (many builds lack them; `ffmpeg.drawtext` tells you). Use `fal-ai/workflow-utilities/auto-subtitle` (`language` is a two-letter code; `tr` works), or `veed/subtitles` when you hold the exact text as SRT. Always also write a sidecar `.srt`; it is free.

**Tie-breakers**

- Voice before visuals: the measured voice-over length sets clip count and durations. Generate and probe the voice in stage 1.
- Cheap before expensive: stills before clips, clips before upscale, draft resolution before final. Put a checkpoint in front of every step that costs more than everything before it.
- Merge, then upscale, when the target fits 2048 px per side (one upscale job). Above that, upscale per clip and concatenate locally: `merge-videos` clamps width and height to 512-2048.
- Pass fal CDN URLs from stage to stage. Upload only user files and locally processed intermediates.

**Traps**

- One giant batch: jobs inside one plan are independent. A job cannot read a sibling's output. Stage it.
- Bare-string outputs: `fal-ai/ffmpeg-api/compose` and `fal-ai/auto-caption` return `.result.video_url` as a plain string. `--download` only saves file objects, so no file lands on disk; the helper does record the URL as an output with `path: null`, so `pipeline.py fetch --label <slug> --step <job id> --out <path>` saves it without `--url`. Do it right after the run.
- `fal-ai/ffmpeg-api/metadata` echoes its input as `.result.media.url`; set the job-level key `"download": false` (next to `input`, never inside it) or the input is downloaded again.
- `fal-ai/workflow-utilities/trim-video` defaults to `start_time` 1 and `duration` 2. Always pass both ends.
- `fal-ai/ffmpeg-api/merge-audios` concatenates; it does not mix. No listed endpoint overlays two tracks: mix locally or use two audio tracks in compose.
- Start-frame field names differ per family (`image_url`, `start_image_url`, `first_frame_url`). A wrong name is silently ignored on some models and the job bills anyway.
- `duration: "auto"` makes cost unknowable. Always set it.
- Editing the input of a completed job does nothing: the batch resumes the recorded request and flags `input_changed`. A re-roll needs a new job id.

## Workflow

1. **Scope and slug.** Pick a short slug (`spring-ad`). It is the batch `label`, the ledger filter, the output folder `genmedia-output/<slug>/` and the project folder `.genmedia/projects/<slug>/`. One label for all stages.
2. **Node table.** List every node: id (unique across the project: `vo`, `kf01`, `clip01`, `cut`), role, endpoint, inputs, depends-on, output. Group nodes into stages. Pick the closest worked example in `references/batch-plans.md` and adapt it.
3. **Schema preflight for every node.** One catalog call for all IDs, then one schema per distinct endpoint:

   ```bash
   genmedia models --endpoint_id <id1>,<id2>,<id3> --status all --limit 50 --json
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
   ```

   Every ID must be `active`. Check each planned input key, enum value, range and required field against the schema, and note the output path (`images[0]`, `video`, `audio`, or a bare string). Fix the node table before pricing it.
4. **Price the plan.** `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price <id1>,<id2>,<id3>`; add `--explain` and read `pricing_text` where `needs_llms_txt` is true (always for video). Estimate per node, sum per stage and in total, round up. Method: `references/platform.md` section 7.
5. **Plan card.** Fill the template in `references/plan-card.md`, save it with the Write tool to `.genmedia/projects/<slug>/plan.md`, show it in chat, apply the cost gate. Waiting for a yes is a hard stop: no uploads, no submits.
6. **Upload user files** once: `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload <path>...`, then register each so later plans can reference it by name:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" add --label <slug> --step product --path ./product.png --url <cdn_url>
   ```

7. **Run a stage.** Write the batch plan with the Write tool to `.genmedia/projects/<slug>/stage-<n>-<name>.tmpl.json`. Reference earlier outputs as `"@<job_id>"` or `"@<job_id>[<index>]"` instead of pasting URLs, then resolve and run:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" fill --template .genmedia/projects/<slug>/stage-2-clips.tmpl.json --out .genmedia/projects/<slug>/stage-2-clips.json
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/stage-2-clips.json
   ```

   - Give the Bash call a 600000 ms timeout; the helper polls for at most 540 s.
   - `max_parallel`: set it to the number of jobs in the stage, up to 12. fal's queue never rejects; the account limit (2 on new accounts) only decides how many render at once, and jobs that are already queued keep moving while you are between tool calls. Tell the user the expected wall-clock in one line before a large stage.
   - Canary: before fanning out 4 or more paid jobs on an endpoint not yet run in this project, run a one-job plan with the first job (same label, same id). When it completes and passes QA, run the full plan; the helper resumes that id from the ledger and does not pay twice.
   - `status: "pending"`: run the same batch command again. It resumes by label and id and never resubmits a job that has a request ID. Stop after 6 consecutive reruns in which no job changed state, report, and offer to continue later; the ledger keeps everything resumable.
   - Some jobs failed, others completed: keep what landed, repair only the failed ids (step 9).
8. **QA gate.** Look at the outputs before spending on the next stage: Read every image; for clips build a contact sheet or extract frames (`references/qa-gates.md`). Verdict per asset: pass, re-roll, or fail. If the plan declares a checkpoint here, send the checkpoint message from Delivery and stop.
9. **Repair one node, never the pipeline.** Failed id: change what the error names in the template, `fill` again, then rerun the stage plan with `--retry-failed`. The flag resubmits every failed id in that plan file: fix each one, or run a plan file that holds only the repaired ids (same label, same ids). Weak but completed id: add a new job id (`clip03-r2`) with a changed prompt or seed and point later stages at it. Maximum 3 attempts per node, each one different; then stop and explain. Policy and budgets: `references/qa-gates.md`.
10. **Assemble.** Follow the assembly decision. Local: `references/assembly.md` recipes, writing only under `genmedia-output/<slug>/`, then record the result with `pipeline.py add --label <slug> --step final --path <file> --tool ffmpeg --from <ids>`. fal utilities: a final one-job stage plan; bare-string results go through `pipeline.py fetch`.
11. **Manifest and mechanical gate.**

    ```bash
    python3 "${CLAUDE_SKILL_DIR}/scripts/pipeline.py" manifest --label <slug>
    ```

    It writes `.genmedia/projects/<slug>/manifest.json` from the ledger plus the local assets and exits 1 while `problems` is not empty (missing or empty files, unfinished or failed nodes, results that were never fetched). Resolve or explain every problem before delivering.
12. **Deliver** with the template below. Append the outcome to `plan.md` (what ran, what was re-rolled, estimated spend from `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --label <slug> --sum`).

## Delivery

Plan approval (after the plan card):

```
Plan v<n> for "<title>": <k> steps, about $<total> in total (estimate; re-rolls are extra).
I will stop for your approval after: <checkpoint steps>.
Reply "go" to start, or tell me what to change.
```

Checkpoint:

```
Checkpoint: <step label>
<numbered list: local path, one line on what it shows>
Spent so far: about $<est_cost_usd_completed>. Next: <next step>, about $<next cost>.
Approve all, or name the numbers to redo (and what to change).
```

Final:

```
Done: <title>
Final: <local path of the deliverable> (<duration or size>, <resolution>)
Parts: genmedia-output/<slug>/  |  Manifest: .genmedia/projects/<slug>/manifest.json
Link: <CDN URL if one exists> (public to anyone who has it, may expire; the local file is your durable copy)
Models: <display names>. Estimated spend: about $<est_cost_usd_completed>, including <r> re-rolls. Gallery: <gallery_url>
```

Translate the templates; keep paths, IDs and numbers unchanged.

## Errors

| Signal (verbatim) | Action |
|---|---|
| `"status":"pending"` with `resume` | Run the same `gm.py batch --plan` (or `gm.py wait`) again. Never resubmit. |
| `input.<key>: '@kf01' is not a URL` (exit 2, nothing sent) | The template was run unfilled. Run `pipeline.py fill`, then the filled plan. |
| `pipeline.py fill`: `"unresolved"` lists a job | The upstream job is not completed. Finish or repair it first; never paste a guessed URL. |
| `pipeline.py fill`: `"placeholders"` lists a JSON path | A template placeholder (`{LOCK}`, `{{TOKEN}}`, `<describe it>`) survived in that string. Nothing was written: put the real text there. A bracket that belongs in the prompt is escaped `\{ \} \< \>`. |
| `"kind":"validation"` with `"fields":[]` and the truncation `hint` | Queued jobs lose field details. Compare the input with the OpenAPI schema; usual pipeline causes: an expired or unfetchable upstream URL, the wrong start-frame field name, an out-of-enum `duration`, media over the model's limits. Fix that job, rerun with `--retry-failed`. |
| `"kind":"content_policy"` | Rewrite that job's prompt or input. Never resend unchanged, never reword to slip past a filter. |
| `submission state unknown` | Check https://fal.ai/dashboard/requests. Use `--retry-failed` only if the job never started. |
| `"input_changed":true` | The file on disk came from a different input than the plan now holds. Restore the plan, or re-roll under a new id. |
| `"kind":"auth"` | Stop every stage. The user fixes the key or balance. |
| A job stays `IN_PROGRESS` across 6 reruns | `gm.py cancel <endpoint_id> <request_id>`, report that a cancel acknowledgement is not final, point to the dashboard. Never follow a cancel with `--retry-failed` in the same turn: the job may still finish and both would bill. |

More: `references/troubleshooting-pipelines.md`. Platform error types: `references/platform.md` section 4.

## Reference index

- `references/plan-card.md`: read when drafting, saving or revising a plan card, deciding where checkpoints go, or logging an approval.
- `references/batch-plans.md`: read when writing a stage plan; five worked staged examples (keyframes to clips, narrated short, product still to ad clip, TTS to talking head, upscale chain) with verified fields.
- `references/assembly.md`: read when cutting, mixing, muxing, trimming, scaling or captioning; local ffmpeg recipes next to the fal utility calls, with output paths and quirks.
- `references/qa-gates.md`: read when checking a stage's outputs, deciding pass or re-roll, applying re-roll budgets, or running the pre-delivery gate.
- `references/troubleshooting-pipelines.md`: read when a stage fails, hangs, resumes oddly, or a plan, ledger and files disagree.
- `references/routing-utility.md`: read when you need a utility, understanding or 3D endpoint with its verified fields, limits and prices.
- `references/cli-contract.md`: read when you need helper flags, JSON shapes, the batch plan format, ledger fields or the raw-CLI fallback.
- `references/platform.md`: read when estimating cost, reacting to a platform error type, or reasoning about URLs, billing, concurrency and safety.
- `scripts/gm.py`: the shared helper (`preflight`, `price`, `upload`, `run`, `wait`, `cancel`, `batch`, `ledger`).
- `scripts/pipeline.py`: project state for pipelines (`urls`, `fill`, `add`, `fetch`, `manifest`); prints one JSON object, exit 0 ok, 1 problems, 2 usage.
