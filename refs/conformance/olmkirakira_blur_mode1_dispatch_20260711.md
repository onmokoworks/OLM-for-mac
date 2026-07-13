# OLMKiraKira Blur Mode 1 Dispatch

Date: 2026-07-11

## Scope

Implemented only the statically grounded box-filter pass mapping from
`olmkirakira_mode_dispatch_static_audit_20260710.md`:

- Blur Mode 1: one pass.
- Blur Mode 2: three passes.
- Blur Modes 3/4: retain the port's current three-pass behavior; Gaussian and
  recursive/separable implementations are not claimed.
- An explicit CLI `--falloff` remains a diagnostic override. `box3` selects
  three passes and every other accepted/current value selects one, matching
  the pre-change CLI behavior.

No hotspot composition, gain, quantization, or ray-kernel code was changed.

## Implementation

- `cli/OLMKiraKira/main.cpp` records whether `--falloff` was explicitly
  supplied. Without it, `blur_mode == 1` selects one pass and all other values
  select the existing three passes.
- `mac/OLMKiraKira/OLMKiraKira.cpp` passes one iteration only for
  `info.blur_mode == 1`; all other values retain three.
- `refs/scripts/smoke_olmkirakira_blur_mode_dispatch.py` renders a retained
  textured source and verifies dispatch through output identity.

## Regression Result

Command:

```sh
python3 refs/scripts/smoke_olmkirakira_blur_mode_dispatch.py
```

Result: exit 0. The script rebuilt the CLI and passed all assertions:

- Mode 1 equals explicit `box1`.
- Mode 2 equals explicit `box3`, proving the default Mode 2 output remains on
  the prior three-pass path.
- Mode 1 and Mode 2 outputs differ on the focused fixture.
- Explicit `box3` overrides Mode 1 and explicit `box1` overrides Mode 2.
- Modes 3 and 4 remain identical to the current Mode 2 three-pass output.

CLI build command (also run by the regression):

```sh
refs/scripts/build_olmkirakira_cli.sh
```

Result: exit 0, output
`cli/OLMKiraKira/olmkirakira_cli`; no compiler diagnostics.

Mac build command:

```sh
xcodebuild -project mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj -scheme OLMKiraKira -configuration Debug build CODE_SIGNING_ALLOWED=NO
```

Result: exit 0, `** BUILD SUCCEEDED **`. The arm64 plugin linked at Xcode's
DerivedData product path. Existing SDK `#pragma pack`, Carbon Resources, and
traditional-headermap warnings remain.

The independently rebuilt arm64 candidate was installed as the sole
`OLMKiraKira.plugin` in MediaCore while AE was closed. Binary SHA-256:
`421f670fdf26cc61170028e4b65709c8232358f4a63a04f46b498b6dd4b96b0a`.
The previous installed bundle is retained outside MediaCore at
`/tmp/OLMKiraKira.plugin.pre_blur_mode1_20260711`.

## Reference Boundary

The retained Windows corpus has three OLMKiraKira random cases whose manifests
set Blur Mode 1. Those cases also vary other controls and therefore do not
isolate this dispatch. They were not used to claim a Mode 1 quality or AE-exact
measurement. The regression proves parameter-to-pass routing and preservation
of the CLI's Mode 2 path only; CLI output is not claimed AE exact.
