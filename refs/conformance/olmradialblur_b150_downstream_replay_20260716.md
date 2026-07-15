# OLMRadialBlur B150 downstream replay proof

Date: 2026-07-16

## Scope

This is a bounded Mac-only actual-AEX/emulator proof for `case_0009`. It runs
the existing `FUN_18000B150` live/no-op differential on the reduced `32x32`
direct geometry, then replays the retained downstream sample cells with a
portable operation-by-operation float32 mirror. The mirror covers bilinear
weights, alpha-weighted accumulation, normalization by sampled alpha, and
truncate-to-u8 conversion. It does not render or tune PNG values.

## FACT

- Command:

  ```sh
  python3 tools/emulation/run_radialblur_case0009_b150_downstream_replay.py \
    --combined-json /tmp/olmradialblur_b150_downstream_20260716.json \
    --output-json /tmp/olmradialblur_b150_downstream_20260716.analysis.json \
    --output-md /tmp/olmradialblur_b150_downstream_20260716.analysis.md
  ```

- The live actual-AEX run reached and returned from B150 once. The paired
  no-op detour was hit once. Both used the same bounded `width=49`,
  `row_start=0`, `row_end=5` typed contract.
- The live B150-owned slice changed from `9` to `245` nonzero cells. The
  no-op slice remained at `9` nonzero cells.
- The live normalized plane contained `196` informative cells. The no-op
  normalized plane contained `0` informative cells.
- Live and no-op normalized-plane hashes differed for all four captured planes
  (`final`, `accum`, `denom`, and `valid`).
- The retained output samples at `(7,0)`, `(8,0)`, and `(24,0)` used the same
  AEX inverse-sampler coordinates and cell selections in the paired runs.
  Live samples were `[0,0,0,1]` with truncate-u8 `[0,0,0,255]`; no-op samples
  were `[0,0,0,0]` with truncate-u8 `[0,0,0,0]`.
- The portable replay matched the actual-AEX sample float32 words and
  truncate-u8 values at all `3/3` points for both live and no-op captures.
- Focused checks passed:

  ```text
  [OK] case0009 sampler/prepass/writeback analyzer invariants
  [OK] B150 downstream portable replay gate
  status=pass classification=b150-to-normalized-sampler-writeback-propagation-proven
  ```

## INFERENCE

- In this bounded scaffold, B150-owned changes are consumed by the downstream
  normalized polar planes and reach the inverse sampler and final byte
  conversion. This narrows `case_0009` away from a disconnected-B150 or
  generic final-u8-only explanation for this witness.
- The proof does not identify the full-frame residual cause, establish Mac/AE
  equivalence, or justify any production-code change.

## Limits

- Reduced local actual-AEX geometry only; the retained sample points are not a
  full-frame equivalence witness.
- No Windows execution or package was created or sent.
- No shared ledger was modified.
