#!/usr/bin/env python3
"""glbinfo.py - header-level inspector for 3D assets. Python 3.8+, stdlib only, no network, no cost.

An agent cannot look at a mesh. This script reads what a file says about itself so the agent can
review a generated asset honestly: counts, bounds, materials, textures, rig, clips and warnings.

  inspect <file>... [--use product|game|ar|print] [--max-triangles N] [--expect-textures]
                    [--expect-rig] [--expect-animations] [--deep] [--deep-limit N]
      .glb / .gltf: meshes, primitives, vertices, triangles, materials, textures (mime, bytes, pixel
      size), bounding box through the node transforms, animations, skins, extensions, container
      checks. .obj / .stl / .ply: counts and bounds. .fbx / .usdz / .blend: container facts only.
      --deep welds vertices by position and counts open and non-manifold edges (GLB, glTF, STL, OBJ).
  textures <file.glb|.gltf|.usdz> --out-dir <dir>
      Writes the embedded images to disk so they can be opened with an image viewer (or the Read tool).
  tools
      Which optional local viewers and converters exist on this machine. Nothing is required.

Prints ONE compact JSON object on stdout. Exit: 0 ok (warnings included) | 1 failed | 2 usage.
Budgets behind --use are labelled heuristics, not rules of any engine, store or printer.
"""
import argparse
import base64
import json
import math
import os
import re
import shutil
import struct
import sys
import zipfile
from urllib.parse import unquote

GLB_MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942
COMPONENT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
TYPE_SIZE = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
MODES = {0: "POINTS", 1: "LINES", 2: "LINE_LOOP", 3: "LINE_STRIP", 4: "TRIANGLES", 5: "TRIANGLE_STRIP",
         6: "TRIANGLE_FAN"}
KNOWN_EXTENSIONS = {
    "KHR_materials_pbrSpecularGlossiness", "KHR_materials_unlit", "KHR_materials_clearcoat",
    "KHR_materials_transmission", "KHR_materials_ior", "KHR_materials_specular", "KHR_materials_sheen",
    "KHR_materials_volume", "KHR_materials_emissive_strength", "KHR_materials_iridescence",
    "KHR_materials_anisotropy", "KHR_texture_transform", "KHR_texture_basisu", "KHR_mesh_quantization",
    "KHR_draco_mesh_compression", "EXT_meshopt_compression", "EXT_texture_webp", "KHR_lights_punctual",
    "KHR_materials_variants", "EXT_mesh_gpu_instancing"}
# Labelled heuristics, not rules. Sources: common engine and viewer guidance; the target decides.
USE_BUDGETS = {
    "product": {"max_triangles": 1000000, "web_triangles": 200000, "max_texture": 4096, "max_mb": None},
    "game": {"max_triangles": 100000, "web_triangles": None, "max_texture": 4096, "max_mb": None},
    "ar": {"max_triangles": 100000, "web_triangles": None, "max_texture": 2048, "max_mb": 25},
    "print": {"max_triangles": None, "web_triangles": None, "max_texture": None, "max_mb": None},
}
DEEP_LIMIT = 1000000
MAX_RESOURCE_BYTES = 1 << 30  # external buffers, images and zip entries above 1 GiB are not loaded
CRASHES = (struct.error, zipfile.BadZipFile, zipfile.LargeZipFile, AttributeError, IndexError, KeyError,
           TypeError, ValueError, OverflowError, OSError, RecursionError, MemoryError, RuntimeError,
           NotImplementedError)  # what a hostile or broken file can raise; always reported as JSON


class InspectError(Exception):
    def __init__(self, kind, message):
        Exception.__init__(self, message)
        self.kind = kind
        self.message = message


def emit(obj, code=0):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.exit(code)


def warn(bucket, level, code, message):
    bucket.append({"level": level, "code": code, "message": message})


def fmt_int(n):
    return "{:,}".format(int(n))


def fmt_size(n):
    if n >= 1048576:
        return "%.1f MB" % (n / 1048576.0)
    if n >= 1024:
        return "%.0f KB" % (n / 1024.0)
    return "%d B" % n


def fmt_num(x):
    if x == 0:
        return "0"
    a = abs(x)
    if a >= 100:
        return "%.0f" % x
    if a >= 1:
        return "%.2f" % x
    return "%.3g" % x


# ---------------------------------------------------------------- images
def image_info(data):
    """(mime, width, height) from the first bytes of PNG, JPEG, WebP, KTX2 or GIF; None when unknown."""
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        w, h = struct.unpack(">II", data[16:24])
        return "image/png", w, h
    if data[:3] == b"\xff\xd8\xff":
        pos, size = 2, len(data)
        while pos + 9 < size:
            if data[pos] != 0xFF:
                pos += 1
                continue
            marker = data[pos + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                pos += 2
                continue
            if marker == 0xFF:
                pos += 1
                continue
            seg = struct.unpack(">H", data[pos + 2:pos + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[pos + 5:pos + 9])
                return "image/jpeg", w, h
            pos += 2 + seg
        return "image/jpeg", None, None
    if len(data) >= 30 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        kind = data[12:16]
        if kind == b"VP8X":
            w = 1 + (data[24] | data[25] << 8 | data[26] << 16)
            h = 1 + (data[27] | data[28] << 8 | data[29] << 16)
            return "image/webp", w, h
        if kind == b"VP8L" and data[20] == 0x2F:
            bits = struct.unpack("<I", data[21:25])[0]
            return "image/webp", (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if kind == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
            w, h = struct.unpack("<HH", data[26:30])
            return "image/webp", w & 0x3FFF, h & 0x3FFF
        return "image/webp", None, None
    if len(data) >= 28 and data[:12] == b"\xabKTX 20\xbb\r\n\x1a\n":
        w, h = struct.unpack("<II", data[20:28])
        return "image/ktx2", w, h
    if data[:6] in (b"GIF87a", b"GIF89a") and len(data) >= 10:
        w, h = struct.unpack("<HH", data[6:10])
        return "image/gif", w, h
    return None


EXT_BY_MIME = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/ktx2": "ktx2",
               "image/gif": "gif"}


# ---------------------------------------------------------------- glTF container
def read_glb(path):
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) < 20:
        raise InspectError("parse", "file is %d bytes: too short for a GLB header" % len(data))
    magic, version, length = struct.unpack("<III", data[:12])
    if magic != GLB_MAGIC:
        raise InspectError("parse", "not a GLB: magic bytes are %r" % data[:4])
    doc, blob, pos, chunks = None, None, 12, []
    while pos + 8 <= len(data):
        clen, ctype = struct.unpack("<II", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + clen]
        chunks.append({"type": "JSON" if ctype == CHUNK_JSON else "BIN" if ctype == CHUNK_BIN else hex(ctype),
                       "bytes": clen, "truncated": len(body) < clen})
        if ctype == CHUNK_JSON and doc is None:
            try:
                doc = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, ValueError) as exc:
                raise InspectError("parse", "GLB JSON chunk is not valid JSON: %s" % exc)
        elif ctype == CHUNK_BIN and blob is None:
            blob = body
        pos += 8 + clen  # chunk lengths already include their 4-byte padding
    if not isinstance(doc, dict):
        raise InspectError("parse", "GLB has no JSON chunk")
    container = {"version": version, "declared_length": length, "length_ok": length == size, "chunks": chunks}
    return doc, blob, container


