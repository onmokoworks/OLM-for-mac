# OLMRadialBlur typed deep render (2026-07-18)

Status: `candidate6_internal_plane_exact_diagnostic`

The Mac production source now executes typed Zoom processing for PF16 and
PF32 instead of copying the input unchanged. PF8 keeps its existing path.

## Evidence

- Actual-AEX checkpoint: `480a7b012441b5863418835a8caf2fe16231dc8d7c59252fc05b69ec0407a909`
- Pinned AEX: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`
- Checkpoint RIP: `0x180005c9f`, immediately before in-place normalization
- Actual-AEX pre-blur plane: `31,795,200` bytes, `fc7b13739f081703137b771d51924e27219e34f93cc3b9ca7278fad4c46634ef`
- Production pre-blur plane: `31,795,200` bytes, `8e245bccbda1a856df3e079d4b49d81af256c844acee6557a1375ebebad11530`
- Production pre-blur differing bytes: `327,417`
- First pre-blur difference: byte `4,192`, float word `1,048`, angle `0`, radius `262`, channel `R`
- First pre-blur values/bits: production `0.24313725531101227` / `0x3e78f8f9`; oracle `0.24313727021217346` / `0x3e78f8fa`
- Mac worker from actual-AEX pre-blur: `31,795,200` bytes, `76669d0d85dd711e73ff130335a3667bc3bbc0799ac0116c2ac17320e35e81c0`
- Worker-only differing bytes: `12,744,511`
- First worker-only difference: byte `5`, float word `1`, angle `0`, radius `0`, channel `G`
- First worker-only values/bits: Mac `2.5326962749261384e-15` / `0x27368000`; oracle `0.0` / `0x00000000`
- AEX worker candidate-1: `31,795,200` bytes, `9a68c2f490aa62c156389e1682f8ac37d6b1d34d769cc8beadcd3941d3f0c4bb`
- Candidate-1 differing bytes: `5,779,701`
- First candidate difference: byte `4,768`, float word `1,192`, angle `0`, radius `298`, channel `R`
- First candidate values/bits: candidate `0.6571832299232483` / `0x3f283d29`; oracle `0.6571832895278931` / `0x3f283d2a`
- Candidate-2 with AEX-style table generation: `5,535,769` differing bytes, SHA `0095a814ddaae2f82a13bf98c02c79f2b8c8a67a7ba5837010d06b311e81e4fe`
- Candidate-2 first difference: angle `0`, radius `399`, `G`, candidate `0x3aa21e3b`, oracle `0x3aa21e3c`
- Candidate-3 with asm RGB multiply order: `5,533,669` differing bytes, SHA `5b911036e356ed2d17a47b4aa89ca59271b4106abf8c8f19899870a5d0284331`
- Candidate-3 improves candidate-2 by `2,100` bytes; first difference remains angle `0`, radius `399`, `G`
- AexLoader exact table: `FUN_18000b680(1717)`, `6,868` bytes, SHA `82d66d41ebba38e15638fd369acdf3a218a9160d39b0ad12a2aad482df8242d8`
- Candidate-4 with that raw table: `5,465,443` differing bytes, SHA `221d571e6ddaba753d982af61fe4d7e4d6b5d8be2ed61eb97c9fb5d078f4c6d5`
- Candidate-4 first difference: angle `0`, radius `961`, `R`, candidate `0x3dcc9f84`, oracle `0x3dccf017`
- Candidate-4 differing float words: `1,638,955` of `7,948,800`
- Channel counts: `R=563,315`, `G=537,689`, `B=537,907`, `A=44`
- ULP histogram: `1=34`, `2=11`, `3=2`, `4=0`, `>4=1,638,908`; max `1,022,593,211`
- Zero-vs-nonzero float words: `15,644`
- Checkpoint eligibility mask: `1,987,200` bytes, SHA `861d873df6a1e616f356fef86524e15580558591ea93945cd7ba8662ecdee2b7`, counts `0=565,113`, `1=1,422,087`
- Candidate-5 direction/mask diagnostic: `21,375` differing bytes, SHA `940d3d8c914111362674f7c49216dab1e59ce0e7dffef18e1934e7ee9004d79e`
- Candidate-5 first difference: angle `757`, radius `1096`, `A`, candidate `0x3f800000`, oracle `0x3f800001`
- Candidate-5 channel counts: `R=6,882`, `G=6,363`, `B=6,363`, `A=44`
- Checkpoint span plane `+0x40`: `7,948,800` bytes, 11 values, SHA `2af5c86165c5b96b4c686e05f9e4587b0b1b464efbd389803a9d623e69da9a1f`
- Checkpoint source scalar `+0x50`: `7,948,800` bytes, 4 values, SHA `13a5c887cd8c8c9a6a5380bf65ed8aacebc820d0751a0be81321053a596412ce`
- Candidate-6 scalar-plane diagnostic: `0` differing bytes
- Candidate-6 SHA: `c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8`, identical to the normalized actual-AEX oracle
- Actual-AEX normalized polar plane: `31,795,200` bytes, `c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8`
- Production normalized polar plane: `31,795,200` bytes, `64b237cd1e46d65aef300f94caf5bec1b45bfac9a2b9b945f86780f435e64cdd`
- Production polar differing bytes: `13,953,051`
- First polar difference: byte `6`, float word `1`, angle `0`, radius `0`, channel `G`
- First polar values/bits: production `2.609024107869118e-15` / `0x273c0000`; oracle `0.0` / `0x00000000`
- Actual-AEX complete PF32 frame: `7de7d9700fddce9f77261fe3e81db8b89ffc88a06c897b866ffe512392562010`
- Compared frame bytes: `33,177,600`
- Reconstructed final sampler differing bytes: `144,584`
- Production typed PF32 differing bytes: `10,047,226`
- Universal build: `x86_64 arm64`
- Clean universal production binary: `ccdc55c12330f1b09ca97fc50d47d1353bc357a9aaf5bd525b1ed3329dc3bddb`

PF16 uses the binary-grounded `1/32768` reader and multiply-by-`32768`
truncate writer. PF32 reads and writes native floats directly.

The PF32-only `OLM_RADIALBLUR_TEST_SEAM` entrypoint copies both pre-blur
`polar.rgba` and post-blur `blurred.rgba` from one `RenderZoomTyped` run into
caller-owned buffers. Both report geometry `1104x1800` and exactly
`31,795,200` bytes.

The actual-AEX pre-blur oracle is not the normalized oracle. It is extracted
from `work+0x38` in the identity-validated merged checkpoint at RIP
`0x180005c9f`, before normalization overwrites that buffer in place. The test
re-extracts the checkpoint bytes and requires byte equality with the oracle
file before comparing production output.

The relatively narrow pre-blur residual becomes `13,953,051` differing bytes
after blur. The post-blur hash and difference count exactly reproduce the
earlier single-plane run.

`BuildZoomBlurredPolar` now owns the production worker and normalization
implementation. Both `RenderZoomTyped` and the worker-only test entrypoint call
that same function; there is no duplicate comparison implementation. Feeding
the exact AEX pre-blur plane into this worker still leaves `12,744,511`
differing bytes against the normalized AEX oracle. This causally excludes the
Mac Cartesian-to-polar sampler as the sole or dominant explanation.

## Worker Candidates

The test-only AEX worker candidate implements the accepted B150 seed, a
barrier, outer-only A9D0 forward scatter with fixed source-radius and `k`
ordering, float32 multiply/add helpers, and final RGB/accumulated-alpha plus
max-alpha normalization. Angle rows are processed independently in parallel;
ordering within each row is fixed.

Using the existing `ZoomGaussianWeights(1717)` table, candidate-1 reduces the
worker-only residual from `12,744,511` to `5,779,701` bytes. The first residual
is one ULP. The original Mac double-generated table differs from the audited
AEX table in `688/1717` entries.

Candidate-2 uses the audited scalar sequence: float length, two `MULSS`, one
`ADDSS`, double `+1e-5`, float conversion, `DIVSS`, integer-square conversion,
`MULSS`, then `expf`. That sequence matches the loader oracle for all 1717
weights, but macOS `expf` itself leaves `13/1717` values different. Candidate-2
reduces the plane residual to `5,535,769` bytes.

Candidate-3 keeps the candidate-2 table and changes only RGB contribution
ordering to the asm-proven `(alpha * weight) * sourceRGB`. It improves another
`2,100` bytes to `5,533,669`. All candidates remain under
`OLM_RADIALBLUR_TEST_SEAM`.

Candidate-4 runs the pinned AEX itself through `AexLoader`, directly invokes
`FUN_18000b680(1717)`, and passes its raw 1717-float output file to the C++
probe. Extraction fails closed on AEX SHA, function, length, output byte size,
and output SHA. Candidate-4 calls the same candidate-3 worker with these
caller-owned exact weights, reducing the residual by `68,226` bytes.

Only `47` differing words are within four ULP, while `1,638,908` are greater
than four ULP. Alpha differs in just `44` words and almost all residual words
are RGB. This excludes weight generation and simple host rounding as the main
remaining cause; the live boundary is RGB seed/accumulation, source eligibility,
destination span, or ADDSS/store order. A clean normal build retains plug-in SHA
`ccdc55c12330f1b09ca97fc50d47d1353bc357a9aaf5bd525b1ed3329dc3bddb`.

## Candidate-5 Diagnostic

The identity-bound checkpoint stores the A9D0 source eligibility pointer at
`RBP-0x60`. Its `1,987,200` bytes are byte-identical to the pinned mask file.
All `565,113` mask-zero cells have nonzero pre-blur alpha, while no mask-one
cell has zero alpha, so this is an independent gate and cannot be represented
by the existing alpha condition. Mask zeros occur only at radii `540..1103`.

The caller audit maps state `+0x3ed8` to `outer_strength=1717` from
`param2+0x64`, and `+0x3edc` to `outer_offset=0` from `param2+0x68`.
Therefore case0009 disables the backward branch and uses the forward
`destination=source_ri+k` branch without wrapping. Normalization reads RGB and
denominator alpha from `param1[0x842]` and output alpha from the
`param1[0x843]` max plane.

Candidate-5 preserves the candidate-4 exact table and asm multiply order, then
adds the checkpoint mask as a source-cell-indexed gate. This reduces the full
plane residual from `5,465,443` to `21,375` bytes. It remains a diagnostic,
not a complete AEX worker reconstruction: exact B150 intermediate output,
independent scalar/denominator state, max plane, and barrier boundaries have
not yet been compared independently.

## Candidate-6 Exact Diagnostic

Candidate-6 additionally extracts and pins the caller slots `param1[8]`
(`+0x40` span) and `param1[10]` (`+0x50` source scalar). The source scalar has
exactly four bit patterns: `1.0` for `1,922,504` cells, `0x3f7fffff` for
`58,895`, `0x3f800001` for `5,108`, and `0x3f7ffffe` for `693`. The span plane
contains those major values plus seven edge values.

For the inner-zero case0009 path, candidate-6 seeds accumulated RGB with
`sourceRGB * source_scalar` and seeds accumulated alpha and max from that same
source scalar. A9D0 uses `limit=trunc(outer_strength*span)`,
`tableIndex=trunc(k*(1/span))`, `destination=source_ri+k`, the exact eligibility
gate, and `(source_scalar*weight)*sourceRGB` ordering.

The resulting `31,795,200`-byte plane is byte-identical to the actual-AEX
normalized oracle: differing bytes `0`, all channel counts `0`, SHA
`c8037b713512573f8b4346a5e0efc6dd1862f0a53da39d673b005f15a06469f8`.
This is a case0009 internal-plane diagnostic exact result, not Mac AE exactness
and not a production implementation.

## Limit

This is not AE exact. No Mac AE or Windows process was used. Rotation and
unsupported deep-color feature combinations are still copied. The next proof
boundary is to reproduce the eligibility and scalar planes locally from
production inputs and validate additional parameter families. Candidate-6
remains test-only until that generalization is proved.
No candidate is ready for production promotion.

Verification: `python3 tools/emulation/test_olmradialblur_typed_deep_render_20260718.py`
