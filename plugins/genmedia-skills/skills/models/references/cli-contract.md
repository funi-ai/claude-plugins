<!-- GENERATED from shared/references/cli-contract.md — edit the source, then run scripts/sync_shared.py -->
# genmedia CLI contract

How every skill calls fal's `genmedia` CLI. Verified live on 2026-09-19 against genmedia v0.7.0. Use the `gm.py` helper first; the raw CLI is the fallback when `python3` is missing. Platform behaviour (URLs, billing, error types, cost gate) is in [platform.md](platform.md).

## Rules

1. Endpoint ID is the first token after `run`. Never `genmedia run "<prompt>"`: smart routing picks stale or broken defaults.
2. Always pass `--json`. Parse stdout only. Keep stderr separate (shells print noise there); never `2>&1 | jq`.
3. Never `--key=value` for model parameters or `--download`. Always `--key value`.
4. Free text (`prompt`, `negative_prompt`, `text`, `lyrics`, ...) goes in as a JSON string literal. The CLI JSON-parses every value: `2001` becomes a number, `true` a boolean, `""` a bare flag, `--ar 16:9` another flag, a JSON-looking prompt an object.
5. Arrays and objects are compact JSON. Repeated flags overwrite, comma lists stay strings, dotted keys and `--no-x` do not exist (`--x false`).
6. Files are never uploaded implicitly. Upload first, read `.cdn_url` (not `.url`), pass the URL.
7. Model output is under `.result` (`.result.images[0].url`, `.result.video.url`, ...). Check the schema for the exact keys.
8. `--download <template>` goes last. Placeholders: `{index}` (0-based), `{name}`, `{ext}`, `{request_id}`. Existing files are never overwritten (`_1`, `_2` suffixes).
9. Anything slower than a few seconds: `--async`, write down the `request_id` at once, poll bare `status` until `COMPLETED`, then `status --download` once. Never ask for `--result`/`--download` earlier.
10. `COMPLETED` is not success. A failed job surfaces when the result is fetched. Never resubmit to "check"; a new submit is a new billable job.
11. A cancel acknowledgement is not a terminal status.
12. Never read, print or pass the API key. Key missing: the user runs `genmedia setup` or exports `FAL_KEY` themselves.

## Calls that do not prompt

A skill pre-approves its helper scripts, the free `genmedia` commands, `Read` and edits under `.genmedia/`. Anything else asks the user for permission, or is refused in a headless session. Observed in paid end-to-end runs on 2026-09-20:

- No `mkdir`. The Write tool creates parent folders; `gm.py` creates `.genmedia/` and the download folders itself.
- Fields, enums and limits come from `gm.py schema <endpoint_id>`, which reads the OpenAPI schema for you. Run `genmedia models` and `genmedia pricing` bare. Never pipe a `genmedia` command into `python3 -c`, `jq` or a redirect to filter it: that pipe is refused in default permission mode, and reading the raw schema instead costs 10 to 20 KB of context per endpoint.
- Read reference files and images with the Read tool, not `cat`, `grep` or `ls` on the plugin folder.
- Pricing text comes from `gm.py price <ids> --explain`, never from WebFetch or `curl` on `llms.txt`.
- One command per Bash call. Never a `for` loop, a `&&` chain with `mkdir` or `cp`, a `printf ... >` or `echo ... >` redirect, or an environment prefix (`GENMEDIA_SESSION_ID=... genmedia ...`): none matches a pre-approval, so each prompts. Run the command once per file instead, and use `gm.py gallery` for this project's gallery page.
- Text files a local tool reads (an ffmpeg concat list, a plan, a script) are written with the Write tool under `.genmedia/tmp/` or `.genmedia/projects/<slug>/`, never under `genmedia-output/`: only `.genmedia/` is pre-approved for edits. `genmedia-output/` is for media the helpers and ffmpeg write.

## Helper: `gm.py`

