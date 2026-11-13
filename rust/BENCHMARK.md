# Rust versus original Windows AEX render speed

Measured 2026-11-13 on an AMD Ryzen 9 5900X (12 cores / 24 logical processors),
Windows 11, using the already-built AEXCompat fresh-case resident batch path.
**The Rust port is generally slower in this harness. AntiAntiAlias's 32-color
preset is the clear exception: about 2.1-2.3x faster at 1080p. UV Map 32-bpc
is essentially tied.** This is a workload comparison, not a claim about the
inherent speed of Rust or native After Effects.

At 1080p, 67/70 cells have five valid timed frame pairs plus one warm-up.
Active RadialBlur cannot supply a valid original resident result, so its three
heavy rows have no ratio. Across both image sizes and the 1x1 controls,
**1,206 original/Rust frame pairs
are byte-identical**, including 1,005 timed pairs.
There are no observed pixel mismatches among valid pairs. Successful Rust-only
Radial frames are not counted as paired sanity passes.

[Compact evidence](tools/bench/evidence/speed-20261113.json) contains every sample,
minimum, median, request, input/output hash, binary identity, CPU observation and
failure. [Offline audit](tools/bench/evidence/audit-20261113.json) rechecked all
accepted artifacts and raw reports. [Runner and reproduction](tools/bench/README.md).
The two main measurement campaigns took 25.78 minutes combined;
the small Zoom and per-process diagnostics add under a minute. No AE or GUI ran.

## Method and clock boundaries

- 1920x1080 and 960x540, deterministic PCG64 seed 20261113; same pixels on both
  sides, repeated for all six frames. UV Map receives a same-size texture from
  seed 20261114. PNG-derived deep inputs, downsample 1, CPU/software, color
  management off. Defaults have no parameter edits except UV's required layer.
- Smoother uses Classic8/16. All other effects use Smart8/16/32. Each side gets
  a separate `--render-request-batch`: shared globals, fresh instance/sequence
  for every frame, one warm-up followed by five timed frames. Side order
  alternates by cell (default original-first, heavy Rust-first); no within-cell
  interleaving, affinity, machine-wide isolation, or confidence interval.
- The primary clock is the harness's `render_selector_ns`, converted to ms.
  It excludes process startup, but includes the audited selector call and host
  callbacks. Worker-render and broker-frame samples are also retained. This is
  **not a pure kernel timer**. The selector timing source wraps
  `invoke_audited_effect_call_seh` in `minihost/src/worker_selector_dispatch.cpp`.
- Each side's matching 1x1 median estimates fixed overhead. Adjusted values
  subtract it from every measured sample. This still includes size-dependent
  host work; the control itself also runs plug-in code. Negative adjusted
  samples remain unresolved rather than being clamped. Raw ratios are primary.
- Execution is serial (`jobs=1`), with normal harness priority. Private Windows
  Jobs collect owned descendants, verify zero active processes, and wait for
  children. Original files were neither copied nor committed.
- Whole-batch CPU/wall ratios include discovery, harness and worker; maximum
  observed ratio in the selected matrix is **0.988**. No cell establishes
  concurrent multi-core execution by this metric. Short parallel phases cannot
  be ruled out. AEXCompat's `iterate_world_typed` and `iterate_generic` run serial
  loops; the latter maps once-per-processor to one invocation
  (`minihost/src/worker_pf_suites.cpp`). Native AE threading can differ.

## Presets

All unlisted values remain untouched. Slot numbers and full inspected metadata
are in evidence. Palette RGB entries are `(71i,113i,173i) mod 256`, alpha 255.

| Plug-in | Heavy preset |
|---|---|
| ColorKeep | 32 distinct colors |
| DistanceGradation | Both; inside/outside threshold 64; Power 2.25; Blur mode 3, size 12 |
| OLMBlur | Amount 40; six repeats; default smoothness 100 |
| OLMColorKey | Threshold .15; Lab94; dilation 8 / Euclidean; feather 8 / Euclidean; eight colors |
| OLMDirectionalBlur | Angle 35 degrees; front/back strengths 80/40 |
| OLMKiraKira | Gaussian; all four lengths 100; highlight radius 12; Gain untouched |
| OLMRadialBlur | Rotation; front/back strengths 30/15; quality 10 (resident original fails) |
| OLMSmoother | Smooth range 64 |
| OLMSmoother2 | Extra Smooth 50; range 20; v2 Oklab |
| OLMToonDilate | Search radius 8 |
| OLMUVMap | Default trilinear; smoothness 1; texture supplied |
| OLMAntiAntiAlias | 32 distinct colors |

## 1080p results

Milliseconds are **median (minimum)** of five frames. Ratio = Rust/original;
**<1 means faster**. Adjusted columns are medians after the matching 1x1 control
subtraction; adjusted minima and all three timing clocks are in JSON. An
incomplete row's Rust-only timing does not establish equivalent performance.

