# OLMSmoother2 current-AEX 0012 typed bind/read contract

## Target and scope

Trace only `legacy_case_0012_gamma5_red_blue_current_aex` at `(91,841)` in
one fresh current-AEX Windows Software run. The scanner `idx` is `105` and the
descriptor is `[91,841,1,91,843,5]`.

This is a new package. Do not reuse an earlier failed package, retained return,
broad trace, or second render/run. The Mac local witness is field schema evidence only, not a Windows expected value.

## Same-run required observations

First bind the live producer/class buffer at the witness-local stop. Record the
run id, case id, pixel, module/base, exact hook, held xy, and pointer/address
arithmetic. Without restarting or rebinding from another run, read and return:

- `idx` and `descriptor`
- class bytes `center_b0`, `prev_b0`, `left_b1`
- observed `e170.c`
- `f270.append`, `f270.source_xy`, and `f270.weight`
- `e3a0.append`, `e3a0.source_xy`, and `e3a0.weight`
- `polygon_count` before the cce0 consumer
- `cce0.output_rgba_float` and raw float hex
- same-run `final_writer` site, RGBA bytes, and RGBA floats

All listed observations are mandatory and must share the same run id and
witness stop. Final-writer values do not replace producer reads.

## Exact failure

If run start, witness gate, bind, pointer recovery, or any typed read fails,
return `status: "exact_bind_failure"`, never a vague partial result. Include
all of the following: `stage` (`run_start`, `witness_gate`, `bind`,
`pointer_recovery`, or `typed_read`), verbatim concrete `reason`, module/base,
hook, run id, held case/pixel, pointer context, and the last observation.
Use `null` only when that item was never observed. Local Mac values are never a
substitute for Windows observations.

`answered_partial` and `partial` are forbidden statuses. The return is
`answered` only when every required field above came from the same fresh run.

The package is project-local only, must not be sent to NAS, and must contain no
machine-local absolute paths.

## Executable handoff

Run `runner/run_olmsmoother2_current_aex_0012_typed_bind_read_20260710.ps1`
from the extracted package. It requires the packaged JSX entry, `AfterFX.exe`,
and CDB, creates one fresh-run script with the e170/f270/e3a0/cce0 hooks, and
writes `exact_bind_failure` when the complete typed bind/read result is not
decoded. It exits non-zero on that failure and never emits `answered_partial`.
## Concrete runner behavior

The packaged JSX is the proven ae_render_single_case.jsx fixture runner. The
package also carries request_manifest.json, reference_manifest.json, and the
exact case_0012_before_effects.png input. The launcher forces one fresh
Software project, anchors (91,841) at OLMSmoother2+0x3370, and arms typed
e170/f270/e3a0, polygon, cce0, and writer +0x3610 markers. PowerShell parses
those markers into RETURN.json and reaches status "answered" only when every
mandatory marker and witness identity is present. Missing any marker or field
emits structured exact_bind_failure and exits non-zero.
