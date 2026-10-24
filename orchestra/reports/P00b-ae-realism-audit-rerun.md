status: done
summary:

- Fresh Universal Release bundles audited through the SDK host; native AE and pixel exactness are not claimed.
- No plugin source, release gate, ledger, MAIN or AEXCompat edits.
- Baseline: 60 rows, {'ok': 60}.
- Matrix: 6930 rows, {'ok': 6555, 'refusal': 314, 'timeout': 61}.
- All 25 slow default/heaviest performance cells have successful stack samples; concrete follow-up tickets are listed below.

facts:

- Runtime: Apple M1 Pro, 16 GiB, macOS 15.7.2 (24G325), native arm64 host. Shared-machine single-frame measurements; recorded memory checks are in `P00b-evidence/runtime.json`.
- Verification: `python3 tools/fuzz/verify_P00b.py` passed all cell-coverage, profile and cache-hash checks; exact output is retained in `P00b-evidence/verification.txt`.
- Source build HEAD: d1b18b9accaee821543548c1d2d7adf33781dcca (merge of P00).
- Host and bundle identities, parameter paths/hashes and raw rows are in `P00b-evidence/`.
- This is an oracle-free SDK host loading real arm64 plugin bundles, not native AE or a pixel-exact comparison.
- Unlisted status counts are zero; OK nonzero counts refer to active output bytes only.
- Matrix uses independent host-shape probes, with two additional 4K downsample probes. ROI keeps the full source world; large-layer is a comp-sized viewport, not a compositor. Expansion occurs only when PreRender asks for larger bounds; the situation label alone does not prove expansion.
- ColorKeep uses three nested T15b anchors sampled with replacement; ColorKey/KiraKira/Smoother2 also sample with replacement (9/8/8 unique paths).
- Corpus values are reused unchanged, including absolute point coordinates from small original cases; this is not a rescaled artistic preset benchmark.
- Timeouts are 60-second process wall limits; successful times below are render-selector seconds.

- Fresh Universal Release build: `python3 tools/fuzz/build_F47_bundles.py --scratch orchestra/state/P00b-ae-realism-audit-rerun/build` completed for all ten bundles; products were copied to the registered P00b cache and scratch xcode trees removed.
- Initial host baseline: 54 OK / 6 ColorKeep iterate host errors; after the host-only rectangle correction: 60 OK. `test_P00b_iterate.cpp` compiled and exited 0.
- Original default probe: `python3 tools/fuzz/probe_P00b_defaults.py`; 32x24 original Smart succeeds at PF8/PF16/PF32, real Mac PF32 returns 516 (the two lower depths return zero). See the hash-bound JSON.
- Native process profiling uses `sample PID 2 1 -file PATH`; live profiles and separate default/heaviest-cell reruns are retained. No Instruments, oracle rebuild, plugin source change or pixel oracle in the matrix.
- All runs use `--jobs 1 --timeout 60`; at most two rendering/oracle processes run concurrently. Interrupted in-flight calls while splitting lanes were discarded and rerun; only completed rows/timeouts are counted.

baseline: 60 rows; {'ok': 60}

**OLMBlur**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 1} | {} | 1/1 |
| half | {'ok': 1} | {} | 1/1 |
| quarter | {'ok': 1} | {} | 1/1 |
| 4k | {'ok': 1} | {} | 1/1 |
| 4k-half | {'ok': 1} | {} | 1/1 |
| 4k-quarter | {'ok': 1} | {} | 1/1 |

**ColorKeep**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 1} | {} | 1/1 |
| half | {'ok': 1} | {} | 1/1 |
| quarter | {'ok': 1} | {} | 1/1 |
| 4k | {'ok': 1} | {} | 1/1 |
| 4k-half | {'ok': 1} | {} | 1/1 |
| 4k-quarter | {'ok': 1} | {} | 1/1 |

**OLMColorKey**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 1} | {} | 1/1 |
| half | {'ok': 1} | {} | 1/1 |
| quarter | {'ok': 1} | {} | 1/1 |
| 4k | {'ok': 1} | {} | 1/1 |
| 4k-half | {'ok': 1} | {} | 1/1 |
| 4k-quarter | {'ok': 1} | {} | 1/1 |

