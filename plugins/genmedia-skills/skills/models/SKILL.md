---
name: models
description: >-
  Choose, verify, price and compare fal.ai models for the genmedia CLI, from dated routing tables (Seedream 5.0 Pro and GPT Image 2.5 for stills, Seedance 2.5 for video, ElevenLabs and Gemini for audio) plus live catalog discovery. Questions about models land here; making the deliverable does not.
  Use when: "which model should I use for", "what's the best model for posters", "is Veo 4 on fal", "what's the newest Kling", "compare these models", "same prompt on three models", "how much will this cost", "what's new on fal since August", "this tutorial uses fal-ai/flux-pro", "hangi model daha iyi", "bu kaça patlar", "fal'da yeni ne var".
  Chain: hands a verified endpoint ID, its parameter names and a cost estimate to `image`, `video`, `audio`, `character`, `3d`, `pipelines` and the scenario skills.
  NOT for: producing the deliverable once the model is chosen (use `image`, `video`, `audio`, `3d` or the scenario skill); multi-step productions (use `pipelines`); install, key or CLI problems (use `setup`).
argument-hint: "[task or model name] [compare <id>,<id>] [cost of <plan>] [new since <YYYY-MM-DD>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/catalog.py" *) Bash(command -v genmedia) Bash(genmedia version *) Bash(genmedia models *) Bash(genmedia schema *) Bash(genmedia pricing *) Bash(genmedia docs *) WebFetch(domain:fal.ai) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 and python3 >= 3.8.
---

# Models

Owner of model-routing knowledge for every genmedia skill: which endpoint fits a use case, whether an ID is alive, what is new, what a plan will cost, and side-by-side comparisons.
Answers come from four dated routing tables plus live catalog checks. The tables are a cache; the live catalog is the truth.

## Step 0 — Preflight

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
```

- Once per session. `blockers` non-empty: relay them and stop (exception: the advice-only case below). Details: `references/cli-contract.md`; fixes: `/genmedia-skills:setup`.
- Key missing: the user runs `genmedia setup` or exports `FAL_KEY` themselves; wait. Never read, print, request or type a key.
- No CLI or no key and the user only wants advice: answer from the routing tables, say "from the table dated <verified_on>, not checked live", offer setup. Quote no price as current in that mode.

## UX rules

1. Reply in the user's language (often Turkish). Comparison prompts are written in English unless the requested on-image or spoken text is in another language. Endpoint IDs, flags and field names stay as they are.
2. No JSON, request IDs or tool narration in chat. IDs live in the ledger. At most one status line per batch.
3. **Question budget: 1.** Act on the most likely use case and state the assumption. Spend the question only when the task itself is unknowable ("best model?" with no modality), as labelled options (AskUserQuestion when available). A cost confirmation is not a question.
4. Recommend one model and one fallback. At most three rows unless the user asks for a survey.
5. A model the user names is final: verify it, price it, warn about it, never swap it silently. Offer the newer or cheaper option and let them choose.
6. Every price in chat is fresh (`gm.py price --explain`: pricing API plus the `llms.txt` Pricing text, today) or carries the table date. Never from memory.
7. Comparisons carry no quality verdict. Label fastest and cheapest from measured numbers; the user judges.
8. Never infer approval from silence or from a successful run.
9. Cost gate on the whole plan (`references/platform.md` §8): under USD 0.50 run; USD 0.50 to USD 2 announce and run; USD 2 or more confirm first. `.genmedia/config.json` overrides the thresholds.
10. Bounded repair: at most 3 attempts per step, each one different; never resend a content-policy rejection unchanged; a job with a request ID is resumed, never resubmitted.
11. Likeness, brands and ad honesty (`references/platform.md` §9) apply to comparison prompts too.

## Discovery guardrail

- The routing tables are a dated cache. Before calling an ID "current", look it up by exact ID with the `catalog.py status` call shown in flow A (state `active` | `deprecated` | `unlisted` | `removed`). Raw form: `genmedia models --endpoint_id <endpoint_id> --json`, then read `.models[0].status` (`null` = unlisted, a 404 = removed); the top-level `.status` is only the filter echo.
- Before the first paid call to an endpoint in a session: that lookup plus `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>`, which resolves the nested shapes and limits the short CLI view drops; `--field <name>` prints one field in full, with its description; `https://fal.ai/models/<endpoint_id>/llms.txt` covers what no schema states (this skill pre-approves `WebFetch(domain:fal.ai)` for that; prices never need it).
- Never invent endpoint IDs, parameters, enums, limits or prices. A user names a model you do not know: search, trust that it may exist, pick the newest active match and say which one you picked.
- Read the catalog through `scripts/catalog.py`: it always sends `--no-classify`, caps `--limit` at 100, pages with the cursor, isolates removed IDs and returns compact rows. A raw `genmedia models "<query>"` without `--no-classify` or `--category` lets the CLI guess a category and can return zero rows.
- `--status` is not a deprecation filter: `deprecated` and `all` both return active and deprecated rows mixed, and unlisted or removed IDs appear in no list or search. The exact-ID lookup is the only state oracle. A `llms.txt` that loads proves nothing: deprecated and unlisted models still serve one.
- NEVER use smart routing (`genmedia run` with a prompt instead of an endpoint ID): its defaults are stale and one of them does not exist.
- New releases land under vendor namespaces (`bytedance/`, `openai/`, `google/`, `minimax/`, `alibaba/`, `xai/`, `blackforestlabs/` ...), not `fal-ai/`. A family whose newest `fal-ai/` ID looks old has probably moved.

