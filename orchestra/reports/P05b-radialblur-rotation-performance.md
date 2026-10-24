status: blocked
summary: |
  Restored the original once-per-angle trig table and vectorized independent RGBA scatter lanes with exact SSE NaN handling.
  Heavy 240x135 renders improved from 37.8–39.7 s to 16.8–17.4 s; 480x270 now completes in 32.6–33.4 s.
  1080p and 4K still exceed 60 s: the requested 2 s / 8 s targets are NOT achieved.
  Smart differential campaigns have zero numerical mismatches / Mac-only refusals; one pre-existing original-AEX failure prevents all corpora replaying true.

facts:

### Scope and arithmetic

- Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, the compatibility plan, and the RadialBlur ledger restrictions. No release gates, ledger, other plugin sources, MAIN files, emulator sources, or oracle binaries were changed. No push or history rewrite.
- Original MAIN `decomp/OLMRadialBlur.aex.c.txt`, around lines 2054–2065, calls `FUN_18001d060` once per angle and stores a paired trig table **before** radius traversal. The port previously recomputed this pair for every radius/angle cell. The table now uses the identical `RadialF32Mul` and `RadialAEXPairedSinCos`, with unchanged downstream multiplication/addition order.
- Original `FUN_1800024c0` / `FUN_180001c90` traverses radius, source angle, then offsets; the port retains this traversal and every destination's accumulation order. Four independent channels are evaluated together. The exceptional path implements the existing `x86_float::sse_result` first-NaN/payload/generated-invalid rules per lane. The finite path uses separate float multiply/add, with contraction and fast math disabled. Alpha receives the original contribution directly.
- `python3 orchestra/reports/P05b-evidence/work_counts.py` derives the following counts from the current source and the actual P00b corpus05 parameters. These are source-derived counts, not runtime instrumentation. Quality=50 gives 18,000 angles. Size Variation is enabled, so each polar cell makes one RGBA and two scalar sampling calls. Scatter tap counts additionally depend on eligibility, alpha, sampled span factors, and the per-radius offset modes; they are **not** a constant number of taps per output pixel.

| Output | Radius rows | Polar cells / RGBA calls | RGBA calls per output pixel | Before `RadialAEXSinHot` calls | After calls |
|---|---:|---:|---:|---:|---:|
| 240x135 | 276 | 4,968,000 | 153.3333 | 9,935,448 | 35,998 |
| 480x270 | 552 | 9,936,000 | 76.6667 | 19,870,896 | 35,998 |
| 1920x1080 | 2,204 | 39,672,000 | 19.1319 | 79,339,592 | 35,998 |
| 3840x2160 | 4,407 | 79,326,000 | 9.5638 | 158,643,186 | 35,998 |

For this positive step, only angle zero uses the tiny-angle branch; every other pair calls the hot sine polynomial twice. At fixed geometry, angular sampling grows approximately with Quality. For this fixed near-corner center, radius rows grow approximately with linear image size. Fade and scatter work still grow with their effective spans; the original scatter clamps the unscaled span at 3000 before multiplying the per-cell factor. The optimization does not change that work or impose a budget.

### Measurements

`tools/fuzz/ae_realism_audit.py --phase matrix --plugins radialblur --cases corpus05 --jobs 1 --timeout 60`, using the registered P00b host and the indicated bundles. `P05b-evidence/perf.py` reproduces the driver invocation and a bounded `sample PID 2 1` capture. All timings are shared-machine single measurements in seconds, not medians. `>60` means the host was killed at the 60-second wall timeout, not a refusal.

| Output | Depth | P00b retained baseline | Angle table only | Angle table + exact SIMD |
|---|---:|---:|---:|---:|
| 240x135 | 8 | 38.977332 | 38.343124 | 16.781520 |
| 240x135 | 16 | 39.743750 | 38.360785 | 16.975897 |
| 240x135 | 32 | 37.803887 | 36.018652 | 17.371435 |
| 480x270 | 8 | >60 | >60 | 32.600147 |
| 480x270 | 16 | >60 | >60 | 33.259580 |
| 480x270 | 32 | >60 | >60 | 33.445240 |
| 1920x1080 | 8 / 16 / 32 | >60 (historical P00b) | >60 each | >60 each |
| 3840x2160 | 8 / 16 / 32 | >60 (historical P00b) | >60 each | >60 each |

