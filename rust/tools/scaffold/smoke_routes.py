#!/usr/bin/env python3
"""Check generated pass-through wiring against independent endpoint pixels, not original algorithms."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
import olm_scaffold as s


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--summary",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    campaign=json.loads(args.summary.read_text(encoding="utf-8"));oracle=s.oracle_module()
    # Full-alpha endpoint samples avoid any guessed host rounding or alpha normalization.
    pixels=np.zeros((5,7,4),dtype=np.uint8)
    for y in range(5):
        for x in range(7):pixels[y,x]=[255*((x+y)%2),255*(x%2),255*(y%2),255]
    Image.fromarray(pixels,'RGBA').save(out/'input.png')
    request=oracle.make_request({'assignments':[],'size':[7,5],'downsample':'1'})
    s.write_json(out/'request.json',request)
    result={'purpose':'pass-through CPU wiring only; no original algorithm equivalence',
            'summary_sha256':s.sha(args.summary.read_bytes()),'cases':[]}
    for plugin in campaign['plugins']:
        if plugin['status']!='pass':continue
        candidate=Path(plugin['candidate']['path'])
        if s.sha(candidate.read_bytes())!=plugin['candidate']['sha256']:raise ValueError('candidate changed')
        config=json.loads((candidate.parent/'crate/oracle.json').read_text(encoding='utf-8'))
        for route in config['routes']:
            depth,command=oracle.ROUTES[route]
            output=out/f"{plugin['name']}-{route}.png"
            row={'plugin':plugin['name'],'route':route,'candidate_sha256':plugin['candidate']['sha256']}
            try:
                r=s.run_checked(oracle,[campaign['harness']['path'],'--headless',command,candidate,out/'input.png',output,out/'request.json'],60,
                                oracle.frame_deadline_environment(60),out/f"{plugin['name']}-{route}.process.json")
                actual=oracle.load_output(output,depth)
                expected=pixels if depth==8 else ((pixels.astype('<u2')//255)*32768 if depth==16 else (pixels.astype('<f4')/255).view('<u4'))
                row['exact_copy']=bool(np.array_equal(actual,expected))
                row['process_exit']=r['returncode']
            except Exception as e:row['exact_copy']=False;row['error']=str(e)
            result['cases'].append(row);s.write_json(out/'summary.json',result)
            print(plugin['name'],route,row['exact_copy'],row.get('error',''),flush=True)
    return 0 if result['cases'] and all(r['exact_copy'] for r in result['cases']) else 1


if __name__=='__main__':raise SystemExit(main())
