# OLMDirectionalBlur Gaussian Divisor Patch

This is a narrow Mac-source patch note. It does not promote
`OLMDirectionalBlur` to `AE exact`.

## Patch

- File: `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`
- Function: `DirectionalGaussianWeights`
- Change: gaussian denominator now uses `length / 3.0f` instead of
  `length / 0.5f`.

## Evidence

- `cli/OLMDirectionalBlur/main.cpp` documents the AEX weight-table builder as
  using `length / 3.0f`.
- `notes/IR_OLMDirectionalBlur.md` fixes the same rule as binary-grounded IR.
- `refs/conformance/olmdirectionalblur_mac_static_surface_audit_20260709.md`
  identified the Mac plug-in as the remaining outlier using `length / 0.5f`.

## Boundary

This patch is intentionally limited to the static divisor mismatch. It does not
close the angle-0 or diagonal lanes. The angle-0 lane still needs the
single-shot witness for `(494,169)` and `(579,169)` with rowdriver/group
membership, denominator, valid-alpha/side-channel, pre-writeback RGBA, and
final bytes.

## Forbidden Follow-up

Do not use this patch as permission for broad PNG tuning. The next closeout
proof for DirectionalBlur remains runtime witness evidence, not look matching.