- The fresh baseline repeats 240x135 and 480x270. The original large-frame results are explicitly historical, streamed from committed `P00b-evidence/matrix.jsonl.gz`; they are retained in `historical-large-baseline.json`.
- Fresh `sample` profiles are retained for the P00b baseline, angle-only candidate, and final candidate. Their collapsed hot stack is `RenderRotationTyped`. Baseline ARM64 disassembly at the sampled scatter offsets contains scalar contribution/accumulation and repeated SSE classification. The final early-frame sample still contains scalar SSE operations in `RenderRotationTyped`; no claim that the entire remaining time is one stage.
- Universal builds: `python3 tools/fuzz/build_F47_bundles.py --plugins OLMRadialBlur --scratch "$TMPDIR/simd-build"` succeeded for `x86_64 arm64`. Final executable SHA-256: `82edc42334ed9dee3a9af08ad0eb10e036638d3e2c66e6a8cf4fc2a7abe9122e`.
- Durable bundles are registered under `~/.cache/olm-emu/P05b-radialblur-rotation-performance` (angle-only) and `~/.cache/olm-emu/P05b-radialblur-simd` (final). Both reuse the existing P00b host; neither is an oracle. Build/source/helper hashes are archived in this report's evidence directory.
- `memory_pressure` checks observed 48–62% free, above the required 30%. Campaigns used `--jobs 1` alongside one measurement lane. One early standalone SIMD leaf-test invocation was launched while both lanes were active; its exact subprocess overlap was not recorded, so strict adherence to the two-process ceiling for that brief interval is unverified. Later leaf builds were serialized with the measurement lane. Generated build trees are removed at closeout; logs and compact evidence remain.

### Exactness and acceptance limits

Commands are reproducible through `P05b-evidence/verify.py` (standard `tools/fuzz/run.py`, `--jobs 1`, no shrinking). Final measured Smart results:

| Campaign | Requested | Exact | Original rejects | Original budgets | Smart mismatches | Mac-only refusals |
|---|---:|---:|---:|---:|---:|---:|
| default, seed 1 | 300 | 276 | 20 | 4 | 0 | 0 |
| realistic-v1, seed 1 | 100 | 87 | 11 | 2 | 0 | 0 |
| realistic-v1, fresh seed 20261025 | 100 | 91 | 7 | 2 | 0 | 0 |
| odd-even-v1 + realistic, seed 2026 | 150 | 131 | 15 | 4 | 0 | 0 |
| odd-even-v1 + realistic, seed 2027 | 150 | 136 | 11 | 3 | 0 | 0 |

- Odd-even uses `--max-size 1920 --size-max-height 1080`, matching the T15b summary. One seed-2026 case also exhausted the Mac time budget while its original oracle was unavailable. Unavailable cases are not counted as exact. Classic is exercised and retains historical mismatches/refusals; the ticket's contract route is Smart.
- The committed P03b default-after report's source SHA-256 `90dfdefb23c810263d8c1f4220dd179fb917e413b65ca757887da4eb737081cb` exactly matches this ticket's initial source. Comparing its 276 Smart exact cases with the final default run gives **zero exact-to-non-exact transitions and zero exact-output hash changes**.
- Standard replay: root corpus **60/61 matches saved**, realistic P02d **180/180**, T15b odd-even **4/4**, new labelled P05b corpus **6/6**. Both declared routes are retained; these are not rebaselined results.
- The single root replay failure is **C49_seed1_case000117.json**: original AEX guest stops at **RIP 0x180002cc3**. This also failed in the angle-only replay and is an existing P03b boundary. Mac still returns success and the **same saved Smart raw SHA-256** `6958423267181cc23ab6aed257b5007841f3a39d3532abb0ea2a9e616947593d`; Classic remains refusal 516. There is no first numerical mismatch: Smart is `uncompared` because its oracle did not return. This blocks the literal “all corpora replay true” acceptance condition; no worker was rebuilt or corpus result rewritten to conceal it.
- `OLM_TEST_JOBS=1 python3 -m unittest discover -s tests -p 'test_*radialblur*.py'`: baseline after SDK setup **267 tests, 76 failures, 63 errors**; final **268 tests, 76 failures, 63 errors**. Failure/error name sets are identical. The extra test passes. These legacy suites are **not green**. The earlier missing-SDK run (65 errors) is excluded from the before/after comparison.
- `python3 tests/test_radialblur_scatter_simd_P05b.py` and `P05B_TEST_ARCH=x86_64 python3 tests/test_radialblur_scatter_simd_P05b.py`: both pass **105,832 tuples / 423,328 lane comparisons**, with no first mismatch, against the original scalar SSE helpers. Includes signed zero, subnormals, maximum finite values, infinities, signaling/quiet NaNs and payloads, plus deterministic random bit patterns. This is arithmetic regression evidence, not an independent original-AEX oracle.
- `python3 orchestra/reports/P05b-evidence/witnesses.py`: six fresh original-AEX Smart exact renders (PF8/PF16/PF32, Quality 1/50, forward/back scatter) saved under `tests/fuzz_corpus/radialblur/P05b-rotation-performance`; standard replay is 6/6 true.
- Heavy-frame raw bundle comparison found **zero differing bytes and no first mismatch across 907,200 bytes** (129,600 PF8 / 259,200 PF16 / 518,400 PF32). It is archived separately in `bundle-compare-results.json.gz`: same P00b host/input, raw byte comparison rather than PNGs or a checksum-only verdict. It compares retained P00b to the final bundle, not to a full-size emulated AEX. Counts, full SHA-256 hashes and first-mismatch fields are retained there.

