status: blocked

summary:
- Technical validation is complete: seed-1 n300 improves E/M/R/U 62/29/95/114 → 205/0/95/0; no exact case is lost.
- Built and indexed F32 from F30 with legacy DEEP_PIXELS allocation; all 679 non-Smoother-v1 saved corpus outputs are byte-identical.
- The second PF8 harness omitted ceilf/floorf implementations. Implementing them makes all 29 retained outputs match the frozen/F32 oracle.
- Fixed the Mac PF8/PF16 color comparator's reversed rounding imports; sanitized retained replay is 29/29 exact.
- `blocked` is the brief's required administrative status after an SDK-discovery shell command encountered macOS permission denials; no technical acceptance failure remains in the tested scope.

facts:

**Scope and provenance.** Read AGENT_GUIDE, GOTCHAS, T11/F22 reports, the Smoother v1 ledger decision row, and the compatibility plan. No release gate, forbidden list, corpus, other plugin, MAIN, or original emulator checkout was modified. Fuzzer defaults remain unchanged. Source copy is `/Users/onmk/.cache/olm-emu/src-F32/reference-guest`; installed worker is `/Users/onmk/.cache/olm-emu/worker-F32-deep/aex-guest-worker`.

| Artifact | SHA256 |
|---|---|
| Original Smoother AEX | `6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82` |
| Frozen worker | `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2` |
| F30 worker | `8b51d0456ff55aa2034a0bbb00b822bd2339cbe27247021c289170a78a3fb53b` |
| F32 worker | `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1` |

Full source manifest, patch hash, build command, and memory measurement are committed in `tools/emulation/aexcompat_patches/F32-evidence/build-manifest.json`. The pinned F30 source manifest matches the actual parent tree. Worker registration used the shared `.index.lock` and appended `worker-F32-deep`, parent `worker-F30-ucrtmath`, without replacing existing entries.

**DEEP_PIXELS contract.** `probe_F32_deep.py` executed the original selector 11 (`PF_Cmd_RENDER`) on a 3×3 PF16, key-enabled input and recorded:

- Legacy `in_data->utils->new_world(effect_ref,3,3,2,world)`, utility-table offset `0x70`. This allocation callback has no acquired suite name/version.
- Two acquisitions of **`PF iterate16 Suite`, version 1** (key pass and main pass).
- 72 output bytes. Exact invocation evidence is `F32-evidence/deep-callbacks.json`.

SDK root: `/Users/onmk/Documents/After Effects SDK/ae25.2_20.64bit.AfterEffectsSDK/AfterEffectsSDK/Examples/Headers`.

- `AE_EffectCB.h:535–542`: CLEAR_PIXELS is bit 0 and DEEP_PIXELS is bit 1.
- `AE_EffectCB.h:663–669,817–825`: new-world scratch ownership/disposal and the legacy five-argument signature. The stale inline “always 32 bit” comment is not treated as overriding DEEP_PIXELS.
- `AE_Effect.h:484–485,500–505`: world DEEP/WRITEABLE flags, depth predicate, and `PF_MAX_CHAN16=32768`.
- `AE_Effect.h:1306–1308`: PF_Pixel16 uses four unsigned-short ARGB channels.
- `AE_EffectCBSuites.h:620–658`: exact iterate16 suite name, version 1, and PF_Pixel16 callback signature.

F32 selects existing format `0x36316561` (PF16) for legacy flag 2 and reuses the typed allocator: 8 bytes/pixel, width×8 rowbytes, DEEP|WRITEABLE world flags, existing limits/ownership/disposal and clear behavior. PF8 allocation remains the same. There is no full-range-65535 conversion or output clipping. The captured flags=2 does not request clearing; existing deterministic uninitialized-memory fill remains in effect.

**PF8 first differing internal boundary and cause.** A frozen-worker trace at the natural executor call (`function=0x6710,arg=stack6,size=1`) captures the classifier result. For the retained 1×3 case, the 12 direction results are:

- Second host without math providers: `0,0,0,4, 0,0,4,0, 0,0,4,0`.
- Frozen worker and corrected second host: `0,0,0,0, 0,0,4,0, 0,0,4,0`.

