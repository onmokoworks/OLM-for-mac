# OLMDistanceGradation 0010 Compose Single-Site Follow-up Contract

Date: 2026-07-10

Request id:
`olmdistancegradation_0010_compose_single_site_followup_20260710`

## Purpose

The fresh `compose_exact_address_partial_windows` return established live
output/source row geometry, but its multi-breakpoint command script became
unstable after the entry witness and retained no downstream typed values. This
follow-up deliberately reduces each Windows invocation to one normalized
Software case, one target pixel, and one downstream site.

## 2026-07-10 Break-Ignore Retry

The first return reached the entry witness in both field and source runs, then
stopped on first-chance `0x80000003` before either downstream breakpoint could
be evaluated. The retry adds `sxi 80000003` and otherwise preserves the same
one-site shape. This is a debugger-control correction, not a new algorithm
hypothesis.

The current retry intentionally remains immutable while it is staged. There is
not yet a checked-in live log proving that CDB's debugger-set software `bp`
still stops under `sxi 80000003`. If the retry reaches module load but records
neither entry nor selected-site stops, classify that result as debugger-control
failure rather than algorithm evidence. The next and only allowed debugger
successor is the same one-site script with the entry and selected-site stops
changed to execute hardware breakpoints (`ba e 1`); do not add broader gates or
another PNG probe.

Do not use `rbp=y`, broad `r9=x`, broad PF interleave, PNG bytes, or a Mac
plugin. Do not run both target pixels in one invocation.

## Required Run Matrix

Primary case:
`olmdistancegradation_extended__case_0010`

Run each site separately for one target pixel. Start with `(6,40)`; repeat
the same commands for `(901,394)` only if the first pixel is stable.

- `field`: `DistanceGradation+0x117057d`
- `source`: `DistanceGradation+0x11705f1`
- `writer`: `DistanceGradation+0x1170814`

The field and source runs are the minimum useful proof. The writer run is
optional if the first two runs are stable.

## Static Address Relation

The local static disassembly at `DistanceGradation+0x1170480` shows:

- callback `EDX`/`R9` is the x argument and `R8D` is the y argument;
- field descriptor is `R10 = [RBX+0x8]`, then
  `RCX = [R10+0x18] + y * [R10+0x20] + x * 8`;
- source descriptor is `R10 = [RBX]`, then
  `RDX = [R10+0x18] + y * [R10+0x20] + x * 8`;
- callback output is `RDI`, with the live return showing
  `output_addr = output_base + y * 0x3c00 + x * 8`.

The package derives `output_base` once at the entry breakpoint from the live
output argument, then gates the selected downstream breakpoint by exact
`RDI == output_base + y*rowbytes + x*pixel_size`. This is the actual gating
relation. The field run must print `RCX` and its `dw RCX L8` words; the source
run must print `RDX` and its `dw RDX L8` words. Both runs must print the live
`RDI`, target address, x/y registers where still intact, and the relevant XMM
registers.

## Acceptance

Satisfactory for one target pixel:

- the selected site stops once at the exact output address;
- `field` returns `RCX` plus eight field PF16 words, or `source` returns `RDX`
  plus eight source/shade PF16 words;
- the console states the exact equality gate and the callback's live base
  formula;
- no instability is needed to interpret the result.

Best result:

- separate stable field, source, and writer runs for both case_0010 pixels;
- writer includes the scalar XMM inputs and the final PF16 words at `RDI`.

Partial but useful:

- one selected site is typed for `(6,40)`; or
- the selected site misses while the entry output address and the exact
  failed `RDI`/target comparison are retained.

Failure:

- no target-address gate;
- `rbp=y` or broad `r9=x` gate;
- multiple downstream breakpoints in one run when a single-site run was
  requested;
- package-local recomputation without a live Windows stop.

## Exact Smoke

On the Windows helper, from the extracted package directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\artifacts\run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1 -Site field -X 6 -Y 40
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\artifacts\run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1 -Site source -X 6 -Y 40
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\artifacts\run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1 -Site writer -X 6 -Y 40
```

For the second target, substitute `-X 901 -Y 394`. Each invocation owns one
target and one downstream site and writes its own CDB console/log directory.

## Inputs and Scope

Use the existing exact request folder:

`ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`

The normal runtime-trace package includes that request's `request_manifest`,
`reference_manifest`, case_0010 input and expected PNG, plus
`scripts/ae_render_single_case.jsx`. Preserve the extracted directory tree;
the launcher resolves these assets from its package root and fails early if
any required path is missing.

Use only `olmdistancegradation_extended__case_0010`. This package adds no
Mac-side source, build, installation, NAS, or share-publish action.
