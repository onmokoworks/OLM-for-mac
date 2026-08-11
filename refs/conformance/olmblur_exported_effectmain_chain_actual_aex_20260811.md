# OLMBlur exported EffectMain render chain

- Status: `exact`
- Binary: actual Windows 2025 `OLMBlur.aex`, SHA-256
  `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`
- Matrix: PF8/PF16/PF32 × Legacy off/on
- Geometry: `24×24`; row padding is `17/23/32` bytes respectively
- Parameters: Amount `5`, Smoothness `100`, Repeat `1`, Bias Direction `1`

All six rows now execute the actual exported `entryPointFunc` at `0x18000a970`:

1. `PF_Cmd_SMART_PRE_RENDER` (`23`)
2. input-layer pre-render checkout
3. `PF_Cmd_SMART_RENDER` (`24`)
4. input pixels and output checkout
5. parameter checkout/checkin in order `1,2,3,4,5`
6. the depth/Legacy worker selected by the export
7. typed output writer

Every active output byte equals the existing hash-pinned actual-worker oracle.
The export's initial copy changes output padding from its `0xEE` sentinel to the
source padding sentinel `0xA5`; no later worker or writer modifies it.  Thus the
test distinguishes the public copy stage from an out-of-row write.

The smart entry dispatches all three tested depths, so no row in this bounded
matrix selects the classic `PF_Cmd_RENDER` fallback.  This does not claim that a
different AE host configuration cannot choose the classic command.

This is an AE-free AEXCompat/Unicorn execution of the actual Windows export
with bounded synthetic host suites.  It proves command and suite plumbing for
these six rows, not native After Effects host behavior or other parameter and
geometry ranges.  No production source change was needed.

```sh
python3 tools/emulation/test_olmblur_exported_effectmain_chain_actual_aex_20260811.py
```
