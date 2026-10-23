#!/usr/bin/env python3
"""Run Smart-only campaigns or selected generated cases using the normal runner.

Extra option: --indices 62,117 selects original generator indices (never changes
case content). Other arguments are exactly those of run.py. No oracle limits
are changed except by the explicit run.py --case-timeout option.
"""
import argparse
import importlib
import sys

sys.dont_write_bytecode = True
import run


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--indices')
    extra, rest = parser.parse_known_args()
    sys.argv = [sys.argv[0], *rest]
    args = run.options()
    adapter = importlib.import_module('adapters.' + args.plugin).Adapter
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
