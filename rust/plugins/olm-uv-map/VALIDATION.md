# OLM UV Map — integrated 2026-11-12 release

## Current direct qualification (2026-11-13)

The final twelve-plug-in workspace candidate passes the **ordinary direct oracle**
using AEXCompat `032a187621353bac7b92a76ae394ac387ddedf51`. No bridge or sparse
fixture is used. Smart8/16/32, downsample 1, 1/2 and 1/4, fresh per-process
renders, at most three concurrent renders. Counts below are **per depth**.

| Reference | Smart8 | Smart16 | Smart32 |
| --- | ---: | ---: | ---: |
| New 64/2025 | 30 exact | 30 exact | 30 exact |
| New 64/2026 sample | 12 exact | 12 exact | 12 exact |
| New original-verified golden | 18 exact | 18 exact | 18 exact |

Zero pixel mismatches, reference/candidate failures or timeouts remain in these
campaigns. Inventory matches the 2025 original. Textures are separate 17x9, 1x5 and 33x17 inputs.

[Integration report](../../INTEGRATION.md),
[hash-bound qualification](../../evidence/integration-20261112/qualification.json),
[staged identity](../../evidence/integration-20261112/staged-identities.json) and
[golden verification](../../tools/golden/verification.json) are the current
authority. Native AE UI/project acceptance remains unverified. Prior job reports
below retain their original hashes and diagnostic observations as **history**;
their old bridge, harness-limit, pending-golden or local-only hoisting statements
are superseded by the direct evidence above.

---

﻿# OLM UV Map validation — Job N-uvmap

2026-11-13, Windows x64. The Rust CPU port passes every declared AEXCompat
route (`smart8`, `smart16`, `smart32`) against the 2025 original. All final
image comparisons are bit-exact, without tolerances or residual exceptions.
Native AE and macOS acceptance remain unverified.

Machine-readable results: [validation-results.json](validation-results.json).
Large raw campaigns and decompilation stay in ignored `local/`; original DLLs
remain outside the repository.

## Identity and saved-project declarations

| Artifact | SHA-256 |
| --- | --- |
| Original 64/2025 | `412de99a5af617f41d8c0deddc2bdc7fb8b38065b34af2966730e01b72cb2c62` |
| Original 64/2026 | `c8afcf81c4c037611ccacf9bb2eeed645b33f06d131e9220984c49fa1904e0a8` |
| Qualified `local/final-bin-v3/OLMUVMap.aex` | `9b99346d70716491f0e2ef18b347f9a4bcc43dfdbd901cdb2626bd1b53484631` |
| AEXCompat harness | `68a251fed8131d3a32cdcbd8797aba9959be417d8da68d1e80f44d087c75e9ba` |
| Complete 290-byte Windows PiPL | `ade072a4261f2b5ae623d0776a0cfaf730e7e11e07020b45fe244405b5c18c52` |

Scaffold output was generated in `rust/tools/scaffold/local/N-uvmap-initial`
and reviewed before moving into this crate. Public inventory and supplemental
PARAMS_SETUP recapture are identical. Complete Windows PiPL bytes, type `PIPL`,
ID 16000 and language 1033 match. Evidence: `local/release-inventory/`,
`local/release-declarations/`.

- Name/match name `OLM UV Map`, category `OLM Plug-ins`, entry `entryPointFunc`.
- Runtime version 559104 (1.1.1 Develop); flags `0x02000040` / `0x18001400`.
- Four parameters including input. Texture slot/disk ID 1, default -1;
  interpolation slot/ID 2, default 3, exact strings
  `Nearest Neighbor|Bilinear|Trilinear`; Smoothness slot/ID 3, range 0..1,
  default 0.5, flags 64. Raw defaults/precision/flags are preserved.
- No arbitrary-data parameter is declared. The inherited opaque callback test
  is not evidence of an actual saved-project round trip.

Smoothness enable/disable follows the manual and original UI function `0x4080`;
Rust uses PF ParamUtils rather than the original AEGP stream lookup. Native UI
and saved-project loading remain untested. `scaffold.json` retains historical
generator TODO metadata; this document describes the completed port.

## Final render campaigns

Fresh processes are authoritative; at most three render workers were used.
Every row below uses the qualified production DLL above.

| Campaign | 8bpc exact | 16bpc exact | 32bpc exact | Failures |
| --- | ---: | ---: | ---: | ---: |
| 2025, seed 20261113 | 103 | 103 | 103 | 0 |
| 2025, seed 20261114 | 103 | 103 | 103 | 0 |
| 2026, seed 20261115 | 24 | 24 | 24 | 0 |
| 2025, cropped output demand | 12 | 12 | 12 | 0 |
| 2025, no texture, methods 1/2/3 | 3 | 3 | 3 | 0 |

