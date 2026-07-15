# OLMBlur residual-locus analysis 2026-07-15

- Verdict: `separate-lanes`
- Scope: `OLMBlur non-Legacy 16bpc case_0006`

## FACT

- Windows export is canonical/current-AEX byte identity.
- Mac single differs at exactly one exported pixel: (601,598), Windows [18,18,18,255] versus Mac [17,17,18,255].
- Historical typed witnesses are (314,14) and (29,71); the actual-AEX report does not localize a Windows internal difference.

## Export Evidence

| Artifact | SHA-256 |
| --- | --- |
| `windows_export` | `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f` |
| `mac_single_export` | `8990ef5b4cbf82b2d86e4a6014e4d8944eff24397aa97c1fb8ceafcc310a8787` |

| Coordinate | Windows | Mac single | Delta |
| --- | --- | --- | --- |
| `(601,598)` | `[18, 18, 18, 255]` | `[17, 17, 18, 255]` | `[1, 1, 0, 0]` |

## Host And Actual-AEX Gates

- Manifest contracts compatible: `True` (1920x1080, 16bpc, SOFTWARE, pixel aspect 1, resolution [1,1], same OLMBlur case parameters).
- Dated Windows return classification: accepted same-run export provenance=`True`, not OLMBlur worker trace=`True`.
- Actual-AEX typed replay self-check: `True`; first Windows internal difference: `Windows evidence is final PNG words only; no same-run Windows helper/pre-store values are present`.
- CDB attach used by this analysis: `False`.

## Coordinate/Provenance Decision

- Status: `not-proven`.
- The only declared host transform is identity; (601,598) is distinct from (314,14) and (29,71), and no artifact supplies a provenance transform or same-run OLMBlur internal trace.
- Therefore the current evidence supports `separate-lanes`: the exported residual lane is separate from the historical internal-witness lane. This does not identify the upstream cause of either lane.

## INFERENCE

- No coordinate/provenance mapping is proven by current artifacts.
- The export residual and historical internal witnesses must remain separate evidence lanes.
- No helper, kernel, or rounding conclusion follows from this image-level residual.

## Automated Tests

- `python3 refs/scripts/smoke_analyze_olmblur_residual_locus_20260715.py`
- The smoke test asserts exact Windows SHA-256, exact one-pixel residual and channel deltas, manifest geometry/parameter compatibility, actual-AEX limitation, no CDB flag, and fail-closed missing-artifact behavior.
