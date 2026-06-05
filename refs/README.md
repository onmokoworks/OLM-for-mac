# Reference Render Diff Harness

`fixtures/test_cellanim.png` is the shared input image for Win/Mac renders.

Expected local-only folders:

- `win/` Windows reference PNG sequence
- `mac/` macOS port PNG sequence
- `diff/` amplified diff output

These folders are ignored by git.

Usage:

```sh
python3 refs/scripts/make_test_cellanim.py
refs/scripts/diff_all.sh
```

Parameterized case verification:

```sh
python3 refs/scripts/verify_cases.py
```

The default manifest is `cases/olmsmoother_v1_minimal.json`. It records the
input image, expected frame names, and the parameters used for each render.
Reports are written to `reports/`, and amplified diff images are written to
`diff/`.

Windows reference transfer:

```sh
python3 refs/scripts/normalize_render_names.py path/to/ae_png_sequence
python3 refs/scripts/package_win_reference.py path/to/rendered_pngs --out OLMSmoother_win_reference.zip
python3 refs/scripts/import_win_reference.py path/to/OLMSmoother_win_reference.zip
```

If AE outputs arbitrary sequence names, normalize them first. The normalizer maps
sorted PNGs to the manifest case order and writes `f0.png`, `f1.png`, and so on
into `_normalized/`. The package stores PNGs, parameter values from the manifest,
and SHA-256 hashes. The import command validates the package and copies the
reference frames into `win/`.

For a single file:

```sh
refs/scripts/diff_one.py refs/win/frame.png refs/mac/frame.png refs/diff/frame.diff.png
```

For AE-free algorithm debugging, see `ALGORITHM_HARNESS.md`.

Windows-side reference requests live in `reference_requests/`. These are
case lists that can be handed to the Windows AE/Codex environment when the Mac
port needs stronger CUDA vs SOFTWARE or parameter-isolation references.

Imported Windows AE reference sets live in `win_references/`:

- `win_references/20260604_olm/`: first broad OLM reference package.
- `win_references/20260605_extra/`: Distance Gradation, RadialBlur img2, and
  Smoother v2 extra references from Windows AE 25.2x131.

Smoke-test the whole AE-free harness:

```sh
python3 refs/scripts/smoke_algorithm_harness.py
```

Smoke-test the simple ColorKeep algorithm CLI:

```sh
python3 refs/scripts/smoke_colorkeep_cli.py
```

End-to-end reference package test:

```sh
python3 refs/scripts/run_reference_test.py path/to/windows_reference_folder_or_zip \
  --input refs/fixtures/test_cellanim.png \
  --command 'python3 refs/scripts/identity_image_cli.py --input "{input}" --params "{params}" --output "{output}"'
```
