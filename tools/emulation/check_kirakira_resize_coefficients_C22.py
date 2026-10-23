#!/usr/bin/env python3
"""Check captured IPP RGBA half-scale coordinate tables, without pixel fitting."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    raw = args.trace.read_bytes()
    trace = json.loads(raw)
    result = dict(trace_sha256=hashlib.sha256(raw).hexdigest(), rows=[])
    for record in trace['rows']:
        assert record['public_bound'], 'unbound original trace'
        for call in record['aex_resize_writers']:
            sw, sh = call['source']
            dw, dh = call['destination']
            count = 0
            for row in call['horizontal_coefficients']:
                n = row['count']
                indices = struct.unpack('<'+'i'*n, bytes.fromhex(row['indices_hex']))
                weights = bytes.fromhex(row['weights_hex'])
                # IPP handles symmetric replicated borders separately. This
                # center-aligned interior table excludes those edge columns.
                assert (dw-n) % 2 == 0
                start = (dw-n)//2
                for i, index in enumerate(indices):
                    value = (i+start+0.5)*(sw/dw)-0.5
                    assert index == math.floor(value)*4, (record['index'], i, index, value)
                    assert struct.pack('<f', value-math.floor(value)) == weights[i*4:i*4+4]
                    count += 1
            for row in call['vertical_rows']:
                y = row['destination_word']//(dw*4)
                value = (y+0.5)*(sh/dh)-0.5
                assert struct.pack('<f', value-math.floor(value)).hex() == row['weight_hex']
                count += 1
            assert count > 0
            result['rows'].append(dict(source=call['source'], destination=call['destination'],
                                       coordinate_entries_exact=count))
    result['status'] = 'passed'
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print('PASS coordinate entries', sum(row['coordinate_entries_exact'] for row in result['rows']))


if __name__ == '__main__':
    main()
