#!/usr/bin/env python3
"""catalog.py - compact, quirk-proof reads of fal's model catalog through `genmedia models`.
Python 3.8+, stdlib only. Free calls only: this tool cannot spend money.

Prints ONE compact JSON object on stdout. Exit: 0 ok | 1 failed | 2 usage.
Never prints, stores or forwards the API key (FAL_KEY is scrubbed from error text).

  status <endpoint_id>[,<id>...]
      Exact-ID lookup, the only deprecation oracle. state per ID:
      active | deprecated | unlisted (bare object, no metadata) | removed (404).
      One removed ID fails a multi-ID call, so a 404 is retried one ID at a time.
  search <query> [--category C] [--limit 10] [--cursor TOKEN] [--all]
      Keyword search: best text match first, then newest (read `released`, not the position).
      Always sends --no-classify (the CLI otherwise guesses a category and can return zero rows). --all adds deprecated models (`--status all`); each row carries its
      status. Unlisted and removed IDs never show up in a search: use `status` for those.
  leaders <category>[,<category>...] [--limit 15]
      fal's default (popularity-like) order inside each category, with rank.
  new-since <YYYY-MM-DD> [--category C[,C...]] [--max-pages 20] [--max-rows 60]
      Pages the catalog (limit 100 + cursor) and keeps models released on or after the date.
      List order is not by date, so every page is read; complete:false means --max-pages stopped it.

Rows: {endpoint_id, name, category, released, status, about}. `about` is the description cut to 140
characters. Errors: {ok:false, kind, http_status, message}; kind is
not_found|rate_limit|auth|validation|server|unknown or usage|cli_missing (raised here).
Env: GM_GENMEDIA_BIN (binary override), GM_CATALOG_BACKOFF (first 429 wait in seconds, default 8),
GM_CATALOG_PACE (pause between consecutive catalog calls in seconds, default 0.3).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

API_LIMIT = 100          # the catalog API rejects larger pages
FIND_MAX_IDS = 50        # documented maximum of IDs per exact lookup
CALL_TIMEOUT = 60        # seconds per CLI call
RETRIES_429 = 3
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9._-]+)+$")


class CatalogError(Exception):
    def __init__(self, kind, message, http_status=None, code=1):
        Exception.__init__(self, message)
        self.kind, self.message, self.http_status, self.code = kind, message, http_status, code


def redact(text):
    key = os.environ.get("FAL_KEY") or ""
    text = text or ""
    if len(key) >= 8:
        text = text.replace(key, "[redacted]")
    return text


def emit(doc, code=0):
    sys.stdout.write(redact(json.dumps(doc, ensure_ascii=False, separators=(",", ":"))) + "\n")
    return code


def binary():
    path = shutil.which(os.environ.get("GM_GENMEDIA_BIN") or "genmedia")
    if not path:
        raise CatalogError("cli_missing", "genmedia is not on PATH; see /genmedia-skills:setup")
    return path


def env_seconds(name, default):
    try:
        return max(0.0, float(os.environ.get(name) or default))
    except ValueError:
        return float(default)


def backoff_seconds():
    return env_seconds("GM_CATALOG_BACKOFF", "8")


_calls_made = [0]


def pace():
    """The catalog API throttles bursts: pause before every call after the first."""
    if _calls_made[0]:
        time.sleep(env_seconds("GM_CATALOG_PACE", "0.3"))
    _calls_made[0] += 1


def parse_error(stderr, returncode):
    """The CLI prints {error, details} JSON on stderr after whatever noise the shell adds."""
    text = stderr or ""
    doc = None
    for match in re.finditer(r"^\{", text, re.M):
        try:
            doc, _ = json.JSONDecoder().raw_decode(text[match.start():])
            break
        except ValueError:
            continue
    message = (doc or {}).get("error") if isinstance(doc, dict) else None
    details = (doc or {}).get("details") if isinstance(doc, dict) else None
    blob = " ".join(str(part) for part in (message, details) if part) or text[-400:]
    status = None
    found = re.search(r"\((\d{3})\)", str(message or "")) or re.search(r"\bstatus:\s*(\d{3})\b", text)
    if found:
        status = int(found.group(1))
    if status is None and re.search(r"no fal\.ai api key|api key", blob, re.I):
        status = 401
    kind = {400: "validation", 401: "auth", 403: "auth", 404: "not_found", 422: "validation",
            429: "rate_limit"}.get(status or 0)
    if kind is None:
        kind = "server" if status and status >= 500 else "unknown"
    inner = None
    if isinstance(details, str):
        try:
            parsed = json.loads(details)
            err = parsed.get("error") if isinstance(parsed, dict) else None
            inner = err.get("message") if isinstance(err, dict) else parsed.get("message")
        except (ValueError, AttributeError):
            inner = details.strip()[:300]
    text_out = "%s%s" % (message or "genmedia models failed (exit %s)" % returncode,
                         ": %s" % inner if inner else "")
    return CatalogError(kind, redact(text_out.strip()), status)


def call_models(args):
    """Run `genmedia models <args> --json`; stdout and stderr stay separate. Retries 429 only."""
    argv = [binary(), "models"] + list(args) + ["--json"]
    env = dict(os.environ, NO_COLOR="1")
    wait = backoff_seconds()
    for attempt in range(RETRIES_429 + 1):
        pace()
        try:
            proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                                  timeout=CALL_TIMEOUT, universal_newlines=True)
        except subprocess.TimeoutExpired:
            raise CatalogError("unknown", "genmedia models did not answer within %d s" % CALL_TIMEOUT)
        except OSError as exc:
            raise CatalogError("cli_missing", "cannot run genmedia: %s" % exc)
        if proc.returncode == 0:
            try:
                doc = json.loads(proc.stdout)
            except ValueError:
                raise CatalogError("unknown", "genmedia models printed no JSON (usage text?): %s"
                                   % redact(proc.stdout.strip()[:200]))
            if not isinstance(doc, dict) or not isinstance(doc.get("models"), list):
                raise CatalogError("unknown", "unexpected `genmedia models` output shape")
            return doc
        error = parse_error(proc.stderr, proc.returncode)
        if error.kind == "rate_limit" and attempt < RETRIES_429:
            time.sleep(wait)
            wait *= 2
            continue
        raise error
    raise CatalogError("rate_limit", "catalog API still rate-limited after %d retries" % RETRIES_429, 429)


def row(model, rank=None):
    about = " ".join(str(model.get("description") or "").split())
    if len(about) > 140:
        about = about[:137].rstrip() + "..."
    out = {"endpoint_id": model.get("endpoint_id"), "name": model.get("name"),
           "category": model.get("category"), "released": (model.get("date") or "")[:10] or None,
           "status": model.get("status"), "about": about or None}
    if rank is not None:
        out["rank"] = rank
    return out


def state_of(model):
    status = model.get("status")
    if status in ("active", "deprecated"):
        return status
    if status is None and not model.get("name") and not model.get("category"):
        return "unlisted"
    return str(status)


def split_csv(value, what):
    items = [part.strip() for part in str(value).split(",") if part.strip()]
    if not items:
        raise CatalogError("usage", "no %s given" % what, code=2)
    return items


def status_entry(endpoint_id, model):
    if model is None:
        return {"endpoint_id": endpoint_id, "state": "removed", "name": None, "category": None,
                "released": None, "updated": None}
    return {"endpoint_id": endpoint_id, "state": state_of(model), "name": model.get("name"),
            "category": model.get("category"), "released": (model.get("date") or "")[:10] or None,
            "updated": (model.get("updated_at") or "")[:10] or None}


def cmd_status(ns):
    ids = []
    for chunk in ns.ids:
        ids.extend(split_csv(chunk, "endpoint IDs"))
    ids = list(dict.fromkeys(ids))
    bad = [one for one in ids if not ID_RE.match(one)]
    if bad:
        raise CatalogError("usage", "not an endpoint ID (owner/model...): %s" % ", ".join(bad), code=2)
    if len(ids) > FIND_MAX_IDS:
        raise CatalogError("usage", "at most %d IDs per call" % FIND_MAX_IDS, code=2)
    found, calls = {}, 0
    try:
        calls += 1
        doc = call_models(["--endpoint_id", ",".join(ids)])
        found = {m.get("endpoint_id"): m for m in doc["models"]}
        results = [status_entry(one, found.get(one)) for one in ids]
    except CatalogError as exc:
        if exc.kind != "not_found":
            raise
        results = []
        for one in ids:                      # a removed ID fails the whole call: isolate it
            if len(ids) == 1:
                results.append(status_entry(one, None))
                break
            try:
                calls += 1
                doc = call_models(["--endpoint_id", one])
                model = next((m for m in doc["models"] if m.get("endpoint_id") == one), None)
                results.append(status_entry(one, model))
            except CatalogError as inner:
                if inner.kind != "not_found":
                    raise
                results.append(status_entry(one, None))
    usable = [r["endpoint_id"] for r in results if r["state"] == "active"]
    return {"ok": True, "results": results, "active": usable,
            "not_active": [r["endpoint_id"] for r in results if r["state"] != "active"], "calls": calls}


def clamp_limit(value, warnings):
    if value < 1:
        raise CatalogError("usage", "--limit must be >= 1", code=2)
    if value > API_LIMIT:
        warnings.append("limit lowered to %d (API maximum); use --cursor for more" % API_LIMIT)
        return API_LIMIT
    return value


def cmd_search(ns):
    warnings = []
    query = " ".join(ns.query.split())
    if not query:
        raise CatalogError("usage", "empty query", code=2)
    args = [query, "--no-classify", "--limit", str(clamp_limit(ns.limit, warnings))]
    if ns.category:
        args += ["--category", ns.category]
    if ns.cursor:
        args += ["--cursor", ns.cursor]
    if ns.all:
        args += ["--status", "all"]
    doc = call_models(args)
    out = {"ok": True, "query": query, "category": ns.category or None, "order": "best match first, then newest",
           "includes_deprecated": bool(ns.all),
           "count": len(doc["models"]), "has_more": bool(doc.get("has_more")),
           "next_cursor": doc.get("next_cursor"), "rows": [row(m) for m in doc["models"]]}
    if warnings:
        out["warnings"] = warnings
    return out


def cmd_leaders(ns):
    warnings = []
    limit = clamp_limit(ns.limit, warnings)
    categories = {}
    for category in split_csv(ns.categories, "categories"):
        doc = call_models(["--category", category, "--limit", str(limit)])
        categories[category] = [row(m, rank) for rank, m in enumerate(doc["models"], 1)]
    out = {"ok": True, "order": "fal default order (popularity-like, not quality, not date)",
           "categories": categories}
    empty = [name for name, rows in categories.items() if not rows]
    if empty:
        warnings.append("no models in: %s (category names are exact strings)" % ", ".join(empty))
    if warnings:
        out["warnings"] = warnings
    return out


def cmd_new_since(ns):
    if not DATE_RE.match(ns.date):
        raise CatalogError("usage", "date must be YYYY-MM-DD", code=2)
    if ns.max_pages < 1 or ns.max_rows < 1:
        raise CatalogError("usage", "--max-pages and --max-rows must be >= 1", code=2)
    scopes = split_csv(ns.category, "categories") if ns.category else [None]
    seen, rows, pages, scanned, complete = set(), [], 0, 0, True
    for category in scopes:
        cursor = None
        while True:
            if pages >= ns.max_pages:
                complete = False
                break
            args = ["--limit", str(API_LIMIT)]
            if category:
                args += ["--category", category]
            if cursor:
                args += ["--cursor", cursor]
            doc = call_models(args)
            pages += 1
            for model in doc["models"]:
                scanned += 1
                endpoint_id = model.get("endpoint_id")
                if endpoint_id in seen:
                    continue
                seen.add(endpoint_id)
                if (model.get("date") or "")[:10] >= ns.date:
                    rows.append(row(model))
            cursor = doc.get("next_cursor")
            if not doc.get("has_more") or not cursor:
                break
        if not complete:
            break
    rows.sort(key=lambda r: (r["released"] or "", r["endpoint_id"] or ""), reverse=True)
    counts = {}
    for one in rows:
        counts[one["category"] or "unknown"] = counts.get(one["category"] or "unknown", 0) + 1
    out = {"ok": True, "since": ns.date, "categories": [c for c in scopes if c] or "all",
           "pages": pages, "scanned": scanned, "complete": complete, "total": len(rows),
           "counts": counts, "rows": rows[:ns.max_rows]}
    if len(rows) > ns.max_rows:
        out["truncated"] = len(rows) - ns.max_rows
    if not complete:
        out["warnings"] = ["stopped at --max-pages %d; the list is not by date, so newer models may "
                           "be missing: narrow --category or raise --max-pages" % ns.max_pages]
    return out


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CatalogError("usage", message, code=2)


def build_parser():
    parser = Parser(prog="catalog.py", description=__doc__,
                    formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>", parser_class=Parser)
    one = sub.add_parser("status", help="exact-ID lookup: active | deprecated | unlisted | removed")
    one.add_argument("ids", nargs="+", metavar="id[,id...]")
    one.set_defaults(func=cmd_status)
    one = sub.add_parser("search", help="keyword search (best match, then newest), never auto-classified")
    one.add_argument("query")
    one.add_argument("--category")
    one.add_argument("--limit", type=int, default=10)
    one.add_argument("--cursor")
    one.add_argument("--all", action="store_true", help="include deprecated models")
    one.set_defaults(func=cmd_search)
    one = sub.add_parser("leaders", help="fal's default order inside one or more categories")
    one.add_argument("categories", metavar="category[,category...]")
    one.add_argument("--limit", type=int, default=15)
    one.set_defaults(func=cmd_leaders)
    one = sub.add_parser("new-since", help="models released on or after a date")
    one.add_argument("date", metavar="YYYY-MM-DD")
    one.add_argument("--category", metavar="C[,C...]")
    one.add_argument("--max-pages", type=int, default=20)
    one.add_argument("--max-rows", type=int, default=60)
    one.set_defaults(func=cmd_new_since)
    return parser


def main(argv=None):
    try:
        ns = build_parser().parse_args(argv)
        if not getattr(ns, "func", None):
            raise CatalogError("usage", "missing command: status | search | leaders | new-since", code=2)
        return emit(ns.func(ns))
    except CatalogError as exc:
        return emit({"ok": False, "kind": exc.kind, "http_status": exc.http_status,
                     "message": exc.message}, exc.code)
    except KeyboardInterrupt:
        return emit({"ok": False, "kind": "unknown", "http_status": None, "message": "interrupted"}, 1)


if __name__ == "__main__":
    sys.exit(main())
