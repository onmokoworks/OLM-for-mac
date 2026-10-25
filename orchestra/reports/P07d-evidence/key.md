status: partial
summary:
- ColorKey classifier uses eight disjoint row ranges with task-local lazy Lab caches; pixel arithmetic/key order stays unchanged.
- Reference/fast 675 comparisons exact; AEX campaigns: 827 Smart exact, 23 original rejects, no mismatch or Mac-only refusal.
- Corpus 44/44 replay true; forced caps 1/2/8 and TSan each 50 cases pass.
- Before/after unit outcomes identical. Performance and concurrent-render checks are queued behind the shared benchmark lock.

facts:
- `profile_key.py`, under the required lock: sample exit 0 and host exit 0; Lab94Distance dominates the sampled classifier (1215 samples in its RenderTyped caller).
- `ref_vs_fast.py --plugin olmcolorkey --jobs 1 --parallel 1 2 8`: before and after each 675 exact, 0 refusal, 0 mismatch. First mismatch: none. Includes 200 small, 20 HD, five UHD cases and heavy presets. Driver now defaults ColorKey to all three thread caps.
- `verify.py olmcolorkey key`: default seed1 n300=300 exact; realistic-v1 seed1=91 exact/9 AEX rejects, seed2026102507=94/6; odd-even T15b seed2026 n150=142/8; realistic-v2 seeds1/2026102507 n100 each=100/0. All Smart, no mismatches or Mac-only refusals. Default pre-change n300 outputs also exactly match the after hashes. Classic's pre-existing mismatches remain outside this contract route.
- Replay: root 9, P02i 8, P05c 24, T15b 3: all true. The generic replay script now also passes each stored height ceiling explicitly.
- `key_threads.py`: 50 cases at caps1/2/8 and another 50 under TSan, all 200 executions returned successful images with equal per-case hashes; no sanitizer reports.
- `units.py olmcolorkey key-units-before/after`: identical module statuses: 30 modules, 21 exit1 and 9 exit5. `functions.py olmcolorkey key-functions-before/after`: identical eight module statuses, seven nonzero. Missing historical evidence/assets and stale pinned hashes are not fixed or called passing.
- Universal candidate built with one Xcode job; registered `~/.cache/olm-emu/P07d-key`, SHA256 `f92403bf9151a2ac31a6faf92c5a1184f9f0cb301b48a8b00a071ebbf046d1f2`. Memory free check 55%.
- The shared lock delayed initial profiling/measurement for about 19 minutes; the after matrix/concurrent runner remains queued. No timing was taken outside that lock.

Before command: `lockf -k ~/.cache/olm-emu/bench.lock python3 tools/fuzz/ae_realism_audit.py --phase matrix --plugins olmcolorkey --cases default corpus05 --situations full 4k --jobs 1 --cache ~/.cache/olm-emu/P05c-key --state orchestra/state/P07d-distancegradation-blur-colorkey-threading/key-before`. 12 OK, zero refusals. Single measurements on a shared machine can be load-affected.

| Case | Size | Depth | Before seconds | After seconds |
|---|---|---:|---:|---:|
| default | full | 8 | 0.019039 | pending lock |
| default | full | 16 | 0.022706 | pending lock |
| default | full | 32 | 0.023263 | pending lock |
| default | 4k | 8 | 0.066451 | pending lock |
| default | 4k | 16 | 0.070043 | pending lock |
| default | 4k | 32 | 0.101802 | pending lock |
| corpus05 | full | 8 | 0.766329 | pending lock |
| corpus05 | full | 16 | 0.803676 | pending lock |
| corpus05 | full | 32 | 0.764806 | pending lock |
| corpus05 | 4k | 8 | 3.075226 | pending lock |
| corpus05 | 4k | 16 | 3.171459 | pending lock |
| corpus05 | 4k | 32 | 3.061910 | pending lock |

inference:
- Task-local caches remove shared mutable classifier state while preserving each pixel's operation order. Native/AEX evidence supports byte equality; speed and concurrent-render acceptance are not yet established.

changed_files:
- mac/OLMColorKey/OLMColorKey.cpp
- tools/perf/ref_vs_fast.py (ColorKey default thread caps)
- orchestra/reports/P07d-evidence/ key scripts, compressed results, this report; shared verification height flag
- orchestra/reports/P07d-distancegradation-blur-colorkey-threading.md

verify:
```
python3 tools/perf/ref_vs_fast.py --plugin olmcolorkey --jobs 1 --scratch orchestra/state/P07d-distancegradation-blur-colorkey-threading/key-recheck
python3 orchestra/reports/P07d-evidence/verify.py olmcolorkey key
python3 orchestra/reports/P07d-evidence/key_threads.py
python3 orchestra/reports/P07d-evidence/units.py olmcolorkey key-units-recheck
python3 orchestra/reports/P07d-evidence/functions.py olmcolorkey key-functions-recheck
python3 orchestra/reports/P07d-evidence/build_key.py
python3 orchestra/reports/P07d-evidence/key_concurrent.py --build-only
python3 orchestra/reports/P07d-evidence/key_bench.py
```
Expected numerical counts above; the last command takes the shared lock and writes after-matrix and concurrent-render logs. Its performance result is pending. Scripts place temporary outputs in ticket scratch and builds/fuzz run serially.

next:
- Complete threshold/concurrent and timing acceptance, then finalize this plugin before DistanceGradation.
