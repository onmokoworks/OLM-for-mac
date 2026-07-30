# OLMKiraKira hotspot / outer-stage reconciliation

Date: 2026-07-30
Status: **binary-grounded static path / runtime outer writer unbound**
AE exact: **false**

## Separate static facts

The pinned PF8 AEX contains the following separately proven facts:

1. `FUN_18114d220` calls the ray driver at `0x18114d62c`.
2. `FUN_18114f4a0` selects inner Mode 1 through vtable slot `+0x08` at
   `0x18114fc86`, or inner Mode 2 through `+0x10` at `0x18114fc28`.
3. After the ray-driver call, the owner copies pointer fields `+0x78` to
   `+0x128` and `+0x140` to `+0x190`, at `0x18114d71e..0x18114d730`.
4. The owner then calls PF8 outer compose `FUN_18114e110` at `0x18114d73d`.
5. That function reads glow from owner `+0x190`, source from `+0x128`, and
   writes through `FUN_181230b90` at `0x18114e287` or `0x18114e3e9`.

Static ordering does not prove that the runtime pointer staged at `+0x190`
aliases the output written by the selected inner aggregator, nor that the
pointer-to-XY placement used by the 2026-07-01 artifact is the same as the
outer writer. Continuous runtime dataflow remains unbound.

Owner `+0x44 == 1` reaches the normalized branch at `0x18114e2b7`; its
`DIVSS` is at `0x18114e374`. Value `2` reaches the direct weighted-sum branch
at `0x18114e167`. Neither branch implements screen composition.

## Hotspot arithmetic

The executable test strictly parses these values from
`olmkirakira_hotspot_lane_audit_20260701.json`:

- `case_id` and `witness_xy`
- `mac_compose_boundary.src_rgba_float`
- `mac_compose_boundary.glow_rgba_float`
- `mac_compose_boundary.out_u8` (`144`)
- `mac_compose_boundary.windows_reference_u8` (`131`)

The comparison artifact separately declares source/glow opacity `1` under
`windows.fun_18114fd90_aggregation.entry`. The test strictly parses those
fields and requires the comparison case to match the lane-audit case. Because
that entry is not itself bound to the outer writer, the following values are
classified as **hypothetical unit-opacity outer predictions**, not captured
outer outputs:

| Model | Float RGB | PF8 RGBA |
| --- | --- | --- |
| Outer Mode 1 | `0.41469344...` | `[105,105,105,255]` |
| Outer Mode 2 | `0.62515270...` | `[159,159,159,255]` |
| 2026-07-01 screen model | `0.56544616...` | `[144,144,144,255]` |

These are three distinct output classes. The canonical PNG value `131` is a
fourth class.

## Reconciliation limit

The parsed case is `kk_vertical_len50_brightness1_strength100`, the parsed XY
is `(934,118)`, its Mac output is `144`, and its retained Windows reference is
`131`. The 2026-07-01 artifact identifies the formula under test as
screen composition, but it does not bind that value to `FUN_18114e110`, either
PF8 writer callsite, concrete owner `+0x128/+0x190` pointers, or a concrete
writer destination. Its `144` therefore remains an outer-writer-unbound model
or stage witness. It cannot override the pinned static outer path.

Static evidence proves that the pinned outer functions are not screen
composition. It does not prove that the retained artifact traversed those
functions with the parsed values, and therefore does not uniquely authorize a
production edit.

## Required runtime witness

At PF8 Mode 1 writer call `0x18114e3e9`, and Mode 2 call `0x18114e287` if both
modes will be implemented, capture for one same-run pixel:

- loaded AEX SHA-256 and owner `+0x44`
- owner `+0x128` and `+0x190` pointer values
- source and glow RGBA float words at the selected XY
- `XMM0..XMM3` immediately before `FUN_181230b90`
- destination pointer at `[RSP+0x20]`
- four destination bytes after the writer returns
- the same-run exported pixel and render metadata

Until that witness binds path, pointers, XY, and output, production compose
changes remain **not authorized**.

## Verification

```sh
python3 -m unittest tests.test_olmkirakira_hotspot_outer_stage_reconciliation_20260730
```
