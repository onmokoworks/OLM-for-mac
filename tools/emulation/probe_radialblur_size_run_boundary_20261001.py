#!/usr/bin/env python3
"""Read actual source masks/areas/factors and test row-end count/write behavior."""
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import subprocess

from PIL import Image
import probe_radialblur_rotation_size_noise_20261001 as restoration
public = restoration.public
fields = restoration.fields


def masks():
    result = [([20, 14], 'opaque', [1]*280), ([7, 5], 'empty', [0]*35), ([7, 5], 'opaque', [1]*35),
              ([1, 5], 'column', [1]*5), ([5, 1], 'row', [1]*5)]
    for name, predicate in [
        ('left_column', lambda x,y: x == 0),
        ('right_column', lambda x,y: x == 6),
        ('later_right_overwrites_left', lambda x,y: x == 0 or (x == 6 and y < 4)),
        ('separate_row_end', lambda x,y: (y == 0 and x >= 5) or (y == 1 and x <= 1)),
        ('merge_inside', lambda x,y: x in (0,6) or y == 2),
        ('alternating_runs', lambda x,y: (x+y) % 2 == 0),
        ('small_hole', lambda x,y: not (x == 3 and y in (1,2,3))),
        ('two_floating_runs', lambda x,y: (x >= 4 and y in (0,1)) or (x <= 2 and y in (2,3))),
        ('mixed_edges', lambda x,y: (x in (0,6) and y % 2 == 0) or (y in (1,3) and x <= 3)),
    ]:
        result.append(([7, 5], name, [int(predicate(x,y)) for y in range(5) for x in range(7)]))
    assert len(result) == 14
    return result


def component_model(w, h, mask, size):
    labels = [0]*(w*h); areas = [0]
    for start, on in enumerate(mask):
        if not on or labels[start]: continue
        label = len(areas); labels[start] = label; pending = [start]; area = 0
        while pending:
            cell = pending.pop(); area += 1; x,y = cell % w, cell//w
            for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if not (0 <= nx < w and 0 <= ny < h): continue
                other = ny*w+nx
                if mask[other] and not labels[other]: labels[other] = label; pending.append(other)
        areas.append(area)
    for edge in range(w-1, w*h-1, w):
        if mask[edge] and mask[edge+1]: areas[labels[edge]] += 1
    maximum = max(areas); values = []
    for cell, label in enumerate(labels):
        if cell > 0 and cell % w == 0 and mask[cell-1] and mask[cell]: label = max(label, labels[cell-1])
        values.append(areas[label])
    inverse = fields.f32(1/maximum) if maximum else 1.0
    sv = fields.f32(fields.f32(size)*fields.f32(.01)); remain = fields.f32(1-sv)
    factors = [fields.f32(fields.f32(fields.f32(float(a)*inverse)*sv)+remain) for a in values]
    return struct.pack('<%df'%len(values), *values), struct.pack('<%df'%len(factors), *factors), maximum, sorted(areas[1:])