Python 3.8+, stdlib only. Call it as `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" <command>`; the examples below shorten that to `gm.py`. Every command prints one compact JSON object on stdout. Exit codes: `0` ok (including `pending`), `1` failed, `2` usage error (nothing was sent). It runs the CLI without a shell, applies rules 1-11, and sets `GENMEDIA_SESSION_ID` to the project directory name unless it is already set.

```bash
gm.py preflight                       # free: CLI >= 0.7.0, key works, jq, ffmpeg+drawtext, fal Assets, stock skills
gm.py schema fal-ai/flux/schnell      # free: input fields with enums and limits, output names
gm.py price fal-ai/flux/schnell       # free: unit prices, comma-separate several IDs
gm.py upload ./product.png ./logo.png # -> .files[].cdn_url, .urls[]
gm.py gallery                         # free, local: this project's gallery page, opens nothing
```

`schema` is the discovery call before the first paid job on an endpoint. It makes one free `genmedia schema <id> --format openapi --json` call and folds it into a compact object, so the raw 10-20 KB document never has to be read and never has to be piped anywhere:

```bash
gm.py schema fal-ai/flux/schnell                  # -> {input:[...], output:[...]}
gm.py schema fal-ai/flux/schnell --field image_size  # one field, with its description and nesting
```

`$ref`, `anyOf`, `oneOf` and `allOf` are resolved: `image_size` comes back as `type:"object|string"` with both its enum and its `{width,height}` properties, where the short `genmedia schema <id> --json` view only says `type:"unknown"` and drops every limit. Required fields come first, then fal's own playground order. Descriptions are left out of the list; `--field <name>` prints that one field in full. Output names are paths inside `.result` (`images[].url`, `video.url`), which is what rule 7 needs.

Run one job. Write the model input as a JSON object, from a file or a quoted heredoc (no shell expansion, no escaping):

```bash
gm.py run fal-ai/flux/schnell --input - --label boat-demo --est-cost 0.003 <<'JSON'
{"prompt": "2001: a \"paper\" boat -- on a puddle, macro photo", "image_size": "square_hd", "num_images": 1}
JSON
```

| Option | Meaning |
|---|---|
| `--input <file.json\|->` | JSON object, UTF-8. `null` values are skipped. A lone surrogate (half an emoji) is refused. `*_url`/`*_urls` values must be `https://` or `data:`; keys `async`, `json`, `help`, `logs`, `download` cannot be sent. |
| `--download <template>` | Default `genmedia-output/<label>/<label>_<last 8 of request_id>_{index}.{ext}`. `--no-download` fetches the result JSON only. A template must not start with `-`. |
| `--label <slug>` | Groups ledger lines and the output folder. Default `adhoc`. |
| `--est-cost <usd>` | Your estimate (finite, >= 0), recorded in the ledger. |
| `--timeout <s>` | Polling budget, finite and >= 0, default 540 (under the 600 s Bash ceiling). Backoff 2 s to 15 s. Give the Bash tool call a longer timeout than this (600000 ms), or lower it to fit. |
| `--async` | Submit, record, return `status:"submitted"` immediately. |

Success: `{ok:true, status:"completed", endpoint_id, request_id, label, outputs:[{path,url,json_path}], result:{...}, gallery_url, est_cost_usd, elapsed_s}`. A file that failed to download appears in `outputs` with `path:null` and `error`; fetch its `url` with `curl -L -o`.
`outputs` is written to the ledger, so it outlives the process. Besides the downloaded files it carries every media URL left in the result: file objects with a `url`, and bare strings under a `url`/`*_url`/`*_urls` key, which `--download` ignores (`fal-ai/ffmpeg-api/compose` answers `video_url` that way). Those keep `path:null` in result order; save one with `pipeline.py fetch --label <slug> --step <job id> --out <path>`, which reads the URL from the ledger. A URL that was already in the job's input is an echo, not an output, and is left out.
A result over 16 KB of JSON (word timings, long transcripts) is written to `.genmedia/results/<label>_<request id tail>.json`; the output then carries `result_path` and `result_bytes` instead of `result`. Read or pipe that file (`audiokit.py captions` follows `result_path` by itself). Never rerun a paid job to see its result again: `gm.py wait <endpoint_id> <request_id>` returns the same `result_path` for free.