def read_gltf(path):
    try:
        with open(path, "rb") as fh:
            doc = json.loads(fh.read().decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise InspectError("parse", "not a glTF JSON document: %s" % exc)
    if not isinstance(doc, dict) or "asset" not in doc:
        raise InspectError("parse", "JSON without an `asset` object: not glTF")
    return doc


def contained_path(base_dir, uri):
    """A relative resource URI resolved next to the document; None when it points outside that folder."""
    base = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base, unquote(uri)))
    return target if target.startswith(base + os.sep) else None


class Resources(object):
    """Resolves buffers and images of one document (GLB chunk, data URIs, files next to a .gltf)."""

    def __init__(self, doc, base_dir, glb_blob):
        self.doc, self.base_dir, self.glb_blob = doc, base_dir, glb_blob
        self.cache = {}

    def uri_bytes(self, uri):
        if uri.startswith("data:"):
            head, _, payload = uri.partition(",")
            try:
                return base64.b64decode(payload) if ";base64" in head else unquote(payload).encode("latin-1")
            except (ValueError, UnicodeEncodeError):
                return None
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", uri):
            return None  # remote resources are never fetched: no network
        target = contained_path(self.base_dir, uri)
        if target is None or not os.path.isfile(target) or os.path.getsize(target) > MAX_RESOURCE_BYTES:
            return None
        with open(target, "rb") as fh:
            return fh.read()

    def buffer(self, index):
        if index in self.cache:
            return self.cache[index]
        buffers = self.doc.get("buffers") or []
        data = None
        if 0 <= index < len(buffers):
            uri = buffers[index].get("uri")
            data = self.glb_blob if uri is None and index == 0 else self.uri_bytes(uri) if uri else None
        self.cache[index] = data
        return data

    def view(self, index):
        views = self.doc.get("bufferViews") or []
        if not isinstance(index, int) or not 0 <= index < len(views):
            return None
        view = views[index]
        data = self.buffer(view.get("buffer", 0))
        if data is None:
            return None
        start = view.get("byteOffset", 0)
        return data[start:start + view.get("byteLength", 0)]


def read_accessor(doc, res, index):
    """List of tuples (or None when the data is compressed, sparse-only or missing)."""
    accessors = doc.get("accessors") or []
    if not isinstance(index, int) or not 0 <= index < len(accessors):
        return None
    acc = accessors[index]
    if "bufferView" not in acc or acc.get("sparse"):
        return None
    fmt = COMPONENT.get(acc.get("componentType"))
    width = TYPE_SIZE.get(acc.get("type"))
    if not fmt or not width:
        return None
    views = doc.get("bufferViews") or []
    view = views[acc["bufferView"]] if 0 <= acc["bufferView"] < len(views) else None
    data = res.view(acc["bufferView"])
    if view is None or data is None:
        return None
    code, comp = fmt
    item = comp * width
    stride = view.get("byteStride") or item
    offset, count = acc.get("byteOffset", 0), acc.get("count", 0)
    if count and offset + (count - 1) * stride + item > len(data):
        return None
    if stride == item:
        return list(struct.iter_unpack("<%d%s" % (width, code), data[offset:offset + count * item]))
    unpack = struct.Struct("<%d%s" % (width, code)).unpack_from
    return [unpack(data, offset + i * stride) for i in range(count)]


# ---------------------------------------------------------------- matrices (row-major 4x4)
IDENTITY = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def mat_mul(a, b):
    return [sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4)) for r in range(4) for c in range(4)]


def node_matrix(node):
    m = node.get("matrix")
    if isinstance(m, list) and len(m) == 16:  # glTF stores column-major
        return [float(m[c * 4 + r]) for r in range(4) for c in range(4)]
    tx, ty, tz = (node.get("translation") or [0, 0, 0])[:3]
    qx, qy, qz, qw = (node.get("rotation") or [0, 0, 0, 1])[:4]
    sx, sy, sz = (node.get("scale") or [1, 1, 1])[:3]
    xx, yy, zz, xy, xz, yz = qx * qx, qy * qy, qz * qz, qx * qy, qx * qz, qy * qz
    wx, wy, wz = qw * qx, qw * qy, qw * qz
    return [(1 - 2 * (yy + zz)) * sx, (2 * (xy - wz)) * sy, (2 * (xz + wy)) * sz, tx,
            (2 * (xy + wz)) * sx, (1 - 2 * (xx + zz)) * sy, (2 * (yz - wx)) * sz, ty,
            (2 * (xz - wy)) * sx, (2 * (yz + wx)) * sy, (1 - 2 * (xx + yy)) * sz, tz,
            0.0, 0.0, 0.0, 1.0]


def transform_point(m, p):
    x, y, z = p
    return (m[0] * x + m[1] * y + m[2] * z + m[3], m[4] * x + m[5] * y + m[6] * z + m[7],
            m[8] * x + m[9] * y + m[10] * z + m[11])


def mesh_instances(doc):
    """[(mesh_index, world_matrix)] for the default scene (or every root when no scene exists)."""
    nodes = doc.get("nodes") or []
    scenes = doc.get("scenes") or []
    if scenes:
        scene = doc.get("scene", 0)
        picked = [scenes[scene]] if isinstance(scene, int) and 0 <= scene < len(scenes) else scenes
        roots = [n for s in picked for n in (s.get("nodes") or [])]
    else:
        children = {c for n in nodes for c in (n.get("children") or [])}
        roots = [i for i in range(len(nodes)) if i not in children]
    out, seen = [], set()
    stack = [(r, IDENTITY) for r in roots]  # type: list
    while stack:
        index, parent = stack.pop()
        if not isinstance(index, int) or not 0 <= index < len(nodes) or index in seen:
            continue
        seen.add(index)
        node = nodes[index]
        world = mat_mul(parent, node_matrix(node))
        if isinstance(node.get("mesh"), int):
            out.append((node["mesh"], world))
        stack.extend((c, world) for c in (node.get("children") or []))
    return out


# ---------------------------------------------------------------- topology (deep)
def edge_report(triangles):
    """triangles: iterable of 3 hashable vertex keys. Counts edges by how many triangles use them."""
    edges, degenerate, total = {}, 0, 0
    for a, b, c in triangles:
        total += 1
        if a == b or b == c or a == c:
            degenerate += 1
            continue
        for u, v in ((a, b), (b, c), (c, a)):
            key = (u, v) if u <= v else (v, u)
            edges[key] = edges.get(key, 0) + 1
    open_edges = sum(1 for n in edges.values() if n == 1)
    non_manifold = sum(1 for n in edges.values() if n > 2)
    return {"triangles_checked": total, "edges": len(edges), "open_edges": open_edges,
            "non_manifold_edges": non_manifold, "degenerate_triangles": degenerate,
            "closed": total > 0 and open_edges == 0 and non_manifold == 0}


