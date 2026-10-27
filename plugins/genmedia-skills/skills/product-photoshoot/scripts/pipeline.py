#!/usr/bin/env python3
# GENERATED from shared/scripts/pipeline.py — edit the source, then run scripts/sync_shared.py
r"""pipeline.py - project state for multi-step genmedia pipelines. Python 3.8+, stdlib only.

Reads the gm.py ledger (.genmedia/runs.jsonl; never writes it) and keeps per-project state in
.genmedia/projects/<label>/. Prints ONE compact JSON object on stdout.
Exit: 0 ok | 1 problems | 2 usage. Never reads the API key, never calls a paid endpoint.

  urls     --label <slug>
      Latest request per job id under the label: status, output URLs, local paths. Plus local assets.
  fill     --template <plan.tmpl.json> --out <plan.json> [--label <slug>]
           [--placeholder <regex>] [--allow-placeholders]
      Replace whole-string references inside jobs[].input with URLs of earlier outputs:
        "@kf01"     first output URL of job kf01 (or of a local asset registered with --url)
        "@kf01[2]"  third output URL (0-based, same order as {index} in download templates)
        "@@text"    escape: the literal string "@text"
      Any unresolved reference: exit 1 and nothing is written.
      A string value that still carries a template placeholder ({LOCK}, {{BRAND_LOCK}}, <describe it>)
      is the same refusal, with the JSON path of every hit: a placeholder that reaches the model is a
      wasted paid job. A bracket that belongs in the prompt is backslash-escaped (\{ \} \< \>) and the
      backslash is dropped on write; --placeholder replaces the pattern, --allow-placeholders drops it.
  add      --label <slug> --step <id> --path <file> [--url <https-url>] [--tool <name>]
           [--from <id,id>] [--note <text>]
      Register a file made outside the ledger (uploaded user file, local ffmpeg product).
  fetch    --label <slug> --step <id> --out <relative-path> [--url <https-url>] [--index N]
           [--endpoint <endpoint_id>] [--request-id <id>] [--note <text>]
      Download a result the CLI did not save (its --download only sees file objects) and register it.
      Without --url the URL comes from the ledger: the latest completed request under this label whose
      job id is <id>, its first output that has no local path (--index picks a later one, in result
      order - video_url before thumbnail_url). Never overwrites a file.
  manifest --label <slug>
      Write .genmedia/projects/<label>/manifest.json from the ledger plus local assets and run the
      mechanical gate. Exit 1 while `problems` is not empty.
"""
import argparse
import json
import os
import re
import unicodedata
import sys
import time
import urllib.error
import urllib.request

LEDGER = os.path.join(".genmedia", "runs.jsonl")
PROJECTS = os.path.join(".genmedia", "projects")
LOCAL_ASSETS = "local-assets.jsonl"
REF_RE = re.compile(r"^@([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[(\d+)\])?$")
# The same notion of "placeholder" as brandkit.py: {{TOKEN}}, <describe this>, {LOCK}.
PLACEHOLDER_RE = re.compile(r"\{\{[^{}]*\}\}|<[A-Za-z][^<>\n]{0,60}>|\{[A-Z][A-Z0-9_ .-]{0,60}\}")
ESCAPED_RE = re.compile(r"\\([{}<>])")  # \{ \} \< \> keep a literal bracket; unescaped on write
PROMPT_KEYS = ("prompt", "text", "lyrics", "text_prompt")
FETCH_TIMEOUT = 300
UNFINISHED = {"submitted": "still running or never fetched; run the stage plan again to resume",
              "cancel_requested": "cancel was requested; its real end state is unknown",
              "submit_unknown": "submission state unknown; check https://fal.ai/dashboard/requests"}


class UsageError(Exception):
    pass


TR_ASCII = str.maketrans("ıİşŞğĞüÜöÖçÇ", "iIsSgGuUoOcC")


def slug(text):
    """Same normalisation as gm.py (transliterate, then strip), so labels and job ids match the ledger."""
    folded = unicodedata.normalize("NFKD", str(text or "").translate(TR_ASCII))
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return re.sub(r"[^A-Za-z0-9._-]+", "-", folded).strip("-.")


def need_slug(text, what):
    value = slug(text)
    if not value:
        raise UsageError("%s is empty after normalisation" % what)
    return value


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_lines(path):
    try:
        with open(path, "rb") as handle:
            return handle.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return []


