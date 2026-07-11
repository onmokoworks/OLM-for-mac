# OLMDistanceGradation 0010 Visited-Tile Source Witness

Date: 2026-07-10

Request id:
`olmdistancegradation_0010_compose_visited_tile_source_0_45_20260710`

## Purpose

The `901,394` retry bound the live output address but missed the downstream
site. Its entry witness proved that this invocation actually entered the
callback at `(0,45)`. This successor asks for the source witness at that known
visited coordinate, rather than inferring that a residual pixel belongs to the
same callback tile.

## Required Run

Run exactly one Software case and one site:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File \
  .\artifacts\run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1 \
  -Site source -X 0 -Y 45
```

Use `olmdistancegradation_extended__case_0010`. Keep `sxi 80000003`, retain
only the entry and `DistanceGradation+0x11705f1` source breakpoints, and gate
the downstream stop with:

`RDI == output_base + 45*0x3c00 + 0*8`.

At the exact gated stop, return `RDX`, `dw RDX L8`, the source XMM scalars, the
live `RDI`, and the derived target address. If it misses, retain the exact
failed comparison rather than a PNG or package-local reconstruction.

Do not run field/writer sites in this request, do not use `rbp=y` or broad
`r9=x`, and do not retry `(6,40)` or `(901,394)`.

## Acceptance

Satisfactory: one exact-gated source hit with typed `RDX` words.

Partial but useful: entry address plus an exact failed `RDI` comparison.

Not evidence: a callback entry with no downstream gate result, broad hits, or
PNG-only output.
