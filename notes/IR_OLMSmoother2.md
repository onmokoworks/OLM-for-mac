# Binary-Grounded IR: OLMSmoother2

## Feature

- Plug-in: OLM Smoother v2
- Feature/path: 8bpc cel-line smoother, color-key, gamma/color-space, v1/v2
  compatibility
- Bit depth: 8bpc documented here; 16/32bpc still need references
- Reference set: `refs/win_references/20260605_extra/OLMSmoother2`
- Current status: no-key grid has packaged 8bpc `AE exact` evidence from the
  2026-06-19/2026-06-20 AE pixel returns. Standalone OLMSmoother v1
  `case_0001..0003` is also 8bpc `AE exact` after the corrected 960x540 rerun.
  Smoother2 legacy key/gamma slices remain guarded residuals, so Smoother2 as
  a whole is not complete.

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| Smoother is specialized in smoothing cel animation drawings. | Official v1/v2 manuals under `refs/upstream_official/20260619_olm_official_zips/pdf_text/`. | manual-backed |
| v2 adds color space conversion, Smoothness, Extra Smooth, Gamma Correction, 32-bit support, and improved diagonal smoothing. | Official v2 manual. | manual-backed |
| `Smoother Version` v1/v2 mainly affects Gamma Correction / linearization. | Official v2 manual says v1 does not linearize prior to processing. | manual-backed |
| Parameter setter initializes mode/key/palette/gamma fields and routes invert-key through the active palette. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_180004e10`. | binary-grounded |
| Frame setup order is setup, optional unpremultiply, active-palette filter, non-invert scalar-key filter, then optional sRGB decode. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_180002e90`. | binary-grounded |
| Active-palette filter compares RGB against palette entries using threshold `0.001960922` and zeroes alpha for non-matches. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_180002930`. | binary-grounded |
| Non-invert scalar-key filter compares RGB against scalar key with threshold `0.001960922` and zeroes alpha for matches. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_180002a70`. | binary-grounded |
| Class-plane generation uses Smooth Range in the no-key path as `SmoothRange / 100.0 + 0.001`. | `notes/OLMSmoother2_ASM_FACTS.md`, no-key grid finding. | binary-grounded / reference-confirmed |
| Class-plane bytes record self-vs-left, self-vs-top, self-vs-top-left, self-vs-top-right local comparisons. | `notes/OLMSmoother2_ASM_FACTS.md`, `FUN_18000ae10`. | binary-grounded |
| Smoothing geometry is not an 8-neighbor blur. It is a 2x2-cell classifier that builds an 8-bit switch index and dispatches into a large helper table. | `disasm/OLMSmoother2_port_gap_analysis.md`, `FUN_18000c280`, `disasm/OLMSmoother2_case_map.txt`. | binary-grounded |
| Polygon vertices sample integer grid pixels, not bilinear positions. | `disasm/OLMSmoother2_port_gap_analysis.md`, `FUN_1800104d0`. | binary-grounded |
| Small corner helper family uses `0.125` base step and `0.4/0.2/0.4` weights. | `disasm/OLMSmoother2_port_gap_analysis.md`, `FUN_1800134c0`, `FUN_180013570`, `FUN_180012c20`, `FUN_180012ce0`. | binary-grounded |
| `FUN_18000cc70` normalizes emitted vertex weights by vertex count. | `disasm/OLMSmoother2_port_gap_analysis.md`. | binary-grounded |
| Final writeback premultiplies RGB by output alpha in `FUN_1800036e0`-like path. | `notes/OLMSmoother2_ASM_FACTS.md` and current CLI improvement. | binary-grounded / guarded |

## Parameters

| UI / manifest name | Internal meaning | Evidence |
| --- | --- | --- |
| `Use Color Key` / `Enable Color Key` | Enables key filtering before smoothing. | asm setter |
| `Invert Color Key` | Routes key color through active-palette keep filter when enabled; non-invert uses scalar-key remove filter. | asm setter/frame setup |
| `Color Key` | Scalar key color or one-entry active palette, depending on invert. | asm setter |
| `Smoothness` | Strength of smoother interpolation. | manual + port |
| `Extra Smooth` | Additional smoothing strength/path. | manual + port |
| `Smooth Range` | No-key class-plane threshold; nearby colors can be treated as same-color. | asm/grid |
| `Smoother Version` | v1/v2 gamma/linearization behavior. | official manual + asm |
| `Gamma Correction`, `Gamma Value`, `Gamma Colors` | Post-linearization gamma handling; gamma colors list is separate from active palette. | asm setter |

