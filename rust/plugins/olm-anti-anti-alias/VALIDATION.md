# OLM Anti Anti Alias — integrated 2026-11-12 release

## Current direct qualification (2026-11-13)

The final twelve-plug-in workspace candidate passes the **ordinary direct oracle**
using AEXCompat `032a187621353bac7b92a76ae394ac387ddedf51`. No bridge or sparse
fixture is used. Smart8/16/32, downsample 1, 1/2 and 1/4, fresh per-process
renders, at most three concurrent renders. Counts below are **per depth**.

| Reference | Smart8 | Smart16 | Smart32 |
| --- | ---: | ---: | ---: |
| New 64/2025 baseline | 226 exact | 226 exact | 224 exact + 2 session-open failures |
| New 64/2026 sample | 12 exact | 12 exact | 12 exact |
| New original-verified golden | 18 exact | 18 exact | 18 exact |

No pixel mismatch or timeout remains. Smart32 has two baseline session-open
`os error 80` failures, one reference and one candidate. Five fixed unchanged
repeats per side and case all succeed exactly; ubdetect reports
`inconclusive / no_mismatch`, with cleanup verified. These are not UB findings
and replay passes do not change baseline totals. See
[startup replays](../../evidence/integration-20261112/startup-replays.json). Inventory matches the 2025 original. Seeds 20261121/20261122 each supply 110
random plus default/min/max plans: **220 random plans per depth**, and scale totals
76/76/74. The shared upstream host now tolerates the redundant original checkin; the
bridge is no longer needed.

[Integration report](../../INTEGRATION.md),
[hash-bound qualification](../../evidence/integration-20261112/qualification.json),
[staged identity](../../evidence/integration-20261112/staged-identities.json) and
[golden verification](../../tools/golden/verification.json) are the current
authority. Native AE UI/project acceptance remains unverified. Prior job reports
below retain their original hashes and diagnostic observations as **history**;
their old bridge, harness-limit, pending-golden or local-only hoisting statements
are superseded by the direct evidence above.

---

# Job N-antialias validation — 2026-11-13

**Status: implementation delivered; direct-original host acceptance is blocked.**
The render algorithm and palette UI are implemented, and the labelled diagnostic
bridge comparisons below are exact. They are not promoted to direct original
AEXCompat passes. Native AE project round trips and macOS execution are unverified.

## Identity and declarations

| Artifact | SHA-256 |
| --- | --- |
| Original 64/2025 | `9ea6e2d85ab64ec6549653072a00e81315ae9c6791752a5ee634d2f599490cc0` |
| Original 64/2026 | `c0348e4d8351a71c9cca0420cfdfcbda151413c0a013818e2cc1ebf20f05ec4e` |
| Final Rust AEX | `50eb895baf749c06dfa7bf152e98e4f43c3879c3042220040992111c38e9b8e8` |
| Diagnostic bridge | `50ebed58fa2f6a1c684423bdf6cdab6d43d7f8042dc439e88d4f6dc31af5c080` |
| AEXCompat harness | `68a251fed8131d3a32cdcbd8797aba9959be417d8da68d1e80f44d087c75e9ba` |

The final artifact is `local/final-build/OLMAntiAntiAlias.aex`. Resource
`PIPL/16000/1033` is byte-identical to the original, SHA-256
`9ab79ea8d6a467649eca157cefcff39672e17a6266440b1680d4d15152d2c05d`.
All 107 non-input parameter declarations and exposed host inventory fields
match (`local/inventory-final`). Name: `OLM Anti Anti Alias`; match name:
`OLM OLM Anti Anti Alias`; category: `OLM Plug-ins`; version: 569344;
out_flags: 33554496; out_flags2: 134222848. Declared CPU routes are Smart8/16/32.
No unsupported classic route was forced.

`inventory.json`, `declarations.json`, `scaffold.json` and `resources/` retain
initial capture provenance. The scaffold's historical TODO text is superseded
by this document. Runtime has no arbitrary-data or sequence-data implementation
because the original palette is stored in ordinary parameter streams.