def fixtures():
    seed = next(row for row in json.loads(restoration.BEFORE.read_text())['rows'] if row['matrix'] == 'getters' and row['row_index'] == 27)
    result = []
    for geometry, name, mask in masks():
        for size in [25, 100]:
            case = {key: copy.deepcopy(seed[key]) for key in ['family', 'parameters']}
            case.update(geometry=geometry, pattern=name, depth=32, mask=mask, size=size, row_index=len(result))
            for q in case['parameters']:
                if q['slot'] == 2: q['value'] = [geometry[0]//2, geometry[1]//2]
                if q['slot'] == 7: q['value'] = 0
                if q['slot'] == 22: q['value'] = size
                if q['slot'] == 24: q['value'] = 25
            result.append(case)
    return result


def pixels(case):
    w,h = case['geometry']; return [(255 if case['mask'][y*w+x] else 0, 71, 89, 107) for y in range(h) for x in range(w)]


def source(case, depth):
    values = pixels(case)
    if depth == 8: return b''.join(bytes(row) for row in values)
    if depth == 16: return b''.join(struct.pack('<4H', *((c*32768+127)//255 for c in row)) for row in values)
    return b''.join(struct.pack('<4f', *(c/255 for c in row)) for row in values)


def trace(worker, directory, case):
    w,h = case['geometry']; image = Image.new('RGBA', (w,h)); image.putdata([(r,g,b,a) for a,r,g,b in pixels(case)]); image.save(directory/'input.png')
    assignments = [f"param_{q['slot']}@{q['slot']}"+(':angle' if q['kind']=='a' else '')+'='+(','.join(map(str,q['value'])) if isinstance(q['value'],list) else str(q['value'])) for q in public.native_case(case)['parameters']]
    watches = []
    for spec in [f'function=0x8930,arg=rdx,size={w*h+1},occurrence=1', f'function=0x8930,arg=r8,size={w*h*4},occurrence=1',
                 'function=0x8930,arg=rcx,size=16,occurrence=1', f'function=0x6aa0,arg=rcx,deref=0x88,size={w*h*4},occurrence=1']:
        watches += ['--watch',spec]
    run = subprocess.run([str(worker),'render-trace-png',str(public.initial.AEX),str(directory/'input.png'),str(directory/'trace.png'),'--pixel-format','argb32f',*watches,*assignments],capture_output=True,check=True)
    (directory/'trace.json').write_bytes(run.stdout); report=json.loads(run.stdout)
    assert not report['render_error'] and report['guards_intact']
    assert not report['unsupported_suite_calls'] and not report['dropped_unsupported_suite_calls']
    smart=next(t for t in report['execution_traces'] if t['selector']=='SMART_RENDER')
    assert not smart['truncated'] and not smart['dropped_memory_witnesses'] and not smart['trace_configuration']['unhookable_watches']
    witness={q['watch_id']:q for q in smart['memory_witnesses']}; assert len(witness)==4
    mask=bytes.fromhex(witness['watch-1']['before']['hex']); area=bytes.fromhex(witness['watch-2']['after']['hex'])
    context=bytes.fromhex(witness['watch-3']['after']['hex']); factor=bytes.fromhex(witness['watch-4']['before']['hex'])
    assert mask==bytes(case['mask'])+b'\0'
    maximum=struct.unpack_from('<i',context,12)[0]
    for name, data in [('mask',mask),('area',area),('factor',factor),('context',context)]: (directory/f'{name}.bin').write_bytes(data)
    return area,factor,maximum,{'trace_sha256':public.sha(run.stdout),'raw_sha256':report['raw_pixel_sha256'],'witness_count':4,'guards_intact':True,'mask_guard_byte':0}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True)
    args=ap.parse_args();args.output.mkdir(exist_ok=False,parents=True)
    capture=json.loads(restoration.BEFORE.read_text());build=json.loads((public.ROOT/'reports/radialblur_readonly_windows_reference_build_20261001.json').read_text())
    assert public.sha(args.worker.read_bytes())==build['worker_sha256'];assert public.sha(public.initial.AEX.read_bytes())==capture['aex_sha256']
    start_source=public.sha(public.SOURCE.read_bytes()); candidate=restoration.candidate_source(restoration.before_source())
    harness=public.initial.HARNESS
    try:
        public.initial.HARNESS=Path(__file__).with_name('radialblur_size_factor_sdk_harness_20261001.cpp')
        binaries={name:public.build(args.output/name,candidate,name=='san') for name in ['o2','san']}
    finally:public.initial.HARNESS=harness
    env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1');rows=[]
    for case in fixtures():
        directory=args.output/f"case_{case['row_index']}";directory.mkdir();area,factor,maximum,record=trace(args.worker,directory,case)
        model_area,model_factor,model_maximum,areas=component_model(*case['geometry'],case['mask'],case['size'])
        assert area==model_area and factor==model_factor and maximum==model_maximum,(case['pattern'],case['size'],maximum,model_maximum,fields.compare_words(area,model_area),fields.compare_words(factor,model_factor))
        for name,binary in binaries.items():
            for depth in [8,16,32]:
                input_file=directory/f'input_{depth}.raw';input_file.write_bytes(source(case,depth))
                run=subprocess.run([str(binary),*map(str,case['geometry']),str(depth),str(case['size']),str(input_file)],capture_output=True,check=True,env=env)
                assert run.stdout==factor;assert run.stderr.decode().strip()=='AREAS'+''.join(' '+str(a) for a in areas)
        rows.append({'case':case,'trace':record,'maximum_area':maximum,'component_areas':areas,'area_sha256':public.sha(area),'factor_sha256':public.sha(factor),'area_word_count':len(area)//4,'typed_sdk_replays':6})
        print('SIZE_RUN',case['pattern'],case['size'],maximum,areas,flush=True)
    assert public.sha(public.SOURCE.read_bytes())==start_source
    import pefile
    pe=pefile.PE(str(public.initial.AEX))
    report={'schema':'radialblur.size-run-boundary/1','source_sha256':public.sha(candidate.encode()),'source_before_sha256':capture['source_sha256'],'aex_sha256':capture['aex_sha256'],'window_worker_sha256':build['worker_sha256'],'probe_start_source_sha256':start_source,'production_source_changed_during_probe':False,'summary':{'case_count':len(rows),'native_source_maps_exact':len(rows),'typed_sdk_replays':len(rows)*6},'rows':rows,'scanner_read_before_bound_code_sha256':public.sha(pe.get_data(0x8ad0,0x19)),'inclusive_run_write_code_sha256':public.sha(pe.get_data(0x8da0,0x40)),'normalization_code_sha256':public.sha(pe.get_data(0x8294,0x3a)),'dependencies_sha256':{str(p.relative_to(public.ROOT)):public.sha(p.read_bytes()) for p in [Path(__file__),Path(restoration.__file__),Path(__file__).with_name('radialblur_size_factor_sdk_harness_20261001.cpp')]},'claims_not_made':['Read-only natural owner masks have a measured zero end guard; arbitrary native allocator contents and non-finite alpha are not proved.','Finite run masks do not prove all geometry/inputs, native Windows AE/UCRT/ROI/downsample or all-ten completion.']}
    args.report.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print('SIZE_RUN_DONE',report['summary'],flush=True)


if __name__=='__main__':main()
