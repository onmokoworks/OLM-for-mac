# OLMBlur 8bpc Windows Software canonical recapture contract

Date: 2026-07-11  
Package: `refs/reference_requests/olmblur_windows_software_8bpc_aex_canonical_recapture_20260711.zip`

## Purpose

Replace the provenance gap identified by `olmblur_8bpc_reference_aex_provenance_audit_20260711.md` for the normalized seven-case family. The package reuses the normalized inputs, expected PNGs, and exact parameters from the 2026-06-19 request; it does not change implementation code, the ledger, pending reports, or NAS.

## Required runtime

- Windows After Effects, exact installed AE version recorded in `run/provenance.json` and each result.
- 1920x1080, 24 fps, 8bpc project; project renderer explicitly `Software`.
- OLMBlur installed as an exact absolute path to `OLMBlur.aex`.
- Required SHA-256: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
- Record AEX path, byte size, UTC last-write timestamp, and SHA-256 before rendering.
- Record working space, linear blending, and bits per channel as project color settings.

## Fail-closed gate

`run_olmblur_recapture.ps1` must write `hash_mismatch` and exit before launching After Effects when the AEX is missing, ambiguous, or its SHA-256 differs. A returned render without the matching provenance record is invalid.

The seven cases are `case_0001` through `case_0007`, with one PNG per case. The effect parameters, including the `GPU Rendering` parameter, are copied from the normalized manifest. A no-effect control is required. `ADBE Force CPU GPU` may be recorded if visible, but it cannot establish CPU/GPU or renderer state.

## Acceptance artifacts

`run/provenance.json`, `run/run_summary.json`, seven `run/rendered/case_####.png` files, per-case AE result/log files, and no-effect control evidence. The summary must state AE version, Software renderer, 8bpc project, color settings, verified plugin provenance, and all seven output paths.