def merge_reports(reports):
    keys = ("triangles_checked", "edges", "open_edges", "non_manifold_edges", "degenerate_triangles")
    merged = {k: sum(r[k] for r in reports) for k in keys}
    merged["closed"] = bool(reports) and all(r["closed"] for r in reports)
    return merged


def primitive_triangles(mode, order):
    if mode == 4:
        return [(order[i], order[i + 1], order[i + 2]) for i in range(0, len(order) - 2, 3)]
    if mode == 5:
        return [(order[i], order[i + 1], order[i + 2]) if i % 2 == 0 else (order[i + 1], order[i], order[i + 2])
                for i in range(len(order) - 2)]
    if mode == 6:
        return [(order[0], order[i], order[i + 1]) for i in range(1, len(order) - 1)]
    return []


def deep_gltf(doc, res, limit, warnings):
    total = sum(p["triangles"] for m in summarize_meshes(doc)["per_mesh"] for p in m["primitives"])
    if total > limit:
        warn(warnings, "info", "deep_skipped", "deep check skipped: %s triangles exceed --deep-limit %s"
             % (fmt_int(total), fmt_int(limit)))
        return None
    used = set(doc.get("extensionsUsed") or [])
    if used & {"KHR_draco_mesh_compression", "EXT_meshopt_compression"}:
        warn(warnings, "info", "deep_skipped", "deep check unavailable: geometry is compressed (%s)"
             % ", ".join(sorted(used & {"KHR_draco_mesh_compression", "EXT_meshopt_compression"})))
        return None
    reports, unreadable = [], 0
    for mesh in doc.get("meshes") or []:
        weld, triangles = {}, []
        for prim in mesh.get("primitives") or []:
            mode = prim.get("mode", 4)
            if mode not in (4, 5, 6):
                continue
            positions = read_accessor(doc, res, (prim.get("attributes") or {}).get("POSITION"))
            if positions is None:
                unreadable += 1
                continue
            ids = [weld.setdefault(tuple(round(v, 6) for v in p), len(weld)) for p in positions]
            if "indices" in prim:
                raw = read_accessor(doc, res, prim["indices"])
                if raw is None:
                    unreadable += 1
                    continue
                order = [ids[i[0]] for i in raw if i[0] < len(ids)]
            else:
                order = ids
            triangles.extend(primitive_triangles(mode, order))
        if triangles:
            reports.append(edge_report(triangles))
    if unreadable:
        warn(warnings, "info", "deep_partial", "%d primitive(s) could not be read (missing buffer, sparse "
             "accessor); the edge counts cover the rest" % unreadable)
    return merge_reports(reports) if reports else None


def deep_warnings(report, warnings):
    if not report:
        return
    if report["open_edges"]:
        warn(warnings, "warn", "open_edges", "%s open edge(s) after welding vertices by position: the surface "
             "is not closed (not watertight)" % fmt_int(report["open_edges"]))
    if report["non_manifold_edges"]:
        warn(warnings, "warn", "non_manifold_edges", "%s edge(s) shared by more than two triangles "
             "(non-manifold)" % fmt_int(report["non_manifold_edges"]))
    if report["degenerate_triangles"]:
        warn(warnings, "info", "degenerate_triangles", "%s zero-area triangle(s) after welding"
             % fmt_int(report["degenerate_triangles"]))
    if report["closed"]:
        warn(warnings, "info", "closed_surface", "no open or non-manifold edges found; self-intersections, "
             "inverted normals and wall thickness are NOT checked: a slicer still decides")


# ---------------------------------------------------------------- glTF summary
def summarize_meshes(doc):
    accessors = doc.get("accessors") or []

    def count(index):
        return accessors[index].get("count", 0) if isinstance(index, int) and 0 <= index < len(accessors) else 0

    per_mesh, modes, attrs_all = [], {}, set()
    for index, mesh in enumerate(doc.get("meshes") or []):
        prims = []
        for prim in mesh.get("primitives") or []:
            attributes = prim.get("attributes") or {}
            mode = prim.get("mode", 4)
            verts = count(attributes.get("POSITION"))
            n = count(prim["indices"]) if "indices" in prim else verts
            tris = n // 3 if mode == 4 else max(0, n - 2) if mode in (5, 6) else 0
            modes[MODES.get(mode, str(mode))] = modes.get(MODES.get(mode, str(mode)), 0) + 1
            attrs_all.update(attributes.keys())
            prims.append({"mode": MODES.get(mode, str(mode)), "vertices": verts, "triangles": tris,
                          "indexed": "indices" in prim, "material": prim.get("material"),
                          "attributes": sorted(attributes.keys()), "position": attributes.get("POSITION"),
                          "draco": "KHR_draco_mesh_compression" in (prim.get("extensions") or {}),
                          "morph_targets": len(prim.get("targets") or [])})
        per_mesh.append({"index": index, "name": mesh.get("name"), "primitives": prims})
    return {"per_mesh": per_mesh, "modes": modes, "attributes": sorted(attrs_all)}


def texture_roles(doc):
    """image index -> sorted list of roles, through textures[].source (and the webp / basisu extensions)."""
    textures = doc.get("textures") or []
    roles = {}

    def image_of(tex_index):
        if not isinstance(tex_index, int) or not 0 <= tex_index < len(textures):
            return None
        tex = textures[tex_index]
        if isinstance(tex.get("source"), int):
            return tex["source"]
        for ext in (tex.get("extensions") or {}).values():
            if isinstance(ext, dict) and isinstance(ext.get("source"), int):
                return ext["source"]
        return None

    def note(info, role):
        if isinstance(info, dict):
            image = image_of(info.get("index"))
            if image is not None:
                roles.setdefault(image, set()).add(role)

    for mat in doc.get("materials") or []:
        pbr = mat.get("pbrMetallicRoughness") or {}
        note(pbr.get("baseColorTexture"), "base_color")
        note(pbr.get("metallicRoughnessTexture"), "metallic_roughness")
        note(mat.get("normalTexture"), "normal")
        note(mat.get("occlusionTexture"), "occlusion")
        note(mat.get("emissiveTexture"), "emissive")
        spec = (mat.get("extensions") or {}).get("KHR_materials_pbrSpecularGlossiness") or {}
        note(spec.get("diffuseTexture"), "base_color")
    return {k: sorted(v) for k, v in roles.items()}


def summarize_images(doc, res):
    roles, out = texture_roles(doc), []
    for index, image in enumerate(doc.get("images") or []):
        entry = {"index": index, "name": image.get("name"), "mime": image.get("mimeType"),
                 "roles": roles.get(index, []), "bytes": None, "width": None, "height": None}
        data = None
        if isinstance(image.get("bufferView"), int):
            entry["source"] = "embedded"
            data = res.view(image["bufferView"])
        elif isinstance(image.get("uri"), str):
            entry["source"] = "data-uri" if image["uri"].startswith("data:") else "external"
            if entry["source"] == "external":
                entry["uri"] = image["uri"]
            data = res.uri_bytes(image["uri"])
        if data is not None:
            entry["bytes"] = len(data)
            info = image_info(data)
            if info:
                entry["mime"], entry["width"], entry["height"] = info[0], info[1], info[2]
        out.append((entry, data))
    return out


