# Character sheet: schema, anchor guide, helper commands

The sheet is the source of truth for a character. Everything else (CDN URLs, a fal Assets mirror, a trained profile) can be rebuilt from it. It lives in the user's project, not in the plugin.

```text
.genmedia/characters/<handle>/
  character.json          the sheet
  refs/r1-face.png        copies of the reference images, named <id>-<role>.<ext>
  dataset.zip             only after `pack` (training)
```

Suggest adding `.genmedia/` to `.gitignore` only when the project is a git repository and the user agrees; for a real person's photos, recommend it.

## `character.json`

Written only through `scripts/character.py`. Read it freely; do not hand-edit it unless the helper cannot express the change.

```json
{
  "schema": 1,
  "handle": "mara",
  "name": "Mara",
  "description": "Mara, a woman in her early thirties, oval face, ...",
  "style": "35mm photo look, soft natural light, muted earth palette",
  "real_person": false,
  "consent_confirmed_at": null,
  "refs": [
    {"id": "r1", "role": "face", "path": "refs/r1-face.png", "sha256": "...", "bytes": 1482211,
     "cdn_url": "https://v3b.fal.media/files/...", "uploaded_at": "2026-09-19T10:12:00Z",
     "added_at": "2026-09-19T10:12:00Z", "note": "approved hero", "active": true}
  ],
  "next_ref": 2,
  "anchor_history": [{"ts": "2026-09-19T11:00:00Z", "description": "previous anchor"}],
  "trained": {"type": "profile", "endpoint": "fal-ai/phota/edit", "profile_id": "...",
              "trainer": "fal-ai/phota/create-profile", "trained_at": "..."},
  "fal_assets": {"character_id": "...", "synced_at": "..."},
  "created_at": "...", "updated_at": "..."
}
```

| Field | Meaning |
|---|---|
| `handle` | `a-z`, `0-9`, `-`, `_`; at most 64 characters; immutable. Users write it as `@handle`. Default: slug of the name. |
| `description` | **The anchor**: immutable traits only. English. Goes into every prompt verbatim. |
| `style` | How the character is rendered (medium, lens, palette, line quality). Separate from identity so a shot can override it. |
| `real_person`, `consent_confirmed_at` | Set by `--real-person --consent`. `resolve` repeats `real_person` so downstream skills keep the safety rules in view. |
| `refs[].role` | `face`, `full-body`, `turnaround`, `expression`, `outfit` (next section). |
| `refs[].cdn_url`, `uploaded_at` | Public fal CDN URL of that exact file and when it was obtained. `null` until the first `resolve` or an `add-ref --cdn-url`. |
| `refs[].path` | Relative to the sheet folder. A path that resolves outside that folder (also through a symlink) counts as a missing file: it is never uploaded or packed. |
| `refs[].active` | `false` after `drop-ref`. The file stays on disk. |
| `trained` | Optional. `type` is `profile` (with `profile_id`) or `lora` (with `url`, optional `trigger`, `scale`). `endpoint` is the inference endpoint. See `references/training.md`. |
| `fal_assets` | Optional cloud mirror id. See `references/assets-mirror.md`. |

## Roles

| Role | What the image shows | Notes |
|---|---|---|
| `face` | Front-facing head and shoulders, neutral expression, even light, plain background | The identity carrier. At least one; the first one added is the primary. For a mascot or product: the front hero view. |
| `full-body` | Head to toe, relaxed neutral pose, default outfit | Carries build, proportions, default wardrobe. |
| `turnaround` | Three-quarter, profile or back view; or one strip image with several views | Needed when shots show the character from the side or behind. |
| `expression` | Close-up with a non-neutral expression (open smile, anger, surprise) | Stops the model from freezing the neutral face, and shows teeth and smile lines. |
| `outfit` | The character in an alternative outfit, or a clean image of a signature garment or prop | Pass only when the shot uses that outfit: `resolve --roles face,outfit`. |