## Frame Setup

Current binary-grounded order:

1. `FUN_1800024c0`: frame scratch setup.
2. If byte `[SMParams + 0x18] != 0`: unpremultiply.
3. If qword `[SMParams + 0x60] != 0`: active-palette filter
   `FUN_180002930`.
4. If byte `[SMParams + 0x14] != 0`: non-invert scalar-key filter
   `FUN_180002a70`.
5. If dword `[SMParams + 0x0] != 1`: sRGB decode.

Important caution: the scalar-key filter gate is not the UI invert checkbox.
It corresponds to the non-invert scalar-key branch populated by the setter.

## Class Plane

- Built after frame setup.
- Effective threshold for no-key path:
  `SmoothRange / 100.0 + 0.001`.
- Byte layout:
  - byte 0: self vs left, when `x >= 1`
  - byte 1: self vs top, when `y >= 1`
  - byte 2: self vs top-left, when `x >= 1 && y >= 1`
  - byte 3: self vs top-right, when `y >= 1 && x + 1 < width - 1`
- ASM writes `0` or `1` via `SETNC`. Current port uses zero/nonzero semantics;
  storing `0xff` is equivalent only if downstream never compares numeric byte
  values.
- Optional pruning guarded by `[SMParams + 0x70]` should not run for no-key
  `case_0001` unless stronger evidence appears.

## Polygon Builder / Dispatch

`FUN_18000c280` builds the anti-aliased smoothing polygon. The important
structural rule is that this is a cell classifier, not a free 8-neighbor
filter.

- The switch value is:
  `switch_val = (iVar3 + uVar9 + ((!bVar16 + uVar7 * 2) * 4)) * 0x10 + iVar4 + (local_1b7 == 0) + iVar11 + iVar10`.
- The low nibble comes from four class-plane bytes for the current 2x2-ish
  cell; the high nibble comes from neighboring context probes.
- `disasm/OLMSmoother2_case_map.txt` currently maps 222 used cases and 34
  fallthrough/default cases.
- The polygon struct uses a vertex array at Win offset `+0x40` and a count at
  `+0x130`. Each vertex is sampled by integer grid coordinate through
  `FUN_1800104d0` as `{R,G,B,A,w}`.
- Corner helpers are small and already high-confidence:
  - NW `FUN_1800134c0`: `(-1,0)`, `(-1,-1)`, `(0,-1)` with `0.4/0.2/0.4`.
  - NE `FUN_180013570`: `(0,-1)`, `(+1,-1)`, `(+1,0)` with `0.4/0.2/0.4`.
  - SW `FUN_180012c20`: `(-1,0)`, `(-1,+1)`, `(0,+1)` with `0.4/0.2/0.4`.
  - SE `FUN_180012ce0`: `(0,+1)`, `(+1,+1)`, `(+1,0)` with `0.4/0.2/0.4`.
- The current Mac port has many literal helper/dispatcher pieces already, but
  it still contains diagnostic controls such as `--idx18-mode` and
  `--skip-index`. Those are probes only; they must not be used as acceptance
  fixes.

## Distance Metric

`FUN_18000b2b0`:

- returns zero when both alphas are zero;
- otherwise returns `max(abs(dR), abs(dG), abs(dB), abs(dY709)) + abs(dA)`;
- luma coefficients are `0.2126`, `0.7152`, `0.0722`.

## Current Residual Interpretation

- 2026-06-19 AE pixel return update:
  `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmsmoother2_no_key_grid_20260619/reports/ae_pixel_no_key_grid_exact.json`
  is exact for all 12 no-key grid cases. This means the current Mac AE plug-in
  path matches the packaged Windows Software reference for that grid. The older
  AE-free residual remains useful as a harness/IR discrepancy, not as a reason
  to PNG-tune the no-key Mac AE path.
- The same return leaves the legacy key/gamma request red:
  `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json`
  fails all 7 cases with max diff up to `254`. The next Smoother blocker is
  legacy setup/key/gamma/writeback evidence, plus optional runtime trace to
  explain why the no-key AE path is exact while the CLI harness previously was
  only near-exact.
