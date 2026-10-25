status: done
summary:
- Blur keeps six existing partitions and schedules them through the shared GCD helper (up to six tasks); reference builds remain sequential.
- Native reference/fast: 675 exact comparisons before and after; original AEX Smart: 850 exact cases; all 139 corpus records replay true.
- TSan 50 cases: no reports; four simultaneous renders remain exact and improve median elapsed time.
- Historical unit module failures are unchanged, not a green suite.

facts:
- Baseline worktree HEAD: 3d270436. Memory checks: 49%, 50%, 53% free. Each build/fuzz command uses one job; at most two build/emulator processes.
- `profile_blur.py` under `lockf -k ~/.cache/olm-emu/bench.lock`: sample exit 0, host exit 0; 3040 aggregate samples in `olm::blur::horizontal`. No arithmetic changes were made.
- `ref_vs_fast.py --plugin olmblur --jobs 1 --parallel 1 2 8`: both before/after 675 exact, 0 refusals, 0 mismatches (200 small, 20 HD, 5 UHD, including heavy presets). First mismatch: none.
- `verify.py olmblur blur`: default seed 1 n300; realistic-v1 and v2 each seeds 1/2026102507 n100; T15b odd-even seed 2026 n150 with 1920x1080 bounds: 850 Smart exact, 0 mismatches, 0 Mac-only refusals. Fresh seed search found no prior use outside these scripts.
- Standard replay: root 39, P05c boundary 18, T15b 3, downsample P01a 43, realistic P02h 36: all `replay_matches_saved=true`.
- `threads.py`: 50 generated cases at caps 1/2/8 have equal hashes; repeated under `-fsanitize=thread`, cap 8, `halt_on_error=1`: 50 pass, no reports. Half the inputs are enlarged to 257x259 to exercise dispatch.
- `units.py olmblur blur-units-before` and `blur-units-after`: identical 34 module statuses, 7 exit 0, 24 exit 1, 3 exit 5. Baseline missing evidence/assets remain; logs are retained.
- `concurrent.py` uses four threads in one process, disjoint frames, joined before comparison. All 90 runs exact; 1080p four-render median seconds: cap1 2.886202417, cap2 1.743037958, cap8 1.708832291. No deadlock. Below 256x256 dispatch stays serial; at 256x256 single-render median cap1 0.087462, cap8 0.021030; four-render cap1 0.093286, cap8 0.062690. Existing dimensional cutoff retained with this measurement.
- The first concurrent-test compile referenced a reference-driver build directory that the driver had already removed. Fixed its library path to the retained normal thread-test build; this was a harness path error, not a numerical hypothesis.
- Durable Universal bundle: `~/.cache/olm-emu/P07d-blur`, registered in INDEX.json; SHA256 `be976592ffebdb1679267a62bd1a002e791be243374b46223e27ad9a7e1d9b9d`.

Timing command, before/after: `lockf -k ~/.cache/olm-emu/bench.lock python3 tools/fuzz/ae_realism_audit.py --phase matrix --plugins olmblur --cases default corpus05 --situations full 4k --jobs 1 --cache CACHE --state STATE`. Before cache is `~/.cache/olm-emu/P05c-blur`; after is the newly built candidate. Both runs: 12 OK, no refusal. Other workers were active; these single measurements may be load-affected. Numbers are host render-selector seconds, not native AE timings.

| Case | Size | Depth | Before seconds | After seconds |
|---|---|---:|---:|---:|
| default | full | 8 | 0.448255 | 0.440882 |
| default | full | 16 | 0.459238 | 0.452037 |
| default | full | 32 | 0.465863 | 0.457254 |
| default | 4k | 8 | 1.804813 | 1.761276 |
| default | 4k | 16 | 1.894996 | 1.807721 |
| default | 4k | 32 | 1.961776 | 1.838926 |
| corpus05 | full | 8 | 1.456208 | 0.637664 |
| corpus05 | full | 16 | 1.467622 | 0.607359 |
| corpus05 | full | 32 | 1.521018 | 0.567191 |
| corpus05 | 4k | 8 | 6.059794 | 2.302393 |
| corpus05 | 4k | 16 | 6.209152 | 2.389635 |
| corpus05 | 4k | 32 | 6.120272 | 2.486450 |

inference:
- Independent pass scheduling explains the heavy-case speedup without changing floating-point operations. The existing six boundaries are retained; this does not claim a new AE numerical profile or improved legacy helpers.

changed_files:
- core/olmblur_parallel_parts.h
- orchestra/reports/P07d-evidence/ (scripts, compressed results, this report)
- orchestra/reports/P07d-distancegradation-blur-colorkey-threading.md

verify:
Run from the worktree, serially, with `OLM_TEST_JOBS=1`:
```
python3 tools/perf/ref_vs_fast.py --plugin olmblur --jobs 1 --parallel 1 2 8 --scratch orchestra/state/P07d-distancegradation-blur-colorkey-threading/recheck
python3 orchestra/reports/P07d-evidence/verify.py olmblur blur
python3 orchestra/reports/P07d-evidence/threads.py
python3 orchestra/reports/P07d-evidence/concurrent.py
python3 orchestra/reports/P07d-evidence/units.py olmblur blur-units-recheck
```
Expected: 675 exact comparisons, 850 Smart exact cases, 139 matching replays, 50 forced-thread and 50 TSan passes, 90 exact concurrent/threshold runs, unchanged historical unit outcomes. Scripts set scratch/temp paths. `build_blur.py` rebuilds only the candidate bundle; `retain_blur.py` registers it and retains evidence. No oracle rebuild.

next:
- Proceed to ColorKey, then DistanceGradation. Restore historical unit assets in a separate environment ticket.
