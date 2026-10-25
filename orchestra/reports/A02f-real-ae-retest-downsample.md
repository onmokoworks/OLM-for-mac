status: partial
summary: A02f checkpoint; serial priority aerender campaign is in progress.
  Saved A02e projects are reused with ticket-local output overrides.
  Script-progress windows are now wait-only and both preference files restore.
  Full 1080p I/O control is exact; original-AEX comparisons are underway.
facts:
- Watcher 17 tests, preference 3 tests, render 2 tests and pipeline 7 tests pass.
- Initial aerender command failed because `-mfr OFF` omitted required CPU percent;
  local aerender help confirms `-mfr mfr_flag max_cpu_percent`. Fixed to OFF 100.
- Six errors were recorded before stopping the Python campaign (SIGTERM sent only
  to owned Python PID 76308, never AE/aerender). Its in-flight child exited normally;
  the outstanding preference backup was restored after all AE/aerender exited.
- The replacement run uses fresh ID priority-f2. First Full control has 0 differing
  samples, hash 6e2ec261728aebbb68b008c004b1b73ce1a10c138e55255a8daa2cc7fb889143.
- DistanceGradation Full/Half transparent black matches original AEX exactly.
  ColorKeep Full has 6,220,800 raw sample differences, first at (0,0) R: AE=00,
  original=20. Transparent RGB export loss is being checked, not patched.
inference:
- Premultiplied TIFF may explain ColorKeep hidden RGB differences. Queue resolution
  and control pixels are proxies for plugin input; no live InData trace exists.
changed_files:
- tools/ae_smoke/{run_ae_smoke.py,render_downsample.py,compare_downsample.py,test_downsample.py,README.md}
- tools/ae_smoke/ae_dialog_watch/{Policy.swift,main.swift,prefs.py,test_prefs.py,test_watch.py}
- orchestra/reports/A02f-real-ae-retest-downsample.md and A02f-evidence/
verify:
```sh
TMPDIR="$PWD/orchestra/state/A02f-real-ae-retest-downsample" PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02f-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-priority --stage render --run-id priority-f2 --scratch orchestra/state/A02f-real-ae-retest-downsample
TMPDIR="$PWD/orchestra/state/A02f-real-ae-retest-downsample" PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02f-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/compare_downsample.py orchestra/state/A02f-real-ae-retest-downsample/priority-f2 --timeout 15
```
Expected: resume completed outputs; compare pending rendered 8 bpc frames. Do not
run concurrently with the active campaign. Final evidence supersedes this checkpoint.
next:
- Finish priority; depth/corpus projects, calibrated high-depth output and live
  geometry binding remain outstanding. No plugin source change is authorized.
