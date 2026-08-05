#!/usr/bin/env python3
"""PF16 Rotation offset mode 3/UI 3 actual-AEX/production fixture."""

import json
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as fixture

fixture.FIXTURE_OUTER_STRENGTH=4;fixture.FIXTURE_OUTER_OFFSET_MODE=3;fixture.FIXTURE_OUTER_OFFSET=3
fixture.FIXTURE=fixture.ROOT/"refs/fixtures/olmradialblur_rotation_pf16_offset_mode3_ui3_small_20260805"
fixture.REPORT=fixture.ROOT/"refs/conformance/olmradialblur_rotation_pf16_offset_mode3_ui3_small_actual_aex_20260805.json"
fixture.EXPECTED={
 "source_pf16":("d059727f9096038fea75037a9ba49b82f99c9dd84fd74b15fb11b09f72ca6f85","5a57d8c8f898bfc576ba38654a81eccf47635c5c30314d59c7c86e8a8ab29f55"),
 "polar":("aa822e3d1353b5eeff97581c7bf20bf4c73e8def305a9f2e4cb00f140aaa9ce3","5a083bd125c501c5d2b3aba8b02f7c7d366917e9bfaf289a92ca91bb6a9e2690"),
 "source_scalar":("7b4468c91d59a9b63747818dfcd672e87646e3c9b05bc3d7ce8d4efc160826bc","21d9bf07a607e761267078f796e5c6462d90df31d4e2d66f900655de740a75a4"),
 "accum":("eae0443e8886c9f678897b16629efae682db077bc3151994bfa18deb066c5098","8645a4bc83b908303b5461138475a3e4c9979ec1e0fd2738b95b412a6de1bf63"),
 "max_alpha":("4408f98deb7c33c7bd738f47da8ca5032c8638aa7ec8abebea179d9eb8be759c","2ffa2dbb1641d2e2f4ea08cfe2fdc08349470b0189b98991a89a5603c6c686f3"),
 "coordinates":("e9c455c90aa39569783043925d1b890ae7cd67728a09a729b665d8b67976d07b","aaccf447e96339787ca82d3003a056cae7c03cab57f626370fb06ce1d60d1937"),
 "final_rgba":("bc9937f6c44315d474aae7785cfb49fc7bd9b7979d39e53dfbbb5b52620cefd7","a79a6a13c7054b31eb36418365cc44e3ed14c793d9c1b0df6ee28d52d4260872"),
 "output":("25341b4983740601bbd1f48d1b23a6dc0d684cf79a4ccd4e6a3ff15cdc77ff58","1bb6eeb5f9a663eec68ff83cde483478720c4694a8f9300690d22d5be8b63456"),
}

def main():
    code=fixture.main();report=json.loads(fixture.REPORT.read_text())
    report["kind"]="olmradialblur_rotation_pf16_offset_mode3_ui3_small_actual_aex_20260805"
    report["scope"]="independent PF16 Rotation mode 3/UI offset 3, padded 9x7; no PF32 quantization reuse, other offset/depth/geometry, or AE-host claim"
    report["parameter_branch"]={
      "outer_strength":4,"outer_offset_mode":3,"outer_offset_ui":3,"worker_offset_zero_based":2,
      "radius_half":4,"dynamic_worker_spans_by_radius":[8,4,2,2,1,1,1,1,0],
      "ui2_spans":[4,2,1,1,0,0,0,0,0],"non_equivalent_to_ui2":True,
      "formula":"floor((radius_count/2)*(outer_offset_ui-1)/(radius_index+1))",
      "weight_table_rule":"actual 30000-entry float32 exponent generation sampled independently by PF16 owner",
      "length8_actual_words":{"i5":"0x3e308f4e","i7":"0x3d02a41f"},
    }
    report["typed_pf16_contract"]={
      "source":"PF_Pixel16 ARGB words normalized independently by float32 multiply with 1/32768",
      "writer":"FUN_180017440: float32 multiply by 32768, CVTTSS2SI, low u16 ARGB stores",
      "pf8_or_pf32_quantization_reused":False,"rowbytes":80,"visible_bytes":72,"padding_bytes":8,
    }
    fixture.REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");return code

if __name__=="__main__":raise SystemExit(main())
