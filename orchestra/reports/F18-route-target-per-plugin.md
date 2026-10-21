status: partial

summary:
- Original Windows 2025 AEX resources and executed GLOBAL_SETUP select Smart for nine plugins; Smoother v1 alone selects Classic.
- All ten original PiPL flag pairs agree with their emulated runtime pairs. Fresh Universal Mac resources agree with both Mac runtime slices.
- Two Mac/original compatibility bugs are measured: Smoother v1 adds Smart Render; ColorKey changes four other capability bits.
- Baseline audit is complete; the separately committed flag correction and its verification follow.

facts:

Base: `cbb2d255`, branch `orch/F18-route-target-per-plugin`. Read `AGENT_GUIDE.md`, the plan's Windows-2025/CPU route contract, GOTCHAS, F17, and the ten plugin rows of the ledger decision matrix. MAIN, reference AEX, and SDK were read-only. No reference workers were rebuilt. No installation, AE launch, release gate, ledger, numerical algorithm, or fuzz oracle/corpus change.

`tools/emulation/audit_route_flags_F18.py --report reports/route_flags_F18_before.json`, run with MAIN's emulation Python and ticket-local TMPDIR, completed: **10 plugins, 8 exact Mac/original flag pairs, 9 original Smart routes**. Full absolute AEX paths, SHA256s, original exported addresses, raw resource bytes, property offsets, source/binary/resource hashes, build commands, callback transcripts, and decoded flags are committed in that JSON.

The audit walks PE resource directories and parses every PiPL property; `eGLO`/`eGL2` are not located by an unstructured byte search. Original `8664` names select the actual PE export (`entryPointFunc` or `entry_point`). GLOBAL_SETUP executes in the existing AexLoader/Unicorn with established Windows PF_OutData offsets `0x60`/`0x190`, bounded instruction counts and a verified normal return. Each AEX is independently run with output initialized to zero and `0xa5`: **20/20 calls return zero**, both fills produce identical flags. Host substitutes provide utility registration, PF handles, and Smoother2's AEGP memory handles; this is emulated original code, not native Windows AE.

Mac measurements use fresh **arm64+x86_64 Xcode bundles** (`Debug` project configuration, explicit `GCC_OPTIMIZATION_LEVEL=2`), read the compiled `.rsrc` resource map and PiPL, then `dlopen` each bundle and call its exported `EffectMain(PF_Cmd_GLOBAL_SETUP)` using real SDK structures. Each architecture is run in a new process for each of the same two fills: **40/40 calls return zero**. This is not a source-included shim and not an installed-plugin or native AE observation. Build outputs are removed after each plugin.

The independent import-free DirectionalBlur prepass at `0x180001000` passed the established `aex_witness.leaf_check` ABI control: 16 destination bytes zeroed, and two 16-byte buffers passed through Win64 stack arguments 5/6 each have only their first four bytes zeroed. No import calls. Its AEX SHA256 is `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`. This control is also built into the committed audit runner.

All flag pairs below are `OutFlags / OutFlags2`. Original PiPL and original GLOBAL_SETUP agree in every row; Mac PiPL and both Mac GLOBAL_SETUP slices agree in every row. **Mac values here are the measured pre-fix baseline.**

| Plugin | Original PiPL = runtime | Mac PiPL = runtime, before | Original smart? | Original Classic used by AE? | Mac agrees, before? | Target route |
|---|---|---|---|---|---|---|
| ColorKeep | `02000040 / 08001400` | same | Yes | No | Yes | Smart |
| OLMBlur | `06000040 / 08001400` | same | Yes | No | Yes | Smart |
| OLMColorKey | `02000440 / 08001400` | `06000040 / 00801400` | Yes | No | **No** | Smart |
| OLMDirectionalBlur | `06000040 / 08001408` | same | Yes | No | Yes | Smart |
| OLMDistanceGradation | `06000040 / 08001400` | same | Yes | No | Yes | Smart |
| OLMKiraKira | `02008040 / 08001400` | same | Yes | No | Yes | Smart |
| OLMRadialBlur | `06008040 / 08001408` | same | Yes | No | Yes | Smart |
| OLMSmoother v1 | `02000040 / 08000000` | `02000040 / 08000400` | **No** | **Yes** | **No** | **Classic** |
| OLMSmoother2 | `02000440 / 08001400` | same | Yes | No | Yes | Smart |
| OLMToonDilate | `02000044 / 08021400` | same | Yes | No | Yes | Smart |

Flag names/masks come from the locally installed SDK's `AE_Effect.h` (hash recorded in JSON). These decode **all** set bits, not just the route bit:

