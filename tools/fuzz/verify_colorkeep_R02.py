#!/usr/bin/env python3
"""R02: replay F19 corpora and check SmartRender independently of DEEP bits."""
import argparse
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

from adapters.colorkeep import Adapter
from adapters.public import replace_once
from core import evaluate
from run import ROOT, main_checkout
from verify_colorkeep_F19 import snapshot


class FlagAdapter(Adapter):
    def compile_sdk(self, scratch, body, source, deadline, cores=()):
        body = replace_once(body, 'iw.world_flags=depth==16?PF_WorldFlag_DEEP:0;',
                            'iw.world_flags=atoi(getenv("R02_INPUT_FLAGS"));')
        body = replace_once(body, 'ow=iw;ow.data=',
                            'ow=iw;ow.world_flags=atoi(getenv("R02_OUTPUT_FLAGS"));ow.data=')
        return super().compile_sdk(scratch, body, source, deadline, cores)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--worker', type=Path, required=True)
    args = parser.parse_args()
    scratch = args.scratch.resolve()
    assert scratch.is_relative_to(ROOT/'orchestra/state/R02-colorkeep-pf32-world-flags')
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch))
    evidence = json.loads((ROOT/'reports/fuzz/colorkeep_F19.json').read_text())
    for phase in ('after', 'shrunk'):
        snapshot(evidence, scratch/('corpus-'+phase), phase)
    adapter = FlagAdapter(SimpleNamespace(main=main_checkout(), worker=args.worker,
                                          max_size=256, case_timeout=10))
    adapter.routes = ('smart',)
    adapter.oracle_routes = {'smart': 'smart'}
    deadline = time.monotonic() + 180
    provenance = adapter.prepare(scratch, deadline)
    cases = {}
    for index in range(300):
        case = adapter.generate(1, index)
        cases.setdefault(case['depth'], case)
    assert set(cases) == {8, 16, 32}
    records = []
    for depth, case in sorted(cases.items()):
        for input_flags in range(4):
            for output_flags in range(4):
                adapter.env.update(R02_INPUT_FLAGS=str(input_flags), R02_OUTPUT_FLAGS=str(output_flags))
                result = evaluate(adapter, case, scratch, deadline)
                records.append(dict(depth=depth, index=case['index'], input_flags=input_flags,
                                    output_flags=output_flags, result=result))
                assert result['routes']['smart']['status'] == 'exact', records[-1]
    (scratch/'flags.json').write_text(json.dumps(dict(provenance=provenance, cases=records), indent=2)+'\n')
    print(f'{len(records)}/48 Smart flag combinations AEX exact')


if __name__ == '__main__':
    main()