Timeout: `{ok:true, status:"pending", queue_status, request_id, resume:"python3 \"<skill dir>/scripts/gm.py\" wait <endpoint_id> <request_id>"}` with exit 0. The `resume` value is a whole command line in the pre-approved form (absolute path, quoted): run it as printed, do not shorten it. The job keeps running. Resume it; never submit it again. The same `pending` + `resume` shape, with the error fields and exit 1, comes back when the job reached `COMPLETED` but the result could not be fetched for a local reason (network, timeout, 401/403/429): the job is not recorded as failed, run `wait` again. On SIGTERM or Ctrl-C the helper still prints this shape with an `interrupted` entry in `warnings[]`. If the tool call itself was killed, `gm.py ledger --tail 5` still has the `request_id`:

```bash
gm.py wait fal-ai/flux/schnell <request_id>      # label and template come from the ledger
gm.py cancel fal-ai/flux/schnell <request_id>    # -> status:"cancel_requested", terminal:false
```

`wait` on a job the ledger already shows as completed (files still on disk) answers from the ledger with `resumed:true` and downloads nothing twice. `wait --refetch` asks the queue for the result again instead (free, never a resubmission; add `--no-download` to skip the files): the way back to a URL the ledger did not record. It also accepts a `request_id` that was submitted with the raw CLI. `cancel` on a finished job fails with `http_status:400` and `ALREADY_COMPLETED` in `message`; after a successful cancel, run `wait` later or check https://fal.ai/dashboard/requests to learn what really happened.

Batch: independent jobs, at most `max_parallel` in flight, one bounded wait, per-job failure isolation.

```bash
cat > plan.json <<'JSON'
{"label": "boat-demo", "max_parallel": 4, "jobs": [
  {"id": "shot1", "endpoint_id": "fal-ai/flux/schnell", "est_cost_usd": 0.003,
   "input": {"prompt": "a paper boat, macro", "image_size": "square_hd"}, "download": "shots/shot1_{index}.{ext}"},
  {"id": "shot2", "endpoint_id": "fal-ai/flux/schnell", "est_cost_usd": 0.003,
   "input": {"prompt": "a paper boat, aerial view", "image_size": "square_hd"}}
]}
JSON
gm.py batch --plan plan.json            # options: --timeout 540, --max-parallel N (overrides the plan), --retry-failed
```

Result: `{ok, status:"completed|pending|failed", label, counts:{completed,failed,pending,not_submitted}, est_cost_usd, elapsed_s, jobs:[{id, status, endpoint_id, request_id, outputs, result, error?, resumed?, input_changed?}], gallery_url, resume?}`. Exit 1 when any job has an error; the other jobs still finish. The whole plan is validated before the first submit. Default template per job: `genmedia-output/<label>/<id>_{index}.{ext}`; `"download": false` skips files.

Resume rule: a job `id` that already has a `request_id` in the ledger under the same `label` is resumed, never resubmitted. Run the same command again after `pending`. To redo a failed id after changing its input, add `--retry-failed`; the flag never touches an id whose job is pending, cancelled-but-not-terminal or completed (a cancel acknowledgement does not stop the job or the billing, so a cancelled id is resumed until fal reports it terminal, and only a failed one can be redone); to redo a completed one, use a new `id`. `input_changed:true` means the recorded request used a different input than the plan now holds.

