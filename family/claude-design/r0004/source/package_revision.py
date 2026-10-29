#!/usr/bin/env python3
"""claude-design: verify frozen r0004 evidence, then inventory exact deliverables.

Consumes existing evidence without generating geometry or granting visual acceptance.
"""
from pathlib import Path
import argparse, hashlib, json, struct
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
NEW=['hose-drogue-left','hose-drogue-right','fulton-yoke','jato-kit']
REUSED=['gau23-visual','m102-airborne-visual','eoir-visual']
INPUT='ad3b1ff76fcff48dbb7dbc4901665f65def89f9db12d56112a00ee86389a0b12'
PARENT='e7075a4097d1842de0b0353cb27e5e294ee3506ee5d0ecdb47e8eeea22e94e93'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for data in iter(lambda:f.read(1048576),b''):h.update(data)
    return h.hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def write(p,v):(ROOT/p).write_text(json.dumps(v,indent=2)+'\n')
def verify_entry(root,e):
    p=root/e.get('path',e.get('file'))
    assert p.is_file(),('missing',str(p))
    assert sha(p)==e['sha256'],('hash',str(p))
    if 'bytes'in e:assert p.stat().st_size==e['bytes'],('bytes',str(p))
def gltf(p):
    data=Path(p).read_bytes();assert data[:4]==b'glTF'
    n=struct.unpack_from('<I',data,12)[0];return json.loads(data[20:20+n])

