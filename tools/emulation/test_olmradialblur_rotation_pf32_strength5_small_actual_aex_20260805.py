#!/usr/bin/env python3
"""PF32 Rotation Outer Strength 5 natural actual-AEX/production fixture."""

import json
from pathlib import Path
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as fixture

fixture.OUTER_STRENGTH=5
fixture.OUTER_OFFSET_MODE=1
fixture.OUTER_OFFSET=0
fixture.FIXTURE=fixture.ROOT/"refs/fixtures/olmradialblur_rotation_pf32_strength5_small_20260805"
fixture.REPORT=fixture.ROOT/"refs/conformance/olmradialblur_rotation_pf32_strength5_small_actual_aex_20260805.json"
fixture.EXPECTED={
 "source_pf32":("31fab74e9856c24ca6aa724ef8cd72dd2e53399286f1eecaaa2589edac3b0b33","e2f9ca3d94aa06ad68b6990d6a66912f1bffc77d20e91ad643a5d23f90bade19"),
 "polar":("aa822e3d1353b5eeff97581c7bf20bf4c73e8def305a9f2e4cb00f140aaa9ce3","5a083bd125c501c5d2b3aba8b02f7c7d366917e9bfaf289a92ca91bb6a9e2690"),
 "source_scalar":("7b4468c91d59a9b63747818dfcd672e87646e3c9b05bc3d7ce8d4efc160826bc","21d9bf07a607e761267078f796e5c6462d90df31d4e2d66f900655de740a75a4"),
 "accum":("1f2b04046a3ae0c60407af8a928d74e27a17bdf0c73c6e8473154beb97d91ae7","d6752684d3c1f78f2624e57d3bf35087187f53928cc314d9eb797e383e90dade"),
 "max_alpha":("4b63bcde7212e5bf5854c9dbd67b29ac20e8e47f3256ddf05870723b0c495acc","b82e5eab50766b23897b967342757a0ec474abf6a47c5e2b79df369aa60fbe0e"),
 "coordinates":("e9c455c90aa39569783043925d1b890ae7cd67728a09a729b665d8b67976d07b","aaccf447e96339787ca82d3003a056cae7c03cab57f626370fb06ce1d60d1937"),
 "final_rgba":("7c3f8b5a19e9e8559539f779050d0ed6f900024ede6683cf44ab190eb814ce12","5bf0d427ee6369dbcd0dfe9ffd2f0a6005f000e62336c5329d69fb7e8e2b2a9e"),
 "output":("f32900f11ea537c4b818879f6b04d1a473e8ab09101ee008170f1d2b2eb408ca","8736195b170f64c540b71d27af6e019e6f609f1c805724408be6308bc79708ac"),
}

def main():
    code=fixture.main()
    report=json.loads(fixture.REPORT.read_text())
    report["kind"]="olmradialblur_rotation_pf32_strength5_small_actual_aex_20260805"
    report["scope"]="independent PF32 Rotation Outer Strength 5, mode 1/offset 0, padded 9x7; distinct from Strength 4 baseline; no other depth or AE-host claim"
    report["parameter_branch"]={"outer_strength":5,"baseline_outer_strength":4,"outer_offset_mode":1,"outer_offset":0,"actual_accum_differs_from_baseline":True,"actual_output_differs_from_baseline":True}
    fixture.REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return code

if __name__=="__main__":raise SystemExit(main())