def summarize_materials(doc):
    out = []
    for index, mat in enumerate(doc.get("materials") or []):
        pbr = mat.get("pbrMetallicRoughness") or {}
        out.append({"index": index, "name": mat.get("name"),
                    "base_color_texture": "baseColorTexture" in pbr,
                    "metallic_roughness_texture": "metallicRoughnessTexture" in pbr,
                    "normal_texture": "normalTexture" in mat, "occlusion_texture": "occlusionTexture" in mat,
                    "emissive_texture": "emissiveTexture" in mat,
                    "base_color_factor": pbr.get("baseColorFactor"), "alpha_mode": mat.get("alphaMode", "OPAQUE"),
                    "double_sided": bool(mat.get("doubleSided")),
                    "extensions": sorted((mat.get("extensions") or {}).keys())})
    return out


def summarize_bounds(doc, per_mesh):
    accessors = doc.get("accessors") or []
    lo, hi, skipped = [math.inf] * 3, [-math.inf] * 3, 0
    instances = mesh_instances(doc) or [(m["index"], IDENTITY) for m in per_mesh]
    by_index = {m["index"]: m for m in per_mesh}
    for mesh_index, world in instances:
        for prim in (by_index.get(mesh_index) or {}).get("primitives", []):
            pos = prim.get("position")
            acc = accessors[pos] if isinstance(pos, int) and 0 <= pos < len(accessors) else {}
            mn, mx = acc.get("min"), acc.get("max")
            if not (isinstance(mn, list) and isinstance(mx, list) and len(mn) >= 3 and len(mx) >= 3):
                skipped += 1
                continue
            for corner in [(x, y, z) for x in (mn[0], mx[0]) for y in (mn[1], mx[1]) for z in (mn[2], mx[2])]:
                p = transform_point(world, corner)
                for axis in range(3):
                    lo[axis], hi[axis] = min(lo[axis], p[axis]), max(hi[axis], p[axis])
    if math.isinf(lo[0]):
        return None, skipped, len(instances)
    size = [hi[i] - lo[i] for i in range(3)]
    return ({"min": [round(v, 6) for v in lo], "max": [round(v, 6) for v in hi],
             "size": [round(v, 6) for v in size], "max_dimension": round(max(size), 6),
             "center": [round((lo[i] + hi[i]) / 2.0, 6) for i in range(3)],
             "method": "POSITION accessor min/max through node transforms (skinning and morphs ignored)"},
            skipped, len(instances))


def summarize_animations(doc):
    accessors = doc.get("accessors") or []
    out = []
    for index, anim in enumerate(doc.get("animations") or []):
        duration = 0.0
        for sampler in anim.get("samplers") or []:
            acc = sampler.get("input")
            mx = accessors[acc].get("max") if isinstance(acc, int) and 0 <= acc < len(accessors) else None
            if isinstance(mx, list) and mx and isinstance(mx[0], (int, float)):
                duration = max(duration, float(mx[0]))
        paths = sorted({p for p in ((c.get("target") or {}).get("path") for c in anim.get("channels") or []) if p is not None})
        out.append({"index": index, "name": anim.get("name"), "channels": len(anim.get("channels") or []),
                    "duration_s": round(duration, 3), "paths": paths})
    return out


