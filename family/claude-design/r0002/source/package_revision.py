#!/usr/bin/env python3
"""Hash the delivered files and bind scoped QA to the exact exported aircraft.

This packaging gate never upgrades photographic, licensing, continuous-clearance,
browser GPU, or native Unreal acceptance. Re-run after any deliverable changes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def verify_png(path):
    data=path.read_bytes()
    assert data[:8]==b'\x89PNG\r\n\x1a\n',('PNG signature',str(path))
    offset=8;compressed=[];ended=False
    while offset<len(data):
        assert offset+12<=len(data),('truncated PNG chunk',str(path))
        length=struct.unpack_from('>I',data,offset)[0]
        kind=data[offset+4:offset+8];end=offset+8+length
        assert end+4<=len(data),('truncated PNG payload',str(path))
        assert zlib.crc32(data[offset+4:end]) & 0xffffffff == struct.unpack_from('>I',data,end)[0],('PNG CRC',str(path))
        if kind==b'IDAT':compressed.append(data[offset+8:end])
        offset=end+4
        if kind==b'IEND':
            assert length==0 and offset==len(data),('PNG ending',str(path))
            ended=True;break
    assert ended and compressed,('incomplete PNG',str(path))
    decoder=zlib.decompressobj();decoder.decompress(b''.join(compressed));decoder.flush()
    assert decoder.eof and not decoder.unused_data,('incomplete PNG image stream',str(path))


def role(rel):
    if '/history/' in rel:return 'historical_evidence_not_current_acceptance'
    return {'models':'assembled_glb','editable':'native_blender','previews':'actual_model_render',
            'articulation':'mechanism_and_component_data','source':'reproducible_authoring',
            'viewer':'interactive_review','references':'reference_evidence','qa':'validation_evidence'}.get(rel.split('/')[0],'documentation')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--created-utc',required=True)
    a=p.parse_args();root=a.root.resolve()
    fmt=read(root/'qa/gltf-validator-summary.json')
    runtime=read(root/'viewer/model-runtime-qa.json')
    portable=read(root/'viewer/portable-manifest.json')
    portable_qa=read(root/'viewer/portable-qa.json')
    independent=read(root/'qa/independent_articulation_report.json')
    crossings=read(root/'qa/sampled_surface_crossings.json')
    closures=read(root/'qa/gear_closure_projected_coverage.json')
    indexing=read(root/'qa/exact_indexing_equivalence.json')
    assert indexing['status']=='PASS_EXACT_EQUIVALENCE','exact indexing proof is incomplete'
    assert closures['status']=='PASS_SCOPED','closed-gear native review is not complete'
    models=[]
    for mid in ['c130','ac130','ac130j']:
        path=root/'models'/f'{mid}.glb';data=path.read_bytes();digest=sha(path)
        json_length=struct.unpack_from('<I',data,12)[0]
        doc=json.loads(data[20:20+json_length])
        sidecar=read(root/'articulation'/f'{mid}.json')
        native=read(root/'qa'/f'{mid}-blender.json')
        f=next(x for x in fmt['models'] if x['id']==mid)
        r=next(x for x in runtime['models'] if x['id']==mid)
        cpu=next(x for x in independent['models'] if Path(x['file']).stem==mid)
        surface=next(x for x in crossings['models'] if x['id']==mid)
        closure=next(x for x in closures['models'] if x['id']==mid)
        exact=next(x for x in indexing['models'] if x['id']==mid)
        assert exact['after_sha256']==digest and exact['status']=='PASS_EXACT_EQUIVALENCE' and all(exact['checks'].values()),('exact indexing gate',mid)
        assert sidecar['sha256']==digest,('sidecar hash',mid)
        assert f['sha256']==digest and f['status']=='PASS' and f['errors']==0,('format gate',mid)
        assert r['model_sha256']==digest and runtime['status']=='PASS',('Three gate',mid)
        assert r['articulation_sha256']==sha(root/'articulation'/f'{mid}.json'),('sidecar QA gate',mid)
        assert cpu['sha256']==digest and cpu['status']=='PASS_SCOPED' and not cpu['errors'],('independent CPU gate',mid)
        assert surface['sha256']==digest,('surface-probe hash',mid)
        assert closure['sha256']==digest and closure['status']=='PASS_SCOPED',('closed-gear review gate',mid)
        assert native['input_sha256']==digest and native['import']=='PASS',('native hash/import gate',mid)
        assert native['native_animation_evaluation']['result']=='PASS',('native clip gate',mid)
        assert native['blend_reopen']['result']=='PASS',('native reopen gate',mid)
        assert native['controller_pose_source']['model_sha256']==digest,('render-pose hash',mid)
        assert native['controller_pose_source']['articulation_sha256']==sha(root/'articulation'/f'{mid}.json'),('render-pose sidecar hash',mid)
        assert sha(root/native['blend_path'])==native['blend_sha256'],('blend changed',mid)
        for image in native['renders']:
            assert sha(root/image['path'])==image['sha256'],('render changed',image['path'])
            verify_png(root/image['path'])
        models.append({'id':mid,'label':sidecar['label'],'file':f'models/{mid}.glb',
            'bytes':len(data),'sha256':digest,'meshes':len(doc.get('meshes',[])),
            'nodes':len(doc.get('nodes',[])),'clips':len(doc.get('animations',[])),
            'skins':len(doc.get('skins',[])),'controls':len(sidecar['controls']),
            'articulation':f'articulation/{mid}.json','editable':native['blend_path'],
            'previews':[x['path'] for x in native['renders']],
            'validation':{'khronos_format':{'status':f['status'],'errors':f['errors'],'warnings':f['warnings']},
                'three_actual_model_and_controller':'PASS','native_blender_import_and_clips':'PASS',
                'native_blend_save_reopen':'PASS','native_unreal':'NOT_RUN',
                'independent_decoded_geometry':cpu['status'],'independent_warnings':cpu['warnings'],
                'sampled_surface_probe':surface['status'],
                'closed_gear_geometry_review':closure['status'],
                'exact_indexing_preservation':'PASS_EXACT_EQUIVALENCE',
                'photographic_acceptance':'NOT_ACCEPTED','continuous_clearance':'NOT_PROVEN',
                'license_provenance':'REVIEW_REQUIRED'}})
    assert runtime['controller_sha256']==sha(root/'viewer/controller.mjs'),'controller changed after test'
    assert runtime['pose_driver_sha256']==sha(root/'viewer/pose-driver.mjs'),'pose driver changed after test'
    expected_models={m['id']:m['sha256'] for m in models}
    expected_previews={p for m in models for p in m['previews']}
    actual_previews={p.relative_to(root).as_posix() for p in (root/'previews').glob('*.png')}
    assert actual_previews==expected_previews,'stale or unreported preview images remain'
    assert portable['source_models']==expected_models,'portable embeds a different model revision'
    portable_path=root/'viewer'/portable['file']
    assert portable_path.stat().st_size==portable['bytes'] and sha(portable_path)==portable['sha256'],'portable bytes changed'
    assert portable_qa['status']=='PASS' and portable_qa['portable_sha256']==portable['sha256'],'portable integrity gate'
    files=[]
    for path in sorted(root.rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(root).as_posix()
        if rel.startswith('qa/history/exact-indexing-baseline/'):continue
        if any(x in path.parts for x in ['node_modules','__pycache__']):continue
        if path.name in ['manifest.json','SHA256SUMS.txt'] or path.suffix in ['.pyc','.blend1','.log']:continue
        if path.name.endswith('_provisional.json'):continue
        files.append({'path':rel,'bytes':path.stat().st_size,'sha256':sha(path),'role':role(rel)})
    manifest={'schema':'jcnc.asset-revision/2','revision':'r0002','author':'claude-design',
        'created_utc':a.created_utc,'status':'DRAFT_ARTICULATED_REVIEW',
        'production_accepted':False,'source':{'repository':'g1mmel/jcom-bigplanes',
            'commit':'65f83c26c0d03773fc1bc885728d7188a722960f','revision':'family/r0001',
            'input':'family/r0001/c130-hercules-unified-r0001.glb',
            'sha256':'ad3b1ff76fcff48dbb7dbc4901665f65def89f9db12d56112a00ee86389a0b12',
            'original_shared_meshes':24,'preservation':'r0001 bytes unchanged'},
        'coordinate_contract':{'units':'metres','up':'+Y','forward':'-Z','right':'+X','animated_parent_scale':'uniform'},
        'family_architecture':{'master':'source/build_family.py','configurations':'source/variants.json',
            'component_registry':'articulation/component-registry.json','delivery':'three complete assembled GLBs from common source and explicit compatible modules'},
        'models':models,'validation_reports':{'format':'qa/gltf-validator-summary.json',
            'controller':'viewer/controller-qa.json','actual_three_models':'viewer/model-runtime-qa.json',
            'independent_geometry':'qa/independent_articulation_report.json',
            'sampled_surface_crossings':'qa/sampled_surface_crossings.json','portable_integrity':'viewer/portable-qa.json',
            'closed_gear_review':'qa/gear_closure_projected_coverage.json',
            'exact_indexing_equivalence':'qa/exact_indexing_equivalence.json',
            'native_blender':['qa/'+m+'-blender.json' for m in ['c130','ac130','ac130j']],
            'scope':'qa/QA_SCOPE.md','incidents':'qa/INCIDENT_LEDGER.json'},
        'remaining_acceptance':{'photo_reference_fit':'NOT_ACCEPTED','full_swept_clearance':'NOT_PROVEN',
            'browser_webgl_visual_smoke_test':'NOT_RUN','native_unreal_import_animation_cook_runtime':'NOT_RUN',
            'source_license_provenance':'REVIEW_REQUIRED','game_damage_collision_lod_performance':'NOT_ACCEPTED'},
        'files':files,'integrity_note':'The manifest intentionally excludes its own hash and SHA256SUMS.txt; SHA256SUMS includes the manifest. Commit-pinned recovery receipts are recorded separately.'}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    checksums=[f"{x['sha256']}  {x['path']}" for x in files]
    checksums.append(f"{sha(root/'manifest.json')}  manifest.json")
    (root/'SHA256SUMS.txt').write_text('\n'.join(checksums)+'\n')
    print(json.dumps({'status':'PACKAGED_SCOPED_QA_PASS','files':len(files),'models':[{k:m[k] for k in ['id','bytes','sha256','meshes','nodes','clips','controls']} for m in models],'manifest_sha256':sha(root/'manifest.json')},indent=2))


if __name__=='__main__':main()