def parse_line(raw):
    try:
        doc = json.loads(raw)
    except ValueError:
        return None
    return doc if isinstance(doc, dict) else None


def project_dir(label):
    return os.path.join(PROJECTS, label)


# ---------------------------------------------------------------- state readers
def ledger_requests(label):
    """Ledger lines merged per request_id (later lines win, first ts kept), in submission order."""
    merged = {}
    for number, raw in enumerate(read_lines(LEDGER)):
        line = parse_line(raw)
        if not line or not (line.get("request_id") or line.get("status") == "submit_unknown"):
            continue
        record = merged.setdefault(line.get("request_id") or "unknown:%d" % number, {})
        first_ts = record.get("ts") or line.get("ts")
        record.update(line)
        record["ts"], record["updated"] = first_ts, line.get("ts")
    return [r for r in merged.values() if r.get("label") == label]


def step_name(record):
    return record.get("job_id") or "run-%s" % str(record.get("request_id") or "unknown")[-8:]


def latest_per_step(requests):
    latest = {}
    for record in requests:  # submission order: a retry of the same id comes later and wins
        latest[step_name(record)] = record
    return latest


def local_assets(label):
    """One entry per step; a later `add`/`fetch` of the same step replaces the earlier one."""
    entries = {}
    for raw in read_lines(os.path.join(project_dir(label), LOCAL_ASSETS)):
        line = parse_line(raw)
        if line and line.get("step"):
            entries[line["step"]] = line
    return entries


def file_size(path):
    try:
        return os.path.getsize(path) if path and os.path.isfile(path) else None
    except OSError:
        return None


