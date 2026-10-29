#!/usr/bin/env python3
"""claude-design: isolated source, native editable files and four r0004 packages.

Run only after the aircraft/component geometry has been frozen. The supplied
master hash is a guard against packaging a moving candidate, not a build input.
The isolated component builders never read an aircraft or use the network.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import numpy as np
from family_glb import access, read_glb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
IDS = ('hose-drogue-left', 'hose-drogue-right', 'fulton-yoke', 'jato-kit')
SOURCES = ('gltf_core.py', 'build_family.py', 'family_glb.py',
           'loadout_components.py', 'gun_components.py', 'eoir_component.py')
DEFAULT_BLENDER = '/workspace/scratch/ebccaf89de48/claude-design-tools/blender-4.5.15-linux-x64/blender'
TOLERANCE = 1e-5


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


BUILD_SOURCE = r'''#!/usr/bin/env python3
"""Rebuild this component without an aircraft file, adjacent package or network."""
from pathlib import Path
import argparse, copy, json, sys

NETWORK_ATTEMPTS=[]
ASSET_READS=[]
def isolated_audit(event,args):
    if event in {'socket.connect','socket.connect_ex','socket.getaddrinfo','socket.sendto'}:
        NETWORK_ATTEMPTS.append(event)
        raise RuntimeError('Component rebuilding has no network dependency: '+event)
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        path=str(args[0]);mode=str(args[1]) if len(args)>1 else ''
        if path.lower().endswith(('.glb','.gltf','.blend')) and ('r' in mode or mode=='None'):
            ASSET_READS.append(path)
            raise RuntimeError('Standalone builder must not read a prebuilt asset: '+path)
sys.addaudithook(isolated_audit)

from build_family import Model
from family_glb import subset_component
from loadout_components import add_tanker_pod, add_skyhook, add_jato

def main():
    here=Path(__file__).resolve().parent
    p=argparse.ArgumentParser()
    p.add_argument('--output-dir',type=Path,default=here.parent/'rebuilt')
    a=p.parse_args();out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((here/'component.json').read_text())
    m=Model(cfg['id'],cfg['label'],[])
    # The shared Model provides the authoring interface. This fresh model has
    # no preserved aircraft images; discard unused placeholder map references.
    for material in m.glb.doc['materials']:material.pop('normalTexture',None)
    if cfg['kind']=='pod':result=add_tanker_pod(m,cfg['side'],[0,0,0])
    elif cfg['kind']=='fulton':result=add_skyhook(m,[0,0,0])
    elif cfg['kind']=='jato':result=add_jato(m)
    else:raise ValueError('Unknown component '+cfg['kind'])
    receipt,controls=subset_component(m,result['component_root'],out/'model.glb',m.controls)
    art=copy.deepcopy(cfg['articulation_template'])
    art.update(file='model.glb',sha256=receipt['sha256'],controls=controls)
    (out/'articulation.json').write_text(json.dumps(art,indent=2)+'\n')
    report={'status':'PASS','component':cfg['id'],'model':receipt,
        'parent_aircraft_dependency':False,'network_dependency':False,
        'blocked_network_attempts':NETWORK_ATTEMPTS,'prebuilt_asset_reads':ASSET_READS,
        'origin':cfg['origin'],'scope':'Fresh procedural Model; only this source directory and installed Python libraries.'}
    (out/'rebuild-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main()
'''


NATIVE_SOURCE = r'''#!/usr/bin/env python3
"""Import the actual component GLB, exercise native object/morph actions, save/reopen."""
from pathlib import Path
import argparse, hashlib, json, math, struct, sys
import bpy

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def document(p):
    b=Path(p).read_bytes();length=struct.unpack_from('<I',b,12)[0]
    return json.loads(b[20:20+length])
def flat(m):return [float(v)for row in m for v in row]
def delta(a,b):return max((abs(x-y)for x,y in zip(a,b)),default=0.)
def owners(objects):
    for o in objects:
        if o.animation_data:yield o,o.name,'object'
        if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data:
            yield o.data.shape_keys,o.name,'shape_keys'
def inventory(objects):
    return {'objects':sorted((o.name,o.type,o.parent.name if o.parent else None)for o in objects),
      'actions':sorted((a.name,len(a.slots))for a in bpy.data.actions),
      'shape_keys':sorted((o.name,len(o.data.shape_keys.key_blocks))for o in objects if o.type=='MESH' and o.data.shape_keys),
      'tracks':sorted((name,kind,t.name,len(t.strips))for owner,name,kind in owners(objects)for t in owner.animation_data.nla_tracks),
      'vertices':sum(len(o.data.vertices)for o in objects if o.type=='MESH')}
def select_clip(objects,clip):
    selected=[]
    for owner,name,kind in owners(objects):
        ad=owner.animation_data;ad.action=None
        for track in ad.nla_tracks:
            match=track.name==clip or any(s.action and s.action.name==clip for s in track.strips)
            track.mute=not match;track.is_solo=False
            if match:
                for strip in track.strips:
                    selected.append({'owner':name,'kind':kind,'track':track.name,
                        'start':float(strip.frame_start),'end':float(strip.frame_end),
                        'action':strip.action.name if strip.action else None})
    return selected
def frame(value):
    whole=math.floor(value);bpy.context.scene.frame_set(whole,subframe=value-whole)
    bpy.context.view_layer.update()
def snapshot(objects):
    return {o.name:{'basis':flat(o.matrix_basis),'weights':[float(k.value)for k in list(o.data.shape_keys.key_blocks)[1:]]
        if o.type=='MESH' and o.data.shape_keys else []}for o in objects}
def evaluated_vertices(obj):
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    values=[float(v)for vert in mesh.vertices for v in vert.co]
    evaluated.to_mesh_clear();return values
def main():
    p=argparse.ArgumentParser();p.add_argument('--component-dir',type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.component_dir.resolve()
    source=root/'model.glb';doc=document(source);cfg=json.loads((root/'source/component.json').read_text())
    assert sha(source)==cfg['frozen_model_sha256'],'Frozen model changed'
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source))
    objects=list(bpy.context.scene.objects);by={o.name:o for o in objects}
    scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    scene['jcnc_component_id']=cfg['id'];scene['jcnc_model_sha256']=sha(source)
    scene['jcnc_origin']=cfg['origin'];scene['jcnc_articulation']=json.dumps(json.loads((root/'articulation.json').read_text()))
    scene['jcnc_timeline']='Actual imported normalized glTF clip, NLA frames 1..25 at 24fps. Physical presentation duration is in articulation.json.'
    clips=[];all_ok=True
    sample_times=[0,.125,.25,.5,.75,.875,1]
    for clip in doc.get('animations',[]):
        selected=select_clip(objects,clip['name']);assert selected,'No imported NLA strips for '+clip['name']
        start=min(s['start']for s in selected);end=max(s['end']for s in selected)
        morph_names=sorted({doc['nodes'][c['target']['node']]['name']for c in clip['channels']if c['target']['path']=='weights'})
        frame(start);rest=snapshot(objects);rest_vertices={n:evaluated_vertices(by[n])for n in morph_names}
        samples=[];maxima={};morph_maxima={n:0. for n in morph_names}
        for t in sample_times:
            frame(start+(end-start)*t);snap=snapshot(objects)
            per_channel={}
            for c in clip['channels']:
                name=doc['nodes'][c['target']['node']]['name'];kind=c['target']['path'];key=name+':'+kind
                if name not in by:raise KeyError('Missing native node '+name)
                value=delta(snap[name]['weights'],rest[name]['weights']) if kind=='weights' else delta(snap[name]['basis'],rest[name]['basis'])
                per_channel[key]=value;maxima[key]=max(maxima.get(key,0.),value)
            for n in morph_names:morph_maxima[n]=max(morph_maxima[n],delta(evaluated_vertices(by[n]),rest_vertices[n]))
            samples.append({'normalized_time':t,'frame':start+(end-start)*t,'max_channel_delta':max(per_channel.values(),default=0),
                'morph_weights':{n:snap[n]['weights']for n in morph_names}})
        frame(start);reset=snapshot(objects)
        reset_delta=max((max(delta(reset[n]['basis'],rest[n]['basis']),delta(reset[n]['weights'],rest[n]['weights']))for n in rest),default=0.)
        moving=all(v>1e-6 and math.isfinite(v)for v in maxima.values())
        morph_ok=all(v>1e-6 and math.isfinite(v)for v in morph_maxima.values())
        ok=moving and morph_ok and reset_delta<1e-6;all_ok=all_ok and ok
        clips.append({'clip':clip['name'],'status':'PASS'if ok else'FAIL','expected_channels':len(clip['channels']),
            'native_object_tracks':sum(s['kind']=='object'for s in selected),'native_shape_key_tracks':sum(s['kind']=='shape_keys'for s in selected),
            'channel_peak_deltas':maxima,'morph_local_vertex_peak_deltas_m':morph_maxima,'samples':samples,
            'reset_max_delta':reset_delta,'frame_range':[start,end]})
    defaults={n['name']:list(by[n['name']].scale)for n in doc['nodes']if '_BASKET_'in n['name']and n.get('extras',{}).get('loadout_module_root')}
    basket_ok=all(all(abs(v-(0 if name.endswith('_LOW')else 1))<1e-7 for v in scale)for name,scale in defaults.items())
    assert basket_ok,defaults
    first=doc['animations'][0]['name'];selected=select_clip(objects,first);start=min(s['start']for s in selected);end=max(s['end']for s in selected)
    scene.frame_start=round(start);scene.frame_end=round(end);frame(start)
    for action in bpy.data.actions:action.use_fake_user=True
    for im in bpy.data.images:
        if im.type not in {'RENDER_RESULT','COMPOSITING'} and not im.packed_file:im.pack()
    expected_inventory=inventory(objects);object_names=[o.name for o in objects]
    path=root/'editable.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(path));objects=[bpy.data.objects[n]for n in object_names]
    reopened=inventory(objects)==expected_inventory and bpy.context.scene['jcnc_model_sha256']==sha(source)
    packed=all(im.packed_file for im in bpy.data.images if im.type not in {'RENDER_RESULT','COMPOSITING'})
    report={'author':'claude-design','component':cfg['id'],'model_sha256':sha(source),
        'status':'PASS'if all_ok and reopened and packed and basket_ok else'FAIL',
        'blender_version':bpy.app.version_string,'import':'PASS','save_reopen':'PASS'if reopened else'FAIL',
        'packed_images':'PASS'if packed else'FAIL','default_basket_scales':defaults,'native_inventory':expected_inventory,
        'clips':clips,'editable_sha256':sha(path),'script_sha256':sha(__file__),
        'scope':'Actual imported object and shape-key NLA action evaluation at seven normalized samples, local evaluated morph vertices, reset, native save/reopen. No continuous collision, browser rendering or Unreal validation.'}
    (root/'native-blender.json').write_text(json.dumps(report,indent=2)+'\n')
    print('COMPONENT_NATIVE',json.dumps({'component':cfg['id'],'status':report['status'],'save_reopen':report['save_reopen']}))
    if report['status']!='PASS':raise RuntimeError('Component native evaluation failed')
if __name__=='__main__':main()
'''


def component_config(cid, root):
    art = json.loads((root / 'articulation.json').read_text())
    kind = 'pod' if cid.startswith('hose-drogue') else 'fulton' if cid == 'fulton-yoke' else 'jato'
    origin = ('C-130 aircraft reference datum; eight bottles retain their installation coordinates. '
              'No aircraft mesh or file dependency.' if kind == 'jato' else
              'Local mounting datum at [0,0,0]; +X right, +Y up, forward -Z; metres.')
    cfg = {'id': cid, 'label': art['label'], 'kind': kind, 'origin': origin,
           'basis': '+X right,+Y up,nose -Z', 'units': 'metres',
           'frozen_model_sha256': sha(root / 'model.glb'), 'articulation_template': art,
           'parent_aircraft_dependency': False, 'external_network_dependency': False}
    if kind == 'pod':
        cfg['side'] = cid.rsplit('-', 1)[1]
        cfg['default_basket'] = 'high'
    return cfg


def snapshot_source(cid, root):
    out = root / 'source'
    out.mkdir(parents=True, exist_ok=True)
    for name in SOURCES:
        shutil.copy2(HERE / name, out / name)
    # The included general authoring interface also has an unused aircraft
    # CLI repository locator. Remove its folder-depth assumption so importing
    # Model works even when the independent package is extracted at /tmp/foo.
    interface = out / 'build_family.py'
    interface.write_text(interface.read_text().replace('REPO=HERE.parents[3]',
        'REPO=HERE.parent  # Standalone package: aircraft CLI locator is unused.'))
    (out / 'requirements.txt').write_text('# Reproducible authoring environment; Python 3.12.\nnumpy==2.3.5\nscipy==1.17.0\nPillow==12.3.0\n')
    (out / 'build_component.py').write_text(BUILD_SOURCE)
    (out / 'make_editable.py').write_text(NATIVE_SOURCE)
    save_json(out / 'component.json', component_config(cid, root))
    return {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}


def image_bytes(doc, buf, index):
    im = doc['images'][index]
    assert 'uri' not in im, 'Component must embed its images'
    view = doc['bufferViews'][im['bufferView']]
    start = view.get('byteOffset', 0)
    return bytes(buf[start:start + view['byteLength']])


def normalized_material(doc, buf, value):
    if isinstance(value, list):
        return [normalized_material(doc, buf, v) for v in value]
    if not isinstance(value, dict):
        return value
    out = {}
    for key, val in value.items():
        if key == 'extras':
            continue
        if key.endswith('Texture') and isinstance(val, dict) and 'index' in val:
            texture = doc['textures'][val['index']]
            binding = copy.deepcopy(val)
            binding['index'] = {'image_sha256': hashlib.sha256(image_bytes(doc, buf, texture['source'])).hexdigest(),
                                'sampler': doc.get('samplers', [])[texture['sampler']] if 'sampler' in texture else None}
            out[key] = binding
        else:
            out[key] = normalized_material(doc, buf, val)
    return out


def compare_models(frozen, rebuilt):
    d1, b1 = read_glb(frozen)
    d2, b2 = read_glb(rebuilt)
    errors = []
    max_delta = 0.
    compared_arrays = 0
    geometry_values = 0
    animation_values = 0

    def compare_array(a, b, label, category):
        nonlocal max_delta, compared_arrays, geometry_values, animation_values
        a = np.asarray(a); b = np.asarray(b)
        compared_arrays += 1
        if category == 'geometry': geometry_values += a.size
        if category == 'animation': animation_values += a.size
        if a.shape != b.shape:
            errors.append(label + ': shape ' + str(a.shape) + ' != ' + str(b.shape))
            return
        diff = float(np.max(np.abs(a.astype(float) - b.astype(float)))) if a.size else 0.
        max_delta = max(max_delta, diff)
        if not np.isfinite(diff) or diff > TOLERANCE:
            errors.append(label + ': maximum absolute delta ' + str(diff))

    by1 = {n['name']: n for n in d1['nodes']}
    by2 = {n['name']: n for n in d2['nodes']}
    if set(by1) != set(by2):
        errors.append('Node-name sets differ: ' + str(sorted(set(by1) ^ set(by2))))
    for name in sorted(set(by1) & set(by2)):
        n1 = by1[name]; n2 = by2[name]
        c1 = [d1['nodes'][i]['name'] for i in n1.get('children', [])]
        c2 = [d2['nodes'][i]['name'] for i in n2.get('children', [])]
        if c1 != c2: errors.append(name + ': hierarchy differs')
        for k, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1]), ('weights', [])]:
            compare_array(n1.get(k, default), n2.get(k, default), name + ':' + k, 'state')
        if ('mesh' in n1) != ('mesh' in n2):
            errors.append(name + ': mesh attachment differs'); continue
        if 'mesh' not in n1: continue
        m1 = d1['meshes'][n1['mesh']]; m2 = d2['meshes'][n2['mesh']]
        if len(m1['primitives']) != len(m2['primitives']):
            errors.append(name + ': primitive count differs'); continue
        for p1, p2 in zip(m1['primitives'], m2['primitives']):
            if p1.get('mode', 4) != p2.get('mode', 4): errors.append(name + ': primitive mode differs')
            indices1 = access(d1, b1, p1['indices']).ravel().astype(int) if 'indices' in p1 else np.arange(d1['accessors'][p1['attributes']['POSITION']]['count'])
            indices2 = access(d2, b2, p2['indices']).ravel().astype(int) if 'indices' in p2 else np.arange(d2['accessors'][p2['attributes']['POSITION']]['count'])
            if set(p1['attributes']) != set(p2['attributes']): errors.append(name + ': attribute set differs')
            for k in set(p1['attributes']) & set(p2['attributes']):
                compare_array(access(d1, b1, p1['attributes'][k])[indices1], access(d2, b2, p2['attributes'][k])[indices2], name + ':' + k, 'geometry')
            t1 = p1.get('targets', []); t2 = p2.get('targets', [])
            if len(t1) != len(t2): errors.append(name + ': morph target count differs')
            for i, (a, b) in enumerate(zip(t1, t2)):
                if set(a) != set(b): errors.append(name + ': morph attribute set differs')
                for k in set(a) & set(b):
                    compare_array(access(d1, b1, a[k])[indices1], access(d2, b2, b[k])[indices2], name + ':morph' + str(i) + ':' + k, 'geometry')
            mat1 = normalized_material(d1, b1, d1['materials'][p1['material']])
            mat2 = normalized_material(d2, b2, d2['materials'][p2['material']])
            if mat1 != mat2: errors.append(name + ': material or embedded texture binding differs')

    def animation_channels(doc, buf):
        result = {}
        for clip in doc.get('animations', []):
            for channel in clip['channels']:
                sampler = clip['samplers'][channel['sampler']]
                key = (clip['name'], doc['nodes'][channel['target']['node']]['name'], channel['target']['path'])
                if key in result: raise ValueError('Duplicate animation channel ' + str(key))
                result[key] = (sampler.get('interpolation', 'LINEAR'), access(doc, buf, sampler['input']), access(doc, buf, sampler['output']))
        return result
    a1 = animation_channels(d1, b1); a2 = animation_channels(d2, b2)
    if set(a1) != set(a2): errors.append('Animation channel set differs')
    for key in sorted(set(a1) & set(a2)):
        if a1[key][0] != a2[key][0]: errors.append(str(key) + ': interpolation differs')
        compare_array(a1[key][1], a2[key][1], str(key) + ':times', 'animation')
        compare_array(a1[key][2], a2[key][2], str(key) + ':values', 'animation')
    basket_defaults = {n: x.get('scale', [1, 1, 1]) for n, x in by2.items() if '_BASKET_' in n and x.get('extras', {}).get('loadout_module_root')}
    for name, scale in basket_defaults.items():
        expected = [0, 0, 0] if name.endswith('_LOW') else [1, 1, 1]
        if scale != expected: errors.append(name + ': incorrect default visibility')
    if any('FENDING_LINE' in n for n in by2): errors.append('Host-specific Fulton fending line leaked into independent yoke')
    if any('uri' in x for x in d2.get('images', []) + d2.get('buffers', [])): errors.append('External resource reference')
    report = {'status': 'PASS' if not errors else 'FAIL', 'frozen_model_sha256': sha(frozen), 'rebuilt_model_sha256': sha(rebuilt),
              'byte_identical': Path(frozen).read_bytes() == Path(rebuilt).read_bytes(),
              'comparison': 'Expanded indexed geometry attributes, morph targets, node hierarchy/rest TRS, material/image bindings and every animation input/output.',
              'absolute_tolerance': TOLERANCE, 'relative_tolerance': 0, 'maximum_absolute_delta': max_delta,
              'compared_arrays': compared_arrays, 'geometry_scalar_values': geometry_values, 'animation_scalar_values': animation_values,
              'nodes': len(by2), 'meshes': len(d2['meshes']), 'animation_channels': len(a2),
              'default_basket_scales': basket_defaults, 'errors': errors,
              'qualification': 'Semantic equivalence within 0.00001; floating point origin baking and metadata can prevent identical GLB bytes.'}
    return report


def isolation_test(cid, root):
    with tempfile.TemporaryDirectory(prefix='c130-r4-component-isolated-') as tmp:
        tmp = Path(tmp)
        shutil.copytree(root / 'source', tmp / 'source', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        assert not list(tmp.rglob('*.glb')) and not list(tmp.rglob('*.blend'))
        env = dict(os.environ); env.pop('PYTHONPATH', None)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        process = subprocess.run([sys.executable, str(tmp / 'source/build_component.py'), '--output-dir', str(tmp / 'rebuilt')],
                                 cwd=tmp, env=env, capture_output=True, text=True)
        if process.returncode:
            raise RuntimeError(cid + ' isolated build failed:\n' + process.stdout + '\n' + process.stderr)
        report = compare_models(root / 'model.glb', tmp / 'rebuilt/model.glb')
        receipt = json.loads((tmp / 'rebuilt/rebuild-receipt.json').read_text())
        rebuilt_art = json.loads((tmp / 'rebuilt/articulation.json').read_text())
        expected_art = json.loads((root / 'articulation.json').read_text())
        controls_equal = rebuilt_art['controls'] == expected_art['controls']
        report.update(component=cid, fresh_directory=True, prebuilt_input_files=0,
                      parent_aircraft_dependency=False, network_guard='Python audit hook rejects socket connection/DNS/send attempts',
                      attempted_network_calls=receipt['blocked_network_attempts'], prebuilt_asset_reads=receipt['prebuilt_asset_reads'],
                      articulation_controls_equal=controls_equal)
        if not controls_equal:
            report['errors'].append('Articulation controls differ'); report['status'] = 'FAIL'
        save_json(root / 'source-isolation.json', report)
        return report


def extract_textures(root):
    doc, buf = read_glb(root / 'model.glb')
    directory = root / 'textures'; directory.mkdir(exist_ok=True)
    images = []
    for i, image in enumerate(doc.get('images', [])):
        suffix = '.png' if image.get('mimeType') == 'image/png' else '.jpg' if image.get('mimeType') == 'image/jpeg' else '.bin'
        name = re.sub('[^A-Za-z0-9_-]', '_', image.get('name', 'image_' + str(i))) + suffix
        path = directory / name; path.write_bytes(image_bytes(doc, buf, i))
        images.append({'index': i, 'name': image.get('name'), 'file': 'textures/' + name,
                       'sha256': sha(path), 'bytes': path.stat().st_size, 'mimeType': image.get('mimeType')})
    (directory / 'README.md').write_text('# Component materials\n\n' + (
        'The original component image payloads are embedded in model.glb and copied here byte for byte. The editable Blender file packs its images.\n' if images else
        'This component uses named PBR material colors and scalar roughness/metallic values. It has no raster texture dependency.\n'))
    save_json(root / 'materials.json', {'materials': doc['materials'], 'textures': doc.get('textures', []), 'images': images,
                                      'embedded_resources': True, 'source': 'model.glb'})
    return images


def readme(cid, root, isolation, native):
    cfg = component_config(cid, root)
    detail = {
        'hose-drogue-left': 'The high-speed basket is active at rest; the low-speed alternative is present with its configuration scale zero. Change the basket selector in the independent inspector to preview either variant. Hose and woven fabric use actual morph targets; coupling and rib pivots use transform tracks.',
        'hose-drogue-right': 'The high-speed basket is active at rest; the low-speed alternative is present with its configuration scale zero. Change the basket selector in the independent inspector to preview either variant. Hose and woven fabric use actual morph targets; coupling and rib pivots use transform tracks.',
        'fulton-yoke': 'The package includes the local nose yoke, its supports, hinged arms and pickup alignment socket. Wing-to-nose fending lines are airframe installation parts and are deliberately outside this reusable yoke subtree.',
        'jato-kit': 'Eight historical visual bottles, their mounting brackets and a visual exhaust cycle are included. The complete kit intentionally retains the aircraft reference datum so its paired bottle groups can be installed as one module. Individual bottle nodes remain separately editable.'
    }[cid]
    text = f'''# {cfg['label']} — r0004

Author: **claude-design**. Independent reusable visual component, tagged `level 1`.

{detail}

## Files and use

- `model.glb`: compact standalone geometry, materials, embedded resources and real animation channels.
- `articulation.json`: named controls and presentation durations.
- `inspector.html`: self-contained component inspector; open in a WebGL2 browser. It includes Actuate everything, pause, reverse, reset, individual controls and surface/wireframe/X-ray views.
- `editable.blend`: actual GLB imported into Blender {native['blender_version']}, with editable meshes, named pivots, materials and imported object/shape-key actions. Saved and reopened during validation.
- `source/`: complete local Python source and configuration for a fresh rebuild; no aircraft GLB or external project is required.
- `source-isolation.json`, `native-blender.json`, `inspector.manifest.json`: separate source, native and inspector evidence.
- `materials.json` and `textures/`: material bindings and any exact embedded image payloads.
- `manifest.json`: file hashes, datum and acceptance scope.

## Datum and timeline

{cfg['origin']}

glTF basis is +X right, +Y up, forward -Z, in metres. Blender performs its standard glTF basis conversion to +Z up. The imported normalized animation occupies NLA frames 1–25 at 24 fps; runtime presentation duration comes from `articulation.json`. Scrub the timeline to evaluate the preserved native animation. The saved file starts in the canonical rest state.

## Rebuild independently

Use Python 3.12 with the versions in `source/requirements.txt` installed. From this component folder:

```sh
python source/build_component.py --output-dir rebuilt
```

The command creates `rebuilt/model.glb`, `rebuilt/articulation.json` and `rebuilt/rebuild-receipt.json`. The builder creates a fresh empty authoring model and extracts only this component subtree. It has a network audit guard and rejects attempts to read prebuilt GLB, glTF or Blender assets. Shared utility source is included to resolve imports; the aircraft build entry point is not called.

To recreate the native editable file from the delivered model, use Blender 4.5 LTS:

```sh
blender --background --factory-startup --python source/make_editable.py -- --component-dir .
```

## Verification and limits

Isolated rebuilding passed with no prebuilt model input and no network calls. Every expanded geometry attribute, morph target, node hierarchy/rest transform, material/image binding and animation input/output was compared with the delivered component. Maximum absolute numeric difference: **{isolation['maximum_absolute_delta']:.9g}**; tolerance: **0.00001**, relative tolerance zero. The result is semantic equivalence; metadata and local origin baking can produce different GLB bytes.

Blender import, seven-sample native object and shape-key animation evaluation, actual local morph vertex movement, reset and save/reopen passed. These are visible game representations informed by public references. Exact dimensions, travel, flexible material behavior and effect timing are artist authored. Browser/WebGL rendering, continuous physical clearance, photographic acceptance and native Unreal acceptance are not established by these component checks. See each evidence file for its exact scope.
'''
    (root / 'README.md').write_text(text)


def make_manifest(cid, root, isolation, native, source_hashes, images):
    inspector = json.loads((root / 'inspector.manifest.json').read_text())
    assert inspector['model_sha256'] == sha(root / 'model.glb'), cid + ': stale inspector model'
    assert inspector['sha256'] == sha(root / 'inspector.html'), cid + ': stale inspector file'
    assert inspector['articulation_sha256'] == sha(root / 'articulation.json'), cid + ': stale inspector controls'
    cfg = component_config(cid, root)
    files = []
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.name != 'manifest.json' and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.blend1'}:
            files.append({'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    manifest = {'schema': 'jcnc.independent-component/1.0', 'author': 'claude-design', 'revision': 'r0004',
                'component_id': cid, 'tags': ['level 1'], 'units': 'metres', 'basis': cfg['basis'], 'origin': cfg['origin'],
                'model': {'file': 'model.glb', 'sha256': sha(root / 'model.glb'), 'bytes': (root / 'model.glb').stat().st_size},
                'parent_aircraft_dependency': False, 'external_network_dependency': False,
                'source_copy_adaptations': {'build_family.py': 'Unused aircraft CLI repository locator changed from HERE.parents[3] to HERE.parent so Model imports at any package directory depth; geometry and authoring functions are unchanged.'},
                'source_files': source_hashes, 'embedded_images': images, 'editable': {'file': 'editable.blend', 'sha256': sha(root / 'editable.blend')},
                'verification': {'source_isolation': isolation['status'], 'semantic_rebuild_tolerance': TOLERANCE,
                                 'byte_identical_rebuild': isolation['byte_identical'], 'native_blender': native['status'],
                                 'inspector': inspector['verification']['status'], 'browser_rendering': 'NOT_RUN', 'native_unreal': 'NOT_RUN',
                                 'photographic_acceptance': 'NOT_ACCEPTED', 'continuous_clearance': 'NOT_PROVEN'},
                'files': files}
    save_json(root / 'manifest.json', manifest)
    return manifest


def make_package(cid, root):
    packages = ROOT / 'packages'; packages.mkdir(exist_ok=True)
    output = packages / (cid + '-r0004.zip')
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for p in sorted(root.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.blend1'}:
                archive.write(p, cid + '/' + p.relative_to(root).as_posix())
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        manifest = json.loads(archive.read(cid + '/manifest.json'))
        for entry in manifest['files']:
            assert hashlib.sha256(archive.read(cid + '/' + entry['path'])).hexdigest() == entry['sha256']
    return {'file': output.relative_to(ROOT).as_posix(), 'bytes': output.stat().st_size, 'sha256': sha(output), 'zip_crc_and_manifest_hashes': 'PASS'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--master-sha256', required=True)
    p.add_argument('--blender', default=DEFAULT_BLENDER)
    p.add_argument('--components', nargs='+', choices=IDS, default=list(IDS))
    p.add_argument('--package-only', action='store_true', help='Refresh manifests/archives after inspector-only updates; reuse frozen source/native evidence.')
    a = p.parse_args()
    assert sha(ROOT / 'models/c130-family.glb') == a.master_sha256, 'Master geometry changed before packaging'
    frozen = {cid: sha(ROOT / 'components' / cid / 'model.glb') for cid in a.components}
    source_initial = {name: sha(HERE / name) for name in SOURCES}
    reports = []
    for cid in a.components:
        root = ROOT / 'components' / cid
        assert sha(root / 'model.glb') == frozen[cid]
        if a.package_only:
            source_hashes = {p.name: sha(p) for p in sorted((root / 'source').iterdir()) if p.is_file()}
            isolation = json.loads((root / 'source-isolation.json').read_text())
            native = json.loads((root / 'native-blender.json').read_text())
            images = json.loads((root / 'materials.json').read_text())['images']
            assert isolation['frozen_model_sha256'] == frozen[cid] and native['model_sha256'] == frozen[cid], 'Stale component evidence'
        else:
            assert {name: sha(HERE / name) for name in SOURCES} == source_initial, 'Shared source changed during packaging'
            source_hashes = snapshot_source(cid, root)
            isolation = isolation_test(cid, root)
            if isolation['status'] != 'PASS':
                raise RuntimeError(cid + ' semantic isolation failed: ' + json.dumps(isolation['errors']))
            process = subprocess.run([a.blender, '--background', '--factory-startup', '--python', str(root / 'source/make_editable.py'), '--', '--component-dir', str(root)], capture_output=True, text=True)
            (root / 'native-blender.log').write_text(process.stdout + '\n' + process.stderr)
            if process.returncode:
                raise RuntimeError(cid + ' Blender failed; see ' + str(root / 'native-blender.log'))
            native = json.loads((root / 'native-blender.json').read_text())
            assert native['status'] == 'PASS', cid + ' native evaluation failed'
            images = extract_textures(root)
            readme(cid, root, isolation, native)
        assert sha(root / 'model.glb') == frozen[cid], 'Component changed during packaging'
        make_manifest(cid, root, isolation, native, source_hashes, images)
        archive = make_package(cid, root)
        reports.append({'component': cid, 'model_sha256': frozen[cid], 'source_isolation': isolation, 'native_blender': {
            'status': native['status'], 'save_reopen': native['save_reopen'], 'blender_version': native['blender_version'],
            'object_tracks': sum(c['native_object_tracks'] for c in native['clips']),
            'shape_key_tracks': sum(c['native_shape_key_tracks'] for c in native['clips']),
            'editable_sha256': native['editable_sha256']}, 'package': archive})
        print(json.dumps({'component': cid, 'status': 'PASS', 'model_sha256': frozen[cid], 'rebuild_max_delta': isolation['maximum_absolute_delta'], 'package': archive}), flush=True)
    assert sha(ROOT / 'models/c130-family.glb') == a.master_sha256, 'Master changed during packaging'
    report = {'status': 'PASS', 'author': 'claude-design', 'revision': 'r0004', 'master_model_sha256': a.master_sha256,
              'script_sha256': sha(__file__), 'source_snapshots': source_initial, 'components': reports,
              'source_copy_adaptations': {'build_family.py': 'Only unused aircraft CLI repository locator changes to HERE.parent, allowing arbitrary extraction directory depth. Geometry/authoring functions unchanged.'},
              'scope': 'Four new independent components. Parent aircraft required only as a frozen delivery identity guard, never as source input. Reused r0003 gun/sensor components are packaged separately.'}
    save_json(ROOT / 'qa/component-source-isolation.json', report)


if __name__ == '__main__':
    main()
