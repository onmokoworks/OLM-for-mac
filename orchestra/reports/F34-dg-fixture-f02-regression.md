status: done
summary:
- Disposition: the retained expectations are internal AEX-probe artifacts, not valid same-contract public-render truth. Do not change them or revert F02 on their authority.
- Both current default and F30 workers reproduce current Mac Smart exactly for both fixture inputs at the regression harness's settings.
- Public Classic is a separate unresolved contract: both workers return zero buffers; current Mac Classic differs. No claim of Classic closure is made.
- No production, expected bytes, corpus, release gate, or ledger was changed. Orchestrator decides how to retire/replace the obsolete regression.

facts:
- Audited HEAD `9c20b67ad78d6a592d8efebf1295e57bbe1f1077` on `orch/F34-dg-fixture-f02-regression`.
- `git log --oneline -- refs/fixtures/olmdistancegradation_pf32_owner_17x11_20260805` identifies introduction at `743500fb927ee499dce6b78dde83321267b2dac2` (2026-08-06).
- Generator: `tools/emulation/probe_olmdistancegradation_pf32_owner_20260805.py`, direct call to internal `FUN_181172a10`, not exported EffectMain. Its artifact-writing block stores the original emulator output, not Mac output.
- Provenance: `refs/conformance/olmdistancegradation_pf32_owner_probe_20260805.json` and `_controlled_source_20260805.json`. Both recorded output hashes match the committed fixture bytes (checked by the new audit). Original AEX SHA-256 is `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`, also verified by the current public adapter.
- First fixture's recorded checkout values are slots 5/6/9 = **0/0/1**; the retained Mac regression requests **1/1/2** (RGB/background enabled/Linear). Its old color shim supplies the same purple floating color for both colors; the Mac regression requests a red background. Thus the first fixture does not bind the tested parameter tuple.
- Both old logs acquire only ColorParamSuite and Handle Suite, never iterateFloat. The old acquire callback returns Handle Suite for every non-Color request. The later corrected public contract (`refs/conformance/olmdistancegradation_public_smart_owner_contract_20260812.md`) explicitly identifies Smart → `181173d20` → `181172a10` → iterateFloat → `181170c90`. Direct owner invocation and completion alone did not prove that public contract.
- `PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/F34-compare-fixtures.py` exited 0, twice. It uses the original typed 2992-byte inputs, all 12 explicitly bound controls matching the retained regression, full 17×11 worlds, origin zero, downsample 1:1, no blur, raw ARGB FLOAT32. It compiles current production, runs Classic and Smart separately, and checks worker setup declarations, route, output guards/checksum/size and session cleanup. It saves raw outputs in ticket scratch and the full identity/first-mismatch evidence in `F34-fixture-evidence.json`.
- Default worker hash: `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. F30 INDEX worker hash: `8b51d0456ff55aa2034a0bbb00b822bd2339cbe27247021c289170a78a3fb53b`. Default and F30 outputs agree for every corresponding route/input (4/4). No worker rebuilt.

Byte comparisons (each output 2992 bytes; same results on both workers):

| Input | Mac Classic vs retained | AEX Classic vs retained | AEX Smart vs retained | AEX Smart vs Mac Smart |
| --- | ---: | ---: | ---: | ---: |
| zero | 748 | 0 | 748 | 0 |
| controlled | 0 | 1664 | 1818 | 0 |

- Zero: first Mac Classic / retained mismatch is byte offset **2**, pixel (0,0), **A**: bytes 128 / 0; words `0x3f800000` / `0x00000000` (1.0 / 0.0). AEX Smart has the same mismatch against retained. AEX Classic returns all zeros on **both** inputs; its equality to the first all-zero expected file does not establish the old whole-owner contract.
- Controlled: first AEX Classic / retained mismatch is offset **2**, pixel (0,0), **A**: bytes 0 / 128; words `0x00000000` / `0x3f800000` (0.0 / 1.0). First AEX Smart / retained mismatch is offset **4**, pixel (0,0), **R**: bytes 225 / 0; words `0x3de0e0e1` / `0x3f800000` (0.10980392247438431 / 1.0).
- Zero expected/source hash: `cda258b2a722a9336224ca9bb3997f0761213a8dac68d24b5fed88d80f18e2a3`. Zero Mac Classic/Smart and AEX Smart hash: `a793be73e5af89ff7572bcd6750c102ad3ccf6fa8c7a055c5f8cef4574947679`.
- Controlled expected/Mac Classic hash: `c014b5d14d68e4ec6ce49592029067f6415bce31366a7f66694ecb9eb57c8540`; public AEX/Mac Smart hash: `766f4fbde7835110aa3bf782024beec13f9cd2afe2c932fd83c63fcdde603034`. All input/worker/production dependency hashes are committed in the evidence JSON.
- Existing `test_olmdistancegradation_pf32_effectmain_fixture_20260805.py` still exits 1: `AssertionError: byte mismatches=748`. Its first-failure short circuit does not inspect fixture two; the new audit does.
- No production change was justified by this invalid-reference outcome, so no n300 or corpus replay is claimed or needed to validate changed production. Existing F02/C14/C19/C27 behavior and all corpus bytes are untouched.

inference:
- The retained regression conflates a historical internal-owner shim contract with a production Classic call, and the zero-source row additionally conflates parameter tuples. These expectations cannot adjudicate public output correctness. They really were emitted by AEX, but not under the tested public contract; calling them an old Mac capture would be incorrect.
- F02's changed zero-source background output is supported by both current public Smart workers. Reverting the uniform-mask handling to satisfy this fixture would discard that evidence.
- Public Classic differences are real data, not fixed by this ticket's invalid-reference disposition. The previously documented exported Render boundary says Classic has no PF32 target; a zero output is not sufficient evidence to implement a whole-render zero fill. Resolving Classic requires that owner/staging contract, not a per-fixture override.

changed_files:
- `orchestra/reports/F34-compare-fixtures.py` — reproducible read-only audit with scratch-only builds/outputs and assertions for paired worker equality and Smart exactness.
- `orchestra/reports/F34-fixture-evidence.json` — full current comparison and provenance.
- `orchestra/reports/F34-dg-fixture-f02-regression.md` — this report.

verify:
```sh
mkdir -p orchestra/state/F34-dg-fixture-f02-regression
export TMPDIR="$PWD/orchestra/state/F34-dg-fixture-f02-regression"
export TMP="$TMPDIR" TEMP="$TMPDIR" PYTHONDONTWRITEBYTECODE=1
python3 orchestra/reports/F34-compare-fixtures.py > "$TMPDIR/comparison.log" 2>&1
# Expected exit 0; comparisons as table above, 4/4 AEX-vs-Mac Smart exact.
python3 tools/emulation/test_olmdistancegradation_pf32_effectmain_fixture_20260805.py > "$TMPDIR/retained.log" 2>&1
# Expected exit 1, byte mismatches=748. This retained expectation is intentionally unchanged.
git diff --check
# Expected exit 0.
```
The audit uses one process at a time; it removes its compiled binary. No native AE or Windows execution is claimed.

next:
- Orchestrator: classify/replace the retained regression using the corrected public Smart contract; preserve its historical artifacts rather than editing expected bytes in place.
- Separate Classic owner/staging follow-up: determine intended PF32 Classic contract and reconcile the existing legacy Mac whole-owner path. Include the controlled fixture, whose apparent retained pass currently disagrees with both public AEX routes.