Earlier paired probes found equal key/tolerance bytes, equal 1×3 rowbytes/dimensions, equal normalized neighborhood pointer tables for all 12 classifier calls, and equal center/next input bytes `c6137aa1f905713d`. World headers differ in unused fixture metadata; those differences were not patched to force equality. The causal earlier boundary is an imported math callback result:

- First ceilf argument in this case: **0.9494171142578125**. The unimplemented host leaves XMM0 at that value; the implemented host returns **1.0**.
- The next floorf argument is **−0.9494171142578125**; unimplemented leaves it unchanged, implemented returns **−1.0**.
- The original then executes CVTTSS2SI, so the missing provider changes the converted integer from ±1 to 0. This changes the classifier's sign decision.

`AexLoader._register_default_impls()` does not provide these functions; its generic unimplemented-import path writes RAX=0 and leaves XMM0 unchanged. Even `register_libm_impls()` does not include ceilf/floorf. The retained helper did not register them. `probe_F32_hosts.py` isolates the two providers while preserving its InData, world, parameter, iterate, copy, and checkout behavior. All **29/29** corrected-host outputs equal F32; **0/29** no-op-provider outputs equal F32. Per-case first changed import, output hashes and classifier differences are committed in `F32-evidence/summary.json`; the full reproducible import logs remain scratch.

The PE import table independently resolves `0x18000c41e` → IAT `0x18000d0d0` → **ceilf**, and `0x18000c424` → IAT `0x18000d0c8` → **floorf**. The color comparator branches to ceilf for positive luma delta and floorf otherwise. The Mac implementation had these reversed in both integer-depth comparators, accompanied by an incorrect “truncate toward zero” comment. Both are now corrected generally. No worker PF8-host patch was needed. This is a missing import implementation, not an AE world/checkout contract dispute; the worker follows the original PE imports.

Frozen-worker tracing cannot hook arbitrary instructions: attempted watches at 0x2639 and 0x2647 were reported unhookable. No worker XMM0 observation is claimed. The committed probe uses the supported classifier-to-executor call-site boundary, the original import mapping, and controlled provider substitution. Historical second-host/classifier evidence without these imports must not be treated as an independent valid oracle.

**Measured counts.** Three fresh `tools/fuzz/run.py --plugin olmsmoother --n 300 --seed 1 --jobs 1 --shrink-attempts 0` runs used explicit F30/F32 paths and ticket-local scratch/corpora; report names are `f30-seed1.json`, `f32-seed1.json`, `fixed-seed1.json`. Both wrappers show the following, but Classic is the original advertised owner:

| State | PF8 E/M | PF16 E/M/U | PF32 R | Total E/M/R/U |
|---|---|---|---:|---|
| F30, original Mac | 62/29 | 0/0/114 | 95 | 62/29/95/114 |
| F32 allocator only, original Mac | 62/29 | 113/1/0 | 95 | 175/30/95/0 |
| F32, corrected Mac | 91/0 | 114/0/0 | 95 | **205/0/95/0** |

No baseline-exact → non-exact transition; all 205 admitted outputs are exact. Original PF32 refusals remain untouched. The newly exposed PF16 mismatch was seed case 261, 231×200: first byte 88888, expected word `0080`, actual `c074`, 4 differing words / 8 bytes. The common rounding correction resolves it too.

`validate_F32.py` ran every non-Smoother-v1 saved corpus case serially: **679 successful F30 outputs, 679 successful F32 outputs, 0 changed raw hashes/statuses**, including Smoother2. It reads but does not rebaseline any corpus.

`compare_olmsmoother_classifier8.py --jobs 1` with both minimal representatives and the 29-case owner corpus: **88/88 classifier directions**, **29/29 owner=Mac=worker** after registering real math providers. Fatal ASan/UBSan retained replay: **29/29 exact**, both wrappers, no candidate errors. `matches_saved` is **0/29**, deliberately: saved records describe the old mismatches; no saved file was changed. The replay command returns success with `replay_complete`, so exactness is checked from the result statuses rather than inferred from that exit code.