Ledger: `.genmedia/runs.jsonl`, append-only, one `submitted` line per request written before the first poll (`ts, label, job_id, endpoint_id, request_id, status, input, download, est_cost_usd`), then `completed` (`outputs[{path,url,json_path}]`), `failed` (`error{kind,http_status,message}`, written only when fal reported the failure) or `cancel_requested`. A submit that ended without a `request_id` although it may have been accepted (exit 0 without JSON, a call that hung for 120 s, an interrupt) writes a `submit_unknown` line without `request_id` and returns `message:"submission state unknown ..."`: check https://fal.ai/dashboard/requests before submitting again. `batch` reports such an id as `failed` and resubmits it only with `--retry-failed`.

```bash
gm.py ledger --tail 5                 # merged per request, newest last; --full adds inputs, --label filters
gm.py ledger --sum                    # est_cost_usd total and per status
```

`--sum` returns `est_cost_usd` (every request in the ledger, failed and unfinished ones included) and `est_cost_usd_completed` (finished requests only). Quote `est_cost_usd_completed` as the spend in checkpoint and delivery lines; name the gap when failed requests make the two differ. Both are estimates; real charges are on https://fal.ai/dashboard/billing.

Other shapes:

| Command | Output |
|---|---|
| `preflight` | `{ok, genmedia:{found,version,ok}, key:{present,valid}, python, jq, ffmpeg:{found,drawtext}, assets:{enabled:true\|false\|"unknown", reason?}, stock_skills:[{name,path}], session:{name,source}, config:{path,exists,announce_above_usd,confirm_above_usd}, blockers:[], warnings:[]}`. Exit 1 when `blockers` is non-empty. Two free network calls (`pricing`, one `assets browse`); `--no-network` skips both. |
| `upload` | `{ok, files:[{source,cdn_url,error?}], urls:[...]}`; exit 1 if any file failed. |
| `gallery` | `{ok, session, url, path, exists}` from one local `genmedia gallery open current --print --json` under the helper's session. `exists:false` only means nothing was fetched in this session yet. |
| `schema` | `{ok, endpoint_id, category, input:[{name,type,required,default?,enum?,minimum?,maximum?,minLength?,maxLength?,minItems?,maxItems?,exclusiveMinimum?,exclusiveMaximum?,items?,properties?}], output:[names], note}`. `--field <name>` answers `{ok, endpoint_id, category, field:{...,description}}` instead; an unknown name is a usage error that lists the real ones (exit 2, no second call). `type` joins the branches of an `anyOf` (`object|string`) and is `unknown` only when the document says nothing. Nesting is expanded three levels deep. |
| `price` | `{ok, prices:[{endpoint_id,unit_price,unit,currency,needs_llms_txt,llms_txt,pricing_text?}], missing:[ids]}`. `needs_llms_txt:true` for every unit except per image/second/minute/video/request/generation/characters (so: `megapixels`, `units`, `1000 tokens`, `compute seconds`): rerun with `--explain`, which fetches the model's public `llms.txt` without credentials and adds its Pricing paragraph as `pricing_text` to every row (`null` when offline), and estimate from that text. Per-second and per-image models can have resolution or audio tiers that only this text shows; never fetch `llms.txt` with WebFetch or curl, it prompts for permission. |

### Helper errors

`{ok:false, kind, http_status, message, fields:[{field,type,message}], raw_tail, hint?}` plus `status`, `endpoint_id`, `request_id` when a job exists.

| `kind` | Meaning | Do |
|---|---|---|
| `usage` | Bad arguments or input; nothing was sent (exit 2). | Fix the call. |
| `cli_missing` | `genmedia` not on PATH. | Send the user to `/genmedia-skills:setup`. |
| `auth` | 401/403, no key, locked balance, feature not enabled. | Stop. The user fixes the key or account. |
| `not_found` | Unknown endpoint, request or file. | Re-check the ID with `genmedia models --endpoint_id <endpoint_id> --json`. |
| `validation` | 422. | Fix the input; see the limit below. Never resend unchanged. |
| `content_policy` | A field has type `content_policy_violation`. | Change the prompt or input; never resend unchanged. |
| `rate_limit`, `server` | 429, 5xx. | Wait, then `wait`/rerun the batch; never blind-loop. |
| `still_running` | Result requested too early (the helper handles it itself). | `gm.py wait`. |
| `unknown` | Anything else. | Read `message` and `raw_tail`. |

