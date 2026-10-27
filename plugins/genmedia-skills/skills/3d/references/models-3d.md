# 3D generation endpoints (verified 2026-09-20)

Dated cache for this skill. Every ID below was `active` on **2026-09-20** (`genmedia models --category image-to-3d|text-to-3d --no-classify --limit 100 --json`: 41 image-to-3d, 12 text-to-3d endpoints). Fields, enums and limits come from each endpoint's live OpenAPI schema on that day; prices from the pricing API plus the Pricing paragraph of `https://fal.ai/models/<id>/llms.txt`. Re-verify before the first paid call (SKILL.md, Discovery guardrail). Post-processing endpoints (category `3d-to-3d`) are in [post-processing.md](post-processing.md).

`*` = required. "File" = an object with `url`, `file_name`, `content_type`, `file_size`; the helper downloads every File in the result and reports it in `outputs[]` with its `json_path`. Pick outputs by `json_path`, never by index. A `model_urls.<format>` slot is nullable: a format exists only when its `json_path` shows up in `outputs[]`.

## 1. Selection at a glance

| Need | Endpoint | Input image field | Views | Face control | Formats in the result | Preview | Base price |
|---|---|---|---|---|---|---|---|
| Default mesh | `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d` | `input_image_url` | 1 + up to 7 named views | `face_count` 40,000 to 1,500,000 | glb; slots for obj, mtl, fbx, usdz, texture | `thumbnail` | $0.375 |
| Draft of the default | `fal-ai/hunyuan-3d/v3.1/rapid/image-to-3d` | `input_image_url` | 1 | none | glb or obj; slots as above | `thumbnail` | $0.225 |
| Polygon budget, cheap | `tripo3d/h3.1/image-to-3d` | `image_url` | 1 | `face_limit` 1,000 to 2,000,000 | glb (fbx when quads); slots glb, fbx, base_model, pbr_model | `rendered_image` | $0.30 textured |
| 2 to 4 ordered views | `tripo3d/h3.1/multiview-to-3d` | `image_urls` | 2 to 4 | same | same | `rendered_image` | $0.30 textured |
| Tiny budgets | `tripo3d/p1/image-to-3d` | `image_url` | 1 | `face_limit` 48 to 20,000 | as Tripo | `rendered_image` | $0.50 textured |
| Rig and animate in one call | `meshy/v7.1/image-to-3d` | `image_url` | 1 | `target_polycount` 100 to 300,000 | glb; slots glb, fbx, obj, usdz, stl, blend | `thumbnail` | $1.20 textured |
| Rig, from several views | `meshy/v7.1/multi-image-to-3d` | `image_urls` | 1 to 4 | same | same | `thumbnail` | $1.20 |
| Direct STL, USDZ, FBX, OBJ | `fal-ai/hyper3d/rodin/v2.5` | `image_urls` | 1 to 5 | `quality_mesh_option` | one format per call: glb, usdz, fbx, obj, stl | optional `preview_render` | $0.40 |
| Texture resolution control | `fal-ai/trellis-2` | `image_url` | 1 | `decimation_target` 5,000 to 2,000,000 vertices | glb only | none | $0.30 at 1024 |
| Highest geometry detail | `hitem3d/hi3d/v3.0/image-to-3d` | `image_url` | 1 (multi-view sibling: 4 named views) | `face_count` 100,000 to 5,000,000 | one format per call: glb, obj, stl, fbx, usdz | `thumbnail` | $2.10 |

Multi-view capable (verified): Hunyuan v3.1 Pro (named fields), Tripo H3.1 multiview (ordered list), Meshy 7.1 multi-image (unordered list of 1 to 4), Rodin v2.5 (list of 1 to 5), Hi3D v3.0 multi-view (named fields). View-to-field mapping: [input-prep.md](input-prep.md).

## 2. Hunyuan3D v3.1 Pro — `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d`

For: the default single-image mesh; product visualisation and AR; the multi-view route with named slots.

