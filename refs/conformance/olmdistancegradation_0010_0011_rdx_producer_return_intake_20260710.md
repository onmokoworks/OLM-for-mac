# OLMDistanceGradation 0010/0011 rdx producer return intake

Date: 2026-07-10

Return:
`refs/returns/windows/20260710_distancegradation_0010_0011_rdx_producer_partial/20260710_000306__olmdistancegradation_0010_0011_rdx_producer_packsite_partial_windows.zip`

Request:
`olmdistancegradation_0010_0011_rdx_producer_packsite_witness_20260709`

Status: `partial_watch_miss_prepopulated_rdx`

## Classification

This return is not full acceptance and does not identify the producer
instruction/function. It is still useful negative evidence: both watched `rdx`
addresses were already populated before the first captured
`DistanceGradation+0x1170480` callback.

Static asm then corrects the request interpretation: the late `rdx` pointer is
source/shade input from `param_1[0]`, not the field-world pointer. Field-world
must be observed earlier through `RCX` at `DistanceGradation+0x117057d`.

## Facts from the return

Live run:
`distancegradation_rdx_producer_watch_20260709_case0010/cdb_console.txt`

- `out_base`: `000001e28e0b0100`
- relation used in the run: `rdx = rdi - 0xfe0000`

For `(6,40)`:

- `rdi`: `000001e28e146130`
- `rdx`: `000001e28d166130`
- pre-watch words: `0000 0000 0000 0000 0000 0000 0000 0000`
- watch: `ba w 8 000001e28d166130`
- watch hit: `false`

For `(901,394)`:

- `rdi`: `000001e28e677528`
- `rdx`: `000001e28d697528`
- pre-watch words: `8000 8000 0000 0000 8000 8000 0000 0000`
- watch: `ba w 8 000001e28d697528`
- watch hit: `false`

Conclusion from the return:

- both target `rdx` locations were already populated at the first captured
  `DistanceGradation+0x1170480` `(x=0,y=0)` callback;
- a later callback-level data watch cannot catch the producer;
- producer search must move earlier than the callback or bind the callback's
  actual compose inputs instead.

## Corrected next action

Use
`refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_contract_20260709.md`.

That corrected request binds:

- `RCX` field-world words at `DistanceGradation+0x117057d`
- `RDX` source/shade words at `DistanceGradation+0x11705f1`
- final writer scalars at `DistanceGradation+0x1170808..0x1170824`

## Forbidden actions

- Do not resend the `rdx producer` request unchanged.
- Do not treat late `rdx` words as field-world proof.
- Do not retune Mac final rounding from this return.
