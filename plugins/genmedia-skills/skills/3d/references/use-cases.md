# Use cases: what each intended use needs (2026-09-20)

The intended use decides format, triangle budget, textures and the endpoint options. Numbers marked **heuristic** are rules of thumb built into `scripts/glbinfo.py --use`; they are not requirements of any engine, store, viewer or printer. The target decides: tell the user to check its current rules. Endpoint fields: [models-3d.md](models-3d.md); post-processing calls: [post-processing.md](post-processing.md). Prices are hints dated 2026-09-20.

## 1. Defaults per use

| | A product visualisation (default) | B game prop or engine asset | C AR on a phone | D 3D printing |
|---|---|---|---|---|
| Deliver | GLB, plus OBJ, FBX, USDZ when the endpoint returns them | GLB and FBX | USDZ (iOS) and GLB (Android, web) | STL |
| Triangles (heuristic) | offline render: the endpoint default is fine; web viewer: about 100k to 200k | prop 5k to 30k; hero or character 30k to 100k | about 100k or less | not critical; very heavy files slow slicers down |
| Textures | yes; PBR when the material matters | yes, PBR; 2048 px is a common ceiling (heuristic) | yes; 2048 px or less (heuristic); file about 25 MB or less (heuristic) | none: geometry only |
| Scale | not needed for renders | set in the engine | **matters**: 1 unit = 1 metre; needs the user's real size | set in the slicer, in millimetres |
| Endpoint | `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d` | `tripo3d/h3.1/image-to-3d`; characters `meshy/v7.1/image-to-3d` | `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d` with `face_count`; a missing USDZ is offered as a next step (section 4) | `fal-ai/hyper3d/rodin/v2.5` |
| Est. per asset | $0.375 to $0.525 | $0.30; character $1.20 to $1.52 | $0.525; a USDZ from fal adds $0.40 or $0.75 (section 4) | $0.40 |
| `glbinfo.py inspect` flags | `--use product --expect-textures` | `--use game --expect-textures` plus `--max-triangles <budget>`; characters add `--expect-rig` | `--use ar --expect-textures` on the GLB, then the USDZ | `--use print --deep` on the STL |

Widely known basics used below (stable for years, still **check the current documentation** of the target): glTF units are metres and +Y is up; iOS AR Quick Look opens USDZ; Android Scene Viewer and the `<model-viewer>` web component open GLB; Unity and Unreal import FBX, Godot and Blender import glTF directly; STL carries no unit and slicers assume millimetres.

## 2. A — product visualisation and web viewers

Input JSON (`.genmedia/tmp/<slug>.json`):

```json
{"input_image_url": "<front or cut-out url>", "generate_type": "Normal", "enable_pbr": true}
```

- `enable_pbr: true` (+$0.15) when the product is metal, glass-like, glossy plastic, leather or ceramic: the material reacts to light in a viewer. Matte or fabric products, or a tight budget: leave it false ($0.375).
- Leave `face_count` unset for offline renders (500,000 faces, no surcharge). For a web viewer set it once, for example `150000` (+$0.15): cheaper and safer than remeshing a textured model afterwards.
- A 360 degree viewer shows the back: use orbit views or real photos ([input-prep.md](input-prep.md) section 6); add the view fields (+$0.15 once, however many views).
- Label text on products does not survive: it comes back as a blurry texture. Say so up front; a retexture from the real photo can help the base colour, not the lettering.
- Check: textures present, preview silhouette matches the photo, bounding-box proportions match (a bottle that is 3:1 in the photo should be about 3:1 in `bounds.size`), `heavy_for_web` when it goes on a web page.
- Tell the user: which sides were guessed; the file sizes; that a store or 3D viewer may cap file size and texture size: check its current limits.

## 3. B — game props and engine assets

Prop, static (`tripo3d/h3.1/image-to-3d`, $0.30):

```json
{"image_url": "<url>", "face_limit": 15000, "texture": true, "pbr": true, "texture_quality": "standard", "geometry_quality": "standard", "quad": false}
```

