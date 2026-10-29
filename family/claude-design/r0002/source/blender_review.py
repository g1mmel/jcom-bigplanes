"""claude-design: reopen actual exported GLBs, save editable Blender source, render evidence.

This script uses Blender's own glTF importer. It does not certify Unreal or photographs.
Run: blender -b --factory-startup --python source/blender_review.py -- --root /revision --model c130
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def cli():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--model', default='c130')
    p.add_argument('--input', type=Path)
    p.add_argument('--probe-only', action='store_true')
    p.add_argument('--samples', type=int, default=24)
    p.add_argument('--resolution', type=int, default=1200)
    p.add_argument('--pose', default='parked')
    return p.parse_args(args)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def mat(name, rgba, roughness=.65, metallic=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = rgba
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    return m


def light(name, location, energy, size):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    o.location = location
    look_at(o, (0,0,3))
    return o


def main():
    a = cli()
    root = a.root.resolve()
    path = a.input or root/'models'/f'{a.model}.glb'
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    aircraft = list(bpy.context.scene.objects)
    meshes = [o for o in aircraft if o.type == 'MESH']
    coords = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = [min(v[k] for v in coords) for k in range(3)]
    hi = [max(v[k] for v in coords) for k in range(3)]
    inventory = []
    for o in aircraft:
        tracks = []
        if o.animation_data:
            for t in o.animation_data.nla_tracks:
                tracks.append({'track':t.name,'mute':t.mute,'strips':[{'name':s.name,'action':s.action.name if s.action else None,'start':s.frame_start,'end':s.frame_end} for s in t.strips]})
        if tracks:
            inventory.append({'node':o.name,'tracks':tracks})
    report = {'author':'claude-design','input':str(path),'input_sha256':sha,
        'blender_version':bpy.app.version_string,'import':'PASS',
        'objects':len(aircraft),'meshes':len(meshes),'actions':len(bpy.data.actions),
        'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),
        'blender_bounds_min':lo,'blender_bounds_max':hi,
        'materials':[m.name for m in bpy.data.materials],
        'images':[{'name':i.name,'width':i.size[0],'height':i.size[1],'packed':bool(i.packed_file)} for i in bpy.data.images],
        'animation_inventory':inventory,'native_unreal':'NOT_RUN','photographic_acceptance':'NOT_RUN'}
    qa = root/'qa';qa.mkdir(exist_ok=True)
    if a.probe_only:
        (qa/f'{a.model}-blender-probe.json').write_text(json.dumps(report,indent=2)+'\n')
        print('claude-design native import', json.dumps({k:v for k,v in report.items() if k not in ('animation_inventory','images','materials')}),flush=True)
        return
    # Native .blend is saved with the model, its actual imported NLA clips and packed maps.
    out = root/'editable';out.mkdir(exist_ok=True)
    for image in bpy.data.images:
        if not image.packed_file:
            try:image.pack()
            except RuntimeError:pass
    bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{a.model}-r0002.blend'),compress=True)
    report['blend_path']=f'editable/{a.model}-r0002.blend'
    report['blend_sha256']=hashlib.sha256((out/f'{a.model}-r0002.blend').read_bytes()).hexdigest()
    # Neutral lighting and scale ground belong only to the evidence scene.
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=a.samples
    scene.cycles.use_denoising=True
    scene.render.resolution_x=a.resolution
    scene.render.resolution_y=int(a.resolution*.68)
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.world=bpy.data.worlds.new('claude_design_review_world')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.16,.20,.27,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
    scene.view_settings.view_transform='AgX'
    bpy.ops.mesh.primitive_plane_add(size=220,location=(0,0,-.03))
    ground=bpy.context.object;ground.name='review_ground';ground.data.materials.append(mat('review_ground_material',(.075,.095,.12,1)))
    light('review_key',(22,18,34),48000,24)
    light('review_fill',(-20,8,22),30000,20)
    light('review_rim',(8,-28,26),42000,16)
    camera_data=bpy.data.cameras.new('review_camera')
    camera=bpy.data.objects.new('review_camera',camera_data)
    scene.collection.objects.link(camera);scene.camera=camera
    camera.data.type='ORTHO';camera.data.ortho_scale=51
    previews=root/'previews';previews.mkdir(exist_ok=True)
    views={
       'hero':((-39,48,29),(0,0,4.2),51),
       'rear':((35,-42,21),(0,0,4),51),
       'side':((-55,0,8),(0,0,5.3),43),
       'front':((0,60,8),(0,0,5.2),49),
       'top':((0,0,65),(0,0,0),49),
    }
    rendered=[]
    for label,(location,target,scale) in views.items():
        camera.location=location;look_at(camera,target);camera.data.ortho_scale=scale
        fname=f'{a.model}-{a.pose}-{label}.png'
        scene.render.filepath=str(previews/fname)
        bpy.ops.render.render(write_still=True)
        rendered.append({'path':'previews/'+fname,'sha256':hashlib.sha256((previews/fname).read_bytes()).hexdigest(),'pose':a.pose,'camera':label})
    report['renders']=rendered
    report['render_runtime']='Blender Cycles CPU'
    (qa/f'{a.model}-blender.json').write_text(json.dumps(report,indent=2)+'\n')
    print('claude-design native review complete',a.model,sha,flush=True)


if __name__=='__main__':main()
