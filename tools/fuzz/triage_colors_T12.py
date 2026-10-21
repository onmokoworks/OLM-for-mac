#!/usr/bin/env python3
"""T12 runner: use only the AE-selected Smart route, including pre-F17 trees.

Without --target-only this delegates unchanged to the normal replay runner.
All other arguments (including mandatory --jobs 2) are run.py arguments.
"""
import importlib
import sys

import run


if __name__ == '__main__':
    plugin = sys.argv[sys.argv.index('--plugin') + 1]
    if plugin not in ('colorkeep', 'olmcolorkey'):
        raise SystemExit('T12 is limited to ColorKeep and ColorKey')
    if '--jobs' not in sys.argv or sys.argv[sys.argv.index('--jobs') + 1] != '2':
        raise SystemExit('Use --jobs 2 on the shared machine')
    if '--target-only' in sys.argv:
        sys.argv.remove('--target-only')
        importlib.import_module('adapters.' + plugin).Adapter.routes = ('smart',)
    raise SystemExit(run.main())
