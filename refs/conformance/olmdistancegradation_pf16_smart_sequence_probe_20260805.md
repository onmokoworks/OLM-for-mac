# OLMDistanceGradation PF16 Smart outer sequence probe

`FUN_1811741a0` now executes naturally through the outer sequence setup and returns zero after a focused gate at render owner `FUN_1811743b0`.

Observed suite order and ABI:

1. `AEGP PF Interface Suite` v1, callback `+0x00`, returns the sequence object through RDX.
2. `AEGP Layer Suite` v11, callback `+0x70`, returns pre-render/layer state through R8.
3. PF Interface callback `+0x08`, returns the retained pre-render handle through R8.
4. `AEGP Effect Suite` v3, callback `+0x40`, closes the setup lifetime before render.
5. The same `PF_InData` pointer reaches `FUN_1811743b0`.

The sequence and pre-render objects are distinct mapped 0x100-byte allocations; their full raw bytes are retained at the gate. The owner returns in 434 instructions with EAX zero.

With `OLM_DG_SMART_RENDER=1`, the owner is no longer gated. It performs the
parameter checkout/checkin sequence for slots `9, 10, 2, 4, 3, 5, 6, 7, 8,
11, 12`, including `PF Param Utils Suite` v3 for the relevant parameters, and
returns zero naturally in 4,621 instructions.

This also corrected an important boundary assumption: `FUN_1811743b0` is the
Smart pre-render parameter owner. It does not call the typed renderer.
`entryPointFunc` command `0xe` invokes the pre-render sequence, while command
`0xb` independently tests request byte `+0x10` bit 0 and dispatches PF16 to
`FUN_181170280`. With `OLM_DG_SMART_DISPATCH=1`, a second command `0xb` call on
the same mapped host state reaches `FUN_181170280` naturally in 56 instructions
and returns zero through a focused wrapper gate. The probe does not call the
wrapper directly.

The wrapper gate is not final Smart conformance. Result/max rectangles,
retained pre-render data, checked-out PF16 input/output worlds, row padding,
and independently captured final bytes remain the next stage. No classic PF16
output is used as a Smart oracle.

The gate has subsequently been released. The same-state `0xe` then `0xb`
execution acquires `PF iterate16 Suite` v1 and invokes the actual
`FUN_181170480` callback for all 187 pixels of a 17x11 frame. The observed
iterate ABI is: callback-entry stack `+0x30` = temporary refcon,
`+0x38` = typed callback, and `+0x40` = destination world. The refcon contains
`[source=params[0], destination]`.

Input and destination rowbytes are deliberately distinct (`146` and `150`),
with active row width `136`. All input and destination padding bytes retain
the `0xA5` sentinel. The independently captured active output SHA-256 is
`40033c11b790b2b93832553dc9e422b5bd6293f2965bf593df4b0f14c58c252f`.
Across all 187 pixels the actual callback contract is exactly
`out.A = source.A` and `out.G/R/B = staged_destination.G`.

Production implements this only in the PF16 Smart boundary through
`RenderSmartPF16PreseededField`; classic `RenderBits` is unchanged. The
production comparison covers all 1,650 destination bytes, including padding,
with zero mismatches. Classic PF16 remains exact for 748 typed words and both
controlled PF32 classic captures remain exact for 2,992 bytes each.
