"""Replay legal Around + Thin owner witnesses through real-SDK public entries."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/emulation'))
import probe_olmcolorkey_around_composition_owner_20261001 as owner


def test_around_composition_public_owner_exact() -> None:
    with tempfile.TemporaryDirectory(prefix='olmck_around_replay_') as raw:
        executable = owner.compile_public(Path(raw)/'mac', owner.SOURCE.read_text())
        for filename, count in (('colorkey_around_composition_production_20261001.json',1080),
                                ('colorkey_around_composition_boundary_production_20261001.json',1512)):
            report = json.loads((ROOT/'reports'/filename).read_text())
            assert report['production'] and report['case_count'] == len(report['cases']) == count
            assert report['summary'] == {'classic':count,'smart':count}
            assert report['aex_sha256'] == owner.thin_owner.general.base.retained.actual_probe.AEX_SHA256
            identities = set()
            for case in report['cases']:
                fixture = case['fixture']
                source, _ = owner.thin_owner.general.fixture(fixture, case['depth'])
                assert owner.thin_owner.general.base.sha(source) == case['input_sha256']
                values = {p['slot']:p.get('value') for p in case['parameter_values']}
                required = {1:int(case['keep']),4:int(case['premultiplied']),14:case['thin'],
                            15:case['type'],18:4,19:2,20:2,23:int(case['replace'])}
                assert all(values[k] == v for k,v in required.items()) and case['guards_intact']
                identity = (fixture['id'],case['depth'],case['keep'],case['premultiplied'],case['replace'],case['thin'],case['type'])
                assert identity not in identities
                identities.add(identity)
                for route in (0,1):
                    output = subprocess.check_output([str(executable),str(fixture['width']),str(fixture['height']),
                        case['depth'][2:],str(case['thin']),str(case['type']),str(int(case['keep'])),str(route),
                        '4',str(int(case['premultiplied'])),str(int(case['replace']))],input=source)
                    assert len(output) == fixture['width']*fixture['height']*owner.thin_owner.general.DEPTHS[case['depth']]
                    assert owner.thin_owner.general.base.sha(output) == case['actual_sha256'],(identity,route)


def test_around_column_under_asan_ubsan() -> None:
    report = json.loads((ROOT/'reports/colorkey_around_composition_boundary_production_20261001.json').read_text())
    selected = [c for c in report['cases'] if c['fixture']['width']==1 and c['keep'] and
                not c['premultiplied'] and not c['replace'] and c['thin'] in (-100,0,100)]
    assert len(selected)==54
    with tempfile.TemporaryDirectory(prefix='olmck_column_sanitizers_') as raw:
        directory = Path(raw)/'mac'
        executable = owner.compile_public(directory, owner.SOURCE.read_text())
        sdk = subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
        subprocess.run(['clang++','-std=c++17','-arch','arm64','-O1','-g','-fno-fast-math','-ffp-contract=off',
            '-fsanitize=address,undefined','-fno-omit-frame-pointer','-Wno-pragma-pack','-Wno-deprecated-declarations',
            '-isysroot',sdk,'-IHeaders','-IHeaders/SP','-IUtil','-IResources','-Imac/OLMColorKey',
            str(directory/'public.cpp'),'mac/OLMColorKey/OLMColorKey_Strings.cpp','Util/AEGP_SuiteHandler.cpp',
            'Util/MissingSuiteError.cpp','-framework','Cocoa','-o',str(executable)],cwd=ROOT,check=True,capture_output=True)
        env = dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
        for case in selected:
            f=case['fixture']; source,_=owner.thin_owner.general.fixture(f,case['depth'])
            for route in (0,1):
                output = subprocess.check_output([str(executable),str(f['width']),str(f['height']),case['depth'][2:],
                    str(case['thin']),str(case['type']),'1',str(route),'4','0','0'],input=source,env=env)
                assert owner.thin_owner.general.base.sha(output)==case['actual_sha256']


if __name__=='__main__':
    test_around_composition_public_owner_exact()
    test_around_column_under_asan_ubsan()
