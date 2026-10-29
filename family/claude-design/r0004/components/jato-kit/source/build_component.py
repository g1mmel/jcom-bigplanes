#!/usr/bin/env python3
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
