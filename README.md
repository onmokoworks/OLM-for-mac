# OLM for Mac

Private working repo for porting OLM After Effects plug-ins to modern macOS.

## Porting Status

Current progress:

- `OLMSmoother2`: port complete
- `OLMSmoother` v1: port in progress
- `DistanceGradation`: port complete
- all other OLM plug-ins: not started / pending

Current source:

- `mac/OLMSmoother2/`
- `mac/OLMDistanceGradation/`
- `mac/OLMSmoother/`
- main implementation: `mac/OLMSmoother/Mac/OLMSmoother_port.cpp`
- reverse-engineering notes: `disasm/v1_analysis/`
- verification fixture/scripts: `refs/`

Large local artifacts are intentionally ignored:

- Ghidra projects
- full decompiler dumps
- raw disassembly dumps
- built `.aex` / `.plugin` binaries
- local Win/Mac render outputs

## Build

This source was developed inside the After Effects SDK template tree:

```sh
/Users/onmk/Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples/Template/OLMSmoother
```

To build, copy or sync `mac/OLMSmoother/` into the AE SDK `Examples/Template`
folder as `OLMSmoother`, then run:

```sh
cd "/Users/onmk/Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples/Template/OLMSmoother/Mac"
xcodebuild -project OLMSmoother.xcodeproj -configuration Debug
```

Install target used during development:

```sh
~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMSmoother.plugin
```

## Verification

Generate the shared input image:

```sh
python3 refs/scripts/make_test_cellanim.py
```

Render the same AE comp on Windows and macOS, then place PNGs here:

- `refs/win/`
- `refs/mac/`

Run:

```sh
refs/scripts/diff_all.sh
```

`max=0` means byte-perfect for that frame.

## Status

See `notes/HANDOFF.md`.
