# Model comparison

Run the same prompt on several endpoints, deliver the files and a facts-only table, and let the user judge. This is the one paid flow of the `models` skill. Helper options, the batch plan contract and error kinds: [cli-contract.md](cli-contract.md). Cost gate and billing rules: [platform.md](platform.md) §5 and §8.

`gm.py` below means `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py"`.

## 1. Ground rules

- **No verdict.** Never write "best", "winner", "better" or "I recommend" about the outputs. Compute two labels from numbers, fastest and cheapest, and stop. Taste is the user's.
- **Same prompt.** Identical prompt text for every endpoint. Do not tune the wording per model; that turns a model comparison into a prompt contest. The only allowed difference is syntax a model requires (for example how references are cited), and it is listed under the table.
- **Same visible settings.** Equalise what the user can see: aspect or size, duration, resolution tier, audio on or off, one output per model. Leave model-internal knobs (steps, guidance, safety) at their defaults. Where a prompt-rewriting switch must be set, choose the value that leaves the prompt as written and say so.
- **Same task.** Compare text-to-image with text-to-image, image-to-video with image-to-video. An edit endpoint against a generation endpoint is not a comparison.
- **Two to four endpoints.** More than four: ask the user to narrow it (this is the skill's one question) or show the cost and let them confirm.
- **Named models are final.** Do not add, drop or swap a model the user named. One of them is not `active`: say so, propose the successor, and let them decide.
- **The gate covers the whole batch.** Sum every job before the first submit.

## 2. Choosing the endpoints

- The user names them: translate marketing names or stale IDs ([discovery.md](discovery.md) §3 and §4), keep the set.
- The user says "compare the top models for X": take the routing row for the task and use `default`, `budget` and the first alternate that the row ties to an arena rank. Three models, three price points.
- A user-supplied image, clip or audio file is uploaded **once** and the same URL goes into every job:
  ```bash
  gm.py upload ./input.png
  ```
  Tell the user first that uploaded inputs sit on a public, expiring URL when the material looks personal or confidential.

## 3. Build one input per endpoint

For each endpoint read `genmedia schema <endpoint_id> --format openapi --json` and express the shared settings in that endpoint's own fields. Parameter names do not transfer.

| Shared setting | Shows up as | Rule |
|---|---|---|
| Frame shape, stills | `image_size` (preset or `{width,height}`) on some models, `aspect_ratio` plus `resolution` on others | Passing the field a model does not have raises no error and changes nothing: use the one in its schema. Pick pixel sizes that satisfy every model's constraints (multiples of 16, area bounds). |
| Duration | integer, string enum (`"5"`), or suffixed (`"8s"`) | Use the nearest allowed value per model; never leave `auto`. Report differences under the table. |
| Resolution tier | `720p`, `768P`, `1K` ... | Nearest tier per model; case matters. |
| Audio | `generate_audio`, `generate_audio_switch`, or not switchable | Set it the same everywhere it can be set. It changes the price tier on some families. |
| Outputs per model | `num_images`, `num_samples`, `num_results` | 1, unless the user asked for variations. |
| Output format | `output_format` | The same value where every model offers it (`png` for anything with text). |
| Start image, references | `image_url`, `start_image_url`, `image_urls`, `reference_image_urls` ... | Same uploaded URL, each model's own field. |
| Seed | `seed` | Irrelevant across different models; leave it out. |

Video default when the user gave no settings: about 5 s, the 720p-class tier, audio off unless speech is the point. Lower tiers hide the differences a comparison is meant to show; if the total crosses the confirmation threshold, offer the 480p-class variant in the same sentence as the estimate.

## 4. Estimate and gate

1. Price all endpoints in one call and work out one figure per job for the exact settings ([cost-estimation.md](cost-estimation.md)):
   ```bash
   gm.py price <endpoint_id>,<endpoint_id>,<endpoint_id>
   ```
2. Put each figure into its job as `est_cost_usd`; the helper records it in the ledger and sums it.
3. Sum the batch. Under $0.50: run. $0.50 to $2: one line ("Comparing three models, about $0.85 in total."), then run. $2 or more: show the per-model figures and the total, wait for an explicit yes. Thresholds come from `.genmedia/config.json` when present.
4. An approval covers the batch that was shown. Adding a model or raising resolution afterwards needs a new one.
5. Say the concurrency consequence only when it matters: a new fal account runs two jobs at a time, so four video jobs take about two rounds.

## 5. Plan file and run

Write the plan with the Write tool (no shell quoting of prompts) to `.genmedia/tmp/compare-<slug>.json`. Job `id` is a short model slug: it becomes the file name and the ledger key. Shape, with fields verified on 2026-09-19 for these three endpoints (estimates are illustrations, price yours today):

```json
{"label": "compare-<slug>", "max_parallel": 2, "jobs": [
  {"id": "seedream-5-pro", "endpoint_id": "bytedance/seedream/v5/pro/text-to-image", "est_cost_usd": 0.07,
   "input": {"prompt": "<same prompt>", "image_size": {"width": 1536, "height": 864}, "num_images": 1, "output_format": "png"}},
  {"id": "gpt-image-25-flare", "endpoint_id": "openai/gpt-image-2.5/flare/text-to-image", "est_cost_usd": 0.06,
   "input": {"prompt": "<same prompt>", "image_size": {"width": 1536, "height": 864}, "num_images": 1, "quality": "high", "output_format": "png"}},
  {"id": "nano-banana-2", "endpoint_id": "fal-ai/nano-banana-2", "est_cost_usd": 0.08,
   "input": {"prompt": "<same prompt>", "aspect_ratio": "16:9", "resolution": "1K", "num_images": 1, "output_format": "png"}}
]}
```

```bash
gm.py batch --plan .genmedia/tmp/compare-<slug>.json
```

- `max_parallel: 2` keeps jobs from queueing behind each other on a new account, which would inflate the time column. Raise it only when the user knows their concurrency limit is higher.
- Files land in `genmedia-output/compare-<slug>/<job id>_{index}.<ext>`.
- Give the Bash call a 600000 ms timeout; the helper polls for up to 540 s.
- Exit code 1 with a JSON result means at least one job failed; the other jobs are complete. Read `jobs[]` and deliver.
- `status: "pending"` with a `resume` line: run the identical command again later. Jobs with a recorded request ID are resumed, never resubmitted. Do not edit the plan between the two runs.
- Wait silently. At most one status line for the whole batch.

## 6. Reading the result

Batch result: `jobs[] {id, status, endpoint_id, outputs[{path,url}], result, error?}`, `counts`, `est_cost_usd`, `gallery_url`.

| Column | Source |
|---|---|
| Model | display name from the routing row or `genmedia models`, not the raw ID |
| Output | pixel size from `.result` (`images[0].width` and `height`) when present; otherwise probe the local file (`ffprobe` when preflight found ffmpeg); otherwise the requested setting marked "requested". Add duration for video and audio. |
| Time | per job from the ledger: `gm.py ledger --label compare-<slug> --tail 10`, `updated` minus `ts`, in seconds. It is submit-to-result wall-clock: queue wait and cold start included, polling step of 2 to 15 s. |
| Est. cost | the job's `est_cost_usd`. It is an estimate; the CLI never reports the charge. |
| File | local path first. CDN URLs go below the table. |

Labels:

- **Fastest**: lowest time among completed jobs. If the two lowest differ by less than 15 s, write "similar speed" instead; the measurement cannot resolve it.
- **Cheapest**: lowest estimate among completed jobs; name both on a tie.
- One run is one sample. Write "in this run", never "is faster".
- After an image batch, check `.result.has_nsfw_concepts` and look at each file: a black frame is a filter hit, not an output ([platform.md](platform.md) §3).

## 7. Delivery template

Translate the fixed words; keep names, numbers and paths.

```
Comparison: "<prompt, first ~80 characters>" (<shared settings, e.g. 16:9, png, one image each>)

| Model | Output | Time | Est. cost | File |
|---|---|---|---|---|
| <Display name> | <W>x<H> <ext> | <n> s | $<x> | <local path> |
| <Display name> | <W>x<H> <ext> | <n> s | $<x> | <local path> |
| <Display name> | failed: <reason in plain words> | - | <$0 or "may have been billed"> | - |

Fastest in this run: <model> (<n> s). Cheapest: <model> ($<x>).
Total: about $<sum> (estimate). Gallery: <gallery_url>
Links (public to anyone who has them, may expire): <model>: <url> | <model>: <url>
Not identical: <settings that could not be equalised, or "nothing">.
Which one do you prefer? I can carry on with it.
```

Then stop. The next step (more variations, an edit, image-to-video) belongs to the skill for that modality, with the chosen endpoint ID handed over.

If the user asks what *you* see, answer with checkable observations per file, not a ranking: is the requested text spelled correctly, is the aspect as asked, is every requested object present, are there visible artifacts, does the clip hold the subject's identity to the last frame. Look at the files before saying anything; never describe an output you did not open.

## 8. Failures inside a batch

| Situation | Do |
|---|---|
| One job `failed` with `kind: "validation"`, `http_status: 422`, empty `fields` and a `hint` | Batch jobs are queued, and the CLI reports **every** provider-side failure of a queued job this way: a bad input, a filter hit, an unreachable input URL, "no media generated". Such a job can look finished in the queue and still have failed; the helper already reports it as `failed`. Compare that job's input with its OpenAPI schema. It differs: fix it and rerun with `--retry-failed` (completed jobs are untouched; counts toward the three-attempt limit). It matches: treat it as a runtime failure, write "failed at the provider, may have been billed" in the row, point to https://fal.ai/dashboard/requests, and do not resend it unchanged. |
| A black image, `has_nsfw_concepts` true, or a runtime failure on a prompt that plausibly trips a filter | Keep the row as "blocked by this model's filter". Do not reword the prompt for that model alone: it would no longer be the same prompt. Offer to rerun the whole set with a revised prompt (new label, new cost). |
| `kind: "server"` or `rate_limit` | Not billed for 5xx. Rerun once with `--retry-failed`. Second failure: keep the row as failed and say the provider is failing. |
| `kind: "not_found"` | The ID died between verification and run. Row says "not available"; do not substitute silently. |
| `kind: "auth"` | Stop the whole flow; the user fixes the key or balance. |
| `pending` after the timeout | Rerun the same command later. Never cancel and resubmit a queued job: it loses its place and risks paying twice. |
| A download failed (`path: null`) | Fetch the row's `url` with `curl -L -o <path> <url>`; the job itself succeeded. |

A comparison with a failed row is still delivered: the completed rows are what the user paid for.
