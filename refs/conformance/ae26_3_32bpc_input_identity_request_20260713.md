# AE 26.3 32bpc Input Identity Request

The request is now a bounded, standalone-executable capture package for
`OLMColorKey` case `olmcolorkey__case_0002`. It no longer claims entry-buffer
coverage for plugins that are not instrumented, and it no longer accepts
`OLM_PF_PIXELFLOAT_ENTRY_CAPTURE_COMMAND`.

## FACT

- The macOS source captures immediately after
  `checkout_layer_pixels(..., &input_world)` succeeds in `SmartRender`, before
  `checkout_output`, parameter checkout, or `RenderWorld`.
- The macOS gate requires `OLM_PF_PIXELFLOAT_ENTRY_CAPTURE=1`, the exact case
  ID, a 32-byte-or-longer same-run nonce, dump path, metadata path, and a
  runner-pinned executable SHA-256. It writes all `rowbytes * height` bytes and
  atomically publishes provenance last.
- The macOS instrumentation obtains its loaded executable path with `dladdr`.
  The helper resolves that path, requires it to equal the runner's exact binary
  path, hashes the file independently, and compares it with the pre-launch hash.
- The universal macOS Debug plugin builds successfully with Xcode.
- The 2025 Windows AEX SHA-256 is
  `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
- Disassembly of that binary shows the 32bpc dispatch call at VA
  `0x180001a14` targeting VA `0x180009960`, hence RVA `0x9960`.
- At RVA `0x9960`, the first instructions preserve the incoming arguments and
  `mov r15,r8` occurs at `0x1800099a6`. Subsequent instructions read width and
  height from `[r15+0x24]` and `[r15+0x28]`, proving that `R8` is the input
  `PF_EffectWorld*` at function entry. The SDK layout binds data at `+0x08` and
  rowbytes at `+0x10`.
- The generated Windows runner requires no pre-existing AfterFX process. Its
  ready marker carries the same-run nonce, case, fixture, and PID discovered
  from the marker-writing process. The runner requires that PID to be a fresh
  AfterFX process related to the `Start-Process` PID, in the caller's session,
  with the launch fixture present in the launcher command line.
- Module path/hash/base lookup is restricted to that bound PID. CDB is armed at
  `base+0x9960` and uses `.writemem` on `[R8+0x08]` for
  `dwo(R8+0x10) * dwo(R8+0x28)` bytes.
- The helper independently parses and compares the trace nonce, case, PID, AEX
  hash, RVA, input-world address, data address, rowbytes, width, and height.
- The package smoke rejects raw-only and legacy provenance, Windows wrong
  nonce/PID/hash/RVA/address/dimensions/process binding, and macOS wrong loaded
  executable hash. Every rejection verifies that no acceptance manifest remains.

## INFERENCE

- RVA `0x9960` is the earliest practical typed 32bpc AEX boundary available
  from the existing binary analysis: it is entered after the host/plugin setup
  path but before the float worker's first processing operation.
- The Windows CDB command is expected to capture the corresponding input world
  exactly because its pointer/register and field offsets are instruction- and
  SDK-layout-backed. It remains runtime-unconfirmed here because this workspace
  is macOS and has no PowerShell/CDB execution environment.

## Acceptance

The validator requires schema-3 instrument provenance bound to platform,
same-run nonce, AE PID, exact capture method/point, 64x64 dimensions, valid
rowbytes, and exact byte count. Windows additionally requires the pinned AEX
hash/RVA, parsed trace identity, and fresh launch relation. macOS requires the
run-pinned hash of the exact `dladdr` loaded executable. A raw-only,
contract-only, legacy external-command, short,
misaligned, wrong-case, wrong-process, or wrong-method return cannot produce an
accepted entry manifest.

The no-effect host render is copied to `source_input_00000.exr`; source,
no-effect, and effect-on EXRs are all present and SHA-256-bound in the return.
