# OLMDistanceGradation Current-AEX Same-Run Exact-Address Contract

Request id: `olmdistancegradation_current_aex_same_run_exact_address_20260711`

This is the strict successor to `olmdg_compose_exact_address_witness_20260710`.
Use one fresh Windows AE 2026 Software current-AEX run and retain one shared
`run_id` for both `olmdistancegradation_extended__case_0010` and
`olmdistancegradation_extended__case_0011`, at `(6,40)` and `(901,394)`.

## Required live tuple

## Case Fingerprint

The fingerprint is grounded by `decomp/DistanceGradation.aex.c.txt` in
`FUN_181170ff0`: property 3 is stored at `[param_6+0xB8]` and property 4 at
`[param_6+0xBC]`. The packaged request manifest gives the corresponding values:
case_0010 is `Inside=63, Outside=82`; case_0011 is `Inside=348, Outside=0`.
At `FUN_181170480` entry, read `dwo(@rbx+0xB8)` and `dwo(@rbx+0xBC)` into
dedicated registers. Set case tag `10` or `11` only for those exact pairs;
otherwise set `0xDEAD` and emit no typed witness.

For all four case/XY records, return the live values from that same run:

- current `DistanceGradation.aex` module base and binary identity;
- field-world base, header pointer/layout, rowbytes, pixel size, and channel layout;
- exact `RCX` field address and the word read at `RCX+0x2`;
- exact `RDX` source/shade address and the word read at `RDX+0x2`;
- output address, stored PF16 word, compose scalar bit patterns, and final writer inputs/words.

Use the live address formulas, not `rbp=y` or broad `r9=x` gates. At minimum,
record the full formulas for field, source, and output, including sub-rect origin
terms if present. The known output geometry is `rowbytes=0x3c00`, `pixel_size=8`.

## Runnable entry

Extract the package and run the package-local orchestrator:
`artifacts/run_olmdistancegradation_current_aex_same_run_exact_address_20260711.ps1`.
It starts one CDB/AfterFX process, invokes the included queue JSX, renders
case_0010 and case_0011 serially in that process. At each callback entry, CDB
reads the live parameter-block DWORDs `[RBX+0xB8]` and `[RBX+0xBC]`: the
disassembly-backed manifest fingerprints are `(63,82)` for case_0010 and
`(348,0)` for case_0011. CDB sets a pseudo-register case tag `10` or `11`,
otherwise `0xDEAD`, and emits literal `case_0010` or `case_0011` in
every ENTRY/FIELD/SOURCE/COMPOSE/WRITER marker. CDB rebinds the live output base
at every callback entry, gates field/source/compose/writer stops by exact output
address, derives XY from that address at each downstream site, and emits
separate stage markers. It writes
`RETURN_RUNTIME_TRACE.json`. The package includes both case fixtures and the
request/reference manifests. `-ParseOnly -TracePath` runs the same parser against
the included stdout fixtures.

## Acceptance and failure

`answered` requires all four joined witnesses and every required live field. Every
marker must carry its own literal live case id; no JSX output, phase marker, or
marker ordering may supply identity. FIELD/SOURCE/COMPOSE markers must not
contain future writer values. Writer words must be read from all four live
output lanes. If any field,
address, word, scalar bit pattern, or writer value is unavailable, return
`exact_bind_failure` with `stage`, concrete `reason`, `missing_fields`, and the
last live observation. `answered_partial` and `partial` are forbidden, including
when only one case or one pixel was reached. Do not substitute local AEX,
package-local recomputation, PNG-only evidence, or NAS paths.
