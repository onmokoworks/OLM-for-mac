status: blocked
summary:
- Both retained realistic-v2 RadialBlur Smart mismatches reproduce byte-for-byte.
- Both routes are recorded in a new labelled, unresolved corpus; replay matches saved results for 2/2.
- No production change or original-bug exemption is justified by the available intermediate evidence.
- F53 geometry replay succeeds but produces no C53b watch trace; C53b rejects geometry arguments.
- Geometry-stripped C53b probes crash before the watched processing stages, so they cannot substitute for the original witnesses.

facts:
- Read AGENT_GUIDE.md, emulation GOTCHAS, RadialBlur ledger row, P02d/P03b/C46/C57 evidence and relevant original decompilation. MAIN and emulator sources remained read-only.
- Standard replay command, once for each NAME below (TMPDIR set to the ticket scratch):
  `python3 tools/fuzz/run.py --plugin radialblur --geometry realistic-v2 --jobs 1 --replay orchestra/reports/nightly-20261025/witnesses/NAME.json --scratch "$TMPDIR/replayTAG" --report "$TMPDIR/replayTAG.json"`
- NAME `403be984da1ad8593fa159b4`, TAG `403`: Smart PF32 mismatch, 64 differing words / 168 bytes, first word 0, original `00000000`, candidate `ca93803f`. Original SHA256 `5341e6b2646979a70e57653007a1f310169421ec9bdd9f1a5648f75ade005af1`; candidate `0b1a0fb57f978ba0ea2a2ec66a4dae56eb0c2f51f9303fe7a1fb49c35cb440d3`.
- NAME `ab18858afb75411545de86c7`, TAG `ab`: Smart PF16 mismatch, 40 differing words / 54 bytes, first word 0, original `0000`, candidate `f912`. Original SHA256 `5b6fb58e61fa475939767d68a446f97f1bff02c0e5935a3ea8bb51e6515783d8`; candidate `ee831fd1a52ccbb49bf9d57820878689bff8b227b0db19043638866a3558ad02`.
- Both Classic candidates return 516 with successful original renders. These routes are recorded separately under the existing T14 SmartFX decision; they were absent from the nightly Smart-only witness result.
- Both initial replay commands exit 1 / replay_matches_saved=false because standard replay adds Classic and per-route oracle records to the saved Smart-only result. Smart diff objects and hashes reproduce exactly. Labelled replay, retaining both routes, exits 0 / replay_matches_saved=true for 2/2. This means stable mismatches, NOT exact output.
- F53 worker SHA256 `d88c22f67d06c419608d007619df42eac863a35e317ab7cb380617eff2051fb9`; original AEX SHA256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- `python3 orchestra/reports/N02-evidence/trace.py --mode geometry`: 2/2 original output hashes bind, 0 trace files. Watch configuration covers typed noise helpers 65C0/6AA0 and Zoom 56F0, context and source-size/span/final allocations.
- Same script `--mode legacy`: retained C53b trace worker rejects both geometry-bearing invocations with usage exit 2; no trace. No worker was rebuilt.
- Same script `--mode normalized`: removes geometry fields explicitly (therefore NOT the same witness). Both C53b calls fail with UC_ERR_WRITE_UNMAPPED at RVA `0xDA65`, destinations `0x1000000001` and `0x1200000001`; no processing trace. These are not output-bound evidence for the nightly cases.
- Static MAIN decomp `FUN_1800065c0`/`FUN_180006aa0` skips span writes for Type 3 with null layer; C46/C57 already describe that undefined allocation/stack-pointer family. No newly captured read address or byte value connects the nightly mismatches to that family.
- No mathematical patch hypothesis was tested/refuted. Two failed instrumentation approaches and a changed-geometry probe are recorded above; the two-refuted-mathematical-hypotheses stop rule is not asserted as triggered.
- Acceptance campaigns (three n200 seeds, default n300, all older corpora, ref_vs_fast) were NOT run: the original failing witnesses remain unresolved, and there is no candidate fix to validate. R10 split and earlier production fixes are unchanged.

inference:
- Both witnesses have width 1 and Noise Type 3. The earlier undefined layer/span behavior is a plausible lead, not a diagnosis of these mismatches.
- The current blocker is obtaining geometry-preserving, output-bound original intermediate captures. Substituting zeros or granting an original-bug exemption from final outputs alone would be unsupported.
- A trace-enabled F53-compatible retained worker, or an equivalent original trace that preserves its geometry and hashes, is the next useful boundary. C53b alone is not interchangeable with F53.

changed_files:
- `tests/fuzz_corpus/radialblur_N02-nightly-20261025/*.json`: two unresolved labelled witnesses, both routes retained.
- `orchestra/reports/N02-evidence/trace.py`: reproducible three-mode read-only trace probe.
- `orchestra/reports/N02-evidence/{replay403,replayab,labelled}.json`: standard replay results.
- `orchestra/reports/N02-evidence/recheck-*/*/result.json`: six trace-attempt results with worker/input/AEX hashes.
- `orchestra/reports/N02-radialblur-nightly-20261025.md`.

verify:
```sh
export TMPDIR="$PWD/orchestra/state/N02-radialblur-nightly-20261025"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
python3 tools/fuzz/run.py --plugin radialblur --geometry realistic-v2 --jobs 1 --replay tests/fuzz_corpus/radialblur_N02-nightly-20261025 --scratch "$TMPDIR/verify-labelled" --report "$TMPDIR/verify-labelled.json" > "$TMPDIR/verify-labelled.log" 2>&1
for mode in geometry legacy normalized; do
  python3 orchestra/reports/N02-evidence/trace.py --mode "$mode" > "$TMPDIR/verify-trace-$mode.log" 2>&1
done
git diff --check
```
Expected: labelled replay exits 0, replay_matches_saved=true for 2/2, with the two Smart mismatches and two Classic refusals above. Trace script reports 2 successful hash-bound originals without traces in geometry mode; 2 argument rejects in legacy mode; 2 unbound memory-write crashes in normalized mode. No exactness claim follows from these results.

next:
- Supply/build an F53-geometry-compatible watch worker in a dedicated instrumentation ticket, using the prescribed space-free build/cache recipe. Capture span/size/prepass/scatter/normalized planes and bind them to these original output hashes.
- If undefined reads are demonstrated, document their actual addresses/bytes and exempt only that demonstrated behavior. Otherwise fix the first divergent general stage, then run every acceptance campaign, both reference/fast paths and all corpora.
- No production, release-gate, ledger, MAIN or emulator source edits; no push, stash or history rewrite. No worker/build process remains. Standard runner removed its temporary builds; scratch is below 1 MiB.
