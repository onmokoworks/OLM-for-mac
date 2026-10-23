status: blocked
summary:
- Added one read-only asset resolver and migrated the fixed-fixture runner and reachable input consumers.
- Latest combined result: 76 PASS, 125 command FAIL, 3 installed-identity FAIL; 89 commands skipped.
- Classified all 134 initially failing entries: (a) 6 fixed, (b) 72 stale bindings, (c) 18 numerical assertions, (d) 38 other.
- Bisected numerical witnesses; four failing commands retain exact final output and differ only in intermediate planes.
- Full requested provenance remains blocked: unavailable historical assets, copy-dependent tamper tests, and an unbound installed KiraKira build.

facts:

Base: `979c4db232e37a7775b786c48c60a0c2f4c71294` on `orch/F36-fixture-runner-worktree-and-triage`.
Code commits: `24e8b60d5584d4e0ea1411b148bb01d4a3415e3a` and
`eb808af11cc99a1d19e0c9b415dfff0a1d37d81b`.

The resolver prefers the worktree input, then `OLM_MAIN_ASSETS`, defaulting to
`git rev-parse --git-common-dir`'s parent. It never creates/copies/links inputs.
Source files, output directories, and generated fixture destinations stay in the
worktree. The runner supplies the resolved Python environment and SDK include
paths to descendants, keeps their temporary files in worktree scratch, and
optionally streams each command to its own log plus `results.json`. Repository
scripts are executed from the worktree, never from MAIN. `asset_relative` only
preserves repository-relative evidence labels for resolved read-only inputs.

Execution was sequential within each runner with `OLM_TEST_JOBS=1`; at most two
emulator/build jobs were launched concurrently across suite and diagnosis work.
No workers were rebuilt, no installed binaries changed, no identities repinned,
and no numerical assertions or expected data were weakened.

| Execution | Real result |
|---|---|
| Full default runner, `--results-dir orchestra/state/F36-fixture-runner-worktree-and-triage/full` | exit 1; 70 PASS, 130 executed FAIL, 1 missing test, 3 identity FAIL; 89 skipped; 1367.24 s |
| Recheck blur/colorkeep/colorkey/directionalblur/distancegradation/kirakira after path fixes | exit 1; 64 PASS, 85 executed FAIL, 1 missing test; 375.45 s |
| Command 165 after label correction | exit 1; now reaches retained numerical comparison, with exact final PF8 bytes but different intermediate planes |
| Combined latest outcome per command | 76 PASS / 124 executed FAIL / 1 missing test; plus 3 identity FAIL / 89 skipped |
| `python3 -B -m unittest tests.test_olm_assets -v` | 4 tests PASS; precedence, missing/external paths, default common-dir lookup, logical labels |
| Changed Python syntax and `git diff --check` | PASS |

The full run began while helper migration was being completed. Therefore the
combined result is explicitly **not** presented as one clean post-commit full
run: the first 150 commands use the later recheck logs; command 165 uses its
follow-up; remaining commands use the full-run logs. A mechanical label rewrite
initially produced `FULL_PF8_asset_relative`; commit `eb808af1` fixes it and the
follow-up exposes the existing intermediate-plane discrepancy.

Six failures actually fixed between the full run and recheck are SDK source
inputs (037–039, 068) and MAIN decomp input access (057–058). Other newly passing
AEX campaigns are not assigned fabricated before/after causal counts from I02.
F35's two 2,992-byte DG public Smart fixtures pass here; I02's superseded 748-byte
Classic/internal-fixture discrepancy is not a current F36 numerical failure.

Numerical boundary evidence (class c):

The commands below compare raw bytes/words with original-AEX-derived retained or
fresh Unicorn expectations. This establishes a regression of these assertions,
not that the older emulation math is necessarily more faithful than later
native-trace evidence. No production numerical change was made.