- 2026-06-20 AE pixel rerun:
  `refs/reports/ae_host_validation_20260620_1425/`.
  This confirms the v1 reference-shape issue was a packaging/render setup
  problem, not an algorithm result: `OLMSmoother v1 case_0001..0003` are exact
  at `960x540`. The same rerun keeps Smoother2 legacy key/gamma red at `0/7`
  exact, with the same `max=101/254` range.
- No-key `case_0001` residual is dominated by pixels where candidate smoothed
  but reference looks like input. This points to class-plane / dispatch firing
  too often, not final PNG premultiply alone.
- Diagnostics that skip cardinal branches are not valid promotions because the
  Windows binary calls those branches.
- 2026-06-19 diagnostic run:
  `refs/reports/olmsmoother2_forecast_20260619_021900/`.
  The no-key grid still has 3 exact zero-smoothness cases and 9 residual
  cases with `max=4/8/9`. The hottest classifier indices are `0xff`, `0x1f`,
  `0xf8`, `0x18`, `0x00`, `0xd6`, `0x6b`, and `0x42`.
- In the same run, `idx=0x18` leaf histograms are concentrated at:
  - cardinal 12: keys `0x29`, `0x55`, plus tiny counts at `0x2a`, `0x01`,
    `0x28`.
  - cardinal 3: keys `0x21`, `0x4d`, plus tiny counts at `0x14`, `0x1e`,
    `0x13`, `0x2b`.
- Negative probes saved beside that diagnostic run show that suppressing all
  `idx=0x18`, or suppressing either of its cardinal sides, worsens the grid.
  Therefore `idx=0x18` is a hot fidelity target, not a branch to delete.
- 2026-06-19 follow-up with `--trace-pixel` found that the current max-diff
  pixels in `sm2_no_key_s100_r3` are mostly `idx=0x10` and `idx=0x08`.
  These pixels emit two duplicate samples:
  - `idx=0x10`: weights `0.4` and `0.2`.
  - `idx=0x08`: weights `0.32` and `0.2`.
  Candidate pixels are weaker than the Windows reference. However, globally
  changing `W_IN_W` from `0.2` to `0.4` worsens the grid and does not move
  those sampled pixels, so the hot `0.2` is not the global corner-helper
  constant. Suppressing `idx=0x08` or `idx=0x10` also worsens the grid.
- Static recheck of those hot paths confirms the top-level dispatch:
  `idx=0x08/0x10` both call `FUN_180010820` and then `FUN_1800105f0`.
  The observed `cardinal3` keys (`0x14` / `0x1e`) and `cardinal12` key
  (`0x29`) map to the same leaf sequences in Mac as in the Windows decomp.
  `FUN_1800104d0`, `FUN_18000c0d0`, `FUN_18000ab00`, `FUN_18000b120`, and
  `FUN_1800036e0` also match structurally.
- 2026-06-19 Ghidra follow-up rechecked the hot span leaves
  `FUN_18000ec40` and `FUN_18000e640`. Their weights are built from scanned
  run endpoints using `(span + 1) * (extra * 0.2 + 0.5) / total`, then emitted
  through `FUN_18000e430` / `FUN_18000e320` and `FUN_180013630`. The Mac
  formulas still match at the decomp level, so the next trace request now asks
  for the scan helper returns as well as append/writeback values.
- 2026-06-19 Ghidra MCP recheck of `FUN_18000d520`, `FUN_18000dbd0`,
  `FUN_18000d230`, and `FUN_18000d800`: the call sites set `RCX`, `RDX`, `R8`,
  `R9`, and `[RSP+0x20]` immediately before `FUN_180010550`. The classifier
  first uses only `CL`, `DL`, and `R8B` to choose the jump target:
  `index = p1 + (p3 + p2 * 2) * 2`, table base `DAT_1800105d0`. Existing
  disasm notes resolve `idx=0..6` as fixed classes, while `idx=7` jumps to a
  variable target that reads the extra context (`R9B` and the stack argument)
  to return classes `6..9`. Therefore the live model is "3-input index,
  optional 2-input refinement for idx=7", not a plain 3-input table.
