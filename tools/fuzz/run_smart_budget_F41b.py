#!/usr/bin/env python3
"""Run Smart-only campaigns or selected generated cases using the normal runner.

Extra option: --indices 62,117 selects original generator indices (never changes
case content). Other arguments are exactly those of run.py. No oracle limits
are changed except by the explicit run.py --case-timeout option.
"""
import argparse
import importlib
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
import run


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--indices')
    parser.add_argument('--radial-source', type=Path,
                        help='Compile a retained RadialBlur source snapshot')
    extra, rest = parser.parse_known_args()
    sys.argv = [sys.argv[0], *rest]
    args = run.options()
    if args.replay:
        parser.error('Use run.py for corpus replay so saved Classic results are checked too')
    module = importlib.import_module('adapters.' + args.plugin)
    adapter = module.Adapter
    if extra.radial_source:
        if args.plugin != 'radialblur':
            parser.error('--radial-source requires radialblur')
        original = module.public.SOURCE
        source_dir = args.scratch / 'source-snapshot'
        source_dir.mkdir(parents=True, exist_ok=False)
        body = re.sub(r'^#include "([^" ]+)"',
                      lambda match: '#include "' + str((original.parent / match.group(1)).resolve()) + '"',
                      extra.radial_source.read_text(), flags=re.MULTILINE)
        snapshot = source_dir / original.name
        snapshot.write_text(body)
        for name in ('OLMRadialBlur.h', 'OLMRadialBlur_Strings.h', 'OLMRadialBlur_Strings.cpp'):
            (source_dir / name).symlink_to(original.parent / name)
        module.public.SOURCE = snapshot
    adapter.routes = ('smart',)
    adapter.oracle_routes = {'smart': adapter.oracle_routes['smart']}
    if extra.indices:
        indices = [int(index) for index in extra.indices.split(',')]
        if args.replay or args.n != len(indices) or any(index < 0 for index in indices):
            parser.error('--indices requires generation with --n equal to its length')
        generate = adapter.generate
        adapter.generate = lambda self, seed, index: generate(self, seed, indices[index])
    run.main()


if __name__ == '__main__':
    main()