## Routing

### Which flow

| The user wants | Flow | Spends money |
|---|---|---|
| "which model for X", "best model for X" | A. Recommend | no |
| "is <model> on fal", "newest <family>", an unknown model name | B. Look up | no |
| "what's new", "what changed since <date>" | C. What is new | no |
| a pasted old ID, a snippet from an old tutorial or skill | D. Translate | no |
| "how much will this cost" | E. Estimate | no |
| "compare A and B", "same prompt on N models" | F. Compare | **yes** |
| "this recommendation looks outdated" | G. Stale-row report | no |

Tie-breakers: a question that names two or more models and a prompt is F; without a prompt it is A with both priced (offer F). "Cheapest model for X" is A with the budget tier, not E. Once the model is settled and the user wants the asset, hand off (Chain in the description); do not generate deliverables here.

### Where the row lives

| Request is about | File | Task IDs |
|---|---|---|
| stills: photoreal, product, typography, vector, drafts, edit, multi-reference, identity, inpaint, erase, outpaint, try-on, background removal, upscale, layers, LoRA training | `references/routing-image.md` | `t2i-*`, `image-*`, `character-identity`, `virtual-try-on`, `product-shot`, `bg-remove-image`, `upscale-image`, `train-lora` |
| clips: text/image-to-video, dialogue, first-last frame, references, multi-shot, edit, extend, reframe, motion transfer, lipsync, talking head, upscale, background removal | `references/routing-video.md` | `t2v`, `t2v-dialogue`, `i2v`, `first-last-frame`, `reference-to-video`, `multi-shot`, `video-*`, `motion-transfer`, `lipsync`, `talking-head`, `upscale-video`, `bg-remove-video` |
| sound: TTS, Turkish TTS, voice clone, STT, dubbing, music, SFX, foley, cleanup | `references/routing-audio.md` | `tts`, `tts-turkish`, `voice-clone`, `stt`, `dubbing`, `music`, `sfx`, `foley`, `audio-cleanup` |
| assembly utilities, understanding/QA models, text LLM, 3D | `references/routing-utility.md` | `util-*`, `understand-*`, `llm-text`, `image-to-3d`, `text-to-3d` |

Read only the file for the modality in play. Each file ends with a "Stale IDs" table (flow D) and carries its own `verified_on` date (the "verified" date in its title).

### The policy (reason with it when no row fits)