- 2026-06-19 second Ghidra MCP assembly check pinned the concrete scanner
  argument mapping. This matters because the decompiler often presents
  `FUN_180010550` as 3-argument, but the call ABI clearly carries two extra
  context bits:
  - `FUN_18000d520` at `0x18000d640..0x18000d64d`: `CL=R@(x-1,y)`,
    `DL=A@(x,y-1)`, `R8B=A@(x,y)`, `R9B=G@(x,y)`,
    `[RSP+0x20]=B@(x-1,y)`.
  - `FUN_18000d230` at `0x18000d367..0x18000d377`: `CL=R@(x-1,y+1)`,
    `DL=A@(x,y)`, `R8B=A@(x,y+1)`, `R9B=G@(x,y+1)`,
    `[RSP+0x20]=B@(x-1,y+1)`.
  - `FUN_18000dbd0` at `0x18000ddaa..0x18000ddc0`: `CL=R@(x,y)`,
    `DL=A@(x,y)`, `R8B=A@(x,y-1)`, `R9B=G@(x,y)`,
    `[RSP+0x20]=B@(x-1,y)`.
  - `FUN_18000d800` at `0x18000d9e7..0x18000d9fd`: `CL=R@(x,y+1)`,
    `DL=A@(x,y+1)`, `R8B=A@(x,y)`, `R9B=G@(x,y+1)`,
    `[RSP+0x20]=B@(x-1,y+1)`.
  The current Mac port's p4/p5-aware classifier model matches this assembly
  shape; the remaining no-key residual should be traced at the scanner return
  and append stages rather than by removing the idx=7 refinement.
- 2026-06-19 rejection probe: forcing `win_FUN_180010550` back to the resolved
  fixed 3-input table worsened the no-key grid from the guarded `max=4/8/9`
  band to `max=14/24/41` with about `1.0%..2.5%` nonzero pixels. Keep the
  current scanner-sensitive idx=7 refinement until Windows runtime trace proves
  the exact scan helper return behavior and context bytes.
- A Mac-side baseline trace for witness pixel `(211,139)` was saved at
  `refs/reports/olmsmoother2_trace_baseline_20260619_024716/mac_trace_211_139.log`.
  A fuller four-pixel baseline was later saved at
  `refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/`.
  The current Windows request package is
  `refs/runtime_trace_packages/olm_runtime_trace_olmsmoother2_no_key_grid_scan_append_p1p5_with_mac_baseline_20260619_030034.zip`.
- Next required evidence is a Windows runtime trace of the exact witness
  pixels, not another PNG-only tuning pass. The trace should decide whether
  Windows emits an additional duplicate sample, differs in the leaf span/weight
  formula at runtime, or matches the polygon and diverges only during final
  composite/writeback.

2026-06-19 Ghidra MCP recheck:

- `FUN_1800104d0` appends exactly one integer-grid source sample, copying two
  qwords of float RGBA from the source world and storing the caller-supplied
  float weight at `vertex + 0x10`.
- `FUN_18000c280` still dispatches `idx=0x08/0x10` through
  `FUN_180010820` and `FUN_1800105f0`, then copies the local 12-vertex polygon
  to the caller.
- `FUN_1800036e0` composites through `FUN_18000cce0`, optionally applies
  sRGB/gamma conversion, optionally premultiplies by alpha, and writes float
  RGBA in output order `{A,R,G,B}`.
- The trace request now asks for `FUN_180010550` p1/p2/p3 plus the surrounding
  idx=7 context at the four scan helpers because an incorrect scanner
  endpoint/context descriptor would explain the residual without changing
  global weights.

## Conformance Cases

| Case group | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| no-key grid | 8bpc | AE exact for packaged grid | 12/12 exact in 2026-06-19 and 2026-06-20 AE pixel returns | Optional runtime trace for binary-grounding; do not PNG-tune |
| key/gamma paths | 8bpc | guarded | 0/7 exact in 2026-06-20 legacy AE pixel rerun | Runtime/static proof for legacy key/gamma setup and writeback |
| standalone v1 | 8bpc | AE exact for packaged v1 slices | 3/3 exact in corrected 960x540 2026-06-20 AE pixel rerun | Decide whether v1 stays independent or maps to v2 compatibility |

## Open Questions

- Remaining scanner/leaf behavior around `idx=0x18`.
- Whether class-plane byte value `1` vs `0xff` matters in any downstream path.
- Exact AE-host Mac output against Windows Software refs for legacy key/gamma.
- 16bpc and 32bpc smoothing/writeback behavior.