def append_local(label, entry):
    folder = project_dir(label)
    os.makedirs(folder, exist_ok=True)
    line = {"ts": now()}
    line.update((key, value) for key, value in entry.items() if value not in (None, "", []))
    with open(os.path.join(folder, LOCAL_ASSETS), "a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, ensure_ascii=False, separators=(",", ":")) + "\n")
    return line


def check_https(url, what="--url"):
    allow_http = os.environ.get("PIPELINE_TEST_ALLOW_HTTP") == "1"  # offline tests only
    if isinstance(url, str) and (url.startswith("https://") or
                                 (allow_http and re.match(r"http://(127\.0\.0\.1|localhost)[:/]", url))):
        return url
    raise UsageError("%s must be an https:// URL" % what)


# ---------------------------------------------------------------- commands
def cmd_urls(args):
    label = need_slug(args.label, "--label")
    jobs, counts = [], {}
    for step, record in latest_per_step(ledger_requests(label)).items():
        outputs = record.get("outputs") or []
        status = record.get("status") or "unknown"
        counts[status] = counts.get(status, 0) + 1
        jobs.append({"id": step, "status": status, "endpoint_id": record.get("endpoint_id"),
                     "urls": [o.get("url") for o in outputs if o.get("url")],
                     "paths": [o.get("path") for o in outputs if o.get("path")]})
    local = [{"step": step, "path": entry.get("path"), "url": entry.get("url")}
             for step, entry in local_assets(label).items()]
    return {"ok": True, "label": label, "counts": counts, "jobs": jobs, "local": local}, 0


def resolve_ref(name, index, latest, local):
    """-> (url, None) or (None, reason)."""
    record = latest.get(name)
    if record is not None:
        status = record.get("status") or "unknown"
        if status != "completed":
            return None, "job %s is %s, not completed" % (name, status)
        urls = [o.get("url") for o in record.get("outputs") or [] if o.get("url")]
        if not urls and name in local and local[name].get("url"):
            urls = [local[name]["url"]]  # bare-string result that was fetched and registered
        if not urls:
            return None, ("job %s has no output URL in the ledger; its result carried none under a "
                          "`url`/`*_url` key. Read the result and register the URL with "
                          "`fetch --url` or `add --url`" % name)
        if index >= len(urls):
            return None, "job %s has %d output(s); index %d does not exist" % (name, len(urls), index)
        return urls[index], None
    entry = local.get(name)
    if entry is not None:
        if not entry.get("url"):
            return None, "local asset %s has no URL; upload it and `add` it again with --url" % name
        if index:
            return None, "local asset %s has one URL; index %d does not exist" % (name, index)
        return entry["url"], None
    return None, "no job or local asset named %s under this label" % name


def find_placeholders(text, pattern):
    """Placeholders left in a string, in order. An escaped bracket cannot open one."""
    masked = ESCAPED_RE.sub("  ", text)  # two characters for two, so the spans still fit `text`
    return [text[match.start():match.end()] for match in pattern.finditer(masked)]


def cmd_fill(args):
    if os.path.abspath(args.template) == os.path.abspath(args.out):
        raise UsageError("--out must differ from --template")
    try:
        with open(args.template, "rb") as handle:
            plan = json.loads(handle.read().decode("utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise UsageError("cannot read the template %s: %s" % (args.template, exc))
    if not isinstance(plan, dict) or not isinstance(plan.get("jobs"), list) or not plan["jobs"]:
        raise UsageError('template must be {"label": "...", "jobs": [{"id", "endpoint_id", "input"}, ...]}')
    label = need_slug(plan.get("label") or args.label, "label (set it in the template or pass --label)")
    if args.label and slug(args.label) != label:
        raise UsageError("--label %r does not match the template label %r" % (args.label, label))
    plan["label"] = label
    try:
        pattern = None if args.allow_placeholders else re.compile(args.placeholder or PLACEHOLDER_RE.pattern)
    except re.error as exc:
        raise UsageError("--placeholder is not a valid regular expression: %s" % exc)
    latest, local = latest_per_step(ledger_requests(label)), local_assets(label)
    resolved, unresolved, placeholders, hits = {}, [], [], set()

    def literal(text, where):
        """Any string the plan keeps: report leftover placeholders, then drop the bracket escapes."""
        for found in [] if pattern is None else find_placeholders(text, pattern):
            if (where, found) not in hits:
                hits.add((where, found))
                placeholders.append({"placeholder": found, "at": where})
        return ESCAPED_RE.sub(r"\1", text)

    def walk(value, where):
        if isinstance(value, dict):
            return {key: walk(child, "%s.%s" % (where, key)) for key, child in value.items()}
        if isinstance(value, list):
            return [walk(child, "%s[%d]" % (where, i)) for i, child in enumerate(value)]
        if isinstance(value, str):
            if value.startswith("@@"):
                return literal(value[1:], where)
            match = REF_RE.match(value)
            if match:
                url, reason = resolve_ref(match.group(1), int(match.group(2) or 0), latest, local)
                if url is None:
                    unresolved.append({"ref": value, "at": where, "reason": reason})
                    return value
                resolved[value] = url
                return url
            return literal(value, where)
        return value

    seen = set()
    for number, job in enumerate(plan["jobs"]):
        if not isinstance(job, dict) or not job.get("id"):
            raise UsageError("jobs[%d] needs an id" % number)
        job_id = slug(job["id"])
        if job_id in seen:
            raise UsageError("duplicate job id %r" % job_id)
        seen.add(job_id)
        if not isinstance(job.get("input"), dict):
            raise UsageError("jobs[%d].input must be an object" % number)
        job["input"] = walk(job["input"], "jobs[%d].input" % number)
    if unresolved or placeholders:
        told = ["finish or repair the upstream jobs first"] if unresolved else []
        if placeholders:
            told.append("replace every placeholder with the real text "
                        "(a bracket that belongs in the prompt is escaped: \\{ \\} \\< \\>)")
        problem = {"ok": False, "label": label, "message": "nothing was written; " + " and ".join(told)}
        if unresolved:
            problem["unresolved"] = unresolved
        if placeholders:
            problem["placeholders"] = placeholders
        return problem, 1
    folder = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(folder, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(plan, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
    in_ledger = sorted(step for step in seen if step in latest)
    return {"ok": True, "label": label, "out": args.out, "jobs": len(plan["jobs"]),
            "resolved": resolved, "already_in_ledger": in_ledger}, 0


def cmd_add(args):
    label, step = need_slug(args.label, "--label"), need_slug(args.step, "--step")
    size = file_size(args.path)
    if size is None:
        raise UsageError("--path %s is not a file" % args.path)
    url = check_https(args.url) if args.url else None
    sources = [slug(part) for part in (args.sources or "").split(",") if slug(part)]
    entry = append_local(label, {"step": step, "path": os.path.normpath(args.path), "url": url,
                                 "tool": args.tool, "from": sources, "note": args.note})
    return {"ok": True, "label": label, "step": step, "path": entry["path"], "url": url, "bytes": size}, 0


def safe_relative(path):
    """A relative path that stays inside the project directory."""
    normal = os.path.normpath(path)
    if os.path.isabs(normal) or normal == os.pardir or normal.startswith(os.pardir + os.sep):
        raise UsageError("--out must be a relative path inside the project directory")
    return normal


def ledger_url(label, step, index):
    """The URL of a step's unsaved output, from the ledger. -> (url, record)."""
    record = latest_per_step(ledger_requests(label)).get(step)
    if record is None:
        raise UsageError("no job %s under label %s in the ledger; pass --url" % (step, label))
    status = record.get("status") or "unknown"
    if status != "completed":
        raise UsageError("job %s is %s, not completed; pass --url to save a URL anyway" % (step, status))
    urls = [o.get("url") for o in record.get("outputs") or [] if o.get("url") and not o.get("path")]
    if not urls:
        raise UsageError("job %s has no unsaved output URL in the ledger; pass --url" % step)
    if index >= len(urls):
        raise UsageError("job %s has %d unsaved output(s); --index %d does not exist" % (step, len(urls), index))
    return urls[index], record


def cmd_fetch(args):
    label, step = need_slug(args.label, "--label"), need_slug(args.step, "--step")
    index = args.index or 0
    if index < 0:
        raise UsageError("--index must be 0 or greater")
    record = {}
    if args.url:
        url = check_https(args.url)
    else:
        url, record = ledger_url(label, step, index)
        url = check_https(url, "the ledger URL of job %s" % step)
    endpoint = args.endpoint or record.get("endpoint_id")
    request_id = args.request_id or record.get("request_id")
    out = safe_relative(args.out)
    if os.path.exists(out):
        raise UsageError("%s already exists; choose another --out (files are never overwritten)" % out)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    partial = out + ".part"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "genmedia-skills-pipeline/1"})
        with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT) as response, open(partial, "wb") as handle:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                handle.write(chunk)
        os.replace(partial, out)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        try:
            os.remove(partial)
        except OSError:
            pass
        return {"ok": False, "label": label, "step": step, "url": url,
                "message": "download failed: %s" % exc}, 1
    size = file_size(out)
    if not size:
        return {"ok": False, "label": label, "step": step, "url": url, "path": out,
                "message": "downloaded file is empty"}, 1
    append_local(label, {"step": step, "path": out, "url": url, "tool": "fetch",
                         "endpoint_id": endpoint, "request_id": request_id, "note": args.note})
    return {"ok": True, "label": label, "step": step, "path": out, "url": url, "bytes": size}, 0


def first_prompt(input_obj):
    if isinstance(input_obj, dict):
        for key in PROMPT_KEYS:
            if isinstance(input_obj.get(key), str):
                return input_obj[key]
    return None


def cmd_manifest(args):
    label = need_slug(args.label, "--label")
    requests, local = ledger_requests(label), local_assets(label)
    latest = latest_per_step(requests)
    problems, assets, attempts, by_status, total = [], [], {}, {}, 0.0
    for record in requests:
        step, status = step_name(record), record.get("status") or "unknown"
        attempts[step] = attempts.get(step, 0) + 1
        is_latest = latest.get(step) is record
        by_status[status] = by_status.get(status, 0) + 1
        cost = record.get("est_cost_usd")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool) and record.get("request_id"):
            total += cost
        files = []
        for output in record.get("outputs") or []:
            path = output.get("path")
            size = file_size(path)
            files.append({"path": path, "url": output.get("url"), "json_path": output.get("json_path"),
                          "bytes": size})
            if not is_latest or status != "completed":
                continue
            if not path and (record.get("download") is False or step in local):
                continue  # "download": false was planned, or the file was saved with `fetch` under this step
            if not path:
                problems.append("%s: output was not downloaded (%s); save it with `pipeline.py fetch "
                                "--label %s --step %s --out <path>`" % (step, output.get("url"), label, step))
            elif size is None:
                problems.append("%s: local file is missing: %s" % (step, path))
            elif size == 0:
                problems.append("%s: local file is empty: %s" % (step, path))
        asset = {"step": step, "attempt": attempts[step], "latest": is_latest,
                 "endpoint_id": record.get("endpoint_id"), "request_id": record.get("request_id"),
                 "status": status, "prompt": first_prompt(record.get("input")), "input": record.get("input"),
                 "files": files, "est_cost_usd": cost, "submitted_at": record.get("ts"),
                 "updated_at": record.get("updated")}
        if record.get("error"):
            asset["error"] = record["error"]
        assets.append(asset)
        if not is_latest:
            continue
        if status == "failed":
            error = record.get("error") or {}
            problems.append("%s: failed (%s): %s" % (step, error.get("kind") or "unknown",
                                                     str(error.get("message") or "")[:160]))
        elif status in UNFINISHED:
            problems.append("%s: %s" % (step, UNFINISHED[status]))
        elif status == "completed" and not files and step not in local:
            problems.append("%s: completed with no media URL in the result; read the result "
                            "(`gm.py wait <endpoint_id> <request_id> --refetch --no-download`) and "
                            "register the file with `fetch --url` or `add`" % step)
    local_list = []
    for step, entry in local.items():
        size = file_size(entry.get("path"))
        local_list.append(dict(entry, bytes=size))
        if size is None:
            problems.append("%s: local file is missing: %s" % (step, entry.get("path")))
        elif size == 0:
            problems.append("%s: local file is empty: %s" % (step, entry.get("path")))
    if not assets and not local_list:
        problems.append("no ledger entries and no local assets under label %s" % label)
    manifest = {"project": label, "generated_at": now(), "ledger": LEDGER,
                "totals": {"requests": len(assets), "steps": len(latest), "local_assets": len(local_list),
                           "by_status": by_status, "est_cost_usd": round(total, 4)},
                "assets": assets, "local": local_list, "problems": problems}
    folder = project_dir(label)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "manifest.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return {"ok": not problems, "label": label, "path": path, "requests": len(assets),
            "steps": len(latest), "local_assets": len(local_list), "by_status": by_status,
            "est_cost_usd": round(total, 4), "problems": problems}, int(bool(problems))


