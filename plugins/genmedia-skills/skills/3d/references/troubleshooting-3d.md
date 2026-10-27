# Troubleshooting 3D assets (2026-09-20)

For results that are **wrong rather than failed**, for inspector warnings that need a decision, and for jobs that misbehave. Platform error types: [platform.md](platform.md) section 4. Helper and ledger mechanics: [cli-contract.md](cli-contract.md). Fields named here are verified in [models-3d.md](models-3d.md) and [post-processing.md](post-processing.md).

## 1. The review rubric (run it on every asset before it is shown)

You cannot see the mesh. You can see four things: the inspector's JSON, the preview image, the texture maps and the input picture. Use all four, in this order; stop at the first hard fail.

| # | Check | Evidence | Pass | Fail → |
|---|---|---|---|---|
| R1 | The file is a mesh | `glbinfo.py inspect`: `ok: true`, no `length_mismatch`, no `chunk_truncated` | parses, size plausible (a textured GLB is usually megabytes, not kilobytes) | section 4, "download is not a mesh" |
| R2 | Geometry exists and fits the budget | `triangles`, `over_budget`, `heavy_for_web` | inside the user's or the heuristic budget | lower the face target or remesh |
| R3 | It is an object, not a relief | `bounds.size`, `thin_bounds`, `zero_bounds` | no dimension under about 2% of the largest, unless the object really is flat (a coin, a card) | section 2, "flat relief" |
| R4 | Proportions match the picture | compare `bounds.size` ratios with the object's width to height in the input (Read it) | within roughly 15% | section 2, "stretched or squashed" |
| R5 | Textures are there and mapped | `textures.images`, `has_uv`, `no_textures`, `no_uv`, `vertex_colors_only`, `unused_textures` | base-colour image present, UVs present | section 2, "no or broken texture" |
| R6 | Colours are right | `glbinfo.py textures`, then Read the `base_color` map; Read the preview | recognisable colours of the product; not black, grey or blank | section 2, "wrong colours" |
| R7 | Silhouette and parts | Read `thumbnail` or `rendered_image` next to the input | same outline, same number of parts (handles, legs, wheels), no floor plate, no background slab, no second object | section 2 |
| R8 | Rig and clips, when asked | `skins`, `joints`, `animations[].duration_s`, `no_skin`, `no_animations` | one skin with a plausible humanoid joint count; clips longer than 0 s | section 3 |
| R9 | Printing only | `--deep`: `topology.open_edges`, `non_manifold_edges`; `multiple_parts` | reported as numbers, never as "watertight" | section 2, "open edges" |
| R10 | Scale, AR only | `bounds.max_dimension`, `scale_large`, `scale_tiny`, `scale_unverified` | matches the user's real size after a resize; otherwise reported as unscaled | [use-cases.md](use-cases.md) section 4 |

No preview image (Trellis 2, some post-processing results): R6 on the texture map still works; R7 cannot be done: say so in the delivery ("no preview was returned; silhouette not checked").

What you may say: "file structure, preview render and texture map checked". What you may not say: "looks great from all sides", "watertight", "game-ready", "print-ready".

## 2. Wrong results → cause → change

Each row is one repair attempt (max 3 per asset, something must change each time; every attempt is a new paid generation: add it to the running total and respect the cost gate).

