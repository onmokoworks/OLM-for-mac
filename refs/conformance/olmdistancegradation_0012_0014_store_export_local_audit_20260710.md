# OLMDistanceGradation `case_0012`/`case_0014` 16bpc Store/Export Local Audit

Date: 2026-07-10

## Scope and verdict

This is a local audit of existing reports/logs only. No Windows request was
made, no Mac source was changed, and no PNG-only tuning is proposed.

**FACT:** Existing evidence does not close the required pre-store -> PF16
store -> export chain for either case. The prior Windows returns are
`failed_partial`/`failed` and contain package-local PNG/residual material, not
fresh live callback values.

**INFERENCE:** `case_0012` is compatible with an export-only rounding family,
but that hypothesis is not proven. `case_0014` is not closed as export-only;
the retained local sample leaves a store-side or pre-store difference open.
Together, the existing evidence closes neither family as an implementation
rule.

## Evidence ledger

### `case_0012`

**FACT:** The canonical 2026-07-09 residual audit reports max true16 delta
`2`, with representative `(438,0)` candidate `[42307,42307,42307,64997]`
versus reference `[42309,42309,42309,64997]`, or `[-2,-2,-2,0]`.

**FACT:** The local PF16 sample analysis records `(438,0)` with Mac debug
store `a=32499`, `r=21330`, Mac PNG `42307`, and Windows reference `42309`.
It records the same pattern at `(1034,1)` and says a round-style export can
explain the Windows value without changing the stored PF16 word.

**INFERENCE:** These samples support an export-only explanation for at least
the observed `case_0012` residual shape. They do not prove it, because the
Windows pre-store float, Windows PF16 store word, and same-run exported
true16 value are absent. The local arithmetic is not a Windows witness.

### `case_0014`

**FACT:** The canonical 2026-07-09 residual audit reports max true16 delta
`4`. At `(448,0)` and `(752,10)`, the candidate is
`[19985,19985,19985,36151]`, the reference is
`[19989,19989,19989,36151]`, and the delta is `[-4,-4,-4,0]`.

**FACT:** The local PF16 sample analysis records `(448,0)` under the current
Both-only rule as Mac debug store `a=18076`, `r=18117`, Mac PNG `19985`, and
Windows reference `19989`. It explicitly reports that simple round-style
export from that same store word does not fully explain the reference.

**FACT:** A deferred dominant-channel probe changed the local debug store RGB
to `18119` and reached PNG `19989`, but the report marks that probe as
non-adoptable evidence.

**INFERENCE:** `case_0014` remains a pre-store/store-versus-export
discriminator, not a closed export-only family. The probe supports the
direction of a source/store effect, but does not establish the Windows rule
or justify a Mac change.

## Existing return status

**FACT:** The 2026-07-08 shared store/export return intake is `failed_partial`.
For both cases it lacks direct Windows pre-store RGBA float, direct Windows
PF16 store word, and same-run exported TIFF/EXR true16 value; it reports only
package-local PNG bytes for the selected points.

**FACT:** The 2026-07-09 `case_0014` resend is classified `failed`: it has no
fresh Windows callback witness and no exact fresh hook/watchpoint failure
artifact. The earlier layer-source return likewise says its PNG/residual
values are not binary-grounded proof of the live Windows source/compose path.

## Closure decision

| Family | Export-only closed? | Pre-store/store family closed? | Reason |
| --- | --- | --- | --- |
| `case_0012` | **No** | **No** | Local store/export arithmetic makes export-only plausible, but no same-run cross-stage witness binds the stages. |
| `case_0014` | **No** | **No** | The retained local store sample is not fully explained by export rounding; pre-store/store remains unresolved, and no Windows chain exists. |

The exact conclusion is therefore **open for both cases**. No unsupported
claim is made about which host owns the rounding.

## Narrow next witness

Use one same-run witness per case at the existing representative points:

- `case_0012`: `(438,0)` (the `(657,0)` point is an equivalent fallback).
- `case_0014`: `(448,0)` (the `(752,10)` point is an equivalent fallback).

For each point, bind only these six values in order: source RGBA16 from the
AE input world; normalized source RGBA; field `X` and `d_alpha`; composed RGBA
float immediately before PF16 conversion; PF16 words immediately after store;
and the exported true16 value from that same run. This single paired witness
would distinguish export-only from pre-store/store behavior without a broad
rerender or implementation change.

## Commands and files inspected

Commands run from the repository root:

```sh
find refs/conformance reports logs -type f 2>/dev/null \\
  | rg 'olmdistancegradation|bitdepth_16bpc|case0012|case0014' | sort
rg -l -i 'case[_ -]?0012|case[_ -]?0014' refs/conformance reports logs 2>/dev/null | sort
sed -n '1,260p' <selected report/log files>
git status --short
```

Primary files inspected:

- `refs/conformance/olmdistancegradation_case0012_case0014_store_export_rounding_contract_20260708.md`
- `refs/conformance/olmdistancegradation_case0012_case0014_store_export_rounding_return_intake_20260708.md`
- `refs/conformance/olmdistancegradation_16bpc_export_rounding_residual_audit_20260709.md`
- `refs/conformance/olmdistancegradation_pf16_store_export_sample_analysis_20260709.md`
- `refs/conformance/olmdistancegradation_true16_residual_family_audit_20260709.md`
- `refs/conformance/olmdistancegradation_case0012_dominant_channel_closeout_20260708.md`
- `refs/conformance/olmdistancegradation_case0012_pointdebug_20260708.md`
- `refs/conformance/olmdistancegradation_case0014_layer_source_witness_contract_20260708.md`
- `refs/conformance/olmdistancegradation_case0014_layer_source_return_intake_20260708.md`
- `refs/conformance/olmdistancegradation_case0014_layer_source_return_resend2_intake_20260709.md`
- `refs/conformance/olmdistancegradation_current_integrated_16bpc_batch_20260709.md`
- `refs/conformance/olmdistancegradation_depthgate_true16_reverify_20260709.md`

