# OLMDirectionalBlur PF_ParamCheckout ABI audit 20260711

Status: `static-AEX-grounded`; no existing file was modified. The audited binary
is `plugins_2025/OLMDirectionalBlur.aex` (image base `0x180000000`).

## Scope and method

This is an address/line audit of the 2025 AEX's parameter checkout and worker
context materialization. `disasm/OLMDirectionalBlur.aex.asm.txt` is treated as
primary; `decomp/OLMDirectionalBlur.aex.c.txt` is used to name fields and
control flow. The full-render fixture implements the host parameter checkout
callback. This sidecar itself is a static audit; the fixture now also records
the materialized worker context immediately after `FUN_180006c50` returns.

## Checkout record layout

**FACT:** `FUN_180006c50` clears `0xb0` bytes at `RSP+0x30`, passes that address
to the parameter checkout callback, then calls the parameter checkout cleanup
callback. See asm `0x180006c83..0x180006cc7`, `0x180006ce0..0x180006d29`, and
the corresponding decomp at lines 3260-3267 and 3267-3273.

**FACT:** In this function's stack frame, the callback result is consumed as:

| Effective offset in the `PF_ParamDef` record | Binary access | Effective type | Used by |
| --- | --- | --- | --- |
| `u` at `+0x38` | `dword [RBP-0x59]` / `qword [RBP-0x59]` | 32-bit integer/popup or 64-bit `PF_FpLong` | integer/popup fields and Brightness/Thickness |
| `u` at `+0x3a` | `word [RBP-0x57]`, sign-extended | signed 16-bit fixed-point/slider payload as actually consumed by this AEX | Angle, percentage-style float sliders, Noise Offset |

The offset calculation is direct: callback buffer is `RSP+0x30` and the
function establishes `RBP = entry-RSP-0x57`; therefore `[RBP-0x59]` is
buffer `+0x38` and `[RBP-0x57]` is buffer `+0x3a`. The reads are visible at
asm `0x180006cd0`, `0x180006d62`, `0x180006dce`, `0x180006eac`,
`0x180006f10`, `0x1800070bc`, `0x180007225`, and `0x18000729e`.

This describes the **actual wire reads**. It is intentionally not a claim that
every SDK-level `PF_ParamDef.u` member has the same nominal C type: the AEX's
loads are the conformance contract here.

## Requested indices

The setup routine establishes the sequential parameter order and types/defaults
in decomp lines 3473-3747; the worker checkout below is the authoritative
index-to-context mapping.

