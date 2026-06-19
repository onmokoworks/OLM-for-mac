# OLMSmoother2 Forecast Audit - 2026-06-19

This note records no-new-PNG progress for OLMSmoother2. It is deliberately
not a completion claim; the target remains Mac AE exact against Windows
Software render.

## Inputs

- Reference request: `smoother2_no_key_grid_20260606`
- Windows Software references: covered under `refs/win_references/`
- CLI binary rebuilt with `refs/scripts/build_olmsmoother2_cli.sh`
- Diagnostic output saved in
  `refs/reports/olmsmoother2_forecast_20260619_021900/`

## Commands

```sh
bash refs/scripts/build_olmsmoother2_cli.sh
python3 refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py \
  --cli-extra='--index-hist /tmp/olmsmoother2_index_hist.csv --idx18-key-hist /tmp/olmsmoother2_idx18_key_hist.csv' \
  --run-suffix hist
```

The `/tmp` CSVs were copied into the project report directory listed above.

Additional negative probes:

```sh
python3 refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py \
  --cli-extra='--skip-index 24' \
  --run-suffix skip_idx18
python3 refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py \
  --cli-extra='--idx18-mode skip-cardinal3' \
  --run-suffix skip_cardinal3
python3 refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py \
  --cli-extra='--idx18-mode skip-cardinal12' \
  --run-suffix skip_cardinal12
```

Their summaries were copied into the same report directory as
`skip_idx18_summary.csv`, `skip_cardinal3_summary.csv`, and
`skip_cardinal12_summary.csv`.

## Result

The grid remains guarded, not complete:

- `sm2_no_key_s000_r1/r2/r3`: exact.
- Smoothness `25`: `max=4`.
- Smoothness `50`: `max=8`.
- Smoothness `100`: `max=9`.
- Nonzero pixel percentages stay tiny but increase with Smooth Range:
  roughly `0.0027%` to `0.0137%`.

This pattern is consistent with a small geometry/coverage mismatch, not a
large frame setup or color-space error.

The negative probes are important:

- Skipping all `idx=0x18` worsens the grid to `max=15/16/22` and up to about
  `1.06%` nonzero pixels.
- Skipping either cardinal side of `idx=0x18` also worsens the grid to
  `max=15/16` and roughly `0.13%..0.54%` nonzero pixels.

So `idx=0x18` is not simply an over-fired branch to delete. The current
residual is more likely a small coverage/weight/scanner-detail mismatch within
hot leaves, or an interaction with neighboring hot classifier indices.

## Dispatch Hotspots

Top classifier indices from `index_hist.csv`:

| idx | count | note |
| --- | ---: | --- |
| `0xff` | 1866072 | fully stable/opaque region, likely not residual owner |
| `0x1f` | 24444 | edge context |
| `0xf8` | 24424 | edge context |
| `0x18` | 22908 | current suspected residual family |
| `0x00` | 19704 | full-corner smooth case |
| `0xd6` | 18820 | edge context |
| `0x6b` | 18744 | edge context |
| `0x42` | 17052 | edge context |

`idx=0x18` key histogram:

| cardinal | key | count | next read |
| --- | --- | ---: | --- |
| 12 | `0x29` | 11512 | `FUN_18000fbf0` case `0x29` |
| 3 | `0x21` | 11384 | `FUN_1800101e0` case `0x21` |
| 12 | `0x55` | 11376 | secondary |
| 3 | `0x4d` | 11376 | secondary |

Tiny counts also appear at cardinal 3 keys `0x14`, `0x1e`, `0x13`, `0x2b`
and cardinal 12 keys `0x2a`, `0x01`, `0x28`. These are lower priority unless
the hot paths prove exact.

## Binary-Grounded Read Order

1. Re-read `FUN_18000fbf0` for key `0x29` and verify the Mac leaf sequence,
   emitted directions, and weight post-processing.
2. Re-read `FUN_1800101e0` for key `0x21` with the same checks.
3. Verify the span denominator and `+1` rules in `win_leaf_ec40`,
   `win_leaf_e640`, `win_leaf_ef20`, and `win_leaf_e950`.
4. Confirm whether the corresponding leaves call any weight amplification in
   Windows for those keys.
