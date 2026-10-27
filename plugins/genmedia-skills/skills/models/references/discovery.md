# Live discovery

How to read fal's live catalog so an answer never depends on a table that aged. Every behaviour below was observed on 2026-09-19 with genmedia v0.7.0. All commands here are free. Command and JSON shapes of the CLI in general: [cli-contract.md](cli-contract.md).

`catalog.py` below means `python3 "${CLAUDE_SKILL_DIR}/scripts/catalog.py"` (the call pre-approved in SKILL.md). It wraps `genmedia models`, prints one compact JSON object, always disables the classifier, caps `--limit`, pages with the cursor, isolates removed IDs, pauses between consecutive calls and backs off on HTTP 429 (8, 16, 32 s). Exit codes: `0` ok, `1` failed, `2` usage. Prefer it: a raw 100-row page is tens of kilobytes of thumbnails and descriptions in your context. The raw CLI forms are given as the fallback when `python3` is missing.

## 1. Surfaces

| Surface | Key | Tells you | Cannot tell you |
|---|---|---|---|
| `genmedia models` (catalog API) | CLI needs one | which endpoints exist, category, release `date`, `status` in exact-ID mode | quality, price, parameters |
| `genmedia schema <endpoint_id> --json` | yes | field names, scalar types, direct enums, defaults, `required` | ranges, nested objects, `anyOf` enums (shown as `type: "unknown"`); whether the ID is alive (unlisted IDs still return a schema) |
| `genmedia schema <endpoint_id> --format openapi --json` | yes | everything: nested types, `minimum`/`maximum`, fal limits (`max_file_size`, `max_duration`, ...) | price |
| `https://fal.ai/models/<endpoint_id>/llms.txt` | no | flat human-readable schema **and the `## Pricing` text with tiers** (the latter comes back as `pricing_text` from `gm.py price <ids> --explain`; never WebFetch it for a price) | whether the model is alive (loads for deprecated and unlisted IDs); nested types are named, not expanded |
| `genmedia pricing <id>[,<id>...] --json` | yes | one base number and a `unit` per ID | tiers, surcharges, promos ([cost-estimation.md](cost-estimation.md)) |
| `genmedia docs "<query>" --json` | no (re-checked 2026-09-23) | platform documentation snippets with URLs | anything about a specific model's parameters |

Not a source: fal's root `https://fal.ai/llms.txt` (its model picks are stale), `genmedia run` smart routing (stale baked-in defaults), model IDs remembered from training data.

## 2. Three modes of `genmedia models`

| Mode | Trigger | Order | Use for |
|---|---|---|---|
| Find | `--endpoint_id <id>[,<id>...]` | as asked | Is this ID alive? The **only** deprecation oracle. |
| Search | a `QUERY` argument | best text match first, then newest | Does a model or family exist, what is its newest generation. |
| List | no query; optional `--category` | fal's default order: popularity-like, **not** quality and **not** date | Category leaders where no arena board exists; full sweeps. |

Rules that hold in every mode:

- A search without `--no-classify` or `--category` is broken by design: the CLI infers one of five categories from the query and filters by it. `genmedia models "lipsync" --limit 3 --json` returns `"category":"text-to-image","inferred_category":"text-to-image","count":0`. If you ever see `inferred_category` in a response, the result is not trustworthy.
- `--limit` above 100 fails: `Failed (400)` with `Requested limit 101 exceeds maximum of 100 for this query`. Default is 20.
- Paging: the response carries `has_more` and `next_cursor` (an opaque token such as `Mg`). Pass it back with `--cursor` and the **same** filters until `has_more` is `false`.
- List and search return `active` models by default. `--status` is not a deprecation filter: `deprecated` and `all` behave alike and return active **and** deprecated rows (deprecated ones after the active ones in a list, by match in a search). Unlisted and removed IDs never appear. Read each row's own `status`; `catalog.py search ... --all` does this for you.
- The top-level `.status` of any response is that filter echo. A model's own state is `.models[i].status`.
- The catalog API throttles even with a key: `Failed (429)` with `Rate limit exceeded`. It recovers in 20 to 30 s. Make fewer, larger calls (comma lists, `--limit 100`); never loop tightly.
- `highlighted` and `pinned` are always `false`; they rank nothing. The CLI strips `license_type`, `kind`, `group` and the trainer/inference links from the API response.
- Row keys from the CLI: `endpoint_id, name, category, status, description, tags, updated_at, date, model_url, thumbnail_url, is_favorited, highlighted, pinned`. `date` is the release date on fal; `updated_at` is the last metadata edit.

## 3. Is this ID alive (find mode)

```bash
catalog.py status <endpoint_id>,<endpoint_id>
```

Returns `results[] {endpoint_id, state, name, category, released, updated}` plus `active[]` and `not_active[]`.