| Index | Parameter | Checkout union read | Worker context conversion/storage | Evidence |
| ---: | --- | --- | --- | --- |
| 1 | Angle | signed 16-bit at `u+0x3a` | raw value to `ctx+0x24`, then `(value + const)/const * const` conversion | decomp 3264-3273; asm `0x180006cb5..0x180006d24` |
| 2 | Brightness Gain | 64-bit `PF_FpLong` at `u+0x38` | narrowed to float at `ctx+0x28` | decomp 3277-3283; asm `0x180006d45..0x180006d70` |
| 3 | Size Variation | signed 16-bit at `u+0x3a` | divide by `0x18000b384` and store float at `ctx+0x30` | decomp 3287-3295; asm `0x180006d9e..0x180006dea` |
| 5 | Front Blur Strength | 32-bit integer at `u+0x38` | stored at `ctx+0x48` | decomp 3300-3308; asm `0x180006e18..0x180006e4b` |
| 6 | Front Alpha Fade | 32-bit integer at `u+0x38` | stored at `ctx+0x4c` | decomp 3312-3320; asm `0x180006e7c..0x180006eb4` |
| 7 | Front Sharp Tail | signed 16-bit at `u+0x3a` | divide by `0x18000b384`, store float at `ctx+0x40` | decomp 3324-3332; asm `0x180006ee0..0x180006f24` |
| 10 | Back Blur Strength | 32-bit integer at `u+0x38` | stored at `ctx+0x50` | decomp 3336-3344; asm `0x180006f52..0x180006f8a` |
| 11 | Back Alpha Fade | 32-bit integer at `u+0x38` | stored at `ctx+0x54` | decomp 3348-3356; asm `0x180006fb6..0x180006fee` |
| 12 | Back Sharp Tail | signed 16-bit at `u+0x3a` | divide by `0x18000b384`, store float at `ctx+0x44` | decomp 3360-3368; asm `0x18000701a..0x18000705e` |
| 15 | Noise Variation | signed 16-bit at `u+0x3a` | divide by `0x18000b384`, store float at `ctx+0x2c` | decomp 3372-3380; asm `0x18000709f..0x1800070d0` |
| 16 | Noise Type | 32-bit popup at `u+0x38` | store popup at `ctx+0x3c`; `ctx+0x80bc = (value == 1)` | decomp 3384-3393; asm `0x180007111..0x180007145` |
| 18 | Seed | 32-bit integer at `u+0x38` | store at `ctx+0x8108` | decomp 3401-3409; asm `0x1800071a1..0x1800071c6` |
| 19 | Noise Offset | signed 16-bit at `u+0x3a` | divide by constant `0x18000b380`, store float at `ctx+0x810c` | decomp 3413-3421; asm `0x180007208..0x18000723d` |
| 20 | Thickness | 64-bit `PF_FpLong` at `u+0x38` | narrowed to float at `ctx+0x8110` | decomp 3425-3434; asm `0x180007281..0x1800072ac` |

The setup code independently corroborates the intended control classes: popup
index 16 is created with type `7` at decomp 3653-3663, Seed index 18 with
type `1` and range/default material at 3675-3689, Noise Offset index 19 with
type `3` at 3691-3700, and Thickness index 20 with type `10` at 3702-3717.

## Current case values and output relevance

**FACT:** The current case values are `Noise Variation=0`, `Noise Type=1`,
`Seed=1`, `Noise Offset=0`, and `Thickness=10`; the existing parameter source
of truth records the same values at `notes/PARAMETER_SOURCE_OF_TRUTH.md:288-292`.

**FACT:** After checkout, the AEX stores Noise Variation at `ctx+0x2c` and
Noise Type at `ctx+0x3c`, then initializes internal mode `ctx+0x20` to `1`.
Only if `ctx+0x2c > 0` does it replace that mode with `2` when type is not `3`
or `3` when type is `3` (decomp 3391-3400; asm `0x180007158..0x180007176`).

**FACT:** The row driver applies the noise map only for internal mode `2`, or
calls the procedural noise helper only for mode `3`; mode `1` falls through
without either operation (decomp 1549-1566). The full render path repeats the
same mode-3 helper gate for its other passes at decomp 1916-1924, 2418-2426,
and 2917-2925.

**CONCLUSION:** With variation exactly zero, current `Noise Type=1`, `Seed=1`,
`Offset=0`, and `Thickness=10` cannot affect the output through the noise
variation/map/procedural-noise path. They are still correctly staged into
`ctx+0x3c`, `ctx+0x8108`, `ctx+0x810c`, and `ctx+0x8110`; changing them may
affect output only after variation becomes positive or through an unobserved
side path not present in these instructions. This last possibility is an
**INFERENCE**, not a claimed negative proof over the whole binary.

## Capture status

`tools/emulation/dblur_fullrender_host_fixture_20260711.py` provides the host
parameter-checkout callback and records the resulting worker context at
`0x180007cda`, `0x180007d85`, or `0x180007e30` for the active bit-depth path.
The 8bpc probe completed that gate. The actual AEX materialized mode `1`, angle
`1.5707963705062866`, brightness `1.0`, size/noise variation `0.0`, popup `1`,
seed `1`, offset `0.0`, and thickness `10.0`; all requested zero-valued
front/back fields also remained zero. The runtime values agree with the static
map above.