**OLMDirectionalBlur**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 1} | {} | 1/1 |
| half | {'ok': 1} | {} | 1/1 |
| quarter | {'ok': 1} | {} | 1/1 |
| 4k | {'ok': 1} | {} | 1/1 |
| 4k-half | {'ok': 1} | {} | 1/1 |
| 4k-quarter | {'ok': 1} | {} | 1/1 |

**OLMDistanceGradation**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 1} | {} | 0/1 |
| half | {'ok': 1} | {} | 0/1 |
| quarter | {'ok': 1} | {} | 0/1 |
| 4k | {'ok': 1} | {} | 0/1 |
| 4k-half | {'ok': 1} | {} | 0/1 |
| 4k-quarter | {'ok': 1} | {} | 0/1 |

**OLMKiraKira**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 1} | {} | 1/1 |
| half | {'ok': 1} | {} | 1/1 |
| quarter | {'ok': 1} | {} | 1/1 |
| 4k | {'ok': 1} | {} | 1/1 |
| 4k-half | {'ok': 1} | {} | 1/1 |
| 4k-quarter | {'ok': 1} | {} | 1/1 |

**OLMSmoother2**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 1} | {} | 1/1 |
| half | {'ok': 1} | {} | 1/1 |
| quarter | {'ok': 1} | {} | 1/1 |
| 4k | {'ok': 1} | {} | 1/1 |
| 4k-half | {'ok': 1} | {} | 1/1 |
| 4k-quarter | {'ok': 1} | {} | 1/1 |

**OLMToonDilate**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 1} | {} | 1/1 |
| half | {'ok': 1} | {} | 1/1 |
| quarter | {'ok': 1} | {} | 1/1 |
| 4k | {'ok': 1} | {} | 1/1 |
| 4k-half | {'ok': 1} | {} | 1/1 |
| 4k-quarter | {'ok': 1} | {} | 1/1 |

**OLMRadialBlur**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 1} | {} | 1/1 |
| half | {'ok': 1} | {} | 1/1 |
| quarter | {'ok': 1} | {} | 1/1 |
| 4k | {'ok': 1} | {} | 1/1 |
| 4k-half | {'ok': 1} | {} | 1/1 |
| 4k-quarter | {'ok': 1} | {} | 1/1 |

**OLMSmoother**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 1} | {} | 1/1 |
| half | {'ok': 1} | {} | 1/1 |
| quarter | {'ok': 1} | {} | 1/1 |
| 4k | {'ok': 1} | {} | 1/1 |
| 4k-half | {'ok': 1} | {} | 1/1 |
| 4k-quarter | {'ok': 1} | {} | 1/1 |

matrix: 6930 rows; {'ok': 6555, 'refusal': 314, 'timeout': 61}

**OLMBlur**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 33} | {} | 33/33 |
| half | {'ok': 33} | {} | 33/33 |
| quarter | {'ok': 33} | {} | 33/33 |
| third | {'ok': 33} | {} | 33/33 |
| eighth | {'ok': 33} | {} | 33/33 |
| asymmetric | {'ok': 33} | {} | 33/33 |
| 4k | {'ok': 33} | {} | 33/33 |
| 4k-half | {'ok': 33} | {} | 33/33 |
| 4k-quarter | {'ok': 33} | {} | 33/33 |
| square | {'ok': 33} | {} | 33/33 |
| odd | {'ok': 33} | {} | 33/33 |
| odd-half | {'ok': 33} | {} | 33/33 |
| large-layer | {'ok': 33} | {} | 33/33 |
| aligned-odd | {'ok': 33} | {} | 33/33 |
| padded | {'ok': 33} | {} | 33/33 |
| extent | {'ok': 33} | {} | 33/33 |
| roi | {'ok': 33} | {} | 33/33 |
| expanded | {'ok': 33} | {} | 33/33 |
| cropped-expand | {'ok': 33} | {} | 33/33 |
| aspect09 | {'ok': 33} | {} | 33/33 |
| aspect2 | {'ok': 33} | {} | 33/33 |