| `state` | Raw shape behind it | Meaning | Do |
|---|---|---|---|
| `active` | full row, `"status":"active"` | usable | proceed |
| `deprecated` | full row, `"status":"deprecated"`; `updated` is roughly when it was flagged | still documented, on its way out | use the successor from the Stale IDs table; say so |
| `unlisted` | a bare `{"endpoint_id":"..."}` with no other key, so `.status` reads `null` | exists but is hidden from the catalog; whether it still executes is unknown | do not recommend; treat as stale |
| `removed` | the call exits 1 with `Failed (404)` and `Endpoint(s) not found` | gone, renamed without redirect, or mistyped | search by name (section 4) |

Raw fallback, one ID per call, because a single removed ID turns a multi-ID call into a 404 for all of them (unlisted and deprecated IDs do not):

```bash
genmedia models --endpoint_id <endpoint_id> --json
```

Check the exit code first: on failure stdout is empty and stderr holds `{"error":"Failed (404)","details":"..."}` after any shell noise.

## 4. Find a model or a family (search mode)

```bash
catalog.py search "<name or family>" --limit 10
```

Raw: `genmedia models "<name>" --no-classify --limit 10 --json`.

- Results come best text match first, then newest. Inside one family that is newest first in practice (`seedance`, `kling`), but a loose query mixes in neighbours (`dreamo` also returns Seedream rows). Decide "the newest" from `released` and the ID, never from the position. Regional and tier variants (`/us/`, `/fast`, `/4k`) can be released later than the base endpoint of the same generation: they are not a newer model.
- The query matches name, description and category text. Marketing names work better split into words (`gpt image`, `nano banana`, `seedance`) than with version punctuation.
- Zero rows: retry with the family word alone, then the vendor (`bytedance`, `alibaba`, `minimax`, `google`, `openai`, `xai`, `blackforestlabs`, `lightricks`, `luma`, `topaz`, `elevenlabs`, `recraft`, `ideogram`, `meta`, `bria`). Still nothing: answer "not in fal's active catalog today"; the user may know of a release that has not landed.
- Several variants per generation are normal (`/pro`, `/standard`, `/fast`, `/lite`, `/turbo`, `/4k`, and one endpoint per task: `text-to-video`, `image-to-video`, `reference-to-video`, `edit`). Pick the task variant first, then the tier by the routing policy.
- When the same model exists as `fal-ai/<vendor>/...` and `<vendor>/...`, the vendor-namespaced ID is the current one; the old one is usually unlisted.
- Confirm the final pick with section 3 before presenting it as current.

## 5. Candidates for a task with no routing row

1. List the leaders of every category the task can hide in (table below):
   ```bash
   catalog.py leaders <category>,<category> --limit 15
   ```
   Raw: `genmedia models --category <category> --limit 15 --json` per category.
2. Search the task keywords for the newest entries (section 4). A model can be too new to have climbed the default order.
3. Shortlist at most four: prefer a low rank, the newest generation of a family, a vendor-namespaced ID, and a plain unit price when the user is cost-sensitive.
4. Read each schema for the need that defines the task (section 7). A candidate without the required field is out, whatever its rank.
5. Price the shortlist in one call ([cost-estimation.md](cost-estimation.md)).
6. Present it as a "live pick, not in the dated table". If quality matters and the cost is small, offer a comparison ([comparison.md](comparison.md)).

Category labels are not task labels. Search all of these:

| Task | Categories to list | Search words |
|---|---|---|
| TTS | `text-to-speech`, `text-to-audio` | `tts`, `speech` |
| Voice clone / change | `audio-to-audio`, `text-to-speech`, `speech-to-speech` | `clone`, `voice` |
| Music, SFX | `text-to-audio` | `music`, `sound effects` |
| Foley | `video-to-audio`, `video-to-video` | `foley`, `sfx` |
| STT | `speech-to-text`, `audio-to-text` | `transcribe`, `asr` |
| Lipsync | `video-to-video`, `image-to-video`, `audio-to-video`, `text-to-video` | `lipsync`, `lip sync` |
| Avatar / talking head | `image-to-video`, `audio-to-video`, `text-to-video` | `avatar`, `talking` |
| Reference-to-video | `image-to-video`, `video-to-video` | `reference-to-video` |
| Video edit, extend, reframe, upscale, background removal | `video-to-video` | `edit`, `extend`, `reframe`, `upscale`, `background removal` |
| Image edit, upscale, background removal, try-on, product | `image-to-image` | `edit`, `upscale`, `background removal`, `try-on`, `product` |
| Vector / logo | `text-to-image`, `image-to-image` | `vector`, `svg` |
| 3D | `image-to-3d`, `text-to-3d`, `3d-to-3d` | `3d`, `rigging` |
| Training | `training` | `trainer`, `lora` |
| Utilities (ffmpeg-style) | `video-to-video`, `image-to-image`, `audio-to-audio`, `json`, `unknown`, `workflow`, `image-to-video` | `ffmpeg`, `workflow utilities` |
| LLM / vision / understanding | `llm`, `text-to-text`, `vision`, `video-to-text`, `image-to-text`, `audio-to-text`, `unknown` | `openrouter`, `vision` |

