# OLMDistanceGradation 0010/0011 Writeback Follow Return Intake

Date: 2026-07-09

Return archive:
`refs/returns/windows/20260709_distancegradation_0010_0011_writeback_follow_failed_partial/20260709_203732__olmdistancegradation_0010_0011_writeback_follow_witness_failed_partial_windows.zip`

Request id:
`olmdistancegradation_0010_0011_writeback_follow_witness_20260709`

## Classification

`failed_partial`, not implementation proof.

This return is a useful debugger-path proof. It does not yet bind the contract
pixels `(6,40)` and `(901,394)`.

## Useful Facts

- Symbol-free frozen stepping reached `DistanceGradation+0x117051c`.
- The same run continued into `PF!PF_Interleave1to4<float>+0x1585..+0x15a9`.
- PF interleave symbols resolve via `x PF!*Interleave*`.
- CDB expressions using the decorated
  `PF!PF_Interleave1to4<float>` name remain fragile in `bu` / `.if`.
- A retained PF interleave witness at `WBSTEP 410` reports:
  - `rip=00007ff89c7559f5` (`PF!PF_Interleave1to4<float>+0x1585`)
  - `rdi=0000021b8e6fbda8`
  - `rdx=0000021b8cdfbda0`
  - `r8=000000000034bc00`
  - `r9=0000000000000014`
  - `words_rdi=3b4a 3b4a 3b4a 3b4a 3b9f 3b9f 3b9f 3b9f`
  - `words_rdx=0000 0000 0000 0000 0000 0000 0000 0000`
  - `xmm0=[0,0,0,32768]`
  - `xmm1=[0,0,0,32768]`
  - `xmm2_alpha=0.538361`
  - `xmm3=[0,0,0,0]`

## Missing Required Evidence

- contract pixel `(6,40)` same-run binding;
- contract pixel `(901,394)` same-run binding;
- typed source/field/out_a/pre-store/PF16/export chain for those pixels;
- true16 TIFF/EXR sample tied to the same witness.

## Next Retry Shape

Do not retry the same package unchanged.

The next proof must add output pointer / stride / pixel-address mapping before
following PF writeback. Use symbol-free step logging, `bm PF!*Interleave1to4*`,
or resolved numeric PF addresses; avoid decorated CDB `PF!PF_Interleave1to4<float>`
expressions in `.if` / `bu` conditions.

Minimum useful next result:

- derive the output base pointer, rowbytes/stride, pixel size, and exact expected
  addresses for `(6,40)` and `(901,394)`;
- data-watch or conditionally log only those target output/PF16 addresses;
- capture the same-run PF interleave/writeback values and final export for both
  target pixels.

