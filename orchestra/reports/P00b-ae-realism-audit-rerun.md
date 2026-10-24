status: partial
summary:
- Fresh-bundle audit checkpoint; matrix/performance work is still in progress.
- No plugin source, release gate, ledger, MAIN or AEXCompat edits.

facts:
- Source build HEAD: d1b18b9accaee821543548c1d2d7adf33781dcca (merge of P00).
- Host and bundle identities, parameter paths/hashes and raw rows are in `P00b-evidence/`.
- This is an oracle-free SDK host loading real arm64 plugin bundles, not native AE or a pixel-exact comparison.
- Matrix uses independent host-shape probes, with two additional 4K downsample probes.
- ColorKeep uses three nested T15b anchors sampled with replacement; ColorKey/KiraKira/Smoother2 also sample with replacement (9/8/8 unique paths).
- Timeouts are 60-second process wall limits; successful times below are render-selector seconds.

baseline: 60 rows; {'ok': 60}

| Plugin / situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| olmblur / full | {'ok': 1} | {} | 1/1 |
| olmblur / half | {'ok': 1} | {} | 1/1 |
| olmblur / quarter | {'ok': 1} | {} | 1/1 |
| olmblur / 4k | {'ok': 1} | {} | 1/1 |
| olmblur / 4k-half | {'ok': 1} | {} | 1/1 |
| olmblur / 4k-quarter | {'ok': 1} | {} | 1/1 |
| colorkeep / full | {'ok': 1} | {} | 1/1 |
| colorkeep / half | {'ok': 1} | {} | 1/1 |
| colorkeep / quarter | {'ok': 1} | {} | 1/1 |
| colorkeep / 4k | {'ok': 1} | {} | 1/1 |
| colorkeep / 4k-half | {'ok': 1} | {} | 1/1 |
| colorkeep / 4k-quarter | {'ok': 1} | {} | 1/1 |
| olmcolorkey / full | {'ok': 1} | {} | 1/1 |
| olmcolorkey / half | {'ok': 1} | {} | 1/1 |
| olmcolorkey / quarter | {'ok': 1} | {} | 1/1 |
| olmcolorkey / 4k | {'ok': 1} | {} | 1/1 |
| olmcolorkey / 4k-half | {'ok': 1} | {} | 1/1 |
| olmcolorkey / 4k-quarter | {'ok': 1} | {} | 1/1 |
| olmdirectionalblur / full | {'ok': 1} | {} | 1/1 |
| olmdirectionalblur / half | {'ok': 1} | {} | 1/1 |
| olmdirectionalblur / quarter | {'ok': 1} | {} | 1/1 |
| olmdirectionalblur / 4k | {'ok': 1} | {} | 1/1 |
| olmdirectionalblur / 4k-half | {'ok': 1} | {} | 1/1 |
| olmdirectionalblur / 4k-quarter | {'ok': 1} | {} | 1/1 |
| olmdistancegradation / full | {'ok': 1} | {} | 0/1 |
| olmdistancegradation / half | {'ok': 1} | {} | 0/1 |
| olmdistancegradation / quarter | {'ok': 1} | {} | 0/1 |
| olmdistancegradation / 4k | {'ok': 1} | {} | 0/1 |
| olmdistancegradation / 4k-half | {'ok': 1} | {} | 0/1 |
| olmdistancegradation / 4k-quarter | {'ok': 1} | {} | 0/1 |
| olmkirakira / full | {'ok': 1} | {} | 1/1 |
| olmkirakira / half | {'ok': 1} | {} | 1/1 |
| olmkirakira / quarter | {'ok': 1} | {} | 1/1 |
| olmkirakira / 4k | {'ok': 1} | {} | 1/1 |
| olmkirakira / 4k-half | {'ok': 1} | {} | 1/1 |
| olmkirakira / 4k-quarter | {'ok': 1} | {} | 1/1 |
| olmsmoother2 / full | {'ok': 1} | {} | 1/1 |
| olmsmoother2 / half | {'ok': 1} | {} | 1/1 |
| olmsmoother2 / quarter | {'ok': 1} | {} | 1/1 |
| olmsmoother2 / 4k | {'ok': 1} | {} | 1/1 |
| olmsmoother2 / 4k-half | {'ok': 1} | {} | 1/1 |
| olmsmoother2 / 4k-quarter | {'ok': 1} | {} | 1/1 |
| olmtoondilate / full | {'ok': 1} | {} | 1/1 |
| olmtoondilate / half | {'ok': 1} | {} | 1/1 |
| olmtoondilate / quarter | {'ok': 1} | {} | 1/1 |
| olmtoondilate / 4k | {'ok': 1} | {} | 1/1 |
| olmtoondilate / 4k-half | {'ok': 1} | {} | 1/1 |
| olmtoondilate / 4k-quarter | {'ok': 1} | {} | 1/1 |
| radialblur / full | {'ok': 1} | {} | 1/1 |
| radialblur / half | {'ok': 1} | {} | 1/1 |
| radialblur / quarter | {'ok': 1} | {} | 1/1 |
| radialblur / 4k | {'ok': 1} | {} | 1/1 |
| radialblur / 4k-half | {'ok': 1} | {} | 1/1 |
| radialblur / 4k-quarter | {'ok': 1} | {} | 1/1 |
| olmsmoother / full | {'ok': 1} | {} | 1/1 |
| olmsmoother / half | {'ok': 1} | {} | 1/1 |
| olmsmoother / quarter | {'ok': 1} | {} | 1/1 |
| olmsmoother / 4k | {'ok': 1} | {} | 1/1 |
| olmsmoother / 4k-half | {'ok': 1} | {} | 1/1 |
| olmsmoother / 4k-quarter | {'ok': 1} | {} | 1/1 |

