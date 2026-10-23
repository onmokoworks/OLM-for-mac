# Original noise-table out-of-bounds reads (C45)

The user-approved Mac contract returns **positive `0.0f` for each noise-table
read outside `[0, 101)`**. A valid interpolation endpoint is still read normally.
The allocation remains 101 floats (404 bytes); indices are neither clamped nor
wrapped at the lower bound. All unrelated admission guards remain in place.

| Plugin | Original read RVAs | Trigger |
|---|---|---|
| OLMDirectionalBlur | `0x37f3`, `0x37f8` | Negative normalized Noise Offset can produce a negative signed index after upper-only wrapping. |
| OLMRadialBlur | `0x95cd`, `0x95d8` | The noise generator likewise permits negative signed table indices. |

FACT: Prior C18/C25/C36 and C11/C44 investigations establish the invalid
allocation-relative reads. C45 does not reinterpret adjacent heap bytes as
part of the table or claim native Windows output is defined there. Its public
AEX comparisons use the default F46 Unicorn worker; final-output equality is
not a new memory-read trace.

The C45 report records seed 1 and two fresh n300 campaigns for each plugin.
Exact witnesses, with full parameters, input hashes and before/after provenance,
are `tests/fuzz_corpus/{olmdirectionalblur,radialblur}/C45_*.json`.

Non-comparable exceptions: **none recorded by C45**. No Smart output mismatch
was observed in those campaigns, so no mismatch is excused as a non-zero heap
read. Any future exception requires the actual out-of-range address, read RVA,
non-zero bytes, parameters and oracle identity; output disagreement alone is
insufficient evidence. Historical Classic-route discrepancies are separate
and are not classified as this original bug.

INFERENCE: Deterministic zero semantics remove allocator dependence in the
port. Passing finite emulation campaigns does not establish equality to every
native Windows heap layout or exhaustive parameter coverage.

## RadialBlur Type 3 with zero Noise Variation and no layer (C46)

The deterministic Mac contract initializes the **scatter span to positive
zero** when Noise Type is 3 and Noise Variation is zero (no layer checkout).
The size-factor plane remains separate: Zoom's B150 prepass uses its sampled
size factor when enabled, and literal one when disabled. Rotation likewise
retains its existing size-factor prepass. This is not a neutral procedural
noise substitution and does not change positive-amount layer checkout errors.

FACT: Original `FUN_1800065c0` skips the span writes when Type 3's layer
pointer at owner +0xA8 is null. `FUN_1800045a0` allocates handle storage without
explicit initialization. C17 established this allocation boundary. C46's F46
trace of the committed 7x1 PF8 fixture compares 4096-byte prefixes: polar and
scatter span match, but substituting the zero scatter span for the prepass
factor differs in 442/1024 floats (first AEX 1.0, candidate 0.0). Keeping the
size plane separately makes all three prefixes equal and the public output
exact. Prefix equality is not a claim of a complete intermediate-plane trace.

FACT: The independent C46 matrix's AEX-rendered cases and seed campaigns have
no admitted Smart mismatches with the final rule. Some Type-3 matrix inputs
make the original emulator stop with an invalid memory write; those are
uncompared, not evidence of exactness or a diagnosed non-zero allocation.
See `orchestra/reports/C46-radial-smart-r8.md` and its bound evidence.

INFERENCE: Zero initialization removes dependence on uninitialized allocation
contents, consistent with observed emulator values. Native Windows allocator
contents remain undefined; no native Windows/AE parity is claimed for this bug.

## DistanceGradation Smart large Median assertion (C56)

FACT: Original DistanceGradation Smart rendering raises `cv::Exception` at
`median_blur.simd.hpp:985`, with the assertion
`src.depth() == CV_8U && (cn == 1 || cn == 3 || cn == 4)`, for the retained
PF16 seed105 cases205 (24x27, Size3600) and296 (18x24, Size2237), and fresh
seed156 case51 (11x20, Size3416). The F46 worker reports a throw through
`0x181186c7f` rather than a successful Smart output. Complete parameters,
input identities and diagnostics are retained in `orchestra/reports/C56-evidence/`.
This is an original filter/type assertion, not evidence of undefined reads or
uninitialized memory. No deterministic replacement output is certified here.

INFERENCE: The original Smart render cannot complete normally for these
witnesses. In native AE, the underlying render would fail unless host/plugin
exception handling supplies another outcome; the emulator does not establish
whether AE displays an error, aborts a frame, or handles the exception another
way. No native AE UI/crash behavior is claimed. Mac output in this domain is
not labelled AEX exact. C56's Median optimization preserves the previous Mac
bytes and does not convert the original exception into an exact reference.

## RadialBlur Smart missing Layer (C57)

FACT: In the original Smart callback `0x40F0`, the context at `RSP+0x40`
receives no initialization of its Layer pointer at offset `0xA8`. Builder
`0x8690` reads that pointer at `0x88B6` and passes it to Layer getter `0xD9D0`.
That getter checks out the parameter and copies its 120-byte Layer descriptor
through the pointer (`0x19F20`), then checks the parameter in. The Smart callback
checks out input id 0 twice; it does not check out a separate noise pixel world.
This is an uninitialized stack pointer use, in addition to the uninitialized
span allocation described in C46. A literal null pointer is not a safe branch.

FACT: C57 captures of seed1/index248 and seed105/index158/214 bind to their
saved F46 public output hashes. Before and after the builder, the Layer pointer
is respectively `0x10000002c`, `0x100000016`, `0x100000001` (the packed width and
height of these one-row inputs). The getter copies an all-zero descriptor into
that address. The typed owner compares descriptor dimensions and clears the
pointer (`0x7910` PF8, `0x7100` PF16, `0x8120` PF32). It has allocated source,
output, size and scatter planes through `0x45A0`/HandleSuite without clearing
the scatter plane. Helpers `0x6830`/`0x65C0`/`0x6AA0` return on null Layer without
writing that plane. All 67 captured source scatter cells are positive zero
before and after the helper and renderer; the independent size plane is retained.
The full-plane captures are bound to unchanged public outputs, not PNGs.

INFERENCE: The pointer value is stale stack content; its valid mapping and the
zero allocation contents in the emulator do not establish native Windows/AE
behavior. Reproducing the invalid write or reading uninitialized C++ storage
would not define a deterministic port.

The deterministic Mac policy for a successful Smart checkout returning a
non-null, zero-width/zero-height descriptor with no pixel data reuses C46's
positive-zero scatter span and preserves the size/fade plane. Noise Variation
is unused by the original's skipped helper, so its effective render value is
zero in this state. Checkout/checkin remains balanced. True null descriptors,
nonzero-sized descriptors with missing data, checkout errors, and independent
nonempty Layer handling are not promoted by C57. See the C57 report for finite
oracle qualification and remaining native-host limitations.
