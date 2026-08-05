#!/usr/bin/env python3
"""PF32 Rotation offset mode 3 natural actual-AEX/production fixture."""

import json
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as fixture

fixture.OUTER_STRENGTH=4
fixture.OUTER_OFFSET_MODE=3
fixture.OUTER_OFFSET=2
fixture.FIXTURE=fixture.ROOT/"refs/fixtures/olmradialblur_rotation_pf32_offset_mode3_small_20260805"
fixture.REPORT=fixture.ROOT/"refs/conformance/olmradialblur_rotation_pf32_offset_mode3_small_actual_aex_20260805.json"
fixture.EXPECTED={
 "source_pf32":("31fab74e9856c24ca6aa724ef8cd72dd2e53399286f1eecaaa2589edac3b0b33","e2f9ca3d94aa06ad68b6990d6a66912f1bffc77d20e91ad643a5d23f90bade19"),
 "polar":("aa822e3d1353b5eeff97581c7bf20bf4c73e8def305a9f2e4cb00f140aaa9ce3","5a083bd125c501c5d2b3aba8b02f7c7d366917e9bfaf289a92ca91bb6a9e2690"),
 "source_scalar":("7b4468c91d59a9b63747818dfcd672e87646e3c9b05bc3d7ce8d4efc160826bc","21d9bf07a607e761267078f796e5c6462d90df31d4e2d66f900655de740a75a4"),
 "accum":("d9bb8c3313c184cb14cbc8766f9eb2a2fc976899f6e180863323ea08bf11e927","ab5a36659088061e56f7649e77ecf6cbd7272016efea1319225f406164ea7524"),
 "max_alpha":("4408f98deb7c33c7bd738f47da8ca5032c8638aa7ec8abebea179d9eb8be759c","2ffa2dbb1641d2e2f4ea08cfe2fdc08349470b0189b98991a89a5603c6c686f3"),
 "coordinates":("e9c455c90aa39569783043925d1b890ae7cd67728a09a729b665d8b67976d07b","aaccf447e96339787ca82d3003a056cae7c03cab57f626370fb06ce1d60d1937"),
 "final_rgba":("a8f64911ad3b79539265ecf281ad914bae0344d8d12f881d5e4567b2a1cb7be4","735f5373a580b1ef86d953f6b6549b43d52df57119e246006c257c4171d15ca9"),
 "output":("8b1e9d6710a1ab31710d122dc81045dc50e31c2542ebf5b88340f572214ae11e","1e044be48190077fb33129003920f0027e24d130c60254a9496fa0bb9b013832"),
}

def main():
    code=fixture.main();report=json.loads(fixture.REPORT.read_text())
    report["kind"]="olmradialblur_rotation_pf32_offset_mode3_small_actual_aex_20260805"
    report["scope"]="independent PF32 Rotation mode 3/offset 2, padded 9x7; no other mode, depth, offset, geometry, or AE-host claim"
    report["parameter_branch"]={
      "outer_strength":4,"outer_offset_mode":3,"outer_offset_ui":2,
      "worker_offset_zero_based":1,"radius_half":4,
      "dynamic_worker_spans_by_radius":[4,2,1,1,0,0,0,0,0],
      "formula":"floor((radius_count/2)*(outer_offset_ui-1)/(radius_index+1))",
      "fixed_strength_branch_selected":False,
      "actual_accum_differs_from_mode1_baseline":True,
      "actual_output_differs_from_mode1_baseline":True,
    }
    fixture.REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");return code

if __name__=="__main__":raise SystemExit(main())