**ColorKeep**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 33} | {} | 33/33 |
| half | {'ok': 33} | {} | 33/33 |
| quarter | {'ok': 33} | {} | 33/33 |
| third | {'ok': 33} | {} | 33/33 |
| eighth | {'ok': 33} | {} | 33/33 |
| asymmetric | {'ok': 33} | {} | 33/33 |
| 4k | {'ok': 33} | {} | 33/33 |
| 4k-half | {'ok': 33} | {} | 33/33 |
| 4k-quarter | {'ok': 33} | {} | 33/33 |
| square | {'ok': 33} | {} | 33/33 |
| odd | {'ok': 33} | {} | 33/33 |
| odd-half | {'ok': 33} | {} | 33/33 |
| large-layer | {'ok': 33} | {} | 33/33 |
| aligned-odd | {'ok': 33} | {} | 33/33 |
| padded | {'ok': 33} | {} | 33/33 |
| extent | {'ok': 33} | {} | 33/33 |
| roi | {'ok': 33} | {} | 33/33 |
| expanded | {'ok': 33} | {} | 33/33 |
| cropped-expand | {'ok': 33} | {} | 33/33 |
| aspect09 | {'ok': 33} | {} | 33/33 |
| aspect2 | {'ok': 33} | {} | 33/33 |

**OLMColorKey**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 33} | {} | 33/33 |
| half | {'ok': 33} | {} | 33/33 |
| quarter | {'ok': 33} | {} | 33/33 |
| third | {'ok': 33} | {} | 33/33 |
| eighth | {'ok': 33} | {} | 33/33 |
| asymmetric | {'ok': 33} | {} | 33/33 |
| 4k | {'ok': 33} | {} | 33/33 |
| 4k-half | {'ok': 33} | {} | 33/33 |
| 4k-quarter | {'ok': 33} | {} | 33/33 |
| square | {'ok': 33} | {} | 33/33 |
| odd | {'ok': 33} | {} | 33/33 |
| odd-half | {'ok': 33} | {} | 33/33 |
| large-layer | {'ok': 33} | {} | 33/33 |
| aligned-odd | {'ok': 33} | {} | 33/33 |
| padded | {'ok': 33} | {} | 33/33 |
| extent | {'ok': 33} | {} | 33/33 |
| roi | {'ok': 33} | {} | 33/33 |
| expanded | {'ok': 33} | {} | 33/33 |
| cropped-expand | {'ok': 33} | {} | 33/33 |
| aspect09 | {'ok': 33} | {} | 33/33 |
| aspect2 | {'ok': 33} | {} | 33/33 |

**OLMDirectionalBlur**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 33} | {} | 33/33 |
| half | {'ok': 33} | {} | 33/33 |
| quarter | {'ok': 33} | {} | 33/33 |
| third | {'ok': 33} | {} | 33/33 |
| eighth | {'ok': 33} | {} | 33/33 |
| asymmetric | {'ok': 33} | {} | 33/33 |
| 4k | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| 4k-half | {'ok': 33} | {} | 33/33 |
| 4k-quarter | {'ok': 33} | {} | 33/33 |
| square | {'ok': 33} | {} | 33/33 |
| odd | {'ok': 33} | {} | 33/33 |
| odd-half | {'ok': 33} | {} | 33/33 |
| large-layer | {'ok': 33} | {} | 33/33 |
| aligned-odd | {'ok': 33} | {} | 33/33 |
| padded | {'ok': 33} | {} | 33/33 |
| extent | {'ok': 33} | {} | 33/33 |
| roi | {'ok': 33} | {} | 33/33 |
| expanded | {'ok': 33} | {} | 33/33 |
| cropped-expand | {'ok': 4, 'refusal': 29} | {'SmartRender:smart-generic-world-or-budget@2707': 29} | 4/4 |
| aspect09 | {'ok': 33} | {} | 33/33 |
| aspect2 | {'ok': 33} | {} | 33/33 |

