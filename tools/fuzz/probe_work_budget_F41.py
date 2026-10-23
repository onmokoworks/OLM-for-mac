#!/usr/bin/env python3
"""Reproduce F41's rejected RadialBlur work-only experiment in scratch.

No production files, oracle limits, allocation limits or pixel arithmetic change.
Run this script with ordinary tools/fuzz/run.py arguments (plugin radialblur).
"""
import os
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
import run
from adapters.radialblur import public


def main():
    args = run.options()
    if args.plugin != 'radialblur' or args.replay:
        raise SystemExit('This experiment requires a radialblur generation campaign')
    root = run.ROOT / 'orchestra/state/F41-relax-work-budget'
    if not args.scratch.is_relative_to(root):
        raise SystemExit('Use --scratch beneath orchestra/state/F41-relax-work-budget')
    source_dir = args.scratch / 'experiment-source'
    source_dir.mkdir(parents=True, exist_ok=False)
    original = public.SOURCE
    source = original.read_text()
    old = 'static constexpr uint64_t kMaxWork = UINT64_C(350000000);'
    assert source.count(old) == 1, 'Budget site changed; re-audit before testing'
    source = source.replace(old,
        'static constexpr uint64_t kMaxWork = UINT64_MAX; // F41 experiment: work only.')
    source = re.sub(r'^#include "([^" ]+)"',
        lambda m: '#include "' + str((original.parent / m.group(1)).resolve()) + '"',
        source, flags=re.MULTILINE)
    snapshot = source_dir / original.name
    snapshot.write_text(source)
    for name in ('OLMRadialBlur.h', 'OLMRadialBlur_Strings.h', 'OLMRadialBlur_Strings.cpp'):
        (source_dir / name).symlink_to(original.parent / name)
    public.SOURCE = snapshot
    os.environ.update(TMPDIR=str(args.scratch), TMP=str(args.scratch), TEMP=str(args.scratch))
    run.main()


if __name__ == '__main__':
    main()