All 27 category strings seen in the catalog on 2026-09-23 (1512 listed endpoints; its one `text-to-text` endpoint was released on 2026-09-21): `image-to-image`, `video-to-video`, `image-to-video`, `text-to-image`, `text-to-video`, `training`, `text-to-audio`, `audio-to-audio`, `image-to-3d`, `text-to-speech`, `vision`, `audio-to-video`, `3d-to-3d`, `text-to-3d`, `speech-to-text`, `llm`, `json`, `video-to-audio`, `speech-to-speech`, `video-to-text`, `image-to-json`, `text-to-json`, `audio-to-text`, `unknown`, `image-to-text`, `workflow`, `text-to-text`. The CLI passes any string through; a typo returns zero rows, not an error.

## 6. Freshness probe and "what is new"

Run the probe when the routing file's `verified_on` is older than 30 days, when the user asks for "the newest", or when a routed ID is not `active`.

```bash
catalog.py search "<family of the routed default>" --limit 10
catalog.py new-since <verified_on> --category <category>,<category>
```

- A newer active generation of the routed family, or a new family released after `verified_on` in the task's categories, is a candidate to replace the row. Apply the policy in SKILL.md: a successor supersedes its predecessor; an unrelated newcomer is an alternate until a quality signal exists. Tell the user what you found and what you chose (stale-row template in SKILL.md).
- `new-since` without `--category` sweeps the whole catalog (about 15 pages of 100 and roughly 15 s on 2026-09-19, growing). It must read every page because the list is not ordered by date. `complete:false` means `--max-pages` cut it short: narrow the categories or raise the cap.
- Output: `rows[] {endpoint_id, name, category, released, status, about}` newest first, `counts` per category, `total`, and `truncated` when more than `--max-rows` (default 60) matched.

Raw fallback for one category (several calls; filter each page by `date` yourself):

```bash
genmedia models --category <category> --limit 100 --json
genmedia models --category <category> --limit 100 --cursor <next_cursor> --json
```

## 7. Schemas: compact, OpenAPI, `llms.txt`

```bash
genmedia schema <endpoint_id> --json
genmedia schema <endpoint_id> --format openapi --json
```

| Need | Read |
|---|---|
| Field names, which are required, scalar enums and defaults | compact |
| A field shows `type: "unknown"` or `array<unknown>` (`image_size`, `seed`, `elements`, `multi_prompt`, `keyframes`, `tracks`, `voice_setting`, any nullable or `anyOf` field) | OpenAPI: resolve `components.schemas` |
| Numeric ranges, list lengths, file size, dimension and duration limits | OpenAPI (`minimum`, `maximum`, `maxItems`, fal's `x-fal` limits) or the `Range` lines in `llms.txt` |
| Pricing tiers | `pricing_text` from `gm.py price <ids> --explain` |
| Human-readable limits in one page | `llms.txt` (WebFetch, pre-approved for `fal.ai` in this skill only) |
| Output keys for the download path | compact `output[]`, then the routing row's "-> output" column |

Known compact-mode blind spots: a field with a default can still be marked `required` (MiniMax H3 `prompt_expansion_mode`); `minimum`/`maximum` are dropped, so `num_images` looks unbounded; a maximum reference count is often stated nowhere (Nano Banana 2 edit) and must not be invented. `llms.txt` follows a 308 redirect for some renamed IDs and returns 404 for others and for removed IDs; neither outcome says anything about catalog status.

Parameter names never transfer between families. The same idea appears as `image_url`, `start_image_url` or `first_frame_url`; `end_image_url` or `last_frame_url`; `generate_audio` or `generate_audio_switch`; `duration` as an integer, as `"5"` or as `"8s"`; `resolution` as `720p`, `768P`, `1K` or `1k`. Read the schema of every endpoint you hand to another skill or put into a comparison.

## 8. Vendor namespaces and renamed IDs

New releases land under the vendor's own namespace: `bytedance/`, `openai/`, `google/`, `minimax/`, `alibaba/`, `xai/`, `blackforestlabs/`, `lightricks/`, `luma/`, `meshy/`, `topaz/`, `elevenlabs/`, `recraft/`, `ideogram/`, `meta/`, `bria/`, `tripo3d/`, `veed/`, `openrouter/`. Older IDs of the same models under `fal-ai/<vendor>/...` were renamed and are now unlisted. A tutorial ID that fails is far more often renamed than gone: translate it with the Stale IDs table of the matching routing file, then confirm with section 3.

## 9. Telling the user a table row is stale

The routing references are generated from the repository's `routing.json` by the maintainers' `refresh_routing.py` script (`--check` verifies every routed ID, `--new-since` lists releases, `--prices` refreshes base prices, `--render` rewrites the four files) and copied into each skill by the sync script. Editing a copy inside a skill folder is pointless: the next sync overwrites it.

So, in a session: use the live result for the task at hand, tell the user in one or two lines what differs (old ID and state, or old and new price, or the newer generation you found) and that a plugin update will carry the refreshed table. If they maintain the plugin themselves, point them to CONTRIBUTING.md in the repository. Never present a dated row as current when the live check disagrees, and never hide that you deviated from the table.
