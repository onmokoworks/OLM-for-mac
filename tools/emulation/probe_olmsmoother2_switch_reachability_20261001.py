#!/usr/bin/env python3
"""Replay retained geometry witnesses and construct natural missing-index inputs.

The eight dispatch bits compare the center to eight independent neighbors.
At (1,1) in a 4x3 image all required classifier guards are open. A black
center and black/white neighbors realize every index without injecting a
class plane. Native comparisons here are classifier/worker emulation, not AE.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
RETAINED = ROOT / 'refs/conformance/olmsmoother2_geometry_classifier_matrix_actual_aex_20260811.json'
REPLAY_HARNESS = ROOT / 'tools/emulation/olmsmoother2_geometry_classifier_matrix_production_harness_20260811.cpp'
HARNESS = ROOT / 'tools/emulation/olmsmoother2_switch_reachability_harness_20261001.cpp'
W, H = 4, 3
# Dispatch bit -> neighbor of the center at (1,1).
NEIGHBORS = ((0,0), (1,0), (2,0), (0,1), (2,1), (0,2), (1,2), (2,2))

def sha(data): return hashlib.sha256(data).hexdigest()

def fixture(index):
    pixels = [(0,0,0,255)] * (W*H)
    for bit, (x,y) in enumerate(NEIGHBORS):
        if not (index >> bit) & 1:
            pixels[y*W+x] = (255,255,255,255)
    return pixels

def typed_input(pixels, depth):
    chunks = []
    for r,g,b,a in pixels:
        if depth == 'PF8': chunks.append(struct.pack('<4B',a,r,g,b))
        elif depth == 'PF16': chunks.append(struct.pack('<4H',*(round(c*32768/255) for c in (a,r,g,b))))
        else: chunks.append(struct.pack('<4f',*(c/255 for c in (a,r,g,b))))
    return b''.join(chunks)

def parse(result):
    lines = dict(line.split(' ',1) for line in result.stdout.decode().splitlines())
    hist = {int(k):int(v) for k,v in (x.split(':') for x in lines['HIST'].split(','))} if lines['HIST'] else {}
    return bytes.fromhex(lines['RAW']), hist

def compile_harness(path, binary, sanitize=False):
    flags = ['-O1','-fsanitize=address,undefined','-fno-omit-frame-pointer'] if sanitize else ['-O2']
    subprocess.run(['clang++','-std=c++17',*flags,'-Wno-deprecated-declarations','-I',str(ROOT/'cli/OLMSmoother2/shim'),'-I',str(SOURCE.parent),str(path),'-o',str(binary)],check=True)

def replay(binary, retained):
    rows = []
    for c in retained['core_cases'] + retained['feature_cases']:
        s,r,e = retained['tuples'][c['tuple']]
        args = [str(binary),*map(str,c['geometry']),c['pattern'],str(c.get('version',2)),str(s),str(r),str(e),c['depth'],c.get('feature','none')]
        raw,hist = parse(subprocess.run(args,check=True,capture_output=True))
        rows.append({'id':c['id'],'tuple':c['tuple'],'version':c.get('version',2),'depth':c['depth'],'feature':c.get('feature','none'),'raw_sha256':sha(raw),'raw_exact':sha(raw)==c['raw_sha256'],'histogram_exact':hist=={int(k):v for k,v in c['switch_index_histogram'].items()}})
    return rows

def native_setup():
    import test_olmsmoother2_geometry_classifier_matrix_actual_aex_20260811 as matrix
    base = matrix.typed.AexLoader
    instances = []
    class AuditedLoader(base):
        def __init__(self,*args,**kwargs):
            self.executed_imports = set()
            self.import_errors = []
            super().__init__(*args,**kwargs)
            instances.append(self)
        def _on_code(self,uc,address,size,user_data):
            if address in self.import_stubs:
                dll,name = self.import_stubs[address]
                self.executed_imports.add(name)
                if name not in self.import_impls:
                    raise RuntimeError('Unimplemented executed import: '+dll+'!'+name)
            return super()._on_code(uc,address,size,user_data)
        def register_libm_impls(self,*args,**kwargs):
            super().register_libm_impls(*args,**kwargs)
            # The shared loader catches implementation exceptions. Retain them
            # and reject the resulting witness rather than accepting RAX=0.
            for name,impl in list(self.import_impls.items()):
                def audited(uc,args,fn=impl,label=name):
                    try: return fn(uc,args)
                    except Exception as exc:
                        self.import_errors.append(label+': '+repr(exc))
                        raise
                self.import_impls[name] = audited
    if sha(matrix.typed.AEX_PATH.read_bytes()) != matrix.typed.AEX_SHA256:
        raise RuntimeError('AEX identity mismatch')
    matrix.typed.AexLoader = AuditedLoader
    return matrix, instances

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native',action='store_true')
    ap.add_argument('--all-indices',action='store_true')
    ap.add_argument('--output',type=Path,required=True)
    args = ap.parse_args()
    retained = json.loads(RETAINED.read_text())
    missing = sorted(set(range(256))-set(retained['distinct_switch_indices']))
    targets = list(range(256)) if args.all_indices else missing
    matrix,instances = native_setup() if args.native else (None,[])
    rows = []
    with tempfile.TemporaryDirectory(prefix='sm2_switch_') as td:
        binary = Path(td)/'arbitrary'; old = Path(td)/'retained'
        compile_harness(HARNESS,binary); compile_harness(REPLAY_HARNESS,old)
        replay_rows = replay(old,retained)
        for index in targets:
            for version in (1,2):
                for depth in ('PF8','PF16','PF32'):
                    px = fixture(index); input_bytes = typed_input(px,depth)
                    raw,hist = parse(subprocess.run([str(binary),str(W),str(H),depth,str(version)],input=input_bytes,check=True,capture_output=True))
                    row = {'target_index':index,'version':version,'depth':depth,'input_sha256':sha(input_bytes),'production_raw_sha256':sha(raw),'production_histogram':hist,'target_reached':index in hist}
                    if matrix:
                        if depth=='PF8':
                            inv = matrix.f32(1/255)
                            encoded = [tuple(matrix.f32(matrix.f32(c)*inv) for c in p) for p in px]
                        elif depth=='PF16': encoded = [tuple(matrix.f32(round(c*32768/255)/32768) for c in p) for p in px]
                        else: encoded = [tuple(matrix.f32(c/255) for c in p) for p in px]
                        native,plane,ci,wi = matrix.actual(depth,version,encoded,matrix.DEPTHS[depth][1],W,H,100,2,0)
                        nh = matrix.histogram(plane,W,H)
                        # Isolate the intended center, not an incidental hit elsewhere.
                        single = bytearray(plane)
                        def bit(x,y,b): return single[(y*W+x)*4+b] != 0
                        center_index = sum((not present)<<i for i,present in enumerate((bit(1,1,2),bit(1,1,1),bit(1,1,3),bit(1,1,0),bit(2,1,0),bit(0,2,3),bit(1,2,1),bit(2,2,2))))
                        if instances[-1].import_errors: raise RuntimeError(str(instances[-1].import_errors))
                        row.update(native_raw_sha256=sha(native),native_class_plane_sha256=sha(plane),native_histogram=nh,native_center_index=center_index,raw_exact=raw==native,histogram_exact=hist==nh,native_center_reached=center_index==index,executed_imports=sorted(instances[-1].executed_imports),classifier_instructions=ci,worker_instructions=wi)
                    rows.append(row)
            print('index',index,'cases',len(rows),'differences',sum(r.get('raw_exact') is False for r in rows),flush=True)
    report = {'schema':'olmsmoother2.switch-reachability/1','production_source_sha256':sha(SOURCE.read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'harness_sha256':sha(HARNESS.read_bytes()),'retained_report_sha256':sha(RETAINED.read_bytes()),'retained_source_sha256':retained['production_source_sha256'],'retained_replay':replay_rows,'missing_indices_before':missing,'target_indices':targets,'geometry':[W,H],'center':[1,1],'settings':{'smoothness':100,'smooth_range':2,'extra_smooth':0,'key':False,'gamma':'none'},'native_emulation':args.native,'cases':rows,'claims_not_made':['No Windows AE execution','No public entry or native parameter-builder coverage','No arbitrary parameter or image generalization','No bit-exact Windows UCRT proof for host math or captured LUTs']}
    if matrix:
        report['aex_sha256'] = matrix.typed.AEX_SHA256
        report['decode_lut_sha256'] = sha(matrix.v2.DECODE)
        report['encode_lut_sha256'] = sha(matrix.v2.ENCODE)
        report['loader_sha256'] = sha((ROOT/'tools/emulation/aex_loader.py').read_bytes())
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    good = all(r['raw_exact'] and r['histogram_exact'] for r in replay_rows) and all(r['target_reached'] and (not args.native or (r['raw_exact'] and r['histogram_exact'] and r['native_center_reached'])) for r in rows)
    print('PASS' if good else 'DIFFERENT',len(replay_rows),'retained',len(rows),'new')
    return 0 if good else 1

if __name__ == '__main__': raise SystemExit(main())