matrix: 6458 rows; {'ok': 6153, 'refusal': 305}

| Plugin / situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| olmblur / full | {'ok': 33} | {} | 33/33 |
| olmblur / half | {'ok': 33} | {} | 33/33 |
| olmblur / quarter | {'ok': 33} | {} | 33/33 |
| olmblur / third | {'ok': 33} | {} | 33/33 |
| olmblur / eighth | {'ok': 33} | {} | 33/33 |
| olmblur / asymmetric | {'ok': 33} | {} | 33/33 |
| olmblur / 4k | {'ok': 33} | {} | 33/33 |
| olmblur / 4k-half | {'ok': 33} | {} | 33/33 |
| olmblur / 4k-quarter | {'ok': 33} | {} | 33/33 |
| olmblur / square | {'ok': 33} | {} | 33/33 |
| olmblur / odd | {'ok': 33} | {} | 33/33 |
| olmblur / odd-half | {'ok': 33} | {} | 33/33 |
| olmblur / large-layer | {'ok': 33} | {} | 33/33 |
| olmblur / aligned-odd | {'ok': 33} | {} | 33/33 |
| olmblur / padded | {'ok': 33} | {} | 33/33 |
| olmblur / extent | {'ok': 33} | {} | 33/33 |
| olmblur / roi | {'ok': 33} | {} | 33/33 |
| olmblur / expanded | {'ok': 33} | {} | 33/33 |
| olmblur / cropped-expand | {'ok': 33} | {} | 33/33 |
| olmblur / aspect09 | {'ok': 33} | {} | 33/33 |
| olmblur / aspect2 | {'ok': 33} | {} | 33/33 |
| colorkeep / full | {'ok': 33} | {} | 33/33 |
| colorkeep / half | {'ok': 33} | {} | 33/33 |
| colorkeep / quarter | {'ok': 33} | {} | 33/33 |
| colorkeep / third | {'ok': 33} | {} | 33/33 |
| colorkeep / eighth | {'ok': 33} | {} | 33/33 |
| colorkeep / asymmetric | {'ok': 33} | {} | 33/33 |
| colorkeep / 4k | {'ok': 33} | {} | 33/33 |
| colorkeep / 4k-half | {'ok': 33} | {} | 33/33 |
| colorkeep / 4k-quarter | {'ok': 33} | {} | 33/33 |
| colorkeep / square | {'ok': 33} | {} | 33/33 |
| colorkeep / odd | {'ok': 33} | {} | 33/33 |
| colorkeep / odd-half | {'ok': 33} | {} | 33/33 |
| colorkeep / large-layer | {'ok': 33} | {} | 33/33 |
| colorkeep / aligned-odd | {'ok': 33} | {} | 33/33 |
| colorkeep / padded | {'ok': 33} | {} | 33/33 |
| colorkeep / extent | {'ok': 33} | {} | 33/33 |
| colorkeep / roi | {'ok': 33} | {} | 33/33 |
| colorkeep / expanded | {'ok': 33} | {} | 33/33 |
| colorkeep / cropped-expand | {'ok': 33} | {} | 33/33 |
| colorkeep / aspect09 | {'ok': 33} | {} | 33/33 |
| colorkeep / aspect2 | {'ok': 33} | {} | 33/33 |
| olmcolorkey / full | {'ok': 33} | {} | 33/33 |
| olmcolorkey / half | {'ok': 33} | {} | 33/33 |
| olmcolorkey / quarter | {'ok': 33} | {} | 33/33 |
| olmcolorkey / third | {'ok': 33} | {} | 33/33 |
| olmcolorkey / eighth | {'ok': 33} | {} | 33/33 |
| olmcolorkey / asymmetric | {'ok': 33} | {} | 33/33 |
| olmcolorkey / 4k | {'ok': 33} | {} | 33/33 |
| olmcolorkey / 4k-half | {'ok': 33} | {} | 33/33 |
| olmcolorkey / 4k-quarter | {'ok': 33} | {} | 33/33 |
| olmcolorkey / square | {'ok': 33} | {} | 33/33 |
| olmcolorkey / odd | {'ok': 33} | {} | 33/33 |
| olmcolorkey / odd-half | {'ok': 33} | {} | 33/33 |
| olmcolorkey / large-layer | {'ok': 33} | {} | 33/33 |
| olmcolorkey / aligned-odd | {'ok': 33} | {} | 33/33 |
| olmcolorkey / padded | {'ok': 33} | {} | 33/33 |
| olmcolorkey / extent | {'ok': 33} | {} | 33/33 |
| olmcolorkey / roi | {'ok': 33} | {} | 33/33 |
| olmcolorkey / expanded | {'ok': 33} | {} | 33/33 |
| olmcolorkey / cropped-expand | {'ok': 33} | {} | 33/33 |
| olmcolorkey / aspect09 | {'ok': 33} | {} | 33/33 |
| olmcolorkey / aspect2 | {'ok': 33} | {} | 33/33 |
| olmdistancegradation / full | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / half | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / quarter | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / third | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / eighth | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / asymmetric | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / 4k | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / 4k-half | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / 4k-quarter | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / square | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / odd | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / odd-half | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / large-layer | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / aligned-odd | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / padded | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / extent | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 32/32 |
| olmdistancegradation / roi | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / expanded | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / cropped-expand | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / aspect09 | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmdistancegradation / aspect2 | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| olmkirakira / full | {'ok': 33} | {} | 33/33 |
| olmkirakira / half | {'ok': 33} | {} | 33/33 |
| olmkirakira / quarter | {'ok': 33} | {} | 33/33 |
| olmkirakira / third | {'ok': 33} | {} | 33/33 |
| olmkirakira / eighth | {'ok': 33} | {} | 33/33 |
| olmkirakira / asymmetric | {'ok': 33} | {} | 33/33 |
| olmkirakira / 4k | {'ok': 33} | {} | 33/33 |
| olmkirakira / 4k-half | {'ok': 33} | {} | 33/33 |
| olmkirakira / 4k-quarter | {'ok': 33} | {} | 33/33 |
| olmkirakira / square | {'ok': 33} | {} | 33/33 |
| olmkirakira / odd | {'ok': 33} | {} | 33/33 |
| olmkirakira / odd-half | {'ok': 33} | {} | 33/33 |
| olmkirakira / large-layer | {'ok': 33} | {} | 33/33 |
| olmkirakira / aligned-odd | {'ok': 33} | {} | 33/33 |
| olmkirakira / padded | {'ok': 33} | {} | 33/33 |
| olmkirakira / extent | {'ok': 33} | {} | 33/33 |
| olmkirakira / roi | {'ok': 33} | {} | 33/33 |
| olmkirakira / expanded | {'ok': 33} | {} | 33/33 |
| olmkirakira / cropped-expand | {'ok': 33} | {} | 33/33 |
| olmkirakira / aspect09 | {'ok': 33} | {} | 33/33 |
| olmkirakira / aspect2 | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / full | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / half | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / quarter | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / third | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / eighth | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / asymmetric | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / 4k | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / 4k-half | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / 4k-quarter | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / square | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / odd | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / odd-half | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / large-layer | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / aligned-odd | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / padded | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / extent | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / roi | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / expanded | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / cropped-expand | {'refusal': 33} | {'ValidatePublicWorlds:validate-world-shape@5240': 33} | 0/0 |
| olmsmoother2 / aspect09 | {'ok': 33} | {} | 33/33 |
| olmsmoother2 / aspect2 | {'ok': 33} | {} | 33/33 |
| olmtoondilate / full | {'ok': 33} | {} | 33/33 |
| olmtoondilate / half | {'ok': 33} | {} | 33/33 |
| olmtoondilate / quarter | {'ok': 33} | {} | 33/33 |
| olmtoondilate / third | {'ok': 33} | {} | 33/33 |
| olmtoondilate / eighth | {'ok': 33} | {} | 33/33 |
| olmtoondilate / asymmetric | {'ok': 33} | {} | 33/33 |
| olmtoondilate / 4k | {'ok': 33} | {} | 33/33 |
| olmtoondilate / 4k-half | {'ok': 33} | {} | 33/33 |
| olmtoondilate / 4k-quarter | {'ok': 33} | {} | 33/33 |
| olmtoondilate / square | {'ok': 33} | {} | 33/33 |
| olmtoondilate / odd | {'ok': 33} | {} | 33/33 |
| olmtoondilate / odd-half | {'ok': 33} | {} | 33/33 |
| olmtoondilate / large-layer | {'ok': 33} | {} | 33/33 |
| olmtoondilate / aligned-odd | {'ok': 33} | {} | 33/33 |
| olmtoondilate / padded | {'ok': 33} | {} | 33/33 |
| olmtoondilate / extent | {'ok': 33} | {} | 33/33 |
| olmtoondilate / roi | {'ok': 33} | {} | 33/33 |
| olmtoondilate / expanded | {'ok': 33} | {} | 33/33 |
| olmtoondilate / cropped-expand | {'ok': 33} | {} | 33/33 |
| olmtoondilate / aspect09 | {'ok': 33} | {} | 33/33 |
| olmtoondilate / aspect2 | {'ok': 33} | {} | 33/33 |
| olmsmoother / full | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / half | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / quarter | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / third | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / eighth | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / asymmetric | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / 4k | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / 4k-half | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / 4k-quarter | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / square | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / odd | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / odd-half | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / large-layer | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / aligned-odd | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / padded | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / extent | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / roi | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / expanded | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / cropped-expand | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / aspect09 | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmsmoother / aspect2 | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| olmdirectionalblur / full | {'ok': 27} | {} | 27/27 |
| olmdirectionalblur / half | {'ok': 27} | {} | 27/27 |
| olmdirectionalblur / quarter | {'ok': 27} | {} | 27/27 |
| olmdirectionalblur / third | {'ok': 27} | {} | 27/27 |
| olmdirectionalblur / eighth | {'ok': 27} | {} | 27/27 |
| olmdirectionalblur / asymmetric | {'ok': 27} | {} | 27/27 |
| olmdirectionalblur / 4k | {'ok': 27} | {} | 27/27 |
| olmdirectionalblur / 4k-half | {'ok': 27} | {} | 27/27 |
| olmdirectionalblur / 4k-quarter | {'ok': 27} | {} | 27/27 |
| olmdirectionalblur / square | {'ok': 27} | {} | 27/27 |
| olmdirectionalblur / odd | {'ok': 26} | {} | 26/26 |
| olmdirectionalblur / odd-half | {'ok': 24} | {} | 24/24 |
| olmdirectionalblur / large-layer | {'ok': 24} | {} | 24/24 |
| olmdirectionalblur / aligned-odd | {'ok': 24} | {} | 24/24 |
| olmdirectionalblur / padded | {'ok': 24} | {} | 24/24 |
| olmdirectionalblur / extent | {'ok': 24} | {} | 24/24 |
| olmdirectionalblur / roi | {'ok': 24} | {} | 24/24 |
| olmdirectionalblur / expanded | {'ok': 24} | {} | 24/24 |
| olmdirectionalblur / cropped-expand | {'ok': 4, 'refusal': 20} | {'SmartRender:smart-generic-world-or-budget@2707': 20} | 4/4 |
| olmdirectionalblur / aspect09 | {'ok': 24} | {} | 24/24 |
| olmdirectionalblur / aspect2 | {'ok': 24} | {} | 24/24 |
| radialblur / full | {'ok': 18} | {} | 18/18 |
| radialblur / half | {'ok': 18} | {} | 18/18 |
| radialblur / quarter | {'ok': 18} | {} | 18/18 |
| radialblur / third | {'ok': 18} | {} | 18/18 |
| radialblur / eighth | {'ok': 18} | {} | 18/18 |
| radialblur / asymmetric | {'ok': 18} | {} | 18/18 |
| radialblur / 4k | {'ok': 18} | {} | 18/18 |
| radialblur / 4k-half | {'ok': 18} | {} | 18/18 |
| radialblur / 4k-quarter | {'ok': 18} | {} | 18/18 |
| radialblur / square | {'ok': 18} | {} | 18/18 |
| radialblur / odd | {'ok': 18} | {} | 18/18 |
| radialblur / odd-half | {'ok': 18} | {} | 18/18 |
| radialblur / large-layer | {'ok': 18} | {} | 18/18 |
| radialblur / aligned-odd | {'ok': 18} | {} | 18/18 |
| radialblur / padded | {'ok': 18} | {} | 18/18 |
| radialblur / extent | {'ok': 18} | {} | 18/18 |
| radialblur / roi | {'ok': 18} | {} | 18/18 |
| radialblur / expanded | {'ok': 18} | {} | 18/18 |
| radialblur / cropped-expand | {'ok': 18} | {} | 18/18 |
| radialblur / aspect09 | {'ok': 18} | {} | 18/18 |
| radialblur / aspect2 | {'ok': 18} | {} | 18/18 |

