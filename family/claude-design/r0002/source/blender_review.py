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
from mathutils import Vector, Matrix


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
    p.add_argument('--poses', action='store_true', help='Render actual Three controller snapshots, with exact hash match.')
    p.add_argument('--views', nargs='+', default=['hero','rear','side','front','top'])
    p.add_argument('--pose-labels', nargs='+', default=['SERVICE','FLYING','GLOBAL_INSPECTION_OPEN','GLOBAL_ACCESS_OPEN','GLOBAL_50'])
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


def native_clip_checks(aircraft, controls):
    """Evaluate actual imported NLA clips in Blender; do not drive metadata pivots."""
    scene = bpy.context.scene
    rest = {o.name:o.matrix_basis.copy() for o in aircraft}
    rest_world = {o.name:o.matrix_world.copy() for o in aircraft}
    tracks = [(o,t) for o in aircraft if o.animation_data for t in o.animation_data.nla_tracks]
    results = []
    for control in controls:
        clip = control['clip']
        selected = [(o,t) for o,t in tracks if t.name == clip]
        for o,t in tracks:
            t.mute = True
        for o in aircraft:
            if o.animation_data:
                o.animation_data.action = None
            o.matrix_basis = rest[o.name]
        for o,t in selected:
            t.mute = False
        samples = []
        for u in [0,.125,.25,.5,.75,.875,1]:
            frame=1+24*u
            scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame))
            bpy.context.view_layer.update()
            max_delta = 0.0
            finite = True
            for o,t in selected:
                matrix = o.matrix_world
                finite = finite and all(math.isfinite(v) for row in matrix for v in row)
                max_delta=max(max_delta,max(abs(matrix[i][j]-rest_world[o.name][i][j]) for i in range(4) for j in range(4)))
            samples.append({'normalized_time':u,'max_target_matrix_delta':max_delta,'finite':finite})
        results.append({'clip':clip,'native_tracks':len(selected),'sampled_times':samples,
                        'result':'PASS' if selected and all(s['finite'] for s in samples) and max(s['max_target_matrix_delta'] for s in samples)>1e-6 else 'FAIL'})
    for o,t in tracks:
        t.mute=True
    for o in aircraft:
        if o.animation_data:o.animation_data.action=None
        o.matrix_basis=rest[o.name]
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return {'method':'Actual imported Blender NLA tracks, seven samples per clip; finite target matrices and actual change required. This is not collision or photographic certification.',
            'clips':results,'result':'PASS' if results and all(r['result']=='PASS' for r in results) else 'FAIL'}


def apply_snapshot(aircraft, sample):
    """Apply exact controller world matrices after disabling native animation drivers."""
    C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
    inv=C.inverted()
    by_name={o.name:o for o in aircraft}
    missing=[]
    for o in aircraft:
        if o.animation_data:
            o.animation_data.action=None
            for t in o.animation_data.nla_tracks:t.mute=True
    # Snapshot node list is the source graph's parent-first traversal.
    for n in sample['nodes']:
        o=by_name.get(n['name'])
        if o is None:
            missing.append(n['name']);continue
        values=n['matrix_world']
        m=Matrix(tuple(tuple(values[c*4+r] for c in range(4)) for r in range(4)))
        o.matrix_world=C@m@inv
        bpy.context.view_layer.update()
    if missing:raise RuntimeError('Controller/Blender node mismatch: '+repr(missing))
    max_error=0.0
    for n in sample['nodes']:
        values=n['matrix_world']
        expected=C@Matrix(tuple(tuple(values[c*4+r] for c in range(4)) for r in range(4)))@inv
        actual=by_name[n['name']].matrix_world
        max_error=max(max_error,max(abs(actual[i][j]-expected[i][j]) for i in range(4) for j in range(4)))
    if max_error>2e-5:raise RuntimeError('Controller pose conversion error: '+str(max_error))
    return max_error


