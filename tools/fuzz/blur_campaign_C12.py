#!/usr/bin/env python3
"""C12 OLMBlur campaigns: current small-fixture gate bypass and sanitizer replay.

All other guards and the numerical core stay intact. Accepts run.py arguments.
The source revision option makes before/after and gate-off runs reproducible
without changing the worktree. Sanitizers abort on the first finding per case.
"""
import argparse
import os
import re
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
    parser.add_argument('--blur-native-expf-depth', type=int, choices=(16, 32))
    parser.add_argument('--blur-expf-legacy', action='store_true')
    options, remaining = parser.parse_known_args()
    original = olmblur.SOURCE

    def build(adapter, scratch, deadline):
        source = (subprocess.check_output(['git','show',options.blur_source_revision+':mac/OLMBlur/OLMBlur.cpp']).decode()
                  if options.blur_source_revision else original.read_text())
        if options.blur_small_off:
            anchor = next(line for line in source.splitlines() if 'return "generic-small-fixture";' in line)
            if source.count(anchor) != 1:
                raise ValueError('small-fixture bypass anchor changed')
            source = source.replace(anchor, '\t// C12 diagnostic only: small-fixture guard bypassed.')
            source = re.sub(r'!SmallDefaultPF32Source\(input_world(?:,[^)]*)?\)', 'false', source)
        root = scratch/'variant'
        target = root/'mac/OLMBlur'
        target.mkdir(parents=True)
        (root/'ucrtmath').symlink_to(run.ROOT/'ucrtmath', target_is_directory=True)
        core = root/'core'; core.mkdir()
        for path in (run.ROOT/'core').iterdir():
            if path.is_file(): (core/path.name).symlink_to(path)
        if options.blur_source_revision:
            for path in olmblur.CORES:
                copy = core/path.name; copy.unlink()
                copy.write_bytes(subprocess.check_output(['git','show',options.blur_source_revision+':core/'+path.name]))
        olmblur.CORES = [core/path.name for path in olmblur.CORES]
        if options.blur_native_expf_depth:
            lane = 'legacy' if options.blur_expf_legacy else 'nonlegacy'
            path = core/f'olmblur_worker{options.blur_native_expf_depth}_{lane}.cpp'
            text, count = re.subn(r'static_cast<float>\(\s*std::exp\(static_cast<double>\(exponent\)\)\)',
                                 'std::exp(exponent)', path.read_text())
            assert count == 1
            path.unlink()  # Never write through the production-source symlink.
            path.write_text(text)
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
