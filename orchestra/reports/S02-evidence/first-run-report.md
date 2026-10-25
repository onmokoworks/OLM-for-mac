status: blocked
summary:
- Removed Smoother2's Mac-only float-vs-byte equality refusal; read only enabled Key Color and active Gamma Colors through the float suite.
- Default seed 1/n300: 300 Smart exact, 0 pixel mismatches; 300 unchanged Classic refusals.
- Added opt-in float colour sampling, source fake-host transport and an isolated F53/F54 worker build recipe; float oracle coverage is NOT validated.
- Two build-path hypotheses failed at QEMU's spaces-in-path restriction. Stopped under the ticket stop rule.
- Do not merge as accepted S02: float campaigns, actual-AE float witness, all-corpus replay and ref_vs_fast remain outstanding.

facts:

Original render-path analysis (retained exact decompiler excerpts and source SHA-256 in `S02-evidence/original-colour-read.txt`):
- Smart builder `0x180004e10` reads version, then Enable Key. If enabled, it reads Invert Key and Key Color (disk ID 2) through `0x1800014a0 -> 0x180007540 -> 0x180016660`.
- The last function acquires `PF ColorParamSuite` version 1, calls its first function (floating-point colour), checks the returned error, and releases the suite. The parameter is checked out before this call and checked in afterwards.
- After smoothing controls, the builder reads Gamma mode/value. For Gamma Colors mode it reads the count, then colour disk IDs 10 onward in ascending order. Public slots differ from disk IDs because Invert Key was inserted earlier in the UI.
- These render colour reads use the floating-point suite; no comparison with `u.cd.value/255` occurs on this path. The separate byte getter `0x180016600` reads the byte colour, but is not called by this builder's colour getter.
- Mac FetchParams already used the float suite, but fetched all six colours unconditionally. SmartRender then rejected any float/byte disagreement, including unused colours. The change removes that comparison and follows the original's enabled-key/active-palette selection.
- The A02h corpus witness has Enable Key=0 and Gamma mode=None. Its colours are unused by the original render builder. This ticket did not capture AE's actual floating-point colour values and does not claim to have reproduced them.

Other-plugin audit:
- Ran `rg -n 'u.cd.value|GetFloatingPointColor' mac --glob '*.cpp'` and inspected colour/memcmp references in ColorKeep, OLMColorKey, OLMDistanceGradation and OLMKiraKira.
- No second general float-must-equal-byte/255 guard was found. Smoother v1 reads bytes directly. ColorKeep and ColorKey retain both byte and float representations; DistanceGradation/ColorKey also have historical fixed-fixture predicates. Those are not the same general equality guard and were not changed.

Commands and real results:
1. `python3 tools/emulation/aexcompat_patches/build_S02.py --parent F53` (first version, direct scratch path): exit 1. QEMU configure: `main directory cannot contain spaces nor colons`. Also exposed an overbroad copy exclusion that removed QEMU's `target` directory; that exclusion was corrected.
2. Same command with a space-free symlink to worktree scratch: exit 1. Configure still rejected spaces (resolved working directory); compilation subsequently failed with `typedef redefinition with different types ('Int128' ... vs '__int128')`. Logs retained as `build-F53-first.log` and `build-F53.log`. No worker was installed or registered. F54 build was not attempted.
3. From this worktree:
   `TMPDIR="$PWD/orchestra/state/S02-smoother2-float-color-guard" python3 tools/fuzz/run.py --plugin olmsmoother2 --n 300 --seed 1 --jobs 1 --budget-minutes 30 --scratch "$PWD/orchestra/state/S02-smoother2-float-color-guard/default" --report orchestra/reports/S02-evidence/default.json --corpus "$PWD/orchestra/state/S02-smoother2-float-color-guard/corpus" --shrink-attempts 0`
   Exit 0, completed 300. Smart exact=300, pixel_mismatch_cases=0, Classic refusal=300, AEX Classic/Smart success=300 each. No first Smart mismatch or refusal. Report retained losslessly as `default.json.gz`; no corpus or historical result was rewritten.
4. `git diff --check`: exit 0.

