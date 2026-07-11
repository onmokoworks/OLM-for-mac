# OLMDistanceGradation 0010/0011 Writeback Pointer Map Contract

Date: 2026-07-09

Request id:
`olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709`

## Purpose

This is the narrowed successor to
`olmdistancegradation_0010_0011_writeback_follow_witness_20260709`.

The previous return reached `DistanceGradation+0x117051c` and continued into
`PF!PF_Interleave1to4<float>+0x1585..+0x15a9`, retaining PF interleave registers
and words. It still failed to bind those writes to the contract pixels `(6,40)`
and `(901,394)`.

This request asks for the missing output pointer / stride / pixel-address map.
Do not repeat broad stepping without address binding.

## Required Case Path

Use the exact 16bpc Software request:

`handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/`

Primary case:

- `olmdistancegradation_extended__case_0010`

Target pixels:

- `(6,40)` where Mac store is one word lower than Windows-implied store.
- `(901,394)` where Mac store is one word higher than Windows-implied store.

Optional control:

- `olmdistancegradation_extended__case_0011` at `(915,392)`.

## Required Mapping Facts

Before following PF writeback, derive and return:

- output world base pointer used by the final writeback;
- output rowbytes / stride;
- pixel size / channel layout for the final PF16 store;
- exact calculated output addresses for `(6,40)` and `(901,394)`;
- whether the previously observed `out_arg5=...bd00` and `rdi=...bda8` style
  pointers are header-relative, row-relative, pixel-relative, or a PF scratch
  buffer;
- how `rdi`, `rdx`, `r8`, and `r9` in `PF!PF_Interleave1to4<float>` map to
  source, destination, count/stride, and channels.

## Capture Strategy

Use symbol-free or numeric-address logging:

- `x PF!*Interleave*` is known to resolve symbols.
- Decorated `PF!PF_Interleave1to4<float>` is fragile inside CDB `bu` / `.if`.
- Prefer `bm PF!*Interleave1to4*`, numeric resolved addresses, or compact
  symbol-free logging followed by `ln @rip` postprocessing.

Once target addresses are computed:

- data-watch the exact PF16 output words for `(6,40)` and `(901,394)`, or
  conditionally log PF interleave/writeback only when `rdi/rdx` span covers the
  target addresses;
- capture pre-store float RGBA, PF16 words after writeback, and same-run
  true16 TIFF/EXR export for those pixels.

## Acceptance Rule

Satisfactory:

- the output pointer map is explicit; and
- both primary target addresses are bound; and
- both pixels have same-run pre-store / PF16 store / export evidence.

Partial:

- one primary target address is bound and fully typed; or
- the output pointer map is explicit but the target watchpoint still fails, with
  the exact address/register reason preserved.

Failed:

- broad PF interleave hits without output address mapping;
- PNG/display bytes only;
- package-local recomputation or Windows-implied store words;
- another decorated-symbol CDB expression failure without numeric fallback.

