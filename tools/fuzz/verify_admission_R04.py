#!/usr/bin/env python3
"""Original-AEX render checks accompanying the R02/F41b admission assertions."""
import importlib
import hashlib
import json
import os
import shutil
from pathlib import Path
import time
from types import SimpleNamespace

from core import evaluate
from run import ROOT, main_checkout, default_worker
from verify_colorkeep_R02 import FlagAdapter


def main():
    scratch = ROOT/'orchestra/state/R04-assertion-drift-and-corpus/admission'
    scratch.mkdir(parents=True, exist_ok=True)
    os.environ.update(TMPDIR=str(scratch), TMP=str(scratch), TEMP=str(scratch), OLM_TEST_JOBS='2')
    args = SimpleNamespace(main=main_checkout(), worker=default_worker(), max_size=256, case_timeout=120)
    records = []
    for plugin in ('colorkeep', 'olmblur', 'olmdistancegradation', 'radialblur'):
        adapter_type = FlagAdapter if plugin == 'colorkeep' else importlib.import_module('adapters.'+plugin).Adapter
        # Reuse F41b's recorded reference for its three admission witnesses.
        # Other plugins use the current default reference worker.
        args.worker = (Path.home()/'.cache/olm-emu/worker-F32-deep/aex-guest-worker'
                       if plugin == 'radialblur' else default_worker())
        adapter = adapter_type(args)
        adapter.routes = ('smart',)
        adapter.oracle_routes = {'smart':'smart'}
        directory = scratch/plugin
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir()
        deadline = time.monotonic()+600
        provenance = adapter.prepare(directory, deadline)
        if plugin == 'colorkeep':
            cases = {}
            for index in range(300):
                case = adapter.generate(1, index)
                cases.setdefault(case['depth'], case)
            assert set(cases) == {8,16,32}
            samples = [(case, i, o) for case in cases.values() for i in range(4) for o in range(4)]
        else:
            # F41b merge 7a0cd797: these Radial indices were refusal -> exact.
            # Blur/Distance retain the representative seed-777 Smart render.
            samples = [(adapter.generate(1 if plugin == 'radialblur' else 777, i), None, None)
                       for i in ((62,104,235) if plugin == 'radialblur' else (0,))]
        for case, input_flags, output_flags in samples:
            if input_flags is not None:
                adapter.env.update(R02_INPUT_FLAGS=str(input_flags), R02_OUTPUT_FLAGS=str(output_flags))
            result = evaluate(adapter, case, directory, deadline)
            row = dict(plugin=plugin, case={k:v for k,v in case.items() if k != "pixels"},
                       pixels_sha256=hashlib.sha256(case["pixels"]).hexdigest(),
                       input_flags=input_flags, output_flags=output_flags,
                       provenance=provenance, result=result)
            records.append(row)
            (scratch/'results.json').write_text(json.dumps(records, indent=2)+'\n')
            assert result['routes']['smart']['status'] == 'exact', (plugin,case['index'],result)
        print(plugin, len(samples), 'AEX exact', flush=True)


if __name__ == '__main__':
    main()
