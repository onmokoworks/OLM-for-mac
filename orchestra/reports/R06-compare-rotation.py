#!/usr/bin/env python3
"""Compare a current typed production capture to two original C53b traces."""
import base64, importlib, json, os, struct, sys, tempfile, zlib, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'orchestra/state/R06-release-gate-closure'
os.environ.update(TMPDIR=str(S),TMP=str(S),TEMP=str(S),OLM_TEST_JOBS='2',PYTHONDONTWRITEBYTECODE='1');tempfile.tempdir=str(S)
sys.path[:0]=[str(ROOT),str(ROOT/'tools/emulation')]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    index=int(sys.argv[1]);old=next(r for r in json.loads((ROOT/'orchestra/reports/F39-evidence.json').read_text()) if r['command_index']==index)
    q=old['profile'];d=S/str(index)
    m=importlib.import_module('test_olmradialblur_rotation_pf32_small_actual_aex_20260805')
    if q.get('large'):
        x=importlib.import_module('test_olmradialblur_pf32_ellipse_32x18_actual_aex_20260811');x.configure_rotation(q.get('ratio',1),0)
    b=m.base
    for key,value in dict(OUTER_STRENGTH=q.get('strength',4),OUTER_OFFSET_MODE=3 if 'offset' in q else 1,OUTER_OFFSET=q.get('offset',0),RATIO=q.get('ratio',1),OUTER_EDGE_FADE=q.get('fade',0),SIZE_VARIATION=q.get('size',0),NOISE_VARIATION=q.get('noise',0)).items():
        setattr(m,key,value);setattr(b,'FIXTURE_'+key,value)
    if q.get('depth')==16:m=b
    if q.get('zoom'):
        if q.get('depth',32)==32:
            x=importlib.import_module('test_olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810');x.configure(q.get('inner',0),q.get('noise',0));m=x.zoom
        else:m=importlib.import_module('test_olmradialblur_zoom_pf16_small_actual_aex_20260805')
        m.OUTER_STRENGTH=q.get('strength',4)
    cells=old['legacy_vs_mac'].get('polar',old['legacy_vs_mac'].get('pre_blur'))['left_bytes']//16
    assert cells%1800==0
    frame=m.fixture if q.get('zoom') else m
    raw=frame.source_frame();packed=b''.join(raw[y*frame.ROWBYTES:y*frame.ROWBYTES+frame.VISIBLE] for y in range(frame.H));assert sha(packed)==old['source_sha256']
    mac=m.mac_production({'geometry':struct.pack('<II',1800,cells//1800)})
    traces=[json.loads((d/f'worker-C53b-trace-{n}'/'trace.json').read_text()) for n in (1,2)]
    for trace in traces:
        assert not trace['truncated'] and trace['dropped_memory_witnesses']==0
        assert not trace['trace_configuration']['unhookable_watches']
        assert trace['image_sha256']=='ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb'
    bindings={'polar':('2780-polar','before'),'source_scalar':('2780-source_scalar','before'),'prepass_alpha':('2780-prepass_alpha','after'),'accum':('24c0-accum','after'),'max_alpha':('24c0-max_alpha','after'),'final_rgba':('4640-final','after')}
    if q.get('zoom'):bindings={'pre_blur':('zoom-pre','before'),'post_blur':('zoom-post','before')}
    rows={}
    for name,(watch,stage) in bindings.items():
        if name not in mac:continue
        snapshots=[next(w for w in t['memory_witnesses'] if w['watch_id']==watch)[stage] for t in traces]
        originals=[bytes.fromhex(v['hex']) for v in snapshots]
        hashes=[v['sha256'] for v in snapshots]
        assert all(v['status']=='captured' and len(raw)==v['size'] and sha(raw)==v['sha256'] for v,raw in zip(snapshots,originals))
        assert originals[0]==originals[1]
        assert len(originals[0])==len(mac[name])
        mismatches=[i for i,(a,b) in enumerate(zip(originals[0],mac[name])) if a!=b]
        (d/f'original-{name}.zlib').write_bytes(zlib.compress(originals[0],9))
        rows[name]=dict(original_hashes=hashes,mac_sha256=sha(mac[name]),bytes=len(mac[name]),repeat_identical=originals[0]==originals[1],different_bytes=len(mismatches),first_byte=mismatches[0] if mismatches else None,exact=originals[0]==mac[name])
        (d/f'mac-{name}.zlib').write_bytes(zlib.compress(mac[name],9))
    packed_output=b''.join(mac['output'][y*frame.ROWBYTES:y*frame.ROWBYTES+frame.VISIBLE] for y in range(frame.H))
    finals=[zlib.decompress((d/f'{worker}-{repeat}'/'output.argb.zlib').read_bytes()) for worker in ('worker-F46-pow','worker-C53b-trace') for repeat in (1,2)]
    assert all(raw==finals[0] for raw in finals)
    final_diff=[i for i,(a,b) in enumerate(zip(finals[0],packed_output)) if a!=b]
    assert len(finals[0])==len(packed_output)
    rows['output']=dict(bytes=len(packed_output),original_hashes=[sha(v) for v in finals],mac_sha256=sha(packed_output),repeat_identical=True,different_bytes=len(final_diff),first_byte=final_diff[0] if final_diff else None,exact=packed_output==finals[0])
    padding_base=m.PADDING_BASE if q.get('zoom') else 0xc0 if old['depth']==32 else 0xa0
    padding_exact=all(mac['output'][y*frame.ROWBYTES+frame.VISIBLE:(y+1)*frame.ROWBYTES]==bytes([(padding_base+y)&255])*(frame.ROWBYTES-frame.VISIBLE) for y in range(frame.H))
    assert padding_exact
    report=dict(command_index=index,padding_exact=padding_exact,planes=rows,scope='F39 first witness only; coordinates/padding and full legacy commands remain separate',production_source_sha256=sha(frame.SOURCE.read_bytes()))
    if not all(row['exact'] for row in rows.values()):
        witness=dict(schema='olm-fuzz-case/1',plugin='radialblur',generator_version=1,seed=0,index=index,max_size=1920,operations=[],case=dict(geometry=old['geometry'],depth=old['depth'],parameters=old['parameters'],input_padding=0,output_padding=0),input_sha256=sha(packed),pixels_zlib_base64=base64.b64encode(zlib.compress(packed,9)).decode(),result=report,provenance=dict(ticket='R06',scope='intermediate-plane comparison; final output is checked separately'),reduction=dict(attempts=0,accepted=[],bounded=True,minimality_claimed=False))
        (d/'witness.json').write_text(json.dumps(witness,indent=2)+'\n')
    (d/'planes.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
