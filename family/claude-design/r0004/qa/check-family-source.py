#!/usr/bin/env python3
"""Rebuild the master from only delivered source and declared original inputs."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    expected={'models/c130-family.glb':sha(ROOT/'models/c130-family.glb')}
    for cid in ['hose-drogue-left','hose-drogue-right','fulton-yoke','jato-kit']:
        rel=f'components/{cid}/model.glb';expected[rel]=sha(ROOT/rel)
    with tempfile.TemporaryDirectory(prefix='c130-family-source-')as tmp:
        root=Path(tmp);shutil.copytree(ROOT/'source',root/'source',ignore=shutil.ignore_patterns('__pycache__','*.pyc','build-systems-all-receipts.json'))
        guard=r'''
import json,os,runpy,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();source=root/'source';reads=set();network=[]
allowed={(source/'inputs/c130-hercules-unified-r0001.glb').resolve(),(source/'inputs/r0003-ac130j.glb').resolve()}
def hook(event,args):
    if event in {'socket.connect','socket.connect_ex','socket.getaddrinfo','socket.sendto'}:
        network.append(event);raise RuntimeError('Source build attempted network access')
    if event=='open'and isinstance(args[0],(str,bytes,os.PathLike)):
        p=Path(os.fsdecode(args[0])).resolve();flags=args[2]if len(args)>2 else 0
        if p.suffix=='.glb'and(flags&os.O_ACCMODE)!=os.O_WRONLY:
            if p not in allowed:raise RuntimeError('Undeclared prebuilt GLB read: '+str(p))
            reads.add(str(p.relative_to(root)))
sys.addaudithook(hook);sys.path.insert(0,str(source))
runpy.run_path(str(source/'build_loadout_family.py'),run_name='__main__')
(root/'source-access.json').write_text(json.dumps({'declared_input_glb_reads':sorted(reads),'network_attempts':network},indent=2)+'\n')
'''
        result=subprocess.run([sys.executable,'-c',guard,str(root)],cwd=root,capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stdout+'\n'+result.stderr)
        actual={rel:sha(root/rel)for rel in expected}
        assert actual==expected,{'expected':expected,'rebuilt':actual}
        access=json.loads((root/'source-access.json').read_text())
        assert len(access['declared_input_glb_reads'])==2 and not access['network_attempts']
        report={'author':'claude-design','status':'PASS','method':'Fresh shallow temporary directory; only delivered source copied. Network guarded; prebuilt GLB reads restricted to the two declared original inputs. Every delivered master/new-component GLB rebuilt byte-identically.',
            'model_sha256':expected['models/c130-family.glb'],'script_sha256':sha(__file__),
            'source_files':{p.relative_to(ROOT/'source').as_posix():sha(p)for p in sorted((ROOT/'source').rglob('*'))if p.is_file()and'__pycache__'not in p.parts and p.name!='build-systems-all-receipts.json'and p.suffix in {'.py','.glb','.json','.txt'}},
            'python_version':sys.version.split()[0],'model_hashes':actual,'access':access,'byte_identical':True,
            'scope':'Reproduction and source dependency closure; does not establish real aircraft accuracy, collision clearance, browser or native Unreal acceptance.'}
        (ROOT/'qa/family-source-isolation.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'status':report['status'],'model_sha256':report['model_sha256'],'byte_identical_models':len(actual),'declared_original_inputs':2,'network_attempts':0}))

if __name__=='__main__':main()
