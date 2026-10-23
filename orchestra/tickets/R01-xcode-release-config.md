# R01: add Release configurations to the Mac Xcode projects (release blocker found by F47)

## Facts
F47 found that the production Xcode projects under `mac/*/Mac/*.xcodeproj` contain only a
**Debug** configuration. `tools/fuzz/build_F47_bundles.py` had to synthesise Release in
disposable copies: O2, x86_64+arm64, the original FP flags retained.

## Do
- Add a proper Release configuration to every plugin project. Use the same source files and
  preprocessor defines as Debug, with `-O2`. Keep `-ffp-contract=off` and `-fno-fast-math`
  (they are required for bit-exactness), ARCHS = x86_64 arm64, and the deployment target as in
  Debug. Leave code signing as it is, unset or ad hoc; the orchestrator will handle signing
  later.
- Build every plugin in Release with xcodebuild into scratch. Verify both slices with `lipo -info`.
- Check FP flag parity between Debug and Release: dump the effective `OTHER_CFLAGS` and
  `GCC_*` settings with `xcodebuild -showBuildSettings` and compare them.
- Check bit-exactness: for each plugin, run the existing public fuzz harness on seed 1 n100 with
  the Release flags. The source harness already uses `-O2 -ffp-contract=off`. Report any
  difference.
- Do not install into AE. Do not touch the release gate/ledger. Use 1-2 processes.