inference:

- Trig recomputation is redundant and diverges from the original's work organization, but was not the dominant heavy-frame cost: its removal alone scarcely changed timings.
- Vectorizing independent scatter channels gives a measured 2.2–2.3x improvement at 240x135, but does not make full frames practical. The hypotheses that angle hoisting alone, or this channel-arithmetic optimization, would close the requested performance gap were not supported. No third speculative optimization was applied.
- Remaining scalar fade/prepass work, per-tap indexing and row-level concurrency deserve separate measured work. Independent channel evaluation is proven locally; this ticket does not claim arbitrary original-AEX/native-Windows equivalence outside the retained tests.
- Completion is blocked by the unmet performance target and the original C49 replay failure. The existing oracle failure must be handled without weakening acceptance or changing numerical output to satisfy it.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `mac/OLMRadialBlur/RadialScatterSIMD.h`
- `tests/test_radialblur_scatter_simd_P05b.py`
- `tests/fuzz_corpus/radialblur/P05b-rotation-performance/*.json` (six witnesses)
- `orchestra/reports/P05b-radialblur-rotation-performance.md`
- `orchestra/reports/P05b-evidence/*` (reproduction scripts and measured evidence)

verify:

From this worktree:

```sh
export TMPDIR="$PWD/orchestra/state/P05b-radialblur-rotation-performance"
export TMP="$TMPDIR" TEMP="$TMPDIR" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$TMPDIR"
python3 tests/test_radialblur_scatter_simd_P05b.py
P05B_TEST_ARCH=x86_64 python3 tests/test_radialblur_scatter_simd_P05b.py
python3 orchestra/reports/P05b-evidence/verify.py
python3 -m unittest discover -s tests -p 'test_*radialblur*.py' > "$TMPDIR/units-verify.log" 2>&1
python3 orchestra/reports/P05b-evidence/perf.py --label verify-perf --cache "$HOME/.cache/olm-emu/P05b-radialblur-simd"
python3 orchestra/reports/P05b-evidence/compare_bundles.py
python3 orchestra/reports/P05b-evidence/work_counts.py
```

Expected: SIMD test OK on both architectures; zero Smart numerical mismatches/Mac-only refusals among available oracle cases; no default exact hash regression; all declared corpus replays true **except the documented C49 original guest failure**; unchanged legacy unit failure/error names; raw heavy-frame bundle differences zero. Original budgets and shared-machine timings can vary. Full-size performance is still expected to miss the target. The performance script deliberately stops its extra profiling render after sampling and never counts that stop as a completed timing.

next:
- Orchestrator review of the exact partial optimization; **do not mark P05b done** on this evidence.
- Follow-up performance ticket: measure fade/prepass versus scatter separately; investigate invariant classification/indexing and deterministic parallelism over owned radius rows, retaining the current accumulation order.
- Separate original-oracle ticket for C49 RIP 0x180002cc3. Preserve the saved Mac hash and standard replay contract; no oracle rebuilding was authorized here.
