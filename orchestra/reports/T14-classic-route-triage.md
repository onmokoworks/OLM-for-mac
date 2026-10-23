status: done

summary:
- Reproduced all nine selected I03 Classic mismatches (one per 8/16/32 bpc for each of ColorKey, DirectionalBlur, DistanceGradation), with identical original and Mac Classic hashes.
- ColorKey and DirectionalBlur original Classic are successful no-write handlers; their Mac Classic wrappers render the Smart algorithm instead.
- DistanceGradation original Classic consumes uninitialized stack settings and existing destination pixels; the fake host makes this appear deterministic. Forced PF32 is interpreted as PF16.
- Ten fresh original PiPL/GLOBAL_SETUP flag pairs match cached I03 Mac PiPLs; ordinary AE selects Smart for nine, Classic for Smoother v1. Other-host reachability is conditional, not an AE fallback guarantee.
- Recommend no-write semantic parity for ColorKey/DirectionalBlur and explicit Classic refusal for DistanceGradation in follow-up tickets. No production change here.

facts:

Scope: branch `orch/T14-classic-route-triage`. Read AGENT_GUIDE, emulation GOTCHAS, compatibility plan, relevant ledger decision rows, F17/F18 and I03 evidence. Only report/evidence files were written. MAIN, original binaries, emulator source, cache/index, production, release gates and ledger were read-only. No build, install, push or reference-worker rebuild. Sequential processes; scratch below 1 MiB at inspection. No native AE/Premiere session was run. `done` means triage completed, not all-host exactness established.

**1. Advertised capabilities and reachability**

`T14-metadata.py` parsed current original PE resources, checked their SHA256 against F18, executed original GLOBAL_SETUP with AexLoader/Unicorn, and read cached I03 Mac resources. All ten setup calls returned 0; all ten flag pairs agree between original resource, original runtime and Mac resource. F18 separately measured both Mac runtime architectures; this ticket does not claim a fresh Mac runtime flag capture. The actual cached Mac bundles are also loaded for the nine render witnesses below.

| Original / Mac | OutFlags | OutFlags2 | AE CPU route | AEGP acquired at original setup |
|---|---|---|---|---|
| ColorKeep | 02000040 | 08001400 | Smart | Utility 7 |
| OLMBlur | 06000040 | 08001400 | Smart | none |
| OLMColorKey | 02000440 | 08001400 | Smart | Utility 13 |
| OLMDirectionalBlur | 06000040 | 08001408 | Smart | Utility 7 |
| OLMDistanceGradation | 06000040 | 08001400 | Smart | Utility 7 |
| OLMKiraKira | 02008040 | 08001400 | Smart | Utility 13 |
| OLMRadialBlur | 06008040 | 08001408 | Smart | Utility 13 |
| OLMSmoother v1 | 02000040 | 08000000 | Classic | none |
| OLMSmoother2 | 02000440 | 08001400 | Smart | Utility 13, Memory 1 |
| OLMToonDilate | 02000044 | 08021400 | Smart | Utility 13 |

All advertise USE_OUTPUT_EXTENT, DEEP_COLOR_AWARE and SUPPORTS_THREADED_RENDERING. Nine add SUPPORTS_SMART_RENDER (0x400) and FLOAT_COLOR_AWARE (0x1000); Smoother v1 does not. Additional bits are PIX_INDEPENDENT (ColorKey/Smoother2), SEND_UPDATE_PARAMS_UI (Blur/Directional/Distance/Radial), CUSTOM_UI (Kira/Radial), collapsed parameter groups (Directional/Radial), NON_PARAM_VARY and AUTOMATIC_WIDE_TIME_INPUT (ToonDilate). None sets the Premiere-specific colorspace-enumeration, destination-combination, opaque-preservation or sequence-clone flags. Those optional optimization bits are **not a universal Premiere support switch**.

All originals have one AEEffect PiPL, the same 12 property keys (`kind,name,catg,8664,ePVR,eSVR,eVER,eINF,eGLO,eGL2,eMNA,aeFL`), eSVR bytes `0d001c00` (API 13.28), and just one exported entry (`entryPointFunc` or `entry_point`). There is no host allow-list, explicit Premiere registration export, or Premiere-native pixel-format declaration in these resources. Current Mac resources retain the same effect flags, with Mac architecture entry properties and a support URL. Some Mac plugins (including ColorKey/DirectionalBlur) additionally export `PluginDataEntryFunction2`; this metadata callback is not evidence of working Premiere rendering. **No explicit original promise of Premiere/other-host compatibility was found in the examined metadata/setup evidence.** This is narrower than proving every original function lacks host-dependent behavior.

