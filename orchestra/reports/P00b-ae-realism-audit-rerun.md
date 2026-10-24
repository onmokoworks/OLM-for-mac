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

matrix: 741 rows; {'ok': 738, 'refusal': 3}

| Plugin / situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| olmblur / full | {'ok': 30} | {} | 30/30 |
| olmblur / half | {'ok': 30} | {} | 30/30 |
| olmblur / quarter | {'ok': 30} | {} | 30/30 |
| olmblur / third | {'ok': 30} | {} | 30/30 |
| olmblur / eighth | {'ok': 30} | {} | 30/30 |
| olmblur / asymmetric | {'ok': 30} | {} | 30/30 |
| olmblur / 4k | {'ok': 30} | {} | 30/30 |
| olmblur / 4k-half | {'ok': 27} | {} | 27/27 |
| olmblur / 4k-quarter | {'ok': 27} | {} | 27/27 |
| olmblur / square | {'ok': 27} | {} | 27/27 |
| olmblur / odd | {'ok': 27} | {} | 27/27 |
| olmblur / odd-half | {'ok': 27} | {} | 27/27 |
| olmblur / large-layer | {'ok': 27} | {} | 27/27 |
| olmblur / aligned-odd | {'ok': 27} | {} | 27/27 |
| olmblur / padded | {'ok': 27} | {} | 27/27 |
| olmblur / extent | {'ok': 27} | {} | 27/27 |
| olmblur / roi | {'ok': 27} | {} | 27/27 |
| olmblur / expanded | {'ok': 27} | {} | 27/27 |
| olmblur / cropped-expand | {'ok': 27} | {} | 27/27 |
| olmblur / aspect09 | {'ok': 27} | {} | 27/27 |
| olmblur / aspect2 | {'ok': 27} | {} | 27/27 |
| olmdirectionalblur / full | {'ok': 9} | {} | 9/9 |
| olmdirectionalblur / half | {'ok': 9} | {} | 9/9 |
| olmdirectionalblur / quarter | {'ok': 9} | {} | 9/9 |
| olmdirectionalblur / third | {'ok': 9} | {} | 9/9 |
| olmdirectionalblur / eighth | {'ok': 9} | {} | 9/9 |
| olmdirectionalblur / asymmetric | {'ok': 9} | {} | 9/9 |
| olmdirectionalblur / 4k | {'ok': 9} | {} | 9/9 |
| olmdirectionalblur / 4k-half | {'ok': 9} | {} | 9/9 |
| olmdirectionalblur / 4k-quarter | {'ok': 9} | {} | 9/9 |
| olmdirectionalblur / square | {'ok': 6} | {} | 6/6 |
| olmdirectionalblur / odd | {'ok': 6} | {} | 6/6 |
| olmdirectionalblur / odd-half | {'ok': 6} | {} | 6/6 |
| olmdirectionalblur / large-layer | {'ok': 6} | {} | 6/6 |
| olmdirectionalblur / aligned-odd | {'ok': 6} | {} | 6/6 |
| olmdirectionalblur / padded | {'ok': 6} | {} | 6/6 |
| olmdirectionalblur / extent | {'ok': 6} | {} | 6/6 |
| olmdirectionalblur / roi | {'ok': 6} | {} | 6/6 |
| olmdirectionalblur / expanded | {'ok': 6} | {} | 6/6 |
| olmdirectionalblur / cropped-expand | {'ok': 3, 'refusal': 3} | {'SmartRender:smart-generic-world-or-budget@2707': 3} | 3/3 |
| olmdirectionalblur / aspect09 | {'ok': 6} | {} | 6/6 |
| olmdirectionalblur / aspect2 | {'ok': 6} | {} | 6/6 |

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
