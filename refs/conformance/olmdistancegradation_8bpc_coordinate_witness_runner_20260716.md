# OLMDistanceGradation 8bpc Coordinate Witness Runner

Date: 2026-07-16

## Scope

`scripts/run_olmdistancegradation_8bpc_coordinate_witness.py` is a bounded
Mac-local witness runner/checker for the three coordinates selected by the
8bpc liveness census in
`refs/conformance/olmdistancegradation_8bpc_coordinate_liveness_census_return_20260715.md`:

| Case | Coordinate |
| --- | --- |
| `case_0001` | `(17,0)` |
| `case_0015` | `(780,495)` |
| `case_0029` | `(987,496)` |

The script validates the canonical split 8bpc request manifests, limits
`OLM_DG_DEBUG_POINTS` to one coordinate per case, and passes
`OLM_DG_DEBUG_DUMP_PATH` and `OLM_DG_SHADE_DEBUG_PATH` to the existing
`scripts/run_ae_single_case.py`. The checker requires one PF8 field witness and
one PF8 shade witness at the requested coordinate, plus an AE result reporting
project depth 8. It does not compare output PNGs or claim exactness.

`case_0001` and `case_0015` use
`handoff/ae_pixel_validation_20260618/requests/ae_pixel_olmdistancegradation_basic_exact_20260619`;
`case_0029` uses
`handoff/ae_pixel_validation_20260618/requests/ae_pixel_olmdistancegradation_blur_exact_20260619`.
The runner does not copy or mutate request fixtures.

## Use

Discovery/dry-run, with no AE invocation:

```sh
python3 scripts/run_olmdistancegradation_8bpc_coordinate_witness.py --dry-run
```

Execute into a disposable directory:

```sh
python3 scripts/run_olmdistancegradation_8bpc_coordinate_witness.py --run --output-dir /tmp/olmdg_8bpc_coordinate_witness_run
```

Check an existing run without invoking AE:

```sh
python3 scripts/run_olmdistancegradation_8bpc_coordinate_witness.py --check --output-dir /tmp/olmdg_8bpc_coordinate_witness_run
```

## Validation

Dry-run validation and a live Mac AE execution were performed on 2026-07-16.
The live run used AE `26.3x87`, Software, a fresh project, color management
disabled, and reported 8bpc for every case. All three coordinates produced
exactly one PF8 field record and one PF8 shade record:

| Case | Field value | Stored ARGB | Output SHA-256 |
| --- | --- | --- | --- |
| `case_0001` | `0.0078125` | `57,255,0,0` | `77b57253e0b1076267bfff2bed639ac22343b6434d18b3ff5506d2b71f857224` |
| `case_0015` | `0.037291009` | `10,10,0,0` | `3679cc373c8d2544540c38817fc8307710c5decc269ad3682585ac768d98f4ce` |
| `case_0029` | `0.250339508` | `64,28,0,238` | `b615818e1ec29afb32bd0d994a0ed83e6001d1278da3c7b7c926ae6500c0a86b` |

The current-source universal bundle binary SHA-256 was
`f60fecc36b108202e7e724487d2c46695743526fcf358c766bf4b52de2c2d596`.
Two fresh three-case runs with that installed binary produced the same output
hashes above. For every point, the pre-assignment clamped ARGB bytes equaled
the immediate destination-world readback bytes. An earlier run used a stale
installed bundle and produced different output hashes; those hashes are
superseded and are not conformance evidence.

The run is a Mac path-liveness proof, not a Windows comparison and not an
`AE exact` claim. No Windows or NAS operation is part of this tool.

The runner passes `--keep-open` because the single-case JSX otherwise quits AE
after the first case, invalidating the next Apple Event connection. This note
and the script are harness-only changes. Production plugin source is unchanged.
