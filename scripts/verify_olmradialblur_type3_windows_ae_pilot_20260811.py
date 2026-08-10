#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument("return_root",type=Path);ap.add_argument("--package-root",type=Path);a=ap.parse_args()
    if a.package_root is None:
        here=Path(__file__).resolve().parent
        a.package_root=here if (here/"BATCH_CONTRACT.json").is_file() else here.parent
    sys.path.insert(0,str(a.package_root/"tools"))
    try:
        from olmradialblur_type3_pf32_pilot_contract_20260811 import validate_return
    except ImportError:
        # In the ZIP the validator sits beside BATCH_CONTRACT and carries a copy below.
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from olmradialblur_type3_pf32_pilot_contract_20260811 import validate_return
    try: result=validate_return(a.package_root,a.return_root)
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as e:
        print(f"[FAIL_CLOSED] {e}",file=sys.stderr);return 2
    print(json.dumps(result,indent=2));return 0
if __name__=="__main__": raise SystemExit(main())