| Plug-in | bpc | Preset | Original ms | Rust ms | Rust/original | Adjusted O / R ms | Adjusted ratio | Sanity |
|---|---:|---|---:|---:|---:|---:|---:|---|
| ColorKeep | 8 | default | 11.74 (11.57) | 52.79 (52.36) | 4.496 | 8.47 / 49.94 | 5.895 | exact |
| ColorKeep | 8 | heavy | 41.04 (40.36) | 72.36 (70.50) | 1.763 | 38.23 / 69.17 | 1.809 | exact |
| ColorKeep | 16 | default | 14.45 (13.17) | 60.78 (54.09) | 4.206 | 11.12 / 58.14 | 5.226 | exact |
| ColorKeep | 16 | heavy | 43.87 (43.44) | 87.48 (75.02) | 1.994 | 40.53 / 84.50 | 2.085 | exact |
| ColorKeep | 32 | default | 13.70 (13.25) | 40.40 (39.37) | 2.948 | 10.67 / 37.25 | 3.492 | exact |
| ColorKeep | 32 | heavy | 45.16 (42.96) | 66.46 (66.02) | 1.472 | 42.62 / 63.53 | 1.491 | exact |
| DistanceGradation | 8 | default | 58.81 (55.03) | 156.75 (152.72) | 2.665 | 55.50 / 153.70 | 2.769 | exact |
| DistanceGradation | 8 | heavy | 111.16 (107.20) | 320.75 (317.38) | 2.885 | 107.79 / 317.96 | 2.950 | exact |
| DistanceGradation | 16 | default | 62.16 (59.41) | 143.20 (141.26) | 2.304 | 58.82 / 140.04 | 2.381 | exact |
| DistanceGradation | 16 | heavy | 114.85 (110.01) | 317.36 (312.95) | 2.763 | 111.60 / 314.83 | 2.821 | exact |
| DistanceGradation | 32 | default | 71.94 (67.73) | 143.61 (142.88) | 1.996 | 68.67 / 140.45 | 2.045 | exact |
| DistanceGradation | 32 | heavy | 122.81 (116.56) | 303.25 (301.17) | 2.469 | 119.26 / 300.38 | 2.519 | exact |
| OLMBlur | 8 | default | 67.36 (65.34) | 275.83 (271.97) | 4.095 | 64.40 / 272.60 | 4.233 | exact |
| OLMBlur | 8 | heavy | 371.56 (370.28) | 1712.02 (1690.24) | 4.608 | 368.95 / 1708.31 | 4.630 | exact |
| OLMBlur | 16 | default | 66.68 (66.22) | 287.89 (283.76) | 4.317 | 63.59 / 284.24 | 4.470 | exact |
| OLMBlur | 16 | heavy | 369.29 (365.26) | 1746.54 (1708.69) | 4.729 | 366.35 / 1742.71 | 4.757 | exact |
| OLMBlur | 32 | default | 61.93 (60.56) | 291.27 (287.39) | 4.703 | 59.28 / 287.99 | 4.858 | exact |
| OLMBlur | 32 | heavy | 371.95 (364.48) | 1713.90 (1692.18) | 4.608 | 368.96 / 1709.93 | 4.634 | exact |
| OLMColorKey | 8 | default | 35.09 (32.24) | 141.61 (136.95) | 4.036 | 32.74 / 138.07 | 4.217 | exact |
| OLMColorKey | 8 | heavy | 1007.81 (994.71) | 1818.91 (1792.80) | 1.805 | 1005.21 / 1815.72 | 1.806 | exact |
| OLMColorKey | 16 | default | 33.45 (32.81) | 124.80 (123.11) | 3.731 | 31.21 / 121.56 | 3.895 | exact |
| OLMColorKey | 16 | heavy | 1029.94 (1014.39) | 1785.30 (1780.99) | 1.733 | 1027.24 / 1781.93 | 1.735 | exact |
| OLMColorKey | 32 | default | 34.19 (33.78) | 136.74 (134.96) | 4.000 | 31.94 / 132.99 | 4.164 | exact |
| OLMColorKey | 32 | heavy | 1119.99 (1104.24) | 1824.79 (1806.77) | 1.629 | 1117.42 / 1821.37 | 1.630 | exact |
| OLMDirectionalBlur | 8 | default | 3.76 (3.44) | 34.75 (34.11) | 9.243 | 0.87 / 32.21 | 37.071 | exact |
| OLMDirectionalBlur | 8 | heavy | 714.97 (697.00) | 2497.02 (2348.51) | 3.492 | 712.25 / 2494.32 | 3.502 | exact |
| OLMDirectionalBlur | 16 | default | 4.83 (4.30) | 37.71 (35.94) | 7.807 | 1.88 / 34.70 | 18.431 | exact |
| OLMDirectionalBlur | 16 | heavy | 713.19 (656.39) | 2463.11 (2425.99) | 3.454 | 710.05 / 2460.09 | 3.465 | exact |
| OLMDirectionalBlur | 32 | default | 6.05 (5.74) | 54.49 (53.88) | 9.003 | 2.97 / 51.69 | 17.414 | exact |
| OLMDirectionalBlur | 32 | heavy | 754.38 (672.57) | 2436.89 (2421.75) | 3.230 | 751.16 / 2434.35 | 3.241 | exact |
| OLMKiraKira | 8 | default | 372.26 (345.14) | 670.52 (584.97) | 1.801 | 369.66 / 668.23 | 1.808 | exact |
| OLMKiraKira | 8 | heavy | 952.30 (883.90) | 12953.76 (12622.50) | 13.603 | 949.48 / 12951.36 | 13.641 | exact |
| OLMKiraKira | 16 | default | 365.16 (347.62) | 668.81 (590.58) | 1.832 | 362.58 / 666.27 | 1.838 | exact |
| OLMKiraKira | 16 | heavy | 909.05 (866.98) | 13024.11 (12605.11) | 14.327 | 906.37 / 13021.71 | 14.367 | exact |
| OLMKiraKira | 32 | default | 372.12 (355.44) | 629.13 (563.64) | 1.691 | 369.51 / 626.83 | 1.696 | exact |
| OLMKiraKira | 32 | heavy | 846.92 (833.23) | 12003.13 (10816.99) | 14.173 | 844.12 / 12000.70 | 14.217 | exact |
| OLMRadialBlur | 8 | default | 3.80 (3.39) | 33.99 (33.68) | 8.939 | 1.02 / 31.32 | 30.614 | exact |
| OLMRadialBlur | 8 | heavy | — | 2430.57 (2285.17) | — | — | — | incomplete |
| OLMRadialBlur | 16 | default | 4.31 (4.20) | 31.69 (31.08) | 7.352 | 1.62 / 29.03 | 17.869 | exact |
| OLMRadialBlur | 16 | heavy | — | 2120.64 (2092.38) | — | — | — | incomplete |
| OLMRadialBlur | 32 | default | 5.97 (5.53) | 36.84 (36.61) | 6.167 | 3.41 / 33.97 | 9.953 | exact |
| OLMRadialBlur | 32 | heavy | — | 2462.66 (2344.17) | — | — | — | incomplete |
| OLMSmoother | 8 | default | 254.11 (249.16) | 1574.84 (1420.94) | 6.197 | 251.30 / 1572.28 | 6.257 | exact |
| OLMSmoother | 8 | heavy | 228.05 (222.98) | 1246.26 (1096.41) | 5.465 | 225.41 / 1243.70 | 5.518 | exact |
| OLMSmoother | 16 | default | 243.20 (241.26) | 3010.48 (2342.93) | 12.379 | 240.66 / 3007.90 | 12.499 | exact |
| OLMSmoother | 16 | heavy | 230.38 (224.92) | 2672.00 (2348.96) | 11.598 | 227.74 / 2668.90 | 11.719 | exact |
| OLMSmoother2 | 8 | default | 373.20 (370.72) | 481.63 (473.32) | 1.291 | 369.85 / 478.01 | 1.292 | exact |
| OLMSmoother2 | 8 | heavy | 937.97 (826.63) | 1191.98 (991.30) | 1.271 | 935.09 / 1188.90 | 1.271 | exact |
| OLMSmoother2 | 16 | default | 406.88 (385.01) | 471.45 (465.82) | 1.159 | 403.79 / 467.86 | 1.159 | exact |
| OLMSmoother2 | 16 | heavy | 906.62 (840.86) | 1085.16 (953.10) | 1.197 | 903.22 / 1082.13 | 1.198 | exact |
| OLMSmoother2 | 32 | default | 363.27 (353.48) | 450.81 (446.23) | 1.241 | 360.25 / 447.80 | 1.243 | exact |
| OLMSmoother2 | 32 | heavy | 889.14 (824.75) | 1042.24 (927.27) | 1.172 | 885.38 / 1039.25 | 1.174 | exact |
| OLMToonDilate | 8 | default | 27.89 (27.42) | 46.12 (45.54) | 1.654 | 24.76 / 43.00 | 1.737 | exact |
| OLMToonDilate | 8 | heavy | 27.95 (27.63) | 46.58 (45.36) | 1.667 | 25.01 / 43.72 | 1.748 | exact |
| OLMToonDilate | 16 | default | 28.09 (26.64) | 49.38 (48.82) | 1.758 | 25.18 / 46.56 | 1.849 | exact |
| OLMToonDilate | 16 | heavy | 27.75 (27.63) | 50.41 (47.88) | 1.817 | 24.77 / 47.77 | 1.928 | exact |
| OLMToonDilate | 32 | default | 30.47 (28.87) | 58.35 (57.29) | 1.915 | 27.81 / 55.55 | 1.998 | exact |
| OLMToonDilate | 32 | heavy | 29.64 (29.14) | 59.14 (56.84) | 1.995 | 26.58 / 56.46 | 2.124 | exact |
| OLMUVMap | 8 | default | 142.65 (137.94) | 154.11 (151.08) | 1.080 | 139.30 / 151.34 | 1.086 | exact |
| OLMUVMap | 8 | heavy | 141.34 (137.43) | 150.79 (147.50) | 1.067 | 137.99 / 147.52 | 1.069 | exact |
| OLMUVMap | 16 | default | 137.45 (135.62) | 152.50 (147.98) | 1.109 | 134.53 / 149.63 | 1.112 | exact |
| OLMUVMap | 16 | heavy | 133.35 (131.15) | 156.35 (150.58) | 1.172 | 130.18 / 153.63 | 1.180 | exact |
| OLMUVMap | 32 | default | 139.69 (134.87) | 138.86 (135.21) | 0.994 | 136.38 / 135.71 | 0.995 | exact |
| OLMUVMap | 32 | heavy | 143.10 (140.46) | 142.82 (137.16) | 0.998 | 139.50 / 139.52 | 1.000 | exact |
| OLMAntiAntiAlias | 8 | default | 24.01 (22.77) | 25.74 (24.20) | 1.072 | 20.05 / 22.94 | 1.144 | exact |
| OLMAntiAntiAlias | 8 | heavy | 826.20 (739.42) | 387.23 (375.82) | 0.469 | 823.10 / 384.37 | 0.467 | exact |
| OLMAntiAntiAlias | 16 | default | 26.33 (24.58) | 30.41 (29.30) | 1.155 | 23.35 / 27.69 | 1.186 | exact |
| OLMAntiAntiAlias | 16 | heavy | 820.56 (741.49) | 388.78 (388.53) | 0.474 | 817.94 / 385.94 | 0.472 | exact |
| OLMAntiAntiAlias | 32 | default | 25.62 (24.98) | 25.28 (23.58) | 0.987 | 22.52 / 22.14 | 0.983 | exact |
| OLMAntiAntiAlias | 32 | heavy | 815.09 (723.59) | 351.58 (341.10) | 0.431 | 812.33 / 348.76 | 0.429 | exact |

