# Windows Dense Runtime Trace Strategy

Goal: reduce Mac/Windows round trips by asking the Windows helper to collect
dense intermediate logs instead of one narrow witness at a time.

This does not move the porting target to Windows. The Mac side still owns the
Apple Silicon implementation, build, CLI comparison, Mac AE validation, and
IR updates. The Windows side should own extraction of the official Windows AEX
runtime facts.

## Division of Labor

Windows helper:

- Render with Windows AE Software renderer.
- Attach CDB/WinDbg or an equivalent debugger/tracer to the Windows AEX.
- Log the effective parameter struct, selected branches, intermediate buffers,
  per-pixel samples, writeback floats, and final bytes.
- Return structured JSON, raw logs, and any short notes needed to explain which
  values were directly observed versus inferred from static analysis.

Mac porting side:

- Compare returned trace JSON against Mac CLI trace/baseline logs.
- Update binary-grounded IR before changing implementation.
- Patch the C++/Rust/Mac plug-in implementation.
- Verify with AE-free CLI and Mac AE exact validation.

## Trace Contract

Each plugin trace should prefer a few high-value witness pixels over broad PNG
collection. For each witness, capture the full path from input to output:

1. AE/project context:
   - AE version;
   - project renderer name/raw value;
   - bit depth;
   - color management if visible;
   - plug-in module base address.
2. Effective parameters:
   - UI values as shown in AE;
   - decoded values inside the AEX parameter/context struct;
   - any flags controlling legacy mode, keying, gamma, premultiply, border
     mode, interpolation, or writeback.
3. Kernel path:
   - function names/addresses hit;
   - branch or dispatch index;
   - loop bounds/radius/span/count;
   - sample order and sample coordinates;
   - boundary handling.
4. Intermediate values:
   - input RGBA;
   - unpremultiply/premultiply steps;
   - key/matte/classification values;
   - distance/weight/accumulation values;
   - filter or OpenCV call arguments;
   - pre-writeback RGBA floats.
5. Final writeback:
   - color-space encode/decode if any;
   - floor/round/truncate/cvt operation if observable;
   - clamp;
   - final byte or 16/32bpc channel values.

## Priority

1. OLMSmoother2 legacy key/gamma: currently blocks the Smoother path.
2. OLMColorKey Edge Blur / Edge Thin: core is mostly exact, edge path remains
   insufficiently explained.
3. OLMDistanceGradation field prep / OpenCV arguments: AE-host exact exists,
   but CLI/IR needs the upstream field construction explained.
4. OLMBlur residual writeback: AE-host exact exists, but the remaining CLI
   residual should be classified without changing passing AE behavior.
5. OLMKiraKira: focus on OpenCV 4.5.5 stage values and aggregation/compose,
   not more broad PNGs.
6. OLMRadialBlur / OLMDirectionalBlur: collect sampler/scatter/normalize and
   writeback logs before tuning.
7. OLMToonDilate: light binary-grounding trace only, because the current 8bpc
   packaged slices are AE exact.

## Stop Rules

- Do not tune from PNG residuals when the trace fields are missing.
- Mark a return `trace-too-sparse` if it contains only final PNGs, branch names,
  or static guesses without witness values.
- Prefer returning fewer cases with complete input-to-output logs over many
  cases with partial logs.
- If CDB cannot isolate a value, return the failed breakpoint/watchpoint attempt
  and the nearest static evidence rather than silently omitting the field.

## Current Package

Generate the all-plugin dense request with:

```sh
python3 scripts/package_runtime_trace_requests.py --profile dense-all \
  --output refs/runtime_trace_packages/olm_runtime_trace_dense_all_YYYYMMDD_HHMMSS.zip
```

The resulting zip is intended for the Windows Codex/helper session. It should
be treated as a work queue: start with Smoother2 legacy, then continue through
the other plugin areas while Mac work continues independently.