## Why the direct oracle does not pass

The original render takes this callback sequence:

1. checkout slot 1, check it in successfully;
2. checkout slot 2, check it in successfully;
3. check the same parameter address in a second time, with no live checkout.

AEXCompat returns error 4 on step 3; the original propagates it. The trace-only
proxy preserves this failure. With exactly that first unmatched checkin after
slot 2 suppressed, the original completes. The two traces and process records
are under `../../tools/autoport/local/n-antialias/{trace-0,trace-1,proxy-process-0,proxy-process-1}.json`.
The original is loaded from its existing location and never copied or modified.
The bridge changes no world, palette or arithmetic operation. Native AE's
behavior on the redundant callback was not measured, so the bridge is an
explicit compatibility hypothesis, not an assertion about AE.

Direct 2025 baseline: **0 exact, 12 reference failures per depth** (36 total),
with all candidate renders successful. Direct 2026 against the final build:
**0 exact, 6 reference failures per depth** (18 total). These are failures,
not pixel mismatches or passing exclusions.

`ubdetect classify` on a direct failed Smart8 case, three repeats per side,
returned **inconclusive / incomplete_evidence**: 0 successful original renders,
3 stable candidate renders; owned-process cleanup verified. This is not evidence
of original undefined-memory reads and is not labelled `original_ub`.

## Final diagnostic render comparison

All rows below use the final Rust AEX and the original 2025 through the bridge.
Seeds are 20261113 and 20261114; each has 103 plans: default/min/max plus 100
random parameter plans. Sizes: 1×1, 3×7, 11×7, 31×19. Per seed, downsample
1, 1/2, 1/4 receive 35/34/34 cases respectively; random subsets are 34/33/33.
Runs use the oracle's per-process mode, at most three concurrent renders.
Every output sample is compared exactly; float comparison uses bit patterns.

| Route | Baseline planned | Baseline exact | Pixel mismatches | Reference session-open failures | Unchanged exact replays |
| --- | ---: | ---: | ---: | ---: | ---: |
| Smart8 | 206 | 206 | 0 | 0 | 0 |
| Smart16 | 206 | 204 | 0 | 2 | 2 |
| Smart32 | 206 | 206 | 0 | 0 | 0 |

Smart16 seed 20261113 cases 16 and 87 failed before rendering with
`session open failed ... os error 80` (file already exists). Replaying those
hash-bound cases unchanged succeeded exactly. The baseline summaries and their
nonzero campaign exit code are retained; replays do not rewrite those totals.
Across successful baseline/replay coverage, **200 distinct random plans per
depth over two seeds** have exact output. This remains bridge-qualified evidence.

Artifacts: `local/final-campaign/{provenance.json,campaign.json,seed-20261113,seed-20261114}`
and `local/replay-final-{16,87}`. The provenance separately binds the original
loaded by the forwarding bridge; the standard oracle manifest only names the
bridge itself. Both enclosing campaign job trees report verified cleanup.

Additional final-build cases (`local/supplemental-02`) cover opaque plateaus,
anti-aliased boundaries, alpha 0/1/127/128/254/255, empty/automatic palettes,
real color hits and duplicate colors: **12/12 exact per depth**, all scales.
An earlier supplemental run used low-valued palette channels; it also matched,
but is kept separately rather than substituted for the intended full-color cases.

The 2026 binary is not byte-identical to 2025 (`.text`, `.rdata`, `.pdata` and
resources differ). A distinct seed-20261115 diagnostic corpus matched the Rust
build in **18/18 cases per depth**, all three scales (`local/bridged-2026`).
This establishes equality on that corpus, not complete 2025/2026 equivalence.
That comparison used build-06; final changes since build-06 were formatting,
removal of an unused scaffold helper, and an opt-in witness module.

