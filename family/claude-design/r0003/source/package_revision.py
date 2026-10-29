#!/usr/bin/env python3
"""Verify the frozen r0003 evidence and inventory exact delivery bytes."""
from pathlib import Path
import argparse, hashlib, json, struct
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
COMPONENTS=['gau23-visual','m102-airborne-visual','eoir-visual']
IDS=['c130','ac130','ac130j']+COMPONENTS
BASELINE='7bfc25e94d4b99900db6f25fa731bc867111dd5debb3a763aa7b619ee86b4146'
INPUT='ad3b1ff76fcff48dbb7dbc4901665f65def89f9db12d56112a00ee86389a0b12'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def read(p):return json.loads((ROOT/p).read_text())
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n')
def modelpath(mid):return Path('components')/mid/'model.glb' if mid in COMPONENTS else Path('models')/(mid+'.glb')
def sidepath(mid):return Path('components')/mid/'articulation.json' if mid in COMPONENTS else Path('articulation')/(mid+'.json')
def gltf(p):
    data=p.read_bytes();n=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+n])
def verify_entry(root,e):
    p=root/e['path'];assert p.is_file(),('missing',str(p))
    assert sha(p)==e['sha256'],('hash',str(p))
    if 'bytes' in e:assert p.stat().st_size==e['bytes'],('bytes',str(p))

