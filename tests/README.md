# Python test execution

Use the isolated unittest runner for repository-wide checks:

```sh
python3 scripts/run_python_unittest_isolated.py \
  --output refs/reports/python_unittest_isolated.json
```

The historical tests import helper modules from `tools/emulation`, and several
helpers have the same module basename as files under `tests`. A single
`python3 -m unittest discover -s tests` process can therefore retain one helper
in `sys.modules` and import a later test from the wrong directory. The isolated
runner executes each `tests/test*.py` file in a fresh Python process, preserves
stdout and stderr in a machine-readable report, applies a per-file timeout, and
supports parallel jobs with `--jobs`.

Classify a completed run with:

```sh
python3 scripts/classify_python_unittest_summary.py \
  refs/reports/python_unittest_isolated.json \
  --output refs/reports/python_unittest_classification.json
```

The classifier is triage, not a release verdict. In particular, source SHA
drift and legacy rejection-contract failures do not establish a numerical
regression. Run `scripts/run_olm_mac_fixed_fixture_regression_20260805.py` to
check retained behavioral fixtures, and investigate its numerical, compiler,
or lifecycle failures before refreshing identity pins.

Some files use pytest-style free functions or are executable audit scripts
rather than `unittest.TestCase` suites. The isolated unittest report records
these as `NO TESTS RAN`; run their native framework or entrypoint separately.
