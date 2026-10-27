#!/usr/bin/env python3
# GENERATED from shared/scripts/gm.py — edit the source, then run scripts/sync_shared.py
"""gm.py - safe wrapper around fal.ai's `genmedia` CLI (>= 0.7.0). Python 3.8+, stdlib only.

Prints ONE compact JSON object on stdout. Exit: 0 ok (also "pending") | 1 failed | 2 usage.
Never prints, stores or forwards the API key (FAL_KEY is only tested for presence and scrubbed from
error text).

  preflight [--no-network]
      genmedia found/version, key present/valid (one free pricing call), python, jq, ffmpeg+drawtext,
      fal Assets enabled (one free read; 403 -> false), stock fal skills in the project, gallery
      session name, cost thresholds. Exit 1 when a blocker exists.
  upload <path-or-url>...
      -> {files:[{source,cdn_url}], urls:[...]}
  run <endpoint_id> --input <file.json|-> [--download <template> | --no-download] [--async]
      [--timeout 540] [--label <slug>] [--est-cost <usd>]
      Builds argv from a JSON object (strings -> JSON string literals, numbers/booleans raw,
      arrays/objects -> compact JSON, null skipped), submits with --async, writes the ledger line
      IMMEDIATELY, polls bare `status` with backoff, then calls `status --download` once.
      Timeout -> {status:"pending", request_id, resume}, exit 0. A job is NEVER resubmitted. A result
      that cannot be fetched for a local reason (network, timeout) also stays "pending", not "failed".
  wait <endpoint_id> <request_id> [--download <template> | --no-download] [--timeout 540] [--label <slug>]
      [--refetch]
      Resume polling; label and template default to what the ledger recorded. A job the ledger already
      shows as completed is answered from the ledger; --refetch asks the queue again instead (free,
      never a resubmission) and is the way back to a result this helper did not record. It re-downloads
      the files too unless --no-download is given.
  cancel <endpoint_id> <request_id>
      Request cancellation; the acknowledgement is NOT a terminal status.
  batch --plan <plan.json|-> [--timeout 540] [--max-parallel N] [--retry-failed]
      {"label":"slug","max_parallel":4,"jobs":[{"id":"shot1","endpoint_id":"owner/model",
       "input":{...},"download":"dir/shot1_{index}.{ext}","est_cost_usd":0.1}]}
      At most max_parallel jobs in flight; failures are isolated per job. A job id that already has a
      request_id in the ledger under the same label is resumed, never resubmitted (--retry-failed
      resubmits only ids whose last request FAILED or has an unknown submit state; a cancelled
      request is resumed until it is terminal, because a cancel ack does not stop the billing).
  schema <endpoint_id> [--field <name>]
      One free `genmedia schema --format openapi --json` call, folded into a compact object:
      {input:[{name,type,required,default,enum,minimum,maximum,maxLength,items,properties}],
       output:[dotted leaf names]}. $ref, anyOf, oneOf and allOf are resolved, so `image_size`
      shows both its enum and its {width,height} shape instead of the bare `type:"unknown"` the
      short `genmedia schema --json` prints. Required fields come first. Descriptions are left
      out; --field <name> prints that one input field with its description and full nesting.
  price <endpoint_id>[,<id>...] [--explain]
      One `genmedia pricing` call; needs_llms_txt:true marks units that cannot simply be multiplied
      (tokens, compute seconds, megapixels, "units"); each row carries the model's llms.txt URL.
      --explain also fetches that public page (no credentials are sent) and adds its Pricing
      paragraph as pricing_text to every row: per-second and per-image models have tiers
      (resolution, audio) that only the page describes.
  ledger [--tail N] [--sum] [--label <slug>] [--full]
      .genmedia/runs.jsonl merged per request.
  gallery
      This project's gallery page: one local `genmedia gallery open current --print --json` call under
      the same GENMEDIA_SESSION_ID the jobs ran with. Free, no browser, no key. {ok, session, url,
      path, exists}; exists:false only means nothing was fetched in this session yet.

Resume hints: a "resume" value is a whole command line, `python3 "<absolute path of this file>" wait ...`
  (or `... batch --plan <plan>`), which is the form skills pre-approve; a plan path that needs quoting is
  quoted. Run it as printed; the examples in this help shorten it to `gm.py`.
Errors: {ok:false, kind, http_status, message, fields:[{field,type,message}], raw_tail}; kind is
  validation|auth|not_found|rate_limit|content_policy|still_running|server|unknown (parsed from the
  CLI's stderr JSON or its non-JSON crash dump) or usage|cli_missing (raised by this helper).
Large results: a model result over 16 KB of JSON (word timings, transcripts) is written to
  .genmedia/results/<label>_<request id tail>.json and the output carries result_path and
  result_bytes instead of result. Read that file; NEVER rerun a paid job to see its result again
  (`gm.py wait <endpoint_id> <request_id>` returns the same result_path for free).
Outputs: every completed job records outputs[] in the ledger - the downloaded files, the ones whose
  download failed, and the media URLs left in the result, including bare strings under a `url`/`*_url`
  key that the CLI's --download ignores (fal-ai/ffmpeg-api/compose). A bare string keeps path:null; save
  it with `pipeline.py fetch --label <slug> --step <job id> --out <path>`. A URL that was already in the
  job's input is an echo, not an output, and is left out.
State in the project cwd: .genmedia/runs.jsonl (append-only), .genmedia/config.json (read only),
  .genmedia/results/ (large results); downloads default to ./genmedia-output/<label>/.
Env: GENMEDIA_SESSION_ID (gallery session; default = project directory name), GM_GENMEDIA_BIN
  (binary override), GM_POLL_INITIAL / GM_POLL_MAX (poll backoff seconds), GM_RESULT_INLINE_MAX
  (bytes of result JSON kept inline; default 16000).
"""
import argparse
import json
import math
import os
import platform
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import unicodedata
import urllib.request

MIN_VERSION = (0, 7, 0)
RESERVED_KEYS = {"async", "json", "help", "logs", "download"}  # CLI flags; cannot be model inputs
LEDGER, CONFIG = os.path.join(".genmedia", "runs.jsonl"), os.path.join(".genmedia", "config.json")
DEFAULT_TIMEOUT = 540.0          # stays under Claude Code's 600 s Bash ceiling
CALL_TIMEOUT, FETCH_TIMEOUT, UPLOAD_TIMEOUT = 120, 300, 600
MAX_TOKEN_BYTES = 120000         # Linux caps a single argv element at 128 KiB
MAX_POLL_ERRORS = 5
RESULTS_DIR = os.path.join(".genmedia", "results")
RESULT_INLINE_MAX = 16000        # a bigger result floods the agent's context and cannot be read back
KEY_PROBE_ID = "fal-ai/flux/schnell"  # `pricing` is free and needs a valid key
SIMPLE_UNITS = {"image", "images", "second", "seconds", "minute", "minutes", "video", "videos",
                "request", "requests", "generation", "generations", "character", "characters",
                "1000 characters"}