## Interpretation

AntiAntiAlias's explicit 32-color workload is substantially faster in Rust;
its defaults are near parity. UV Map 32-bpc differences are below 1% at 1080p,
so the practical reading is a tie in this small sample. Smoother2 is relatively
close. The other comparable 1080p workloads favor the original.

The following are source-supported hypotheses, not profiling results:

- DirectionalBlur and RadialBlur defaults disable the filter. Rust still copies
  through checked per-pixel `get`/`set` loops (`olm-directional-blur/src/ae.rs`,
  `olm-radial-blur/src/algorithm.rs`). Large default ratios therefore do not
  describe an expensive blur kernel.
- Kira's Gaussian path uses ordered scalar tap loops and boundary reflection
  (`olm-kirakira/src/filters.rs`). Preserving the original/OpenCV arithmetic
  order without the original's optimized SIMD implementation is a plausible
  contributor to its large heavy-preset gap. DistanceGradation also reproduces
  native SIMD/FMA arithmetic profiles in scalar Rust loops.
- Smoother retains mechanical instruction translation and dispatch loops
  (`olm-smoother/src/lib.rs`, `generated.rs`). Checked pixel access, conversions,
  allocation/copy work and compiler optimization opportunities are plausible
  contributors elsewhere. This benchmark does not apportion their costs.
