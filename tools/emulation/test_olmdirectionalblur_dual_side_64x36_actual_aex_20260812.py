#!/usr/bin/env python3
"""Promote the four proven dual-side tuples to padded 64x36."""
from __future__ import annotations
import importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/emulation/test_olmdirectionalblur_dual_side_32x18_actual_aex_20260811.py'
REPORT=ROOT/'refs/conformance/olmdirectionalblur_dual_side_64x36_actual_aex_20260812.json'
NOTE=ROOT/'refs/conformance/olmdirectionalblur_dual_side_64x36_actual_aex_20260812.md'

def main()->int:
 spec=importlib.util.spec_from_file_location('dblur_dual64_base',BASE)
 if spec is None or spec.loader is None: raise RuntimeError('base import')
 m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 m.W,m.H=64,36; m.REPORT,m.NOTE=REPORT,NOTE
 rc=m.main()
 report=json.loads(REPORT.read_text()); reps=report['representatives']
 widths={r['rowdriver_first_call']['width'] for r in reps}; ranges={tuple(map(tuple,r['rowdriver_ranges'])) for r in reps}
 if len(widths)!=1 or len(ranges)!=1: raise RuntimeError('owner partition differs across cells')
 work_width=next(iter(widths)); row_ranges=list(next(iter(ranges)))
 expected_ranges=[(i*2,(i+1)*2) for i in range(32)]
 if row_ranges != expected_ranges: raise RuntimeError(f'unexpected owner row partition: {row_ranges}')
 report.update({'schema_version':1,'status':'exact_bounded_geometry_promotion','geometry':[64,36],
                'control_geometry':[32,18],
                'rotated_work_partition':{'work_width':work_width,'worker_calls':len(row_ranges),
                    'row_ranges':[list(x) for x in row_ranges],
                    'contract':'actual owner 32 two-row partitions cover rows 0..63; rotated rows 64..75 remain preseeded before rotate-back'},
                'admission':'Only the existing four dual-side tuples at 64x36 are newly admitted.',
                'fail_closed':['other dual-side tuple','geometry other than 16x16, 32x18, or 64x36','Noise Type 3']})
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 NOTE.write_text(f'# OLMDirectionalBlur simultaneous Front + Back at 64×36 — 2026-08-12\n\nThe four dual-side tuples are raw exact at padded 64×36 for PF8/PF16/PF32 (12 cells). The actual owner uses a rotated work width of {work_width} and 32 two-row worker calls covering rows 0..63; rotated rows 64..75 stay preseeded before rotate-back. The prior 32×18 matrix remains the control. Admission is limited to 16×16, 32×18, and 64×36; Type 3 and unlisted tuples remain fail-closed.\n\nReproduction: `python3 tools/emulation/test_olmdirectionalblur_dual_side_64x36_actual_aex_20260812.py`\n')
 print('PASS_OLMDIRECTIONALBLUR_DUAL_SIDE_64X36 PF8=4 PF16=4 PF32=4 raw=exact')
 return rc
if __name__=='__main__': raise SystemExit(main())