Default run identities:
- AEX SHA-256: `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`
- Existing F46 worker SHA-256: `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`
- Candidate SHA-256: `159089f735bd1866f7843be9d28271e5a34bc70e9d3fcfe13ede02874eaf23e6`
- Full dependency bindings and all 300 comparisons are in the compressed report.

inference:
- The removed check is an unsupported Mac admission restriction. The conditional fetch should also avoid the A02h refusal for unused colours regardless of their float values. Native AE success has not been measured here.
- The second worker failure is consistent with QEMU resolving the symlink to the space-containing directory, leaving generated configuration incomplete. No third build hypothesis was attempted.
- The 300/300 default result preserves exactness for this sampled set only. It is not evidence for independent float colours, native AE, all corpora or reference/fast equivalence.

changed_files:
- `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`: active float reads and removal of equality guard.
- `cli/OLMSmoother2/shim/OLMSmoother2.h`: explicit optional float colour in test parameter definitions.
- `tools/emulation/olmsmoother2_public_key_gamma_harness_20261001.cpp`: opt-in C record carrying bytes plus float ARGB; old c records unchanged.
- `tools/fuzz/adapters/olmsmoother2.py`: independent `float-v1` RNG stream and candidate serialization.
- `tools/fuzz/adapters/public.py`: optional slot-indexed float fixture to a capability-marked S02 worker. Rejects unqualified workers and unsupported bundle bridge rather than silently ignoring floats.
- `tools/fuzz/core.py`: persist sampler identity for procedural replay; old corpus replay defaults to the original sampler.
- `tools/fuzz/run.py`: `--color-sampler default|float-v1` (Smoother2 only) and report metadata.
- `tools/emulation/aexcompat_patches/build_S02.py`: WIP isolated F53/F54 copies with an opt-in suite callback fixture; recipe is currently blocked by the host build environment. No original AEX algorithm is patched.
- This report and `orchestra/reports/S02-evidence/`.

verify:
```sh
mkdir -p orchestra/state/S02-smoother2-float-color-guard
export TMPDIR="$PWD/orchestra/state/S02-smoother2-float-color-guard"
export PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmsmoother2 --n 300 --seed 1 --jobs 1 \
  --budget-minutes 30 --scratch "$TMPDIR/recheck-default" \
  --report "$TMPDIR/recheck-default.json" --corpus "$TMPDIR/recheck-corpus" \
  --shrink-attempts 0 > "$TMPDIR/recheck-default.log" 2>&1
# Expected: completed 300; Smart exact 300; pixel mismatches 0; Classic refusals 300.
python3 - <<'PY'
import gzip,json
r=json.load(gzip.open('orchestra/reports/S02-evidence/default.json.gz','rt'))
assert r['completed']==300
assert r['summary']['smart_exact']==300
assert r['summary']['pixel_mismatch_cases']==0
print(r['summary'])
PY
git diff --check
```
The float campaign command must wait for a qualified, installed worker:
`python3 tools/fuzz/run.py --plugin olmsmoother2 --color-sampler float-v1 --worker ~/.cache/olm-emu/worker-S02-F53/aex-guest-worker --seed 1 --n 100 --jobs 1 --scratch "$TMPDIR/float-seed1" --report "$TMPDIR/float-seed1.json" --corpus "$TMPDIR/float-corpus"`.
There is no expected measured result for that command yet. Repeat several seeds, each depth explicitly, with both F53 and F54, and verify actual suite-value delivery and sensitivity before claiming acceptance.

next:
- Resolve the QEMU build-path problem while retaining ticket scratch constraints, or assign an oracle-worker prerequisite ticket. Parent emulator checkouts remain read-only.
- Compile/qualify the fixture patch for both worker families; register successful workers with source hashes under ~/.cache/olm-emu. Validate slot mapping, default worker equivalence and non-byte colour delivery before pixel comparison.
- Capture the actual AE float colours for A02h; replay that exact witness, then the requested Smart PF8/16/32 campaigns (several seeds, n100).
- Run all Smoother2 corpora and reference/fast comparisons. Add focused colour-order/error/callback and procedural-replay tests. Bundle-host independent floats are intentionally rejected until implemented.
- No background processes remain. Build trees were removed; scratch is 32 KiB. Empty worker directory and temporary path alias were removed. No writes to MAIN, release gates, ledger or emulator source checkouts; no push.
