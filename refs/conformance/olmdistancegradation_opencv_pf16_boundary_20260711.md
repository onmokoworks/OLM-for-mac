# OLMDistanceGradation OpenCV/PF16 Boundary

Date: 2026-07-11

## Verdict

The 16bpc sparse `case_0010/0011` family is closed for the current Mac plug-in.
The missing operation was the Windows field-world boundary, not the final
compose writer:

1. OpenCV `NORM_MINMAX` applies one float32 reciprocal scale and multiplies the
   field values.
2. OpenCV then converts the normalized float field to the PF16 world with
   round-to-nearest-even.
3. `FUN_181170480` reads those PF16 words back for compose.

After reproducing that boundary, the canonical 16bpc extended batch improves
from `5/16` to `7/16 AE exact`; `case_0010` and `case_0011` are the two newly
exact cases. This does not complete the plug-in.

The same investigation also corrected a stale 8bpc claim. A fresh canonical
Mac AE run at an explicitly forced project depth is `0/29` exact for the
current plug-in. The historical `29/29` artifact has no loaded Mac plug-in
hash and is not current-binary conformance evidence.

## Binary-Grounded Boundary

### FACT

- Actual AEX `FUN_181174760` produces the representative normalized float
  values `22891.5`, `29500.5`, and `4408.5009765625` after scaling to the PF16
  range.
- The fieldgen path calls the OpenCV 4.5.5 normalize wrapper
  `FUN_18117ca50`, then converts the field world before the PF Iterate16
  callback `FUN_181170480` consumes it.
- OpenCV 4.5.5 `cv2.add(float32, zero, dtype=CV_16U)` converts the six focused
  half-boundary values to `[22892, 29500, 4409, 2, 2, 4]`. This is
  round-to-nearest-even, including opposite directions for the first two
  witnesses.
- Dividing each field value by `raw_max` is not float32-equivalent to OpenCV's
  single reciprocal-scale multiply. The one-ULP difference decides which side
  of the later PF16 half boundary is consumed.
- The portable core still replays the actual-AEX fieldgen and compose fixtures
  exactly after the change.

### Implementation

- `core/olmdistancegradation_fieldgen.cpp`
  - computes one float32 reciprocal scale and multiplies each field value;
  - provides deterministic PF16 round-to-nearest-even pack/roundtrip helpers.
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
  - roundtrips `df.x` and `df.d_alpha` through the PF16 field-world boundary
    only for `PF_Pixel16` renders;
  - leaves the 8bpc and float field-world boundary unchanged.
- `tools/emulation/test_dg_core_distance_stage.cpp`
  - locks the six focused PF16 conversion witnesses.

## 16bpc Mac AE Result

Installed binary SHA-256:
`c4949d03ce7e74fef3d1f34b7346dcb880b3d8849bf210a0aeba0d6d77a7defb`.

| Case | Max diff | Nonzero pixels | Status |
| --- | ---: | ---: | --- |
| `case_0008` | 0 | 0 | `AE exact` |
| `case_0010` | 0 | 0 | `AE exact` (new) |
| `case_0011` | 0 | 0 | `AE exact` (new) |
| `case_0012` | 2 | 2,793 | known-red |
| `case_0013` | 2 | 10,135 | known-red |
| `case_0014` | 4 | 10,664 | known-red |
| `case_0016` | 2 | 5,373 | known-red |
| `case_0020` | 0 | 0 | `AE exact` |
| `case_0021` | 0 | 0 | `AE exact` |
| `case_0022` | 0 | 0 | `AE exact` |
| `case_0023` | 0 | 0 | `AE exact` |
| `case_0024` | 2 | 991,667 | known-red |
| `case_0025` | 2 | 808,516 | known-red |
| `case_0026` | 2 | 819,532 | known-red |
| `case_0027` | 2 | 505,602 | known-red |
| `case_0028` | 3,080 | 461,476 | known-red |

Compared with the prior canonical `5/16` batch, the exact set only grows; the
previous five exact cases remain exact. The `case_0024..0027` maximum falls to
`2`, but those cases remain non-exact and are not promoted.

## 8bpc Current-Binary Correction

The old reference manifests store depth in `comp.bpc`, while the AE runners
only read `project.bits_per_channel`. Because AE retains project depth between
runs, the first attempted regression rendered 16bpc candidates and was
invalid. Both batch and single-case JSX runners now use
`project.bits_per_channel`, falling back to `comp.bpc`.

The corrected batch log records `bits_per_channel 8 source=comp.bpc` for all
three request groups, and the rendered files are 8-bit RGBA PNGs. The current
binary measures:

| Group | Exact | Total | Worst max diff |
| --- | ---: | ---: | ---: |
| basic | 0 | 12 | 64 |
| extended | 0 | 16 | 254 |
| blur | 0 | 1 | 23 |

This is a current-binary `known-red` result, not a regression caused by the
new PF16 boundary. An A/B run against the immediately preceding binary
(`05667d61...`) produced byte-identical PNGs for 27 of 29 cases. Only
`case_0014` and `case_0015` changed, each at two pixels, six channel values,
and `max_diff=1`; both binaries remain `0/29` exact.

Two retained June 18 binaries were also checked:

- `4adb6d1d...`: `0/29` exact.
- `068a4a08...`: `0/29` exact and AE reports an internal Code/PiPL version
  mismatch despite both being displayed as 2.4.

That warning belongs to the retained `068a4a08...` A/B binary, not the
currently installed build. A post-restore bundle audit found:

- current `GlobalSetup` stores `0x120405` in `out_data->my_version`;
- the installed PiPL `eVER` payload is also `0x120405`;
- the installed bundle and the current Xcode Debug bundle are identical under
  `diff -qr`;
- the current binary SHA-256 is `c4949d03...`.

The A/B process must replace the complete `.plugin` bundle while AE is closed.
Replacing only `Contents/MacOS/OLMDistanceGradation` can combine a retained
binary with another bundle's PiPL and is no longer an accepted host-validation
procedure.

A fresh AE 26.3 host run then loaded the restored current bundle without the
warning and rendered both canonical 16bpc `case_0023` variants. Background on
and background off each compared `max_diff=0` against the Windows Software
reference (`2/2 AE exact`). This closes the host-version warning for the
current bundle; it does not change the plug-in-wide conformance count.

The historical exact candidate images still match the canonical Windows
references, but no result metadata binds them to a loaded Mac plug-in path or
SHA-256. Keep them as historical artifacts; do not use them to claim current
8bpc `AE exact`.

## Focused Verification

```text
python3 refs/scripts/smoke_dg_cpu_fixture.py
  DG core distance stage: PASS (286 values)
  portable fieldgen: exact (748 bytes)
  portable compose: exact (24 bytes)

python3 refs/scripts/smoke_dg_case0023_cpu_fixture.py
  full-frame inside/outside fieldgen: exact (8,294,400 bytes each)
  compose words: 0,32768,32768

tools/emulation/.venv-cv455/bin/python <focused cv2 conversion probe>
  cv2 4.5.5
  [22892, 29500, 4409, 2, 2, 4]
```

## Remaining Boundary

- `case_0012/0013/0014/0016`: Layer/no-background source/export family.
- `case_0024..0027`: broad max-2 field/export family.
- `case_0028`: separate large residual; do not merge it into the max-2 family.
- 8bpc: current implementation is known-red and must be repaired from
  binary-grounded field/compose rules. The unbound historical `29/29` output
  is not an implementation oracle.
