# OLMBlur case_0006 Current-AEX Export Contract - 2026-07-01

> **Evidence correction (2026-07-10):** the current-AEX export identity below
> remains valid, but the accompanying claim that Windows and Mac agree on the
> internal pre-store float and stored word is invalid. The debugger target was
> never captured. Use
> `refs/conformance/olmblur_case0006_unverified_windows_value_audit_20260710.md`
> for the corrected boundary.

This note defines the exact missing Windows artifact for the remaining
`OLMBlur` 16bpc `case_0006` provenance lane.

It is intentionally not a live implementation patch note. Its purpose is to
make any future Windows follow-up precise and cheap.

## 2026-07-09 Return Status

The requested current-AEX export has returned and matches Outcome A.

- Imported manifest:
  `refs/win_references/olmblur_case0006_current_aex_export_20260709/OLMBlur/reference_manifest.json`
- Audit:
  `refs/conformance/olmblur_case0006_current_aex_export_contract_audit_20260701.md`
- Decision: `outcome-a-current-aex-matches-canonical`
- Key identity: the Windows current-AEX export has SHA-256
  `27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f`,
  byte-identical to the canonical 2026-06-25 Windows Software reference.

Do not resend this request unchanged. The `case_0006` question is no longer
"is the canonical Windows reference equivalent to the current Windows AEX
export?" It is now a Mac export / AE-host run provenance question if reopened.

## Why this artifact was needed

The current repo now has three important facts at once:

1. canonical Windows 16bpc reference and handoff expected mirror are
   byte-identical
2. Windows and Mac agree on the traced pre-store float and stored internal word
   at the two lane-defining witnesses `(314,14)` and `(29,71)`
3. current repo export artifacts split by path:
   - single-case Mac export matches the local stored-word model at the active
     pair
   - batch candidate matches canonical at some representative points and misses
     at others

That means the unresolved question is no longer "what does the OLMBlur math do
here?" but "which exported PNG artifact is actually equivalent to the canonical
2026-06-25 Windows Software reference?"

## Exact requested artifact

A same-run Windows current-AEX exported PNG for:

- plug-in: `OLM Blur`
- case id: `olmblur__case_0006`
- bit depth: `16bpc`
- renderer: `SOFTWARE`
- parameter slice:
  - `Blur Amount=5`
  - `Blur Smoothness=100`
  - `Number of Repeat=10`
  - `Bias Direction=1`
  - `Legacy=0`

## Prepared Request Package

2026-07-09: the one-case Windows reference request is materialized as:

- request JSON:
  `refs/reference_requests/olmblur_case0006_current_aex_export_20260709.json`
- handoff zip:
  `handoffs/windows_batch/olm_windows_reference_request_olmblur_case0006_current_aex_export_20260709.zip`

This is a reference/export-provenance request, not a runtime trace request. Do
not overwrite an active `/Volumes/onmk/olm_pr/new` runtime-trace exchange with
this package; send it after the currently staged runtime request has returned or
after the exchange folder is intentionally cleared.

## Minimum return payload

To count as actionable, the return should include all of:

1. the exported PNG file itself
2. AE version
3. project renderer metadata
4. bit depth metadata
5. manifest/property snapshot proving the same parameter slice
6. explicit statement whether the PNG came from:
   - the same current AEX build/path as the witness run, and
   - the same comp/render setup as the canonical 2026-06-25 reference family

## Witness points to compare immediately

The 2026-07-09 return compares these 16-bit points as follows:

| XY | canonical ref | single-case Mac export | 2026-06-26 batch candidate | why it matters |
| --- | --- | --- | --- | --- |
| `(314,14)` | `[2201,2201,2201,65535]` | `[2199,2199,2199,65535]` | `[2201,2201,2201,65535]` | lane-defining witness A |
| `(29,71)` | `[725,725,725,65535]` | `[727,727,727,65535]` | `[727,727,727,65535]` | lane-defining witness B |
| `(601,598)` | `[4609,4609,4637,65535]` | `[4607,4607,4637,65535]` | `[4609,4609,4637,65535]` | batch aligns here |
| `(378,487)` | `[64767,35,35,65535]` | `[64767,35,35,65535]` | `[64769,35,35,65535]` | single-case aligns here |

## Decision outcomes

### Outcome A: current-AEX export matches canonical reference

Status: matched on 2026-07-09.

Interpretation:

- canonical reference is likely the right compare artifact for this lane
- the remaining disagreement is then between exported Mac artifacts, not
  between Windows canonical and current-AEX Windows export

Next step:

- audit Mac export path / AE-host run differences more narrowly before
  reopening implementation

### Outcome B: current-AEX export matches one of the Mac exports instead

Interpretation:

- canonical 2026-06-25 reference is not equivalent to the current-AEX export
  class for this lane
- `case_0006` should be reclassified as a reference-generation /
  export-provenance split rather than a live porting bug

Next step:

- keep `mac/OLMBlur/OLMBlur.cpp` frozen for this lane
- reclassify the case in the provenance ledger / conformance notes

### Outcome C: current-AEX export matches neither canonical nor current Mac exports

Interpretation:

- export-side or run-setup provenance is still mixed
- the lane remains provenance-first

Next step:

- compare against the exact witness-run metadata and source frame before
  considering any source changes

## Forbidden moves after this artifact

- no global 16bpc writer swap
- no helper surgery from `case_0006` alone
- no treating the Mac single-case export as the Windows current-AEX behavior
- no collapsing this lane into `case_0007` Legacy work
- no resending this same reference/export request unless a newer Windows AEX or
  changed AE render setup invalidates the 2026-07-09 proof
