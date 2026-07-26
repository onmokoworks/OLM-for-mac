# OLMSmoother2 case-07 16bpc Mac AE exact

The declared no-key `final_random10_olm_smoother_v2_07` 16bpc slice is
`AE exact` on Mac AE `26.3x87` against the unchanged Windows AE Software
reference.

The fail-closed contract binds 16bpc, Software renderer raw value `1816`,
working-space raw `None`, linear blending disabled, the hash-pinned AEP, and
FLOAT OpenEXR output. Both required gates pass:

- no-effect control: `0/8,294,400` mismatched FLOAT32 words,
  max raw u32 delta `0`
- effect-on output: `0/8,294,400` mismatched FLOAT32 words,
  max raw u32 delta `0`

The final `-O2` Mac binary is
`45227dd84cad09eb483c8ce534132df1b80322e4ac1d6f32320d3887b1a35c3d`.
The same binary preserves the frozen current-AEX 8bpc suite at `12/12`,
`max_diff=0`, and preserves the declared 32bpc case-07 slice at raw FLOAT32
exact for PF32 entry, no-effect, and effect-on.

## Runtime localization

The original 16bpc effect residual contained 71 max-1 output words. Routing
only the PF16 inverse writer through the captured Windows 10,000-entry LUT
reduced it to 21 R-channel words. At representative pixel `(477,897)`, the
Windows and Mac polygon weight already matched at `0x3b8bf256`, while the
center and sample colors differed by one to three float32 ULP before
compositing. CDB proved the Windows runtime uses the captured LUT for PF16
frame decode as well as its inverse writer. Routing PF16 decode through that
same interpolation made the composite inputs bit-identical and closed both
AE gates.

The frozen PF8 path remains on its previously exact literal transform.
An experimental PF16 composite/FMA split was removed after an independent
render proved it unnecessary.

## Durable evidence

The machine-readable attestation and compressed Windows/Mac FLOAT EXRs are:

- `refs/conformance/olmsmoother2_case07_16bpc_mac_ae_exact_20260727.json`
- `refs/conformance/fixtures/olmsmoother2_case07_16bpc_ae_exact_20260727/`

Do not generalize this one case to all 16bpc inputs. Preserve all three exact
slices and expand additional 16/32bpc cases under independent contracts.
