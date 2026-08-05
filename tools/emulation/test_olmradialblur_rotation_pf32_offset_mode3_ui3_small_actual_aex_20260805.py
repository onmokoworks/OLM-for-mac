#!/usr/bin/env python3
"""PF32 Rotation offset mode 3/UI 3 actual-AEX/production fixture."""

import json
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as fixture

fixture.OUTER_STRENGTH=4;fixture.OUTER_OFFSET_MODE=3;fixture.OUTER_OFFSET=3
fixture.FIXTURE=fixture.ROOT/"refs/fixtures/olmradialblur_rotation_pf32_offset_mode3_ui3_small_20260805"
fixture.REPORT=fixture.ROOT/"refs/conformance/olmradialblur_rotation_pf32_offset_mode3_ui3_small_actual_aex_20260805.json"
fixture.EXPECTED={
 "source_pf32":("31fab74e9856c24ca6aa724ef8cd72dd2e53399286f1eecaaa2589edac3b0b33","e2f9ca3d94aa06ad68b6990d6a66912f1bffc77d20e91ad643a5d23f90bade19"),
 "polar":("aa822e3d1353b5eeff97581c7bf20bf4c73e8def305a9f2e4cb00f140aaa9ce3","5a083bd125c501c5d2b3aba8b02f7c7d366917e9bfaf289a92ca91bb6a9e2690"),
 "source_scalar":("7b4468c91d59a9b63747818dfcd672e87646e3c9b05bc3d7ce8d4efc160826bc","21d9bf07a607e761267078f796e5c6462d90df31d4e2d66f900655de740a75a4"),
 "accum":("eae0443e8886c9f678897b16629efae682db077bc3151994bfa18deb066c5098","8645a4bc83b908303b5461138475a3e4c9979ec1e0fd2738b95b412a6de1bf63"),
 "max_alpha":("4408f98deb7c33c7bd738f47da8ca5032c8638aa7ec8abebea179d9eb8be759c","2ffa2dbb1641d2e2f4ea08cfe2fdc08349470b0189b98991a89a5603c6c686f3"),
 "coordinates":("e9c455c90aa39569783043925d1b890ae7cd67728a09a729b665d8b67976d07b","aaccf447e96339787ca82d3003a056cae7c03cab57f626370fb06ce1d60d1937"),
 "final_rgba":("bc9937f6c44315d474aae7785cfb49fc7bd9b7979d39e53dfbbb5b52620cefd7","a79a6a13c7054b31eb36418365cc44e3ed14c793d9c1b0df6ee28d52d4260872"),
 "output":("cee87fb72088c48c34c882f18b3bb0ba579343cbb517face958def078ec34a88","4d9744f5c9917f20d94e7e25ed9a949e76c084fdc56d7eb44dd312c8ebe52b28"),
}

def main():
    code=fixture.main();report=json.loads(fixture.REPORT.read_text())
    report["kind"]="olmradialblur_rotation_pf32_offset_mode3_ui3_small_actual_aex_20260805"
    report["scope"]="independent PF32 Rotation mode 3/UI offset 3, padded 9x7; explicit bounded gate, no other offset/depth/geometry or AE-host claim"
    report["parameter_branch"]={
      "outer_strength":4,"outer_offset_mode":3,"outer_offset_ui":3,
      "worker_offset_zero_based":2,"radius_half":4,
      "dynamic_worker_spans_by_radius":[8,4,2,2,1,1,1,1,0],
      "ui2_spans":[4,2,1,1,0,0,0,0,0],
      "formula":"floor((radius_count/2)*(outer_offset_ui-1)/(radius_index+1))",
      "non_equivalent_to_ui2":True,"fixed_strength_branch_selected":False,
      "actual_output_differs_from_ui2":True,
      "length8_aex_weight_words":{"i5":"0x3e308f4e","i7":"0x3d02a41f"},
    }
    fixture.REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");return code

if __name__=="__main__":raise SystemExit(main())
