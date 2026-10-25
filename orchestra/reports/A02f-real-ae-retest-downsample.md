status: partial
summary: A02f checkpoint; all 132 priority items rendered; depth campaign is in progress.
  Saved A02e projects are reused with ticket-local output overrides.
  Script-progress windows are now wait-only and both preference files restore.
  108 effect outputs are raw exact; 12 ColorKeep outputs lose hidden RGB in export.
  All three Full 8 bpc controls and the first Full 16 bpc control are exact.
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

checkpoint_2_facts:
- Priority: 132/132 successful renders, no refusal tags; 24 transparent/black outputs
  are 12 ColorKeep and 12 DistanceGradation defaults. 108/120 effect raw comparisons
  exact, 12 hidden-RGB-only I/O differences. 110 effects used original F53 AEX;
  10 Full-4K effects used the same installed bundle through retained F47d hosts.
- F53 geometry bundle host aborted at Full 4K. F51 full-frame host succeeded for
  nine plugins; ColorKeep needs ordinary iterate, absent in that older host.
  Existing V01 full-frame F51/F47d transport supplied ColorKeep's reference;
  no host was rebuilt. These are reference-host limitations, not AE failures.
- Four new 16/32 bpc projects built with one GUI session, single DoScriptFile,
  complete marker and clean AE exit. Both preference files restored byte-exactly.
- 16 bpc FLOAT EXR control at 1080p is exact: 0 differing samples, SHA-256
  16fdd57773d5fce4b0d214b7fc24dcf5931650a96e33c48b5b7e1c8aa5549150.
- Corpus selector has decoded/hash-checked 20 existing exact SDR full-frame
  witnesses (two per plugin). Original dimensions, depths, pixels and parameters
  are retained; these are not resized substitutes. GUI reproduction is pending.
