status: blocked
summary:
- Reproduced all ten in-scope R03 contract command failures against current builds; no assertion was weakened.
- Fixtures162–164 are reserved for R08 under the explicit prohibition on touching Radial fixtures152–181.
- Contract failures are not numerical Mac-versus-original witnesses; replacing them requires more than changing an expected rejection to acceptance.
- Group2 and group3 results are being recorded in separate commits; no release promotion is made.

facts:

Branch `orch/R07-gate-contracts-and-bindings`. Read AGENT_GUIDE, GOTCHAS, compatibility plan, the relevant ledger decision rows and R03/R05/R06 reports. SDK links were prepared with `bash scripts/setup_ae_sdk_links.sh`. No production code, MAIN assets, cached workers, release predicate, installed bundle or forbidden-action list is changed.

Group1 before/after table. “Before” is R03/R05 retained evidence; “after” is the fresh `R07-check-items.py --group contracts` run. All ten child commands return1; the driver returns0 to indicate completion, not acceptance. Exact commands, elapsed times and full diagnostics are in `R07-contracts-evidence.tar.xz` with a member-hash manifest.

| Item | Before | After / reason it remains blocked |
|---|---|---|
| fixture047 ColorKey atomic | probe3 | probe3; the test requires 63 positive / 567 negative cases, including rejection after flipping one active source byte. A generic source-admitting implementation cannot be repinned to this source-whitelist contract. Need paired original output for every newly admitted mutation, retaining genuine layout/alias/atomicity negatives. |
| fixture063 Directional cleanup | probe134 | probe134: err=-3, allocation attempts=1, output unchanged=1, layer/output/checkin=2/1/1, parameter checkout/checkin=21/21. Test requires BAD_CALLBACK_PARAM and zero allocations for a 1×2 world with output stride1,700,000,000. This is a safety/lifecycle finding; changing the expected error alone removes its pre-allocation guarantee. No production fix is authorized. |
| fixture083 Directional adapter | probe38 | probe38: layer3 err=-1, exact=0, visible=0, padding=1. PF16 source uses alpha65535 with Layer noise100/front8. Rejection occurs before equality; no actual-original pixel mismatch has been established. Need typed original/production admission and budget trace for this exact world. |
| fixture126 Kira Mode3 | PF8/16/32=10 | Same three codes; the test demands fail-close for the modulo-192-alpha 32×18 source. Need a replacement original-backed accepted-source contract across all three depths, preserving precommit failures. |
| fixtures162,163,164 | failed | Not rerun or edited: reserved Radial152–181 range. R08 owns adjudication; not silently dropped or passed. |
| fixture184 Radial Type3 host plumbing | mock10 | mock10 at SmartPreRender/checkout event expectation. Requires original public callback/order evidence before changing the lifecycle assertion. Not a measured pixel difference. |
| generic Directional back-only | probe10 / code1568 | Same: operation-budget rejection assertion. The UHD guard-mapped test is a budget contract, not an original-output reference. Need explicit current admission/budget proof plus retained atomicity checks. |
| generic Directional cleanup | probe134 | Same as fixture063; duplicate gate entry retained. |
| generic Distance production | probe75 | Current normal probe46 and sanitizer probe75. Both identify `pf32_blurred_budget_rejects`: 67×43 PF32, Sphere, Layer/Both, Median size500. Need original-backed acceptance/output plus replacement safety boundary; simply accepting success would remove the budget check. |
| generic Kira UI length | 3 failed tests | 8 tests run, 3 failures; length0 reject check reports ok=0 at all depths. Need original-backed zero-length contract; length301's reject check reports ok=1. No all-UI completion claim. |
| generic Radial baseline | probe38 | probe38; PF32 baseline center-domain assertion (`30*type + 8` for type1). Need fresh original boundary output and admission evidence; no final-byte pin is implicated by this code alone. |

inference:

The source-whitelist failures are consistent with later generalization, but that is not evidence permitting wholesale deletion of negatives. Allocation ordering, budget guarantees, host callback order and typed Layer rejection need distinct adjudication. These are open contract findings/blocked migrations, not newly proven Mac-versus-original pixel differences. No fuzz witness is emitted from an exit code alone.

changed_files:

- `orchestra/reports/R07-check-items.py`: sequential confined rerunner, restoring any generated tracked conformance reports.
- `orchestra/reports/R07-package.py`: streaming evidence archive/manifest writer.
- `orchestra/reports/R07-contracts-evidence.tar.xz`, `R07-contracts-manifest.json`.
- This report. Later groups append their artifacts below.

verify:

```sh
bash scripts/setup_ae_sdk_links.sh
python3 -B orchestra/reports/R07-check-items.py --group contracts
python3 -B orchestra/reports/R07-package.py contracts
git diff --check
```

Expected: ten command exits1; no source/assertion or conformance-pin changes. The archive checksum can change with temporary paths; every listed member digest must verify. All child execution temporaries use `orchestra/state/R07-gate-contracts-and-bindings`, `OLM_TEST_JOBS=2`, MAIN's existing absolute-path Python and assets. The driver never runs reserved fixtures152–181.

next:

Resolve source-whitelist assertions by capturing all affected positive/mutation outputs twice through a current registered original worker; retain independent malformed-world, alias and lifecycle checks. Investigate the allocation/budget and callback contracts separately; production fixes require a follow-up ticket. R08 handles162–164. Group2/group3 adjudication follows below.