Performance (seconds per render selector; **bold** flags >2 s at 1080p):
Heaviest means the largest observed render time among sampled corpus tuples for that size/depth; a timeout is only a process-time lower bound.
| Plugin | bpc | Default 1080p | Default 4K | Heaviest 1080p (case) | Heaviest 4K (case) |
|---|---|---|---|---|---|
| olmblur | 8 | 0.452 | 1.804 | **2.885** (corpus05) | 11.667 (corpus05) |
| olmblur | 16 | 0.457 | 1.814 | **2.896** (corpus05) | 11.649 (corpus05) |
| olmblur | 32 | 0.463 | 1.850 | **2.929** (corpus05) | 11.709 (corpus05) |
| colorkeep | 8 | 0.007 | 0.028 | 0.121 (corpus02) | 0.495 (corpus02) |
| colorkeep | 16 | 0.008 | 0.033 | 0.124 (corpus02) | 0.483 (corpus02) |
| colorkeep | 32 | 0.011 | 0.048 | 0.080 (corpus02) | 0.337 (corpus02) |
| olmcolorkey | 8 | 0.017 | 0.069 | 1.873 (corpus05) | 7.351 (corpus05) |
| olmcolorkey | 16 | 0.019 | 0.075 | 1.857 (corpus05) | 7.328 (corpus05) |
| olmcolorkey | 32 | 0.025 | 0.110 | 1.858 (corpus05) | 7.489 (corpus05) |
| olmdirectionalblur | 8 | 0.003 | 0.010 | **5.363** (corpus07) | 22.269 (corpus07) |
| olmdirectionalblur | 16 | 0.004 | 0.017 | **5.416** (corpus07) | 22.292 (corpus07) |
| olmdirectionalblur | 32 | 0.008 | 0.038 | **5.505** (corpus07) | 22.177 (corpus07) |
| olmdistancegradation | 8 | 0.077 | 0.340 | 0.032 (corpus02) | 0.112 (corpus04) |
| olmdistancegradation | 16 | 0.077 | 0.334 | 0.031 (corpus04) | 0.135 (corpus01) |
| olmdistancegradation | 32 | refusal | refusal | 0.041 (corpus01) | 0.250 (corpus02) |
| olmkirakira | 8 | 0.426 | 1.653 | 0.396 (corpus05) | 1.605 (corpus05) |
| olmkirakira | 16 | 0.414 | 1.712 | 0.397 (corpus05) | 1.653 (corpus05) |
| olmkirakira | 32 | 0.415 | 1.735 | 0.388 (corpus05) | 1.635 (corpus05) |
| olmsmoother2 | 8 | 0.379 | 1.557 | 0.400 (corpus03) | 1.579 (corpus05) |
| olmsmoother2 | 16 | 0.388 | 1.589 | 0.395 (corpus03) | 1.610 (corpus03) |
| olmsmoother2 | 32 | 0.388 | 1.690 | 0.404 (corpus03) | 1.621 (corpus03) |
| olmtoondilate | 8 | 0.011 | 0.043 | 0.011 (corpus06) | 0.043 (corpus06) |
| olmtoondilate | 16 | 0.012 | 0.052 | 0.015 (corpus08) | 0.054 (corpus03) |
| olmtoondilate | 32 | 0.015 | 0.067 | 0.019 (corpus03) | 0.066 (corpus06) |
| radialblur | 8 | 0.002 | 0.004 | 0.776 (corpus01) | 2.189 (corpus01) |
| radialblur | 16 | 0.002 | 0.010 | 0.745 (corpus01) | 2.178 (corpus01) |
| radialblur | 32 | 0.005 | 0.024 | 0.746 (corpus01) | 2.149 (corpus01) |
| olmsmoother | 8 | 0.346 | 1.399 | 1.535 (corpus00) | 6.125 (corpus00) |
| olmsmoother | 16 | 1.077 | 4.269 | **2.151** (corpus00) | 8.585 (corpus00) |
| olmsmoother | 32 | refusal | refusal | unavailable | unavailable |