**OLMDistanceGradation**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| half | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| quarter | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| third | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| eighth | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| asymmetric | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| 4k | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| 4k-half | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| 4k-quarter | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| square | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| odd | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| odd-half | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| large-layer | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| aligned-odd | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| padded | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| extent | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 32/32 |
| roi | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| expanded | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| cropped-expand | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| aspect09 | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |
| aspect2 | {'ok': 32, 'refusal': 1} | {'RenderBits:pf32-smart-profile@2201': 1} | 0/32 |

**OLMKiraKira**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 33} | {} | 33/33 |
| half | {'ok': 33} | {} | 33/33 |
| quarter | {'ok': 33} | {} | 33/33 |
| third | {'ok': 33} | {} | 33/33 |
| eighth | {'ok': 33} | {} | 33/33 |
| asymmetric | {'ok': 33} | {} | 33/33 |
| 4k | {'ok': 33} | {} | 33/33 |
| 4k-half | {'ok': 33} | {} | 33/33 |
| 4k-quarter | {'ok': 33} | {} | 33/33 |
| square | {'ok': 33} | {} | 33/33 |
| odd | {'ok': 33} | {} | 33/33 |
| odd-half | {'ok': 33} | {} | 33/33 |
| large-layer | {'ok': 33} | {} | 33/33 |
| aligned-odd | {'ok': 33} | {} | 33/33 |
| padded | {'ok': 33} | {} | 33/33 |
| extent | {'ok': 33} | {} | 33/33 |
| roi | {'ok': 33} | {} | 33/33 |
| expanded | {'ok': 33} | {} | 33/33 |
| cropped-expand | {'ok': 33} | {} | 33/33 |
| aspect09 | {'ok': 33} | {} | 33/33 |
| aspect2 | {'ok': 33} | {} | 33/33 |

**OLMSmoother2**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 33} | {} | 33/33 |
| half | {'ok': 33} | {} | 33/33 |
| quarter | {'ok': 33} | {} | 33/33 |
| third | {'ok': 33} | {} | 33/33 |
| eighth | {'ok': 33} | {} | 33/33 |
| asymmetric | {'ok': 33} | {} | 33/33 |
| 4k | {'ok': 33} | {} | 33/33 |
| 4k-half | {'ok': 33} | {} | 33/33 |
| 4k-quarter | {'ok': 33} | {} | 33/33 |
| square | {'ok': 33} | {} | 33/33 |
| odd | {'ok': 33} | {} | 33/33 |
| odd-half | {'ok': 33} | {} | 33/33 |
| large-layer | {'ok': 33} | {} | 33/33 |
| aligned-odd | {'ok': 33} | {} | 33/33 |
| padded | {'ok': 33} | {} | 33/33 |
| extent | {'ok': 33} | {} | 33/33 |
| roi | {'ok': 33} | {} | 33/33 |
| expanded | {'ok': 33} | {} | 33/33 |
| cropped-expand | {'refusal': 33} | {'ValidatePublicWorlds:validate-world-shape@5240': 33} | 0/0 |
| aspect09 | {'ok': 33} | {} | 33/33 |
| aspect2 | {'ok': 33} | {} | 33/33 |

**OLMToonDilate**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 33} | {} | 33/33 |
| half | {'ok': 33} | {} | 33/33 |
| quarter | {'ok': 33} | {} | 33/33 |
| third | {'ok': 33} | {} | 33/33 |
| eighth | {'ok': 33} | {} | 33/33 |
| asymmetric | {'ok': 33} | {} | 33/33 |
| 4k | {'ok': 33} | {} | 33/33 |
| 4k-half | {'ok': 33} | {} | 33/33 |
| 4k-quarter | {'ok': 33} | {} | 33/33 |
| square | {'ok': 33} | {} | 33/33 |
| odd | {'ok': 33} | {} | 33/33 |
| odd-half | {'ok': 33} | {} | 33/33 |
| large-layer | {'ok': 33} | {} | 33/33 |
| aligned-odd | {'ok': 33} | {} | 33/33 |
| padded | {'ok': 33} | {} | 33/33 |
| extent | {'ok': 33} | {} | 33/33 |
| roi | {'ok': 33} | {} | 33/33 |
| expanded | {'ok': 33} | {} | 33/33 |
| cropped-expand | {'ok': 33} | {} | 33/33 |
| aspect09 | {'ok': 33} | {} | 33/33 |
| aspect2 | {'ok': 33} | {} | 33/33 |