Earlier exploratory 12-case bridge runs had one mismatch per depth with the
first projection translation. Native witnesses located duplicate-endpoint NaN
and score addition-order errors. The corrected helper removed those mismatches.
Earlier larger build-05/build-06 campaigns also matched 106 cases per seed per
depth, but are not added to the final-build totals above.

## Function recovery and verification

Ghidra imported 152 internal functions and 31 externals into an isolated project
on port 8774. `funcdb` reported 88 exact, 6 fuzzy and 58 unknown functions, with
33 decompiler-listing fallbacks. None of its candidates had an admitted verified
Rust mapping; many exact hits were runtime/vector boilerplate. No unproved
shared-kernel substitution was made.

| Native RVA | Production translation | Native verification |
| --- | --- | --- |
| 0x1680 | generated 16-bit palette membership | 512 vectors, exact |
| 0x1740 | generated 8-bit palette membership | 512 vectors, exact |
| 0xa630 | generated 10-argument RGB projection and pair score | 1,024 vectors, exact on final build |
| 0x4d40 / 0x4830 / 0x5230 | manual plateau detector, with witness-only ABI adapters | 256 vectors per depth, exact |
| 0xa630 during actual Smart32 rendering | original debugger record, replay into original and production Rust | 8 calls; all nine buffers and return bits exact |
| Remaining classification/neighborhood/alpha image passes | manual translation | integrated render corpus above; not individually native-witness qualified |

Detection vectors exercise edges, opacity, excluded colors, previously appended
colors, row padding, writes and no-writes. The comparison includes the native
vector count, pointer relationships, untouched capacity and surrounding guards.
Projection vectors include coincident endpoints, points at endpoints and
midpoints, and finite random colors; duplicate endpoints exercise NaN behavior.
`replay_projection.py` uses record's alias-preserving contracts and diverge's
bitwise element comparison. Scope is the mapped projection call, not every
stage of the renderer. Raw manifests verify every witness worker was cleaned up.

Three generated functions are used by `algorithm.rs`; no original binary is
loaded by the production DLL. Intermediate accumulation order, float widths,
CVTT/narrowing and unordered comparisons are preserved. The only non-basic
numeric operation is hardware square root; there are no UCRT transcendental
calls, platform libm substitutions, fast-math or `mul_add` operations.

Autoport used **7 Codex calls of the 80-call budget**: four for two leaf functions
(two attempts each), three for the projection. Leaf attempt time was 64.313 s;
projection generation time was 112.781 s. The initial empty corpus was rejected
with zero Codex calls. Manual work recovered host/pointer contracts, vector
layouts, plateau detection, three image passes and all UI/SmartFX wiring. The
autoport graph remained `needs_human`; no full automatic plug-in port is claimed.
Details: [tool report](../../tools/autoport/N_ANTIALIAS.md).

## Detection triggers and saved state

This conclusion is grounded in both EN/JP manuals and native selectors:
entry 0x8600 dispatches USER_CHANGED_PARAM to 0x6be0, UPDATE_PARAMS_UI to
0x69d0, SMART_RENDER to 0x6380. The clear helper is 0x5b00, visibility 0x6710.

- Slot 2's checkbox adds temporary render-time detected colors (limit 9,999).
  It does not write parameter streams or sequence data.
- Slots 3/4/5 are supervised PF_Param_BUTTON controls, with Init/Add/Clear labels.
  Slot 3's display typo `Initalize colors` is intentionally unchanged.
- Init/Add use AEGP PF Interface, full-resolution upstream Layer Render Options,
  a checked-out frame and the same depth-specific plateau detector. They write
  the count/color streams with AEGP Stream Suite 8 (AEGP_StreamSuite3).
- Clear writes four zero channels to all 100 colors, keeping the count. Init
  clears first, then fills from slot 7. Add keeps active nonblack entries and
  one active black; duplicate black and inactive slots are available for new
  colors. Count only increases to the preserved-plus-detected count.