Refusal interpretation (FACT and INFERENCE kept separate):

- **DirectionalBlur / `SmartRender:smart-generic-world-or-budget@2707`**.
  FACT: the cropped-expand probe has full layer 1920×1080 but checked-out
  input 960×540. For this plugin PreRender returns 960×540 too: the situation
  name does **not** mean output actually expanded. The Mac guard at
  `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:2707` compares the worlds
  against sampled full-layer dimensions through
  `DirectionalGenericWorldIsFullFrame` at line 2378. Default zero blur passes;
  nondefault blur triggers the guard. P02j's retained original excerpts
  (`P02j-evidence/original-geometry-excerpts.txt`, worker `0x180004a20`)
  establish that working planes derive from input-world dimensions and
  PreRender forwards the request; output extent controls Iterate.
  T15b's 295/300 exact Smart rows include downsample and ROI but do not prove
  this exact cropped-checkout case.
  INFERENCE: this is a remaining Mac-only full-layer admission restriction,
  likely to make such a valid cropped checkout black in AE. Original acceptance
  at these exact sizes/parameters is unmeasured; get a small original witness
  and native checkout trace before changing the guard. Unlike Smoother2 below,
  these input/output worlds are equal-sized.

- **DistanceGradation / `RenderBits:pf32-smart-profile@2201`**.
  FACT: all default PF32 probes fail the explicit union of retained admission
  profiles at `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:2180–2201`.
  T15b legal-default original calibration completed PF32 at 1080×1080 in 0.9041 s
  (`T15b-odd-even-random-comp-sweep.md`, calibration table and
  `T15b-evidence/olmdistancegradation-calibration.json`). Its original full-HD
  PF32 limitation is the oracle arena, not a measured AEX profile rejection.
  IMPORTANT: the fuzz adapter clamps DistanceGradation’s out-of-range builder
  In/Out default 0 to legal value 1. P00 uses the real PARAMS_SETUP defaults.
  Therefore T15b alone does not prove original acceptance of this exact default.
  The new `original-default-probe.json` closes that boundary: at 32×24 with
  zero parameter overrides, the registered F52c original succeeds at all three
  depths, while the real Mac bundle returns 516 with this tag only at PF32.
  Original guard/session checks pass; AEX and worker hashes and output hashes
  are retained. INFERENCE: this is a confirmed Mac-only default PF32 admission
  group; original success at 4K remains unmeasured.

