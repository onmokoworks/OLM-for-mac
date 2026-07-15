# OLMBlur PF16 current-HEAD build provenance

Date: 2026-07-16

## Verdict

Fresh no-install build succeeded from git HEAD. The candidate contains the
checked-out `rounded_i32` and `packed_low16` PF16 writer diagnostics and differs
from the supplied installed-binary SHA-256 reference. This is build provenance
only; no AE exact claim is made.

## FACT

- Git HEAD: `448e9f000e9b0e64582416d9b18f55d414b5068e`.
- Primary source: `mac/OLMBlur/OLMBlur.cpp`.
  - Source SHA-256: `d690adb9e6c4993caf50a16aed8d91b704f0a4622bc987601ddf630de4424346`.
  - Git blob OID: `4163ec5fb816575b35befc97085a292ee1f9fda4`.
- Input tree listing SHA-256 (sorted `mac/OLMBlur` file list): `9d7f6deaf33c9f7894dcf48917a3a6e0a979e0f145010fa4409c9e18700e0bc4`.
- Build command template:

  `xcodebuild -project mac/OLMBlur/Mac/OLMBlur.xcodeproj -scheme OLMBlur -configuration Debug -derivedDataPath "$TRANSIENT_DERIVED_DATA_DIR" build CODE_SIGNING_ALLOWED=NO`

- `xcodebuild` exit status: `0`; result: `** BUILD SUCCEEDED **`.
- The build used a transient system temporary directory for DerivedData and then removed it after hashing.
- Transcript SHA-256: `ba835660fe8ef85be534fa35f3b2cb19b98cb36c4c292a22b37b97b3e5c348ff`.
- Candidate bundle product: `OLMBlur.plugin`.
- Candidate binary bundle-relative path: `Contents/MacOS/OLMBlur`.
  - SHA-256: `bdf2fae1d913f295fbbb696e26e4c1894db25e09e600993b567738fbfa7f5793`.
  - Size: `176040` bytes; bundle disk usage: `184 KiB`.
  - Architecture: `arm64`.
  - UUID: `880AA676-F1B1-345E-B2B6-52D6B37B659F`.
- Bundle identifier: `com.adobe.AfterEffects.OLMBlur`.
- SDK metadata from the build settings: `MacOSX26.2.sdk`; minimum OS `26.2`.
- Binary string proof includes the exact writer diagnostic format with
  `rounded_i32=(%d,%d,%d)` and `packed_low16=(%u,%u,%u)`, plus
  `OLMBLUR_DEBUG_STORE16_BEGIN` and `OLMBLUR_DEBUG_STORE16_END`.
- Supplied installed-binary reference SHA-256:
  `c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206`.
  Fresh-build comparison: unequal.
- No-install audit:
  - The audited command was `xcodebuild` only.
  - DerivedData was created in a transient system temp directory.
  - No candidate copy or install operation was performed in this audit.
  - The transient build directory and transcript were removed after metadata and
    hashes were recorded.

## INFERENCE

- The candidate is a fresh current-HEAD OLMBlur build carrying the new PF16
  writer diagnostics, and its binary hash differs from the supplied
  installed-binary reference SHA-256.
- This evidence proves source/build/binary provenance only. It does not prove
  AE loading, AE runtime output, or AE exactness.

## Scope guard

No AE or Ghidra operation was run. The install-side comparison is hash-only and
does not assert a live install path or current host state. No tracked file
outside this JSON/Markdown report pair was edited.