| Field | Type, default | Notes |
|---|---|---|
| `input_image_url`* | string | Front view. 128 to 5000 px, at most 8 MB, JPG, PNG or WEBP. The schema's own tip: simple background, single object, object over 50% of the frame. |
| `back_image_url`, `left_image_url`, `right_image_url` | string, optional | Extra views, JPG or PNG recommended. |
| `top_image_url`, `bottom_image_url`, `left_front_image_url`, `right_front_image_url` | string, optional | v3.1-only views; the two `_front` ones are 45 degree views. |
| `generate_type` | `Normal` (default) or `Geometry` | `Geometry` = untextured white model; `enable_pbr` is then ignored. No LowPoly or Sketch in v3.1. |
| `enable_pbr` | boolean, false | Adds metallic, roughness and normal maps. +$0.15. |
| `face_count` | integer, 500000, range 40000 to 1500000 | Any custom value is billed +$0.15. |

Output: `model_glb` (File, the mesh), `thumbnail` (File, preview PNG), `model_urls.glb|obj|mtl|fbx|usdz|texture` (each nullable), `seed`. Measured 2026-09-21 (`platform.md` section 10): `glb` (the same file as `model_glb`), `obj`, `mtl` and `texture` filled, `fbx` and `usdz` null; 500k triangles and one 4096 px base-colour texture at the defaults.
Price (2026-09-20): $0.375 per generation; +$0.15 PBR; +$0.15 when any extra view is sent; +$0.15 custom face count. The pricing API shows `0.015 units`, which is not the per-call price.

Text sibling `fal-ai/hunyuan-3d/v3.1/pro/text-to-3d`: `prompt`* (at most 1024 characters), `generate_type`, `enable_pbr`, `face_count`; same output and prices.

Rapid tier `fal-ai/hunyuan-3d/v3.1/rapid/image-to-3d`: `input_image_url`*, `enable_pbr` (false), `enable_geometry` (false; geometry-only, no OBJ). Output: `model_glb` (nullable; "GLB if available, otherwise OBJ"), `model_urls.*`, `texture`, `material_mtl`, `thumbnail`. $0.225, +$0.15 PBR. Its text sibling `fal-ai/hunyuan-3d/v3.1/rapid/text-to-3d` takes a `prompt` of at most 200 characters and returns `model_obj` instead of `model_glb`.

## 3. Tripo H3.1 — `tripo3d/h3.1/image-to-3d`, `tripo3d/h3.1/multiview-to-3d`, `tripo3d/h3.1/text-to-3d`

For: polygon budgets (game props, web, mobile), the cheapest current-generation mesh, real-world auto scale, quads.

| Field | Type, default | Notes |
|---|---|---|
| `image_url`* (image) / `image_urls`* (multiview) / `prompt`* (text) | string / list of 2 to 4 / string up to 1024 | Multiview order is fixed: front, left, back, right; the front view is required. Text also takes `negative_prompt` and `image_seed`. |
| `face_limit` | integer 1000 to 2000000, unset = adaptive | The triangle budget. No surcharge in the pricing text. |
| `texture` | boolean, true | false = geometry only ($0.20 tier; text-to-3D $0.10). |
| `pbr` | boolean, **true** | true forces `texture` on. Set false on purpose when PBR maps are unwanted. |
| `texture_quality` | `standard` (default) or `detailed` | `detailed` = HD texture tier ($0.40; text $0.30). |
| `geometry_quality` | `standard` (default) or `detailed` | `detailed` +$0.20. |
| `quad` | boolean, false | +$0.05. "When Tripo emits FBX bytes for quad output, the returned model file is FBX." |
| `auto_size` | boolean, false | Scales the model to real-world dimensions in metres, as estimated by the model: an estimate, not a measurement. |
| `orientation` | `default` or `align_image` | `align_image` rotates the model to match the input picture. |
| `texture_alignment` | `original_image` (default) or `geometry` | Image endpoints only. |
| `model_seed`, `texture_seed` | integer | Reproducibility. |

