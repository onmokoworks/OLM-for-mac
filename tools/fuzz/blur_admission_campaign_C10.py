#!/usr/bin/env python3
"""C10 OLMBlur campaigns: current small-fixture gate bypass and sanitizer replay.

All other guards and the numerical core stay intact. Accepts run.py arguments.
The source revision option makes before/after and gate-off runs reproducible
without changing the worktree. Sanitizers abort on the first finding per case.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True
import run
import triage_olmblur as triage
from adapters import olmblur


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blur-small-off', action='store_true')
    parser.add_argument('--blur-sanitize', action='store_true')
    parser.add_argument('--blur-source-revision')
    options, remaining = parser.parse_known_args()
    original = olmblur.SOURCE

    def build(adapter, scratch, deadline):
        source = (subprocess.check_output(['git','show',options.blur_source_revision+':mac/OLMBlur/OLMBlur.cpp']).decode()
                  if options.blur_source_revision else original.read_text())
        if options.blur_small_off:
            anchor = next(line for line in source.splitlines() if 'return "generic-small-fixture";' in line)
            if source.count(anchor) != 1:
                raise ValueError('small-fixture bypass anchor changed')
            source = source.replace(anchor, '\t// C10 diagnostic only: small-fixture guard bypassed.')
            source = source.replace('!SmallDefaultPF32Source(input_world)', 'false')
        root = scratch/'variant'
        target = root/'mac/OLMBlur'
        target.mkdir(parents=True)
        (root/'core').symlink_to(run.ROOT/'core', target_is_directory=True)
        for name in ('OLMBlur.h','OLMBlur_Strings.cpp','OLMBlur_Strings.h'):
            shutil.copyfile(original.with_name(name),target/name)
        olmblur.SOURCE = target/'OLMBlur.cpp'
        olmblur.SOURCE.write_text(source)
        adapter.env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                           UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        binary = triage.build_binary(adapter, scratch, sanitize=options.blur_sanitize)
        return binary, [olmblur.SOURCE, original, olmblur.HOST, olmblur.MAIN, olmblur.PARAMETERS, *olmblur.CORES]

    olmblur.Adapter.build = build
    sys.argv = [sys.argv[0], *remaining]
    return run.main()


if __name__ == '__main__':
    raise SystemExit(main())