5. Only then touch `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`.

Do not promote `--idx18-mode skip-cardinal3` or `skip-cardinal12`; those are
diagnostic probes and contradict the Windows dispatch when used as a fix.

## 2026-06-19 Follow-up: Max-Diff Pixel Traces

Added a diagnostic-only CLI hook:

```sh
cli/OLMSmoother2/olmsmoother2_cli ... --trace-pixel x,y
```

This does not change default output. It prints the `FUN_18000c280` switch
index, cell bits, emitted sample count, and first samples for one pixel.

Representative `sm2_no_key_s100_r3` max-diff coordinates:

| pixel | idx | emitted samples | observed issue |
| --- | ---: | --- | --- |
| `(211,139)` | `0x10` | two duplicate samples, weights `0.4` and `0.2` | candidate is weaker than Windows reference |
| `(731,139)` | `0x10` | two duplicate samples, weights `0.4` and `0.2` | candidate is weaker than Windows reference |
| `(991,139)` | `0x10` | two duplicate samples, weights `0.4` and `0.2` | candidate is weaker than Windows reference |
| `(215,145)` | `0x08` | two duplicate samples, weights `0.32` and `0.2` | candidate is weaker than Windows reference |
| `(995,145)` | `0x08` | two duplicate samples, weights `0.32` and `0.2` | candidate is weaker than Windows reference |

Important negative probes:

- Globally changing `W_IN_W` from `0.2` to `0.4` worsened the grid
  (`s100/r3 max=20`, `nz=392`), and did not affect the sampled max-diff
  coordinates. Therefore the hot `0.2` at these pixels is not the global
  corner-helper `W_IN_W` constant.
- `--skip-index 8` worsened the grid (`s100/r3 max=27`, `nz=480`).
- `--skip-index 16` worsened the grid (`s100/r3 max=41`, `nz=452`).

Interpretation:

- `idx=0x08` and `idx=0x10` are necessary branches, not over-firing branches.
- The remaining no-key grid residual is now more likely in the specific
  cardinal leaf path that emits the second `0.2` sample, or in the small
  span/endpoint weight formula for those indices.
- The next binary read should inspect the exact `FUN_18000c280` case bodies
  for `0x08` and `0x10`, then trace into the called cardinal dispatchers and
  leaf keys for these pixels.

## 2026-06-19 Follow-up: Static Leaf Recheck

Ghidra/decomp recheck of the hot `idx=0x08/0x10` path:

- `FUN_18000c280` sends both `idx=0x08` and `idx=0x10` through the same case
  body as `idx=0x18`: `FUN_180010820` (`cardinal3`) followed by
  `FUN_1800105f0` (`cardinal12`).
- For the traced `idx=0x10` pixels, `cardinal3` key `0x1e` maps to
  `FUN_18000f2c0` and then the `FUN_18000e950` tail. The Mac dispatcher has
  the same sequence.
- For the traced `idx=0x08` pixels, `cardinal3` key `0x14` maps to
  `FUN_18000f2c0`, boost-last, `FUN_18000f180`, boost-last. The Mac dispatcher
  has the same sequence, and the trace shows the first append boosted from
  `0.4` to `0.32000002`.
- For both, `cardinal12` key `0x29` maps to `FUN_18000ec40` and the
  `FUN_18000e640` tail. The Mac dispatcher has the same sequence.
- `FUN_1800104d0`, `FUN_18000c0d0`, `FUN_18000ab00`, `FUN_18000b120`, and
  `FUN_1800036e0` were rechecked against decomp and still match the current
  Mac structure at the algorithm level.

Current interpretation:

- The static read does not justify changing the dispatch order or deleting a
  branch.
- The next decisive evidence is a Windows runtime trace of the exact witness
  pixels, especially the `FUN_1800104d0` append sequence and the
  `FUN_18000ab00` / `FUN_1800036e0` values.
- A dedicated package can be generated with:

```sh
python3 scripts/package_runtime_trace_requests.py \
  --profile smoother2-no-key-grid \
  --output refs/runtime_trace_packages/olm_runtime_trace_olmsmoother2_no_key_grid_YYYYMMDD_HHMMSS.zip
```