Target: 4 to 8 active references. Typical good set: 2 `face` (neutral front, slight angle), 1 `full-body`, 2 `turnaround` (profile, back or three-quarter), 1 to 2 `expression`. Order inside a role is priority: add the best first.

## Writing the anchor

The anchor is the text half of identity. It is pasted into every prompt, so it must be true for every future shot.

Rules:
1. Immutable traits only: apparent age range, face shape, eyes (colour and shape), brows, nose, lips, skin tone and marks with their side (left or right from the character's point of view), hair (colour, length, texture, parting), build and height impression, permanent items (glasses, a scar, a tattoo, a prosthetic, a mascot's emblem).
2. Add at most one or two **signature items** that really appear in every shot (a red scarf, round tortoiseshell glasses). Anything worn only sometimes is a shot variable.
3. Concrete and visual. "Dark brown almond eyes", not "beautiful eyes". No personality, backstory, mood or profession unless it is visible.
4. No shot variables: pose, action, location, time of day, lighting, camera, emotion, outfit of the day.
5. No names of real people, living artists or copyrighted characters as shorthand for a look.
6. 60 to 120 words. Start with the name and the category ("Mara, a woman in her early thirties" / "Bolt, a small round robot mascot"). English, present tense, one paragraph.
7. After the hero image is approved, rewrite the anchor to match the image, not the other way round.

Non-human characters use the same slots with different words: body shape and proportions, material and finish, colour codes or plain colour names, face layout (eye shape, mouth), emblem placement, number of limbs or fingers.

### Good and bad

Bad (mood, variables, vague):

```text
Mara is a mysterious, confident woman standing in a rainy alley at night, wearing a leather jacket, beautiful face, cinematic lighting.
```

Good:

```text
Mara, a woman in her early thirties with an oval face, high cheekbones and a narrow straight nose. Dark brown almond-shaped eyes, thick straight brows, full lips. Light olive skin with a small mole under the right eye. Straight black hair to the shoulders, parted on the left, tucked behind the left ear. Slim athletic build, medium height. Always wears a thin silver hoop in the left ear.
```

Bad mascot (adjectives, no geometry):

```text
A cute friendly robot for our brand, modern and playful.
```

Good mascot:

```text
Bolt, a small round robot mascot about as tall as a coffee mug. Glossy off-white egg-shaped body, no neck, short stubby arms with three-finger mitten hands, two small wheels instead of legs. Face is a flat black oval screen showing two mint-green dot eyes and a short curved line mouth. One mint-green antenna with a ball tip on top, a mint-green lightning-bolt emblem on the chest.
```

Style notes belong in `style`, for example `flat vector illustration, thick even outlines, two-tone shading` or `35mm photo look, soft natural light, shallow depth of field`.

### Shot variables (never in the anchor)

Per shot you describe: action and pose, expression, outfit when it differs from the default, location and props, framing and lens, light, time of day, mood, aspect ratio. The prompt order that works across the routed editors:

```text
The same character as in the reference images: <anchor>.
Keep identical: face, hair, skin marks, build, <signature item>.
Shot: <action>, <place>, <framing and lens>, <light>, <outfit if it differs>.
Style: <style>.
```

When a model cites references by number (`alibaba/qwen-image-3/edit`: "image 1"; Seedance: `@Image1`; Kling: `@Element1`), use the `legend` that `resolve` returns to write "the woman from image 1" style phrases. Details per endpoint: `references/consistency-playbook.md`.

## Evolving a character

| Change | Do |
|---|---|
| Permanent change (new haircut, aged up, redesign) | `update --description`, generate or add new references, `drop-ref` the ones that contradict the new anchor. The old anchor stays in `anchor_history`. |
| Temporary look (costume, season outfit) | Do not touch the anchor. Add an `outfit` reference and name the outfit in the shot line. |
| A result is better than an existing reference | `add-ref` it with `--cdn-url`, then `drop-ref` the weaker one. Keep 4 to 8. |
| Wrong role | `drop-ref`, then `add-ref` the same file with the right role (a dropped duplicate is restored with the new role). |
| Rename | `update --name`. The handle never changes; create a new character if the handle must change. |

