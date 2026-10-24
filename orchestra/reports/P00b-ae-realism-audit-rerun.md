status: partial
summary:
- Fresh-bundle audit checkpoint; matrix/performance work is still in progress.
- No plugin source, release gate, ledger, MAIN or AEXCompat edits.

facts:
- Source build HEAD: d1b18b9accaee821543548c1d2d7adf33781dcca (merge of P00).
- Host and bundle identities, parameter paths/hashes and raw rows are in `P00b-evidence/`.
- This is an oracle-free SDK host loading real arm64 plugin bundles, not native AE or a pixel-exact comparison.
- Matrix uses independent host-shape probes, with two additional 4K downsample probes.
- ColorKeep has zero eligible corpus files. ColorKey/KiraKira/Smoother2 sample with replacement (9/8/8 unique paths).
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

matrix: 4723 rows; {'ok': 4619, 'refusal': 104}

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
| colorkeep / full | {'ok': 3} | {} | 3/3 |
| colorkeep / half | {'ok': 3} | {} | 3/3 |
| colorkeep / quarter | {'ok': 3} | {} | 3/3 |
| colorkeep / third | {'ok': 3} | {} | 3/3 |
| colorkeep / eighth | {'ok': 3} | {} | 3/3 |
| colorkeep / asymmetric | {'ok': 3} | {} | 3/3 |
| colorkeep / 4k | {'ok': 3} | {} | 3/3 |
| colorkeep / 4k-half | {'ok': 3} | {} | 3/3 |
| colorkeep / 4k-quarter | {'ok': 3} | {} | 3/3 |
| colorkeep / square | {'ok': 3} | {} | 3/3 |
| colorkeep / odd | {'ok': 3} | {} | 3/3 |
| colorkeep / odd-half | {'ok': 3} | {} | 3/3 |
| colorkeep / large-layer | {'ok': 3} | {} | 3/3 |
| colorkeep / aligned-odd | {'ok': 3} | {} | 3/3 |
| colorkeep / padded | {'ok': 3} | {} | 3/3 |
| colorkeep / extent | {'ok': 3} | {} | 3/3 |
| colorkeep / roi | {'ok': 3} | {} | 3/3 |
| colorkeep / expanded | {'ok': 3} | {} | 3/3 |
| colorkeep / cropped-expand | {'ok': 3} | {} | 3/3 |
| colorkeep / aspect09 | {'ok': 3} | {} | 3/3 |
| colorkeep / aspect2 | {'ok': 3} | {} | 3/3 |
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
| olmsmoother / full | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / half | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / quarter | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / third | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / eighth | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / asymmetric | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / 4k | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / 4k-half | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / 4k-quarter | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / square | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / odd | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / odd-half | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / large-layer | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / aligned-odd | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / padded | {'ok': 4, 'refusal': 2} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 2} | 4/4 |
| olmsmoother / extent | {'ok': 3, 'refusal': 1} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 1} | 3/3 |
| olmsmoother / roi | {'ok': 2, 'refusal': 1} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 1} | 2/2 |
| olmsmoother / expanded | {'ok': 2, 'refusal': 1} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 1} | 2/2 |
| olmsmoother / cropped-expand | {'ok': 2, 'refusal': 1} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 1} | 2/2 |
| olmsmoother / aspect09 | {'ok': 2, 'refusal': 1} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 1} | 2/2 |
| olmsmoother / aspect2 | {'ok': 2, 'refusal': 1} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 1} | 2/2 |
| olmdirectionalblur / full | {'ok': 21} | {} | 21/21 |
| olmdirectionalblur / half | {'ok': 21} | {} | 21/21 |
| olmdirectionalblur / quarter | {'ok': 21} | {} | 21/21 |
| olmdirectionalblur / third | {'ok': 21} | {} | 21/21 |
| olmdirectionalblur / eighth | {'ok': 21} | {} | 21/21 |
| olmdirectionalblur / asymmetric | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / 4k | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / 4k-half | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / 4k-quarter | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / square | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / odd | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / odd-half | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / large-layer | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / aligned-odd | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / padded | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / extent | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / roi | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / expanded | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / cropped-expand | {'ok': 4, 'refusal': 14} | {'SmartRender:smart-generic-world-or-budget@2707': 14} | 4/4 |
| olmdirectionalblur / aspect09 | {'ok': 18} | {} | 18/18 |
| olmdirectionalblur / aspect2 | {'ok': 18} | {} | 18/18 |

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
Expected complete coverage: 60 baseline rows and 6300 matrix rows. Checkpoint counts above are measured, not a completion claim. Build products must be installed under P00b/xcode before running the host.

next:
- Finish matrix; profile each slow full-size default/heaviest-corpus performance cell.
- Classify each remaining refusal against F52c/T15b evidence and current source before proposing fix tickets.
- Retain ten independent exact ColorKeep corpus tuples in a separate coverage ticket.