def inspect_gltf(path, fmt, opts):
    warnings = []
    if fmt == "glb":
        doc, blob, container = read_glb(path)
        if not container["length_ok"]:
            warn(warnings, "warn", "length_mismatch", "GLB header declares %s bytes but the file has %s: "
                 "truncated or padded download" % (fmt_int(container["declared_length"]),
                                                  fmt_int(os.path.getsize(path))))
        if any(c["truncated"] for c in container["chunks"]):
            warn(warnings, "warn", "chunk_truncated", "a GLB chunk ends before its declared length")
    else:
        doc, blob, container = read_gltf(path), None, None
    res = Resources(doc, os.path.dirname(os.path.abspath(path)), blob)
    asset = doc.get("asset") or {}
    meshes = summarize_meshes(doc)
    per_mesh = meshes["per_mesh"]
    prims = [p for m in per_mesh for p in m["primitives"]]
    vertices, triangles = sum(p["vertices"] for p in prims), sum(p["triangles"] for p in prims)
    bounds, bounds_skipped, instances = summarize_bounds(doc, per_mesh)
    by_index = {m["index"]: sum(p["triangles"] for p in m["primitives"]) for m in per_mesh}
    placed = mesh_instances(doc)
    in_scene = sum(by_index.get(i, 0) for i, _ in placed) if placed else triangles
    images = summarize_images(doc, res)
    image_entries = [e for e, _ in images]
    materials = summarize_materials(doc)
    animations = summarize_animations(doc)
    skins = [{"index": i, "name": s.get("name"), "joints": len(s.get("joints") or [])}
             for i, s in enumerate(doc.get("skins") or [])]
    used, required = sorted(doc.get("extensionsUsed") or []), sorted(doc.get("extensionsRequired") or [])
    vertex_colors = any(a.startswith("COLOR_") for a in meshes["attributes"])
    info = {
        "format": fmt, "container": container,
        "asset": {"version": asset.get("version"), "generator": asset.get("generator"),
                  "copyright": asset.get("copyright")},
        "scenes": len(doc.get("scenes") or []), "nodes": len(doc.get("nodes") or []),
        "meshes": len(per_mesh), "mesh_instances": instances, "primitives": len(prims),
        "vertices": vertices, "triangles": triangles, "triangles_in_scene": in_scene,
        "primitive_modes": meshes["modes"], "vertex_attributes": meshes["attributes"],
        "has_uv": "TEXCOORD_0" in meshes["attributes"], "has_normals": "NORMAL" in meshes["attributes"],
        "vertex_colors": vertex_colors,
        "morph_targets": sum(p["morph_targets"] for p in prims),
        "mesh_list": [{"index": m["index"], "name": m["name"], "primitives": len(m["primitives"]),
                       "vertices": sum(p["vertices"] for p in m["primitives"]),
                       "triangles": sum(p["triangles"] for p in m["primitives"])} for m in per_mesh[:50]],
        "materials": materials,
        "textures": {"count": len(doc.get("textures") or []), "images": image_entries,
                     "embedded_bytes": sum(e["bytes"] or 0 for e in image_entries if e.get("source") != "external"),
                     "max_side": max([max(e["width"] or 0, e["height"] or 0) for e in image_entries] or [0])},
        "bounds": bounds,
        "animations": animations, "skins": skins, "joints": sum(s["joints"] for s in skins),
        "cameras": len(doc.get("cameras") or []),
        "extensions_used": used, "extensions_required": required,
    }
    # ---- warnings
    if not per_mesh or triangles == 0:
        warn(warnings, "warn", "no_geometry", "no triangles: %d mesh(es), primitive modes %s"
             % (len(per_mesh), json.dumps(meshes["modes"])))
    if bounds is None:
        warn(warnings, "warn", "no_bounds", "no POSITION min/max to derive a bounding box from")
    else:
        size = bounds["size"]
        largest = max(size)
        if largest <= 0:
            warn(warnings, "warn", "zero_bounds", "bounding box has zero size")
        else:
            if min(size) <= 0:
                warn(warnings, "warn", "zero_bounds", "one dimension of the bounding box is zero: a flat plane")
            elif min(size) < 0.02 * largest:
                warn(warnings, "warn", "thin_bounds", "thinnest dimension is %.1f%% of the largest: likely a "
                     "flat relief or a card, not a full object" % (100.0 * min(size) / largest))
            if largest > 20:
                warn(warnings, "warn", "scale_large", "largest dimension is %s units; glTF units are metres: "
                     "the file is probably in centimetres or millimetres" % fmt_num(largest))
            elif largest < 0.01:
                warn(warnings, "warn", "scale_tiny", "largest dimension is %s units; glTF units are metres"
                     % fmt_num(largest))
            if opts.use in ("ar", "print"):
                warn(warnings, "info", "scale_unverified", "largest dimension is %s units. Generated meshes are "
                     "normalised, not measured: set the real size from the user's own figure" % fmt_num(largest))
    if bounds_skipped:
        warn(warnings, "info", "bounds_partial", "%d primitive(s) have no POSITION min/max" % bounds_skipped)
    if placed and instances != len(per_mesh):
        warn(warnings, "info", "mesh_reuse", "%d mesh definition(s), %d instance(s) in the scene: the scene "
             "draws %s triangles" % (len(per_mesh), instances, fmt_int(in_scene)))
    textured = bool(image_entries)
    if opts.expect_textures and not textured:
        if vertex_colors:
            warn(warnings, "warn", "vertex_colors_only", "no texture images; colour is stored per vertex "
                 "(COLOR_0). Many viewers, AR Quick Look and engines expect textures")
        else:
            warn(warnings, "warn", "no_textures", "textures were expected but the file has no images"
                 + ("" if materials else " and no materials"))
    if textured and not info["has_uv"]:
        warn(warnings, "warn", "no_uv", "images exist but no primitive has TEXCOORD_0: textures cannot map")
    if textured and not any(m["base_color_texture"] for m in materials):
        if not any("KHR_materials_pbrSpecularGlossiness" in m["extensions"] for m in materials):
            warn(warnings, "warn", "unused_textures", "images exist but no material uses a base-colour texture")
    for entry in image_entries:
        if entry["bytes"] is None:
            warn(warnings, "warn", "missing_resource", "image %d could not be loaded (%s)"
                 % (entry["index"], entry.get("uri") or entry.get("source") or "no source"))
    for buf in doc.get("buffers") or []:
        uri = buf.get("uri")
        if isinstance(uri, str) and not uri.startswith("data:"):
            if not os.path.isfile(contained_path(res.base_dir, uri) or ""):
                warn(warnings, "warn", "missing_resource", "external buffer not found next to the file: %s "
                     "(counts come from the JSON; deliver the .gltf together with its files)" % uri)
    budget = dict(USE_BUDGETS.get(opts.use) or {}, use=opts.use, source="heuristic") if opts.use else None  # type: dict | None
    limit = opts.max_triangles if opts.max_triangles is not None else (budget or {}).get("max_triangles")
    if limit is not None and in_scene > limit:
        source = "--max-triangles" if opts.max_triangles is not None else "heuristic for use `%s`" % opts.use
        warn(warnings, "warn", "over_budget", "%s triangles exceed the budget of %s (%s): remesh or regenerate "
             "with a lower face target" % (fmt_int(in_scene), fmt_int(limit), source))
    elif budget and budget.get("web_triangles") and in_scene > budget["web_triangles"] and opts.max_triangles is None:
        warn(warnings, "info", "heavy_for_web", "%s triangles: fine for offline rendering, heavy for a web "
             "viewer (heuristic %s)" % (fmt_int(in_scene), fmt_int(budget["web_triangles"])))
    if budget:
        if opts.max_triangles is not None:
            budget["max_triangles"], budget["source"] = opts.max_triangles, "flag"
        side = info["textures"]["max_side"]
        if budget.get("max_texture") and side > budget["max_texture"]:
            warn(warnings, "warn" if opts.use == "ar" else "info", "large_texture", "largest texture side is "
                 "%d px (heuristic for use `%s`: %d)" % (side, opts.use, budget["max_texture"]))
        size_mb = os.path.getsize(path) / 1048576.0
        if budget.get("max_mb") and size_mb > budget["max_mb"]:
            warn(warnings, "warn", "large_file", "file is %.1f MB (heuristic for use `%s`: %d MB)"
                 % (size_mb, opts.use, budget["max_mb"]))
        if opts.use == "print" and len(per_mesh) + sum(len(m["primitives"]) - 1 for m in per_mesh) > 1:
            warn(warnings, "info", "multiple_parts", "%d primitives: parts may be separate shells that a "
                 "slicer treats as separate bodies" % len(prims))
        if opts.use == "print" and not opts.deep:
            warn(warnings, "info", "print_unverified", "run again with --deep to count open edges; "
                 "watertightness is never proven by this script")
    info["budget"] = budget
    if opts.expect_rig and not skins:
        warn(warnings, "warn", "no_skin", "a rig was expected but the file has no skins or joints")
    if opts.expect_animations and not animations:
        warn(warnings, "warn", "no_animations", "animation clips were expected but the file has none")
    if any(p["draco"] for p in prims) or "KHR_draco_mesh_compression" in used:
        warn(warnings, "info", "draco", "geometry is Draco-compressed: the target viewer or engine needs a decoder")
    unknown = [e for e in required if e not in KNOWN_EXTENSIONS]
    if unknown:
        warn(warnings, "info", "required_extensions", "requires extensions some loaders lack: %s" % ", ".join(unknown))
    if opts.deep:
        info["topology"] = deep_gltf(doc, res, opts.deep_limit, warnings)
        deep_warnings(info["topology"], warnings)
    info["warnings"] = warnings
    return info


# ---------------------------------------------------------------- other formats
def bounds_dict(lo, hi, method):
    if math.isinf(lo[0]):
        return None
    size = [hi[i] - lo[i] for i in range(3)]
    return {"min": [round(v, 6) for v in lo], "max": [round(v, 6) for v in hi], "size": [round(v, 6) for v in size],
            "max_dimension": round(max(size), 6), "center": [round((lo[i] + hi[i]) / 2.0, 6) for i in range(3)],
            "method": method}