## Helper commands

Call it as `python3 "${CLAUDE_SKILL_DIR}/scripts/character.py" <command>`; shortened to `character.py` here. One compact JSON object on stdout. Exit `0` ok, `1` failed, `2` usage (nothing written). Errors: `{ok:false, kind, message}` with `kind` one of `usage`, `consent`, `not_found`, `exists`, `io`, `no_refs`, `upload`, `helper_missing`, `unknown` (usually a hand-edited sheet: run `show`, repair the field).

| Command | Does | Network |
|---|---|---|
| `init <handle> --name <n> --description <anchor> [--style <s>] [--real-person --consent]` | Creates the sheet. Refuses to overwrite. `--real-person` without `--consent` fails with `kind:"consent"`. | none |
| `update <handle> [--name] [--description] [--style] [--real-person --consent]` | Changes fields; keeps the last 10 anchors. | none |
| `add-ref <handle> <image>... --role <role> [--cdn-url <https>] [--note <text>]` | Copies PNG, JPG or WebP files into `refs/`. Detects duplicates by content. `--cdn-url` (one file) records a URL you already hold, for example the output URL of the run that made the image. Warns above 10 MB and when no `face` exists. | none |
| `drop-ref <handle> <ref-id>... [--restore]` | De-lists or restores references. Never deletes files. | none |
| `list` | All characters of the project with reference counts, `trained`, `mirrored`. | none |
| `show <handle>` | The whole sheet plus checks: missing files, references without URL, URLs older than 7 days, `has_face`. | none |
| `resolve <handle>... [--max 8] [--roles a,b] [--refresh \| --no-upload]` | The hand-off (below). | **uploads when needed** |
| `set-trained <handle> --type profile\|lora --endpoint <id> [--profile-id \| --lora-url] [--trigger] [--trainer] [--scale] \| --clear` | Records a trained identity. | none |
| `set-mirror <handle> --character-id <id> \| --clear` | Records the fal Assets character id. | none |
| `pack <handle> [--from <dir>]... [--no-refs] [--caption <text>] [--out <zip>]` | Builds a training ZIP (`001.jpg`, `001.txt`, ...). Never uploads, never trains. | none |

### `resolve` contract

```json
{"ok": true, "handle": "mara", "name": "Mara", "description": "<anchor>", "style": "<style>",
 "real_person": false, "trained": null,
 "urls": ["https://<cdn>/r1-face.png", "https://<cdn>/r3-full-body.png"],
 "legend": [{"index": 1, "handle": "mara", "ref": "r1", "role": "face"},
            {"index": 2, "handle": "mara", "ref": "r3", "role": "full-body"}],
 "characters": [{"handle": "mara", "description": "...", "indexes": [1, 2], "urls": ["..."]}],
 "uploaded": 0, "skipped": [], "warnings": []}
```

- Selection: round-robin over the roles in priority order (`face`, `full-body`, `turnaround`, `expression`, `outfit`, or the order given in `--roles`) until `--max` is reached; inside a role the first added wins. `--max 3` yields face, full-body, turnaround; `--max 6` adds expression, outfit, second face.
- Set `--max` to the endpoint's documented reference limit, or lower. Default 8.
- Several handles: `--max` is shared evenly (the remainder goes to the first handles); top-level `description` is omitted, read `characters[]`. `indexes` are 1-based positions in `urls`.
- Upload rule: a picked reference without `cdn_url` is uploaded through `gm.py upload` and the URL is stored in the sheet. A reference that has a URL is never uploaded again unless you pass `--refresh`. `--no-upload` skips references without a URL. Uploading gives the file a public, expiring URL on the user's fal account (`references/platform.md` sections 1 and 2): an external side effect. Resolve only characters you are about to use.
- A URL older than 7 days produces a warning, not a re-upload. If a job then fails with `file_download_error`, run `resolve --refresh` and submit once more.
- Exit 1 with `kind:"upload"`: some uploads failed; `urls` holds the ones that worked and `errors[]` names the rest.
