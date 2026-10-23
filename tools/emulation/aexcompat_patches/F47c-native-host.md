# F47c native OLMBlur Smart bridge

This opt-in continuation uses the F47 cached Rust source without editing it.
`build_F47c.py` stages a disposable copy, adds the SDK-typed C++ bridge, and
patches `ClassicHost::render_smart`. No plug-in source is included in the host.
The separately built Universal bundle's arm64 `EffectMain` is loaded with
`dlopen` for each render; x86_64 execution is untested.

## Shared state and scope

The resident session still loads the original AEX for declarations, parameter
validation and world allocation. Both reference and candidate use the same Rust
worker binary. With `OLM_NATIVE_BUNDLE_EXECUTABLE` set, the Smart dispatch copies
that arena's `PF_InData`, all six parameter definitions, and input/output worlds
into native storage. Only pointers/callbacks and lifecycle handles are replaced.
The bundle runs GLOBAL_SETUP, PARAMS_SETUP, SEQUENCE_SETUP, SMART_PRE_RENDER,
SMART_RENDER and setdowns. Native declaration count/types are checked against
the AEX; F47b separately established setup metadata agreement. Native default
values are not used to overwrite the shared AEX parameter values.

Output bytes return to the arena and pass through the existing Rust session
checksum/report/write path. Native snapshots have 64-byte guards on each side;
input mutation and guard changes fail the render. The arena's output guards
remain independently checked. This is a bounded shared-arena bridge, **not** a
standalone native session host: AEX setup is still required; arbitrary/layer
parameters, persistent native sequence state, GPU and trace/census are excluded.

The fuzz adapter enables only Smart. The source candidate remains the default.
Both sides receive the same full-frame primary input with padding rounded up to
pixel alignment and filled with 0xA5 (the resident allocator rejects odd byte
strides). Output is packed on both sides. The generated `output_padding` field
is unused. Neither this campaign nor the bridge establishes independent output
padding, ROI, nonzero origins, AE or native Windows compatibility.

## Implemented functions

- `PF_InteractCallbacks`: add_param (count/type validation), checkout_param,
  checkin_param, abort, progress.
- `PF_PreRenderCallbacks`: checkout_layer for primary slot/ID 0, returning the
  actual shared world's extent and dimensions.
- `PF_SmartRenderCallbacks`: checkout_layer_pixels, checkout_output,
  checkin_layer_pixels for primary ID 0. Host-owned worlds live through selector
  return, matching the existing emulated scope cleanup.
- `SPBasicSuite`: AcquireSuite/ReleaseSuite for `PF World Suite`, version 2,
  with acquisition/release balance checking and stderr evidence.
- `PF_WorldSuite2`: GetPixelFormat for the two known worlds and all three depths.
- `PF_UtilCallbacks.copy`: full-frame, equal geometry, independent rowbytes,
  active-pixel bytes only; no rectangle or conversion support.

## Unsupported functions

WorldSuite2 NewWorld/DisposeWorld return 516 and mark the render failed.
Utility new_handle/lock_handle return null, handle_size returns zero, and
unlock_handle/dispose_handle log and mark failure. They are deliberately loud
stubs: the observed OLMBlur Smart route uses its own C++ memory allocation and
never requests host handles or temporary worlds.

PixelFormatSuite, Iterate8/16/Float suites, HandleSuite, WorldSuite1 and every
other suite fail AcquireSuite with `kSPSuiteNotFoundError`, a cleared pointer,
and a failure flag. They are not needed by the audited OLMBlur Smart path.
Unpopulated utility/optional callback table members are null, not callable error
stubs; using this bridge for another plugin is unsupported. This distinction
must not be mistaken for complete AE API coverage.

`verify_F47c.py` asserts one byte-exact padded-input anchor and checks that the
AEX route remains identical to cached F47. Fuzz results include actual native
selector and callback traces; a worker ignoring the native switch fails closed.
