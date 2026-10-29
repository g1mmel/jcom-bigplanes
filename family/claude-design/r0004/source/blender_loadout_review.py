"""claude-design / cg47: native import/reopen and exact live-loadout renders.

Uses exported Three.js matrices AND flexible-mesh weights. Inactive loadout
modules stay hidden. No substitute geometry or generated reference imagery.
"""
from pathlib import Path
import argparse,hashlib,json,re,sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import blender_systems_review as R

def hashfile(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

CAMERAS={
 'hero':{'position':[-36,21,-36],'target':[0,3,0],'scale':49},
 'port':{'position':[-42,6,0],'target':[0,3,0],'scale':34},
 'cargo':{'position':[-7,5,17],'target':[0,2.4,5.3],'scale':11},
 'ramp-belly':{'position':[-5,-4,11],'target':[0,2.2,6.6],'scale':8},
 'ramp-side':{'position':[-12,2.7,6.8],'target':[0,2.2,6.6],'scale':7},
 'tanker':{'position':[-23,9,24],'target':[-12,3,5.5],'scale':24},
 'skyhook':{'position':[-13,9,-26],'target':[0,3,-14.4],'scale':15},
 'jato':{'position':[-9,5,10],'target':[-1.4,2.8,4.9],'scale':8},
 'receiver':{'position':[-3,8,-14],'target':[0,4.5,-11.85],'scale':3.8},
 'gun30':R.DEFAULT_CAMERAS['gun30-exterior'],
 'gun105':R.DEFAULT_CAMERAS['gun105-exterior'],
}

def visibility_and_morph(objects,sample):
    by={o.name:o for o in objects}
    for o in objects:by.setdefault(re.sub(r'[\[\]\.:/]','',re.sub(r'\s','_',o.name)),o)
    shown=hidden=0;morphs=[]
    for n in sample['nodes']:
        o=by.get(n['name'])
        if not o:continue
        o.hide_render=not n.get('effective_visible',True)
        o.hide_set(not n.get('effective_visible',True))
        if o.type=='MESH':
            if o.hide_render:hidden+=1
            else:shown+=1
            weights=n.get('morphTargetInfluences')
            shape=o.data.shape_keys
            if weights is not None and shape:
                for block,value in zip(list(shape.key_blocks)[1:],weights):block.value=float(value)
                morphs.append({'node':o.name,'weights':weights})
    bpy.context.view_layer.update()
    return {'visible_meshes':shown,'hidden_option_meshes':hidden,'morphs':morphs}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--quick',action='store_true');p.add_argument('--views',nargs='*');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    root=a.root.resolve();glb=root/'models/c130-family.glb';poses=root/'qa/viewer-poses-c130-family.json'
    data=json.loads(poses.read_text());assert data['model_sha256']==hashfile(glb)
    for field,rel in [('articulation_sha256','articulation/c130-family.json'),('controller_sha256','viewer/controller.mjs'),('pose_driver_sha256','viewer/pose-driver.mjs'),('loadout_catalog_sha256','loadouts/catalog.json')]:assert data[field]==hashfile(root/rel),(field,'stale')
    samples={s['label']:s for s in data['samples']}
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(glb))
    objects=list(bpy.context.scene.objects);names=[o.name for o in objects]
    # Configuration visibility is distinct from mechanical scale. Evaluate
    # imported clips at canonical module scale, as the live viewer does; then
    # restore each actual loadout's visibility for every render and saved scene.
    source=R.glb_document(glb)
    module_names={n['name']for n in source['nodes']if n.get('extras',{}).get('loadout_module_root')}
    for o in objects:
        if o.name in module_names:o.scale=(1,1,1)
    bpy.context.view_layer.update();rest=R.capture_rest(objects)
    R.restore(objects,rest);R.CLIP_SCOPE=re.compile('.*')
    clips=[x['name']for x in source.get('animations',[])]
    native=R.native_checks(objects,rest,clips)
    native['scope']='Eight samples per imported action at canonical module scale. Tests named NLA object actions and actual matrix/vertex motion; per-loadout render visibility and flexible morph weights are checked separately. No collision or real operational certification.'
    print('claude-design NATIVE_CLIPS',native.get('result'),flush=True)
    for action in bpy.data.actions:action.use_fake_user=True
    args=argparse.Namespace(samples=12 if a.quick else 24,resolution=1100,height_ratio=.70)
    camera,lights,label=R.review_scene(args)
    R.apply_snapshot(objects,rest,samples['PARKED']);visibility_and_morph(objects,samples['PARKED'])
    R.configure_view(args,CAMERAS['hero'],objects,camera,lights,label,'C-130 modular family / r0004 / editable master')
    visibility_and_morph(objects,samples['PARKED'])
    for im in bpy.data.images:
        if im.type not in {'RENDER_RESULT','COMPOSITING'} and not im.packed_file:
            try:im.pack()
            except RuntimeError:pass
    scene=bpy.context.scene;scene['jcnc_model_sha256']=hashfile(glb);scene['jcnc_loadout_catalog']=json.dumps(json.loads((root/'loadouts/catalog.json').read_text()))
    path=root/'editable/C130-family-r0004.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    inventory=R.action_inventory(objects);actions=sorted(x.name for x in bpy.data.actions)
    bpy.ops.wm.open_mainfile(filepath=str(path));objects=[bpy.data.objects[n]for n in names];rest=R.capture_rest(objects)
    reopen=(R.action_inventory(objects)==inventory and sorted(x.name for x in bpy.data.actions)==actions and bpy.context.scene['jcnc_model_sha256']==hashfile(glb))
    assert reopen
    camera=bpy.data.objects['SYSTEM_REVIEW_CAMERA'];lights=[bpy.data.objects['SYSTEM_REVIEW_'+x]for x in ('KEY','FILL','RIM','INTERIOR_INSPECTION')];label=bpy.data.objects['SYSTEM_REVIEW_LABEL']
    tasks=[('transport-h','LOADOUT_TRANSPORT_H','hero'),('transport-j','LOADOUT_TRANSPORT_J','hero'),('gunship-j','LOADOUT_GUNSHIP_J','hero'),('tanker-j','LOADOUT_TANKER_J','hero'),('tanker-deployed','LOADOUT_TANKER_J_DEPLOYED','tanker'),('fulton-deployed','LOADOUT_RECOVERY_E_DEPLOYED','skyhook'),('jato-active','LOADOUT_LEGACY_JATO_JATO_25','jato'),('cargo-open','SERVICE','cargo'),('gun30-panel','LOADOUT_GUNSHIP_J','gun30'),('gun105-panel','LOADOUT_GUNSHIP_J','gun105')]
    tasks += [('ramp-closed-belly','PARKED','ramp-belly'),('ramp-closed-side','PARKED','ramp-side'),('fulton-folded','LOADOUT_RECOVERY_E','skyhook')]
    if a.views:tasks=[t for t in tasks if t[0]in a.views]
    report={'author':'claude-design','input_sha256':hashfile(glb),'snapshots_sha256':hashfile(poses),'script_sha256':hashfile(__file__),'blender_version':bpy.app.version_string,'native_animation_evaluation':native,'import':'PASS','save_reopen':'PASS' if reopen else 'FAIL','editable':{'path':str(path.relative_to(root)),'sha256':hashfile(path)},'renders':[],'browser_rendering':'NOT_RUN','native_unreal':'NOT_RUN','continuous_clearance':'NOT_PROVEN'}
    for name,pose,view in tasks:
        if pose not in samples:raise KeyError('Missing requested exact controller pose '+pose)
        R.apply_snapshot(objects,rest,samples[pose]);R.configure_view(args,CAMERAS[view],objects,camera,lights,label,'C-130 / r0004 / '+name+'\nActual export / '+pose)
        state=visibility_and_morph(objects,samples[pose]);destination=root/'previews'/('loadout-'+name+'.png');bpy.context.scene.render.filepath=str(destination);bpy.ops.render.render(write_still=True)
        report['renders'].append({'path':str(destination.relative_to(root)),'sha256':hashfile(destination),'pose':pose,'camera':CAMERAS[view],**state})
    report['status']='PASS' if native['result']!='FAIL' else 'FAIL';(root/'qa/native-loadout-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print('claude-design NATIVE_REVIEW',json.dumps({'status':report['status'],'renders':len(report['renders']),'sha256':report['input_sha256']}),flush=True)
if __name__=='__main__':main()
