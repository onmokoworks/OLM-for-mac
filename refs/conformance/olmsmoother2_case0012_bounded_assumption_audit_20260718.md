# OLMSmoother2 case0012 bounded assumption hard audit - 2026-07-18

- Verdict: `FAIL_CLOSED_BOUNDED_ACTUAL_AEX_NOT_LIVE_PIXEL_COMPARABLE`
- AE exact: `false`
- Full accepted Windows live case reproduced: `false`

## Answer: 0.8575 vs 233

The bounded result is cce0 float4 `[0.8575195670127869, 0.8575195670127869, 0.8575195670127869, 0.9387068152427673]`. The accepted Windows image pixel is final PF8 `[233, 233, 233, 237]`.

They are not legitimately comparable yet. They share a case id and coordinate, but not a proved semantic stage. The bounded runner directly calls cce0 with reconstructed state and never executes the natural worker-to-writer bridge. Therefore even the naive conversion shown in JSON is diagnostic only and is not evidence of either agreement or disagreement.

The retained first-vertex records are not a valid weight comparison: Windows `0x3e91a7b9` is captured at raw `f270` return, while bounded `0x3e25bedb` is a post-dispatch polygon weight. The recorded RGB word delta `[-3, -3, -3, 0]` remains diagnostic only.

## Assumption Inventory

| Boundary | Classification | AEX executes | Windows-live equivalent |
| --- | --- | --- | --- |
| `parameter_context` | `fixture-grounded/manual-runtime-struct` | no | no |
| `crop_translation` | `synthetic-coordinate-translation` | no | no |
| `host_input` | `export-grounded-translated-adapter` | no | no |
| `class_plane` | `actual-aex-bounded/three-live-bytes-only` | yes | no |
| `dispatcher` | `actual-aex-dispatch/direct-cce0-entry` | yes | no |
| `second_vertex` | `actual-aex-local-continuation/windows-live-unobserved` | yes | no |
| `cce0_config` | `manual-struct-reconstruction` | yes | no |
| `writer` | `absent` | no | no |

## Detailed Boundaries

### parameter_context

- Grounded: The manifest pins the case id, 1920x1080 comp, Software renderer, and visible AE parameter values.; The bounded runner rejects drift in the principal visible parameters.
- Synthetic/manual: The runner manually writes selected fields at render_config +0x00/+0x20/+0x28/+0x30/+0x38/+0x40.; Unwritten config bytes are zeroed and the sixth cce0 argument is manually set to zero.; The retained Windows weight is captured at f270 return while the bounded snapshot is after dispatcher normalization; those weights are not a same-stage comparison.
- Missing proof: Same-run Windows dump of the complete cce0 config and sixth argument at the accepted pixel.

### crop_translation

- Grounded: Local descriptor plus the hard-coded crop origin arithmetically equals the accepted host descriptor.
- Synthetic/manual: A 16x16 image replaces the accepted 1920x1080 plane.; Host coordinates are recovered by adding the manually selected origin (84,833).
- Missing proof: Proof that full-frame worker/scan state and all reachable neighborhoods are invariant under this crop.

### host_input

- Grounded: The integer PF8 premultiply rule matches all 256 before-effects bytes in the crop.; The first retained source sample agrees structurally with the accepted first vertex.
- Synthetic/manual: AE host checkout and PF8-to-float conversion are replaced by Python/PIL plus an integer adapter.; The retained post-sRGB sample differs by 3 float32 ULPs. Independent pow-boundary audit shows Mac libm and a high-precision oracle agree, and forcing the retained word does not change class, descriptor, weight, or cce0 output for this witness.
- Missing proof: Same-run Windows post-host/post-sRGB float plane for the complete dependency neighborhood.

### class_plane

- Grounded: Actual AEX ada0/ac00/ae10 produces the bounded class plane.; Accepted center, previous, and left class bytes are available; the runner asserts center and previous.
- Synthetic/manual: The remaining bounded class plane is generated from translated crop input, not captured from the live Windows run.
- Missing proof: Same-run Windows class-plane dependency region or a proof that the three retained pixels are sufficient.

### dispatcher

- Grounded: Actual AEX cce0 calls c280/fef0 and selects key 20 from the generated descriptor.; The accepted Windows run proves descriptor, e170 c=7, and the first f270 append.
- Synthetic/manual: The bounded runner enters cce0 directly instead of reaching it through the full-frame AE worker/caller.; The bounded first-vertex snapshot is downstream of f270/dispatcher normalization, so its weight cannot be compared to the accepted raw f270-return weight.
- Missing proof: Same-run Windows or full-frame actual-AEX proof of the cce0 call arguments and dispatch continuation.

### second_vertex

- Grounded: Actual AEX f130/e290 appends a second vertex in the bounded execution.
- Synthetic/manual: Windows live evidence ends after f270 with vertex_count=1; it contains no f130/e290 return or post-f130 polygon.
- Missing proof: Same-run Windows post-f130 polygon including the second vertex float32 words and weight.

### cce0_config

- Grounded: Known manifest values are placed into offsets inferred from AEX/decomp and existing local oracles.
- Synthetic/manual: The config allocation is manually zero-filled and populated field by field.; The gamma mode byte 3 is a reconstructed mapping from UI value 2 (Gamma Colors), not a same-run config capture.
- Missing proof: Accepted Windows cce0 config bytes/pointers and caller argument values from the same run.

### writer

- Grounded: none
- Synthetic/manual: The runner stops at the cce0 float output buffer.; No full worker return, writer call, output color transform, clamp, premultiply, or PF8 pack executes.
- Missing proof: Natural continuation from this exact cce0 result through the accepted Windows writer to the final PF8 byte.

## Fail-Closed Rule

- Executing actual AEX instructions does not prove that manually supplied caller state equals the accepted live state.
- A crop-translated descriptor match does not prove full-frame equivalence.
- An internal float may not be compared to an exported PF8 byte without a proved same-chain writer bridge.
- Any future live-pixel comparison requires every required boundary to have windows_live_equivalence_proved=true.

## Next Evidence

- Same-run Windows post-f130 polygon capture for the accepted descriptor, including the second vertex.
- Same-run Windows cce0 config bytes, arguments, input polygon, and returned float4.
- Same-run natural continuation from cce0 return through the actual PF8 writer for pixel (92,841).

## Reproduction

```sh
python3 tools/emulation/audit_olmsmoother2_case0012_bounded_assumptions_20260718.py
```