**Execution issues and cleanup.** Initial SDK discovery used `rg --files /Users/onmk`, which encountered “Operation not permitted” / “Permission denied” for unrelated macOS-protected Library directories. No escalation or access bypass was attempted; the command completed and the SDK was found under Documents. Per the brief, this report conservatively uses `blocked`. This was an OS read denial inside an accepted shell call, not an automatic approval-review rejection. Initial Rust build under the space-containing worktree path failed in Unicorn CMake (`main directory cannot contain spaces nor colons`, then `__int128_t` redefinition). Rebuilt successfully under the explicitly authorized cache output directory. `memory_pressure` immediately before that build reported **53% free**; build used Cargo/CMake jobs=1 and completed in **2m56s**. No more than two emulator/build processes were active. Regenerable build trees were removed; ticket scratch was under 5 GiB throughout. No background task remains.

inference:

- Controlled replacement of only the missing math providers, with unchanged host geometry/parameter/callback setup, identifies the second host as incorrect for these 29 cases. The PE mapping and matching classifier transition establish the corresponding general Mac rounding defect.
- Local CPU-AEX evidence supports this tested seed/corpus scope. It is not a new native AE render, arbitrary-input proof, or release-gate promotion.
- All technical acceptance checks in this ticket passed. The blocked label records the explicit permission-denial rule, not a remaining numerical mismatch.

changed_files:
- `mac/OLMSmoother/Mac/OLMSmoother_port.cpp`: PF8/PF16 color comparison rounds away from zero as the original imports require.
- `tools/emulation/test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810.py`: explicit ceilf/floorf providers for the diagnostic original host.
- `tools/fuzz/compare_olmsmoother_classifier8.py`: same providers for leaf probes; allow jobs=1; updated provenance wording.
- `tools/emulation/aexcompat_patches/F32-deep-pixels.patch`: isolated legacy PF16 allocation support.
- `tools/emulation/aexcompat_patches/{build_F32.py,validate_F32.py,probe_F32_hosts.py,probe_F32_deep.py,summarize_F32.py,verify_F32.sh}`: pinned build, locked registration, serial differential and reproductions.
- `tools/emulation/aexcompat_patches/F32-evidence/*.json`: build manifest, compact campaign/host evidence, all-corpus differential, classifier, sanitizer and callback results.
- `orchestra/reports/F32-smoother-oracle-deep-pixels.md`: this report.
- External authorized cache: `src-F32`, `worker-F32-deep`, `F32-deep-build.json`, and appended INDEX entry.

verify:

```sh
sh tools/emulation/aexcompat_patches/verify_F32.sh
```

This bundles the exact component commands used above, writing fresh logs/reports only under ticket scratch. Expected: 679/679 unchanged non-Smoother outputs; owner 29 corrected / 0 unimplemented equal; PF16 allocation flags=2 and iterate16 v1; seed1 205/0/95/0; fatal sanitizer 29 exact; 88/88 directions; 29/29 owner/worker/Mac equality; `git diff --check` clean. The assembled wrapper is provided for orchestration; its component commands were run individually in this ticket.

For a new build environment with absent F32 cache destinations, run `python3 tools/emulation/aexcompat_patches/build_F32.py` (logs go to ticket scratch; memory ≥30% required). It verifies pinned F30/F32 manifests and refuses to overwrite workers. Absolute build paths/revisions influence binary hashes; use functional replay for relocated rebuilds. Registration is separately `python3 tools/emulation/aexcompat_patches/build_F32.py --register`, only after validation and only when its INDEX entry is absent. Do not rerun registration against the already registered worker.

next:
- Orchestrator: review/merge the isolated allocator and general Mac rounding fix; acknowledge the administrative blocked status required by the permission-denial clause.
- Propose a follow-up switch from F30 to F32 with SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`; coordinate with F31. This ticket does not change the default.
- Treat older Smoother diagnostics driven without explicit ceilf/floorf providers as invalid numerical evidence until rerun. Existing corpus records remain historical mismatch records; any migration should be separately authorized.