def world_matrices(doc):
    worlds={}
    def visit(i,parent):
        n=doc['nodes'][i]
        if 'matrix' in n:m=np.array(n['matrix']).reshape((4,4),order='F')
        else:
            m=np.eye(4);m[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
        worlds[i]=parent@m
        for j in n.get('children',[]):visit(j,worlds[i])
    for i in doc['scenes'][doc.get('scene',0)]['nodes']:visit(i,np.eye(4))
    return worlds

def main():
    a=argparse.ArgumentParser();a.add_argument('--created-utc',default='2026-10-29');args=a.parse_args()
    fmt=read('qa/gltf-validator-summary.json');geo=read('qa/system_geometry_report.json')
    runtime=read('viewer/model-runtime-qa.json');fire=read('viewer/firing-model-qa.json');obstruction=read('viewer/case-obstruction-qa.json')
    portable=read('viewer/portable-manifest.json');portableqa=read('viewer/portable-qa.json')
    assert all(x['status']=='PASS' for x in [fmt,geo,runtime,fire,obstruction,portableqa])
    assert geo['inputs_unchanged_during_audit']
    assert sha(ROOT/'source/inputs/c130-hercules-unified-r0001.glb')==INPUT
    assert runtime['controller_sha256']==sha(ROOT/'viewer/controller.mjs')
    assert runtime['pose_driver_sha256']==sha(ROOT/'viewer/pose-driver.mjs')
    models=[];expected={};documents={}
    for mid in IDS:
        rel=modelpath(mid);path=ROOT/rel;digest=sha(path);expected[mid]=digest
        doc=gltf(path);documents[mid]=doc;side=read(sidepath(mid));assert side['sha256']==digest
        rt=next(x for x in runtime['models'] if x['id']==mid)
        assert rt['model_sha256']==digest and rt['articulation_sha256']==sha(ROOT/sidepath(mid))
        assert rt['reset_max_matrix_error']==0 and rt['bindings']=='PASS'
        native=None;f=None
        if mid=='c130':assert digest==BASELINE
        else:
            f=next(x for x in fmt['models'] if x['id']==mid)
            assert f['sha256']==digest and f['errors']==0 and f['warnings']==0 and f['status']=='PASS'
            g=next(x for x in geo['files'] if x['file']==rel.as_posix())
            assert g['sha256']==digest and g['status']=='PASS'
            native=read('qa/system-review-'+mid+'-r0003-rest.json')
            assert native['status']=='PASS' and native['input_sha256']==digest and native['input_unchanged_during_review']
            assert native['native_animation_evaluation']['result']=='PASS' and native['blend_reopen']['result']=='PASS'
            verify_entry(ROOT,native['editable_blend'])
        models.append({'id':mid,'label':side['label'],'file':rel.as_posix(),'bytes':path.stat().st_size,'sha256':digest,
            'nodes':len(doc['nodes']),'meshes':len(doc['meshes']),'triangles':sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives']),
            'clips':len(doc.get('animations',[])),'controls':len(side['controls']),'articulation':sidepath(mid).as_posix(),
            'editable':native['editable_blend']['path'] if native else None,
            'validation':{'khronos':{'errors':f['errors'],'warnings':f['warnings'],'status':'PASS'} if f else {'status':'UNCHANGED_R0002_BY_HASH'},
                'three_actual_controls':'PASS','native_blender':'PASS' if native else 'UNCHANGED_R0002_BY_HASH','native_unreal':'NOT_RUN','photographic_acceptance':'NOT_ACCEPTED'},
            'unchanged_from_r0002':mid=='c130'})
    assert sum(x['controls'] for x in models)==113
    for report in [fire,obstruction]:
        for row in report['models']:
            assert row.get('sha256',row.get('model_sha256'))==expected[row['id']]
    for iso in geo['source_isolation']:
        assert iso['status']=='PASS' and iso['delivered_sha256']==expected[iso['component']]
        for s in iso['source_files']:
            assert sha(ROOT/'components'/iso['component']/'source'/s['file'])==s['sha256']
    native_paths=[];images=set()
    for path in sorted((ROOT/'qa').glob('system-review-*-r0003-*.json')):
        n=json.loads(path.read_text());assert n['status']=='PASS' and n['input_sha256']==expected[n['asset_id']]
        assert n['script_sha256']==sha(ROOT/'source/blender_systems_review.py')
        verify_entry(ROOT,n['editable_blend']);native_paths.append(path.relative_to(ROOT).as_posix())
        for render in n['renders']:
            verify_entry(ROOT,render)
            with Image.open(ROOT/render['path']) as im:im.verify()
            images.add(render['path'])
    baseline_report=read('qa/system-review-ac130j-r0002-rest.json')
    for render in baseline_report['renders']:
        verify_entry(ROOT,render);images.add(render['path'])
    assert {p.relative_to(ROOT).as_posix() for p in (ROOT/'previews').glob('*.png')}==images,'stale previews'
    assert portable['source_models']==expected
    assert portableqa['portable_sha256']==portable['sha256']
    verify_entry(ROOT,{'path':'viewer/'+portable['file'],'bytes':portable['bytes'],'sha256':portable['sha256']})
    for cid in COMPONENTS:
        cm=read('components/'+cid+'/manifest.json')
        for entry in cm['files']:verify_entry(ROOT/'components'/cid,entry)
        pm=read('components/'+cid+'/inspector.manifest.json');pq=read('components/'+cid+'/inspector.html.qa.json')
        assert pm['source_models']=={cid:expected[cid]} and pq['status']=='PASS' and pq['portable_sha256']==pm['sha256']
        verify_entry(ROOT,{'path':'components/'+cid+'/inspector.html','bytes':pm['bytes'],'sha256':pm['sha256']})
    instances=[]
    for mid in ['ac130','ac130j']:
        doc=documents[mid];worlds=world_matrices(doc)
        for i,n in enumerate(doc['nodes']):
            cid=n.get('extras',{}).get('asset_id')
            if n.get('extras',{}).get('component_asset')=='JCNC_EOIR_MX20_FAMILY_VISUAL_r0003' and 'level 1' in n.get('extras',{}).get('tags',[]):cid='eoir-visual'
            if cid in COMPONENTS:
                instances.append({'assembly':mid,'component_id':cid,'node':n['name'],'canonical_component_sha256':expected[cid],
                    'world_rest_matrix_column_major':worlds[i].reshape(-1,order='F').tolist(),
                    'interface':'Aircraft-specific skin-conforming gun interface and J bag finish are assembly overrides; shared source definition retained.'})
    assert len(instances)==8,'Expected two guns and two optical systems in each gunship'
    write('articulation/component-registry.json',{'author':'claude-design','revision':'r0003','units':'metres','basis':'+X right,+Y up,nose -Z',
        'components':[{'id':cid,'file':str(modelpath(cid)),'sha256':expected[cid],'parent_aircraft_dependency':False} for cid in COMPONENTS],
        'instances':instances,'note':'Software asset architecture; no real aircraft interchangeability claim.'})
    files=[]
    for p in sorted(ROOT.rglob('*')):
        rel=p.relative_to(ROOT).as_posix()
        if not p.is_file() or any(x in p.parts for x in ['node_modules','__pycache__','.delivery','history']):continue
        if p.is_symlink():raise AssertionError('Unexpected symlink: '+rel)
        if rel in ['manifest.json','SHA256SUMS.txt'] or p.suffix in ['.pyc','.blend1','.log','.tmp']:continue
        if 'candidate' in p.name or 'adapter-probe' in p.name:continue
        files.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p),'role':rel.split('/')[0]})
    result={'schema':'jcnc.asset-revision/3','revision':'r0003','author':'claude-design','created_utc':args.created_utc,
        'status':'DRAFT_SYSTEMS_VISUAL_REVIEW','production_accepted':False,
        'parent':{'repository':'g1mmel/jcom-bigplanes','commit':'e9021ef629be8bb8afb096883d63186afae9dce8','revision':'family/claude-design/r0002'},
        'source':{'input':'source/inputs/c130-hercules-unified-r0001.glb','sha256':INPUT,'licensing':'INHERITED_AIRFRAME_PROVENANCE_REVIEW_REQUIRED','third_party_component_meshes_used':False},
        'coordinate_contract':{'units':'metres','up':'+Y','nose':'-Z','right':'+X'},
        'models':models,'component_registry':'articulation/component-registry.json',
        'validation_reports':{'format':'qa/gltf-validator-summary.json','geometry_and_isolation':'qa/system_geometry_report.json','runtime':'viewer/model-runtime-qa.json',
            'firing':'viewer/firing-model-qa.json','scoped_case_obstructions':'viewer/case-obstruction-qa.json','portable':'viewer/final-portable-receipt.json','native_blender':native_paths,'scope':'qa/QA_SCOPE.md','incidents':'qa/INCIDENT_LEDGER.json'},
        'remaining_acceptance':{'photographic_fit':'NOT_ACCEPTED','photorealistic_finish':'NOT_ACCEPTED','browser_rendering':'NOT_RUN','native_unreal':'NOT_RUN','continuous_combined_clearance':'NOT_PROVEN','gameplay_damage_lod_performance':'NOT_ACCEPTED'},
        'files':files,'integrity_note':'Manifest excludes itself and root SHA256SUMS; SHA256SUMS includes manifest. Hosted preservation receipts are recorded after publication.'}
    write('manifest.json',result)
    (ROOT/'SHA256SUMS.txt').write_text('\n'.join(f"{x['sha256']}  {x['path']}" for x in files)+'\n'+sha(ROOT/'manifest.json')+'  manifest.json\n')
    print(json.dumps({'status':'FROZEN_SCOPED_QA_PASS','files':len(files),'total_file_bytes':sum(x['bytes'] for x in files),'controls':sum(x['controls'] for x in models),'manifest_sha256':sha(ROOT/'manifest.json')},indent=2))

if __name__=='__main__':main()