**OLMRadialBlur**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| half | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| quarter | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| third | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| eighth | {'ok': 33} | {} | 33/33 |
| asymmetric | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| 4k | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| 4k-half | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| 4k-quarter | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| square | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| odd | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| odd-half | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| large-layer | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| aligned-odd | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| padded | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| extent | {'ok': 32, 'timeout': 1} | {} | 32/32 |
| roi | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| expanded | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| cropped-expand | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| aspect09 | {'ok': 30, 'timeout': 3} | {} | 30/30 |
| aspect2 | {'ok': 30, 'timeout': 3} | {} | 30/30 |

**OLMSmoother**

| Situation | Status counts | Refusal tags | OK nonzero / OK |
|---|---|---|---|
| full | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| half | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| quarter | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| third | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| eighth | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| asymmetric | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| 4k | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| 4k-half | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| 4k-quarter | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| square | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| odd | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| odd-half | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| large-layer | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| aligned-odd | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| padded | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| extent | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| roi | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| expanded | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| cropped-expand | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| aspect09 | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |
| aspect2 | {'ok': 22, 'refusal': 11} | {'ValidatePublicWorlds:world-depth-32-unsupported@4062': 11} | 22/22 |

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
| olmdirectionalblur | 8 | 0.003 | 0.010 | **17.579** (corpus09) | >=60 wall (timeout) (corpus09) |
| olmdirectionalblur | 16 | 0.004 | 0.017 | **17.662** (corpus09) | >=60 wall (timeout) (corpus09) |
| olmdirectionalblur | 32 | 0.008 | 0.038 | **17.571** (corpus09) | >=60 wall (timeout) (corpus09) |
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
| radialblur | 8 | 0.002 | 0.004 | **>=60 wall (timeout)** (corpus05) | >=60 wall (timeout) (corpus05) |
| radialblur | 16 | 0.002 | 0.010 | **>=60 wall (timeout)** (corpus05) | >=60 wall (timeout) (corpus05) |
| radialblur | 32 | 0.005 | 0.024 | **>=60 wall (timeout)** (corpus05) | >=60 wall (timeout) (corpus05) |
| olmsmoother | 8 | 0.346 | 1.399 | 1.535 (corpus00) | 6.125 (corpus00) |
| olmsmoother | 16 | 1.077 | 4.269 | **2.151** (corpus00) | 8.585 (corpus00) |
| olmsmoother | 32 | refusal | refusal | unavailable | unavailable |

Profile reruns (sampling is separate from the performance table):
Each rerun samples a two-second window after a one-second startup delay, then deliberately stops a still-running host. `sampled_then_stopped` is not a crash or a new timeout measurement. Late live profiles additionally identify DirectionalBlur scatter and RadialBlur rotation; sampled leaf counts are not whole-frame time fractions.

