#!/usr/bin/env python3
"""PF32 Rotation offset mode 3/UI 4 actual-AEX/production fixture."""

import json
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as fixture

fixture.OUTER_STRENGTH=4;fixture.OUTER_OFFSET_MODE=3;fixture.OUTER_OFFSET=4
fixture.FIXTURE=fixture.ROOT/"refs/fixtures/olmradialblur_rotation_pf32_offset_mode3_ui4_small_20260805"
fixture.REPORT=fixture.ROOT/"refs/conformance/olmradialblur_rotation_pf32_offset_mode3_ui4_small_actual_aex_20260805.json"
fixture.EXPECTED={
 "source_pf32":("31fab74e9856c24ca6aa724ef8cd72dd2e53399286f1eecaaa2589edac3b0b33","e2f9ca3d94aa06ad68b6990d6a66912f1bffc77d20e91ad643a5d23f90bade19"),
 "polar":("aa822e3d1353b5eeff97581c7bf20bf4c73e8def305a9f2e4cb00f140aaa9ce3","5a083bd125c501c5d2b3aba8b02f7c7d366917e9bfaf289a92ca91bb6a9e2690"),
 "source_scalar":("7b4468c91d59a9b63747818dfcd672e87646e3c9b05bc3d7ce8d4efc160826bc","21d9bf07a607e761267078f796e5c6462d90df31d4e2d66f900655de740a75a4"),
 "accum":("0ddf8481cbd51ff20d11d085beff66ae34787554a507fb411d0163f6265cf0fc","8cd6d125c65b358ff4d4aa84d92483688f4cc433b4f7e9fa5d74666fd33ee3da"),
 "max_alpha":("4408f98deb7c33c7bd738f47da8ca5032c8638aa7ec8abebea179d9eb8be759c","2ffa2dbb1641d2e2f4ea08cfe2fdc08349470b0189b98991a89a5603c6c686f3"),
 "coordinates":("e9c455c90aa39569783043925d1b890ae7cd67728a09a729b665d8b67976d07b","aaccf447e96339787ca82d3003a056cae7c03cab57f626370fb06ce1d60d1937"),
 "final_rgba":("874e10885088e49fe7bc2375ed7e330bf0c42df5c62a8de3ac13e69ff14c4d71","ec7e3e9664c4d4b28c7dc11fe8f1aaa5d8959367d756f61d2feb3c673f51fea9"),
 "output":("45027094459b2a548f164da1e66426b926d7a0ce066471cf6661f1683da02e88","8a79be9e69a9216a1ba76679150a3c4ef4377bed8e3786c6785cfde89de70c09"),
}

def main():
    code=fixture.main();report=json.loads(fixture.REPORT.read_text())
    report["kind"]="olmradialblur_rotation_pf32_offset_mode3_ui4_small_actual_aex_20260805"
    report["scope"]="independent PF32 Rotation mode 3/UI offset 4, padded 9x7; explicit bounded gate, no other offset/depth/geometry or AE-host claim"
    report["parameter_branch"]={
      "outer_strength":4,"outer_offset_mode":3,"outer_offset_ui":4,
      "worker_offset_zero_based":3,"radius_half":4,
      "dynamic_worker_spans_by_radius":[12,6,4,3,2,2,1,1,1],
      "ui3_spans":[8,4,2,2,1,1,1,1,0],"non_equivalent_to_ui3":True,
      "formula":"floor((radius_count/2)*(outer_offset_ui-1)/(radius_index+1))",
      "fixed_strength_branch_selected":False,"actual_output_differs_from_ui3":True,
    }
    report["weight_table_derivation"]={
      "table_length":30000,"denominator":"f32(f32(f32(30000*30000)*0.111111119389534)*2)+double(1e-5), then f32 reciprocal",
      "entry":"exponent=f32(-index_squared*inv_denom); value=f32(exp(double(exponent)))",
      "length12_index_scale":2500,
      "actual_length12_words":["0x3f800000","0x3f781fab","0x3f61eb51","0x3f413d2b","0x3f1b4598","0x3eea6923","0x3ea638da","0x3e5d74a1","0x3e0a9557","0x3da2f01b","0x3d33f73a","0x3cbabae3"],
      "policy":"one recovered float32 table-generation rule; no length/index-specific nextafter patches",
    }
    fixture.REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");return code

if __name__=="__main__":raise SystemExit(main())
