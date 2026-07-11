# OLMBlur Full-Worker Branch Map

Date: 2026-07-11

## Dispatch proof

The actual AEX dispatch is `FUN_18000a380`, not a helper-name inference.
`FUN_180009b40` reads effect properties in indices `1..5` and stores the
worker parameter block as follows:

| Worker offset | Property | Mac disk id | Meaning |
| --- | --- | ---: | --- |
| `+0x20` | 1 | 5 | Blur Amount |
| `+0x24` | 2 | 6 | Blur Smoothness |
| `+0x28` | 3 | 3 | Number of Repeat |
| `+0x2c` | 4 | 4 | Bias Direction |
| `+0x30` | 5 | 7 | Legacy checkbox |

The same mapping is present in the existing parameter definitions and
reference manifests: `mac/OLMBlur/OLMBlur.h`,
`refs/reference_requests/olm_bitdepth_16bpc_normalized_exact_20260625.json`,
and the OLMBlur reference manifests.

`FUN_18000a380` then dispatches by world depth and the byte at `+0x30`:

| World depth | Legacy `+0x30 == 1` | Non-Legacy `+0x30 == 0` |
| ---: | --- | --- |
| 8 | `FUN_180007300` -> `FUN_1800014f0` / `FUN_180001ea0` | `FUN_180003710` -> `FUN_180001000` / `FUN_180001980` |
| 16 | `FUN_180005f20` -> `FUN_1800014f0` / `FUN_180001ea0` | `FUN_180002280` -> `FUN_180001000` / `FUN_180001980` |
| 32 | `FUN_1800086d0` -> `FUN_1800014f0` / `FUN_180001ea0` | `FUN_180004b80` -> `FUN_180001000` / `FUN_180001980` |

The dispatch conditions are visible at:

- `disasm/OLMBlur.aex.asm.txt:18000a4f8-18000a506` for 8bpc;
- `disasm/OLMBlur.aex.asm.txt:18000a600-18000a60e` for 16bpc;
- `disasm/OLMBlur.aex.asm.txt:18000a705-18000a713` for 32bpc.

Therefore `0x14f0/0x1ea0` are precisely the Legacy family, and
`0x1000/0x1980` are precisely the Non-Legacy family for this AEX. This is a
dispatch fact, not a naming assumption.

## Bias Direction

Every worker family tests `param+0x2c`:

- value `1` (`BIAS_DIR_VERTICAL` in the Mac header): horizontal helper calls
  first, then vertical helper calls;
- value `2` (`BIAS_DIR_HORIZONTAL`): vertical helper calls first, then
  horizontal helper calls.

For `FUN_180005f20` specifically, the mode-1 call block is
`0x18000662d..0x180006878`: six `0x14f0` calls followed by six `0x1ea0`
calls. The mode-2 block is `0x18000690d..0x180006b58`: six `0x1ea0` calls
followed by six `0x14f0` calls. The same ordering is duplicated by the 8bpc
and 32bpc Legacy workers.

## Mac comparison

The current Mac logical ordering matches this Bias Direction mapping:

- `legacy_blur_1d_horizontal` then `legacy_blur_1d_vertical` for bias `1`;
- `legacy_blur_1d_vertical` then `legacy_blur_1d_horizontal` for bias `2`.

The literal ABI does **not** match. The AEX helper ABI is
`flags, srcRGB, dstRGB, weights, width, height/packed-width, columns, rows,
offset, radius`, with the first four arguments in `RCX/RDX/R8/R9` and the
remaining arguments on the Windows x64 stack. The Mac functions take
`srcRGB, srcA, dstRGB, dstA, w, h, radius, kernel, debug, iter` and process
the complete plane. They are therefore semantically ordered counterparts,
not drop-in ABI equivalents; the AEX's six subpass offsets and plane swaps
are not represented by the current Mac call signature.

## Decision

Before any Mac integration, preserve the separate families exactly as above:
the existing portable `0x1000/0x1980` core is Non-Legacy evidence, while the
new `0x14f0/0x1ea0` candidate is Legacy evidence. No Mac source, ledger, or
reference files were edited.