Host conclusions (SDK contract vs observed execution kept separate):

- **AE with SmartFX:** the SDK dispatch contract replaces FRAME_SETUP/RENDER/FRAME_SETDOWN with SMART_PRE_RENDER/SMART_RENDER for an effect advertising Smart. This applies to 8/16 bpc too; 32 bpc AE rendering requires Smart. There is no documented render-queue, proxy-generation, reduced-resolution, ROI or CPU fallback exception that turns a Smart-advertising CPU effect into Classic. Queue/proxy execution follows the same contract if the effect is rendered; using an existing proxy can bypass it. These are contract-based inferences, not native call traces. [SmartFX](https://ae-plugins.docsforadobe.dev/smartfx/smartfx/), [selectors](https://ae-plugins.docsforadobe.dev/effect-basics/command-selectors/).
- **AE versions:** pre-Smart hosts can only use Classic if they can load the binary/API and the plugin supports that lifecycle. Do not interpret this as the 2025 AEX supporting AE 6.x, or the Apple Silicon bundles supporting old AE. The current originals request API 13.28, identified by the local SDK header as AE 23.4-era; the SDK version table already identifies AE 7.0 as API 12.12. A metadata/API version is not a tested minimum-host matrix. For loadable Smart-capable AE versions the Smart flag governs dispatch, not project depth or queue mode. [Version compatibility](https://ae-plugins.docsforadobe.dev/intro/compatibility-across-multiple-versions/); MAIN `Headers/AE_Effect.h:180` and `:189`.
- **Premiere:** the SDK's legacy AE-effect hosting documentation specifies Classic and basic ARGB8; its separate float path requires Premiere pixel-format registration plus Classic float handling. AE DEEP/FLOAT flags alone do not supply that support. The same docs list AEGP and SmartFX as unsupported. Eight originals acquire AEGP suites during setup, including all three investigated here, so even reaching their render command in Premiere requires compatible suite availability/handling. Blur/Smoother lack that observed setup dependency but are not thereby certified. [Pixel formats](https://ae-plugins.docsforadobe.dev/ppro/bigger-differences/), [unsupported features](https://ae-plugins.docsforadobe.dev/ppro/unsupported-features/).
- **Documentation limit:** current selector docs also describe Smart pre-render when MediaCore hosts. Therefore “every Premiere version can only call Classic” is too broad. The justified result is that non-Smart AE-compatible hosting can call Classic, not that any particular current Premiere build successfully loads these original binaries. No version-by-version Premiere load test was performed.
- **Other hosts:** Classic is reachable in a non-Smart implementation that accepts the binary and supplies required suites. Smart support and AEGP availability must be tested per host. `appl_id` distinguishes FXTC/PrMr, but no host allow-list appears in these PiPLs. [Host differences](https://ae-plugins.docsforadobe.dev/intro/third-party-plug-in-hosts/), [other hosts](https://ae-plugins.docsforadobe.dev/ppro/other-hosts/). The SDK's dated third-party-host statement is not treated as a 2026 product inventory.

**2. Nine retained witnesses and replay**

Selection is deterministic: first archived Classic mismatch at each depth for each plugin. Each is seed 777, index 1 at 8 bpc (13x7), index 0 at 16 bpc (17x9), index 2 at 32 bpc (13x8). Full filenames, inputs, settings, provenance and hashes are retained in `T14-evidence.tar.gz`. These are the actual archived inputs, not regenerated approximations. Original worker F46 SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`; Mac host F51 SHA256 `7a5bc8c328503b6cd3918ae1db9b29ef9b0d0e3f274ae31904de0354aa3f0f28`; bundles are the indexed `I03-bundles-545f06bd924497e5` artifacts. Individual AEX and Mach-O hashes are in replay/metadata JSON. Evidence archive: 60,347 bytes, SHA256 `b05a85ada110532b06ab78afd79d8f05a8c836d391740b33c55ee2b8f67dd551`.

`T14-replay.py`: 18 original sessions, 18 cached arm64 bundle sessions. All 9 Classic original hashes and all 9 Classic Mac hashes equal I03. All original Smart hashes also equal I03. Eight admitted Mac Smart results are exact; DistanceGradation PF32 Smart refuses (516 in real SDK bundle, versus -1 in historical shim); neither refusal buffer is a numeric comparison. All 9 Mac Classic commands succeed.

| Plugin | bpc | Different Classic words | First byte offset | First expected → actual word, little-endian hex | Classification |
|---|---:|---:|---:|---|---|
| ColorKey | 8 | 334 | 0 | 00 → 68 | c, plus comparator no-write issue |
| ColorKey | 16 | 557 | 2 | 0000 → 8241 | c, plus comparator no-write issue |
| ColorKey | 32 | 390 | 3 | 00000000 → 0000003f | c; forced non-AE Classic32 |
| DirectionalBlur | 8 | 334 | 0 | 00 → 68 | c, plus comparator no-write issue |
| DirectionalBlur | 16 | 404 | 0 | 0000 → e50e | c, plus comparator no-write issue |
| DirectionalBlur | 32 | 332 | 16 | 00000000 → 93bbcd3d | c; forced non-AE Classic32 |
| DistanceGradation | 8 | 250 | 0 | ff → 00 | b + c |
| DistanceGradation | 16 | 294 | 0 | 9f05 → cf02 | b + c |
| DistanceGradation | 32 | 393 | 2 | 4dd00080 → 4dd0813e | b: deep16 callback on float world; c |

Here **c** means the observable Mac implementation intentionally provides a rendering wrapper sharing the Smart algorithm; it does not infer the original author's intentions or approve incompatibility. **b** means a fake-host/precondition-dependent oracle result, not necessarily an emulator instruction bug. None of these nine demonstrates **a**, a missing numerical Smart kernel in the Mac implementation.

ColorKey: original entry `0x18000ffb0`, selector 11 calls `0x18000bba0` which simply returns 0, after locking global state. DirectionalBlur: original entry `0x1800083f0`, selector 11 only constructs/destructs a suite handler (`0x180008740/8780`); no image worker. `T14-boundary.py` drives both original entries on the nine-witness geometries with real input bytes and destination fill 0x5a. For these six cases: return 0, 0 destination stores (Unicorn memory-write hooks), every destination byte preserved. ColorKey's locked dummy global state is valid allocated storage; that no-write arm does not dereference it. This bounded direct probe supplements the full-lifecycle worker replay and static dispatch proof; it is not native AE. Mac ColorKey `Render` calls `RenderWorld` (`mac/OLMColorKey/OLMColorKey.cpp:2695`); DirectionalBlur does the same (`mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:2225`). Their Mac Classic and Smart raw outputs equal in all six witnesses. The AEX's zero output in I03 was the fake host's initial buffer, not a black-image algorithm.

DistanceGradation: original entry `0x181174bd0`, selector 11 selects `0x181170380` (iterate8/compose `0x181170870`) or `0x181170280` (iterate16/compose `0x181170480`) solely using the destination DEEP flag. Unlike Smart, it does not run the parameter reader / distance-field builder. It puts source/destination/in_data pointers in a stack context and initializes only limited other fields. Compose reads settings at context offsets 0x90,0x94,0xc0,0xc1,0xc8,0xcc,0xd0 and reads the **existing destination red channel as the distance field**. Static excerpts with original decomp hashes are committed in the evidence.

Fresh boundary observations: intercepted the iterate call and copied its 0xd8-byte context, then invoked the original compose callback for the full witness using that copied context. No synthetic expected-value arithmetic was used. With zero-filled stack and zero-filled destination, reconstructed original compose bytes match the complete worker Classic output **3/3**. With stack fill 0xa5, the listed setting fields remain 0xa5 (all three depths); the filled context is captured, not treated as legitimate settings or run as a valid render. With zero-stack settings and destination fill 0x5a, all three hashes change. This establishes both uninitialized-state and destination-input dependence at an actual original boundary, rather than attributing all differences to ROI or rounding.

PF32 detail: the worker marks both ARGB16 and ARGB32f as DEEP (`pixel.rs::world_flags`). Original Classic consequently selects **iterate16**, processes 8-byte pixels on a 16-byte-per-pixel world, and leaves the remaining row bytes at their initial fill. This exact geometry reproduces the saved PF32 bytes. A diagnostic attempt with DEEP cleared selected iterate8 and did **not** match; it is retained separately as `boundary-worldflags0.json`, not discarded. Correcting the probe to the observed worker flag gave the new boundary and 3/3 equality. This is not a valid AE float Classic contract and is not evidence that Premiere float registration exists.

Mac DistanceGradation Classic queries the actual WorldSuite pixel format and executes `RenderBits<PF_Pixel8/16/Float>` (`mac/OLMDistanceGradation/OLMDistanceGradation.cpp:2191`). Its 8/16 outputs equal Mac Smart and original Smart in the selected cases. PF32 Classic admits this case while Smart refuses; that admission difference is real and is retained, not counted as exact. Full-frame origins, extent rectangle and downsample 1:1 are used here. Padding/ROI/downsample are not the cause needed to explain these nine; this does not certify arbitrary layout.

inference:

**3. Recommendation and effort (engineering estimates, not measured durations)**

| Plugin | Recommended follow-up | Estimated effort |
|---|---|---|
| ColorKey | Fix Classic **semantics** to original success/no-write, retaining Smart numerical implementation. Update comparator to check destination preservation, never a zero-image expectation. | 0.5–1 day implementation + 1–2 days lifecycle/nonzero-fill/Smart regression and one host smoke. |
| DirectionalBlur | Same success/no-write parity. Do not “fix” the Smart kernel to produce black pixels. | 0.5–1 day implementation + 1–2 days regression/host smoke. |
| DistanceGradation | Make unsupported Classic refuse explicitly and atomically; keep Smart. Do not imitate uninitialized stack or destination-dependent garbage as portable exactness. This is an intentional capability restriction, not Classic bit-exact success. | 1–2 days with refusal/admission regression; 2–5 additional days if a named non-Smart host must first be traced. Full Classic parity has no defensible fixed estimate until that host supplies a defined original contract. |
| ColorKeep | Leave code as-is pending separate 3-witness boundary triage; it has an actual Classic renderer, unlike the two stubs above. | 1–3 days triage; numerical-fix effort unestimated. |
| KiraKira, RadialBlur | Leave as-is in this ticket. F17 zero destinations alone are insufficient to conclude no-write; trace their dispatch before choosing parity/refusal. | 0.5–2 days triage each; fix estimate after boundary proof. |
| OLMBlur | Leave as-is; F17 already distinguishes supported Classic depth/settings. Do not remove working Classic merely because Smart is advertised. | No proposed implementation; 0.5–1 day focused recheck if other-host support is requested. |
| Smoother2, ToonDilate | Leave existing policies pending explicit host scope: F17 already identifies original no-write. Smoother2 refuses; ToonDilate preserves destination. | 0.5–1 day policy/regression review each if changed. |
| Smoother v1 | Leave working Classic owner intact. | No change proposed. |

This favors exact defined behavior where it exists and explicit refusal where the original forced route has no stable image contract. Refusal does not satisfy bit-exactness and must be reported as unsupported. Leaving the two working Mac wrappers unchanged is possible only as an explicitly documented extension, not a claim of original Classic compatibility. Do not change flags to force Classic in AE or strip Smart support. None of these recommendations is implemented here.

changed_files:
- `orchestra/reports/T14-classic-route-triage.md`
- `orchestra/reports/T14-replay.py`
- `orchestra/reports/T14-boundary.py`
- `orchestra/reports/T14-metadata.py`
- `orchestra/reports/T14-evidence.tar.gz` — nine full witnesses, raw paired outputs, logs, metadata, boundary captures and bounded decomp excerpts.

verify:

From this worktree (MAIN assets/cache must remain at the documented locations):

```sh
s="$PWD/orchestra/state/T14-classic-route-triage"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" orchestra/reports/T14-replay.py > "$s/replay.log" 2>&1
"$py" orchestra/reports/T14-boundary.py > "$s/boundary.log" 2>&1
"$py" orchestra/reports/T14-metadata.py > "$s/metadata.log" 2>&1
tail -9 "$s/replay.log"
tail -4 "$s/boundary.log"
tail -10 "$s/metadata.log"
git diff --check
```

Expected: all three commands exit 0. Replay: 9/9 reproduced Classic mismatches, 8 admitted Smart exact, one Smart refusal. Boundary: 12 entry probes, six no-write cases, six DG captures (two stack fills), all three zero-fill compose replays match worker; all three alternate destination fills differ. ABI leaf control passes. Metadata: 10 original setup/resource/Mac-resource agreements. No build outputs are produced. Absolute paths and callback addresses appear in diagnostics; raw image hashes and comparison counts are the reproducibility targets.

next:
- T14a: implement/test ColorKey + DirectionalBlur Classic no-write semantic parity and comparator attribution, explicitly authorizing those production changes.
- T14b: decide/document DistanceGradation Classic refusal and PF32 admission policy; preserve this evidence as an oracle-contract limitation.
- T14c: named-host/native dispatch trace if Premiere, an older AE or another host is a supported delivery target; include load/setup suite availability, version, pixel-format registration, buffer initialization and queue/proxy commands. PiPL alone cannot settle that product matrix.
- T14d: ColorKeep/Kira/Radial Classic boundary triage. Do not extrapolate these nine witnesses to S01's 5,873 cases or claim a new release gate pass.
