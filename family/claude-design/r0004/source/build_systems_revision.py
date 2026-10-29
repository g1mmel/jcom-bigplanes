#!/usr/bin/env python3
"""claude-design: build r0003 gunships and independently reusable visual systems.

The r0002 transport bytes remain the family's unchanged baseline. The original
r0001 geometry stays the input for reproducible gunship assemblies.
"""
from pathlib import Path
import argparse, copy, hashlib, json
import build_family as base
from gun_components import add_gun
from eoir_component import add_sensor
from gltf_core import load_source

def standalone(cid,label,kind):
    m=base.Model(cid,label,[])
    # Component-owned materials must never point to absent aircraft images.
    for mat in m.glb.doc['materials']:mat.pop('normalTexture',None)
    m.glb.doc['nodes'][0]['name']='INDEPENDENT_SYSTEM_ROOT'
    m.glb.doc['nodes'][0]['extras'].update(component=True,aircraft_dependency=False)
    if kind=='sensor':add_sensor(m,'eoir',[0,0,0])
    else:add_gun(m,'gun105' if kind=='105' else 'gun30',[0,0,0],large=kind=='105')
    result=base.save_model(m,component=True)
    d=base.OUT/'components'/cid
    src=d/'source';src.mkdir(exist_ok=True)
    for name in ['gltf_core.py','gun_components.py','eoir_component.py','component_source.py']:
        (src/name).write_bytes((base.HERE/name).read_bytes())
    (src/'component.json').write_text(json.dumps({'id':cid,'label':label,'kind':kind},indent=2)+'\n')
    (d/'README.md').write_text(f'''# {label}\n\nclaude-design / cg46 · r0003 · original photo-guided game visual component.\n\n`model.glb` is self-contained and includes materials, actual clips and effect geometry. `articulation.json` binds the exported controls. The parent aircraft is not required.\n\nRebuild with `python source/component_source.py` (Python, NumPy, SciPy, Pillow). The generated component is visually approximate; it is not manufacturing data, a targeting system, or a verified operational simulation. Playback timing and case trajectories are authored.\n\nThe independent portable inspector is generated from the revision's pinned local viewer, and is copied beside this file at delivery. Source master is the Python component authoring code; a native editable Blender scene is delivered after import/reopen review.\n\nNative Unreal, exact photographic acceptance, continuous clearance, damage and runtime performance remain unaccepted. The aircraft installation transform belongs to the family assembly, outside this package.\n''')
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--only',choices=['ac130','ac130j','components','all'],default='all');a=p.parse_args()
    rows=[]
    if a.only!='components':
        packaged_input=base.HERE/'inputs/c130-hercules-unified-r0001.glb'
        input_path=packaged_input if packaged_input.is_file() else base.REPO/'family/r0001/c130-hercules-unified-r0001.glb'
        src,images,h=load_source(input_path,canonical=True)
        assert h==base.INPUT_HASH
        common,surfaces=base.prepare_common(src)
        configs=json.loads((base.HERE/'variants.json').read_text())['variants']
        for cfg in configs:
            mid=cfg['id']
            if mid=='c130' or a.only not in ['all',mid]:continue
            model=base.build_one(mid,cfg['label'],src,images,common,surfaces)
            r=base.save_model(model);rows.append(r)
            (base.OUT/'qa'/f'{mid}-component-inventory.json').write_text(json.dumps(base.component_inventory(model),indent=2)+'\n')
            print('claude-design BUILT',json.dumps(r),flush=True)
    if a.only in ['all','components']:
        for cid,label,kind in [('gau23-visual','GAU-23 family aircraft cannon — visual component','30'),('m102-airborne-visual','Legacy 105 mm aircraft gun — visual component','105'),('eoir-visual','MX-20-family representative EO/IR visual component','sensor')]:
            r=standalone(cid,label,kind);rows.append(r);print('claude-design COMPONENT',json.dumps(r),flush=True)
    (base.HERE/f'build-systems-{a.only}-receipts.json').write_text(json.dumps({'revision':'r0003','author':'claude-design','original_source_sha256':base.INPUT_HASH,'outputs':rows},indent=2)+'\n')

if __name__=='__main__':main()
