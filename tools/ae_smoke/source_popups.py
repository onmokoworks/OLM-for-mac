#!/usr/bin/env python3
"""Extract PF_ADD_POPUP declarations and resolve the source string table.
Does not claim that ExtendScript exposes third-party popup labels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from run_ae_smoke import ROOT, PLUGINS


def extract():
    rows=[]
    for name in PLUGINS:
        source=ROOT/f'mac/{name}/{name}.cpp'
        if name == 'OLMSmoother':
            source=ROOT/'mac/OLMSmoother/Mac/OLMSmoother_port.cpp'
        strings=ROOT/f'mac/{name}/{name}_Strings.cpp'
        text=source.read_text()
        table=dict(re.findall(r'\{\s*(StrID_\w+)\s*,\s*("(?:[^"\\]|\\.)*")\s*\}',strings.read_text()))
        popups=[]
        for match in re.finditer(r'PF_ADD_POPUP\((.*?)\);',text,re.S):
            args=match.group(1)
            ids=re.findall(r'GetStringPtr\((StrID_\w+)\)',args)
            if len(ids)!=2:
                raise ValueError(f'Unresolved popup in {source}: {args}')
            count_default=re.search(r'\),\s*(\d+)\s*,\s*([A-Za-z_0-9]+)\s*,',args)
            if not count_default:
                raise ValueError('Nonliteral popup count/default: '+args)
            default=count_default[2]
            if not default.isdigit():
                default=re.search(r'\b'+default+r'\s*=\s*(\d+)',source.with_suffix('.h').read_text())[1]
            popups.append(dict(name=json.loads(table[ids[0]]),labels=json.loads(table[ids[1]]).split('|'),
                count=int(count_default[1]),default=int(default),
                line=text[:match.start()].count('\n')+1,ae_labels=None,
                ae_label_status='unavailable: ExtendScript has no third-party popup label getter'))
        rows.append(dict(plugin=name,source=str(source.relative_to(ROOT)),
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            strings_sha256=hashlib.sha256(strings.read_bytes()).hexdigest(),
            header_sha256=hashlib.sha256((ROOT/f'mac/{name}/{name}.h').read_bytes()).hexdigest(),popups=popups))
    return rows

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    rows=extract()
    args.output.write_text(json.dumps(rows,indent=2)+'\n')
    print(f'{len(rows)} plugins, {sum(len(row["popups"]) for row in rows)} popup declarations')
