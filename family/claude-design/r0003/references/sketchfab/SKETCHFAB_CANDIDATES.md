# claude-design — Sketchfab gunship component search

Checked 2026-10-29. Exact public model metadata and thumbnails were inspected. No third-party model binary was ingested.

## Decision

No exact independently downloadable component was both available through this session and appropriate as a finished AC-130W/J installation. Continue authoring visual components from military/manufacturer photographs. The M102 listing remains a possible donor after authenticated download and provenance review; the aircraft installation still requires its own mount, hierarchy, surface finish, and animation.

| Candidate | Creator | Listed geometry | License / availability | Disposition |
|---|---|---:|---|---|
| [M102 howitzer](https://sketchfab.com/3d-models/m102-howitzer-d4189d67fdcc4920ae3997ebe530f26b) | Ford mondeo | 7,097 triangles; 0 clips | CC Attribution / downloadable=true | Ground-carriage M102 with wheels and trail; not a finished aircraft installation. License offered is CC BY 4.0, but original provenance is undescribed. Official download API returns 401 without authentication. |
| [AC-130 - 105mm HC](https://sketchfab.com/3d-models/ac-130-105mm-hc-68b8a004365a4f4cb3f98727c6f893a9) | ZombieGunshipSurvival | 14,500 triangles; 0 clips | No license / downloadable=false | Independent game gun visually resembling an aircraft 105mm assembly, but download is disabled and no reuse license is provided. Cannot incorporate into project. |
| [30mm Bushmaster Cannon](https://sketchfab.com/3d-models/30mm-bushmaster-cannon-2b46c9d9e0b9482980a3b35fc7a56903) | Black Hole M. PR. | 1,243,600 triangles; 0 clips | CC Attribution / downloadable=true | Despite title, this is a cartridge; not the GAU-23/A gun. Excessively dense for a case effect. |
| [Wescam Homeland Security](https://sketchfab.com/3d-models/wescam-homeland-security-411a4dd6915c4e1db39ab7372625e588) | jjwiseman | 32,516 triangles; 0 clips | CC Attribution / downloadable=true | Terrain/video reconstruction, not a Wescam sensor turret. |
| [Lockheed AC-130J Ghostrider](https://sketchfab.com/3d-models/lockheed-ac-130j-ghostrider-f1cfdf557a424ea4b6c3b64ffc493f9f) | timonfreud | 44,265 triangles; 1 clips | Editorial / downloadable=false | Complete aircraft, not independent systems. Download disabled; editorial license unsuitable for game reuse without separate license. |

## Download result

The official M102 endpoint `https://api.sketchfab.com/v3/models/d4189d67fdcc4920ae3997ebe530f26b/download` was requested once without credentials and returned HTTP 401, `Authentication credentials were not provided.` The metadata endpoint is public and offered CC BY 4.0. No attempt was made to bypass that authentication requirement.

## Rejected substitutions

- M242 Bushmaster listings are a different gun type, so they do not establish a correct GAU-23/A asset.
- A listing titled “30mm Bushmaster Cannon” is visibly a cartridge.
- “Wescam Homeland Security” is visibly a landscape reconstruction.
- The fictional “Gau MX-23” rotary cannon is not a GAU-23/A.
- Full AC-130 aircraft listings are not independently reusable component packages, and disabled downloads/editorial licensing do not permit game incorporation.

## Evidence

`sketchfab-component-shortlist.json` includes exact API URLs, creator profiles, per-model verdicts, and metadata filenames. The associated JPGs are the published model thumbnails and were inspected to catch title mismatches. Model accuracy, native materials, rig separation and motion could not be validated without binaries. Public API documentation: https://sketchfab.com/developers/data-api/v3 .
