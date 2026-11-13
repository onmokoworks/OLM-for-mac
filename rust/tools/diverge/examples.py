"""Small reproducible inputs for the worked examples; writes only a new directory/file."""
import argparse
from pathlib import Path
import shutil
import struct
import olm_diverge as d
import stage_maps


def directional(source, out):
    source, out = source.resolve(), out.resolve()
    manifest = d.load_json(source/'case.json')
    expected = manifest['assets']['input.png']
    if d.witness.sha256(source/'input.png') != expected:
        raise ValueError('source image hash changed')
    if manifest['case']['size'] != [31,19] or manifest['case']['downsample'] != '1':
        raise ValueError('worked example requires the saved 31x19 full-resolution case')
    out.mkdir(parents=True, exist_ok=False)
    (out/'requests').mkdir()
    shutil.copyfile(source/'input.png',out/'input.png')
    request = d.load_json(source/'requests/candidate.json')
    request['assignments'] = [{'slot':1,'components':[0]},{'slot':2,'value':1},{'slot':3,'value':0},
        {'slot':5,'value':8},{'slot':6,'value':0},{'slot':7,'value':0},{'slot':10,'value':3},
        {'slot':11,'value':0},{'slot':12,'value':0},{'slot':15,'value':0},{'slot':16,'value':1},
        {'slot':18,'value':1},{'slot':19,'components':[0]},{'slot':20,'value':10}]
    for side in ('reference','candidate'):
        d.write_json(out/'requests'/(side+'.json'), request)
    manifest['case']['assignments'] = request['assignments']
    manifest['assets'] = {str(p.relative_to(out)):d.witness.sha256(p) for p in
        [out/'input.png',out/'requests/reference.json',out/'requests/candidate.json']}
    d.write_json(out/'case.json',manifest)


def historical(original, candidate, out):
    if out.exists():
        raise ValueError('output exists')
    # Derived by zeroing the actual case-39 column-stage input. One nonzero word
    # remains; zeroing it makes the native/SSE result exact (14 measured trials).
    raw = bytearray(97*61*4)
    struct.pack_into('<I',raw,5915*4,0x3c9784c5)
    case = stage_maps.build('distance',original,candidate,w=97,h=61,kx=1,ky=8193,historical=True,source=bytes(raw))
    out.parent.mkdir(parents=True,exist_ok=True)
    d.write_json(out,case)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('directional-render')
    a.add_argument('source',type=Path)
    a.add_argument('--out',required=True,type=Path)
    a=sub.add_parser('historical-column')
    a.add_argument('--original',required=True,type=Path)
    a.add_argument('--candidate',required=True,type=Path)
    a.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    if args.command == 'directional-render': directional(args.source,args.out)
    else: historical(args.original,args.candidate,args.out)
