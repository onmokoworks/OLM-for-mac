# OLMSmoother v1 Mac Port Handoff

Updated: 2026-05-08

## Goal

Port Windows `OLMSmoother.aex` v1 to a modern macOS After Effects `.plugin`,
then verify it against Windows output with pixel-level diffs.

Target private repo:

```txt
https://github.com/hakumeilab/OLM-for-mac.git
```

## Work Location

Repo staging directory:

```txt
/Users/onmk/Documents/Projects/Personal/OLM as
```

Active SDK build directory used by the previous session:

```txt
/Users/onmk/Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples/Template/OLMSmoother
```

Installed plugin path:

```txt
/Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMSmoother.plugin
```

## Current State

Overall plug-in status:

- `OLMSmoother2`: port complete
- `DistanceGradation`: port complete
- `ColorKeep`: port complete
- `OLMSmoother` v1: currently being ported
- other OLM plug-ins: pending / not started

Done:

- v1 plug-in skeleton renamed from `OLMSmoother2` to `OLMSmoother`.
- PiPL/version/out flags matched to Win v1:
  - `eVER 0x00090800`
  - `out_flags 0x02000040`
  - `out_flags2 0x08000000`
- PARAMS_SETUP corrected to Win v1:
  - `Use Color Key` checkbox, disk id 1
  - `Color Key` color picker, disk id 2
  - `Smooth Length Tolerance` slider, min 0, max 255, UI 0..6, default 6, disk id 3
- Classic Render and SmartRender are wired.
- 8-bpc and 16-bpc render paths are implemented.
- Stage 2 kernel literal port is in place:
  - classifier
  - sub-handler
  - alt-handler
  - main interpolation kernel
  - interpolation executor
  - edge walker
- Last reported build succeeded and was installed to MediaCore.
- Repo verification scaffold exists under `refs/`.

Known remaining work:

- Implement first-pass key-mask path:
  - `LAB_1800026e0`
  - `LAB_180002670`
  - temporary `PF_EffectWorld` allocation/free in `RenderEntryChain`
- Verify 8-bpc output against Windows reference PNGs.
- Verify 16-bpc output after 8-bpc converges.
- Float/32-bpc path is pass-through because Win v1 has no known float analogue.
- The current repo copy is a source snapshot; the SDK build tree may need to be
  synced from `mac/OLMSmoother/` before rebuilding.

## Important Files

```txt
mac/OLMSmoother2/
mac/OLMDistanceGradation/
mac/ColorKeep/
mac/OLMSmoother/Mac/OLMSmoother_port.cpp
mac/OLMSmoother/OLMSmoother.h
mac/OLMSmoother/OLMSmootherPiPL.r
mac/OLMSmoother/OLMSmoother_Strings.cpp
mac/OLMSmoother/OLMSmoother_Strings.h
disasm/v1_analysis/
refs/scripts/
refs/fixtures/test_cellanim.png
```

## Win Reference Flow

Use the same input image and comp on both machines.

Input:

```txt
refs/fixtures/test_cellanim.png
```

Minimum 8-frame matrix:

```txt
f0: UseKey=off, Tol=0
f1: UseKey=off, Tol=3
f2: UseKey=off, Tol=6
f3: UseKey=on,  KeyColor=#FFFFFF, Tol=0
f4: UseKey=on,  KeyColor=#FFFFFF, Tol=3
f5: UseKey=on,  KeyColor=#FFFFFF, Tol=6
f6: UseKey=on,  KeyColor=#000000, Tol=3
f7: UseKey=on,  KeyColor=#FF0000, Tol=3
```

Render Windows PNGs into:

```txt
refs/win/
```

Render macOS PNGs into:

```txt
refs/mac/
```

Then run:

```sh
refs/scripts/diff_all.sh
```

## Next Best Steps

1. Initialize/push this staged repo to `hakumeilab/OLM-for-mac`.
2. On Windows, render the 8-frame reference set from the original
   `OLMSmoother.aex`.
3. On macOS, render the same `.aep` using the ported `.plugin`.
4. Run `refs/scripts/diff_all.sh`.
5. If `UseKey=off` frames differ, debug Stage 2 kernel first.
6. If only `UseKey=on` frames differ, implement the key-mask first pass.
