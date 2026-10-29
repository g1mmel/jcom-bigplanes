"""Package frozen independent components; never alter model or controller bytes.

Exports original embedded image bytes, documents materials and provenance, binds
existing review receipts, then hashes and archives every standalone package file.
This is a packaging step, not a new geometry or runtime validation campaign.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REVISION = "r0003"
REQUIREMENTS = "numpy==2.3.5\nscipy==1.17.0\nPillow==12.3.0\n"
IMAGE_NAMES = [
    "muzzle-flash-soft-alpha", "smoke-soft-alpha", "gun-metallic-roughness",
    "mount-paint-metallic-roughness", "canvas-boot-metallic-roughness",
    "ochre-guard-metallic-roughness", "khaki-bag-metallic-roughness",
    "orange-bag-metallic-roughness", "brass-case-metallic-roughness",
]
CONFIG = {
    "gau23-visual": {
        "title": "GAU-23 family aircraft cannon — visual component",
        "sha256": "2850c4d215d90f96839d724733a44d9b1a237360385a2672c76ea1830709e053",
        "root": "PIVOT_gun30_component",
        "axis": "barrel axis toward local −X",
        "description": "The aircraft-style 30 mm component contains a single barrel, receiver, mount and articulated feed-guide detail, a flexible installation boot, and an empty-case collection bag. Its fire-cycle clip coordinates a brief muzzle flash, recoil, a visible empty case passing through the receiver opening toward the bag, and dissipating smoke. The separate yaw, pitch and recoil clips support visual inspection.",
        "limitations": "The visible mount, feed guides and case path are authored approximations of an aircraft installation. Mechanical internals and ammunition feeding are not simulated. The case is an empty visual prop; no projectile, ballistic path, fire-control solution, damage or combat behavior is supplied. The flash, smoke, recoil distance, motion limits and clip timing are presentation choices, not measured operating data. Use the fire cycle on its own when inspecting coordinated firing; its recoil track overlaps the separate recoil demonstration clip.",
        "references": [
            ("USAF/DVIDS: AC-130J exterior 30 mm installation", "https://www.dvidshub.net/image/6427944/ac-130j-crew-maintain-proficiency-combat-readiness"),
            ("USAF/DVIDS: AC-130W interior installation", "https://www.dvidshub.net/image/6317363/ac-130w-supports-uae-us-maritime-surface-warfare-exercise"),
            ("USAF/DVIDS: AC-130W live-fire visual reference", "https://www.dvidshub.net/image/3486265/live-fire-training-with-ac-130w"),
            ("USAF/DVIDS: AC-130J early firing reference", "https://www.dvidshub.net/image/3146917/angry-annie-fires-first-rounds"),
        ],
    },
    "m102-airborne-visual": {
        "title": "Legacy 105 mm aircraft gun — visual component",
        "sha256": "597e8897d855229c0e98ebcaf652518fc050ff7b5221e90201251ff38cd2d026",
        "root": "PIVOT_gun105_component",
        "axis": "barrel axis toward local −X",
        "description": "The legacy 105 mm aircraft-style component contains the barrel, receiver, recoil assembly, mount, ochre guard, flexible installation boot and case-handling tray. A coordinated fire-cycle clip combines flash, recoil and smoke with a visual receiver-cover opening and an empty case leaving the cut receiver cavity. Separate yaw, pitch and recoil clips support visual inspection. The form is intended to represent an earlier, approximately 2021 installation; it is not a model of the subsequent replacement gun.",
        "limitations": "The receiver-cover motion is an authored visual device; it is not a verified depiction of the real breech mechanism. Internal loading, extraction and crew handling are not reconstructed. The empty case and tray trajectory are visual approximations, and no projectile, ballistic path, fire-control solution, damage or combat behavior is supplied. Flash, smoke, recoil distance, motion limits and clip timing are presentation choices, not measured operating data. Use the fire cycle on its own when inspecting coordinated firing; its recoil track overlaps the separate recoil demonstration clip.",
        "references": [
            ("USAF/DVIDS: earlier AC-130J exterior gun installation", "https://www.dvidshub.net/image/5621883/73rd-amu-air-commandos-perform-post-flight-inspection-ac-130j-ghostrider-gunship"),
            ("USAF/DVIDS: AC-130J interior gun installation", "https://www.dvidshub.net/image/3146918/angry-annie-fires-first-rounds"),
            ("USAF/DVIDS: AC-130W firing/recoil reference", "https://www.dvidshub.net/image/3486262/live-fire-training-with-ac-130w"),
            ("USAF/DVIDS: 2021 AC-130J installation", "https://www.dvidshub.net/image/6637434/ac-130j-gunship-trains-with-multinational-forces-during-trojan-footprint-21"),
            ("USAF/DVIDS: interior case-handling reference", "https://www.dvidshub.net/image/6427973/ac-130j-crew-maintain-proficiency-combat-readiness"),
        ],
    },
    "eoir-visual": {
        "title": "MX-20-family representative EO/IR visual component",
        "sha256": "6ceb0589b84eb83a6bbde926e709ab46f62f7e3b794ea7c4ed29c4ae92e5843f",
        "root": "PIVOT_eoir_component",
        "axis": "optical face toward local −Z",
        "description": "This representative sensor has a matte gray housing, its own top cap, an open fork/yoke, recessed unequal optical windows, dark optical barrels, seals and fastener details. Separate yaw and pitch hierarchies articulate the housing and optical assembly. It is an independent visual component; aircraft pylons, installation transforms and aircraft geometry are outside the package.",
        "limitations": "The visible form is guided by public MX-20 family imagery. Exact aperture assignments, window sizes, surface finishes, motion limits and internal gimbal construction are not established. The AC-130W source identifies two MX-20 sensors, but the exact sensor type fitted to each AC-130J slot remains configuration-dependent; this package does not establish a particular J tail/block fit. It contains no sensor image generation, tracking, laser, targeting or other operational sensor simulation. The manufacturer product photograph is a later family-form reference, not proof of a specific 2021 installation.",
        "references": [
            ("L3Harris: WESCAM MX-20 manufacturer product page", "https://www.l3harris.com/all-capabilities/wescam-mx-20-air-surveillance-and-reconnaissance"),
            ("L3Harris: manufacturer product photograph used for visible form", "https://www.l3harris.com/sites/default/files/2026-04/wescam-mx-20-eo-ir-air-surveillance-reconnaissance.png"),
            ("L3Harris: public MX-20 family brochure", "https://www.l3harris.com/sites/default/files/2020-07/ims_eo_brochure_wescam_MX-20-0102AB-Brochure.pdf"),
            ("USAF: MC-130W Dragon Spear sensor identification", "https://www.robins.af.mil/News/Article-Display/Article/377994/mc-130w-dragon-spear-visits-robins/"),
            ("USAF/DVIDS: 2019 AC-130J chin installation photograph", "https://www.dvidshub.net/image/5621880/73rd-amu-air-commandos-perform-post-flight-inspection-ac-130j-ghostrider-gunship"),
        ],
    },
}


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(path.read_bytes())


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def read_glb(path):
    blob = path.read_bytes()
    json_size = struct.unpack_from("<I", blob, 12)[0]
    doc = json.loads(blob[20:20 + json_size])
    binary = blob[28 + json_size:]
    return doc, binary


def material_bindings(material):
    bindings = []
    def walk(value, path=""):
        if not isinstance(value, dict):
            return
        for key, item in value.items():
            current = f"{path}.{key}" if path else key
            if key.endswith("Texture") and isinstance(item, dict) and "index" in item:
                color = "sRGB RGB; linear alpha" if key in ("baseColorTexture", "emissiveTexture") else "linear data"
                bindings.append({"property": current, "texture_index": item["index"], "texcoord": item.get("texCoord", 0), "interpretation": color})
            else:
                walk(item, current)
    walk(material)
    return bindings


def export_materials(folder, cfg):
    doc, binary = read_glb(folder / "model.glb")
    texdir = folder / "textures"
    texdir.mkdir(exist_ok=True)
    images = []
    for index, source in enumerate(doc.get("images", [])):
        view = doc["bufferViews"][source["bufferView"]]
        start = view.get("byteOffset", 0)
        data = binary[start:start + view["byteLength"]]
        ext = {"image/png": "png", "image/jpeg": "jpg"}[source["mimeType"]]
        label = IMAGE_NAMES[index] if index < len(IMAGE_NAMES) else "embedded"
        relative = f"textures/image-{index:02d}-{label}.{ext}"
        (folder / relative).write_bytes(data)
        with Image.open(io.BytesIO(data)) as im:
            size, mode = list(im.size), im.mode
        images.append({"image_index": index, "file": relative, "mime_type": source["mimeType"], "bytes": len(data), "sha256": sha_bytes(data), "size_pixels": size, "mode": mode, "provenance": "Original analytic image authored for this revision; exact embedded image bytes exported without re-encoding."})

    uses = {i: [] for i in range(len(doc.get("materials", [])))}
    for mesh_index, mesh in enumerate(doc.get("meshes", [])):
        for primitive_index, primitive in enumerate(mesh.get("primitives", [])):
            if "material" in primitive:
                uses[primitive["material"]].append({"mesh_index": mesh_index, "mesh_name": mesh.get("name"), "primitive_index": primitive_index})
    materials, texture_uses = [], {i: [] for i in range(len(doc.get("textures", [])))}
    for index, material in enumerate(doc.get("materials", [])):
        bindings = material_bindings(material)
        for binding in bindings:
            tex_index = binding["texture_index"]
            image_index = doc["textures"][tex_index]["source"]
            binding.update(image_index=image_index, file=images[image_index]["file"])
            texture_uses[tex_index].append({"material_index": index, "material_name": material.get("name"), "used_by_geometry": bool(uses[index]), "property": binding["property"]})
        materials.append({"material_index": index, "name": material.get("name"), "used_by_geometry": bool(uses[index]), "mesh_primitives": uses[index], "gltf_material": material, "texture_bindings": bindings})
    textures = []
    for index, texture in enumerate(doc.get("textures", [])):
        textures.append({"texture_index": index, "gltf_texture": texture, "image_file": images[texture["source"]]["file"], "used_by_geometry": any(x["used_by_geometry"] for x in texture_uses[index]), "material_bindings": texture_uses[index], "sampler": doc.get("samplers", [])[texture["sampler"]] if "sampler" in texture else "glTF default sampler"})
    inventory = {
        "schema": "jcnc-component-material-inventory-1",
        "asset_id": folder.name,
        "revision": REVISION,
        "model": {"file": "model.glb", "sha256": cfg["sha256"]},
        "scope": "Inventory and original-byte texture exports only. The frozen GLB is unchanged and remains self-contained.",
        "image_count": len(images),
        "material_count": len(materials),
        "materials_used_by_geometry": sum(x["used_by_geometry"] for x in materials),
        "color_and_channel_notes": ["Base-color and emissive texture RGB channels are interpreted as sRGB; alpha is linear.", "Metallic-roughness maps are linear data: G is roughness and B is the metallic multiplier. R is not connected as occlusion.", "PBR factors multiply the corresponding texture channels. No normal maps or photographic texture bakes are supplied.", "Unused material definitions and their images are retained and inventoried exactly as exported. The family placeholder materials and empty metadata node do not carry aircraft geometry or resource dependencies."],
        "images": images,
        "textures": textures,
        "samplers": doc.get("samplers", []),
        "materials": materials,
    }
    write_json(folder / "materials.json", inventory)
    if images:
        texture_readme = """# Original embedded texture exports

