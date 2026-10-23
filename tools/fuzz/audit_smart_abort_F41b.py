#!/usr/bin/env python3
"""Inventory direct PF_InData abort/progress-shaped calls in retained decomp.

PF_InData starts with inter: abort/progress are slots 3/4 (+0x18/+0x20),
and the Win64 effect_ref is at +0xb8 (slot 0x17). This intentionally narrow
scan does NOT prove absence of aliased/indirect callbacks or library polling.
"""
import argparse
import json
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decomp', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    expressions = [
        re.compile(r'\(\*\(code \*\)(param_\d+)\[([34])\]\)\(\1\[0x17\]'),
        re.compile(r'\(\*\*\(code \*\*\)\((param_\d+) \+ 0x(18|20)\)\)\(\*\(undefined8 \*\)\(\1 \+ 0xb8\)'),
    ]
    records = {}
    for name in ('OLMRadialBlur', 'OLMBlur', 'OLMDirectionalBlur',
                 'OLMKiraKira', 'OLMToonDilate', 'DistanceGradation'):
        hits, buffer, function = [], '', ''
        with (args.decomp / (name + '.aex.c.txt')).open() as stream:
            for number, line in enumerate(stream, 1):
                if line.startswith('// === '):
                    function = line.strip()
                buffer = (buffer + line)[-1500:]
                if any(expression.search(buffer) for expression in expressions):
                    hits.append({'line': number, 'function': function})
                    buffer = ''
        records[name] = hits
    args.output.write_text(json.dumps(records, indent=2) + '\n')
    print({name: len(hits) for name, hits in records.items()})


if __name__ == '__main__':
    main()
