# OLMBlur non-default Smoothness public EffectMain seam — 2026-08-10

## Result

Mac-local focused regression passes for representative PF8, PF16, and PF32
Legacy cases. In every case, the production public `EffectMain` Smart Render
path checks out parameters in order `1,2,3,4,5`, observes the exact 16.16
fixed-point `Blur Smoothness` word, dispatches the typed Legacy renderer, and
matches the retained Windows AEX worker output byte-for-byte. Row padding is
also exact.

| Depth | Smoothness | Fixed word | Actual-AEX output SHA-256 |
| --- | ---: | ---: | --- |
| PF8 | 43.75 | 2867200 | `67037ca39d5ffad4a2ae21a1a846cab4778c6c064c5b2e0ee355db62756ebfdf` |
| PF16 | 62.5 | 4096000 | `7ac117f2430da7a8d132c1f5318b89218cefa0601100173a99294b1ea175b305` |
| PF32 | 37.5 | 2457600 | `a0b48d578a84dda09d4d71d0bb801a70ef0ed92c7f59f32b72ace8bb753ecf44` |

The pinned Windows AEX SHA-256 is
`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.

## Evidence boundary

The expected typed buffers come from the actual Windows AEX workers. The Mac
side executes production `EffectMain(PF_Cmd_SMART_PRE_RENDER)` followed by
`EffectMain(PF_Cmd_SMART_RENDER)` with synthetic AE suites. This closes the
previously missing Mac parameter-materialization-to-public-entry seam.

It does not execute the Windows AEX public Smart Render callback chain, prove
native AE control materialization/layout, or generalize beyond the listed
values and geometries.

## Reproduction

```sh
python3 tools/emulation/test_olmblur_nondefault_smoothness_effectmain_actual_aex_20260810.py
```