1. **Use case, not a global winner.** There is no "best model". Pick the row for the use case: a poster and a product photo route to different families.
2. **default = quality first.** Where an OpenArt arena board exists for the use case, the default follows it. Scores within about 15 points are a tie, broken by recency, then price, then control surface.
3. **Recency supersedes.** A successor released on fal after the arena snapshot replaces its predecessor for the same use case even though the board does not list it yet. Arena names are marketing names; map them to endpoint IDs through the table or a search.
4. **budget = cheapest current-generation endpoint that still does the job.** Use it when the user asks for cheap, drafts or volume, or offer it when the cost gate would trigger. Never silently.
5. **premium = highest fidelity regardless of price. control = richest control surface for a named need** (end frame, elements, multi-shot, masks, reference count, a language enum). A named need beats the quality default.
6. **No board** (audio, 3D, utilities, training, understanding): fal's catalog order inside the category, the newest generation in a family, and the verified schema surface decide.
7. **No row at all:** run the candidate search in `references/discovery.md`, apply rules 1 to 6 to what comes back, verify the schema for the need, price it, and label the answer "live pick, not in the dated table".

### External leaderboards

- The OpenArt arena snapshot named in each routing file's header is **one** signal from **one** vendor: Elo-style scores from pairwise votes, per use-case board. It says nothing about price, limits, licence or whether fal hosts the model.
- Gaps under about 15 points are ties. Say "in the leading group", never "ranked first by 2 points".
- Boards lag releases. A model that is missing from a board is not thereby worse; a successor inherits its predecessor's slot until the board lists it (policy rule 3).
- Use the board that matches the use case (Ads, Film, Graphic design, Image editing ...), not Overall.
- A user brings another or newer leaderboard: treat it the same way. Map each marketing name to an endpoint with flow B, check it against the policy, and when two leaders are within a tie offer flow F instead of arguing from scores.
- Never quote a score from memory; quote the routing file with its snapshot date or what the user pasted.

### Named traps

| Trap | What goes wrong | Do instead |
|---|---|---|
| Catalog order read as quality | `--category` order is popularity-like; it lists a cheap throughput model first for text-to-video. | Use it as the signal only where no arena board exists (rule 6). |
| Arena Lip sync board | It ranks native-audio video generators, not post-hoc lipsync endpoints. | New footage with speech: `t2v-dialogue`. Existing footage: `lipsync`. |
| Category as task label | TTS sits in `text-to-speech` and `text-to-audio`; lipsync in `video-to-video`; avatars in `image-to-video` and `audio-to-video`. | Search the category sets in `references/discovery.md`. |
| Pricing API number taken as the price | It is one base number; audio, resolution and quality tiers exist only in the `llms.txt` Pricing text (`--explain`). Rows tagged `[mismatch]`, `[promo]`, `[tentative]`, `[token-priced]` say so. | `references/cost-estimation.md`. |
| Parameter names carried across families | `image_url` vs `start_image_url` vs `first_frame_url`; `duration` as integer, `"5"` or `"8s"`; `720p` vs `768P` vs `1K`. | Read each endpoint's schema; in a comparison build each input separately. |
| fal's root `llms.txt` used for picks | It still recommends unlisted and deprecated models. | Per-model `llms.txt` only, and only for schema and pricing text. |
| Old `fal-ai/<vendor>/...` ID "not found" | The family moved to a vendor namespace. | Flow D, then a name search. |

## Workflow

**A. Recommend**
1. Extract modality, use case and hard needs from the message (references? text on image? speech language? duration? end frame? budget words?).
2. Open the routing file for the modality, find the task row, choose the tier with the policy.
3. Confirm the pick and the fallback are alive:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/catalog.py" status <default_id>,<fallback_id>
   ```
4. Table older than 30 days, user asks for "the newest", or a pick is not `active`: run the freshness probe in `references/discovery.md` and prefer a newer active successor in the same family.
5. Price both in one call and read the pricing text for any row that needs it (`references/cost-estimation.md`):
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price <default_id>,<fallback_id>
   ```
6. Reply with template A and name the skill that runs it: stills `image`, clips `video`, sound `audio`, identity sheets `character`, meshes `3d`, multi-step work `pipelines`, and the scenario skill when the job is one (`product-photoshoot`, `ads`, `short-video`, `video-explainer`, `youtube-thumbnail`, `marketplace-cards`, `brandkit`). Hand over the endpoint ID, the field names you verified and the estimate.

**B. Look up a model or family**
```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/catalog.py" search "<name or family>" --limit 10
```
Rows come best text match first, then newest: read `released` and the ID, not the position, before calling something "the newest" (regional or tier variants such as `/us/`, `/fast`, `/4k` share a generation). Zero rows: retry with the family word alone, the vendor name, and the marketing name split into words ("gpt image"); then say "not in fal's active catalog today", never "does not exist". Confirm the chosen ID with `status`. Template B. Without python3: `genmedia models "<name>" --no-classify --limit 10 --json`.

