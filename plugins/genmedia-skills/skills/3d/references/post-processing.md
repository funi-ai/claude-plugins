# Post-processing an existing mesh (verified 2026-09-20, catalog re-read 2026-10-05)

Category `3d-to-3d`: 10 active endpoints on 2026-10-05 (`genmedia models --category 3d-to-3d --no-classify --limit 100 --json`). Fields below come from the live OpenAPI schemas; prices from the pricing API and each model's `llms.txt`. Every call here is a paid step: verify the endpoint (SKILL.md, Discovery guardrail), price it, add it to the plan total, run it through `gm.py run` with a 600000 ms Bash timeout, and **inspect the output again** with `scripts/glbinfo.py`. Compare the two stats lines; that comparison is the review.

Tier rows for the four routed post-processing tasks (`mesh-remesh`, `mesh-retexture`, `mesh-rig`, plus `multiview-to-3d` on the generation side) are in [routing-utility.md](routing-utility.md); this file is the field-level detail behind them, and adds the endpoints no tier row carries (splitting, colour reduction, conversion).

`fal-ai/meshy/v5/remesh` and `fal-ai/meshy/v5/retexture` were unlisted on 2026-10-05: do not call them. Nothing active took over their target formats, real-world height, pivot or text-prompt retexture; the rows below say what is left. <!-- lint:ignore -->

## 1. Getting the mesh in

Every endpoint takes a **URL**, under a family-specific field name: `model_url` (Meshy), `mesh_url` (Tripo, Hi3D, Trellis), `input_file_url` (Hunyuan).

- A mesh from this session: reuse the `url` of the right `outputs[]` entry. Links expire; `file_download_error` → upload the local file again.
- A local file from the user:
  ```bash
  python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" upload ./chair.glb
  ```
  Inspect it first (`glbinfo.py inspect ./chair.glb`): format, triangles, textures, rig. The CLI uploads `.glb` and `.obj` with a model MIME type and everything else (`.fbx`, `.stl`, `.usdz`) as a generic binary; an endpoint that rejects it needs a GLB instead.
- A mesh the user did not make: ask once whether they have the right to modify it. Uploads are public URLs.

## 2. Intent → endpoint