Limit of queued jobs: the CLI reports a failed `--async` job as a non-JSON crash dump in which fal's `detail` list is truncated to `[Object ...]`. The helper then returns `kind:"validation"`, `http_status:422`, `fields:[]` and a `hint`; the field name and error type (including `content_policy_violation`) are not recoverable from the CLI. Compare the input with `gm.py schema <endpoint_id>`; if it matches, treat it as a runtime model error (content policy, unreachable or oversized input file, no media generated) and check https://fal.ai/dashboard/requests. To see field-level errors before spending on a media-input model, run it sync once with the required media field omitted: the schema-level 422 comes back as JSON, lists every other problem, and normally costs nothing (`platform.md` §5).

## Raw CLI fallback

Only when `python3` is missing. This path is meant to ask for permission: none of it is pre-approved.

<!-- prompts:ok -->
```bash
PROMPT='2001: a "paper" boat -- on a puddle'
PROMPT_JSON=$(printf '%s' "$PROMPT" | jq -Rs .)        # without jq: --prompt '"plain text without quotes"'
URL=$(genmedia upload ./product.png --json 2>/dev/null | jq -r .cdn_url)   # for models with a *_url input: --image_url "$URL"
mkdir -p .genmedia
genmedia run fal-ai/flux/schnell --prompt "$PROMPT_JSON" --image_size square_hd --num_images 1 --async --json > submit.json 2> submit.err
REQ=$(jq -r .request_id submit.json); echo "$REQ fal-ai/flux/schnell" >> .genmedia/requests.txt
for i in $(seq 1 55); do                                # bounded: stays under the 600 s Bash ceiling
  STATUS=$(genmedia status fal-ai/flux/schnell "$REQ" --json 2>/dev/null | jq -r '.status // "UNKNOWN"')
  [ "$STATUS" = "COMPLETED" ] && break; sleep 8
done
[ "$STATUS" = "COMPLETED" ] && genmedia status fal-ai/flux/schnell "$REQ" --json --download "genmedia-output/boat-demo/boat_{index}.{ext}" > result.json 2> result.err
```

If the last call exits non-zero, the job failed and `result.err` holds the non-JSON reason. If the loop ends without `COMPLETED`, keep `REQ` and poll again later; never resubmit.

Arrays and objects: `--image_urls '["https://a/1.png","https://a/2.png"]'`, `--image_size '{"width":1280,"height":720}'`. Numbers and booleans stay raw (`--num_images 2`, `--enable_safety_checker false`). fal coerces a JSON number into a string enum server-side, so `--duration 5` works where the schema says `"5"`. Check the exit code before parsing stdout: usage errors print help text on stdout. Sync `run` (no `--async`) prints nothing until it ends, has no timeout, and loses the `request_id` if the tool call is killed while the job keeps billing; use it only for calls that finish in seconds.

## CLI JSON shapes