| Cell | Corpus identity | Rerun status | sample exit | Top sampled leaf functions |
|---|---|---|---|---|
| olmdirectionalblur-heaviest-full-8 | corpus09 | sampled_then_stopped | 0 | olm_dblur_scatter_f32; olm::x86_float::sse_result(float, float, float); olm::x86_float::generated_nan(float, float, float) |
| olmdirectionalblur-heaviest-full-16 | corpus09 | sampled_then_stopped | 0 | olm_dblur_scatter_f32; olm::x86_float::sse_result(float, float, float); olm::x86_float::generated_nan(float, float, float) |
| olmdirectionalblur-heaviest-full-32 | corpus09 | sampled_then_stopped | 0 | olm_dblur_scatter_f32; olm::x86_float::sse_result(float, float, float); olm::x86_float::generated_nan(float, float, float) |
| olmdirectionalblur-heaviest-4k-8 | corpus09 | sampled_then_stopped | 0 | olm::x86_float::sse_result(float, float, float); olm::x86_float::generated_nan(float, float, float); (anonymous namespace)::fmul(float, float) |
| olmdirectionalblur-heaviest-4k-16 | corpus09 | sampled_then_stopped | 0 | olm::x86_float::sse_result(float, float, float); olm::x86_float::generated_nan(float, float, float); olm::x86_float::bits(float) |
| olmdirectionalblur-heaviest-4k-32 | corpus09 | sampled_then_stopped | 0 | olm::x86_float::sse_result(float, float, float); olm::x86_float::generated_nan(float, float, float); olm::x86_float::bits(float) |
| radialblur-heaviest-full-8 | corpus05 | sampled_then_stopped | 0 | SampleScalarAEXNoRepeat(std::vector<float> const&, int, int, float, float); RadialAEXSinHot(float); int RenderRotationTyped<PF_Pixel>(PF_LayerDef*, PF_LayerDef*, OLMRadialBlurInfo const&) |
| radialblur-heaviest-full-16 | corpus05 | sampled_then_stopped | 0 | SampleScalarAEXNoRepeat(std::vector<float> const&, int, int, float, float); RadialAEXSinHot(float); int RenderRotationTyped<PF_Pixel16>(PF_LayerDef*, PF_LayerDef*, OLMRadialBlurInfo const&) |
| radialblur-heaviest-full-32 | corpus05 | sampled_then_stopped | 0 | SampleScalarAEXNoRepeat(std::vector<float> const&, int, int, float, float); RadialAEXSinHot(float); int RenderRotationTyped<PF_PixelFloat>(PF_LayerDef*, PF_LayerDef*, OLMRadialBlurInfo const&) |
| radialblur-heaviest-4k-8 | corpus05 | sampled_then_stopped | 0 | SampleScalarAEXNoRepeat(std::vector<float> const&, int, int, float, float); RadialAEXSinHot(float); int RenderRotationTyped<PF_Pixel>(PF_LayerDef*, PF_LayerDef*, OLMRadialBlurInfo const&) |
| radialblur-heaviest-4k-16 | corpus05 | sampled_then_stopped | 0 | SampleScalarAEXNoRepeat(std::vector<float> const&, int, int, float, float); RadialAEXSinHot(float); int RenderRotationTyped<PF_Pixel16>(PF_LayerDef*, PF_LayerDef*, OLMRadialBlurInfo const&) |
| radialblur-heaviest-4k-32 | corpus05 | sampled_then_stopped | 0 | SampleScalarAEXNoRepeat(std::vector<float> const&, int, int, float, float); RadialAEXSinHot(float); int RenderRotationTyped<PF_PixelFloat>(PF_LayerDef*, PF_LayerDef*, OLMRadialBlurInfo const&) |
| olmblur-heaviest-full-8 | corpus05 | completed | 0 | olm::blur::vertical(unsigned char const*, float const*, float*, float const*, olm::blur::HelperParams const&); olm::blur::horizontal(unsigned char const*, float const*, float*, float const*, olm::blur::HelperParams const&); mach_msg2_trap |
| olmblur-heaviest-full-16 | corpus05 | completed | 0 | olm::blur::vertical(unsigned char const*, float const*, float*, float const*, olm::blur::HelperParams const&); olm::blur::horizontal(unsigned char const*, float const*, float*, float const*, olm::blur::HelperParams const&); mach_msg2_trap |
| olmblur-heaviest-full-32 | corpus05 | completed | 0 | olm::blur::vertical(unsigned char const*, float const*, float*, float const*, olm::blur::HelperParams const&); olm::blur::horizontal(unsigned char const*, float const*, float*, float const*, olm::blur::HelperParams const&); mach_msg2_trap |
| olmblur-heaviest-4k-8 | corpus05 | sampled_then_stopped | 0 | olm::blur::horizontal(unsigned char const*, float const*, float*, float const*, olm::blur::HelperParams const&) |
| olmblur-heaviest-4k-16 | corpus05 | sampled_then_stopped | 0 | olm::blur::horizontal(unsigned char const*, float const*, float*, float const*, olm::blur::HelperParams const&) |
| olmblur-heaviest-4k-32 | corpus05 | sampled_then_stopped | 0 | olm::blur::horizontal(unsigned char const*, float const*, float*, float const*, olm::blur::HelperParams const&) |
| olmcolorkey-heaviest-4k-8 | corpus05 | sampled_then_stopped | 0 | ucrt_powf; RGBToPluginLab76(float const*, float*); ucrt_atan2f |
| olmcolorkey-heaviest-4k-16 | corpus05 | sampled_then_stopped | 0 | ucrt_powf; RGBToPluginLab76(float const*, float*); ucrt_atan2f |
| olmcolorkey-heaviest-4k-32 | corpus05 | sampled_then_stopped | 0 | ucrt_powf; RGBToPluginLab76(float const*, float*); ucrt_atan2f |
| olmsmoother-heaviest-full-16 | corpus00 | completed | 0 | _platform_memset; SubHandler8Memory::read32(unsigned long long) const; EdgeWalker16Exact(RenderState*, int, int, int, unsigned int, int*, int*, int) |
| olmsmoother-heaviest-4k-8 | corpus00 | sampled_then_stopped | 0 | SubHandler8Memory::read32(unsigned long long) const; EdgeWalker8(RenderState*, int, int, int, unsigned int, int*, int*, int); _platform_memset |
| olmsmoother-default-4k-16 | default | sampled_then_stopped | 0 | _platform_memset; Classifier16Exact(RenderState*, unsigned int, unsigned int, unsigned long const*, unsigned int); SubHandler8Memory::read32(unsigned long long) const |
| olmsmoother-heaviest-4k-16 | corpus00 | sampled_then_stopped | 0 | _platform_memset; SubHandler8Memory::read32(unsigned long long) const; EdgeWalker16Exact(RenderState*, int, int, int, unsigned int, int*, int*, int) |

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
  group; original success at 4K remains unmeasured. The three original 32×24
  output hashes match all-zero raw buffers of their recorded lengths. Thus the
  Mac PF8/PF16 all-zero sanity result has a bounded original counterpart; an
  all-zero output alone is not classified as a refusal.

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