Output: `model_mesh` (File; GLB, or FBX for quads), `rendered_image` (File, preview), `model_urls.glb|fbx|base_model|pbr_model` (nullable). Measured 2026-09-21: `glb` and `pbr_model` filled, both the same file as `model_mesh`; `fbx` and `base_model` null. Without `face_limit` a character came back at 1.5 million triangles: set it for any budget.
Price (2026-09-20), image and multiview: $0.20 untextured, $0.30 standard texture, $0.40 HD texture; +$0.20 detailed geometry; +$0.05 quads. Text: $0.10, $0.20, $0.30 with the same add-ons. The pricing API shows `0.01 credits`.

`tripo3d/p1/image-to-3d` and `tripo3d/p1/text-to-3d`: only `image_url`* or `prompt`*, `face_limit` 48 to 20000, `texture` (true), `model_seed`; same output keys. Image: $0.40 untextured, $0.50 textured. The text endpoint publishes only `$0.01 per credits` with no credit count: treat its cost as unknown and ask first.

## 4. Meshy 7.1 — `meshy/v7.1/image-to-3d`, `meshy/v7.1/multi-image-to-3d`, `meshy/v7.1/text-to-3d`

Successor of Meshy v7 (fal release 2026-09-19; verified 2026-09-22): the same fields, defaults and output keys, with `4k` added to `geometry_resolution` on image and text. The `meshy/v7/*` IDs still run; use them only when the user names them.

For: humanoid characters that need a rig and animation clips in the same call; quad topology; a low-poly style; all six export formats in one result.

| Field | Type, default | Notes |
|---|---|---|
| `image_url`* / `image_urls`* / `prompt`* | string / list of 1 to 4 (extra images are ignored) / string up to 600 | jpg, jpeg, png; AVIF and HEIF are converted by the endpoint. Multi-image: the same object from different angles. |
| `should_texture` | boolean, true | false = $0.80 tier (image and text). Text uses `mode`: `full` (default, textured) or `preview` (untextured geometry). |
| `enable_pbr` | boolean, false | Metallic, roughness and normal maps besides base colour. |
| `texture_prompt` (at most 600 characters), `texture_image_url` | optional | Guide the texturing. |
| `should_remesh` | boolean, true | false returns the raw triangle mesh and ignores `topology` and `target_polycount`. |
| `target_polycount` | integer, 30000, range 100 to 300000 | With `model_type: "smart-topology"` the default is 4,000 and the maximum 15,000. |
| `topology` | `triangle` (default) or `quad` | |
| `model_type` (image and text only) | `standard` (default), `lowpoly`, `smart-topology` | `lowpoly` is a style: it ignores `topology`, `target_polycount`, `should_remesh`. `smart-topology` returns clean, natively separated parts. |
| `symmetry_mode` | `auto` (default), `on`, `off` | Force `on` for symmetric products and characters, `off` for asymmetric ones. |
| `pose_mode` | `""` (default), `a-pose`, `t-pose` | Normalises a character's pose before rigging. `is_a_t_pose` is deprecated. |
| `geometry_resolution` | `standard`, `2k` or `4k` (image and text); `standard` or `2k` (multi-image) | The 2026-09-22 pricing text names no surcharge for `2k` or `4k` (Meshy v7 billed `2k` at $1.40): treat the cost of a higher resolution as unknown and ask first. `ultra_mode` is deprecated. |
| `enable_rigging` | boolean, false | Humanoid auto-rig, "best results with humanoid characters that have clearly defined limbs"; adds walking and running clips. +$0.20. |
| `rigging_height_meters` | number, 1.7 | Character height, used only with rigging. Take it from the user or keep the default and say so. |
| `enable_animation`, `animation_action_id` | false; 92 | Needs `enable_rigging`. ID 0 to 696 (0 = Idle) from Meshy's animation library (https://docs.meshy.ai/en/api/animation-library); the ID is read only when `enable_animation` is true, and then a value outside the range is a 422. Never guess what an ID means: look it up. +$0.12. |
| `seed`, `enable_prompt_expansion` (text only), `enable_safety_checker` (true) | | Leave the safety checker on. |

