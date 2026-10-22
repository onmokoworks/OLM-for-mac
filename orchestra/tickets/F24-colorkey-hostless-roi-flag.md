## Goal
Fix the ColorKey hostless ROI/generic gate regression introduced by merge 58ef6188 (F18).

## Facts
`orchestra/reports/I01-integration-check.md`: `python3 scripts/run_olm_generic_beta_gate.py --run-test-file
tests/test_olmcolorkey_generic_roi_tile.py` fails with an undeclared `PF_OutFlag2_SUPPORTS_THREADED_RENDERING`
(the hostless adapter compiles against SDK headers that lack it). Good parent cbb2d255 passes.

## Requirements
Keep F18's measured flag values (original AEX GlobalSetup out_flags2) bit-identical. Fix the build by using the
numeric value / a guarded define in the hostless adapter or the shared header, not by changing flags.
Verify: the ROI test passes, F18's flag audit (`tools/emulation/audit_route_flags_F18.py`) still 10/10, ColorKey
corpus replay matches.
