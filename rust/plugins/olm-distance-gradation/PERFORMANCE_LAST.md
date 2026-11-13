# S-last performance qualification

Base: origin/main 523e4ec6 (c91bf2b8 plus PR #17). Only DistanceGradation and
RadialBlur were changed. All render measurements and oracle cases run serially.

## Changes and exactness

DistanceGradation reads active row slices instead of invoking the generic checked
pixel getter for every mask/composition pixel. Integer ownership reads only alpha:
U8 >= 2 and U16 >= 192. Exhaustive tests cover all 256/65536 alpha words, including
U16 words above nominal white. Float mask admission, composition, quantization,
field construction, canonical sqrt groups and architecture-specific math are
unchanged. Row slices respect padding and the original preview-border coordinates.
No new SIMD, FMA, reassociation, global pool, cache or allocation was introduced.
In particular, aarch64 NaN behavior follows the same scalar operations as before.

RadialBlur already had a packed contiguous-copy path on the base. It now establishes
no-op with six integer SDK records on the stack, balancing each checkout/checkin
at the same address. It avoids allocating all parameter metadata and values in
both render and cropped pre-render probes. Nonzero controls still use the existing
active kernel; differently sized/origin worlds still use legacy PF_COPY. No-op
parameter slots are 4, 6, 7, 10, 12, 13. Failure-injection tests verify address and
checkin lifetime, and the existing copy test covers padding and all depths.

## Measurement method

`perf_defaults.py` retains eight alternating-order blocks, one discarded warmup
and five measured frames per side per block: 40 measured samples per side. Original,
previous Rust and candidate use the same image/request, with native sidecar and
PNG hash equality checked for every frame. No favorable blocks are selected.
`examples/distance-profile.rs` reports 40 warm pure-kernel samples without frames.
The standard bench uses its unmodified five-frame default matrix and serial Jobs.
The command-line name is `DistanceGradation` (not `OLMDistanceGradation`).

960x540 concurrent-free default medians/minima in ms:

| bpc | Original | Previous Rust | Candidate | Candidate/original |
|---|---:|---:|---:|---:|
| 8 | 15.5368 / 14.9268 | 20.99365 / 20.3845 | 8.8072 / 8.0749 | 0.5669 |
| 16 | 16.64005 / 16.1190 | 18.47035 / 17.6554 | 8.1728 / 7.6521 | 0.4912 |

An independent initial 40-sample baseline reproduced ratios 1.3565 and 1.1101,
so the serial regression is reproducible rather than only a five-sample outlier.
Pure 960x540 micro medians: field 2.3444 ms; U8 staging plus packing 1.3556 ms;
U16 packing 0.7172 ms; empty scoped row drivers 0.1218/0.2041/0.3830/0.7498 ms
for 2/4/8/16 workers. Thread scheduling and packing remain unchanged. The example's alpha-only checked
access micro is deliberately narrower than the old full four-channel normalization
and float-admission loop; it must not be treated as a profile of that whole loop.

A same-run 40-sample 8-bpc ablation leaves the old mask loop intact and changes
only composition to row reads. Its median/min is 21.0295 / 20.1619 ms versus
8.80875 / 8.4375 ms for the final build, original 15.5651 / 14.8933 ms.
Thus the 12.22 ms saving is overwhelmingly the integer mask loop's depth dispatch,
checked decoding and full-channel normalization, not composition or thread startup.

Radial 1080p default 8-bpc, same 40-sample method: original 3.62415 / 3.0632 ms,
previous Rust 3.4858 / 2.9490 ms, candidate 3.4063 / 2.8970 ms; ratio 0.9399.
All eight paired block medians are below 1 (0.8651 to 0.9959).

The retained PR #14 `D:/olm-rs-target/misc-evidence/bench-after-final.json`
explains the apparent reversal. Both reports use the same harness/worker/original
hashes; `git diff 74bcd6ae..523e4ec6` is empty for DistanceGradation, olm-core,
olm-ae, Cargo.toml and Cargo.lock. Their DLL identities differ (separate builds).

| bpc | PR #14 original median/min | PR #14 Rust median/min | Serial original median/min | Serial Rust median/min |
|---|---:|---:|---:|---:|
| 8 | 77.9940 / 64.1214 | 74.8196 / 73.7673 | 54.5623 / 53.8211 | 70.0759 / 69.6047 |
| 16 | 65.3136 / 59.7319 | 60.5664 / 59.8392 | 60.1803 / 58.9344 | 63.0589 / 62.5082 |

At 8 bpc the PR original median is 43% higher, while the authoritative Rust is
6% faster, not slower. At 16 bpc the original improves 7.9% while Rust slows
4.1%. PR #14's original sample spread (8 bpc median/min = 1.216) makes the
five-sample ratio an unstable claim of a win. The historical denominator dominates
the 8-bpc reversal. The fresh 40-sample controls reproduce the actual shortfall.
This does not identify the historical scheduler/background-load cause, and no
claim is made that thread spawn, allocation or a lost SIMD branch changed at merge.
The new optimization removes checked access/conversion work rather than changing
thread scheduling, allocation or default-only SIMD admission.

## Verification

17 DistanceGradation tests and 11 Radial tests pass; one explicit reciprocal-profile
regeneration test is ignored. Owned-crate rustfmt and release Clippy pass (existing
warnings). Goldens: 54 DistanceGradation + 40 Radial exact; 14 historical Radial
exclusions unchanged. Native macOS/aarch64 execution is not claimed by this Windows
run; no architecture-specific arithmetic changed.

Distance oracle: 113 plans per seed, seeds 20261210/20261211, three depths and
scales 1, 1/2, 1/4. Thresholds bounded 0..128, blur size 0..12, sizes 1x1/3x7/11x7;
all other generated ranges retained. Baseline exact counts are 222/222/220.
Twelve route-cases remain original render failures (four parameter cases across
three depths), not passes. Two Smart32 mismatches are original-unstable: three
fixed replay pairs each show two original hashes, one candidate hash, successful
renders and an exact original/candidate replay. Both match previous Rust exactly.
Per-process authority results are retained separately, not spliced into baselines.

Local evidence and cleanup candidates: `D:/olm-rs-target/last/` and worktree
`D:/olm-rs-wt-last/`. No manual directory deletion, worktree removal or install.

Radial oracle seed 20261210 (per process): 110/113/108 exact at 8/16/32 bpc,
with 3/0/5 mismatches and no failures/timeouts. Seed 20261211 resident: 3 exact
and 110 original protocol failures per depth. All 330 failures received per-process
authority: 108/107/108 exact, 1/3/2 mismatches, one original Smart8 timeout,
no candidate failures. These transport populations remain separate. The timeout's
single bounded replay is exact; it does not replace the initial observation.
All 14 pixel mismatches have changing originals and stable candidates, successful
fixed replays and an exact pair. Three pairs each; two initially non-exact replay
sets received one fixed ten-pair block each, both qualifying. All 14 also match
the previous Rust build byte-for-byte. Exclusions are not counted as passes.
Noise Type 3 alone is skipped before rendering under the existing validation rule;
full numeric ranges and 1x1/3x7/11x7/17x9 sizes are retained. Both seeds cover
three scales and exceed 100 random successful comparisons per depth in aggregate.

Targeted Radial no-op/geometry: 33/33 exact, including changed irrelevant controls,
three scales/depths, odd dimensions, cropped demand and padded/origin fixtures.
The first resident-wrapper attempt failed before render (`KeyError: radial_oracle`);
registering the dynamically loaded module fixes that owned validation-tool defect.
Its failed run directory is retained and is not counted as a render campaign.

## Final 1080p alternating controls

40 measured samples per side, eight alternating blocks, all hashes exact:

| Plugin/depth | Original median/min ms | Previous Rust median/min ms | Final Rust median/min ms | Final/original |
|---|---:|---:|---:|---:|
| Distance 8 | 54.8111 / 53.5390 | 70.75465 / 68.0948 | 21.36605 / 20.8207 | 0.3898 |
| Distance 16 | 60.1680 / 57.9874 | 62.68655 / 59.1610 | 20.0114 / 18.5333 | 0.3326 |
| Radial 8 | 3.62415 / 3.0632 | 3.4858 / 2.9490 | 3.4063 / 2.8970 | 0.9399 |

All eight paired blocks are below 1 for each of these three cells. The before
Distance ratios (1.2909 / 1.0419) reproduce the authoritative serial report;
the new integer mask path eliminates the shortfall with substantial margin.

## Final standard serial matrix

One unrepeated default-size sweep (1x1, 960x540, 1920x1080); below is 1080p. Times are median (minimum) ms. Historical before ratios are the authoritative main report, not simultaneous samples.

| Plugin | bpc | Preset | Before ratio | Original | Final Rust | Final ratio |
|---|---:|---|---:|---:|---:|---:|
| DistanceGradation | 8 | default | 1.284 | 54.942 (54.634) | 22.129 (20.846) | 0.403 |
| DistanceGradation | 8 | heavy | 0.915 | 106.424 (105.679) | 45.447 (45.060) | 0.427 |
| DistanceGradation | 16 | default | 1.048 | 59.589 (58.897) | 18.790 (18.569) | 0.315 |
| DistanceGradation | 16 | heavy | 0.775 | 111.825 (109.862) | 46.951 (46.238) | 0.420 |
| DistanceGradation | 32 | default | 0.786 | 71.440 (66.839) | 34.279 (33.209) | 0.480 |
| DistanceGradation | 32 | heavy | 0.743 | 116.856 (113.624) | 64.690 (63.456) | 0.554 |
| OLMRadialBlur | 8 | default | 1.010 | 3.504 (3.194) | 3.544 (2.920) | 1.011 |
| OLMRadialBlur | 8 | heavy | n/a | n/a | 322.200 (314.682) | n/a |
| OLMRadialBlur | 16 | default | 0.967 | 4.070 (3.966) | 3.691 (3.464) | 0.907 |
| OLMRadialBlur | 16 | heavy | n/a | n/a | 325.228 (319.729) | n/a |
| OLMRadialBlur | 32 | default | 0.879 | 5.710 (5.391) | 4.804 (4.617) | 0.841 |
| OLMRadialBlur | 32 | heavy | n/a | n/a | 330.025 (319.834) | n/a |

The final Radial 8-bpc sweep ratio is **1.011**, so a strict requirement that every final-sweep cell be below 1 is **not met**. The separate 40-sample alternating control is 0.9399 (8/8 paired block wins); this supports a modest improvement, but not an unconditional win in a five-frame sweep. No sweep was repeated or favorable samples selected. 540p Radial defaults are also marginal (1.050/1.089/1.013). Distance defaults meet the 0.9 target with substantial margin.

Original Radial active resident rows remain incomplete; no heavy ratio is invented. The audit passes (all accepted frame hashes, loaded executable identities, statistics and raw reports).