TR_ASCII = str.maketrans("ıİşŞğĞüÜöÖçÇ", "iIsSgGuUoOcC")  # labels become file and folder names
DASHBOARD = "https://fal.ai/dashboard/requests"
ENDPOINT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9._-]+)+")
URL_KEY_RE = re.compile(r"(^|_)urls?$")  # url, video_url, image_urls: keys that name media
PLUMBING_KEYS = {"status_url", "response_url", "cancel_url", "logs_url", "webhook_url"}  # never media
STATUS_KINDS = {401: "auth", 403: "auth", 404: "not_found", 422: "validation", 429: "rate_limit"}
WARNINGS = []                    # problems that must not stop a paid job; added to the final JSON


class GmError(Exception):
    def __init__(self, payload, code=1):
        super().__init__(payload.get("message", ""))
        self.payload, self.code = payload, code


def usage(message):
    return GmError({"ok": False, "kind": "usage", "message": message}, 2)


def self_call():
    """Canonical invocation of this file, the one a skill pre-approves: `python3 "<absolute path>"`.

    Hints must be runnable as printed. `python3` stays literal (sys.executable can be a venv path or a
    bare `python` that no permission rule matches) and the path is quoted because ${CLAUDE_SKILL_DIR}
    may contain spaces; a path with a double quote in it would not be quotable, so it falls back to the
    directory-independent form.
    """
    path = os.path.abspath(__file__)
    return "python3 gm.py" if '"' in path else 'python3 "%s"' % path


# ---------------------------------------------------------------- CLI plumbing
def session_name():
    return os.environ.get("GENMEDIA_SESSION_ID") or os.path.basename(os.getcwd()) or "genmedia"


