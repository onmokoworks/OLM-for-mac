status: done
summary:
- Identified two original Smart defects: an uninitialized Layer destination pointer and an unwritten scatter-span allocation.
- Bound three complete missing-layer span/size captures to unchanged original public outputs.
- Added deterministic zero-span semantics only for successful Smart checkout of an empty descriptor; retained true-null/error refusals.
- Independent controls: 48 exact, 24 original execution failures, zero mismatches; nine invalid-host cases refuse atomically.
- Seed1/105/fresh57003: 823 Smart exact, zero admitted mismatches; 900 sanitizer checks; 580 prior hashes and 61 corpus outcomes preserved.

facts:

FACT: Base `8185488d110b8de03f876e93865f8f8ae276aa1b`, branch
`orch/C57-radial-missing-layer`. Read AGENT_GUIDE, GOTCHAS, C49/C53b reports,
the compatibility plan and Radial ledger restrictions. No MAIN, emulator source,
cache worker, other-plugin implementation, ledger, or release-gate changes.
No reference rebuild, push, stash, history rewrite, or delegation.

FACT: Oracles are the retained F46 worker
`6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`
and read-only C53b trace worker
`df51edc461ee13ae826c94e62b29c17b813181ef1c2719388e4d9faf180099a2`.
Both execute original AEX
`ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
`static_radialblur_C57.py` disassembled that exact PE with Capstone: 4287 lines,
including all three typed owners, span generators, allocation helpers, Smart
callback and Layer getter. This is original disassembly, not Mac source inference.

FACT: The brief's nullable noise-world description does not describe the
original Smart callback's actual Layer transport:

- Smart `40F0` obtains primary id 0 twice and output twice. Its local context
  begins at `RSP+40`; its Layer pointer at context+A8 is not initialized.
- Builder `8690` selects Type3 at `88B0`, reads that pointer at `88B6`, and calls
  `D9D0`. This getter obtains the Layer through parameter checkout, copies the
  120-byte descriptor through the supplied pointer via `19F20`, and checks the
  parameter in. There is no separate Smart noise-pixel checkout in this callback.
- Captures before/after the builder give Layer pointers `10000002c`, `100000016`,
  `100000001` for the three witnesses. All are unchanged by the builder; the
  descriptor copied through each pointer is entirely zero. These numerical
  pointer values equal packed input width/height for the one-row fixtures.
- Typed owners `7520` (PF8), `6D10` (PF16), `7D30` (PF32) dereference Layer
  dimensions without a preceding null test. Dimension mismatch clears the
  pointer at `7910`/`7100`/`8120`, respectively. A true null pointer is not an
  original safe path. No pixels are read from the zero-size descriptor.
- Before that check, owner allocation through `45A0`/HandleSuite reserves
  N*16 source and output bytes, N*4 size and scatter-span bytes, an N-byte mask
  and N*4 size scratch. `43C0` locks the allocations. Source/output and size
  receive explicit writes; the scatter span does not. `45A0` does not clear it.
- Helpers `6830`/`65C0`/`6AA0` test Type3 and the null internal pointer, then
  return without reading Noise Variation, size, or Layer pixels and without
  writing scatter span. The Zoom/Rotation renderer consumes the size and span
  allocations separately. The retained worker maps fresh handle memory;
  observed scatter bytes are zero, not an AEX initialization operation.

FACT: `probe_radialblur_C57.py --output .../trace-builder` exited 0: 39 captures,
no unhookable watches, dropped witnesses or trace truncation. All 67 source
scatter cells are positive zero both before/after the helper and before/after
the renderer. Full size planes are retained separately (seed105:158 includes
0, 1/3 and 1, so they are not the zero scatter plane). Renderer final planes and
raw public outputs are retained. The three final hashes equal C49's saved F46
hashes; the final O2 and ASan/UBSan public reproductions give 6/6 exact.

| Witness | Geometry/depth | Public output SHA256 |
|---|---|---|
|1:248|44x1 PF8|`ed315cec05c375f4c0f4c4de8a5a21ff20c510369ce3e99bdf361211ec7a4bb4`|
|105:158|22x1 PF32|`6219b098ea5b04ef9e47efe47ea33f1855add3bd6e0a9ab9d5521053dec5d8fd`|
|105:214|1x1 PF32|`f6bb1294da2f78cd935b01c7656280df5eaa0439e9d97bc03775825a41a508e4`|

FACT: The implementation recognizes only a successful Smart checkout of a
non-null descriptor with null data and both dimensions zero. It treats that
state as the existing C46 missing-Layer zero-span contract by setting the
otherwise-unused effective Noise Variation to zero after verifying the original
pre-render requirement. Type3, Size, Fade and all other controls are preserved.
Checkout ownership remains balanced; no source image or synthetic noise pixels
are substituted. True-null descriptors, nonzero-sized missing-data worlds and
checkout errors retain refusal. The public Radial-only harness now supplies an
empty descriptor for its documented None Layer fixture rather than error 710.
Classic and nonempty Layer implementation paths are unchanged.

FACT: `controls_radialblur_C57.py` independently generates 72 cases with seed
57057: 1x1/7x1/7x5, three depths, Zoom/Rotation, Noise 0/1/53.25/100, Size 67.5,
dual strength/fade/offset, Quality 1.25, typed random inputs and odd byte stride.
48 AEX completions match raw bytes exactly under ASan/UBSan. All 24 7x5 cases
stop in the original with `UC_ERR_WRITE_UNMAPPED`, with destination `500000007`.
They remain uncompared, not exact or Mac mismatches. No sanitizer diagnostics.

FACT: Null / nonempty-without-data / checkout-error controls on the three
witnesses give nine atomic refusals: six error516 noise-world, three error711
host failures, balanced callbacks, no sanitizer diagnostics. The first test
runner compared the status against the wrong spelling `refused` and exited1;
its retained results all said `refusal`. Corrected the test assertion and reran
all nine successfully (`invalid-host-recheck.log`). No production fix was
needed for this test-code error.

FACT: Smart qualification used jobs1, n300, no shrinking and a 10-second oracle
budget on the final production source:

| Seed | exact | mismatch | refusal | uncompared | candidate budget |
|---|---:|---:|---:|---:|---:|
|1|275|0|0|25|0|
|105|273|0|0|27|0|
|57003 (fresh)|275|0|2|22|1|

There are 823 fresh exact Smart comparisons and zero admitted mismatches.
All 580 previous C53b candidate hashes survive, including all 546 previously
exact rows. Newly exact former refusals are seed1:248 and seed105:158/214;
changes in original availability are not counted as admission gains.
Historical transport calibration remains 4/6, not newly relabeled exact.

FACT: All 900 sanitizer calls completed: 898 renders and two atomic refusals,
zero sanitizer diagnostics. 899 statuses/output hashes agree with the O2
campaign directly. Fresh57003:228 initially timed out after10 seconds on both
routes; the sanitizer render completed within its60-second budget. This caused
one strict replay status-comparison failure (budget -> ok), not a pixel mismatch.
An independent O2 retry completed in16.260390459 seconds with the identical
sanitizer hash `b918100fe6b749a8a4955e0a87471c6de5e5aeb12d8ec688ab7c68be11b37ab3`.
The original retry stopped in20.014781208 seconds at RIP `180002cc3` without
returning an output, despite the120-second transport allowance. It remains
uncompared. Original campaign and failed status-comparison reports are retained
unchanged; the audit requires the separately bound O2 retry for this transition.

FACT: Corpus replay completed61/61, exit1: Smart59 fresh exact plus two
uncompared originals (`C46_seed1_case000280`, `C49_seed1_case000117`). Both Mac
hashes still equal their saved successful originals. All61 candidate outputs/
refusal outcomes are preserved on both routes;59 whole-result rows match.
The replay uses each record's retained worker identity, including historical
offset/pow workers. Classic remains outside this promotion:1 exact,29 historical
mismatches,31 refusals, all unchanged. No corpus expectation was added, removed,
or relaxed. `audit_radialblur_C57.py` exits0 with complete preservation checks.

FACT: Complete reports, original traces, raw public witness outputs, static
instructions and logs are committed under `C57-evidence/` with an uncompressed
SHA256 manifest. Archive restoration and the restored-evidence audit pass.
All started processes exited; regenerable build directories were removed by
the reproducers. Scratch is approximately12MiB; the41-file compressed evidence is520KiB,
below5GiB. The report does not claim that an oracle
execution stop is a newly exact comparison.

FACT: Python syntax and `git diff --check` pass. The two-refuted-hypotheses stop
condition was not reached: the one zero-span semantic hypothesis agrees with
all observed completed originals, and the captures establish new boundaries.
No permission rejection occurred.

inference:

INFERENCE: The original's Layer destination is stale stack content. Its accidental
mapping in one-row emulator cases and fresh zero handle memory explain the
observed successful renders; they are not native Windows/AE guarantees. C57's
explicit empty-world/zero-span policy defines a deterministic Mac result for
this original bug and agrees with every measured original value. It does not
reproduce the invalid write or read uninitialized C++ storage. True-null host
behavior, arbitrary native allocator contents, and native AE qualification remain
undefined/unverified, rather than being labeled exact.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `notes/KNOWN_ORIGINAL_BUGS.md`
- `tools/emulation/radialblur_topology_effectmain_harness_20261001.cpp`
- `tools/emulation/{probe_radialblur_C57,static_radialblur_C57,archive_radialblur_C57}.py`
- `tools/fuzz/{verify_radialblur_C57,controls_radialblur_C57,audit_radialblur_C57}.py`
- `orchestra/reports/C57-evidence/*`
- `orchestra/reports/C57-radial-missing-layer.md`

verify:

Fast retained-evidence audit, then fresh public witness checks (no worker rebuild):

```sh
S="$PWD/orchestra/state/C57-radial-missing-layer/recheck"
python3 tools/emulation/archive_radialblur_C57.py --restore --state "$S"
python3 tools/fuzz/audit_radialblur_C57.py --state "$S"
python3 tools/fuzz/verify_radialblur_C57.py --witnesses --output "$S/new-witnesses" > "$S/new-witnesses.log" 2>&1
python3 tools/emulation/probe_radialblur_C57.py --output "$S/new-trace" > "$S/new-trace.log" 2>&1
git diff --check
```

Expected: manifest matches; audit asserts 900 sanitizer verifications (including the documented budget retry), all previous
candidate hashes and all 61 corpus outputs/outcomes preserved, zero mismatches;
6/6 public witnesses; three bound trace outputs, 39 captures.

Full reproduction, run sequentially with fresh output paths:

```sh
S="$PWD/orchestra/state/C57-radial-missing-layer/full-recheck"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
for seed in 1 105 57003; do
  python3 tools/fuzz/verify_radialblur_C57.py --seed "$seed" --output "$S/seed$seed" > "$S/seed$seed.log" 2>&1 || exit
  python3 tools/fuzz/verify_radialblur_C57.py --sanitize-campaign "$S/seed$seed/campaign.json" --output "$S/san$seed" > "$S/san$seed.log" 2>&1
done
python3 tools/fuzz/verify_radialblur_C57.py --retry-case 57003:228 --output "$S/retry57003-228" > "$S/retry57003-228.log" 2>&1
python3 tools/fuzz/verify_radialblur_C57.py --replay tests/fuzz_corpus/radialblur --output "$S/corpus" > "$S/corpus.log" 2>&1
python3 tools/fuzz/controls_radialblur_C57.py --output "$S/controls" > "$S/controls.log" 2>&1
python3 tools/fuzz/controls_radialblur_C57.py --invalid-host --output "$S/invalid-host" > "$S/invalid-host.log" 2>&1
python3 tools/fuzz/verify_radialblur_C57.py --witnesses --output "$S/witnesses" > "$S/witnesses.log" 2>&1
python3 tools/emulation/probe_radialblur_C57.py --output "$S/trace-builder" > "$S/trace-builder.log" 2>&1
python3 tools/fuzz/audit_radialblur_C57.py --state "$S"
```

Expect zero admitted mismatches and sanitizer failures, 48 exact/24 uncompared
independent controls, nine invalid-host refusals and all saved outputs preserved.
The sanitizer replay can exit1 when a previous 10-second candidate budget
becomes a successful 60-second render; the audit requires an independent O2
retry with the identical input, source and output hash before accepting that
status change. It does not waive numerical differences or sanitizer errors.
Oracle availability can change exact/uncompared counts; corpus exit1 on original
stops is not a numerical mismatch. Never count an unavailable oracle as fresh exact.
Original static evidence can be regenerated using MAIN's
`tools/emulation/.venv/bin/python tools/emulation/static_radialblur_C57.py --output "$S/static"`.

next:
- Native Windows/AE investigation of the uninitialized Smart Layer pointer and
  allocator contents is separate; do not emulate its invalid writes in the port.
- Fresh seed57003/index194 is an AEX-renderable refusal at the unchanged
  `RenderZoomTyped:generic-size-variation-topology` guard: PF32 nonfinite input,
  Size100, Noise Type1/amount0. Investigate in a separate nonfinite-topology
  ticket; the brief's "last non-oracle refusal" premise did not hold for this
  fresh campaign. Index87 hits the same guard but its original fails.
- Nonempty independent Layer, true-null checkout and original execution failures
  remain outside this promotion. No new numerical guess is required for the
  AEX-renderable empty-descriptor witnesses closed here.
