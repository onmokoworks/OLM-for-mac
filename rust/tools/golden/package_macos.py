"""Stage verified universal bundles using the C++ Mac metadata as authority."""
import json
import plistlib
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLUGINS = {
    'color-keep': 'ColorKeep', 'olm-blur': 'OLMBlur',
    'olm-color-key': 'OLMColorKey', 'olm-directional-blur': 'OLMDirectionalBlur',
    'olm-distance-gradation': 'OLMDistanceGradation', 'olm-kirakira': 'OLMKiraKira',
    'olm-radial-blur': 'OLMRadialBlur', 'olm-smoother': 'OLMSmoother',
    'olm-smoother2': 'OLMSmoother2', 'olm-toon-dilate': 'OLMToonDilate',
}


def pipl_properties(raw):
    """Read classic resource map, then the sole PiPL (ID 16000)."""
    data, rmap, _, _ = struct.unpack_from('>4I', raw)
    types = rmap + struct.unpack_from('>H', raw, rmap + 24)[0]
    assert struct.unpack_from('>H', raw, types)[0] == 0, 'one resource type required'
    assert raw[types+2:types+6] == b'PiPL'
    count, refs = struct.unpack_from('>HH', raw, types + 6)
    assert count == 0
    ref = types + refs
    assert struct.unpack_from('>h', raw, ref)[0] == 16000
    offset = int.from_bytes(raw[ref+5:ref+8], 'big')
    size = struct.unpack_from('>I', raw, data + offset)[0]
    pipl = raw[data+offset+4:data+offset+4+size]
    version, count = struct.unpack_from('>II', pipl)
    assert version == 0
    at, props = 8, {}
    for _ in range(count):
        vendor, key, ident, length = struct.unpack_from('>4s4sII', pipl, at)
        assert vendor == b'8BIM' and ident == 0 and key not in props
        props[key] = pipl[at+16:at+16+length]
        at += 16 + ((length + 3) // 4) * 4
    assert at == len(pipl)
    return props


def verify_resource(raw, name):
    props = pipl_properties(raw)
    source = (ROOT / 'mac' / name / f'{name}PiPL.r').read_text(encoding='utf-8')
    for key, field in [(b'name', 'Name'), (b'catg', 'Category'),
                       (b'eMNA', 'AE_Effect_Match_Name'), (b'eURL', 'AE_Effect_Support_URL')]:
        expected = re.search(r'\b' + field + r'\s*\{\s*"([^"]+)"', source)[1].encode()
        assert props[key][0] == len(expected) and props[key][1:1+len(expected)] == expected, field
    for key, field in [(b'eVER', 'AE_Effect_Version'), (b'eGLO', 'AE_Effect_Global_OutFlags'),
                       (b'eGL2', 'AE_Effect_Global_OutFlags_2')]:
        expected = int(re.search(r'\b' + field + r'\s*\{\s*(0x[0-9a-fA-F]+|\d+)', source)[1], 0)
        assert int.from_bytes(props[key], 'big') == expected, field
    assert props[b'kind'] == b'eFKT'
    assert props[b'ePVR'] == struct.pack('>HH', 2, 0)
    assert props[b'eSVR'] == struct.pack('>HH', 13, 28)
    assert props[b'eINF'] == b'\0\0'
    assert props[b'aeFL'] == b'\0' * 4
    assert props[b'mi64'] == b'\x0aEffectMain'
    assert props[b'ma64'] == b'\x0aEffectMain'
    assert len(props) == 14


def main():
    target, dest = (Path(x).resolve() for x in sys.argv[1:])
    assert not dest.exists(), 'refuse overwrite'
    dest.mkdir(parents=True)
    for crate, name in PLUGINS.items():
        arm = target / 'aarch64-apple-darwin/release'
        intel = target / 'x86_64-apple-darwin/release'
        resources = [(d / f'{crate}.rsrc').read_bytes() for d in (arm, intel)]
        assert resources[0] == resources[1], f'{name}: architecture-dependent PiPL'
        verify_resource(resources[0], name)
        bundle = dest / f'{name}.plugin'
        contents = bundle / 'Contents'
        (contents / 'MacOS').mkdir(parents=True)
        (contents / 'Resources').mkdir()
        exe = contents / 'MacOS' / name
        dylib = f'lib{crate.replace("-", "_")}.dylib'
        subprocess.run(['lipo', '-create', str(arm/dylib), str(intel/dylib), '-output', str(exe)], check=True)
        assert set(subprocess.check_output(['lipo', '-archs', str(exe)], text=True).split()) == {'arm64', 'x86_64'}
        for arch in ('arm64', 'x86_64'):
            symbols = subprocess.check_output(['nm', '-arch', arch, '-gU', str(exe)], text=True)
            for symbol in ('_EffectMain', '_PluginDataEntryFunction2'):
                assert re.search(r'\b' + symbol + r'$', symbols, re.M), (name, arch, symbol)
            build = subprocess.check_output(['xcrun', 'vtool', '-show-build', '-arch', arch, str(exe)], text=True)
            assert re.search(r'minos\s+11\.0\b', build), build
        original = ROOT / 'mac' / name / 'Mac'
        plist = plistlib.loads((original / f'{name}.plugin-Info.plist').read_bytes())
        project = (original / f'{name}.xcodeproj/project.pbxproj').read_text(encoding='utf-8')
        ids = set(re.findall(r'PRODUCT_BUNDLE_IDENTIFIER = "?([^";]+)"?;', project))
        assert len(ids) == 1
        plist.update(CFBundleIdentifier=ids.pop(), CFBundleExecutable=name, CFBundleName=name,
                     CFBundlePackageType='eFKT', CFBundleSignature='FXTC', LSMinimumSystemVersion='11.0')
        (contents / 'Info.plist').write_bytes(plistlib.dumps(plist))
        assert (arm / f'{crate}_PkgInfo').read_bytes() == b'eFKTFXTC'
        assert (intel / f'{crate}_PkgInfo').read_bytes() == b'eFKTFXTC'
        (contents / 'PkgInfo').write_bytes(b'eFKTFXTC')
        (contents / 'Resources' / f'{name}.rsrc').write_bytes(resources[0])
        # ARM Mach-O needs a valid ad-hoc seal after lipo; this is not Developer ID signing.
        subprocess.run(['codesign', '--force', '--sign', '-', str(bundle)], check=True)
        subprocess.run(['codesign', '--verify', '--deep', '--strict', str(bundle)], check=True)
        print(f'{name}: universal, PiPL matches C++ Mac declaration, ad-hoc seal verified')
    shutil.copy2(ROOT / 'LICENSE', dest / 'LICENSE')
    shutil.copy2(ROOT / 'ucrtmath/NOTICE', dest / 'UCRTMATH-NOTICE')


if __name__ == '__main__':
    main()