The principal seeds give **200 random plus six boundary/default cases per
depth**, 618 comparisons total. The first three cases per seed are untouched
defaults, minima and maxima; the next 100 are random. Downsample requests cover
**1, 1/2, 1/4**. Primary sizes: 1x1, 3x7, 11x7, 31x19, 97x61. Texture sizes:
17x9, 1x1, 2x1, 1x5, 33x17, 8x16 for seed A, reverse order for seed B.
16bpc compares native u16 sidecars; 32bpc compares raw f32 words.

2026 uses primary sizes 3x7/11x7/31x19, textures 17x9/1x5/33x17 and all three
scales: 72 comparisons, not another 200-random campaign. Crop probes use 11x7,
textures 17x9/1x5, demand `(1,1,9,6)`, seed 778899 and all three scales.
No-texture probes cover all methods/depths at 11x7/full scale; all nine agree
with the original's transparent result.

Evidence directories: `local/release-seed-20261113/`, `release-seed-20261114/`,
`release-2026/`, `release-crop/`, `release-no-texture/`. Earlier pilot,
`final-seed-*`, and failed crop runs are not counted again.

After diagnostic exports were built, Cargo relinked the production target DLL
(SHA-256 `6d6cda2c775f8ead338598ae35a5c88815827b887edfe4c5a1f3ba2b6b20c08e`).
`local/production-rebuild-identity.json` proves identity with the qualified DLL
except PE/debug timestamps and CodeView GUID/age. Code/resources/data are
unchanged; the staged qualification DLL is retained.

## Secondary-layer and extent contract

Oracle requests assign slot 1 to a hashed PNG. The harness supplies its world
through PF_CHECKOUT_PARAM, promotes native depth, and retains independent
texture dimensions. PNGs are preview worlds; downsample metadata must not cause
an additional resize in the port. The adapter checks depth and balances layer
checkout/checkin for every render.

Original Smart render uses plain Iterate over **output.extent_hint**, with
local input/output coordinates, not world-origin offsets. The first crop probe
exposed a port bug in the scaffold-derived origin adjustment. Ghidra `0x3be0`,
a real-render record of preparation `0x3750`, and 40 pixel callback records
showed an 8x5 output walked at x=0..7/y=0..4. The adapter was corrected and both
crop and full campaigns rerun. This was a port bug, not original UB.

Fifteen fixture-v2 pairs attempting custom primary/secondary padding, origin
and extent were rejected before rendering:
`still primary requires a non-cluster Smart session without custom layer layouts`.
`local/geometry-01/` retains these failures. They are not passing image tests.
Padded rows are separately covered by function witnesses. Actual AE checkout
geometry, especially nonzero texture origins, remains a host acceptance item.

## Reverse engineering and automatic/manual work

Ghidra analyzed 118 internal functions. Funcdb found 91 exact, five fuzzy,
22 unknown (`rust/tools/scaffold/local/N-uvmap-funcdb.json`). Effect kernels
were unknown; matching runtime/suite wrappers did not prove a reusable Rust
effect kernel. Existing olm-math conversion helpers are reused.

Autoport was tried first, with render root `0x3be0`, pixel callbacks
`0x1bf0/0x2550/0x2ea0`, and derivative `0x4780`. One reviewed ABI/vector
contract was admitted under a two-attempt budget. **One Codex call** generated
derivative `0x4780`, built it and passed **128 native witness vectors** on its
first attempt. Generation: 26.453 seconds; entire attempt: **27.609 seconds**;
usage: 13,821 input and 984 output tokens. Its algorithm was integrated unchanged
(formatting only). Evidence: `D:/olm-rs-target/N-uvmap/autoport-01/` and
`local/autoport-config.json`.

Final autoport graph state was `needs_human`: other nodes lacked admitted
contracts or verified callees. It did not integrate the whole plug-in or run
the image oracle automatically. Manual work comprised three depth-generic
kernel groups (bilinear sampling, pixel processing, mipmaps), numerical support,
and AE/UI lifecycle integration. Manual wall time was not separately measured;
autoport attempt time is not presented as total port time.

| Native witness family | Original RVA(s) | Exact calls |
| --- | --- | ---: |
| Bilinear 8/16/32 | 0x14a0, 0x11c0, 0x1770 | 48/depth = 144 |
| Pixel callbacks, Nearest/Bilinear branches | 0x2550, 0x1bf0, 0x2ea0 | 48/depth = 144 |
| Mipmap generation, all depths | 0x4ab0 | 18/depth = 54 |
| Autoport derivative vectors | 0x4780 | 128 |
| Real-render recorded derivative calls | 0x4780 | 61 |