| Failing commands / witness | Boundary and measured result |
|---|---|
| 153, 168: PF32 Rotation neutral/NV0 | `f5a74754df8b279455dd1c13839313078faa68b1`; parent `6d0904f8ea86d2deb572aa4ddb4c2aca2c5ba61c` exact. HEAD has 83 differing output bytes / 1,120; first byte 4: AEX `0x15`, Mac `0x16`. Expected SHA `beb7ce8ac537a172873092d1439121019f2dbedee2d3cff04e4f6e3bf5d8ea94`, actual `640aa561344b88927b81dcd74ee51b1823acd61d5615911282fcbb4babb41cab`. |
| 155, 156: Ratio2/Angle0, 9x7 and 32x18 | Same adjacent good/bad commits; 82 and 674 output bytes differ respectively. Both HEAD witnesses reproduce the boundary output. |
| 157, 158: Strength5/NV25 and OffsetMode3/Offset2/NV25 | Same adjacent boundary; 85 and 4 differing output bytes. These commands also contain obsolete negative-admission assertions. |
| 167, 171, 178, 179: PF16 neutral; PF32 Strength5; PF32 Offset3/4 | Same adjacent boundary; 2, 9, 1, 41 differing output bytes respectively. |
| 169: OuterFade50 | Same first boundary; 85 output bytes differ there and 102 at HEAD. Later fade changes alter the residual further. |
| 165: full retained case0010 PF8 | Same adjacent boundary; parent returns 0 with all planes exact. Bad/HEAD differ in 1,801,691 accumulation words (first word 0) and 95,441 normalized words (first word 541932). Final output remains exact, SHA `cb39306e0e340bfa121e5ea55c9e1b43f87696237b4d6c855a47ce09dba188fc`. |
| 172, 181: PF16 Strength5/Offset3 | Same adjacent boundary; final output remains exact. Accumulation differs in 2,105 and 229 bytes; final floating RGBA differs in 9 and 1 bytes before PF16 conversion. |
| 170: OuterFade50/NV25 | `7a7f53feb6d064a550124971e4920fb8d846efe4`, parent `bed824a79503ef2028a56d5f2428897c85329cbc` exact. HEAD has 50 output-byte differences, first byte 8: `0xee` → `0xed`. Full bisection retained. |
| 159: Zoom Inner50/NV25 | `b07f5c008c2c74ba4112ff851aff959dda71f0d9`, parent `47b8632a38a714e20de5983b4bf55be5444e76de` exact. 48 output-byte differences, first byte 4: `0x48` → `0x4a`. Expected SHA `3cc6bb415ea5b7f075d4c5ad955da7878dd0e9dcd0b5cbb51f3843024640f568`, actual `470ee3c2fb36adf781fb606b307f471b7bc5777c897cfa61d851a4cc04c7fea5`. |
| 174: Zoom PF16 Strength5 | Same independently bisected `b07f5c00` boundary; 10,373 post-blur bytes differ, first byte 48. Final 560 output bytes remain exact. |
| 152: opaque Size1 | Non-monotonic admission history: `f3765f38288f92e2296cdf941ce82eaa5fadee77` first changes the old exact case to refusal (parent `f4e4dac8` exact). `ea3a16c5` re-admits it with 83 differing output bytes; immediate parent `58175851` refuses. A separate capture explicitly sets the original AEX Size1 field and confirms its expected output is the neutral SHA above. Do not describe the earlier refusal as a byte comparison. |

The first-bad commits above are **single-parent commits on the first-parent
history**, predating the current orchestration merges. There is no introducing
merge at those boundaries; the exact commits and their parents are reported
instead of inventing merge attribution. The comparison scripts extract only
tracked Mac/core source snapshots, use the same AEX/SDK inputs, compile one
snapshot at a time, and delete every snapshot/build on exit.

Other concrete diagnostics:

- ColorKey command 047: captured stdout is 2,304 bytes with SHA
  `2b05dfeed6c1385d4818cd727aabc6931581b6d39ce22f84a13461b91a33e740`, exactly its first
  retained expected output. Stderr is `SOURCE_BOUND_ATOMIC pass=0 positives=0 negatives=0`.
  The C++ probe emits that positive output before its first mutated-input rejection
  check. Its failure is the old rejection contract, not that positive output.
- DirectionalBlur 083 exits 38 with `layer3 err=-1 exact=0 visible=0 pad=1`.
  This remains an unresolved host-adapter refusal, class (d), not a stale hash or
  a demonstrated output-byte mismatch.
- Radial 164 refuses before output comparison (probe rc=3); 184 fails its first
  Type3 SmartPreRender/event-order check (rc=10). These remain class (d).
- Request validator 105 now reads the MAIN package, then finds analyzer binding
  `d5da42b0…` → `fb79973f7a6fd116e2cf7464976c0ba334bc0063e8b19b03ef9166ec53e0f4df`,
  introduced by `744fc49e42d3a5ca426b56f4dc6e788d5dc27f01`.
- Two tamper suites (106, 190) explicitly copy package directories/ZIPs. Their
  worktree copies do not exist. The worker brief forbids copying MAIN assets;
  those mutation-oriented paths were not silently redirected or copied.
- Missing historical AEXCompat issue851/issue1135 checkouts and old handoff
  products are not supplied by the worktree/main fallback. The provided cached
  workers were inspected; no different worker was silently substituted for a
  pinned historical one. Missing-input paths and existence checks are retained
  in `F36-command-triage.json`.

Class (b) proposed values and commit evidence:

`F36-binding-candidates.json` contains full proposed SHA-256 values for 277
source/helper inputs, with each file's last-changing commit. This is an inventory
of observed replacement values, **not acceptance or an instruction to repin**.
Examples of source commits yielding the current values are OLMBlur `810ced04`,
ColorKeep `b3294649`, ColorKey `9dc68a8a`, DirectionalBlur `9a0e4eb7`, DG `90714962`,
KiraKira `3ca06908`, and RadialBlur `d8eff1dd`. F36 helper-only binding changes are
at `24e8b60d` (plus the label fix `eb808af1`). These are last changes yielding the
observed hashes, not claims that every historical assertion first broke there.

Installed values were freshly hashed. The receipt column names a commit that
records that installed hash; it is **not proof of a build from present HEAD**.
In particular KiraKira has only an I02 diagnostic observation, not a matching
accepted build/install receipt. An exact installer/source commit cannot honestly
be assigned to that untracked binary from the available evidence.

