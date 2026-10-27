---
name: 3d
description: >-
  3D mesh files through the genmedia CLI: image-to-3D, multi-view-to-3D, text-to-3D and post-processing of a mesh (remesh, retexture, rig, animate, convert to USDZ, FBX or STL) for product visualisation, game props, AR and 3D printing. Hunyuan3D v3.1 Pro by default, Tripo H3.1 for polygon budgets, Meshy 7.1 for rigged characters, Rodin v2.5 for STL; files checked by a GLB inspector.
  Use when: "turn this photo into a 3D model", "make a GLB of my product", "3D model from these four views", "low-poly game prop", "rig this character", "USDZ for AR", "STL for 3D printing", "bu fotoğraftan 3D model yap", "ürünümün 3 boyutlu modelini çıkar", "3D yazıcı için STL hazırla".
  Chain: consumes reference images from `image` and character sheets from `character`; produces GLB, USDZ, FBX, OBJ, STL files.
  NOT for: a picture that only looks 3D (use `image`); turntable or product videos (use `video`); product photos (use `product-photoshoot`); batches (use `pipelines`); model choice (use `models`); setup problems (use `setup`).
argument-hint: "[image paths | description | mesh file] [--use product|game|ar|print] [--model <endpoint-id>]"
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" *) Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/glbinfo.py" *) Bash(command -v genmedia) Bash(genmedia models *) Bash(genmedia schema *) Edit(.genmedia/**) Read
license: MIT
compatibility: Requires the genmedia CLI >= 0.7.0 with a fal key configured by the user, and python3 >= 3.8. A glTF viewer, Blender or macOS Quick Look is optional and only used by the user to look at the result.
---

# 3D

Meshes from one image, several views or a description, plus post-processing of a mesh that already exists. Half of the quality is decided before the paid call (the input picture), and the agent cannot look at a mesh: so this skill is input prep, routing by intended use, and an honest file inspection. Mechanics live in `references/cli-contract.md` and `references/platform.md`.

## Step 0 — Preflight

```bash
command -v genmedia
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" preflight
```

- `blockers` not empty, CLI missing or older than 0.7.0 → `/genmedia-skills:setup`. Key missing → the user runs `genmedia setup` or exports `FAL_KEY` themselves; wait. Never read, print, request or type a key.
- Keep `config.announce_above_usd` and `config.confirm_above_usd` (defaults 0.50 and 2): they are the cost gate. One default asset sits just under the announce line; most options push it over.
- Resume first: `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --label <slug> --tail 5`. A `submitted` or `pending` request for this asset → `gm.py wait`, never a second `run`.

## UX rules

1. Reply in the user's language (Turkish in → Turkish out). Prompts to models are English. IDs, field names and paths stay as they are.
2. No JSON, request IDs or tool narration in chat. Wait silently; one status line at most.
3. **Question budget: 1, as labelled options, only when the request does not reveal the intended use.** The use decides format, triangle budget and textures:

   | Use (first = default) | Deliver | Triangle budget (heuristic) | Texture |
   |---|---|---|---|
   | A product visualisation, web viewer, general | GLB, plus the other formats the endpoint returns | endpoint default; web viewer about 100k to 200k | yes; PBR when the material matters (metal, glass, leather) |
   | B game prop or engine asset | GLB and FBX | prop 5k to 30k, hero asset up to about 100k | yes, PBR |
   | C AR on a phone | USDZ (iOS) and GLB (Android, web) | about 100k or less, textures 2048 px or less | yes |
   | D 3D printing | STL | not critical | none, geometry only |

   "For my shop", "Unity", "AR", "print" answer it: ask nothing, with one exception: use C without a real size → spend the question on the object's real height (options: a number in cm, or "skip: deliver unscaled"), because scaling later is another paid call. Vaguest request ("make this 3D") → use A with every default, stated in the delivery line. Not counted: a missing input file, consent, a cost confirmation. Budgets are labelled heuristics (`references/use-cases.md`); the target engine or store decides: tell the user to check its current rules.
4. Never infer approval from silence or success. Two checkpoints: a reference picture made for a mesh call that costs `announce_above_usd` or more is shown and approved before the mesh is paid for (below that, self-check it and continue); and a generated mesh is delivered and looked at **by the user** (they can open it, you cannot) before you pay for rigging, retexture variants or a premium retry on top of it. Mechanical derivatives the user already asked for (a remesh to a stated budget) run without a stop.
5. Cost: estimate before the first paid call (Workflow step 5). Under announce → run; up to confirm → one line with the estimate, then run; at or above confirm, or a batch that crosses it → wait for an explicit yes. Never swap a model the user named to save money.
6. Honesty: you inspect file structure, a preview image and texture maps. You never claim to have seen the model from all sides, and never promise a watertight, print-ready or engine-approved mesh. Sides the input does not show are invented by the model: say so once.
7. Facts come from the user: real-world size, part names, materials. Never invent dimensions. A real person's photo or a scanned likeness needs the user's confirmation of consent. No third-party characters, toys or branded products the user does not own the rights to. Uploads and results are public URLs: say so once for unreleased products.
8. Bounded repair: 3 attempts per asset, something changes each time, a policy rejection is never resent unchanged, a job with a request ID is resumed, never resubmitted.

## Discovery guardrail

`references/models-3d.md` (verified 2026-09-20) and `references/routing-utility.md` are dated caches. Before the first paid call to an endpoint in a session:

```bash
genmedia models --endpoint_id <endpoint_id> --json
python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" schema <endpoint_id>
```

- `status` must be `active`. Otherwise: next row for that intent below, else list the live catalog and pick the newest active match, and say which model ran:
  ```bash
  genmedia models --category image-to-3d --no-classify --limit 100 --json
  ```
  The other two categories are `text-to-3d` and `3d-to-3d`.
- Field names do not transfer between families: `input_image_url` (Hunyuan), `image_url` (Tripo, Meshy, Trellis, Hi3D), `image_urls` (Rodin, multi-view endpoints), `model_url` (Meshy post-processing), `mesh_url` (Tripo, Hi3D, Trellis post-processing), `input_file_url` (Hunyuan post-processing). Read the schema, never guess.
- Never `genmedia run` without an endpoint ID: smart routing still resolves a 3D default that fal has removed (`references/models-3d.md` section 8).

## Routing

First match wins. No picture yet → make one first (row "Description only"), then route it by the rows above that one. Exact fields, options and output paths: `references/models-3d.md`. Prices are hints dated 2026-09-20; `gm.py price` and the model's pricing text decide.

| Intent | Endpoint | Why | Price hint |
|---|---|---|---|
| Change a mesh that already exists (remesh, retexture, rig, convert, split, scale) | see `references/post-processing.md` | 3d-to-3d endpoints take a mesh URL, not an image | USD 0.20 to USD 0.75 |
| Humanoid character that must be rigged or animated | `meshy/v7.1/image-to-3d` (`enable_rigging`, `pose_mode`); 2 to 4 views: `meshy/v7.1/multi-image-to-3d` | the only generation family with rigging and animation presets in the same call | USD 1.20 textured, +USD 0.20 rig, +USD 0.12 animation |
| 3D printing | `fal-ai/hyper3d/rodin/v2.5` with `geometry_file_format: "stl"`, `material: "None"` | writes STL directly, takes 1 to 5 images | USD 0.40 |
| Polygon budget under 40,000 faces (game prop, web, mobile) | `tripo3d/h3.1/image-to-3d` with `face_limit` | `face_limit` 1,000 to 2,000,000 at no surcharge; PBR on by default; optional quads | USD 0.30, +USD 0.05 quads |
| 2 to 4 real photos of one object | `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d` with named view fields; polygon budget needed: `tripo3d/h3.1/multiview-to-3d` | named slots (`back_image_url`, `left_image_url`, ...) avoid order mistakes; Tripo takes `image_urls` in the order front, left, back, right | USD 0.525; Tripo USD 0.30 |
| One image, product visualisation, AR or general (**default**) | `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d` | routing default; returns GLB, OBJ (with MTL and texture) and a preview thumbnail; its FBX and USDZ slots came back null on 2026-09-21; optional PBR | USD 0.375, +USD 0.15 each for PBR, extra views, custom `face_count` |
| Description only | reference picture first (`/genmedia-skills:image`, brief in `references/input-prep.md`), then the rows above | you see and fix a cheap picture before paying for a mesh | picture cents + mesh |
| Description only, no picture step wanted | `fal-ai/hunyuan-3d/v3.1/pro/text-to-3d`; budget `tripo3d/h3.1/text-to-3d`; rigged `meshy/v7.1/text-to-3d` | same families, prompt at most 1024 characters (Meshy 600) | USD 0.375; USD 0.20; USD 1.20 |
| Highest geometry detail, user accepts the price | `hitem3d/hi3d/v3.0/image-to-3d` | 100,000 to 5,000,000 faces, five export formats | USD 2.10 and up: always confirm |

Tie-breakers:

1. The user named a model → use it after the live check; mention the default in one line.
2. Budget wins only when the user asks for cheap or a draft: `tripo3d/h3.1/image-to-3d` with `texture: false` (about USD 0.20) or `fal-ai/hunyuan-3d/v3.1/rapid/image-to-3d` (about USD 0.225). Never downgrade silently.
3. Texture resolution is the complaint → `fal-ai/trellis-2` (`texture_size` up to 4096) or Tripo `texture_quality: "detailed"`; see `references/troubleshooting-3d.md`.
4. A format the chosen endpoint does not return → convert afterwards (`references/post-processing.md`), do not switch the generation model for the format alone, except for printing.
5. `@handle` or a character sheet → `/genmedia-skills:character` owns the sheet; crop ONE figure per image before any mesh call.

Named traps:

- **3D-looking picture.** "3D render of a logo", "isometric icon", "clay style illustration" are pictures: `/genmedia-skills:image`. A spinning product clip is `/genmedia-skills:video`. This skill starts when the user needs a mesh file.
- **Rigging where there is none.** Only the Meshy rows rig. Hunyuan, Tripo, Rodin, Trellis and Hi3D return static meshes; rig them afterwards with `fal-ai/meshy/rigging` (humanoids with clearly separated limbs only).
- **Sheet as input.** A turnaround sheet or a collage becomes one fused object. One object per image, always.
- **Low-poly look vs polygon budget.** Meshy `model_type: "lowpoly"` is a style and ignores `topology`, `target_polycount` and `should_remesh`. A number of triangles is a budget: `target_polycount` (Meshy) or `face_limit` (Tripo). A bare "low-poly" next to an engine name (Unity, Unreal, Godot, mobile) means the budget; the look only when the user describes a style (faceted, flat-shaded, stylised). Say which one you chose.
- **Hunyuan minimum.** `face_count` starts at 40,000 and any custom value adds USD 0.15. A small budget is a Tripo job or a remesh afterwards.
- **Quad output changes the file.** Tripo `quad: true` can return FBX in `model_mesh`; `glbinfo.py` reads FBX only as a header.
- **Meshy price.** `gm.py price` shows 0.8 per generation; that is the untextured base. The default call (`should_texture: true`) is USD 1.20.
- **Watertight.** No endpoint documents a watertight guarantee. `glbinfo.py --deep` counts open edges; a slicer decides.

## Workflow

1. **Intent and use.** Decide image, multi-view, text or post-processing, and the use (UX rule 3). Pick a slug (`seramik-kupa`): it is the label, the ledger filter and `genmedia-output/<slug>/`. Natural-language labels work; the helper transliterates Turkish letters. More than one paid step (views, mesh, post-processing) → keep a state card at `.genmedia/projects/<slug>/3d.md` (Write tool) and update it after every step, so a later session resumes instead of paying again:
   ```text
   # <asset> — 3d   use: product | game | ar | print   budget: <triangles or default>   real height: <metres from the user | unknown>
   inputs: <file → what it is: user photo | cut-out | generated view (guess)>
   route: <endpoint_id> {<the options you set>}   est: $<plan total>
   [ ] input check  [ ] views  [ ] mesh  [ ] inspect  [ ] user looked  [ ] post: <step>  [ ] delivered
   log:
   - <date> mesh attempt 1: <stats_line> | warnings: <codes> | change next: <what>
   ```
2. **Look at every input with the Read tool** and run the input checklist in `references/input-prep.md`: one object, whole and uncropped, plain background, neutral light, no strong perspective, no text overlays, size and format inside the endpoint's limits. HEIC, TIFF or oversize → convert first. A failing input is fixed before any mesh call:
   - busy background → one background-removal call (exact input in `references/input-prep.md`);
   - cropped, held in a hand, several objects, harsh shadows, or no picture at all → `/genmedia-skills:image` with the reference-picture brief from `references/input-prep.md`; take back the file path and URL;
   - back and sides matter (360 degree product view, characters) and the user has one photo → orbit views, step 3.
3. **Optional orbit views.** Real photos of the other sides beat generated ones: use them whenever the user sent or offered them (asking for them is not worth the question budget; mention it in the delivery instead). Otherwise generate back, left and right from the front picture with `fal-ai/qwen-image-edit-2511-multiple-angles` (plan in `references/input-prep.md`, about USD 0.04 per view), Read all of them, drop any view that changed the object, and tell the user these sides are the model's guess.
4. **Verify** each endpoint (Discovery guardrail) and build the input JSON from the row in `references/models-3d.md`. Set on purpose, never by default: texture on or off, PBR, the face or polygon target for the use, topology, pose (`a-pose` for characters to be rigged), export format.
5. **Price it.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price <endpoint_id> --explain
   ```
   Assets are priced per generation with add-ons, and the API number is often not the price (`0.015 units`, `0.01 credits`, Meshy's `0.8`). Dollars = the tier in `pricing_text` that matches YOUR input + every add-on your input switches on (PBR, extra views, custom face count, detailed geometry or texture, quads, rigging, animation, HighPack). No `pricing_text` for a Meshy or Rodin row → use the dated tiers in `references/models-3d.md` and say "about". A unit price with no published unit count (`tripo3d/tripo/remesh`, `hitem3d/hi3d/texture`) → say the cost is unknown and ask before running. Sum the whole plan: prep calls + mesh + post-processing; say that repairs are extra. One default asset is about USD 0.38 (run); PBR, views or Meshy cross the announce line; a batch of six default assets, or one Hi3D call, crosses the confirm line.
6. **Upload and run**, one asset per call. Write the input with the Write tool to `.genmedia/tmp/<slug>.json` (no heredocs), then:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload ./mug-front.png
   python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" run fal-ai/hunyuan-3d/v3.1/pro/image-to-3d --input .genmedia/tmp/<slug>.json --label "<slug>" --est-cost 0.38 --download "genmedia-output/<slug>/<slug>_{index}.{ext}"
   ```
   Give the Bash call a **600000 ms timeout**: the helper submits async and polls up to 540 s, and meshes take minutes. `status: "pending"` → `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" wait <endpoint_id> <request_id>` with the same timeout, as often as needed. Never a second `run` for the same asset. Several assets → one `gm.py batch` plan (`references/cli-contract.md`), one job per asset, gate on the sum.
7. **Pick the files by `outputs[].json_path`**, not by index: `model_glb` or `model_mesh` (the mesh), `model_urls.<format>` (other formats, often null; `model_urls.glb` and Tripo's `pbr_model` repeat the main mesh, so the same GLB can arrive two or three times), `thumbnail` or `rendered_image` (preview), `texture_urls[0].base_color`, `rigged_character_glb`, `animation_glb`. Full map: `references/models-3d.md`.
8. **Inspect before anything is shown.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/glbinfo.py" inspect genmedia-output/<slug>/<file>.glb --use product --expect-textures
   python3 "${CLAUDE_SKILL_DIR}/scripts/glbinfo.py" textures genmedia-output/<slug>/<file>.glb --out-dir genmedia-output/<slug>/textures
   ```
   `--use product|game|ar|print` sets the heuristic budgets; add `--max-triangles <n>` for the user's own budget, `--expect-rig --expect-animations` for characters, `--deep` for printing (open and non-manifold edges). Then Read the preview image and the extracted base-colour map. Review, in this order: file parses → mesh count and triangles against the budget → textures present when asked → bounds not zero and not flat (a thin box is a relief, not an object) → bounding-box proportions match the object in the picture → preview silhouette and colours match the input, no floor plate, no fused background → rig and clips present when asked. Every `warn` is either repaired or reported. Rubric and fixes: `references/troubleshooting-3d.md`.
9. **Repair or post-process** inside the budget (UX rule 8): better input, extra views, another face target, remesh, retexture, convert, rig. Repair without asking only on a hard fail (file does not parse, no geometry, flat relief, textures or rig missing although asked) and only while the running total stays under `confirm_above_usd`; any other warning is delivered in plain words with the fix as the next step. Each post-processing call is a paid step: price it, add it to the estimate, inspect its output again. A regenerated mesh invalidates every step after it (remesh, retexture, rig): untick them on the state card and redo them from the new URL; never mix files from two attempts.
10. **Deliver** with the template below. Offer one next step.

## Delivery

```
3D model ready: genmedia-output/<slug>/<file>.glb
Also: <file>.usdz, <file>.fbx, <file>.obj <only formats that were really returned>
Stats: <stats_line from glbinfo.py: size, meshes, vertices, triangles, materials, textures, dimensions, rig, clips>
Checked: file structure, preview render and texture map. I have not seen the model from every side. <warnings in plain words, or "No warnings.">
<only when sides were generated or unseen:> The back and sides are the model's guess; send photos of them for a closer match.
<only for printing:> Open edges found: <n>. Watertightness is not guaranteed: open the STL in your slicer and run its repair before printing. Set the size there: the file has no real-world scale.
View it: <only what fits the delivered files:> macOS Quick Look (select the .usdz, .obj or .stl, press space), any glTF viewer in the browser (drag the .glb in), or Blender (File, Import, glTF 2.0).
Link: <cdn url> (public to anyone with the link; may expire: the local files are your copy)
<model display name> · use: <use> · est. $<total> <including n repairs>
<only for several assets:> Gallery: <gallery_url>
Chosen for you: <every default the user did not set: use, texture, PBR, face target, format>
Next: <one step: remesh to <n> triangles, USDZ for AR, rig and animate, retexture>
```

Translate it; keep paths, numbers and field names. A failed or withheld asset: say which check failed and what you would change, never deliver it as done.

## Errors

| Signal (verbatim) | Do |
|---|---|
| `"status":"pending"` with `resume` | `gm.py wait <endpoint_id> <request_id>`, 600000 ms timeout. Never resubmit: a second mesh is a second charge. |
| `fields[].type: "missing"`, field `input_image_url`, `image_url`, `image_urls`, `model_url` or `mesh_url` | Wrong input field for this family. Re-read the schema (Discovery guardrail). |
| `"kind":"validation"` with `"fields":[]` and a `hint` (queue said `COMPLETED`, the job failed) | Check in order, change the first thing that is off: fields and ranges against the OpenAPI schema (`face_count` 40000 to 1500000, `animation_action_id` 0 to 696, `enable_animation` only with `enable_rigging`) → the input file (format, 8 MB and 5000 px on Hunyuan, expired URL → upload again) → the picture itself (no clear object, a person, a policy term in the prompt). Max 3 attempts; may have been billed. |
| `image_too_large`, `file_too_large`, `image_too_small`, `unsupported_image_format` | Resize or re-encode locally to PNG or JPEG inside the limits in `references/models-3d.md`, upload again. |
| `file_download_error` on a mesh URL | The mesh link expired or is not public. `gm.py upload` the local GLB and pass the new `cdn_url`. |
| `"kind":"content_policy"` | Do not resend unchanged. Usual causes: a real person, a branded character, a weapon prompt. Say what was flagged, offer a compliant change. |
| `"kind":"not_found"` | Stale ID → Discovery guardrail; say which model ran. |
| `"kind":"auth"` | Stop. The user fixes the key or balance. |
| `glbinfo.py`: `"kind":"parse"`, `"format":"unknown"` or a `length_mismatch` warning | The download is not a whole mesh (error page, truncated file); the job itself succeeded. Move the broken file away and run `gm.py wait <endpoint_id> <request_id>` to download again; never deliver it, never regenerate to replace a download. |

Wrong rather than failed (flat relief, melted back, floor plate, blurry texture, too heavy, mirrored sides, rig fails): `references/troubleshooting-3d.md`. Platform error types: `references/platform.md` section 4.

## This skill does NOT

- Render pictures or turntable videos of a model (use `/genmedia-skills:image`, `/genmedia-skills:video`), shoot product photos (use `/genmedia-skills:product-photoshoot`), or place the mesh in a scene.
- Look at the mesh. It reads headers, counts, bounds, textures and the preview image, and says exactly that.
- Guarantee watertight, manifold, print-ready, game-ready or store-approved output. It states what was measured and what the user must check.
- Reproduce readable label text or a logo on the texture: print comes back blurred on every tier. Say so before paying when the product carries text.
- Invent real-world dimensions, or rig non-humanoid shapes (animals, vehicles, props): the rigging endpoints are humanoid-only.
- Run Blender, slicers or converters for the user. `glbinfo.py tools` reports what is installed; suggestions are optional extras.

## Common mistakes

- Paying for a mesh from a bad picture: cropped object, busy background, strong perspective, several objects. Fix the picture first; it costs cents.
- Leaving texture, PBR and face targets to the defaults, then discovering a 500,000-face file for a phone.
- Asking Hunyuan for a small polygon budget, or asking any non-Meshy endpoint for a rig.
- Feeding a character sheet or a collage as one image.
- Reading outputs by index instead of `json_path`, and delivering the thumbnail as the model.
- Submitting again after a timeout instead of `gm.py wait`.
- Saying "looks great" about a file you cannot see, or "ready to print" about a mesh nobody sliced.
- Re-running the same input hoping for a better mesh. Change the input, the views, the options or the model.

## Reference index

- `references/models-3d.md`: read when building any input JSON; per endpoint (dated 2026-09-20): purpose, exact input fields, options, limits, output `json_path` map, price tiers.
- `references/input-prep.md`: read before every image-based call; the input checklist, local conversion, the background-removal call, the reference-picture brief for `image`, the orbit-view plan and the view-to-field mapping per multi-view endpoint.
- `references/use-cases.md`: read after the use is known; per use (product visualisation, game prop, AR, printing): formats, labelled triangle and texture heuristics, endpoint options, what to check, what to tell the user.
- `references/post-processing.md`: read when the user brings a mesh or a delivered asset needs remesh, retopology, retexture, rigging, animation, conversion, scaling or splitting; verified 3d-to-3d endpoints with exact fields and chains.
- `references/troubleshooting-3d.md`: read when a result is wrong rather than failed, a warning from `glbinfo.py` needs a decision, or a job misbehaves; the review rubric and the repair ladder.
- `references/routing-utility.md`: read when the default is not active or the user asks for another tier; tasks `image-to-3d`, `text-to-3d`, `multiview-to-3d`, `mesh-remesh`, `mesh-retexture`, `mesh-rig` and the stale-ID table.
- `references/routing-image.md`: read when preparing inputs; tasks `bg-remove-image`, `character-identity` (the multiple-angles endpoint) and `t2i-general`.
- `references/cli-contract.md`: read when a helper call fails, a job is pending, or you need `batch`, `wait`, `cancel`, the ledger or the raw CLI.
- `references/platform.md`: read when estimating cost, reacting to a platform error type, or explaining URL privacy, expiry and billing.
- `scripts/gm.py`: shared helper for every paid call (`preflight`, `price`, `upload`, `run`, `wait`, `batch`, `ledger`).
- `scripts/glbinfo.py`: local, free, no network: `inspect` (GLB, glTF, plus header-level OBJ, STL, FBX, USDZ), `textures` (extract embedded maps so you can Read them), `tools` (viewers and converters installed here); one JSON object per call, exit 0 ok, 1 failed, 2 usage.
