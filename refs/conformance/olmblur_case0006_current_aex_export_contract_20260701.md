# OLMBlur case_0006 Current-AEX Export Contract - 2026-07-01

This note defines the exact missing Windows artifact for the remaining
`OLMBlur` 16bpc `case_0006` provenance lane.

It is intentionally not a live implementation patch note. Its purpose is to
make any future Windows follow-up precise and cheap.

## Why this artifact is still needed

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

## Exact missing artifact

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

When the artifact lands, compare these 16-bit points first:

| XY | canonical ref | single-case Mac export | 2026-06-26 batch candidate | why it matters |
| --- | --- | --- | --- | --- |
| `(314,14)` | `[2201,2201,2201,65535]` | `[2199,2199,2199,65535]` | `[2201,2201,2201,65535]` | lane-defining witness A |
| `(29,71)` | `[725,725,725,65535]` | `[727,727,727,65535]` | `[727,727,727,65535]` | lane-defining witness B |
| `(601,598)` | `[4609,4609,4637,65535]` | `[4607,4607,4637,65535]` | `[4609,4609,4637,65535]` | batch aligns here |
| `(378,487)` | `[64767,35,35,65535]` | `[64767,35,35,65535]` | `[64769,35,35,65535]` | single-case aligns here |

## Decision outcomes

### Outcome A: current-AEX export matches canonical reference

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

## Forbidden moves until this artifact exists

- no global 16bpc writer swap
- no helper surgery from `case_0006` alone
- no treating the canonical reference as equivalent to current-AEX export
  without proof
- no collapsing this lane into `case_0007` Legacy work