| Call | stdout, exit 0 |
|---|---|
| `run <endpoint_id> ... --json` | `{status:"completed", endpoint_id, request_id, result:{...}, downloaded_files?:[{url,path,size_bytes,json_path}], download_failures?:[{url,json_path,error}], gallery?:{session_id,path,url}, logs?}` |
| `run ... --async --json` | `{status:"submitted", request_id, endpoint_id, hint}`; `--download` is ignored here |
| `status <endpoint_id> <request_id> --json` | `{status:"IN_QUEUE"\|"IN_PROGRESS"\|"COMPLETED", request_id, queue_position?, logs?}` (uppercase) |
| `status ... --json --download <template>` or `--result` | same as sync `run` (lowercase `completed`); every call adds a gallery entry |
| `status ... --cancel --json` | `{status:"cancelled", request_id}`; bare `status` may keep saying `IN_PROGRESS` |
| `upload <path\|url> --json` | `{cdn_url, hint}`; one file per call |
| `pricing <id>[,<id>...] --json` | `{prices:[{endpoint_id,unit_price,unit,currency}], next_cursor, has_more}`; one unknown ID fails the whole call (404) |
| `models --endpoint_id <id> --json` | `{status, endpoint_ids, count, has_more, models:[{endpoint_id,name,category,status,description,...}]}`; unknown ID: exit 1 `Failed (404)`; several IDs return at most `--limit` rows (default 20), so pass `--limit` at or above the ID count |
| `schema <endpoint_id> --json` | `{endpoint_id,name,category,input:[{name,type,required,description,default,enum?}],output:[...]}`; `type:"unknown"` hides enums and nested objects and no limit survives, so `gm.py schema` reads `--format openapi` instead |
| `version --json` | `{version, update_available}` |
| `gallery open current --print --json` | `{scope,target,session_id,path,url,exists,opened,hint?}`; `exists:false` until a result was fetched in this session |

Errors, exit code always 1:

| Path | stderr |
|---|---|
| Handled error (sync `run` failure, `pricing`, `models`, `schema`, `assets`, missing key or file) | JSON `{error, details?}`. For `run`: `details:{endpoint_id, request_id, status, error_type, validation_errors:[{field,message,type,input}], body}`. For `pricing`/`models`, `details` is the HTTP body as a string. stdout is empty. |
| Thrown error (any `status` failure, fetching a failed or unfinished job, failed `--async` submit, upload/network errors) | Not JSON: minified source lines, then `ApiError: Bad Request` or `ValidationError: Unprocessable Entity`, `status: 400`, `body: { detail: "Request is still in progress", ... }`. Read `status:` and `detail:` with a regex. |
| Usage error | Help text on stdout, one line on stderr. |

## Environment

| Variable | Effect |
|---|---|
| `FAL_KEY` | API key; wins over `~/.genmedia/config.json`. Never echo it. |
| `GENMEDIA_SESSION_ID=<string>` | Pins the gallery session (the CLI hashes it to 12 hex chars). Must be set on every call; the helper does it. |
| `GENMEDIA_NO_GALLERY=1` | No gallery recording (`1` or `true`). |
| `GENMEDIA_NO_ANALYTICS=1` | No analytics (must be exactly `1`). |
| `NO_COLOR=1` | Plain help text. |
| `GM_GENMEDIA_BIN`, `GM_POLL_INITIAL`, `GM_POLL_MAX` | Helper only: binary override, poll backoff bounds in seconds (tests). |

## Gallery

Every fetched result (`run`, `status --result`, `status --download`) is recorded in a local HTML gallery, one per session, no server. The helper returns it as `gallery_url`. With the raw CLI use the same session name the helper uses:

```bash
GENMEDIA_SESSION_ID="$(basename "$PWD")" genmedia gallery open current --print --json
```

Give the user `.url` (a `file://` link) after multi-asset work. Drop `--print` only if the user asks you to open the browser. The gallery prefers downloaded local files, so always download; jobs fetched through `status` show no prompt.

## Free and paid

Free: `models`, `schema`, `pricing`, `docs`, `version`, `upload`, `gallery`, bare `status`, `status --cancel`, fetching a result, any `--help`, and all `gm.py` commands except `run` and `batch`. A schema-level 422 (missing field, bad enum, out of range) normally costs nothing; a 422 raised during processing may be billed (`platform.md` §5). Paid: every accepted `genmedia run` (sync or `--async`), so also `gm.py run` and `gm.py batch`. Estimate first (`gm.py price`), apply the cost gate in `platform.md`, and never resubmit a job that already has a `request_id`.