- **Smoother v1 / `world-depth-32-unsupported@4062`**.
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
- The classification above distinguishes observed return behavior from original-host and native-AE inference.

changed_files:

- `tools/fuzz/ae_realism_audit.py`: 60-second timeout, required 8bpc baseline, additional 4K probes, cache-specific registration, incremental manifests.
- `tools/emulation/aexcompat_patches/P00-host-realism.{cpp,md}`: SDK iterate clipping and rerun documentation.
- `tools/fuzz/{report_P00b,profile_P00b,probe_P00b_defaults,verify_P00b}.py`, `test_P00b_iterate.cpp`, this report and `P00b-evidence/`.
- P00 host/driver and stale evidence were brought in by the required merge.

verify:
Read-only evidence check first; optional full rerun uses a fresh subdirectory and the registered binaries. Timing/timeout boundaries may vary with shared-machine load.
```sh
python3 tools/fuzz/verify_P00b.py
mkdir -p orchestra/state/P00b-ae-realism-audit-rerun/recheck
export TMPDIR="$PWD/orchestra/state/P00b-ae-realism-audit-rerun/recheck" PYTHONDONTWRITEBYTECODE=1
scripts/setup_ae_sdk_links.sh > "$TMPDIR/sdk-links.log" 2>&1
clang++ -std=c++17 -O2 -Wno-pragma-pack -IHeaders -IHeaders/SP tools/fuzz/test_P00b_iterate.cpp -o "$TMPDIR/test-iterate" > "$TMPDIR/test-build.log" 2>&1
"$TMPDIR/test-iterate"
python3 tools/fuzz/ae_realism_audit.py --phase baseline --jobs 1 --timeout 60 --cache "$HOME/.cache/olm-emu/P00b" --state "$TMPDIR" > "$TMPDIR/baseline.log" 2>&1
python3 tools/fuzz/ae_realism_audit.py --phase matrix --jobs 1 --timeout 60 --cache "$HOME/.cache/olm-emu/P00b" --state "$TMPDIR" > "$TMPDIR/matrix.log" 2>&1
python3 tools/fuzz/ae_realism_audit.py --summarize --state "$TMPDIR"
git diff --check
```
Expected: integrity OK, iterate regression exit 0, 60 baseline OK rows and 6930 unique matrix rows; compare measured status/tag counts above. The matrix is not an all-success gate. Full reruns take substantial time because every timed-out cell gets 60 seconds.