| Intent | Endpoint | Why | Price hint |
|---|---|---|---|
| Clean retopology of a heavy AI mesh, triangles or quads, without a numeric target (routing default) | `fal-ai/hunyuan-3d/v3.1/smart-topology` | density levels instead of a count; GLB or OBJ up to 200 MB | $0.75 |
| A numeric budget (500 to 20,000 faces) with textures baked onto the new mesh | `tripo3d/tripo/remesh` | `bake` is documented; keeps named parts | unit-priced, cost per call unpublished: ask first |
| Real-world height, pivot at the bottom | no active endpoint (2026-10-05) | say so; the user scales in the AR view or in their tool | - |
| Texture or retexture a mesh from a reference picture | `fal-ai/trellis-2/retexture` (GLB, OBJ, PLY, STL in; GLB out) or `hitem3d/hi3d/texture` (GLB in; five formats out) | image-conditioned texturing; no active endpoint takes a text prompt (section 5) | Trellis $0.20 to $0.24; Hi3D unit-priced, unpublished: ask first |
| Rig a humanoid, walking and running clips included | `fal-ai/meshy/rigging` | works on GLBs from any generator | $0.20, +$0.12 with one animation (the pricing API's 0.8 is per generation; a rig bills 0.25: section 4) |
| Rig once, several animation clips | `fal-ai/meshy/rigging/multi-animation` | up to 10 clips against one rig | $0.20 + $0.12 per clip |
| Split into parts (articulated figures, print-in-parts, kitbashing) | `hitem3d/hi3d/split`; FBX under 30,000 faces: `fal-ai/hunyuan-3d/v3.1/part`; named parts for a later remesh: `tripo3d/tripo/segment` | character templates with printable joints; general split by granularity | $0.40; $0.45; Tripo unpublished |
| Reduce a textured model to 1 to 8 flat colours (multi-colour printing) | `hitem3d/hi3d/multicolor` | GLB in; GLB, OBJ or FBX out | $0.40 |
| Format conversion only | see section 6 | the catalog has no pure converter | - |

## 3. Remesh and retopology

`fal-ai/hunyuan-3d/v3.1/smart-topology`: `input_file_url` (GLB or OBJ, at most 200 MB), `input_file_type` `glb` (default) or `obj`, `polygon_type` `triangle` (default) or `quadrilateral` (mixed quads and triangles), `face_level` `high`, `medium` (default), `low`. Output: `model_glb`, `model_urls.glb|fbx|obj|mtl|texture|usdz` (the schema lists them; which ones come back was not measured). $0.75 per call. **Trap:** `input_file_url` is not marked required and defaults to fal's sample model: a call without it bills $0.75 for retopologising the sample. Always set it, and check the result's proportions against your input.

`tripo3d/tripo/remesh`: `mesh_url`* (GLB, OBJ, FBX, STL, at most 150 MB), `face_limit` 500 to 20000 (500 to 10000 with quads; unset = adaptive), `quad` (false; true forces FBX output and a 10000 default), `bake` (true: bakes textures onto the new mesh), `part_names` (from a previous `tripo3d/tripo/segment` call, to keep parts separate). Output: `model_mesh`, `rendered_image`, `model_urls.glb|fbx|base_model|pbr_model`. Price: `$0.01 per units` with no unit count published → tell the user the cost is unknown before running it.

Neither schema promises that textures survive. Inspect the result with `--expect-textures`; when they are gone, retexture from the original photo (section 5) or go back to a generation-time face target. Neither takes a height or a pivot: a real-world size is set by the user in the AR view, the engine or Blender, never guessed.

## 4. Rigging and animation

`fal-ai/meshy/rigging`: `model_url`* (a GLB; "must be a humanoid character with clearly defined limbs"), `height_meters` (1.7), `enable_animation` (false), `animation_action_id` (92; read only when `enable_animation` is true, and then a value outside 0 to 696 is a 422; 0 = Idle; library: https://docs.meshy.ai/en/api/animation-library), `enable_safety_checker`. Output: `rigged_character_glb`, `rigged_character_fbx`, `basic_animations.walking_glb|running_glb|walking_fbx|running_fbx|walking_armature_glb|running_armature_glb`, with animation `animation_glb`, `animation_fbx`, plus `rig_task_id`.

`fal-ai/meshy/rigging/multi-animation`: `model_url`*, `animation_action_ids`* (1 to 10 distinct IDs, each 0 to 696; duplicates are dropped), `height_meters`. Output: the rig files as above and `animations[]` with `action_id`, `animation_glb`, `animation_fbx` in request order.

- Price: $0.20 per rig. The `llms.txt` text says $0.20 per rig, +$0.12 per animation clip; the pricing API returns 0.8 (rigging) and 0.08 (multi-animation) per "generation", and a request bills a fraction of one: the fal billing page showed one rig (no animation) as 0.25 generations x $0.80 = $0.20 (2026-09-21). Estimate from the pricing text (`--explain`): $0.20, +$0.12 with `enable_animation`; multi-animation $0.20 + $0.12 per clip (the animation surcharges were not measured). The CLI and the result never show what a job cost; only the account's billing page does.
- Before paying, Read the asset's preview image: one humanoid, A-pose or T-pose, arms and legs clearly apart, nothing crossing the silhouette. A pose with fused limbs fails or rigs badly; regenerating with `pose_mode: "a-pose"` (Meshy) or a corrected reference picture is the real fix.
- Measured 2026-09-21 (`platform.md` section 10): a 500k-triangle Hunyuan GLB rigged without a remesh: a 24-joint armature, the rigged GLB kept its texture, and the walking and running clips (about 1.1 s loops) came as GLB, FBX and armature-only GLB. With a download template all eight files arrive, about 230 MB for that mesh; deliver the ones the user needs.
- One 500k-triangle rig succeeded, so do not remesh first by reflex. After a failed rig, a remesh to a game budget (section 3) is still the first thing to change; it is not a documented limit.
- Animals, vehicles, props, creatures with extra limbs: not supported by these endpoints. Say so; deliver the static mesh.
- Pick an animation ID only from the user's words ("idle", "wave", "run") by looking it up in the linked library; never invent an ID's meaning. No lookup possible → rig without `enable_animation`; walking and running clips are included anyway.
- Inspect `rigged_character_glb` with `--expect-rig`, each clip file with `--expect-rig --expect-animations`; report joints, clip count and durations. The FBX twins are delivered unparsed (header only).

## 5. Retexture and texturing

`fal-ai/trellis-2/retexture`: `image_url`* (the reference photo), `mesh_url`* (an untextured GLB, OBJ, PLY or STL), `texture_size` 1024, 2048 (default), 4096, `resolution` 512 or 1024 (default), `seed`, sampler fields (`tex_slat_*`) left at their defaults. Output: `model_glb`. $0.20 at 512, $0.24 at 1024.

`hitem3d/hi3d/texture`: `image_url`*, `mesh_url`* (GLB only, for example a geometry-only Hi3D result), `model` `hitem3dv1.5` (default) or `scene-portraitv1.5`, `resolution` `512`, `1024`, `1536`, `1536pro`, `export_format`. Output: `model_mesh`, `thumbnail`. Billed per credit with no count published → unknown cost, ask first.

Both take a picture, not words. A look the user describes ("matte black", "three colourways") needs a reference picture per look first: hand off to `/genmedia-skills:image` for an edit of the product photo in that finish, check that the edit kept the product, then texture from it. Both schemas describe `mesh_url` as an untextured mesh; how they treat a textured one was not measured, so inspect the result.

- Colour variants of one asset → one picture per variant, then one `gm.py batch` plan, the same `mesh_url`, one `image_url` per job; the gate applies to the sum.
- The user's brand colours and materials come from the user. No third-party logos or character designs.

After any texturing call: `glbinfo.py textures <file> --out-dir <dir>`, Read the base-colour map (not black, not blank, colours as asked) and the `thumbnail` when the endpoint returns one.

## 6. Format conversion, honestly

Searched on 2026-09-20 and 2026-10-05: fal's catalog has **no pure mesh converter**. Options, best first:

1. The format was already returned. Look for `model_urls.<format>` in `outputs[]`. Measured 2026-09-21: Hunyuan 3.1 Pro returned obj (with mtl and texture) and left fbx and usdz null; Tripo H3.1 returned glb (and `pbr_model`, the same file) only; fbx comes with `quad`. Meshy 7.1's schema lists fbx, obj, usdz, stl, blend.
2. Generate straight into the format when generation is still ahead: Rodin v2.5 `geometry_file_format`, Hi3D `export_format`. From an existing asset this is a second mesh from the same picture, not a conversion: say so.
3. A paid post-processing call whose schema lists the format: `tripo3d/tripo/remesh` (FBX; cost unpublished), `fal-ai/hunyuan-3d/v3.1/smart-topology` (FBX, OBJ, USDZ; $0.75), `hitem3d/hi3d/texture` `export_format` (needs a picture; cost unpublished). Each rebuilds or retextures the mesh, none of these slots was measured: offer it priced, never as a sure conversion, and inspect for lost textures.
4. A local tool when one exists (`glbinfo.py tools`): Blender, `usdzconvert`, `gltf-transform`, `assimp`. Optional; suggest the command to the user instead of assuming it works, and never block delivery on it.

GLB is the reference deliverable: it is the one format the inspector reads fully.

## 7. Splitting and colour reduction

`hitem3d/hi3d/split`: `mesh_url`* (GLB, STL or OBJ, at most 200 MB), `model` `character` (default; humanoid templates) or `general`, `part` `a` to `f` (character templates: a = 6 parts, b = 5, c = 4 without head, d = 4 with head, e = 3, f = 2), `joint` `none`, `ball` (default), `dovetail` (connectors between character parts, useful for printing), `level` `low`, `medium`, `high` (granularity, general model only), `export_format` (character split: GLB only). Output: `model_mesh`, `thumbnail`. $0.40.

`fal-ai/hunyuan-3d/v3.1/part`: `input_file_url`* (**FBX only**, at most 100 MB, at most 30,000 faces). Output: `result_files[]` (FBX parts). $0.45.

`tripo3d/tripo/segment`: `mesh_url`* (GLB, OBJ, FBX, STL, at most 150 MB). Output: `model_mesh`, `part_names[]` (feed them to `tripo3d/tripo/remesh`), `rendered_image`. Cost per call unpublished.

`hitem3d/hi3d/multicolor`: `mesh_url`* (a textured GLB, at most 200 MB), `number_of_colors` 0 to 8 (default 4; 0 = the maximum, for later editing), `export_format` `glb`, `obj`, `fbx` (no STL, USDZ or 3MF). Output: `model_mesh`, `thumbnail`. $0.40.

## 8. Chains that work

| Goal | Steps | Est. |
|---|---|---|
| AR pair from a fresh asset | generate (Hunyuan, `face_count` 100000) → take `model_glb` and `model_urls.usdz` if it came back (it was null on 2026-09-21) → a missing USDZ is an offer, not an automatic step (section 6) | $0.525 |
| Game prop from a heavy mesh the user owns | inspect → `tripo3d/tripo/remesh` with `face_limit` = the budget (ask first: cost unpublished), or Hunyuan Smart Topology with `face_level: "low"` → inspect with `--max-triangles` → retexture only if textures were lost | $0.75 for Hunyuan, Tripo unpublished |
| Rigged character from a static mesh | Read the preview (pose check) → `fal-ai/meshy/rigging` (remesh first only for a game budget or after a failed rig) → inspect `rigged_character_glb` | $0.20; +$0.20 with a remesh; +$0.12 with an animation clip |
| Print in parts with joints | generate geometry-only → `hitem3d/hi3d/split` (`character`, `joint: "dovetail"`) → inspect the GLB with `--deep`; the STL comes from the user's own tool (`glbinfo.py tools` lists what is installed here) | $0.80 and up |
| Three colourways of a product | three reference pictures (`/genmedia-skills:image`) → one batch of `fal-ai/trellis-2/retexture`, the same `mesh_url`, one picture per job | $0.72 at 1024, plus the pictures |

Order rule: geometry first (remesh, split), then texture, rig last. No schema here documents that a remesh or a retexture keeps a skeleton: assume the rig is lost and re-inspect with `--expect-rig` if you ever process a rigged file. Texturing before a remesh can be wasted money.