| Symptom | Likely cause | Change (first option first) |
|---|---|---|
| Flat relief, a card with a picture on it (`thin_bounds`) | frontal flat-lit photo of a shallow object, or the model saw the background as part of the object | remove the background; use a three-quarter view; add a side view through a multi-view endpoint |
| Floor plate, slab or halo behind the object | shadow or background reconstructed; transparent cut-out misread | cut-out flattened onto white ([input-prep.md](input-prep.md) section 4); crop the shadow; re-shoot with softer light |
| Back is melted, mirrored or plain | the back was never shown | real photos of the back; else generated orbit views, with the honesty line; Meshy `symmetry_mode: "on"` for truly symmetric objects |
| Side details mirrored left to right | left and right views swapped for this model's convention | swap the two side views once |
| Stretched or squashed (R4) | perspective distortion in the photo; wrong view in a named slot | re-shoot from further away; check each view's slot; Tripo `orientation: "align_image"` |
| Parts fused (arms to the torso, handle to the body, legs together) | the picture shows them touching | a new picture with separated parts (A-pose); Meshy `pose_mode` |
| Holes or missing thin parts | wires, straps, glass, spokes: a known weak spot | say so; try a higher detail tier once (Tripo `geometry_quality: "detailed"`, Meshy `geometry_resolution: "2k"`, Rodin higher `tier`); else accept or model by hand |
| Extra blobs, a second object | clutter or a hand in the input | fix the input; never re-run the same picture |
| No texture although asked (`no_textures`) | texture switched off in the input (`texture: false`, `should_texture: false`, `generate_type: "Geometry"`, `material: "None"`, `mode: "preview"`), or lost in a remesh | read your own input JSON first; after a remesh: retexture from the original photo |
| `vertex_colors_only` | the generator stored colour per vertex | most viewers and AR need textures: regenerate on the routed endpoint, or retexture |
| Blurry or low-resolution texture | default texture tier | Tripo `texture_quality: "detailed"` (+$0.10); `fal-ai/trellis-2` with `texture_size: 4096`; Rodin `addons: {"high_pack": true}` (+$0.80, confirm); printed label text will stay unreadable on any tier |
| Shadows and highlights painted into the texture | lighting baked from the photo | flatter input light; Rodin `texture_delight: true`; Hi3D `shading` towards 1; retexture from an evenly lit picture (`post-processing.md` section 5) |
| Wrong colours (R6) | colour cast in the photo, or a guessed back | retexture with `fal-ai/trellis-2/retexture`, `image_url` = the clean product photo; give colours in words in `texture_prompt` (Meshy, at generation) |
| Too heavy (`over_budget`, `heavy_for_web`, `large_file`) | endpoint default (Hunyuan 500,000 faces) | face target at generation (`face_count`, `face_limit`, `target_polycount`, `decimation_target`), or one remesh call |
| Too coarse, faceted where it should be smooth | budget too low for the shape | raise the target; quads (`topology: "quad"`) for smooth subdividable surfaces |
| `large_texture` for AR | 4096 px maps | lower `texture_size` (Trellis), avoid HighPack, or retexture with `fal-ai/trellis-2/retexture` at `texture_size: 2048`; else tell the user to downscale in their tool |
| Open edges for printing (R9) | AI meshes are not guaranteed closed | report the number; slicer repair first (free); a remesh as a paid try; never promise |
| `multiple_parts` for printing | separate shells | tell the user; most slicers merge or treat them as bodies; a remesh may fuse them |
| `scale_large`, `scale_tiny` | file in centimetres or millimetres, or a normalised unit cube | report the numbers; no active endpoint rescales (2026-10-05), so the user scales in the AR view, the target app or Blender |
| `mesh_reuse`, `draco`, `required_extensions` (info) | file structure notes | mention only when the target tool is known to choke on them |

Third attempt: change the **model family**, not the wording (Hunyuan → Tripo or Meshy → Rodin), with the best input you now have. After three, stop, show what you have with its warnings, and say what a human modeller would need to fix.

## 3. Rigging and animation problems

| Symptom | Change |
|---|---|
| Rigging job fails (`kind: "validation"`, empty `fields`) | check in order: the GLB URL is public and fresh (upload again) → the mesh is one humanoid with clear limbs (Read the preview) → the mesh is heavy: remesh to a game budget, then rig → regenerate the character in A-pose |
| `422` naming `animation_action_id` or `enable_animation` | the ID is outside 0 to 696 (it is validated only when `enable_animation` is true); on generation endpoints also check that `enable_animation` came with `enable_rigging: true`, which the schema requires |
| Rig present but limbs deform together | fused limbs in the source picture: new picture, `pose_mode: "a-pose"` |
| `no_skin` on the delivered file | you inspected `model_glb`; the skeleton is in `rigged_character_glb` |
| `no_animations` on the rigged file | clips are separate files: `basic_animations.*`, `animation_glb`, `animations[].animation_glb` |
| Character floats or sinks in the engine | `height_meters` or `rigging_height_meters` did not match the intended size; the pivot is the engine's job for skinned meshes |
| A creature, animal or vehicle | not supported by the humanoid auto-rig: deliver static, say so |

