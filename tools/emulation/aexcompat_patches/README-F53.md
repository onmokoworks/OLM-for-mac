# F53 cropped input checkout

This patch applies only to the cached F52c source; it does not modify AEXCompat
or the default fuzz worker. Build with `python3 tools/emulation/aexcompat_patches/build_F53.py`,
then `--register`; `--verify-source` binds the patch, source manifest and binary.
Build the independent candidate bundle host with `build_F53_bundle.py`.

The new checkout path is used with `--negotiate-output 1` (the adapters supply it).
`--checkout-rect left,top,right,bottom` accepts packed pixels for that rectangle,
in sampled layer coordinates. Full layer dimensions and downsample remain
independent. `--checkout-rect auto` accepts the full sampled payload and makes
Smart checkout views from each PreRender request intersected with the layer.
Candidate hosts use the equivalent `OLM_F53_CHECKOUT=auto` or
`OLM_F53_CHECKOUT=l,t,r,b` environment option.
The v2 adapter selects `auto` when its case has no explicit `checkout_rect`.
Omitting the option entirely preserves F52c behavior, including its full input
world. This opt-in default reconciles automatic checkout with legacy replay.
Explicit rectangles describe supplied availability (possibly extra pixels).
Empty explicit payload rectangles are rejected; auto intersections can be empty.

SDK grounding (MAIN read-only `Headers/AE_Effect.h`):

- 1559–1560: world origin is the buffer origin in layer coordinates for Smart checkouts.
- 2402–2404: PreRender actual output and maximum possible output are distinct;
  maximum must not depend on the requested output size.
- 2416–2422: checkout result is actual availability, maximum is full-request
  availability, PAR is separate, reference width/height exclude downsample.
- 2431–2437 and 2465–2470: checkout ID connects the PreRender request with the
  SmartRender world returned through `checkout_layer_pixels`.
- 3023–3024: `output_origin` is input buffer origin in output buffer coordinates.

Inference/host policy: a rectangular dense layer has maximum `[0,0,sampled_w,
sampled_h]`; its automatic availability is request intersect layer. The SDK
comments establish coordinates and bounds but do not prove all AE scheduling,
extra-pixel or sparse-layer policies. This harness does not claim that proof.
Auto views preserve parent row stride. Explicit worlds use width-derived stride
plus padding. World extents are local to the available buffer; layer metadata
stays separate. No plugin algorithm is changed.

`python3 tools/fuzz/verify_F53.py` records DirectionalBlur and Smoother2 explicit,
automatic and offset witnesses. `--survey --n 100 --jobs 1 --label survey-auto` measures seed 1
for all ten source hosts, sequentially. Per-case oracle stderr, statuses, raw
hashes, first mismatches and refusal traces are committed as evidence. A host
reject or emulator budget is not labeled an original plugin refusal.

The final realistic-v2 generator preserves v1 pixels, parameters, and RNG draws;
its changed host policy crops the Smart input to actual PreRender requests.
The source payload remains full sampled storage in auto mode. Explicit witnesses
instead supply only the packed checkout pixels. Neither mode resamples pixels.
The all-plugin survey uses Smart for nine plugins and Classic for OLMSmoother,
whose original adapter has no supported Smart render route. Existing v1 bundle
qualification is unchanged. P00b bundle smoke results retain the pre-existing
ColorKeep iterate callback limitation as harness errors, not plugin refusals.