- Every original: `USE_OUTPUT_EXTENT=0x40`, `DEEP_COLOR_AWARE=0x02000000`, `SUPPORTS_THREADED_RENDERING=0x08000000` (last flag belongs to OutFlags2).
- Every original except Smoother v1: `SUPPORTS_SMART_RENDER=0x400` and `FLOAT_COLOR_AWARE=0x1000` in OutFlags2. Smoother v1 has no float-aware capability; an AE 32-bpc composition does not establish a native PF32 plugin route.
- ColorKey and Smoother2: `PIX_INDEPENDENT=0x400` in OutFlags.
- Blur, DirectionalBlur, DistanceGradation, RadialBlur: `SEND_UPDATE_PARAMS_UI=0x04000000`.
- KiraKira and RadialBlur: `CUSTOM_UI=0x8000`.
- DirectionalBlur and RadialBlur: `PARAM_GROUP_START_COLLAPSED_FLAG=0x8` in OutFlags2.
- ToonDilate: `NON_PARAM_VARY=0x4` in OutFlags and `AUTOMATIC_WIDE_TIME_INPUT=0x20000` in OutFlags2.
- No original sets GPU-F32, DirectX, mutable-render-sequence-data, flattened-sequence support, the obsolete thread-safe flags, or the PiPL override flag. MFR's threaded capability is distinct from Smart routing: Smoother v1 advertises threaded rendering on its Classic route.

**First capability disagreement:** ColorKey original `OutFlags=0x02000440`, Mac `0x06000040` (XOR `0x04000400`); original `OutFlags2=0x08001400`, Mac `0x00801400` (XOR `0x08800000`). Mac removes PIX_INDEPENDENT and SUPPORTS_THREADED_RENDERING, adds SEND_UPDATE_PARAMS_UI and SUPPORTS_GET_FLATTENED_SEQUENCE_DATA. Smart/float/deep support stays the same. Original AEX SHA256 and both compiled Mac slices are bound in the baseline JSON. The extra UI bit originated in the separate helper/UI implementation and is not evidence that original GLOBAL_SETUP sets it.

**Route disagreement:** Smoother v1's Mac `OutFlags2` adds `0x400` relative to original `0x08000000`. Original AEX SHA256: `6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82`. Unlike a diagnostic wrapper being callable, advertising this bit changes the host-selected render commands.

Harness development corrected an SDK header double-include, dataclass JSON serialization, nonuniform original export names (now derived from PiPL), and the missing AEGP Memory Suite provider. These were inspection/setup failures, not rejected pixel hypotheses or passing comparisons. The completed baseline above supersedes those incomplete runs.

inference:

The route and “Classic used by AE?” columns apply the SDK host contract to measured capabilities. The [SmartFX SDK guide](https://ae-plugins.docsforadobe.dev/smartfx/smartfx/#how-to-smartify) specifies Smart pre-render/render selectors for Smart-advertising effects instead of the Classic frame sequence; the [command-selector guide](https://ae-plugins.docsforadobe.dev/effect-basics/command-selectors/) limits Classic plugin rendering to 8/16 bpc. This is a capability-based conclusion, **not a fresh native AE call trace**. It concerns AE's supported CPU path, not Premiere/non-Smart hosts or manually forced emulator commands.

Accordingly F17's Classic results for all nine Smart-advertising originals, including ColorKeep/Blur/DistanceGradation which can produce Classic output, are diagnostic compatibility data for another route. They do not define the normal AE target. The six all-zero Classic families do not need a numerical “zero output” Mac patch to satisfy AE's Smart target. Smoother v1's compatibility owner remains original Classic, including when a test manually invokes a Mac Smart wrapper. No F17 residual, corpus, or comparison verdict is changed by this audit.

changed_files:
- `tools/emulation/audit_route_flags_F18.py`
- `tools/emulation/route_flags_mac_F18.cpp`
- `reports/route_flags_F18_before.json`
- `orchestra/reports/F18-route-target-per-plugin.md`

verify:

Run from this worktree with the existing SDK and MAIN assets:

```sh
s="$PWD/orchestra/state/F18-route-target-per-plugin"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" \
  tools/emulation/audit_route_flags_F18.py --report "$s/verify.json" \
  > "$s/verify.log" 2>&1
tail -11 "$s/verify.log"
git diff --check
```

Baseline expected: `plugin_count=10`, `flags_agree=8`, `smart=9`; only ColorKey and Smoother v1 disagree. All setup calls and the independent ABI control pass. Fresh build UUIDs/hashes can vary; compare bound inputs, flags, and routes rather than requiring an identical Mach-O hash.

next:
- Separate flag-fix commit: restore original ColorKey capability pairs and remove Smoother v1's advertised Smart bit in both PiPL and GLOBAL_SETUP; then repeat the audit and relevant existing tests.
- Native AE dispatch/lifecycle confirmation after a future authorized aggregate install remains separate. Neither this inspection nor a capability repair proves arbitrary pixel equivalence, MFR safety, UI redraw equivalence, or native host conversion.