**C. What is new since a date**
```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/catalog.py" new-since <YYYY-MM-DD> --category <category>,<category>
```
Omit `--category` for the whole catalog (about 15 pages). The list is not ordered by date, so the helper reads every page; `complete:false` means it was cut short. Category sets per task: `references/discovery.md`. No date given: use the routing file's `verified_on`. Template C.

**D. Translate a stale ID**
1. Find it in the "Stale IDs" table of the matching routing file.
2. Confirm today's status of the old ID and the successor in one `catalog.py status <old_id>,<successor_id>` call (shape as in A.3).
3. `superseded` still runs: if the user insists, keep it and mention the successor. `deprecated`, unlisted (`null`) or removed: use the successor, say so, and re-read the successor's schema because field names change between generations.
4. Not in the table: flow B on the family name.

**E. Estimate a cost**
List every paid call with the arguments that drive price, price all IDs in one `gm.py price` call, convert units, add `--explain` and read `pricing_text` where required, sum, round up, and say which gate the plan will meet. Nothing runs here: the skill that produces the asset asks for the confirmation. Units, the token and megapixel worked examples, promo and tentative flags: `references/cost-estimation.md`. Template D.

**F. Compare models** (paid; full procedure in `references/comparison.md`)
1. Two to four endpoints of the same task; verify each alive, read each schema, build one input per endpoint from the same prompt and the same settings expressed in that endpoint's own fields. A local input file is uploaded once (`gm.py upload <path>`, public expiring URL: say so) and the same `urls[0]` goes into every job.
2. Estimate every job, sum, apply the gate to the **whole batch**. State the total before running when it is USD 0.50 or more; at USD 2 or more show models, shared settings, per-model figures and the total, offer the draft tier for video, and wait for a yes.
3. Write the plan with the Write tool to `.genmedia/tmp/compare-<slug>.json`, then:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/tmp/compare-<slug>.json
   ```
   Give the Bash call a 600000 ms timeout (the helper polls up to 540 s). Exit 1 with a JSON result means at least one job failed: read `jobs[]`, the others are done.
4. `status: "pending"`: run the same command again later; never resubmit. A failed job stays a row in the table with its reason (`references/comparison.md` §8).
5. Reply with template E: table, fastest and cheapest labels, no verdict.

**G. Stale-row report**
A row is stale when its ID is not `active`, a newer active generation of the same family exists, the live price differs from the row by more than about 20%, or a schema field named in the row is gone. Use the live result for the user's task, tell them the table is behind (template F), and do not edit any file under `references/`: the tables are generated by the repository's `refresh_routing.py` maintainer script and overwritten on the next sync.

## Delivery

Translate the fixed words into the user's language; keep IDs and numbers as they are.

**A. Recommendation**
```
<Display name> (`<endpoint_id>`)
Why: <one clause tied to the use case>. Table dated <verified_on>; checked active today.
Cost: about $<x> per <image | second | 1000 characters> at <the settings assumed>, priced today.
Watch: <one limit that shapes the plan: max duration, reference count, language, field name>.
Cheaper: `<budget_id>`, about $<y>: <what you give up>.
Next: <skill name> runs it.
```

**B. Look-up**
```
<Name> on fal: yes, `<endpoint_id>` (released <YYYY-MM-DD>) | not in the active catalog today.
Newest in the family: `<endpoint_id>` (<YYYY-MM-DD>).
<old_id>: <deprecated | unlisted | removed> -> use `<successor_id>`.
```

**C. What is new** - table `Released | Endpoint | Category | What it is`, newest first, at most 15 rows, then "<n> more". One closing line: which rows would change a routing default, if any.

**D. Estimate**
```
| Step | Model | Quantity | Unit price | Subtotal |
Total: about $<sum rounded up> (estimate; re-rolls are extra; prices checked today).
<gate line: "runs without asking" | "will be announced, then run" | "needs your OK before it runs">
Next: <skill name> runs it; levers if it is too much: <draft resolution | shorter | budget model and its total>.
```

**E. Comparison** - see `references/comparison.md` for the literal table. Files first, then one line: "Fastest: <model>. Cheapest: <model>. Which one do you prefer?"

**F. Stale row**
```
Heads-up: the routing table (dated <verified_on>) still lists `<old_id>` for <task>; today <what changed>.
I used `<live_id>` instead. The table is refreshed by the plugin maintainers; updating the plugin picks it up.
```

## Errors

| Signal (verbatim) | Meaning | Do |
|---|---|---|
| `state: "removed"`; raw: `Failed (404)` and `Endpoint(s) not found` | The ID is gone, renamed or mistyped. Raw: one bad ID fails a whole multi-ID call. | Flow D, then flow B on the name. |
| `state: "unlisted"`; raw: a bare `{"endpoint_id": ...}`, `.status` reads `null` | Hidden from the catalog; may not run. | Do not recommend it; flow D, template F. |
| `state: "deprecated"` | On its way out. | Successor from the Stale IDs table; say so. |
| `"count": 0` with `"inferred_category"` set (raw CLI) | The classifier forced a wrong category. | Repeat with `--no-classify`. |
| `kind: "rate_limit"`; raw: `Failed (429)` and `Rate limit exceeded` | Catalog or pricing API throttled; the helper already retried three times. | Wait 30 s, then fewer, larger calls. No tight loops. |
| `Requested limit <n> exceeds maximum of 100 for this query` (raw CLI) | `--limit` too high. | `--limit 100` and page with `--cursor`. |
| `Schema fetch failed (404)` or `Pricing fetch failed (404)` with `Endpoint(s) not found` (raw CLI) | No such endpoint; one bad ID fails a whole raw pricing call. A schema that loads proves nothing: unlisted IDs still serve one. | `catalog.py status`, then flow B on the name. |
| `gm.py price` returns `ok:false` with `missing:[...]` | Those IDs have no price (removed or mistyped); the rest are priced. | Fix or drop the missing IDs; never guess their price. |
| `needs_llms_txt: true`, or any video model | The unit cannot simply be multiplied, or tiers are hidden. | Rerun `gm.py price <ids> --explain` and read `pricing_text`. |
| `No fal.ai API key found` | No key. | Step 0. |

Run and batch errors (`validation`, `content_policy`, `auth`, `server`): `references/cli-contract.md` "Helper errors" and `references/platform.md` §4. In a batch every provider-side failure, a filter hit included, arrives as `kind: "validation"` with empty `fields` and may have been billed: `references/comparison.md` §8.

## Reference index

| File | Read when |
|---|---|
| `references/discovery.md` | read when searching the live catalog: candidate search for a task, freshness probe, "what is new" paging loop, category sets, find-mode status shapes, schema formats, catalog quirks. |
| `references/cost-estimation.md` | read when any price is quoted or a plan is estimated: unit semantics, when the pricing text (`--explain`) is mandatory, worked token-video and megapixel-image examples, promo/tentative/mismatch flags. |
| `references/comparison.md` | read when running flow F: plan file shape, equalising settings across endpoints, gate on the batch, timing and cost columns, the literal results table, failure rows. |
| `references/routing-image.md` | read when the request concerns stills, editing, identity, try-on, upscale, vectors or LoRA training; also its Stale IDs table. |
| `references/routing-video.md` | read when the request concerns any video task, lipsync or talking heads; also its Stale IDs table. |
| `references/routing-audio.md` | read when the request concerns TTS (incl. Turkish), voice clone, STT, dubbing, music, SFX or foley. |
| `references/routing-utility.md` | read when the request concerns ffmpeg-style utilities, understanding/QA models, text LLMs or 3D. |
| `references/cli-contract.md` | read when a command shape, JSON shape, helper option, batch plan or error `kind` is unclear. |
| `references/platform.md` | read when billing rules, pricing units, the cost gate, concurrency, error types or safety rules matter. |
| `scripts/gm.py` | the shared helper (generated copy; run it, never edit it): `preflight`, `price`, `upload`, `batch`, `ledger`. `--help` lists every command. |
| `scripts/catalog.py` | this skill's catalog reader: `status`, `search`, `leaders`, `new-since`. Free calls only; one compact JSON object; `--help` documents the output. |
