status: blocked
summary:
- F52c cannot represent a checked-out input smaller than ceil(layer × downsample).
- Explicit 20×15 input / 40×30 layer witness is rejected by the reference transport before original rendering.
- The same pixels/settings with a 20×15 layer are Smart raw exact; cropped Mac rendering refuses.
- No production or shared sampler changes: removing the guard without the required original witness is not justified.
- A separately authorized oracle geometry extension is required before completing P04b.

facts:
- Branch: `orch/P04b-directionalblur-cropped-checkout`. `memory_pressure` reported 64% free before builds; scratch remained below 5 GiB.
- `python3 orchestra/reports/P04b-evidence/smoke.py --label before --n 10`: seed 1 realistic-v1, then doubled full_geometry without changing checkout pixels or downsample. Results: 1 exact, 4 candidate refusals, 5 uncompared. Nine original oracle calls rejected payload lengths; the sole exact case rounds to the same 1×1 world and is NOT a cropped witness. Results and provenance retained in `P04b-evidence/before-*`.
- `python3 orchestra/reports/P04b-evidence/measure.py --label witness`: two PF8 cases, same deterministic 1,200 input bytes, 20×15 checkout/output, unit downsample/aspect, Front Strength 5, other controls defaults. Index 0 layer 20×15: original and Mac Smart exact, SHA256 `0a21ff72492dcdd55e430eb9607534bfa730a2b4340415c461fa1e6104129597`. Index 1 layer 40×30: original transport rejects `resident input slot has 1200 bytes, expected 4800`; Mac error 516, `SmartRender:smart-generic-world-or-budget@2710`. First pixel mismatch: unavailable, because the original did not render index 1. This is NOT evidence of an original-plugin refusal or a Mac-only refusal.
- Cached worker SHA256 `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`; original AEX SHA256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`. Full candidate/source identities are in witness-provenance.json.
- Read-only inspection of the cached F52c source: geometry.rs `Geometry::world()` derives dimensions exclusively from full layer × downsample. Options include request, extent, padding, aspect and output negotiation, but no independent input checkout dimensions. resident.rs validates input payload length before dispatch. Relevant source excerpts committed in `P04b-evidence/oracle-geometry-excerpts.txt`.
- Unit commands: `OLM_TEST_JOBS=1 python3 orchestra/reports/P04b-evidence/unit_tests.py --label before` and `--label after`. Both runs: 39 files, 7 pass / 32 fail, zero per-file exit changes. Diagnostics are recorded in units-before.json and units-after.json.
- No algorithm hypothesis was changed or tested. The blocker is reference-host capability, under the explicit prohibition on oracle rebuilds. No MAIN, emulator source, release gate, ledger or other plugin was modified.

inference:
- Original input-sized planes described in P02j remain a plausible reason to remove the full-layer guard, but do not provide the requested executable witness for this geometry.
- Passing downsample 1/2 would make the payload fit, but would change blur parameter scaling and make the checkout equal the sampled full layer; it would not test this ticket's boundary.
- Request/extent rectangles cannot fix this input allocation limitation. Adding a shared sampler now would generate unavailable reference calls rather than establish cropped conformance.

changed_files:
- `orchestra/reports/P04b-directionalblur-cropped-checkout.md`
- `orchestra/reports/P04b-evidence/measure.py`, `smoke.py`, `unit_tests.py`
- `orchestra/reports/P04b-evidence/*-results.jsonl`, `*-summary.json`, `*-provenance.json`, `units-*.json`, `oracle-geometry-excerpts.txt`

verify:
```sh
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
python3 orchestra/reports/P04b-evidence/measure.py --label verify
python3 orchestra/reports/P04b-evidence/smoke.py --label verify-smoke --n 10
python3 orchestra/reports/P04b-evidence/unit_tests.py --label verify
git diff --check
```
Expected witness: 1 exact and 1 refusal, with the latter oracle rejected for 1200 versus 4800 bytes (not a conformance pass). Smoke: 1 exact / 4 refusal / 5 uncompared. Unit baseline: 7 pass / 32 fail across 39 files, same counts as P02j's historical failures. Scripts build only disposable candidate test hosts under this ticket's scratch, never the oracle. Source excerpts identify cached host implementation; no inference is substituted for original pixels.

next:
- Separate oracle ticket: authorize independent checkout width/height in the reference host, preserve layer/downsample independently, validate payload/rowbytes and checkout/output allocation, install/hash/register the new worker in the shared cache.
- Resume P04b with that worker: obtain the original cropped witness, fix the DirectionalBlur guard/workspace only as supported, add the opt-in realistic-v1 cropped sampler and labelled reproducible corpus, survey all plugins, then run all required default/realistic/odd-even campaigns and standard both-route corpus replays.
- Those campaigns, all-plugin survey, sampler option, new passing corpus and production fix remain unperformed; acceptance is not claimed.