def main():
    a = cli()
    root = a.root.resolve()
    path = a.input or root/'models'/f'{a.model}.glb'
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=1.0
    bpy.context.scene.unit_settings.length_unit='METERS'
    bpy.context.scene.render.fps=24
    bpy.context.scene.frame_start=1
    bpy.context.scene.frame_end=25
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_location=Vector((0,0,4))
                area.spaces.active.region_3d.view_distance=48
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
        'native_units':'metres; +Z up; nose +Y; scene unit scale 1',
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
    controls=json.loads((root/'articulation'/f'{a.model}.json').read_text())['controls']
    report['native_animation_evaluation']=native_clip_checks(aircraft,controls)
    if report['native_animation_evaluation']['result']!='PASS':
        (qa/f'{a.model}-blender.json').write_text(json.dumps(report,indent=2)+'\n')
        raise RuntimeError('A native imported animation clip failed sampled evaluation')
    # Native .blend is saved with the model, its actual imported NLA clips and packed maps.
    out = root/'editable';out.mkdir(exist_ok=True)
    for image in bpy.data.images:
        if not image.packed_file:
            try:image.pack()
            except RuntimeError:pass
    bpy.ops.wm.save_as_mainfile(filepath=str(out/f'{a.model}-r0002.blend'),compress=True)
    report['blend_path']=f'editable/{a.model}-r0002.blend'
    report['blend_sha256']=hashlib.sha256((out/f'{a.model}-r0002.blend').read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(out/f'{a.model}-r0002.blend'))
    aircraft=list(bpy.context.scene.objects)
    report['blend_reopen']={'result':'PASS','objects':len(aircraft),'actions':len(bpy.data.actions),'packed_images':all(bool(i.packed_file) for i in bpy.data.images)}
    if len(aircraft)!=report['objects'] or len(bpy.data.actions)!=report['actions'] or not report['blend_reopen']['packed_images']:
        raise RuntimeError('Native .blend reopen did not preserve the asset')
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
    belly_fill=light('review_belly_inspection_fill',(-16,12,-12),14000,16)
    belly_fill.hide_render=True
    cargo_fill=light('review_cargo_inspection_fill',(0,-23,4),4500,9)
    cargo_fill.hide_render=True
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
       'cargo':((-5,-26,4),(0,-8,2.3),15),
       'entry':((-18,16,7),(-1.5,8,2),17),
       'belly':((-24,25,-12),(0,2,2.5),36),
    }
    rendered=[]
    for label in a.views:
        location,target,scale=views[label]
        camera.location=location;look_at(camera,target);camera.data.ortho_scale=scale
        fname=f'{a.model}-{a.pose}-{label}.png'
        scene.render.filepath=str(previews/fname)
        bpy.ops.render.render(write_still=True)
        rendered.append({'path':'previews/'+fname,'sha256':hashlib.sha256((previews/fname).read_bytes()).hexdigest(),'pose':a.pose,'camera':label})
    report['renders']=rendered
    if a.poses:
        pose_file=qa/f'viewer-poses-{a.model}.json'
        pose_data=json.loads(pose_file.read_text())
        if pose_data['model_sha256']!=sha:raise RuntimeError('Controller pose file is from a different GLB hash; regenerate it')
        report['controller_pose_source']={k:pose_data[k] for k in ['model_sha256','articulation_sha256','controller_sha256','pose_driver_sha256','runtime']}
        report['pose_conversions']=[]
        for sample in pose_data['samples']:
            label=sample['label']
            if label not in a.pose_labels:continue
            err=apply_snapshot(aircraft,sample)
            report['pose_conversions'].append({'pose':label,'max_matrix_error':err,'result':'PASS'})
            pose_views=['hero','cargo','entry'] if label in ['SERVICE','GLOBAL_ACCESS_OPEN'] else (['hero','rear','belly'] if label=='FLYING' else ['hero','rear'])
            for view in pose_views:
                location,target,scale=views[view]
                camera.location=location;look_at(camera,target);camera.data.ortho_scale=scale
                ground.hide_render=(view=='belly')
                belly_fill.hide_render=(view!='belly')
                cargo_fill.hide_render=(view!='cargo')
                fname=f'{a.model}-{label.lower()}-{view}.png'
                scene.render.filepath=str(previews/fname)
                bpy.ops.render.render(write_still=True)
                rendered.append({'path':'previews/'+fname,'sha256':hashlib.sha256((previews/fname).read_bytes()).hexdigest(),'pose':label,'camera':view})
                ground.hide_render=False
                belly_fill.hide_render=True
                cargo_fill.hide_render=True
    report['render_runtime']='Blender Cycles CPU'
    (qa/f'{a.model}-blender.json').write_text(json.dumps(report,indent=2)+'\n')
    print('claude-design native review complete',a.model,sha,flush=True)


if __name__=='__main__':main()