These PNG files are byte-for-byte copies of the images embedded in `../model.glb`. The GLB does not load these external copies. `../materials.json` maps image indices, texture indices, material slots and actual mesh usage; some exported maps belong to unused material definitions.

The flash and smoke textures are original analytic soft-alpha images. The surface maps are original analytic material variation, not photographs. Base-color/emissive RGB uses sRGB; alpha and metallic-roughness data are linear. In metallic-roughness maps, G controls roughness and B multiplies metallic. No normal map or photographic texture bake is included.
"""
    else:
        texture_readme = """# No raster textures in this component

The EO/IR component has no embedded or external image maps. Its appearance uses the exported PBR material factors, surface geometry and vertex normals. `../materials.json` records the exact gray, gasket, metal and optical material values and their mesh usage. No photographic texture bake is included.
"""
    (texdir / "README.md").write_text(texture_readme)
    return inventory


def readme(cfg, inventory, native):
    references = "\n".join(f"- [{label}]({url})" for label, url in cfg["references"])
    maps = (f"{inventory['image_count']} original analytic PNG images are embedded in the GLB and copied unchanged to `textures/`. The material inventory marks maps and materials that are retained but unused by this component." if inventory["image_count"] else "This component uses PBR material factors without image maps. The `textures/` directory explains that intentional absence.")
    return f"""# {cfg['title']}