`local/release-witness/` is the final 342-call manual-kernel run, using diagnostic
bridges built with the `witness` feature. Pointer arenas, guard/padding bytes,
native return/output bits, and odd/non-power-of-two dimensions are checked.
Standalone pixel witnesses cover methods 1/2; Trilinear integration is covered
by the image oracle and golden fixtures. `local/record-01/` contains 61 completed
real-render derivative calls with verified cleanup; `local/record-witness-01/`
replays all 61 exactly against the generated Rust helper.

A local logf extension was required because olm-math lacks that API. It passes
**50,009 native inputs per FMA/non-FMA mode**, zero differing bits. Provider,
raw table provenance, and the ownership exception are in [NUMERICS.md](NUMERICS.md).
There is no platform-libm fallback.

There are no residual image mismatches to send to ubdetect. The diagnosed crop
bug was corrected; custom-layout rejection is a harness limitation, not evidence
of original UB. Record/witness localized the issue without needing diverge.
No unrun tool is claimed as validation.

## Tool improvements and tests

Existing public function signatures/request schemas remain compatible.

- **oracle:** additive `--layer-sizes` and optional per-slot `layer_sizes`, with
  same-size default unchanged; minimized metadata follows actual asset sizes;
  fixed deep request-sidecar labels to RGBA (fixture buffers remain ARGB).
  **47 tests passed**.
- **scaffold:** proxy builds honor CARGO_TARGET_DIR; fallback unchanged.
  **11 tests passed**. Initial bootstrap exposed the old behavior and wrote its
  target inside the ignored capture directory; the tool was fixed afterward.
  No captured state was deleted.
- **record:** uses DBG_REPLY_LATER for another owned suspended thread's queued
  INT3 until the single-step owner resumes it; same-thread nested INT3 remains
  an error. Fixes a reproduced intermittent capture race. **20 tests passed**,
  including eight repeated concurrent captures, crash, timeout and cleanup.
- **crate:** release build and strict Clippy pass; **12 Rust tests pass, zero
  ignored**. Nine golden fixtures cover all methods/depths, are extracted from
  hash-verified final original outputs, and record provenance. The tests were
  rerun after regenerating those fixtures.

```powershell
$env:CARGO_TARGET_DIR='D:/olm-rs-target/N-uvmap'
cargo test --manifest-path rust/Cargo.toml --release --offline -p olm-uv-map -j 2
cargo clippy --manifest-path rust/Cargo.toml --release --offline -p olm-uv-map -j 2 -- -D warnings
python -m unittest discover -s rust/tools/oracle -p 'test_*.py' -q
python -m unittest discover -s rust/tools/scaffold -p test_scaffold.py -q
python -m unittest discover -s rust/tools/record -p test_record.py -q
```

[README.md](README.md) gives full campaign commands. Oracle's WindowsJob waits
for owned descendant count zero before returning. The four main campaigns
contain 1,452 successful process exits; no-texture adds nine reference/candidate
pairs. Witness/record manifests also verify cleanup. No task-owned daemon
remains. The existing Ghidra hub, port 8766/PID 32480, was reused and left alive
under the user's lifecycle instructions; it was not owned by this job.
No AE, GUI, install, commit or push was performed.

## Handoff and remaining gaps

1. **olm-math owner:** migrate local logf/tables into the shared crate, preserving
   both modes, numerical evidence and OLM-internal notices.
2. **autoport owner:** support reviewed recorded pointer-arena contracts,
   dynamic Iterate callback roots and integration into a layer-aware scaffold.
   No autoport source was changed. The one-function trial did not close the
   whole render graph automatically.
3. **harness owner:** support fixture-v2 custom Smart world layouts so texture
   origin/extent/padding can be qualified at the adapter boundary.
4. **workspace owner:** add this plug-in to bundle/CI golden lists and refresh
   Cargo.lock for olm-uv-map. Cargo generated that entry during builds; this
   job removes only its own new block afterward to respect assigned ownership.
   Other jobs' lockfile changes are preserved.
5. **macOS/AE:** compile/package both architectures, load in AE, exercise UI,
   saved projects and actual checkout geometry. Source cfg and Mac PiPL are
   present; no Mac build/bundle or native-host acceptance is claimed.
6. **Numerical domain:** image tests use PNG-promoted finite SDR values.
   Arbitrary HDR/negative/NaN images, temporal texture sequences, other CPU math
   profiles and all IEEE edge states remain unqualified.
