#!/usr/bin/env python3
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
