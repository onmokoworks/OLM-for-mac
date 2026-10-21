#!/usr/bin/env python3
"""Validate bounded public admissions and fail-closed owner/lifecycle guards."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
V1=ROOT/'mac/OLMSmoother/Mac/OLMSmoother_port.cpp'
V2=ROOT/'mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp'
SHIM1=ROOT/'cli/OLMSmoother/shim/OLMSmoother.h'
H1=ROOT/'tools/emulation/olmsmoother_v1_public_guard_harness_20260812.cpp'
H2=ROOT/'tools/emulation/olmsmoother2_public_guard_harness_20260812.cpp'
UNIT=ROOT/'tools/emulation/test_olmsmoother_public_admission_guard_closure_unit_20260812.py'
REAL_SUITE_PROBE=ROOT/'tools/emulation/probe_olmsmoother_real_sdk_suite_lifecycle_20260813.cpp'
REAL_SUITE_UNIT=ROOT/'tests/test_olmsmoother_real_sdk_suite_lifecycle_20260813.py'
SHA_ROWS=ROOT/'core/olm_sha256_rows.h'
REPORT=ROOT/'refs/conformance/olmsmoother_public_admission_guard_closure_20260812.json'
DOC=ROOT/'refs/conformance/olmsmoother_public_admission_guard_closure_20260812.md'
INVENTORY=[
 ROOT/'refs/conformance/olmsmoother_v1_case0001_pf8_fullframe_actual_aex_20260805.json',
 ROOT/'refs/conformance/olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810.json',
 ROOT/'refs/conformance/olmsmoother_v1_colored_fractional_alpha_actual_aex_20260811.json',
 ROOT/'refs/conformance/olmsmoother_v1_pf16_colorkey_effectmain_actual_production_20260810.json',
 ROOT/'refs/conformance/olmsmoother_v1_pf16_practical_geometry_actual_aex_20260812.json',
 ROOT/'refs/conformance/olmsmoother2_effectmain_pf16_chain_installed_20260805.json',
 ROOT/'refs/conformance/olmsmoother2_effectmain_pf32_smart_chain_installed_20260805.json',
 ROOT/'refs/conformance/olmsmoother2_public_effectmain_all_depths_actual_aex_20260812.json',
 ROOT/'refs/conformance/olmsmoother2_exported_owner_version_key_gamma_smoothing_20260811.json',
 ROOT/'refs/conformance/olmsmoother2_gamma18_keyendpoint_exported_owner_closure_20260812.json',
 ROOT/'refs/conformance/olmsmoother2_public_smoothing_endpoints_actual_aex_20260810.json',
 ROOT/'refs/conformance/olmsmoother2_semtransparent_premul_actual_aex_20260810.json',
 ROOT/'refs/conformance/olmsmoother2_gamma_key_smoothing_crossproduct_actual_aex_20260812.json',
]
VERDICT='PASS_69_SOURCE_BOUND_ATOMIC_PUBLIC_GUARD_AND_LIFECYCLE_CASES'
SCOPE='OLMSmoother classic and OLMSmoother2 Smart owner guards; entry-specific fixed-source public/exported-owner exact-evidence admission maps; source mutations, partial overlap, unowned entries, malformed worlds, PF32 classic, one-away tuples/geometries, and partial callback failures fail closed'
AEX={'OLMSmoother':'6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82','OLMSmoother2':'7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7'}
ADMISSION={
 'OLMSmoother classic':['PF8 960x540 tight canonical no-key/tolerance6','PF8/PF16 7x5 +8 bytes row padding, key (202,187,230), key off/on, tolerance 0/1/6/127/255','PF16 64x36 +32 bytes padding, key off/on, tolerance 6/127','PF16 5x3 rowbytes48 key-on tolerance6'],
 'OLMSmoother Smart':[],
 'OLMSmoother2 classic':[],
 'OLMSmoother2 Smart':['3x2 installed-owner PF32 default cell','5x5 Gamma1.8 exported-owner 12 cells','5x5 Gamma2.4 exported-owner representatives','17x11 six-cell public EffectMain all-depth matrix']}
WORLD=['non-null input/output data with overflow-safe disjoint active spans','same positive dimensions','same positive rowbytes with active span and row-offset capacity','full-frame input/output extent hints','input/output format equality from PF World Suite v2','classic PF32 rejected for both plug-ins','exact admitted geometry/rowbytes and fixed active-source SHA-256 only']
LIFECYCLE=['check in only parameters whose checkout succeeded','check in input layer after every successful layer checkout, including later output/parameter failure','do not check in input layer when layer checkout failed','render into aligned private staging and commit only after successful parameter/layer cleanup','propagate ColorParamSuite and parameter-checkin errors while leaving host output untouched','do not union uninitialized checkout rectangles after SmartPreRender failure','leave output bytes untouched on rejected cases']
CLAIMS=['No arbitrary input or parameter-product generalization','No direct-core-only fixture is promoted to a public admission','No v1 Smart or v2 classic numerical ownership','No admission outside the listed entry, geometry/rowbytes, and parameter cells','No installed bundle or AE-host claim from this closure']
REPORT_KEYS={'schema','verdict','scope','actual_aex_sha256','guard_cases','case_ids','admission_map','world_contract','lifecycle_contract','real_sdk_suite_lifecycle','identities','claims_not_made'}
DOC_TEXT='# OLMSmoother / OLMSmoother2 source-bound public admission guards\n\nVerdict: `PASS_69_SOURCE_BOUND_ATOMIC_PUBLIC_GUARD_AND_LIFECYCLE_CASES`\n\nBoth implementations obtain input and output pixel formats from the output-owning world contract and require matching worlds with overflow-safe disjoint active spans and proven row layouts. Admission is entry-specific and fixed-source: OLMSmoother v1 admits only retained exported classic-owner tuples paired with their rowwise active-source SHA-256; OLMSmoother2 does the same for retained Smart-owner cells. V1 Smart and v2 classic remain fail-closed.\n\nThirty OLMSmoother and thirty-nine OLMSmoother2 cases cover accepted evidence cells, unaligned PF16 input safely copied into aligned staging, first/middle source mutation rejection, both partial-overlap directions, unowned-entry and PF32 classic rejection, format/data/dimension/rowbytes/row-offset/extent/layout faults, inactive-field and tuple/geometry one-aways, ColorParamSuite returned errors and one-ULP decoded-color mutation, parameter/layer checkin failures, and partial Smart/PreRender checkout failures. Padding is excluded from source identity. Numerical work uses aligned private staging; host output is committed only after successful cleanup. Rejected/error outputs and failed PreRender rectangles remain untouched. Direct-core-only fixtures and the synthetic 3x2 PF16 classic adapter remain regression evidence but are not public admissions. Universal build, install, and AE smoke are separate gates.\n'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def run_harness(source:Path,shim:Path)->list[str]:
 with tempfile.TemporaryDirectory(prefix='smoother-guard-') as td:
  exe=Path(td)/'h'
  subprocess.run(['clang++','-std=c++17','-O2','-I',str(shim),'-I',str(source.parent.parent),str(source),'-o',str(exe)],check=True)
  out=subprocess.run([str(exe)],check=True,text=True,capture_output=True).stdout.splitlines()
 return out
def cases(lines:list[str],expected:int)->list[str]:
 rows=[x for x in lines if x.startswith('CASE ')]
 if len(rows)!=expected or any(not x.endswith(' PASS') for x in rows):raise RuntimeError(f'guard harness failed: {rows}')
 if f'SUMMARY {expected} {expected}' not in lines:raise RuntimeError('summary drift')
 return [x.split()[1] for x in rows]
def identities()->dict:
 return {'production_v1_sha256':sha(V1),'production_v2_sha256':sha(V2),'shim_v1_sha256':sha(SHIM1),
         'sha256_rows_header_sha256':sha(SHA_ROWS),
         'harness_v1_sha256':sha(H1),'harness_v2_sha256':sha(H2),'generator_sha256':sha(Path(__file__)),
         'validator_unit_sha256':sha(UNIT),
         'real_sdk_suite_probe_sha256':sha(REAL_SUITE_PROBE),'real_sdk_suite_unit_sha256':sha(REAL_SUITE_UNIT),
         'documentation_sha256':sha(DOC),
         'inventory':{str(p.relative_to(ROOT)):sha(p) for p in INVENTORY}}
def validate_source()->None:
 for path,text in ((V1,V1.read_text()),(V2,V2.read_text())):
  required=['WorldDepth(','ValidatePublicWorlds(','input_begin < output_begin + span','input_depth != output_depth',
            'param_checked_out[SM_NUM_PARAMS]','layer_checked_out','PF_Err_BAD_CALLBACK_PARAM']
  if any(x not in text for x in required):raise RuntimeError(f'guard token missing: {path}')
 if 'input_depth != output_depth || input_depth == 32' not in V1.read_text():raise RuntimeError('v1 PF32 owner guard missing')
 if 'V1SourceIs(' not in V1.read_text() or 'V2SourceIs(' not in V2.read_text():raise RuntimeError('fixed-source guard missing')
 if 'return PF_Err_BAD_CALLBACK_PARAM;' not in V2.read_text() or 'V2SmartAdmission' not in V2.read_text():raise RuntimeError('v2 entry-specific owner guard missing')
def validate_report()->None:
 d=json.loads(REPORT.read_text())
 if set(d)!=REPORT_KEYS:raise RuntimeError('top-level schema drift')
 if d.get('schema')!='olm.smoother-public-admission-guard/1' or d.get('verdict')!=VERDICT or d.get('scope')!=SCOPE:raise RuntimeError('header drift')
 if d.get('identities')!=identities():raise RuntimeError('identity drift')
 if d.get('guard_cases')!={'OLMSmoother':30,'OLMSmoother2':39,'total':69}:raise RuntimeError('count drift')
 expected_ids={'OLMSmoother':cases(run_harness(H1,ROOT/'cli/OLMSmoother/shim'),30),'OLMSmoother2':cases(run_harness(H2,ROOT/'cli/OLMSmoother2/shim'),39)}
 if d.get('case_ids')!=expected_ids:raise RuntimeError('case id/result drift')
 if d.get('actual_aex_sha256')!=AEX or d.get('admission_map')!=ADMISSION:raise RuntimeError('oracle/admission drift')
 if d.get('world_contract')!=WORLD or d.get('lifecycle_contract')!=LIFECYCLE or d.get('claims_not_made')!=CLAIMS:raise RuntimeError('contract drift')
 if d.get('real_sdk_suite_lifecycle')!={'OLMSmoother':{'world_cases':6},'OLMSmoother2':{'world_cases':6,'color_cases':6},'result':'PASS'}:raise RuntimeError('real SDK suite lifecycle drift')
 if DOC.read_text()!=DOC_TEXT:raise RuntimeError('documentation drift')
 validate_source()
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--validate-only',action='store_true');a=ap.parse_args()
 if a.validate_only:validate_report();print(VERDICT);return 0
 validate_source()
 v1=cases(run_harness(H1,ROOT/'cli/OLMSmoother/shim'),30)
 v2=cases(run_harness(H2,ROOT/'cli/OLMSmoother2/shim'),39)
 DOC.write_text(DOC_TEXT)
 report={
  'schema':'olm.smoother-public-admission-guard/1','verdict':VERDICT,'scope':SCOPE,'actual_aex_sha256':AEX,
  'guard_cases':{'OLMSmoother':len(v1),'OLMSmoother2':len(v2),'total':len(v1)+len(v2)},
  'case_ids':{'OLMSmoother':v1,'OLMSmoother2':v2},
 'admission_map':ADMISSION,'world_contract':WORLD,'lifecycle_contract':LIFECYCLE,
  'real_sdk_suite_lifecycle':{'OLMSmoother':{'world_cases':6},'OLMSmoother2':{'world_cases':6,'color_cases':6},'result':'PASS'},
  'identities':identities(),
  'claims_not_made':CLAIMS}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 validate_report();print(report['verdict']);return 0
if __name__=='__main__':raise SystemExit(main())
