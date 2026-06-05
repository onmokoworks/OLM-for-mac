# Generic Image Algorithm Harness

This repo should not need After Effects for every algorithm-debugging loop.

The target workflow is:

1. Capture Windows AE reference renders once.
2. Store PNGs and the exact effect parameter snapshot in a manifest.
3. Port the effect kernel into a small CLI.
4. Run the CLI from the same manifest.
5. Diff CLI output against the Windows reference PNGs.

## Smoke Test

Before wiring a real plug-in kernel, verify the harness itself:

```sh
python3 refs/scripts/smoke_algorithm_harness.py
```

This creates a temporary reference manifest, runs the sample identity CLI, and
checks that all PNGs are byte-perfect.

Smoke-test a real simple algorithm CLI:

```sh
python3 refs/scripts/smoke_colorkeep_cli.py
```

This verifies the ColorKeep alpha-mask behavior with a synthetic manifest and
PNG pair.

Smoke-test the OLMColorKey RGB/binary-alpha reference slice:

```sh
python3 refs/scripts/smoke_olmcolorkey_cli.py
```

This verifies Windows reference `case_0001..case_0004` exactly.

Smoke-test the OLMColorKey premultiplied Edge Thin slice:

```sh
python3 refs/scripts/smoke_olmcolorkey_extended_cli.py
```

This verifies `case_0005..case_0007` with a tolerance gate for the known
boundary residual in the erode cases.

Build and smoke-test the OLMBlur C++ CLI against all Windows reference cases:

```sh
refs/scripts/build_olmblur_cli.sh
python3 refs/scripts/smoke_olmblur_cli.py
```

This verifies all seven OLMBlur cases with a max-diff 1 tolerance gate for the
known PNG/rounding-level residuals.

Audit OLMRadialBlur reference parameters before implementing its CLI:

```sh
python3 refs/scripts/audit_olmradialblur_manifest.py
```

This separates the duplicate Outer Blur / Inner Blur property names and points
at the simplest first Rotation case.

Run the current experimental OLMRadialBlur Rotation slice:

```sh
python3 refs/scripts/smoke_olmradialblur_rotation_cli.py
```

This is expected to report DIFF for the broad Rotation cases. The tiny
Rotation guard is separate:

```sh
python3 refs/scripts/smoke_olmradialblur_tiny_rotation_cli.py
```

Run the current OLMRadialBlur Zoom no-noise slice:

```sh
python3 refs/scripts/smoke_olmradialblur_zoom_cli.py
```

This verifies `case_0009` with a max-diff 1 / mean 0.01 tolerance gate.

Run the current OLMRadialBlur Zoom Offset guard:

```sh
python3 refs/scripts/smoke_olmradialblur_zoom_offset_cli.py
```

This verifies `case_0003..0005` with Size Variation explicitly ignored. It is a
regression guard for the current Zoom/Offset baseline, not proof that Size
Variation is implemented.

Run the current OLMRadialBlur Inner measurement scaffold:

```sh
python3 refs/scripts/smoke_olmradialblur_inner_cli.py
```

This is expected to report DIFF for `case_0011..0013`. It keeps inner-blur
work measurable while the `FUN_180001c90` / validity / edge handling is still
incomplete.

Run the current OLMDistanceGradation basic gate:

```sh
python3 refs/scripts/smoke_olmdistancegradation_cli.py
```

This verifies the new `20260605_extra/OLMDistanceGradation` stable cases
`case_0001..0007`, `case_0015`, `case_0017`, `case_0018`, and `case_0019`
with a gated residual (`max<=7`, `mean<=0.11`, `nonzero<=22%`). Later blur and
constant/interpolation cases remain measurement targets rather than green
gates.

Run the current OLMSmoother2 measurement scaffold:

```sh
refs/scripts/build_olmsmoother2_cli.sh
python3 refs/scripts/smoke_olmsmoother2_keypaths_cli.py
python3 refs/scripts/smoke_olmsmoother2_cli.py
```

This drives `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp` through the C++ CLI
against `20260605_extra/OLMSmoother2`. The key-path smoke is a green regression
gate for cases 2-4 (`max<=95`, `mean<=0.022`, `nonzero<=0.15%`). The broader
cases 1-4 smoke is expected-red for now; the current measurement is
`mean=0.4304/0.0216/0.0000/0.0189`. The large `case_0002` improvement came
from the disasm-confirmed active-palette path for Color Key + Invert;
`case_0003` exact and the `case_0004` improvement came from the
objdump-confirmed non-invert scalar-key path. See
`notes/OLMSmoother2_ASM_FACTS.md`.

Run every current green AE-free smoke in one command:

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py --profile quick
```

This runs only the current green regression gates. Use it as the default
iteration check after normal implementation edits.

Run every current AE-free smoke, including known-red diagnostics:

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py
```

This script builds the C++ CLIs that have build scripts, runs the green
regression smokes, and also runs the known-red measurement scaffolds
(`OLMSmoother`, `OLMSmoother2`, broad `OLMRadialBlur Rotation`,
`OLMRadialBlur Inner`, `OLMDirectionalBlur`, `OLMKiraKira`). A red measurement
counts as healthy only when it produces `[DIFF]` output; missing CLIs/references
or failures without a diff still fail the aggregate. This is the default
`--profile full` behavior.

## CLI Contract

Each extracted algorithm should eventually have a tiny command-line runner:

```txt
<plugin>_cli --input input.png --params params.json --output output.png
```

The CLI should:

- read one image,
- read one case's parameter JSON,
- run only the image-processing core,
- write one PNG,
- avoid AE SDK dependencies in the core path.

AE-specific code should stay in a wrapper layer. The kernel should be callable
from both the AE plug-in and the CLI runner.

## Running Cases

Use:

```sh
python3 refs/scripts/run_algorithm_cases.py reference_manifest.json \
  --command './plugin_cli --input {input} --params {params} --output {output}' \
  --out-dir refs/mac_cli
```

The runner writes one params JSON per case and invokes the command once per
manifest case.

Then compare `refs/win/` and `refs/mac_cli/` with:

```sh
python3 refs/scripts/verify_cases.py
```

or use a manifest-specific verification command once the imported Windows
manifest format is wired in.

## One-Command Package Test

Given a Windows reference folder or zip containing `reference_manifest.json` and
the case PNGs:

```sh
python3 refs/scripts/run_reference_test.py path/to/windows_reference_folder_or_zip \
  --input refs/fixtures/test_cellanim.png \
  --command './plugin_cli --input "{input}" --params "{params}" --output "{output}"'
```

This creates a local run under `refs/runs/`, copies reference PNGs, runs the CLI
for every case, and writes diff reports.

## Suggested C++ Shape

```txt
mac/<Plugin>/
  <Plugin>.cpp              AE entry points and parameter translation
  <Plugin>Core.h            AE-free structs and function declarations
  <Plugin>Core.cpp          image-processing algorithm
  cli/<plugin>_cli.cpp      PNG/JSON adapter for tests
```

Core functions should prefer plain inputs:

```txt
render(input_pixels, width, height, rowbytes, params, output_pixels)
```

This makes Ghidra-derived algorithm debugging much faster: most iterations can
happen in a terminal, and AE only has to be used for capturing references or
final plug-in validation.
