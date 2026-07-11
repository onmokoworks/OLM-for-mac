# OLMDistanceGradation case_0023 Mac reverify runner

The reproducible entry point is:

```bash
python3 scripts/run_distancegradation_case0023_mac_reverify.py --dry-run
```

It materializes two cases, `case_0023__bg_on` and `case_0023__bg_off`, from the canonical Windows AE Software 16bpc references. The request fixes `bits_per_channel=16`, `gpu_accel_type=SOFTWARE`, and an exact gate of `max_diff=0`, `mean_diff=0`, and `nonzero_px_percent=0`. Each live run forces a fresh AE project and passes `Use Background Color=1` or `0` explicitly, so the generic runner cannot inherit an 8bpc project depth.

On a Mac with AE GUI available, omit `--dry-run`. The runner executes both cases and writes `report/case0023_mac_reverify.json` and `.csv`. A successful exact run ends with `validated_exact`; GUI-unavailable hosts stop at `dry_run_ready_for_mac_ae_gui` and leave the two recorded commands in `MAC_AE_READINESS.json`.

The exact gate is also independently reproducible from the materialized work directory:

```bash
python3 refs/scripts/verify_manifest.py \
  /tmp/olmdg_case0023_mac_reverify/request/reference_manifest.json \
  --reference-dir /tmp/olmdg_case0023_mac_reverify/request/expected \
  --candidate-dir /tmp/olmdg_case0023_mac_reverify/candidate \
  --max-diff 0 --mean-diff 0 --nonzero-px-percent 0
```

No GUI run means no conformance claim: readiness is the terminal state until both candidate PNGs exist and the verifier reports `ok=2 fail=0 missing=0`.

## Executed result

The shared-core build was installed and this runner was executed against live
Mac AE `26.3x87` with a fresh project and Software renderer on 2026-07-10:

```text
[OK] olmdistancegradation_extended__case_0023__bg_on  max=0 mean=0.0000
[OK] olmdistancegradation_extended__case_0023__bg_off max=0 mean=0.0000
ok=2 fail=0 missing=0 total=2
status=validated_exact
```

The authoritative slice verdict and plug-in binary hashes are recorded in
`refs/conformance/olmdistancegradation_shared_core_mac_ae_case0023_20260710.md`.

This change owns only DG runner/request/readiness tooling and this conformance contract. It does not modify Mac plug-in source.
