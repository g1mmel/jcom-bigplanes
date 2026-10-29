#!/usr/bin/env python3
"""Restore exact reviewed bytes from bounded transport chunks; never build models.

Used only because the GitHub connector cannot submit a complete large binary in
one request. All chunks, the archive and every delivered file are hash checked.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def verify_files(root):
    manifest=json.loads((root/'manifest.json').read_text())
    for entry in manifest['files']:
        path=root/entry['path']
        if path.stat().st_size!=entry['bytes'] or digest(path)!=entry['sha256']:
            raise ValueError('Delivered file mismatch: '+entry['path'])
    for line in (root/'SHA256SUMS.txt').read_text().splitlines():
        expected,rel=line.split('  ',1)
        if digest(root/rel)!=expected:raise ValueError('Checksum mismatch: '+rel)
    return manifest


def main():
    p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    if a.verify_only:
        m=verify_files(root);print('Exact delivered file hashes verified:',len(m['files']));return
    transport=root/'.delivery'
    spec=json.loads((transport/'transfer.json').read_text())
    with tempfile.TemporaryDirectory(prefix='c130-exact-transfer-') as temp:
        archive=Path(temp)/'reviewed-package.tar.xz'
        with archive.open('wb') as out:
            for item in spec['chunks']:
                name=PurePosixPath(item['path'])
                if name.is_absolute() or '..' in name.parts or len(name.parts)!=1:raise ValueError('Invalid transport path')
                path=transport/item['path']
                if path.stat().st_size!=item['bytes'] or digest(path)!=item['sha256']:raise ValueError('Transport chunk mismatch: '+item['path'])
                with path.open('rb') as f:shutil.copyfileobj(f,out)
        if archive.stat().st_size!=spec['archive_bytes'] or digest(archive)!=spec['archive_sha256']:
            raise ValueError('Archive hash mismatch')
        with tarfile.open(archive,'r:xz') as tf:
            for member in tf.getmembers():
                rel=PurePosixPath(member.name)
                if rel.is_absolute() or '..' in rel.parts or not member.isfile():raise ValueError('Unexpected archive member: '+member.name)
                if rel.parts[0] in {'.delivery','.git'}:raise ValueError('Reserved archive path')
                target=root.joinpath(*rel.parts)
                if not target.resolve().is_relative_to(root.resolve()):raise ValueError('Archive path escaped revision')
                target.parent.mkdir(parents=True,exist_ok=True)
                with tf.extractfile(member) as inp,target.open('wb') as out:shutil.copyfileobj(inp,out)
    manifest=verify_files(root)
    if digest(root/'manifest.json')!=spec['revision_manifest_sha256']:raise ValueError('Revision manifest changed in transport')
    receipt={'author':'claude-design','method':'Exact reviewed-byte restoration; no model-generation or rendering command executed',
             'status':'PASS','restored_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'staging_commit':os.environ.get('GITHUB_SHA'),'workflow_run_id':os.environ.get('GITHUB_RUN_ID'),
             'archive_sha256':spec['archive_sha256'],'revision_manifest_sha256':spec['revision_manifest_sha256'],
             'file_count':len(manifest['files']),'models':[{'id':m['id'],'bytes':m['bytes'],'sha256':m['sha256']} for m in manifest['models']]}
    (root/'qa/github-preservation-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    shutil.rmtree(transport)
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
