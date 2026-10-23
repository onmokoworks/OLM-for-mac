#!/usr/bin/env python3
"""Reuse the C54 public/sanitized comparison for the C56 Bilateral timeout."""
import copy
import struct
import sys
sys.dont_write_bytecode = True
import probe_distancegradation_C54 as probe

original_matrix = probe.matrix
original_negatives = probe.negatives
target_case = (1, 10)
radius_two = False
median = False


def matrix(adapter, mode, extreme=False):
    if mode == 'target':
        yield f'seed{target_case[0]}/{target_case[1]}', adapter.generate(*target_case)
    else:
        for label, case in original_matrix(adapter, mode, extreme):
            if median:
                if case['depth'] == 32:
                    values = list(struct.unpack('<'+'f'*(len(case['pixels'])//4), case['pixels']))
                    case['pixels'] = struct.pack('<'+'f'*len(values), *(max(0., min(1., v)) for v in values))
                for p in case['parameters']:
                    if p['slot'] == 11: p['value'] = 4
                    if p['slot'] == 12: p['value'] = 1 if p['value'] == 3 else 2
                label = 'median/' + label
            if radius_two:
                size = next(p for p in case['parameters'] if p['slot'] == 12)
                old_size = size['value']
                size['value'] = 2
                label = label.replace('size33', 'size2').replace('size392', 'size2').replace('size500', 'size2')
                if old_size == 500:
                    for w, h in ((4,9),(19,3),(3,19)):
                        expanded = copy.deepcopy(case)
                        raw = expanded['pixels']
                        expanded['geometry'] = [w,h]
                        expanded['pixels'] = (raw*((w*h*16+len(raw)-1)//len(raw)))[:w*h*16]
                        yield label.replace('7x3',f'{w}x{h}'), expanded
                    continue
            yield label, case


def negatives(adapter):
    for label, case in original_negatives(adapter):
        if radius_two and label == 'radius2':
            case['geometry'] = [5,5]
            raw = case['pixels']
            case['pixels'] = (raw*2)[:5*5*16]
            label = 'radius2-non-scalar-shape'
        yield label, case


if __name__ == '__main__':
    if '--median' in sys.argv:
        median = True
        sys.argv.remove('--median')
    if '--radius-two' in sys.argv:
        radius_two = True
        sys.argv.remove('--radius-two')
    if '--target-case' in sys.argv:
        i = sys.argv.index('--target-case')
        target_case = (int(sys.argv[i+1]), int(sys.argv[i+2]))
        del sys.argv[i:i+3]
    probe.matrix = matrix
    probe.negatives = negatives
    probe.main()