claude-design / cg46 · {REVISION} · `DRAFT_ARTICULATED_REVIEW`

{cfg['description']}

## Package contents

| File | Purpose |
| --- | --- |
| `model.glb` | Self-contained glTF 2.0 geometry, materials and named animation clips. |
| `articulation.json` | Exported controls, playback and visual-effect bindings. |
| `editable.blend` | Direct import of the delivered GLB, saved and reopened in Blender {native['blender_version']}; named actions/NLA tracks and packed texture images are retained. |
| `source/` | Independent Python authoring source, component selection and pinned dependency versions. |
| `materials.json`, `textures/` | Exact PBR definitions, mesh/material/texture mappings and original embedded-image exports. |
| `inspector.html` | Portable inspector with the model and controls embedded. Its companion manifest and QA receipt describe that viewer artifact. |
| `manifest.json` | SHA-256 and size of every package file except the manifest itself, plus the delivered model/native-scene binding. |

## Rebuild and integration

From this component directory, install the pinned dependencies into a Python environment and run:

```bash
python -m pip install -r source/requirements.txt
python source/component_source.py
```

The entry point writes `model-rebuilt.glb` and `rebuild-receipt.json`; it leaves the delivered `model.glb` and controller unchanged. It needs no parent aircraft files or network access after dependency installation. The existing isolation review matched the rebuilt component's geometry, materials, hierarchy and clips. Whole-file bytes can differ because the assembled export retains additional unused material/metadata definitions.

