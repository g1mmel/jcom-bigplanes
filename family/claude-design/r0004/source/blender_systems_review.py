"""claude-design | Native GLB systems review; geometry is never reconstructed.

Run with Blender, for example::

    blender -b --factory-startup --python source/blender_systems_review.py -- \
      --root /revision --model ac130j --views gun30-exterior gun105-exterior

    blender -b --factory-startup --python source/blender_systems_review.py -- \
      --root /revision --component /component.glb --asset-id eoir --views isolated

The imported named NLA tracks are the only native animation source.  Camera
contracts use the source glTF coordinate system (+Y up, nose -Z); this script
converts them to Blender.  Controller world-matrix snapshots are optional and
are accepted only when their source hashes match the current export.  All
renders are evidence from the actual exported mesh, with inspection lighting.
This script does not certify continuous clearance, photographic equivalence,
browser rendering, Unreal import, or real weapon operation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


AUTHOR = "claude-design"
CONVERSION = Matrix(((1, 0, 0, 0), (0, 0, -1, 0),
                     (0, 1, 0, 0), (0, 0, 0, 1)))
SAMPLES = (0., .08, .16, .28, .44, .62, .82, 1.)
CLIP_SCOPE = re.compile(r"(?:gun\d+_(?:fire_)?cycle|(?:eoir|sensor).*_(?:yaw|pitch))", re.I)

# Explicit authored review cameras, not measurements of a real installation.
# --camera-file can replace these with an agreed camera contract.
DEFAULT_CAMERAS = {
    "gun30-exterior": {"position": [-5.5, 3.0, -9.6],
                       "target": [-2.3, 2.5, -7.7], "scale": 3.7},
    "gun105-exterior": {"position": [-8.0, 3.7, 5.1],
                        "target": [-2.95, 2.25, 2.35], "scale": 4.3},
    "gun30-interior": {"position": [.75, 3.12, -5.9],
                       "target": [-.8, 2.5, -7.72], "scale": 2.8,
                       "inspection_fill": True},
    "gun105-interior": {"position": [.85, 3.1, 4.15],
                        "target": [-.7, 2.3, 2.35], "scale": 3.3,
                        "inspection_fill": True},
    "sensor-chin": {"position": [-1.5, .8, -16.4],
                    "target": [0., 1.15, -13.92], "scale": 1.45},
    "sensor-port": {"position": [-4.0, 1.1, -7.6],
                    "target": [-1.42, 1.18, -5.65], "scale": 1.45},
}


def cli():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--model", default="ac130j")
    p.add_argument("--input", type=Path)
    p.add_argument("--component", type=Path)
    p.add_argument("--asset-id")
    p.add_argument("--label", default="r0003")
    p.add_argument("--views", nargs="+", default=None)
    p.add_argument("--camera-file", type=Path)
    p.add_argument("--clip", help="Exact imported NLA track to render")
    p.add_argument("--time", type=float, default=0., help="Normalized native clip time")
    p.add_argument("--snapshot-file", type=Path)
    p.add_argument("--snapshot-label")
    p.add_argument("--compare-input", type=Path,
                   help="Render an earlier GLB from the identical cameras, at rest")
    p.add_argument("--compare-label", default="r0002")
    p.add_argument("--samples", type=int, default=24)
    p.add_argument("--resolution", type=int, default=1000)
    p.add_argument("--height-ratio", type=float, default=.74)
    p.add_argument("--probe-only", action="store_true")
    p.add_argument("--reuse-editable", action="store_true",
                   help="Reuse a prior native scene only if input and script hashes match")
    a = p.parse_args(args)
    if a.component and a.input:
        p.error("Use either --component or --input")
    if a.clip and a.snapshot_label:
        p.error("Use one pose source: --clip or --snapshot-label")
    if not 0 <= a.time <= 1:
        p.error("--time must be in [0,1]")
    if a.samples < 1 or a.resolution < 128:
        p.error("Invalid render quality")
    return a


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative(path, root):
    try:
        return str(Path(path).resolve().relative_to(root))
    except ValueError:
        return str(Path(path).resolve())


def slug(value):
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")


def glb_document(path):
    b = path.read_bytes()
    if b[:4] != b"glTF":
        raise ValueError("Expected binary glTF: " + str(path))
    length, kind = struct.unpack_from("<II", b, 12)
    if kind != 0x4E4F534A:
        raise ValueError("Missing GLB JSON chunk")
    return json.loads(b[20:20 + length])


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def vec_gltf(v):
    return Vector((v[0], -v[2], v[1]))


def matrix_error(a, b):
    return max(abs(a[i][j] - b[i][j]) for i in range(4) for j in range(4))


def bounds(objects):
    coords = [o.matrix_world @ Vector(c) for o in objects if o.type == "MESH"
              for c in o.bound_box]
    if not coords:
        raise RuntimeError("No imported meshes")
    return ([min(v[k] for v in coords) for k in range(3)],
            [max(v[k] for v in coords) for k in range(3)])


def tracks_for(objects):
    return [(o, t) for o in objects if o.animation_data
            for t in o.animation_data.nla_tracks]


def capture_rest(objects):
    return {o.name: o.matrix_basis.copy() for o in objects}


def restore(objects, rest):
    for o in objects:
        if o.animation_data:
            o.animation_data.action = None
            for t in o.animation_data.nla_tracks:
                t.mute = True
        o.matrix_basis = rest[o.name]
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()


def activate_clip(objects, rest, clip, normalized_time):
    restore(objects, rest)
    selected = [(o, t) for o, t in tracks_for(objects) if t.name == clip]
    if not selected:
        raise ValueError("No imported NLA tracks named " + clip)
    strips = [s for _, t in selected for s in t.strips]
    start = min(s.action_frame_start for s in strips)
    end = max(s.action_frame_end for s in strips)
    # Blender 4.5 glTF stashes can remain unevaluated when only their mute flag
    # is cleared.  Bind the exact imported action AND its action slot, as the
    # glTF importer's own restore_animation_on_object does.  The NLA stashes
    # remain intact; no keys, curves, or source transforms are reconstructed.
    for o, t in selected:
        if len(t.strips) != 1:
            raise RuntimeError("Expected a single imported GLB action per NLA track")
        s = t.strips[0]
        o.animation_data.action = s.action
        o.animation_data.action_slot = s.action_slot
    frame = start + normalized_time * (end - start)
    bpy.context.scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
    bpy.context.view_layer.update()
    return selected, {"start_frame": start, "end_frame": end, "sample_frame": frame}


def animated_meshes(selected):
    objects = set()
    for o, _ in selected:
        objects.add(o)
        objects.update(o.children_recursive)
    return sorted((o for o in objects if o.type == "MESH"), key=lambda o: o.name)


def native_checks(objects, rest, source_clips):
    """Sample actual imported tracks and actual mesh vertices, not declared pivots."""
    clips = sorted(n for n in source_clips if CLIP_SCOPE.search(n))
    rows = []
    for clip in clips:
        selected, extent = activate_clip(objects, rest, clip, 0.)
        moving = animated_meshes(selected)
        targets = sorted({o for o, _ in selected}, key=lambda o: o.name)
        restore(objects, rest)
        baselines = {o.name: o.matrix_world.copy() for o in targets}
        # Evenly spaced real mesh vertices, up to 24 per animated mesh.
        points = {}
        for o in moving:
            count = len(o.data.vertices)
            indices = sorted({round(i * (count - 1) / min(23, count - 1))
                              for i in range(min(24, count))}) if count > 1 else ([0] if count else [])
            points[o.name] = [(o.data.vertices[i].co.copy(),
                               o.matrix_world @ o.data.vertices[i].co) for i in indices]
        samples = []
        for u in SAMPLES:
            activate_clip(objects, rest, clip, u)
            finite = all(math.isfinite(v) for o in targets + moving
                         for row in o.matrix_world for v in row)
            max_matrix = max((matrix_error(o.matrix_world, baselines[o.name])
                              for o in targets), default=0.)
            target_changes = {o.name: matrix_error(o.matrix_world, baselines[o.name])
                              for o in targets}
            max_vertex = max(((o.matrix_world @ local - original).length
                              for o in moving for local, original in points[o.name]), default=0.)
            samples.append({"normalized_time": u, "finite": finite,
                            "max_target_matrix_delta": max_matrix,
                            "target_matrix_deltas": target_changes,
                            "max_sampled_vertex_displacement_m": max_vertex})
        changed = max((s["max_sampled_vertex_displacement_m"] for s in samples), default=0.) > 1e-6
        all_targets_changed = all(max(s["target_matrix_deltas"][o.name] for s in samples) > 1e-6
                                  for o in targets)
        rows.append({"clip": clip, "native_track_count": len(selected),
                     "animated_target_nodes": [o.name for o in targets],
                     "animated_mesh_count": len(moving),
                     "sampled_vertex_count": sum(len(v) for v in points.values()),
                     "frame_extent": extent, "samples": samples,
                     "all_animated_targets_changed": all_targets_changed,
                     "result": "PASS" if changed and all_targets_changed and all(s["finite"] for s in samples) else "FAIL"})
    restore(objects, rest)
    return {"result": "PASS" if rows and all(r["result"] == "PASS" for r in rows)
            else ("FAIL" if rows else "NOT_RUN"),
            "scope": "Eight samples per imported gun cycle / sensor action retained in named NLA tracks. Exact imported actions and action slots are evaluated natively. Actual mesh vertices and target matrices; no continuous collision or real operational certification.",
            "clips": rows}


def snapshot_source(a, root, sha):
    path = a.snapshot_file or root / "qa" / ("viewer-poses-" + a.model + ".json")
    if not path.exists():
        if a.snapshot_label:
            raise FileNotFoundError("Requested controller snapshots are missing: " + str(path))
        return None, {"result": "NOT_RUN", "reason": "No controller snapshot file available"}
    data = json.loads(path.read_text())
    checks = {"model_sha256": data.get("model_sha256") == sha}
    sources = {"articulation_sha256": root / "articulation" / (a.model + ".json"),
               "controller_sha256": root / "viewer/controller.mjs",
               "pose_driver_sha256": root / "viewer/pose-driver.mjs"}
    for key, source in sources.items():
        if key in data and source.exists():
            checks[key] = data[key] == digest(source)
    ok = all(checks.values())
    report = {"path": relative(path, root), "sha256": digest(path),
              "result": "PASS" if ok else "BLOCKED", "source_hash_checks": checks,
              "pose_labels": [s["label"] for s in data.get("samples", [])],
              "scope": "Source identity check; this does not render the browser."}
    if not ok and a.snapshot_label:
        raise RuntimeError("Controller snapshots do not match current source hashes")
    return data if ok else None, report


def apply_snapshot(objects, rest, sample):
    restore(objects, rest)
    by_name = {o.name: o for o in objects}
    # Three.js PropertyBinding.sanitizeNodeName replaces whitespace with '_'
    # and removes reserved characters [].:/ before GLTFLoader exposes names.
    # Preserve exact Blender/source names; add only unambiguous read aliases.
    aliases = {}
    for o in objects:
        name = re.sub(r"[\[\]\.:/]", "", re.sub(r"\s", "_", o.name))
        if name in aliases and aliases[name] != o:
            raise RuntimeError("Ambiguous sanitized controller node name: " + name)
        aliases[name] = o
    for name, o in aliases.items():
        if name in by_name and by_name[name] != o:
            raise RuntimeError("Controller alias conflicts with native object name: " + name)
        by_name[name] = o
    inv = CONVERSION.inverted()
    expected = {}
    missing = []
    for n in sample["nodes"]:
        o = by_name.get(n["name"])
        if o is None:
            missing.append(n["name"])
            continue
        v = n["matrix_world"]
        m = Matrix(tuple(tuple(v[c * 4 + r] for c in range(4)) for r in range(4)))
        expected[o.name] = CONVERSION @ m @ inv
        o.matrix_world = expected[o.name]
        bpy.context.view_layer.update()
    if missing:
        raise RuntimeError("Controller/Blender node mismatch: " + repr(missing))
    error = max((matrix_error(by_name[n].matrix_world, m) for n, m in expected.items()), default=0.)
    if error > 2e-5:
        raise RuntimeError("Controller-to-Blender world-matrix error: " + str(error))
    return {"result": "PASS", "label": sample["label"],
            "converted_nodes": len(expected), "maximum_world_matrix_error": error,
            "node_name_mapping": "Exact names plus collision-checked Three.js PropertyBinding.sanitizeNodeName aliases"}


def emission_material(name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    tree = m.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    emit = tree.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = color
    emit.inputs["Strength"].default_value = 1.
    tree.links.new(emit.outputs[0], output.inputs["Surface"])
    return m


def review_scene(a):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = a.samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = a.resolution
    scene.render.resolution_y = round(a.resolution * a.height_ratio)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    world = bpy.data.worlds.new("SYSTEM_REVIEW_NEUTRAL_WORLD")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (.12, .135, .15, 1.)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = .55
    scene.world = world
    camera = bpy.data.objects.new("SYSTEM_REVIEW_CAMERA", bpy.data.cameras.new("SYSTEM_REVIEW_CAMERA"))
    scene.collection.objects.link(camera)
    camera.data.type = "ORTHO"
    camera.data.clip_start = .001
    camera.data.clip_end = 500.
    scene.camera = camera
    lights = []
    for name in ("KEY", "FILL", "RIM", "INTERIOR_INSPECTION"):
        data = bpy.data.lights.new("SYSTEM_REVIEW_" + name, "AREA")
        data.shape = "DISK"
        light = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(light)
        lights.append(light)
    text_data = bpy.data.curves.new("SYSTEM_REVIEW_LABEL", type="FONT")
    label = bpy.data.objects.new("SYSTEM_REVIEW_LABEL", text_data)
    scene.collection.objects.link(label)
    label.parent = camera
    label.data.materials.append(emission_material("SYSTEM_REVIEW_LABEL_INK", (.72, .76, .79, 1.)))
    label.visible_shadow = False
    label.visible_diffuse = False
    label.visible_glossy = False
    label.visible_transmission = False
    plate_mesh = bpy.data.meshes.new("SYSTEM_REVIEW_LABEL_PLATE")
    plate_mesh.from_pydata([(-1., -1., 0.), (1., -1., 0.), (1., 1., 0.), (-1., 1., 0.)],
                          [], [(0, 1, 2, 3)])
    plate = bpy.data.objects.new("SYSTEM_REVIEW_LABEL_PLATE", plate_mesh)
    scene.collection.objects.link(plate)
    plate.parent = camera
    plate.data.materials.append(emission_material("SYSTEM_REVIEW_LABEL_BACK", (.025, .031, .037, 1.)))
    plate.visible_shadow = False
    plate.visible_diffuse = False
    plate.visible_glossy = False
    plate.visible_transmission = False
    return camera, lights, label


def isolated_cameras(lo, hi, height_ratio):
    c = (Vector(lo) + Vector(hi)) * .5
    size = Vector(hi) - Vector(lo)
    d = max(size)
    # Inverse coordinate conversion: Blender [x,y,z] -> glTF [x,z,-y].
    def source(v):
        return [v[0], v[2], -v[1]]
    corners = [Vector((x, y, z)) for x in (lo[0], hi[0])
               for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    result = {}
    for name, offset in (("isolated", (-1.2, 1.8, .85)),
                         ("isolated-front", (0., 2.8, .12)),
                         ("isolated-side", (-2.8, .02, .15))):
        position = c + Vector(offset) * d
        orientation = (c - position).to_track_quat("-Z", "Y").conjugated()
        projected = [orientation @ (v - c) for v in corners]
        width = max(v.x for v in projected) - min(v.x for v in projected)
        height = max(v.y for v in projected) - min(v.y for v in projected)
        scale = max(width, height / height_ratio) * 1.22
        result[name] = {"position": source(position), "target": source(c),
                        "scale": scale, "framing": "Projected source bounds plus 22 percent margin"}
    return result


def configure_view(a, spec, objects, camera, lights, label, caption):
    camera.location = vec_gltf(spec["position"])
    target = vec_gltf(spec["target"])
    look_at(camera, target)
    scale = float(spec["scale"])
    camera.data.ortho_scale = scale
    # Light positions follow the review target, with energy scaled by scene size.
    size = max(.5, scale)
    rotations = camera.rotation_euler.to_matrix()
    offsets = ((-1.2, .9, 1.4), (1.2, .35, .8), (.3, 1.0, -.8))
    energies = (100., 55., 95.)
    for light, offset, energy in zip(lights[:3], offsets, energies):
        light.location = target + rotations @ (Vector(offset) * size)
        light.data.energy = energy * size * size
        light.data.size = size * .9
        look_at(light, target)
        light.hide_render = bool(spec.get("inspection_fill"))
    inside = lights[3]
    inside.hide_render = not bool(spec.get("inspection_fill"))
    inside.location = camera.location + rotations @ Vector((0., .12 * size, -.15))
    inside.data.energy = 55. * size * size
    inside.data.size = size * .45
    look_at(inside, target)
    # Cutaway is render visibility only; all mesh data stays intact in the blend.
    keep_pattern = spec.get("keep_mesh_regex")
    hide_pattern = spec.get("hide_mesh_regex")
    if (keep_pattern or hide_pattern) and not spec.get("cutaway"):
        raise ValueError("A camera hiding asset geometry must declare cutaway=true")
    hidden = []
    for o in objects:
        o.hide_render = False
        if o.type != "MESH":
            continue
        if ((keep_pattern and not re.search(keep_pattern, o.name)) or
                (hide_pattern and re.search(hide_pattern, o.name))):
            o.hide_render = True
            hidden.append(o.name)
    suffix = " / CUTAWAY INSPECTION" if spec.get("cutaway") else ""
    suffix += " / INTERIOR INSPECTION LIGHT" if spec.get("inspection_fill") else ""
    label.data.body = caption + suffix
    label.data.size = scale * .014
    label.data.space_line = 1.2
    label.location = (-scale * .477, -scale * a.height_ratio * .44, -.04)
    label.rotation_euler = (0., 0., 0.)
    plate = bpy.data.objects["SYSTEM_REVIEW_LABEL_PLATE"]
    plate.location = (0., -scale * a.height_ratio * .455, -.045)
    plate.scale = (scale * .5, scale * a.height_ratio * .045, 1.)
    return hidden


def action_inventory(objects):
    return [{"node": o.name, "track": t.name,
             "strips": [{"name": s.name, "action": s.action.name if s.action else None,
                         "start_frame": s.frame_start, "end_frame": s.frame_end}
                        for s in t.strips]} for o, t in tracks_for(objects)]


def review_one(a, root, path, asset_id, label_value, cameras, before=False):
    source_sha = digest(path)
    doc = glb_document(path)
    source_clips = [clip.get("name", "") for clip in doc.get("animations", [])]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.
    scene.render.fps = 24
    scene.frame_start, scene.frame_end = 1, 25
    objects = list(scene.objects)
    names = [o.name for o in objects]
    meshes = [o for o in objects if o.type == "MESH"]
    rest = capture_rest(objects)
    restore(objects, rest)
    lo, hi = bounds(objects)
    inventory = action_inventory(objects)
    actions = sorted(action.name for action in bpy.data.actions)
    for action in bpy.data.actions:
        action.use_fake_user = True
    native = native_checks(objects, rest, source_clips)
    report = {
        "author": AUTHOR, "asset_id": asset_id, "revision_label": label_value,
        "input": relative(path, root), "input_sha256": source_sha,
        "script_sha256": digest(Path(__file__)), "blender_version": bpy.app.version_string,
        "import": "PASS", "asset_objects": len(objects), "meshes": len(meshes),
        "triangles": sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes),
        "bounds_blender_m": {"min": lo, "max": hi},
        "coordinate_conversion": "Source glTF [x,y,z] -> native Blender [x,-z,y]; metres, scale 1",
        "source_clip_names": source_clips, "native_action_names": actions,
        "native_animation_inventory": inventory, "native_animation_evaluation": native,
        "render_runtime": "Blender Cycles CPU", "render_samples": a.samples,
        "render_resolution": [a.resolution, round(a.resolution * a.height_ratio)],
        "browser_rendering": "NOT_RUN", "native_unreal": "NOT_RUN",
        "continuous_clearance": "NOT_RUN", "photographic_equivalence": "NOT_RUN",
        "geometry_changes": "NONE; direct native glTF import",
        "camera_contract": {"path": relative(a.camera_file, root), "sha256": digest(a.camera_file)}
            if a.camera_file else {"source": "Script defaults / projected component bounds"},
        "renders": [],
    }
    data, snapshot_report = snapshot_source(a, root, source_sha) if not before else (
        None, {"result": "NOT_RUN", "reason": "Earlier baseline comparison uses canonical rest"})
    report["controller_snapshot_source"] = snapshot_report
    camera, lights, text_obj = review_scene(a)
    merged_cameras = {**DEFAULT_CAMERAS, **isolated_cameras(lo, hi, a.height_ratio), **cameras}
    views = a.views or (["isolated", "isolated-front"] if a.component else
                        ["gun30-exterior", "gun105-exterior", "gun30-interior", "gun105-interior", "sensor-chin"])
    for view in views:
        if view not in merged_cameras:
            raise ValueError("Unknown camera: " + view)
    configure_view(a, merged_cameras[views[0]], objects, camera, lights, text_obj,
                   asset_id + " / actual GLB / editable rest pose")
    for o in objects:
        o.hide_render = False
    for im in bpy.data.images:
        if im.type in {"RENDER_RESULT", "COMPOSITING"}:
            continue
        if not im.packed_file:
            try:
                im.pack()
            except RuntimeError:
                pass
    editable = root / "editable" / ("system-" + slug(asset_id) + "-" + slug(label_value) + ".blend")
    editable.parent.mkdir(exist_ok=True)
    scene["system_review_input_sha256"] = source_sha
    scene["system_review_script_sha256"] = digest(Path(__file__))
    if not a.reuse_editable:
        bpy.ops.wm.save_as_mainfile(filepath=str(editable), compress=True)
    elif not editable.exists():
        raise FileNotFoundError("--reuse-editable requested but native file is missing")
    report["editable_blend"] = {"path": relative(editable, root), "sha256": digest(editable)}
    bpy.ops.wm.open_mainfile(filepath=str(editable))
    if bpy.context.scene.get("system_review_input_sha256") != source_sha or bpy.context.scene.get("system_review_script_sha256") != digest(Path(__file__)):
        raise RuntimeError("Native scene input or script identity is stale; rebuild without --reuse-editable")
    objects = [bpy.data.objects[name] for name in names]
    rest = capture_rest(objects)
    camera = bpy.data.objects["SYSTEM_REVIEW_CAMERA"]
    lights = [bpy.data.objects["SYSTEM_REVIEW_" + n] for n in ("KEY", "FILL", "RIM", "INTERIOR_INSPECTION")]
    text_obj = bpy.data.objects["SYSTEM_REVIEW_LABEL"]
    reopened_actions = sorted(action.name for action in bpy.data.actions)
    packed = [i for i in bpy.data.images if i.type not in {"RENDER_RESULT", "COMPOSITING"}]
    reopened_tracks = action_inventory(objects)
    reopen_ok = reopened_actions == actions and reopened_tracks == inventory and all(bool(i.packed_file) for i in packed)
    report["blend_reopen"] = {
        "result": "PASS" if reopen_ok else "FAIL", "asset_objects": len(objects),
        "named_actions_retained": reopened_actions == actions,
        "nla_track_inventory_retained": reopened_tracks == inventory,
        "all_texture_images_packed": all(bool(i.packed_file) for i in packed),
    }
    if not reopen_ok:
        raise RuntimeError("Native save/reopen lost actions, tracks, or image packing")
    pose = "rest"
    if not before and a.clip:
        _, extent = activate_clip(objects, rest, a.clip, a.time)
        pose = a.clip + "-" + ("%.3f" % a.time).replace(".", "p")
        report["render_pose"] = {"source": "exact action/slot from imported NLA track", "clip": a.clip,
                                  "normalized_time": a.time, **extent}
    elif not before and a.snapshot_label:
        matching = [s for s in data["samples"] if s["label"] == a.snapshot_label]
        if len(matching) != 1:
            raise ValueError("Expected one matching controller snapshot")
        report["render_pose"] = apply_snapshot(objects, rest, matching[0])
        report["render_pose"]["source"] = "exact controller world-matrix snapshot"
        pose = a.snapshot_label
    else:
        restore(objects, rest)
        report["render_pose"] = {"source": "canonical imported rest"}
    if not a.probe_only:
        for view in views:
            spec = merged_cameras[view]
            caption = asset_id + " / " + label_value + " / " + view + "\nACTUAL EXPORTED MESH / " + pose
            hidden = configure_view(a, spec, objects, camera, lights, text_obj, caption)
            fname = "system-" + "-".join(map(slug, (asset_id, label_value, view, pose))) + ".png"
            destination = root / "previews" / fname
            destination.parent.mkdir(exist_ok=True)
            bpy.context.scene.render.filepath = str(destination)
            bpy.ops.render.render(write_still=True)
            report["renders"].append({"path": relative(destination, root), "sha256": digest(destination),
                                      "view": view, "camera_gltf": spec, "pose": pose,
                                      "hidden_meshes": hidden, "cutaway": bool(spec.get("cutaway")),
                                      "inspection_light": bool(spec.get("inspection_fill"))})
    report["input_unchanged_during_review"] = digest(path) == source_sha
    report["status"] = "PASS" if reopen_ok and report["input_unchanged_during_review"] and native["result"] != "FAIL" else "FAIL"
    qapath = root / "qa" / ("system-review-" + "-".join(map(slug, (asset_id, label_value, pose))) + ".json")
    qapath.parent.mkdir(exist_ok=True)
    qapath.write_text(json.dumps(report, indent=2) + "\n")
    print("SYSTEM_REVIEW_COMPLETE " + json.dumps({"asset": asset_id, "label": label_value,
          "status": report["status"], "input_sha256": source_sha,
          "report": str(qapath), "renders": len(report["renders"])}), flush=True)
    return report


def main():
    a = cli()
    root = a.root.resolve()
    source = (a.component or a.input or root / "models" / (a.model + ".glb")).resolve()
    asset_id = a.asset_id or (source.stem if a.component else a.model)
    cameras = {}
    if a.camera_file:
        contract = json.loads(a.camera_file.read_text())
        cameras = contract.get("cameras", contract)
        if isinstance(cameras, list):
            cameras = {c["id"]: c for c in cameras}
        scales = {"gun30": 3.7, "gun105": 4.3, "internal30": 2.8,
                  "internal105": 3.3, "hero": 51., "port": 43., "cargo": 15.}
        for name, camera in cameras.items():
            camera.setdefault("scale", scales.get(name, 3.))
            if name.startswith("internal"):
                camera.setdefault("inspection_fill", True)
    if a.compare_input:
        review_one(a, root, a.compare_input.resolve(), asset_id, a.compare_label, cameras, before=True)
    result = review_one(a, root, source, asset_id, a.label, cameras)
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Blender can otherwise exit 0 after a Python exception; fail explicitly
        # and leave a scoped report instead of an unreported partial render.
        a = cli()
        asset = a.asset_id or (a.component.stem if a.component else a.model)
        failed = a.root.resolve() / "qa" / ("system-review-" + slug(asset) + "-" + slug(a.label) + "-FAILED.json")
        failed.parent.mkdir(exist_ok=True)
        failed.write_text(json.dumps({"author": AUTHOR, "status": "FAIL",
            "asset_id": asset, "error_type": type(exc).__name__, "error": str(exc),
            "script_sha256": digest(Path(__file__)),
            "native_unreal": "NOT_RUN", "browser_rendering": "NOT_RUN"}, indent=2) + "\n")
        print("SYSTEM_REVIEW_FAILED " + str(failed) + " " + str(exc), flush=True)
        raise SystemExit(2) from exc
