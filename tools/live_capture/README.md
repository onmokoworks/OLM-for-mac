# Live AE world capture (T22)

Build from the worktree root with `python3 tools/live_capture/build.py`. This
uses the Release settings in `scripts/build_all_mac_plugins.sh` (DG O2, Kira O3,
arm64+x86_64, minimum macOS 11.0), with SDK paths supplied in scratch. It does
not install a plugin. Products are in
`orchestra/state/T22-live-world-capture-dg-kirakira/build/`.

Create a writable directory and launch AE with `OLM_LIVE_CAPTURE_DIR` set to its
absolute path. The variable must be in **AE's process environment**, not merely
in a terminal opened after AE started. Each Classic/Smart render invocation
creates an exclusive `PLUGIN-route-XXXXXX/` directory. Unset/empty means no
capture allocation or I/O; the only overhead is getenv, null checks and a TLS
pointer check at parameter reads. Concurrent render calls use separate TLS
sessions and exclusive directories. No arithmetic is changed.

Each completed capture has:

- `input.raw`: input before staging or rendering, including every row's padding.
- `output_initial.raw`: AE's destination before rendering, including padding.
- `output.raw`: destination after rendering/copy-back, including padding.
- `capture.json`: schema 1, route, loaded binary path/SHA-256, compile stamp,
  host dimensions/downsample/time/field/origins/pixel aspect, request and output
  rectangles, world dimensions/stride/depth/origin/extent, parameters by public
  slot and type, floating color-suite values, active ramp payloads (all ramps
  read by Classic), and render error. Native ARGB little-endian words; PF16 is
  AE's 0..32768 scale, with no PNG conversion. Request rectangle is absent in
  Classic, which has no Smart output request. Shim-only fields unavailable to
  a legacy test host are null; a real AE build records them.

JSON is written last. Missing/invalid JSON means incomplete capture. Diagnostic
write/allocation errors go to stderr and never change the render error/output.
An early rejected render may leave an incomplete directory. Keep those as
failure evidence; the replay tool refuses them.

Replay:

```sh
python3 tools/live_capture/replay_aex.py /absolute/path/to/one/capture \
  --scratch "$PWD/orchestra/state/T22-live-world-capture-dg-kirakira/replay"
```

Default oracle is the retained `worker-F53-geom/aex-guest-worker`, loading the
original `plugins_2025/DistanceGradation.aex` or `OLMKiraKira.aex` from MAIN.
`--main` and `--worker` override these paths. For independent floating color-suite
values, use `--worker "$HOME/.cache/olm-emu/worker-S02-F53/aex-guest-worker"`.
The tool reuses the existing fuzz session protocol and process lifecycle helper.
It saves the command, framed worker messages, stderr and AEX output in scratch.

Exit codes: **0 exact, 1 mismatch, 2 unsupported/error**. Counts and first x/y/ARGB
channel are bit-exact sample-word comparisons. PF32 compares raw words even for
signed zero/NaNs; max numeric difference is null for differing nonfinite words.
Padding is preserved in captures but excluded from image comparisons: the
existing worker allocates its own padding contents. No tolerance is used.

## Transport boundary (do not silently normalize captures)

The retained worker supports full sampled inputs, downsample, request rectangles,
negotiated output, equal input/output padding (worker limit 256 bytes), content
extent and aspect. Replay checks the negotiated rectangle and guards/checksum.
It rejects cropped/nonzero-origin inputs, pre-effect source offsets, field renders,
unequal input/output padding, custom arbitrary ramps, and independent color-suite
values with a worker lacking the S02 capability. Arbitrary initial destination
contents cannot be injected by this worker; `output_initial.raw` is retained for
investigation. These restrictions are transport limitations, not plugin results.
The tool does not claim equality of memory padding or AE compositing/export.

## Verification

```sh
python3 tools/live_capture/self_test.py
python3 tools/live_capture/regression.py
```

Self-test uses saved fuzz-corpus active pixels and parameters, with a common
three-byte padded stride, through the existing standalone bundle host. It checks
both positive replay and an intentional one-byte output change. Results live in
`orchestra/state/T22-live-world-capture-dg-kirakira/self-test/results.json`.
Regression invokes existing corpus replay machinery with capture unset, serially.
