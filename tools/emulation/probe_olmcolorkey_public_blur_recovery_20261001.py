#!/usr/bin/env python3
"""Capture the revised recovery with its own dependency and matrix binding."""
import argparse,json,sys
from pathlib import Path
import colorkey_public_blur_candidate_20261001 as recovery
owner=recovery.initial
def main():
    ap=argparse.ArgumentParser(add_help=False);ap.add_argument('--toggle-transfer',action='store_true')
    options,remaining=ap.parse_known_args()
    original=owner.SOURCE.read_text();candidate=recovery.candidate_source(original)
    def frozen_candidate(body):
        assert body==original
        return candidate
    owner.candidate_source=frozen_candidate
    if options.toggle_transfer:
        assert '--full' in remaining and '--boundaries' not in remaining
        owner.thin_owner.general.FIXTURES=owner.thin_owner.general.FIXTURES[1:2]
    sys.argv=[sys.argv[0],*remaining];owner.main()
    path=Path(remaining[remaining.index('--report')+1]);r=json.loads(path.read_text())
    r['recovery_probe_sha256']=owner.sha(Path(__file__).read_bytes())
    r['recovery_candidate_tool_sha256']=owner.sha(Path(recovery.__file__).read_bytes())
    r['matrix']='17x15-mixed-four-toggles' if options.toggle_transfer else 'boundary-three-geometries'
    head=dict(r);del head['cases'];text=json.dumps(head,sort_keys=True,indent=2)[:-2]+',\n  "cases": [\n'+',\n'.join('    '+json.dumps(c,sort_keys=True) for c in r['cases'])+'\n  ]\n}\n'
    path.write_text(text);assert json.loads(text)==r
if __name__=='__main__':main()