- The budget is the user's. None given → 15,000 for a prop, stated in the delivery as chosen for them. Pass the same number to `glbinfo.py --max-triangles`.
- `quad: true` (+$0.05) only when the user will subdivide or deform the mesh; the file may then be FBX, which the inspector reads only as a header. Keep triangles for a GLB you can verify.
- Low-poly **look** (faceted, stylised) → `meshy/v7.1/image-to-3d` with `model_type: "lowpoly"`; it ignores polygon targets. A low polygon **count** with a normal look → `face_limit` here or `target_polycount` on Meshy. Never both expectations in one call.
- A set of props → one `gm.py batch` plan, one job per prop, the same options for all; the gate applies to the sum (eight props at $0.30 = $2.40 → confirm). Written with the Write tool to `.genmedia/projects/<slug>/props.json`, run with `python3 "${CLAUDE_SKILL_DIR}/scripts/gm.py" batch --plan .genmedia/projects/<slug>/props.json` (600000 ms Bash timeout; `pending` → the same command again):

```json
{"label": "<slug>", "max_parallel": 4, "jobs": [
  {"id": "barrel", "endpoint_id": "tripo3d/h3.1/image-to-3d", "est_cost_usd": 0.3,
   "input": {"image_url": "<barrel url>", "face_limit": 15000, "texture": true, "pbr": true}},
  {"id": "crate", "endpoint_id": "tripo3d/h3.1/image-to-3d", "est_cost_usd": 0.3,
   "input": {"image_url": "<crate url>", "face_limit": 15000, "texture": true, "pbr": true}}
]}
```

  Files land in `genmedia-output/<slug>/<id>_{index}.{ext}`; pick each job's mesh by `json_path` (`model_mesh`), inspect all of them in one call (`glbinfo.py inspect a.glb b.glb --use game --max-triangles 15000 --expect-textures`), and give the gallery link with the delivery.

Humanoid character with rig (`meshy/v7.1/image-to-3d`, $1.40 with rig, $1.52 with one animation):

```json
{"image_url": "<front A-pose url>", "pose_mode": "a-pose", "symmetry_mode": "auto", "should_texture": true, "enable_pbr": true, "topology": "triangle", "target_polycount": 30000, "enable_rigging": true, "rigging_height_meters": 1.7}
```

- Rigging already returns walking and running clips (`basic_animations.*`). Add `"enable_animation": true, "animation_action_id": <id>` only when the user asks for a specific motion; ID 0 is Idle, the library is at https://docs.meshy.ai/en/api/animation-library. Several clips for one character → `fal-ai/meshy/rigging/multi-animation` afterwards ([post-processing.md](post-processing.md)).
- `rigging_height_meters`: the user's figure, else the 1.7 default, named in the delivery.
- Deliver `rigged_character_glb` (inspect it with `--expect-rig`), `rigged_character_fbx` for Unity or Unreal, and the clips. The plain `model_glb` has no skeleton.
- Non-humanoids (animals, vehicles, creatures with extra limbs) are generated as static meshes; say that the auto-rig is humanoid-only and the rig is work for an artist.
- FBX: take `model_urls.fbx` when it is in `outputs[]` (Hunyuan and Tripo left it null on 2026-09-21). The user asked for FBX (or named Unity or Unreal) before generation → Tripo with `quad: true` (+$0.05); its schema says the file is FBX when Tripo emits FBX for quad output, so it may still be a GLB, and an FBX is read only as a header. Asked after delivery → the GLB stays the deliverable; offer, priced, a `tripo3d/tripo/remesh` call at the same `face_limit` (its schema lists an FBX output; cost unpublished, ask first) or an export from the user's Blender (`post-processing.md` section 6). Never promise the FBX before it is in `outputs[]`.
- Check: triangles against the budget, `has_uv`, one material per prop (many materials cost draw calls), texture side, rig joints and clip durations.
- Tell the user: topology from these models is automatic: fine for props and background characters, not a substitute for hand retopology on a hero asset that deforms.

## 4. C — AR on a phone

