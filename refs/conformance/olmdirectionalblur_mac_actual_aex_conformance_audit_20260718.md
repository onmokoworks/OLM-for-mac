# OLMDirectionalBlur Mac vs bounded actual-AEX audit

Date: 2026-07-18
Scope: `OLMDirectionalBlur` only. Production source and ledger unchanged.

## Verdict

`bounded-8bpc-front-only-pass; modes-2/3-and-full-frame-unresolved`

No evidence-backed production patch is justified. The current Mac source is
exact only on the narrow front-only 8bpc seam exercised by the bounded
actual-AEX differential. The broader controls and depth paths remain
fail-closed.

## Audit

| Surface | Current Mac source | Evidence / result |
| --- | --- | --- |
| Host parameter binding | `InfoFromParams` reads the checked-out controls at `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:494-514`; `SmartRender` checks out params `1..NUM_PARAMS-1` at `:607-631`. | The exact-path Mac host-adapter probe passes its full/partial ROI cases and rejects unsupported gates. No binding defect is proven for the front-only lane. The natural AEX path still needs a same-run parameter-to-worker witness. |
| Modes 2/3 | `OLMDirectionalBlurInfo` has no mode-specific host buffers/state; `core/dblur_rowdriver.cpp:167-171` returns immediately for modes 2 and 3. | Actual AEX mode-2 setup is in `FUN_180004A20`, `FUN_180003C90`, and `FUN_1800057B0`; each branch requests host sampling (`PF callback selector 0x11`) and populates the auxiliary plane. Mode 3 dispatches `FUN_1800034E0` for the noise texture. These are not represented in the Mac port. |
| Front alpha writer | `RenderExactFrontOnly8` copies the core RGBA result into PF pixels at `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:410-427`. | Actual AEX output callback is `LAB_180006B30`; bounded evidence confirms PF8 A/R/G/B store order and nonzero writer samples. The bounded direct writer agrees with the portable truncating writer, but the known Windows witness still differs at 226 focused pixels. This is not an evidence-backed writer fix. |
| Full-frame bridge | `RenderWorld` dispatches the proven 8bpc seam and copy-throughs 16/32bpc at `:456-473`; Smart PreRender unions checkout rectangles at `:571-592`. | Bounded angle/rowdriver/helper/host checks pass, but natural full-render scheduling is not bound to `FUN_1800038D0`. The remaining bridge is the real worker continuation from `FUN_180006980` populate through rowdriver, normalization, rotate-back, and `FUN_180006B30`. |
| 16/32bpc | `RenderWorld` copy-throughs `PF_Pixel16` and `PF_PixelFloat`. | Existing 16bpc evidence contains no DirectionalBlur exact rows. Existing 32bpc returns are mixed variation/fade/tail/back/noise Windows references only, so implementing these paths from them would be speculative. |

## Exact unresolved boundaries

- `FUN_180006980` (`0x180006980`): actual populate callback is reached in the
  natural 26x26 checkpoint, but the continuation after its captured
  `params+0x8078` write is not yet proven.
- `FUN_1800038D0` (`0x1800038D0`): bounded ABI and helper calls are exact, but
  natural worker scheduling and its real rowdriver arguments remain unresolved.
- `FUN_180005554` (`0x180005554`): full-frame normalization entry is not
  reached by an accepted natural continuation witness.
- `LAB_180006B30` (`0x180006B30`): bounded PF8 writer contract is proven, but
  complete same-run output-frame ownership is not.
- Mode 2 auxiliary-plane setup in the depth-specific renderers
  (`FUN_180004A20 @ 0x180004A20`, `FUN_180003C90 @ 0x180003C90`,
  `FUN_1800057B0 @ 0x1800057B0`) and mode-3 texture generation
  (`FUN_1800034E0 @ 0x1800034E0`) have no Mac implementation or accepted
  callback evidence.

## Evidence used

- `refs/conformance/olmdirectionalblur_fullframe_readiness_20260718.json`:
  bounded readiness passes; natural full-frame readiness is blocked.
- `refs/conformance/olmdirectionalblur_rowdriver_binding_20260718.json`:
  bounded rowdriver/helper ABI passes; natural worker dispatch is unresolved.
- `refs/conformance/olmdirectionalblur_final_pf_output_contract_20260718.json`:
  actual `0x180006980 -> 0x180006B30` bounded callback/writer contract passes,
  without a full-frame equivalence claim.
- `refs/conformance/olmdirectionalblur_32bpc_float_evidence_audit_20260715.md`:
  16bpc has no DirectionalBlur exact rows; 32bpc is reference-only.
- `refs/conformance/dblur_alpha_fade_witness_row_20260712.md`:
  bounded destination/denominator/alpha/normalization exactness passes, while
  the writer differs from the Windows PF output.

## Reproduction

```sh
python3 tools/emulation/audit_olmdirectionalblur_fullframe_readiness_20260718.py
python3 tools/emulation/test_olmdirectionalblur_final_pf_output_contract_20260718.py
python3 tests/refs/conformance/test_binary_contracts.py
```