- The measurements do not establish an original-threading advantage: host
  iteration is serial and CPU/wall observations show none. FMA versus NOFMA was
  not varied; exact numerical profiles must not be relaxed to improve a score.

## Caps, corrections and unresolved host limitation

The first campaign used a 10-second frame deadline and 70-second side-batch cap.
Three Kira heavy 1080p Rust warm-ups exceeded the frame deadline. A complete
Kira repeat used 20 seconds/frame and 130 seconds/batch, keeping the same preset,
images and binaries. All replacement samples, rather than selected passing
frames, supply the table. Initial cap events remain under `superseded`.

The initial Directional heavy request encoded angle 35 as `value`; both sides
rejected it at preflight because an angle requires `components: [35]`. A complete
Directional repeat corrected only this transport encoding. The first campaign
and all nine rejected requests remain in evidence; they never count as renders.

Active original RadialBlur fails the resident protocol with
`frame_done_mismatch` / worker exit 57005 at every tested depth and size,
including 1x1. This is not a deadline and no original timing is accepted.
A bounded 97x61 Zoom probe (strengths 80/40, quality 10) fails in the same way.
The saved 960x540 Rotation Smart8 request succeeds through the per-process
transport and its PNG equals the resident Rust PNG byte-for-byte. That check
is diagnostic only: its timing is excluded. This localizes a transport/lifetime
limitation for this workload, but does not prove the underlying root cause.
No harness change, native AE test, or replacement speed ratio is claimed.

## Harness and build identity

The harness is `D:/Projects/01_Project/04_Tools/AEXCompat-wt-main/broker/target/release/aexcompat-harness.exe`.
The checkout HEAD observed during the run was
`032a187621353bac7b92a76ae394ac387ddedf51`; executable hashes are authoritative,
not a claim that every current source file was compiled into these binaries.

- Harness SHA-256: `92280aa7ca441a59f9edb0b9343779ebf237e6d6949a3e33d2d54515d4130dbc`
- Loaded worker SHA-256: `7a6598974b903fd4b068587b726d41c8adb8b198a294add88d544582482c71cf`

Rust files came from the user-supplied `olm-stage-20261113121904` main-build
staging directory; no rebuild or installation was performed. Six originals are
2025 builds from the 2026-11-12 release (ColorKeep, DistanceGradation, ColorKey,
Smoother2, UV Map, AntiAntiAlias); the remaining six are the specified retained
originals. All 24 plug-in SHA-256 values and paths are in evidence and were
rechecked after rendering. Workspace base: `bd25ec61712397b051f583ccc9e68490a6fb43f4`.

