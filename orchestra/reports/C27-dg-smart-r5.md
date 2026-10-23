status: partial

summary:
- Closed the small-image scalar Bilateral operation for Smart PF8/PF32, radii 3–32.
- Seed1 n300 Smart E/M/R/U: 284/1/8/7 -> 286/0/7/7; all 284 baseline-exact outputs and all Classic results are unchanged.
- Independent 324 cases are exact with sanitizer equality; corpus145 remains exact without expectation edits.
- Fresh seed7 Smart exact278->280; all278 baseline-exact outputs are byte-identical. Remaining residual investigation continues.

facts:
- Base `a96ed24cbc9c49127215b9ea01bccad0499ce0f2`, branch `orch/C27-dg-smart-r5`. Read AGENT_GUIDE, emulator GOTCHAS, DG ledger forbidden actions, compatibility plan and T07/C03/C08/C14/C19/F10/F12 reports. Reused C19 WIP probe/trace code without merging its branch.
- Original AEX SHA256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`; retained worker SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. MAIN assets and emulator source are read-only; no worker rebuild. These are CPU Unicorn/public SDK-shim comparisons, not native AE/UCRT certification.
- Initial and final `run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0` both complete. Original Smart290 success/8 reject/2 budget remains unchanged. Before284/1/8/7, after286/0/7/7. Exact dictionary/RAW equality holds for all284 prior Smart exacts and all300 Classic dictionaries. Only case7 refusal->exact and case200 mismatch->exact change.
- Case200 (239x1 PF8, Bilateral18): pre-filter239/239 words agree; post-filter128 words differ, first word original `feff4b42`, prior Mac `00004c42`. First final difference is byte28, original `de`, prior Mac `dd`, with45 differing bytes. The old PF8 path omitted the filter. This is a filter-stage correction, not output rounding.
- Original IPP init/filter at `18000c280`/`18000c2f0` reproduces the complete public post-filter plane and dispatches to `1806be1e0`, without imports or numerical detours. Candidate output and sanitizer output are exact.
- Original `FUN_1802a1640` selects the padded scalar path when width or height is less than `2*radius+1`. The circular row-major kernel, center inclusion, cutoff strictly greater than -25, border replication and separate float operations are restored. Disassembly at `1806be3d8..1806be3ed` multiplies color by spatial weight, then sample by that weight, and accumulates separately. Eighteen direct dispatch probes cover both sides of the shape boundary at radii3/4/7; optimized dispatch appears outside the admitted shape.
- Case7 (23x24 PF32, Bilateral17): same-mask PNG public trace plus relocated original typed callback binds to the separate typed public output. All552 pre/post words and final output agree. Its original IPP body independently reproduces552/552 post words without imports. This proxy binding is explicitly not a natural typed-input full-owner capture.
- Both original IPP-bound planes match O2, O3 with contraction requested, and ASan/UBSan. The existing exponential helper is checked at8217 FLOAT32 inputs over [-25,0], including original consumed inputs and cutoff neighbors; all8217 outputs match the original import-free body in all three builds. Leak detection disabled.
- Independent324 public original-AEX cases span PF8/PF32, radii3/4/7/17/18/32, horizontal/vertical/2D geometries, all three ownership modes and Constant/Linear/Sphere, RGB/Layer/background/inversion variation and odd padding. All324 exact and sanitizer-identical:162 PF32 refusal->exact;162 PF8 outputs unchanged exact. No admitted mismatch.
- Before/candidate/sanitized candidate verification completes seed1 all300 and corpus145. All changes are asserted exact, not merely baseline-preserving. Seven existing Bilateral negative controls remain unchanged refusals with sanitizer equality. Arbitrary Power, extended/nonfinite effective-filter inputs, radius2, larger radii, PF16 and other dispatch shapes retain their prior policy.
- Fresh seed7 n300 completes278/1/12/9 before; before/current/sanitized verification completes all300 and adds exact cases103/280 only (both refusal->exact), yielding280/1/10/9. No sanitizer diagnostics or timeout; unchanged large PF8 Median case169 takes substantially longer under sanitizers.
- Strict corpus replay exits0, completed145, `replay_matches_saved=true`, honoring both hash-bound worker groups. Beta9 and transactional2 tests pass. Machine evidence: `reports/fuzz/olmdistancegradation_C27_bilateral.json`.
- Candidate arithmetic was copied unchanged to production; only the radius-one comment block was relocated to its correct function afterward.

| Corpus replay | Before | After | Expectation edits |
| --- | --- | --- | --- |
| All145 Smart cases |145 exact|145 exact, identical statuses and bytes|None|

inference:
- The absent generic Bilateral operation caused the measured PF8 residual; the same restored scalar operation justifies bounded PF32 admission under the original scalar dispatch condition.
- Other dispatch shapes, arbitrary UCRT Power, and extended-source effective filters require separate evidence. The successful matrix is not a claim of universal Bilateral equivalence.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `tools/fuzz/probe_distancegradation_C19.py`
- `tools/fuzz/verify_distancegradation_smart_C14.py`
- `tools/emulation/trace_distancegradation_blur_C14.py`
- `tools/emulation/trace_distancegradation_smart_C14.py`
- `tools/emulation/trace_distancegradation_bilateral_C19.py`
- `tools/emulation/trace_distancegradation_dispatch_C27.py`
- `reports/fuzz/olmdistancegradation_C27_bilateral.json`
- `orchestra/reports/C27-dg-smart-r5.md`

verify:
Run from this worktree. All commands use ticket-local scratch and at most one worker per campaign.
```sh
s="$PWD/orchestra/state/C27-dg-smart-r5"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$s" --report "$s/check1.json" --corpus "$s/check-corpus" > "$s/check1.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 7 --jobs 1 --case-timeout 30 --shrink-attempts 0 --scratch "$s" --report "$s/check7.json" --corpus "$s/check7-corpus" > "$s/check7.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C14.py --before-ref a96ed24c --strict-improvement --campaign "$s/check1.json" --campaign "$s/check7.json" --corpus --bilateral-negative --case-timeout 120 --scratch "$s/check" --report "$s/check.json" > "$s/check.log" 2>&1
python3 tools/fuzz/probe_distancegradation_C19.py --before-ref a96ed24c --experiment production --matrix --matrix-family bilateral --strict-improvement --require-exact --scratch "$s/check-matrix" --report "$s/check-matrix.json" > "$s/check-matrix.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_blur_C14.py --index 200 --scratch "$s/check-trace200" --report "$s/check-trace200.json" > "$s/check-trace200.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C14.py --case-index 7 --scratch "$s/check-trace7" --report "$s/check-trace7.json" > "$s/check-trace7.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_bilateral_C19.py --trace "$s/check-trace200.json" --source mac/OLMDistanceGradation/OLMDistanceGradation.cpp --width 239 --height 1 --radius 18 --scratch "$s/check-ipp200" --report "$s/check-ipp200.json" > "$s/check-ipp200.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_bilateral_C19.py --trace "$s/check-trace7.json" --source mac/OLMDistanceGradation/OLMDistanceGradation.cpp --width 23 --height 24 --radius 17 --scratch "$s/check-ipp7" --report "$s/check-ipp7.json" > "$s/check-ipp7.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_dispatch_C27.py --report "$s/check-dispatch.json" > "$s/check-dispatch.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 1 --scratch "$s" --report "$s/check-replay.json" > "$s/check-replay.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py' > "$s/check-beta.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_smart_transactional_20260822.py' > "$s/check-transactional.log" 2>&1
git diff --check
```
Expected seed1:286/0/7/7, original completion counts unchanged; matrix324 exact, negative7 unchanged refusal, corpus145 exact unchanged, direct planes239+552 exact and exp8217 exact in each build. Oracle timeout counts may depend on machine load.

next:
- First cluster verified on seed1, fresh seed7 and independent cases. Investigate remaining AEX-rendered refusals. Keep fractional Power separate as `ucrt-math` when its first divergence is established there.
