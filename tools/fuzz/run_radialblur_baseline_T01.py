#!/usr/bin/env python3
"""Run the unchanged fuzz framework against a historical RadialBlur source.

Only the candidate source selection changes. Inputs, AEX worker, compiler flags,
header/core and admission switches are the same as the production run. This
avoids attributing a change of reference-worker math to the Offset promotion.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

import run
from adapters import radialblur


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--baseline-revision', required=True)
    parser.add_argument('--baseline-scratch', type=Path, required=True)
    args, remaining = parser.parse_known_args()
    directory = args.baseline_scratch.resolve()
    assert directory.is_relative_to(run.ROOT/'orchestra/state/T01-radial-offset-promote')
    directory.mkdir(parents=True, exist_ok=True)
    source = subprocess.check_output(['git', 'show', args.baseline_revision+
        ':mac/OLMRadialBlur/OLMRadialBlur.cpp'], cwd=run.ROOT)
    with tempfile.TemporaryDirectory(prefix='baseline_source_', dir=directory) as name:
        path = Path(name)/'OLMRadialBlur.cpp'
        path.write_bytes(source)
        path.with_suffix('.h').symlink_to(radialblur.public.SOURCE.with_suffix('.h'))
        radialblur.public.SOURCE = path
        sys.argv = [sys.argv[0], *remaining]
        return run.main()


if __name__ == '__main__':
    sys.exit(main())