Validation: nine parsing/statistics tests passed. The offline audit verifies
all accepted output artifacts, loaded worker hashes, actual depth, complete
batch cleanup evidence and recomputed statistics. Byte equality is a bounded
sanity check on this corpus, not new native AE qualification.

## 540p sanity check

| Plug-in | bpc | Preset | Original ms | Rust ms | Rust/original | Adjusted O / R ms | Adjusted ratio | Sanity |
|---|---:|---|---:|---:|---:|---:|---:|---|
| ColorKeep | 8 | default | 5.29 (4.77) | 14.79 (14.44) | 2.795 | 2.02 / 11.94 | 5.903 | exact |
| ColorKeep | 8 | heavy | 12.84 (12.51) | 20.06 (19.48) | 1.563 | 10.03 / 16.88 | 1.683 | exact |
| ColorKeep | 16 | default | 5.38 (4.84) | 15.49 (14.90) | 2.878 | 2.06 / 12.85 | 6.244 | exact |
| ColorKeep | 16 | heavy | 12.66 (12.55) | 19.93 (19.29) | 1.574 | 9.32 / 16.95 | 1.819 | exact |
| ColorKeep | 32 | default | 5.63 (5.10) | 13.78 (13.14) | 2.448 | 2.60 / 10.63 | 4.097 | exact |
| ColorKeep | 32 | heavy | 12.78 (12.57) | 18.22 (17.57) | 1.426 | 10.23 / 15.28 | 1.493 | exact |
| DistanceGradation | 8 | default | 16.44 (16.16) | 42.31 (40.36) | 2.574 | 13.13 / 39.26 | 2.990 | exact |
| DistanceGradation | 8 | heavy | 29.97 (28.84) | 81.51 (78.65) | 2.720 | 26.59 / 78.72 | 2.960 | exact |
| DistanceGradation | 16 | default | 17.78 (17.04) | 38.94 (38.11) | 2.190 | 14.44 / 35.77 | 2.478 | exact |
| DistanceGradation | 16 | heavy | 32.87 (29.63) | 81.25 (78.80) | 2.472 | 29.62 / 78.73 | 2.658 | exact |
| DistanceGradation | 32 | default | 20.07 (19.25) | 36.94 (34.78) | 1.840 | 16.81 / 33.78 | 2.010 | exact |
| DistanceGradation | 32 | heavy | 32.60 (31.87) | 79.53 (77.29) | 2.440 | 29.05 / 76.66 | 2.639 | exact |
| OLMBlur | 8 | default | 18.50 (17.60) | 71.62 (70.48) | 3.872 | 15.54 / 68.39 | 4.402 | exact |
| OLMBlur | 8 | heavy | 74.90 (74.45) | 423.40 (417.99) | 5.652 | 72.29 / 419.69 | 5.805 | exact |
| OLMBlur | 16 | default | 18.21 (18.05) | 77.31 (74.56) | 4.245 | 15.12 / 73.66 | 4.871 | exact |
| OLMBlur | 16 | heavy | 76.87 (75.90) | 427.46 (415.76) | 5.561 | 73.92 / 423.62 | 5.731 | exact |
| OLMBlur | 32 | default | 17.49 (17.42) | 76.89 (75.27) | 4.396 | 14.84 / 73.61 | 4.959 | exact |
| OLMBlur | 32 | heavy | 75.74 (74.36) | 432.98 (424.21) | 5.716 | 72.75 / 429.01 | 5.897 | exact |
| OLMColorKey | 8 | default | 10.20 (9.62) | 39.52 (38.17) | 3.875 | 7.85 / 35.99 | 4.583 | exact |
| OLMColorKey | 8 | heavy | 252.09 (250.04) | 453.15 (446.66) | 1.798 | 249.50 / 449.96 | 1.803 | exact |
| OLMColorKey | 16 | default | 10.35 (9.91) | 35.69 (35.18) | 3.447 | 8.12 / 32.45 | 3.996 | exact |
| OLMColorKey | 16 | heavy | 267.53 (255.55) | 459.46 (447.37) | 1.717 | 264.83 / 456.10 | 1.722 | exact |
| OLMColorKey | 32 | default | 10.70 (10.34) | 37.12 (36.36) | 3.468 | 8.46 / 33.37 | 3.945 | exact |
| OLMColorKey | 32 | heavy | 259.80 (256.96) | 462.31 (455.12) | 1.779 | 257.23 / 458.89 | 1.784 | exact |
| OLMDirectionalBlur | 8 | default | 3.59 (2.49) | 10.91 (10.48) | 3.037 | — | — | exact |
| OLMDirectionalBlur | 8 | heavy | 167.90 (165.30) | 531.67 (514.50) | 3.166 | 165.19 / 528.97 | 3.202 | exact |
| OLMDirectionalBlur | 16 | default | 3.29 (3.11) | 11.43 (10.98) | 3.473 | 0.34 / 8.42 | 24.501 | exact |
| OLMDirectionalBlur | 16 | heavy | 165.34 (162.91) | 533.63 (522.81) | 3.227 | 162.21 / 530.61 | 3.271 | exact |
| OLMDirectionalBlur | 32 | default | 3.54 (3.39) | 15.64 (14.78) | 4.421 | 0.45 / 12.84 | 28.316 | exact |
| OLMDirectionalBlur | 32 | heavy | 169.22 (162.83) | 536.14 (518.01) | 3.168 | 166.00 / 533.60 | 3.214 | exact |
| OLMKiraKira | 8 | default | 83.10 (80.91) | 140.39 (139.22) | 1.689 | 80.50 / 138.11 | 1.716 | exact |
| OLMKiraKira | 8 | heavy | 206.81 (205.46) | 3214.39 (3160.57) | 15.543 | 203.99 / 3212.00 | 15.746 | exact |
| OLMKiraKira | 16 | default | 85.22 (80.74) | 145.97 (144.65) | 1.713 | 82.64 / 143.43 | 1.736 | exact |
| OLMKiraKira | 16 | heavy | 208.21 (204.00) | 3246.02 (3076.99) | 15.590 | 205.53 / 3243.62 | 15.782 | exact |
| OLMKiraKira | 32 | default | 83.57 (80.52) | 146.79 (143.08) | 1.756 | 80.96 / 144.49 | 1.785 | exact |
| OLMKiraKira | 32 | heavy | 211.66 (209.19) | 3288.84 (3129.92) | 15.538 | 208.87 / 3286.41 | 15.735 | exact |
| OLMRadialBlur | 8 | default | 4.12 (3.09) | 12.36 (11.59) | 2.999 | 1.34 / 9.69 | 7.214 | exact |
| OLMRadialBlur | 8 | heavy | — | 1160.38 (1093.02) | — | — | — | incomplete |
| OLMRadialBlur | 16 | default | 3.10 (2.89) | 9.69 (9.26) | 3.122 | 0.42 / 7.03 | 16.830 | exact |
| OLMRadialBlur | 16 | heavy | — | 1091.92 (1013.70) | — | — | — | incomplete |
| OLMRadialBlur | 32 | default | 3.74 (3.28) | 13.10 (12.38) | 3.499 | 1.18 / 10.22 | 8.655 | exact |
| OLMRadialBlur | 32 | heavy | — | 1358.56 (1096.53) | — | — | — | incomplete |
| OLMSmoother | 8 | default | 66.57 (65.34) | 356.17 (351.24) | 5.350 | 63.76 / 353.61 | 5.546 | exact |
| OLMSmoother | 8 | heavy | 60.43 (58.58) | 297.12 (284.68) | 4.916 | 57.79 / 294.56 | 5.097 | exact |
| OLMSmoother | 16 | default | 62.74 (61.46) | 500.21 (492.31) | 7.973 | 60.20 / 497.63 | 8.266 | exact |
| OLMSmoother | 16 | heavy | 59.61 (57.54) | 442.78 (432.24) | 7.427 | 56.97 / 439.68 | 7.718 | exact |
| OLMSmoother2 | 8 | default | 97.79 (95.39) | 119.83 (118.56) | 1.225 | 94.43 / 116.20 | 1.231 | exact |
| OLMSmoother2 | 8 | heavy | 191.95 (187.35) | 221.24 (220.83) | 1.153 | 189.06 / 218.16 | 1.154 | exact |
| OLMSmoother2 | 16 | default | 97.31 (93.97) | 124.05 (119.76) | 1.275 | 94.23 / 120.47 | 1.278 | exact |
| OLMSmoother2 | 16 | heavy | 192.21 (189.67) | 230.16 (228.81) | 1.197 | 188.81 / 227.13 | 1.203 | exact |
| OLMSmoother2 | 32 | default | 96.00 (94.48) | 121.74 (117.28) | 1.268 | 92.98 / 118.72 | 1.277 | exact |
| OLMSmoother2 | 32 | heavy | 192.44 (188.21) | 224.11 (222.45) | 1.165 | 188.68 / 221.13 | 1.172 | exact |
| OLMToonDilate | 8 | default | 9.18 (8.68) | 14.31 (13.58) | 1.559 | 6.04 / 11.19 | 1.852 | exact |
| OLMToonDilate | 8 | heavy | 9.63 (8.82) | 14.11 (13.37) | 1.465 | 6.70 / 11.25 | 1.680 | exact |
| OLMToonDilate | 16 | default | 9.17 (8.51) | 14.97 (14.76) | 1.633 | 6.26 / 12.14 | 1.941 | exact |
| OLMToonDilate | 16 | heavy | 8.96 (8.66) | 14.92 (14.22) | 1.665 | 5.98 / 12.27 | 2.052 | exact |
| OLMToonDilate | 32 | default | 9.77 (9.44) | 17.04 (16.10) | 1.743 | 7.11 / 14.23 | 2.003 | exact |
| OLMToonDilate | 32 | heavy | 9.86 (9.47) | 17.41 (15.78) | 1.765 | 6.81 / 14.73 | 2.163 | exact |
| OLMUVMap | 8 | default | 38.97 (37.81) | 41.55 (40.94) | 1.066 | 35.62 / 38.78 | 1.089 | exact |
| OLMUVMap | 8 | heavy | 37.78 (36.50) | 41.92 (41.03) | 1.109 | 34.43 / 38.65 | 1.122 | exact |
| OLMUVMap | 16 | default | 37.09 (35.97) | 41.77 (39.99) | 1.126 | 34.17 / 38.90 | 1.138 | exact |
| OLMUVMap | 16 | heavy | 38.13 (36.99) | 41.19 (40.72) | 1.080 | 34.96 / 38.47 | 1.100 | exact |
| OLMUVMap | 32 | default | 40.07 (38.15) | 38.62 (36.34) | 0.964 | 36.75 / 35.48 | 0.965 | exact |
| OLMUVMap | 32 | heavy | 40.77 (39.53) | 39.15 (36.34) | 0.960 | 37.17 / 35.86 | 0.965 | exact |
| OLMAntiAntiAlias | 8 | default | 8.05 (7.87) | 8.89 (8.80) | 1.104 | 4.10 / 6.08 | 1.485 | exact |
| OLMAntiAntiAlias | 8 | heavy | 210.58 (188.12) | 102.16 (100.45) | 0.485 | 207.48 / 99.30 | 0.479 | exact |
| OLMAntiAntiAlias | 16 | default | 10.90 (10.34) | 11.57 (10.74) | 1.061 | 7.93 / 8.85 | 1.116 | exact |
| OLMAntiAntiAlias | 16 | heavy | 188.66 (187.79) | 99.75 (99.49) | 0.529 | 186.05 / 96.90 | 0.521 | exact |
| OLMAntiAntiAlias | 32 | default | 9.65 (8.66) | 8.81 (8.54) | 0.913 | 6.55 / 5.66 | 0.865 | exact |
| OLMAntiAntiAlias | 32 | heavy | 185.67 (184.79) | 89.74 (88.39) | 0.483 | 182.91 / 86.92 | 0.475 | exact |