The canonical component root is `{cfg['root']}` and carries the `level 1` tag. Units are metres, with +Y up and {cfg['axis']}. The native Blender import converts glTF `[x, y, z]` to Blender `[x, -z, y]`. Attach or reposition the component root; aircraft installation placement belongs to the containing aircraft asset. The empty `AIRFRAME_COMMON_SOURCE` node and unused family material names are retained metadata and carry no aircraft mesh or image dependency.

{maps} The editable Python source is the parametric authoring master; `editable.blend` is the reviewed native import of the delivered model.

## Provenance

The mesh geometry and visual animation were authored for this revision from public photographic references. No Sketchfab model, downloaded viewer geometry, third-party mesh or photographic texture was incorporated. The Sketchfab search did not produce an exact component with a readily available authorized original download suitable for this delivery. Reference pages guided visible form and configuration; they are not engineering drawings. Linked photographs and manufacturer materials are not bundled and retain their original terms.

{references}

## Scope and limitations

{cfg['limitations']}

Surface finish, dimensions and travel are visual approximations. Photographic equivalence and photorealistic acceptance have not been established. This is a game/visualization component, with no manufacturing or operational specification implied.

The delivered bytes passed the existing glTF format and scoped geometry/source-isolation checks, plus the native Blender import/save/reopen review. These checks do not establish continuous collision clearance, a particular aircraft tail/block fit, damage behavior, runtime performance or native Unreal acceptance. Those gates remain open. The manifest binds the existing review results to the delivered model and native scene; detailed receipts are in the full family revision's `qa/` directory.
"""


def file_role(relative):
    if relative == "model.glb": return "standalone_model"
    if relative == "editable.blend": return "reviewed_native_editable"
    if relative.startswith("source/"): return "independent_authoring_source"
    if relative.startswith("textures/"): return "texture_export_or_documentation"
    if relative.startswith("inspector"): return "portable_inspector_or_receipt"
    return "metadata_or_documentation"


def main():
    validation = json.loads((ROOT / "qa/gltf-validator-summary.json").read_text())
    geometry = json.loads((ROOT / "qa/system_geometry_report.json").read_text())
    archives = ROOT / "packages"
    archives.mkdir(exist_ok=True)
    summaries = []
    for cid, cfg in CONFIG.items():
        folder = ROOT / "components" / cid
        # Bind existing review receipts to frozen artifacts before documenting them.
        assert sha_file(folder / "model.glb") == cfg["sha256"], f"Unexpected model bytes: {cid}"
        native_path = ROOT / "qa" / f"system-review-{cid}-r0003-rest.json"
        native = json.loads(native_path.read_text())
        assert native["input_sha256"] == cfg["sha256"] and native["status"] == "PASS"
        assert sha_file(folder / "editable.blend") == native["editable_blend"]["sha256"]
        inventory = export_materials(folder, cfg)
        (folder / "source/requirements.txt").write_text(REQUIREMENTS)
        (folder / "README.md").write_text(readme(cfg, inventory, native))
        format_result = next(x for x in validation["models"] if x["id"] == cid)
        geometry_result = next(x for x in geometry["files"] if x["file"] == f"components/{cid}/model.glb")
        isolation = next(x for x in geometry["source_isolation"] if x["component"] == cid)
        assert format_result["sha256"] == geometry_result["sha256"] == isolation["delivered_sha256"] == cfg["sha256"]
        files = []
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path == folder / "manifest.json": continue
            if path.is_symlink(): raise ValueError(f"External symlink is not a standalone package file: {path}")
            relative = path.relative_to(folder).as_posix()
            files.append({"path": relative, "role": file_role(relative), "bytes": path.stat().st_size, "sha256": sha_file(path)})
        manifest = {
            "schema": "jcnc-standalone-package-manifest-1",
            "asset_id": cid,
            "revision": REVISION,
            "author": "claude-design",
            "acceptance": "DRAFT_ARTICULATED_REVIEW",
            "model": {"file": "model.glb", "sha256": cfg["sha256"], "component_root": cfg["root"], "units": "metres", "aircraft_dependency": False},
            "editable_native": {"file": "editable.blend", "sha256": native["editable_blend"]["sha256"], "source_model_sha256": native["input_sha256"], "blender_version": native["blender_version"], "import": native["import"], "reopen": native["blend_reopen"], "geometry_changes": native["geometry_changes"]},
            "provenance": {"geometry": "Original photo-guided visual component authored for this revision.", "textures": "Original analytic PNGs; no third-party or photographic texture ingestion." if inventory["image_count"] else "PBR factors only; no image maps.", "third_party_models_ingested": [], "reference_pages": [{"label": label, "url": url} for label, url in cfg["references"]]},
            "existing_review_summary": {
                "gltf_validator": {key: format_result[key] for key in ("status", "errors", "warnings", "infos", "issue_codes")},
                "scoped_geometry": {key: geometry_result[key] for key in ("status", "triangles", "meshes", "clips_total", "embedded_images")},
                "isolated_source_rebuild": {key: isolation[key] for key in ("status", "network_disabled", "parent_project_reads_forbidden", "byte_identical", "expected_byte_difference")},
                "native_review": native["status"],
                "full_family_receipts": [
                    {"path": f"qa/{cid}.gltf-validator.json", "sha256": sha_file(ROOT / "qa" / f"{cid}.gltf-validator.json")},
                    {"path": "qa/system_geometry_report.json", "sha256": sha_file(ROOT / "qa/system_geometry_report.json")},
                    {"path": native_path.relative_to(ROOT).as_posix(), "sha256": sha_file(native_path)},
                ],
                "receipt_note": "Summaries transcribed from the existing final-byte reviews; detailed receipts are distributed in the full family package. Packaging did not rerun geometry or runtime tests.",
            },
            "limitations": [cfg["limitations"], "Appearance, dimensions and motion are visual approximations, not an operational model.", "Photographic acceptance, native Unreal, runtime performance, damage and continuous collision clearance remain open."],
            "hash_algorithm": "SHA-256",
            "hash_scope": "Every regular file in this component directory, excluding only manifest.json. Archive is stored outside this directory to avoid recursion.",
            "file_count_excluding_manifest": len(files),
            "bytes_excluding_manifest": sum(x["bytes"] for x in files),
            "files": files,
        }
        write_json(folder / "manifest.json", manifest)
        archive = archives / f"{cid}-{REVISION}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for path in sorted(folder.rglob("*")):
                if path.is_file(): z.write(path, Path(cid) / path.relative_to(folder))
        summaries.append({"asset_id": cid, "files_in_archive": len(files) + 1, "texture_images": inventory["image_count"], "used_materials": inventory["materials_used_by_geometry"], "archive": archive.relative_to(ROOT).as_posix(), "bytes": archive.stat().st_size, "sha256": sha_file(archive), "manifest_sha256": sha_file(folder / "manifest.json")})
    print(json.dumps({"status": "PACKAGED", "components": summaries}, indent=2))


if __name__ == "__main__":
    main()