# ---------------------------------------------------------------- entry point
class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def build_parser():
    parser = Parser(prog="pipeline.py", description=__doc__,
                    formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True
    urls = sub.add_parser("urls", help="output URLs and paths per job id under a label")
    urls.add_argument("--label", required=True)
    urls.set_defaults(func=cmd_urls)
    fill = sub.add_parser("fill", help="resolve @job references in a stage plan template")
    fill.add_argument("--template", required=True, metavar="FILE")
    fill.add_argument("--out", required=True, metavar="FILE")
    fill.add_argument("--label")
    fill.add_argument("--placeholder", metavar="REGEX",
                      help="placeholder pattern to refuse; default %s" % PLACEHOLDER_RE.pattern)
    fill.add_argument("--allow-placeholders", action="store_true",
                      help="write the plan even when a placeholder is left in it")
    fill.set_defaults(func=cmd_fill)
    add = sub.add_parser("add", help="register a file made outside the ledger")
    add.add_argument("--label", required=True)
    add.add_argument("--step", required=True)
    add.add_argument("--path", required=True)
    add.add_argument("--url")
    add.add_argument("--tool")
    add.add_argument("--from", dest="sources", metavar="ID,ID")
    add.add_argument("--note")
    add.set_defaults(func=cmd_add)
    fetch = sub.add_parser("fetch", help="download a result URL the CLI did not save and register it")
    fetch.add_argument("--label", required=True)
    fetch.add_argument("--step", required=True)
    fetch.add_argument("--url", help="default: the step's first unsaved output URL in the ledger")
    fetch.add_argument("--index", type=int, metavar="N", help="which unsaved output URL to take (default 0)")
    fetch.add_argument("--out", required=True, metavar="PATH")
    fetch.add_argument("--endpoint")
    fetch.add_argument("--request-id", dest="request_id")
    fetch.add_argument("--note")
    fetch.set_defaults(func=cmd_fetch)
    manifest = sub.add_parser("manifest", help="write manifest.json and run the mechanical gate")
    manifest.add_argument("--label", required=True)
    manifest.set_defaults(func=cmd_manifest)
    return parser


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        result, code = args.func(args)
    except UsageError as exc:
        result, code = {"ok": False, "kind": "usage", "message": str(exc)}, 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