def generic_shape_warnings(info, opts, warnings):
    bounds = info.get("bounds")
    if info.get("triangles") == 0:
        warn(warnings, "warn", "no_geometry", "no faces found")
    if bounds:
        size, largest = bounds["size"], max(bounds["size"])
        if largest <= 0 or min(size) <= 0:
            warn(warnings, "warn", "zero_bounds", "bounding box has a zero dimension")
        elif min(size) < 0.02 * largest:
            warn(warnings, "warn", "thin_bounds", "thinnest dimension is %.1f%% of the largest: likely a flat "
                 "relief" % (100.0 * min(size) / largest))
        if opts.use in ("ar", "print") and largest > 0:
            warn(warnings, "info", "scale_unverified", "largest dimension is %s units and the format carries no "
                 "unit: set the real size in the slicer or target app" % fmt_num(largest))
    limit = opts.max_triangles
    if limit is None and opts.use:
        limit = USE_BUDGETS[opts.use]["max_triangles"]
    if limit is not None and (info.get("triangles") or 0) > limit:
        warn(warnings, "warn", "over_budget", "%s triangles exceed the budget of %s"
             % (fmt_int(info["triangles"]), fmt_int(limit)))
    if opts.use == "print" and not opts.deep:
        warn(warnings, "info", "print_unverified", "run again with --deep to count open edges; watertightness "
             "is never proven by this script")


def inspect_stl(path, opts):
    warnings, size = [], os.path.getsize(path)
    with open(path, "rb") as fh:
        head = fh.read(84)
        declared = struct.unpack("<I", head[80:84])[0] if len(head) == 84 else None
        binary = declared is not None and 84 + 50 * declared == size
        lo, hi, keys = [math.inf] * 3, [-math.inf] * 3, []
        want_topology = opts.deep
        if binary and declared is not None:
            triangles = declared
            if opts.deep and triangles > opts.deep_limit:
                warn(warnings, "info", "deep_skipped", "deep check skipped: %s triangles exceed --deep-limit %s"
                     % (fmt_int(triangles), fmt_int(opts.deep_limit)))
                want_topology = False
            weld = {}
            for rec in struct.iter_unpack("<12fH", fh.read(50 * declared)):
                tri = []
                for k in (3, 6, 9):
                    p = rec[k:k + 3]
                    for axis in range(3):
                        lo[axis], hi[axis] = min(lo[axis], p[axis]), max(hi[axis], p[axis])
                    if want_topology:
                        tri.append(weld.setdefault(tuple(round(v, 6) for v in p), len(weld)))
                if want_topology:
                    keys.append(tuple(tri))
            encoding = "binary"
        else:
            fh.seek(0)
            text = fh.read().decode("latin-1")
            if not text.lstrip().lower().startswith("solid"):
                raise InspectError("parse", "not an STL: neither a consistent binary header nor ASCII `solid`")
            verts = re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", text)
            triangles = len(verts) // 3
            weld = {}
            for i, v in enumerate(verts):
                try:
                    p = tuple(float(c) for c in v)
                except ValueError:
                    continue
                for axis in range(3):
                    lo[axis], hi[axis] = min(lo[axis], p[axis]), max(hi[axis], p[axis])
                if want_topology:
                    keys.append(weld.setdefault(tuple(round(c, 6) for c in p), len(weld)))
            if want_topology:
                keys = [tuple(keys[i:i + 3]) for i in range(0, len(keys) - 2, 3)]
            encoding = "ascii"
    info = {"format": "stl", "encoding": encoding, "triangles": triangles, "vertices": triangles * 3,
            "bounds": bounds_dict(lo, hi, "all vertices"), "textures": {"count": 0, "images": []},
            "materials": [], "animations": [], "skins": []}
    generic_shape_warnings(info, opts, warnings)
    if want_topology:
        info["topology"] = edge_report(keys)
        deep_warnings(info["topology"], warnings)
    info["warnings"] = warnings
    return info


def inspect_obj(path, opts):
    warnings = []
    lo, hi = [math.inf] * 3, [-math.inf] * 3
    counts = {"v": 0, "vt": 0, "vn": 0, "f": 0}
    triangles, objects, materials, libs = 0, 0, set(), []
    positions, faces = [], []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if not parts:
                continue
            tag = parts[0]
            if tag == "v" and len(parts) >= 4:
                counts["v"] += 1
                try:
                    p = (float(parts[1]), float(parts[2]), float(parts[3]))
                except ValueError:
                    continue
                for axis in range(3):
                    lo[axis], hi[axis] = min(lo[axis], p[axis]), max(hi[axis], p[axis])
                if opts.deep:
                    positions.append(p)
            elif tag in ("vt", "vn"):
                counts[tag] += 1
            elif tag == "f":
                counts["f"] += 1
                triangles += max(0, len(parts) - 3)
                if opts.deep:
                    faces.append([p.split("/")[0] for p in parts[1:]])
            elif tag in ("o", "g"):
                objects += 1
            elif tag == "usemtl" and len(parts) > 1:
                materials.add(parts[1])
            elif tag == "mtllib" and len(parts) > 1:
                libs.append(" ".join(parts[1:]))
    if counts["v"] == 0:
        raise InspectError("parse", "no `v` lines: not a Wavefront OBJ")
    base = os.path.dirname(os.path.abspath(path))
    info = {"format": "obj", "vertices": counts["v"], "uvs": counts["vt"], "normals": counts["vn"],
            "faces": counts["f"], "triangles": triangles, "objects": objects,
            "materials": [{"name": m} for m in sorted(materials)],
            "material_libraries": [{"file": lib, "found": os.path.isfile(os.path.join(base, lib))} for lib in libs],
            "has_uv": counts["vt"] > 0, "bounds": bounds_dict(lo, hi, "all `v` lines"),
            "textures": {"count": 0, "images": [], "note": "textures live in the .mtl and image files next to it"},
            "animations": [], "skins": []}
    for lib in info["material_libraries"]:
        if not lib["found"]:
            warn(warnings, "warn", "missing_resource", "material library not found next to the file: %s" % lib["file"])
    if opts.expect_textures and not libs:
        warn(warnings, "warn", "no_textures", "textures were expected but the OBJ names no material library")
    generic_shape_warnings(info, opts, warnings)
    if opts.deep:
        if triangles > opts.deep_limit:
            warn(warnings, "info", "deep_skipped", "deep check skipped: %s triangles exceed --deep-limit %s"
                 % (fmt_int(triangles), fmt_int(opts.deep_limit)))
        else:
            weld, ids = {}, []
            for p in positions:
                ids.append(weld.setdefault(tuple(round(v, 6) for v in p), len(weld)))
            tris = []
            for face in faces:
                try:
                    idx = [int(t) for t in face]
                except ValueError:
                    continue
                idx = [ids[i - 1] if i > 0 else ids[i] for i in idx if -len(ids) <= i <= len(ids) and i != 0]
                tris.extend((idx[0], idx[k], idx[k + 1]) for k in range(1, len(idx) - 1))
            info["topology"] = edge_report(tris)
            deep_warnings(info["topology"], warnings)
    info["warnings"] = warnings
    return info


