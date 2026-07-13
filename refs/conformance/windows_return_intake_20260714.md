# Windows return intake - 2026-07-14

## DistanceGradation 8bpc depth control

- Return: `RETURN_RUNTIME_TRACE.zip`
- Return SHA-256: `1d2dc615a3e684a814341fee9353229793eaffd4d16b6807dfc92cd9dce72ea3`
- Status: `answered`
- Request ID: `olmdistancegradation_8bpc_current_aex_depth_control_20260713`
- Run ID: `dglive-43815e7910e54746afe28fc2d4d786e5`
- AE PID: `65392`
- Module base: `0x7ff866300000`
- AEX SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`
- Project depth: `8bpc`
- PF8 callback `+0x1170870`: `41177` hits
- PF32 callback `+0x1170c90`: `0` hits

This is accepted evidence for callback depth dispatch only. It does not prove
pixel exactness, field/compose correctness, or AE exactness. The next allowed
DistanceGradation request remains the typed field/compose/store boundary.

## DirectionalBlur row 755

- Return: `RETURN_OLMDIRECTIONALBLUR_ROW755.zip`
- Return SHA-256: `05e4d2ae45300342e76c3f3404da61e2419494d4236269204b25d22437d578d1`
- Request ID: `olmdirectionalblur_row755_20260713`
- Status: `exact_bind_failure`
- Failure stage: `cdb_launch`
- Missing field: `cdb_bootstrap_exit`
- Observed AE command line contained the queue JSX path, but
  `bootstrap_host_image_marker_observed=false`, `queue_bootstrap_marker_observed=false`,
  and no typed witness artifacts were returned.

This return is not evidence against the DirectionalBlur algorithm or RVAs. It
is a launcher/bootstrap failure. Do not promote it to partial runtime evidence.

## Classification rule

The two returns are kept separate: the DistanceGradation control is accepted
for its declared gate, while the DirectionalBlur return remains fail-closed.
