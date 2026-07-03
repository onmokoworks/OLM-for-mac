# OLM Reference Provenance Ledger

Updated: 2026-07-01

This note exists to keep reference questions separate from implementation
questions. Use it when the open lane is not “what math does the AEX do?” but
“which render/export/reference artifact are we actually comparing?”

## Scope

Track only high-signal provenance-sensitive lanes here. Do not mirror every
reference set in the repo.

| Family | Canonical reference | Alternate / legacy reference | Candidate/export side | Current question |
| --- | --- | --- | --- | --- |
| `OLMBlur 8bpc normalized` | `20260618 normalized Software refs` | `20260604 legacy refs` | Mac AE packaged exact slices | Canonical normalized refs are already the exact gate; do not retune from old legacy drift alone |
| `OLMBlur 16bpc case_0006` | Canonical 16bpc Windows Software reference used by current compare lane | Current-AEX exported PNG / any recaptured export used in narrow witness work | Mac AE 16bpc output with sign-mixed one-word residual | Confirm whether the compared exported PNG and canonical reference are truly the same render class and export path before touching writer/helper code |
| `OLMBlur 16bpc case_0007` | Canonical 16bpc Windows Software reference | Legacy family witness bundles and old normalized 8bpc family | Mac AE Legacy carry-prev path | Keep provenance split explicit; do not collapse this into `case_0006` |
| `OLMColorKey Edge case_0009` | 20260618 normalized/current reference | 20260604 older reference | Mac AE / CLI candidate exact against normalized ref | Already classified as `reference-generation split`; do not tune from the older ref |
| `OLMDistanceGradation 8bpc normalized` | 20260618 normalized Software refs | Legacy drift bundles | Mac AE packaged exact slices | 8bpc is already exact against canonical normalized refs |
| `OLMDistanceGradation 16bpc case_0023 threshold family` | Latest Windows Software/runtime-traced threshold triplet | Packaged expected PNG under `ae_single_distancegradation_case0023_probe_20260701/expected/` | Live Mac AE single-case rerun | `(415,393)` is now a provenance split candidate: live Mac and latest Windows typed final are red, while the packaged expected PNG is blue. Keep threshold-family provenance separate from the still-unresolved edge-family pixels. |
| `OLMRadialBlur case numbering` | Request filename + manifest identity | Parent-folder names and conflicting 20260604/20260605 same-numbered cases | Mac CLI / Mac AE probes | Never compare by case number alone; always carry request/manifest identity |

## Provenance fields to record when a lane opens

- plug-in / lane
- case id
- bit depth
- AE version
- renderer / renderer metadata
- color-management metadata if relevant
- reference root path
- whether the reference is canonical, legacy, normalized, or current-AEX recapture
- candidate/export root path
- whether the candidate is Mac AE, Mac CLI, or exported Windows current-AEX
- the exact unresolved question

## Decision rule

When a lane is provenance-first:

1. Do not change implementation until the compared artifacts are named.
2. Prefer canonical normalized/current references over legacy folders.
3. Keep current-AEX recapture and canonical Software reference as separate
   artifacts unless proven equivalent.
4. If a mismatch is only against a superseded or legacy reference, classify it
   as a provenance split rather than an implementation failure.

## Current high-signal lane notes

- `OLMBlur 16bpc case_0006`
  - canonical 16bpc Windows Software ref and handoff expected mirror are
    byte-identical
  - Windows and Mac now agree on the tracked pre-store float and stored
    internal word at `(314,14)` and `(29,71)`
  - current repo artifacts already split by export path:
    the single-case Mac export matches the local stored-word model at the
    lane-defining pair, while the 2026-06-26 batch candidate matches canonical
    at `(314,14)` / `(601,598)` but not at `(29,71)` / `(378,487)`; see
    `refs/conformance/olmblur_case0006_reference_provenance_20260701.md`
  - the missing durable artifact is a same-run Windows current-AEX 16bpc export
    that can be compared directly against the canonical 2026-06-25 reference
  - until that exists, keep this lane classified as provenance/export audit
    rather than writer/helper surgery
