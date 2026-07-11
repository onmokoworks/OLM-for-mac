# Milestone 3: case_0010 tiny Rotation witness (1614,6)

- Reference set: `refs/win_references/20260604_olm/OLMRadialBlur`
- Comp: 1920x1080, bpc=8
- Witness output px (1614,6): **[255, 255, 255, 255]** (Windows/GPU reference); input px there: [0, 0, 0, 255]
- case_0010 params: Blur Type=2 (2=Rotation), Center=[960, 540], Angle=0, Ratio=1, Repeat Border=1, Quality=5, **GPU Rendering=1**

## Verified witness geometry (independent of emulation)

- (1614,6) - center(960,540): dx=654, dy=-534, radius = **844.317**, angle = **320.768deg** (frac of 2pi = 0.8910).
- Polar plane in FUN_180004640 is laid out `[radial_row][angular_col]` (population loop: outer = radial `fVar5` rows, inner = angular `iVar29` cols; see decomp lines ~2077-2121).
  - iVar29=1440: maps to (radial_row=844, angular_col=1283)
  - iVar29=1800: maps to (radial_row=844, angular_col=1604)
- **iVar29=1800 reproduces the Windows-traced cell family exactly**: radial_row 844 = Windows `row844`, angular_col 1604 in-range of Windows `col1601-1603`.
- iVar29 = (int)(360.0 / param_1[0]); iVar29=1800 => param_1[0] ~= 0.2, i.e. `FUN_180001ac0` took its `strength <= 0` default branch (`*param_1 = 0.2`). This pins the effective angular resolution of the polar grid for case_0010 without running the render.

## Bright-lobe localization (upstream population check)

- The radius-844 source circle carries **17 bright samples** (luma>40) -- matching the lane_state "reference bright count in local window: 17".
- Nearest bright arcs to the witness angle (320.8deg):
  - 327.1deg, source px (1669,81), luma 158 (delta 6.3deg from witness)
  - 329.0deg, source px (1684,105), luma 214 (delta 8.2deg from witness)
  - 329.1deg, source px (1684,106), luma 59 (delta 8.3deg from witness)
  - 346.7deg, source px (1782,346), luma 222 (delta 25.9deg from witness)
- **Consequence**: the bright family EXISTS on the witness radius circle, ~7deg clockwise of the witness angle. The witness pixel itself is black in the input; Windows produces white by gathering the neighboring-angle bright lobe during the rotation smear. This is the lane's decision-ladder **scenario #2** (bright family exists upstream, lost in ownership / substitute / neighboring-angle promotion before final inverse sampling), NOT scenario #1 (population absence).

## Windows typed polar cells (for the eventual bit compare)

| cell | hex | float (RGB; A=1.0) |
|------|-----|--------------------|
| row844 col1603 | `0xbc70f44b` | -0.014707 |
| row845 col1603 | `0xbd46d045` | -0.048538 |
| row843 col1601 | `0x3dd69702` | +0.104780 |
| row843 col1602 | `0x3de119ce` | +0.109912 |
- Note the row843 cells are positive (+0.10.., +0.11..) and the row844/845 cells negative (-0.014.., -0.048..): the polar plane holds signed lobes, consistent with the lane_state positive/negative cluster evidence. Reproducing these bit-for-bit is the emulation-validity goal.

## Emulation status and the reproduction blocker

- The M2 harness already drives `FUN_180004640` to completion and the witness sub-regions (f250/f252/+0xe) are typed-addressable. What M3 still needs for a *bit-exact* typed-cell compare is a `param_2` built from case_0010's REAL parameter values, not synthetic placeholders.
- `param_2` is populated by `FUN_180008690` (the AE param reader), which calls `FUN_18000e190/e270/e430/e5f0/e6d0/de60/e7b0` -- PICA param-checkout suite calls -- to pull each AE parameter into a struct byte offset. The reader-index -> offset map is documented in `CASE0010_PARAM_MAPPING.md`. To build `param_2` "by the real code" (lowest fabrication risk) we must mock those ~20 reader calls to return case_0010's manifest values, then run `FUN_180008690 -> FUN_180007520 -> FUN_180004640` on the real 1920x1080 input.
- **Compute is tractable**: with iVar29=1800 and radius ~844 the polar population is ~1800*844 ~= 1.5M cells; with the source unpack (1920*1080 px) and the final inverse-sample loop the whole render is on the order of ~0.75-1.0 billion x86 instructions -- minutes under the new `fast=True` loader mode (range-limited code hook; see README). Speed is not the blocker.
- **The blocker is parameter provenance**, not compute or geometry. Rather than hand-fabricate the ~20 `param_2` scalar fields (which the lane's constraints and the no-fabrication rule forbid), M3 stops here with the geometry + bright-lobe findings proven, and hands the param-reader mocking to the next step.

## Honest scope note

- No bit-exact typed-cell match is claimed. The row844/col1603 = `bc70f44b` comparison is NOT yet performed against emulator output; doing so requires the real `param_2` (above).
- The Windows reference was captured with **GPU Rendering=1**; per the project memory this can diverge from the CPU `.aex` path. The typed polar cells, however, come from a CPU CDB trace of the `.aex` (anchors at `+0x4eb9/+0x4ec8`), so they are the correct target for a CPU-`.aex` emulation compare.
- Findings respect the lane's forbidden list: no validity-alpha rewrite, no final-byte-conversion retune, no PNG-appearance matching is proposed. The evidence points at scatter/substitute-path ownership before final inverse sampling (decision-ladder #2).
