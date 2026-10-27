# Troubleshooting pipelines

Read when a stage fails, hangs, resumes oddly, or when plan, ledger and files disagree. `gm.py` and `pipeline.py` abbreviate the calls shown in SKILL.md; run them from the project root. Helper error kinds are in `cli-contract.md` and platform error types in `platform.md` section 4. Behaviour below was checked against the helper code and its offline tests on 2026-09-19.

## Look before you touch anything (free, read-only)

```text
pipeline.py urls --label <slug>            # latest request per job id: status, URLs, paths, local assets
gm.py ledger --label <slug> --tail 20      # merged per request, newest last; --full adds inputs
gm.py ledger --label <slug> --sum          # estimated spend per status
```

Three sources, three meanings. The **ledger** is what was submitted and therefore paid for; never edit or delete its lines. The **files** under `genmedia-output/<slug>/` are the deliverable. **plan.md and the stage files** are intent. When they disagree, the ledger wins and the plan is corrected to match it, never the other way round.

Two rules hold in every case below: a job that has a `request_id` is resumed, not submitted again; and a fix touches one node, not the stage.

## A stage fails

| What the batch output shows | Cause | Do |
|---|---|---|
| Exit 2, `"kind":"usage"`, nothing sent | Bad plan: duplicate `id`, `download` inside `input`, a non-URL in a `*_url` field, invalid JSON | Fix the file. Nothing was billed. `'@kf01' is not a URL` means the template was run instead of the filled plan. |
| `"status":"failed"`, some jobs `completed` | Per-job isolation worked | Keep what landed. Repair only the failed ids (below). Later stages that do not consume the failed node may go on. |
| `"kind":"validation"`, `"fields":[]`, a `hint` | The CLI drops field details of queued jobs | Compare the input with `genmedia schema <endpoint_id> --format openapi --json`. Pipeline causes, most frequent first: an upstream URL that expired or is not fetchable; the wrong start-frame field name for this family; `duration` outside the enum or as `auto`; media over the model's limit (avatar audio of 60 s or more at 720p, an image above 30 MB); `image_size` outside the model's pixel range. |
| `"kind":"content_policy"`, or a black image with `has_nsfw_concepts` true | Filter hit, assume billed | Rewrite the flagged part plainly. Never resend unchanged, never switch the checker off. |
| `"kind":"not_found"` on submit | Endpoint retired since the plan was made | `genmedia models "<name>" --no-classify --limit 10 --json`, pick the newest active match, re-price. A swapped model is a new plan version. |
| `"kind":"auth"`; remaining jobs `not_submitted` | Key or balance; the helper stops submitting | Stop every stage. The user fixes it; then run the same command again. |
| `submission state unknown` | The submit call ended without a request ID but may have been accepted | Ask the user to look at https://fal.ai/dashboard/requests. Only when the job is not there: `--retry-failed`. |
| `"kind":"server"` or `"rate_limit"` | fal side, not billed | Wait a minute, rerun the same command once. A second failure: another model, and ask first if the user named this one. |

Repairing a failed id: edit that job in the stage template, run `pipeline.py fill` again, then `gm.py batch --plan <plan> --retry-failed`. The flag resubmits **every** id in that file whose last request failed, was cancelled or has an unknown submit state. When two ids failed and only one is fixed, the other is resent unchanged and may bill again: fix both, or write a plan file that contains only the repaired ids (same `label`, same `id`s). Three attempts per node, each different, then stop and explain.

Expired or unfetchable upstream URL: the local copy is the source. `gm.py upload <path>`, then `pipeline.py add --label <slug> --step <name> --path <path> --url <cdn_url>` under a new step name, point the template at `"@<name>"`, fill, retry. CDN URLs from an earlier session are the usual suspects on a resumed project.

## It hangs, times out or was interrupted

| Situation | Do |
|---|---|
| `"status":"pending"` with `resume` | Run the identical `gm.py batch --plan <plan>` again. It polls the recorded requests and submits only ids that never got a request ID. |
| The Bash tool call was killed (600 s ceiling) or the session ended | Same: rerun. Every request was written to the ledger before the first poll. Nothing is lost and nothing is paid twice. |
| A job with `"status":"pending"` plus an `error` whose `hint` says the result could not be fetched (batch exit 1) | The job reached `COMPLETED` but fetching failed for a local reason (network, 401, 429). It is not recorded as failed. Rerun the same command. |
| `queue_status` stays `IN_QUEUE` | Normal waiting at the account's concurrency limit. Never cancel and resubmit: that loses the place in the queue. |
| Some jobs change state on each rerun | Progress. Keep going; one status line to the user per rerun at most. |
| No job changed state in 6 consecutive reruns (about an hour) | Stop. Report what landed, offer to continue later. For an `IN_PROGRESS` job the user may want gone: `gm.py cancel <endpoint_id> <request_id>` (IDs from `gm.py ledger`). |

Cancel semantics: the answer is `status:"cancel_requested", terminal:false`. A queued job is removed; a running job may still finish and bill. After a cancel, do not use `--retry-failed` in the same turn. First run the plain batch command (or `gm.py wait <endpoint_id> <request_id>`) once more later: if the job completed after all, the result is fetched and nothing needs to be paid again. Resubmit only when the user confirms on the dashboard that the job ended without a result, or accepts the risk of paying twice.

## Plan, ledger and files disagree