next:

- **P00c-DG-default-PF32** — confirmed Mac-only refusal group. Recover the
  original no-override In/Out=0/default PF32 owner behavior from the retained
  32×24 witness, then extend general admission with independent alpha/source
  and geometry tests. Do not insert a default-only zero-output shortcut.
- **P00c-DBlur-cropped-world** — probable Mac-only full-layer guard. Start
  with equal 960×540 checkout/output worlds under 1920×1080 layer metadata,
  plus a small original witness; reconstruct input-sized workspace/request
  handling before changing `DirectionalGenericWorldIsFullFrame` admission.
- **P00c-Sm2-checkout-contract** — qualify native/original cropped checkout
  negotiation. Preserve the original-backed equal-world guard; determine
  whether Mac's forced full-frame PreRender creates the unequal world pair.
  This is not a proposal to accept mismatched buffers blindly.
- **P00p-DBlur-rotation-softfloat** — profile `olm_dblur_rotate_rgba_f32_trig`
  and its `x86_float::{sse_result,generated_nan,bits}` calls. Optimize only with
  bit-exact independent finite/nonfinite and signed-zero regression evidence.
- **P00p-DBlur-scatter** — investigate `olm_dblur_scatter_f32` on `corpus09`,
  including the 4K timeouts and 1080p timings. Preserve scatter accumulation
  order and distinguish invariant work from arithmetic changes.
- **P00p-Radial-rotation** — investigate `RenderRotationTyped` using C45
  `C45_seed1_case000108.json` (matrix `corpus05`). The current observed boundary
  is 240×135 completing in 36.4–38.3 s versus 480×270 exceeding 60 s. Establish
  stage/work-count scaling before an exact optimization. The 1080p extent-hint/
  transparent-source variant completed near the limit at PF8/PF32 but timed out
  at PF16; separate metadata effects from alpha coverage and shared-load noise.
  Do not replace the
  timeout with a refusal budget or an approximate blur.
- **P00p-Blur-horizontal** — optimize the measured `olm::blur::horizontal`
  convolution hotspot (`corpus05`, three depths), preserving tap traversal,
  intermediate precision and output bits. Recheck both 1080p and 4K.
- **P00p-ColorKey-Lab-UCRT** — investigate `ucrt_powf` / `RGBToPluginLab76`
  and `ucrt_atan2f` in the heavy 4K Lab-distance path. Look for invariant work
  before changing arithmetic; replacing UCRT with a faster approximate math
  library is outside the bit-exact contract.
- **P00p-Smoother-scratch-memory** — investigate `_platform_memset` and
  `SubHandler8Memory::read32` in default/heavy PF16 and heavy PF8 profiles.
  Establish which clears and address translations are redundant without
  changing initialized-state or traversal semantics.
- **P00p-Smoother-edgewalk** — separately measure `EdgeWalker8`,
  `EdgeWalker16Exact` and the classifier paths after attributing scratch-memory
  cost. Preserve visit order, branching and typed arithmetic in any optimization.
- **P00c-corpus-diversity** — retain ten independent exact tuples for
  ColorKeep, ColorKey, KiraKira and Smoother2. This audit explicitly samples
  smaller corpora with replacement and does not invent independent witnesses.
