depends: F47b-native-plugin-host-render

# F47c: native `.plugin` host — SMART_PRE_RENDER / SMART_RENDER for OLMBlur (continuation)

## Facts
F47b (merged, `orchestra/reports/F47b-native-plugin-host-render.md`,
`tools/emulation/aexcompat_patches/F47b-native-host.{rs,md}`): the arm64 OLMBlur bundle runs its
setup and setdown selectors through the native C ABI. Params are captured, and AcquireSuite calls
are logged. Rendering is not implemented yet.

## Do (one goal: one OLMBlur Smart render, byte-compared with the AEX in the same host)
1. From F47b's AcquireSuite log plus the OLMBlur source, implement only the suites the Smart path
   needs: PF_SmartRenderCallbacks (checkout_layer_pixels, checkout_output, checkin), the
   world/pixel suites it uses, PF_WorldSuite / PF_PixelFormatSuite / PF_Iterate*, and
   handle/memory.
   - Back them with the Rust host state the emulated path uses: same worlds, same
     rowbytes/padding, same params.
2. Run SMART_PRE_RENDER then SMART_RENDER. Hash the output world exactly as the AEX session does.
3. Add `--candidate plugin-bundle` to `tools/fuzz/` with a minimal adapter for OLMBlur. Run seed 1
   n100 for both the AEX and the bundle in the same host. Classify every difference.
4. If time remains, do the same for ColorKey.

## Rules
- Use 1-2 processes. Check `memory_pressure` before the Rust build. Make no plugin source changes,
  and leave the default candidate unchanged.
- Report exactly which suites/functions are implemented, and which are stubbed and fail loudly.
