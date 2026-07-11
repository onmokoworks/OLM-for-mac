# OLMDistanceGradation 0010/0011 field-world pack/read return intake

Date: 2026-07-09

Return:
`refs/returns/windows/20260709_distancegradation_0010_0011_field_world_pack_read_partial/20260709_230618__olmdistancegradation_0010_0011_field_world_pack_read_partial_windows.zip`

Request:
`olmdistancegradation_0010_0011_field_world_pack_read_witness_20260709`

Status: `partial_success_fieldread_boundary_not_pack`

## Classification

This return is decision-useful but not full acceptance. It reaches the final
writer/read boundary and captures the read-side candidate pointer in `rdx`,
but it does not yet bind the upstream field-world pack routine or the direct
field float before storage.

Do not classify this as proof for a Mac implementation change.

## Accepted facts

The return reuses the previously accepted output pointer map:

- PF16 output pointer formula: `out = base + y * 0x3c00 + x * 8`
- pixel size: `8`
- `(6,40)` output offset: `0x96030`
- `(901,394)` output offset: `0x5c7428`

New same-run evidence from
`distancegradation_target_pf16_watch_fieldread_20260709_case0010/cdb_console.txt`:

- module/output base: `000001868d970100`
- boundary instruction: `DistanceGradation+0x1170814`
- observed relation in this retained run: `rdx = rdi - 0xfe0000`

For `(6,40)`:

- `rdi` destination: `000001868da06130`
- `rdx` read-side candidate: `000001868ca26130`
- `dst_words`: `733c 8000 733c 733c 72a7 72a7 72a7 72a7`
- `rdx_src_words`: `0000 0000 0000 0000 0000 0000 0000 0000`
- `xmm2_alpha`: `0.0997314`
- `xmm6`: `3268`
- previous final PF16 words: `0cc4 8000 0000 0000`

For `(901,394)`:

- `rdi` destination: `000001868df37528`
- `rdx` read-side candidate: `000001868cf57528`
- `dst_words`: `596c 8000 596c 596c 5a2e 5a2e 5a2e 5a2e`
- `rdx_src_words`: `8000 8000 0000 0000 8000 8000 0000 0000`
- `xmm2_alpha`: `0.301392`
- `xmm6`: `9876`
- previous final PF16 words: `2694 8000 0000 0000`

The read-side candidate buffer is therefore not a PNG/export artifact. It is a
live buffer consumed immediately before the final PF16 write boundary.

## Static correction

A static read of `FUN_181170480` after this intake shows that the late `rdx`
value captured at `DistanceGradation+0x1170814` is the source/shade pixel
pointer derived from `param_1[0]`, not the field-world pointer. The field-world
pointer is built earlier in `RCX` from `param_1[1]` and read at
`DistanceGradation+0x117057d`.

The captured `rdx_src_words` remain useful source/shade evidence, but they must
not be treated as the direct field-world pack/read value. The corrected next
ask is
`refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_contract_20260709.md`.

## Missing for full acceptance

- direct field float before storage
- direct field-world stored word/read value before invert
- raw distance / clamp / denominator
- producer instruction or function that writes the `rdx` read-side buffer
- true16 TIFF/EXR export sample, if export binding remains necessary

## Next allowed action

Generate a corrected compose-input witness that records the `RCX` field-world
read at `DistanceGradation+0x117057d` and the `RDX` source/shade read at
`DistanceGradation+0x11705f1` for the same target pixels. If feasible, data-watch
the `RCX` field-world address backwards to the producer/pack site.

## Forbidden actions

- Do not resend `olmdistancegradation_0010_0011_field_world_pack_read_witness_20260709` unchanged.
- Do not send the misclassified `rdx producer` request unchanged.
- Do not retune Mac final PF16 rounding from this return.
- Do not accept final PNG/display bytes or package-local recomputation as proof.