def inspect_ply(path, opts):
    warnings, elements, fmt = [], {}, None
    with open(path, "rb") as fh:
        if fh.readline().strip() != b"ply":
            raise InspectError("parse", "not a PLY file")
        for _ in range(2000):
            line = fh.readline().decode("latin-1").strip()
            if not line or line == "end_header":
                break
            parts = line.split()
            if parts[0] == "format" and len(parts) > 1:
                fmt = parts[1]
            elif parts[0] == "element" and len(parts) == 3 and parts[2].isdigit():
                elements[parts[1]] = int(parts[2])
    info = {"format": "ply", "encoding": fmt, "vertices": elements.get("vertex", 0),
            "faces": elements.get("face", 0), "triangles": None, "bounds": None,
            "textures": {"count": 0, "images": []}, "materials": [], "animations": [], "skins": []}
    if not elements.get("face"):
        warn(warnings, "warn", "no_geometry", "no face element: a point cloud or a Gaussian splat, not a mesh")
    info["warnings"] = warnings
    return info


def inspect_fbx(path, opts):
    with open(path, "rb") as fh:
        head = fh.read(64)
    warnings = []
    if head.startswith(b"Kaydara FBX Binary"):
        version = struct.unpack("<I", head[23:27])[0] if len(head) >= 27 else None
        encoding = "binary"
    elif b"FBX" in head[:40]:
        match = re.search(rb"FBX\s+(\d+)\.(\d+)\.(\d+)", head)
        version = int(match.group(1)) * 1000 + int(match.group(2)) * 100 + int(match.group(3)) if match else None
        encoding = "ascii"
    else:
        raise InspectError("parse", "not an FBX file")
    warn(warnings, "info", "header_only", "FBX is read as a header only: counts, rig and clips are not parsed. "
         "Inspect the GLB twin of this asset, or open the FBX in Blender or the target engine")
    return {"format": "fbx", "encoding": encoding, "fbx_version": version, "warnings": warnings}


def inspect_usdz(path, opts):
    warnings = []
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            layers = [e.filename for e in entries if e.filename.lower().endswith((".usd", ".usda", ".usdc"))]
            images = []
            for e in entries:
                if e.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".ktx2")):
                    with archive.open(e) as fh:
                        meta = image_info(fh.read(65536))
                    images.append({"name": e.filename, "bytes": e.file_size, "mime": meta[0] if meta else None,
                                   "width": meta[1] if meta else None, "height": meta[2] if meta else None})
            compressed = any(e.compress_type != zipfile.ZIP_STORED for e in entries)
    except zipfile.BadZipFile:
        raise InspectError("parse", "not a USDZ package (no zip structure)")
    if not layers:
        warn(warnings, "warn", "no_usd_layer", "the package holds no .usd, .usda or .usdc layer")
    if compressed:
        warn(warnings, "warn", "usdz_compressed", "entries are compressed; the USDZ specification requires "
             "stored (uncompressed) entries and AR Quick Look may refuse the file")
    if opts.expect_textures and not images:
        warn(warnings, "warn", "no_textures", "textures were expected but the package holds no images")
    side = max([max(i["width"] or 0, i["height"] or 0) for i in images] or [0])
    if opts.use == "ar" and side > USE_BUDGETS["ar"]["max_texture"]:
        warn(warnings, "warn", "large_texture", "largest texture side is %d px (heuristic for use `ar`: %d)"
             % (side, USE_BUDGETS["ar"]["max_texture"]))
    size_mb = os.path.getsize(path) / 1048576.0
    if opts.use == "ar" and size_mb > USE_BUDGETS["ar"]["max_mb"]:
        warn(warnings, "warn", "large_file", "file is %.1f MB (heuristic for use `ar`: %d MB)"
             % (size_mb, USE_BUDGETS["ar"]["max_mb"]))
    warn(warnings, "info", "header_only", "USDZ is read as a package listing: geometry counts are not parsed. "
         "Inspect the GLB twin of this asset for counts and bounds")
    return {"format": "usdz", "entries": len(entries), "layers": layers,
            "textures": {"count": len(images), "images": images, "max_side": side}, "warnings": warnings}


def detect_format(path):
    with open(path, "rb") as fh:
        head = fh.read(512)
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if head[:4] == b"glTF":
        return "glb"
    if head[:4] == b"PK\x03\x04":
        return "usdz" if ext in ("usdz", "") else ext or "zip"
    if head.startswith(b"Kaydara FBX Binary") or (ext == "fbx" and b"FBX" in head[:40]):
        return "fbx"
    if head[:7] == b"BLENDER":
        return "blend"
    if head[:3] == b"ply":
        return "ply"
    stripped = head.lstrip()
    if stripped[:1] == b"<":  # an HTML or XML error page saved under a mesh name
        return "unknown"
    if ext in ("gltf", "obj", "stl"):  # text formats (and binary STL) carry no magic bytes
        return ext
    if stripped[:1] == b"{" and b'"asset"' in head:
        return "gltf"
    if stripped[:5].lower() == b"solid":
        return "stl"
    return "unknown"


def stats_line(info):
    parts = ["%s %s" % (info["format"].upper(), fmt_size(info["size_bytes"]))]
    if info["format"] in ("glb", "gltf"):
        parts.append("%d mesh%s / %d primitive%s" % (info["meshes"], "" if info["meshes"] == 1 else "es",
                                                     info["primitives"], "" if info["primitives"] == 1 else "s"))
    if isinstance(info.get("vertices"), int):
        parts.append("%s vertices" % fmt_int(info["vertices"]))
    if isinstance(info.get("triangles"), int):
        parts.append("%s triangles" % fmt_int(info["triangles"]))
    if info["format"] in ("glb", "gltf", "obj"):
        parts.append("%d material%s" % (len(info["materials"]), "" if len(info["materials"]) == 1 else "s"))
    textures = info.get("textures") or {}
    if info["format"] in ("glb", "gltf", "usdz"):
        images = textures.get("images") or []
        if images:
            sizes = sorted({"%sx%s" % (i["width"], i["height"]) for i in images if i.get("width")})
            parts.append("%d texture%s%s" % (len(images), "" if len(images) == 1 else "s",
                                             " (%s)" % ", ".join(sizes[:3]) if sizes else ""))
        else:
            parts.append("no textures")
    if info.get("bounds"):
        parts.append("%s units" % " x ".join(fmt_num(v) for v in info["bounds"]["size"]))
    if info["format"] in ("glb", "gltf"):
        parts.append("rig: %d joints" % info["joints"] if info["skins"] else "no rig")
        clips = info["animations"]
        parts.append("%d clip%s (%s s)" % (len(clips), "" if len(clips) == 1 else "s",
                                           ", ".join(fmt_num(c["duration_s"]) for c in clips[:4]))
                     if clips else "no animation")
    if info.get("topology"):
        parts.append("open edges: %s" % fmt_int(info["topology"]["open_edges"]))
    return " · ".join(parts)