- Count is disk/slot 1; colors are 7–106. These are the persistent project values.
  UPDATE_PARAMS_UI hides color streams at indices beyond the active count.

Rust tests simulate those actual AEGP suite callbacks and verify stream edits,
visibility, count preservation and balanced resource release on a failed edit.
That is not a native project save/load/Undo test. Parameter schema compatibility
is measured; saved-project behavior in AE remains an acceptance gap.

## Build, tests, ownership and remaining work

- Isolated offline Windows release build: passed, no warnings.
- Rust tests: **10 passed, 0 ignored** (`local/test-final`). Includes checked
  spans, nonzero-origin copy/crop and padding at all depths, palette insertion,
  temporary automatic palette, alpha cutoff and mocked suite lifetime tests.
- Autoport tests: **23 passed** (existing suite plus three new regression tests).
- Python helper syntax compilation: passed. Mac staging script was not executed.
- macOS build metadata includes both CPU entry declarations and
  PluginDataEntryFunction2. `stage_macos.py` provides isolated universal staging;
  both architecture builds, ARM NaN behavior and native Mac rendering remain
  unverified on this Windows host. No claim of a working Mac binary is made.
- Whole-image HDR/nonfinite input, cropped/tiled native-host neighborhoods and
  every manual image pass's individual witness remain unqualified. The tested
  PNG render corpus is bounded to ordinary 0–1 channel input.
- Direct original-host qualification needs a reviewed host compatibility fix
  or native AE evidence for duplicate checkin semantics. Do not silently relax
  unrelated host lifetime checks. Two session-name collisions also need host
  investigation; their successful replays are retained separately.
- No AE/GUI, installation, Git operation, commit, remote action or sub-agent was
  used. No original was copied or modified. Only the two assigned directories
  were edited; all Cargo artifacts used `D:/olm-rs-target/N-antialias`.
- Owned Ghidra PID **53256**, port **8774**, was stopped gracefully. Owned PIDs
  6748, 50764, 53256 and 53148 exited; remaining list empty; subsequent status
  reported `running:false` and PID 53256 was absent. The pre-existing shared hub
  was left untouched. All build/witness/record/campaign processes completed.

## Reproduction

Build/test instructions are in [README.md](README.md). From the repository root:

```powershell
python rust/plugins/olm-anti-anti-alias/witness_projection.py --candidate rust/plugins/olm-anti-anti-alias/local/final-build/OLMAntiAntiAlias.aex --out rust/plugins/olm-anti-anti-alias/local/new-projection
python rust/plugins/olm-anti-anti-alias/build_local.py --features witness --out rust/plugins/olm-anti-anti-alias/local/new-witness-build
python rust/plugins/olm-anti-anti-alias/witness_detection.py --candidate rust/plugins/olm-anti-anti-alias/local/new-witness-build/OLMAntiAntiAlias.aex --out rust/plugins/olm-anti-anti-alias/local/new-detection
python -m unittest discover -s rust/tools/autoport -p 'test_*.py' -v
```

`campaign.py --candidate PATH --original ORIGINAL_2025 --reference BRIDGE --out NEW`
runs the two-seed bridge campaign and records both identities and process cleanup.
`supplemental.py` accepts the same arguments for plateau/edge cases.
`record_bridge.py` plus the saved projection profile/request captures native
calls; `replay_projection.py --capture DIR --candidate PATH --out NEW` replays them.
Build a fresh bridge with `python rust/tools/autoport/build_reference_proxy.py --pipl rust/plugins/olm-anti-anti-alias/resources/pipl-0.bin --out rust/tools/autoport/local/new-bridge`. The helper writes a standalone crate, records input identities and verifies owned build-process cleanup.
Local binary/build artifacts are ignored; no third-party AEX is included.

Compact identities, source hashes and result totals are retained in
[validation-evidence.json](validation-evidence.json); raw failure/success records
remain under the local paths above. No original-host failure is counted as exact.
