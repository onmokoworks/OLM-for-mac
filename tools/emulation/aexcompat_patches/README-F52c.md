# F52c negotiated geometry hosts

F52c adds `--negotiate-output 1` to the retained F52 oracle options. Without it,
output allocation remains the F52 policy; the default worker is unchanged.
The option is enabled by `tools/fuzz/run.py --geometry realistic` for qualified
source and bundle adapters. Explicit `--worker` still wins. Bundle geometry uses
the separate `worker-F52c-bundle/plugin-host`, not the Rust native-plugin bridge.

The input file contains packed sampled pixels; no resampling is performed.
Input allocation has exactly the requested byte padding. Full layer dimensions,
rational downsample, pixel aspect and extent are forwarded. Smart checkout
metadata reports full reference dimensions and pixel aspect. After successful
PreRender, the output allocation follows **result_rect**, including its origin;
max_result_rect is a bound, not an instruction to allocate a union. Output rows
have the requested padding; raw output files contain active pixels only.
Session `frame_done.output.rect` records layer-coordinate bounds. Comparisons
require both that rectangle and sample bytes to match. Empty results skip the
render selector. The existing 1920x1080 output cap is retained; invalid/excessive
bounds are host errors, never reported as faithful original PF errors.

SDK basis (read-only MAIN `Headers/AE_Effect.h`):

- 2374–2412: request rectangle, result/max rectangles and RETURNS_EXTRA_PIXELS.
- 2415–2426: checkout aspect and original layer reference dimensions.
- 1539–1560: world dimensions, byte row stride, extent, aspect, world origin.
- 2945–2950 and 3023–3024: input-buffer origin relative to output buffer.
- 2951–2961: full layer/sample distinction and scalar downsample factors.

See also the [SmartFX SDK guide](https://ae-plugins.docsforadobe.dev/smartfx/smartfx/),
particularly Rectangles and The Size Of A Layer. This implementation is a
bounded fake-host contract, not a trace establishing native AE allocation.
Classic has no Smart request: adapters forward extent/aspect/downsample/padding
but omit `--request-rect` for Classic. The worker still rejects explicit Classic
region requests, preserving the old interface. Smoother realistic campaigns are
Classic only. ColorKey/DirectionalBlur were not qualified in this ticket.

Build and binding verification (one job, >=30% free memory, space-free cache):

```sh
python3 tools/emulation/aexcompat_patches/build_F52c.py
python3 tools/emulation/aexcompat_patches/build_F52c.py --register
python3 tools/emulation/aexcompat_patches/build_F52c.py --verify-source
python3 tools/emulation/aexcompat_patches/build_F52c_bundle.py
```

Build scripts refuse to overwrite durable binaries by default. The bundle build
accepts `--refresh`, preserving its previous hash-bound binary/manifest in cache
history before updating only its own INDEX entry. Reproduction on a fresh
cache uses hash-bound `src-F52/reference-guest` and the committed patch. Source
and binary manifests are registered under `~/.cache/olm-emu/INDEX.json`; neither
MAIN nor `04_Tools/AEXCompat*` is edited. The synthetic Windows PE test is built
with clang plus Rust's bundled LLD; it tests allocation, not OLM algorithms.

```sh
python3 tools/fuzz/verify_F52c_host.py
python3 tools/fuzz/verify_F52c_guest.py
python3 tools/fuzz/verify_F52c_bundle_empty.py
python3 tools/fuzz/validate_F52c.py
python3 tools/fuzz/qualify_F52c.py
python3 tools/fuzz/qualify_F52c_bundle.py
python3 tools/fuzz/measure_F52c.py --plugin olmblur --geometry realistic --jobs 1 --n 100
```

Source shims are extended in scratch copies only. The source and standalone
bundle hosts share `harnesses/geometry.hpp`; their input/output wrappers are
inactive without the explicit geometry environment. The F47d bridge changes
are compiled only by the new F52c standalone transport. Cached A01 bundles are
used as-is, with their hashes recorded; they predate P01a and need not have the
same refusals as current source. Bundle host is Universal; qualification here
executes its native arm64 slice only.