## After optimisation — 2026-11-13 (main c91bf2b8)

Same harness (AEXCompat 032a1876, harness SHA-256 92280aa7…), same originals, inputs, presets and
protocol as above; run serially on the same machine with no other jobs. Rendered frames were
deleted after hashing (`--keep-frames` not used). Median `render_selector` ms at 1920×1080.
"First Rust" is the Rust median from the table above. Ratio = now / original (< 1 is faster).
Every completed cell is byte-identical to the original.

| Plug-in | bpc | Preset | Original ms | First Rust ms | Rust now ms | Now / original |
|---|---:|---|---:|---:|---:|---:|
| ColorKeep | 8 | default | 11.43 | 52.79 | 5.69 | 0.497 |
| ColorKeep | 8 | heavy | 40.05 | 72.36 | 7.26 | 0.181 |
| ColorKeep | 16 | default | 12.00 | 60.78 | 5.67 | 0.472 |
| ColorKeep | 16 | heavy | 41.59 | 87.48 | 6.38 | 0.153 |
| ColorKeep | 32 | default | 12.99 | 40.40 | 5.77 | 0.444 |
| ColorKeep | 32 | heavy | 41.11 | 66.46 | 6.31 | 0.153 |
| DistanceGradation | 8 | default | 54.56 | 156.75 | 70.08 | 1.284 |
| DistanceGradation | 8 | heavy | 104.52 | 320.75 | 95.59 | 0.915 |
| DistanceGradation | 16 | default | 60.18 | 143.20 | 63.06 | 1.048 |
| DistanceGradation | 16 | heavy | 111.45 | 317.36 | 86.36 | 0.775 |
| DistanceGradation | 32 | default | 72.73 | 143.61 | 57.15 | 0.786 |
| DistanceGradation | 32 | heavy | 114.70 | 303.25 | 85.27 | 0.743 |
| OLMBlur | 8 | default | 64.07 | 275.83 | 31.02 | 0.484 |
| OLMBlur | 8 | heavy | 369.69 | 1712.02 | 81.79 | 0.221 |
| OLMBlur | 16 | default | 64.96 | 287.89 | 33.02 | 0.508 |
| OLMBlur | 16 | heavy | 367.16 | 1746.54 | 81.01 | 0.221 |
| OLMBlur | 32 | default | 61.98 | 291.27 | 32.12 | 0.518 |
| OLMBlur | 32 | heavy | 365.11 | 1713.90 | 80.44 | 0.220 |
| OLMColorKey | 8 | default | 32.03 | 141.61 | 10.30 | 0.322 |
| OLMColorKey | 8 | heavy | 996.59 | 1818.91 | 195.04 | 0.196 |
| OLMColorKey | 16 | default | 33.24 | 124.80 | 12.24 | 0.368 |
| OLMColorKey | 16 | heavy | 1001.19 | 1785.30 | 181.24 | 0.181 |
| OLMColorKey | 32 | default | 34.17 | 136.74 | 15.38 | 0.450 |
| OLMColorKey | 32 | heavy | 1023.62 | 1824.79 | 191.02 | 0.187 |
| OLMDirectionalBlur | 8 | default | 3.47 | 34.75 | 3.32 | 0.956 |
| OLMDirectionalBlur | 8 | heavy | 645.14 | 2497.02 | 324.92 | 0.504 |
| OLMDirectionalBlur | 16 | default | 4.21 | 37.71 | 3.83 | 0.910 |
| OLMDirectionalBlur | 16 | heavy | 650.66 | 2463.11 | 321.78 | 0.495 |
| OLMDirectionalBlur | 32 | default | 5.79 | 54.49 | 5.10 | 0.881 |
| OLMDirectionalBlur | 32 | heavy | 649.82 | 2436.89 | 313.36 | 0.482 |
| OLMKiraKira | 8 | default | 327.14 | 670.52 | 195.11 | 0.596 |
| OLMKiraKira | 8 | heavy | 807.18 | 12953.76 | 277.82 | 0.344 |
| OLMKiraKira | 16 | default | 332.50 | 668.81 | 202.82 | 0.610 |
| OLMKiraKira | 16 | heavy | 807.37 | 13024.11 | 277.98 | 0.344 |
| OLMKiraKira | 32 | default | 328.78 | 629.13 | 201.05 | 0.611 |
| OLMKiraKira | 32 | heavy | 808.57 | 12003.13 | 275.45 | 0.341 |
| OLMRadialBlur | 8 | default | 3.42 | 33.99 | 3.45 | 1.010 |
| OLMRadialBlur | 8 | heavy | — | — | 327.58 | — |
| OLMRadialBlur | 16 | default | 3.90 | 31.69 | 3.77 | 0.967 |
| OLMRadialBlur | 16 | heavy | — | — | 318.15 | — |
| OLMRadialBlur | 32 | default | 5.52 | 36.84 | 4.85 | 0.879 |
| OLMRadialBlur | 32 | heavy | — | — | 329.42 | — |
| OLMSmoother | 8 | default | 249.36 | 1574.84 | 164.95 | 0.662 |
| OLMSmoother | 8 | heavy | 222.30 | 1246.26 | 175.39 | 0.789 |
| OLMSmoother | 16 | default | 238.81 | 3010.48 | 163.76 | 0.686 |
| OLMSmoother | 16 | heavy | 218.04 | 2672.00 | 198.54 | 0.911 |
| OLMSmoother2 | 8 | default | 356.06 | 481.63 | 75.85 | 0.213 |
| OLMSmoother2 | 8 | heavy | 779.05 | 1191.98 | 112.08 | 0.144 |
| OLMSmoother2 | 16 | default | 345.71 | 471.45 | 77.58 | 0.224 |
| OLMSmoother2 | 16 | heavy | 784.64 | 1085.16 | 119.25 | 0.152 |
| OLMSmoother2 | 32 | default | 338.80 | 450.81 | 66.89 | 0.197 |
| OLMSmoother2 | 32 | heavy | 783.14 | 1042.24 | 113.94 | 0.145 |
| OLMToonDilate | 8 | default | 25.63 | 46.12 | 7.59 | 0.296 |
| OLMToonDilate | 8 | heavy | 26.75 | 46.58 | 7.80 | 0.291 |
| OLMToonDilate | 16 | default | 25.74 | 49.38 | 10.76 | 0.418 |
| OLMToonDilate | 16 | heavy | 26.19 | 50.41 | 10.99 | 0.419 |
| OLMToonDilate | 32 | default | 27.37 | 58.35 | 19.59 | 0.715 |
| OLMToonDilate | 32 | heavy | 27.64 | 59.14 | 19.33 | 0.699 |
| OLMUVMap | 8 | default | 130.23 | 154.11 | 39.24 | 0.301 |
| OLMUVMap | 8 | heavy | 130.50 | 150.79 | 43.39 | 0.332 |
| OLMUVMap | 16 | default | 129.37 | 152.50 | 42.06 | 0.325 |
| OLMUVMap | 16 | heavy | 129.66 | 156.35 | 42.81 | 0.330 |
| OLMUVMap | 32 | default | 132.46 | 138.86 | 39.36 | 0.297 |
| OLMUVMap | 32 | heavy | 133.51 | 142.82 | 39.63 | 0.297 |
| OLMAntiAntiAlias | 8 | default | 21.49 | 25.74 | 5.17 | 0.240 |
| OLMAntiAntiAlias | 8 | heavy | 717.59 | 387.23 | 356.22 | 0.496 |
| OLMAntiAntiAlias | 16 | default | 21.65 | 30.41 | 4.91 | 0.227 |
| OLMAntiAntiAlias | 16 | heavy | 720.20 | 388.78 | 360.44 | 0.500 |
| OLMAntiAntiAlias | 32 | default | 23.72 | 25.28 | 5.66 | 0.239 |
| OLMAntiAntiAlias | 32 | heavy | 708.96 | 351.58 | 327.89 | 0.462 |

OLMRadialBlur heavy: the original still fails the resident protocol (incomplete), so no ratio;
per-process wall timing in PR #13 measured 0.64–0.73. DistanceGradation 8/16 bpc defaults are
still slower than the original in this serial run (1.28 / 1.05) although the PR #14 run measured
0.96 / 0.93; tracked as follow-up. Evidence: `tools/bench/evidence/final-20261113.json` and
`final-20261113-audit.json` (audit passed: 1,005 exact timed frame pairs, 9 incomplete cells).
