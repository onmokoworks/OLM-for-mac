# OLMRadialBlur tiny Rotation Source-Candidates Refresh - 2026-07-03

Status: `tiny-rotation-pending-upstream-rgb-or-substitute-proof`

This is a persisted summary of the latest Mac-only source/polar audit for
`OLMRadialBlur tiny Rotation` `case_0010`, witness `(1614,6)`.

The refreshed local audit re-confirmed:

- current candidate RGBA at the witness is `[0,0,0,255]`
- Windows reference RGBA at the same witness is `[255,255,255,255]`
- direct witness source cells on rows `844/845` are still black
- the local bright family still lives around row `843` / angles `1601..1604`
- the active same-row branch still cannot directly see that cluster
- the 25x25 reference patch still contains `17` bright pixels while the tested
  local variants keep the bright count at `0`

## Decision

The live source boundary stays upstream of final inverse sampling.

Priority order remains:

1. `RenderRotation8` polar population / preserved-validity capture
2. scatter / substitute-path / neighboring-row ownership before inverse sampling
3. final inverse-sample / writeback only if a later Windows typed witness
   explicitly contradicts the current upstream reading

## Forbidden actions

- do not promote a global validity-alpha rewrite
- do not promote a same-row-only tweak from the row-843 cluster evidence alone
- do not retune final byte conversion while the witness remains black before the
  proven upstream boundary

## Source of the refresh

The persisted facts here come from the refreshed local command sequence:

- `bash refs/scripts/build_olmradialblur_cli.sh`
- `python3 scripts/analyze_olmradialblur_tiny_rotation_source_polar_probe.py ...`
- `python3 scripts/analyze_olmradialblur_tiny_rotation_support_envelope.py ...`
- `python3 scripts/analyze_olmradialblur_tiny_rotation_source_candidates.py ...`

The ephemeral generated outputs for this refresh were written under `/tmp`, so
this note records the conclusions in-tree.
