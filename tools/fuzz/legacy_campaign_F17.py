#!/usr/bin/env python3
"""Reproduce the pre-F17 comparator for before/after measurement only.

The fixed base commit is read without checking out or modifying any source.
Run with the same run.py arguments; never use this for admission decisions.
"""
import argparse
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import run
BASE = '53715716482c3278e9af0771fad16e30db7261d0'
legacy = {'__name__':'legacy_core'}
exec(compile(subprocess.check_output(['git','show',BASE+':tools/fuzz/core.py']),
             '<pre-F17 core>', 'exec'), legacy)
core.evaluate = run.evaluate = legacy['evaluate']
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blur-before', action='store_true', help='Use pre-F17 OLMBlur source as well as the old comparator')
    options, remaining = parser.parse_known_args()
    sys.argv = [sys.argv[0], *remaining]
    if options.blur_before:
        import blur_admission_campaign_F17
        sys.argv += ['--blur-source-revision', BASE]
        raise SystemExit(blur_admission_campaign_F17.main())
    raise SystemExit(run.main())