- **Smoother2 / `ValidatePublicWorlds:validate-world-shape@5240`**.
  FACT: cropped-expand supplies 960×540 input and allocates 1920×1080 output
  from Mac PreRender. The check is in
  `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp:5240`. P02f retained disassembly
  (`P02f-evidence/static.json`) identifies original worker `0x180003eb0`,
  dimension comparisons `0x180003f16..0x180003f4e`, and the mismatch branch
  `0x180004244` constructing invalid_argument from `0x180022410`.
  F52c's 7×5-to-2×2 probe reached that original check; T15b also retained
  exception-transport failures. These do not establish a native AE PF code.
  INFERENCE: original plausibly fails the same unequal-world contract too;
  do not remove the guard. Whether Mac PreRender unnecessarily creates this
  unequal layout in native AE remains a negotiation question.

- **Smoother v1 / `world-depth-32-unsupported`** (if observed).
  FACT: Smoother does not advertise FLOAT_COLOR_AWARE. T15b original calibration
  rejects PF32 even at 1×1, and its sweep has 112 unsupported-PF32 rows.
  INFERENCE: a deliberate direct PF32 host call is unsupported on both sides;
  this is not evidence that an AE 32bpc composition renders black, because AE
  can convert to the plugin's supported depth.

These are host-return observations, bounded prior evidence, and the explicitly
labelled small DistanceGradation original-AEX probe, not native-AE numerical validation. The matrix has no pixel oracle, so no pixel mismatch count or first differing
byte is claimed; the small probe establishes return behavior only.