Output: `model_glb` (File), `thumbnail`, `model_urls.glb|fbx|obj|usdz|stl|blend` (nullable), `texture_urls[]` with `base_color` and optional `metallic`, `roughness`, `normal`; with rigging `rigged_character_glb`, `rigged_character_fbx`, `basic_animations.walking_glb|running_glb|walking_fbx|running_fbx|walking_armature_glb|running_armature_glb`, `rig_task_id`; with animation `animation_glb`, `animation_fbx`. Text adds `prompt`, `actual_prompt`.
Price (2026-09-22, `llms.txt`): $0.80 untextured, $1.20 textured on all three; +$0.20 rigging; +$0.12 animation; no `geometry_resolution` tier is published. The pricing API shows `0.8 generations` for all three and the helper does not flag it: the default textured call is $1.20.

## 5. Rodin v2.5 — `fal-ai/hyper3d/rodin/v2.5`, `fal-ai/hyper3d/rodin/v2.5/text-to-3d`

For: a specific file format straight from generation (STL for printing, USDZ, FBX, OBJ), quad presets, 1 to 5 input images.

| Field | Type, default | Notes |
|---|---|---|
| `image_urls` (image endpoint) / `prompt`* (text endpoint) | list of 1 to 5 / string up to 1024 | The image endpoint also takes an optional `prompt`; empty = auto-described from the images. |
| `geometry_file_format` | `glb` (default), `usdz`, `fbx`, `obj`, `stl` | One format per call. |
| `material` | `All` (default), `PBR`, `Shaded`, `None` | `None` = geometry only, the right choice for printing. |
| `quality_mesh_option` | `Auto` (default); `4K Quad`, `8K Quad`, `18K Quad`, `50K Quad`, `100K Quad`, `200K Quad`; `2K Triangle`, `20K Triangle`, `50K Triangle`, `150K Triangle`, `500K Triangle`, `1M Triangle`, `2M Triangle` | Valid counts depend on `tier` (schema text): up to 1M Triangle on Extreme-Low, Low and Medium; 20K to 2M Triangle on High and Extreme-High, so `2K Triangle` is not for the default tier. `Auto` picks 50K Triangle on the low tiers, 500K on Medium and High, 1M on Extreme-High. |
| `tier` | `Gen-2.5-High` (default); `Gen-2.5-Minimum`, `-Extreme-Low`, `-Low`, `-Medium`, `-Extreme-High` | `Gen-2.5-Minimum` forces 50K Triangle. |
| `TAPose` | boolean, false | T or A pose for characters. |
| `use_original_alpha` | boolean, false | Keeps the transparency of the input images (image endpoint). |
| `preview_render` | boolean, false | Asks for a preview render; the output schema does not name its slot: look for an image among `outputs[]`. |
| `texture_mode`, `hd_texture`, `texture_delight`, `is_micro`, `enable_creative_mode`, `bbox_condition` {`width`, `height`, `length`: 1 to 2048}, `seed` 0 to 65535 | optional | `texture_delight` removes baked lighting. |
| `addons` | `{"high_pack": true}` | 4K textures; in Quad mode about 16x the faces. +$0.80. |

Output: `model_mesh` (File, in the requested format), `model_meshes[]` (additional files), `textures[]` (images with `width`, `height`), `seed`. No `model_urls`.
Price (2026-09-20): $0.40 per generation, +$0.80 with HighPack (pricing API: `0.4 generations`). Faster siblings exist (`fal-ai/hyper3d/rodin/v2.5/fast`, `fal-ai/hyper3d/rodin/v2.5/text-to-3d/fast`): verify their schema before use.

## 6. Trellis 2 — `fal-ai/trellis-2`

For: texture resolution and vertex budget control from an open model. GLB only, no preview image, no multi-view.