Generate at the AR budget. Hunyuan 3.1 Pro left `model_urls.usdz` null on 2026-09-21, and since `fal-ai/meshy/v5/remesh` was unlisted (2026-10-05) no measured fal call turns a GLB into a USDZ or sets a real-world height. Run step 1, deliver what came back, and make the USDZ an offer. <!-- lint:ignore -->

1. `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d` ($0.525: base + custom face count; add `enable_pbr` for shiny products, +$0.15):

```json
{"input_image_url": "<url>", "generate_type": "Normal", "face_count": 100000}
```

   Take `model_glb` and, when it is in `outputs[]`, `model_urls.usdz`. Inspect the GLB with `--use ar --expect-textures`, then the USDZ (the inspector lists its layers and textures and warns about compressed entries).
2. `model_urls.usdz` missing → deliver the GLB (Android, web) and offer one of these, priced, as the next step:
   - free: the user's own converter; `glbinfo.py tools` says whether `usdzconvert` or Blender is installed here, and you suggest the command instead of running it;
   - `fal-ai/hyper3d/rodin/v2.5` with `geometry_file_format: "usdz"` from the same picture ($0.40): a second mesh, not a conversion of the first, so the iPhone and Android files can differ;
   - `fal-ai/hunyuan-3d/v3.1/smart-topology` on the step 1 GLB ($0.75): its schema lists a `model_urls.usdz` slot that was never measured, and it rebuilds the mesh.

- Real size: no active endpoint scales a mesh or moves its pivot. Never guess a product's size; tell the user the model can be resized by hand in the AR view, or scaled in Blender before shipping (glTF units are metres).
- After any second call, inspect its files with `--use ar --expect-textures`. `no_textures` fires → deliver the step 1 files and say the second file lost its textures. Do not pay for the same call twice with the same input.
- Tell the user how to test: AirDrop or mail the `.usdz` to an iPhone and tap it (AR Quick Look); on Android and the web a GLB opens in Scene Viewer or a `<model-viewer>` page. Both platforms publish size and texture recommendations: check the current ones before shipping to customers.

## 5. D — 3D printing

Input JSON for `fal-ai/hyper3d/rodin/v2.5` ($0.40):

```json
{"image_urls": ["<front url>", "<back url>"], "geometry_file_format": "stl", "material": "None", "quality_mesh_option": "Auto", "tier": "Gen-2.5-High"}
```

- Geometry only. Colour printing is a different job ([post-processing.md](post-processing.md), `hitem3d/hi3d/multicolor`).
- Views matter more here than anywhere: a guessed back is a printed back. Prefer real photos of every side.
- Inspect: `glbinfo.py inspect <file>.stl --use print --deep`. Report `open_edges`, `non_manifold_edges` and the part count honestly:
  - 0 open and 0 non-manifold edges → "no open edges found"; still not a guarantee (self-intersections, inverted normals and wall thickness are not checked).
  - open edges > 0 → the mesh is not closed. Say so; most slicers and mesh tools offer an automatic repair; a remesh ([post-processing.md](post-processing.md)) often closes small gaps but is a paid try, not a promise.
- What the file cannot tell and the user must decide in the slicer: size in millimetres, minimum wall and detail thickness for their printer and material, overhangs and supports, orientation, hollowing and drain holes for resin.
- Thin parts from the weak-spot list (wires, hair, fingers) often print badly or break: warn before paying.
- Tell the user: never call the file "print-ready"; say "STL exported, n triangles, open edges: n, check and repair in your slicer".

## 6. Mixed and unclear requests

- "For my shop" → A, and mention AR (C) as the next step when the shop supports 3D or AR product views.
- "For Unity / Unreal / Godot / Roblox" → B. Marketplaces and platforms have their own polygon, texture and rig rules: check the current ones; pass the user's number to `--max-triangles`.
- "For Blender" → A with OBJ or GLB; the user will edit it anyway.
- "Figurine", "miniature", "keychain" → D.
- Two uses at once (AR and print) → generate once with textures, deliver the AR chain, then derive the STL with a remesh conversion (`target_formats: ["stl"]`) instead of paying for a second generation; inspect the STL with `--deep`.
