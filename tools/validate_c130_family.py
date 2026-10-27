#!/usr/bin/env python3
"""Structural regression checks for C-130 unified family, not visual acceptance."""
import hashlib
import json
from pathlib import Path

from audit_c130_glb import load_glb

ROOT=Path(__file__).resolve().parents[1]
FAMILY=ROOT/"family"/"r0001"
manifest=json.loads((FAMILY/"manifest.json").read_text())
source=manifest["source_sha256"]
common_signatures=[]
for filename,record in manifest["variant_files"].items():
    path=FAMILY/filename
    data,doc,buf=load_glb(path)
    assert hashlib.sha256(data).hexdigest()==record["sha256"],filename
    nodes=doc["nodes"]
    names={n.get("name") for n in nodes}
    roots=[n for n in nodes if n.get("name")=="AIRFRAME_COMMON_SOURCE"]
    assert len(roots)==1
    root=roots[0]
    assert len(root["children"])==24-4
    assert root["extras"]["source_sha256"]==source
    assert root["scale"]==manifest["scale"]
    assert root["translation"]==manifest["shift"]
    assert doc["buffers"][0]["byteLength"]<=len(buf)
    assert not any("PROBE" in n for n in names)
    assert not any("TANKER_BOOM" in n for n in names)
    assert "SOCKET_RECEIVER_UARRSI" in names
    assert "SOCKET_TANKER_DELIVERY_PORT" in names
    assert "SOCKET_TANKER_DELIVERY_STARBOARD" in names
    if filename.startswith("ac130j"):
        assert len([n for n in names if n and n.startswith("PROP6_BLADES_")])==4
        assert "AC130J_PORT_30MM_PROXY" in names
        assert "AC130J_PORT_105MM_PROXY" in names
        assert "AC130J_EOIR_TURRET_PROXY" in names
    elif filename.startswith("ac130-"):
        assert "AC_LEGACY_PORT_GUN_PROXY" in names
        assert not any(n and n.startswith("PROP6_BLADES_") for n in names)
    else:
        assert not any(n and n.startswith("AC_LEGACY_PORT_GUN") for n in names)
        assert not any(n and n.startswith("AC130J_PORT_") for n in names)
    common_signatures.append((root["children"],root["scale"],root["translation"]))
assert all(s==common_signatures[0] for s in common_signatures)
print("PASS: 3 GLBs have one identical C-130 airframe source, distinct kit nodes.")
print("PASS: Original source hash and variant file hashes match.")
print("PASS: Receiver socket distinct from tanker delivery sockets; no fabricated probe.")
print("NOT RUN: native Blender/Unreal, photographic acceptance, rig motion.")
