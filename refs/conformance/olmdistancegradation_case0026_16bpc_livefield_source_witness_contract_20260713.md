# OLMDistanceGradation case0026 16bpc live field/source witness contract

The acceptance unit is one same-run tuple spanning all four target points.

Date: 2026-07-13

Request id:
`olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713`

## Scope

This request is for one fresh Windows current-AEX Software 16bpc run of
`olmdistancegradation_extended__case_0026`.

Target points:

- `(907,222)`
- `(395,477)`
- `(1589,579)`
- `(898,670)`

The return is acceptable only when all four points are captured from the same
AE/CDB run id.

## Required typed capture

For every target point, return all of the following from that same run:

- bound coordinate `(x,y)`
- live case tuple from the callback parameter block
  - `In/Out=3`
  - `Inside Threshold=158`
  - `Outside Threshold=13`
  - `Use Background Color=1`
  - `Invert=1`
  - `Render Mode=1`
  - `Interpolation Mode=4`
  - `Power=0x40263bec`
  - gradation/background color raw float bits
- source raw `A,G,R,B` words
- field raw `A,G,R,B` words
- exact `[RCX+2]` word consumed by `FUN_181170480`
- pre-call output words
- post-call output words after `FUN_181170480`

The package pins the loaded Windows `DistanceGradation.aex` identity:

- path: `C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\DistanceGradation.aex`
- SHA-256:
  `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`
- size: `26289664`

It also requires AE Software rendering and 16bpc project depth.

## Binding strategy

The runner binds the witness lane at `FUN_181170480` entry by:

1. matching the live case tuple from the parameter block, and
2. matching one of the four target `(x,y)` coordinates in that same callback.

After the bind, it records:

- entry-time output pointer and pre-call words,
- field read at `DistanceGradation+0x117057d`,
- source read at `DistanceGradation+0x11705f1`,
- post-call output words at the exact caller return address captured from
  `[RSP]` on entry (`bp /1 @$t2`). This binds the post-state to the same
  invocation without assuming a shared internal exit offset.

This request does not accept replayed values, PNG-derived values, or prior
carry-store evidence substituted for live field words.

## PowerShell 5.1 runner requirement

The packaged runner must launch `cdb.exe` via `Start-Process` with one explicit
quoted argument string, not a PowerShell argument array. This is part of the
contract.

## Acceptance

`answered` requires:

- one shared run id across all four points;
- all four points present;
- exact case tuple match on every point;
- live source raw words, field raw words, `[RCX+2]`, and pre/post output words
  on every point;
- AEX hash pin and AE Software/16bpc host contract satisfied.

Otherwise the result must be:

- `status: "exact_bind_failure"`
- with concrete `stage`, `reason`, `missing`, and `last_observation`

`answered_partial`, `partial`, and vague summaries are forbidden.
