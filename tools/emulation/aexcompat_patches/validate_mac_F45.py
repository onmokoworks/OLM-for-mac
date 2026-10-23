#!/usr/bin/env python3
"""Qualify actual Xcode math objects after the Carbon-prefix wrapper fix.

Run after build_F45.sh; serialized producers/comparators, no concurrent pool.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[3]
S = ROOT/'orchestra/state/F45-integrate-ms-double'
DLL = Path.home()/'.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll'
assert hashlib.sha256(DLL.read_bytes()).hexdigest() == '385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3'
env = dict(os.environ, TMPDIR=str(S), TMP=str(S), TEMP=str(S))
rows = []
with (S/'mac-object-validation.log').open('w') as log:
    subprocess.run(['clang','-arch','x86_64','-O2','-Wno-deprecated-declarations',str(ROOT/'ucrtmath/ms/double_compare.c'),'-o',str(S/'mac-compare')], env=env, stdout=log, stderr=log, check=True)
    for plugin in ['OLMColorKey','OLMKiraKira','OLMRadialBlur']:
        for arch in ['arm64','x86_64']:
            obj = S/f'xcode/{plugin}/obj/{plugin}.build/Debug/{plugin}.build/Objects-normal/{arch}/ucrt_ms_double_mac.o'
            assert obj.is_file(), obj
            producer = S/'mac-object-probe'
            subprocess.run(['clang','-arch',arch,'-O2','-I'+str(ROOT/'ucrtmath/include'),str(ROOT/'ucrtmath/ms/double_native.c'),str(obj),'-o',str(producer)], env=env, stdout=log, stderr=log, check=True)
            for fn in ['sin','cos','exp']:
                stream = S/'mac-object-stream.bin'
                with stream.open('wb') as output:
                    subprocess.run(['/usr/bin/arch','-'+arch,str(producer),fn,'random','1000000'], env=env, stdout=output, stderr=log, check=True)
                with stream.open('rb') as inp:
                    run = subprocess.run(['/usr/bin/arch','-x86_64',str(S/'mac-compare'),str(DLL),fn,'1000000'],env=env,stdin=inp,stdout=subprocess.PIPE,stderr=log,text=True,check=True)
                stream.unlink()
                row = json.loads(run.stdout)
                row.update(plugin=plugin, architecture=arch, object_sha256=hashlib.sha256(obj.read_bytes()).hexdigest())
                rows.append(row)
                print(plugin,arch,fn,row['count'],[m['mismatches'] for m in row['modes']],flush=True)
(Path(ROOT/'orchestra/reports/F45-evidence/mac-object-results.json')).write_text(json.dumps(rows,indent=2)+'\n')
