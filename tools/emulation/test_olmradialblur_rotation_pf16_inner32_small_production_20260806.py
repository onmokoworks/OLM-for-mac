#!/usr/bin/env python3
"""Bounded production PF16 Rotation Inner32 against pinned actual-AEX planes."""
import hashlib,json,sys,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE))
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as base
FIX=ROOT/'refs/fixtures/olmradialblur_rotation_pf16_inner32_small_20260806'
REPORT=ROOT/'refs/conformance/olmradialblur_rotation_pf16_inner32_small_production_20260806.json'
def raw(n):return zlib.decompress((FIX/f'{n}.bin.zlib').read_bytes())
def sha(x):return hashlib.sha256(x).hexdigest()
def main():
 base.FIXTURE_OUTER_STRENGTH=0;base.FIXTURE_INNER_STRENGTH=32
 expected={'geometry':(1800).to_bytes(4,'little')+(9).to_bytes(4,'little'),'polar':raw('pre_b150__polar_rgba'),'source_scalar':raw('post_normalize__span_gate'),'accum':raw('post_normalize__accum_rgba'),'max_alpha':raw('post_normalize__max_alpha'),'final_rgba':raw('final_rgba'),'output':raw('output')}
 production=base.mac_production(expected);expected.pop('geometry')
 matches={k:production[k]==v for k,v in expected.items()}
 gates={**matches,'padding_exact':all(production['output'][y*80+72:(y+1)*80]==bytes([0xa0+y])*8 for y in range(7))}
 report={'kind':'olmradialblur_rotation_pf16_inner32_small_production_20260806','status':'exact' if all(gates.values()) else 'fail_closed','scope':'Production PF16 audited 9x7 rowbytes80 Rotation Inner32 tuple only; internal accum/max and padded output against pinned actual-AEX','gates':gates,'hashes':{k:{'actual':sha(v),'production':sha(production[k])} for k,v in expected.items()}}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True));return 0 if report['status']=='exact' else 2
if __name__=='__main__':raise SystemExit(main())
