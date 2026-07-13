# DirectionalBlur Alpha Fade Full-Render Row 755 Trace (Chunked Capture)

## 2026-07-13 no-space JSX retry

The quoted `-r` retry still failed before the JSX wrote its first marker. This
package now fails if After Effects is already running, copies the JSX to
`%PUBLIC%\OLMTrace\<run-id>\runner.jsx`, rejects whitespace in that launch
path, and invokes `AfterFX.exe -m -r <no-space-path>` without nested quoting.
Do not run it concurrently with another AE request.

This nested-CDB revision keeps the `+0x5554` breakpoint command short. It
executes `capture_at_5554.cdb` with `$><`, so the 63 chunk writes remain
separate CDB commands instead of one overlong quoted command. The row-coverage
predicate uses nested `.if` statements rather than unsupported `&&` syntax.

This package requests one current 2025 `OLMDirectionalBlur.aex` Software render
for `db_angle0_alpha_fade_hard_edges`, PREMULTIPLIED 8bpc. It captures the
in-situ internal row `755`, immediately after the real worker schedule and at
the first instruction of normalization (`OLMDirectionalBlur+0x5554`), before
normalization executes.

The focused segment is internal x `747..1080` inclusive. This retry reads it in
21 bounded chunks of 16 pixels (the final chunk has 14 pixels), then combines
the chunks only after exact-size checks. It must return little-endian float32
words for destination RGBA, denominator, and alpha/valid. The return also
records the run id, PID, AEX hash, worker/rowdriver call identity, the shared
params pointer, and exact base/offset/row/stride provenance.

The work planes are tiled. Treat `row0` and `col0` as global origins: global
`(x,y)` maps to local `((y-row0)*stride + (x-col0))`. Nonzero origins are
expected and must not be rejected.

Run from the extracted package directory on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_alpha_fade_row755.ps1 -AexPath "C:\path\to\installed\OLMDirectionalBlur.aex"
```

Run that script exactly as supplied. It launches After Effects, pauses the JSX
after the effect has been added, resolves the hash-pinned AEX base from the
live process module list, then attaches CDB and installs absolute-address
breakpoints before allowing the render to continue. Do not replace this with
module-name expressions or a pre-load attach. Missing ready marker, loaded
module, absolute base, or breakpoint-ready marker is an `exact_bind_failure`.

Only `answered` with all three combined artifacts and all bindings is accepted.
Missing, wrong-size, contradictory, post-normalization, surrogate, partial, or
unbound data returns `exact_bind_failure`.

The supplied case is imported as PREMULTIPLIED and the runner forces Software.
No per-pixel breakpoint is used. RadialBlur is outside this request.
