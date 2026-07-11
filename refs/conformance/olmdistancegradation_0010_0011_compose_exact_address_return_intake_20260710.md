# OLMDistanceGradation Compose Exact-Address Return Intake

Date: 2026-07-10

Request: `olmdistancegradation_0010_0011_compose_exact_address_witness_20260710`

Classification: `answered_partial`

## Accepted Facts

- The live Windows run is `olmdistancegradation_extended__case_0010` at
  16bpc.
- Source and output worlds both use `rowbytes=15360` (`0x3c00`) and
  `pixel_size=8` with PF_Pixel16 channel layout.
- Same-run entry logs derive stable bases:
  - output: `0x0000017d8d9b0100`
  - source: `0x0000017d8c9d0100`
- The formula `base + y * 0x3c00 + x * 8` gives:
  - `(6,40)` output `0x0000017d8daa0130`, source `0x0000017d8cac0130`
  - `(901,394)` output `0x0000017d8e71f908`, source `0x0000017d8d73f908`

## Missing Proof

The return does not contain any of the requested exact-pixel values:

- field address or channel layout
- RCX field words at `DistanceGradation+0x117057d`
- RDX source words at `DistanceGradation+0x11705f1`
- field-read/transform scalar values
- final PF16 words or final-writer scalars

The downstream breakpoints did not retain same-run hits after the entry
witness. Therefore this return binds source/output addresses only. It does not
classify the `case_0010/0011` residual and does not authorize a Mac source
change.

## Intake Caveat

The returned JSON uses outer `status=answered` while its observation-level
classification and summary say `answered_partial`. The generic verifier
accepted this as a returned response; that is not conformance completion. The
runtime comparator must preserve the partial classification and require typed
field/source/store evidence before promoting this request to proof.

## Next Action

Use the newly grounded base/address formula in a narrower Windows follow-up:
one case, one target, and one downstream site per debugger run. Avoid combining
field, source, and writer breakpoints in one unstable session.
