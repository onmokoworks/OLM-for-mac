#!/usr/bin/env python3
"""Attribute AEX-rendered noise-plane refusals without performing invalid reads."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
sys.dont_write_bytecode = True
from adapters.radialblur import Adapter, ROOT
from core import sha


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--campaign', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'orchestra/state/C44-radial-smart-r7')
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), TMP=str(out), TEMP=str(out))
    core = ROOT/'core/dblur_noise.h'
    text = core.read_text().replace('#include "../ucrtmath/include/ucrtmath.h"', '#include "'+str(ROOT/'ucrtmath/include/ucrtmath.h')+'"')
    marker = 'if (table_index < 0 || table_index >= 100) return false;'
    assert text.count(marker) == 1
    text = '#include <iostream>\n'+text.replace(marker, 'if (table_index < 0 || table_index >= 100) { std::cout << table_index << " " << table_position << " "; return false; }')
    (out/'noise.h').write_text(text)
    (out/'noise.cpp').write_text('''#include "noise.h"
int main() {
 int w,h,raw; unsigned seed; float size;
 while (std::cin >> w >> h >> raw >> seed >> size) {
  std::vector<float> values; int pw=0,ph=0;
  bool ok=olm::dblur::generate_radial_noise_plane(w,h,size,
    (float)((double)raw*2.663161090079238e-7),seed,&values,&pw,&ph);
  std::cout << ok << " " << pw << " " << ph << "\\n";
 }
}
''')
    subprocess.run(['clang++','-std=c++17','-O1','-fsanitize=address,undefined','-fno-fast-math','-ffp-contract=off',str(out/'noise.cpp'),'-o',str(out/'noise')],check=True)
    campaign=json.loads(args.campaign.read_text())
    adapter=Adapter(SimpleNamespace(main=ROOT.parent.parent,worker=Path.home()/'.cache/olm-emu/worker-F46-pow/aex-guest-worker',max_size=256,case_timeout=30))
    rows=[]
    for row in campaign['cases']:
        guards=row.get('refusal_guards',{}).get('smart',[])
        if row['result']['oracles']['smart']['status'] != 'ok' or not any('noise-plane-failure' in g for g in guards):
            continue
        case=adapter.generate(campaign['seed'],row['index'])
        assert sha(case['pixels'])==row['input_sha256']
        p={v['slot']:v['value'] for v in case['parameters']}
        w,h=case['geometry']
        data=f'{w} {h} {round(p[28]*65536)} {p[27]} {p[29]}\n'
        run=subprocess.run([str(out/'noise')],input=data,text=True,capture_output=True,check=True)
        assert not run.stderr
        index,position,ok,pw,ph=run.stdout.split()
        assert int(index)<0 and ok=='0'
        rows.append(dict(index=row['index'],input=data.strip(),first_invalid_index=int(index),position=float(position),plane=[int(pw),int(ph)],sanitizer_stderr=run.stderr))
    report=dict(core_sha256=sha(core.read_bytes()),campaign_sha256=sha(args.campaign.read_bytes()),rows=rows)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'noise').unlink()
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    main()
