#!/usr/bin/env python3
"""Reuse the C54 public/sanitized comparison for the C56 Bilateral timeout."""
import sys
sys.dont_write_bytecode = True
import probe_distancegradation_C54 as probe

original_matrix = probe.matrix


def matrix(adapter, mode, extreme=False):
    if mode == 'target':
        yield 'seed1/10', adapter.generate(1, 10)
    else:
        yield from original_matrix(adapter, mode, extreme)


if __name__ == '__main__':
    probe.matrix = matrix
    probe.main()