| Symptom | Meaning | Do |
|---|---|---|
| `fill` reports `already_in_ledger: []` for a stage you know ran, or `urls` is empty | Wrong working directory or a changed `label` | Stop before `batch`: it would submit everything again. `cd` to the project root, use the original label. |
| `"input_changed":true` | The stage file was edited after that id ran; the file on disk is from the old input | Restore the input, or add a new id (`clip03-r2`) for the new one. |
| A delivered file was deleted or moved | The ledger still has the request | Rerun the stage plan: the helper fetches the result again at no cost while the CDN copy exists. If it is gone, a new id is the only way, and it costs. |
| `fill`: `job X is submitted, not completed` | The upstream stage is unfinished | Rerun that stage's plan first. Never paste a URL by hand. |
| `fill`: `job X has no output URL in the ledger` | A result with no URL at all under a `url`/`*_url` key (next section) | Read the result (`gm.py wait <endpoint_id> <request_id> --refetch --no-download`), then `pipeline.py fetch --url` or `add --url`, then fill again. |
| `fill`: `index N does not exist` | Fewer outputs than the template expects (`num_images`) | Check `pipeline.py urls`; fix the index or the upstream job. |
| Manifest: `output was not downloaded` | A download failed, or the result URL was a bare string the CLI cannot save | `pipeline.py fetch --label <slug> --step <id> --out genmedia-output/<slug>/<file>` (the job's own id as `--step` clears the problem; the URL comes from the ledger). Jobs planned with `"download": false` are not reported. |
| Manifest: `local file is missing` for a registered asset | A file registered with `add` or `fetch` was moved | Put it back, or `add` the new path under the same step (the later entry replaces the earlier one). |
| Manifest lists ids the plan does not have | Re-rolls, canaries, abandoned takes | Expected. Both takes stay; the plan log says which one was used. Note superseded failures at delivery. |
| Spend in `ledger --sum` above the plan | Re-rolls and repairs | Over 20 percent above the approved total is a new plan version: stop and ask. |

## Bare-string outputs that `--download` skips

`fal-ai/ffmpeg-api/compose` and `fal-ai/auto-caption` return `result.video_url` as a plain string. `--download` only saves file objects, so no file is written and the manifest reports `output was not downloaded`. The URL itself is not lost: the helper records every string under a `url`/`*_url`/`*_urls` key as an `outputs` entry with `path: null`, in result order, and writes it to the ledger.

1. Save it with the job's own id as `--step`, which is what clears the manifest problem: `pipeline.py fetch --label <slug> --step <id> --out genmedia-output/<slug>/<file>.mp4`. No `--url`: the URL, endpoint and request id come from the ledger. `--index 1` takes the second URL (compose: the thumbnail). `"@<id>"` resolves from the ledger whether or not the file was fetched, so a later stage can cite it either way.
2. Nothing in the ledger either - a job run before this rule, or a URL under a key the rule misses. Read the request ID with `gm.py ledger --label <slug> --tail 5` and ask the queue for the result again (free, never a resubmission):

   ```bash
   gm.py wait <endpoint_id> <request_id> --refetch --no-download
   ```

   Then pass the URL you read from `result` as `pipeline.py fetch --url`.
3. `fetch` never overwrites; pick a new `--out` for a second take. A `download failed` answer usually means the URL expired: the job must be run again under a new id.

## Assembly mismatches

Probe every part first (`assembly.md` A1). Most broken cuts come from parts that differ in one of four properties.

| Symptom | Cause | Fix |
|---|---|---|
| Local concat stutters, freezes, loses sync or stops after the first clip | `-c copy` on parts with different size, frame rate, codec or audio layout | Normalize every part with A2 (same size, `fps`, `yuv420p`, 48 kHz stereo), then A3. |
| Concat output is silent from some clip on | One part has no audio stream (clips made with `generate_audio` false, stills turned into clips) | A2 silent-clip variant adds a silent track to those parts. |
| `merge-videos` result is smaller or choppier than the clips | Defaults are the minimum width and height and the lowest frame rate across inputs | Pass `resolution` (each side 512-2048) and `target_fps` explicitly. Above 2048 px: local concat. |
| Black bars or stretched picture in the cut | Mixed aspect ratios. Image-to-video output follows the keyframe's shape | Give all keyframes one `image_size`; for existing clips A2 with pad or crop, or `scale-video` with `mode` set. |
| Clips came back at different sizes from the same model | Keyframes had different sizes, or some clips were upscaled and others not | Normalize after the upscale, not before. |
| Final is shorter than the picture | `-shortest` with an audio bed shorter than the cut | Build the bed to `DUR` (A4 pads the voice and trims the music). |
| Voice is cut off at the end, or the picture ends early | Measured voice is longer than the summed clip durations; with `merge-audio-video`, a sound shorter than the picture cuts the picture too | Long voice: add or lengthen the last clip (a still-to-clip hold, A8, is free), or trim the script; never speed the voice up silently. Short sound: pad it to the picture (A4) or trim the picture to it (A9). |
| Durations drift after crossfades | Each `xfade` shortens the total by its length | Recompute `DUR` after A10, before A4. |
| Timeline (`compose`) result has an unexpected size or length, a slowed or sped-up clip, or a voice that starts too early | Compose concatenates: output at the first clip's size and frame rate, other frame rates not converted, gaps and keyframe durations ignored, a later keyframe in an audio track follows the previous one without a gap (`assembly.md`, Timeline compose) | Trim and normalize every clip to one size and frame rate first, join the voice into one file, then compose again; or assemble locally. |
| Avatar chunks show a jump at each join | Separate generations start from the same portrait pose | Expected with chunked audio. Cut on sentence ends; a short crossfade (A10) hides it. |
| Captions soft or mis-scaled | Burned in before an upscale or a rescale | Captions are always the last step. |
