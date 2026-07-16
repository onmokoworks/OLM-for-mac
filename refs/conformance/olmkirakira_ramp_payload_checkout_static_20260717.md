# OLMKiraKira Ramp Payload Checkout Static Audit

Date: 2026-07-17
Scope: read-only static analysis of `plugins_2025/OLMKiraKira.aex`
Evidence: `decomp/OLMKiraKira.aex.c.txt` and `disasm/OLMKiraKira.aex.asm.txt`

This artifact records the ramp parameter checkout/copy path only. It does not
modify production code, the ledger, or the current Mac implementation.

## FACT

### Registration and defaults

`FUN_18114c1a0` registers five ramp parameters through
`FUN_181152eb0`, whose local parameter type is `0xD`:

| Ramp | Disk ID | Decomp registration line |
| --- | ---: | ---: |
| Vertical Color Ramp | `0x1D` | 3522283 |
| Horizontal Color Ramp | `0x1F` | 3522298 |
| Diagonal Color Ramp | `0x21` | 3522313 |
| Diagonal 2 Color Ramp | `0x25` | 3522328 |
| Highlight Color Ramp | `0x27` | 3522343 |

Source: `decomp/OLMKiraKira.aex.c.txt:3522240-3522350`.

For all five calls, the ramp helper receives `param_5 = 0`. The second
default argument is the masked bit pattern built from the color defaults before
the ramp registration. The exact call-site pattern is preserved in the
decomp; its host-ramp field semantics are not proven by this binary alone.

The corresponding `Use Ramp` parameters are registered with a zero default
(`uVar2 = 0`) at decomp lines 3522285, 3522300, 3522315, 3522330, and
3522346.

### Handler construction and vtable

`FUN_1811513a0` constructs the effect-owned handler object and installs
`ae_param::RampDataHandler::vftable` at `param_1[0x40]`:

- Decomp: `decomp/OLMKiraKira.aex.c.txt:3525013-3525022`
- Constructor call: `FUN_181232790` at `0x181232790`
- Constructor assembly: `disasm/OLMKiraKira.aex.asm.txt:3790042-3790046`

The vtable address is VA `0x1814D66C8`, raw PE offset `0x14D58C8`. Its first
entries are `0x1812327B0` and `0x181232860`; subsequent entries point to the
exception stub at `0x18132D5E8`:

```text
0x1814D66C8: 0x1812327B0
0x1814D66D0: 0x181232860
0x1814D66D8+: 0x18132D5E8
```

`FUN_181232760` invokes the handler's second slot to release the stored host
handle (`decomp:3695690-3695700`). These entries are lifetime/handle cleanup,
not a separately recovered plugin flatten/unflatten implementation.

### Exact checkout and host payload copy

`FUN_181154630` is the ramp checkout helper. It searches the effect parameter
ID array, obtains PF Handle Suite, checks out the parameter handle, calls the
returned ramp object's method at `+0x8`, then adds `0x10` to that returned
object pointer before copying.

Relevant references:

- Decomp function: `FUN_181154630`,
  `decomp/OLMKiraKira.aex.c.txt:3527291-3527390`
- Function VA: `0x181154630`
- Assembly: `disasm/OLMKiraKira.aex.asm.txt:3572927-3573032`
- Host checkout call: assembly `0x181154706-0x181154712`
- Object payload base: assembly `0x181154714` (`returned_object + 0x10`)

The copy is exactly `0x144` bytes:

| Destination range | Source range | Size | Evidence |
| --- | --- | ---: | --- |
| `dst + 0x000 .. 0x0FF` | `object + 0x010 .. 0x10F` | `0x100` | two `0x80`-byte SIMD copy loops, asm `0x181154720-0x181154770` |
| `dst + 0x100 .. 0x143` | `object + 0x110 .. 0x153` | `0x44` | four SIMD moves plus one dword, asm `0x181154772-0x181154796` |

The host object is released through its method at `+0x10`, then the temporary
PF handle wrapper is released (`FUN_181232760`). This establishes the byte
layout and size, but not semantic names for the fields inside the payload.

### Five state destinations and use bytes

`FUN_18114e860` checks out each ramp only if its corresponding use byte is
nonzero:

| Ramp | Use byte | Payload destination | Call site |
| --- | ---: | ---: | --- |
| Vertical | `state + 0x83C` | `state + 0x1E8` | decomp 3523497 |
| Horizontal | `state + 0x83D` | `state + 0x32C` | decomp 3523503 |
| Diagonal | `state + 0x83E` | `state + 0x470` | decomp 3523509 |
| Diagonal 2 | `state + 0x83F` | `state + 0x5B4` | decomp 3523515 |
| Highlight | `state + 0x840` | `state + 0x6F8` | decomp 3523521 |

The destination spacing is `0x144` in every case, matching the checkout copy
size exactly. The complete setup sequence is at
`decomp/OLMKiraKira.aex.c.txt:3523420-3523530` and assembly offsets
`0x18114E860-0x18114EB05`.

## INFERENCE

- The opaque PF handle maps to ramp bytes through host checkout, not by using
  the numeric handle as an array index:

  `PF parameter handle -> PF Handle Suite checkout -> host ramp object -> object + 0x10 -> 0x144-byte state block`.

- The five blocks are intended as the render-side ramp inputs because they are
  copied into fixed state slots immediately before the 8/16/32-bit render
  dispatches (`FUN_18114d220`, `FUN_18114cc50`, and `FUN_18114d7f0`).

- A color lookup likely occurs downstream from these blocks during ray
  rendering, but the inspected static evidence does not identify a single
  direct `opaque_handle -> RGBA` routine. The visible `FUN_18114ca70` path only
  gates color parameters and use-ramp controls; it does not flatten ramp data.

## EXPLICIT BLOCKERS

1. The host ramp object's internal field semantics are not labeled in the
   plugin binary. Only the exact `0x144` byte ranges are proven.
2. No distinct plugin flatten/unflatten callback body was recovered. The
   visible `RampDataHandler` vtable entries are handle lifetime operations;
   serialization ownership appears to remain in the host/parameter layer.
3. No static callsite conclusively maps an individual ray scalar or arbitrary
   handle to one RGBA lookup result. Recovering that requires a bounded render
   trace or host ramp-object witness with payload bytes and the consuming
   state address.
4. The default registration bit patterns prove plugin-side arguments only;
   they do not prove the host's expanded default stop positions, colors,
   interpolation mode, or premultiplication convention.

## Non-claims

This audit does not revisit the already-known PF_ADD_ARBITRARY/custom-UI
conclusion and does not authorize changes to the Mac ramp surface or render
path.