| Plugin | Pinned executable SHA-256 | Proposed observed SHA-256 | Historical receipt / observation commit |
|---|---|---|---|
| OLMBlur | `ecdf3d93b4b38fe71f4b66f717079aa86b961205d0a3f1b5b7edbd29e353284d` | `b6df72f7c2ef12a8ccb013bcd98f95b113b59571731f2cf26a6080615bae30b9` | `b34f9398` (refs/conformance/olm_native_ae_declared_matrix_54_20260823.json) |
| ColorKeep | `dae59a6faf54ed18ac803ad042be2cdab688c5f814edf322d64c108d5247f46d` | `ae9643a5a02f111ac48d284d646418cb1f6c4e9b3eaf213a34c17c5698dd1a10` | `8bcce08c` (refs/conformance/colorkeep_native_ae_count100_major_ops_20260824.json) |
| OLMColorKey | `51f551a32bd975b7ae1c2437809ecb81af1d06f9e967a8fccbd9dc2a6190ce4d` | `60b5ba2d4cf39d97bd32a9da99cd0ee31778374031a8dad78fd5deb70aec791a` | `b34f9398` (refs/conformance/olm_native_ae_declared_matrix_54_20260823.json) |
| OLMDirectionalBlur | `c64f8ff701008ae0390eb9da1a9e073dcde97a77e9b32701becf6eaa241a2666` | `bced525426da29a67c45d5cb3071de06cc417d9732a15108dfa1188cb03a7bcc` | `b34f9398` (refs/conformance/olm_native_ae_declared_matrix_54_20260823.json) |
| OLMDistanceGradation | `9a97a076c118fd1015f40d922bf7f21be7a041f1f049a0e465cc0bc9cd1cd349` | `ce48b9ebf92bb1b66db9e3da1c0c17f4b176553a4f5097fed0b5f5630d6cb1e5` | `b34f9398` (refs/conformance/olm_native_ae_declared_matrix_54_20260823.json) |
| OLMKiraKira | `d4c9b587d41797259de8627e2d3d5bcf7a376f12fa3c8b99dcd820e0b6d80ae3` | `69e87ce32570ebf299d8a3e94b707321b607ac51de42324e6a0444f490714c4d` | `64d84bc8` (reports/integration_I02_evidence.json) |
| OLMRadialBlur | `9be59d18601dc2b031335f4fec8c8c6a1eb13a4888bf0f228efa65e2d5b676b5` | `0ed4a2f573c1e48471309b3a35209bbefda90d977aee8ddca3b216a94f7014c9` | `b34f9398` (refs/conformance/olm_native_ae_declared_matrix_54_20260823.json) |
| OLMSmoother | `f416579eeb61b73da683437d382f786781e6ecdf27d9c4fc52f3ad1d55577162` | `0c4db1cf1fa6b495ea4644e55332794704d9a3a4a7e94c9b79b7f3e300cc71e3` | `b34f9398` (refs/conformance/olm_native_ae_declared_matrix_54_20260823.json) |
| OLMSmoother2 | `c8ea1f0e7dbe7398006578b91e01adfcea975a8c8a3244657ea934eda587c53f` | `b465f78b5668d6280c0d1d8250fe172af19f63fa79af3bb7a66e0efbcaed7ff5` | `b34f9398` (refs/conformance/olm_native_ae_declared_matrix_54_20260823.json) |
| OLMToonDilate | `cf029885921b6f7cd9ff5ce26ac6c60aa51392cf0bd31d0a721e2a0f6239d029` | `fb51ccf3373bded030b1d3a809d1dc23b2df9270161ac55e0d29cba34201eb9d` | `b34f9398` (refs/conformance/olm_native_ae_declared_matrix_54_20260823.json) |

Every initially failing command is listed below. Class (a) means the failure was
actually fixed and rechecked PASS; (b)/(c)/(d) describe the latest primary failure.
Some unit suites have secondary stale-documentation or missing-input errors;
full stdout/stderr remains available rather than being hidden by this primary
classification. Command IDs match the full-run logs, including the three final
identity checks. They are not individual unittest case counts.