`image_url`*; `resolution` 512, 1024 (default), 1536; `texture_size` 1024, 2048 (default), 4096; `decimation_target` 500000 (5000 to 2000000 **vertices**; the schema suggests 20k to 50k for web and mobile); `remesh` (true); `seed`; many sampler fields (`ss_*`, `shape_slat_*`, `tex_slat_*`, `uv_unwrap_*`, `remesh_band`, `remesh_project`) that stay at their defaults unless a troubleshooting step names one. Output: `model_glb` only. Price: $0.25 at 512, $0.30 at 1024, $0.35 at 1536. Retexture sibling: [post-processing.md](post-processing.md).

## 7. Hi3D v3.0 — `hitem3d/hi3d/v3.0/image-to-3d`, `hitem3d/hi3d/v3.0/multi-view-to-3d`

For: the premium tier when the user asks for maximum geometric detail and accepts the price. Always a confirm-gate call.

`image_url`* (PNG, JPEG or WebP, at most 20 MB) or, on the multi-view endpoint, `front_image_url`, `back_image_url`, `left_image_url`, `right_image_url` (all optional in the schema; send at least the front); `resolution` `2048quality` (default) or `2048master`; `face_count` 100000 to 5000000 (the schema recommends 2,000,000 for quality and 5,000,000 for master); `enable_texture` (true); `enable_pbr` (true); `shading` 0 to 1 (de-shading strength, 0.5); `export_format` `glb` (default), `obj`, `stl`, `fbx`, `usdz`; `enable_safety_checker`. Output: `model_mesh` (File), `thumbnail`. Price: $0.02 per credit; the pricing text quotes $2.10 (`2048quality`) or $9.10 (`2048master`) for a textured PBR model.

## 8. Not routed by default

| Endpoint | Why not |
|---|---|
| `fal-ai/triposr` | removed from the catalog (404 on 2026-10-05), yet still the baked-in 3D default of CLI smart routing: never use smart routing <!-- lint:ignore --> |
| `fal-ai/meshy/v5/multi-image-to-3d` | unlisted on 2026-10-05; `meshy/v7.1/multi-image-to-3d` is current <!-- lint:ignore --> |
| `fal-ai/trellis`, `fal-ai/hunyuan3d/v2*`, `fal-ai/hunyuan3d-v3/*`, `fal-ai/meshy/v6*`, `tripo3d/tripo/v2.5/*`, `fal-ai/hyper3d/rodin`, `fal-ai/hyper3d/rodin/v2`, `hitem3d/hi3d/image-to-3d` | older generations of the families above; use only when the user names them, after the live check |
| `tripo3d/triposplat`, `fal-ai/hunyuan_world/image-to-world`, `fal-ai/sam-3/3d-objects`, `fal-ai/sam-3/3d-body` | splats, worlds and scene reconstruction, not a single deliverable mesh; read the schema first if the user asks |
| `fal-ai/hunyuan-motion`, `fal-ai/hunyuan-motion/fast` | text-to-motion, listed under text-to-3d; not a mesh generator |
| `fal-ai/hunyuan3d-v3/sketch-to-3d`, `fal-ai/pixal3d`, `fal-ai/reconviagen-0.5`, `fal-ai/trellis-2-lora` | niche inputs; verify schema and price live before offering |

## 9. Turning `gm.py price` into dollars

1. `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" price <id1>,<id2> --explain` prices the whole plan in one call.
2. Rows with `needs_llms_txt: true` carry `pricing_text`: pick the tier that matches your input (texture on or off, texture quality, resolution) and add every add-on your input switches on, including defaults you did not override (Tripo `pbr` defaults to true, Meshy `should_texture` to true).
3. Meshy and Rodin rows come back as plain `generations` without `pricing_text`. Meshy's number is the untextured base: use the tiers in section 4 and say "about". Rodin's $0.40 is the real base; HighPack adds $0.80.
4. Pricing API and text disagree → quote the higher. No unit count published → the cost is unknown: say so and ask.
5. Typical totals (2026-09-20): default asset $0.375; default with PBR $0.525; three generated orbit views + multi-view Hunyuan about $0.12 + $0.525; Tripo game prop $0.30; Meshy rigged and animated character $1.52; Rodin STL $0.40.
