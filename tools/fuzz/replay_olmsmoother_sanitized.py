#!/usr/bin/env python3
"""Run the standard Smoother corpus replay with fatal ASan/UBSan at -O2.

Accepts run.py's arguments; requires --plugin olmsmoother and --replay.
The standard evaluator and matches_saved comparison are unchanged.
"""
import sys

sys.dont_write_bytecode = True
from adapters import olmsmoother
import run


class SanitizedAdapter(olmsmoother.Adapter):
    def compile(self, argv, deadline):
        argv = [*argv, '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                '-fno-omit-frame-pointer', '-g']
        self.sanitizer_command = list(map(str, argv))
        self.env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',
                        UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
        return super().compile(argv, deadline)

    def prepare(self, scratch, deadline):
        result = super().prepare(scratch, deadline)
        result['sanitizer_build_command'] = self.sanitizer_command
        return result


if __name__ == '__main__':
    args = run.options()
    if args.plugin != 'olmsmoother' or not args.replay:
        raise SystemExit('Requires --plugin olmsmoother and --replay')
    olmsmoother.Adapter = SanitizedAdapter
    sys.exit(run.main())
