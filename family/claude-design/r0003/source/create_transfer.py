#!/usr/bin/env python3
"""Package only frozen, checksum-verified delivery files into bounded chunks."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import tarfile


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[1];out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if out.is_relative_to(root):raise ValueError('Keep transport scratch outside the revision inventory')
    manifest=json.loads((root/'manifest.json').read_text())
    for item in manifest['files']:
        f=root/item['path']
        if f.stat().st_size!=item['bytes'] or digest(f)!=item['sha256']:raise ValueError('Revision is not frozen: '+item['path'])
    paths=[x['path'] for x in manifest['files']]+['manifest.json','SHA256SUMS.txt']
    # Adjacent models allow the long compression dictionary to reuse shared data.
    order={'models':0,'editable':1,'viewer':2,'previews':3}
    paths.sort(key=lambda x:(order.get(x.split('/')[0],4),x))
    archive=out/'C130-family-r0003.tar.xz'
    with lzma.open(archive,'wb',filters=[{'id':lzma.FILTER_LZMA2,'preset':6,'dict_size':64*1024*1024}]) as compressed:
        with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as tf:
            for rel in paths:
                f=root/rel;info=tarfile.TarInfo(rel);info.size=f.stat().st_size
                info.mtime=0;info.uid=0;info.gid=0;info.mode=0o644
                with f.open('rb') as stream:tf.addfile(info,stream)
    chunks=[]
    with archive.open('rb') as f:
        while True:
            data=f.read(1024*1024)
            if not data:break
            name=f'part-{len(chunks):04d}.bin';(out/name).write_bytes(data)
            chunks.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                           'git_sha':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()})
    spec={'schema':'jcnc.exact-byte-transfer/1','author':'claude-design',
          'purpose':'Restore reviewed files; no model generation or rendering',
          'archive_name':archive.name,
          'archive_bytes':archive.stat().st_size,'archive_sha256':digest(archive),
          'revision_manifest_sha256':digest(root/'manifest.json'),'file_count':len(paths),'chunks':chunks}
    (out/'transfer.json').write_text(json.dumps(spec,indent=2)+'\n')
    print(json.dumps({k:v for k,v in spec.items() if k!='chunks'},indent=2));print('Chunks:',len(chunks))


if __name__=='__main__':main()
