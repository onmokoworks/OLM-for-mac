# OLMSmoother2 case0012 return failure analysis (2026-07-13)

Scope: classify the two latest Windows case0012 returns against the current
common Windows witness launcher. No Mac algorithm or PNG changes are implied.

## FACTS

- The `09:58` and `11:03` returns both used the legacy dedicated runner
  `run_olmsmoother2_case0012_live_config_binding_20260713.ps1`, not
  `tools/windows_witness/runtime/run_witness.ps1`.
- That runner launches `cdb -cf <script> AfterFX.exe -r <jsx>` and never performs
  a later `cdb -p <observed AfterFX PID>` attach. It also does not wait for the
  JSX render-ready marker before arming the witness.
- Its CDB file uses deferred expressions `bu OLMSmoother2+0x3370`,
  `+0xc280`, `+0xcce0`, and `+0x3610`. Both returns report four immediate
  `contains symbols not qualified with module name` diagnostics. The `09:58`
  stdout then contains 352 and the `11:03` stdout 1380 `Unable to resolve
  unqualified symbol` diagnostics.
- Each stdout contains exactly one `S2_CFG_RUN_START`, emitted by the CDB command
  file before `g`, and no `S2_CFG_BIND`, `S2_CFG_C280`, `S2_CFG_CCE0`, or
  `S2_CFG_WRITER`. Both `RETURN.json` files therefore classify the missing
  decoded fields as `status=exact_bind_failure`, `failure.stage=bind`, and
  `last_observation=null`.
- The supplied logs contain no `ModLoad` line for `OLMSmoother2.aex`. Thus these
  returns do not prove whether the target AEX was loaded into this debuggee; the
  pinned on-disk hash alone is not loaded-module evidence.
- The current common launcher first uses a bootstrap CDB only through the
  `AfterFX.exe` image-load event, detaches with `qd`, validates a queue marker
  bound to run id/work/package/queue hash and the same observed PID, waits for a
  render-ready marker, discovers the exact loaded AEX path and hash, records its
  base address, renders every RVA to an absolute address, and only then runs
  `cdb -cf <resolved script> -p <bound PID>`.
- The current case0012 probe consequently uses `bp <absolute address>` rather
  than `bu OLMSmoother2+RVA`. Its static smoke and all common-runner tests pass.

## INFERENCES

- `exact_bind_failure` is the legacy runner's fail-closed result category, while
  unresolved breakpoint expressions are the observed proximal failure. The
  returns do not establish a bad RVA, an unhit algorithm path, or a Mac/PNG
  defect because no breakpoint was shown to bind and no loaded AEX/base identity
  was captured.
- The failure is not evidence against the current image-bootstrap/PID-attach
  design. That design removes both ambiguities present here: symbolic deferred
  binding and uncertainty about which process/module/base receives the probe.
- Re-running the legacy package with spelling changes to the symbolic expression
  would still leave process/module identity and render timing under-proven. The
  next useful run should use the already compiled common-core case0012 package.

## Minimum next-run conditions

Diagnostic minimum (required before interpreting a missing hit):

1. Bootstrap trace contains both `WITNESS_CDB_BOOTSTRAP_ARMED` and
   `WITNESS_CDB_AFTERFX_IMAGE_LOADED`.
2. Queue marker matches run id, work path, package root, and queue SHA-256, and
   process diagnostics preserve the same AfterFX PID/session/path.
3. Ready marker says `effect_loaded=1` and `parameters_applied=1` for case0012.
4. Loaded-module evidence records that same PID, the exact AEX path/hash, and a
   non-null module base.
5. Returned probe CDB contains resolved absolute `bp` addresses; trace contains
   `S2_UNIFIED_BREAKPOINTS_ARMED` before the continue marker is released; CDB was
   invoked with `-p <that PID>`.

Witness minimum (required to answer the current config-binding question): in one
run/PID/module-base/hash identity, capture `S2_BIND`, `S2_CCE0` with the fifth
argument config pointer, `S2_C2BB` proving pointer identity and the eight raw
control bytes, and `S2_WRITER`. The broader current contract may additionally
require its typed `E170/F270/E3A0` records for promotion; absence must remain a
typed-read/capture failure, not be collapsed back into symbolic bind failure.

## Commands run

```sh
git status --short
rg --files | rg -i 'smoother2|case0012|launcher|windows_returns'
unzip -l refs/windows_returns/20260713/20260713_095201__RETURN__olm_runtime_trace_olmsmoother2_case0012_live_config_binding_20260713__exact_bind_failure_unresolved_breakpoints.zip
unzip -l refs/windows_returns/20260713/olm_smoother2_case0012_live_config_binding_20260713_return.zip
ditto -x -k refs/windows_returns/20260713/20260713_095201__RETURN__olm_runtime_trace_olmsmoother2_case0012_live_config_binding_20260713__exact_bind_failure_unresolved_breakpoints.zip /tmp/olms2_ret_095201
ditto -x -k refs/windows_returns/20260713/olm_smoother2_case0012_live_config_binding_20260713_return.zip /tmp/olms2_ret_0958
jq . /tmp/olms2_ret_095201/RETURN.json
jq . '/tmp/olms2_ret_0958/execution\single_fresh_run\RETURN.json'
rg -n -i 'Unable to resolve|breakpoint|ModLoad|S2_CFG' '/tmp/olms2_ret_095201/artifacts\cdb_stdout.txt'
rg -n -i 'Unable to resolve|breakpoint|ModLoad|S2_CFG' '/tmp/olms2_ret_0958/execution\single_fresh_run\cdb_stdout.txt'
nl -ba tools/windows_witness/runtime/run_witness.ps1
git diff -- refs/scripts/smoke_windows_witness_olmsmoother2_case0012_20260713.py
python3 refs/scripts/smoke_windows_witness_olmsmoother2_case0012_20260713.py
python3 -m unittest tools.windows_witness.tests.test_windows_witness
python3 -m tools.windows_witness.smoke
```

No Windows zip was created.