def cli(args, timeout=CALL_TIMEOUT):
    """Run genmedia without a shell. Returns (exit_code, stdout, stderr)."""
    binary = shutil.which(os.environ.get("GM_GENMEDIA_BIN") or "genmedia")
    if not binary:
        raise GmError({"ok": False, "kind": "cli_missing",
                       "message": "genmedia CLI not found on PATH (see /genmedia-skills:setup)"})
    env = dict(os.environ, GENMEDIA_SESSION_ID=session_name(), NO_COLOR="1")
    try:
        proc = subprocess.run([binary] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              stdin=subprocess.DEVNULL, env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, "", "gm.py: genmedia call timed out after %s s" % timeout
    except OSError as exc:
        return 127, "", "gm.py: cannot execute genmedia: %s" % exc
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


def parse_json(text):
    """Parse a JSON document, tolerating non-JSON noise around it. None when there is none."""
    text = (text or "").strip()
    try:
        return json.loads(text)
    except ValueError:
        pass
    fallback = None
    for match in re.finditer(r"^[{\[]", text, re.M):
        try:
            doc = json.JSONDecoder().raw_decode(text[match.start():])[0]
        except ValueError:
            continue
        if isinstance(doc, dict):
            return doc  # shell noise such as "[1]" must not hide the real document
        fallback = doc if fallback is None else fallback
    return fallback


def parse_object(text):
    doc = parse_json(text)
    return doc if isinstance(doc, dict) else {}


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def redact(text):
    key = os.environ.get("FAL_KEY") or ""
    if len(key) >= 8:
        text = text.replace(key, "[REDACTED]")
    text = re.sub(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}:[0-9a-f]{16,}\b", "[REDACTED]", text, flags=re.I)
    return re.sub(r"\bKey\s+[A-Za-z0-9_-]+:[A-Za-z0-9_-]+", "Key [REDACTED]", text)


def raw_tail(stdout, stderr):
    text = stderr.strip() or stdout.strip()
    heads = list(re.finditer(r"^\w*Error\b.*$", text, re.M))
    if heads:  # drop the minified source lines Bun prints above the error
        text = text[heads[-1].start():]
    text = "\n".join(line[:300] for line in text.splitlines() if line.strip())
    return redact(text[:800] if heads or text.startswith("{") else text[-800:])


def normalize_error(stdout, stderr, code=1):
    """Map the CLI's stderr JSON, or its non-JSON crash dump, onto one error shape."""
    status, message, etype, fields = None, "", "", []
    doc = parse_json(stderr)
    if isinstance(doc, dict) and "error" in doc:
        message, details = str(doc["error"]), doc.get("details")
        if not isinstance(details, dict):  # `pricing`/`models` pass the HTTP body through as text
            details = parse_object(details if isinstance(details, str) else "")
        status = details["status"] if isinstance(details.get("status"), int) else None
        inner = details["error"] if isinstance(details.get("error"), dict) else {}
        if inner.get("message"):
            message = "%s: %s" % (message, inner["message"])
        etype = str(inner.get("type") or details.get("error_type") or "")
        fields = [{"field": v.get("field"), "type": v.get("type"), "message": v.get("message")}
                  for v in details.get("validation_errors") or [] if isinstance(v, dict)]
    else:  # Bun inspection of an ApiError/ValidationError, a usage text, or a note from cli()
        found = re.search(r"^\s*status:\s*(\d{3})\b", stderr, re.M)
        status = int(found.group(1)) if found else None
        heads = re.findall(r"^(\w*Error): (.*)$", stderr, re.M)
        etype, message = heads[-1] if heads else ("", "")
        found = (re.search(r'\bdetail:\s*"((?:[^"\\]|\\.)*)"', stderr)
                 or re.search(r'\bmessage:\s*"((?:[^"\\]|\\.)*)"', stderr))
        message = found.group(1) if found else message
        found = re.search(r'^\s*status:\s*"(\w+)"', stderr, re.M)  # e.g. NOT_FOUND, ALREADY_COMPLETED
        if found:
            message = ("%s (%s)" % (message, found.group(1))).strip()
        if not message:
            lines = [line.strip() for line in stderr.splitlines() if line.strip()]
            message = lines[-1][:300] if lines else "genmedia exited with code %s" % code
    if status is None:
        found = re.search(r"\((\d{3})\)", message)  # "Pricing fetch failed (404)"
        status = int(found.group(1)) if found else None
    low = message.lower()
    if "content_policy" in low or "content_policy_violation" in stderr or any(f["type"] == "content_policy_violation" for f in fields):
        kind = "content_policy"
    elif "still in progress" in low:
        kind = "still_running"
    elif fields or etype == "ValidationError":
        kind = "validation"
    elif status in STATUS_KINDS:
        kind = STATUS_KINDS[status]
    elif "api key" in low or etype == "authorization_error":
        kind = "auth"
    elif "not found" in low or "not_found" in low:
        kind = "not_found"
    elif "rate limit" in low:
        kind = "rate_limit"
    else:
        kind = "server" if status is not None and status >= 500 else "unknown"
    return {"ok": False, "kind": kind, "http_status": status, "message": redact(message),
            "fields": fields, "raw_tail": raw_tail(stdout, stderr)}


def brief(error):
    return {key: error.get(key) for key in ("kind", "http_status", "message")}


# ---------------------------------------------------------------- argv building
def encode_value(key, value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise usage("input.%s: NaN/Infinity cannot be sent" % key)
        return json.dumps(value)
    if isinstance(value, (str, list, dict)):  # a JSON string literal survives the CLI's value coercion
        try:
            json.dumps(value, ensure_ascii=False).encode("utf-8")
        except UnicodeEncodeError:
            raise usage("input.%s contains a broken character (lone surrogate, e.g. half an emoji)" % key)
        return json.dumps(value, separators=(",", ":"))
    raise usage("input.%s: unsupported value type %s" % (key, type(value).__name__))


def check_urls(key, value):
    """fal never reads local paths: *_url / *_urls inputs must already be URLs (or data URIs)."""
    if key.endswith("_url") or key.endswith("_urls"):
        for item in value if isinstance(value, list) else [value]:
            if isinstance(item, str) and not re.match(r"(https?://|data:)", item):
                raise usage("input.%s: %r is not a URL; run `gm.py upload <path>` and pass the cdn_url"
                            % (key, item[:80]))


def build_run_argv(endpoint_id, input_obj):
    """['run', <endpoint>, '--key', <encoded>, ..., '--async', '--json']: endpoint first, never '='."""
    if not isinstance(endpoint_id, str) or not ENDPOINT_RE.fullmatch(endpoint_id):
        raise usage("endpoint_id must look like owner/model[/variant]; smart routing is never used")
    if not isinstance(input_obj, dict):
        raise usage("input must be a JSON object")
    argv = ["run", endpoint_id]
    for key, value in input_obj.items():
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", key):
            raise usage("input key %r is not a valid parameter name" % key)
        if key in RESERVED_KEYS:
            raise usage("input key %r collides with a genmedia CLI flag and cannot be sent" % key)
        if value is None:
            continue
        check_urls(key, value)
        token = encode_value(key, value)
        if len(token.encode("utf-8")) > MAX_TOKEN_BYTES:
            raise usage("input.%s is too large for argv; upload the file and pass its URL" % key)
        argv += ["--" + key, token]
    return argv + ["--async", "--json"]


def check_job_options(download, est_cost, where=""):
    """A template that looks like a flag would be dropped by the CLI; NaN would break the JSON output."""
    if download not in (None, False) and (not isinstance(download, str) or not download.strip()
                                          or download.startswith("-")):
        raise usage("%sdownload must be a path template that does not start with '-' (or false)" % where)
    if est_cost is not None and (isinstance(est_cost, bool) or not isinstance(est_cost, (int, float))
                                 or not math.isfinite(est_cost) or est_cost < 0):
        raise usage("%sest_cost_usd must be a finite number >= 0" % where)


def check_timeout(value):
    if not math.isfinite(value) or value < 0:
        raise usage("--timeout must be a finite number of seconds >= 0")
    return value


def slug(text, fallback="adhoc"):
    # transliterate before stripping, so "İstanbul tanıtım" becomes "Istanbul-tanitim", not "stanbul-tan-t-m"
    folded = unicodedata.normalize("NFKD", str(text or "").translate(TR_ASCII))
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return re.sub(r"[^A-Za-z0-9._-]+", "-", folded).strip("-.") or fallback


def check_ids(endpoint_id, request_id):
    if not ENDPOINT_RE.fullmatch(endpoint_id):
        raise usage("endpoint_id must look like owner/model[/variant]")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", request_id):
        raise usage("request_id looks malformed")


def read_json_arg(source, what):
    try:
        if source == "-":  # bytes: the locale must not decide how a prompt is decoded
            return json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        with open(source, "rb") as handle:
            return json.loads(handle.read().decode("utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise usage("cannot read %s from %s: %s" % (what, source, exc))


# ---------------------------------------------------------------- ledger
def ledger_append(record):
    line = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    line.update((key, value) for key, value in record.items() if value is not None)
    try:
        os.makedirs(os.path.dirname(os.path.abspath(LEDGER)), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8", errors="backslashreplace") as handle:
            handle.write(json.dumps(line, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    except Exception as exc:  # the job is already paid for: keep going, but say so
        WARNINGS.append("ledger not written (%s); keep request_id %s from this output"
                        % (exc, record.get("request_id")))


def ledger_state():
    """Merge the append-only lines per request_id: later lines win, the first ts is kept."""
    merged = {}
    for number, raw in enumerate(read_text(LEDGER).splitlines()):
        line = parse_json(raw)
        if isinstance(line, dict) and (line.get("request_id") or line.get("status") == "submit_unknown"):
            record = merged.setdefault(line.get("request_id") or "unknown:%d" % number, {})
            first_ts = record.get("ts") or line.get("ts")
            record.update(line)
            record["ts"], record["updated"] = first_ts, line.get("ts")
    return merged


def outputs_intact(record):
    return all(not o.get("path") or os.path.exists(o["path"]) for o in record.get("outputs") or [])


def stash_result(job, result):
    """Keep a small result inline; write a large one to .genmedia/results/ and point at it."""
    try:
        limit = int(os.environ.get("GM_RESULT_INLINE_MAX") or RESULT_INLINE_MAX)
    except ValueError:
        limit = RESULT_INLINE_MAX
    text = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    size = len(text.encode("utf-8", "backslashreplace"))
    if result is None or size <= limit:
        return result, None, None
    path = os.path.join(RESULTS_DIR, "%s_%s.json" % (job["label"], job["request_id"][-8:]))
    try:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8", errors="backslashreplace") as handle:
            handle.write(text)
    except OSError as exc:  # the job is paid for: an oversized answer beats a lost one
        WARNINGS.append("large result kept inline (%s not written: %s)" % (path, exc.strerror or exc))
        return result, None, None
    return None, path, size


# ---------------------------------------------------------------- job engine
def media_refs(node, path="", key=None):
    """Media URLs in a result, in discovery order, each URL reported once.

    Two shapes count. A file object with an http(s) `url` is the rule the CLI downloads by. A bare
    string under a `url`/`*_url`/`*_urls` key is NOT: `--download` ignores it, so the URL would be
    lost once the process exits (fal-ai/ffmpeg-api/compose answers with `video_url` that way). Both
    become `outputs` entries; a bare string keeps `path: null` until `pipeline.py fetch` saves it.
    Queue plumbing (`status_url`, `cancel_url`, ...) is not media and is skipped.
    """
    refs, seen = [], set()
    for ref in walk_refs(node, path, key):
        if ref["url"] not in seen:
            seen.add(ref["url"])
            refs.append(ref)
    return refs


def walk_refs(node, path, key):
    refs = []
    if isinstance(node, dict):
        if isinstance(node.get("url"), str) and re.match(r"https?://", node["url"]):
            refs.append({"path": None, "url": node["url"], "json_path": path})
        for name, value in node.items():
            refs += walk_refs(value, "%s.%s" % (path, name) if path else name, name)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            refs += walk_refs(value, "%s[%d]" % (path, index), key)  # the list's own key names its items
    elif (isinstance(node, str) and key and URL_KEY_RE.search(key) and key not in PLUMBING_KEYS
          and re.match(r"https?://", node)):
        refs.append({"path": None, "url": node, "json_path": path})
    return refs


def input_urls(node):
    """Every http(s) string anywhere in a model input: a result that echoes one is not an output."""
    if isinstance(node, dict):
        return {url for value in node.values() for url in input_urls(value)}
    if isinstance(node, list):
        return {url for value in node for url in input_urls(value)}
    return {node} if isinstance(node, str) and re.match(r"https?://", node) else set()


def new_job(endpoint_id, label, job_id=None, input_obj=None, download=None, est_cost=None):
    return {"id": job_id, "endpoint_id": endpoint_id, "label": label, "input": input_obj,
            "download": download, "est_cost_usd": est_cost, "request_id": None, "state": "todo",
            "poll_errors": 0}


def submit(job):
    try:
        code, out, err = cli(job["argv"])
    except KeyboardInterrupt:
        code, out, err = 124, "", "gm.py: interrupted while submitting"
        job["interrupted"] = True
    request_id = parse_object(out).get("request_id") if code == 0 else None
    if not isinstance(request_id, str) or not request_id:
        error = normalize_error(out, err, code)
        if code in (0, 124):  # exit 0 without an id, a hung or an interrupted call: the job may exist
            error["message"] = "submission state unknown (%s); check %s before submitting again" % (
                error["message"], DASHBOARD)
            ledger_append({"label": job["label"], "job_id": job["id"], "endpoint_id": job["endpoint_id"],
                           "status": "submit_unknown", "input": job["input"], "error": brief(error),
                           "est_cost_usd": job["est_cost_usd"]})
        job.update(state="failed", error=error)
        if job.pop("interrupted", False):
            raise KeyboardInterrupt
        return
    job.update(request_id=request_id, state="inflight")
    record = {"label": job["label"], "job_id": job["id"], "endpoint_id": job["endpoint_id"],
              "request_id": request_id, "status": "submitted", "input": job["input"],
              "download": job["download"], "est_cost_usd": job["est_cost_usd"]}
    ledger_append(record)  # before any polling: a killed process can no longer lose the request


def fetch_result(job):
    """Call `status --download` (or --result) once after COMPLETED. False = not ready after all."""
    args = ["status", job["endpoint_id"], job["request_id"], "--json"]
    if job["download"] is False:
        args.append("--result")
    else:
        stem = job["id"] or "%s_%s" % (job["label"], job["request_id"][-8:])
        default = os.path.join("genmedia-output", job["label"], stem + "_{index}.{ext}")
        args += ["--download", job["download"] or default]  # --download stays last
    code, out, err = cli(args, FETCH_TIMEOUT)
    doc = parse_object(out) if code == 0 else {}
    base = {"label": job["label"], "endpoint_id": job["endpoint_id"], "request_id": job["request_id"]}
    if not doc:  # COMPLETED also covers failed jobs; this is where they surface
        error = normalize_error(out, err, code)
        if error["kind"] == "still_running":
            return False
        if error["http_status"] is None or error["kind"] in ("auth", "rate_limit"):
            # fal did not say the job failed (timeout, network, local error): it stays resumable and
            # is NOT recorded as failed, so --retry-failed can never pay for it a second time
            error["hint"] = "the result could not be fetched; the job itself is not known to have failed"
            job.update(state="pending", queue_status="COMPLETED", error=error)
            return True
        if error["kind"] == "validation" and not error["fields"]:
            error["hint"] = ("the CLI truncates field details of queued jobs: compare the input with "
                             "`%s schema %s`; if it matches, this is a runtime model error (content "
                             "policy, unreachable or oversized input file, no media generated) - see %s"
                             % (self_call(), job["endpoint_id"], DASHBOARD))
        job.update(state="failed", error=error)
        ledger_append(dict(base, status="failed", error=brief(error)))
        return True
    outputs = [{"path": f.get("path"), "url": f.get("url"), "json_path": f.get("json_path")}
               for f in doc.get("downloaded_files") or []]
    outputs += [{"path": None, "url": f.get("url"), "json_path": f.get("json_path"), "error": f.get("error")}
                for f in doc.get("download_failures") or []]
    known = {o["url"] for o in outputs} | input_urls(job.get("input"))
    outputs += [ref for ref in media_refs(doc.get("result")) if ref["url"] not in known]
    gallery = doc.get("gallery")
    if not isinstance(gallery, dict):
        gallery = {}
    result, result_path, result_bytes = stash_result(job, doc.get("result"))
    job.update(state="completed", outputs=outputs, result=result, result_path=result_path,
               result_bytes=result_bytes, gallery_url=gallery.get("url"))
    ledger_append(dict(base, status="completed", outputs=outputs, result_path=result_path))
    return True


def drive(jobs, timeout, max_parallel=4):
    """Submit 'todo' jobs (bounded in flight), poll with backoff, fetch results. Never resubmits."""
    started = time.monotonic()
    initial = poll_seconds("GM_POLL_INITIAL", 2.0)
    ceiling = max(initial, poll_seconds("GM_POLL_MAX", 15.0))
    try:
        drive_loop(jobs, timeout, max_parallel, started, initial, ceiling)
    except KeyboardInterrupt:  # Ctrl-C or SIGTERM: still answer with every request_id
        WARNINGS.append("interrupted; submitted jobs keep running and stay resumable")
    for job in jobs:
        if job["state"] in ("todo", "inflight"):
            job["state"] = "pending" if job["request_id"] else "not_submitted"
    return round(time.monotonic() - started, 1)


def poll_seconds(name, default):
    """Backoff bounds from the environment; garbage, zero or negative values must not spin or crash."""
    try:
        value = float(os.environ.get(name) or default)
    except ValueError:
        return default
    return min(max(value, 0.01), 60.0) if math.isfinite(value) else default


def drive_loop(jobs, timeout, max_parallel, started, initial, ceiling):
    interval, halted = initial, False
    while True:
        inflight = [job for job in jobs if job["state"] == "inflight"]
        for job in jobs:
            if job["state"] == "todo" and not halted and len(inflight) < max_parallel:
                submit(job)
                if job["state"] == "inflight":
                    inflight.append(job)
                elif job["error"]["kind"] == "auth":
                    halted = True  # every further submit would fail the same way
        if not inflight:
            break
        progressed = False
        for polled, job in enumerate(inflight):
            if polled and time.monotonic() - started > timeout:
                break  # a slow round must not overrun the budget; the rest is polled on resume
            code, out, err = cli(["status", job["endpoint_id"], job["request_id"], "--json"])
            status = parse_object(out).get("status") if code == 0 else None
            if status == "COMPLETED":
                progressed = fetch_result(job) or progressed
            elif status:
                job["poll_errors"], job["queue_status"] = 0, status
            else:
                error = normalize_error(out, err, code)
                job["poll_errors"] += 1
                if error["kind"] == "not_found":
                    job.update(state="failed", error=error)
                elif error["kind"] == "auth" or job["poll_errors"] >= MAX_POLL_ERRORS:
                    job.update(state="pending", error=error)  # remote state unknown; still resumable
        if progressed:
            interval = initial
        elif time.monotonic() - started + interval > timeout:
            break
        else:
            time.sleep(interval)
            interval = min(interval * 1.5, ceiling)


def job_view(job):
    view = {"id": job["id"], "status": job["state"], "endpoint_id": job["endpoint_id"],
            "request_id": job["request_id"]}
    if job["state"] == "pending":
        view["queue_status"] = job.get("queue_status")  # IN_QUEUE | IN_PROGRESS as last seen
    for key in ("outputs", "gallery_url", "est_cost_usd", "resumed", "input_changed", "result",
                "result_path", "result_bytes", "error"):
        if job.get(key) is not None:
            view[key] = job[key]
    return {key: value for key, value in view.items() if key != "id" or value}


def single_result(job, elapsed):
    view = dict(job_view(job), label=job["label"], elapsed_s=elapsed)
    if job["state"] in ("pending", "submitted"):
        view["resume"] = "%s wait %s %s" % (self_call(), job["endpoint_id"], job["request_id"])
    error = view.pop("error", None)  # on failure the normalized error is the top-level shape
    return (dict(error, **view), 1) if error else (dict({"ok": True}, **view), 0)


# ---------------------------------------------------------------- commands
def cmd_run(args):
    input_obj = read_json_arg(args.input, "input")
    check_job_options(args.download, args.est_cost)
    check_timeout(args.timeout)
    job = new_job(args.endpoint_id, slug(args.label), None, input_obj,
                  False if args.no_download else args.download, args.est_cost)
    job["argv"] = build_run_argv(args.endpoint_id, input_obj)
    if not args.submit_only:
        return single_result(job, drive([job], args.timeout))
    submit(job)
    job["state"] = "submitted" if job["request_id"] else job["state"]
    return single_result(job, 0.0)


def cmd_wait(args):
    check_ids(args.endpoint_id, args.request_id)
    check_job_options(args.download, None)
    check_timeout(args.timeout)
    known = ledger_state().get(args.request_id, {})
    job = new_job(args.endpoint_id, slug(args.label or known.get("label")), known.get("job_id"),
                  known.get("input"))
    job.update(request_id=args.request_id, state="inflight", est_cost_usd=known.get("est_cost_usd"),
               download=False if args.no_download else (args.download or known.get("download")))
    stashed = known.get("result_path")
    if not args.refetch and known.get("status") == "completed" and outputs_intact(known) \
            and (not stashed or os.path.exists(stashed)):
        job.update(state="completed", outputs=known.get("outputs"), result_path=stashed, resumed=True)
        return single_result(job, 0.0)  # already fetched: do not download the files twice
    elapsed = drive([job], args.timeout)
    if not known and job["state"] == "pending":  # submitted outside the helper and still running: adopt it
        ledger_append({"label": job["label"], "endpoint_id": args.endpoint_id, "status": "submitted",
                       "request_id": args.request_id, "download": job["download"], "note": "adopted by wait"})
    return single_result(job, elapsed)


def cmd_cancel(args):
    check_ids(args.endpoint_id, args.request_id)
    ids = {"endpoint_id": args.endpoint_id, "request_id": args.request_id}
    code, out, err = cli(["status", args.endpoint_id, args.request_id, "--cancel", "--json"])
    if code != 0:
        return dict(normalize_error(out, err, code), **ids), 1
    ledger_append(dict(ids, status="cancel_requested"))
    note = ("A cancel acknowledgement is not a terminal status: a running job may still finish and "
            "bill. Verify at " + DASHBOARD)
    return dict({"ok": True, "status": "cancel_requested", "terminal": False, "note": note}, **ids), 0


def plan_jobs(plan, label, retry_failed):
    """Validate every job before spending anything; attach ledger state for resumable ids."""
    previous = {}
    for record in ledger_state().values():
        if record.get("label") == label and record.get("job_id"):
            previous[record["job_id"]] = record  # the latest request per job id wins
    jobs = []
    for index, spec in enumerate(plan["jobs"]):
        if not isinstance(spec, dict) or not spec.get("id"):
            raise usage("jobs[%d] needs an id" % index)
        job_id, download = slug(spec["id"]), spec.get("download")
        if any(job["id"] == job_id for job in jobs):
            raise usage("duplicate job id %r" % job_id)
        check_job_options(download, spec.get("est_cost_usd"), "jobs[%d]." % index)
        job = new_job(spec.get("endpoint_id"), label, job_id, spec.get("input"), download,
                      spec.get("est_cost_usd"))
        job["argv"] = build_run_argv(job["endpoint_id"], job["input"])
        old = previous.get(job_id)
        # cancel_requested is NOT retriable: a cancel ack is not terminal, the job may still finish and
        # bill. It is resumed like any in-flight request and only becomes retriable once it has failed.
        retriable = old and old.get("status") in ("failed", "submit_unknown")
        if old and old.get("status") == "submit_unknown" and not retry_failed:
            message = ("an earlier submission of this id has an unknown state; check %s, then rerun with "
                       "--retry-failed if it never started" % DASHBOARD)
            job.update(state="failed", resumed=True, error=dict(normalize_error("", ""), message=message))
        elif old and not (retry_failed and retriable):
            job.update(request_id=old["request_id"], endpoint_id=old.get("endpoint_id") or job["endpoint_id"],
                       resumed=True, input_changed=(old.get("input") != job["input"]) or None)
            if old.get("status") == "completed" and outputs_intact(old):
                job.update(state="completed", outputs=old.get("outputs"))
            elif old.get("status") == "failed":
                job.update(state="failed", error=dict(normalize_error("", ""), **(old.get("error") or {})))
            else:
                job["state"] = "inflight"
        jobs.append(job)
    return jobs


def cmd_batch(args):
    plan = read_json_arg(args.plan, "plan")
    if not isinstance(plan, dict) or not isinstance(plan.get("jobs"), list) or not plan["jobs"]:
        raise usage('plan must be {"label": "...", "jobs": [{"id", "endpoint_id", "input"}, ...]}')
    label = slug(plan.get("label"), "batch")
    check_timeout(args.timeout)
    jobs = plan_jobs(plan, label, args.retry_failed)
    try:
        max_parallel = max(1, int(args.max_parallel or plan.get("max_parallel") or 4))
    except (TypeError, ValueError):
        raise usage("max_parallel must be an integer")
    elapsed = drive(jobs, args.timeout, max_parallel)
    counts = {}
    for job in jobs:
        counts[job["state"]] = counts.get(job["state"], 0) + 1
    unfinished = counts.get("pending", 0) + counts.get("not_submitted", 0)
    troubled = any(job.get("error") for job in jobs)
    result = {"ok": not troubled, "label": label, "counts": counts, "elapsed_s": elapsed,
              "status": "failed" if troubled else "pending" if unfinished else "completed",
              "est_cost_usd": round(sum(job["est_cost_usd"] or 0 for job in jobs if job["request_id"]), 4),
              "jobs": [job_view(job) for job in jobs]}
    galleries = [job["gallery_url"] for job in jobs if job.get("gallery_url")]
    if galleries:
        result["gallery_url"] = galleries[-1]
    if unfinished:
        result["resume"] = "%s batch --plan %s" % (self_call(), shlex.quote(args.plan))
    return result, int(troubled)


def cmd_upload(args):
    files = []
    for source in args.sources:
        target = source if re.match(r"https?://", source) else os.path.abspath(source)
        code, out, err = cli(["upload", target, "--json"], UPLOAD_TIMEOUT)
        cdn_url = parse_object(out).get("cdn_url") if code == 0 else None  # the field is cdn_url, not url
        if cdn_url:
            files.append({"source": source, "cdn_url": cdn_url})
        else:
            files.append({"source": source, "cdn_url": None, "error": brief(normalize_error(out, err, code))})
    failed = any(not f["cdn_url"] for f in files)
    return {"ok": not failed, "files": files, "urls": [f["cdn_url"] for f in files if f["cdn_url"]]}, int(failed)


def pricing_text(endpoint_id):
    """Pricing paragraph of the model's public llms.txt. Fetched WITHOUT credentials; None on any failure."""
    base = os.environ.get("GM_LLMS_TXT_BASE") or "https://fal.ai/models"
    if not re.match(r"https?://", base):
        return None
    try:
        request = urllib.request.Request("%s/%s/llms.txt" % (base.rstrip("/"), endpoint_id),
                                         headers={"User-Agent": "genmedia-skills"})
        with urllib.request.urlopen(request, timeout=15) as response:
            text = response.read(400000).decode("utf-8", "replace")
    except Exception:  # offline, 404, 429, TLS: the caller still has the URL
        return None
    match = re.search(r"^##\s*Pricing\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    body = re.sub(r"\n{3,}", "\n\n", match.group(1) if match else "").strip()
    return body[:1200] or None


def cmd_price(args):
    ids = [part.strip() for part in ",".join(args.endpoint_ids).split(",") if part.strip()]
    if not ids or not all(ENDPOINT_RE.fullmatch(one) for one in ids):
        raise usage("pass endpoint IDs as id1,id2 (each owner/model[/variant])")
    code, out, err = cli(["pricing", ",".join(ids), "--json"])
    rows = (parse_object(out).get("prices") or []) if code == 0 else []
    if code != 0:
        error = normalize_error(out, err, code)
        if error["kind"] != "not_found" or len(ids) == 1:
            return error, 1
        for one in ids:  # one unknown ID fails the whole call: ask again per ID to name it
            code, out, err = cli(["pricing", one, "--json"])
            rows += (parse_object(out).get("prices") or []) if code == 0 else []
    prices = [{"endpoint_id": row.get("endpoint_id"), "unit_price": row.get("unit_price"),
               "unit": row.get("unit"), "currency": row.get("currency"),
               "needs_llms_txt": str(row.get("unit") or "").strip().lower() not in SIMPLE_UNITS,
               "llms_txt": "https://fal.ai/models/%s/llms.txt" % row.get("endpoint_id")} for row in rows]
    missing = [one for one in ids if one not in {p["endpoint_id"] for p in prices}]
    if args.explain:
        for price in prices:
            price["pricing_text"] = pricing_text(price["endpoint_id"])
    note = ("needs_llms_txt:true -> unit_price cannot simply be multiplied; use pricing_text (rerun with "
            "--explain). Tiers (audio, resolution) are only described there too, also for per-second "
            "and per-image units. Do not fetch llms_txt yourself: --explain already did.")
    return {"ok": not missing, "prices": prices, "missing": missing, "note": note}, int(bool(missing))


# ---------------------------------------------------------------- schema
SCHEMA_LIMITS = ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
                 "minLength", "maxLength", "minItems", "maxItems")
SCHEMA_MAX_DEPTH = 3     # image_size.width is depth 1; anything deeper is named, not expanded
SCHEMA_MAX_OUTPUT = 60   # leaf names of the result object
SCHEMA_DESC_MAX = 600
JSON_TYPES = ((bool, "boolean"), (int, "integer"), (float, "number"), (str, "string"),
              (list, "array"), (dict, "object"))  # bool first: isinstance(True, int) is true
MISSING = object()       # a field whose default is JSON null still has a default


def dig(node, *keys):
    for key in keys:
        node = node.get(key) if isinstance(node, dict) else None
    return node if isinstance(node, dict) else {}


def ref_target(node, doc, trail):
    """Follow a `$ref` chain inside one document. Returns (node, trail).

    fal puts `description` and `default` next to a `$ref` (`voice_setting`), so the siblings win over
    the target's own keys. The trail carries the refs already followed: a schema that refers back to
    itself must not recurse forever.
    """
    while isinstance(node, dict) and isinstance(node.get("$ref"), str):
        ref = node["$ref"]
        siblings = {key: value for key, value in node.items() if key != "$ref"}
        if not ref.startswith("#/") or ref in trail:
            return siblings, trail  # external or cyclic: keep what is on this node
        target = doc
        for part in ref[2:].split("/"):
            target = target.get(part.replace("~1", "/").replace("~0", "~")) if isinstance(target, dict) else None
        if not isinstance(target, dict):
            return siblings, trail
        node, trail = dict(target, **siblings), trail | {ref}
    return (node if isinstance(node, dict) else {}), trail


def collect_schema(node, doc, trail, view, depth):
    """Fold one JSON-Schema node, and every anyOf/oneOf/allOf branch under it, into one view."""
    node, trail = ref_target(node, doc, trail)
    for key in ("allOf", "anyOf", "oneOf"):
        for branch in node.get(key) or []:
            resolved, sub_trail = ref_target(branch, doc, trail)
            if resolved.get("type") == "null" or depth >= SCHEMA_MAX_DEPTH:
                continue  # a null branch only says the field may be omitted
            collect_schema(resolved, doc, sub_trail, view, depth + 1)
    kinds = node.get("type")
    for kind in (kinds if isinstance(kinds, list) else [kinds]):
        if isinstance(kind, str) and kind != "null" and kind not in view["types"]:
            view["types"].append(kind)
    for value in node.get("enum") or []:
        if value is not None and value not in view["enum"]:
            view["enum"].append(value)
    for name in SCHEMA_LIMITS:
        if name in node and name not in view["limits"]:
            view["limits"][name] = node[name]
    if "default" in node and view["default"] is MISSING:
        view["default"] = node["default"]
    if node.get("description") and not view["description"]:
        view["description"] = " ".join(str(node["description"]).split())
    if isinstance(node.get("properties"), dict) and view["object"] is None:
        view["object"] = (node, trail)
    if node.get("items") is not None and view["items"] is None:
        view["items"] = (node["items"], trail)


def schema_view(node, doc, trail=frozenset()):
    view = {"types": [], "enum": [], "limits": {}, "object": None, "items": None,
            "description": "", "default": MISSING}
    collect_schema(node, doc, trail, view, 0)
    return view


def type_text(view):
    """`string`, `array`, `object|string` for image_size; `unknown` only when nothing said so."""
    types = list(view["types"])
    if not types:  # an enum branch often carries no `type`; the values still say what it is
        for value in view["enum"]:
            for cls, name in JSON_TYPES:
                if isinstance(value, cls) and name not in types:
                    types.append(name)
                    break
    if not types and view["object"]:
        types = ["object"]
    if not types and view["items"] is not None:
        types = ["array"]
    return "|".join(types) or "unknown"


def field_view(name, node, doc, required, trail=frozenset(), depth=0, describe=False):
    view = schema_view(node, doc, trail)
    field = {"name": name, "type": type_text(view), "required": bool(required)}
    if view["default"] is not MISSING:
        field["default"] = view["default"]
    if view["enum"]:
        field["enum"] = view["enum"]
    field.update(view["limits"])
    if view["object"] and depth < SCHEMA_MAX_DEPTH:
        parent, sub_trail = view["object"]
        field["properties"] = object_fields(parent, doc, sub_trail, depth + 1, describe)
    if view["items"] is not None and depth < SCHEMA_MAX_DEPTH:
        item, sub_trail = view["items"]
        inner = field_view("", item, doc, False, sub_trail, depth + 1, describe)
        field["items"] = {key: value for key, value in inner.items() if key not in ("name", "required")}
    if describe and view["description"]:
        field["description"] = view["description"][:SCHEMA_DESC_MAX]
    return field


def object_fields(parent, doc, trail, depth, describe):
    """Properties of one object schema: required first, then fal's own playground order."""
    props = parent.get("properties") or {}
    required = [name for name in parent.get("required") or [] if isinstance(name, str)]
    order = [name for name in parent.get("x-fal-order-properties") or [] if name in props]
    order += [name for name in props if name not in order]
    order.sort(key=lambda name: 0 if name in required else 1)  # stable: fal's order survives per group
    return [field_view(name, props[name], doc, name in required, trail, depth, describe)
            for name in order]


def top_fields(node, doc, describe=False):
    view = schema_view(node, doc)
    if not view["object"]:
        return []
    parent, trail = view["object"]
    return object_fields(parent, doc, trail, 0, describe)


def output_names(node, doc, prefix="", trail=frozenset(), depth=0, found=None):
    """Dotted leaf names of the result object: `images[].url`, `video.url`, `seed`."""
    found = [] if found is None else found
    if len(found) >= SCHEMA_MAX_OUTPUT:
        return found
    view = schema_view(node, doc, trail)
    if view["object"] and depth <= SCHEMA_MAX_DEPTH:
        parent, sub_trail = view["object"]
        props = parent.get("properties") or {}
        order = [name for name in parent.get("x-fal-order-properties") or [] if name in props]
        order += [name for name in props if name not in order]
        for name in order:
            output_names(props[name], doc, "%s.%s" % (prefix, name) if prefix else name,
                         sub_trail, depth + 1, found)
    elif view["items"] is not None and depth <= SCHEMA_MAX_DEPTH:
        item, sub_trail = view["items"]
        output_names(item, doc, prefix + "[]", sub_trail, depth + 1, found)
    elif prefix:
        found.append(prefix)
    return found


def openapi_schemas(doc):
    """(input, output) nodes of a fal queue OpenAPI document."""
    input_node, output_node = None, None
    for path, item in (doc.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        if input_node is None and isinstance(item.get("post"), dict) and "{request_id}" not in path:
            input_node = dig(item["post"], "requestBody", "content", "application/json").get("schema")
        if output_node is None and isinstance(item.get("get"), dict) and path.endswith("{request_id}"):
            output_node = dig(item["get"], "responses", "200", "content", "application/json").get("schema")
    schemas = dig(doc, "components", "schemas")
    for name, node in schemas.items():  # a document without `paths` still names its models
        if input_node is None and name.endswith("Input"):
            input_node = node
        if output_node is None and name.endswith("Output"):
            output_node = node
    return input_node, output_node


def cmd_schema(args):
    if not isinstance(args.endpoint_id, str) or not ENDPOINT_RE.fullmatch(args.endpoint_id):
        raise usage("endpoint_id must look like owner/model[/variant]")
    code, out, err = cli(["schema", args.endpoint_id, "--format", "openapi", "--json"])
    doc = parse_object(out) if code == 0 else {}
    if not doc:
        return normalize_error(out, err, code), 1
    meta = dig(doc, "info", "x-fal-metadata")
    input_node, output_node = openapi_schemas(doc)
    result = {"ok": True, "endpoint_id": meta.get("endpointId") or args.endpoint_id,
              "category": meta.get("category")}
    fields = top_fields(input_node, doc, describe=bool(args.field))
    if args.field:
        for field in fields:
            if field["name"] == args.field:
                return dict(result, field=field), 0
        raise usage("%s has no input field %r; fields: %s"
                    % (args.endpoint_id, args.field, ", ".join(f["name"] for f in fields) or "(none)"))
    result["input"] = fields
    result["output"] = output_names(output_node, doc)
    result["note"] = ("compact view of `genmedia schema <id> --format openapi --json`; enums, defaults "
                      "and limits are complete, descriptions are not (`--field <name>` prints one field "
                      "in full). Output names are paths inside `.result`.")
    if not fields:
        result["ok"] = False
        result["note"] = "no input fields found in the OpenAPI document; read the raw schema yourself"
    return result, int(not result["ok"])


def cmd_ledger(args):
    records = list(ledger_state().values())
    if args.label:
        records = [record for record in records if record.get("label") == slug(args.label)]
    result = {"ok": True, "path": os.path.abspath(LEDGER), "count": len(records)}
    if args.sum:
        by_status = {}
        for record in records:
            bucket = by_status.setdefault(record.get("status") or "unknown", {"count": 0, "est_cost_usd": 0.0})
            bucket["count"] += 1
            bucket["est_cost_usd"] = round(bucket["est_cost_usd"] + (record.get("est_cost_usd") or 0), 4)
        result["by_status"] = by_status
        result["est_cost_usd"] = round(sum(bucket["est_cost_usd"] for bucket in by_status.values()), 4)
        result["est_cost_usd_completed"] = (by_status.get("completed") or {}).get("est_cost_usd", 0.0)
        result["note"] = ("estimates, not an invoice; est_cost_usd includes failed and unfinished requests "
                          "(fal does not bill 5xx failures), est_cost_usd_completed counts finished ones only")
    tail = records[-args.tail:] if args.tail > 0 else []
    result["runs"] = tail if args.full else [{k: v for k, v in r.items() if k != "input"} for r in tail]
    return result, 0


def probe_account(key, warnings):
    """Two free calls: `pricing` proves the key works, `assets browse` tells whether Assets is on."""
    code, out, err = cli(["pricing", KEY_PROBE_ID, "--json"], 60)
    error = normalize_error(out, err, code) if code else None
    if not error or error["kind"] == "not_found":  # a 404 still proves the key was accepted
        key.update(present=True, valid=True)
    elif "no fal.ai api key" in error["message"].lower():
        key.update(present=False, valid=False)
    elif error["kind"] == "auth":
        key.update(present=True, valid=False)
    else:
        warnings.append("key check inconclusive: " + error["message"])
    if not key["valid"]:
        return {"enabled": "unknown"}
    code, out, err = cli(["assets", "browse", "--limit", "1", "--json"], 60)
    error = normalize_error(out, err, code) if code else None
    if error and error["http_status"] != 403:
        return {"enabled": "unknown", "reason": error["message"]}
    return {"enabled": False, "reason": error["message"]} if error else {"enabled": True}


def stock_skills():
    """Skills installed by `genmedia init` / `genmedia skills install` overlap with this plugin."""
    found = []
    for base in (".claude/skills", ".agents/skills"):
        skills = parse_object(read_text(os.path.join(base, ".installed.json"))).get("skills")
        for skill in skills if isinstance(skills, list) else []:
            if isinstance(skill, dict) and skill.get("name"):
                found.append({"name": skill["name"], "path": "%s/%s" % (base, skill["name"])})
    return found


def cmd_preflight(args):
    blockers, warnings = [], []
    path = shutil.which(os.environ.get("GM_GENMEDIA_BIN") or "genmedia")
    gm = {"found": bool(path), "version": None, "ok": False}
    if path:
        gm["version"] = parse_object(cli(["version", "--json"], 30)[1]).get("version")
        parts = re.match(r"(\d+)\.(\d+)\.(\d+)", str(gm["version"]))
        gm["ok"] = bool(parts) and tuple(map(int, parts.groups())) >= MIN_VERSION
    if not gm["ok"]:
        blockers.append("genmedia CLI >= %s is required" % ".".join(map(str, MIN_VERSION)))
    key = {"present": True if os.environ.get("FAL_KEY") else None, "valid": None}
    assets = probe_account(key, warnings) if gm["ok"] and not args.no_network else {"enabled": "unknown"}
    if key["present"] is False or key["valid"] is False:
        blockers.append("no working fal key: the user must run `genmedia setup` or export FAL_KEY themselves")
    ffmpeg = {"found": bool(shutil.which("ffmpeg")), "drawtext": False}
    if ffmpeg["found"]:
        try:
            listing = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, timeout=15).stdout
            ffmpeg["drawtext"] = re.search(rb"\bdrawtext\b", listing) is not None
        except (OSError, subprocess.SubprocessError):
            pass
    stock = stock_skills()
    if stock:
        warnings.append("stock fal skills are installed in this project and overlap with this plugin")
    config = parse_object(read_text(CONFIG))
    session = {"name": session_name(), "source": "env" if os.environ.get("GENMEDIA_SESSION_ID") else "project-dir"}
    result = {"ok": not blockers, "genmedia": gm, "key": key, "python": platform.python_version(),
              "jq": bool(shutil.which("jq")), "ffmpeg": ffmpeg, "assets": assets, "stock_skills": stock,
              "session": session,
              "config": {"path": os.path.abspath(CONFIG), "exists": bool(config),
                         "announce_above_usd": config.get("announce_above_usd", 0.5),
                         "confirm_above_usd": config.get("confirm_above_usd", 2.0)},
              "blockers": blockers, "warnings": warnings}
    return result, int(bool(blockers))


# ---------------------------------------------------------------- gallery
def cmd_gallery(args):
    """Resolve this project's gallery page. The CLI hashes GENMEDIA_SESSION_ID into its session id,
    so a skill cannot name the page itself; an env-var prefix in front of `genmedia` would prompt."""
    code, out, err = cli(["gallery", "open", "current", "--print", "--json"], 30)
    doc = parse_object(out) if code == 0 else {}
    if not doc.get("url"):
        return normalize_error(out, err, code or 1), 1
    result = {"ok": True, "session": session_name(), "url": doc.get("url"), "path": doc.get("path"),
              "exists": bool(doc.get("exists"))}
    return result, 0


# ---------------------------------------------------------------- entry point
class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise usage("%s (see `%s --help`)" % (message, self.prog))


def build_parser():
    parser = Parser(prog="gm.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    def add(name, func, summary, positionals=(), waits=False):
        command = sub.add_parser(name, help=summary, description=summary)
        command.set_defaults(func=func)
        for positional in positionals:
            command.add_argument(positional)
        if waits:
            group = command.add_mutually_exclusive_group()
            group.add_argument("--download", metavar="TEMPLATE", help="placeholders: {index} {name} {ext} {request_id}")
            group.add_argument("--no-download", action="store_true", help="fetch the result JSON only")
            command.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds to poll (540)")
            command.add_argument("--label", help="project slug: groups ledger lines and the output folder")
        return command

    command = add("preflight", cmd_preflight, "check CLI, key, tools, fal Assets, stock skills (free calls only)")
    command.add_argument("--no-network", action="store_true", help="skip the key and Assets probes")
    command = add("upload", cmd_upload, "upload local files or re-host URLs; prints cdn_url per file")
    command.add_argument("sources", nargs="+", metavar="path-or-url")
    command = add("run", cmd_run, "submit one job from a JSON input object, wait, download", ["endpoint_id"], True)
    command.add_argument("--input", required=True, metavar="FILE|-", help="JSON object with the model input")
    command.add_argument("--async", dest="submit_only", action="store_true", help="submit and return at once")
    command.add_argument("--est-cost", type=float, metavar="USD", help="estimate to record in the ledger")
    command = add("wait", cmd_wait, "resume polling a submitted request; never resubmits",
                  ["endpoint_id", "request_id"], True)
    command.add_argument("--refetch", action="store_true",
                         help="ask the queue for the result again instead of answering from the ledger "
                              "(free; add --no-download to skip the files)")
    add("cancel", cmd_cancel, "request cancellation (the acknowledgement is not terminal)",
        ["endpoint_id", "request_id"])
    command = add("batch", cmd_batch, "run a plan of independent jobs; resumable from the ledger")
    command.add_argument("--plan", required=True, metavar="FILE|-")
    command.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds to poll (540)")
    command.add_argument("--max-parallel", type=int, metavar="N", help="jobs in flight (default: plan value or 4)")
    command.add_argument("--retry-failed", action="store_true", help="resubmit ids whose last request failed")
    command = add("schema", cmd_schema, "compact input fields and output names of an endpoint (free)",
                  ["endpoint_id"])
    command.add_argument("--field", metavar="NAME",
                         help="print this one input field with its description and full nesting")
    command = add("price", cmd_price, "unit prices for one or more endpoint IDs in one call")
    command.add_argument("endpoint_ids", nargs="+", metavar="id[,id...]")
    command.add_argument("--explain", action="store_true",
                         help="add the Pricing paragraph of each model's public llms.txt (no credentials sent)")
    command = add("ledger", cmd_ledger, "read .genmedia/runs.jsonl merged per request")
    command.add_argument("--tail", type=int, default=20, metavar="N")
    command.add_argument("--sum", action="store_true", help="add estimated cost totals per status")
    command.add_argument("--label")
    command.add_argument("--full", action="store_true", help="include each run's input")
    add("gallery", cmd_gallery, "this project's local gallery page (free, opens nothing)")
    return parser


def on_sigterm(signum, frame):
    raise KeyboardInterrupt  # handled like Ctrl-C: record what is known, print one JSON object


def main(argv=None):
    try:
        signal.signal(signal.SIGTERM, on_sigterm)
    except (ValueError, OSError, AttributeError):  # not the main thread, or an odd platform
        pass
    try:
        args = build_parser().parse_args(argv)
        payload, code = args.func(args)
    except GmError as exc:
        payload, code = exc.payload, exc.code
    except KeyboardInterrupt:
        payload, code = {"ok": False, "kind": "unknown",
                         "message": "interrupted; submitted jobs keep running - see `gm.py ledger`"}, 1
    except Exception as exc:  # always answer with one JSON object
        payload, code = {"ok": False, "kind": "unknown", "message": redact(
            "gm.py internal error: %r; anything already submitted is in `gm.py ledger`" % (exc,))}, 1
    if WARNINGS:
        payload["warnings"] = list(payload.get("warnings") or []) + WARNINGS
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.buffer.write(text.encode("utf-8", "backslashreplace") + b"\n")  # lone surrogate -> \udXXX
    sys.stdout.flush()
    return code


if __name__ == "__main__":
    sys.exit(main())