inference:
- Successful return and nonzero output are sanity checks only; no numerical compatibility inference.
- Refusal classification and hotspot attribution remain pending until the matrix completes.

changed_files:
- `tools/fuzz/ae_realism_audit.py`: 60-second timeout, required 8bpc baseline, additional 4K probes, cache-specific registration, incremental manifests.
- `tools/fuzz/report_P00b.py`, this report and `P00b-evidence/`.
- P00 host/driver and stale evidence were brought in by the required merge.

verify:
```sh
python3 tools/fuzz/build_F47_bundles.py --scratch orchestra/state/P00b-ae-realism-audit-rerun/build
python3 tools/fuzz/ae_realism_audit.py --build-host --cache "$HOME/.cache/olm-emu/P00b" --state orchestra/state/P00b-ae-realism-audit-rerun
python3 tools/fuzz/ae_realism_audit.py --phase baseline --jobs 1 --timeout 60 --cache "$HOME/.cache/olm-emu/P00b" --state orchestra/state/P00b-ae-realism-audit-rerun
python3 tools/fuzz/ae_realism_audit.py --phase matrix --jobs 1 --timeout 60 --cache "$HOME/.cache/olm-emu/P00b" --state orchestra/state/P00b-ae-realism-audit-rerun
python3 tools/fuzz/report_P00b.py
git diff --check
```
Expected complete coverage: 60 baseline rows and 6930 matrix rows. Checkpoint counts above are measured, not a completion claim. Build products must be installed under P00b/xcode before running the host.

next:
- Finish matrix; profile each slow full-size default/heaviest-corpus performance cell.
- Classify each remaining refusal against F52c/T15b evidence and current source before proposing fix tickets.
- Retain ten independent exact ColorKeep corpus tuples in a separate coverage ticket.
