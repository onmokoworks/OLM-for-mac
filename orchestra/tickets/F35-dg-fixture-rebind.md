# F35: replace the obsolete DG retained-fixture expectation with original-AEX public-Smart truth

## Orchestrator decision (based on F34, `orchestra/reports/F34-dg-fixture-f02-regression.md`)
The expected bytes of `refs/fixtures/olmdistancegradation_pf32_owner_17x11_20260805` came from a
direct internal call (`FUN_181172a10`) with different checkout values: 0/0/1 instead of 1/1/2,
and a different background color. So the expectation does not bind the parameters the
regression tests. AE uses the Smart route for DG (F18).

## Do
1. Use F34's harness (`orchestra/reports/F34-compare-fixtures.py`) to generate new expected bytes
   by running the **original AEX** through the public Smart route with the regression's exact
   12 controls. Use both fixture inputs. Use the default worker and confirm the F30 worker gives
   identical output.
2. Add these as a new fixture version, e.g. `..._public_smart_<date>`, with a provenance JSON:
   AEX sha, worker sha, controls, route, and command. Point the retained regression at the new
   fixture.
   - Keep the old fixture files. Mark them superseded with a README note that cites F34.
   - Never generate expected bytes from Mac output.
3. Classic route: AE does not call it for DG. If the regression tests Classic, scope it out
   explicitly, with a comment citing F18, rather than asserting zero buffers.
4. Run the DG fixed-fixture regression (`scripts/run_olm_mac_fixed_fixture_regression_20260805.py`,
   DG part only) and the DG unit tests. Both must pass.
- Do not touch the release gate/ledger.
