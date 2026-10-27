#!/usr/bin/env python3
"""character.py - local character sheets for the genmedia-skills `character` skill.

Python 3.8+, stdlib only. Prints ONE compact JSON object on stdout.
Exit: 0 ok | 1 failed | 2 usage (nothing was written or sent).

State lives in the project cwd:
  .genmedia/characters/<handle>/character.json   the sheet (source of truth)
  .genmedia/characters/<handle>/refs/<id>-<role>.<ext>   copies of the reference images
  .genmedia/characters/<handle>/dataset.zip      only after `pack`

  init <handle> --name <name> --description <anchor> [--style <notes>] [--real-person --consent]
  update <handle> [--name] [--description] [--style] [--real-person --consent]
      Old anchors are kept in anchor_history (last 10).
  add-ref <handle> <image>... --role face|full-body|turnaround|expression|outfit
      [--cdn-url <https url>] [--note <text>]
      Copies the file into refs/. Order within a role is priority: add the best first.
      --cdn-url records a URL you already have (one file only), e.g. the output URL of the
      generation that made the image, so `resolve` does not upload it again.
  drop-ref <handle> <ref-id>... [--restore]
      De-lists a reference (the file stays on disk); --restore brings it back.
  list
  show <handle>
  resolve <handle>... [--max 8] [--roles face,full-body] [--refresh | --no-upload]
      -> {description, style, urls:[...], legend:[{index,handle,ref,role}], characters:[...]}
      Picks references round-robin over the roles (face first) up to --max; several handles
      share --max evenly. A picked reference WITHOUT a cdn_url is uploaded through
      `gm.py upload`; --refresh re-uploads every picked reference; --no-upload never uploads.
      Uploading is an external side effect: the file gets a public, expiring URL on the
      user's fal account. Nothing else in this script touches the network.
  set-trained <handle> --type profile|lora --endpoint <inference endpoint id>
      [--profile-id <id> | --lora-url <https url>] [--trigger <phrase>] [--trainer <endpoint id>]
      [--scale <n>] | --clear
  set-mirror <handle> --character-id <fal Assets character id> | --clear
  pack <handle> [--from <dir>]... [--no-refs] [--caption <text>] [--out <zip>]
      Builds a training ZIP (001.jpg, 002.png, ... plus optional 001.txt captions) locally.
      Never uploads it and never starts a training job.

This script never calls a generation or training endpoint. The only command it ever passes to
gm.py is `upload`.
Env (tests): GM_HELPER = path to gm.py (default: next to this file).
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

SCHEMA_VERSION = 1
BASE_DIR = os.path.join(".genmedia", "characters")
ROLES = ("face", "full-body", "turnaround", "expression", "outfit")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
HANDLE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
ENDPOINT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)+$")
DEFAULT_MAX = 8
STALE_DAYS = 7            # fal documents "at least 7 days by default" for CDN files
BIG_FILE_BYTES = 10 * 1024 * 1024
MIRROR_MAX_REFS = 20      # fal Assets characters accept 1-20 reference images
MIRROR_MAX_DESCRIPTION = 2000
HISTORY_KEEP = 10
UPLOAD_TIMEOUT = 600


class CharError(Exception):
    def __init__(self, payload, code=1):
        Exception.__init__(self, payload.get("message", ""))
        self.payload, self.code = payload, code


def fail(kind, message, code=1, **extra):
    payload = {"ok": False, "kind": kind, "message": message}
    payload.update(extra)
    return CharError(payload, code)


def usage(message):
    return fail("usage", message, 2)


# ---------------------------------------------------------------- small helpers
def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(text):
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None


def age_days(text):
    moment = parse_iso(text)
    return None if moment is None else max(0, (now() - moment).days)


def norm_handle(raw):
    handle = str(raw or "").strip().lstrip("@").lower()
    if not HANDLE_RE.match(handle):
        raise usage("handle %r is invalid: use a-z, 0-9, '-' or '_', start with a letter or digit, "
                    "at most 64 characters" % raw)
    return handle


def sheet_dir(handle):
    return os.path.join(BASE_DIR, handle)


def sheet_path(handle):
    return os.path.join(sheet_dir(handle), "character.json")


def known_handles():
    if not os.path.isdir(BASE_DIR):
        return []
    return sorted(entry for entry in os.listdir(BASE_DIR)
                  if os.path.isfile(os.path.join(BASE_DIR, entry, "character.json")))


def load(handle):
    path = sheet_path(handle)
    if not os.path.isfile(path):
        raise fail("not_found", "no character @%s in %s" % (handle, BASE_DIR), available=known_handles())
    try:
        with open(path, "r", encoding="utf-8") as fh:
            sheet = json.load(fh)
    except (OSError, ValueError) as exc:
        raise fail("io", "cannot read %s: %s" % (path, exc))
    if not isinstance(sheet, dict) or not isinstance(sheet.get("refs", []), list):
        raise fail("io", "%s is not a character sheet" % path)
    sheet.setdefault("refs", [])
    return sheet


def save(handle, sheet):
    sheet["updated_at"] = iso(now())
    folder = sheet_dir(handle)
    os.makedirs(os.path.join(folder, "refs"), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".character-", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(sheet, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp, sheet_path(handle))
    except OSError as exc:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise fail("io", "cannot write the sheet: %s" % exc)


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def active_refs(sheet):
    return [ref for ref in sheet["refs"] if ref.get("active", True)]


def count_by_role(refs):
    counts = {}
    for ref in refs:
        counts[ref.get("role")] = counts.get(ref.get("role"), 0) + 1
    return counts


def ref_file(handle, ref):
    """Path of a reference file, or "" when the sheet points outside its own folder.

    character.json can be hand-edited; a `path` that climbs out of the folder must never reach
    `gm.py upload` or a training ZIP, so anything that escapes the sheet folder counts as missing.
    """
    base = os.path.realpath(sheet_dir(handle))
    path = os.path.realpath(os.path.join(base, str(ref.get("path") or "")))
    return path if path.startswith(base + os.sep) else ""


def check_https(value, flag):
    if not re.match(r"^https://\S+$", value or ""):
        raise usage("%s must be an https:// URL" % flag)
    return value


def anchor_warnings(description):
    warnings = []
    if len(description) < 60:
        warnings.append("anchor is short (%d chars): name face, hair, skin marks, build, age range and "
                        "signature items" % len(description))
    if len(description) > MIRROR_MAX_DESCRIPTION:
        warnings.append("anchor exceeds %d chars: too long for a fal Assets mirror and for most prompts"
                        % MIRROR_MAX_DESCRIPTION)
    return warnings


def apply_consent(sheet, args):
    if args.real_person:
        if not args.consent:
            raise fail("consent", "a real person needs the user's confirmation that they have that "
                                  "person's consent: ask, then pass --real-person --consent", 2)
        sheet["real_person"] = True
        sheet["consent_confirmed_at"] = iso(now())
    elif args.consent:
        raise usage("--consent only makes sense together with --real-person")


# ---------------------------------------------------------------- commands
def cmd_init(args):
    handle = norm_handle(args.handle)
    if os.path.isfile(sheet_path(handle)):
        raise fail("exists", "character @%s already exists; use `update`, or pick another handle" % handle)
    name, description = args.name.strip(), args.description.strip()
    if not name or not description:
        raise usage("--name and --description must not be empty")
    sheet = {"schema": SCHEMA_VERSION, "handle": handle, "name": name, "description": description,
             "style": (args.style or "").strip(), "real_person": False, "consent_confirmed_at": None,
             "refs": [], "next_ref": 1,
             "created_at": iso(now())}
    apply_consent(sheet, args)
    save(handle, sheet)
    return {"ok": True, "handle": handle, "name": name, "path": sheet_path(handle),
            "real_person": sheet["real_person"], "warnings": anchor_warnings(description),
            "next": "add-ref %s <image> --role face" % handle}, 0


def cmd_update(args):
    handle = norm_handle(args.handle)
    sheet = load(handle)
    changed = []
    if args.name is not None:
        if not args.name.strip():
            raise usage("--name must not be empty")
        sheet["name"] = args.name.strip()
        changed.append("name")
    if args.description is not None:
        description = args.description.strip()
        if not description:
            raise usage("--description must not be empty")
        if description != sheet.get("description"):
            history = sheet.setdefault("anchor_history", [])
            history.append({"ts": iso(now()), "description": sheet.get("description", "")})
            del history[:-HISTORY_KEEP]
            sheet["description"] = description
            changed.append("description")
    if args.style is not None:
        sheet["style"] = args.style.strip()
        changed.append("style")
    if args.real_person or args.consent:
        apply_consent(sheet, args)
        changed.append("real_person")
    if not changed:
        raise usage("nothing to update: pass --name, --description, --style or --real-person --consent")
    save(handle, sheet)
    return {"ok": True, "handle": handle, "changed": changed,
            "warnings": anchor_warnings(sheet.get("description", ""))}, 0


def cmd_add_ref(args):
    handle = norm_handle(args.handle)
    sheet = load(handle)
    if args.cdn_url is not None:
        check_https(args.cdn_url, "--cdn-url")
        if len(args.files) != 1:
            raise usage("--cdn-url describes exactly one file")
    sources = []
    for source in args.files:  # validate everything before the first copy
        if not os.path.isfile(source):
            raise fail("not_found", "file not found: %s" % source, 2)
        ext = os.path.splitext(source)[1].lower()
        if ext not in IMAGE_EXTS:
            raise usage("%s: references must be %s" % (source, ", ".join(IMAGE_EXTS)))
        size = os.path.getsize(source)
        if size == 0:
            raise usage("%s is empty" % source)
        sources.append((source, ext, size))
    refs_dir = os.path.join(sheet_dir(handle), "refs")
    os.makedirs(refs_dir, exist_ok=True)
    added, duplicates, warnings = [], [], []
    for source, ext, size in sources:
        digest = file_sha256(source)
        twin = next((ref for ref in sheet["refs"] if ref.get("sha256") == digest), None)
        if twin is not None:
            restored = not twin.get("active", True)
            twin["active"] = True
            if restored:
                twin["role"] = args.role
            if args.cdn_url and not twin.get("cdn_url"):
                twin["cdn_url"], twin["uploaded_at"] = args.cdn_url, iso(now())
            duplicates.append({"id": twin["id"], "source": source, "restored": restored})
            continue
        ref_id = "r%d" % int(sheet.get("next_ref") or (len(sheet["refs"]) + 1))
        sheet["next_ref"] = int(ref_id[1:]) + 1
        inside = os.path.realpath(os.path.dirname(source)) == os.path.realpath(refs_dir)
        filename = os.path.basename(source) if inside else "%s-%s%s" % (ref_id, args.role, ext)
        if not inside:
            try:
                shutil.copyfile(source, os.path.join(refs_dir, filename))
            except OSError as exc:
                raise fail("io", "cannot copy %s: %s" % (source, exc))
        ref = {"id": ref_id, "role": args.role, "path": "refs/" + filename, "sha256": digest, "bytes": size,
               "cdn_url": args.cdn_url, "uploaded_at": iso(now()) if args.cdn_url else None,
               "added_at": iso(now()), "note": (args.note or "").strip(), "active": True}
        sheet["refs"].append(ref)
        added.append({"id": ref_id, "role": args.role, "path": ref["path"], "source": source})
        if size > BIG_FILE_BYTES:
            warnings.append("%s is %.1f MB: several models reject reference images above 10 MB"
                            % (ref_id, size / 1048576.0))
    save(handle, sheet)
    live = active_refs(sheet)
    if len(live) > MIRROR_MAX_REFS:
        warnings.append("%d active references: a fal Assets mirror accepts %d at most" % (len(live), MIRROR_MAX_REFS))
    if not any(ref.get("role") == "face" for ref in live):
        warnings.append("no `face` reference yet: identity rests on it")
    return {"ok": True, "handle": handle, "added": added, "duplicates": duplicates,
            "refs_total": len(live), "by_role": count_by_role(live), "warnings": warnings}, 0


def cmd_drop_ref(args):
    handle = norm_handle(args.handle)
    sheet = load(handle)
    by_id = {ref.get("id"): ref for ref in sheet["refs"]}
    missing = [ref_id for ref_id in args.refs if ref_id not in by_id]
    if missing:
        raise fail("not_found", "unknown reference id(s): %s" % ", ".join(missing), 2,
                   available=sorted(by_id))
    for ref_id in args.refs:
        by_id[ref_id]["active"] = bool(args.restore)
    save(handle, sheet)
    live = active_refs(sheet)
    return {"ok": True, "handle": handle, "restored" if args.restore else "dropped": list(args.refs),
            "refs_total": len(live), "by_role": count_by_role(live),
            "note": "files stay in refs/; dropped references are ignored by resolve and pack"}, 0


def cmd_list(_args):
    rows = []
    for handle in known_handles():
        try:
            sheet = load(handle)
        except CharError as exc:
            rows.append({"handle": handle, "error": exc.payload.get("message")})
            continue
        live = active_refs(sheet)
        rows.append({"handle": handle, "name": sheet.get("name"), "refs": len(live),
                     "by_role": count_by_role(live), "real_person": bool(sheet.get("real_person")),
                     "trained": (sheet.get("trained") or {}).get("type"),
                     "mirrored": bool((sheet.get("fal_assets") or {}).get("character_id")),
                     "updated_at": sheet.get("updated_at")})
    return {"ok": True, "dir": BASE_DIR, "count": len(rows), "characters": rows}, 0


def cmd_show(args):
    handle = norm_handle(args.handle)
    sheet = load(handle)
    live = active_refs(sheet)
    missing_files = [ref["id"] for ref in live if not os.path.isfile(ref_file(handle, ref))]
    no_url = [ref["id"] for ref in live if not ref.get("cdn_url")]
    stale = [ref["id"] for ref in live if ref.get("cdn_url") and (age_days(ref.get("uploaded_at")) or 0) > STALE_DAYS]
    checks = {"refs_active": len(live), "refs_dropped": len(sheet["refs"]) - len(live),
              "by_role": count_by_role(live), "missing_files": missing_files, "without_cdn_url": no_url,
              "cdn_url_older_than_%d_days" % STALE_DAYS: stale,
              "has_face": any(ref.get("role") == "face" for ref in live)}
    return {"ok": True, "path": sheet_path(handle), "character": sheet, "checks": checks}, 0


def pick_refs(refs, roles, limit):
    """Round-robin over roles in priority order; within a role, stored order is priority."""
    queues = [[ref for ref in refs if ref.get("role") == role] for role in roles]
    picked = []
    while len(picked) < limit and any(queues):
        for queue in queues:
            if queue and len(picked) < limit:
                picked.append(queue.pop(0))
    return picked


def gm_upload(paths):
    """Run `gm.py upload <paths>`; returns ({abs_path: cdn_url}, {abs_path: error}). Upload only."""
    helper = os.environ.get("GM_HELPER") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "gm.py")
    if not os.path.isfile(helper):
        raise fail("helper_missing", "gm.py not found next to character.py (%s)" % helper)
    try:
        proc = subprocess.run([sys.executable, helper, "upload"] + paths, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, timeout=UPLOAD_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise fail("upload", "gm.py upload timed out after %d s" % UPLOAD_TIMEOUT)
    except OSError as exc:
        raise fail("upload", "cannot start gm.py: %s" % exc)
    lines = [line for line in proc.stdout.decode("utf-8", "replace").splitlines() if line.strip()]
    try:
        result = json.loads(lines[-1]) if lines else {}
    except ValueError:
        result = {}
    if not isinstance(result, dict) or "files" not in result:
        message = result.get("message") if isinstance(result, dict) else None
        raise fail("upload", message or "gm.py upload returned no file list (exit %d)" % proc.returncode,
                   gm=result if isinstance(result, dict) and result else None)
    urls, errors = {}, {}
    for path, entry in zip(paths, result.get("files") or []):
        if entry.get("cdn_url"):
            urls[path] = entry["cdn_url"]
        else:
            errors[path] = (entry.get("error") or {}).get("message") or "upload failed"
    for path in paths:
        if path not in urls and path not in errors:
            errors[path] = "upload failed"
    return urls, errors


def cmd_resolve(args):
    handles = []
    for raw in args.handles:
        handle = norm_handle(raw)
        if handle not in handles:
            handles.append(handle)
    if args.max < 1:
        raise usage("--max must be at least 1")
    if args.max < len(handles):
        raise usage("--max %d cannot cover %d characters: each needs at least one reference"
                    % (args.max, len(handles)))
    roles = list(ROLES)
    if args.roles:
        roles = [part.strip() for part in args.roles.split(",") if part.strip()]
        unknown = [role for role in roles if role not in ROLES]
        if unknown or not roles:
            raise usage("--roles takes a comma list of: %s" % ", ".join(ROLES))
    sheets = {handle: load(handle) for handle in handles}  # fail before any upload
    share, extra = divmod(args.max, len(handles))
    warnings, skipped, plan = [], [], []
    for position, handle in enumerate(handles):
        usable = []
        for ref in active_refs(sheets[handle]):
            has_file = os.path.isfile(ref_file(handle, ref))
            if not has_file and not ref.get("cdn_url"):
                skipped.append({"handle": handle, "ref": ref["id"], "why": "file missing and no cdn_url"})
            elif args.no_upload and not ref.get("cdn_url"):
                skipped.append({"handle": handle, "ref": ref["id"], "why": "no cdn_url and --no-upload"})
            else:
                usable.append(ref)
        picked = pick_refs(usable, roles, share + (1 if position < extra else 0))
        if not picked:
            raise fail("no_refs", "@%s has no usable reference for roles %s" % (handle, ",".join(roles)),
                       skipped=skipped)
        if not any(ref.get("role") == "face" for ref in picked):
            warnings.append("@%s: no `face` reference in this selection" % handle)
        plan.append((handle, picked))

    to_upload = []
    for handle, picked in plan:
        for ref in picked:
            path = ref_file(handle, ref)  # absolute, inside the sheet folder, or ""
            if not ref.get("cdn_url") or args.refresh:
                if os.path.isfile(path):
                    to_upload.append((handle, ref, path))
                else:
                    warnings.append("@%s %s: local file missing, kept the old cdn_url" % (handle, ref["id"]))
    errors = []
    if to_upload:
        urls, failed = gm_upload([path for _, _, path in to_upload])
        stamp = iso(now())
        for handle, ref, path in to_upload:
            if path in urls:
                ref["cdn_url"], ref["uploaded_at"] = urls[path], stamp
            else:
                errors.append({"handle": handle, "ref": ref["id"], "message": failed.get(path, "upload failed")})
        for handle in {handle for handle, _, _ in to_upload}:
            save(handle, sheets[handle])

    all_urls, legend, characters = [], [], []
    for handle, picked in plan:
        sheet, indexes, own_urls = sheets[handle], [], []
        for ref in picked:
            if not ref.get("cdn_url"):
                continue
            all_urls.append(ref["cdn_url"])
            own_urls.append(ref["cdn_url"])
            indexes.append(len(all_urls))
            legend.append({"index": len(all_urls), "handle": handle, "ref": ref["id"], "role": ref.get("role")})
            days = age_days(ref.get("uploaded_at"))
            if days is not None and days > STALE_DAYS:
                warnings.append("@%s %s: cdn_url is %d days old; on file_download_error rerun with --refresh"
                                % (handle, ref["id"], days))
        characters.append({"handle": handle, "name": sheet.get("name"), "description": sheet.get("description"),
                           "style": sheet.get("style") or "", "real_person": bool(sheet.get("real_person")),
                           "trained": sheet.get("trained"), "indexes": indexes, "urls": own_urls})
    empty = [entry["handle"] for entry in characters if not entry["urls"]]
    result = {"ok": not errors and not empty, "urls": all_urls, "legend": legend, "characters": characters,
              "uploaded": len(to_upload) - len(errors), "skipped": skipped, "warnings": warnings}
    if len(characters) == 1:
        only = characters[0]
        result.update(handle=only["handle"], name=only["name"], description=only["description"],
                      style=only["style"], real_person=only["real_person"], trained=only["trained"])
    if to_upload:
        result["note"] = "uploaded references now have public, expiring URLs on the user's fal account"
    if errors or empty:
        result.update(kind="upload" if errors else "no_refs", errors=errors,
                      message="some references could not be uploaded" if errors
                      else "no usable reference for: %s" % ", ".join(empty))
        return result, 1
    return result, 0


def cmd_set_trained(args):
    handle = norm_handle(args.handle)
    sheet = load(handle)
    if args.clear:
        sheet.pop("trained", None)
        save(handle, sheet)
        return {"ok": True, "handle": handle, "trained": None}, 0
    if not args.type or not args.endpoint:
        raise usage("set-trained needs --type and --endpoint (or --clear)")
    if not ENDPOINT_RE.match(args.endpoint) or (args.trainer and not ENDPOINT_RE.match(args.trainer)):
        raise usage("--endpoint and --trainer must look like owner/model[/variant]")
    trained = {"type": args.type, "endpoint": args.endpoint, "trainer": args.trainer,
               "trigger": args.trigger, "trained_at": iso(now())}
    if args.type == "profile":
        if not args.profile_id or args.lora_url:
            raise usage("--type profile needs --profile-id (and no --lora-url)")
        trained["profile_id"] = args.profile_id
    else:
        if not args.lora_url or args.profile_id:
            raise usage("--type lora needs --lora-url (and no --profile-id)")
        trained["url"] = check_https(args.lora_url, "--lora-url")
        if args.scale is not None:
            trained["scale"] = args.scale
    sheet["trained"] = {key: value for key, value in trained.items() if value is not None}
    save(handle, sheet)
    return {"ok": True, "handle": handle, "trained": sheet["trained"]}, 0


def cmd_set_mirror(args):
    handle = norm_handle(args.handle)
    sheet = load(handle)
    if args.clear:
        sheet.pop("fal_assets", None)
    elif args.character_id:
        sheet["fal_assets"] = {"character_id": args.character_id, "synced_at": iso(now())}
    else:
        raise usage("set-mirror needs --character-id or --clear")
    save(handle, sheet)
    return {"ok": True, "handle": handle, "fal_assets": sheet.get("fal_assets")}, 0


def cmd_pack(args):
    handle = norm_handle(args.handle)
    sheet = load(handle)
    candidates = []
    if not args.no_refs:
        candidates += [ref_file(handle, ref) for ref in active_refs(sheet)]
    for folder in args.sources or []:
        if not os.path.isdir(folder):
            raise fail("not_found", "--from %s is not a directory" % folder, 2)
        candidates += [os.path.join(folder, entry) for entry in sorted(os.listdir(folder))
                       if os.path.splitext(entry)[1].lower() in IMAGE_EXTS]
    seen, images, warnings = set(), [], []
    for path in candidates:
        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            warnings.append("skipped (missing or empty): %s" % path)
            continue
        digest = file_sha256(path)
        if digest in seen:
            continue
        seen.add(digest)
        images.append(path)
    if not images:
        raise fail("no_refs", "nothing to pack: add references or pass --from <dir> with images")
    out = args.out or os.path.join(sheet_dir(handle), "dataset.zip")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    caption = (args.caption or "").strip()
    try:
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
            for number, path in enumerate(images, 1):
                stem = "%03d" % number
                archive.write(path, stem + os.path.splitext(path)[1].lower())
                if caption:
                    archive.writestr(stem + ".txt", caption)
    except OSError as exc:
        raise fail("io", "cannot write %s: %s" % (out, exc))
    count = len(images)
    if count < 10:
        warnings.append("%d images: the LoRA trainers ask for at least 10" % count)
    return {"ok": True, "handle": handle, "zip": out, "images": count, "captions": bool(caption),
            "bytes": os.path.getsize(out),
            "fits": {"lora_10_plus": count >= 10, "phota_30_to_50": 30 <= count <= 50},
            "warnings": warnings,
            "next": "upload the ZIP yourself only after the user confirmed the training cost"}, 0


# ---------------------------------------------------------------- argument parsing
class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise usage("%s (see `%s --help`)" % (message, self.prog))


def build_parser():
    parser = Parser(prog="character.py", description=__doc__,
                    formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    def add(name, func, summary):
        command = sub.add_parser(name, help=summary, description=summary)
        command.set_defaults(func=func)
        return command

    def consent_flags(command):
        command.add_argument("--real-person", action="store_true", help="the character depicts a real person")
        command.add_argument("--consent", action="store_true",
                             help="the user confirmed they have that person's consent")

    init = add("init", cmd_init, "create a character sheet")
    init.add_argument("handle")
    init.add_argument("--name", required=True)
    init.add_argument("--description", required=True, help="the anchor: immutable traits only")
    init.add_argument("--style", help="style notes (rendering, palette, lens)")
    consent_flags(init)

    update = add("update", cmd_update, "change name, anchor or style; old anchors are kept")
    update.add_argument("handle")
    update.add_argument("--name")
    update.add_argument("--description")
    update.add_argument("--style")
    consent_flags(update)

    add_ref = add("add-ref", cmd_add_ref, "copy reference images into the sheet")
    add_ref.add_argument("handle")
    add_ref.add_argument("files", nargs="+", metavar="image")
    add_ref.add_argument("--role", required=True, choices=ROLES)
    add_ref.add_argument("--cdn-url", dest="cdn_url", help="existing https URL of this exact file")
    add_ref.add_argument("--note")

    drop = add("drop-ref", cmd_drop_ref, "de-list references (files stay on disk)")
    drop.add_argument("handle")
    drop.add_argument("refs", nargs="+", metavar="ref-id")
    drop.add_argument("--restore", action="store_true")

    add("list", cmd_list, "list the characters of this project")

    show = add("show", cmd_show, "print one sheet plus health checks")
    show.add_argument("handle")

    resolve = add("resolve", cmd_resolve, "handle(s) -> anchor text + reference URLs (uploads only when needed)")
    resolve.add_argument("handles", nargs="+", metavar="handle")
    resolve.add_argument("--max", type=int, default=DEFAULT_MAX,
                         help="total references to return (default %d); set it to the endpoint's limit" % DEFAULT_MAX)
    resolve.add_argument("--roles", help="comma list, priority order (default: %s)" % ",".join(ROLES))
    mode = resolve.add_mutually_exclusive_group()
    mode.add_argument("--refresh", action="store_true", help="re-upload every picked reference")
    mode.add_argument("--no-upload", dest="no_upload", action="store_true", help="never upload")

    trained = add("set-trained", cmd_set_trained, "record a trained profile or LoRA")
    trained.add_argument("handle")
    trained.add_argument("--type", choices=("profile", "lora"))
    trained.add_argument("--endpoint", help="inference endpoint id")
    trained.add_argument("--profile-id", dest="profile_id")
    trained.add_argument("--lora-url", dest="lora_url")
    trained.add_argument("--trigger")
    trained.add_argument("--trainer", help="training endpoint id")
    trained.add_argument("--scale", type=float)
    trained.add_argument("--clear", action="store_true")

    mirror = add("set-mirror", cmd_set_mirror, "record the fal Assets character id")
    mirror.add_argument("handle")
    mirror.add_argument("--character-id", dest="character_id")
    mirror.add_argument("--clear", action="store_true")

    pack = add("pack", cmd_pack, "build a training ZIP locally (no upload, no training)")
    pack.add_argument("handle")
    pack.add_argument("--from", dest="sources", action="append", metavar="dir")
    pack.add_argument("--no-refs", dest="no_refs", action="store_true")
    pack.add_argument("--caption")
    pack.add_argument("--out")
    return parser


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
        payload, code = args.func(args)
    except CharError as exc:
        payload, code = exc.payload, exc.code
    except KeyboardInterrupt:
        payload, code = {"ok": False, "kind": "unknown", "message": "interrupted"}, 1
    except Exception as exc:  # a hand-edited sheet can break any assumption: still answer in JSON
        payload, code = {"ok": False, "kind": "unknown", "message": "%s: %s" % (type(exc).__name__, exc)}, 1
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