def inspect_file(path, opts):
    base = {"file": path}
    if not os.path.isfile(path):
        return dict(base, ok=False, kind="not_found", message="no such file")
    size = os.path.getsize(path)
    base["size_bytes"] = size
    try:
        fmt = detect_format(path)
        if fmt in ("glb", "gltf"):
            info = inspect_gltf(path, fmt, opts)
        elif fmt == "stl":
            info = inspect_stl(path, opts)
        elif fmt == "obj":
            info = inspect_obj(path, opts)
        elif fmt == "ply":
            info = inspect_ply(path, opts)
        elif fmt == "fbx":
            info = inspect_fbx(path, opts)
        elif fmt == "usdz":
            info = inspect_usdz(path, opts)
        elif fmt == "blend":
            info = {"format": "blend", "warnings": [{"level": "info", "code": "header_only",
                                                     "message": "Blender file: open it in Blender"}]}
        else:
            with open(path, "rb") as fh:
                head = fh.read(200)
            hint = " (looks like an HTML or JSON error page)" if head.lstrip()[:1] in (b"<", b"{") else ""
            return dict(base, ok=False, format="unknown", kind="parse",
                        message="unrecognised 3D format%s; first bytes %r" % (hint, head[:16]))
    except InspectError as exc:
        return dict(base, ok=False, kind=exc.kind, message=exc.message)
    except CRASHES as exc:
        return dict(base, ok=False, kind="parse", message="malformed file: %s: %s" % (type(exc).__name__, exc))
    info = dict(base, ok=True, **info)  # type: dict
    info["stats_line"] = stats_line(info)
    return info


# ---------------------------------------------------------------- commands
def cmd_inspect(opts):
    files = [inspect_file(path, opts) for path in opts.files]
    warns = sum(1 for f in files for w in f.get("warnings", []) if w["level"] == "warn")
    ok = all(f.get("ok") for f in files)
    emit({"ok": ok, "files": files, "warn_count": warns,
          "note": "header-level facts only: nobody has looked at this model"}, 0 if ok else 1)


def cmd_textures(opts):
    path = opts.file
    if not os.path.isfile(path):
        emit({"ok": False, "kind": "not_found", "message": "no such file: %s" % path}, 1)
    stem = os.path.splitext(os.path.basename(path))[0]
    written = []
    try:
        fmt = detect_format(path)
        os.makedirs(opts.out_dir, exist_ok=True)
        if fmt in ("glb", "gltf"):
            doc, blob = (read_glb(path)[:2]) if fmt == "glb" else (read_gltf(path), None)
            res = Resources(doc, os.path.dirname(os.path.abspath(path)), blob)
            for entry, data in summarize_images(doc, res):
                if data is None:
                    continue
                role = "-".join(entry["roles"]) or "unused"
                ext = EXT_BY_MIME.get(entry["mime"], "bin")
                target = os.path.join(opts.out_dir, "%s_img%d_%s.%s" % (stem, entry["index"], role, ext))
                with open(target, "wb") as fh:
                    fh.write(data)
                written.append({"index": entry["index"], "roles": entry["roles"], "path": target,
                                "mime": entry["mime"], "width": entry["width"], "height": entry["height"],
                                "bytes": len(data)})
        elif fmt == "usdz":
            with zipfile.ZipFile(path) as archive:
                for number, e in enumerate(archive.infolist()):
                    if not e.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                        continue
                    if e.file_size > MAX_RESOURCE_BYTES:
                        continue
                    data = archive.read(e)
                    meta = image_info(data)
                    name = re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.basename(e.filename)) or "image_%d" % number
                    target = os.path.join(opts.out_dir, "%s_%s" % (stem, name))
                    with open(target, "wb") as fh:
                        fh.write(data)
                    written.append({"index": number, "roles": [], "path": target, "mime": meta[0] if meta else None,
                                    "width": meta[1] if meta else None, "height": meta[2] if meta else None,
                                    "bytes": len(data)})
        else:
            emit({"ok": False, "kind": "unsupported", "format": fmt,
                  "message": "textures can be extracted from .glb, .gltf and .usdz only"}, 1)
    except InspectError as exc:
        emit({"ok": False, "kind": exc.kind, "message": exc.message}, 1)
    except CRASHES as exc:
        emit({"ok": False, "kind": "parse", "message": "malformed file: %s: %s" % (type(exc).__name__, exc)}, 1)
    emit({"ok": True, "file": path, "count": len(written), "files": written,
          "hint": "open the base_color image to judge colours; a black or blank map is a failed texture"
          if written else "the file embeds no images"})


def cmd_tools(_opts):
    names = ["blender", "qlmanage", "usdzconvert", "usdcat", "usdchecker", "gltf-transform", "gltf_validator",
             "assimp", "f3d", "npx"]
    found = {name: shutil.which(name) for name in names}
    mac_blender = "/Applications/Blender.app/Contents/MacOS/Blender"
    if not found["blender"] and os.path.isfile(mac_blender):
        found["blender"] = mac_blender
    viewers = []
    if found["qlmanage"]:
        viewers.append("macOS Quick Look: select a .usdz (or .obj, .stl) in Finder and press space")
    if found["blender"]:
        viewers.append("Blender: File > Import > glTF 2.0 / FBX / OBJ / STL")
    if found["f3d"]:
        viewers.append("f3d <file>")
    viewers.append("any browser glTF viewer: drag the .glb into it")
    emit({"ok": True, "tools": found, "viewers": viewers,
          "note": "all optional; the deliverable is the file as returned by the model"})


class JsonParser(argparse.ArgumentParser):
    def error(self, message):  # usage errors are JSON too: exit 2, nothing was read
        emit({"ok": False, "kind": "usage", "message": message, "usage": self.format_usage().strip()}, 2)


def build_parser():
    parser = JsonParser(prog="glbinfo.py", description=__doc__,
                        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    ins = sub.add_parser("inspect", help="facts and warnings for one or more 3D files")
    ins.add_argument("files", nargs="+", metavar="file")
    ins.add_argument("--use", choices=sorted(USE_BUDGETS), help="intended use: selects heuristic budgets")
    ins.add_argument("--max-triangles", type=int, metavar="N", help="the user's own triangle budget")
    ins.add_argument("--expect-textures", action="store_true", help="warn when the file has no texture images")
    ins.add_argument("--expect-rig", action="store_true", help="warn when the file has no skin")
    ins.add_argument("--expect-animations", action="store_true", help="warn when the file has no clips")
    ins.add_argument("--deep", action="store_true", help="weld by position, count open and non-manifold edges")
    ins.add_argument("--deep-limit", type=int, default=DEEP_LIMIT, metavar="N",
                     help="skip --deep above this many triangles (default %d)" % DEEP_LIMIT)
    ins.set_defaults(func=cmd_inspect)
    tex = sub.add_parser("textures", help="write the embedded images of a .glb, .gltf or .usdz to a folder")
    tex.add_argument("file")
    tex.add_argument("--out-dir", required=True, metavar="DIR")
    tex.set_defaults(func=cmd_textures)
    tools = sub.add_parser("tools", help="optional local viewers and converters found on this machine")
    tools.set_defaults(func=cmd_tools)
    return parser


def main(argv=None):
    parser = build_parser()
    opts = parser.parse_args(argv)
    if not getattr(opts, "func", None):
        parser.error("a command is required: inspect, textures or tools")
    if getattr(opts, "max_triangles", None) is not None and opts.max_triangles < 0:
        parser.error("--max-triangles must be >= 0")
    if getattr(opts, "deep_limit", 0) < 0:
        parser.error("--deep-limit must be >= 0")
    opts.func(opts)


if __name__ == "__main__":
    main()
