# Original embedded texture exports

These PNG files are byte-for-byte copies of the images embedded in `../model.glb`. The GLB does not load these external copies. `../materials.json` maps image indices, texture indices, material slots and actual mesh usage; some exported maps belong to unused material definitions.

The flash and smoke textures are original analytic soft-alpha images. The surface maps are original analytic material variation, not photographs. Base-color/emissive RGB uses sRGB; alpha and metallic-roughness data are linear. In metallic-roughness maps, G controls roughness and B multiplies metallic. No normal map or photographic texture bake is included.
