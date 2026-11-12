"""Build and stage this plug-in alone on macOS; unqualified until run on both CPUs.
No installation, signing identity, notarization, shared workspace edits or GUI.
"""
import argparse,os,plistlib,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent

def stage(out):
    if sys.platform!='darwin':raise SystemExit('Run on macOS with Xcode command-line tools and both Rust targets installed.')
    out=out.resolve();out.mkdir(parents=True,exist_ok=False)
    tree=out/'source';tree.mkdir()
    for name in ['src','resources','tests']:shutil.copytree(HERE/name,tree/name)
    for name in ['Cargo.toml','build.rs']:shutil.copyfile(HERE/name,tree/name)
    with (tree/'Cargo.toml').open('a') as f:f.write('\n[workspace]\n')
    target=out/'target';env={**os.environ,'CARGO_TARGET_DIR':str(target),'MACOSX_DEPLOYMENT_TARGET':'11.0'}
    for arch in ['aarch64-apple-darwin','x86_64-apple-darwin']:
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(tree/'Cargo.toml'),'--target',arch,'-j','2'],env=env,check=True)
    crate='olm-anti-anti-alias';name='OLMAntiAntiAlias'
    arm=target/'aarch64-apple-darwin/release';intel=target/'x86_64-apple-darwin/release'
    raw=(arm/f'{crate}.rsrc').read_bytes()
    if raw!=(intel/f'{crate}.rsrc').read_bytes():raise ValueError('PiPL differs by architecture')
    sys.path.insert(0,str(HERE.parents[1]/'tools/golden'))
    from package_macos import pipl_properties
    props=pipl_properties(raw)
    for key,text in [(b'name','OLM Anti Anti Alias'),(b'eMNA','OLM OLM Anti Anti Alias'),(b'catg','OLM Plug-ins')]:
        if props[key]!=bytes([len(text)])+text.encode():raise ValueError(f'PiPL {key!r} mismatch')
    for key,value in [(b'eVER',569344),(b'eGLO',33554496),(b'eGL2',134222848)]:
        if int.from_bytes(props[key],'big')!=value:raise ValueError(f'PiPL {key!r} mismatch')
    for key in [b'mi64',b'ma64']:
        if props[key]!=b'\x0aEffectMain':raise ValueError('entry mismatch')
    bundle=out/f'{name}.plugin';c=bundle/'Contents';(c/'MacOS').mkdir(parents=True);(c/'Resources').mkdir()
    exe=c/'MacOS'/name;lib='libolm_anti_anti_alias.dylib'
    subprocess.run(['lipo','-create',str(arm/lib),str(intel/lib),'-output',str(exe)],check=True)
    if set(subprocess.check_output(['lipo','-archs',str(exe)],text=True).split())!={'arm64','x86_64'}:raise ValueError('architecture mismatch')
    for arch in ['arm64','x86_64']:
        symbols=subprocess.check_output(['nm','-arch',arch,'-gU',str(exe)],text=True)
        if not all(s in symbols for s in ['_EffectMain','_PluginDataEntryFunction2']):raise ValueError('missing entry export')
    (c/'Info.plist').write_bytes(plistlib.dumps(dict(CFBundleIdentifier='local.olm-rs.anti-anti-alias',CFBundleExecutable=name,CFBundleName=name,CFBundlePackageType='eFKT',CFBundleSignature='FXTC',CFBundleVersion='1.1.6',CFBundleShortVersionString='1.1.6',LSMinimumSystemVersion='11.0')))
    (c/'PkgInfo').write_bytes(b'eFKTFXTC');(c/'Resources'/f'{name}.rsrc').write_bytes(raw)
    subprocess.run(['codesign','--force','--sign','-',str(bundle)],check=True)
    subprocess.run(['codesign','--verify','--deep','--strict',str(bundle)],check=True)
    print(bundle)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);stage(p.parse_args().out)