def main():
    p=argparse.ArgumentParser();p.add_argument('--created-utc',default='2026-10-29');a=p.parse_args()
    model=ROOT/'models/c130-family.glb';master_sha=sha(model);doc=gltf(model)
    cat=read('loadouts/catalog.json');side=read('articulation/c130-family.json')
    assert side['sha256']==master_sha
    assert len(cat['slots'])==12 and sum(len(s['options'])for s in cat['slots'])==28 and len(cat['presets'])==8
    assert len(side['controls'])==44 and len(doc['animations'])==44
    assert sum(n.get('name')=='fuselage'for n in doc['nodes'])==1
    assert sha(ROOT/'source/inputs/c130-hercules-unified-r0001.glb')==INPUT
    assert sha(ROOT/'source/inputs/r0003-ac130j.glb')==PARENT
    source_check=read('qa/family-source-isolation.json')
    assert source_check['status']=='PASS'and source_check['model_sha256']==master_sha and source_check['byte_identical']
    assert source_check['script_sha256']==sha(ROOT/'qa/check-family-source.py')
    for rel,h in source_check['source_files'].items():assert sha(ROOT/'source'/rel)==h
    rt=read('viewer/loadout-runtime-qa.json');assert rt['status']=='PASS'
    assert rt['model_sha256']==master_sha and rt['articulation_sha256']==sha(ROOT/'articulation/c130-family.json')
    assert rt['catalog_sha256']==sha(ROOT/'loadouts/catalog.json')
    assert rt['one_master_scene'] and rt['reset_max_local_transform_error']==0
    for name,h in rt['runtime_hashes'].items():assert sha(ROOT/'viewer'/name)==h
    fmt=read('qa/gltf-validator-summary.json');assert fmt['status']=='PASS'
    validated={x['id']:x for x in fmt['models']}
    assert set(validated)==set(['c130-family']+NEW+REUSED)
    models=[]
    for cid in ['c130-family']+NEW+REUSED:
        rel=('models/c130-family.glb'if cid=='c130-family'else f'components/{cid}/model.glb')
        ap=('articulation/c130-family.json'if cid=='c130-family'else f'components/{cid}/articulation.json')
        f=validated[cid];assert f['sha256']==sha(ROOT/rel)and f['errors']==0 and f['warnings']==0
        info=gltf(ROOT/rel);art=read(ap);assert art['sha256']==sha(ROOT/rel)
        models.append({'id':cid,'file':rel,'bytes':(ROOT/rel).stat().st_size,'sha256':sha(ROOT/rel),
            'nodes':len(info['nodes']),'meshes':len(info['meshes']),
            'triangles_all_options':sum(info['accessors'][pr['indices']]['count']//3 for m in info['meshes']for pr in m['primitives']),
            'clips':len(info.get('animations',[])),'controls':len(art['controls']),'articulation':ap,
            'revision':'r0003-preserved'if cid in REUSED else'r0004','parent_aircraft_dependency':cid=='c130-family',
            'format':{'status':'PASS','errors':0,'warnings':0},'native_unreal':'NOT_RUN'})
    native=read('qa/native-loadout-review.json')
    assert native['status']=='PASS'and native['input_sha256']==master_sha
    assert native['native_animation_evaluation']['result']=='PASS'and native['save_reopen']=='PASS'
    assert native['script_sha256']==sha(ROOT/'source/blender_loadout_review.py')
    assert native['snapshots_sha256']==sha(ROOT/'qa/viewer-poses-c130-family.json')
    verify_entry(ROOT,native['editable'])
    for render in native['renders']:
        verify_entry(ROOT,render)
        with Image.open(ROOT/render['path'])as im:im.verify()
    visual=read('qa/visual-review.json')
    assert visual['status']=='PASS_WITH_DECLARED_LIMITATIONS'and visual['model_sha256']==master_sha
    assert visual['native_report_sha256']==sha(ROOT/'qa/native-loadout-review.json')
    assert not visual['blocking_findings']
    ramp=read('qa/ramp-motion-audit-final.json')
    assert ramp['sha256']==master_sha and ramp['reset_world_matrix_delta']==0
    assert all(x['outside_hinge_above_20um']==0 for x in ramp['pairs'])
    for row in ramp['pairs']:
        if row['pair']!='upper_vs_skin':assert row['strict_crossing_count']==0
    pm=read('viewer/portable-manifest.json');pq=read('viewer/portable-qa.json')
    assert pm['source_models']=={'c130-family':master_sha}
    assert pm['loadout_catalog_sha256']==sha(ROOT/'loadouts/catalog.json')
    assert pq['status']=='PASS'and pq['portable_sha256']==pm['sha256']
    verify_entry(ROOT,{'path':'viewer/'+pm['file'],'bytes':pm['bytes'],'sha256':pm['sha256']})
    for cid in NEW+REUSED:
        base=ROOT/'components'/cid;cm=read(f'components/{cid}/manifest.json')
        for entry in cm['files']:verify_entry(base,entry)
        inspector=read(f'components/{cid}/inspector.manifest.json')
        if cid in NEW:
            assert cm['verification']['source_isolation']=='PASS'and cm['verification']['native_blender']=='PASS'
            assert inspector['model_sha256']==sha(base/'model.glb')
            assert inspector['verification']['status']=='PASS'and inspector['verification']['reset_max_transform_error']==0
            assert not cm['parent_aircraft_dependency']and not inspector['external_network_dependency']
        else:
            assert inspector['source_models']=={cid:sha(base/'model.glb')}
            prior=read(f'components/{cid}/inspector.html.qa.json');assert prior['status']=='PASS'
        verify_entry(base,{'path':'inspector.html','bytes':inspector['bytes'],'sha256':inspector['sha256']})
    isolation=read('qa/component-source-isolation.json');assert isolation['status']=='PASS'
    assert isolation['master_model_sha256']==master_sha
    assert isolation['script_sha256']==sha(ROOT/'source/package_components_r4.py')
    for name,h in isolation['source_snapshots'].items():assert sha(ROOT/'source'/name)==h
    assert {x['component']for x in isolation['components']}==set(NEW)
    for item in isolation['components']:
        cid=item['component'];assert item['model_sha256']==sha(ROOT/'components'/cid/'model.glb')
        assert item['source_isolation']['status']=='PASS'and item['source_isolation']['frozen_model_sha256']==item['model_sha256']
        assert item['native_blender']['status']=='PASS'and item['native_blender']['editable_sha256']==sha(ROOT/'components'/cid/'editable.blend')
        verify_entry(ROOT,item['package'])
    read('components/REUSED_R0003_PROVENANCE.json')
    old=ROOT.parent/'r0003/components'
    if old.exists():
        for cid in REUSED:
            for src in (old/cid).rglob('*'):
                if src.is_file()and '__pycache__'not in src.parts and src.suffix not in {'.pyc','.blend1'}:
                    assert sha(src)==sha(ROOT/'components'/src.relative_to(old))
    instances=[]
    for n in doc['nodes']:
        ex=n.get('extras',{});cid=ex.get('asset_id')
        if ex.get('component_asset')=='JCNC_EOIR_MX20_FAMILY_VISUAL_r0003'and'level 1'in ex.get('tags',[]):cid='eoir-visual'
        if cid in REUSED:instances.append({'component':cid,'node':n['name'],'revision':'r0003-source-preserved','interface':'Host-specific skin/panel and finish may be assembly overrides.'})
    for c in read('qa/build-loadout-receipt.json')['components']:
        assert c['sha256']==sha(ROOT/'components'/c['id']/'model.glb')
        instances.append({'component':c['id'],'node':c['root'],'revision':'r0004','interface':'Independent component with local mounting datum; host fending lines remain airframe installation geometry.'})
    write('articulation/component-registry.json',{'author':'claude-design','revision':'r0004','units':'metres','basis':'+X right,+Y up,nose -Z',
        'components':[x for x in models if x['id']!='c130-family'],'instances':instances,'note':'Software asset architecture; no real aircraft interchangeability claim.'})
    exclusions={'manifest.json','SHA256SUMS.txt','qa/ramp-repaired-c130.glb','source/build-systems-all-receipts.json',
        'qa/github-preservation-receipt.json','qa/hosted-delivery-verification.json'}
    files=[]
    for f in sorted(ROOT.rglob('*')):
        rel=f.relative_to(ROOT).as_posix()
        if not f.is_file()or any(x in f.parts for x in ['node_modules','__pycache__','.delivery']):continue
        if any(x.startswith('.')for x in f.relative_to(ROOT).parts):continue
        if rel.startswith('qa/')and f.suffix=='.glb':continue
        if rel in exclusions or f.suffix in {'.pyc','.blend1','.tmp'}:continue
        assert not f.is_symlink(),('symlink',rel)
        files.append({'path':rel,'bytes':f.stat().st_size,'sha256':sha(f),'role':rel.split('/')[0]})
    result={'schema':'jcnc.asset-revision/4','author':'claude-design','chat_code':'cg47','revision':'r0004','created_utc':a.created_utc,
        'status':'DRAFT_CONFIGURABLE_FAMILY','production_accepted':False,
        'parent':{'repository':'g1mmel/jcom-bigplanes','commit':'b769b1e7ebbc0c32c25546e16054743ad37f39db','revision':'family/claude-design/r0003','model_sha256':PARENT},
        'source':{'input':'source/inputs/c130-hercules-unified-r0001.glb','sha256':INPUT,'licensing':'INHERITED_AIRFRAME_PROVENANCE_REVIEW_REQUIRED','third_party_component_meshes_used':False},
        'coordinate_contract':{'units':'metres','up':'+Y','nose':'-Z','right':'+X'},
        'one_shared_airframe':True,'loadouts':{'catalogue':'loadouts/catalog.json','slots':12,'options':28,'presets':8,'controls':44},
        'models':models,'component_registry':'articulation/component-registry.json',
        'validation_reports':{'format':'qa/gltf-validator-summary.json','runtime':'viewer/loadout-runtime-qa.json','portable':'viewer/portable-qa.json',
            'native_blender':'qa/native-loadout-review.json','visual':'qa/visual-review.json','ramp':'qa/ramp-motion-audit-final.json','component_source':'qa/component-source-isolation.json',
            'family_source':'qa/family-source-isolation.json','reuse':'components/REUSED_R0003_PROVENANCE.json','reference_fit':'qa/loadout-reference-fit-audit.md','scope':'QA_SUMMARY.md'},
        'remaining_acceptance':{'photographic_fit':'NOT_ACCEPTED','photorealistic_finish':'NOT_ACCEPTED','browser_rendering':'NOT_RUN','native_unreal':'NOT_RUN',
            'continuous_combined_clearance':'NOT_PROVEN','upper_ramp_hinge_contacts':'DECLARED_NOT_ACCEPTED','complete_MC130E_or_LC130_conversion':'NOT_INCLUDED','gameplay_damage_lod_performance':'NOT_ACCEPTED'},
        'files':files,'integrity_note':'Manifest excludes itself and root SHA256SUMS; SHA256SUMS includes manifest. Intermediate ramp derivation GLB is reproducible and excluded. Hosted preservation receipts are recorded after publication.'}
    write('manifest.json',result)
    (ROOT/'SHA256SUMS.txt').write_text('\n'.join(f"{x['sha256']}  {x['path']}"for x in files)+'\n'+sha(ROOT/'manifest.json')+'  manifest.json\n')
    print(json.dumps({'status':'FROZEN_SCOPED_QA_PASS','files':len(files),'total_file_bytes':sum(x['bytes']for x in files),'master_sha256':master_sha,'manifest_sha256':sha(ROOT/'manifest.json')},indent=2))

if __name__=='__main__':main()