## 4. Jobs and files that misbehave

| Signal | Do |
|---|---|
| `status: "pending"` after 540 s | Normal for Meshy with rigging, Hi3D and busy hours. `gm.py wait <endpoint_id> <request_id>` with a 600000 ms Bash timeout, again if needed. After about 30 minutes of `IN_PROGRESS`, tell the user, offer `gm.py cancel` (a cancel may still be billed) and the dashboard link https://fal.ai/dashboard/requests. Never a second `run`. |
| The tool call was killed | `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" ledger --tail 5` has the `request_id`; `wait` on it. |
| `kind: "validation"`, empty `fields`, with a `hint` | The queue hides the reason. Order: field names and ranges against `genmedia schema <endpoint_id> --format openapi --json` → input files (size, format, expired URL) → the picture (no single clear object, a real person, a flagged term). The helper cannot recover the field name from a queued job: diff your input JSON against the schema by hand, key by key, before changing the picture. Each retry is a new paid job and counts towards the three attempts. |
| Download is not a mesh (`kind: "parse"`, `format: "unknown"`, a file of a few hundred bytes) | The CDN returned an error page or the download was cut; the job itself succeeded. An `outputs[]` entry with `path: null` and an `error` → fetch that `url` yourself (`curl -L -o genmedia-output/<slug>/<name>.glb "<url>"`). A broken file on disk → move it away, then `gm.py wait <endpoint_id> <request_id>`: the helper downloads again when a recorded file is missing. Inspect the new file. Still broken → report it; never pay for a regeneration to replace a download. |
| Expected format missing from `outputs[]` | `model_urls` slots are nullable. Take the GLB and convert ([post-processing.md](post-processing.md) section 6), or use an endpoint that writes the format directly. |
| Tripo returned FBX instead of GLB | `quad: true`. The inspector reads FBX as a header only. Need verification → rerun without quads, or take `model_urls.glb` when present. |
| Hunyuan Rapid returned OBJ | its `model_glb` slot "contains GLB if available, otherwise OBJ". The inspector reads OBJ counts and bounds; textures live in the `.mtl` and image files beside it: keep `material_mtl` and `texture` together with the OBJ. |
| `.gltf` with missing `.bin` or images (`missing_resource`) | a glTF is a set of files: deliver the whole folder or prefer the GLB. |
| `content_policy` on a harmless product | say which field was flagged (usually the prompt or the image); weapons, real people and branded characters are the usual causes; one retry on another family is allowed for clearly benign content, with the user told. |
| The estimate was wrong | Add-ons are easy to miss: Tripo `pbr` and Meshy `should_texture` default to true; any extra Hunyuan view or custom `face_count` is +$0.15. Say what happened, correct the running total, never hide it. |

## 5. Viewing help for the user

| Platform | How (all free, nothing to install unless noted) |
|---|---|
| macOS | Finder: select the `.usdz`, press space (Quick Look). GLB: drag into a browser glTF viewer, or Blender. |
| iPhone, iPad | open the `.usdz` from Files, Mail or AirDrop: AR Quick Look places it in the room. |
| Windows | Microsoft's 3D Viewer app opens GLB, FBX, OBJ and STL when it is installed (recent Windows versions no longer ship it); otherwise a browser viewer or Blender. |
| Any browser | an online glTF viewer such as https://gltf-viewer.donmccurdy.com or https://sandbox.babylonjs.com: drag the `.glb` in. The file stays local in these viewers, but tell the user to check that for unreleased products. |
| Blender (install needed) | File, Import, then glTF 2.0, FBX, Wavefront OBJ or STL. |
| Slicers (printing) | open the `.stl`, set the size in millimetres, run the repair, preview layers before printing. |

`python3 "${CLAUDE_SKILL_DIR}/scripts/glbinfo.py" tools` lists what is installed on this machine (Blender, Apple's USD tools, `gltf-transform`, `assimp`, `f3d`). All optional: the deliverable is the file as returned, inspected.
