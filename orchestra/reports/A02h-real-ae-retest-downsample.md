status: partial
summary:
- A02h checkpoint: KBar/panel watcher repair passes all 17 offline tests.
- Reusing A02g's four saved projects (176 queue items); depth renders are running serially.
- Corpus and straight-alpha PNG probe preparation is in progress.
facts:
- Initial screen unlocked, no AE main executable, memory 57% free.
- `python3 tools/ae_smoke/ae_dialog_watch/test_watch.py --scratch orchestra/state/A02h-real-ae-retest-downsample/watch-tests`: 17 tests passed, including A02g KBar screenshot and modal-negative cases.
- Saved `depths-g1/build.json` phase=complete, four existing project paths, 176 items; manifest copied to ticket-local depths-h1, footage/projects unchanged.
- At checkpoint, first 24 depth frames rendered with no errors/refusal tags. Full 16 bpc control is raw exact; ColorKeep Full differs in 6,220,800 samples, first R at (0,0), AE=0000/reference=1010. No plugin bug conclusion.
inference:
- KBar was a non-dialog workspace false positive; modal/subrole guards remain authoritative.
- Transparent RGB differences remain an I/O/compositing hypothesis pending straight export.
changed_files:
- tools/ae_smoke/ae_dialog_watch/Policy.swift, test_watch.py
- tools/ae_smoke/run_ae_smoke.py, prepare_downsample.jsx, render_downsample.py, compare_downsample.py, README.md
- orchestra/reports/A02h-real-ae-retest-downsample.md, A02h-evidence/
verify:
```sh
TMPDIR="$PWD/orchestra/state/A02h-real-ae-retest-downsample" PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_watch.py --scratch orchestra/state/A02h-real-ae-retest-downsample/watch-tests
# Offline comparison of already-rendered frames, no AE launch:
TMPDIR="$PWD/orchestra/state/A02h-real-ae-retest-downsample" PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02h-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/compare_downsample.py orchestra/state/A02h-real-ae-retest-downsample/depths-h1 --timeout 15
```
Expected: 17 tests pass; comparison resumes pending frames without modifying AE.
next:
- Finish depths, build/render corpus and straight-alpha probe, retain final evidence and combined tables.
- Smoother Full-4K two-sample difference belongs to S01; not investigated here.

checkpoint_depths:
- 176/176 depth frames rendered, zero errors and zero refusal tags. All four Full controls raw exact.
- 16 bpc effects: 72/80 raw exact vs original, eight ColorKeep hidden-RGB differences.
- 32 bpc effects: 64/80 raw exact vs original, eight ColorKeep hidden-RGB differences, eight Smoother v1 unsupported-reference-depth outcomes.
- ColorKeep 1080p PF32 exhausted the F53 arena. Its same installed bundle rendered through cached V01 F51/F47d full host; the recorded mismatch is hidden RGB only.
- Smoother v1 original rejects PF32 negotiation; direct PF32 bundle host returns 516. AE output is successful but callback depth has not been traced.
- General unittest discovery ran 36 tests with 11 errors because watcher tests need their CLI-initialized Swift binary. Correct dedicated runs pass: watcher 17, pipeline 7, render 2, codec 3. The failed invocation log is retained.
