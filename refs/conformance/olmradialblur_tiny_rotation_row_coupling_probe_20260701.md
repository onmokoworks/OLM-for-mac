# OLMRadialBlur tiny Rotation Row-Coupling Probe

Date: 2026-07-01

Goal:

- Re-run the best current tiny-Rotation row-coupled diagnostics and check whether they
  actually restore the missing bright lobe near the witness `(1614,6)`, not just the
  global `mean_diff`.

Reference bright lobe:

- bright count (`R >= 200` in `25x25` window): `17`
- center of mass: `[1611.7058823529412, 2.7058823529411766]`
- witness RGBA: `[255, 255, 255, 255]`
- witness patch R (rows `y-2..y`, cols `x-2..x`): `[[251, 247, 253], [4, 253, 251], [5, 1, 255]]`

## Variants

| Variant | mean_diff | bright_count | witness_rgba | patch_r |
| - | -: | -: | - | - |
| `baseline` | `0.010320337` | `0` | `[0, 0, 0, 255]` | `[[0, 0, 0], [4, 0, 0], [5, 1, 0]]` |
| `prev2-k2-positive scale=0.0025` | `0.010719039` | `0` | `[0, 0, 0, 255]` | `[[0, 0, 0], [4, 0, 0], [5, 1, 0]]` |
| `prev2-row-tail-positive scale=0.005` | `0.012562572` | `0` | `[0, 0, 0, 255]` | `[[0, 0, 0], [4, 0, 0], [5, 1, 0]]` |

## Interpretation

The tested row-coupled diagnostics still do not recreate the missing bright lobe near the tiny Rotation witness. They can move global mean_diff, but the local 25x25 bright-pixel count remains zero and the witness stays black.

The useful clue remains structural and diagnostic only: a sparse cross-row positive family may exist upstream, but these current row-coupled surrogates are not close enough to promote into the port.

- `prev2-k2-positive` still leaves the witness patch identical to baseline
  (`[[0,0,0],[4,0,0],[5,1,0]]`) and does not produce any nearby `R >= 200` pixels.
- `prev2-row-tail-positive` worsens `mean_diff` further and also leaves the local
  bright-pixel count at zero.
- So the earlier row-coupling hints are still useful as a qualitative clue about an
  upstream positive family, but they are not a close numeric stand-in for the AEX
  bright-lobe path.
