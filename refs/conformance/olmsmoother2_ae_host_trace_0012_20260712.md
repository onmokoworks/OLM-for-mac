# OLMSmoother2 AE Host Trace: Current-AEX 0012

Date: 2026-07-12

## Scope

Mac AE 26.3 host trace for
`legacy_case_0012_gamma5_red_blue_current_aex` at `(91,841)`. The request
was materialized from the existing Windows `reference_manifest.json`; the
temporary request and output are under `/tmp/olm_sm2_trace_*_20260712`.

## FACT

- AE loaded the current `OLM Smoother v2` plug-in and rendered successfully.
- The plug-in trace recorded:

```text
stage=input_setup pixel_bytes=4 xy=91,841 raw=1,1,1,1 setup=1,1,1,0 class=0,255,0,255 range=88 version=2 gamma=2
polygon count=1
vertex=0 rgba=0.991067171,0.991067171,0.991067171,0.996078432 weight=0.356321841
stage=orchestrator xy=91,841 rgba=0.991067231,0.991067231,0.991067231,0.3549245
```

- The corresponding Mac AE output pixel is `[32,32,32,91]`.
- The local CLI trace reaches the same producer shape (`idx=105`, `c=2`,
  one polygon sample) and the same orchestrator float. The AE host's RGB 32
  follows from the enabled premultiplied output writeback (`0.991067231 *
  0.3549245 * 255`); it is not a new RGB-kernel candidate.
- The Windows reference pixel is `[0,0,0,0]`. The Windows-side alpha/class or
  config state is not present in this Mac trace.

## INFERENCE

- The Mac AE input/setup path is now directly observed for the target and is
  consistent with the local CLI producer path.
- The remaining source of the Windows-vs-Mac alpha difference cannot be
  assigned to Mac writeback alone. A same-run Windows witness must return the
  live class bytes/config binding and the c280/e170 decision before production
  changes are justified.
- Do not globally suppress transparent-center appends or alter alpha
  writeback from this result.

## Verification

```sh
python3 refs/scripts/smoke_olmsmoother2_0012_typed_bind_read.py
python3 refs/scripts/smoke_smoother2_fullchain_diff.py
```

Both pass their intended local/fail-closed gates. Neither is an AE exact claim.

## Neighborhood follow-up

The same case was rerun with the 2026-07-12 diagnostic build. A complete 5x5
class/setup neighborhood is now fixed at
`refs/conformance/olmsmoother2_case0012_class_neighborhood_20260712.log`; see
`refs/conformance/olmsmoother2_host_class_neighborhood_trace_20260712.md`.
The target output and polygon/orchestrator values reproduced exactly. Windows
live class/config values are still required before changing the producer.