| ID | Lane | Command (Python prefix omitted) | Class | Evidence / attribution |
|---:|---|---|:---:|---|
| 004 | blur | `refs/scripts/audit_olmblur_pf32_formal_worker_matrix_20260805.py` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 006 | blur | `tools/emulation/test_olmblur_classic_public_real_sdk_20260813.py` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 007 | blur | `tests/test_olmblur_classic_public_real_sdk_20260813.py -v` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 008 | blur | `tools/emulation/test_olmblur_smart_public_admission_20260813.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 009 | blur | `tests/test_olmblur_smart_public_admission_20260813.py -v` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 010 | blur | `tools/emulation/test_olmblur_current_installed_public_closure_20260813.py` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 011 | blur | `-m unittest tests.test_olmblur_current_installed_public_closure_20260813` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 012 | blur | `tools/emulation/test_olmblur_pf16_7x5_exported_public_owner_20260813.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 013 | blur | `tests/test_olmblur_pf16_7x5_exported_public_owner_20260813.py -v` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 014 | blur | `tools/emulation/test_olmblur_pf16_7x5_public_admission_20260813.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 015 | blur | `tests/test_olmblur_pf16_7x5_public_admission_20260813.py -v` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 016 | blur | `tools/emulation/test_olmblur_pf16_worker_sources_exported_public_owner_20260813.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 017 | blur | `tests/test_olmblur_pf16_worker_sources_exported_public_owner_20260813.py -v` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 018 | blur | `tools/emulation/test_olmblur_pf16_retained_tuples_exported_public_owner_20260813.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 019 | blur | `tests/test_olmblur_pf16_retained_tuples_exported_public_owner_20260813.py -v` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 020 | blur | `tools/emulation/test_olmblur_pf16_legacy_retained_exported_public_owner_20260813.py --validate-only` | (d) | Obsolete documentation assertion; no numerical comparison failed. |
| 021 | blur | `tests/test_olmblur_pf16_legacy_retained_exported_public_owner_20260813.py -v` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 022 | blur | `tools/emulation/test_olmblur_pf16_worker_sources_public_admission_20260813.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 023 | blur | `tests/test_olmblur_pf16_worker_sources_public_admission_20260813.py -v` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 024 | blur | `tools/emulation/test_olmblur_pf8_retained_exported_public_owner_20260813.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 025 | blur | `tests/test_olmblur_pf8_retained_exported_public_owner_20260813.py -v` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 026 | blur | `tools/emulation/test_olmblur_pf8_retained_public_admission_20260813.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 027 | blur | `tests/test_olmblur_pf8_retained_public_admission_20260813.py -v` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 028 | blur | `tools/emulation/test_olmblur_pf32_retained_public_closure_20260813.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 029 | blur | `tests/test_olmblur_pf32_retained_public_closure_20260813.py -v` | (b) | Stale source/helper/evidence binding; source last changed 810ced04; migrated helper hashes changed in 24e8b60d. |
| 030 | blur | `handoffs/olmblur_retained_public_universal_candidate_v4_20260813/verify_candidate.py` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 031 | blur | `tests/test_olmblur_retained_public_universal_candidate_v4_20260813.py -v` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 032 | colorkeep | `-m unittest tests.test_colorkeep_public_guard_closure_20260812` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 033 | colorkeep | `tools/emulation/test_colorkeep_nine_color_public_closure_20260813.py --validate-only` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 034 | colorkeep | `-m unittest tests.test_colorkeep_nine_color_public_closure_20260813` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 035 | colorkeep | `tools/emulation/test_colorkeep_current_installed_complete_union_20260814.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 036 | colorkeep | `-m unittest tests.test_colorkeep_current_installed_complete_union_20260814` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 037 | colorkeep | `tools/emulation/test_colorkeep_global_setup_actual_aex_20260805.py` | (a) | SDK Util/AEGP_SuiteHandler.cpp and MissingSuiteError.cpp now resolve; recheck PASS. |
| 038 | colorkeep | `tools/emulation/test_colorkeep_params_setup_actual_aex_20260805.py` | (a) | SDK Util source inputs now resolve; recheck PASS. |
| 039 | colorkeep | `tools/emulation/test_colorkeep_global_setdown_actual_aex_20260805.py` | (a) | SDK Util source inputs now resolve; recheck PASS. |
| 040 | colorkeep | `tools/emulation/test_colorkeep_installed_entry_worker_writer_20260805.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 042 | colorkey | `-m unittest tests.test_olmcolorkey_edge_blur_second_source_20260814` | (d) | Pinned typed-iterate worker missing/drifted; historical worker is not in the supplied cache. |
| 043 | colorkey | `tools/emulation/test_olmcolorkey_public_source_bound_closure_20260813.py --validate-only` | (d) | Validator needs missing issue851 worker (same dependency exposed by command 044); source pins also stale. |
| 044 | colorkey | `-m unittest tests.test_olmcolorkey_public_source_bound_closure_20260813` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 045 | colorkey | `tools/emulation/test_olmcolorkey_current_installed_public_closure_20260813.py` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 046 | colorkey | `-m unittest tests.test_olmcolorkey_current_installed_public_closure_20260813` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 047 | colorkey | `-m unittest tests.test_olmcolorkey_real_sdk_suite_lifecycle_20260813 tests.test_olmcolorkey_source_bound_atomic_20260813 tests.test_olmcolorkey_public_entries_real_sdk_20260813` | (d) | First 2,304 output bytes match expected SHA exactly; first source mutation is now admitted (negatives=0). |
| 048 | colorkey | `-m unittest tests.test_olmcolorkey_public_source_bound_docs_20260813` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 049 | directionalblur | `tools/emulation/test_olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.py --validate-only` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 050 | directionalblur | `-m unittest tests.test_olmdirectionalblur_type2_natural64_aexcompat_closure_20260812` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 051 | directionalblur | `tools/emulation/test_olmdirectionalblur_type3_public_owner_boundary_20260814.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 9a0e4eb7; migrated helper hashes changed in 24e8b60d. |
| 052 | directionalblur | `-m unittest tests.test_olmdirectionalblur_type3_public_owner_boundary_20260814` | (b) | Stale source/helper/evidence binding; source last changed 9a0e4eb7; migrated helper hashes changed in 24e8b60d. |
| 053 | directionalblur | `tools/emulation/test_olmdirectionalblur_dual_side_exported_smart_closure_20260814.py --validate-only` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 054 | directionalblur | `-m unittest tests.test_olmdirectionalblur_dual_side_exported_smart_closure_20260814` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 057 | directionalblur | `tools/emulation/test_olmdirectionalblur_exported_smart_remaining6_census_20260814.py` | (a) | MAIN DirectionalBlur decomp input now resolves; recheck PASS. |
| 058 | directionalblur | `-m unittest tests.test_olmdirectionalblur_exported_smart_remaining6_census_20260814` | (a) | MAIN decomp dependency now resolves; recheck PASS. |
| 059 | directionalblur | `tools/emulation/test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814.py` | (b) | Stale source/helper/evidence binding; source last changed 9a0e4eb7; migrated helper hashes changed in 24e8b60d. |
| 060 | directionalblur | `-m unittest tests.test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814` | (b) | Stale source/helper/evidence binding; source last changed 9a0e4eb7; migrated helper hashes changed in 24e8b60d. |
| 061 | directionalblur | `tools/emulation/test_olmdirectionalblur_dual_side_public_source_guard_closure_20260813.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 9a0e4eb7; migrated helper hashes changed in 24e8b60d. |
| 062 | directionalblur | `-m unittest tests.test_olmdirectionalblur_dual_side_public_source_guard_closure_20260813` | (b) | Stale source/helper/evidence binding; source last changed 9a0e4eb7; migrated helper hashes changed in 24e8b60d. |
| 064 | directionalblur | `-m unittest tests.test_olmdirectionalblur_type2_natural64_current_install_smoke_20260812` | (b) | Stale source/helper/evidence binding; source last changed 9a0e4eb7; migrated helper hashes changed in 24e8b60d. |
| 065 | directionalblur | `tools/emulation/test_olmdirectionalblur_current_installed_complete_bounded_union_20260814.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 066 | directionalblur | `-m unittest tests.test_olmdirectionalblur_current_installed_complete_bounded_union_20260814` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 068 | directionalblur | `tools/emulation/test_olmdirectionalblur_ui_setup_actual_aex_20260806.py` | (a) | SDK Util source inputs now resolve; recheck PASS. |
| 083 | directionalblur | `tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py` | (d) | Host adapter exits 38: layer3 err=-1 exact=0 visible=0 pad=1; no raw numerical mismatch established. |
| 091 | directionalblur | `tools/emulation/test_olmdirectionalblur_installed_completion_route_20260805.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 092 | distancegradation | `tools/emulation/test_olmdistancegradation_installed_identity_20260806.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 095 | distancegradation | `tools/emulation/audit_olmdistancegradation_pf16_smart_natural_capture_20260805.py` | (d) | Source-text topology audit still requires old RenderBits dispatch strings; two string predicates false. |
| 097 | distancegradation | `tools/emulation/test_olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.py --validate-only` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 098 | distancegradation | `-m unittest tests.test_olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 099 | distancegradation | `tools/emulation/test_olmdistancegradation_current_installed_mode5_20260813.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 100 | distancegradation | `-m unittest tests.test_olmdistancegradation_current_installed_mode5_20260813` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 101 | distancegradation | `tools/emulation/test_olmdistancegradation_public_smart_owner_contract_20260812.py --validate-only` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 102 | distancegradation | `-m unittest tests.test_olmdistancegradation_public_smart_owner_contract_20260812` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 103 | distancegradation | `tools/emulation/audit_olmdistancegradation_pf32_mode5_universal_codegen_20260812.py --validate-only` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 104 | distancegradation | `-m unittest tests.test_olmdistancegradation_pf32_mode5_universal_codegen_20260812` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 105 | distancegradation | `tools/emulation/test_olm_math_ucrt_batch_request_20260814.py` | (b) | Analyzer SHA changed d5da42b0… → fb79973f… in 744fc49e; package validation now reaches persisted binding comparison. |
| 106 | distancegradation | `-m unittest tests.test_olm_math_ucrt_batch_request_20260814` | (d) | Package exists only in MAIN; tamper tests copy it. Copying MAIN assets is outside the worker authorization. Also stale generator pin. |
| 107 | distancegradation | `tools/emulation/test_olmdistancegradation_same_table_dual_owner_plumbing_20260814.py` | (b) | Stale source/helper/evidence binding; source last changed 90714962; migrated helper hashes changed in 24e8b60d. |
| 108 | distancegradation | `-m unittest tests.test_olmdistancegradation_same_table_dual_owner_plumbing_20260814` | (b) | Stale source/helper/evidence binding; source last changed 90714962; migrated helper hashes changed in 24e8b60d. |
| 109 | distancegradation | `tools/emulation/test_olm_math_ucrt_native_dual_owner_consumer_readiness_20260814.py` | (b) | Stale source/helper/evidence binding; source last changed 90714962; migrated helper hashes changed in 24e8b60d. |
| 110 | distancegradation | `-m unittest tests.test_olm_math_ucrt_native_dual_owner_consumer_readiness_20260814` | (b) | Stale source/helper/evidence binding; source last changed 90714962; migrated helper hashes changed in 24e8b60d. |
| 111 | distancegradation | `tools/emulation/test_olm_native_ucrt_promotion_table_readiness_20260814.py` | (b) | Stale source/helper/evidence binding; source last changed 90714962; migrated helper hashes changed in 24e8b60d. |
| 112 | distancegradation | `-m unittest tests.test_olm_native_ucrt_promotion_table_readiness_20260814` | (b) | Stale source/helper/evidence binding; source last changed 90714962; migrated helper hashes changed in 24e8b60d. |
| 114 | kirakira | `tools/emulation/test_olmkirakira_public_smart_bounded_closure_20260812.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 3ca06908; migrated helper hashes changed in 24e8b60d. |
| 115 | kirakira | `-m unittest tests.test_olmkirakira_public_smart_bounded_closure_20260812` | (b) | Stale source/helper/evidence binding; source last changed 3ca06908; migrated helper hashes changed in 24e8b60d. |
| 116 | kirakira | `tools/emulation/test_olmkirakira_classic_smart_admission_guard_20260812.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed 3ca06908; migrated helper hashes changed in 24e8b60d. |
| 117 | kirakira | `-m unittest tests.test_olmkirakira_classic_smart_admission_guard_20260812` | (b) | Stale source/helper/evidence binding; source last changed 3ca06908; migrated helper hashes changed in 24e8b60d. |
| 118 | kirakira | `-m unittest tests.test_olmkirakira_smart_workspace_dependency_manifest_20260812` | (b) | Stale source/helper/evidence binding; source last changed 3ca06908; migrated helper hashes changed in 24e8b60d. |
| 119 | kirakira | `tools/emulation/test_olmkirakira_current_installed_public_closure_20260813.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 120 | kirakira | `-m unittest tests.test_olmkirakira_current_installed_public_closure_20260813` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 126 | kirakira | `-m unittest tests.test_olmkirakira_mode3_32x18_public_failclose_20260814` | (d) | Old Mode3 rejection contract: PF8=10 PF16=10 PF32=10; setup fails before numerical comparison. |
| 127 | kirakira | `-m unittest tests.test_olmkirakira_mode3_32x18_public_closure_20260814` | (d) | Historical AEXCompat worker missing; no new worker was substituted or rebuilt. |
| 128 | kirakira | `tools/emulation/test_olmkirakira_mode3_nonwhitelist_production_20260806.py` | (d) | Obsolete exact source-string assertion for RotatedAxisBoxBlur call. |
| 134 | kirakira | `tools/emulation/test_olmkirakira_mode4_cropped_typed_installed_20260805.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 135 | kirakira | `tools/emulation/test_olmkirakira_mode4_mac_ae_runner_preflight_20260805.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 137 | kirakira | `tools/emulation/test_olmkirakira_merge2_mac_production_boundary_20260805.py` | (d) | Source-text audit mode2_typed_truncate is false; other 11 audited predicates true. |
| 152 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf32_size_variation_opaque_actual_aex_20260810.py` | (c) | Size1: 83 output bytes; f3765f38 first refused, ea3a16c5 re-admitted with differences (parent refuses). |
| 153 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf32_noise_variation_type1_actual_aex_20260810.py` | (c) | NV0: 83 output bytes; first bad f5a74754, parent 6d0904f8 exact. |
| 155 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf32_ellipse_actual_aex_20260811.py` | (c) | Ratio2/Angle0 9x7: 82 output bytes; f5a74754 parent exact. |
| 156 | radialblur | `tools/emulation/test_olmradialblur_pf32_ellipse_32x18_actual_aex_20260811.py` | (c) | Ratio2/Angle0 32x18: 674 output bytes; f5a74754 parent exact; Zoom cells pass. |
| 157 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf32_strength5_noise_type1_actual_aex_20260810.py` | (c) | Strength5/NV25: 85 output bytes; f5a74754 parent exact. Also obsolete negative controls. |
| 158 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf32_offset_mode3_noise_type1_actual_aex_20260810.py` | (c) | OffsetMode3/Offset2/NV25: 4 output bytes; f5a74754 parent exact. Also obsolete negatives. |
| 159 | radialblur | `tools/emulation/test_olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810.py` | (c) | Zoom Inner50/NV25: 48 output bytes; b07f5c00 first bad, parent 47b8632a exact. |
| 162 | radialblur | `tools/emulation/test_olmradialblur_unsupported_variation_fail_closed_20260806.py` | (d) | Old unsupported-variation rejection probe exits 1; current broadened admission is not a raw-output comparison. |
| 163 | radialblur | `tools/emulation/test_olmradialblur_unproven_geometry_fail_closed_20260811.py` | (d) | Old unproven-geometry rejection probe exits nonzero; assertion is rejection behavior. |
| 164 | radialblur | `tools/emulation/test_olmradialblur_case0009_pf32_ae_control_replay_20260806.py` | (d) | PF32 full-frame production entry refuses (rc=3) before output comparison; numerical result unavailable. |
| 165 | radialblur | `tools/emulation/test_olmradialblur_case0010_rotation_mac_production_planes_20260805.py` | (c) | Retained full PF8: final output exact; 1,801,691 accum and 95,441 normalized words differ; f5a74754 parent exact. |
| 167 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf16_small_actual_aex_20260805.py` | (c) | PF16 neutral: 2 output bytes; f5a74754 parent exact. |
| 168 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf32_small_actual_aex_20260805.py` | (c) | PF32 neutral: 83 output bytes; f5a74754 parent exact. |
| 169 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf32_edge_fade_actual_aex_20260811.py` | (c) | OuterFade50: 102 output bytes at HEAD, 85 at f5a74754; its parent exact. |
| 170 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf32_edge_fade_intersections_actual_aex_20260811.py` | (c) | OuterFade50/NV25: 50 output bytes; 7a7f53fe first bad, parent bed824a7 exact. |
| 171 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf32_strength5_small_actual_aex_20260805.py` | (c) | PF32 Strength5: 9 output bytes; f5a74754 parent exact. |
| 172 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf16_strength5_small_actual_aex_20260805.py` | (c) | PF16 Strength5: final output exact; 2,105 accum bytes differ; f5a74754 parent exact. |
| 174 | radialblur | `tools/emulation/test_olmradialblur_zoom_pf16_strength5_small_actual_aex_20260805.py` | (c) | Zoom PF16 Strength5: final output exact; 10,373 post-blur bytes differ; b07f5c00 parent exact. |
| 178 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf32_offset_mode3_ui3_small_actual_aex_20260805.py` | (c) | PF32 OffsetMode3/Offset3: 1 output byte; f5a74754 parent exact. |
| 179 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf32_offset_mode3_ui4_small_actual_aex_20260805.py` | (c) | PF32 OffsetMode3/Offset4: 41 output bytes; f5a74754 parent exact. |
| 181 | radialblur | `tools/emulation/test_olmradialblur_rotation_pf16_offset_mode3_ui3_small_actual_aex_20260805.py` | (c) | PF16 OffsetMode3/Offset3: final output exact; 229 accum bytes differ; f5a74754 parent exact. |
| 183 | radialblur | `tools/emulation/test_olmradialblur_zoom_pf32_small_actual_aex_20260805.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 184 | radialblur | `tools/emulation/test_olmradialblur_type3_host_plumbing_20260811.py` | (d) | Host mock exits 10 at first Type3 SmartPreRender/event-order check, before render comparison. |
| 185 | radialblur | `tools/emulation/test_olmradialblur_rotation_type1_inverse_cell_closure_20260812.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed d8eff1dd; migrated helper hashes changed in 24e8b60d. |
| 186 | radialblur | `-m unittest tests.test_olmradialblur_rotation_type1_inverse_cell_closure_20260812` | (b) | Stale source/helper/evidence binding; source last changed d8eff1dd; migrated helper hashes changed in 24e8b60d. |
| 187 | radialblur | `tools/emulation/test_olmradialblur_strength290_exported_math_boundary_20260814.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed d8eff1dd; migrated helper hashes changed in 24e8b60d. |
| 188 | radialblur | `-m unittest tests.test_olmradialblur_strength290_exported_math_boundary_20260814` | (b) | Stale source/helper/evidence binding; source last changed d8eff1dd; migrated helper hashes changed in 24e8b60d. |
| 189 | radialblur | `tools/emulation/test_olmradialblur_strength290_ucrt_math_request_20260814.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed d8eff1dd; migrated helper hashes changed in 24e8b60d. |
| 190 | radialblur | `-m unittest tests.test_olmradialblur_strength290_ucrt_math_request_20260814` | (d) | Historical request package absent in worktree; tamper tests copy directory/ZIP; source provenance pin also stale. |
| 191 | radialblur | `tools/emulation/test_olmradialblur_strength290_native_ucrt_exported_public_boundary_20260815.py` | (b) | Stale source/helper/evidence binding; source last changed d8eff1dd; migrated helper hashes changed in 24e8b60d. |
| 192 | radialblur | `-m unittest tests.test_olmradialblur_strength290_native_ucrt_exported_public_boundary_20260815` | (b) | Stale source/helper/evidence binding; source last changed d8eff1dd; migrated helper hashes changed in 24e8b60d. |
| 193 | radialblur | `tools/emulation/test_olmradialblur_type3_layer_span_natural_closure_20260812.py --validate-only` | (b) | Stale source/helper/evidence binding; source last changed d8eff1dd; migrated helper hashes changed in 24e8b60d. |
| 194 | radialblur | `-m unittest tests.test_olmradialblur_type3_layer_span_natural_closure_20260812` | (b) | Stale source/helper/evidence binding; source last changed d8eff1dd; migrated helper hashes changed in 24e8b60d. |
| 195 | radialblur | `tools/emulation/test_olmradialblur_type3_all_depth_public_closure_20260813.py` | (b) | Stale source/helper/evidence binding; source last changed d8eff1dd; migrated helper hashes changed in 24e8b60d. |
| 196 | radialblur | `-m unittest tests.test_olmradialblur_type3_all_depth_public_closure_20260813` | (b) | Stale source/helper/evidence binding; source last changed d8eff1dd; migrated helper hashes changed in 24e8b60d. |
| 197 | radialblur | `tools/emulation/test_olmradialblur_current_installed_type3_all_depth_closure_20260813.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 198 | radialblur | `-m unittest tests.test_olmradialblur_current_installed_type3_all_depth_closure_20260813` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 199 | radialblur | `-m unittest tests.test_olmradialblur_smart_cleanup_candidate_20260813` | (d) | Required historical worker/handoff absent; see missing-input inventory. Some suites also report stale pins. |
| 200 | radialblur | `tools/emulation/test_olmradialblur_smartrender_fullpath_connection_20260805.py` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 201 | smoother | `installed-identity-manifest OLMSmoother` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 202 | smoother2 | `installed-identity-manifest OLMSmoother2` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |
| 203 | toondilate | `installed-identity-manifest OLMToonDilate` | (b) | Installed/source authority drift; proposed full hashes and historical receipt commits in binding-candidates.json. |

inference:

The asset-resolution changes substantially improve execution coverage, but a red
identity gate is not evidence that the installed binary is numerically wrong.
The numerical boundaries overlap deliberate native-trace restorations; resolving
whether the old host-substitute oracle or newer production arithmetic is the
correct Windows behavior requires a separate numerical ticket. No retuning or
repinning is justified by this triage alone. The named historical build inputs,
copy-dependent tamper suites, and unbound installed KiraKira provenance prevent
claiming the full requested worktree/commit-attribution closure, hence `blocked`.

changed_files:

- `scripts/run_olm_mac_fixed_fixture_regression_20260805.py`
- `tools/emulation/olm_assets.py` and `tests/test_olm_assets.py`
- Reachable Python input consumers and installed identity manifest reader;
  187 code/test files total, mainly mechanical input-path wrapping/bootstrap.
- `orchestra/reports/F36-*` report, command table, JSON inventories, evidence
  archive, and reproducibility scripts.
- Exact complete path inventory: `orchestra/reports/F36-changed-files.txt`.

No plugin C++ implementation, release gate, ledger, pin, or expected fixture is
in the diff. The run generated changes to 29 conformance report files; these
were archived as diagnostics and restored byte-for-byte from HEAD. Regenerable
source/build trees were deleted; retained scratch is about 2.9 MiB. MAIN and
external emulator sources were not modified.

verify:

Run from this worktree. All temporary storage is inside the ticket directory.

```sh
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/orchestra/state/F36-fixture-runner-worktree-and-triage"
export TMP="$TMPDIR" TEMP="$TMPDIR"
mkdir -p "$TMPDIR"
python3 -B -m unittest tests.test_olm_assets -v
python3 -B scripts/run_olm_mac_fixed_fixture_regression_20260805.py --results-dir "$TMPDIR/verify"
```

Expected: 4 unit tests PASS; full runner remains nonzero, with the combined
observed baseline 76 PASS / 125 command FAIL, 3 identity FAIL, 89 skipped. This
expectation assumes the installed binaries and external assets remain unchanged.
The default suite does not request the opt-in slow full Radial Unicorn replay.
Some legacy commands regenerate worktree conformance reports; inspect/restore
those generated diffs rather than treating them as new expectations.

Numerical reproductions (use the resolved MAIN venv by absolute path):

```sh
PY="/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python3"
"$PY" -B orchestra/reports/F36-bisect-radial.py > "$TMPDIR/verify-neutral.log" 2>&1
"$PY" -B orchestra/reports/F36-probe-radial-boundaries.py > "$TMPDIR/verify-boundaries.log" 2>&1
"$PY" -B orchestra/reports/F36-bisect-radial.py --label fadeintersection --outer-fade 50 --noise 25 --good f5a74754 > "$TMPDIR/verify-fade.log" 2>&1
"$PY" -B orchestra/reports/F36-bisect-radial.py --label zoominner --zoom --inner-strength 50 --noise 25 --good 'f3765f38^1' > "$TMPDIR/verify-zoom.log" 2>&1
"$PY" -B orchestra/reports/F36-bisect-radial.py --label zoom16strength5 --zoom --depth 16 --strength 5 --good 'f3765f38^1' > "$TMPDIR/verify-zoom16.log" 2>&1
"$PY" -B orchestra/reports/F36-bisect-radial.py --label sizeone --size 1 --revision 'f3765f38^1' --revision f3765f38 --revision 'ea3a16c5^1' --revision ea3a16c5 --revision 24e8b60d > "$TMPDIR/verify-size.log" 2>&1
"$PY" -B orchestra/reports/F36-probe-retained-planes.py > "$TMPDIR/verify-full-planes.log" 2>&1
python3 -B orchestra/reports/F36-probe-colorkey.py > "$TMPDIR/verify-colorkey.log" 2>&1
```

Expected numerical boundaries/counts are in the table above. The ColorKey probe
intentionally exits 1 and preserves the original failing assertion while exposing
its captured stdout/stderr. Run these sequentially, not alongside more than one
other emulator/build job. The endpoint source snapshot defaults are pinned to
this task's base, not a later potentially changed HEAD.

Retained archive: `F36-evidence.tar.gz`, 199,451 bytes,
SHA-256 `ab1560c153934534a29a4306cad07f3dd515c3f1cfba8179f38ce1f76311e8aa`.
It contains complete command logs, per-command statuses, bisection records, and
generated diagnostic JSON, but no AEX, venv, worker binary, or build tree.
To regenerate the command table from retained evidence:

```sh
tar -xzf orchestra/reports/F36-evidence.tar.gz -C "$TMPDIR"
python3 -B orchestra/reports/F36-triage.py
python3 -B orchestra/reports/F36-collect-identities.py
git diff --check
```

Expected table counts: `(a)=6, (b)=72, (c)=18, (d)=38`; 89 skipped commands remain
unexecuted. Identity collection is read-only apart from writing its report.

next:

1. Supply the exact historical worker/handoff assets or authorize replacing the
   obsolete tests with newly bound evidence; do not silently substitute cached
   workers of another identity.
2. Decide how copy-based package tamper tests should run under the no-copy worker
   rule, and bind the installed KiraKira binary to a reproducible build receipt.
3. Reconcile the three numerical boundaries against their native-trace evidence,
   separately tracking final output differences and intermediate-only differences.
   Preserve the Size1 refusal/re-admission history.
4. Review the proposed identity values; only then regenerate justified bindings
   and repeat the complete suite. Investigate host-adapter refusals separately.
