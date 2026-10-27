#!/usr/bin/env python3
"""Read-only audit of the existing KC-135 model, independent from C-130."""
import json
from pathlib import Path
from audit_c130_glb import audit_one,load_glb
p=Path(__file__).resolve().parents[1]/"kc135-stratotanker.glb"
r=audit_one(p)
print("KC135 AUDIT",json.dumps({k:v for k,v in r.items() if k not in ("exact_position_signatures","node_names","top_meshes")},indent=2))
print("KC135 NODE NAMES",json.dumps(r["node_names"],indent=2))
print("KC135 TOP MESHES",json.dumps(r["top_meshes"][:35],indent=2))
