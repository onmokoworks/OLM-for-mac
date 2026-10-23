#!/usr/bin/env python3
"""Two rejected C39 scratch-only hypotheses; neither is a production fix."""
import sys,os,time,json,argparse
from pathlib import Path
from types import SimpleNamespace
R=Path.cwd();S=R/'orchestra/state/C39-seed45-residual-mismatches'
sys.path.insert(0,str(R/'tools/fuzz'))
from adapters.olmdistancegradation import Adapter,SOURCE
from run import default_worker,main_checkout
from verify_distancegradation_smart_C08 import variant
from core import raw_diff,sha
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S))
p=argparse.ArgumentParser();p.add_argument('--body',choices=['general-scalar','radius-one'],required=True);args=p.parse_args()
a=Adapter(SimpleNamespace(main=main_checkout(),worker=default_worker(),max_size=256,case_timeout=60));d=S/('dg-'+args.body);d.mkdir(exist_ok=False);deadline=time.monotonic()+600;a.prepare(d,deadline)
src=SOURCE.read_text();src=src.replace('p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&\n\t\t p.blur_mode','p.smart_owner && p.pixel_size != sizeof(PF_Pixel16) &&\n\t\t p.blur_mode')
if args.body=='radius-one':
 src=src.replace('} else if (p.pf32_smart_matrix_admitted ||', '} else if ((p.smart_owner && p.pixel_size == sizeof(PF_Pixel8) && p.blur_size <= 1) || p.pf32_smart_matrix_admitted ||')
else:
 src=src.replace('return radius >= 3 && radius <= 32 && (w <= 2*radius || h <= 2*radius);','return ((radius >= 3 && radius <= 32) || (p.pixel_size == sizeof(PF_Pixel8) && radius <= 1)) && (w <= 2*std::max(1L,radius) || h <= 2*std::max(1L,radius));')
(S/'dg-candidate.cpp').write_text(src)
b=variant(a,d/'candidate',deadline,src)
for seed,index in [(45,2),(44,70)]:
 c=a.generate(seed,index);o,ref=a.oracle(c,d,deadline,'smart');s,raw,g=b.candidate(c,d,'smart',deadline)
 print(seed,index,o,s,raw_diff(ref,raw,c['depth']),flush=True)
