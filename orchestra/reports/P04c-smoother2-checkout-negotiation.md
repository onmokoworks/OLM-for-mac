status: blocked

summary:
- F52c cannot supply a cropped input checkout independently of full-layer size/downsample.
- Original PreRender returns a cropped result for a cropped request on a full input, then SmartRender throws for unequal worlds.
- That is not the P00b cropped-input layout; neither faithful refusal nor a Mac fix is established for that layout.
- Production source and equal-world guard are unchanged. No oracle rebuild was attempted.

facts:

- `memory_pressure`: system-wide memory free percentage 60% before running tests.
- `git branch --show-current`: `orch/P04c-smoother2-checkout-negotiation`.
- `PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/P04c-evidence/probe.py`: exit 0, four serial PF8 Smart witnesses. The labelled set is retained in `P04c-evidence/witnesses.json`, with parameters, input/output hashes and complete session observations. Pixels are reproducibly constructed in the driver.
- Worker SHA-256: `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`; original AEX SHA-256: `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.

| Witness | Full layer / supplied input | Scale | Original result / max rectangle | Outcome |
|---|---|---|---|---|
| full-control | 14x10 / 14x10 | 1:1 | `[0,0,14,10]` / `[0,0,14,10]` | 560 output bytes; clean session |
| cropped-checkout-unrepresentable | 14x10 / 7x5 | 1:1 | Not reached | Host rejects `resident input slot has 140 bytes, expected 560` |
| full-input-cropped-extent-request | 14x10 / 14x10; extent/request 7x5 | 1:1 | `[0,0,7,5]` / `[0,0,14,10]` | `SMART_RENDER` exception transport diagnostic names `0x180022410` |
| half-downsample-control | 14x10 / 7x5 | 1:2 | `[0,0,7,5]` / `[0,0,7,5]` | 140 output bytes; clean session |

All reached PreRender calls report flags=0. Full-control output SHA-256 is
`b142817edbf12cc3bf69ac1ab70649e636a40fb43aa85a1516eb878afd63eeaf`;
half-downsample output SHA-256 is
`bc2eb876877f88980928bd5fe36507a74ca74de698e289d3a2eb9e836ef72178`.
No Mac pixel comparison was made; there is no measured first pixel mismatch.

Read-only host inspection, excerpts and source hashes in `P04c-evidence/host-boundary.json`:
- F52c `geometry.rs`, `Geometry::world`: input width/height are ceil(full dimension * downsample); no independent checkout dimension/origin option.
- `resident.rs`: raw input length must match the resulting input slot exactly.
- `classic.rs:3309`: negotiated PreRender result resizes the output only.
- P00b host `tools/emulation/aexcompat_patches/P00-host-realism.cpp:279` instead halves the input dimensions with `extent==2`, leaving the full layer/downsample unchanged; its checkout callback returns source extent and full reference dimensions. This condition is absent from F52c's session interface.

`OLM_TEST_JOBS=1 python3 orchestra/reports/P04c-evidence/unit_tests.py baseline-units`
and the same command with `final-units`: both execute 18 modules serially,
5 pass / 13 fail, identical per-module exit codes. Full per-module diagnostic tails
are committed in `baseline-units.json` and `final-units.json`. Failures include
missing retained artifacts and stale source/dependency identities; these are not
an all-tests-pass result. The ROI full-frame contract module passes both runs.
`git diff --check`: pass before committing.

inference:

- Substituting a full input with a cropped extent/request is not a valid test of a cropped input world. It produces the opposite unequal-world layout to P00b.
- Substituting 1:2 downsample also changes the contract; its successful render cannot establish 1:1 cropped-checkout behavior.
- The original does not always force full-frame result_rect, but its max_result_rect remains full-frame in the measured 1:1 cropped-request case. This alone does not justify changing Mac negotiation while retaining a differently allocated input world.
- A qualified cropped-input oracle is required to choose either requested resolution. The prohibition on rebuilding/modifying the oracle blocks that prerequisite. Stop here rather than claim the original faithfully refuses P00b's layout.

changed_files:
- `orchestra/reports/P04c-smoother2-checkout-negotiation.md`
- `orchestra/reports/P04c-evidence/probe.py`
- `orchestra/reports/P04c-evidence/witnesses.json`
- `orchestra/reports/P04c-evidence/host-boundary.json`
- `orchestra/reports/P04c-evidence/unit_tests.py`
- `orchestra/reports/P04c-evidence/baseline-units.json`
- `orchestra/reports/P04c-evidence/final-units.json`

verify:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 orchestra/reports/P04c-evidence/probe.py
OLM_TEST_JOBS=1 python3 orchestra/reports/P04c-evidence/unit_tests.py verify-units
git diff --check
```

Expected: probe assertions pass with statuses `ok,reject,reject,ok`, output byte
counts `560,0,0,140` and the diagnostics above. Unit runner records 18 modules,
5 pass / 13 fail in scratch `verify-units/summary.json`; its process exit 0 does
not mean all unit modules passed. All temporary paths are under ticket scratch.

next:

- Authorize a separate host ticket to expose independent source checkout size/origin and reference dimensions, retaining genuine original PreRender result/max rectangles and requested checkout rectangles. Alternatively obtain a native AE trace of those fields.
- Re-run this 14x10 layer / 7x5 checkout at 1:1, then patch Mac negotiation only if equal-world original rendering is established.
- Default n300, realistic seed 1/fresh n100, odd-even seeds 2026/2027 n150, and standard corpus replay acceptance remain unrun on this blocked ticket. No production change or acceptance claim is made. The host-boundary witnesses are labelled evidence, not added as accepted fuzz corpus cells.
- No MAIN, emulator source, release gate, ledger, or other plugin changes. No push. Scratch contains only logs/JSON, no remaining build trees or background processes.
